from __future__ import annotations
import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

from app.models.student import GenderEnum, StudentStatusEnum


# ── Request Schemas ──────────────────────────────────────────────────────────

class StudentCreate(BaseModel):
    student_number: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: GenderEnum
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    class_id: Optional[uuid.UUID] = None
    enrollment_date: Optional[date] = None

    @field_validator("student_number")
    @classmethod
    def student_number_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("student_number must not be empty")
        return v


class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    class_id: Optional[uuid.UUID] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None


class StudentStatusUpdate(BaseModel):
    status: StudentStatusEnum


# ── Response Schemas ─────────────────────────────────────────────────────────

class StudentResponse(BaseModel):
    id: uuid.UUID
    student_number: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: GenderEnum
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    class_id: Optional[uuid.UUID] = None
    enrollment_date: date
    status: StudentStatusEnum
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StudentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[StudentResponse]
