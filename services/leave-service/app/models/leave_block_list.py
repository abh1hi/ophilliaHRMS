"""Leave Block List — dates on which employees cannot apply for leave.

LeaveBlockListDate: individual blocked dates + reason.
LeaveBlockListAllowed: users who CAN approve leave on blocked dates (override).
"""
from sqlalchemy import Column, String, Date, DateTime, Integer, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class LeaveBlockList(Base):
    __tablename__ = "leave_block_lists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    # If 1, applies to entire company; otherwise only tagged departments
    applies_to_company = Column(Integer, nullable=False, default=0)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    dates = relationship(
        "LeaveBlockListDate", back_populates="block_list",
        cascade="all, delete-orphan", lazy="selectin",
    )
    allowed_users = relationship(
        "LeaveBlockListAllowed", back_populates="block_list",
        cascade="all, delete-orphan", lazy="selectin",
    )


class LeaveBlockListDate(Base):
    __tablename__ = "leave_block_list_dates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    block_list_id = Column(
        UUID(as_uuid=True),
        ForeignKey("leave_block_lists.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    block_date = Column(Date, nullable=False, index=True)
    reason = Column(String(300), nullable=True)

    block_list = relationship("LeaveBlockList", back_populates="dates")


class LeaveBlockListAllowed(Base):
    """Users who can approve leave applications even on blocked dates."""
    __tablename__ = "leave_block_list_allowed"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    block_list_id = Column(
        UUID(as_uuid=True),
        ForeignKey("leave_block_lists.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    # employee_id of the approver who is allowed to override blocks
    approver_employee_id = Column(UUID(as_uuid=True), nullable=False)

    block_list = relationship("LeaveBlockList", back_populates="allowed_users")
