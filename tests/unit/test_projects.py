import pytest


@pytest.mark.asyncio
async def test_create_project(client, seeded_workspace):
    resp = await client.post("/api/v1/projects/", json={
        "name": "My Project",
        "description": "A test project",
    }, headers=seeded_workspace["headers"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Project"
    assert data["description"] == "A test project"


@pytest.mark.asyncio
async def test_list_projects_empty(client, seeded_workspace):
    resp = await client.get("/api/v1/projects/", headers=seeded_workspace["headers"])
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_project(client, seeded_workspace):
    create = await client.post("/api/v1/projects/", json={
        "name": "Get Me",
    }, headers=seeded_workspace["headers"])
    pid = create.json()["id"]

    resp = await client.get(f"/api/v1/projects/{pid}", headers=seeded_workspace["headers"])
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get Me"


@pytest.mark.asyncio
async def test_update_project(client, seeded_workspace):
    create = await client.post("/api/v1/projects/", json={
        "name": "Original",
    }, headers=seeded_workspace["headers"])
    pid = create.json()["id"]

    resp = await client.patch(f"/api/v1/projects/{pid}", json={
        "name": "Updated",
    }, headers=seeded_workspace["headers"])
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"


@pytest.mark.asyncio
async def test_soft_delete_project(client, seeded_workspace):
    create = await client.post("/api/v1/projects/", json={
        "name": "To Delete",
    }, headers=seeded_workspace["headers"])
    pid = create.json()["id"]

    resp = await client.delete(f"/api/v1/projects/{pid}", headers=seeded_workspace["headers"])
    assert resp.status_code == 204

    # Should not be found after delete
    resp2 = await client.get(f"/api/v1/projects/{pid}", headers=seeded_workspace["headers"])
    assert resp2.status_code == 404
