"""Integration tests for audit log REST endpoints."""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.v1.dependencies import get_audit_service
from app.services.audit_service import AuditService
from app.schemas.audit_log import AuditLogResponse, AuditLogListResponse


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_log_response(**kwargs) -> AuditLogResponse:
    defaults = dict(
        id=uuid.uuid4(),
        event_id=uuid.uuid4(),
        event_version=1,
        event_type="employee.created",
        service_source="employee-service",
        company_id=uuid.uuid4(),
        user_id=None,
        correlation_id=None,
        ip_address=None,
        user_agent=None,
        http_method=None,
        endpoint=None,
        payload={"employee_id": "abc"},
        timestamp=datetime(2026, 3, 3, 10, 0, 0),
        created_at=datetime(2026, 3, 3, 10, 0, 0),
    )
    defaults.update(kwargs)
    return AuditLogResponse(**defaults)


MOCK_TOKEN_PAYLOAD_HR = {
    "sub": str(uuid.uuid4()),
    "role": "hr",
    "company_id": str(uuid.uuid4()),
}

MOCK_TOKEN_PAYLOAD_SUPER_ADMIN = {
    "sub": str(uuid.uuid4()),
    "role": "super_admin",
    "company_id": str(uuid.uuid4()),
}


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_list_audit_logs_unauthenticated():
    """Endpoint must require authentication (no token → 401)."""
    client = TestClient(app)
    response = client.get("/api/v1/audit/logs")
    assert response.status_code == 401


def test_list_audit_logs_authenticated_hr():
    """HR role can list logs and gets paginated response."""
    mock_svc = AsyncMock(spec=AuditService)
    mock_svc.query_logs = AsyncMock(
        return_value=AuditLogListResponse(
            items=[make_log_response()],
            total=1,
            skip=0,
            limit=50,
        )
    )

    with patch("app.core.security.get_current_user", return_value=MOCK_TOKEN_PAYLOAD_HR), \
         patch("app.core.security.require_roles", return_value=lambda r: MOCK_TOKEN_PAYLOAD_HR):
        app.dependency_overrides[get_audit_service] = lambda: mock_svc
        client = TestClient(app)
        response = client.get(
            "/api/v1/audit/logs",
            headers={"Authorization": "Bearer faketoken"},
        )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_get_audit_log_found():
    """GET /audit/logs/{id} — found returns 200."""
    mock_svc = AsyncMock(spec=AuditService)
    log = make_log_response()
    mock_svc.get_log = AsyncMock(return_value=log)

    with patch("app.core.security.get_current_user", return_value=MOCK_TOKEN_PAYLOAD_HR), \
         patch("app.core.security.require_roles", return_value=lambda r: MOCK_TOKEN_PAYLOAD_HR):
        app.dependency_overrides[get_audit_service] = lambda: mock_svc
        client = TestClient(app)
        response = client.get(
            f"/api/v1/audit/logs/{log.id}",
            headers={"Authorization": "Bearer faketoken"},
        )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["event_type"] == "employee.created"


def test_get_audit_log_not_found():
    """GET /audit/logs/{id} — not found returns 404."""
    mock_svc = AsyncMock(spec=AuditService)
    mock_svc.get_log = AsyncMock(return_value=None)

    with patch("app.core.security.get_current_user", return_value=MOCK_TOKEN_PAYLOAD_HR), \
         patch("app.core.security.require_roles", return_value=lambda r: MOCK_TOKEN_PAYLOAD_HR):
        app.dependency_overrides[get_audit_service] = lambda: mock_svc
        client = TestClient(app)
        response = client.get(
            f"/api/v1/audit/logs/{uuid.uuid4()}",
            headers={"Authorization": "Bearer faketoken"},
        )

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_export_csv_requires_super_admin():
    """CSV export should be forbidden for HR role (403)."""
    mock_svc = AsyncMock(spec=AuditService)

    with patch("app.core.security.get_current_user", return_value={"role": "hr"}), \
         patch("app.core.security.require_roles", side_effect=lambda roles: _role_guard(roles)):
        app.dependency_overrides[get_audit_service] = lambda: mock_svc
        client = TestClient(app)
        response = client.get(
            "/api/v1/audit/logs/export/csv",
            headers={"Authorization": "Bearer faketoken"},
        )

    app.dependency_overrides.clear()
    assert response.status_code in (403, 401)


def _role_guard(roles):
    from fastapi import HTTPException
    def dep(request):
        raise HTTPException(status_code=403, detail="Forbidden")
    return dep
