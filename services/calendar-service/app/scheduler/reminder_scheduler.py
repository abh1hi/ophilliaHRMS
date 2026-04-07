"""
Event Reminder Scheduler — publishes calendar.event_reminder and calendar.task_due_soon
to RabbitMQ so the notification-service can send emails/push notifications.

Reminder logic:
  • For each CalendarEvent with reminder_minutes=[15, 60, 1440, ...]:
      compute fire_at = start_time - N minutes
      if now is within (fire_at, fire_at + RUN_INTERVAL_SECONDS) → publish
  • For each CalendarTask where:
      due_date is in [now, now + 24h] AND status not in (done, cancelled)
      → publish calendar.task_due_soon once per day (idempotency via Redis key)

Idempotency: for each (event_id, reminder_minutes) pair a Redis key
    cal:reminder:{event_id}:{minutes}
is set with TTL = reminder_minutes * 60 + RUN_INTERVAL_SECONDS * 2
so the same reminder is never double-sent even if the scheduler restarts.
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar_event import CalendarEvent
from app.models.task import CalendarTask

logger = logging.getLogger(__name__)

# Scheduler polls every 60 seconds — must match the check window below
RUN_INTERVAL_SECONDS = 60


async def run_reminder_scheduler(
    publisher,
    get_session,
    redis_client,
    interval: int = RUN_INTERVAL_SECONDS,
) -> None:
    """Long-running background coroutine.  Call via asyncio.create_task()."""
    logger.info("Reminder scheduler started")
    while True:
        try:
            await asyncio.sleep(interval)
            async with get_session() as db:
                await _process_event_reminders(db, publisher, redis_client)
                await _process_task_due_soon(db, publisher, redis_client)
                await db.commit()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Reminder scheduler error")


async def _process_event_reminders(
    db: AsyncSession,
    publisher,
    redis_client,
) -> None:
    """Fire reminders for events whose reminder window falls within the current tick."""
    now = datetime.now(timezone.utc)
    # Look-ahead: only fetch events starting within the next 24h
    horizon = now + timedelta(hours=24)

    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.start_time.between(now, horizon),
            CalendarEvent.is_deleted == False,
            CalendarEvent.status == "scheduled",
            CalendarEvent.reminder_minutes != None,
        )
    )
    events = result.scalars().all()

    for event in events:
        reminder_list = event.reminder_minutes or []
        for minutes in reminder_list:
            fire_at = event.start_time - timedelta(minutes=int(minutes))
            # Fire if fire_at is within [now - interval, now]
            lower = now - timedelta(seconds=RUN_INTERVAL_SECONDS)
            if lower <= fire_at <= now:
                await _fire_event_reminder(event, minutes, publisher, redis_client, now)


async def _fire_event_reminder(
    event: CalendarEvent,
    minutes: int,
    publisher,
    redis_client,
    now: datetime,
) -> None:
    idempotency_key = f"cal:reminder:{event.id}:{minutes}"
    already_sent = await redis_client.get(idempotency_key)
    if already_sent:
        return

    # Build attendee list for the payload
    attendees = [a.get("employee_id") for a in (event.attendees or []) if a.get("employee_id")]
    # Also include the event creator
    creator_id = str(event.created_by)
    if creator_id not in attendees:
        attendees.append(creator_id)

    payload = {
        "event_id": str(event.id),
        "company_id": str(event.company_id),
        "title": event.title,
        "start_time": event.start_time.isoformat(),
        "end_time": event.end_time.isoformat(),
        "location": event.location or "",
        "calendar_id": str(event.calendar_id),
        "minutes_before": minutes,
        "attendee_employee_ids": attendees,
    }

    await publisher.publish("calendar.event_reminder", payload)

    # TTL: reminder offset + a few extra minutes as buffer
    ttl = int(minutes * 60) + RUN_INTERVAL_SECONDS * 3
    await redis_client.setex(idempotency_key, ttl, "1")

    logger.info(
        f"Fired calendar.event_reminder for event {event.id} "
        f"({minutes}m before) to {len(attendees)} attendee(s)"
    )


async def _process_task_due_soon(
    db: AsyncSession,
    publisher,
    redis_client,
) -> None:
    """Publish calendar.task_due_soon for tasks due within 24 hours."""
    now = datetime.now(timezone.utc)
    tomorrow = now + timedelta(hours=24)

    result = await db.execute(
        select(CalendarTask).where(
            CalendarTask.due_date.between(now, tomorrow),
            CalendarTask.status.notin_(["done", "cancelled"]),
            CalendarTask.is_deleted == False,
        )
    )
    tasks = result.scalars().all()

    for task in tasks:
        idempotency_key = f"cal:task_due:{task.id}:{now.strftime('%Y-%m-%d')}"
        already_sent = await redis_client.get(idempotency_key)
        if already_sent:
            continue

        # Collect assignee IDs
        assignee_ids = [str(a.employee_id) for a in (task.assignees or [])]
        creator_id = str(task.created_by)
        if creator_id not in assignee_ids:
            assignee_ids.append(creator_id)

        hours_until = max(0, round((task.due_date - now).total_seconds() / 3600, 1))

        payload = {
            "task_id": str(task.id),
            "company_id": str(task.company_id),
            "title": task.title,
            "due_date": task.due_date.isoformat(),
            "priority": task.priority,
            "status": task.status,
            "hours_until_due": hours_until,
            "assignee_employee_ids": assignee_ids,
        }

        await publisher.publish("calendar.task_due_soon", payload)

        # TTL: 25 hours so the key expires after the next daily run
        await redis_client.setex(idempotency_key, 25 * 3600, "1")
        logger.info(f"Fired calendar.task_due_soon for task {task.id} ({hours_until}h remaining)")
