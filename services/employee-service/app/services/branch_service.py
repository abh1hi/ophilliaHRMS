import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.branch import Branch
from app.repositories.branch_repository import BranchRepository
from app.schemas.branch import BranchCreate, BranchUpdate

logger = logging.getLogger(__name__)


class BranchService:
    def __init__(self, db: AsyncSession):
        self.repo = BranchRepository(db)

    async def create(self, data: BranchCreate) -> Branch:
        if await self.repo.get_by_name(data.name):
            raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Branch '{data.name}' already exists")
        branch = await self.repo.create(Branch(name=data.name))
        logger.info("Branch created: %s", branch.id, extra={"service_task": "branch_create"})
        return branch

    async def get(self, branch_id: UUID) -> Branch:
        branch = await self.repo.get_by_id(branch_id)
        if not branch:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Branch {branch_id} not found")
        return branch

    async def list_all(self, include_inactive: bool = False):
        return await self.repo.get_all(include_inactive=include_inactive)

    async def update(self, branch_id: UUID, data: BranchUpdate) -> Branch:
        branch = await self.get(branch_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update")
        if "name" in update_data:
            existing = await self.repo.get_by_name(update_data["name"])
            if existing and existing.id != branch_id:
                raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Branch '{update_data['name']}' already exists")
        return await self.repo.update(branch, update_data)

    async def soft_delete(self, branch_id: UUID) -> Branch:
        branch = await self.get(branch_id)
        return await self.repo.update(branch, {"is_active": 0})
