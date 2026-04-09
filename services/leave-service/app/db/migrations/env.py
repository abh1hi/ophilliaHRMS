import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.db.base import Base
from app.models.leave import LeaveType, LeaveBalance, LeaveRequest  # noqa: F401
from app.models.leave_period import LeavePeriod  # noqa: F401
from app.models.holiday_list import HolidayList, HolidayListEntry  # noqa: F401
from app.models.holiday_list_assignment import HolidayListAssignment  # noqa: F401
from app.models.leave_policy import LeavePolicy, LeavePolicyItem  # noqa: F401
from app.models.leave_policy_assignment import LeavePolicyAssignment  # noqa: F401
from app.models.leave_allocation import LeaveAllocation  # noqa: F401
from app.models.leave_adjustment import LeaveAdjustment  # noqa: F401
from app.models.leave_block_list import LeaveBlockList, LeaveBlockListDate, LeaveBlockListAllowed  # noqa: F401
from app.models.compensatory_leave_request import CompensatoryLeaveRequest  # noqa: F401
from app.models.leave_encashment import LeaveEncashment  # noqa: F401
from app.models.leave_ledger_entry import LeaveLedgerEntry  # noqa: F401
from app.core.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
