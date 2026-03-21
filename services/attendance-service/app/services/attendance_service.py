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
from app.repositories.task_repository import TaskRepository
from app.schemas.attendance import (
    ClockInRequest,
    ClockOutRequest,
    ManualAttendanceCreate,
    AttendanceUpdate,
    GeofenceCreate,
    GeofenceUpdate,
    PolicyCreate,
    PolicyUpdate,
    SchoolModeAttendanceCreate,
    ProductivityReportItem,
    ProductivityReportResponse,
    AlertsResponse,
    MissedPunchOutItem,
)
from app.events.publisher import EventPublisher
from app.utils.geofence import is_within_geofence
from app.core.config import settings
from app.core.employee_validator import validate_employee_tenant

logger = logging.getLogger(__name__)


class AttendanceService:
    """Business logic for attendance: clock-in/out, geofence, overtime."""

    def __init__(self, db: AsyncSession, event_publisher: Optional[EventPublisher] = None):
        self.attendance_repo = AttendanceRepository(db)
        self.geofence_repo = GeofenceRepository(db)
        self.policy_repo = PolicyRepository(db)
        self.task_repo = TaskRepository(db)
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

        # Validate employee belongs to current tenant
        company_id = self.attendance_repo.db.info.get("company_id")
        if company_id:
            await validate_employee_tenant(employee_id, company_id)

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
            clock_in_location_name=data.location_name,
            status=attendance_status,
            method=method if method != "both" else "geofence" if data.latitude else "manual",
            notes=data.notes,
            date=today,
        )
        record = await self.attendance_repo.create(record)

        # Publish event
        if self.event_publisher:
            company_id = self.attendance_repo.db.info.get("company_id")
            await self.event_publisher.publish("attendance.clock_in", {
                "company_id": str(company_id) if company_id else None,
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
            "clock_out_location_name": data.location_name,
            "work_hours": total_hours,
            "overtime_hours": overtime,
            "status": current_status,
            "notes": data.notes if data.notes else record.notes,
            "day_rating": data.day_rating,
        }
        record = await self.attendance_repo.update(record, update_data)

        # Process task completions supplied inline with punch-out
        if data.task_completions:
            for item in data.task_completions:
                task = await self.task_repo.get_by_id(item.task_id)
                if task and task.employee_id == employee_id:
                    await self.task_repo.update(task, {
                        "status": item.status,
                        "completion_notes": item.completion_notes,
                        "actual_expenses": item.actual_expenses,
                    })

        # Publish event
        if self.event_publisher:
            company_id = self.attendance_repo.db.info.get("company_id")
            await self.event_publisher.publish("attendance.clock_out", {
                "company_id": str(company_id) if company_id else None,
                "employee_id": str(employee_id),
                "work_hours": total_hours,
                "overtime_hours": overtime,
                "day_rating": data.day_rating,
                "timestamp": now.isoformat(),
            })

        logger.info(
            f"Clock-out: employee={employee_id}, hours={total_hours}, overtime={overtime}, rating={data.day_rating}",
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
        # Validate employee belongs to current tenant
        company_id = self.attendance_repo.db.info.get("company_id")
        if company_id:
            await validate_employee_tenant(data.employee_id, company_id)

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
            company_id = self.attendance_repo.db.info.get("company_id")
            await self.event_publisher.publish("attendance.manual_entry", {
                "company_id": str(company_id) if company_id else None,
                "employee_id": str(data.employee_id),
                "date": str(data.date),
                "created_by": created_by,
            })

        return record


    # ──────────── SCHOOL MODE (Admin/HR) ────────────

    async def mark_school_mode_attendance(self, data: "SchoolModeAttendanceCreate", created_by: str) -> AttendanceRecord:
        # Validate employee belongs to current tenant
        company_id = self.attendance_repo.db.info.get("company_id")
        if company_id:
            await validate_employee_tenant(data.employee_id, company_id)

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
            company_id = self.attendance_repo.db.info.get("company_id")
            await self.event_publisher.publish("attendance.school_mode_entry", {
                "company_id": str(company_id) if company_id else None,
                "employee_id": str(data.employee_id),
                "date": str(today),
                "status": record.status,
                "created_by": created_by,
            })

        return record


    # ──────────── ALERTS (Admin) ────────────

    async def get_alerts(self) -> AlertsResponse:
        """Return today's late punch-in count and employees with missed punch-out."""
        missed = await self.attendance_repo.get_missed_punchout_today()
        late_count = await self.attendance_repo.get_late_count_today()
        missed_items = [
            MissedPunchOutItem(
                employee_id=r.employee_id,
                record_id=r.id,
                clock_in=r.clock_in,
                clock_in_location_name=r.clock_in_location_name,
            )
            for r in missed
        ]
        return AlertsResponse(
            date=date.today(),
            late_count=late_count,
            missed_punch_out_count=len(missed_items),
            missed_punch_outs=missed_items,
        )

    # ──────────── PRODUCTIVITY REPORT (Admin) ────────────

    async def get_productivity_report(
        self,
        year: int,
        month: int,
        employee_id: Optional[UUID] = None,
    ) -> ProductivityReportResponse:
        """Return per-employee productivity stats for a given month."""
        rows = await self.attendance_repo.get_productivity_data(year, month, employee_id)
        items = [ProductivityReportItem(**row) for row in rows]
        return ProductivityReportResponse(month=month, year=year, items=items)


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

    async def list_geofences(self, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> tuple[list, int]:
        return await self.repo.get_all_active(skip=skip, limit=limit, include_inactive=include_inactive)

    async def update_geofence(self, geofence_id: UUID, data: GeofenceUpdate) -> GeofenceLocation:
        geofence = await self.repo.get_by_id(geofence_id)
        if not geofence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Geofence not found",
            )
        updates = data.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )
        # Check name uniqueness if name is being changed
        if "name" in updates and updates["name"] != geofence.name:
            existing = await self.repo.get_by_name(updates["name"])
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Geofence '{updates['name']}' already exists",
                )
        return await self.repo.update(geofence, updates)

    async def soft_delete_geofence(self, geofence_id: UUID) -> GeofenceLocation:
        geofence = await self.repo.get_by_id(geofence_id)
        if not geofence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Geofence not found",
            )
        if not geofence.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Geofence is already deactivated",
            )
        return await self.repo.soft_delete(geofence)


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

    async def list_policies(self, skip: int = 0, limit: int = 100) -> tuple[list, int]:
        return await self.repo.get_all(skip=skip, limit=limit)

    async def update_policy(self, policy_id: UUID, data: PolicyUpdate) -> AttendancePolicy:
        policy = await self.repo.get_by_id(policy_id)
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found",
            )
        updates = data.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )
        # Convert enum to string value if method is present
        if "method" in updates and updates["method"] is not None:
            updates["method"] = updates["method"].value
        return await self.repo.update(policy, updates)

    async def delete_policy(self, policy_id: UUID) -> None:
        policy = await self.repo.get_by_id(policy_id)
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found",
            )
        await self.repo.delete(policy)
