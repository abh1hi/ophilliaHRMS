from pydantic import BaseModel, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class EmployeeGroupCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Employee group name must not be empty")
        return v.strip()


class EmployeeGroupUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[int] = None


class MemberResponse(BaseModel):
    employee_id: UUID

    model_config = {"from_attributes": True}


class EmployeeGroupResponse(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    is_active: int = 1
    created_at: datetime
    updated_at: datetime
    members: List[MemberResponse] = []

    model_config = {"from_attributes": True}
