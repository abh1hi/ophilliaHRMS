import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import date, datetime

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.asyncio
async def test_attendance_status_endpoint():
    from app.main import app
    async with AsyncClient(app=app, base_url="http://testServer") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_school_mode_api_rbac(monkeypatch):
    """Test creating a school mode attendance record without HR/Super Admin privileges."""
    from app.main import app
    from app.core.security import get_current_user, TokenPayload
    
    async def mock_get_current_user():
        return TokenPayload(sub=str(uuid4()), role="employee", email="test@emp.com", company_id=str(uuid4()))
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    async def mock_get_db_with_tenant():
        class MockSession:
            info = {"company_id": str(uuid4())}
            async def close(self): pass
        yield MockSession()
        
    from app.api.v1.dependencies import get_db_with_tenant
    app.dependency_overrides[get_db_with_tenant] = mock_get_db_with_tenant

    async with AsyncClient(app=app, base_url="http://testServer") as ac:
        response = await ac.post("/api/v1/attendance/school-mode", json={
            "employee_id": str(uuid4()),
            "status": "present",
            "notes": "Admin testing"
        })
        
        if response.status_code == 422:
            print("Validation error:", response.json())
        assert response.status_code == 403
        
    app.dependency_overrides.clear()
    
@pytest.mark.asyncio
async def test_clock_in_api(monkeypatch):
    from app.main import app
    from app.services.attendance_service import AttendanceService
    from app.schemas.attendance import AttendanceResponse
    from app.core.security import get_current_user
    from fastapi import Depends
    
    mock_emp_id = uuid4()
    
    async def mock_get_current_user():
        from app.core.security import TokenPayload
        return TokenPayload(sub=str(mock_emp_id), role="employee", email="emp@test.com", company_id=str(uuid4()))
        
    app.dependency_overrides[get_current_user] = mock_get_current_user

    async def mock_get_db_with_tenant():
        class MockSession:
            info = {"company_id": str(uuid4())}
            async def close(self): pass
        yield MockSession()
        
    from app.api.v1.dependencies import get_db_with_tenant
    app.dependency_overrides[get_db_with_tenant] = mock_get_db_with_tenant

    async def mock_clock_in(*args, **kwargs):
        return AttendanceResponse(
            id=uuid4(),
            employee_id=mock_emp_id,
            clock_in=datetime.now(),
            status="present",
            method="manual",
            date=date.today(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
    monkeypatch.setattr(AttendanceService, "clock_in", mock_clock_in)
    
    async with AsyncClient(app=app, base_url="http://testServer") as ac:
        response = await ac.post("/api/v1/attendance/clock-in", json={
            "notes": "Starting shift"
        })
        assert response.status_code == 201
        assert response.json()["status"] == "present"
        assert response.json()["method"] == "manual"
        
    app.dependency_overrides.clear()
