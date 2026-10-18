from typing import AsyncGenerator

from alembic import command
from alembic.config import Config as AlembicConfig
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=50,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


def _alembic_config() -> AlembicConfig:
    """Build Alembic config pointing to project root."""
    import os
    cfg = AlembicConfig(os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    cfg.set_main_option("script_location", os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic"))
    return cfg


async def init_db():
    """Apply all pending migrations to the database."""
    import asyncio
    loop = asyncio.get_running_loop()
    cfg = _alembic_config()
    await loop.run_in_executor(None, lambda: command.upgrade(cfg, "head"))
