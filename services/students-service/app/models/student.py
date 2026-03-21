import uuid
import enum
from datetime import date, datetime, timezone

from sqlalchemy import String, Date, Enum as SAEnum, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class StudentStatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    graduated = "graduated"
    expelled = "expelled"


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    student_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[GenderEnum] = mapped_column(SAEnum(GenderEnum), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    class_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    enrollment_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    status: Mapped[StudentStatusEnum] = mapped_column(
        SAEnum(StudentStatusEnum), nullable=False, default=StudentStatusEnum.active
    )

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=text("NOW()"),
    )

    # Relationships (within same service DB only)
    class_: Mapped["Class"] = relationship("Class", back_populates="students")
    guardians: Mapped[list["Guardian"]] = relationship(
        "Guardian", back_populates="student", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_students_status", "status"),
        Index("ix_students_class_id", "class_id"),
    )
