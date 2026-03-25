"""RabbitMQ consumer — handles leave.*, employee.created, payroll.run, salary.processed events.

Includes DLQ setup, preference enforcement via service layer, and Jinja2 template rendering.
"""
import asyncio
import json
import logging
from aio_pika import connect_robust, IncomingMessage, ExchangeType
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.schemas.notification import NotificationLogCreate
from app.core.constants import NotificationType
from app.services.notification_service import compile_and_send_notification
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


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

        logger.info("Notification consumer started — listening for leave.*, employee.created, onboarding.*, payroll.run, salary.processed")
        await queue.consume(process_event)
    except Exception as exc:
        logger.error(f"Failed to start RabbitMQ consumers: {exc}")
