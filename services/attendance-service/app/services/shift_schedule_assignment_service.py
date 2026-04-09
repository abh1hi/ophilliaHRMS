import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift_schedule_assignment import ShiftScheduleAssignment
from app.repositories.shift_schedule_assignment_repository import ShiftScheduleAssignmentRepository
from app.schemas.shift_schedule_assignment import ShiftScheduleAssignmentCreate

logger = logging.getLogger(__name__)


class ShiftScheduleAssignmentService:
    def __init__(self, db: AsyncSession):
        self.repo = ShiftScheduleAssignmentRepository(db)

    async def assign(self, data: ShiftScheduleAssignmentCreate) -> ShiftScheduleAssignment:
        existing = await self.repo.get_existing(data.schedule_id, data.employee_id)
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Employee already assigned to this schedule")
        result = await self.repo.assign(data.schedule_id, data.employee_id)
        logger.info("ShiftScheduleAssignment created: %s", result.id)
        return result

    async def get(self, assignment_id: UUID) -> ShiftScheduleAssignment:
        obj = await self.repo.get_by_id(assignment_id)
        if not obj:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Assignment {assignment_id} not found")
        return obj

    async def list_all(self, schedule_id: Optional[UUID] = None, employee_id: Optional[UUID] = None):
        return await self.repo.get_all(schedule_id=schedule_id, employee_id=employee_id)

    async def remove(self, assignment_id: UUID) -> None:
        obj = await self.get(assignment_id)
        await self.repo.delete(obj)
