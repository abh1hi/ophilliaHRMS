"""Event publisher for payroll service — emits salary.processed and payroll.run events.

Features (Phase 9A Guards):
- Retry with exponential backoff (2^attempt seconds)
- Dead Letter Queue (DLQ) for failed events after max retries
- Persistent delivery mode (AMQP)
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from aio_pika import connect_robust, Message, DeliveryMode
from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
DLQ_EXCHANGE = "hrms_events_dlq"
DLQ_ROUTING_KEY = "dlq"


async def publish_event(event_type: str, payload: dict) -> None:
    """Publish a standardized HRMS event to RabbitMQ with retry.

    Event format matches cross-service standard:
    {event_id, event_type, event_version, timestamp, company_id, user_id,
     correlation_id, service_source, payload}
    """
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

    for attempt in range(MAX_RETRIES):
        try:
            connection = await connect_robust(settings.RABBITMQ_URL)
        except Exception as exc:
            logger.warning(f"RabbitMQ connection attempt {attempt + 1}/{MAX_RETRIES} failed: {exc}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(2 ** attempt)
            continue

        try:
            async with connection:
                channel = await connection.channel()
                exchange = await channel.declare_exchange("hrms_events", type="topic", durable=True)

                message = Message(
                    json.dumps(event).encode(), delivery_mode=DeliveryMode.PERSISTENT, content_type="application/json"
                )
                await exchange.publish(message, routing_key=event_type)
                logger.info(f"Published {event_type}", extra={"service_task": "event_publish", "event_id": event["event_id"]})
                return
        except Exception as exc:
            logger.warning(f"Publish attempt {attempt + 1}/{MAX_RETRIES} failed for {event_type}: {exc}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(2 ** attempt)

    # ── Guard: Dead Letter Queue ────────────────────────────────────────
    logger.error(
        f"Event publish failed after {MAX_RETRIES} retries; sending to DLQ",
        extra={"event_type": event_type, "event_id": event["event_id"]},
    )
    await _send_to_dlq(event)


async def _send_to_dlq(event: Dict[str, Any]) -> None:
    """Send failed event to Dead Letter Queue for manual intervention.

    DLQ persists events that failed all retries so they can be reprocessed later.

    Args:
        event: Event dict to send to DLQ
    """
    try:
        connection = await connect_robust(settings.RABBITMQ_URL)

        async with connection:
            channel = await connection.channel()
            dlq_exchange = await channel.declare_exchange(
                DLQ_EXCHANGE,
                type="direct",
                durable=True,
            )

            # Add metadata about the failure
            event_with_dlq_meta = {
                **event,
                "_dlq_sent_at": datetime.now(timezone.utc).isoformat(),
                "_dlq_reason": "Max retries exhausted",
                "_dlq_max_retries": MAX_RETRIES,
            }

            message = Message(
                json.dumps(event_with_dlq_meta).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
            )

            await dlq_exchange.publish(message, routing_key=DLQ_ROUTING_KEY)

            logger.info(
                f"Event sent to DLQ: {event['event_type']}",
                extra={
                    "event_id": event["event_id"],
                    "dlq_exchange": DLQ_EXCHANGE,
                },
            )

    except Exception as e:
        logger.exception(
            f"Failed to send event to DLQ: {str(e)}",
            extra={"event_id": event.get("event_id")},
        )
