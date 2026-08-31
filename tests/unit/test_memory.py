import pytest


@pytest.mark.asyncio
async def test_add_memory(client, seeded_workspace):
    resp = await client.post("/api/v1/memory/", json={
        "content": "User prefers dark mode",
        "memory_type": "procedural_memory",
    }, headers=seeded_workspace["headers"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "User prefers dark mode"


@pytest.mark.asyncio
async def test_list_memories(client, seeded_workspace):
    await client.post("/api/v1/memory/", json={
        "content": "Memory one",
    }, headers=seeded_workspace["headers"])
    resp = await client.get("/api/v1/memory/", headers=seeded_workspace["headers"])
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_search_memories(client, seeded_workspace):
    await client.post("/api/v1/memory/", json={
        "content": "The user loves Python programming",
    }, headers=seeded_workspace["headers"])
    resp = await client.post("/api/v1/memory/search", json={
        "query": "Python",
    }, headers=seeded_workspace["headers"])
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
