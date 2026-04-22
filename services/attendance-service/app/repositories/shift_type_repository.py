from typing import Optional
from uuid import UUID
from datetime import date

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift_type import ShiftType
from app.models.shift_schedule import ShiftSchedule
from app.models.shift_schedule_assignment import ShiftScheduleAssignment


class ShiftTypeRepository:
    """Resolves the active ShiftType for an employee on a given date."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session")
        return UUID(cid) if isinstance(cid, str) else cid

    async def get_active_for_employee(
        self, employee_id: UUID, on_date: Optional[date] = None
    ) -> Optional[ShiftType]:
        """Return the ShiftType assigned to the employee on the given date (today if omitted)."""
        target = on_date or date.today()

        result = await self.db.execute(
            select(ShiftType)
            .join(ShiftSchedule, ShiftSchedule.shift_type_id == ShiftType.id)
            .join(ShiftScheduleAssignment, ShiftScheduleAssignment.schedule_id == ShiftSchedule.id)
            .where(
                and_(
                    ShiftScheduleAssignment.company_id == self._company_id,
                    ShiftScheduleAssignment.employee_id == employee_id,
                    ShiftScheduleAssignment.is_active == 1,
                    ShiftScheduleAssignment.effective_from <= target,
                    (ShiftScheduleAssignment.effective_to >= target) | ShiftScheduleAssignment.effective_to.is_(None),
                    ShiftSchedule.is_active == 1,
                    ShiftType.is_active.is_(True),
                )
            )
            .order_by(ShiftScheduleAssignment.effective_from.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def get_by_id(self, shift_type_id: UUID) -> Optional[ShiftType]:
        result = await self.db.execute(
            select(ShiftType).where(
                and_(ShiftType.id == shift_type_id, ShiftType.company_id == self._company_id)
            )
        )
        return result.scalars().first()

    async def create(self, shift_type: ShiftType) -> ShiftType:
        shift_type.company_id = self._company_id
        self.db.add(shift_type)
        await self.db.flush()
        await self.db.refresh(shift_type)
        return shift_type
