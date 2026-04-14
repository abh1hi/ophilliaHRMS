"""Add missing company_id to child tables created without it in 0005.

The SQLAlchemy Base class declares company_id on every model, but migration
0005 created leave_policy_items, holiday_list_entries, leave_block_list_dates,
and leave_block_list_allowed without that column.  This migration adds it with
IF NOT EXISTS guards so it is safe to run on both fresh and existing databases.

Revision ID: 0007_add_company_id_to_child_tables
Revises: 0006_event_log
Create Date: 2026-04-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007_cid_child_tables"
down_revision = "0006_event_log"
branch_labels = None
depends_on = None

# Tables from migration 0005 that were created without company_id
_TABLES = [
    "leave_policy_items",
    "holiday_list_entries",
    "leave_block_list_dates",
    "leave_block_list_allowed",
]


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = 'public' "
            "  AND table_name   = :t "
            "  AND column_name  = :c"
        ),
        {"t": table, "c": column},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    for table in _TABLES:
        if not _column_exists(table, "company_id"):
            op.add_column(
                table,
                sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
            )
            op.create_index(
                f"ix_{table}_company_id",
                table,
                ["company_id"],
            )


def downgrade() -> None:
    for table in _TABLES:
        if _column_exists(table, "company_id"):
            op.drop_index(f"ix_{table}_company_id", table_name=table)
            op.drop_column(table, "company_id")
