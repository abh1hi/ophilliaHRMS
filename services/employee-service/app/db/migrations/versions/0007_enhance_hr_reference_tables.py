"""Enhance HR reference tables: department tree, designation skills, grade policies

Revision ID: 0007_enhance_hr_reference_tables
Revises: 0006_add_hr_reference_tables
Create Date: 2026-04-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "0007_enhance_hr_reference_tables"
down_revision = "0006_add_hr_reference_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── departments: tree structure + leave block list ────────────────────────
    op.add_column("departments", sa.Column("is_group", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("departments", sa.Column(
        "parent_department_id",
        UUID(as_uuid=True),
        sa.ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    ))
    op.add_column("departments", sa.Column("leave_block_list", sa.String(150), nullable=True))
    op.create_index("ix_departments_parent_id", "departments", ["parent_department_id"])

    # ── designations: required skills (JSON array) ────────────────────────────
    op.add_column("designations", sa.Column("required_skills", JSONB(), nullable=True))

    # ── employee_grades: default leave policy + salary structure ──────────────
    op.add_column("employee_grades", sa.Column("default_leave_policy", sa.String(150), nullable=True))
    op.add_column("employee_grades", sa.Column("default_salary_structure", sa.String(150), nullable=True))


def downgrade() -> None:
    op.drop_column("employee_grades", "default_salary_structure")
    op.drop_column("employee_grades", "default_leave_policy")
    op.drop_column("designations", "required_skills")
    op.drop_index("ix_departments_parent_id", table_name="departments")
    op.drop_column("departments", "leave_block_list")
    op.drop_column("departments", "parent_department_id")
    op.drop_column("departments", "is_group")
