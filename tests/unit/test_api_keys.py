"""Sprint 6 — API key management tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_api_key(client: AsyncClient, seeded_workspace):
    """Create an API key and get the raw key."""
    res = await client.post("/api/v1/api-keys/", json={
        "name": "MCP Server",
        "description": "Key for MCP server registration",
    }, headers=seeded_workspace["headers"])
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "MCP Server"
    assert "raw_key" in data
    assert len(data["raw_key"]) == 64
    assert data["key_prefix"] == data["raw_key"][:8]


@pytest.mark.asyncio
async def test_create_api_key_returns_key_once(client: AsyncClient, seeded_workspace):
    """Raw key is returned only on creation, not on list."""
    create_res = await client.post("/api/v1/api-keys/", json={
        "name": "One-time Key",
    }, headers=seeded_workspace["headers"])
    key_id = create_res.json()["id"]

    # List should not contain raw_key
    list_res = await client.get("/api/v1/api-keys/", headers=seeded_workspace["headers"])
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 1
    assert "raw_key" not in items[0]


@pytest.mark.asyncio
async def test_list_api_keys(client: AsyncClient, seeded_workspace):
    """List API keys for the workspace."""
    await client.post("/api/v1/api-keys/", json={"name": "Key 1"}, headers=seeded_workspace["headers"])
    await client.post("/api/v1/api-keys/", json={"name": "Key 2"}, headers=seeded_workspace["headers"])

    res = await client.get("/api/v1/api-keys/", headers=seeded_workspace["headers"])
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 2
    names = {i["name"] for i in items}
    assert names == {"Key 1", "Key 2"}


@pytest.mark.asyncio
async def test_revoke_api_key(client: AsyncClient, seeded_workspace):
    """Revoke an API key."""
    create_res = await client.post("/api/v1/api-keys/", json={"name": "Revoke Me"}, headers=seeded_workspace["headers"])
    key_id = create_res.json()["id"]

    # Revoke
    revoke_res = await client.delete(f"/api/v1/api-keys/{key_id}", headers=seeded_workspace["headers"])
    assert revoke_res.status_code == 204

    # Key should not appear in active list
    list_res = await client.get("/api/v1/api-keys/", headers=seeded_workspace["headers"])
    items = list_res.json()
    assert all(i["id"] != key_id for i in items)


@pytest.mark.asyncio
async def test_revoke_nonexistent_key(client: AsyncClient, seeded_workspace):
    """Revoking a nonexistent key returns 404."""
    res = await client.delete("/api/v1/api-keys/nonexistent-id", headers=seeded_workspace["headers"])
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_rotate_api_key(client: AsyncClient, seeded_workspace):
    """Rotate an API key: new key created, old revoked."""
    create_res = await client.post("/api/v1/api-keys/", json={"name": "Rotate Me"}, headers=seeded_workspace["headers"])
    old_key_id = create_res.json()["id"]

    rotate_res = await client.post(
        f"/api/v1/api-keys/{old_key_id}/rotate",
        headers=seeded_workspace["headers"],
    )
    assert rotate_res.status_code == 200
    data = rotate_res.json()
    assert "raw_key" in data
    assert data["raw_key"] != ""


@pytest.mark.asyncio
async def test_tenant_isolation(client: AsyncClient, seeded_workspace):
    """Tenant B cannot access or delete Tenant A's keys."""
    # Create tenant B
    resp_b = await client.post("/api/v1/auth/register", json={
        "email": "apikey-tenant-b@test.com",
        "password": "SecurePass123!",
        "name": "B",
        "workspace_name": "WS B",
    })
    token_b = resp_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # A creates a key
    key_a_res = await client.post("/api/v1/api-keys/", json={"name": "A Key"}, headers=seeded_workspace["headers"])
    key_a_id = key_a_res.json()["id"]

    # B cannot delete A's key
    res = await client.delete(f"/api/v1/api-keys/{key_a_id}", headers=headers_b)
    assert res.status_code in (403, 404)


@pytest.mark.asyncio
async def test_api_key_requires_auth(client: AsyncClient):
    """Unauthenticated requests to API key endpoints are rejected."""
    res = await client.get("/api/v1/api-keys/")
    assert res.status_code == 401

    res = await client.post("/api/v1/api-keys/", json={"name": "No Auth"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_api_key_with_expiry(client: AsyncClient, seeded_workspace):
    """Can create a key with an expiry date."""
    res = await client.post("/api/v1/api-keys/", json={
        "name": "Expiring Key",
        "expires_at": "2099-01-01T00:00:00Z",
    }, headers=seeded_workspace["headers"])
    assert res.status_code == 201
    assert res.json()["expires_at"] is not None


@pytest.mark.asyncio
async def test_api_key_list_empty(client: AsyncClient, seeded_workspace):
    """Empty list for a new workspace."""
    res = await client.get("/api/v1/api-keys/", headers=seeded_workspace["headers"])
    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.asyncio
async def test_api_key_with_metadata(client: AsyncClient, seeded_workspace):
    """Can create a key with arbitrary metadata."""
    res = await client.post("/api/v1/api-keys/", json={
        "name": "MCP Key",
        "description": "Server key",
        "metadata": {"server_name": "my-mcp", "allowed_tools": "all"},
    }, headers=seeded_workspace["headers"])
    assert res.status_code == 201
    data = res.json()
    assert data["key_extra"]["server_name"] == "my-mcp"
