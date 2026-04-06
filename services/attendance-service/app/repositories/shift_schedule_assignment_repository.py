from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift_schedule_assignment import ShiftScheduleAssignment


class ShiftScheduleAssignmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(ShiftScheduleAssignment.company_id == self._company_id)

    async def assign(self, schedule_id: UUID, employee_id: UUID) -> ShiftScheduleAssignment:
        obj = ShiftScheduleAssignment(
            company_id=self._company_id,
            schedule_id=schedule_id,
            employee_id=employee_id,
        )
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_by_id(self, assignment_id: UUID) -> Optional[ShiftScheduleAssignment]:
        result = await self.db.execute(
            self._scoped(select(ShiftScheduleAssignment).where(ShiftScheduleAssignment.id == assignment_id))
        )
        return result.scalars().first()

    async def get_existing(self, schedule_id: UUID, employee_id: UUID) -> Optional[ShiftScheduleAssignment]:
        result = await self.db.execute(
            self._scoped(
                select(ShiftScheduleAssignment).where(
                    ShiftScheduleAssignment.schedule_id == schedule_id,
                    ShiftScheduleAssignment.employee_id == employee_id,
                )
            )
        )
        return result.scalars().first()

    async def get_by_schedule(self, schedule_id: UUID) -> List[ShiftScheduleAssignment]:
        result = await self.db.execute(
            self._scoped(select(ShiftScheduleAssignment).where(ShiftScheduleAssignment.schedule_id == schedule_id))
        )
        return list(result.scalars().all())

    async def get_by_employee(self, employee_id: UUID) -> List[ShiftScheduleAssignment]:
        result = await self.db.execute(
            self._scoped(select(ShiftScheduleAssignment).where(ShiftScheduleAssignment.employee_id == employee_id))
        )
        return list(result.scalars().all())

    async def get_all(self, schedule_id: Optional[UUID] = None, employee_id: Optional[UUID] = None) -> tuple[List[ShiftScheduleAssignment], int]:
        base = self._scoped(select(func.count(ShiftScheduleAssignment.id)))
        query = self._scoped(select(ShiftScheduleAssignment))
        if schedule_id:
            base = base.where(ShiftScheduleAssignment.schedule_id == schedule_id)
            query = query.where(ShiftScheduleAssignment.schedule_id == schedule_id)
        if employee_id:
            base = base.where(ShiftScheduleAssignment.employee_id == employee_id)
            query = query.where(ShiftScheduleAssignment.employee_id == employee_id)
        total = (await self.db.execute(base)).scalar() or 0
        items = (await self.db.execute(query)).scalars().all()
        return list(items), total

    async def delete(self, obj: ShiftScheduleAssignment) -> None:
        await self.db.delete(obj)
        await self.db.commit()
