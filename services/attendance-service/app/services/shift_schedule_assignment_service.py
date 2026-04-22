import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift_schedule_assignment import ShiftScheduleAssignment
from app.repositories.shift_schedule_assignment_repository import ShiftScheduleAssignmentRepository
from app.schemas.shift_schedule_assignment import ShiftScheduleAssignmentCreate, ShiftScheduleAssignmentUpdate
from app.repositories.shift_schedule_repository import ShiftScheduleRepository

logger = logging.getLogger(__name__)


class ShiftScheduleAssignmentService:
    def __init__(self, db: AsyncSession):
        self.repo = ShiftScheduleAssignmentRepository(db)
        self.schedule_repo = ShiftScheduleRepository(db)

    async def assign(self, data: ShiftScheduleAssignmentCreate) -> ShiftScheduleAssignment:
        schedule = await self.schedule_repo.get_by_id(data.schedule_id)
        if not schedule or schedule.is_active != 1:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="schedule_id must reference an active schedule")
        existing = await self.repo.get_existing(data.schedule_id, data.employee_id, data.effective_from)
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Employee already assigned to this schedule for the same effective date")
        if await self.repo.has_overlapping_assignment(data.employee_id, data.effective_from, data.effective_to):
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Employee already has an active schedule assignment for this date range")
        result = await self.repo.assign(
            data.schedule_id,
            data.employee_id,
            data.effective_from,
            data.effective_to,
            data.notes,
        )
        logger.info("ShiftScheduleAssignment created: %s", result.id)
        return result

    async def get(self, assignment_id: UUID) -> ShiftScheduleAssignment:
        obj = await self.repo.get_by_id(assignment_id)
        if not obj:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Assignment {assignment_id} not found")
        return obj

    async def list_all(self, schedule_id: Optional[UUID] = None, employee_id: Optional[UUID] = None):
        return await self.repo.get_all(schedule_id=schedule_id, employee_id=employee_id)

    async def update(self, assignment_id: UUID, data: ShiftScheduleAssignmentUpdate) -> ShiftScheduleAssignment:
        obj = await self.get(assignment_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update")
        if "schedule_id" in update_data:
            schedule = await self.schedule_repo.get_by_id(update_data["schedule_id"])
            if not schedule or schedule.is_active != 1:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="schedule_id must reference an active schedule")
        effective_from = update_data.get("effective_from", obj.effective_from)
        effective_to = update_data.get("effective_to", obj.effective_to)
        if effective_to is not None and effective_to < effective_from:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="effective_to must be on or after effective_from")
        if update_data.get("is_active", obj.is_active) == 1:
            if await self.repo.has_overlapping_assignment(obj.employee_id, effective_from, effective_to, exclude_id=obj.id):
                raise HTTPException(status.HTTP_409_CONFLICT, detail="Employee already has an active schedule assignment for this date range")
        return await self.repo.update(obj, update_data)

    async def remove(self, assignment_id: UUID) -> None:
        obj = await self.get(assignment_id)
        await self.repo.delete(obj)
