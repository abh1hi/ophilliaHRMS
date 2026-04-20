"""Force Row-Level Security on tenant-scoped tables (calendar-service).

Phase 2 of 2: Apply after validating 0002_rls_enable.py for 24 hours.

Revision ID: 0003_rls_force
Revises: 0002_rls_enable
Create Date: 2026-04-19
"""
from alembic import op

revision = "0003_rls_force"
down_revision = "0002_rls_enable"
branch_labels = None
depends_on = None

TENANT_TABLES = [
    "workspaces",
    "workspace_members",
    "calendars",
    "calendar_events",
    "calendar_tasks",
]


def upgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")


def downgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
