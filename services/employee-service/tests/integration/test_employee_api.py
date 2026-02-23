import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.asyncio
async def test_employee_status_endpoint():
    from app.main import app
    async with AsyncClient(app=app, base_url="http://testServer") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_create_employee_rbaca(monkeypatch):
    """Test creating an employee without Super Admin privileges."""
    from app.main import app
    from app.core.security import get_current_user, TokenPayload
    
    async def mock_get_current_user():
        return TokenPayload(sub=str(uuid4()), role="employee", email="test@emp.com")
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    async with AsyncClient(app=app, base_url="http://testServer") as ac:
        response = await ac.post("/api/v1/employees", json={
            "first_name": "API",
            "last_name": "Test",
            "email": "test@emp.com",
            "user_id": str(uuid4())
        })
        
        # the app dependency overrrides feature ensures 403 is triggered
        assert response.status_code == 403
        
    app.dependency_overrides.clear()
