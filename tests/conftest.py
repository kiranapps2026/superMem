"""Test fixtures for SwarmVault API tests."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.db import Base
from app.main import app

TEST_DATABASE_URL = (
    "postgresql+asyncpg://swarmvault:swarmvault@localhost:5432/swarmvault_test"
)


@pytest_asyncio.fixture(scope="session")
async def _engine():
    """Shared engine — schema created once, dropped once."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    # Drop then create to handle restarts
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
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
    """AsyncClient with DB dependency override."""
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
