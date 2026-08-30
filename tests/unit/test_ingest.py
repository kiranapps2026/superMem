import pytest


@pytest.mark.asyncio
async def test_start_ingest_job(client, seeded_workspace):
    # First create a project
    proj = await client.post("/projects/", json={
        "name": "Ingest Project",
    }, headers=seeded_workspace["headers"])
    pid = proj.json()["id"]

    resp = await client.post("/ingest/", json={
        "project_id": pid,
        "source_type": "google_drive",
        "config": {"folder_id": "abc123"},
    }, headers=seeded_workspace["headers"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "queued"
    assert data["source_type"] == "google_drive"


@pytest.mark.asyncio
async def test_list_ingest_jobs(client, seeded_workspace):
    resp = await client.get("/ingest/jobs", headers=seeded_workspace["headers"])
    assert resp.status_code == 200
    assert "items" in resp.json()
    assert "total" in resp.json()


@pytest.mark.asyncio
async def test_get_ingest_job(client, seeded_workspace):
    proj = await client.post("/projects/", json={"name": "Job Project"}, headers=seeded_workspace["headers"])
    pid = proj.json()["id"]

    create = await client.post("/ingest/", json={
        "project_id": pid,
        "source_type": "web",
    }, headers=seeded_workspace["headers"])
    jid = create.json()["id"]

    resp = await client.get(f"/ingest/jobs/{jid}", headers=seeded_workspace["headers"])
    assert resp.status_code == 200
    assert resp.json()["id"] == jid
