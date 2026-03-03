"""Event publisher for payroll service — emits salary.processed and payroll.run events."""
import json
import logging
import uuid
from datetime import datetime, timezone

from aio_pika import connect_robust, Message, DeliveryMode
from app.core.config import settings

logger = logging.getLogger(__name__)


async def publish_event(event_type: str, payload: dict) -> None:
    """Publish a standardized HRMS event to RabbitMQ.

    Event format matches cross-service standard:
    {event_id, event_type, event_version, timestamp, company_id, user_id,
     correlation_id, service_source, payload}
    """
    try:
        connection = await connect_robust(settings.RABBITMQ_URL)
    except Exception as exc:
        logger.warning(f"RabbitMQ unavailable, skipping event: {exc}")
        return

    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange("hrms_events", type="topic", durable=True)

        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "event_version": 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_source": "payroll-service",
            "company_id": payload.get("company_id"),
            "user_id": payload.get("user_id"),
            "correlation_id": payload.get("correlation_id"),
            "payload": payload,
        }

        message = Message(
            json.dumps(event).encode(), delivery_mode=DeliveryMode.PERSISTENT, content_type="application/json"
        )
        await exchange.publish(message, routing_key=event_type)
        logger.info(f"Published {event_type}", extra={"service_task": "event_publish", "event_id": event["event_id"]})
