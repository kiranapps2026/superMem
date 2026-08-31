import pytest


@pytest.mark.asyncio
async def test_auto_resolve_workspace(client):
    """User with a single membership auto-resolves to that workspace."""
    reg = await client.post("/api/v1/auth/register", json={
        "email": "auto@test.com",
        "name": "Auto User",
        "password": "securepass123",
        "workspace_name": "Auto WS",
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/v1/workspace/", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Auto WS"


@pytest.mark.asyncio
async def test_non_member_blocked(client):
    """User without workspace membership gets 404."""
    # Create two separate users/workspaces
    reg1 = await client.post("/api/v1/auth/register", json={
        "email": "user1@test.com",
        "name": "User One",
        "password": "securepass123",
        "workspace_name": "WS1",
    })
    token1 = reg1.json()["access_token"]

    reg2 = await client.post("/api/v1/auth/register", json={
        "email": "user2@test.com",
        "name": "User Two",
        "password": "securepass123",
        "workspace_name": "WS2",
    })
    token2 = reg2.json()["access_token"]
    ws2_id = (await client.get("/api/v1/workspace/", headers={"Authorization": f"Bearer {token2}"})).json()["id"]

    # User1 tries to access WS2 — not a member
    resp = await client.get("/api/v1/workspace/", headers={
        "Authorization": f"Bearer {token1}",
        "X-Workspace-Id": ws2_id,
    })
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_cross_tenant_isolation(client):
    """Projects from workspace A are not visible from workspace B."""
    # Create workspace A
    reg_a = await client.post("/api/v1/auth/register", json={
        "email": "tenantA@test.com",
        "name": "Tenant A",
        "password": "securepass123",
        "workspace_name": "Tenant A WS",
    })
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Create project in A
    await client.post("/api/v1/projects/", json={"name": "A Project"}, headers=headers_a)

    # Create workspace B
    reg_b = await client.post("/api/v1/auth/register", json={
        "email": "tenantB@test.com",
        "name": "Tenant B",
        "password": "securepass123",
        "workspace_name": "Tenant B WS",
    })
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # B should see no projects
    resp = await client.get("/api/v1/projects/", headers=headers_b)
    assert resp.status_code == 200
    assert resp.json() == []
