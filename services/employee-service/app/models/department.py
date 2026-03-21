from sqlalchemy import Column, String, DateTime, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Department(Base):
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(150), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    manager_id = Column(UUID(as_uuid=True), nullable=True)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(
        DateTime, default=naive_utcnow, nullable=False
    )
    updated_at = Column(
        DateTime,
        default=naive_utcnow,
        onupdate=naive_utcnow,
        nullable=False,
    )

    # Relationships
    employees = relationship("Employee", back_populates="department")

    __table_args__ = (
        Index("ix_departments_name", "name"),
        Index("ix_departments_created_at", "created_at"),
    )
