import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from app.services.auth_service import AuthService
from app.models.user import User
from app.core.constants import UserRole

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def service(mock_db):
    return AuthService(mock_db)

class TestAuthService:
    @pytest.mark.asyncio
    async def test_register_user_success(self, service):
        from app.schemas.request_response_models import UserCreate
        
        data = UserCreate(
            email="test@example.com",
            password="securepassword123",
            role=UserRole.EMPLOYEE,
        )
        
        with patch.object(service.user_repository, "get_by_email", return_value=None), \
             patch.object(service.user_repository, "create") as mock_create:
                 
            mock_user = User(
                id=uuid4(),
                email="test@example.com",
                hashed_password="hashed_pass",
                role=UserRole.EMPLOYEE.value,
                is_active=True
            )
            mock_create.return_value = mock_user
            
            result = await service.register_user(data)
            
            assert result.email == "test@example.com"
            assert result.role == UserRole.EMPLOYEE.value
            mock_create.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, service):
        from app.schemas.request_response_models import UserCreate
        
        data = UserCreate(
            email="existing@example.com",
            password="securepassword123",
            role=UserRole.EMPLOYEE,
        )
        
        existing_user = User(id=uuid4(), email="existing@example.com")
        
        with patch.object(service.user_repository, "get_by_email", return_value=existing_user):
            with pytest.raises(HTTPException) as exc_info:
                await service.register_user(data)
            assert exc_info.value.status_code == 400
            assert "Email already registered" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_credentials(self, service):
        from app.schemas.request_response_models import UserLogin
        data = UserLogin(email="wrong@example.com", password="password")
        
        with patch.object(service.user_repository, "get_by_email", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await service.authenticate_user(data)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, service, monkeypatch):
        # We need to mock verify_password to True but user is inactive
        existing = User(id=uuid4(), email="test@example.com", hashed_password="hashed_pass", is_active=False)
        
        def mock_verify_password(plain, hashed):
            return True
        import app.services.auth_service
        monkeypatch.setattr(app.services.auth_service, "verify_password", mock_verify_password)
        from app.schemas.request_response_models import UserLogin
        data = UserLogin(email="test@example.com", password="password")
        
        with patch.object(service.user_repository, "get_by_email", return_value=existing):
            with pytest.raises(HTTPException) as exc_info:
                await service.authenticate_user(data)
            assert exc_info.value.status_code == 400
            assert "Inactive user" in exc_info.value.detail
