from typing import Optional, List
from uuid import UUID
from datetime import datetime, date

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee_checkin import EmployeeCheckin


class EmployeeCheckinRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(EmployeeCheckin.company_id == self._company_id)

    async def create(self, checkin: EmployeeCheckin) -> EmployeeCheckin:
        checkin.company_id = self._company_id
        self.db.add(checkin)
        await self.db.commit()
        await self.db.refresh(checkin)
        return checkin

    async def get_by_id(self, checkin_id: UUID) -> Optional[EmployeeCheckin]:
        result = await self.db.execute(
            self._scoped(select(EmployeeCheckin).where(EmployeeCheckin.id == checkin_id))
        )
        return result.scalars().first()

    async def get_all(
        self,
        employee_id: Optional[UUID] = None,
        from_dt: Optional[datetime] = None,
        to_dt: Optional[datetime] = None,
        log_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[EmployeeCheckin], int]:
        base = self._scoped(select(func.count(EmployeeCheckin.id)))
        query = self._scoped(
            select(EmployeeCheckin).order_by(EmployeeCheckin.log_datetime.desc())
        )
        if employee_id:
            base = base.where(EmployeeCheckin.employee_id == employee_id)
            query = query.where(EmployeeCheckin.employee_id == employee_id)
        if from_dt:
            base = base.where(EmployeeCheckin.log_datetime >= from_dt)
            query = query.where(EmployeeCheckin.log_datetime >= from_dt)
        if to_dt:
            base = base.where(EmployeeCheckin.log_datetime <= to_dt)
            query = query.where(EmployeeCheckin.log_datetime <= to_dt)
        if log_type:
            base = base.where(EmployeeCheckin.log_type == log_type)
            query = query.where(EmployeeCheckin.log_type == log_type)
        total = (await self.db.execute(base)).scalar() or 0
        items = (await self.db.execute(query.offset(skip).limit(limit))).scalars().all()
        return list(items), total

    async def get_for_auto_attendance(
        self, target_date: date, company_id: UUID
    ) -> List[EmployeeCheckin]:
        """Fetch unprocessed checkins for a given date (for auto-attendance scheduler).

        Bypasses tenant scoping to allow the scheduler to pass company_id directly
        (scheduler sessions don't have tenant info set).
        """
        day_start = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)
        day_end = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)
        result = await self.db.execute(
            select(EmployeeCheckin).where(
                and_(
                    EmployeeCheckin.company_id == company_id,
                    EmployeeCheckin.log_datetime >= day_start,
                    EmployeeCheckin.log_datetime <= day_end,
                    EmployeeCheckin.skip_auto_attendance == 0,
                    EmployeeCheckin.attendance_record_id.is_(None),
                )
            ).order_by(EmployeeCheckin.log_datetime.asc())
        )
        return list(result.scalars().all())

    async def link_record(self, checkin_id: UUID, attendance_record_id: UUID) -> None:
        checkin = await self.get_by_id(checkin_id)
        if checkin:
            checkin.attendance_record_id = attendance_record_id
            await self.db.commit()

    async def update(self, checkin: EmployeeCheckin, data: dict) -> EmployeeCheckin:
        for k, v in data.items():
            setattr(checkin, k, v)
        await self.db.commit()
        await self.db.refresh(checkin)
        return checkin
