from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.guardian import RelationshipEnum


# ── Request Schemas ──────────────────────────────────────────────────────────

class GuardianCreate(BaseModel):
    student_id: uuid.UUID
    first_name: str
    last_name: str
    relationship: RelationshipEnum
    phone: str
    email: Optional[EmailStr] = None
    is_primary: bool = False


class GuardianUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    relationship: Optional[RelationshipEnum] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    is_primary: Optional[bool] = None


# ── Response Schemas ─────────────────────────────────────────────────────────

class GuardianResponse(BaseModel):
    id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    student_id: uuid.UUID
    first_name: str
    last_name: str
    relationship: RelationshipEnum
    phone: str
    email: Optional[str] = None
    is_primary: bool
    created_at: datetime

    model_config = {"from_attributes": True}
