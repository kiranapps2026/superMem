"""Sprint 6 — Pagination and filtering tests."""

import pytest


@pytest.mark.asyncio
async def test_memory_pagination(client, seeded_workspace):
    """List memories with offset/limit pagination."""
    token = seeded_workspace["headers"]["Authorization"]

    # Create 5 memories
    for i in range(5):
        await client.post("/api/v1/memory/", json={
            "memory_type": "episodic_memory",
            "content": f"Memory {i}",
        }, headers=seeded_workspace["headers"])

    # Page 1: limit=2
    res = await client.get("/api/v1/memory/?limit=2&offset=0", headers=seeded_workspace["headers"])
    assert res.status_code == 200
    page1 = res.json()
    assert len(page1) == 2

    # Page 2: limit=2, offset=2
    res2 = await client.get("/api/v1/memory/?limit=2&offset=2", headers=seeded_workspace["headers"])
    assert res2.status_code == 200
    page2 = res2.json()
    assert len(page2) == 2

    # Pages don't overlap
    page1_ids = {m["id"] for m in page1}
    page2_ids = {m["id"] for m in page2}
    assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.asyncio
async def test_memory_limit_rejects_over_max(client, seeded_workspace):
    """Limit > 200 returns 422."""
    res = await client.get("/api/v1/memory/?limit=500", headers=seeded_workspace["headers"])
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_memory_max_limit_works(client, seeded_workspace):
    """Limit at max (200) works."""
    res = await client.get("/api/v1/memory/?limit=200", headers=seeded_workspace["headers"])
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_memory_filter_by_type(client, seeded_workspace):
    """Filter memories by memory_type."""
    await client.post("/api/v1/memory/", json={
        "memory_type": "episodic_memory",
        "content": "Episodic",
    }, headers=seeded_workspace["headers"])
    await client.post("/api/v1/memory/", json={
        "memory_type": "procedural_memory",
        "content": "Procedural",
    }, headers=seeded_workspace["headers"])

    episodic = await client.get(
        "/api/v1/memory/?memory_type=episodic_memory",
        headers=seeded_workspace["headers"],
    )
    assert episodic.status_code == 200
    items = episodic.json()
    assert all(m["memory_type"] == "episodic_memory" for m in items)


@pytest.mark.asyncio
async def test_search_with_limit(client, seeded_workspace):
    """Memory search respects limit parameter."""
    await client.post("/api/v1/memory/", json={
        "content": "unique_search_term_xyz_123",
    }, headers=seeded_workspace["headers"])

    res = await client.post("/api/v1/memory/search", json={
        "query": "unique_search",
        "limit": 5,
    }, headers=seeded_workspace["headers"])
    assert res.status_code == 200
    results = res.json()
    assert len(results) <= 5
    assert any("unique_search_term_xyz_123" in r["content"] for r in results)


@pytest.mark.asyncio
async def test_search_case_insensitive(client, seeded_workspace):
    """Search is case-insensitive."""
    await client.post("/api/v1/memory/", json={
        "content": "UPPERCASE CONTENT",
    }, headers=seeded_workspace["headers"])

    res = await client.post("/api/v1/memory/search", json={
        "query": "uppercase",
    }, headers=seeded_workspace["headers"])
    assert res.status_code == 200
    assert len(res.json()) >= 1


@pytest.mark.asyncio
async def test_timeline_pagination(client, seeded_workspace):
    """Timeline endpoint supports pagination."""
    # Create some memories for timeline
    for i in range(3):
        await client.post("/api/v1/memory/", json={
            "content": f"Timeline event {i}",
            "memory_type": "semantic_memory",
        }, headers=seeded_workspace["headers"])

    res = await client.get("/api/v1/ingest/timeline?limit=2", headers=seeded_workspace["headers"])
    assert res.status_code == 200
    # Timeline returns mixed items
    items = res.json()
    assert len(items) <= 2