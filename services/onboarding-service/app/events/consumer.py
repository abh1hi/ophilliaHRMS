"""RabbitMQ event consumer for the Onboarding Service.

Subscribes to events relevant to onboarding progression:
  - company.created        → Initialize onboarding state for new company
  - departments.seeded     → Mark departments step completed
  - leave_types.seeded     → Mark leave_types step completed
  - salary_structure.seeded → Mark salary_structure step completed
  - attendance_policy.seeded → Mark attendance_policy step completed
  - employee.created       → Mark first_employee step completed

Uses DLQ for failed messages — never requeue indefinitely.
"""
import json
import logging
from uuid import UUID

logger = logging.getLogger(__name__)

try:
    import aio_pika
    from aio_pika.abc import AbstractIncomingMessage
    HAS_AIOPIKA = True
except ImportError:
    HAS_AIOPIKA = False
    logger.warning("aio-pika not installed — event consumer disabled")


# Map event types to onboarding step keys
EVENT_TO_STEP = {
    "departments.seeded": "departments",
    "leave_types.seeded": "leave_types",
    "salary_structure.seeded": "salary_structure",
    "attendance_policy.seeded": "attendance_policy",
    "employee.created": "first_employee",
}


class OnboardingEventConsumer:
    """Consumes HRMS domain events and updates onboarding state."""

    EXCHANGE_NAME = "hrms_events"
    QUEUE_NAME = "onboarding_queue"
    DLQ_EXCHANGE_NAME = "onboarding_dlq_exchange"
    DLQ_QUEUE_NAME = "onboarding_dlq"
    PREFETCH_COUNT = 20

    BINDING_KEYS = [
        "company.created",
        "departments.seeded",
        "leave_types.seeded",
        "salary_structure.seeded",
        "attendance_policy.seeded",
        "employee.created",
    ]

    def __init__(self, rabbitmq_url: str, service_factory):
        """
        Args:
            rabbitmq_url: AMQP connection URL.
            service_factory: Async callable returning an OnboardingService with its own DB session.
        """
        self.rabbitmq_url = rabbitmq_url
        self.service_factory = service_factory
        self._connection = None
        self._channel = None

    async def connect(self) -> None:
        if not HAS_AIOPIKA:
            logger.error("aio-pika not available — cannot start onboarding consumer")
            return

        try:
            self._connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=self.PREFETCH_COUNT)

            # Dead-letter exchange and queue
            dlq_exchange = await self._channel.declare_exchange(
                self.DLQ_EXCHANGE_NAME, aio_pika.ExchangeType.DIRECT, durable=True,
            )
            dlq_queue = await self._channel.declare_queue(self.DLQ_QUEUE_NAME, durable=True)
            await dlq_queue.bind(dlq_exchange, routing_key=self.DLQ_QUEUE_NAME)

            # Main exchange
            exchange = await self._channel.declare_exchange(
                self.EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True,
            )

            # Onboarding queue with DLQ routing
            queue = await self._channel.declare_queue(
                self.QUEUE_NAME,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": self.DLQ_EXCHANGE_NAME,
                    "x-dead-letter-routing-key": self.DLQ_QUEUE_NAME,
                },
            )

            # Bind only to relevant event types
            for key in self.BINDING_KEYS:
                await queue.bind(exchange, routing_key=key)

            await queue.consume(self._on_message)

            logger.info(
                "Onboarding consumer started — listening for onboarding events",
                extra={"service_task": "consumer_start"},
            )
        except Exception as exc:
            logger.error(f"Failed to start onboarding consumer: {exc}", extra={"service_task": "consumer_start"})

    async def _on_message(self, message: "AbstractIncomingMessage") -> None:
        async with message.process(ignore_processed=True):
            event_id = "unknown"
            try:
                raw = json.loads(message.body.decode("utf-8"))
                event_id = raw.get("event_id", "unknown")
                event_type = raw.get("event_type", "unknown")
                correlation_id = raw.get("correlation_id", event_id)
                payload = raw.get("payload", {})

                company_id_str = payload.get("company_id")
                if not company_id_str:
                    logger.warning(
                        f"Event {event_type} missing company_id — skipping",
                        extra={"service_task": "consumer_process", "event_id": event_id},
                    )
                    await message.ack()
                    return

                company_id = UUID(company_id_str)
                service = await self.service_factory()

                if event_type == "company.created":
                    await service.get_or_create_status(company_id)
                    logger.info(
                        "Onboarding initialized for new company",
                        extra={"service_task": "consumer_process", "event_id": event_id, "company_id": company_id_str},
                    )
                elif event_type in EVENT_TO_STEP:
                    step_key = EVENT_TO_STEP[event_type]
                    await service.complete_step(company_id, step_key, skipped=False)
                    logger.info(
                        f"Step '{step_key}' auto-completed via event",
                        extra={"service_task": "consumer_process", "event_id": event_id, "company_id": company_id_str, "step_key": step_key},
                    )
                else:
                    logger.debug(f"Ignoring unhandled event type: {event_type}", extra={"event_id": event_id})

                await message.ack()

            except (ValueError, KeyError, json.JSONDecodeError) as parse_err:
                logger.error(
                    f"Malformed message rejected to DLQ: {parse_err}",
                    extra={"service_task": "consumer_process", "event_id": event_id},
                )
                await message.reject(requeue=False)

            except Exception as exc:
                exc_name = type(exc).__name__.lower()
                if "unique" in exc_name:
                    logger.info(
                        "UniqueViolation — acking as idempotent",
                        extra={"service_task": "consumer_process", "event_id": event_id},
                    )
                    await message.ack()
                else:
                    logger.exception(
                        "Unexpected error processing event — rejecting to DLQ",
                        extra={"service_task": "consumer_process", "event_id": event_id},
                    )
                    await message.reject(requeue=False)

    async def close(self) -> None:
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("Onboarding consumer connection closed", extra={"service_task": "consumer_stop"})
