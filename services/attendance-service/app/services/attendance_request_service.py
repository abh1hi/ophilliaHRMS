import logging
from typing import Optional, List
from uuid import UUID
from datetime import date, timedelta, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_request import AttendanceRequest
from app.models.attendance_record import AttendanceRecord
from app.repositories.attendance_request_repository import AttendanceRequestRepository
from app.repositories.attendance_repository import AttendanceRepository
from app.schemas.attendance_request import AttendanceRequestCreate, AttendanceRequestReview

LATE_CLOCKIN_APPROVAL_MINUTES = 10

logger = logging.getLogger(__name__)


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AttendanceRequestService:
    def __init__(self, db: AsyncSession):
        self.repo = AttendanceRequestRepository(db)
        self.attendance_repo = AttendanceRepository(db)

    async def create(self, data: AttendanceRequestCreate) -> AttendanceRequest:
        if data.from_date > data.to_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="from_date must be on or before to_date",
            )
        request = AttendanceRequest(
            employee_id=data.employee_id,
            from_date=data.from_date,
            to_date=data.to_date,
            reason=data.reason,
            explanation=data.explanation,
            include_holidays=data.include_holidays,
            half_day=data.half_day,
            half_day_date=data.half_day_date,
            status="pending",
        )
        return await self.repo.create(request)

    async def get(self, request_id: UUID) -> AttendanceRequest:
        req = await self.repo.get_by_id(request_id)
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance request not found")
        return req

    async def list_all(
        self,
        employee_id: Optional[UUID] = None,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[AttendanceRequest], int]:
        return await self.repo.get_all(employee_id, status_filter, skip, limit)

    async def cancel(self, request_id: UUID) -> AttendanceRequest:
        req = await self.get(request_id)
        if req.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot cancel a request with status '{req.status}'",
            )
        return await self.repo.update(req, {"status": "cancelled"})

    async def review(
        self, request_id: UUID, data: AttendanceRequestReview, reviewed_by: UUID
    ) -> AttendanceRequest:
        req = await self.get(request_id)
        if req.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot review a request with status '{req.status}'",
            )

        update_data = {
            "status": data.status,
            "reviewed_by": reviewed_by,
            "reviewed_at": naive_utcnow(),
            "review_note": data.review_note,
        }

        if data.status == "approved":
            request_type = getattr(req, "request_type", "regularization")

            if request_type == "late_clockin":
                await self._approve_late_clockin(req, data)
            elif request_type == "off_day_work":
                update_data["off_day_work_type"] = getattr(data, "off_day_work_type", None)
                update_data["off_day_ot_rate"] = getattr(data, "off_day_ot_rate", None)
                await self._approve_off_day_work(req, data)
            else:
                await self._create_attendance_records(req)

        return await self.repo.update(req, update_data)

    async def _approve_late_clockin(self, req: AttendanceRequest, data: AttendanceRequestReview) -> None:
        """Set a 10-minute approval window on the employee's attendance record for today."""
        from datetime import timezone as tz

        target_date = req.for_date or req.from_date
        window_until = datetime.now(tz.utc) + timedelta(minutes=LATE_CLOCKIN_APPROVAL_MINUTES)
        mark_as = getattr(data, "mark_as", "normal_with_late_flag") or "normal_with_late_flag"

        existing = await self.attendance_repo.get_by_employee_and_date(req.employee_id, target_date)
        if existing:
            await self.attendance_repo.update(existing, {
                "hr_approved_late_clockin_until": window_until,
                "late_clockin_mark_as": mark_as,
            })
        else:
            # Create a placeholder record that clock_in will populate
            record = AttendanceRecord(
                employee_id=req.employee_id,
                schedule_id=None,
                clock_in=datetime.now(tz.utc),
                clock_out=datetime.now(tz.utc),
                hr_approved_late_clockin_until=window_until,
                late_clockin_mark_as=mark_as,
                status="absent",
                state="completed",
                method="request_approved",
                notes="Placeholder for HR-approved late clock-in",
                date=target_date,
                shift_number=1,
            )
            try:
                await self.attendance_repo.create(record)
                await self.attendance_repo.commit()
            except Exception:
                await self.attendance_repo.rollback()

    async def _approve_off_day_work(self, req: AttendanceRequest, data: AttendanceRequestReview) -> None:
        """Create an attendance record for off-day work approval."""
        from sqlalchemy.exc import IntegrityError
        from datetime import timezone as tz

        target_date = req.for_date or req.from_date
        work_type = getattr(data, "off_day_work_type", "normal") or "normal"
        ot_rate = getattr(data, "off_day_ot_rate", None)

        clock_in_dt = datetime(target_date.year, target_date.month, target_date.day, 9, 0, 0, tzinfo=tz.utc)
        record = AttendanceRecord(
            employee_id=req.employee_id,
            clock_in=clock_in_dt,
            clock_out=None,
            work_hours=None,
            overtime_hours=0.0,
            status="present",
            method="request_approved",
            notes=f"Off-day work approved: {req.explanation or req.reason}",
            date=target_date,
            state="punched_in",
            is_off_day_work=True,
            off_day_work_type=work_type,
            off_day_ot_rate=ot_rate,
            shift_number=1,
        )
        try:
            await self.attendance_repo.create(record)
            await self.attendance_repo.commit()
        except IntegrityError:
            await self.attendance_repo.rollback()
            logger.debug(f"Off-day work record already exists for employee={req.employee_id} date={target_date}")

    async def _create_attendance_records(self, req: AttendanceRequest) -> None:
        """For each date in the approved range, create/upsert an AttendanceRecord."""
        from sqlalchemy.exc import IntegrityError

        cursor = req.from_date
        end = req.to_date

        while cursor <= end:
            # Skip weekends when include_holidays=0 (Saturday=5, Sunday=6)
            if req.include_holidays == 0 and cursor.weekday() >= 5:
                cursor += timedelta(days=1)
                continue

            # Determine if this is a half day
            is_half = bool(req.half_day and req.half_day_date and cursor == req.half_day_date)

            # Build a minimal clock_in (midnight UTC for the date — admin manual entry)
            from datetime import datetime, timezone
            clock_in_dt = datetime(cursor.year, cursor.month, cursor.day, 9, 0, 0,
                                   tzinfo=timezone.utc)

            record = AttendanceRecord(
                employee_id=req.employee_id,
                clock_in=clock_in_dt,
                clock_out=None,
                work_hours=4.0 if is_half else 8.0,
                overtime_hours=0.0,
                status="half_day" if is_half else "present",
                method="request_approved",
                notes=f"Approved attendance request: {req.reason}",
                date=cursor,
                state="completed",
            )

            try:
                await self.attendance_repo.create(record)
                await self.attendance_repo.commit()
            except IntegrityError:
                await self.attendance_repo.rollback()
                logger.debug(
                    f"Attendance record already exists for employee={req.employee_id} date={cursor} — skipping"
                )

            cursor += timedelta(days=1)
