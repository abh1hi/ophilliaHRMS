"""Idempotency support for payroll API endpoints.

Prevents duplicate payroll runs for the same logical operation within 24 hours.
Uses Idempotency-Key header (RFC 9110) + database response caching.
"""
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payroll import PayrollRun
from app.repositories.payroll_repository import PayrollRepository

logger = logging.getLogger(__name__)

IDEMPOTENCY_CACHE_TTL_HOURS = 24


def parse_idempotency_key(header_value: Optional[str]) -> Optional[str]:
    """Parse and validate Idempotency-Key header.

    Args:
        header_value: Idempotency-Key header value

    Returns:
        Normalized key (max 64 chars), or None if invalid

    RFC 9110: Key must be a string, preferably a UUID or similar
    """
    if not header_value:
        return None

    # Trim and validate
    key = header_value.strip()

    if len(key) > 64:
        logger.warning(f"Idempotency key too long: {len(key)} > 64")
        return None

    # Basic validation: alphanumeric, hyphens, underscores
    if not all(c.isalnum() or c in "-_" for c in key):
        logger.warning(f"Invalid idempotency key characters: {key}")
        return None

    return key


async def check_idempotency(
    db: AsyncSession,
    run_id: UUID,
    idempotency_key: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Check if request has been seen before (idempotency cache hit).

    Args:
        db: Database session
        run_id: PayrollRun ID
        idempotency_key: Idempotency key from request

    Returns:
        Cached response (dict) if hit and not expired, None otherwise
    """
    if not idempotency_key:
        return None

    repo = PayrollRepository(db)
    run = await repo.get_payroll_run(run_id)

    if not run:
        return None

    # Check if key matches and cache not expired
    if run.idempotency_key == idempotency_key and run.idempotency_response:
        if run.idempotency_expires_at and run.idempotency_expires_at > datetime.now(timezone.utc).replace(tzinfo=None):
            logger.info(f"Idempotency cache hit: {idempotency_key}")
            return run.idempotency_response

    return None


async def cache_idempotency_response(
    db: AsyncSession,
    run: PayrollRun,
    idempotency_key: str,
    response_data: Dict[str, Any],
) -> None:
    """Cache API response for idempotency.

    Args:
        db: Database session
        run: PayrollRun model
        idempotency_key: Request idempotency key
        response_data: Response body to cache (dict)
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = now + timedelta(hours=IDEMPOTENCY_CACHE_TTL_HOURS)

    run.idempotency_key = idempotency_key
    run.idempotency_response = response_data
    run.idempotency_expires_at = expires_at

    repo = PayrollRepository(db)
    await repo.update_payroll_run(run)
    logger.debug(f"Idempotency cached: {idempotency_key} (expires {expires_at})")


async def clear_idempotency_cache(
    db: AsyncSession,
    run: PayrollRun,
) -> None:
    """Clear cached response (for state transitions).

    Args:
        db: Database session
        run: PayrollRun model
    """
    run.idempotency_response = None
    run.idempotency_expires_at = None

    repo = PayrollRepository(db)
    await repo.update_payroll_run(run)
