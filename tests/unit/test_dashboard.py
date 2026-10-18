"""Sprint 6 — Dashboard API tests."""

import pytest


@pytest.mark.asyncio
async def test_workspace_overview(client, seeded_workspace):
    """GET /dashboard/ returns workspace overview with counts."""
    res = await client.get("/api/v1/dashboard/", headers=seeded_workspace["headers"])
    assert res.status_code == 200
    data = res.json()
    assert "workspace_id" in data
    assert "total_memories" in data
    assert "total_sources" in data
    assert "total_facts" in data
    assert "total_decisions" in data
    assert "memory_types" in data
    assert isinstance(data["total_memories"], int)
    assert isinstance(data["memory_types"], dict)


@pytest.mark.asyncio
async def test_workspace_overview_empty(client, seeded_workspace):
    """Empty workspace shows zero counts."""
    res = await client.get("/api/v1/dashboard/", headers=seeded_workspace["headers"])
    assert res.status_code == 200
    data = res.json()
    assert data["total_memories"] == 0
    assert data["total_sources"] == 0
    assert data["total_facts"] == 0


@pytest.mark.asyncio
async def test_dashboard_requires_auth(client):
    """Unauthenticated access rejected."""
    res = await client.get("/api/v1/dashboard/")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_project_dashboard(client, seeded_workspace):
    """GET /dashboard/{project_id} returns project stats."""
    # Create a project
    proj = await client.post("/api/v1/projects/", json={
        "name": "Dash Project",
        "description": "Test",
    }, headers=seeded_workspace["headers"])
    assert proj.status_code == 201
    project_id = proj.json()["id"]

    res = await client.get(
        f"/api/v1/dashboard/projects/{project_id}",
        headers=seeded_workspace["headers"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["project_id"] == project_id
    assert "total_memories" in data
    assert "total_sources" in data


@pytest.mark.asyncio
async def test_project_dashboard_404_for_other_workspace(client, seeded_workspace):
    """Another workspace can't view project dashboard."""
    # Create tenant B
    reg_b = await client.post("/api/v1/auth/register", json={
        "email": "dash-b@test.com",
        "password": "Pass123!",
        "name": "B",
        "workspace_name": "WS B",
    })
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # A creates project
    proj_a = await client.post("/api/v1/projects/", json={
        "name": "A Project",
    }, headers=seeded_workspace["headers"])
    pid_a = proj_a.json()["id"]

    # B tries to access
    res = await client.get(f"/api/v1/dashboard/projects/{pid_a}", headers=headers_b)
    assert res.status_code in (403, 404)


@pytest.mark.asyncio
async def test_dashboard_counts_accurate_after_ingest(client, seeded_workspace):
    """Dashboard reflects ingestion counts."""
    # Create project
    proj = await client.post("/api/v1/projects/", json={
        "name": "Ingest Dash",
    }, headers=seeded_workspace["headers"])
    pid = proj.json()["id"]

    # Upload a conversation
    conv = '{"mapping": {"n1": {"message": {"author": {"role": "user"}, "content": {"parts": ["test"]}, "create_time": 1700000000}}}}'
    await client.post("/api/v1/ingest/upload", json={
        "project_id": pid,
        "content": conv,
        "source_type": "chatgpt",
    }, headers=seeded_workspace["headers"])

    # Check dashboard reflects the source
    res = await client.get(f"/api/v1/dashboard/projects/{pid}", headers=seeded_workspace["headers"])
    assert res.status_code == 200
    data = res.json()
    assert data["total_sources"] >= 1
