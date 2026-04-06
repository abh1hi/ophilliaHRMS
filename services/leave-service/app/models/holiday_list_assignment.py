"""Holiday List Assignment — binds a HolidayList to a Company or Employee.

Multiple assignments can exist; the most recent by assignment_from is active.
Employee-level assignments take precedence over company-level.
"""
from sqlalchemy import Column, String, Date, DateTime, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class HolidayListAssignment(Base):
    __tablename__ = "holiday_list_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # applicable_for: "company" | "employee"
    applicable_for = Column(String(20), nullable=False)
    employee_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    holiday_list_id = Column(
        UUID(as_uuid=True),
        ForeignKey("holiday_lists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Date from which this assignment is effective
    assignment_from = Column(Date, nullable=False)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_hl_assignment_company_emp", "company_id", "employee_id", "assignment_from"),
    )
