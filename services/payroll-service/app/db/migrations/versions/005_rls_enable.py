"""Enable Row-Level Security on tenant-scoped tables (payroll-service).

Phase 1 of 2: ENABLE only. Monitor before applying 006_rls_force.py.

Revision ID: 005_rls_enable
Revises: 0004_event_log
Create Date: 2026-04-19
"""
from alembic import op

revision = "005_rls_enable"
down_revision = "0004_event_log"
branch_labels = None
depends_on = None

TENANT_TABLES = [
    "salary_structures",
    "employee_salaries",
    "payroll_runs",
    "payslips",
    "employee_tax_profiles",
    "employee_ytd",
    "payroll_adjustments",
    "payroll_loans",
    "payroll_audit_logs",
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
