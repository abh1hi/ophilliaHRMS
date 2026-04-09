"""Leave Ledger Entry — immutable log of every leave balance change.

Created on: allocation, leave application, adjustment, encashment.
Positive leaves = added; negative leaves = consumed/deducted.
"""
from sqlalchemy import Column, String, Float, Date, DateTime, Integer, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class LeaveLedgerEntry(Base):
    __tablename__ = "leave_ledger_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    leave_type_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Transaction dates
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)

    # Positive = credits, Negative = debits
    leaves = Column(Float, nullable=False)

    # Transaction source: "allocation" | "application" | "adjustment" | "encashment" | "carry_forward"
    transaction_type = Column(String(30), nullable=False, index=True)

    # ID of the source document (allocation_id, leave_request_id, etc.)
    transaction_name = Column(String(100), nullable=True)

    # Flags
    is_carry_forward = Column(Integer, nullable=False, default=0)
    is_expired = Column(Integer, nullable=False, default=0)
    is_lwp = Column(Integer, nullable=False, default=0)   # Leave Without Pay

    holiday_list_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_ledger_company_emp_type", "company_id", "employee_id", "leave_type_id"),
        Index("ix_ledger_transaction_type", "transaction_type"),
    )
