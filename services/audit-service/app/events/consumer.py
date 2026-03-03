"""RabbitMQ event consumer for the Audit Service.

Subscribes to ALL events on the hrms_events topic exchange via wildcard '#'.
Follows enterprise error-handling:
  - UniqueViolation → ack() (idempotent, already recorded)
  - All other errors → reject(requeue=False) → DLQ (never requeue indefinitely)

prefetch_count=50 prevents consumer overload.
"""
import json
import logging

logger = logging.getLogger(__name__)

try:
    import aio_pika
    from aio_pika.abc import AbstractIncomingMessage
    HAS_AIOPIKA = True
except ImportError:
    HAS_AIOPIKA = False
    logger.warning("aio-pika not installed — event consumer disabled")

try:
    from asyncpg.exceptions import UniqueViolationError
except ImportError:
    # Fallback: catch by message string if asyncpg not available at import time
    UniqueViolationError = Exception  # will be refined at runtime


class AuditEventConsumer:
    """Consumes all HRMS domain events and records them as audit logs."""

    EXCHANGE_NAME = "hrms_events"
    QUEUE_NAME = "audit_queue"
    DLQ_EXCHANGE_NAME = "audit_dlq_exchange"
    DLQ_QUEUE_NAME = "audit_dlq"
    PREFETCH_COUNT = 50

    def __init__(self, rabbitmq_url: str, audit_service_factory):
        """
        Args:
            rabbitmq_url: AMQP URL.
            audit_service_factory: Async callable that returns an AuditService instance
                                   with its own DB session (called per message).
        """
        self.rabbitmq_url = rabbitmq_url
        self.audit_service_factory = audit_service_factory
        self._connection = None
        self._channel = None

    async def connect(self) -> None:
        """Establish RabbitMQ connection, declare exchange/queues, begin consuming."""
        if not HAS_AIOPIKA:
            logger.error("aio-pika not available — cannot start audit consumer")
            return

        try:
            self._connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self._channel = await self._connection.channel()

            # Prefetch limit prevents consumer overload
            await self._channel.set_qos(prefetch_count=self.PREFETCH_COUNT)

            # Declare the dead-letter exchange and queue first
            dlq_exchange = await self._channel.declare_exchange(
                self.DLQ_EXCHANGE_NAME,
                aio_pika.ExchangeType.DIRECT,
                durable=True,
            )
            dlq_queue = await self._channel.declare_queue(
                self.DLQ_QUEUE_NAME, durable=True
            )
            await dlq_queue.bind(dlq_exchange, routing_key=self.DLQ_QUEUE_NAME)

            # Main events exchange
            exchange = await self._channel.declare_exchange(
                self.EXCHANGE_NAME,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )

            # Audit queue — durable, with DLQ routing on rejection
            queue = await self._channel.declare_queue(
                self.QUEUE_NAME,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": self.DLQ_EXCHANGE_NAME,
                    "x-dead-letter-routing-key": self.DLQ_QUEUE_NAME,
                },
            )

            # Subscribe to ALL events with wildcard routing key
            await queue.bind(exchange, routing_key="#")

            # Start consuming
            await queue.consume(self._on_message)

            logger.info(
                "Audit consumer started — listening to all HRMS events",
                extra={"service_task": "consumer_start"},
            )

        except Exception as exc:
            logger.error(
                f"Failed to start audit consumer: {exc}",
                extra={"service_task": "consumer_start"},
            )

    async def _on_message(self, message: "AbstractIncomingMessage") -> None:
        """Process a single incoming event message."""
        async with message.process(ignore_processed=True):
            event_id = "unknown"
            try:
                raw = json.loads(message.body.decode("utf-8"))
                event_id = raw.get("event_id", "unknown")
                event_type = raw.get("event_type", "unknown")

                service = await self.audit_service_factory()
                result = await service.record_event(raw)

                if result is None:
                    # Idempotent duplicate — ack and move on
                    logger.info(
                        "Duplicate event — acked without insert",
                        extra={"service_task": "consumer_process", "event_id": event_id},
                    )
                else:
                    logger.info(
                        "Event processed and recorded",
                        extra={
                            "service_task": "consumer_process",
                            "event_id": event_id,
                            "event_type": event_type,
                        },
                    )
                await message.ack()
                # Increment Prometheus counter if available
                _inc_counter("events_processed_total")

            except (ValueError, KeyError, json.JSONDecodeError) as parse_err:
                # Malformed message — reject to DLQ, never requeue
                logger.error(
                    f"Malformed message rejected to DLQ: {parse_err}",
                    extra={"service_task": "consumer_process", "event_id": event_id},
                )
                await message.reject(requeue=False)
                _inc_counter("events_failed_total")

            except Exception as exc:
                # Check for unique violation (idempotent case via DB constraint)
                exc_str = str(type(exc).__name__).lower()
                if "unique" in exc_str or "uniqueviolation" in exc_str:
                    logger.info(
                        "UniqueViolation in DB — acking as idempotent",
                        extra={"service_task": "consumer_process", "event_id": event_id},
                    )
                    await message.ack()
                    _inc_counter("events_duplicate_total")
                else:
                    # Unknown error — reject to DLQ, never requeue
                    logger.exception(
                        f"Unexpected error processing event — rejecting to DLQ",
                        extra={"service_task": "consumer_process", "event_id": event_id},
                    )
                    await message.reject(requeue=False)
                    _inc_counter("events_failed_total")

    async def close(self) -> None:
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("Audit consumer connection closed", extra={"service_task": "consumer_stop"})


def _inc_counter(name: str) -> None:
    """Increment a Prometheus counter if instrumentation is available."""
    try:
        from app.metrics import COUNTERS
        COUNTERS[name].inc()
    except Exception:
        pass  # Metrics are best-effort
