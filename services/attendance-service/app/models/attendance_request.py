from sqlalchemy import Column, String, Date, DateTime, Integer, Index, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AttendanceRequest(Base):
    __tablename__ = "attendance_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Date range for the regularization request
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)

    # Reason: "on_site_duty" | "work_from_home" | "other"
    reason = Column(String(50), nullable=False)
    explanation = Column(Text, nullable=True)

    # 1 = create records for weekends / holidays too
    include_holidays = Column(Integer, nullable=False, default=0)

    # Half-day settings
    half_day = Column(Integer, nullable=False, default=0)
    half_day_date = Column(Date, nullable=True)

    # Workflow: "pending" | "approved" | "rejected" | "cancelled"
    status = Column(String(20), nullable=False, default="pending", index=True)

    # Review metadata
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_note = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_att_request_company_employee_status", "company_id", "employee_id", "status"),
    )
