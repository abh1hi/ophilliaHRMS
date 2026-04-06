import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift_assignment import ShiftAssignment
from app.repositories.shift_assignment_repository import ShiftAssignmentRepository
from app.schemas.shift_assignment import ShiftAssignmentCreate, ShiftAssignmentUpdate

logger = logging.getLogger(__name__)


class ShiftAssignmentService:
    def __init__(self, db: AsyncSession):
        self.repo = ShiftAssignmentRepository(db)

    async def create(self, data: ShiftAssignmentCreate) -> ShiftAssignment:
        assignment = ShiftAssignment(
            employee_id=data.employee_id,
            shift_type_id=data.shift_type_id,
            shift_location_id=data.shift_location_id,
            effective_from=data.effective_from,
            effective_to=data.effective_to,
            notes=data.notes,
        )
        result = await self.repo.create(assignment)
        logger.info("ShiftAssignment created: %s", result.id)
        return result

    async def get(self, assignment_id: UUID) -> ShiftAssignment:
        obj = await self.repo.get_by_id(assignment_id)
        if not obj:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Shift assignment {assignment_id} not found")
        return obj

    async def list_all(self, employee_id: Optional[UUID] = None, include_inactive: bool = False):
        return await self.repo.get_all(employee_id=employee_id, include_inactive=include_inactive)

    async def update(self, assignment_id: UUID, data: ShiftAssignmentUpdate) -> ShiftAssignment:
        obj = await self.get(assignment_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update")
        return await self.repo.update(obj, update_data)

    async def soft_delete(self, assignment_id: UUID) -> ShiftAssignment:
        obj = await self.get(assignment_id)
        return await self.repo.update(obj, {"is_active": 0})
