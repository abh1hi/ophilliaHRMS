from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift_type import ShiftType


class ShiftTypeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(ShiftType.company_id == self._company_id)

    async def create(self, shift_type: ShiftType) -> ShiftType:
        shift_type.company_id = self._company_id
        self.db.add(shift_type)
        await self.db.commit()
        await self.db.refresh(shift_type)
        return shift_type

    async def get_by_id(self, shift_type_id: UUID) -> Optional[ShiftType]:
        result = await self.db.execute(
            self._scoped(select(ShiftType).where(ShiftType.id == shift_type_id))
        )
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[ShiftType]:
        result = await self.db.execute(
            self._scoped(select(ShiftType).where(ShiftType.name == name))
        )
        return result.scalars().first()

    async def get_all(self, include_inactive: bool = False) -> tuple[List[ShiftType], int]:
        base = self._scoped(select(func.count(ShiftType.id)))
        query = self._scoped(select(ShiftType).order_by(ShiftType.name.asc()))
        if not include_inactive:
            base = base.where(ShiftType.is_active == 1)
            query = query.where(ShiftType.is_active == 1)
        total = (await self.db.execute(base)).scalar() or 0
        items = (await self.db.execute(query)).scalars().all()
        return list(items), total

    async def update(self, shift_type: ShiftType, data: dict) -> ShiftType:
        for k, v in data.items():
            if v is not None:
                setattr(shift_type, k, v)
        await self.db.commit()
        await self.db.refresh(shift_type)
        return shift_type
