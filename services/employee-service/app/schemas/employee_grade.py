from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime


class EmployeeGradeCreate(BaseModel):
    name: str
    default_leave_policy: Optional[str] = None
    default_salary_structure: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Employee grade name must not be empty")
        return v.strip()


class EmployeeGradeUpdate(BaseModel):
    name: Optional[str] = None
    default_leave_policy: Optional[str] = None
    default_salary_structure: Optional[str] = None
    is_active: Optional[int] = None


class EmployeeGradeResponse(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    default_leave_policy: Optional[str] = None
    default_salary_structure: Optional[str] = None
    is_active: int = 1
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
