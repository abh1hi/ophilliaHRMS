from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.task import CalendarTask
from app.models.task_assignee import TaskAssignee
from app.models.task_comment import TaskComment


async def get_task(db: AsyncSession, task_id: UUID, company_id: str) -> Optional[CalendarTask]:
    result = await db.execute(
        select(CalendarTask).where(
            CalendarTask.id == task_id,
            CalendarTask.company_id == company_id,
            CalendarTask.is_deleted == False,
        )
    )
    return result.scalars().first()


async def list_tasks(
    db: AsyncSession,
    company_id: str,
    workspace_id: Optional[UUID] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_id: Optional[UUID] = None,
    after_id: Optional[UUID] = None,
    limit: int = 50,
) -> List[CalendarTask]:
    q = select(CalendarTask).where(
        CalendarTask.company_id == company_id,
        CalendarTask.is_deleted == False,
        CalendarTask.parent_task_id == None,
    )
    if workspace_id:
        q = q.where(CalendarTask.workspace_id == workspace_id)
    if status:
        q = q.where(CalendarTask.status == status)
    if priority:
        q = q.where(CalendarTask.priority == priority)
    if assignee_id:
        assignee_sq = select(TaskAssignee.task_id).where(
            TaskAssignee.employee_id == assignee_id,
            TaskAssignee.is_deleted == False,
        ).scalar_subquery()
        q = q.where(CalendarTask.id.in_(assignee_sq))
    q = q.order_by(CalendarTask.created_at.desc()).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


async def get_subtasks(db: AsyncSession, parent_task_id: UUID, company_id: str) -> List[CalendarTask]:
    result = await db.execute(
        select(CalendarTask).where(
            CalendarTask.parent_task_id == parent_task_id,
            CalendarTask.company_id == company_id,
            CalendarTask.is_deleted == False,
        )
    )
    return result.scalars().all()


async def get_assignees(db: AsyncSession, task_id: UUID) -> List[TaskAssignee]:
    result = await db.execute(
        select(TaskAssignee).where(
            TaskAssignee.task_id == task_id,
            TaskAssignee.is_deleted == False,
        )
    )
    return result.scalars().all()


async def get_comments(db: AsyncSession, task_id: UUID, company_id: str) -> List[TaskComment]:
    result = await db.execute(
        select(TaskComment).where(
            TaskComment.task_id == task_id,
            TaskComment.company_id == company_id,
            TaskComment.is_deleted == False,
        ).order_by(TaskComment.created_at)
    )
    return result.scalars().all()


async def get_comment(db: AsyncSession, comment_id: UUID, company_id: str) -> Optional[TaskComment]:
    result = await db.execute(
        select(TaskComment).where(
            TaskComment.id == comment_id,
            TaskComment.company_id == company_id,
            TaskComment.is_deleted == False,
        )
    )
    return result.scalars().first()
