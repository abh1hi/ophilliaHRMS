from datetime import datetime, timezone
from uuid import UUID
from typing import List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import CalendarTask
from app.models.task_assignee import TaskAssignee
from app.models.task_comment import TaskComment
from app.schemas.task import TaskCreate, TaskUpdate, TaskStatusUpdate, AssigneeAdd, CommentCreate, CommentUpdate
from app.repositories import task_repository as repo
from app.core.permissions import check_permission
from app.core.cache import cache_invalidate, company_tasks_pattern


async def create_task(db: AsyncSession, data: TaskCreate, created_by: UUID, company_id: str) -> CalendarTask:
    task_data = data.model_dump(exclude={"assignees"})
    task = CalendarTask(**task_data, created_by=created_by, company_id=company_id)
    db.add(task)
    await db.flush()

    for emp_id in data.assignees:
        assignee = TaskAssignee(
            task_id=task.id,
            employee_id=emp_id,
            company_id=company_id,
            assigned_by=created_by,
            assigned_at=datetime.now(timezone.utc),
        )
        db.add(assignee)

    await db.commit()
    await cache_invalidate(company_tasks_pattern(company_id))
    return task


async def update_task(
    db: AsyncSession, task_id: UUID, data: TaskUpdate,
    current_user_id: UUID, current_user_role: str, company_id: str
) -> CalendarTask:
    task = await repo.get_task(db, task_id, company_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    assignees = await repo.get_assignees(db, task_id)
    assignee_ids = [a.employee_id for a in assignees]
    check_permission("task:assign", current_user_role, current_user_id, task.created_by, assignee_ids)

    update_data = data.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] == "done":
        update_data["completed_at"] = datetime.now(timezone.utc)

    for field, value in update_data.items():
        setattr(task, field, value)
    await db.commit()
    await cache_invalidate(company_tasks_pattern(company_id))
    return task


async def update_task_status(
    db: AsyncSession, task_id: UUID, data: TaskStatusUpdate,
    current_user_id: UUID, current_user_role: str, company_id: str
) -> CalendarTask:
    task = await repo.get_task(db, task_id, company_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    assignees = await repo.get_assignees(db, task_id)
    assignee_ids = [a.employee_id for a in assignees]
    check_permission("task:status", current_user_role, current_user_id, task.created_by, assignee_ids)

    task.status = data.status
    if data.status == "done":
        task.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await cache_invalidate(company_tasks_pattern(company_id))
    return task


async def delete_task(
    db: AsyncSession, task_id: UUID,
    current_user_id: UUID, current_user_role: str, company_id: str
) -> None:
    task = await repo.get_task(db, task_id, company_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    check_permission("task:delete", current_user_role, current_user_id, task.created_by)
    task.is_deleted = True
    task.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    await cache_invalidate(company_tasks_pattern(company_id))


async def add_assignee(
    db: AsyncSession, task_id: UUID, data: AssigneeAdd,
    current_user_id: UUID, current_user_role: str, company_id: str
) -> TaskAssignee:
    task = await repo.get_task(db, task_id, company_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    check_permission("task:assign", current_user_role, current_user_id, task.created_by)

    assignee = TaskAssignee(
        task_id=task_id,
        employee_id=data.employee_id,
        company_id=company_id,
        assigned_by=current_user_id,
        assigned_at=datetime.now(timezone.utc),
    )
    db.add(assignee)
    await db.commit()
    return assignee


async def remove_assignee(
    db: AsyncSession, task_id: UUID, employee_id: UUID,
    current_user_id: UUID, current_user_role: str, company_id: str
) -> None:
    task = await repo.get_task(db, task_id, company_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    check_permission("task:assign", current_user_role, current_user_id, task.created_by)

    assignees = await repo.get_assignees(db, task_id)
    for a in assignees:
        if a.employee_id == employee_id:
            a.is_deleted = True
            a.deleted_at = datetime.now(timezone.utc)
            break
    await db.commit()


async def add_comment(
    db: AsyncSession, task_id: UUID, data: CommentCreate,
    author_id: UUID, company_id: str
) -> TaskComment:
    task = await repo.get_task(db, task_id, company_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    comment = TaskComment(
        task_id=task_id,
        author_id=author_id,
        company_id=company_id,
        body=data.body,
        parent_comment_id=data.parent_comment_id,
    )
    db.add(comment)
    await db.commit()
    return comment


async def edit_comment(
    db: AsyncSession, comment_id: UUID, data: CommentUpdate,
    current_user_id: UUID, company_id: str
) -> TaskComment:
    comment = await repo.get_comment(db, comment_id, company_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    check_permission("comment:edit", "", current_user_id, comment.author_id)
    comment.body = data.body
    comment.status = "edited"
    comment.edited_at = datetime.now(timezone.utc)
    await db.commit()
    return comment


async def delete_comment(
    db: AsyncSession, comment_id: UUID,
    current_user_id: UUID, current_user_role: str, company_id: str
) -> None:
    comment = await repo.get_comment(db, comment_id, company_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    check_permission("comment:delete", current_user_role, current_user_id, comment.author_id)
    comment.is_deleted = True
    comment.deleted_at = datetime.now(timezone.utc)
    await db.commit()
