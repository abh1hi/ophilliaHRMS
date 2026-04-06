from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


class CalendarCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    calendar_type: str = "team"
    workspace_id: Optional[UUID] = None
    is_public: bool = False


class CalendarUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    is_public: Optional[bool] = None
    webhook_url: Optional[str] = None


class CalendarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    company_id: UUID
    workspace_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    calendar_type: str
    owner_id: UUID
    is_default: bool
    is_public: bool
    google_calendar_id: Optional[str] = None
    public_share_token: Optional[str] = None
    webhook_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ShareTokenResponse(BaseModel):
    share_token: str
    share_url: str
