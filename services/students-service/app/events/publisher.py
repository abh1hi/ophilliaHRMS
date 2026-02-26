import uuid
import json
import logging
from typing import Any

import aio_pika
from aio_pika import DeliveryMode, Message
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "students_events"


class EventPublisher:
    """Publishes domain events to RabbitMQ via a durable topic exchange."""

    def __init__(self, rabbitmq_url: str) -> None:
        self._url = rabbitmq_url
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._url)
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
        )
        logger.info("EventPublisher connected to RabbitMQ")

    async def close(self) -> None:
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info("EventPublisher disconnected from RabbitMQ")

    async def publish(
        self,
        event_type: str,
        payload: dict[str, Any],
        routing_key: str | None = None,
    ) -> None:
        if self._exchange is None:
            logger.error("EventPublisher not connected — cannot publish event")
            return

        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "service_source": "students-service",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }

        rk = routing_key or event_type.replace(".", "_")
        body = json.dumps(event).encode()

        try:
            await self._exchange.publish(
                Message(
                    body=body,
                    delivery_mode=DeliveryMode.PERSISTENT,
                    content_type="application/json",
                ),
                routing_key=rk,
            )
            logger.info(
                "Event published",
                extra={"event_type": event_type, "routing_key": rk},
            )
        except Exception as exc:
            logger.error(
                "Failed to publish event",
                extra={"event_type": event_type, "error": str(exc)},
            )
