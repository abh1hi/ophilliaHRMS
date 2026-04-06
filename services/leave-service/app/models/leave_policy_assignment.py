"""Leave Policy Assignment — assigns a Leave Policy to an Employee for a period.

On submission, LeaveAllocation records are auto-created for each LeavePolicyItem.
"""
from sqlalchemy import Column, String, Date, DateTime, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class LeavePolicyAssignment(Base):
    __tablename__ = "leave_policy_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    policy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("leave_policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Optional Leave Period linkage (may be null for date-based or joining-based assignment)
    leave_period_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # "leave_period" | "joining_date" | "custom"
    assignment_based_on = Column(String(30), nullable=False, default="custom")

    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)

    # "active" | "cancelled"
    status = Column(String(20), nullable=False, default="active")

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    policy = relationship("LeavePolicy", back_populates="assignments")
    allocations = relationship("LeaveAllocation", back_populates="assignment")

    __table_args__ = (
        Index("ix_lpa_company_employee", "company_id", "employee_id"),
    )
