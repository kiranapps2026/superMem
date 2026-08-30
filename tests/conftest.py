import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.db import Base, init_db
from app.main import app
from app.models import User, Tenant, Workspace, WorkspaceMember

# Test database
TEST_DATABASE_URL = "postgresql+asyncpg://swarmvault:swarmvault@localhost:5432/swarmvault_test"

# Shared test engine/factory (module-level to avoid creating a pool per test)
_engine = None
_factory = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    return _engine


def _get_factory():
    global _factory
    if _factory is None:
        _factory = async_sessionmaker(_get_engine(), class_=AsyncSession, expire_on_commit=False)
    return _factory


@pytest_asyncio.fixture
async def db_session():
    """Create a fresh database session for each test with rolled-back transaction."""
    engine = _get_engine()
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session = _get_factory()()
    try:
        yield session
    finally:
        await session.close()
        # Drop all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session):
    """AsyncClient with dependency override for DB session."""
    from app.db import async_session_factory as _orig_factory

    # Override get_db to use test session
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
    """Create a tenant, workspace, user, and owner membership. Returns tokens and IDs."""
    email = "owner@test.com"
    password = "testpass123"
    workspace_name = "Test Workspace"

    # Register
    resp = await client.post("/auth/register", json={
        "email": email,
        "name": "Test Owner",
        "password": password,
        "workspace_name": workspace_name,
    })
    assert resp.status_code == 201, f"Registration failed: {resp.text}"
    tokens = resp.json()

    return {
        "email": email,
        "password": password,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "workspace_name": workspace_name,
        "headers": {"Authorization": f"Bearer {tokens['access_token']}"},
    }
