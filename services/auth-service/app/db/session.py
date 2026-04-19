from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,
    connect_args={"timeout": 10},
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Super admin uses a separate restricted DB role (only companies + users tables)
_superadmin_db_url = settings.SUPERADMIN_DATABASE_URL or settings.DATABASE_URL
_superadmin_engine = create_async_engine(
    _superadmin_db_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
    connect_args={"timeout": 10},
)

SuperAdminSessionLocal = sessionmaker(
    _superadmin_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def get_db_superadmin():
    async with SuperAdminSessionLocal() as session:
        yield session
