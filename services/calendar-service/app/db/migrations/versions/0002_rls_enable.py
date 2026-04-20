"""Enable Row-Level Security on tenant-scoped tables (calendar-service).

Phase 1 of 2: ENABLE only. Monitor before applying 0003_rls_force.py.
Note: task_assignees and task_comments have no direct company_id — they inherit
via their parent task. RLS on tasks table covers access control for those children.

Revision ID: 0002_rls_enable
Revises: 0001_initial
Create Date: 2026-04-19
"""
from alembic import op

revision = "0002_rls_enable"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

# Direct company_id tables only — child tables (task_assignees, task_comments) excluded
TENANT_TABLES = [
    "workspaces",
    "workspace_members",
    "calendars",
    "calendar_events",
    "calendar_tasks",
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
