from fastapi import APIRouter, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.api.v1.dependencies import DB, AnyUser
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskStatusUpdate, AssigneeAdd,
    CommentCreate, CommentUpdate,
    CalendarTaskResponse, TaskAssigneeResponse, TaskCommentResponse,
)
from app.core.responses import APIResponse
from app.repositories import task_repository as repo
from app.services import task_service as svc

router = APIRouter()


@router.get("/", response_model=APIResponse[List[CalendarTaskResponse]])
async def list_tasks(
    workspace_id: Optional[UUID] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_id: Optional[UUID] = None,
    fields: Optional[str] = None,
    limit: int = 50,
    *,
    db: DB,
    current_user: AnyUser,
):
    from app.core.cache import cache_get, cache_set, tasks_list_key
    cache_key = tasks_list_key(current_user.company_id, str(workspace_id), str(status))
    cached = await cache_get(cache_key)
    if cached and not assignee_id and not fields:
        return APIResponse(success=True, data=cached)

    items = await repo.list_tasks(db, current_user.company_id, workspace_id, status, priority, assignee_id, limit=limit)
    if not assignee_id and not fields:
        await cache_set(cache_key, [i.__dict__ for i in items], ttl=120)
    return APIResponse(success=True, data=items)


@router.post("/", response_model=APIResponse[CalendarTaskResponse], status_code=status.HTTP_201_CREATED)
async def create_task(data: TaskCreate, *, db: DB, current_user: AnyUser):
    task = await svc.create_task(db, data, UUID(current_user.sub), current_user.company_id)
    return APIResponse(success=True, data=task)


@router.get("/{task_id}", response_model=APIResponse[CalendarTaskResponse])
async def get_task(task_id: UUID, *, db: DB, current_user: AnyUser):
    task = await repo.get_task(db, task_id, current_user.company_id)
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")
    return APIResponse(success=True, data=task)


@router.patch("/{task_id}", response_model=APIResponse[CalendarTaskResponse])
async def update_task(task_id: UUID, data: TaskUpdate, *, db: DB, current_user: AnyUser):
    task = await svc.update_task(db, task_id, data, UUID(current_user.sub), current_user.role, current_user.company_id)
    return APIResponse(success=True, data=task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: UUID, *, db: DB, current_user: AnyUser):
    await svc.delete_task(db, task_id, UUID(current_user.sub), current_user.role, current_user.company_id)


@router.patch("/{task_id}/status", response_model=APIResponse[CalendarTaskResponse])
async def update_status(task_id: UUID, data: TaskStatusUpdate, *, db: DB, current_user: AnyUser):
    task = await svc.update_task_status(db, task_id, data, UUID(current_user.sub), current_user.role, current_user.company_id)
    return APIResponse(success=True, data=task)


@router.post("/{task_id}/assignees", response_model=APIResponse[TaskAssigneeResponse], status_code=status.HTTP_201_CREATED)
async def add_assignee(task_id: UUID, data: AssigneeAdd, *, db: DB, current_user: AnyUser):
    assignee = await svc.add_assignee(db, task_id, data, UUID(current_user.sub), current_user.role, current_user.company_id)
    return APIResponse(success=True, data=assignee)


@router.delete("/{task_id}/assignees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_assignee(task_id: UUID, employee_id: UUID, *, db: DB, current_user: AnyUser):
    await svc.remove_assignee(db, task_id, employee_id, UUID(current_user.sub), current_user.role, current_user.company_id)


@router.get("/{task_id}/comments", response_model=APIResponse[List[TaskCommentResponse]])
async def list_comments(task_id: UUID, *, db: DB, current_user: AnyUser):
    comments = await repo.get_comments(db, task_id, current_user.company_id)
    return APIResponse(success=True, data=comments)


@router.post("/{task_id}/comments", response_model=APIResponse[TaskCommentResponse], status_code=status.HTTP_201_CREATED)
async def add_comment(task_id: UUID, data: CommentCreate, *, db: DB, current_user: AnyUser):
    comment = await svc.add_comment(db, task_id, data, UUID(current_user.sub), current_user.company_id)
    return APIResponse(success=True, data=comment)


@router.patch("/{task_id}/comments/{comment_id}", response_model=APIResponse[TaskCommentResponse])
async def edit_comment(task_id: UUID, comment_id: UUID, data: CommentUpdate, *, db: DB, current_user: AnyUser):
    comment = await svc.edit_comment(db, comment_id, data, UUID(current_user.sub), current_user.company_id)
    return APIResponse(success=True, data=comment)


@router.delete("/{task_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(task_id: UUID, comment_id: UUID, *, db: DB, current_user: AnyUser):
    await svc.delete_comment(db, comment_id, UUID(current_user.sub), current_user.role, current_user.company_id)


@router.get("/{task_id}/subtasks", response_model=APIResponse[List[CalendarTaskResponse]])
async def list_subtasks(task_id: UUID, *, db: DB, current_user: AnyUser):
    subtasks = await repo.get_subtasks(db, task_id, current_user.company_id)
    return APIResponse(success=True, data=subtasks)


@router.post("/{task_id}/subtasks", response_model=APIResponse[CalendarTaskResponse], status_code=status.HTTP_201_CREATED)
async def create_subtask(task_id: UUID, data: TaskCreate, *, db: DB, current_user: AnyUser):
    data_with_parent = data.model_copy(update={"parent_task_id": task_id})
    task = await svc.create_task(db, data_with_parent, UUID(current_user.sub), current_user.company_id)
    return APIResponse(success=True, data=task)
