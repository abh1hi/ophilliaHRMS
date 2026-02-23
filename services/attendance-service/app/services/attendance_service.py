import logging
from typing import Optional
from uuid import UUID
from datetime import date, datetime, timezone, time

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_record import AttendanceRecord
from app.models.geofence_location import GeofenceLocation
from app.models.attendance_policy import AttendancePolicy
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.geofence_repository import GeofenceRepository
from app.repositories.policy_repository import PolicyRepository
from app.schemas.attendance import (
    ClockInRequest,
    ClockOutRequest,
    ManualAttendanceCreate,
    AttendanceUpdate,
    GeofenceCreate,
    PolicyCreate,
    SchoolModeAttendanceCreate,
)
from app.events.publisher import EventPublisher
from app.utils.geofence import is_within_geofence
from app.core.config import settings

logger = logging.getLogger(__name__)


class AttendanceService:
    """Business logic for attendance: clock-in/out, geofence, overtime."""

    def __init__(self, db: AsyncSession, event_publisher: Optional[EventPublisher] = None):
        self.attendance_repo = AttendanceRepository(db)
        self.geofence_repo = GeofenceRepository(db)
        self.policy_repo = PolicyRepository(db)
        self.event_publisher = event_publisher

    # ──────────── POLICY RESOLUTION ────────────

    async def _resolve_policy(
        self, employee_id: UUID, department_id: Optional[UUID] = None
    ) -> tuple[str, Optional[GeofenceLocation], float, Optional[time]]:
        """Resolve attendance policy for an employee.

        Returns: (method, geofence_location, work_hours_per_day, work_start_time)
        """
        policy = await self.policy_repo.get_for_employee(employee_id, department_id)

        if policy is None:
            return "manual", None, settings.DEFAULT_WORK_HOURS_PER_DAY, None

        geofence = None
        if policy.geofence_id:
            geofence = await self.geofence_repo.get_by_id(policy.geofence_id)

        return (
            policy.method,
            geofence,
            policy.work_hours_per_day,
            policy.work_start_time,
        )

    # ──────────── GEOFENCE VALIDATION ────────────

    def _validate_geofence(
        self,
        method: str,
        geofence: Optional[GeofenceLocation],
        lat: Optional[float],
        lng: Optional[float],
    ) -> None:
        """Validate location against geofence if required by policy."""
        if method in ("geofence", "both"):
            if lat is None or lng is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Location (latitude, longitude) is required for geofence-based attendance",
                )
            if geofence is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Geofence location not configured. Contact admin.",
                )
            is_within, distance = is_within_geofence(
                lat, lng,
                geofence.latitude, geofence.longitude,
                geofence.radius_meters,
            )
            if not is_within:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You are {distance:.0f}m away from '{geofence.name}'. "
                           f"Allowed radius: {geofence.radius_meters}m.",
                )

    # ──────────── CLOCK IN ────────────

    async def clock_in(
        self,
        employee_id: UUID,
        data: ClockInRequest,
        department_id: Optional[UUID] = None,
    ) -> AttendanceRecord:
        today = date.today()

        # Check if already clocked in today
        existing = await self.attendance_repo.get_by_employee_and_date(employee_id, today)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Already clocked in for today",
            )

        # Resolve policy and validate geofence
        method, geofence, work_hours, work_start = await self._resolve_policy(
            employee_id, department_id
        )
        self._validate_geofence(method, geofence, data.latitude, data.longitude)

        # Determine status (on-time vs late)
        now = datetime.now(timezone.utc)
        attendance_status = "present"
        if work_start:
            clock_in_time = now.time()
            if clock_in_time > work_start:
                attendance_status = "late"

        record = AttendanceRecord(
            employee_id=employee_id,
            clock_in=now,
            clock_in_lat=data.latitude,
            clock_in_lng=data.longitude,
            status=attendance_status,
            method=method if method != "both" else "geofence" if data.latitude else "manual",
            notes=data.notes,
            date=today,
        )
        record = await self.attendance_repo.create(record)

        # Publish event
        if self.event_publisher:
            await self.event_publisher.publish("attendance.clock_in", {
                "employee_id": str(employee_id),
                "method": record.method,
                "status": record.status,
                "timestamp": now.isoformat(),
            })

        logger.info(
            f"Clock-in: employee={employee_id}, status={attendance_status}",
            extra={"user_id": str(employee_id), "service_task": "clock_in"},
        )
        return record

    # ──────────── CLOCK OUT ────────────

    async def clock_out(
        self,
        employee_id: UUID,
        data: ClockOutRequest,
        department_id: Optional[UUID] = None,
    ) -> AttendanceRecord:
        today = date.today()

        record = await self.attendance_repo.get_by_employee_and_date(employee_id, today)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No clock-in record found for today. Clock in first.",
            )
        if record.clock_out:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Already clocked out for today",
            )

        # Validate geofence on clock-out too
        method, geofence, work_hours_per_day, _ = await self._resolve_policy(
            employee_id, department_id
        )
        self._validate_geofence(method, geofence, data.latitude, data.longitude)

        # Compute work hours and overtime
        now = datetime.now(timezone.utc)
        delta = now - record.clock_in
        total_hours = round(delta.total_seconds() / 3600, 2)
        overtime = max(0.0, round(total_hours - work_hours_per_day, 2))

        # Detect half-day
        current_status = record.status
        if total_hours < (work_hours_per_day / 2):
            current_status = "half_day"

        update_data = {
            "clock_out": now,
            "clock_out_lat": data.latitude,
            "clock_out_lng": data.longitude,
            "work_hours": total_hours,
            "overtime_hours": overtime,
            "status": current_status,
            "notes": data.notes if data.notes else record.notes,
        }
        record = await self.attendance_repo.update(record, update_data)

        # Publish event
        if self.event_publisher:
            await self.event_publisher.publish("attendance.clock_out", {
                "employee_id": str(employee_id),
                "work_hours": total_hours,
                "overtime_hours": overtime,
                "timestamp": now.isoformat(),
            })

        logger.info(
            f"Clock-out: employee={employee_id}, hours={total_hours}, overtime={overtime}",
            extra={"user_id": str(employee_id), "service_task": "clock_out"},
        )
        return record

    # ──────────── GET MY TODAY ────────────

    async def get_today_record(self, employee_id: UUID) -> Optional[AttendanceRecord]:
        return await self.attendance_repo.get_by_employee_and_date(employee_id, date.today())

    # ──────────── LIST (Employee's own) ────────────

    async def get_my_records(
        self,
        employee_id: UUID,
        skip: int = 0,
        limit: int = 20,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> tuple[list, int]:
        return await self.attendance_repo.get_employee_records(
            employee_id, skip, limit, date_from, date_to
        )

    # ──────────── LIST ALL (Admin) ────────────

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 20,
        employee_id: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        status: Optional[str] = None,
    ) -> tuple[list, int]:
        return await self.attendance_repo.get_all(
            skip, limit, employee_id, date_from, date_to, status
        )

    # ──────────── GET BY ID ────────────

    async def get_record(self, record_id: UUID) -> AttendanceRecord:
        record = await self.attendance_repo.get_by_id(record_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attendance record {record_id} not found",
            )
        return record

    # ──────────── MANUAL CORRECTION (Admin) ────────────

    async def update_record(self, record_id: UUID, data: AttendanceUpdate) -> AttendanceRecord:
        record = await self.get_record(record_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No fields to update",
            )
        if "status" in update_data and update_data["status"] is not None:
            update_data["status"] = update_data["status"].value
        return await self.attendance_repo.update(record, update_data)

    # ──────────── MANUAL ENTRY (Admin) ────────────

    async def manual_entry(self, data: ManualAttendanceCreate, created_by: str) -> AttendanceRecord:
        existing = await self.attendance_repo.get_by_employee_and_date(
            data.employee_id, data.date
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Attendance record already exists for {data.date}",
            )

        # Compute work_hours if both clock_in and clock_out provided
        work_hours = None
        overtime = 0.0
        if data.clock_out:
            delta = data.clock_out - data.clock_in
            work_hours = round(delta.total_seconds() / 3600, 2)
            overtime = max(0.0, round(work_hours - settings.DEFAULT_WORK_HOURS_PER_DAY, 2))

        record = AttendanceRecord(
            employee_id=data.employee_id,
            clock_in=data.clock_in,
            clock_out=data.clock_out,
            work_hours=work_hours,
            overtime_hours=overtime,
            status=data.status.value,
            method="manual",
            notes=data.notes,
            date=data.date,
        )
        record = await self.attendance_repo.create(record)

        if self.event_publisher:
            await self.event_publisher.publish("attendance.manual_entry", {
                "employee_id": str(data.employee_id),
                "date": str(data.date),
                "created_by": created_by,
            })

        return record


    # ──────────── SCHOOL MODE (Admin/HR) ────────────

    async def mark_school_mode_attendance(self, data: "SchoolModeAttendanceCreate", created_by: str) -> AttendanceRecord:
        today = date.today()
        existing = await self.attendance_repo.get_by_employee_and_date(
            data.employee_id, today
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Attendance record already exists for today",
            )

        now = datetime.now(timezone.utc)
        record = AttendanceRecord(
            employee_id=data.employee_id,
            clock_in=now,  # Using current time as clock-in time for school mode
            clock_out=now, # Automatically clocking out to complete the entry immediately, or leave None
            work_hours=settings.DEFAULT_WORK_HOURS_PER_DAY if data.status.value in ["present", "late"] else 0, # Assuming full day for present
            overtime_hours=0.0,
            status=data.status.value,
            method="school_mode",
            notes=data.notes,
            date=today,
        )
        record = await self.attendance_repo.create(record)

        if self.event_publisher:
            await self.event_publisher.publish("attendance.school_mode_entry", {
                "employee_id": str(data.employee_id),
                "date": str(today),
                "status": record.status,
                "created_by": created_by,
            })

        return record


class GeofenceService:
    """Business logic for managing geofence locations."""

    def __init__(self, db: AsyncSession):
        self.repo = GeofenceRepository(db)

    async def create_geofence(self, data: GeofenceCreate) -> GeofenceLocation:
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Geofence '{data.name}' already exists",
            )
        geofence = GeofenceLocation(
            name=data.name,
            latitude=data.latitude,
            longitude=data.longitude,
            radius_meters=data.radius_meters,
        )
        return await self.repo.create(geofence)

    async def list_geofences(self) -> tuple[list, int]:
        return await self.repo.get_all_active()


class PolicyService:
    """Business logic for managing attendance policies."""

    def __init__(self, db: AsyncSession):
        self.repo = PolicyRepository(db)

    async def create_policy(self, data: PolicyCreate) -> AttendancePolicy:
        policy = AttendancePolicy(
            department_id=data.department_id,
            employee_id=data.employee_id,
            method=data.method.value,
            geofence_id=data.geofence_id,
            work_start_time=data.work_start_time,
            work_hours_per_day=data.work_hours_per_day,
        )
        return await self.repo.create(policy)

    async def list_policies(self) -> tuple[list, int]:
        return await self.repo.get_all()
