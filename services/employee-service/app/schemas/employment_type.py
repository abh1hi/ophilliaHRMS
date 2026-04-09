from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime


class EmploymentTypeCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Employment type name must not be empty")
        return v.strip()


class EmploymentTypeUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[int] = None


class EmploymentTypeResponse(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    is_active: int = 1
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
