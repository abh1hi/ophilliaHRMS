from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime


class GoogleIntegrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    employee_id: UUID
    google_email: Optional[str] = None
    connected_calendars: List[Any] = []
    status: str
    last_synced_at: Optional[datetime] = None
    sync_error_count: int
    created_at: datetime


class ConnectCalendarsRequest(BaseModel):
    calendar_ids: List[str]


class SyncLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    resource_type: str
    sync_direction: str
    sync_status: str
    error_message: Optional[str] = None
    synced_at: datetime
    retry_count: int
