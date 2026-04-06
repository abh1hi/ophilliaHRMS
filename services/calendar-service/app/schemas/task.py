from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime


class TaskCreate(BaseModel):
    workspace_id: Optional[UUID] = None
    event_id: Optional[UUID] = None
    parent_task_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    tags: List[str] = []
    assignees: List[UUID] = []


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    tags: Optional[List[str]] = None


class TaskStatusUpdate(BaseModel):
    status: str


class AssigneeAdd(BaseModel):
    employee_id: UUID


class CommentCreate(BaseModel):
    body: str
    parent_comment_id: Optional[UUID] = None


class CommentUpdate(BaseModel):
    body: str


class TaskAssigneeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    task_id: UUID
    employee_id: UUID
    assigned_at: datetime
    assigned_by: Optional[UUID] = None


class TaskCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    task_id: UUID
    author_id: UUID
    parent_comment_id: Optional[UUID] = None
    body: str
    status: str
    edited_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CalendarTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    company_id: UUID
    workspace_id: Optional[UUID] = None
    event_id: Optional[UUID] = None
    parent_task_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    created_by: UUID
    completed_at: Optional[datetime] = None
    tags: List[Any] = []
    attachments: List[Any] = []
    google_task_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
