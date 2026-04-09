"""Add account_status, invite_expires_at; make user_id nullable with partial unique index

Revision ID: 0010_add_account_status_nullable_user_id
Revises: 0009_add_employee_code
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0010_add_account_status_nullable_user_id"
down_revision = "0009_add_employee_code"
branch_labels = None
depends_on = None


def upgrade():
    # account_status: server_default="active" keeps existing employees unaffected
    op.add_column("employees", sa.Column(
        "account_status", sa.String(20), nullable=False, server_default="active"
    ))
    op.create_index("ix_employees_account_status", "employees", ["account_status"])

    # invite_expires_at: stores when the current invite token expires
    op.add_column("employees", sa.Column(
        "invite_expires_at", sa.DateTime(timezone=True), nullable=True
    ))

    # Make user_id nullable — employees imported before provisioning have no auth account yet
    op.alter_column(
        "employees", "user_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )

    # Replace the plain unique index with a partial unique index (NULLs must be allowed to repeat)
    op.drop_index("ix_employees_user_id", table_name="employees")
    op.create_index(
        "ix_employees_user_id",
        "employees",
        ["user_id"],
        postgresql_where=sa.text("user_id IS NOT NULL"),
        unique=True,
    )


def downgrade():
    # Restore plain unique index (will fail if any user_id is NULL)
    op.drop_index("ix_employees_user_id", table_name="employees")
    op.create_index("ix_employees_user_id", "employees", ["user_id"], unique=True)

    op.alter_column(
        "employees", "user_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )

    op.drop_column("employees", "invite_expires_at")
    op.drop_index("ix_employees_account_status", table_name="employees")
    op.drop_column("employees", "account_status")
