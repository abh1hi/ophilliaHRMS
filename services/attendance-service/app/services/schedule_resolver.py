from dataclasses import dataclass
from datetime import date, datetime, time, timezone, timedelta
from typing import Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.geofence_location import GeofenceLocation
from app.models.shift_schedule import ShiftSchedule
from app.models.shift_schedule_assignment import ShiftScheduleAssignment
from app.models.shift_type import ShiftType
from app.repositories.geofence_repository import GeofenceRepository
from app.repositories.shift_schedule_assignment_repository import ShiftScheduleAssignmentRepository
from app.repositories.shift_schedule_repository import ShiftScheduleRepository
from app.repositories.shift_type_repository import ShiftTypeRepository
from app.schemas.attendance import TodayScheduleResponse, ScheduleLocationResponse

IST = ZoneInfo("Asia/Kolkata")


def now_ist() -> datetime:
    """Current time in IST (UTC+5:30). All shift window comparisons use this."""
    return datetime.now(IST)


def to_ist(dt: datetime) -> datetime:
    return dt.astimezone(IST)


class ClockInStatus:
    """Possible clock-in statuses based on current time vs shift windows."""
    BEFORE_WINDOW = "before_window"      # before clock_in_start_time
    EARLY_IN = "early_in"                # in window, before shift start
    PRESENT = "present"                  # in window, within grace period
    LATE = "late"                        # in window, after grace period
    WINDOW_CLOSED = "window_closed"      # after clock_in_end_time, no HR approval
    HR_APPROVED = "hr_approved"          # after window, HR approval active


@dataclass
class ResolvedSchedule:
    assignment: ShiftScheduleAssignment
    schedule: ShiftSchedule
    shift_type: ShiftType
    clock_in_locations: list[GeofenceLocation]
    clock_out_locations: list[GeofenceLocation]
    target_date: date

    @property
    def scheduled_clock_in_at(self) -> datetime:
        # Shift times are stored in IST; combine with target_date in IST then convert to UTC
        dt_ist = datetime.combine(self.target_date, self.shift_type.start_time, tzinfo=IST)
        return dt_ist.astimezone(timezone.utc)

    @property
    def scheduled_clock_out_at(self) -> datetime:
        end_date = self.target_date
        if self.shift_type.end_time <= self.shift_type.start_time:
            end_date = end_date + timedelta(days=1)
        dt_ist = datetime.combine(end_date, self.shift_type.end_time, tzinfo=IST)
        return dt_ist.astimezone(timezone.utc)

    @property
    def auto_clock_out_at(self) -> datetime:
        auto_date = self.target_date
        if self.schedule.auto_clock_out_time <= self.schedule.clock_in_start_time:
            auto_date = auto_date + timedelta(days=1)
        dt_ist = datetime.combine(auto_date, self.schedule.auto_clock_out_time, tzinfo=IST)
        return dt_ist.astimezone(timezone.utc)

    def grace_end_time(self) -> time:
        """Time (IST) at which late marking begins: shift_start + grace_period_minutes."""
        shift_start_dt = datetime.combine(self.target_date, self.shift_type.start_time, tzinfo=IST)
        grace_end_dt = shift_start_dt + timedelta(minutes=self.shift_type.grace_period_minutes)
        return grace_end_dt.timetz()

    def is_off_day(self, check_date: date) -> bool:
        """Return True if check_date is an off day per the schedule's off_days list."""
        if not self.schedule.off_days:
            return False
        weekday_name = check_date.strftime("%A").lower()
        return weekday_name in [d.lower() for d in self.schedule.off_days]


class ScheduleResolver:
    def __init__(self, db: AsyncSession):
        self.assignment_repo = ShiftScheduleAssignmentRepository(db)
        self.schedule_repo = ShiftScheduleRepository(db)
        self.shift_type_repo = ShiftTypeRepository(db)
        self.geofence_repo = GeofenceRepository(db)

    async def resolve_for_employee(
        self,
        employee_id: UUID,
        target_date: Optional[date] = None,
        *,
        required: bool = True,
    ) -> Optional[ResolvedSchedule]:
        target = target_date or date.today()
        assignment = await self.assignment_repo.get_active_for_date(employee_id, target)
        if not assignment:
            if required:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="No active attendance schedule is assigned for today. Contact HR/Admin.",
                )
            return None

        schedule = await self.schedule_repo.get_by_id(assignment.schedule_id)
        if not schedule or schedule.is_active != 1:
            if required:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Assigned attendance schedule is inactive or unavailable. Contact HR/Admin.",
                )
            return None

        shift_type = await self.shift_type_repo.get_by_id(schedule.shift_type_id)
        if not shift_type or not shift_type.is_active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Assigned schedule references an inactive shift type. Contact HR/Admin.",
            )

        clock_in_locations = await self.geofence_repo.get_by_ids(
            [UUID(str(x)) for x in schedule.allowed_clock_in_location_ids or []]
        )
        clock_out_locations = await self.geofence_repo.get_by_ids(
            [UUID(str(x)) for x in schedule.allowed_clock_out_location_ids or []]
        )
        if not clock_in_locations:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Assigned schedule has no active clock-in locations. Contact HR/Admin.",
            )
        if not clock_out_locations:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Assigned schedule has no active clock-out locations. Contact HR/Admin.",
            )

        return ResolvedSchedule(
            assignment=assignment,
            schedule=schedule,
            shift_type=shift_type,
            clock_in_locations=clock_in_locations,
            clock_out_locations=clock_out_locations,
            target_date=target,
        )

    async def resolve_by_schedule_id(
        self,
        schedule_id: UUID,
        target_date: date,
        *,
        assignment: Optional[ShiftScheduleAssignment] = None,
    ) -> ResolvedSchedule:
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Attendance record references a schedule that no longer exists.",
            )
        shift_type = await self.shift_type_repo.get_by_id(schedule.shift_type_id)
        if not shift_type:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Attendance record schedule references a shift type that no longer exists.",
            )
        clock_in_locations = await self.geofence_repo.get_by_ids(
            [UUID(str(x)) for x in schedule.allowed_clock_in_location_ids or []]
        )
        clock_out_locations = await self.geofence_repo.get_by_ids(
            [UUID(str(x)) for x in schedule.allowed_clock_out_location_ids or []]
        )
        if assignment is None:
            assignment = ShiftScheduleAssignment(
                schedule_id=schedule.id,
                employee_id=UUID(int=0),
                effective_from=target_date,
            )
        return ResolvedSchedule(
            assignment=assignment,
            schedule=schedule,
            shift_type=shift_type,
            clock_in_locations=clock_in_locations,
            clock_out_locations=clock_out_locations,
            target_date=target_date,
        )

    @staticmethod
    def is_within_window(now_time: time, start: time, end: time) -> bool:
        if start <= end:
            return start <= now_time <= end
        return now_time >= start or now_time <= end

    def get_clock_in_status(
        self,
        resolved: ResolvedSchedule,
        now: datetime,
        hr_approved_until: Optional[datetime] = None,
    ) -> str:
        """Return one of ClockInStatus values based on current IST time vs schedule windows."""
        now_ist_dt = to_ist(now)
        now_time = now_ist_dt.time()
        target_date = resolved.target_date

        window_start = resolved.schedule.clock_in_start_time
        window_end = resolved.schedule.clock_in_end_time
        shift_start = resolved.shift_type.start_time
        grace_end = resolved.grace_end_time()

        in_window = self.is_within_window(now_time, window_start, window_end)

        if not in_window:
            # Check if we're before window start or after window end
            if self.is_within_window(now_time, time(0, 0), window_start) and now_time < window_start:
                return ClockInStatus.BEFORE_WINDOW
            # After window: check HR approval
            if hr_approved_until and now.astimezone(timezone.utc) <= hr_approved_until.astimezone(timezone.utc):
                return ClockInStatus.HR_APPROVED
            return ClockInStatus.WINDOW_CLOSED

        # Inside window — determine specific status
        if now_time < shift_start:
            return ClockInStatus.EARLY_IN
        if now_time <= grace_end.replace(tzinfo=None):
            return ClockInStatus.PRESENT
        return ClockInStatus.LATE

    def require_clock_in_window(
        self,
        resolved: ResolvedSchedule,
        now: datetime,
        hr_approved_until: Optional[datetime] = None,
    ) -> str:
        """Validate clock-in is allowed; return clock-in status or raise 422.

        Returns the ClockInStatus string so caller knows what status to record.
        """
        clock_in_status = self.get_clock_in_status(resolved, now, hr_approved_until)

        if clock_in_status == ClockInStatus.BEFORE_WINDOW:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Too early. Clock-in window opens at "
                    f"{resolved.schedule.clock_in_start_time.strftime('%I:%M %p')} IST."
                ),
            )
        if clock_in_status == ClockInStatus.WINDOW_CLOSED:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Clock-in window has closed. "
                    "Please submit a late arrival request for HR approval."
                ),
            )

        return clock_in_status

    def check_clock_out_early(self, resolved: ResolvedSchedule, now: datetime) -> bool:
        """Return True if clock-out is before the clock-out window (early out)."""
        now_time = to_ist(now).time()
        return now_time < resolved.schedule.clock_out_start_time

    def require_clock_out_window(self, resolved: ResolvedSchedule, now: datetime) -> None:
        """For normal clock-out validation (not early-out path). Raises 422 if after window."""
        now_time = to_ist(now).time()
        if not self.is_within_window(
            now_time,
            resolved.schedule.clock_out_start_time,
            resolved.schedule.clock_out_end_time,
        ):
            # Allow early clock-out (handled separately); only block if after window
            if now_time > resolved.schedule.clock_out_end_time:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Clock-out window has passed. Your attendance may have been auto-closed."
                    ),
                )

    def to_today_response(self, resolved: ResolvedSchedule, now: Optional[datetime] = None) -> TodayScheduleResponse:
        current = now or datetime.now(timezone.utc)
        current_ist_time = to_ist(current).time()
        can_clock_in = self.is_within_window(
            current_ist_time,
            resolved.schedule.clock_in_start_time,
            resolved.schedule.clock_in_end_time,
        )
        can_clock_out = self.is_within_window(
            current_ist_time,
            resolved.schedule.clock_out_start_time,
            resolved.schedule.clock_out_end_time,
        )
        ci_status = self.get_clock_in_status(resolved, current)
        off_day = resolved.is_off_day(resolved.target_date)
        return TodayScheduleResponse(
            schedule_id=resolved.schedule.id,
            schedule_name=resolved.schedule.name,
            shift_type_id=resolved.shift_type.id,
            shift_type_name=resolved.shift_type.name,
            date=resolved.target_date,
            clock_in_start_time=resolved.schedule.clock_in_start_time,
            clock_in_end_time=resolved.schedule.clock_in_end_time,
            clock_out_start_time=resolved.schedule.clock_out_start_time,
            clock_out_end_time=resolved.schedule.clock_out_end_time,
            auto_clock_out_time=resolved.schedule.auto_clock_out_time,
            tasks_mandatory=resolved.schedule.tasks_mandatory,
            allowed_clock_in_locations=[ScheduleLocationResponse.model_validate(x) for x in resolved.clock_in_locations],
            allowed_clock_out_locations=[ScheduleLocationResponse.model_validate(x) for x in resolved.clock_out_locations],
            can_clock_in_now=can_clock_in,
            can_clock_out_now=can_clock_out,
            clock_in_status_reason=None if can_clock_in else "Current time is outside the schedule clock-in window.",
            clock_out_status_reason=None if can_clock_out else "Current time is outside the schedule clock-out window.",
            clock_in_status=ci_status,
            is_off_day=off_day,
            shift_start_time=resolved.shift_type.start_time,
            shift_end_time=resolved.shift_type.end_time,
            grace_period_minutes=resolved.shift_type.grace_period_minutes,
        )
