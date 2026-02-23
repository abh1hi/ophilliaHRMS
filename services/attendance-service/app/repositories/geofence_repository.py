from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.geofence_location import GeofenceLocation


class GeofenceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, geofence: GeofenceLocation) -> GeofenceLocation:
        self.db.add(geofence)
        await self.db.commit()
        await self.db.refresh(geofence)
        return geofence

    async def get_by_id(self, geofence_id: UUID) -> Optional[GeofenceLocation]:
        result = await self.db.execute(
            select(GeofenceLocation).where(GeofenceLocation.id == geofence_id)
        )
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[GeofenceLocation]:
        result = await self.db.execute(
            select(GeofenceLocation).where(GeofenceLocation.name == name)
        )
        return result.scalars().first()

    async def get_all_active(self) -> tuple[List[GeofenceLocation], int]:
        count_result = await self.db.execute(
            select(func.count(GeofenceLocation.id)).where(GeofenceLocation.is_active == True)
        )
        total = count_result.scalar() or 0
        result = await self.db.execute(
            select(GeofenceLocation)
            .where(GeofenceLocation.is_active == True)
            .order_by(GeofenceLocation.name.asc())
        )
        return list(result.scalars().all()), total
