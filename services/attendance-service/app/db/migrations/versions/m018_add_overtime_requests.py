"""Migration 0018: Create overtime_requests table for employee OT request workflow.

Employees submit OT requests; HR/managers approve or reject.
Status: pending → approved | rejected.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "m018"
down_revision = "m017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "overtime_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("requested_hours", sa.Float, nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("reviewed_by", UUID(as_uuid=True), nullable=True),
        sa.Column("review_note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_ot_request_company", "overtime_requests", ["company_id"])
    op.create_index("ix_ot_request_employee", "overtime_requests", ["company_id", "employee_id"])
    op.create_index("ix_ot_request_date", "overtime_requests", ["company_id", "date"])
    op.create_index("ix_ot_request_status", "overtime_requests", ["company_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_ot_request_status", "overtime_requests")
    op.drop_index("ix_ot_request_date", "overtime_requests")
    op.drop_index("ix_ot_request_employee", "overtime_requests")
    op.drop_index("ix_ot_request_company", "overtime_requests")
    op.drop_table("overtime_requests")
