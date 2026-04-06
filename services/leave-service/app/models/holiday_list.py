"""Holiday List — named list of holidays with a date range.

Each company can have multiple HolidayLists (e.g. Head Office, Branch, Optional).
HolidayListEntry stores the individual holiday dates within the list.
"""
from sqlalchemy import Column, String, Date, DateTime, Integer, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class HolidayList(Base):
    __tablename__ = "holiday_lists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    entries = relationship(
        "HolidayListEntry",
        back_populates="holiday_list",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_holiday_list_company", "company_id"),
    )


class HolidayListEntry(Base):
    __tablename__ = "holiday_list_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    holiday_list_id = Column(
        UUID(as_uuid=True),
        ForeignKey("holiday_lists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date = Column(Date, nullable=False, index=True)
    description = Column(String(200), nullable=True)

    holiday_list = relationship("HolidayList", back_populates="entries")
