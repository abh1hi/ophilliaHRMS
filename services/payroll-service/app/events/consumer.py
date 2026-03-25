"""RabbitMQ consumer — listens for employee.created events."""
import json
import logging
import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from app.core.config import settings
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def handle_employee_created(payload: dict) -> None:
    """When a new employee is created, log for salary assignment.
    Salary assignment requires HR action via API.
    """
    employee_id = payload.get("employee_id") or payload.get("user_id")
    company_id = payload.get("company_id")
    logger.info(
        f"Employee created event received — salary assignment pending HR action",
        extra={"service_task": "employee_created", "employee_id": employee_id, "company_id": company_id},
    )


async def process_message(message: AbstractIncomingMessage) -> None:
    async with message.process(ignore_processed=True):
        try:
            data = json.loads(message.body.decode())
            routing_key = message.routing_key or data.get("event_type", "")

            if routing_key == "employee.created":
                await handle_employee_created(data.get("payload", data))
            else:
                logger.debug(f"Ignoring unhandled event: {routing_key}")

            await message.ack()
        except Exception as exc:
            logger.error(f"Error processing message: {exc}", extra={"service_task": "consumer"})
            await message.reject(requeue=False)


async def start_consumer() -> None:
    """Connect to RabbitMQ and consume employee.created events."""
    try:
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        exchange = await channel.declare_exchange("hrms_events", aio_pika.ExchangeType.TOPIC, durable=True)

        # DLQ setup
        dlq_exchange = await channel.declare_exchange("payroll_dlq_exchange", aio_pika.ExchangeType.DIRECT, durable=True)
        dlq_queue = await channel.declare_queue("payroll_dlq", durable=True)
        await dlq_queue.bind(dlq_exchange, routing_key="payroll_dlq")

        queue = await channel.declare_queue(
            "payroll_queue", durable=True,
            arguments={"x-dead-letter-exchange": "payroll_dlq_exchange", "x-dead-letter-routing-key": "payroll_dlq"},
        )
        await queue.bind(exchange, routing_key="employee.created")

        await queue.consume(process_message)
        logger.info("Payroll consumer started — listening for employee.created")
    except Exception as exc:
        logger.error(f"Failed to start payroll consumer: {exc}")
