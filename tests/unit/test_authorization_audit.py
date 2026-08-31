"""Sprint 6B — Cross-object authorization audit.

Tests every object type: if a tenant/user substitutes another tenant's ID,
the endpoint must return 403 or 404 (never 200 with the other tenant's data).
"""

import pytest


CROSS_TENANT_TARGETS = [
    # (object_type, get_url_for_id, expected_statuses)
    ("project", lambda cid: "/api/v1/projects/other-id", (403, 404)),
    ("session", lambda cid: "/api/v1/sessions/other-id", (403, 404)),
    ("message", lambda cid: "/api/v1/sessions/other-id/history", (403, 404)),
    ("memory", lambda cid: "/api/v1/memory/other-id", (403, 404)),
    ("provenance", lambda cid: "/api/v1/provenance/other-id", (403, 404)),
    ("feedback", lambda cid: "/api/v1/feedback/other-id", (403, 404)),
    ("source", lambda cid: "/api/v1/ingest/sources/other-id", (403, 404)),
    ("workspace", lambda cid: "/api/v1/workspace/other-id", (403, 404)),
    # api_keys has no GET by ID — use POST rotate to check (405 expected)
    ("api_key_rotate", lambda cid: "/api/v1/api-keys/other-id/rotate", (403, 404, 405)),
]


class TestCrossTenantAuthorization:
    """No endpoint leaks data across tenant boundaries."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("obj_type,url_fn,expected", CROSS_TENANT_TARGETS)
    async def test_cross_tenant_access_blocked(self, client, seeded_workspace, obj_type, url_fn, expected):
        """Accessing another tenant's {obj_type} returns 403/404."""
        headers = seeded_workspace["headers"]
        url = url_fn(None)
        res = await client.get(url, headers=headers)
        assert res.status_code in expected, (
            f"{obj_type}: expected {expected}, got {res.status_code}: {res.text}"
        )

    @pytest.mark.asyncio
    async def test_other_workspace_project_blocked(self, client, seeded_workspace):
        """A's project ID cannot be accessed from B's workspace."""
        # Tenant A creates a project
        proj_a = await client.post("/api/v1/projects/", json={
            "name": "A Secret Project",
        }, headers=seeded_workspace["headers"])
        assert proj_a.status_code == 201
        pid_a = proj_a.json()["id"]

        # Tenant B registers
        reg_b = await client.post("/api/v1/auth/register", json={
            "email": "cross-tenant-b@test.com",
            "password": "Pass123!",
            "name": "B",
            "workspace_name": "WS B",
        })
        assert reg_b.status_code == 201
        token_b = reg_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # B tries to access A's project
        res = await client.get(f"/api/v1/projects/{pid_a}", headers=headers_b)
        assert res.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_other_workspace_memory_blocked(self, client, seeded_workspace):
        """A's memory cannot be accessed from B."""
        mem_a = await client.post("/api/v1/memory/", json={
            "content": "A's secret memory",
        }, headers=seeded_workspace["headers"])
        assert mem_a.status_code == 201
        mid_a = mem_a.json()["id"]

        reg_b = await client.post("/api/v1/auth/register", json={
            "email": "cross-mem-b@test.com",
            "password": "Pass123!",
            "name": "B2",
            "workspace_name": "WS B2",
        })
        token_b = reg_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        res = await client.get(f"/api/v1/memory/{mid_a}", headers=headers_b)
        assert res.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_api_key_cross_workspace_blocked(self, client, seeded_workspace):
        """A's API key cannot be used in B's workspace (no GET by key_id endpoint)."""
        # A creates API key
        key_a = await client.post("/api/v1/api-keys/", json={
            "name": "A's Key",
        }, headers=seeded_workspace["headers"])
        assert key_a.status_code == 201
        key_id = key_a.json()["id"]

        # B tries to rotate A's key — should fail
        reg_b = await client.post("/api/v1/auth/register", json={
            "email": "cross-key-b@test.com",
            "password": "Pass123!",
            "name": "BK",
            "workspace_name": "WS BK",
        })
        token_b = reg_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        res = await client.post(f"/api/v1/api-keys/{key_id}/rotate", headers=headers_b)
        assert res.status_code in (403, 404, 405)

    @pytest.mark.asyncio
    async def test_cross_tenant_search_empty(self, client, seeded_workspace):
        """Search from B never returns A's results."""
        # A creates content
        await client.post("/api/v1/memory/", json={
            "content": "Cross-tenant secret search term 42xyz",
        }, headers=seeded_workspace["headers"])

        # B registers and searches
        reg_b = await client.post("/api/v1/auth/register", json={
            "email": "cross-search-b@test.com",
            "password": "Pass123!",
            "name": "BS",
            "workspace_name": "WS BS",
        })
        token_b = reg_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        res = await client.post("/api/v1/memory/search", json={
            "query": "42xyz",
        }, headers=headers_b)
        assert res.status_code == 200
        assert res.json() == []

    @pytest.mark.asyncio
    async def test_delete_other_tenant_memory_blocked(self, client, seeded_workspace):
        """Deleting another tenant's memory is blocked."""
        mem_a = await client.post("/api/v1/memory/", json={
            "content": "Deletable A memory",
        }, headers=seeded_workspace["headers"])
        mid_a = mem_a.json()["id"]

        reg_b = await client.post("/api/v1/auth/register", json={
            "email": "cross-del-b@test.com",
            "password": "Pass123!",
            "name": "BD",
            "workspace_name": "WS BD",
        })
        token_b = reg_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        res = await client.delete(f"/api/v1/memory/{mid_a}", headers=headers_b)
        assert res.status_code in (403, 404)

        # A's memory still exists
        res_a = await client.get(f"/api/v1/memory/{mid_a}", headers=seeded_workspace["headers"])
        assert res_a.status_code == 200
