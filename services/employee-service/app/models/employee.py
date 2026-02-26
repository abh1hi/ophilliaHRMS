from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.db.base import Base
from app.core.constants import EmploymentStatus, Gender


def naive_utcnow():
    """Return current UTC time as a timezone-naive datetime.

    SQLAlchemy DateTime (without timezone=True) requires tz-naive datetimes.
    Using tz-aware datetimes causes: can't subtract offset-naive and offset-aware.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    gender = Column(String(10), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    date_joined = Column(Date, nullable=False)
    department_id = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    designation = Column(String(100), nullable=True)
    employment_status = Column(
        String(20),
        nullable=False,
        default=EmploymentStatus.ACTIVE.value,
        index=True,
    )
    address = Column(String(500), nullable=True)
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
    department = relationship("Department", back_populates="employees")

    __table_args__ = (
        Index("ix_employees_employment_status", "employment_status"),
        Index("ix_employees_department_id", "department_id"),
        Index("ix_employees_created_at", "created_at"),
    )
