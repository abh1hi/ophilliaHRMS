"""Migration 0016: Add geofence_consents table for GDPR compliance.

Stores explicit employee consent to GPS/geofence location tracking.
Clock-in with method=geofence or method=both is blocked (HTTP 451)
until the employee records consent via the consent endpoint.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "geofence_consents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("consented", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("consent_given_at", sa.DateTime, nullable=True),
        sa.Column("consent_withdrawn_at", sa.DateTime, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("company_id", "employee_id", name="uq_geofence_consent_employee"),
    )
    op.create_index("ix_geofence_consent_employee", "geofence_consents", ["company_id", "employee_id"])


def downgrade() -> None:
    op.drop_index("ix_geofence_consent_employee", "geofence_consents")
    op.drop_table("geofence_consents")
