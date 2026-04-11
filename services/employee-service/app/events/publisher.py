import asyncio
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Optional RabbitMQ dependency — graceful failure if broker unavailable
try:
    import aio_pika
    HAS_AIOPIKA = True
except ImportError:
    HAS_AIOPIKA = False
    logger.warning("aio-pika not installed. Event publishing will be disabled.")

MAX_RETRIES = 3


def _resolve_correlation_id(explicit: str | None) -> str:
    try:
        from app.middleware.request_id import correlation_id_var
        return explicit or correlation_id_var.get("") or str(uuid.uuid4())
    except Exception:
        return explicit or str(uuid.uuid4())


class EventPublisher:
    """Publishes domain events to RabbitMQ with retry logic.

    Follows the HRMS Event Standard format:
    {
        "event_id": "uuid",
        "event_type": "employee.created",
        "service_source": "employee-service",
        "timestamp": "ISO-8601",
        "payload": {}
    }

    If RabbitMQ is unavailable, retries with exponential backoff up to MAX_RETRIES times.
    """

    def __init__(self, rabbitmq_url: str, exchange_name: str = "hrms_events"):
        self.rabbitmq_url = rabbitmq_url
        self.exchange_name = exchange_name
        self._connection = None
        self._channel = None
        self._exchange = None

    async def connect(self) -> None:
        """Establish connection to RabbitMQ. Safe to call repeatedly."""
        if not HAS_AIOPIKA:
            return
        try:
            self._connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self._channel = await self._connection.channel()
            self._exchange = await self._channel.declare_exchange(
                self.exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
            )
            logger.info("Connected to RabbitMQ", extra={"service_task": "rabbitmq_connect"})
        except Exception as e:
            logger.error(
                f"Failed to connect to RabbitMQ: {e}",
                extra={"service_task": "rabbitmq_connect"},
            )
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

    async def publish(self, event_type: str, payload: dict, correlation_id: str | None = None) -> None:
        """Publish an event to RabbitMQ with retry on failure.

        Args:
            event_type: e.g. 'employee.created', 'employee.updated'
            payload: Event data to include.
            correlation_id: Propagated from X-Correlation-ID header; auto-read from ContextVar if omitted.
        """
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "event_version": "v1",
            "service_source": "employee-service",
            "correlation_id": _resolve_correlation_id(correlation_id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }

        if not HAS_AIOPIKA:
            logger.warning(
                f"RabbitMQ unavailable — event not published: {event_type}",
                extra={"service_task": "event_publish"},
            )
            return

        for attempt in range(MAX_RETRIES):
            if self._exchange is None:
                await self._reconnect()
            if self._exchange is None:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                continue
            try:
                message = aio_pika.Message(
                    body=json.dumps(event).encode(),
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                )
                await self._exchange.publish(message, routing_key=event_type)
                logger.info(
                    f"Event published: {event_type}",
                    extra={"service_task": "event_publish"},
                )
                return
            except Exception as e:
                logger.warning(f"Publish attempt {attempt + 1}/{MAX_RETRIES} failed for {event_type}: {e}")
                self._exchange = None
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)

        logger.error(f"Failed to publish event {event_type} after {MAX_RETRIES} attempts")

    async def close(self) -> None:
        """Close RabbitMQ connection."""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("RabbitMQ connection closed", extra={"service_task": "rabbitmq_close"})
