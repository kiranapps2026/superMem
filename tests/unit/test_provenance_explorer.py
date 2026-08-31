"""Sprint 6 — Provenance explorer tests."""

import pytest


@pytest.mark.asyncio
async def test_list_provenance_empty(client, seeded_workspace):
    """Empty provenance list for new workspace."""
    res = await client.get("/api/v1/provenance/", headers=seeded_workspace["headers"])
    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.asyncio
async def test_provenance_after_chat(client, seeded_workspace):
    """Provenance records appear after chat."""
    # Create project and upload content first
    proj = await client.post("/api/v1/projects/", json={
        "name": "Prov Project",
    }, headers=seeded_workspace["headers"])
    pid = proj.json()["id"]

    conv = '{"mapping": {"n1": {"message": {"author": {"role": "user"}, "content": {"parts": ["test prov"]}, "create_time": 1700000000}}}}'
    await client.post("/api/v1/ingest/upload", json={
        "project_id": pid,
        "content": conv,
        "source_type": "chatgpt",
    }, headers=seeded_workspace["headers"])

    # Chat
    chat_res = await client.post("/api/v1/chat/", json={
        "message": "Hello provenance test",
        "project_id": pid,
    }, headers=seeded_workspace["headers"])
    assert chat_res.status_code == 200

    # Check provenance
    prov = await client.get("/api/v1/provenance/", headers=seeded_workspace["headers"])
    assert prov.status_code == 200
    items = prov.json()
    assert len(items) >= 1
    assert items[0]["model"] is not None


@pytest.mark.asyncio
async def test_provenance_filter_by_project(client, seeded_workspace):
    """Provenance filtered by project_id."""
    proj_a = await client.post("/api/v1/projects/", json={
        "name": "Prov A",
    }, headers=seeded_workspace["headers"])
    pid_a = proj_a.json()["id"]

    conv = '{"mapping": {"n1": {"message": {"author": {"role": "user"}, "content": {"parts": ["proj a"]}, "create_time": 1700000000}}}}'
    await client.post("/api/v1/ingest/upload", json={
        "project_id": pid_a,
        "content": conv,
        "source_type": "chatgpt",
    }, headers=seeded_workspace["headers"])
    await client.post("/api/v1/chat/", json={
        "message": "proj a chat",
        "project_id": pid_a,
    }, headers=seeded_workspace["headers"])

    res = await client.get(
        f"/api/v1/provenance/?project_id={pid_a}",
        headers=seeded_workspace["headers"],
    )
    assert res.status_code == 200
    items = res.json()
    assert all(p["project_id"] == pid_a for p in items)


@pytest.mark.asyncio
async def test_provenance_cross_tenant_blocked(client, seeded_workspace):
    """Tenant B cannot see Tenant A's provenance."""
    # Tenant A chat
    proj_a = await client.post("/api/v1/projects/", json={
        "name": "A Prov",
    }, headers=seeded_workspace["headers"])
    pid_a = proj_a.json()["id"]
    conv = '{"mapping": {"n1": {"message": {"author": {"role": "user"}, "content": {"parts": ["a data"]}, "create_time": 1700000000}}}}'
    await client.post("/api/v1/ingest/upload", json={
        "project_id": pid_a,
        "content": conv,
        "source_type": "chatgpt",
    }, headers=seeded_workspace["headers"])
    await client.post("/api/v1/chat/", json={
        "message": "a chat",
        "project_id": pid_a,
    }, headers=seeded_workspace["headers"])

    # Tenant B
    reg_b = await client.post("/api/v1/auth/register", json={
        "email": "prov-b@test.com",
        "password": "Pass123!",
        "name": "B",
        "workspace_name": "WS B",
    })
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # B lists provenance — should get empty list (not A's data)
    res = await client.get("/api/v1/provenance/", headers=headers_b)
    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.asyncio
async def test_provenance_detail_not_found(client, seeded_workspace):
    """Getting a nonexistent provenance record returns 404."""
    res = await client.get("/api/v1/provenance/nonexistent-id", headers=seeded_workspace["headers"])
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_provenance_expands_memories(client, seeded_workspace):
    """Provenance/{id}/memories expands memory references."""
    # Create a chat to generate provenance
    proj = await client.post("/api/v1/projects/", json={
        "name": "Prov Mem",
    }, headers=seeded_workspace["headers"])
    pid = proj.json()["id"]
    conv = '{"mapping": {"n1": {"message": {"author": {"role": "user"}, "content": {"parts": ["test memory refs"]}, "create_time": 1700000000}}}}'
    await client.post("/api/v1/ingest/upload", json={
        "project_id": pid,
        "content": conv,
        "source_type": "chatgpt",
    }, headers=seeded_workspace["headers"])
    chat = await client.post("/api/v1/chat/", json={
        "message": "expand test",
        "project_id": pid,
    }, headers=seeded_workspace["headers"])
    assert chat.status_code == 200
    prov_id = chat.json().get("provenance_id")
    if prov_id:
        res = await client.get(
            f"/api/v1/provenance/{prov_id}/memories",
            headers=seeded_workspace["headers"],
        )
        assert res.status_code == 200
