import json
import logging
import uuid
from datetime import datetime
from aio_pika import connect_robust, Message, DeliveryMode
from app.core.config import settings

logger = logging.getLogger(__name__)

async def get_rabbitmq_connection():
    try:
        connection = await connect_robust(settings.RABBITMQ_URL)
        return connection
    except Exception as e:
        logger.error(f"RabbitMQ connection failed: {e}")
        return None

async def publish_event(event_type: str, payload: dict):
    connection = await get_rabbitmq_connection()
    if not connection:
        logger.warning("RabbitMQ is down, skipping event publishing.")
        return

    async with connection:
        channel = await connection.channel()
        exchange_name = "hrms_events"
        
        # Declare exchange (fanout or topic depending on how other services listen)
        exchange = await channel.declare_exchange(exchange_name, type="topic", durable=True)
        
        event_message = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "service_source": "leave-service",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "payload": payload
        }
        
        message = Message(
            json.dumps(event_message).encode('utf-8'),
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type='application/json'
        )
        
        routing_key = event_type
        await exchange.publish(message, routing_key=routing_key)
        logger.info(f"Published event {event_type} with ID {event_message['event_id']}")
