"""Force Row-Level Security on tenant-scoped tables (onboarding-service).

Phase 2 of 2: Apply after validating 0004_rls_enable.py for 24 hours.

Revision ID: 0005_rls_force
Revises: 0004_rls_enable
Create Date: 2026-04-19
"""
from alembic import op

revision = "0005_rls_force"
down_revision = "0004_rls_enable"
branch_labels = None
depends_on = None

TENANT_TABLES = ["onboarding_status", "onboarding_steps"]


def upgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")


def downgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
