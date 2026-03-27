"""Idempotency infrastructure and optimistic locking

Adds:
- attendance_records.version column for optimistic locking
- Partial unique index: one open session per employee per day
- idempotency_keys table with tenant-scoped uniqueness
- Composite lookup index for high-throughput middleware queries
- Partial index on stuck "processing" entries for recovery

Revision ID: 0006_idempotency
Revises: 0005_sop_enhancements
Create Date: 2026-03-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0006_idempotency"
down_revision = "0005_sop_enhancements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Optimistic locking on attendance_records ──
    op.add_column(
        "attendance_records",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )

    # ── 2. Partial unique index: at most one open (clock_out IS NULL) record
    #       per employee per day. DB-level guarantee against double punch-in. ──
    op.create_index(
        "ix_one_open_session_per_employee_day",
        "attendance_records",
        ["employee_id", "date"],
        unique=True,
        postgresql_where=sa.text("clock_out IS NULL"),
    )

    # ── 3. Idempotency keys table (tenant-scoped) ──
    op.create_table(
        "idempotency_keys",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("request_path", sa.String(500), nullable=False),
        sa.Column("request_method", sa.String(10), nullable=False),
        sa.Column("request_body_hash", sa.String(64), nullable=True),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="processing",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        # Uniqueness scoped to tenant: two companies can use the same key
        sa.UniqueConstraint("company_id", "key", name="uq_idempotency_tenant_key"),
    )

    # Composite index covering the middleware hot-path SELECT
    op.create_index(
        "ix_idempotency_lookup",
        "idempotency_keys",
        ["company_id", "key", "request_path", "request_method"],
    )

    # TTL cleanup: efficient scan for expired entries
    op.create_index(
        "ix_idempotency_expires",
        "idempotency_keys",
        ["expires_at"],
    )

    # Stuck processing recovery: partial index on status='processing'
    op.create_index(
        "ix_idempotency_stuck",
        "idempotency_keys",
        ["status", "created_at"],
        postgresql_where=sa.text("status = 'processing'"),
    )

    # Company_id index for tenant isolation queries
    op.create_index(
        "ix_idempotency_company",
        "idempotency_keys",
        ["company_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_idempotency_company", table_name="idempotency_keys")
    op.drop_index("ix_idempotency_stuck", table_name="idempotency_keys")
    op.drop_index("ix_idempotency_expires", table_name="idempotency_keys")
    op.drop_index("ix_idempotency_lookup", table_name="idempotency_keys")
    op.drop_table("idempotency_keys")
    op.drop_index(
        "ix_one_open_session_per_employee_day", table_name="attendance_records",
    )
    op.drop_column("attendance_records", "version")
