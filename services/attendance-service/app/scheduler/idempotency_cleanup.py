"""Background job to clean up expired idempotency keys.

Runs periodically (default: every 60 minutes) and deletes:
1. Completed/error entries past their expires_at TTL
2. Stuck "processing" entries older than PROCESSING_TIMEOUT_MINUTES

This keeps the idempotency_keys table small and prevents unbounded growth
under high-throughput scenarios (1000+ req/min).
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.idempotency_key import IdempotencyKey, PROCESSING_TIMEOUT_MINUTES

logger = logging.getLogger(__name__)


async def cleanup_expired_idempotency_keys(db: AsyncSession) -> dict:
    """Delete expired and stuck idempotency key entries.

    Returns a dict with counts of deleted entries by category.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    stuck_threshold = now - timedelta(minutes=PROCESSING_TIMEOUT_MINUTES)

    # 1. Delete expired entries (completed or error, past TTL)
    expired_result = await db.execute(
        delete(IdempotencyKey).where(
            and_(
                IdempotencyKey.expires_at < now,
                IdempotencyKey.status.in_(["completed", "error"]),
            )
        ).returning(IdempotencyKey.id)
    )
    expired_count = len(expired_result.all())

    # 2. Delete stuck "processing" entries older than timeout
    stuck_result = await db.execute(
        delete(IdempotencyKey).where(
            and_(
                IdempotencyKey.status == "processing",
                IdempotencyKey.created_at < stuck_threshold,
            )
        ).returning(IdempotencyKey.id)
    )
    stuck_count = len(stuck_result.all())

    await db.commit()

    total = expired_count + stuck_count
    if total > 0:
        logger.info(
            f"Idempotency cleanup: deleted {expired_count} expired, {stuck_count} stuck "
            f"({total} total)",
            extra={"service_task": "idempotency_cleanup"},
        )
    else:
        logger.debug("Idempotency cleanup: nothing to delete")

    return {"expired": expired_count, "stuck": stuck_count, "total": total}
