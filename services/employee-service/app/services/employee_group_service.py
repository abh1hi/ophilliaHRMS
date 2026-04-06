import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee_group import EmployeeGroup
from app.repositories.employee_group_repository import EmployeeGroupRepository
from app.schemas.employee_group import EmployeeGroupCreate, EmployeeGroupUpdate

logger = logging.getLogger(__name__)


class EmployeeGroupService:
    def __init__(self, db: AsyncSession):
        self.repo = EmployeeGroupRepository(db)

    async def create(self, data: EmployeeGroupCreate) -> EmployeeGroup:
        if await self.repo.get_by_name(data.name):
            raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Employee group '{data.name}' already exists")
        group = await self.repo.create(EmployeeGroup(name=data.name))
        logger.info("EmployeeGroup created: %s", group.id, extra={"service_task": "employee_group_create"})
        return group

    async def get(self, group_id: UUID) -> EmployeeGroup:
        group = await self.repo.get_by_id(group_id)
        if not group:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Employee group {group_id} not found")
        return group

    async def list_all(self, include_inactive: bool = False):
        return await self.repo.get_all(include_inactive=include_inactive)

    async def update(self, group_id: UUID, data: EmployeeGroupUpdate) -> EmployeeGroup:
        group = await self.get(group_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update")
        if "name" in update_data:
            existing = await self.repo.get_by_name(update_data["name"])
            if existing and existing.id != group_id:
                raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Employee group '{update_data['name']}' already exists")
        return await self.repo.update(group, update_data)

    async def soft_delete(self, group_id: UUID) -> EmployeeGroup:
        group = await self.get(group_id)
        return await self.repo.update(group, {"is_active": 0})

    async def add_member(self, group_id: UUID, employee_id: UUID) -> EmployeeGroup:
        group = await self.get(group_id)
        await self.repo.add_member(group_id, employee_id)
        return await self.get(group_id)

    async def remove_member(self, group_id: UUID, employee_id: UUID) -> EmployeeGroup:
        group = await self.get(group_id)
        await self.repo.remove_member(group_id, employee_id)
        return await self.get(group_id)
