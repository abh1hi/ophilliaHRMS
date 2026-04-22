from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.geofence_location import GeofenceLocation


class GeofenceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant dependency")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(GeofenceLocation.company_id == self._company_id)

    async def create(self, geofence: GeofenceLocation) -> GeofenceLocation:
        geofence.company_id = self._company_id
        self.db.add(geofence)
        await self.db.commit()
        await self.db.refresh(geofence)
        return geofence

    async def get_by_id(self, geofence_id: UUID) -> Optional[GeofenceLocation]:
        result = await self.db.execute(
            self._scoped(select(GeofenceLocation)).where(GeofenceLocation.id == geofence_id)
        )
        return result.scalars().first()

    async def get_by_ids(self, geofence_ids: List[UUID]) -> List[GeofenceLocation]:
        if not geofence_ids:
            return []
        result = await self.db.execute(
            self._scoped(select(GeofenceLocation)).where(
                GeofenceLocation.id.in_(geofence_ids),
                GeofenceLocation.is_active == True,
            )
        )
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Optional[GeofenceLocation]:
        result = await self.db.execute(
            self._scoped(select(GeofenceLocation)).where(GeofenceLocation.name == name)
        )
        return result.scalars().first()

    async def update(self, geofence: GeofenceLocation, updates: dict) -> GeofenceLocation:
        for key, value in updates.items():
            setattr(geofence, key, value)
        await self.db.commit()
        await self.db.refresh(geofence)
        return geofence

    async def soft_delete(self, geofence: GeofenceLocation) -> GeofenceLocation:
        geofence.is_active = False
        await self.db.commit()
        await self.db.refresh(geofence)
        return geofence

    async def get_all_active(self, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> tuple[List[GeofenceLocation], int]:
        count_q = self._scoped(select(func.count(GeofenceLocation.id)))
        if not include_inactive:
            count_q = count_q.where(GeofenceLocation.is_active == True)
        count_result = await self.db.execute(count_q)
        total = count_result.scalar() or 0

        query = self._scoped(select(GeofenceLocation)).order_by(GeofenceLocation.name.asc())
        if not include_inactive:
            query = query.where(GeofenceLocation.is_active == True)
        result = await self.db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all()), total
