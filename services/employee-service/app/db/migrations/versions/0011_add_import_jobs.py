"""Add import_jobs table and import_job_id FK on employees

Revision ID: 0011_add_import_jobs
Revises: 0010_account_status
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0011_add_import_jobs"
down_revision = "0010_account_status"
branch_labels = None
depends_on = None


def upgrade():
    # ── 1. Create import_jobs table ───────────────────────────────────────
    op.create_table(
        "import_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.Integer, nullable=True),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.Column("schema_version", sa.String(10), nullable=False, server_default="v1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("duplicate_strategy", sa.String(10), nullable=False, server_default="update"),
        sa.Column("total_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("succeeded_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failed_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("skipped_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_log", postgresql.JSONB, nullable=True),
        sa.Column("auto_corrections", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.UniqueConstraint(
            "company_id", "idempotency_key",
            name="uq_import_jobs_company_idempotency"
        ),
    )
    op.create_index("ix_import_jobs_company_id", "import_jobs", ["company_id"])
    op.create_index("ix_import_jobs_status", "import_jobs", ["status"])
    op.create_index(
        "ix_import_jobs_company_created",
        "import_jobs",
        ["company_id", "created_at"],
    )

    # ── 2. Add import_job_id FK to employees ──────────────────────────────
    op.add_column(
        "employees",
        sa.Column(
            "import_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("import_jobs.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_employees_import_job_id", "employees", ["import_job_id"])


def downgrade():
    op.drop_index("ix_employees_import_job_id", table_name="employees")
    op.drop_column("employees", "import_job_id")

    op.drop_index("ix_import_jobs_company_created", table_name="import_jobs")
    op.drop_index("ix_import_jobs_status", table_name="import_jobs")
    op.drop_index("ix_import_jobs_company_id", table_name="import_jobs")
    op.drop_table("import_jobs")
