import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift_schedule import ShiftSchedule
from app.repositories.shift_schedule_repository import ShiftScheduleRepository
from app.schemas.shift_schedule import ShiftScheduleCreate, ShiftScheduleUpdate

logger = logging.getLogger(__name__)


class ShiftScheduleService:
    def __init__(self, db: AsyncSession):
        self.repo = ShiftScheduleRepository(db)

    async def create(self, data: ShiftScheduleCreate) -> ShiftSchedule:
        if await self.repo.get_by_name(data.name):
            raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Shift schedule '{data.name}' already exists")
        schedule = ShiftSchedule(
            name=data.name,
            description=data.description,
            effective_from=data.effective_from,
            effective_to=data.effective_to,
        )
        result = await self.repo.create(schedule)
        logger.info("ShiftSchedule created: %s", result.id)
        return result

    async def get(self, schedule_id: UUID) -> ShiftSchedule:
        obj = await self.repo.get_by_id(schedule_id)
        if not obj:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Shift schedule {schedule_id} not found")
        return obj

    async def list_all(self, include_inactive: bool = False):
        return await self.repo.get_all(include_inactive=include_inactive)

    async def update(self, schedule_id: UUID, data: ShiftScheduleUpdate) -> ShiftSchedule:
        obj = await self.get(schedule_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update")
        if "name" in update_data:
            existing = await self.repo.get_by_name(update_data["name"])
            if existing and existing.id != schedule_id:
                raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Shift schedule '{update_data['name']}' already exists")
        return await self.repo.update(obj, update_data)

    async def soft_delete(self, schedule_id: UUID) -> ShiftSchedule:
        obj = await self.get(schedule_id)
        return await self.repo.update(obj, {"is_active": 0})
