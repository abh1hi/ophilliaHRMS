"""Retention background task.

Runs once on service startup. Deletes audit log rows older than
LOG_RETENTION_DAYS (default: 730 days / 2 years).

Audit tables grow fast — this prevents unbounded disk growth.
"""
import logging
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.repositories.audit_log_repository import AuditLogRepository

logger = logging.getLogger(__name__)


async def run_retention_cleanup() -> None:
    """Delete audit logs older than LOG_RETENTION_DAYS.

    Called once from the FastAPI lifespan on startup.
    Non-fatal: if this fails the service continues normally.
    """
    try:
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
            days=settings.LOG_RETENTION_DAYS
        )
        async with AsyncSessionLocal() as session:
            repo = AuditLogRepository(session)
            deleted = await repo.delete_older_than(cutoff)
            logger.info(
                f"Retention cleanup complete",
                extra={
                    "service_task": "retention_cleanup",
                    "deleted_rows": deleted,
                    "cutoff_date": cutoff.isoformat(),
                    "retention_days": settings.LOG_RETENTION_DAYS,
                },
            )
    except Exception as exc:
        logger.error(
            f"Retention cleanup failed (non-fatal): {exc}",
            extra={"service_task": "retention_cleanup"},
        )
