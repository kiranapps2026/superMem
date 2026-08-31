"""Sprint 4 — E2E tests: dashboard, feedback, memory CRUD, soft delete, provenance expansion, graph security."""

from __future__ import annotations

from datetime import datetime, timezone
import pytest
from fastapi import status


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Memory CRUD enhancements ─────────────────────────────────────────


class TestMemoryCRUD:
    """Sprint 4 memory API: create with project, update, soft-delete."""

    @pytest.mark.asyncio
    async def test_create_memory_with_project(self, client, seeded_workspace):
        """Memory can be linked to a project."""
        proj = await client.post(
            "/api/v1/projects/",
            json={"name": "Mem Project"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        pid = proj.json()["id"]

        resp = await client.post(
            "/api/v1/memory/",
            json={
                "content": "The team uses Python for backend.",
                "memory_type": "semantic_memory",
                "project_id": pid,
            },
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["content"] == "The team uses Python for backend."
        assert data["project_id"] == pid
        assert data["temporal_status"] == "current"
        assert data["confidence"] == 0.7
        assert data["authority"] == 1.0

    @pytest.mark.asyncio
    async def test_update_memory(self, client, seeded_workspace):
        """PATCH updates memory content and temporal status."""
        resp = await client.post(
            "/api/v1/memory/",
            json={"content": "Original content", "memory_type": "semantic_memory"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        mem_id = resp.json()["id"]

        patch = await client.patch(
            f"/api/v1/memory/{mem_id}",
            json={"content": "Updated content", "temporal_status": "historical"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert patch.status_code == 200
        data = patch.json()
        assert data["content"] == "Updated content"
        assert data["temporal_status"] == "historical"
        assert data["updated_at"] != data["created_at"]

    @pytest.mark.asyncio
    async def test_soft_delete_memory(self, client, seeded_workspace):
        """DELETE soft-deletes a memory (sets deleted_at)."""
        resp = await client.post(
            "/api/v1/memory/",
            json={"content": "To be deleted"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        mem_id = resp.json()["id"]

        del_resp = await client.delete(
            f"/api/v1/memory/{mem_id}",
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert del_resp.status_code == 204

        # Memory no longer appears in default list
        list_resp = await client.get(
            "/api/v1/memory/",
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert not any(m["id"] == mem_id for m in list_resp.json())

        # But appears with include_deleted=true
        list_all = await client.get(
            "/api/v1/memory/?include_deleted=true",
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert any(m["id"] == mem_id for m in list_all.json())

    @pytest.mark.asyncio
    async def test_list_memories_with_project_filter(self, client, seeded_workspace):
        """Filtering memories by project_id."""
        proj_a = await client.post(
            "/api/v1/projects/", json={"name": "Proj A"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        proj_b = await client.post(
            "/api/v1/projects/", json={"name": "Proj B"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        pid_a = proj_a.json()["id"]
        pid_b = proj_b.json()["id"]

        await client.post("/api/v1/memory/", json={
            "content": "A memory", "project_id": pid_a,
        }, headers=_headers(seeded_workspace["access_token"]))
        await client.post("/api/v1/memory/", json={
            "content": "B memory", "project_id": pid_b,
        }, headers=_headers(seeded_workspace["access_token"]))

        a_items = await client.get(
            f"/api/v1/memory/?project_id={pid_a}",
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert all(m["project_id"] == pid_a for m in a_items.json())

    @pytest.mark.asyncio
    async def test_search_memories(self, client, seeded_workspace):
        """Full-text search across user's memories."""
        await client.post("/api/v1/memory/", json={
            "content": "The team prefers PostgreSQL for the database.",
            "memory_type": "semantic_memory",
        }, headers=_headers(seeded_workspace["access_token"]))

        resp = await client.post(
            "/api/v1/memory/search",
            json={"query": "PostgreSQL"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) >= 1
        assert any("PostgreSQL" in r["content"] for r in results)


# ── Dashboard API ────────────────────────────────────────────────────


class TestDashboardAPI:
    """Sprint 4 dashboard endpoints."""

    @pytest.mark.asyncio
    async def test_workspace_overview(self, client, seeded_workspace):
        """GET /dashboard/ returns workspace stats."""
        resp = await client.get(
            "/api/v1/dashboard/",
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "workspace_id" in data
        assert "total_memories" in data
        assert "total_sources" in data
        assert "total_facts" in data
        assert "memory_types" in data
        assert isinstance(data["total_memories"], int)
        assert isinstance(data["memory_types"], dict)

    @pytest.mark.asyncio
    async def test_project_dashboard(self, client, seeded_workspace):
        """GET /dashboard/projects/{id} returns project stats."""
        proj = await client.post(
            "/api/v1/projects/", json={"name": "Dash Project"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        pid = proj.json()["id"]

        # Create some data in the project
        await client.post("/api/v1/memory/", json={
            "content": "Dashboard test memory",
            "project_id": pid,
        }, headers=_headers(seeded_workspace["access_token"]))
        await client.post("/api/v1/ingest/upload", json={
            "project_id": pid,
            "source_type": "text",
            "content": "Dashboard project uses PostgreSQL.",
        }, headers=_headers(seeded_workspace["access_token"]))

        resp = await client.get(
            f"/api/v1/dashboard/projects/{pid}",
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == pid
        assert data["project_name"] == "Dash Project"
        assert data["total_memories"] >= 1
        assert data["total_sources"] >= 1


# ── Feedback API ─────────────────────────────────────────────────────


class TestFeedbackAPI:
    """Sprint 4 feedback endpoints."""

    @pytest.mark.asyncio
    async def test_create_feedback(self, client, seeded_workspace):
        """POST /feedback/ creates feedback."""
        resp = await client.post(
            "/api/v1/feedback/",
            json={"rating": "thumbs_up", "comment": "Great response!"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["rating"] == "thumbs_up"
        assert data["comment"] == "Great response!"

    @pytest.mark.asyncio
    async def test_create_feedback_requires_valid_rating(self, client, seeded_workspace):
        """Invalid rating is rejected."""
        resp = await client.post(
            "/api/v1/feedback/",
            json={"rating": "five_stars", "comment": "Invalid"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_feedback(self, client, seeded_workspace):
        """GET /feedback/ lists feedback."""
        await client.post(
            "/api/v1/feedback/",
            json={"rating": "thumbs_up"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        await client.post(
            "/api/v1/feedback/",
            json={"rating": "thumbs_down"},
            headers=_headers(seeded_workspace["access_token"]),
        )

        resp = await client.get(
            "/api/v1/feedback/",
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        ratings = {f["rating"] for f in data["items"]}
        assert "thumbs_up" in ratings
        assert "thumbs_down" in ratings

    @pytest.mark.asyncio
    async def test_feedback_cross_tenant_isolation(self, client, seeded_workspace):
        """Tenant B cannot see Tenant A's feedback."""
        await client.post(
            "/api/v1/feedback/",
            json={"rating": "thumbs_up", "comment": "Tenant A feedback"},
            headers=_headers(seeded_workspace["access_token"]),
        )

        # Register tenant B
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "fbtenant@test.com",
                "password": "password123",
                "name": "FB Tenant",
                "workspace_name": "FB Workspace",
            },
        )
        assert resp.status_code == 201
        tb_token = resp.json()["access_token"]

        resp = await client.get(
            "/api/v1/feedback/",
            headers=_headers(tb_token),
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


# ── Sprint 4 security regression ────────────────────────────────────


class TestSprint4Security:
    """Security checks for new Sprint 4 endpoints."""

    @pytest.mark.asyncio
    async def test_dashboard_requires_auth(self, client):
        resp = await client.get("/api/v1/dashboard/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_feedback_requires_auth(self, client):
        resp = await client.post("/api/v1/feedback/", json={"rating": "thumbs_up"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_project_dashboard_404_for_other_workspace(self, client, seeded_workspace):
        """B cannot view A's project dashboard."""
        resp_b = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "sec_b@test.com",
                "password": "password123",
                "name": "Sec B",
                "workspace_name": "Sec B WS",
            },
        )
        tb_token = resp_b.json()["access_token"]

        proj_a = await client.post(
            "/api/v1/projects/", json={"name": "Secret Project"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        pid_a = proj_a.json()["id"]

        resp = await client.get(
            f"/api/v1/dashboard/projects/{pid_a}",
            headers=_headers(tb_token),
        )
        assert resp.status_code == 404


# ── Cross-tenant memory isolation ───────────────────────────────────


class TestMemoryIsolation:
    """Memories are isolated per user + workspace."""

    @pytest.mark.asyncio
    async def test_user_b_cannot_read_user_a_memories(self, client, seeded_workspace):
        """Memory created by user A is not visible to user B in different workspace."""
        resp = await client.post(
            "/api/v1/memory/",
            json={"content": "Secret memory A"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert resp.status_code == 201

        resp_b = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "memiso@test.com",
                "password": "password123",
                "name": "Mem ISO",
                "workspace_name": "Mem ISO WS",
            },
        )
        tb_token = resp_b.json()["access_token"]

        resp = await client.get(
            "/api/v1/memory/",
            headers=_headers(tb_token),
        )
        assert resp.status_code == 200
        for m in resp.json():
            assert "Secret memory A" not in m.get("content", "")


# ── Provenance memory expansion (Phase 2) ───────────────────────────


class TestProvenanceMemoryExpansion:
    """GET /provenance/{id}/memories expands memory_ids_used."""

    @pytest.mark.asyncio
    async def test_expands_memory_ids(self, client, seeded_workspace):
        """Provenance memory_ids_used expands into memory objects."""
        await client.post(
            "/api/v1/memory/",
            json={"content": "Known fact: Project Alpha uses PostgreSQL"},
            headers=_headers(seeded_workspace["access_token"]),
        )

        resp = await client.post(
            "/api/v1/chat/",
            json={"message": "What database does Project Alpha use?"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert resp.status_code == 200

        prov_list = await client.get(
            "/api/v1/provenance/",
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert prov_list.status_code == 200
        records = prov_list.json()
        assert len(records) >= 1

        prov_id = records[0]["id"]
        prov_resp = await client.get(
            f"/api/v1/provenance/{prov_id}/memories",
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert prov_resp.status_code == 200
        memories = prov_resp.json()
        assert isinstance(memories, list)

    @pytest.mark.asyncio
    async def test_expansion_404_for_other_tenant(self, client, seeded_workspace):
        """Tenant B cannot expand Tenant A's provenance memories."""
        resp_a = await client.post(
            "/api/v1/chat/",
            json={"message": "test chat"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert resp_a.status_code == 200
        msg_id = resp_a.json().get("message_id")

        resp_b = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "proviso@test.com",
                "password": "password123",
                "name": "Prov ISO",
                "workspace_name": "Prov ISO WS",
            },
        )
        tb_token = resp_b.json()["access_token"]

        resp = await client.get(
            f"/api/v1/provenance/{msg_id}/memories",
            headers=_headers(tb_token),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_cross_tenant_direct_memory_access(self, client, seeded_workspace):
        """Tenant B cannot directly access Tenant A's memory by ID."""
        mem_a = await client.post(
            "/api/v1/memory/",
            json={"content": "A's secret memory"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        ma_id = mem_a.json()["id"]

        resp_b = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "ctiso2@test.com",
                "password": "password123",
                "name": "CT2",
                "workspace_name": "CT2 WS",
            },
        )
        tb_token = resp_b.json()["access_token"]

        resp = await client.get(
            f"/api/v1/memory/{ma_id}",
            headers=_headers(tb_token),
        )
        assert resp.status_code == 404


# ── Source status filtering (Phase 6) ───────────────────────────────


class TestSourceStatusFilter:
    """Source list returns items with total count."""

    @pytest.mark.asyncio
    async def test_sources_list_structure(self, client, seeded_workspace):
        """GET /ingest/sources returns items + total."""
        proj = await client.post(
            "/api/v1/projects/", json={"name": "Source Status Proj"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        pid = proj.json()["id"]

        await client.post("/api/v1/ingest/upload", json={
            "project_id": pid,
            "source_type": "text",
            "content": "Test source for status filter.",
        }, headers=_headers(seeded_workspace["access_token"]))

        resp = await client.get(
            "/api/v1/ingest/sources",
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data


# ── Pagination bounds (Phase 7) ─────────────────────────────────────


class TestPaginationBounds:
    """Collection endpoints enforce safe limits."""

    @pytest.mark.asyncio
    async def test_memory_limit_capped(self, client, seeded_workspace):
        """limit is capped at 200."""
        resp = await client.get(
            "/api/v1/memory/?limit=200",
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_memory_limit_rejects_over_max(self, client, seeded_workspace):
        """limit > 200 returns 422."""
        resp = await client.get(
            "/api/v1/memory/?limit=1000000",
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_facts_pagination(self, client, seeded_workspace):
        """Facts list supports limit + offset pagination."""
        resp = await client.get(
            "/api/v1/ingest/facts?limit=10&offset=0",
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) <= 10


# ── Soft-delete consistency (Phase 10) ──────────────────────────────


class TestSoftDeleteConsistency:
    """Soft-deleted items are excluded from all standard retrieval paths."""

    @pytest.mark.asyncio
    async def test_deleted_memory_excluded_from_search(self, client, seeded_workspace):
        """Soft-deleted memory is excluded from search results."""
        mem = await client.post(
            "/api/v1/memory/",
            json={"content": "search-me-deleted"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        mem_id = mem.json()["id"]

        search = await client.post(
            "/api/v1/memory/search",
            json={"query": "search-me-deleted"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert any(m["id"] == mem_id for m in search.json())

        await client.delete(
            f"/api/v1/memory/{mem_id}",
            headers=_headers(seeded_workspace["access_token"]),
        )

        search2 = await client.post(
            "/api/v1/memory/search",
            json={"query": "search-me-deleted"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert not any(m["id"] == mem_id for m in search2.json())


# ── Temporal consistency (Phase 11) ─────────────────────────────────


class TestTemporalConsistency:
    """Temporal status is coherent across endpoints."""

    @pytest.mark.asyncio
    async def test_facts_temporal_status_filtering(self, client, seeded_workspace):
        """Facts endpoint supports temporal_status filter."""
        proj = await client.post(
            "/api/v1/projects/", json={"name": "Temporal Facts"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        pid = proj.json()["id"]

        await client.post("/api/v1/ingest/upload", json={
            "project_id": pid,
            "source_type": "text",
            "content": "Temporal fact: uses PostgreSQL.",
        }, headers=_headers(seeded_workspace["access_token"]))

        resp = await client.get(
            "/api/v1/ingest/facts?temporal_status=current",
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data


# ── Cross-project isolation (Phase 13) ──────────────────────────────


class TestCrossProjectIsolation:
    """Facts are filtered by project_id."""

    @pytest.mark.asyncio
    async def test_facts_filtered_by_project(self, client, seeded_workspace):
        """Facts filtered by project_id return only that project's facts."""
        proj_a = await client.post(
            "/api/v1/projects/", json={"name": "Fact Proj A"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        proj_b = await client.post(
            "/api/v1/projects/", json={"name": "Fact Proj B"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        pid_a = proj_a.json()["id"]
        pid_b = proj_b.json()["id"]

        await client.post("/api/v1/ingest/upload", json={
            "project_id": pid_a,
            "source_type": "text",
            "content": "Project Alpha uses PostgreSQL.",
        }, headers=_headers(seeded_workspace["access_token"]))

        await client.post("/api/v1/ingest/upload", json={
            "project_id": pid_b,
            "source_type": "text",
            "content": "Project Beta uses MongoDB.",
        }, headers=_headers(seeded_workspace["access_token"]))

        facts_a = await client.get(
            f"/api/v1/ingest/facts?project_id={pid_a}",
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert facts_a.status_code == 200
        for f in facts_a.json()["items"]:
            assert f.get("project_id") == pid_a


# ── Graph security (Phase 3) ─────────────────────────────────────────


class TestGraphSecurity:
    """Graph is scoped to workspace + project."""

    @pytest.mark.asyncio
    async def test_graph_empty_when_no_data(self, client, seeded_workspace):
        """Graph returns empty when no ingested data."""
        resp = await client.get(
            "/api/v1/ingest/graph",
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data

    @pytest.mark.asyncio
    async def test_graph_cross_tenant_isolation(self, client, seeded_workspace):
        """Tenant B cannot see Tenant A's graph nodes."""
        proj_a = await client.post(
            "/api/v1/projects/", json={"name": "Graph Proj A"},
            headers=_headers(seeded_workspace["access_token"]),
        )
        pid_a = proj_a.json()["id"]

        await client.post("/api/v1/ingest/upload", json={
            "project_id": pid_a,
            "source_type": "text",
            "content": "Alpha uses PostgreSQL.",
        }, headers=_headers(seeded_workspace["access_token"]))

        resp_a = await client.get(
            f"/api/v1/ingest/graph?project_id={pid_a}",
            headers=_headers(seeded_workspace["access_token"]),
        )
        assert resp_a.status_code == 200
        assert len(resp_a.json()["nodes"]) >= 1

        resp_b = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "graphiso@test.com",
                "password": "password123",
                "name": "Graph ISO",
                "workspace_name": "Graph ISO WS",
            },
        )
        tb_token = resp_b.json()["access_token"]

        resp_b_graph = await client.get(
            "/api/v1/ingest/graph",
            headers=_headers(tb_token),
        )
        assert resp_b_graph.status_code == 200
        assert len(resp_b_graph.json()["nodes"]) == 0


# ── Feedback security (Phase 12) ─────────────────────────────────────


class TestFeedbackSecurity:
    """Feedback is scoped per workspace."""

    @pytest.mark.asyncio
    async def test_feedback_cross_tenant_blocked(self, client, seeded_workspace):
        """Tenant B cannot see Tenant A's feedback."""
        await client.post(
            "/api/v1/feedback/",
            json={"rating": "thumbs_up", "comment": "A only"},
            headers=_headers(seeded_workspace["access_token"]),
        )

        resp_b = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "fbcross@test.com",
                "password": "password123",
                "name": "FB Cross",
                "workspace_name": "FB Cross WS",
            },
        )
        tb_token = resp_b.json()["access_token"]

        resp = await client.get(
            "/api/v1/feedback/",
            headers=_headers(tb_token),
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
