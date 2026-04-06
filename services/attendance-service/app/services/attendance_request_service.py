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
            await self._create_attendance_records(req)

        return await self.repo.update(req, update_data)

    async def _create_attendance_records(self, req: AttendanceRequest) -> None:
        """For each date in the approved range, create/upsert an AttendanceRecord."""
        from sqlalchemy.exc import IntegrityError

        company_id = self.attendance_repo._company_id
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
