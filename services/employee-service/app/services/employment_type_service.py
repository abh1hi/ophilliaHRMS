import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employment_type import EmploymentType
from app.repositories.employment_type_repository import EmploymentTypeRepository
from app.schemas.employment_type import EmploymentTypeCreate, EmploymentTypeUpdate

logger = logging.getLogger(__name__)


class EmploymentTypeService:
    def __init__(self, db: AsyncSession):
        self.repo = EmploymentTypeRepository(db)

    async def create(self, data: EmploymentTypeCreate) -> EmploymentType:
        if await self.repo.get_by_name(data.name):
            raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Employment type '{data.name}' already exists")
        et = await self.repo.create(EmploymentType(name=data.name))
        logger.info("EmploymentType created: %s", et.id, extra={"service_task": "employment_type_create"})
        return et

    async def get(self, et_id: UUID) -> EmploymentType:
        et = await self.repo.get_by_id(et_id)
        if not et:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Employment type {et_id} not found")
        return et

    async def list_all(self, include_inactive: bool = False):
        return await self.repo.get_all(include_inactive=include_inactive)

    async def update(self, et_id: UUID, data: EmploymentTypeUpdate) -> EmploymentType:
        et = await self.get(et_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update")
        if "name" in update_data:
            existing = await self.repo.get_by_name(update_data["name"])
            if existing and existing.id != et_id:
                raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Employment type '{update_data['name']}' already exists")
        return await self.repo.update(et, update_data)

    async def soft_delete(self, et_id: UUID) -> EmploymentType:
        et = await self.get(et_id)
        return await self.repo.update(et, {"is_active": 0})
