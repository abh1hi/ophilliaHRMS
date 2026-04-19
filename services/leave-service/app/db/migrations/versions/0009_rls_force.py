"""Force Row-Level Security on tenant-scoped tables (leave-service).

Phase 2 of 2: Apply after validating 0008_rls_enable.py for 24 hours.

Revision ID: 0009_rls_force
Revises: 0008_rls_enable
Create Date: 2026-04-19
"""
from alembic import op

revision = "0009_rls_force"
down_revision = "0008_rls_enable"
branch_labels = None
depends_on = None

TENANT_TABLES = [
    "leave_requests",
    "leave_types",
    "leave_approvals",
    "holidays",
    "leave_allocations",
    "leave_periods",
    "leave_policies",
    "leave_policy_assignments",
    "leave_block_lists",
    "compensatory_leave_requests",
    "leave_encashments",
    "leave_ledger_entries",
]


def upgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")


def downgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
