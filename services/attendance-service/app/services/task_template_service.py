import logging
from typing import Optional, List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task_template import TaskTemplate
from app.repositories.task_template_repository import TaskTemplateRepository
from app.schemas.attendance import TaskTemplateCreate, TaskTemplateUpdate

logger = logging.getLogger(__name__)


class TaskTemplateService:
    """Business logic for reusable task templates."""

    def __init__(self, db: AsyncSession):
        self.repo = TaskTemplateRepository(db)

    async def create_template(self, data: TaskTemplateCreate, created_by: UUID) -> TaskTemplate:
        template = TaskTemplate(
            created_by=created_by,
            title=data.title,
            details=data.details,
            estimated_finish_time=data.estimated_finish_time,
            expected_expenses=data.expected_expenses,
            is_shared=data.is_shared,
        )
        return await self.repo.create(template)

    async def list_templates(
        self, employee_id: UUID, skip: int = 0, limit: int = 50
    ) -> tuple[List[TaskTemplate], int]:
        return await self.repo.get_for_employee(employee_id, skip, limit)

    async def update_template(
        self, template_id: UUID, data: TaskTemplateUpdate,
        user_id: UUID, is_admin: bool,
    ) -> TaskTemplate:
        template = await self.repo.get_by_id(template_id)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        if template.created_by != user_id and not is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify another user's template")
        updates = data.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update")
        return await self.repo.update(template, updates)

    async def delete_template(self, template_id: UUID, user_id: UUID, is_admin: bool) -> None:
        template = await self.repo.get_by_id(template_id)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        if template.created_by != user_id and not is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete another user's template")
        await self.repo.delete(template)
