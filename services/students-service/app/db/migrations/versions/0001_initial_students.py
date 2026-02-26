"""Initial student tables with multi-tenancy

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── classes ──────────────────────────────────────────────────────────────
    op.create_table(
        "classes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("grade_level", sa.Integer(), nullable=False),
        sa.Column("section", sa.String(10), nullable=False),
        sa.Column("academic_year", sa.String(20), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="40"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_classes_academic_year", "classes", ["academic_year"])
    op.create_index("ix_classes_grade_level", "classes", ["grade_level"])
    op.create_index("ix_classes_company_id", "classes", ["company_id"])

    # ── students ─────────────────────────────────────────────────────────────
    op.create_table(
        "students",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_number", sa.String(50), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("gender", sa.String(10), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column(
            "class_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("classes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("enrollment_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_students_student_number", "students", ["student_number"], unique=True)
    op.create_index("ix_students_status", "students", ["status"])
    op.create_index("ix_students_class_id", "students", ["class_id"])
    op.create_index("ix_students_company_id", "students", ["company_id"])

    # ── guardians ────────────────────────────────────────────────────────────
    op.create_table(
        "guardians",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("relationship", sa.String(20), nullable=False),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_guardians_student_id", "guardians", ["student_id"])
    op.create_index("ix_guardians_company_id", "guardians", ["company_id"])


def downgrade() -> None:
    op.drop_table("guardians")
    op.drop_table("students")
    op.drop_table("classes")
