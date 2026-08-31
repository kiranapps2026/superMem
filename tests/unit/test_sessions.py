import pytest


@pytest.mark.asyncio
async def test_create_session(client, seeded_workspace):
    resp = await client.post("/api/v1/sessions/", json={
        "title": "Test Session",
    }, headers=seeded_workspace["headers"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test Session"


@pytest.mark.asyncio
async def test_get_session(client, seeded_workspace):
    create = await client.post("/api/v1/sessions/", json={
        "title": "Session to get",
    }, headers=seeded_workspace["headers"])
    sid = create.json()["id"]

    resp = await client.get(f"/api/v1/sessions/{sid}", headers=seeded_workspace["headers"])
    assert resp.status_code == 200
    assert resp.json()["title"] == "Session to get"


@pytest.mark.asyncio
async def test_add_message(client, seeded_workspace):
    create = await client.post("/api/v1/sessions/", json={}, headers=seeded_workspace["headers"])
    sid = create.json()["id"]

    resp = await client.post(f"/api/v1/sessions/{sid}/messages", json={
        "role": "user",
        "content": "Hello world",
    }, headers=seeded_workspace["headers"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "Hello world"
    assert data["role"] == "user"


@pytest.mark.asyncio
async def test_delete_session(client, seeded_workspace):
    create = await client.post("/api/v1/sessions/", json={}, headers=seeded_workspace["headers"])
    sid = create.json()["id"]

    resp = await client.delete(f"/api/v1/sessions/{sid}", headers=seeded_workspace["headers"])
    assert resp.status_code == 204

    resp2 = await client.get(f"/api/v1/sessions/{sid}", headers=seeded_workspace["headers"])
    assert resp2.status_code == 404
