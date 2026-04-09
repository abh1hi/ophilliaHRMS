from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employment_type import EmploymentType


class EmploymentTypeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(EmploymentType.company_id == self._company_id)

    async def create(self, et: EmploymentType) -> EmploymentType:
        et.company_id = self._company_id
        self.db.add(et)
        await self.db.commit()
        await self.db.refresh(et)
        return et

    async def get_by_id(self, et_id: UUID) -> Optional[EmploymentType]:
        result = await self.db.execute(self._scoped(select(EmploymentType).where(EmploymentType.id == et_id)))
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[EmploymentType]:
        result = await self.db.execute(self._scoped(select(EmploymentType).where(EmploymentType.name == name)))
        return result.scalars().first()

    async def get_all(self, include_inactive: bool = False) -> tuple[List[EmploymentType], int]:
        base = self._scoped(select(func.count(EmploymentType.id)))
        query = self._scoped(select(EmploymentType).order_by(EmploymentType.name.asc()))
        if not include_inactive:
            base = base.where(EmploymentType.is_active == 1)
            query = query.where(EmploymentType.is_active == 1)
        total = (await self.db.execute(base)).scalar() or 0
        items = (await self.db.execute(query)).scalars().all()
        return list(items), total

    async def update(self, et: EmploymentType, data: dict) -> EmploymentType:
        for k, v in data.items():
            if v is not None:
                setattr(et, k, v)
        await self.db.commit()
        await self.db.refresh(et)
        return et
