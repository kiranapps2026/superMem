import pytest


@pytest.mark.asyncio
async def test_get_workspace(client, seeded_workspace):
    resp = await client.get("/api/v1/workspace/", headers=seeded_workspace["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == seeded_workspace["workspace_name"]


@pytest.mark.asyncio
async def test_get_workspace_requires_auth(client):
    resp = await client.get("/api/v1/workspace/")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invite_member_by_owner(client, seeded_workspace):
    resp = await client.post("/api/v1/workspace/members", json={
        "email": "member@test.com",
        "role": "member",
    }, headers=seeded_workspace["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_email"] == "member@test.com"
    assert data["role"] == "member"


@pytest.mark.asyncio
async def test_invite_forbidden_for_member(client):
    # Register a member workspace
    reg = await client.post("/api/v1/auth/register", json={
        "email": "memberuser@test.com",
        "name": "Member User",
        "password": "securepass123",
        "workspace_name": "Member WS",
    })
    member_token = reg.json()["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}"}

    # Register another workspace (owner)
    reg2 = await client.post("/api/v1/auth/register", json={
        "email": "other@test.com",
        "name": "Other Owner",
        "password": "securepass123",
        "workspace_name": "Other WS",
    })
    other_token = reg2.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Get other workspace ID
    ws_resp = await client.get("/api/v1/workspace/", headers=other_headers)
    ws_id = ws_resp.json()["id"]

    # Invite memberuser to other workspace as member
    invite_resp = await client.post("/api/v1/workspace/members", json={
        "email": "memberuser@test.com",
        "role": "member",
    }, headers=other_headers)
    assert invite_resp.status_code == 200

    # Now member tries to invite someone — should fail (member role)
    member_ws_headers = {"X-Workspace-Id": ws_id, "Authorization": f"Bearer {member_token}"}
    # First get the member's workspace context — switch workspace
    ws_resp2 = await client.get("/api/v1/workspace/", headers=member_ws_headers)
    assert ws_resp2.status_code == 200

    resp = await client.post("/api/v1/workspace/members", json={
        "email": "new@test.com",
        "role": "member",
    }, headers=member_ws_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_members(client, seeded_workspace):
    resp = await client.get("/api/v1/workspace/members", headers=seeded_workspace["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    emails = [m["user_email"] for m in data]
    assert seeded_workspace["email"] in emails
