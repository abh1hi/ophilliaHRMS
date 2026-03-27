"""Idempotency middleware for safe API retries (multi-tenant, production-grade).

Intercepts POST/PATCH requests with an `Idempotency-Key` header.
- First request: executes normally, stores response.
- Duplicate request (same tenant + key): returns stored response without re-executing.
- Same key + different payload: returns 422 (payload mismatch).
- Stuck "processing" entries older than PROCESSING_TIMEOUT_MINUTES: auto-recovered.

All lookups are scoped to (company_id, key) for tenant isolation.
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone

from fastapi import Request, Response
from jose import jwt, JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy import select, and_, delete

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.idempotency_key import IdempotencyKey, PROCESSING_TIMEOUT_MINUTES

logger = logging.getLogger(__name__)

IDEMPOTENCY_TTL_HOURS = 24
IDEMPOTENT_METHODS = {"POST", "PATCH"}
SKIP_PATHS = {"/health"}


def _hash_body(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _extract_company_id(request: Request) -> str | None:
    """Extract company_id from the Bearer JWT without full auth validation.

    This is safe because the actual auth check happens later in the route
    dependency chain.  We only need the tenant scope for idempotency lookup.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    try:
        # Decode without verification — auth middleware validates later
        payload = jwt.decode(
            token, settings.JWT_PUBLIC_KEY, algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},
        )
        return payload.get("company_id")
    except JWTError:
        return None


def _error_json(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "error": {"code": code, "message": message},
        },
    )


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in IDEMPOTENT_METHODS:
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        if request.url.path in SKIP_PATHS:
            return await call_next(request)

        company_id = _extract_company_id(request)
        if not company_id:
            # No tenant context — skip idempotency (auth will reject later anyway)
            return await call_next(request)

        body = await request.body()
        body_hash = _hash_body(body)
        request_path = request.url.path
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        stuck_threshold = now - timedelta(minutes=PROCESSING_TIMEOUT_MINUTES)

        try:
            async with AsyncSessionLocal() as db:
                # ── Lookup: tenant-scoped ──
                result = await db.execute(
                    select(IdempotencyKey).where(
                        and_(
                            IdempotencyKey.company_id == company_id,
                            IdempotencyKey.key == idempotency_key,
                        )
                    ).with_for_update(skip_locked=True)
                )
                existing = result.scalars().first()

                if existing:
                    # ── Payload mismatch ──
                    if existing.request_body_hash and existing.request_body_hash != body_hash:
                        logger.warning(
                            f"Idempotency payload mismatch: tenant={company_id} key={idempotency_key}",
                            extra={"idempotency_key": idempotency_key, "company_id": company_id},
                        )
                        return _error_json(
                            422, "IDEMPOTENCY_PAYLOAD_MISMATCH",
                            "Idempotency key was already used with a different request payload",
                        )

                    # ── Stuck processing recovery ──
                    if existing.status == "processing":
                        if existing.created_at < stuck_threshold:
                            # Stuck for > PROCESSING_TIMEOUT_MINUTES — delete and allow retry
                            logger.warning(
                                f"Idempotency stuck recovery: tenant={company_id} key={idempotency_key} "
                                f"age={now - existing.created_at}",
                                extra={"idempotency_key": idempotency_key, "company_id": company_id},
                            )
                            await db.delete(existing)
                            await db.commit()
                            # Fall through to create new entry below
                        else:
                            # Genuinely in-flight
                            return _error_json(
                                409, "IDEMPOTENCY_IN_PROGRESS",
                                "A request with this idempotency key is already being processed",
                            )
                    # ── Completed — replay cached response ──
                    elif existing.status == "completed" and existing.response_body:
                        logger.info(
                            f"Idempotency cache hit: tenant={company_id} key={idempotency_key}",
                            extra={"idempotency_key": idempotency_key, "company_id": company_id, "duplicate": True},
                        )
                        return Response(
                            content=existing.response_body,
                            status_code=existing.response_status,
                            media_type="application/json",
                            headers={"X-Idempotency-Replayed": "true"},
                        )
                    # ── Error — allow retry ──
                    elif existing.status == "error":
                        await db.delete(existing)
                        await db.commit()
                    else:
                        # completed but no body — treat as error, allow retry
                        await db.delete(existing)
                        await db.commit()

                # ── Create new idempotency entry (mark as processing) ──
                # Re-open session if we committed above (delete path)
                async with AsyncSessionLocal() as db2:
                    idem_entry = IdempotencyKey(
                        company_id=company_id,
                        key=idempotency_key,
                        request_path=request_path,
                        request_method=request.method,
                        request_body_hash=body_hash,
                        status="processing",
                        created_at=now,
                        expires_at=now + timedelta(hours=IDEMPOTENCY_TTL_HOURS),
                    )
                    db2.add(idem_entry)
                    try:
                        await db2.commit()
                    except Exception:
                        await db2.rollback()
                        return _error_json(
                            409, "IDEMPOTENCY_IN_PROGRESS",
                            "A request with this idempotency key is already being processed",
                        )

        except Exception:
            logger.exception("Idempotency middleware DB error — proceeding without idempotency")
            return await call_next(request)

        # ── Execute the actual request ──
        response = await call_next(request)

        # ── Store the response ──
        try:
            response_body = b""
            async for chunk in response.body_iterator:
                if isinstance(chunk, str):
                    response_body += chunk.encode()
                else:
                    response_body += chunk

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(IdempotencyKey).where(
                        and_(
                            IdempotencyKey.company_id == company_id,
                            IdempotencyKey.key == idempotency_key,
                        )
                    )
                )
                entry = result.scalars().first()
                if entry:
                    entry.response_status = response.status_code
                    entry.response_body = response_body.decode("utf-8", errors="replace")
                    entry.status = "completed" if response.status_code < 500 else "error"
                    await db.commit()

            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        except Exception:
            logger.exception("Failed to store idempotency response")
            try:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(IdempotencyKey).where(
                            and_(
                                IdempotencyKey.company_id == company_id,
                                IdempotencyKey.key == idempotency_key,
                            )
                        )
                    )
                    entry = result.scalars().first()
                    if entry:
                        entry.status = "error"
                        await db.commit()
            except Exception:
                pass
            return Response(
                content=response_body,
                status_code=response.status_code,
                media_type=response.media_type,
            )
