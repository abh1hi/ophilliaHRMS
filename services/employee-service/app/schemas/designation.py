from pydantic import BaseModel, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class DesignationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Designation name must not be empty")
        return v.strip()


class DesignationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    is_active: Optional[int] = None


class DesignationResponse(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    is_active: int = 1
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
