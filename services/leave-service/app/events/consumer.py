"""RabbitMQ event consumer for the Leave Service.

Subscribes to:
  - company.created  → seed default leave policy for new company (ENABLE_EVENT_DRIVEN_ONBOARDING)
  - employee.created → log employee creation (no-op unless feature flag is on)

Uses DLQ for failed messages and event_processing_log for idempotency.
Resilience: asyncio.Semaphore(5) + asyncio.wait_for(timeout=10s) per message.
"""
import asyncio
import json
import logging
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.future import select
from sqlalchemy import delete

from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

try:
    import aio_pika
    from aio_pika.abc import AbstractIncomingMessage
    HAS_AIOPIKA = True
except ImportError:
    HAS_AIOPIKA = False
    logger.warning("aio-pika not installed — leave event consumer disabled")

EXCHANGE_NAME = "hrms_events"
QUEUE_NAME = "leave_queue"
DLQ_EXCHANGE = "leave_dlq_exchange"
DLQ_QUEUE = "leave_dlq"
BINDING_KEYS = ["company.created", "employee.created"]
_HANDLER_TIMEOUT = 10
_semaphore = asyncio.Semaphore(5)

DEFAULT_LEAVE_TYPES = [
    {"name": "Casual Leave", "days_allowed": 12},
    {"name": "Sick Leave", "days_allowed": 10},
    {"name": "Earned Leave", "days_allowed": 15},
]


class EventProcessingLog:
    """Lightweight in-process model reference — avoids circular imports."""
    __tablename__ = "event_processing_log"


async def _is_processed(db, event_id: str) -> bool:
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT 1 FROM event_processing_log WHERE event_id = :eid LIMIT 1"),
        {"eid": event_id},
    )
    return result.fetchone() is not None


async def _mark_processed(db, event_id: str, event_type: str) -> None:
    from sqlalchemy import text
    await db.execute(
        text("INSERT INTO event_processing_log (event_id, event_type) VALUES (:eid, :etype) ON CONFLICT DO NOTHING"),
        {"eid": event_id, "etype": event_type},
    )


async def _handle_company_created(db, company_id: UUID) -> None:
    """Seed default leave types for a new company if none exist yet."""
    from app.models.leave import LeaveType
    existing = await db.execute(
        select(LeaveType).where(LeaveType.company_id == company_id).limit(1)
    )
    if existing.scalars().first():
        logger.info(f"Leave types already exist for company {company_id} — skipping seed")
        return

    for lt_def in DEFAULT_LEAVE_TYPES:
        lt = LeaveType(
            company_id=company_id,
            name=lt_def["name"],
            days_allowed=lt_def["days_allowed"],
            requires_approval=1,
            is_active=1,
        )
        db.add(lt)
    logger.info(f"Seeded {len(DEFAULT_LEAVE_TYPES)} default leave types for company {company_id}")


def _handle_employee_created(company_id: UUID, employee_id: str) -> None:
    """Log employee creation — leave balance initialization is handled by HR via API."""
    logger.info(
        f"Employee {employee_id} created in company {company_id} — leave balance initialization pending HR action",
        extra={"service_task": "employee_created"},
    )


async def _handle_message(message: "AbstractIncomingMessage") -> None:
    """Inner message handler — called with timeout protection by _process_message."""
    event_id = "unknown"
    try:
        raw = json.loads(message.body.decode("utf-8"))
        event_id = raw.get("event_id", "unknown")
        event_type = raw.get("event_type", "unknown")
        payload = raw.get("payload", {})

        company_id_str = payload.get("company_id")
        if not company_id_str:
            logger.warning(f"Event {event_type} missing company_id — acking without processing")
            await message.ack()
            return

        company_id = UUID(company_id_str)

        from app.core.config import settings as _s
        async with AsyncSessionLocal() as db:
            # Idempotency check
            if await _is_processed(db, event_id):
                logger.info(f"Event {event_id} already processed — skipping")
                await message.ack()
                return

            if event_type == "company.created" and _s.ENABLE_EVENT_DRIVEN_ONBOARDING:
                await _handle_company_created(db, company_id)
            elif event_type == "employee.created" and _s.ENABLE_EVENT_DRIVEN_ONBOARDING:
                employee_id = payload.get("employee_id") or payload.get("user_id", "unknown")
                _handle_employee_created(company_id, employee_id)
            else:
                logger.debug(f"Ignoring event {event_type} (flag off or unhandled)")
                await message.ack()
                return

            await _mark_processed(db, event_id, event_type)
            await db.commit()

        await message.ack()

    except (KeyError, ValueError) as parse_err:
        logger.error(f"Malformed message rejected to DLQ: {parse_err}", extra={"event_id": event_id})
        await message.reject(requeue=False)

    except Exception:
        logger.exception("Unexpected error processing event — rejecting to DLQ", extra={"event_id": event_id})
        await message.reject(requeue=False)


async def _process_message(message: "AbstractIncomingMessage") -> None:
    """Outer dispatcher: enforces concurrency limit and per-message timeout."""
    async with _semaphore:
        async with message.process(ignore_processed=True):
            try:
                await asyncio.wait_for(_handle_message(message), timeout=_HANDLER_TIMEOUT)
            except asyncio.TimeoutError:
                logger.error("Leave consumer handler timed out — rejecting to DLQ")
                await message.reject(requeue=False)


async def start_consumer() -> None:
    """Connect to RabbitMQ and start consuming leave domain events."""
    if not HAS_AIOPIKA:
        logger.error("aio-pika not available — leave consumer disabled")
        return
    try:
        connection = await aio_pika.connect_robust(
            __import__("app.core.config", fromlist=["settings"]).settings.RABBITMQ_URL
        )
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        dlq_exchange = await channel.declare_exchange(DLQ_EXCHANGE, aio_pika.ExchangeType.DIRECT, durable=True)
        dlq_queue = await channel.declare_queue(DLQ_QUEUE, durable=True)
        await dlq_queue.bind(dlq_exchange, routing_key=DLQ_QUEUE)

        exchange = await channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True)
        queue = await channel.declare_queue(
            QUEUE_NAME, durable=True,
            arguments={"x-dead-letter-exchange": DLQ_EXCHANGE, "x-dead-letter-routing-key": DLQ_QUEUE},
        )
        for key in BINDING_KEYS:
            await queue.bind(exchange, routing_key=key)

        await queue.consume(_process_message)
        logger.info("Leave consumer started — listening for company.created, employee.created")
    except Exception as exc:
        logger.error(f"Failed to start leave consumer: {exc}")
