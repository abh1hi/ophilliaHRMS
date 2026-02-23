"""Unit tests for AttendanceService business logic."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import date, datetime, timezone, timedelta

from fastapi import HTTPException

from app.services.attendance_service import AttendanceService, GeofenceService
from app.schemas.attendance import ClockInRequest, ClockOutRequest, GeofenceCreate
from app.models.attendance_record import AttendanceRecord
from app.models.geofence_location import GeofenceLocation


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def service(mock_db):
    return AttendanceService(mock_db)


class TestClockIn:
    @pytest.mark.asyncio
    async def test_clock_in_success_manual(self, service):
        """Should clock in when no existing record and method=manual."""
        data = ClockInRequest()

        with patch.object(service.attendance_repo, "get_by_employee_and_date", return_value=None), \
             patch.object(service.policy_repo, "get_for_employee", return_value=None), \
             patch.object(service.attendance_repo, "create") as mock_create:
            mock_record = MagicMock(spec=AttendanceRecord)
            mock_record.method = "manual"
            mock_record.status = "present"
            mock_create.return_value = mock_record

            result = await service.clock_in(uuid4(), data)
            assert result.method == "manual"
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_clock_in_duplicate_rejected(self, service):
        """Should raise 409 if already clocked in today."""
        data = ClockInRequest()

        with patch.object(service.attendance_repo, "get_by_employee_and_date", return_value=MagicMock()):
            with pytest.raises(HTTPException) as exc_info:
                await service.clock_in(uuid4(), data)
            assert exc_info.value.status_code == 409


class TestClockOut:
    @pytest.mark.asyncio
    async def test_clock_out_no_clock_in(self, service):
        """Should raise 404 if no clock-in record for today."""
        data = ClockOutRequest()

        with patch.object(service.attendance_repo, "get_by_employee_and_date", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await service.clock_out(uuid4(), data)
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_clock_out_already_clocked_out(self, service):
        """Should raise 409 if already clocked out."""
        data = ClockOutRequest()
        existing = MagicMock(spec=AttendanceRecord)
        existing.clock_out = datetime.now(timezone.utc)

        with patch.object(service.attendance_repo, "get_by_employee_and_date", return_value=existing):
            with pytest.raises(HTTPException) as exc_info:
                await service.clock_out(uuid4(), data)
            assert exc_info.value.status_code == 409


class TestGeofenceValidation:
    def test_geofence_required_but_no_location(self, service):
        """Should raise 422 when method=geofence but no lat/lng provided."""
        geofence = MagicMock(spec=GeofenceLocation)
        with pytest.raises(HTTPException) as exc_info:
            service._validate_geofence("geofence", geofence, None, None)
        assert exc_info.value.status_code == 422

    def test_geofence_outside_radius(self, service):
        """Should raise 403 when user is outside geofence radius."""
        geofence = MagicMock(spec=GeofenceLocation)
        geofence.latitude = 28.6139   # Delhi
        geofence.longitude = 77.2090
        geofence.radius_meters = 100
        geofence.name = "HQ Office"

        with pytest.raises(HTTPException) as exc_info:
            # Mumbai coords — thousands of km away
            service._validate_geofence("geofence", geofence, 19.0760, 72.8777)
        assert exc_info.value.status_code == 403


class TestSchoolMode:
    @pytest.mark.asyncio
    async def test_mark_school_mode_success(self, service):
        """Should create a school mode record successfully."""
        from app.schemas.attendance import SchoolModeAttendanceCreate
        
        data = SchoolModeAttendanceCreate(
            employee_id=uuid4(),
            status="present",
            notes="Marked by HR"
        )
        
        with patch.object(service.attendance_repo, "get_by_employee_and_date", return_value=None), \
             patch.object(service.attendance_repo, "create") as mock_create:
                 
            mock_record = MagicMock(spec=AttendanceRecord)
            mock_record.method = "school_mode"
            mock_record.status = "present"
            mock_create.return_value = mock_record
            
            result = await service.mark_school_mode_attendance(data, created_by="hr_id")
            
            assert result.method == "school_mode"
            assert result.status == "present"
            mock_create.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_mark_school_mode_duplicate_rejected(self, service):
        """Should raise 409 if record already exists for today."""
        from app.schemas.attendance import SchoolModeAttendanceCreate
        
        data = SchoolModeAttendanceCreate(
            employee_id=uuid4(),
            status="present",
            notes="Marked by HR"
        )
        
        existing = MagicMock(spec=AttendanceRecord)
        
        with patch.object(service.attendance_repo, "get_by_employee_and_date", return_value=existing):
            with pytest.raises(HTTPException) as exc_info:
                await service.mark_school_mode_attendance(data, created_by="hr_id")
            assert exc_info.value.status_code == 409
