"""Enable Row-Level Security on tenant-scoped tables (leave-service).

Phase 1 of 2: ENABLE only. Monitor before applying 0009_rls_force.py.

Revision ID: 0008_rls_enable
Revises: 0007_add_company_id_to_child_tables
Create Date: 2026-04-19
"""
from alembic import op

revision = "0008_rls_enable"
down_revision = "0007_add_company_id_to_child_tables"
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

_POLICY = """
CREATE POLICY tenant_isolation ON {table}
  USING (
    current_setting('app.company_id', true) IS NOT NULL
    AND company_id = current_setting('app.company_id', true)::uuid
  );
"""


def upgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        op.execute(_POLICY.format(table=table))


def downgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
