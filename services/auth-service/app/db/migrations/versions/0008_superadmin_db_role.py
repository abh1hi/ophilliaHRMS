"""Create restricted PostgreSQL role for super admin DB connections.

hrms_superadmin role has access only to companies and users tables.
This limits blast radius if a super admin endpoint is exploited —
it cannot read leave, payroll, attendance, or other tenant data.

Revision ID: 0008_superadmin_db_role
Revises: 0007_rls_enable
Create Date: 2026-04-19
"""
from alembic import op

revision = "0008_superadmin_db_role"
down_revision = "0007_rls_enable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the restricted role if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hrms_superadmin') THEN
                CREATE ROLE hrms_superadmin LOGIN;
            END IF;
        END
        $$;
    """)

    # Revoke all privileges from public schema first
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM hrms_superadmin;")
    op.execute("REVOKE ALL ON SCHEMA public FROM hrms_superadmin;")

    # Grant schema usage
    op.execute("GRANT USAGE ON SCHEMA public TO hrms_superadmin;")

    # Grant only companies and users table access
    op.execute("GRANT SELECT, INSERT, UPDATE ON companies TO hrms_superadmin;")
    op.execute("GRANT SELECT, INSERT, UPDATE ON users TO hrms_superadmin;")

    # Grant sequence usage for UUID generation
    op.execute("GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO hrms_superadmin;")


def downgrade() -> None:
    op.execute("REVOKE ALL ON companies FROM hrms_superadmin;")
    op.execute("REVOKE ALL ON users FROM hrms_superadmin;")
    op.execute("REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM hrms_superadmin;")
    op.execute("REVOKE USAGE ON SCHEMA public FROM hrms_superadmin;")
    op.execute("DROP ROLE IF EXISTS hrms_superadmin;")
