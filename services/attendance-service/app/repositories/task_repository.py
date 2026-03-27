from typing import Optional, List
from uuid import UUID
from datetime import date

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_task import AttendanceTask


class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant dependency")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(AttendanceTask.company_id == self._company_id)

    async def create(self, task: AttendanceTask) -> AttendanceTask:
        task.company_id = self._company_id
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def get_by_id(self, task_id: UUID) -> Optional[AttendanceTask]:
        result = await self.db.execute(
            self._scoped(select(AttendanceTask)).where(AttendanceTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_by_record(self, record_id: UUID) -> List[AttendanceTask]:
        result = await self.db.execute(
            self._scoped(select(AttendanceTask))
            .where(AttendanceTask.attendance_record_id == record_id)
            .order_by(AttendanceTask.created_at)
        )
        return list(result.scalars().all())

    async def update(self, task: AttendanceTask, data: dict) -> AttendanceTask:
        for key, value in data.items():
            setattr(task, key, value)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def delete(self, task: AttendanceTask) -> None:
        await self.db.delete(task)
        await self.db.flush()

    async def commit(self):
        await self.db.commit()

    async def rollback(self):
        await self.db.rollback()
