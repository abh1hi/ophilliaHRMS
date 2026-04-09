from typing import Optional, List
from uuid import UUID
from datetime import date

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift_assignment import ShiftAssignment


class ShiftAssignmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(ShiftAssignment.company_id == self._company_id)

    async def create(self, assignment: ShiftAssignment) -> ShiftAssignment:
        assignment.company_id = self._company_id
        self.db.add(assignment)
        await self.db.commit()
        await self.db.refresh(assignment)
        return assignment

    async def get_by_id(self, assignment_id: UUID) -> Optional[ShiftAssignment]:
        result = await self.db.execute(
            self._scoped(select(ShiftAssignment).where(ShiftAssignment.id == assignment_id))
        )
        return result.scalars().first()

    async def get_all(
        self,
        employee_id: Optional[UUID] = None,
        include_inactive: bool = False,
    ) -> tuple[List[ShiftAssignment], int]:
        base = self._scoped(select(func.count(ShiftAssignment.id)))
        query = self._scoped(select(ShiftAssignment).order_by(ShiftAssignment.effective_from.desc()))
        if employee_id:
            base = base.where(ShiftAssignment.employee_id == employee_id)
            query = query.where(ShiftAssignment.employee_id == employee_id)
        if not include_inactive:
            base = base.where(ShiftAssignment.is_active == 1)
            query = query.where(ShiftAssignment.is_active == 1)
        total = (await self.db.execute(base)).scalar() or 0
        items = (await self.db.execute(query)).scalars().all()
        return list(items), total

    async def get_active_for_date(self, employee_id: UUID, target_date: date) -> List[ShiftAssignment]:
        result = await self.db.execute(
            self._scoped(
                select(ShiftAssignment).where(
                    and_(
                        ShiftAssignment.employee_id == employee_id,
                        ShiftAssignment.is_active == 1,
                        ShiftAssignment.effective_from <= target_date,
                        (ShiftAssignment.effective_to == None) | (ShiftAssignment.effective_to >= target_date),
                    )
                )
            )
        )
        return list(result.scalars().all())

    async def get_all_for_date_range(self, from_date: date, to_date: date, employee_id: Optional[UUID] = None) -> List[ShiftAssignment]:
        query = self._scoped(
            select(ShiftAssignment).where(
                and_(
                    ShiftAssignment.is_active == 1,
                    ShiftAssignment.effective_from <= to_date,
                    (ShiftAssignment.effective_to == None) | (ShiftAssignment.effective_to >= from_date),
                )
            )
        )
        if employee_id:
            query = query.where(ShiftAssignment.employee_id == employee_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, assignment: ShiftAssignment, data: dict) -> ShiftAssignment:
        for k, v in data.items():
            setattr(assignment, k, v)
        await self.db.commit()
        await self.db.refresh(assignment)
        return assignment
