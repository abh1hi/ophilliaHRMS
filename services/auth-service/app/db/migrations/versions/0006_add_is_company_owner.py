"""Add is_company_owner column and remove MAX_ADMINS trigger constraint

Revision ID: 0006_is_company_owner
Revises: 0005_add_outbox_table
Create Date: 2026-04-19
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_is_company_owner"
down_revision = "0005_add_outbox_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add the is_company_owner column
    op.add_column(
        "users",
        sa.Column("is_company_owner", sa.Boolean, nullable=False, server_default="false"),
    )

    # 2. Mark the bootstrapped super_admin's first admin as company owner
    #    (any existing admin is by definition the founding admin of their company)
    op.execute("""
        UPDATE users SET is_company_owner = TRUE
        WHERE role = 'admin'
    """)

    # 3. Replace trigger: keep MAX_SUPER_ADMINS=1, remove MAX_ADMINS=3 limit
    op.execute("DROP TRIGGER IF EXISTS trg_enforce_role_limits ON users;")
    op.execute("DROP FUNCTION IF EXISTS enforce_role_limits();")

    op.execute("""
        CREATE OR REPLACE FUNCTION enforce_role_limits()
        RETURNS TRIGGER AS $$
        DECLARE
            role_count INTEGER;
        BEGIN
            IF NEW.is_active = TRUE AND NEW.role = 'super_admin' THEN
                SELECT COUNT(*) INTO role_count
                FROM users
                WHERE role = 'super_admin' AND is_active = TRUE AND id != NEW.id;
                IF role_count >= 1 THEN
                    RAISE EXCEPTION 'Maximum of 1 super_admin account allowed globally';
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

    # Restore original trigger with MAX_ADMINS=3
    op.execute("""
        CREATE OR REPLACE FUNCTION enforce_role_limits()
        RETURNS TRIGGER AS $$
        DECLARE
            role_count INTEGER;
        BEGIN
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

    op.drop_column("users", "is_company_owner")
