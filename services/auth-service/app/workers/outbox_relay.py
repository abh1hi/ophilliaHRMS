"""Transactional Outbox Relay Worker.

Polls `outbox_events` for PENDING rows and publishes them to RabbitMQ.
Marks rows PUBLISHED on success, increments retry_count and stores last_error on failure.
After 5 retries, marks the row FAILED permanently.

Runs as a background asyncio task in the auth-service lifespan.
Uses SELECT FOR UPDATE SKIP LOCKED for concurrent-safe polling.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.outbox import OutboxEvent

logger = logging.getLogger(__name__)

MAX_RETRIES = 5
POLL_INTERVAL_SECONDS = 2
BATCH_SIZE = 50


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def _publish_batch(publisher, db: AsyncSession) -> int:
    """Poll up to BATCH_SIZE PENDING rows and publish each. Returns count published."""
    result = await db.execute(
        select(OutboxEvent)
        .where(OutboxEvent.status == "PENDING")
        .order_by(OutboxEvent.created_at)
        .limit(BATCH_SIZE)
        .with_for_update(skip_locked=True)
    )
    rows = result.scalars().all()
    if not rows:
        return 0

    published = 0
    for row in rows:
        try:
            payload = json.loads(row.payload_json)
            await publisher.publish(row.event_type, payload)
            row.status = "PUBLISHED"
            row.published_at = naive_utcnow()
            published += 1
        except Exception as exc:
            row.retry_count += 1
            row.last_error = str(exc)[:500]
            if row.retry_count >= MAX_RETRIES:
                row.status = "FAILED"
                logger.error(
                    f"Outbox event {row.id} ({row.event_type}) permanently failed after {MAX_RETRIES} retries: {exc}",
                    extra={"service_task": "outbox_relay"},
                )
            else:
                logger.warning(
                    f"Outbox event {row.id} ({row.event_type}) publish attempt {row.retry_count} failed: {exc}",
                    extra={"service_task": "outbox_relay"},
                )

    await db.commit()
    return published


async def run_outbox_relay(publisher) -> None:
    """Main relay loop — runs indefinitely until cancelled."""
    logger.info("Outbox relay started", extra={"service_task": "outbox_relay"})
    while True:
        try:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            async with AsyncSessionLocal() as db:
                count = await _publish_batch(publisher, db)
                if count:
                    logger.info(f"Outbox relay: published {count} events", extra={"service_task": "outbox_relay"})
        except asyncio.CancelledError:
            logger.info("Outbox relay stopping", extra={"service_task": "outbox_relay"})
            break
        except Exception as exc:
            logger.exception(f"Outbox relay error: {exc}", extra={"service_task": "outbox_relay"})
            # Don't crash the loop — next iteration will retry
