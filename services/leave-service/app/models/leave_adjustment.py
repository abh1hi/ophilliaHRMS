"""Leave Adjustment — corrects an existing Leave Allocation (increase or decrease)."""
from sqlalchemy import Column, String, Float, Date, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class LeaveAdjustment(Base):
    __tablename__ = "leave_adjustments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    allocation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("leave_allocations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # "allocate" (add) | "reduce" (subtract)
    adjustment_type = Column(String(20), nullable=False)
    adjustment_days = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)

    # Who performed the adjustment
    adjusted_by = Column(UUID(as_uuid=True), nullable=False)
    adjustment_date = Column(Date, nullable=False)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_leave_adjustment_alloc", "allocation_id"),
    )
