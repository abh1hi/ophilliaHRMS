"""OvertimeRequest: employee-submitted OT request awaiting HR/manager review."""
from sqlalchemy import Column, String, Float, Date, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class OvertimeRequest(Base):
    """An employee's request to log overtime hours on a specific date.

    Workflow: employee submits (pending) → HR/manager reviews → approved | rejected.
    If approved, HR manually adjusts the attendance record's overtime_hours.
    """
    __tablename__ = "overtime_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False)

    date = Column(Date, nullable=False)
    requested_hours = Column(Float, nullable=False)
    reason = Column(String(500), nullable=False)

    status = Column(String(20), nullable=False, default="pending")  # pending | approved | rejected
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    review_note = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_ot_request_company", "company_id"),
        Index("ix_ot_request_employee", "company_id", "employee_id"),
        Index("ix_ot_request_date", "company_id", "date"),
        Index("ix_ot_request_status", "company_id", "status"),
    )
