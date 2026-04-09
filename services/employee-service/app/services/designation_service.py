import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.designation import Designation
from app.repositories.designation_repository import DesignationRepository
from app.schemas.designation import DesignationCreate, DesignationUpdate

logger = logging.getLogger(__name__)


class DesignationService:
    def __init__(self, db: AsyncSession):
        self.repo = DesignationRepository(db)

    async def create(self, data: DesignationCreate) -> Designation:
        if await self.repo.get_by_name(data.name):
            raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Designation '{data.name}' already exists")
        designation = await self.repo.create(Designation(name=data.name, description=data.description))
        logger.info("Designation created: %s", designation.id, extra={"service_task": "designation_create"})
        return designation

    async def get(self, designation_id: UUID) -> Designation:
        designation = await self.repo.get_by_id(designation_id)
        if not designation:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Designation {designation_id} not found")
        return designation

    async def list_all(self, include_inactive: bool = False):
        return await self.repo.get_all(include_inactive=include_inactive)

    async def update(self, designation_id: UUID, data: DesignationUpdate) -> Designation:
        designation = await self.get(designation_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update")
        if "name" in update_data:
            existing = await self.repo.get_by_name(update_data["name"])
            if existing and existing.id != designation_id:
                raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Designation '{update_data['name']}' already exists")
        return await self.repo.update(designation, update_data)

    async def soft_delete(self, designation_id: UUID) -> Designation:
        designation = await self.get(designation_id)
        return await self.repo.update(designation, {"is_active": 0})
