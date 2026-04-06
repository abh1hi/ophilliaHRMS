from pydantic import BaseModel, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    manager_id: Optional[UUID] = None
    is_group: int = 0
    parent_department_id: Optional[UUID] = None
    leave_block_list: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Department name must not be empty")
        return v.strip()


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    manager_id: Optional[UUID] = None
    is_group: Optional[int] = None
    parent_department_id: Optional[UUID] = None
    leave_block_list: Optional[str] = None
    is_active: Optional[int] = None


class DepartmentResponse(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    description: Optional[str] = None
    manager_id: Optional[UUID] = None
    is_group: int = 0
    parent_department_id: Optional[UUID] = None
    leave_block_list: Optional[str] = None
    is_active: int = 1
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DepartmentListResponse(BaseModel):
    total: int
    departments: List[DepartmentResponse]
