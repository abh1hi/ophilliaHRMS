from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task_template import TaskTemplate


class TaskTemplateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(TaskTemplate.company_id == self._company_id)

    async def create(self, template: TaskTemplate) -> TaskTemplate:
        template.company_id = self._company_id
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def get_by_id(self, template_id: UUID) -> Optional[TaskTemplate]:
        result = await self.db.execute(
            self._scoped(select(TaskTemplate)).where(TaskTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def get_for_employee(
        self, employee_id: UUID, skip: int = 0, limit: int = 50
    ) -> tuple[List[TaskTemplate], int]:
        """Get templates visible to employee: their own + shared company templates."""
        base_filter = and_(
            TaskTemplate.is_active.is_(True),
            or_(
                TaskTemplate.created_by == employee_id,
                TaskTemplate.is_shared.is_(True),
            ),
        )
        query = self._scoped(select(TaskTemplate)).where(base_filter)
        from sqlalchemy import func
        count_query = self._scoped(
            select(func.count(TaskTemplate.id))
        ).where(base_filter)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(TaskTemplate.title).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def update(self, template: TaskTemplate, data: dict) -> TaskTemplate:
        for key, value in data.items():
            setattr(template, key, value)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def delete(self, template: TaskTemplate) -> None:
        await self.db.delete(template)
        await self.db.commit()
