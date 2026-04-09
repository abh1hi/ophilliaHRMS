"""Add HR reference tables: branches, designations, employment_types, employee_grades, employee_groups

Revision ID: 0006_add_hr_reference_tables
Revises: 0005_expand_encrypted_cols
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0006_add_hr_reference_tables"
down_revision = "0005_expand_encrypted_cols"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "branches",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_branches_company_id", "branches", ["company_id"], unique=False)
    op.create_index("ix_branches_company_name", "branches", ["company_id", "name"], unique=True)

    op.create_table(
        "designations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_designations_company_id", "designations", ["company_id"], unique=False)
    op.create_index("ix_designations_company_name", "designations", ["company_id", "name"], unique=True)

    op.create_table(
        "employment_types",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_employment_types_company_id", "employment_types", ["company_id"], unique=False)
    op.create_index("ix_employment_types_company_name", "employment_types", ["company_id", "name"], unique=True)

    op.create_table(
        "employee_grades",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_employee_grades_company_id", "employee_grades", ["company_id"], unique=False)
    op.create_index("ix_employee_grades_company_name", "employee_grades", ["company_id", "name"], unique=True)

    op.create_table(
        "employee_groups",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_employee_groups_company_id", "employee_groups", ["company_id"], unique=False)
    op.create_index("ix_employee_groups_company_name", "employee_groups", ["company_id", "name"], unique=True)

    op.create_table(
        "employee_group_members",
        sa.Column("group_id", UUID(as_uuid=True), sa.ForeignKey("employee_groups.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("employee_id", UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_egm_group_id", "employee_group_members", ["group_id"], unique=False)
    op.create_index("ix_egm_employee_id", "employee_group_members", ["employee_id"], unique=False)
    op.create_index("ix_egm_company_id", "employee_group_members", ["company_id"], unique=False)


def downgrade() -> None:
    op.drop_table("employee_group_members")
    op.drop_table("employee_groups")
    op.drop_table("employee_grades")
    op.drop_table("employment_types")
    op.drop_table("designations")
    op.drop_table("branches")
