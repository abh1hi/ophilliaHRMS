from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime, date


class ShiftScheduleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Schedule name must not be empty")
        return v.strip()


class ShiftScheduleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: Optional[int] = None


class ShiftScheduleResponse(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    description: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
