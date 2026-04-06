from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.branch import Branch


class BranchRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(Branch.company_id == self._company_id)

    async def create(self, branch: Branch) -> Branch:
        branch.company_id = self._company_id
        self.db.add(branch)
        await self.db.commit()
        await self.db.refresh(branch)
        return branch

    async def get_by_id(self, branch_id: UUID) -> Optional[Branch]:
        result = await self.db.execute(self._scoped(select(Branch).where(Branch.id == branch_id)))
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[Branch]:
        result = await self.db.execute(self._scoped(select(Branch).where(Branch.name == name)))
        return result.scalars().first()

    async def get_all(self, include_inactive: bool = False) -> tuple[List[Branch], int]:
        base = self._scoped(select(func.count(Branch.id)))
        query = self._scoped(select(Branch).order_by(Branch.name.asc()))
        if not include_inactive:
            base = base.where(Branch.is_active == 1)
            query = query.where(Branch.is_active == 1)
        total = (await self.db.execute(base)).scalar() or 0
        items = (await self.db.execute(query)).scalars().all()
        return list(items), total

    async def update(self, branch: Branch, data: dict) -> Branch:
        for k, v in data.items():
            if v is not None:
                setattr(branch, k, v)
        await self.db.commit()
        await self.db.refresh(branch)
        return branch
