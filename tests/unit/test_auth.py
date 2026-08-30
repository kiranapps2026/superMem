import pytest


@pytest.mark.asyncio
async def test_register(client):
    resp = await client.post("/auth/register", json={
        "email": "newuser@test.com",
        "name": "New User",
        "password": "securepass123",
        "workspace_name": "My Workspace",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post("/auth/register", json={
        "email": "dup@test.com",
        "name": "First",
        "password": "securepass123",
        "workspace_name": "WS1",
    })
    resp = await client.post("/auth/register", json={
        "email": "dup@test.com",
        "name": "Second",
        "password": "securepass123",
        "workspace_name": "WS2",
    })
    assert resp.status_code == 400
    assert "already" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/auth/register", json={
        "email": "loginok@test.com",
        "name": "Login User",
        "password": "securepass123",
        "workspace_name": "Login WS",
    })
    resp = await client.post("/auth/login", json={
        "email": "loginok@test.com",
        "password": "securepass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/auth/register", json={
        "email": "wrongpw@test.com",
        "name": "WP User",
        "password": "securepass123",
        "workspace_name": "WP WS",
    })
    resp = await client.post("/auth/login", json={
        "email": "wrongpw@test.com",
        "password": "incorrect",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client):
    reg = await client.post("/auth/register", json={
        "email": "me@test.com",
        "name": "Me User",
        "password": "securepass123",
        "workspace_name": "Me WS",
    })
    token = reg.json()["access_token"]
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "me@test.com"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client):
    reg = await client.post("/auth/register", json={
        "email": "refresh@test.com",
        "name": "Refresh User",
        "password": "securepass123",
        "workspace_name": "Refresh WS",
    })
    refresh_token = reg.json()["refresh_token"]
    resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_refresh_invalid_token(client):
    resp = await client.post("/auth/refresh", json={"refresh_token": "totally-fake"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout(client):
    reg = await client.post("/auth/register", json={
        "email": "logout@test.com",
        "name": "Logout User",
        "password": "securepass123",
        "workspace_name": "Logout WS",
    })
    refresh_token = reg.json()["refresh_token"]
    resp = await client.post("/auth/logout", json={"refresh_token": refresh_token},
                             headers={"Authorization": f"Bearer {reg.json()['access_token']}"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_password_not_returned(client):
    reg = await client.post("/auth/register", json={
        "email": "nopw@test.com",
        "name": "No PW",
        "password": "securepass123",
        "workspace_name": "NoPW WS",
    })
    token = reg.json()["access_token"]
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    data = resp.json()
    assert "hashed_password" not in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    resp = await client.post("/auth/login", json={
        "email": "nobody@test.com",
        "password": "anything",
    })
    assert resp.status_code == 401
