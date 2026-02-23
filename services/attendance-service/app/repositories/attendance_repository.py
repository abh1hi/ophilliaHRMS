from typing import Optional, List
from uuid import UUID
from datetime import date

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_record import AttendanceRecord


class AttendanceRepository:
    """Data access layer for attendance records — async CRUD."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, record: AttendanceRecord) -> AttendanceRecord:
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def get_by_id(self, record_id: UUID) -> Optional[AttendanceRecord]:
        result = await self.db.execute(
            select(AttendanceRecord).where(AttendanceRecord.id == record_id)
        )
        return result.scalars().first()

    async def get_by_employee_and_date(
        self, employee_id: UUID, record_date: date
    ) -> Optional[AttendanceRecord]:
        result = await self.db.execute(
            select(AttendanceRecord).where(
                and_(
                    AttendanceRecord.employee_id == employee_id,
                    AttendanceRecord.date == record_date,
                )
            )
        )
        return result.scalars().first()

    async def get_employee_records(
        self,
        employee_id: UUID,
        skip: int = 0,
        limit: int = 20,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> tuple[List[AttendanceRecord], int]:
        query = select(AttendanceRecord).where(
            AttendanceRecord.employee_id == employee_id
        )
        count_query = select(func.count(AttendanceRecord.id)).where(
            AttendanceRecord.employee_id == employee_id
        )

        if date_from:
            query = query.where(AttendanceRecord.date >= date_from)
            count_query = count_query.where(AttendanceRecord.date >= date_from)
        if date_to:
            query = query.where(AttendanceRecord.date <= date_to)
            count_query = count_query.where(AttendanceRecord.date <= date_to)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AttendanceRecord.date.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        employee_id: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        status: Optional[str] = None,
    ) -> tuple[List[AttendanceRecord], int]:
        query = select(AttendanceRecord)
        count_query = select(func.count(AttendanceRecord.id))

        if employee_id:
            query = query.where(AttendanceRecord.employee_id == employee_id)
            count_query = count_query.where(AttendanceRecord.employee_id == employee_id)
        if date_from:
            query = query.where(AttendanceRecord.date >= date_from)
            count_query = count_query.where(AttendanceRecord.date >= date_from)
        if date_to:
            query = query.where(AttendanceRecord.date <= date_to)
            count_query = count_query.where(AttendanceRecord.date <= date_to)
        if status:
            query = query.where(AttendanceRecord.status == status)
            count_query = count_query.where(AttendanceRecord.status == status)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AttendanceRecord.date.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def update(self, record: AttendanceRecord, update_data: dict) -> AttendanceRecord:
        for field, value in update_data.items():
            if value is not None:
                setattr(record, field, value)
        await self.db.commit()
        await self.db.refresh(record)
        return record
