"""Compensatory Leave Request — for working on a holiday."""
from sqlalchemy import Column, String, Date, DateTime, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CompensatoryLeaveRequest(Base):
    __tablename__ = "compensatory_leave_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Leave type must have is_compensatory=1
    leave_type_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Date(s) the employee worked on holiday
    work_from_date = Column(Date, nullable=False)
    work_end_date = Column(Date, nullable=False)

    reason = Column(Text, nullable=True)

    # "pending" | "approved" | "rejected" | "cancelled"
    status = Column(String(20), nullable=False, default="pending", index=True)

    # ID of the leave allocation updated upon approval
    leave_allocation_id = Column(UUID(as_uuid=True), nullable=True)

    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_note = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_comp_leave_company_emp", "company_id", "employee_id", "status"),
    )
