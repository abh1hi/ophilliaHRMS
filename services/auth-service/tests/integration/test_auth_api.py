import pytest
import asyncio
from httpx import AsyncClient
from uuid import uuid4
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
# Setup basic test client for API endpoints

@pytest.fixture
def anyio_backend():
    return 'asyncio'

# In a real environment we would override the get_db dependency to point to SQLite.
# This serves as the integration API smoke test framework snippet.

@pytest.mark.asyncio
async def test_auth_status_endpoint():
    # As an initial check we will create a direct test against the actual FastAPI app
    from app.main import app
    async with AsyncClient(app=app, base_url="http://testServer") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_register_api(monkeypatch):
    """Integration style test for POST /register bypassing actual DB to allow CI/CD pure logic execution."""
    from app.main import app
    from app.services.auth_service import AuthService
    from app.schemas.request_response_models import UserResponse
    
    async def mock_register(*args, **kwargs):
        return UserResponse(
            id=uuid4(),
            email="api_test@example.com",
            role="employee",
            is_active=True,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        
    monkeypatch.setattr(AuthService, "register_user", mock_register)
    
    async with AsyncClient(app=app, base_url="http://testServer") as ac:
        response = await ac.post("/api/v1/auth/register", json={
            "email": "api_test@example.com",
            "password": "strongPassword1",
            "role": "employee"
        })
        assert response.status_code == 201
        assert response.json()["email"] == "api_test@example.com"

@pytest.mark.asyncio
async def test_login_api(monkeypatch):
    from app.main import app
    from app.services.auth_service import AuthService
    from app.schemas.request_response_models import Token
    
    async def mock_login(*args, **kwargs):
        return Token(
            access_token="mock_access_token",
            token_type="bearer",
            refresh_token="mock_refresh_token"
        )
        
    monkeypatch.setattr(AuthService, "authenticate_user", mock_login)
    
    async with AsyncClient(app=app, base_url="http://testServer") as ac:
        response = await ac.post("/api/v1/auth/login", json={
            "email": "api_test@example.com",
            "password": "strongPassword1"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["access_token"] == "mock_access_token"
