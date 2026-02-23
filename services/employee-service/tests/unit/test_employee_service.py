"""Unit tests for EmployeeService business logic."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import date, datetime, timezone

from fastapi import HTTPException

from app.services.employee_service import EmployeeService
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.models.employee import Employee


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def service(mock_db):
    return EmployeeService(mock_db)


class TestCreateEmployee:
    @pytest.mark.asyncio
    async def test_create_employee_success(self, service):
        """Should create employee when no duplicate exists."""
        data = EmployeeCreate(
            user_id=uuid4(),
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            date_joined=date.today(),
        )

        with patch.object(service.repo, "get_by_email", return_value=None), \
             patch.object(service.repo, "get_by_user_id", return_value=None), \
             patch.object(service.repo, "create") as mock_create:
            mock_employee = Employee(
                id=uuid4(),
                user_id=data.user_id,
                first_name=data.first_name,
                last_name=data.last_name,
                email=data.email,
                date_joined=data.date_joined,
                employment_status="active",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            mock_create.return_value = mock_employee

            result = await service.create_employee(data)

            assert result.first_name == "John"
            assert result.email == "john@example.com"
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_employee_duplicate_email(self, service):
        """Should raise 409 when email already exists."""
        data = EmployeeCreate(
            user_id=uuid4(),
            first_name="John",
            last_name="Doe",
            email="existing@example.com",
            date_joined=date.today(),
        )

        with patch.object(service.repo, "get_by_email", return_value=MagicMock()):
            with pytest.raises(HTTPException) as exc_info:
                await service.create_employee(data)
            assert exc_info.value.status_code == 409


class TestGetEmployee:
    @pytest.mark.asyncio
    async def test_get_employee_not_found(self, service):
        """Should raise 404 when employee doesn't exist."""
        with patch.object(service.repo, "get_by_id", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await service.get_employee(uuid4())
            assert exc_info.value.status_code == 404


class TestDeactivateEmployee:
    @pytest.mark.asyncio
    async def test_deactivate_sets_terminated(self, service):
        """Should set employment_status to terminated."""
        emp_id = uuid4()
        mock_employee = Employee(
            id=emp_id,
            user_id=uuid4(),
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            date_joined=date.today(),
            employment_status="terminated",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        with patch.object(service.repo, "get_by_id", return_value=mock_employee), \
             patch.object(service.repo, "deactivate", return_value=mock_employee):
            result = await service.deactivate_employee(emp_id)
            assert result.employment_status == "terminated"
