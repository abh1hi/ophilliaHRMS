from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift_schedule import ShiftSchedule


class ShiftScheduleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(ShiftSchedule.company_id == self._company_id)

    async def create(self, schedule: ShiftSchedule) -> ShiftSchedule:
        schedule.company_id = self._company_id
        self.db.add(schedule)
        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule

    async def exists_shift_type(self, shift_type_id: UUID) -> bool:
        from app.models.shift_type import ShiftType

        result = await self.db.execute(
            select(func.count(ShiftType.id)).where(
                ShiftType.company_id == self._company_id,
                ShiftType.id == shift_type_id,
                ShiftType.is_active.is_(True),
            )
        )
        return bool(result.scalar() or 0)

    async def get_by_id(self, schedule_id: UUID) -> Optional[ShiftSchedule]:
        result = await self.db.execute(
            self._scoped(select(ShiftSchedule).where(ShiftSchedule.id == schedule_id))
        )
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[ShiftSchedule]:
        result = await self.db.execute(
            self._scoped(select(ShiftSchedule).where(ShiftSchedule.name == name))
        )
        return result.scalars().first()

    async def get_all(self, include_inactive: bool = False) -> tuple[List[ShiftSchedule], int]:
        base = self._scoped(select(func.count(ShiftSchedule.id)))
        query = self._scoped(select(ShiftSchedule).order_by(ShiftSchedule.name.asc()))
        if not include_inactive:
            base = base.where(ShiftSchedule.is_active == 1)
            query = query.where(ShiftSchedule.is_active == 1)
        total = (await self.db.execute(base)).scalar() or 0
        items = (await self.db.execute(query)).scalars().all()
        return list(items), total

    async def update(self, schedule: ShiftSchedule, data: dict) -> ShiftSchedule:
        for k, v in data.items():
            setattr(schedule, k, v)
        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule
