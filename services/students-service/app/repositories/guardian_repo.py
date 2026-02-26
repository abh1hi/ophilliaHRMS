from __future__ import annotations
import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guardian import Guardian


class GuardianRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, guardian: Guardian) -> Guardian:
        self._db.add(guardian)
        await self._db.flush()
        await self._db.refresh(guardian)
        return guardian

    async def get_by_id(self, guardian_id: uuid.UUID) -> Optional[Guardian]:
        result = await self._db.execute(
            select(Guardian).where(Guardian.id == guardian_id)
        )
        return result.scalar_one_or_none()

    async def list_by_student(self, student_id: uuid.UUID) -> Sequence[Guardian]:
        result = await self._db.execute(
            select(Guardian).where(Guardian.student_id == student_id)
        )
        return result.scalars().all()

    async def update(self, guardian: Guardian) -> Guardian:
        await self._db.flush()
        await self._db.refresh(guardian)
        return guardian

    async def delete(self, guardian: Guardian) -> None:
        await self._db.delete(guardian)
        await self._db.flush()
