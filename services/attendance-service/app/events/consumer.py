"""RabbitMQ event consumer for the Attendance Service.

Subscribes to:
  - company.created → seed a default attendance policy (ENABLE_EVENT_DRIVEN_ONBOARDING)

Uses DLQ for failed messages and event_processing_log for idempotency.
Resilience: asyncio.Semaphore(5) + asyncio.wait_for(timeout=10s) per message.
"""
import asyncio
import json
import logging
from uuid import UUID

from sqlalchemy.future import select
from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    import aio_pika
    from aio_pika.abc import AbstractIncomingMessage
    HAS_AIOPIKA = True
except ImportError:
    HAS_AIOPIKA = False
    logger.warning("aio-pika not installed — attendance event consumer disabled")

EXCHANGE_NAME = "hrms_events"
QUEUE_NAME = "attendance_events_queue"
DLQ_EXCHANGE = "attendance_dlq_exchange"
DLQ_QUEUE = "attendance_dlq"
BINDING_KEYS = ["company.created"]
_HANDLER_TIMEOUT = 10
_semaphore = asyncio.Semaphore(5)


async def _is_processed(db, event_id: str) -> bool:
    result = await db.execute(
        text("SELECT 1 FROM event_processing_log WHERE event_id = :eid LIMIT 1"),
        {"eid": event_id},
    )
    return result.fetchone() is not None


async def _mark_processed(db, event_id: str, event_type: str) -> None:
    await db.execute(
        text("INSERT INTO event_processing_log (event_id, event_type) VALUES (:eid, :etype) ON CONFLICT DO NOTHING"),
        {"eid": event_id, "etype": event_type},
    )


async def _handle_company_created(db, company_id: UUID) -> None:
    """Seed a company-wide default attendance policy (manual, 8h/day)."""
    from app.models.attendance_policy import AttendancePolicy
    existing = await db.execute(
        select(AttendancePolicy).where(
            AttendancePolicy.company_id == company_id,
            AttendancePolicy.department_id.is_(None),
            AttendancePolicy.employee_id.is_(None),
        ).limit(1)
    )
    if existing.scalars().first():
        logger.info(f"Default attendance policy already exists for company {company_id} — skipping")
        return

    policy = AttendancePolicy(
        company_id=company_id,
        method="manual",
        work_hours_per_day=8.0,
        department_id=None,
        employee_id=None,
    )
    db.add(policy)
    logger.info(f"Seeded default attendance policy for company {company_id}")


async def _handle_message(message: "AbstractIncomingMessage") -> None:
    """Inner handler — feature flag gate + business logic."""
    event_id = "unknown"
    try:
        raw = json.loads(message.body.decode("utf-8"))
        event_id = raw.get("event_id", "unknown")
        event_type = raw.get("event_type", "unknown")
        payload = raw.get("payload", {})

        company_id_str = payload.get("company_id")
        if not company_id_str:
            logger.warning(f"Event {event_type} missing company_id — acking")
            await message.ack()
            return

        company_id = UUID(company_id_str)

        if not settings.ENABLE_EVENT_DRIVEN_ONBOARDING:
            logger.debug(f"ENABLE_EVENT_DRIVEN_ONBOARDING=False — acking {event_type} without processing")
            await message.ack()
            return

        async with AsyncSessionLocal() as db:
            if await _is_processed(db, event_id):
                logger.info(f"Event {event_id} already processed — skipping")
                await message.ack()
                return

            if event_type == "company.created":
                await _handle_company_created(db, company_id)
            else:
                logger.debug(f"Ignoring unhandled event: {event_type}")

            await _mark_processed(db, event_id, event_type)
            await db.commit()

        await message.ack()

    except (KeyError, ValueError) as parse_err:
        logger.error(f"Malformed message rejected to DLQ: {parse_err}", extra={"event_id": event_id})
        await message.reject(requeue=False)
    except Exception:
        logger.exception("Unexpected error — rejecting to DLQ", extra={"event_id": event_id})
        await message.reject(requeue=False)


async def _process_message(message: "AbstractIncomingMessage") -> None:
    """Outer dispatcher: enforces concurrency limit and per-message timeout."""
    async with _semaphore:
        async with message.process(ignore_processed=True):
            try:
                await asyncio.wait_for(_handle_message(message), timeout=_HANDLER_TIMEOUT)
            except asyncio.TimeoutError:
                logger.error("Attendance consumer handler timed out — rejecting to DLQ")
                await message.reject(requeue=False)


async def start_consumer() -> None:
    """Connect and start consuming attendance domain events."""
    if not HAS_AIOPIKA:
        logger.error("aio-pika not available — attendance consumer disabled")
        return
    try:
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        dlq_exchange = await channel.declare_exchange(DLQ_EXCHANGE, aio_pika.ExchangeType.DIRECT, durable=True)
        dlq_queue_obj = await channel.declare_queue(DLQ_QUEUE, durable=True)
        await dlq_queue_obj.bind(dlq_exchange, routing_key=DLQ_QUEUE)

        exchange = await channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True)
        queue = await channel.declare_queue(
            QUEUE_NAME, durable=True,
            arguments={"x-dead-letter-exchange": DLQ_EXCHANGE, "x-dead-letter-routing-key": DLQ_QUEUE},
        )
        for key in BINDING_KEYS:
            await queue.bind(exchange, routing_key=key)

        await queue.consume(_process_message)
        logger.info("Attendance consumer started — listening for company.created")
    except Exception as exc:
        logger.error(f"Failed to start attendance consumer: {exc}")
