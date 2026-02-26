import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import date, timedelta
from fastapi import HTTPException

from app.schemas.leave import LeaveRequestCreate, LeaveStatus
from app.services.leave_service import apply_leave
from app.models.leave import LeaveType, LeaveBalance, LeaveRequest


@pytest.mark.asyncio
async def test_apply_leave_insufficient_balance():
    # Setup mocks
    db_mock = AsyncMock()
    
    employee_id = uuid4()
    leave_type_id = uuid4()
    
    request_in = LeaveRequestCreate(
        employee_id=employee_id,
        leave_type_id=leave_type_id,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=5),
        reason="Vacation"
    )
    
    # Mock Leave Type
    mock_leave_type = LeaveType(id=leave_type_id, requires_approval=True)
    
    # Mock Balance (Only 2 days pending, 0 used out of 4 total, but requesting 6 days)
    mock_balance = LeaveBalance(
        employee_id=employee_id,
        leave_type_id=leave_type_id,
        year=date.today().year,
        total_days=4,
        used_days=0,
        pending_days=2
    )
    
    with patch("app.services.leave_service.get_leave_type", return_value=mock_leave_type):
        with patch("app.services.leave_service.get_leave_balance", return_value=mock_balance):
            # Mock overlapping date check
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = None
            db_mock.execute.return_value = mock_result

            with pytest.raises(HTTPException) as exc_info:
                await apply_leave(db_mock, request_in)
                
            assert exc_info.value.status_code == 400
            assert exc_info.value.detail == "Insufficient leave balance"


@pytest.mark.asyncio
async def test_apply_leave_success():
    # Setup mocks
    db_mock = AsyncMock()
    
    employee_id = uuid4()
    leave_type_id = uuid4()
    
    request_in = LeaveRequestCreate(
        employee_id=employee_id,
        leave_type_id=leave_type_id,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=2), # 3 days total
        reason="Vacation"
    )
    
    # Mock Leave Type
    mock_leave_type = LeaveType(id=leave_type_id, requires_approval=True)
    
    # Mock Balance (10 total, 0 used, 0 pending)
    mock_balance = LeaveBalance(
        employee_id=employee_id,
        leave_type_id=leave_type_id,
        year=date.today().year,
        total_days=10,
        used_days=0,
        pending_days=0
    )
    
    with patch("app.services.leave_service.get_leave_type", return_value=mock_leave_type):
        with patch("app.services.leave_service.get_leave_balance", return_value=mock_balance):
            with patch("app.services.leave_service.publish_event", new_callable=AsyncMock) as mock_publish:
                # Mock result for overlapping dates check
                mock_result = MagicMock()
                mock_result.scalars.return_value.first.return_value = None
                db_mock.execute.return_value = mock_result
                
                # To simulate db.refresh setting the id
                def mock_add(obj):
                    if isinstance(obj, LeaveRequest):
                        obj.id = uuid4()
                db_mock.add = MagicMock(side_effect=mock_add)
                
                result = await apply_leave(db_mock, request_in)
                
                assert result.status == LeaveStatus.PENDING.value
                assert result.total_days == 3
                assert mock_balance.pending_days == 3
                mock_publish.assert_called_once()
                assert mock_publish.call_args[0][0] == "leave.requested"
