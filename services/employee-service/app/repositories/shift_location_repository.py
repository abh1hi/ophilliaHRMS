from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift_location import ShiftLocation


class ShiftLocationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(ShiftLocation.company_id == self._company_id)

    async def create(self, location: ShiftLocation) -> ShiftLocation:
        location.company_id = self._company_id
        self.db.add(location)
        await self.db.commit()
        await self.db.refresh(location)
        return location

    async def get_by_id(self, location_id: UUID) -> Optional[ShiftLocation]:
        result = await self.db.execute(
            self._scoped(select(ShiftLocation).where(ShiftLocation.id == location_id))
        )
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[ShiftLocation]:
        result = await self.db.execute(
            self._scoped(select(ShiftLocation).where(ShiftLocation.name == name))
        )
        return result.scalars().first()

    async def get_all(self, include_inactive: bool = False) -> tuple[List[ShiftLocation], int]:
        base = self._scoped(select(func.count(ShiftLocation.id)))
        query = self._scoped(select(ShiftLocation).order_by(ShiftLocation.name.asc()))
        if not include_inactive:
            base = base.where(ShiftLocation.is_active == 1)
            query = query.where(ShiftLocation.is_active == 1)
        total = (await self.db.execute(base)).scalar() or 0
        items = (await self.db.execute(query)).scalars().all()
        return list(items), total

    async def update(self, location: ShiftLocation, data: dict) -> ShiftLocation:
        for k, v in data.items():
            if v is not None:
                setattr(location, k, v)
        await self.db.commit()
        await self.db.refresh(location)
        return location
