"""Unit tests for DepartmentService business logic."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import HTTPException

from app.services.department_service import DepartmentService
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.models.department import Department


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def service(mock_db):
    return DepartmentService(mock_db)


class TestCreateDepartment:
    @pytest.mark.asyncio
    async def test_create_department_success(self, service):
        """Should create department when name is unique."""
        data = DepartmentCreate(name="Engineering", description="Eng team")

        with patch.object(service.repo, "get_by_name", return_value=None), \
             patch.object(service.repo, "create") as mock_create:
            mock_dept = Department(
                id=uuid4(),
                name=data.name,
                description=data.description,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            mock_create.return_value = mock_dept

            result = await service.create_department(data)

            assert result.name == "Engineering"
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_department_duplicate_name(self, service):
        """Should raise 409 when department name exists."""
        data = DepartmentCreate(name="Engineering")

        with patch.object(service.repo, "get_by_name", return_value=MagicMock()):
            with pytest.raises(HTTPException) as exc_info:
                await service.create_department(data)
            assert exc_info.value.status_code == 409


class TestGetDepartment:
    @pytest.mark.asyncio
    async def test_get_department_not_found(self, service):
        """Should raise 404 when department doesn't exist."""
        with patch.object(service.repo, "get_by_id", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await service.get_department(uuid4())
            assert exc_info.value.status_code == 404
