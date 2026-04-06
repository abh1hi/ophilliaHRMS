import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.db.base import Base
from app.models.employee import Employee             # noqa: F401 - register model
from app.models.department import Department         # noqa: F401 - register model
from app.models.branch import Branch                 # noqa: F401 - register model
from app.models.designation import Designation       # noqa: F401 - register model
from app.models.employment_type import EmploymentType  # noqa: F401 - register model
from app.models.employee_grade import EmployeeGrade  # noqa: F401 - register model
from app.models.employee_group import EmployeeGroup  # noqa: F401 - register model
from app.models.shift_type import ShiftType          # noqa: F401 - register model
from app.models.shift_location import ShiftLocation  # noqa: F401 - register model
from app.core.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Override URL from app config (reads from .env)
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
