import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import date, datetime, timezone
from fastapi import HTTPException

from app.services.attendance_service import AttendanceService
from app.schemas.attendance import ClockInRequest
from app.models.attendance_record import AttendanceRecord

@pytest.fixture
def mock_db():
    mock = AsyncMock()
    mock.info = {"company_id": str(uuid4())}
    return mock

@pytest.fixture
def service(mock_db):
    return AttendanceService(mock_db)

@pytest.mark.asyncio
async def test_get_today_shifts_default_max_shifts(service):
    """Verify that get_today_shifts returns max_shifts=2 by default."""
    employee_id = uuid4()
    
    with patch.object(service.attendance_repo, "get_all_shifts_today", return_value=[]), \
         patch.object(service.policy_repo, "get_for_employee", return_value=None):
        
        result = await service.get_today_shifts(employee_id)
        
        assert result["max_shifts"] == 2
        assert result["shift_count"] == 0
        assert result["can_start_new_shift"] is True

@pytest.mark.asyncio
async def test_can_start_second_shift_after_first_completed(service):
    """Verify that can_start_new_shift is True after one completed shift."""
    employee_id = uuid4()
    
    # Create one completed shift
    mock_shift = MagicMock(spec=AttendanceRecord)
    mock_shift.clock_out = datetime.now(timezone.utc)
    
    with patch.object(service.attendance_repo, "get_all_shifts_today", return_value=[mock_shift]), \
         patch.object(service.policy_repo, "get_for_employee", return_value=None):
        
        result = await service.get_today_shifts(employee_id)
        
        assert result["max_shifts"] == 2
        assert result["shift_count"] == 1
        assert result["can_start_new_shift"] is True

@pytest.mark.asyncio
async def test_cannot_start_third_shift_by_default(service):
    """Verify that can_start_new_shift is False after two completed shifts."""
    employee_id = uuid4()
    
    # Create two completed shifts
    s1 = MagicMock(spec=AttendanceRecord)
    s1.clock_out = datetime.now(timezone.utc)
    s2 = MagicMock(spec=AttendanceRecord)
    s2.clock_out = datetime.now(timezone.utc)
    
    with patch.object(service.attendance_repo, "get_all_shifts_today", return_value=[s1, s2]), \
         patch.object(service.policy_repo, "get_for_employee", return_value=None):
        
        result = await service.get_today_shifts(employee_id)
        
        assert result["max_shifts"] == 2
        assert result["shift_count"] == 2
        assert result["can_start_new_shift"] is False

@pytest.mark.asyncio
async def test_clock_in_allows_second_shift_by_default(service):
    """Verify that clock_in allows a second shift if the first is completed."""
    employee_id = uuid4()
    data = ClockInRequest()
    
    # First shift completed
    existing_record = MagicMock(spec=AttendanceRecord)
    existing_record.clock_out = datetime.now(timezone.utc)
    
    with patch.object(service.attendance_repo, "get_by_employee_and_date", return_value=existing_record), \
         patch.object(service.policy_repo, "get_for_employee", return_value=None), \
         patch.object(service.attendance_repo, "get_shift_count_today", return_value=1), \
         patch.object(service, "_resolve_policy", return_value=("manual", None, 8.0, None)), \
         patch.object(service.attendance_repo, "create") as mock_create:
        
        mock_new_record = MagicMock(spec=AttendanceRecord)
        mock_create.return_value = mock_new_record
        
        result = await service.clock_in(employee_id, data)
        assert result == mock_new_record
        mock_create.assert_called_once()
        # Verify shift_number is 2
        args, _ = mock_create.call_args
        assert args[0].shift_number == 2
