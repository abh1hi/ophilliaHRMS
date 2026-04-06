"""Leave Policy — defines how many leaves of each type are allocated per Leave Period."""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class LeavePolicy(Base):
    __tablename__ = "leave_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    items = relationship(
        "LeavePolicyItem",
        back_populates="policy",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    assignments = relationship("LeavePolicyAssignment", back_populates="policy")

    __table_args__ = (
        Index("ix_leave_policy_company", "company_id"),
    )


class LeavePolicyItem(Base):
    """One row per LeaveType within a policy, specifying annual allocation."""
    __tablename__ = "leave_policy_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("leave_policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    leave_type_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    annual_allocation = Column(Float, nullable=False, default=0)

    policy = relationship("LeavePolicy", back_populates="items")
