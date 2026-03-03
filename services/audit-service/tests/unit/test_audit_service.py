"""Unit tests for AuditService business logic."""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.audit_service import AuditService, sanitize_payload
from app.repositories.audit_log_repository import AuditLogRepository


# ── sanitize_payload ──────────────────────────────────────────────────────────

def test_sanitize_removes_top_level_sensitive_keys():
    payload = {"name": "Alice", "password": "secret123", "email": "a@b.com"}
    result = sanitize_payload(payload)
    assert result["password"] == "[REDACTED]"
    assert result["name"] == "Alice"
    assert result["email"] == "a@b.com"


def test_sanitize_nested_sensitive_keys():
    payload = {"employee": {"salary": 50000, "name": "Bob"}}
    result = sanitize_payload(payload)
    assert result["employee"]["salary"] == "[REDACTED]"
    assert result["employee"]["name"] == "Bob"


def test_sanitize_multiple_sensitive_keys():
    payload = {"token": "abc", "secret": "xyz", "bank_account": "123", "user": "ok"}
    result = sanitize_payload(payload)
    assert result["token"] == "[REDACTED]"
    assert result["secret"] == "[REDACTED]"
    assert result["bank_account"] == "[REDACTED]"
    assert result["user"] == "ok"


def test_sanitize_non_dict_payload():
    result = sanitize_payload("not a dict")
    assert result == {}


def test_sanitize_empty_payload():
    result = sanitize_payload({})
    assert result == {}


# ── AuditService.record_event ─────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_repo():
    repo = AsyncMock(spec=AuditLogRepository)
    return repo


@pytest.fixture
def audit_service(mock_db):
    svc = AuditService(mock_db)
    return svc


@pytest.mark.asyncio
async def test_record_event_success(audit_service):
    event_id = str(uuid.uuid4())
    raw_event = {
        "event_id": event_id,
        "event_type": "employee.created",
        "service_source": "employee-service",
        "company_id": str(uuid.uuid4()),
        "payload": {"employee_id": "123", "name": "Alice"},
        "timestamp": "2026-03-03T10:00:00",
    }

    mock_log = MagicMock()
    mock_log.id = uuid.uuid4()
    mock_log.event_id = uuid.UUID(event_id)
    mock_log.event_version = 1
    mock_log.event_type = "employee.created"
    mock_log.service_source = "employee-service"
    mock_log.company_id = uuid.uuid4()
    mock_log.user_id = None
    mock_log.correlation_id = None
    mock_log.ip_address = None
    mock_log.user_agent = None
    mock_log.http_method = None
    mock_log.endpoint = None
    mock_log.payload = {"employee_id": "123", "name": "Alice"}
    from datetime import datetime
    mock_log.timestamp = datetime(2026, 3, 3, 10, 0, 0)
    mock_log.created_at = datetime(2026, 3, 3, 10, 0, 0)

    with patch.object(AuditLogRepository, "exists", new=AsyncMock(return_value=False)), \
         patch.object(AuditLogRepository, "create", new=AsyncMock(return_value=mock_log)):
        result = await audit_service.record_event(raw_event)

    assert result is not None
    assert result.event_type == "employee.created"


@pytest.mark.asyncio
async def test_record_event_duplicate_returns_none(audit_service):
    """Duplicate event_id should return None without inserting."""
    event_id = str(uuid.uuid4())
    raw_event = {
        "event_id": event_id,
        "event_type": "employee.created",
        "service_source": "employee-service",
        "payload": {},
    }

    with patch.object(AuditLogRepository, "exists", new=AsyncMock(return_value=True)):
        result = await audit_service.record_event(raw_event)

    assert result is None


@pytest.mark.asyncio
async def test_record_event_missing_event_id_returns_none(audit_service):
    result = await audit_service.record_event({"event_type": "x", "payload": {}})
    assert result is None


@pytest.mark.asyncio
async def test_record_event_invalid_event_id_returns_none(audit_service):
    result = await audit_service.record_event({"event_id": "not-a-uuid", "payload": {}})
    assert result is None


@pytest.mark.asyncio
async def test_record_event_sanitizes_sensitive_payload(audit_service):
    """Sensitive keys in payload must be redacted before storage."""
    event_id = str(uuid.uuid4())
    raw_event = {
        "event_id": event_id,
        "event_type": "user.password_reset",
        "service_source": "auth-service",
        "payload": {"user_id": "123", "token": "super-secret-token"},
    }

    captured = {}

    async def fake_create(data):
        captured["payload"] = data["payload"]
        mock = MagicMock()
        mock.id = uuid.uuid4()
        mock.event_id = uuid.UUID(event_id)
        mock.event_version = 1
        mock.event_type = "user.password_reset"
        mock.service_source = "auth-service"
        mock.company_id = data["company_id"]
        mock.user_id = None
        mock.correlation_id = None
        mock.ip_address = None
        mock.user_agent = None
        mock.http_method = None
        mock.endpoint = None
        mock.payload = data["payload"]
        from datetime import datetime
        mock.timestamp = datetime.utcnow()
        mock.created_at = datetime.utcnow()
        return mock

    with patch.object(AuditLogRepository, "exists", new=AsyncMock(return_value=False)), \
         patch.object(AuditLogRepository, "create", new=AsyncMock(side_effect=fake_create)):
        await audit_service.record_event(raw_event)

    assert captured["payload"]["token"] == "[REDACTED]"
    assert captured["payload"]["user_id"] == "123"
