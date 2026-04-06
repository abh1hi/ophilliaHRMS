import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee_checkin import EmployeeCheckin
from app.repositories.employee_checkin_repository import EmployeeCheckinRepository
from app.repositories.shift_assignment_repository import ShiftAssignmentRepository
from app.schemas.employee_checkin import CheckinCreate, CheckinUpdate

logger = logging.getLogger(__name__)


class EmployeeCheckinService:
    def __init__(self, db: AsyncSession):
        self.repo = EmployeeCheckinRepository(db)
        self.shift_repo = ShiftAssignmentRepository(db)

    async def create(self, data: CheckinCreate) -> EmployeeCheckin:
        """Create a checkin log and attempt to auto-resolve shift_type_id."""
        checkin = EmployeeCheckin(
            employee_id=data.employee_id,
            log_datetime=data.log_datetime,
            log_type=data.log_type,
            device_id=data.device_id,
            shift_type_id=data.shift_type_id,
            latitude=data.latitude,
            longitude=data.longitude,
            location_name=data.location_name,
            skip_auto_attendance=data.skip_auto_attendance,
        )

        # Auto-resolve shift_type_id from active assignment if not provided
        if checkin.shift_type_id is None:
            target_date = data.log_datetime.date()
            try:
                assignments = await self.shift_repo.get_active_for_date(
                    data.employee_id, target_date
                )
                if assignments:
                    checkin.shift_type_id = assignments[0].shift_type_id
            except Exception:
                logger.debug("Could not resolve shift for checkin — storing without shift_type_id")

        return await self.repo.create(checkin)

    async def get(self, checkin_id: UUID) -> EmployeeCheckin:
        checkin = await self.repo.get_by_id(checkin_id)
        if not checkin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checkin log not found")
        return checkin

    async def list_all(
        self,
        employee_id: Optional[UUID] = None,
        from_dt: Optional[datetime] = None,
        to_dt: Optional[datetime] = None,
        log_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[EmployeeCheckin], int]:
        return await self.repo.get_all(employee_id, from_dt, to_dt, log_type, skip, limit)

    async def fetch_shift(self, checkin_id: UUID) -> EmployeeCheckin:
        """Re-resolve shift_type_id from the current active assignment for this checkin's date."""
        checkin = await self.get(checkin_id)
        target_date = checkin.log_datetime.date()
        try:
            assignments = await self.shift_repo.get_active_for_date(
                checkin.employee_id, target_date
            )
            if assignments:
                checkin = await self.repo.update(checkin, {"shift_type_id": assignments[0].shift_type_id})
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not resolve shift: {e}",
            )
        return checkin

    async def skip_toggle(self, checkin_id: UUID) -> EmployeeCheckin:
        """Toggle the skip_auto_attendance flag."""
        checkin = await self.get(checkin_id)
        new_val = 0 if checkin.skip_auto_attendance else 1
        return await self.repo.update(checkin, {"skip_auto_attendance": new_val})

    async def update(self, checkin_id: UUID, data: CheckinUpdate) -> EmployeeCheckin:
        checkin = await self.get(checkin_id)
        update_data = data.model_dump(exclude_none=True)
        return await self.repo.update(checkin, update_data)
