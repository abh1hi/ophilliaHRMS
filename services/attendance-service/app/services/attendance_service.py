import json
import logging
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from datetime import date, datetime, timezone, time, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_record import AttendanceRecord
from app.models.geofence_location import GeofenceLocation
from app.models.attendance_policy import AttendancePolicy
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.geofence_repository import GeofenceRepository
from app.repositories.policy_repository import PolicyRepository
from app.repositories.policy_exception_repository import PolicyExceptionRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.attendance import (
    ClockInRequest,
    ClockOutRequest,
    ManualAttendanceCreate,
    AttendanceUpdate,
    GeofenceCreate,
    GeofenceUpdate,
    SchoolModeAttendanceCreate,
    ProductivityReportItem,
    ProductivityReportResponse,
    AlertsResponse,
    MissedPunchOutItem,
    AdminKPIResponse,
    AttendanceTrendItem,
    AttendanceTrendResponse,
    DailyStatusBreakdown,
    EmployeeProductivitySummary,
    PerformersResponse,
)
from app.events.publisher import EventPublisher
from app.utils.geofence import is_within_geofence
from app.core.config import settings
from app.core.employee_validator import validate_employee_tenant

logger = logging.getLogger(__name__)

_POLICY_CACHE_TTL = 300  # seconds


@dataclass
class _CachedGeofence:
    """Lightweight stand-in for GeofenceLocation when deserializing from Redis."""
    id: str
    name: str
    latitude: float
    longitude: float
    radius_meters: int


def _serialize_geofence(geofence) -> Optional[dict]:
    if geofence is None:
        return None
    return {
        "id": str(geofence.id),
        "name": geofence.name,
        "latitude": geofence.latitude,
        "longitude": geofence.longitude,
        "radius_meters": geofence.radius_meters,
    }


def _deserialize_geofence(data: Optional[dict]) -> Optional[_CachedGeofence]:
    if data is None:
        return None
    return _CachedGeofence(**data)


def _parse_time(value: Optional[str]) -> Optional[time]:
    if not value:
        return None
    try:
        parts = value.split(":")
        return time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)
    except Exception:
        return None


class AttendanceService:
    """Business logic for attendance: clock-in/out, geofence, overtime."""

    def __init__(self, db: AsyncSession, event_publisher: Optional[EventPublisher] = None):
        self.attendance_repo = AttendanceRepository(db)
        self.geofence_repo = GeofenceRepository(db)
        self.policy_repo = PolicyRepository(db)
        self.exception_repo = PolicyExceptionRepository(db)
        self.task_repo = TaskRepository(db)
        self.event_publisher = event_publisher

    # ──────────── POLICY RESOLUTION ────────────

    async def _resolve_policy(
        self, employee_id: UUID, department_id: Optional[UUID] = None
    ) -> tuple[str, Optional[object], float, Optional[time], int]:
        """Resolve attendance policy for an employee.

        Checks (in order):
          1. Redis cache
          2. Active PolicyException (employee-level temporary override)
          3. Normal cascade: employee-policy → department-policy → global → defaults

        Returns:
          (method, geofence, work_hours_per_day, work_start_time, late_grace_period_minutes)
        """
        company_id = self.attendance_repo.db.info.get("company_id")
        cache_key = f"policy:resolve:{company_id}:{employee_id}:{department_id or 'none'}"

        # ── 1. Try Redis cache ──
        try:
            from app.core.token_blacklist import _redis
            if _redis is not None:
                cached = await _redis.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    return (
                        data["method"],
                        _deserialize_geofence(data.get("geofence")),
                        data["work_hours_per_day"],
                        _parse_time(data.get("work_start_time")),
                        data.get("late_grace_period_minutes", 0),
                    )
        except Exception:
            logger.debug("Policy cache read failed — falling back to DB", exc_info=True)

        # ── 2. Active exemption overrides normal policy ──
        exception = await self.exception_repo.get_active_for_employee(
            employee_id, date.today()
        )
        if exception:
            geofence = None
            if exception.override_geofence_id:
                geofence = await self.geofence_repo.get_by_id(exception.override_geofence_id)
            method = exception.override_method or "manual"
            work_hours = exception.override_work_hours or settings.DEFAULT_WORK_HOURS_PER_DAY
            result = (method, geofence, work_hours, None, 0)
            await self._cache_policy_result(cache_key, result)
            return result

        # ── 3. Normal policy cascade ──
        policy = await self.policy_repo.get_for_employee(employee_id, department_id)

        if policy is None:
            result = ("manual", None, settings.DEFAULT_WORK_HOURS_PER_DAY, None, 0)
            await self._cache_policy_result(cache_key, result)
            return result

        geofence = None
        if policy.geofence_id:
            geofence = await self.geofence_repo.get_by_id(policy.geofence_id)

        result = (
            policy.method,
            geofence,
            policy.work_hours_per_day,
            policy.work_start_time,
            policy.late_grace_period_minutes,
        )
        await self._cache_policy_result(cache_key, result)
        return result

    async def _cache_policy_result(self, cache_key: str, result: tuple) -> None:
        """Serialize and store a policy resolution result in Redis."""
        try:
            from app.core.token_blacklist import _redis
            if _redis is None:
                return
            method, geofence, work_hours, work_start, grace = result
            payload = {
                "method": method,
                "work_hours_per_day": work_hours,
                "work_start_time": work_start.isoformat() if work_start else None,
                "late_grace_period_minutes": grace,
                "geofence": _serialize_geofence(geofence),
            }
            await _redis.set(cache_key, json.dumps(payload), ex=_POLICY_CACHE_TTL)
        except Exception:
            logger.debug("Policy cache write failed — continuing", exc_info=True)

    # ──────────── GEOFENCE VALIDATION ────────────

    def _validate_geofence(
        self,
        method: str,
        geofence,
        lat: Optional[float],
        lng: Optional[float],
        accuracy_meters: Optional[float] = None,
    ) -> None:
        """Validate location against geofence if required by policy.

        accuracy_meters: GPS accuracy radius reported by the device.
        When provided, the effective radius is expanded by this amount to
        prevent false rejections from GPS jitter.
        """
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
            effective_radius = geofence.radius_meters + (accuracy_meters or 0.0)
            is_within, distance = is_within_geofence(
                lat, lng,
                geofence.latitude, geofence.longitude,
                effective_radius,
            )
            if not is_within:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You are {distance:.0f}m away from '{geofence.name}'. "
                           f"Allowed radius: {geofence.radius_meters}m.",
                )

    # ──────────── CLOCK IN (idempotent) ────────────

    async def clock_in(
        self,
        employee_id: UUID,
        data: ClockInRequest,
        department_id: Optional[UUID] = None,
    ) -> AttendanceRecord:
        """Idempotent clock-in.

        Uses SELECT FOR UPDATE to prevent race conditions between concurrent
        requests.  If a duplicate INSERT hits the unique constraint
        (employee_id, date, shift_number), we catch the IntegrityError and
        return the existing record instead of a 500.
        """
        from sqlalchemy.exc import IntegrityError

        today = date.today()

        # Validate employee belongs to current tenant
        company_id = self.attendance_repo.db.info.get("company_id")
        if company_id:
            await validate_employee_tenant(employee_id, company_id)

        # Resolve policy and validate geofence
        method, geofence, work_hours, work_start, late_grace = await self._resolve_policy(
            employee_id, department_id
        )
        self._validate_geofence(method, geofence, data.latitude, data.longitude, data.accuracy_meters)

        # ── Locked read: prevent two concurrent clock-ins from racing ──
        existing = await self.attendance_repo.get_by_employee_and_date_for_update(
            employee_id, today
        )
        shift_number = 1
        if existing:
            # Already clocked in and still open → idempotent: return existing
            if existing.clock_out is None:
                logger.info(
                    f"Clock-in duplicate detected (idempotent): employee={employee_id}",
                    extra={"user_id": str(employee_id), "service_task": "clock_in", "duplicate": True},
                )
                await self.attendance_repo.commit()
                return existing

            # Allow new shift only if policy permits multiple shifts
            policy = await self.policy_repo.get_for_employee(employee_id, department_id)
            max_shifts = policy.max_shifts_per_day if policy else 2
            current_shift_count = await self.attendance_repo.get_shift_count_today(employee_id, today)
            if current_shift_count >= max_shifts:
                await self.attendance_repo.commit()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Maximum {int(max_shifts)} shift(s) per day reached",
                )
            shift_number = current_shift_count + 1

        # Determine status (on-time vs late) using grace period
        now = datetime.now(timezone.utc)
        attendance_status = "present"
        if work_start and shift_number == 1:
            clock_in_time = now.time()
            grace_end = (
                datetime.combine(today, work_start) + timedelta(minutes=late_grace)
            ).time()
            if clock_in_time > grace_end:
                attendance_status = "late"

        record = AttendanceRecord(
            employee_id=employee_id,
            clock_in=now,
            clock_in_lat=data.latitude,
            clock_in_lng=data.longitude,
            clock_in_location_name=data.location_name,
            status=attendance_status,
            state="punched_in",
            method=method if method != "both" else "geofence" if data.latitude else "manual",
            notes=data.notes,
            date=today,
            shift_number=shift_number,
            device_info=data.device_info,
            network_info=data.network_info,
        )

        try:
            record = await self.attendance_repo.create(record)
            await self.attendance_repo.commit()
        except IntegrityError:
            # Race condition: another request inserted first.
            # Rollback and return the existing record (idempotent).
            await self.attendance_repo.rollback()
            existing = await self.attendance_repo.get_by_employee_and_date(employee_id, today)
            if existing:
                logger.info(
                    f"Clock-in IntegrityError resolved (idempotent): employee={employee_id}",
                    extra={"user_id": str(employee_id), "service_task": "clock_in", "duplicate": True},
                )
                return existing
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Already clocked in for today.",
            )

        # Publish event (after commit — fire-and-forget)
        if self.event_publisher:
            await self.event_publisher.publish("attendance.clock_in", {
                "company_id": str(company_id) if company_id else None,
                "employee_id": str(employee_id),
                "method": record.method,
                "status": record.status,
                "shift_number": shift_number,
                "timestamp": now.isoformat(),
            })

        logger.info(
            f"Clock-in: employee={employee_id}, status={attendance_status}, shift={shift_number}",
            extra={"user_id": str(employee_id), "service_task": "clock_in"},
        )
        return record

    # ──────────── PRODUCTIVITY SCORE ────────────

    @staticmethod
    def _calculate_productivity_score(
        tasks: list,
        day_rating: Optional[int],
        work_hours: float,
        work_hours_per_day: float,
    ) -> float:
        """Calculate system productivity score (0-100).

        Formula:
        - 50% task completion rate
        - 25% self-rating (scaled to 0-25)
        - 25% hours worked vs expected (capped at 100%)
        """
        # Task completion component (50%)
        total_tasks = len(tasks)
        if total_tasks > 0:
            completed = sum(1 for t in tasks if t.status == "completed")
            partial = sum(1 for t in tasks if t.status == "partially_completed")
            task_score = ((completed + partial * 0.5) / total_tasks) * 50
        else:
            task_score = 0.0

        # Rating component (25%)
        rating_score = ((day_rating or 3) / 5) * 25

        # Hours component (25%)
        hours_ratio = min(work_hours / work_hours_per_day, 1.0) if work_hours_per_day > 0 else 0
        hours_score = hours_ratio * 25

        return round(task_score + rating_score + hours_score, 1)

    # ──────────── CLOCK OUT (idempotent) ────────────

    async def clock_out(
        self,
        employee_id: UUID,
        data: ClockOutRequest,
        department_id: Optional[UUID] = None,
    ) -> AttendanceRecord:
        """Idempotent clock-out.

        Uses SELECT FOR UPDATE to lock the open record, preventing concurrent
        punch-outs (manual + auto-close, or double-click) from conflicting.
        If already clocked out, returns the existing completed record.
        """
        today = date.today()

        # ── Locked read: only one punch-out can proceed at a time ──
        record = await self.attendance_repo.get_open_record_today_for_update(
            employee_id, today
        )

        if not record:
            # Maybe already clocked out — check for idempotent return
            latest = await self.attendance_repo.get_by_employee_and_date(employee_id, today)
            if latest and latest.clock_out is not None:
                logger.info(
                    f"Clock-out duplicate detected (idempotent): employee={employee_id}",
                    extra={"user_id": str(employee_id), "service_task": "clock_out", "duplicate": True},
                )
                return latest
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No open clock-in record found for today. Clock in first.",
            )

        # Validate geofence on clock-out too
        method, geofence, work_hours_per_day, _, _ = await self._resolve_policy(
            employee_id, department_id
        )
        self._validate_geofence(method, geofence, data.latitude, data.longitude)

        # Process task completions supplied inline with punch-out FIRST
        if data.task_completions:
            for item in data.task_completions:
                task = await self.task_repo.get_by_id(item.task_id)
                if task and task.employee_id == employee_id:
                    await self.task_repo.update(task, {
                        "status": item.status,
                        "completion_notes": item.completion_notes,
                        "actual_expenses": item.actual_expenses,
                    })

        # Reload tasks after processing completions
        tasks = await self.task_repo.get_by_record(record.id)

        # ── Punch-out validations ──
        if len(tasks) == 0:
            await self.attendance_repo.commit()  # release lock
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one task must be added before punching out",
            )

        pending_tasks = [t for t in tasks if t.status == "pending"]
        if pending_tasks:
            await self.attendance_repo.commit()  # release lock
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{len(pending_tasks)} task(s) still have 'pending' status. "
                       "Update all tasks before punching out.",
            )

        # Compute work hours and overtime
        now = datetime.now(timezone.utc)
        delta = now - record.clock_in
        total_hours = round(delta.total_seconds() / 3600, 2)
        overtime = max(0.0, round(total_hours - work_hours_per_day, 2))

        # Detect half-day
        current_status = record.status
        if total_hours < (work_hours_per_day / 2):
            current_status = "half_day"

        # Calculate productivity score
        productivity = self._calculate_productivity_score(
            tasks, data.day_rating, total_hours, work_hours_per_day
        )

        update_data = {
            "clock_out": now,
            "clock_out_lat": data.latitude,
            "clock_out_lng": data.longitude,
            "clock_out_location_name": data.location_name,
            "work_hours": total_hours,
            "overtime_hours": overtime,
            "status": current_status,
            "state": "completed",
            "notes": data.notes if data.notes else record.notes,
            "day_rating": data.day_rating,
            "rating_comment": data.rating_comment,
            "productivity_score": productivity,
        }
        record = await self.attendance_repo.update(record, update_data)
        await self.attendance_repo.commit()

        # Publish event (after commit — fire-and-forget)
        if self.event_publisher:
            company_id = self.attendance_repo.db.info.get("company_id")
            await self.event_publisher.publish("attendance.clock_out", {
                "company_id": str(company_id) if company_id else None,
                "employee_id": str(employee_id),
                "work_hours": total_hours,
                "overtime_hours": overtime,
                "day_rating": data.day_rating,
                "productivity_score": productivity,
                "timestamp": now.isoformat(),
            })

        logger.info(
            f"Clock-out: employee={employee_id}, hours={total_hours}, overtime={overtime}, "
            f"rating={data.day_rating}, productivity={productivity}",
            extra={"user_id": str(employee_id), "service_task": "clock_out"},
        )
        return record

    # ──────────── GET MY TODAY ────────────

    async def get_today_record(self, employee_id: UUID) -> Optional[AttendanceRecord]:
        return await self.attendance_repo.get_by_employee_and_date(employee_id, date.today())

    # ──────────── GET ALL SHIFTS TODAY ────────────

    async def get_today_shifts(
        self, employee_id: UUID, department_id: Optional[UUID] = None
    ) -> dict:
        """Return all shift records for today plus shift metadata."""
        today = date.today()
        shifts = await self.attendance_repo.get_all_shifts_today(employee_id, today)
        shift_count = len(shifts)

        # Resolve max_shifts_per_day from policy
        policy = await self.policy_repo.get_for_employee(employee_id, department_id)
        max_shifts = int(policy.max_shifts_per_day) if policy else 2

        # Can start a new shift if:
        # - all existing shifts are clocked out
        # - shift count < max_shifts
        all_closed = all(s.clock_out is not None for s in shifts) if shifts else True
        can_start_new_shift = all_closed and shift_count < max_shifts

        return {
            "shifts": shifts,
            "shift_count": shift_count,
            "max_shifts": max_shifts,
            "can_start_new_shift": can_start_new_shift,
        }

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

    # ──────────── MANUAL CORRECTION (Admin, optimistic lock) ────────────

    async def update_record(self, record_id: UUID, data: AttendanceUpdate) -> AttendanceRecord:
        """Update with optimistic locking to prevent silent overwrites from
        concurrent admin corrections."""
        record = await self.get_record(record_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No fields to update",
            )
        if "status" in update_data and update_data["status"] is not None:
            update_data["status"] = update_data["status"].value

        record = await self.attendance_repo.update_with_optimistic_lock(
            record, update_data, expected_version=record.version
        )
        await self.attendance_repo.commit()
        return record

    # ──────────── MANUAL ENTRY (Admin, idempotent) ────────────

    async def manual_entry(self, data: ManualAttendanceCreate, created_by: str) -> AttendanceRecord:
        """Idempotent manual entry.

        Uses SELECT FOR UPDATE to prevent race conditions, then catches
        IntegrityError as a safety net if two requests slip through.
        """
        from sqlalchemy.exc import IntegrityError

        company_id = self.attendance_repo.db.info.get("company_id")
        if company_id:
            await validate_employee_tenant(data.employee_id, company_id)

        # Locked check: prevents two concurrent manual entries from racing
        existing = await self.attendance_repo.get_by_employee_and_date_for_update(
            data.employee_id, data.date
        )
        if existing:
            await self.attendance_repo.commit()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Attendance record already exists for {data.date}",
            )

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

        try:
            record = await self.attendance_repo.create(record)
            await self.attendance_repo.commit()
        except IntegrityError:
            await self.attendance_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Attendance record already exists for {data.date}",
            )

        if self.event_publisher:
            await self.event_publisher.publish("attendance.manual_entry", {
                "company_id": str(company_id) if company_id else None,
                "employee_id": str(data.employee_id),
                "date": str(data.date),
                "created_by": created_by,
            })

        return record

    # ──────────── SCHOOL MODE (Admin/HR, idempotent) ────────────

    async def mark_school_mode_attendance(self, data: "SchoolModeAttendanceCreate", created_by: str) -> AttendanceRecord:
        """Idempotent school-mode attendance.

        Uses SELECT FOR UPDATE + IntegrityError catch to prevent duplicate
        records from concurrent bulk or individual marking.
        """
        from sqlalchemy.exc import IntegrityError

        company_id = self.attendance_repo.db.info.get("company_id")
        if company_id:
            await validate_employee_tenant(data.employee_id, company_id)

        today = date.today()

        # Locked check
        existing = await self.attendance_repo.get_by_employee_and_date_for_update(
            data.employee_id, today
        )
        if existing:
            await self.attendance_repo.commit()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Attendance record already exists for today",
            )

        now = datetime.now(timezone.utc)
        record = AttendanceRecord(
            employee_id=data.employee_id,
            clock_in=now,
            clock_out=now,
            work_hours=settings.DEFAULT_WORK_HOURS_PER_DAY if data.status.value in ["present", "late"] else 0,
            overtime_hours=0.0,
            status=data.status.value,
            method="school_mode",
            notes=data.notes,
            date=today,
        )

        try:
            record = await self.attendance_repo.create(record)
            await self.attendance_repo.commit()
        except IntegrityError:
            await self.attendance_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Attendance record already exists for today",
            )

        if self.event_publisher:
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

    # ──────────── ADMIN KPI DASHBOARD ────────────

    async def get_admin_kpi(self, target_date: Optional[date] = None) -> AdminKPIResponse:
        """Return top-level KPI summary for admin dashboard."""
        target = target_date or date.today()
        return await self.attendance_repo.get_admin_kpi(target)

    async def get_attendance_trend(self, days: int = 7) -> AttendanceTrendResponse:
        """Return attendance trend for the last N days."""
        items = await self.attendance_repo.get_attendance_trend(days)
        return AttendanceTrendResponse(items=items)

    async def get_daily_status_breakdown(self, target_date: Optional[date] = None) -> DailyStatusBreakdown:
        """Return status breakdown for a single day (pie chart data)."""
        target = target_date or date.today()
        return await self.attendance_repo.get_daily_status_breakdown(target)

    async def get_performers(self, year: int, month: int, limit: int = 5) -> PerformersResponse:
        """Return top and low performers for a month."""
        return await self.attendance_repo.get_performers(year, month, limit)

    # ──────────── STATE TRANSITION ────────────

    async def update_state(self, record_id: UUID, employee_id: UUID) -> AttendanceRecord:
        """Transition attendance state based on task count.

        Called after a task is added: PUNCHED_IN → PENDING_TASKS → ACTIVE.
        Commits the transaction so task creation + state change are atomic.
        """
        record = await self.attendance_repo.get_by_id(record_id)
        if not record or record.employee_id != employee_id:
            await self.attendance_repo.commit()
            return record

        tasks = await self.task_repo.get_by_record(record_id)
        new_state = record.state

        if record.state == "punched_in" and len(tasks) > 0:
            new_state = "active"
        elif record.state == "pending_tasks" and len(tasks) > 0:
            new_state = "active"

        if new_state != record.state:
            record = await self.attendance_repo.update(record, {"state": new_state})

        await self.attendance_repo.commit()
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
