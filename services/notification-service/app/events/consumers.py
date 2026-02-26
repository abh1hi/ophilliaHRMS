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
    async with message.process():
        body = message.body.decode('utf-8')
        try:
            event_data = json.loads(body)
            routing_key = message.routing_key
            logger.info(f"Received event {routing_key}")
            
            async with AsyncSessionLocal() as db:
                if routing_key.startswith("leave."):
                    await handle_leave_event(db, routing_key, event_data["payload"])
                elif routing_key == "employee.created":
                    await handle_employee_created(db, event_data["payload"])
                else:
                    logger.warning(f"Unhandled routing key: {routing_key}")
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON from message body.")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

async def handle_leave_event(db: AsyncSession, routing_key: str, payload: dict):
    # Depending on status (requested, approved, rejected, cancelled) 
    # Determine subject and body. Notice we need `employee_id` to fetch their emails.
    employee_id = payload.get("employee_id")
    status = payload.get("status")
    leave_id = payload.get("leave_request_id")
    
    if not employee_id:
        return
        
    subject = f"Leave Request Update - {status}"
    body = f"Your leave request ({leave_id}) has been marked as {status}."
    
    if routing_key == "leave.requested":
        # HR/Managers get notified too (for this demo, we'll just notify employee to simulate system)
        subject = f"Leave Request Submitted"
        body = f"You have submitted a leave request ({leave_id}). Currently pending approval."

    log_obj = NotificationLogCreate(
        user_id=employee_id,
        type=NotificationType.EMAIL,
        subject=subject,
        message=body
    )
    
    await compile_and_send_notification(db, log_obj)


async def handle_employee_created(db: AsyncSession, payload: dict):
    user_id = payload.get("user_id")
    subject = "Welcome to Ophillia HRMS"
    body = "Your employee profile has been created."
    
    log_obj = NotificationLogCreate(
        user_id=user_id,
        type=NotificationType.EMAIL,
        subject=subject,
        message=body
    )
    await compile_and_send_notification(db, log_obj)


async def start_consumers():
    try:
        connection = await connect_robust(settings.RABBITMQ_URL)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        exchange = await channel.declare_exchange(
            "hrms_events", ExchangeType.TOPIC, durable=True
        )

        queue = await channel.declare_queue("notification_queue", durable=True)
        await queue.bind(exchange, routing_key="leave.*")
        await queue.bind(exchange, routing_key="employee.created")

        logger.info("Notification Service is now listening for events...")
        await queue.consume(process_event)
        
        # Keep connection open. (Since it's tied to FastAPI lifespan it runs until shutdown)
    except Exception as e:
        logger.error(f"Failed to start RabbitMQ consumers: {e}")
