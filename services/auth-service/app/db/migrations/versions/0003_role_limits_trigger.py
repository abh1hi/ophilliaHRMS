"""Add database triggers to enforce role limits (defense-in-depth)

Revision ID: 0003_role_limits
Revises: 0002_add_companies
Create Date: 2026-03-24
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_role_limits"
down_revision = "0002_add_companies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION enforce_role_limits()
        RETURNS TRIGGER AS $$
        DECLARE
            role_count INTEGER;
        BEGIN
            -- Only check when role is being set to super_admin or admin on an active user
            IF NEW.is_active = TRUE THEN
                IF NEW.role = 'super_admin' THEN
                    SELECT COUNT(*) INTO role_count
                    FROM users
                    WHERE role = 'super_admin' AND is_active = TRUE AND id != NEW.id;
                    IF role_count >= 1 THEN
                        RAISE EXCEPTION 'Maximum of 1 super_admin account allowed';
                    END IF;
                END IF;

                IF NEW.role = 'admin' THEN
                    SELECT COUNT(*) INTO role_count
                    FROM users
                    WHERE role = 'admin' AND is_active = TRUE AND id != NEW.id;
                    IF role_count >= 3 THEN
                        RAISE EXCEPTION 'Maximum of 3 admin accounts allowed';
                    END IF;
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_enforce_role_limits
        BEFORE INSERT OR UPDATE OF role, is_active ON users
        FOR EACH ROW
        EXECUTE FUNCTION enforce_role_limits();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_enforce_role_limits ON users;")
    op.execute("DROP FUNCTION IF EXISTS enforce_role_limits();")
