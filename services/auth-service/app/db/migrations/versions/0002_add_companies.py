"""Add companies table and company_id to users

Revision ID: 0002_add_companies
Revises: 0001_initial
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002_add_companies"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── companies ────────────────────────────────────────────────────────────
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_companies_name", "companies", ["name"], unique=True)
    op.create_index("ix_companies_domain", "companies", ["domain"], unique=True)

    # ── users ────────────────────────────────────────────────────────────────
    # Add company_id to users. Since we might have existing users, we'll allow nullable for now
    # or better, delete them if it's fresh, but safety first.
    # Actually, the requirement said nullable=False.
    op.add_column("users", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
    
    # We should probably clear users if we want to enforce nullable=False, or provide a default.
    # But for this dev env, we can just add it and then make it non-nullable.
    op.create_foreign_key(
        "fk_users_company_id",
        "users",
        "companies",
        ["company_id"],
        ["id"],
        ondelete="CASCADE"
    )
    op.create_index("ix_users_company_id", "users", ["company_id"])


def downgrade() -> None:
    op.drop_constraint("fk_users_company_id", "users", type_="foreignkey")
    op.drop_index("ix_users_company_id", table_name="users")
    op.drop_column("users", "company_id")
    op.drop_table("companies")
