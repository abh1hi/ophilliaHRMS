import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, ForeignKey, Enum as SAEnum, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class RelationshipEnum(str, enum.Enum):
    father = "father"
    mother = "mother"
    legal_guardian = "legal_guardian"
    other = "other"


class Guardian(Base):
    __tablename__ = "guardians"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    relationship: Mapped[RelationshipEnum] = mapped_column(
        SAEnum(RelationshipEnum), nullable=False
    )
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        server_default=text("NOW()"),
    )

    # Relationships
    student: Mapped["Student"] = orm_relationship("Student", back_populates="guardians")

    __table_args__ = (
        Index("ix_guardians_student_id", "student_id"),
    )
