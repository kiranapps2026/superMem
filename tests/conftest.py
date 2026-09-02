"""Test fixtures for SwarmVault API tests."""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.db import Base
from app.main import app

# Disable rate limiter for all tests
from app.middleware.rate_limit import _rate_limiter
_rate_limiter._disabled_for_testing = True
_rate_limiter._windows.clear()

TEST_DATABASE_URL = (
    "postgresql+asyncpg://swarmvault:swarmvault@localhost:5432/swarmvault_test"
)


def _run_alembic_migrations(database_url: str) -> None:
    """Run all Alembic migrations against the test database."""
    from alembic import command
    from alembic.config import Config as AlembicConfig

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ini_path = os.path.join(base_dir, "alembic.ini")
    cfg = AlembicConfig(ini_path)
    cfg.set_main_option("sqlalchemy.url", database_url)
    cfg.set_main_option("script_location", os.path.join(base_dir, "alembic"))
    command.upgrade(cfg, "head")


@pytest_asyncio.fixture(scope="session", autouse=True)
def _apply_migrations():
    """Apply all Alembic migrations once per test session."""
    _run_alembic_migrations(TEST_DATABASE_URL)
    yield
    # Teardown: drop all tables via migrations in reverse
    try:
        from alembic import command
        from alembic.config import Config as AlembicConfig

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cfg = AlembicConfig(os.path.join(base_dir, "alembic.ini"))
        cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
        cfg.set_main_option("script_location", os.path.join(base_dir, "alembic"))
        command.downgrade(cfg, "base")
    except Exception:
        pass


@pytest_asyncio.fixture(scope="session")
async def _engine():
    """Shared engine for the test session (migrations already applied)."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(_engine) -> AsyncGenerator[AsyncSession, None]:
    """Wrap each test in a transaction that rolls back — zero DB leakage."""
    connection = await _engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """AsyncClient with DB dependency override and test mode."""
    async def _override_get_db():
        yield db_session

    app.dependency_overrides = {}
    from app.db import get_db

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seeded_workspace(client: AsyncClient):
    """Register a unique user and return their token/workspace info."""
    uid = uuid.uuid4().hex[:8]
    resp = await client.post("/api/v1/auth/register", json={
        "email": f"owner-{uid}@test.com",
        "name": "Test Owner",
        "password": "testpass123",
        "workspace_name": f"Test Workspace {uid}",
    })
    assert resp.status_code == 201, f"Registration failed: {resp.text}"
    data = resp.json()

    return {
        "email": f"owner-{uid}@test.com",
        "password": "testpass123",
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "workspace_name": f"Test Workspace {uid}",
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
    }
