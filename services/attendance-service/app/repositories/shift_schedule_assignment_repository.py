from typing import Optional, List
from uuid import UUID

from datetime import date

from sqlalchemy import select, func, and_, or_
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

    async def assign(
        self,
        schedule_id: UUID,
        employee_id: UUID,
        effective_from: date,
        effective_to: Optional[date] = None,
        notes: Optional[str] = None,
    ) -> ShiftScheduleAssignment:
        obj = ShiftScheduleAssignment(
            company_id=self._company_id,
            schedule_id=schedule_id,
            employee_id=employee_id,
            effective_from=effective_from,
            effective_to=effective_to,
            notes=notes,
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

    async def get_existing(self, schedule_id: UUID, employee_id: UUID, effective_from: date) -> Optional[ShiftScheduleAssignment]:
        result = await self.db.execute(
            self._scoped(
                select(ShiftScheduleAssignment).where(
                    ShiftScheduleAssignment.schedule_id == schedule_id,
                    ShiftScheduleAssignment.employee_id == employee_id,
                    ShiftScheduleAssignment.effective_from == effective_from,
                )
            )
        )
        return result.scalars().first()

    async def has_overlapping_assignment(
        self,
        employee_id: UUID,
        effective_from: date,
        effective_to: Optional[date],
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        new_end = effective_to or date.max
        query = self._scoped(
            select(func.count(ShiftScheduleAssignment.id)).where(
                ShiftScheduleAssignment.employee_id == employee_id,
                ShiftScheduleAssignment.is_active == 1,
                ShiftScheduleAssignment.effective_from <= new_end,
                or_(
                    ShiftScheduleAssignment.effective_to.is_(None),
                    ShiftScheduleAssignment.effective_to >= effective_from,
                ),
            )
        )
        if exclude_id:
            query = query.where(ShiftScheduleAssignment.id != exclude_id)
        result = await self.db.execute(query)
        return bool(result.scalar() or 0)

    async def get_active_for_date(
        self, employee_id: UUID, target_date: date
    ) -> Optional[ShiftScheduleAssignment]:
        result = await self.db.execute(
            self._scoped(
                select(ShiftScheduleAssignment).where(
                    and_(
                        ShiftScheduleAssignment.employee_id == employee_id,
                        ShiftScheduleAssignment.is_active == 1,
                        ShiftScheduleAssignment.effective_from <= target_date,
                        or_(
                            ShiftScheduleAssignment.effective_to.is_(None),
                            ShiftScheduleAssignment.effective_to >= target_date,
                        ),
                    )
                )
                .order_by(ShiftScheduleAssignment.effective_from.desc())
                .limit(1)
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

    async def get_all_for_date_range(
        self,
        from_date: date,
        to_date: date,
        employee_id: Optional[UUID] = None,
    ) -> List[ShiftScheduleAssignment]:
        query = self._scoped(
            select(ShiftScheduleAssignment).where(
                ShiftScheduleAssignment.is_active == 1,
                ShiftScheduleAssignment.effective_from <= to_date,
                or_(
                    ShiftScheduleAssignment.effective_to.is_(None),
                    ShiftScheduleAssignment.effective_to >= from_date,
                ),
            )
        )
        if employee_id:
            query = query.where(ShiftScheduleAssignment.employee_id == employee_id)
        result = await self.db.execute(query.order_by(ShiftScheduleAssignment.effective_from.desc()))
        return list(result.scalars().all())

    async def update(self, obj: ShiftScheduleAssignment, data: dict) -> ShiftScheduleAssignment:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: ShiftScheduleAssignment) -> None:
        await self.db.delete(obj)
        await self.db.commit()
