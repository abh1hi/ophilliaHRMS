from pydantic import BaseModel, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime


# ──────────── CREATE ────────────
class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    manager_id: Optional[UUID] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Department name must not be empty")
        return v.strip()


# ──────────── UPDATE ────────────
class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    manager_id: Optional[UUID] = None


# ──────────── RESPONSE ────────────
class DepartmentResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    manager_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ──────────── LIST ────────────
class DepartmentListResponse(BaseModel):
    total: int
    departments: List[DepartmentResponse]
