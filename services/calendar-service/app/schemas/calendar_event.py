from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime, date


class AttendeeIn(BaseModel):
    employee_id: UUID
    rsvp_status: str = "pending"


class EventCreate(BaseModel):
    calendar_id: UUID
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    event_type: str = "meeting"
    start_time: datetime
    end_time: datetime
    all_day: bool = False
    timezone: str = "UTC"
    rrule: Optional[str] = None
    attendees: List[AttendeeIn] = []
    color: Optional[str] = None
    reminder_minutes: List[int] = []


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    event_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    all_day: Optional[bool] = None
    timezone: Optional[str] = None
    rrule: Optional[str] = None
    color: Optional[str] = None
    status: Optional[str] = None
    attendees: Optional[List[AttendeeIn]] = None
    reminder_minutes: Optional[List[int]] = None


class RSVPRequest(BaseModel):
    rsvp_status: str  # accepted | declined | tentative


class OccurrenceOverrideRequest(BaseModel):
    new_start_time: Optional[datetime] = None
    new_end_time: Optional[datetime] = None
    new_title: Optional[str] = None
    new_description: Optional[str] = None
    new_location: Optional[str] = None
    new_all_day: Optional[bool] = None


class CalendarEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    company_id: UUID
    calendar_id: UUID
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    event_type: str
    start_time: datetime
    end_time: datetime
    all_day: bool
    timezone: str
    rrule: Optional[str] = None
    recurrence_master_id: Optional[UUID] = None
    status: str
    created_by: UUID
    attendees: List[Any] = []
    color: Optional[str] = None
    reminder_minutes: List[Any] = []
    google_event_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
