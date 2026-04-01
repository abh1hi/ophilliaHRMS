"""Policy enhancements: grace period, audit trail

Adds:
- attendance_policies.late_grace_period_minutes — configurable grace window
  before an employee is marked late (default 0 = no grace).
- policy_audit_logs table — immutable audit trail for every create/update/delete
  on attendance policies.

Revision ID: 0007_policy_enhancements
Revises: 0006_idempotency
Create Date: 2026-04-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "0007_policy_enhancements"
down_revision = "0006_idempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Add late_grace_period_minutes to attendance_policies ──
    op.add_column(
        "attendance_policies",
        sa.Column(
            "late_grace_period_minutes",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    # ── 2. Create policy_audit_logs table ──
    op.create_table(
        "policy_audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("policy_id", UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("changed_by", UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("old_value", JSONB, nullable=True),
        sa.Column("new_value", JSONB, nullable=True),
    )
    op.create_index("ix_policy_audit_policy_id", "policy_audit_logs", ["policy_id"])
    op.create_index("ix_policy_audit_company_id", "policy_audit_logs", ["company_id"])
    op.create_index("ix_policy_audit_timestamp", "policy_audit_logs", ["timestamp"])


def downgrade() -> None:
    op.drop_index("ix_policy_audit_timestamp", table_name="policy_audit_logs")
    op.drop_index("ix_policy_audit_company_id", table_name="policy_audit_logs")
    op.drop_index("ix_policy_audit_policy_id", table_name="policy_audit_logs")
    op.drop_table("policy_audit_logs")
    op.drop_column("attendance_policies", "late_grace_period_minutes")
