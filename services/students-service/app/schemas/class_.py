from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


# ── Request Schemas ──────────────────────────────────────────────────────────

class ClassCreate(BaseModel):
    name: str
    grade_level: int
    section: str
    academic_year: str
    capacity: int = 40

    @field_validator("grade_level")
    @classmethod
    def grade_level_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("grade_level must be >= 1")
        return v

    @field_validator("capacity")
    @classmethod
    def capacity_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("capacity must be >= 1")
        return v


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    grade_level: Optional[int] = None
    section: Optional[str] = None
    academic_year: Optional[str] = None
    capacity: Optional[int] = None


# ── Response Schemas ─────────────────────────────────────────────────────────

class ClassResponse(BaseModel):
    id: uuid.UUID
    name: str
    grade_level: int
    section: str
    academic_year: str
    capacity: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClassListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ClassResponse]
