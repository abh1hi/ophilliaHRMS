"""Force Row-Level Security on tenant-scoped tables (auth-service).

Phase 2 of 2: Apply FORCE after validating 0007_rls_enable.py for 24 hours.
FORCE ensures even table owner queries are filtered — prevents privilege bypass.

Revision ID: 0009_rls_force
Revises: 0008_superadmin_db_role
Create Date: 2026-04-19
"""
from alembic import op

revision = "0009_rls_force"
down_revision = "0008_superadmin_db_role"
branch_labels = None
depends_on = None

TENANT_TABLES = ["users", "invites", "refresh_tokens", "magic_tokens"]


def upgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")


def downgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
