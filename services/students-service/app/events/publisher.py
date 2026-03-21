import asyncio
import uuid
import json
import logging
from typing import Any

import aio_pika
from aio_pika import DeliveryMode, Message
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "students_events"
MAX_RETRIES = 3


class EventPublisher:
    """Publishes domain events to RabbitMQ via a durable topic exchange with retry."""

    def __init__(self, rabbitmq_url: str) -> None:
        self._url = rabbitmq_url
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def connect(self) -> None:
        try:
            self._connection = await aio_pika.connect_robust(self._url)
            self._channel = await self._connection.channel()
            self._exchange = await self._channel.declare_exchange(
                EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
            )
            logger.info("EventPublisher connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            self._connection = None
            self._channel = None
            self._exchange = None

    async def _reconnect(self) -> bool:
        """Attempt to re-establish the RabbitMQ connection."""
        try:
            await self.connect()
            return self._exchange is not None
        except Exception:
            return False

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
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "service_source": "students-service",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "company_id": payload.get("company_id"),
            "payload": payload,
        }

        rk = routing_key or event_type.replace(".", "_")
        body = json.dumps(event).encode()

        for attempt in range(MAX_RETRIES):
            if self._exchange is None:
                await self._reconnect()
            if self._exchange is None:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                continue
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
                return
            except Exception as exc:
                logger.warning(f"Publish attempt {attempt + 1}/{MAX_RETRIES} failed for {event_type}: {exc}")
                self._exchange = None
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)

        logger.error(f"Failed to publish event {event_type} after {MAX_RETRIES} attempts")
