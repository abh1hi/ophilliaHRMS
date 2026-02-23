from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime

from app.core.constants import EmploymentStatus, Gender


# ──────────── CREATE ────────────
class EmployeeCreate(BaseModel):
    user_id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    date_joined: date
    department_id: Optional[UUID] = None
    designation: Optional[str] = None
    address: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name must not be empty")
        return v.strip()


# ──────────── UPDATE ────────────
class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    department_id: Optional[UUID] = None
    designation: Optional[str] = None
    employment_status: Optional[EmploymentStatus] = None
    address: Optional[str] = None


# ──────────── RESPONSE ────────────
class EmployeeResponse(BaseModel):
    id: UUID
    user_id: UUID
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    date_joined: date
    department_id: Optional[UUID] = None
    designation: Optional[str] = None
    employment_status: str
    address: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ──────────── PAGINATED LIST ────────────
class EmployeeListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    employees: List[EmployeeResponse]
