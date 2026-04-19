import logging
from typing import Optional
from uuid import UUID
from datetime import date, datetime, timezone, time, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_record import AttendanceRecord
from app.models.geofence_location import GeofenceLocation
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
from app.core.config import settings
from app.core.employee_validator import validate_employee_tenant
from app.services.policy_resolver import PolicyResolver
from app.services.geofence_validator import GeofenceValidator
from app.services.overtime_calculator import OvertimeCalculator
from app.repositories.overtime_policy_repository import OvertimePolicyRepository
from app.repositories.shift_type_repository import ShiftTypeRepository
from app.repositories.holiday_calendar_repository import HolidayCalendarRepository
from app.repositories.geofence_consent_repository import GeofenceConsentRepository

logger = logging.getLogger(__name__)


class AttendanceService:
    """Orchestrates clock-in/out, manual entry, and reporting.

    Delegates policy resolution to PolicyResolver, geofence checks to
    GeofenceValidator, and overtime math to OvertimeCalculator.
    """

    def __init__(self, db: AsyncSession, event_publisher: Optional[EventPublisher] = None):
        self.attendance_repo = AttendanceRepository(db)
        self.geofence_repo = GeofenceRepository(db)
        self.policy_repo = PolicyRepository(db)
        self.task_repo = TaskRepository(db)
        self.event_publisher = event_publisher
        self._policy_resolver = PolicyResolver(db)
        self._geofence_validator = GeofenceValidator()
        self._ot_calculator = OvertimeCalculator()
        self._ot_policy_repo = OvertimePolicyRepository(db)
        self._shift_type_repo = ShiftTypeRepository(db)
        self._holiday_repo = HolidayCalendarRepository(db)
        self._consent_repo = GeofenceConsentRepository(db)

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
        method, geofences, work_hours, work_start, late_grace, _ = await self._policy_resolver.resolve(
            employee_id, department_id
        )
        self._geofence_validator.validate(method, geofences, data.latitude, data.longitude, data.accuracy_meters)
        await self._assert_geofence_consent(employee_id, method)

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

    # ──────────── OVERTIME PARAMS ────────────

    async def _resolve_ot_params(
        self, employee_id: UUID, department_id: Optional[UUID]
    ) -> tuple[float, float, bool, float]:
        """Return (daily_ot_threshold, daily_ot_multiplier, is_holiday, holiday_multiplier).

        Priority for threshold:
          1. Assigned ShiftType.work_hours_per_day  (shift-aware OT)
          2. OvertimePolicy.daily_ot_threshold_hours
          3. Hard default 8.0
        """
        ot_policy = await self._ot_policy_repo.get_for_employee(employee_id, department_id=department_id)
        threshold = ot_policy.daily_ot_threshold_hours if ot_policy else 8.0
        multiplier = ot_policy.daily_ot_multiplier if ot_policy else 1.0
        holiday_mult = ot_policy.holiday_multiplier if ot_policy else 2.0

        # Shift-aware: override threshold with actual shift hours when assigned
        shift = await self._shift_type_repo.get_active_for_employee(employee_id)
        if shift:
            threshold = shift.work_hours_per_day

        # Holiday detection: location-aware calendar lookup
        company_id = self.attendance_repo.db.info.get("company_id")
        if company_id:
            from uuid import UUID as _UUID
            holiday = await self._holiday_repo.get_for_date(
                _UUID(company_id) if isinstance(company_id, str) else company_id,
                date.today(),
            )
        else:
            holiday = None

        return threshold, multiplier, holiday is not None, holiday_mult

    async def _assert_geofence_consent(self, employee_id: UUID, method: str) -> None:
        """Raise HTTP 451 if employee hasn't consented to geofence tracking (GDPR)."""
        if method not in ("geofence", "both"):
            return
        consent = await self._consent_repo.get_for_employee(employee_id)
        if not consent or not consent.consented:
            raise HTTPException(
                status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
                detail=(
                    "Geofence-based attendance requires your explicit consent to location tracking. "
                    "Submit consent at POST /api/v1/attendance/geofence/consent before clocking in."
                ),
            )

    # ──────────── NIGHT SHIFT CHECK ────────────

    @staticmethod
    def _check_night_shift(record: "AttendanceRecord", allow_night_shift: bool) -> None:
        """Reject clock-out if the shift spans midnight but night shifts are disabled."""
        now = datetime.now(timezone.utc)
        if record.clock_in.date() != now.date() and not allow_night_shift:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Night shifts (shifts spanning midnight) are not allowed by your attendance policy. "
                    "Contact your administrator if this is incorrect."
                ),
            )

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
        method, geofences, work_hours_per_day, _, _, allow_night_shift = await self._policy_resolver.resolve(
            employee_id, department_id
        )
        self._geofence_validator.validate(method, geofences, data.latitude, data.longitude)
        self._check_night_shift(record, allow_night_shift)

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

        # Compute work hours, overtime, and half-day/holiday status
        now = datetime.now(timezone.utc)
        ot_threshold, ot_multiplier, is_holiday, holiday_mult = await self._resolve_ot_params(
            employee_id, department_id
        )
        total_hours, overtime, status_update = self._ot_calculator.compute(
            record.clock_in, now, work_hours_per_day,
            ot_threshold, ot_multiplier, is_holiday, holiday_mult,
        )
        current_status = status_update if status_update else record.status

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

        # Publish events (after commit — fire-and-forget)
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
            if overtime > 0:
                await self.event_publisher.publish("attendance.overtime_flagged", {
                    "company_id": str(company_id) if company_id else None,
                    "employee_id": str(employee_id),
                    "record_id": str(record.id),
                    "overtime_hours": overtime,
                    "timestamp": now.isoformat(),
                })
            if overtime > 0 or is_holiday:
                await self.event_publisher.publish("payroll.adjustment_required", {
                    "company_id": str(company_id) if company_id else None,
                    "employee_id": str(employee_id),
                    "record_id": str(record.id),
                    "date": str(date.today()),
                    "adjustment_type": "holiday_work" if is_holiday else "overtime",
                    "hours": total_hours if is_holiday else overtime,
                    "multiplier": holiday_mult if is_holiday else ot_multiplier,
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

        first_task_added = record.state == "punched_in" and len(tasks) > 0
        if first_task_added:
            new_state = "active"
            await self._flag_late_task_entry(record)
        elif record.state == "pending_tasks" and len(tasks) > 0:
            new_state = "active"

        if new_state != record.state:
            record = await self.attendance_repo.update(record, {"state": new_state})

        await self.attendance_repo.commit()
        return record

    async def _flag_late_task_entry(self, record: "AttendanceRecord") -> None:
        """Flag the record if the first task was added past the grace window."""
        policy = await self.policy_repo.get_for_employee(record.employee_id, None)
        grace_minutes = policy.task_planning_grace_minutes if policy else 30.0
        elapsed = (datetime.now(timezone.utc) - record.clock_in).total_seconds() / 60
        if elapsed > grace_minutes:
            flag = f" [LATE_TASK_ENTRY: {int(elapsed)}m after clock-in, grace={int(grace_minutes)}m]"
            await self.attendance_repo.update(record, {"notes": (record.notes or "") + flag})
            logger.info(
                f"Late task entry flagged: employee={record.employee_id}, elapsed={elapsed:.1f}m, grace={grace_minutes}m",
                extra={"user_id": str(record.employee_id), "service_task": "task_grace"},
            )

    # ──────────── CSV TEMPLATE ────────────

    def get_csv_template(self) -> bytes:
        """Return a CSV template file with headers and one example row."""
        lines = [
            "employee_id,date,status,clock_in,clock_out,notes",
            "00000000-0000-0000-0000-000000000001,2026-04-01,present,09:00,18:00,On-site",
        ]
        return "\n".join(lines).encode("utf-8")

    # ──────────── CSV UPLOAD ────────────

    async def upload_csv(self, file_bytes: bytes, created_by: str) -> dict:
        """Parse an attendance CSV and bulk-create records.

        CSV columns: employee_id, date, status, clock_in, clock_out, notes
        Returns: {total, succeeded, failed, errors}
        """
        import csv
        import io
        from datetime import datetime, timezone
        from app.schemas.attendance import ManualAttendanceCreate, AttendanceStatus

        reader = csv.DictReader(io.StringIO(file_bytes.decode("utf-8-sig")))
        total = 0
        succeeded = 0
        errors = []

        for row_num, row in enumerate(reader, start=2):
            total += 1
            try:
                emp_id = UUID(row["employee_id"].strip())
                record_date = date.fromisoformat(row["date"].strip())

                # Parse optional times — treat as UTC noon to avoid date-shift issues
                def _parse_dt(time_str: str) -> Optional[datetime]:
                    if not time_str or not time_str.strip():
                        return None
                    h, m = [int(x) for x in time_str.strip().split(":")]
                    return datetime(record_date.year, record_date.month, record_date.day,
                                    h, m, 0, tzinfo=timezone.utc)

                clock_in = _parse_dt(row.get("clock_in", ""))
                clock_out = _parse_dt(row.get("clock_out", ""))

                if clock_in is None:
                    clock_in = datetime(record_date.year, record_date.month, record_date.day,
                                        9, 0, 0, tzinfo=timezone.utc)

                raw_status = row.get("status", "present").strip()
                try:
                    att_status = AttendanceStatus(raw_status)
                except ValueError:
                    att_status = AttendanceStatus.present

                entry = ManualAttendanceCreate(
                    employee_id=emp_id,
                    date=record_date,
                    clock_in=clock_in,
                    clock_out=clock_out,
                    status=att_status,
                    notes=row.get("notes", "").strip() or None,
                )
                await self.manual_entry(entry, created_by)
                succeeded += 1
            except Exception as exc:
                errors.append({"row": row_num, "error": str(exc)})

        return {
            "total": total,
            "succeeded": succeeded,
            "failed": total - succeeded,
            "errors": errors,
        }

    # ──────────── EMPLOYEE FILTER PROXY ────────────

    async def get_employees_by_dept_branch(
        self,
        token: str,
        department_id: Optional[UUID] = None,
        branch_id: Optional[UUID] = None,
    ) -> list:
        """Proxy to employee-service: list employees filtered by dept/branch."""
        from app.core.http_client import get_http_client

        params = {}
        if department_id:
            params["department_id"] = str(department_id)
        if branch_id:
            params["branch_id"] = str(branch_id)
        params["limit"] = "200"

        async with get_http_client(headers={
            "Authorization": f"Bearer {token}",
            "X-Internal-Token": settings.INTERNAL_SERVICE_TOKEN,
        }) as client:
            resp = await client.get(
                f"{settings.EMPLOYEE_SERVICE_URL}/api/v1/employees",
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()
            # Unwrap envelope: {success, data: {employees: [...]}}
            if isinstance(data, dict) and "data" in data:
                inner = data["data"]
                if isinstance(inner, dict) and "employees" in inner:
                    return inner["employees"]
                return inner if isinstance(inner, list) else []
            return data if isinstance(data, list) else []


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
