"""RabbitMQ consumer for calendar-service.

Subscribes to cross-service events:
  - leave.approved  → create CalendarEvent(event_type="leave") for the employee
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, date
from uuid import UUID

from aio_pika import connect_robust, IncomingMessage, ExchangeType
from sqlalchemy.future import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.calendar import Calendar
from app.models.calendar_event import CalendarEvent

logger = logging.getLogger(__name__)


async def _get_or_create_company_calendar(db, company_id: str) -> Calendar:
    """Return the shared company-wide calendar for system-injected events.

    Creates one if it doesn't exist yet (idempotent upsert).
    """
    sentinel_owner = UUID("00000000-0000-0000-0000-000000000001")  # system sentinel
    result = await db.execute(
        select(Calendar).where(
            Calendar.company_id == UUID(company_id),
            Calendar.calendar_type == "company",
            Calendar.is_deleted == False,
        )
    )
    cal = result.scalars().first()
    if not cal:
        cal = Calendar(
            company_id=UUID(company_id),
            name="Company Calendar",
            calendar_type="company",
            owner_id=sentinel_owner,
            is_default=False,
            is_public=True,
        )
        db.add(cal)
        await db.flush()  # populate cal.id before using it
    return cal


async def _handle_leave_approved(payload: dict) -> None:
    """Create a CalendarEvent with event_type='leave' for an approved leave request.

    Idempotent: checks for an existing event with the same leave_request_id in description
    to avoid duplicates on requeue.
    """
    company_id: str = payload.get("company_id", "")
    employee_id: str = payload.get("employee_id", "")
    leave_request_id: str = payload.get("leave_request_id", "")
    start_date_str: str = payload.get("start_date", "")
    end_date_str: str = payload.get("end_date", "")
    leave_type_name: str = payload.get("leave_type_name", "Leave")
    total_days: float = float(payload.get("total_days", 0))

    if not company_id or not employee_id or not start_date_str or not end_date_str:
        logger.warning("leave.approved payload missing required fields — skipping")
        return

    # Parse dates — leave uses date-only ISO strings (YYYY-MM-DD)
    try:
        start_d = date.fromisoformat(start_date_str)
        end_d = date.fromisoformat(end_date_str)
    except ValueError:
        logger.warning(f"Cannot parse leave dates: {start_date_str!r} / {end_date_str!r}")
        return

    # Convert to full-day datetime (UTC midnight)
    start_time = datetime(start_d.year, start_d.month, start_d.day, tzinfo=timezone.utc)
    # End is inclusive for leave; end_time = end_d + 1 day (exclusive) for calendar display
    from datetime import timedelta
    end_time = datetime(end_d.year, end_d.month, end_d.day, tzinfo=timezone.utc) + timedelta(days=1)

    idempotency_marker = f"leave:{leave_request_id}"
    title = f"{leave_type_name} — {total_days:.0f} day(s)"

    async with AsyncSessionLocal() as db:
        # Idempotency: skip if already created
        existing = await db.execute(
            select(CalendarEvent).where(
                CalendarEvent.company_id == UUID(company_id),
                CalendarEvent.event_type == "leave",
                CalendarEvent.description == idempotency_marker,
                CalendarEvent.is_deleted == False,
            )
        )
        if existing.scalars().first():
            logger.debug(f"Leave calendar event already exists for {leave_request_id} — skipping")
            return

        cal = await _get_or_create_company_calendar(db, company_id)

        event = CalendarEvent(
            company_id=UUID(company_id),
            calendar_id=cal.id,
            title=title,
            description=idempotency_marker,
            event_type="leave",
            start_time=start_time,
            end_time=end_time,
            all_day=True,
            timezone="UTC",
            status="scheduled",
            created_by=UUID(employee_id),
            attendees=[{"employee_id": employee_id}],
            reminder_minutes=[],
        )
        db.add(event)
        await db.commit()
        logger.info(
            f"Created leave CalendarEvent for employee {employee_id} "
            f"({start_date_str} → {end_date_str}) — request {leave_request_id}"
        )


async def process_message(message: IncomingMessage) -> None:
    async with message.process(ignore_processed=True):
        try:
            body = message.body.decode("utf-8")
            event_data = json.loads(body)
            routing_key = message.routing_key or event_data.get("event_type", "")
            payload = event_data.get("payload", event_data)

            logger.debug(f"calendar-service consumer received: {routing_key}")

            if routing_key == "leave.approved":
                await _handle_leave_approved(payload)
            else:
                logger.debug(f"Ignoring unhandled event: {routing_key}")

            await message.ack()
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON in calendar consumer — rejecting to DLQ")
            await message.reject(requeue=False)
        except Exception as exc:
            logger.error(f"calendar consumer error processing {message.routing_key}: {exc}")
            await message.reject(requeue=False)


async def start_calendar_consumer() -> None:
    """Connect to RabbitMQ and start consuming cross-service events."""
    try:
        connection = await connect_robust(settings.RABBITMQ_URL)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        exchange = await channel.declare_exchange("hrms_events", ExchangeType.TOPIC, durable=True)

        # DLQ for this consumer
        dlq_exchange = await channel.declare_exchange(
            "calendar_dlq_exchange", ExchangeType.DIRECT, durable=True
        )
        dlq_queue = await channel.declare_queue("calendar_consumer_dlq", durable=True)
        await dlq_queue.bind(dlq_exchange, routing_key="calendar_consumer_dlq")

        _dlx_args = {
            "x-dead-letter-exchange": "calendar_dlq_exchange",
            "x-dead-letter-routing-key": "calendar_consumer_dlq",
        }
        try:
            queue = await channel.declare_queue(
                "calendar_consumer_queue", durable=True, arguments=_dlx_args
            )
        except Exception:
            logger.warning(
                "calendar_consumer_queue exists with incompatible args — "
                "deleting stale queue and recreating"
            )
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=10)
            await channel.queue_delete("calendar_consumer_queue")
            exchange = await channel.declare_exchange(
                "hrms_events", ExchangeType.TOPIC, durable=True
            )
            queue = await channel.declare_queue(
                "calendar_consumer_queue", durable=True, arguments=_dlx_args
            )

        await queue.bind(exchange, routing_key="leave.approved")

        logger.info("Calendar consumer started — listening for leave.approved")
        await queue.consume(process_message)
    except Exception as exc:
        logger.error(f"Failed to start calendar RabbitMQ consumer: {exc}")
