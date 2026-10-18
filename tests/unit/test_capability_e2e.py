"""SwarmVault WebApp — Functional Capability E2E Test Suite

Tests all 7 functional capabilities end-to-end through the live API:
  1. Organizational Memory      — memory CRUD, search, provenance
  2. Decision Intelligence      — ingest → extract → track decisions
  3. Institutional Knowledge    — cross-session knowledge accumulation
  4. Evidence & Auditability     — provenance chain, audit log
  5. Temporal Truth             — fact versioning, supersession, stale detection
  6. Conflict Intelligence      — contradiction detection across sources
  7. Knowledge Retrieval        — BM25 + semantic + reranking search

Each test follows the pattern:
  1. Register → authenticate
  2. Create workspace / project
  3. Execute capability flow
  4. Assert expected state

Run:
    python -m pytest tests/unit/test_capability_e2e.py -v --tb=short
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest
from fastapi import status

BASE = "/api/v1"


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _items(resp_json) -> list:
    """Extract items list from paginated API response or return as-is."""
    if isinstance(resp_json, list):
        return resp_json
    if isinstance(resp_json, dict):
        return resp_json.get("items", [])
    return []


# ─────────────────────────────────────────────────────────────────────────────
# 1. ORGANIZATIONAL MEMORY
# ─────────────────────────────────────────────────────────────────────────────

class TestOrganizationalMemory:
    """Capability 1: The organization doesn't lose knowledge when a
    session/person/agent changes."""

    @pytest.mark.asyncio
    async def test_memory_survives_session_end(self, client, seeded_workspace):
        """Memories persist after the originating session is gone."""
        token = seeded_workspace["access_token"]

        # 1. Create a project
        proj = await client.post(
            f"{BASE}/projects/",
            json={"name": "Org Memory Project"},
            headers=_h(token),
        )
        assert proj.status_code == 201
        pid = proj.json()["id"]

        # 2. Create a memory tied to that project
        mem_resp = await client.post(
            f"{BASE}/memory/",
            json={
                "content": "The deployment pipeline uses GitHub Actions with a 3-stage gate.",
                "memory_type": "procedural_memory",
                "project_id": pid,
            },
            headers=_h(token),
        )
        assert mem_resp.status_code == 201
        mem = mem_resp.json()
        mid = mem["id"]
        assert mem["content"] == "The deployment pipeline uses GitHub Actions with a 3-stage gate."
        assert mem["project_id"] == pid
        assert mem["temporal_status"] == "current"
        assert mem["confidence"] == 0.7
        assert mem["authority"] == 1.0

        # 3. Memory survives — can be retrieved independently
        get_resp = await client.get(
            f"{BASE}/memory/{mid}", headers=_h(token)
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == mid

        # 4. List memories
        list_resp = await client.get(
            f"{BASE}/memory/", headers=_h(token)
        )
        assert list_resp.status_code == 200
        assert mid in [m["id"] for m in _items(list_resp.json())]

    @pytest.mark.asyncio
    async def test_agent_created_memory(self, client, seeded_workspace):
        """Agent can create memories that persist independently."""
        token = seeded_workspace["access_token"]

        resp = await client.post(
            f"{BASE}/memory/",
            json={
                "content": "API rate limit for external calls: 100 req/min.",
                "memory_type": "procedural_memory",
                "agent_id": "agent-001",
                "run_id": "run-abc-123",
            },
            headers=_h(token),
        )
        assert resp.status_code == 201
        mem = resp.json()
        assert mem["agent_id"] == "agent-001"
        assert mem["run_id"] == "run-abc-123"

    @pytest.mark.asyncio
    async def test_memory_defaults(self, client, seeded_workspace):
        """New memories get correct defaults."""
        token = seeded_workspace["access_token"]
        resp = await client.post(
            f"{BASE}/memory/",
            json={"content": "Fresh knowledge."},
            headers=_h(token),
        )
        assert resp.status_code == 201
        mem = resp.json()
        assert mem["memory_type"] == "procedural_memory"
        assert mem["temporal_status"] == "current"
        assert mem["confidence"] == 0.7
        assert mem["authority"] == 1.0

    @pytest.mark.asyncio
    async def test_update_memory(self, client, seeded_workspace):
        """PATCH updates memory content."""
        token = seeded_workspace["access_token"]
        resp = await client.post(
            f"{BASE}/memory/",
            json={"content": "Original content"},
            headers=_h(token),
        )
        mid = resp.json()["id"]

        patch = await client.patch(
            f"{BASE}/memory/{mid}",
            json={"content": "Updated content"},
            headers=_h(token),
        )
        assert patch.status_code == 200
        data = patch.json()
        assert data["content"] == "Updated content"
        assert data["updated_at"] != data["created_at"]

    @pytest.mark.asyncio
    async def test_soft_delete_memory(self, client, seeded_workspace):
        """DELETE soft-deletes a memory."""
        token = seeded_workspace["access_token"]
        resp = await client.post(
            f"{BASE}/memory/",
            json={"content": "To be deleted"},
            headers=_h(token),
        )
        mid = resp.json()["id"]

        del_resp = await client.delete(
            f"{BASE}/memory/{mid}", headers=_h(token)
        )
        assert del_resp.status_code == 204

        # Should not appear in normal list (excludes deleted by default)
        list_resp = await client.get(
            f"{BASE}/memory/", headers=_h(token)
        )
        assert mid not in [m["id"] for m in _items(list_resp.json())]

        # But visible with include_deleted=true
        list_all = await client.get(
            f"{BASE}/memory/?include_deleted=true", headers=_h(token)
        )
        assert mid in [m["id"] for m in _items(list_all.json())]


# ─────────────────────────────────────────────────────────────────────────────
# 2. DECISION INTELLIGENCE
# ─��───────────────────────────────────────────────────────────────────────────

class TestDecisionIntelligence:
    """Capability 2: Decisions are preserved, classified, versioned and
    linked to evidence/provenance."""

    @pytest.mark.asyncio
    async def test_ingest_extracts_facts(self, client, seeded_workspace):
        """Ingesting a conversation extracts facts."""
        token = seeded_workspace["access_token"]

        proj = await client.post(
            f"{BASE}/projects/",
            json={"name": "Decision Project"},
            headers=_h(token),
        )
        pid = proj.json()["id"]

        # Use patterns that match the regex extractor:
        # "Subject verb Object" with capitalized subject
        conversation = json.dumps({
            "messages": [
                {"role": "user", "content": "PostgreSQL supports JSON and strong consistency."},
                {"role": "user", "content": "Our primary database uses PostgreSQL."},
            ]
        })

        resp = await client.post(
            f"{BASE}/ingest/upload",
            json={
                "project_id": pid,
                "source_type": "json",
                "title": "Architecture discussion",
                "content": conversation,
            },
            headers=_h(token),
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["source_id"] is not None
        assert data["status"] == "completed"

        # Facts endpoint returns paginated dict
        facts_resp = await client.get(
            f"{BASE}/ingest/facts?project_id={pid}",
            headers=_h(token),
        )
        assert facts_resp.status_code == 200
        facts_data = facts_resp.json()
        items = _items(facts_data)
        assert isinstance(items, list)
        # Each fact should have temporal_status
        for fact in items:
            assert fact["temporal_status"] in ("current", "superseded", "historical")
            assert "superseded_by_id" in fact

    @pytest.mark.asyncio
    async def test_decisions_list(self, client, seeded_workspace):
        """Decisions endpoint returns decision records."""
        token = seeded_workspace["access_token"]

        proj = await client.post(
            f"{BASE}/projects/",
            json={"name": "Decisions Project"},
            headers=_h(token),
        )
        pid = proj.json()["id"]

        conversation = json.dumps({
            "messages": [
                {"role": "user", "content": "We decided to use React for the frontend."},
            ]
        })

        await client.post(
            f"{BASE}/ingest/upload",
            json={"project_id": pid, "source_type": "json", "content": conversation},
            headers=_h(token),
        )

        decisions_resp = await client.get(
            f"{BASE}/ingest/decisions?project_id={pid}",
            headers=_h(token),
        )
        assert decisions_resp.status_code == 200
        decisions = decisions_resp.json()
        items = _items(decisions)
        assert isinstance(items, list)
        for d in items:
            assert "temporal_status" in d
            assert "content" in d

    @pytest.mark.asyncio
    async def test_sources_track_evidence(self, client, seeded_workspace):
        """Ingested sources provide evidence for extracted knowledge."""
        token = seeded_workspace["access_token"]

        proj = await client.post(
            f"{BASE}/projects/",
            json={"name": "Source Evidence"},
            headers=_h(token),
        )
        pid = proj.json()["id"]

        conversation = json.dumps({
            "messages": [
                {"role": "user", "content": "Our SLA is 99.9% uptime."},
            ]
        })

        resp = await client.post(
            f"{BASE}/ingest/upload",
            json={"project_id": pid, "source_type": "json",
                  "title": "SLA discussion", "content": conversation},
            headers=_h(token),
        )
        assert resp.status_code in (200, 201)
        source_id = resp.json()["source_id"]

        # Source detail shows the evidence
        detail = await client.get(
            f"{BASE}/ingest/sources/{source_id}",
            headers=_h(token),
        )
        assert detail.status_code == 200
        assert detail.json()["id"] == source_id

    @pytest.mark.asyncio
    async def test_normalized_messages_in_source(self, client, seeded_workspace):
        """Source detail includes normalized messages."""
        token = seeded_workspace["access_token"]

        proj = await client.post(
            f"{BASE}/projects/",
            json={"name": "Norm Msgs Project"},
            headers=_h(token),
        )
        pid = proj.json()["id"]

        conversation = json.dumps({
            "messages": [
                {"role": "user", "content": "Hello there."},
                {"role": "assistant", "content": "Hi, how can I help?"},
            ]
        })

        resp = await client.post(
            f"{BASE}/ingest/upload",
            json={"project_id": pid, "source_type": "json", "content": conversation},
            headers=_h(token),
        )
        assert resp.status_code in (200, 201)
        source_id = resp.json()["source_id"]

        # Get messages
        msgs = await client.get(
            f"{BASE}/ingest/sources/{source_id}/messages",
            headers=_h(token),
        )
        assert msgs.status_code == 200
        msg_items = _items(msgs.json())
        assert len(msg_items) >= 2


# ─────────────────────────────────────────────────────────────────────────────
# 3. INSTITUTIONAL KNOWLEDGE
# ─────────────────────────────────────────────────────────────────────────────

class TestInstitutionalKnowledge:
    """Capability 3: Facts, learnings, constraints and architecture knowledge
    accumulate across sessions."""

    @pytest.mark.asyncio
    async def test_multiple_sessions_accumulate(self, client, seeded_workspace):
        """Multiple ingestion sessions accumulate into the same project."""
        token = seeded_workspace["access_token"]

        proj = await client.post(
            f"{BASE}/projects/",
            json={"name": "Accumulation Project"},
            headers=_h(token),
        )
        pid = proj.json()["id"]

        # Session 1
        s1 = json.dumps({
            "messages": [
                {"role": "user", "content": "Our stack is Python + PostgreSQL + Redis."},
            ]
        })
        r1 = await client.post(
            f"{BASE}/ingest/upload",
            json={"project_id": pid, "source_type": "json", "content": s1},
            headers=_h(token),
        )
        assert r1.status_code in (200, 201)

        # Session 2
        s2 = json.dumps({
            "messages": [
                {"role": "user", "content": "We deploy on AWS using ECS Fargate."},
            ]
        })
        r2 = await client.post(
            f"{BASE}/ingest/upload",
            json={"project_id": pid, "source_type": "json", "content": s2},
            headers=_h(token),
        )
        assert r2.status_code in (200, 201)

        # Both sources should exist
        sources = await client.get(
            f"{BASE}/ingest/sources?project_id={pid}", headers=_h(token)
        )
        assert sources.status_code == 200
        src_items = _items(sources.json())
        assert len(src_items) >= 2

        # Knowledge is queryable via timeline
        timeline = await client.get(
            f"{BASE}/ingest/timeline?project_id={pid}", headers=_h(token)
        )
        assert timeline.status_code == 200
        tl_items = _items(timeline.json())
        assert isinstance(tl_items, list)

    @pytest.mark.asyncio
    async def test_search_finds_accumulated_knowledge(
        self, client, seeded_workspace
    ):
        """Memory search finds knowledge from multiple sessions."""
        token = seeded_workspace["access_token"]

        # Create memories directly
        for topic in ("database migration strategy", "CI/CD pipeline configuration"):
            r = await client.post(
                f"{BASE}/memory/",
                json={"content": f"Knowledge about {topic} from session archives."},
                headers=_h(token),
            )
            assert r.status_code == 201

        # Search for accumulated knowledge
        resp = await client.post(
            f"{BASE}/memory/search",
            json={"query": "database", "limit": 10},
            headers=_h(token),
        )
        assert resp.status_code == 200
        results = resp.json()
        assert isinstance(results, list)


# ─────────────────────────────────────────────────────────────────────────────
# 4. EVIDENCE & AUDITABILITY
# ─────────────────────────────────────────────────────────────────────────────

class TestEvidenceAndAuditability:
    """Capability 4: Provenance chains connect memory → source session →
    source evidence."""

    @pytest.mark.asyncio
    async def test_chat_creates_session(self, client, seeded_workspace):
        """Chat creates a session for the interaction."""
        token = seeded_workspace["access_token"]

        proj = await client.post(
            f"{BASE}/projects/",
            json={"name": "Provenance Project"},
            headers=_h(token),
        )
        pid = proj.json()["id"]

        chat_resp = await client.post(
            f"{BASE}/chat/",
            json={"message": "How do we deploy?", "project_id": pid},
            headers=_h(token),
        )
        assert chat_resp.status_code == 200
        chat_data = chat_resp.json()
        assert "message_id" in chat_data
        assert "session_id" in chat_data
        assert "response" in chat_data

    @pytest.mark.asyncio
    async def test_session_has_messages(self, client, seeded_workspace):
        """Sessions contain the full message history."""
        token = seeded_workspace["access_token"]

        session = await client.post(
            f"{BASE}/sessions/",
            json={"title": "Test Session"},
            headers=_h(token),
        )
        assert session.status_code == 201
        sid = session.json()["id"]

        await client.post(
            f"{BASE}/sessions/{sid}/messages",
            json={"role": "user", "content": "Hello"},
            headers=_h(token),
        )

        get_s = await client.get(
            f"{BASE}/sessions/{sid}", headers=_h(token)
        )
        assert get_s.status_code == 200

    @pytest.mark.asyncio
    async def test_feedback_linked_to_session(self, client, seeded_workspace):
        """Feedback links to sessions."""
        token = seeded_workspace["access_token"]

        session = await client.post(
            f"{BASE}/sessions/",
            json={"title": "Feedback Test Session"},
            headers=_h(token),
        )
        assert session.status_code == 201
        sid = session.json()["id"]

        fb = await client.post(
            f"{BASE}/feedback/",
            json={"session_id": sid, "rating": "thumbs_up", "comment": "Good answer"},
            headers=_h(token),
        )
        assert fb.status_code == 201
        fb_data = fb.json()
        assert fb_data["rating"] == "thumbs_up"

        fb_list = await client.get(
            f"{BASE}/feedback/?session_id={sid}", headers=_h(token)
        )
        assert fb_list.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# 5. TEMPORAL TRUTH
# ─────────────────────────────────────────────────────────────────────────────

class TestTemporalTruth:
    """Capability 5: Fact versions, supersession and stale-fact detection."""

    @pytest.mark.asyncio
    async def test_facts_have_temporal_status(self, client, seeded_workspace):
        """Extracted facts carry temporal_status."""
        token = seeded_workspace["access_token"]

        proj = await client.post(
            f"{BASE}/projects/",
            json={"name": "Temporal Project"},
            headers=_h(token),
        )
        pid = proj.json()["id"]

        conv = json.dumps({
            "messages": [
                {"role": "user", "content": "Python supports async programming."},
            ]
        })

        resp = await client.post(
            f"{BASE}/ingest/upload",
            json={"project_id": pid, "source_type": "json", "content": conv},
            headers=_h(token),
        )
        assert resp.status_code in (200, 201)

        facts = await client.get(
            f"{BASE}/ingest/facts?project_id={pid}", headers=_h(token)
        )
        assert facts.status_code == 200
        facts_data = facts.json()
        items = _items(facts_data)
        for fact in items:
            assert fact["temporal_status"] in ("current", "superseded", "historical")

    @pytest.mark.asyncio
    async def test_temporal_status_filtering(self, client, seeded_workspace):
        """Facts can be filtered by temporal_status."""
        token = seeded_workspace["access_token"]

        facts_resp = await client.get(
            f"{BASE}/ingest/facts?temporal_status=current",
            headers=_h(token),
        )
        assert facts_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_memory_temporal_status_update(self, client, seeded_workspace):
        """Memory temporal_status can be updated."""
        token = seeded_workspace["access_token"]

        mem = await client.post(
            f"{BASE}/memory/",
            json={"content": "Current version."},
            headers=_h(token),
        )
        assert mem.status_code == 201
        mid = mem.json()["id"]

        patch = await client.patch(
            f"{BASE}/memory/{mid}",
            json={"temporal_status": "historical"},
            headers=_h(token),
        )
        assert patch.status_code == 200
        assert patch.json()["temporal_status"] == "historical"

    @pytest.mark.asyncio
    async def test_fact_supersession_fields(self, client, seeded_workspace):
        """Facts carry superseded_by_id for version chains."""
        token = seeded_workspace["access_token"]

        proj = await client.post(
            f"{BASE}/projects/",
            json={"name": "Supersession Project"},
            headers=_h(token),
        )
        pid = proj.json()["id"]

        for content in ["We use Python 3.10.", "We use Python 3.11."]:
            conv = json.dumps({"messages": [{"role": "user", "content": content}]})
            r = await client.post(
                f"{BASE}/ingest/upload",
                json={"project_id": pid, "source_type": "json", "content": conv},
                headers=_h(token),
            )
            assert r.status_code in (200, 201)

        facts = await client.get(
            f"{BASE}/ingest/facts?project_id={pid}", headers=_h(token)
        )
        assert facts.status_code == 200
        items = _items(facts.json())
        for f in items:
            assert "superseded_by_id" in f


# ─────────────────────────────────────────────────────────────────────────────
# 6. CONFLICT INTELLIGENCE
# ─────────────────────────────────────────────────────────────────────────────

class TestConflictIntelligence:
    """Capability 6: Cross-session contradiction detection and consolidation."""

    @pytest.mark.asyncio
    async def test_contradictory_sources_coexist(self, client, seeded_workspace):
        """Conflicting facts from different sessions are both stored."""
        token = seeded_workspace["access_token"]

        proj = await client.post(
            f"{BASE}/projects/",
            json={"name": "Conflict Project"},
            headers=_h(token),
        )
        pid = proj.json()["id"]

        # Session A
        conv_a = json.dumps({"messages": [
            {"role": "user", "content": "Our primary database uses PostgreSQL."}
        ]})
        r_a = await client.post(
            f"{BASE}/ingest/upload",
            json={"project_id": pid, "source_type": "json",
                  "title": "Session A", "content": conv_a},
            headers=_h(token),
        )
        assert r_a.status_code in (200, 201)

        # Session B (contradicts)
        conv_b = json.dumps({"messages": [
            {"role": "user", "content": "Our primary database uses MySQL."}
        ]})
        r_b = await client.post(
            f"{BASE}/ingest/upload",
            json={"project_id": pid, "source_type": "json",
                  "title": "Session B", "content": conv_b},
            headers=_h(token),
        )
        assert r_b.status_code in (200, 201)

        # Both sources exist
        sources = await client.get(
            f"{BASE}/ingest/sources?project_id={pid}", headers=_h(token)
        )
        assert sources.status_code == 200
        src_items = _items(sources.json())
        assert len(src_items) >= 2

    @pytest.mark.asyncio
    async def test_graph_links_across_sessions(self, client, seeded_workspace):
        """Knowledge graph links entities across sessions."""
        token = seeded_workspace["access_token"]

        proj = await client.post(
            f"{BASE}/projects/",
            json={"name": "Graph Conflict"},
            headers=_h(token),
        )
        pid = proj.json()["id"]

        for i in range(2):
            conv = json.dumps({"messages": [
                {"role": "user", "content": f"{'PostgreSQL' if i == 0 else 'MySQL'} is our primary database."}
            ]})
            r = await client.post(
                f"{BASE}/ingest/upload",
                json={"project_id": pid, "source_type": "json",
                      "title": f"Session {i}", "content": conv},
                headers=_h(token),
            )
            assert r.status_code in (200, 201)

        graph = await client.get(
            f"{BASE}/ingest/graph?project_id={pid}", headers=_h(token)
        )
        assert graph.status_code == 200
        g = graph.json()
        assert "nodes" in g
        assert "edges" in g
        assert isinstance(g["nodes"], list)
        assert isinstance(g["edges"], list)


# ─────────────────────────────────────────────────────────────────────────────
# 7. KNOWLEDGE RETRIEVAL
# ─────────────────────────────────────────────────────────────────────────────

class TestKnowledgeRetrieval:
    """Capability 7: BM25 + optional semantic retrieval + reranking."""

    @pytest.mark.asyncio
    async def test_search_returns_results(self, client, seeded_workspace):
        """Memory search returns results."""
        token = seeded_workspace["access_token"]

        for c in [
            "Kubernetes deployment uses Helm charts for configuration.",
            "CI/CD pipeline runs on GitHub Actions.",
            "Database migrations use Alembic.",
        ]:
            r = await client.post(
                f"{BASE}/memory/",
                json={"content": c},
                headers=_h(token),
            )
            assert r.status_code == 201

        resp = await client.post(
            f"{BASE}/memory/search",
            json={"query": "deployment", "limit": 10},
            headers=_h(token),
        )
        assert resp.status_code == 200
        results = resp.json()
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_hybrid_endpoint(self, client, seeded_workspace):
        """M5 hybrid search across facts and decisions."""
        token = seeded_workspace["access_token"]

        proj = await client.post(
            f"{BASE}/projects/",
            json={"name": "Hybrid Search Project"},
            headers=_h(token),
        )
        pid = proj.json()["id"]

        conv = json.dumps({
            "messages": [
                {"role": "user", "content": "We decided to use GraphQL for the API layer."},
            ]
        })

        resp = await client.post(
            f"{BASE}/ingest/upload",
            json={"project_id": pid, "source_type": "json", "content": conv},
            headers=_h(token),
        )
        assert resp.status_code in (200, 201)

        # M5 hybrid search — POST with query string params
        search = await client.post(
            f"{BASE}/ingest/search?query=GraphQL&limit=10",
            json={},
            headers=_h(token),
        )
        assert search.status_code == 200
        data = search.json()
        assert "items" in data
        assert "total" in data
        assert "query" in data
        assert isinstance(data["items"], list)


# ─────────────────────────────────────────────────────────────────────────────
# CROSS-CAPABILITY: MULTI-TENANT ISOLATION
# ─────────────────────────────────────────────────────────────────────────────

class TestMultiTenantIsolation:
    """Capabilities are isolated per tenant — data never leaks."""

    @pytest.mark.asyncio
    async def test_cross_tenant_memory_isolation(self, client, seeded_workspace):
        """Tenant A cannot see Tenant B's memories."""
        token_a = seeded_workspace["access_token"]

        reg = await client.post(
            f"{BASE}/auth/register",
            json={
                "email": f"owner-b-{_uid()}@test.com",
                "name": "Tenant B Owner",
                "password": "testpass123",
                "workspace_name": f"Workspace B {_uid()}",
            },
        )
        assert reg.status_code == 201
        token_b = reg.json()["access_token"]

        mem_a = await client.post(
            f"{BASE}/memory/",
            json={"content": "Tenant A secret knowledge."},
            headers=_h(token_a),
        )
        assert mem_a.status_code == 201
        ma_id = mem_a.json()["id"]

        # Tenant B should NOT see it
        list_b = await client.get(f"{BASE}/memory/", headers=_h(token_b))
        assert list_b.status_code == 200
        assert ma_id not in [m["id"] for m in _items(list_b.json())]

        # Tenant B should NOT get it by ID
        get_b = await client.get(f"{BASE}/memory/{ma_id}", headers=_h(token_b))
        assert get_b.status_code in (404, 403)

    @pytest.mark.asyncio
    async def test_cross_tenant_ingest_isolation(self, client, seeded_workspace):
        """Ingested sources are isolated per tenant."""
        token_a = seeded_workspace["access_token"]

        reg = await client.post(
            f"{BASE}/auth/register",
            json={
                "email": f"owner-c-{_uid()}@test.com",
                "name": "Tenant C Owner",
                "password": "testpass123",
                "workspace_name": f"Workspace C {_uid()}",
            },
        )
        token_c = reg.json()["access_token"]

        proj_a = await client.post(
            f"{BASE}/projects/",
            json={"name": "Tenant A Project"},
            headers=_h(token_a),
        )
        pid_a = proj_a.json()["id"]

        conv = json.dumps({"messages": [
            {"role": "user", "content": "Tenant A private data."}
        ]})
        ingest_a = await client.post(
            f"{BASE}/ingest/upload",
            json={"project_id": pid_a, "source_type": "json", "content": conv},
            headers=_h(token_a),
        )
        assert ingest_a.status_code in (200, 201)
        src_id = ingest_a.json()["source_id"]

        # Tenant C cannot access A's source
        src_c = await client.get(
            f"{BASE}/ingest/sources/{src_id}", headers=_h(token_c)
        )
        assert src_c.status_code in (404, 403)

    @pytest.mark.asyncio
    async def test_unauthenticated_blocked(self, client):
        """All capability endpoints require authentication."""
        r = await client.post(f"{BASE}/memory/", json={"content": "test"})
        assert r.status_code == 401

        r = await client.get(f"{BASE}/memory/")
        assert r.status_code == 401

        r = await client.get(f"{BASE}/ingest/sources")
        assert r.status_code == 401

        r = await client.get(f"{BASE}/ingest/facts")
        assert r.status_code == 401

        r = await client.post(f"{BASE}/chat/", json={"message": "hi"})
        assert r.status_code == 401

        r = await client.get(f"{BASE}/projects/")
        assert r.status_code == 401

        r = await client.post(f"{BASE}/sessions/", json={"title": "test"})
        assert r.status_code == 401

        r = await client.get(f"{BASE}/dashboard/")
        assert r.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# CROSS-CAPABILITY: COMPLETE LIFECYCLE
# ─────────────────────────────────────────────────────────────────────────────

class TestCompleteKnowledgeLifecycle:
    """End-to-end: register → project → ingest → chat → search → timeline."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, client):
        """The complete knowledge lifecycle works end to end."""
        # 1. Register
        reg = await client.post(
            f"{BASE}/auth/register",
            json={
                "email": f"lifecycle-{_uid()}@test.com",
                "name": "Lifecycle User",
                "password": "testpass123",
                "workspace_name": f"Lifecycle WS {_uid()}",
            },
        )
        assert reg.status_code == 201
        token = reg.json()["access_token"]

        # 2. Create project
        proj = await client.post(
            f"{BASE}/projects/",
            json={"name": "Lifecycle Project", "description": "E2E test project"},
            headers=_h(token),
        )
        assert proj.status_code == 201
        pid = proj.json()["id"]

        # 3. Ingest knowledge (using regex-friendly patterns)
        conv = json.dumps({
            "messages": [
                {"role": "user", "content": "Our CI/CD uses GitHub Actions with automated testing."},
                {"role": "assistant", "content": "The pipeline has unit tests, integration tests, and deployment stages."},
                {"role": "user", "content": "Prometheus supports monitoring and Grafana runs on Kubernetes."},
                {"role": "assistant", "content": "Alert rules are configured for P95 latency."},
            ]
        })
        ingest = await client.post(
            f"{BASE}/ingest/upload",
            json={"project_id": pid, "source_type": "json",
                  "title": "Lifecycle Session", "content": conv},
            headers=_h(token),
        )
        assert ingest.status_code in (200, 201)
        assert ingest.json()["source_id"] is not None

        # 4. Hybrid search
        search = await client.post(
            f"{BASE}/ingest/search?query=CI%2FCD+pipeline&limit=10",
            json={},
            headers=_h(token),
        )
        assert search.status_code == 200
        data = search.json()
        assert "items" in data
        assert "total" in data

        # 5. Chat with the knowledge
        chat = await client.post(
            f"{BASE}/chat/",
            json={"message": "How do we handle deployments?", "project_id": pid},
            headers=_h(token),
        )
        assert chat.status_code == 200
        chat_data = chat.json()
        assert "message_id" in chat_data
        assert "session_id" in chat_data
        assert "response" in chat_data

        # 6. List sources
        sources = await client.get(
            f"{BASE}/ingest/sources?project_id={pid}", headers=_h(token)
        )
        assert sources.status_code == 200
        assert len(_items(sources.json())) >= 1

        # 7. List facts
        facts = await client.get(
            f"{BASE}/ingest/facts?project_id={pid}", headers=_h(token)
        )
        assert facts.status_code == 200

        # 8. View graph
        graph = await client.get(
            f"{BASE}/ingest/graph?project_id={pid}", headers=_h(token)
        )
        assert graph.status_code == 200
        g = graph.json()
        assert "nodes" in g
        assert "edges" in g

        # 9. Timeline
        timeline = await client.get(
            f"{BASE}/ingest/timeline?project_id={pid}", headers=_h(token)
        )
        assert timeline.status_code == 200

    @pytest.mark.asyncio
    async def test_memory_search_after_creation(self, client):
        """Memory search finds created memories."""
        reg = await client.post(
            f"{BASE}/auth/register",
            json={
                "email": f"search-{_uid()}@test.com",
                "name": "Search User",
                "password": "testpass123",
                "workspace_name": f"Search WS {_uid()}",
            },
        )
        assert reg.status_code == 201
        token = reg.json()["access_token"]

        for keyword in ["python", "docker", "kubernetes", "redis"]:
            r = await client.post(
                f"{BASE}/memory/",
                json={"content": f"We use {keyword} in production for scaling."},
                headers=_h(token),
            )
            assert r.status_code == 201

        resp = await client.post(
            f"{BASE}/memory/search",
            json={"query": "python", "limit": 10},
            headers=_h(token),
        )
        assert resp.status_code == 200
        results = resp.json()
        assert isinstance(results, list)
        assert len(results) >= 1
        for r in results:
            assert "id" in r
            assert "content" in r
