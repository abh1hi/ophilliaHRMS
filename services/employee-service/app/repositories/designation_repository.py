from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.designation import Designation


class DesignationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(Designation.company_id == self._company_id)

    async def create(self, designation: Designation) -> Designation:
        designation.company_id = self._company_id
        self.db.add(designation)
        await self.db.commit()
        await self.db.refresh(designation)
        return designation

    async def get_by_id(self, designation_id: UUID) -> Optional[Designation]:
        result = await self.db.execute(self._scoped(select(Designation).where(Designation.id == designation_id)))
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[Designation]:
        result = await self.db.execute(self._scoped(select(Designation).where(Designation.name == name)))
        return result.scalars().first()

    async def get_all(self, include_inactive: bool = False) -> tuple[List[Designation], int]:
        base = self._scoped(select(func.count(Designation.id)))
        query = self._scoped(select(Designation).order_by(Designation.name.asc()))
        if not include_inactive:
            base = base.where(Designation.is_active == 1)
            query = query.where(Designation.is_active == 1)
        total = (await self.db.execute(base)).scalar() or 0
        items = (await self.db.execute(query)).scalars().all()
        return list(items), total

    async def update(self, designation: Designation, data: dict) -> Designation:
        for k, v in data.items():
            if v is not None:
                setattr(designation, k, v)
        await self.db.commit()
        await self.db.refresh(designation)
        return designation
