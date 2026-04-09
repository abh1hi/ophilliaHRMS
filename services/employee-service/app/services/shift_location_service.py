import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift_location import ShiftLocation
from app.repositories.shift_location_repository import ShiftLocationRepository
from app.schemas.shift_location import ShiftLocationCreate, ShiftLocationUpdate

logger = logging.getLogger(__name__)


class ShiftLocationService:
    def __init__(self, db: AsyncSession):
        self.repo = ShiftLocationRepository(db)

    async def create(self, data: ShiftLocationCreate) -> ShiftLocation:
        if await self.repo.get_by_name(data.name):
            raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Shift location '{data.name}' already exists")
        location = ShiftLocation(
            name=data.name,
            address=data.address,
            latitude=data.latitude,
            longitude=data.longitude,
            radius_meters=data.radius_meters,
        )
        result = await self.repo.create(location)
        logger.info("ShiftLocation created: %s", result.id)
        return result

    async def get(self, location_id: UUID) -> ShiftLocation:
        obj = await self.repo.get_by_id(location_id)
        if not obj:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Shift location {location_id} not found")
        return obj

    async def list_all(self, include_inactive: bool = False):
        return await self.repo.get_all(include_inactive=include_inactive)

    async def update(self, location_id: UUID, data: ShiftLocationUpdate) -> ShiftLocation:
        obj = await self.get(location_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update")
        if "name" in update_data:
            existing = await self.repo.get_by_name(update_data["name"])
            if existing and existing.id != location_id:
                raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Shift location '{update_data['name']}' already exists")
        return await self.repo.update(obj, update_data)

    async def soft_delete(self, location_id: UUID) -> ShiftLocation:
        obj = await self.get(location_id)
        return await self.repo.update(obj, {"is_active": 0})
