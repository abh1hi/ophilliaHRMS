"""Initial audit_logs table

Revision ID: 001
Revises: 
Create Date: 2026-03-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("event_id", UUID(as_uuid=True), nullable=False),
        sa.Column("event_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("service_source", sa.String(100), nullable=False),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("correlation_id", UUID(as_uuid=True), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("http_method", sa.String(10), nullable=True),
        sa.Column("endpoint", sa.String(255), nullable=True),
        sa.Column("payload", JSON, nullable=False, server_default="{}"),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # Unique constraint for idempotency
    op.create_unique_constraint("uq_audit_logs_event_id", "audit_logs", ["event_id"])

    # Individual column indexes
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"])
    op.create_index("ix_audit_logs_service_source", "audit_logs", ["service_source"])
    op.create_index("ix_audit_logs_company_id", "audit_logs", ["company_id"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_correlation_id", "audit_logs", ["correlation_id"])
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])

    # Composite indexes for common query patterns
    op.create_index("idx_company_timestamp", "audit_logs", ["company_id", "timestamp"])
    op.create_index("idx_company_event_type", "audit_logs", ["company_id", "event_type"])
    op.create_index("idx_company_user", "audit_logs", ["company_id", "user_id"])

    # Note: Partial index on recent logs removed — now() is not IMMUTABLE.
    # The composite index idx_company_timestamp handles recent audit queries efficiently.

    # Read-only role for audit readers (SELECT only)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'audit_reader') THEN
                CREATE ROLE audit_reader;
            END IF;
        END $$
    """)
    op.execute("GRANT SELECT ON audit_logs TO audit_reader")

    # Write-only role for audit writers (INSERT only — no UPDATE/DELETE)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'audit_writer') THEN
                CREATE ROLE audit_writer;
            END IF;
        END $$
    """)
    op.execute("GRANT INSERT ON audit_logs TO audit_writer")


def downgrade() -> None:
    op.execute("REVOKE ALL ON audit_logs FROM audit_reader, audit_writer")
    op.drop_index("idx_company_user", table_name="audit_logs")
    op.drop_index("idx_company_event_type", table_name="audit_logs")
    op.drop_index("idx_company_timestamp", table_name="audit_logs")
    op.drop_table("audit_logs")
