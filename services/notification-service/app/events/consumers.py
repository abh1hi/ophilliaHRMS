"""RabbitMQ consumer — handles leave.*, employee.created, payroll.run, salary.processed,
and calendar.* events.

Includes DLQ setup, preference enforcement via service layer, and Jinja2 template rendering.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from aio_pika import connect_robust, IncomingMessage, ExchangeType
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.schemas.notification import NotificationLogCreate
from app.core.constants import NotificationType
from app.services.notification_service import compile_and_send_notification
from app.utils.employee_resolver import get_employee_email, get_employee_emails_bulk
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Redis client shared via module-level reference — set by main.py on startup
_redis = None

def set_consumer_redis(client) -> None:
    global _redis
    _redis = client


async def process_event(message: IncomingMessage):
    async with message.process(ignore_processed=True):
        try:
            body = message.body.decode("utf-8")
            event_data = json.loads(body)
            routing_key = message.routing_key or event_data.get("event_type", "")
            payload = event_data.get("payload", event_data)

            logger.info(f"Received event {routing_key}")

            async with AsyncSessionLocal() as db:
                if routing_key.startswith("leave."):
                    await handle_leave_event(db, routing_key, payload)
                elif routing_key == "employee.created":
                    await handle_employee_created(db, payload)
                elif routing_key.startswith("onboarding."):
                    await handle_onboarding_event(db, routing_key, payload)
                elif routing_key == "payroll.run":
                    await handle_payroll_run(db, payload)
                elif routing_key == "salary.processed":
                    await handle_salary_processed(db, payload)
                elif routing_key == "calendar.event_reminder":
                    await handle_calendar_event_reminder(db, payload)
                elif routing_key == "calendar.event_invited":
                    await handle_calendar_event_invited(db, payload)
                elif routing_key == "calendar.task_due_soon":
                    await handle_calendar_task_due_soon(db, payload)
                else:
                    logger.debug(f"Ignoring unhandled event: {routing_key}")

            await message.ack()
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON — rejecting to DLQ")
            await message.reject(requeue=False)
        except Exception as exc:
            logger.error(f"Error processing message: {exc}")
            await message.reject(requeue=False)


async def handle_leave_event(db: AsyncSession, routing_key: str, payload: dict):
    employee_id = payload.get("employee_id")
    status = payload.get("status", "")
    leave_id = payload.get("leave_request_id", "")
    company_id = payload.get("company_id")

    if not employee_id or not company_id:
        logger.warning(f"Missing employee_id or company_id in leave event")
        return

    subject = f"Leave Request {status}"
    body = f"Your leave request ({leave_id}) has been marked as {status}."

    if routing_key == "leave.requested":
        subject = "Leave Request Submitted"
        body = f"You have submitted a leave request ({leave_id}). Currently pending approval."

    log_obj = NotificationLogCreate(company_id=company_id, user_id=employee_id, type=NotificationType.EMAIL, subject=subject, message=body)
    await compile_and_send_notification(db, log_obj, template_name="leave_update.html", template_context={"status": status, "leave_request_id": leave_id})


async def handle_employee_created(db: AsyncSession, payload: dict):
    user_id = payload.get("user_id") or payload.get("employee_id")
    company_id = payload.get("company_id")

    if not user_id or not company_id:
        logger.warning("Missing user_id or company_id in employee.created")
        return

    log_obj = NotificationLogCreate(company_id=company_id, user_id=user_id, type=NotificationType.EMAIL, subject="Welcome to Ophillia HRMS", message="Your employee profile has been created.")
    await compile_and_send_notification(db, log_obj, template_name="employee_created.html", template_context={})


async def handle_onboarding_event(db: AsyncSession, routing_key: str, payload: dict):
    """Handle onboarding lifecycle emails: welcome, reminder (future), completion."""
    company_id = payload.get("company_id")
    user_id = payload.get("user_id")

    if not company_id:
        return

    if routing_key == "onboarding.wizard_completed":
        if user_id:
            log_obj = NotificationLogCreate(
                company_id=company_id, user_id=user_id,
                type=NotificationType.EMAIL,
                subject="Onboarding Complete - Welcome to Ophillia HRMS!",
                message="Congratulations! Your organization's onboarding wizard is complete. Your HRMS is now fully configured.",
            )
            await compile_and_send_notification(db, log_obj, template_name="onboarding_complete.html", template_context={"progress": 100})
        logger.info(f"Onboarding completion email sent", extra={"service_task": "onboarding_email", "company_id": company_id})

    elif routing_key == "onboarding.step_completed":
        step_key = payload.get("step_key", "")
        progress = payload.get("progress_percent", 0)
        logger.info(
            f"Onboarding step '{step_key}' completed ({progress}%)",
            extra={"service_task": "onboarding_analytics", "company_id": company_id, "step_key": step_key},
        )

    elif routing_key == "onboarding.step_skipped":
        step_key = payload.get("step_key", "")
        logger.info(
            f"Onboarding step '{step_key}' skipped",
            extra={"service_task": "onboarding_analytics", "company_id": company_id, "step_key": step_key},
        )


async def handle_payroll_run(db: AsyncSession, payload: dict):
    company_id = payload.get("company_id")
    period_start = payload.get("period_start", "")
    period_end = payload.get("period_end", "")

    if not company_id:
        return

    # This would ideally notify all employees — for now logs the event
    logger.info(f"Payroll run event: {period_start} to {period_end} for company {company_id}")


async def handle_salary_processed(db: AsyncSession, payload: dict):
    employee_id = payload.get("employee_id")
    company_id = payload.get("company_id")
    period_start = payload.get("period_start", "")
    period_end = payload.get("period_end", "")

    if not employee_id or not company_id:
        return

    log_obj = NotificationLogCreate(company_id=company_id, user_id=employee_id, type=NotificationType.EMAIL, subject="Your Payslip is Ready", message=f"Payroll for {period_start} to {period_end} has been processed.")
    await compile_and_send_notification(db, log_obj, template_name="payroll_processed.html", template_context={"period_start": period_start, "period_end": period_end})


def _fmt_dt(iso: str) -> str:
    """Format an ISO datetime string for human-readable email display."""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%A, %B %-d %Y at %-I:%M %p UTC")
    except Exception:
        return iso


async def handle_calendar_event_reminder(db: AsyncSession, payload: dict):
    """Send event reminder emails to all attendees + the organizer."""
    company_id = payload.get("company_id")
    employee_ids: list = payload.get("attendee_employee_ids", [])
    if not employee_ids or not company_id:
        return

    start_formatted = _fmt_dt(payload.get("start_time", ""))
    end_formatted   = _fmt_dt(payload.get("end_time", ""))
    app_url = f"{settings.ALLOWED_ORIGINS[0] if settings.ALLOWED_ORIGINS else 'http://localhost:3000'}?tab=workspace-calendar"
    minutes_before  = payload.get("minutes_before", "")

    email_map = await get_employee_emails_bulk(employee_ids, _redis)

    for emp_id, to_email in email_map.items():
        log_obj = NotificationLogCreate(
            company_id=company_id,
            user_id=emp_id,
            type=NotificationType.EMAIL,
            subject=f"Reminder: {payload.get('title', 'Event')} starts in {minutes_before}m",
            message=f"Your event '{payload.get('title')}' starts at {start_formatted}.",
        )
        await compile_and_send_notification(
            db, log_obj,
            template_name="calendar_event_reminder.html",
            template_context={
                "title": payload.get("title", ""),
                "start_formatted": start_formatted,
                "end_formatted": end_formatted,
                "location": payload.get("location", ""),
                "minutes_before": minutes_before,
                "app_url": app_url,
            },
        )


async def handle_calendar_event_invited(db: AsyncSession, payload: dict):
    """Send calendar invitation emails to all invited attendees."""
    company_id = payload.get("company_id")
    employee_ids: list = payload.get("attendee_employee_ids", [])
    if not employee_ids or not company_id:
        return

    start_formatted = _fmt_dt(payload.get("start_time", ""))
    app_url = f"{settings.ALLOWED_ORIGINS[0] if settings.ALLOWED_ORIGINS else 'http://localhost:3000'}?tab=workspace-calendar"
    organizer_id = payload.get("organizer_employee_id", "")

    # Resolve organizer display name (best-effort — use ID if unavailable)
    organizer_email = await get_employee_email(organizer_id, _redis) if organizer_id else ""
    organizer_name = organizer_email.split("@")[0] if "@" in organizer_email else organizer_id

    email_map = await get_employee_emails_bulk(employee_ids, _redis)

    for emp_id, to_email in email_map.items():
        # Don't invite the organizer
        if emp_id == organizer_id:
            continue
        log_obj = NotificationLogCreate(
            company_id=company_id,
            user_id=emp_id,
            type=NotificationType.EMAIL,
            subject=f"Invitation: {payload.get('title', 'Event')}",
            message=f"You have been invited to '{payload.get('title')}' on {start_formatted}.",
        )
        await compile_and_send_notification(
            db, log_obj,
            template_name="calendar_event_invited.html",
            template_context={
                "title": payload.get("title", ""),
                "start_formatted": start_formatted,
                "location": payload.get("location", ""),
                "organizer_name": organizer_name,
                "event_id": payload.get("event_id", ""),
                "app_url": app_url,
            },
        )


async def handle_calendar_task_due_soon(db: AsyncSession, payload: dict):
    """Send task due-soon emails to all assignees."""
    company_id = payload.get("company_id")
    employee_ids: list = payload.get("assignee_employee_ids", [])
    if not employee_ids or not company_id:
        return

    due_formatted = _fmt_dt(payload.get("due_date", ""))
    hours_until   = payload.get("hours_until_due", 0)
    priority      = payload.get("priority", "medium")
    app_url = f"{settings.ALLOWED_ORIGINS[0] if settings.ALLOWED_ORIGINS else 'http://localhost:3000'}?tab=workspace-board"

    email_map = await get_employee_emails_bulk(employee_ids, _redis)

    for emp_id, to_email in email_map.items():
        log_obj = NotificationLogCreate(
            company_id=company_id,
            user_id=emp_id,
            type=NotificationType.EMAIL,
            subject=f"Task Due Soon: {payload.get('title', 'Task')} ({hours_until}h remaining)",
            message=f"Task '{payload.get('title')}' is due at {due_formatted}.",
        )
        await compile_and_send_notification(
            db, log_obj,
            template_name="calendar_task_due_soon.html",
            template_context={
                "title": payload.get("title", ""),
                "due_formatted": due_formatted,
                "hours_until_due": hours_until,
                "priority": priority,
                "status": payload.get("status", ""),
                "app_url": app_url,
            },
        )


async def start_consumers():
    try:
        connection = await connect_robust(settings.RABBITMQ_URL)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=20)

        exchange = await channel.declare_exchange("hrms_events", ExchangeType.TOPIC, durable=True)

        # DLQ setup
        dlq_exchange = await channel.declare_exchange("notification_dlq_exchange", ExchangeType.DIRECT, durable=True)
        dlq_queue = await channel.declare_queue("notification_dlq", durable=True)
        await dlq_queue.bind(dlq_exchange, routing_key="notification_dlq")

        # Declare main queue with DLX args.
        # If notification_queue already exists without DLX args (arg mismatch), RabbitMQ closes
        # the channel with precondition_failed. We catch that, open a fresh channel, delete the
        # stale queue, and redeclare with the correct configuration.
        _dlx_args = {
            "x-dead-letter-exchange": "notification_dlq_exchange",
            "x-dead-letter-routing-key": "notification_dlq",
        }
        try:
            queue = await channel.declare_queue("notification_queue", durable=True, arguments=_dlx_args)
        except Exception:
            logger.warning(
                "notification_queue exists with incompatible args (missing DLX) — "
                "deleting stale queue and recreating with DLX configuration"
            )
            # Channel is closed by RabbitMQ after a precondition_failed exception.
            # Open a fresh channel to delete and redeclare the queue.
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=20)
            await channel.queue_delete("notification_queue")
            # Re-obtain exchange reference on the new channel (durable, so broker still has it).
            exchange = await channel.declare_exchange("hrms_events", ExchangeType.TOPIC, durable=True)
            queue = await channel.declare_queue("notification_queue", durable=True, arguments=_dlx_args)

        # Bind to all relevant events
        await queue.bind(exchange, routing_key="leave.*")
        await queue.bind(exchange, routing_key="employee.created")
        await queue.bind(exchange, routing_key="onboarding.*")
        await queue.bind(exchange, routing_key="payroll.run")
        await queue.bind(exchange, routing_key="salary.processed")
        await queue.bind(exchange, routing_key="calendar.event_reminder")
        await queue.bind(exchange, routing_key="calendar.event_invited")
        await queue.bind(exchange, routing_key="calendar.task_due_soon")

        logger.info(
            "Notification consumer started — listening for "
            "leave.*, employee.created, onboarding.*, payroll.run, salary.processed, calendar.*"
        )
        await queue.consume(process_event)
    except Exception as exc:
        logger.error(f"Failed to start RabbitMQ consumers: {exc}")
