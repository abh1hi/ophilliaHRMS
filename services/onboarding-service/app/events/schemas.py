"""Pydantic models for validating incoming RabbitMQ event payloads.

Every consumer validates the raw JSON against these models before processing.
Malformed payloads are rejected to DLQ immediately (no retries for schema errors).
"""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class BaseEventEnvelope(BaseModel):
    """Standard event envelope used across all HRMS services."""
    event_id: str
    event_type: str
    event_version: str = "v1"
    service_source: str = ""
    correlation_id: str = ""
    timestamp: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)


class CompanyCreatedPayload(BaseModel):
    company_id: UUID
    name: Optional[str] = None
    region: Optional[str] = None


class DomainInitializedPayload(BaseModel):
    """Shared payload for *.initialized events (departments, leave_type, etc.)."""
    company_id: UUID


class EmployeeCreatedPayload(BaseModel):
    company_id: UUID
    employee_id: Optional[str] = None
    user_id: Optional[str] = None


# Map event_type → expected payload model
EVENT_PAYLOAD_SCHEMAS: dict[str, type[BaseModel]] = {
    "company.created": CompanyCreatedPayload,
    "department.initialized": DomainInitializedPayload,
    "leave_type.initialized": DomainInitializedPayload,
    "salary_structure.initialized": DomainInitializedPayload,
    "attendance_policy.initialized": DomainInitializedPayload,
    "employee.created": EmployeeCreatedPayload,
}


def validate_event_payload(event_type: str, payload: dict) -> BaseModel:
    """Validate payload against the schema for the given event_type.

    Returns the validated model instance.
    Raises ValidationError if payload is malformed.
    Uses DomainInitializedPayload as fallback for unknown event types.
    """
    schema = EVENT_PAYLOAD_SCHEMAS.get(event_type, DomainInitializedPayload)
    return schema.model_validate(payload)
