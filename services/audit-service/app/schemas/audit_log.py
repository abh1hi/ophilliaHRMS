from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """Full audit log row returned by API."""
    id: UUID
    event_id: UUID
    event_version: int
    event_type: str
    service_source: str
    company_id: UUID
    user_id: Optional[UUID] = None
    correlation_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    http_method: Optional[str] = None
    endpoint: Optional[str] = None
    payload: dict
    timestamp: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Paginated list response."""
    items: List[AuditLogResponse]
    total: int
    skip: int
    limit: int


class AuditLogFilter(BaseModel):
    """Query parameters for filtering audit logs."""
    event_type: Optional[str] = Field(None, description="Filter by event type (e.g. employee.created)")
    service_source: Optional[str] = Field(None, description="Filter by originating service")
    user_id: Optional[UUID] = Field(None, description="Filter by actor user ID")
    company_id: Optional[UUID] = Field(None, description="Filter by tenant company ID")
    correlation_id: Optional[UUID] = Field(None, description="Filter by correlation/trace ID")
    date_from: Optional[datetime] = Field(None, description="Start of date range (inclusive)")
    date_to: Optional[datetime] = Field(None, description="End of date range (inclusive)")
    skip: int = Field(0, ge=0, description="Pagination offset")
    limit: int = Field(50, ge=1, le=500, description="Page size (max 500)")
