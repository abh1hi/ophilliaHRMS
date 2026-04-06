"""Leave Allocation — formal allocation of a specific leave type for an employee.

Created automatically when a LeavePolicyAssignment is submitted.
Can also be created manually. Tracks carry-forward from prior periods.
"""
from sqlalchemy import Column, Float, Date, DateTime, Integer, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class LeaveAllocation(Base):
    __tablename__ = "leave_allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    leave_type_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Optional: link to the policy assignment that created this allocation
    assignment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("leave_policy_assignments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    leave_period_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)

    # Base allocation from policy
    new_leaves_allocated = Column(Float, nullable=False, default=0)
    # Carry-forward from previous period
    carry_forward_days = Column(Float, nullable=False, default=0)
    # Total = new_leaves_allocated + carry_forward_days + adjustments
    total_leaves_allocated = Column(Float, nullable=False, default=0)

    # Running balance (updated on leave consumption)
    used_leaves = Column(Float, nullable=False, default=0)
    leaves_pending_approval = Column(Float, nullable=False, default=0)

    # "active" | "expired" | "cancelled"
    status = Column(String(20), nullable=False, default="active")

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    assignment = relationship("LeavePolicyAssignment", back_populates="allocations")

    __table_args__ = (
        Index("ix_leave_alloc_emp_type", "company_id", "employee_id", "leave_type_id"),
    )
