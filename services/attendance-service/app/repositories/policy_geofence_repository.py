from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_geofence import PolicyGeofence


class PolicyGeofenceRepository:
    """CRUD for the policy_geofences junction table."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_policy(self, policy_id: UUID) -> List[PolicyGeofence]:
        result = await self.db.execute(
            select(PolicyGeofence).where(PolicyGeofence.policy_id == policy_id)
        )
        return list(result.scalars().all())

    async def get_primary(self, policy_id: UUID) -> Optional[PolicyGeofence]:
        result = await self.db.execute(
            select(PolicyGeofence).where(
                and_(PolicyGeofence.policy_id == policy_id, PolicyGeofence.is_primary.is_(True))
            ).limit(1)
        )
        return result.scalars().first()

    async def add(self, policy_id: UUID, geofence_id: UUID, is_primary: bool = False) -> PolicyGeofence:
        entry = PolicyGeofence(policy_id=policy_id, geofence_id=geofence_id, is_primary=is_primary)
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def remove_all(self, policy_id: UUID) -> None:
        entries = await self.get_by_policy(policy_id)
        for entry in entries:
            await self.db.delete(entry)
        await self.db.flush()

    async def replace(self, policy_id: UUID, geofence_ids: List[UUID]) -> List[PolicyGeofence]:
        """Replace all geofences for a policy. First entry is marked primary."""
        await self.remove_all(policy_id)
        results = []
        for idx, gid in enumerate(geofence_ids):
            results.append(await self.add(policy_id, gid, is_primary=(idx == 0)))
        return results
