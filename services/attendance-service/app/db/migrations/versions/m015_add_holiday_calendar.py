"""Migration 0015: Add holiday_calendars and holidays tables.

Scoped per company with an optional location override so that offices in
different regions can carry different public holiday lists.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "m015"
down_revision = "m014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "holiday_calendars",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "location_id",
            UUID(as_uuid=True),
            sa.ForeignKey("geofence_locations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_holiday_calendar_company", "holiday_calendars", ["company_id"])
    op.create_index("ix_holiday_calendar_location", "holiday_calendars", ["location_id"])
    op.create_index("ix_holiday_calendar_year", "holiday_calendars", ["company_id", "year"])

    op.create_table(
        "holidays",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "calendar_id",
            UUID(as_uuid=True),
            sa.ForeignKey("holiday_calendars.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("holiday_type", sa.String(20), nullable=False, server_default="public"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_holiday_date", "holidays", ["date"])
    op.create_index("ix_holiday_calendar_date", "holidays", ["calendar_id", "date"])


def downgrade() -> None:
    op.drop_index("ix_holiday_calendar_date", "holidays")
    op.drop_index("ix_holiday_date", "holidays")
    op.drop_table("holidays")

    op.drop_index("ix_holiday_calendar_year", "holiday_calendars")
    op.drop_index("ix_holiday_calendar_location", "holiday_calendars")
    op.drop_index("ix_holiday_calendar_company", "holiday_calendars")
    op.drop_table("holiday_calendars")
