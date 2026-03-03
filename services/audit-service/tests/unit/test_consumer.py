"""Unit tests for the RabbitMQ event consumer message handling."""
import json
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch, call


@pytest.fixture
def raw_valid_event():
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "employee.created",
        "service_source": "employee-service",
        "timestamp": "2026-03-03T10:00:00",
        "payload": {"employee_id": "abc"},
    }


def make_message(body: dict) -> MagicMock:
    msg = MagicMock()
    msg.body = json.dumps(body).encode()
    msg.ack = AsyncMock()
    msg.reject = AsyncMock()
    # Support async context manager
    msg.__aenter__ = AsyncMock(return_value=None)
    msg.__aexit__ = AsyncMock(return_value=None)
    return msg


@pytest.mark.asyncio
async def test_valid_message_is_acked(raw_valid_event):
    """A valid message that is successfully processed should be acked."""
    from app.events.consumer import AuditEventConsumer

    mock_service = AsyncMock()
    mock_service.record_event = AsyncMock(return_value=MagicMock())

    async def factory():
        return mock_service

    consumer = AuditEventConsumer("amqp://localhost", factory)
    msg = make_message(raw_valid_event)

    with patch("app.events.consumer.HAS_AIOPIKA", True):
        await consumer._on_message(msg)

    msg.ack.assert_called_once()
    msg.reject.assert_not_called()


@pytest.mark.asyncio
async def test_duplicate_message_is_acked(raw_valid_event):
    """A duplicate event (service returns None) should still be acked."""
    from app.events.consumer import AuditEventConsumer

    mock_service = AsyncMock()
    mock_service.record_event = AsyncMock(return_value=None)  # duplicate

    async def factory():
        return mock_service

    consumer = AuditEventConsumer("amqp://localhost", factory)
    msg = make_message(raw_valid_event)

    await consumer._on_message(msg)

    msg.ack.assert_called_once()
    msg.reject.assert_not_called()


@pytest.mark.asyncio
async def test_malformed_json_is_rejected():
    """A message with invalid JSON should be rejected to DLQ (requeue=False)."""
    from app.events.consumer import AuditEventConsumer

    async def factory():
        return AsyncMock()

    consumer = AuditEventConsumer("amqp://localhost", factory)

    msg = MagicMock()
    msg.body = b"{{NOT VALID JSON}}"
    msg.ack = AsyncMock()
    msg.reject = AsyncMock()
    msg.__aenter__ = AsyncMock(return_value=None)
    msg.__aexit__ = AsyncMock(return_value=None)

    await consumer._on_message(msg)

    msg.reject.assert_called_once_with(requeue=False)
    msg.ack.assert_not_called()


@pytest.mark.asyncio
async def test_unique_violation_is_acked(raw_valid_event):
    """UniqueViolation from DB should result in ack (idempotent case)."""
    from app.events.consumer import AuditEventConsumer

    mock_service = AsyncMock()
    mock_service.record_event = AsyncMock(side_effect=Exception("UniqueViolationError"))

    async def factory():
        return mock_service

    consumer = AuditEventConsumer("amqp://localhost", factory)
    msg = make_message(raw_valid_event)

    await consumer._on_message(msg)

    msg.ack.assert_called_once()
    msg.reject.assert_not_called()


@pytest.mark.asyncio
async def test_unknown_exception_is_rejected_to_dlq(raw_valid_event):
    """An unexpected exception should reject the message to DLQ (requeue=False)."""
    from app.events.consumer import AuditEventConsumer

    mock_service = AsyncMock()
    mock_service.record_event = AsyncMock(side_effect=RuntimeError("unexpected"))

    async def factory():
        return mock_service

    consumer = AuditEventConsumer("amqp://localhost", factory)
    msg = make_message(raw_valid_event)

    await consumer._on_message(msg)

    msg.reject.assert_called_once_with(requeue=False)
    msg.ack.assert_not_called()
