import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from aio_pika import connect_robust, Message, DeliveryMode
from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


async def get_rabbitmq_connection():
    try:
        connection = await connect_robust(settings.RABBITMQ_URL)
        return connection
    except Exception as e:
        logger.error(f"RabbitMQ connection failed: {e}")
        return None


async def publish_event(event_type: str, payload: dict):
    event_message = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "service_source": "leave-service",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "company_id": payload.get("company_id"),
        "payload": payload,
    }

    for attempt in range(MAX_RETRIES):
        connection = await get_rabbitmq_connection()
        if not connection:
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(2 ** attempt)
            continue

        try:
            async with connection:
                channel = await connection.channel()
                exchange = await channel.declare_exchange("hrms_events", type="topic", durable=True)

                message = Message(
                    json.dumps(event_message).encode("utf-8"),
                    delivery_mode=DeliveryMode.PERSISTENT,
                    content_type="application/json",
                )
                await exchange.publish(message, routing_key=event_type)
                logger.info(f"Published event {event_type} with ID {event_message['event_id']}")
                return
        except Exception as e:
            logger.warning(f"Publish attempt {attempt + 1}/{MAX_RETRIES} failed for {event_type}: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(2 ** attempt)

    logger.error(f"Failed to publish event {event_type} after {MAX_RETRIES} attempts")
