import pytest


@pytest.mark.asyncio
async def test_chat_creates_session(client, seeded_workspace):
    resp = await client.post("/chat/", json={
        "message": "Hello from chat",
    }, headers=seeded_workspace["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["response"]
    assert data["session_id"]


@pytest.mark.asyncio
async def test_chat_with_existing_session(client, seeded_workspace):
    # Create a session first
    sess = await client.post("/sessions/", json={}, headers=seeded_workspace["headers"])
    sid = sess.json()["id"]

    resp = await client.post("/chat/", json={
        "message": "Hello again",
        "session_id": sid,
    }, headers=seeded_workspace["headers"])
    assert resp.status_code == 200
    assert resp.json()["session_id"] == sid


@pytest.mark.asyncio
async def test_chat_requires_auth(client):
    resp = await client.post("/chat/", json={"message": "test"})
    assert resp.status_code == 401
