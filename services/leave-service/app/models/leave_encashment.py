"""Leave Encashment — exchange unused leaves for monetary compensation."""
from sqlalchemy import Column, String, Float, Date, DateTime, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class LeaveEncashment(Base):
    __tablename__ = "leave_encashments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    leave_type_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    leave_period_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    leave_allocation_id = Column(UUID(as_uuid=True), nullable=True)

    leave_balance = Column(Float, nullable=False, default=0)
    encashable_days = Column(Float, nullable=False, default=0)
    encashment_amount = Column(Float, nullable=False, default=0)

    # Date from which the payment will be included in payroll
    encashment_date = Column(Date, nullable=True)

    # "submitted" | "paid" | "cancelled"
    status = Column(String(20), nullable=False, default="submitted", index=True)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_leave_encashment_company_emp", "company_id", "employee_id"),
    )
