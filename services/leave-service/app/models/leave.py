from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.db.base import Base
from app.core.constants import LeaveStatus


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class LeaveType(Base):
    __tablename__ = "leave_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(100), index=True, nullable=False)
    description = Column(String(255), nullable=True)
    days_allowed = Column(Integer, nullable=False)
    requires_approval = Column(Integer, default=1, nullable=False)  # 1=True, 0=False
    is_active = Column(Integer, default=1, nullable=False)  # 1=True, 0=False

    # ── Extended fields added in migration 0005 ────────────────────────────
    is_carry_forward = Column(Integer, default=0, nullable=True)
    is_leave_without_pay = Column(Integer, default=0, nullable=True)
    is_compensatory = Column(Integer, default=0, nullable=True)
    is_optional_leave = Column(Integer, default=0, nullable=True)
    allow_negative_balance = Column(Integer, default=0, nullable=True)
    allow_over_allocation = Column(Integer, default=0, nullable=True)
    include_holidays_in_leaves = Column(Integer, default=0, nullable=True)
    is_partially_paid = Column(Integer, default=0, nullable=True)
    fraction_of_daily_salary = Column(Integer, default=0, nullable=True)

    # Earned leave: credits accumulate at each interval
    is_earned_leave = Column(Integer, default=0, nullable=True)
    # "monthly" | "quarterly" | "half-yearly" | "yearly"
    earned_leave_frequency = Column(String(20), nullable=True)

    # Leave encashment
    allow_encashment = Column(Integer, default=0, nullable=True)
    non_encashable_leaves = Column(Integer, default=0, nullable=True)

    # Limits
    max_consecutive_days = Column(Integer, nullable=True)
    applicable_after_working_days = Column(Integer, default=0, nullable=True)
    max_leaves_allowed = Column(Integer, nullable=True)
    # ── End extended fields ─────────────────────────────────────────────────

    balances = relationship("LeaveBalance", back_populates="leave_type", cascade="all, delete-orphan")
    requests = relationship("LeaveRequest", back_populates="leave_type", cascade="all, delete-orphan")


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    leave_type_id = Column(UUID(as_uuid=True), ForeignKey("leave_types.id", ondelete="CASCADE"), nullable=False)
    total_days = Column(Integer, nullable=False, default=0)
    used_days = Column(Integer, nullable=False, default=0)
    pending_days = Column(Integer, nullable=False, default=0)
    year = Column(Integer, nullable=False, index=True)

    leave_type = relationship("LeaveType", back_populates="balances")

    __table_args__ = (
        Index("ix_leave_balance_emp_year", "employee_id", "year"),
    )


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    leave_type_id = Column(UUID(as_uuid=True), ForeignKey("leave_types.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_days = Column(Integer, nullable=False) # Or float if half days allowed
    duration_type = Column(String(20), nullable=False, default="FULL_DAY")
    is_emergency = Column(Integer, default=0, nullable=False) # 1=True, 0=False
    reason = Column(Text, nullable=False)
    supporting_document = Column(String(255), nullable=True)
    status = Column(
        String(20),
        nullable=False,
        default=LeaveStatus.PENDING.value,
        index=True,
    )
    approved_by_id = Column(UUID(as_uuid=True), nullable=True) # Superceded by approvals table but kept for immediate caching
    manager_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    leave_type = relationship("LeaveType", back_populates="requests")
    approvals = relationship("LeaveApproval", back_populates="leave_request", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_leave_request_emp_status", "employee_id", "status"),
        Index("ix_leave_request_dates", "start_date", "end_date"),
    )


class LeaveApproval(Base):
    __tablename__ = "leave_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    leave_request_id = Column(UUID(as_uuid=True), ForeignKey("leave_requests.id", ondelete="CASCADE"), nullable=False)
    approver_id = Column(UUID(as_uuid=True), nullable=False)
    level = Column(String(50), nullable=False) # PROJECT_IN_CHARGE, HR, SUPER_ADMIN
    status = Column(String(20), nullable=False, default=LeaveStatus.PENDING.value)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    leave_request = relationship("LeaveRequest", back_populates="approvals")

    __table_args__ = (
        Index("ix_leave_approval_req_level", "leave_request_id", "level"),
    )


class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    date = Column(Date, index=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Integer, default=1, nullable=False) # 1=True, 0=False
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)
