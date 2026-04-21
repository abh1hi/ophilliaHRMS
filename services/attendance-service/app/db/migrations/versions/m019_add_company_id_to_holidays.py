"""Migration 0019: Add company_id to holidays

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = 'm019'
down_revision = 'm018'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Add column as nullable first to avoid constraint validation errors on existing rows
    op.add_column('holidays', sa.Column('company_id', UUID(as_uuid=True), nullable=True))
    
    # 2. Backfill company_id from the parent holiday_calendars table
    op.execute(
        "UPDATE holidays SET company_id = hc.company_id "
        "FROM holiday_calendars hc WHERE hc.id = holidays.calendar_id"
    )
    
    # 3. Alter the column to enforce the NOT NULL constraint seamlessly
    op.alter_column('holidays', 'company_id', nullable=False)
    op.create_index('ix_holidays_company_id', 'holidays', ['company_id'])


def downgrade() -> None:
    op.drop_index('ix_holidays_company_id', table_name='holidays')
    op.drop_column('holidays', 'company_id')
