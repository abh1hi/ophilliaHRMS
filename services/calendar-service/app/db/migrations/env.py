import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.db.base import Base
from app.models.workspace import Workspace                         # noqa: F401
from app.models.workspace_member import WorkspaceMember            # noqa: F401
from app.models.calendar import Calendar                           # noqa: F401
from app.models.calendar_event import CalendarEvent                # noqa: F401
from app.models.recurrence_override import RecurrenceOverride      # noqa: F401
from app.models.task import CalendarTask                           # noqa: F401
from app.models.task_assignee import TaskAssignee                  # noqa: F401
from app.models.task_comment import TaskComment                    # noqa: F401
from app.models.google_integration import GoogleIntegration        # noqa: F401
from app.models.sync_log import SyncLog                            # noqa: F401
from app.models.calendar_audit_log import CalendarAuditLog         # noqa: F401
from app.core.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata,
        literal_binds=True, dialect_opts={"paramstyle": "named"},
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
        prefix="sqlalchemy.", poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
