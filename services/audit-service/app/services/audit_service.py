import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SENSITIVE_PAYLOAD_KEYS
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.audit_log import AuditLogFilter, AuditLogListResponse, AuditLogResponse

logger = logging.getLogger(__name__)


def sanitize_payload(payload: dict) -> dict:
    """Remove sensitive keys from the event payload before storing.

    Performs a shallow top-level key scrub. Nested sensitive keys are
    replaced with the string "[REDACTED]" to preserve structure.
    """
    if not isinstance(payload, dict):
        return {}

    sanitized = {}
    for key, value in payload.items():
        if key.lower() in SENSITIVE_PAYLOAD_KEYS:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_payload(value)
        else:
            sanitized[key] = value
    return sanitized


class AuditService:
    def __init__(self, db: AsyncSession):
        self.repo = AuditLogRepository(db)

    async def record_event(self, raw_event: dict) -> Optional[AuditLogResponse]:
        """Parse, sanitize, and persist a domain event.

        Returns the created AuditLogResponse, or None if the event was a duplicate.
        """
        event_id_raw = raw_event.get("event_id")
        if not event_id_raw:
            logger.warning(
                "Received event without event_id — skipping",
                extra={"service_task": "record_event"},
            )
            return None

        try:
            event_id = UUID(str(event_id_raw))
        except ValueError:
            logger.warning(
                f"Invalid event_id format: {event_id_raw}",
                extra={"service_task": "record_event"},
            )
            return None

        # Idempotency gate — silently skip already-processed events
        if await self.repo.exists(event_id):
            logger.info(
                f"Duplicate event skipped",
                extra={"service_task": "record_event", "event_id": str(event_id)},
            )
            return None

        payload = sanitize_payload(raw_event.get("payload", {}))

        # Parse timestamp from event; fall back to now()
        raw_ts = raw_event.get("timestamp")
        try:
            timestamp = datetime.fromisoformat(raw_ts) if raw_ts else datetime.now(timezone.utc)
        except (ValueError, TypeError):
            timestamp = datetime.now(timezone.utc)
        # Store as tz-naive UTC
        timestamp = timestamp.replace(tzinfo=None)

        # Parse optional UUIDs safely
        def _uuid_or_none(val):
            try:
                return UUID(str(val)) if val else None
            except (ValueError, AttributeError):
                return None

        data = {
            "id": uuid.uuid4(),
            "event_id": event_id,
            "event_version": int(raw_event.get("event_version", 1)),
            "event_type": str(raw_event.get("event_type", "unknown")),
            "service_source": str(raw_event.get("service_source", "unknown")),
            # company_id — may be in payload or top-level
            "company_id": _uuid_or_none(
                raw_event.get("company_id") or payload.get("company_id")
            ) or uuid.uuid4(),  # fallback UUID (should never happen in practice)
            "user_id": _uuid_or_none(raw_event.get("user_id") or payload.get("user_id")),
            "correlation_id": _uuid_or_none(raw_event.get("correlation_id")),
            "ip_address": raw_event.get("ip_address"),
            "user_agent": raw_event.get("user_agent"),
            "http_method": raw_event.get("http_method"),
            "endpoint": raw_event.get("endpoint"),
            "payload": payload,
            "timestamp": timestamp,
        }

        log = await self.repo.create(data)
        logger.info(
            "Audit event recorded",
            extra={"service_task": "record_event", "event_id": str(event_id), "event_type": data["event_type"]},
        )
        return AuditLogResponse.model_validate(log)

    async def get_log(self, log_id: UUID) -> Optional[AuditLogResponse]:
        log = await self.repo.get_by_id(log_id)
        if not log:
            return None
        return AuditLogResponse.model_validate(log)

    async def query_logs(self, filters: AuditLogFilter) -> AuditLogListResponse:
        items = await self.repo.list_logs(filters)
        total = await self.repo.count_logs(filters)
        return AuditLogListResponse(
            items=[AuditLogResponse.model_validate(i) for i in items],
            total=total,
            skip=filters.skip,
            limit=filters.limit,
        )
