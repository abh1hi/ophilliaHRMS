import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift_type import ShiftType
from app.repositories.shift_type_repository import ShiftTypeRepository
from app.schemas.shift_type import ShiftTypeCreate, ShiftTypeUpdate

logger = logging.getLogger(__name__)


class ShiftTypeService:
    def __init__(self, db: AsyncSession, publisher=None):
        self.repo = ShiftTypeRepository(db)
        self.publisher = publisher

    async def create(self, data: ShiftTypeCreate) -> ShiftType:
        if await self.repo.get_by_name(data.name):
            raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Shift type '{data.name}' already exists")
        shift_type = ShiftType(
            name=data.name,
            start_time=data.start_time,
            end_time=data.end_time,
            break_minutes=data.break_minutes,
            grace_period_minutes=data.grace_period_minutes,
            is_overnight=data.is_overnight,
            color_code=data.color_code,
            description=data.description,
        )
        result = await self.repo.create(shift_type)
        logger.info("ShiftType created: %s", result.id)

        if self.publisher:
            await self.publisher.publish("shifttype.created", {
                "id": str(result.id),
                "company_id": str(result.company_id),
                "name": result.name,
                "start_time": result.start_time.isoformat() if result.start_time else None,
                "end_time": result.end_time.isoformat() if result.end_time else None,
                "break_minutes": result.break_minutes,
                "grace_period_minutes": result.grace_period_minutes,
                "is_overnight": bool(result.is_overnight),
                "color_code": result.color_code,
                "description": result.description,
            })

        return result

    async def get(self, shift_type_id: UUID) -> ShiftType:
        obj = await self.repo.get_by_id(shift_type_id)
        if not obj:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Shift type {shift_type_id} not found")
        return obj

    async def list_all(self, include_inactive: bool = False):
        return await self.repo.get_all(include_inactive=include_inactive)

    async def update(self, shift_type_id: UUID, data: ShiftTypeUpdate) -> ShiftType:
        obj = await self.get(shift_type_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update")
        if "name" in update_data:
            existing = await self.repo.get_by_name(update_data["name"])
            if existing and existing.id != shift_type_id:
                raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Shift type '{update_data['name']}' already exists")
        result = await self.repo.update(obj, update_data)

        if self.publisher:
            await self.publisher.publish("shifttype.updated", {
                "id": str(result.id),
                "company_id": str(result.company_id),
                "name": result.name,
                "start_time": result.start_time.isoformat() if result.start_time else None,
                "end_time": result.end_time.isoformat() if result.end_time else None,
                "break_minutes": result.break_minutes,
                "grace_period_minutes": result.grace_period_minutes,
                "is_overnight": bool(result.is_overnight),
                "color_code": result.color_code,
                "description": result.description,
                "is_active": bool(result.is_active),
            })
        return result

    async def soft_delete(self, shift_type_id: UUID) -> ShiftType:
        obj = await self.get(shift_type_id)
        result = await self.repo.update(obj, {"is_active": 0})

        if self.publisher:
            await self.publisher.publish("shifttype.updated", {
                "id": str(result.id),
                "company_id": str(result.company_id),
                "is_active": False,
            })
        return result
