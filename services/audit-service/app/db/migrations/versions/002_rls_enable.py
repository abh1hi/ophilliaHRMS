"""Enable Row-Level Security on tenant-scoped tables (audit-service).

Phase 1 of 2: ENABLE only. Monitor before applying 003_rls_force.py.

Revision ID: 002_rls_enable
Revises: 001
Create Date: 2026-04-19
"""
from alembic import op

revision = "002_rls_enable"
down_revision = "001"
branch_labels = None
depends_on = None

TENANT_TABLES = ["audit_logs"]

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
