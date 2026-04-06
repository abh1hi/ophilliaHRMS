from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    workspace_type: str = "team"
    color: Optional[str] = None
    icon: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    workspace_type: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    company_id: UUID
    name: str
    description: Optional[str] = None
    workspace_type: str
    color: Optional[str] = None
    icon: Optional[str] = None
    owner_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class WorkspaceMemberCreate(BaseModel):
    employee_id: UUID
    role: str = "member"


class WorkspaceMemberUpdate(BaseModel):
    role: str


class WorkspaceMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workspace_id: UUID
    employee_id: UUID
    role: str
    joined_at: datetime
    invited_by: Optional[UUID] = None
