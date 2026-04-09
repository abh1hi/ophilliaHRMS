from sqlalchemy import Column, String, DateTime, Integer, Index, Table, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


employee_group_members = Table(
    "employee_group_members",
    Base.metadata,
    Column("group_id", UUID(as_uuid=True), ForeignKey("employee_groups.id", ondelete="CASCADE"), primary_key=True),
    Column("employee_id", UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True),
    Column("company_id", UUID(as_uuid=True), nullable=False),
    Column("joined_at", DateTime, default=_now, nullable=False),
    Index("ix_egm_group_id", "group_id"),
    Index("ix_egm_employee_id", "employee_id"),
    Index("ix_egm_company_id", "company_id"),
)


class EmployeeGroup(Base):
    __tablename__ = "employee_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    members = relationship("Employee", secondary=employee_group_members, lazy="selectin")

    __table_args__ = (
        Index("ix_employee_groups_company_name", "company_id", "name", unique=True),
    )
