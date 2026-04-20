"""Enable Row-Level Security on tenant-scoped tables (auth-service).

Phase 1 of 2: ENABLE only (no FORCE). Monitor before applying 0009_rls_force.py.

Revision ID: 0007_rls_enable
Revises: 0006_is_company_owner
Create Date: 2026-04-19
"""
from alembic import op

revision = "0007_rls_enable"
down_revision = "0006_is_company_owner"
branch_labels = None
depends_on = None

# companies is intentionally excluded — super admin must see all companies without RLS
TENANT_TABLES = ["users", "invites"]

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
