from typing import Optional, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, field_validator
from typing import Literal


class CheckinCreate(BaseModel):
    employee_id: UUID
    log_datetime: datetime
    log_type: Literal["IN", "OUT"]
    device_id: Optional[str] = None
    shift_type_id: Optional[UUID] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    skip_auto_attendance: int = 0


class CheckinUpdate(BaseModel):
    skip_auto_attendance: Optional[int] = None
    shift_type_id: Optional[UUID] = None


class CheckinResponse(BaseModel):
    id: UUID
    company_id: UUID
    employee_id: UUID
    log_datetime: datetime
    log_type: str
    device_id: Optional[str] = None
    shift_type_id: Optional[UUID] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    skip_auto_attendance: int
    attendance_record_id: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CheckinListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    checkins: List[CheckinResponse]
