"""Enable Row-Level Security on tenant-scoped tables (attendance-service).

Phase 1 of 2: ENABLE only. Monitor before applying 0013_rls_force.py.

Revision ID: 0012_rls_enable
Revises: 0011_event_log
Create Date: 2026-04-19
"""
from alembic import op

revision = "0012_rls_enable"
down_revision = "0011_event_log"
branch_labels = None
depends_on = None

TENANT_TABLES = [
    "attendance_records",
    "attendance_requests",
    "attendance_policies",
    "employee_checkins",
    "shift_assignments",
    "shift_schedules",
    "geofence_locations",
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
