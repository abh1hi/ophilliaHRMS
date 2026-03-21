from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.core.constants import NotificationType, NotificationStatus

# Preference Schemas
class PreferenceBase(BaseModel):
    email_enabled: bool = True
    sms_enabled: bool = True

class PreferenceCreate(PreferenceBase):
    user_id: UUID

class PreferenceUpdate(PreferenceBase):
    pass

class PreferenceResponse(PreferenceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    company_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

# Log Schemas
class NotificationLogBase(BaseModel):
    company_id: UUID
    user_id: UUID
    type: NotificationType
    subject: Optional[str] = None
    message: str

class NotificationLogCreate(NotificationLogBase):
    status: NotificationStatus = NotificationStatus.PENDING
    error_message: Optional[str] = None

class NotificationLogResponse(NotificationLogBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: NotificationStatus
    error_message: Optional[str] = None
    created_at: datetime
    sent_at: Optional[datetime] = None
