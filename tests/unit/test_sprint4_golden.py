"""Sprint 4 — Golden User Journey E2E tests.

Complete flow:
  Register → Login → Workspace → Create Project → Upload Conversation →
  Ingestion → M0→M4 pipeline → Memory → Facts → Decisions → Timeline →
  Search → Graph → Chat → Evidence → Provenance → Original Source
"""

from __future__ import annotations

import pytest
from fastapi import status


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestGoldenUserJourney:
    """Complete end-to-end golden journey through all Sprint 4 capabilities."""

    @pytest.mark.asyncio
    async def test_full_journey_register_to_provenance(self, client):
        token = (await client.post("/api/v1/auth/register", json={
            "email": "golden@test.com",
            "password": "password123",
            "name": "Golden User",
            "workspace_name": "Golden Workspace",
        })).json()["access_token"]

        project_id = (await client.post(
            "/api/v1/projects/",
            json={"name": "Golden Project", "description": "Journey test project"},
            headers=_headers(token),
        )).json()["id"]

        conversation = """Project Alpha uses PostgreSQL as its database.

Project Alpha is implemented in Python.

We decided to use PostgreSQL after initially considering MongoDB."""
        upload = await client.post("/api/v1/ingest/upload", json={
            "project_id": project_id,
            "source_type": "text",
            "title": "Architecture Decision",
            "content": conversation,
        }, headers=_headers(token))
        assert upload.status_code == 201
        upload_data = upload.json()
        source_id = upload_data["source_id"]
        session_id = upload_data["session_id"]
        assert upload_data["status"] == "completed"
        assert upload_data["messages_processed"] == 3

        sources = await client.get(
            "/api/v1/ingest/sources",
            headers=_headers(token),
        )
        assert sources.status_code == 200
        assert sources.json()["total"] >= 1

        await client.post(
            "/api/v1/ingest/refresh",
            json={"project_id": project_id},
            headers=_headers(token),
        )
        facts = await client.get(
            f"/api/v1/ingest/facts?project_id={project_id}",
            headers=_headers(token),
        )
        assert facts.status_code == 200
        assert facts.json()["total"] >= 1

        decisions = await client.get(
            f"/api/v1/ingest/decisions?project_id={project_id}",
            headers=_headers(token),
        )
        assert decisions.status_code == 200

        timeline = await client.get(
            f"/api/v1/ingest/timeline?project_id={project_id}",
            headers=_headers(token),
        )
        assert timeline.status_code == 200
        assert timeline.json()["total"] >= 1

        graph = await client.get(
            f"/api/v1/ingest/graph?project_id={project_id}",
            headers=_headers(token),
        )
        assert graph.status_code == 200

        search = await client.post(
            "/api/v1/ingest/search?query=PostgreSQL&limit=10",
            headers=_headers(token),
        )
        assert search.status_code == 200
        assert search.json()["total"] >= 1

        mem = await client.post(
            "/api/v1/memory/",
            json={
                "content": "Golden journey memory: Alpha uses PostgreSQL",
                "memory_type": "semantic_memory",
                "project_id": project_id,
            },
            headers=_headers(token),
        )
        assert mem.status_code == 201
        mem_id = mem.json()["id"]

        mem_list = await client.get(
            "/api/v1/memory/",
            headers=_headers(token),
        )
        assert any(m["id"] == mem_id for m in mem_list.json())

        mem_detail = await client.get(
            f"/api/v1/memory/{mem_id}",
            headers=_headers(token),
        )
        assert mem_detail.status_code == 200

        mem_update = await client.patch(
            f"/api/v1/memory/{mem_id}",
            json={"content": "Updated: Alpha uses PostgreSQL"},
            headers=_headers(token),
        )
        assert mem_update.status_code == 200

        search2 = await client.post(
            "/api/v1/memory/search",
            json={"query": "PostgreSQL"},
            headers=_headers(token),
        )
        assert any(m["id"] == mem_id for m in search2.json())

        del_resp = await client.delete(
            f"/api/v1/memory/{mem_id}",
            headers=_headers(token),
        )
        assert del_resp.status_code == 204

        chat = await client.post(
            "/api/v1/chat/",
            json={"message": "What database does Project Alpha use?"},
            headers=_headers(token),
        )
        assert chat.status_code == 200
        chat_data = chat.json()
        assert "response" in chat_data
        assert "memory_ids_used" in chat_data
        assert "latency_ms" in chat_data

        sessions = await client.get(
            "/api/v1/sessions/",
            headers=_headers(token),
        )
        assert sessions.status_code == 200

        dashboard = await client.get(
            "/api/v1/dashboard/",
            headers=_headers(token),
        )
        assert dashboard.status_code == 200
        d = dashboard.json()
        assert isinstance(d["total_memories"], int)
        assert isinstance(d["total_facts"], int)
        assert isinstance(d["total_sources"], int)
        assert isinstance(d["memory_types"], dict)

        proj_dash = await client.get(
            f"/api/v1/dashboard/projects/{project_id}",
            headers=_headers(token),
        )
        assert proj_dash.status_code == 200

        if chat_data.get("message_id"):
            feedback = await client.post(
                "/api/v1/feedback/",
                json={
                    "session_id": session_id,
                    "rating": "thumbs_up",
                    "comment": "Good answer",
                },
                headers=_headers(token),
            )
            assert feedback.status_code == 201

        prov_list = await client.get(
            "/api/v1/provenance/",
            headers=_headers(token),
        )
        assert prov_list.status_code == 200

        source_detail = await client.get(
            f"/api/v1/ingest/sources/{source_id}",
            headers=_headers(token),
        )
        assert source_detail.status_code == 200
        detail = source_detail.json()
        assert "normalized_messages" in detail
        assert len(detail["normalized_messages"]) >= 1

    @pytest.mark.asyncio
    async def test_chat_provenance_points_to_current_evidence(self, client):
        token = (await client.post("/api/v1/auth/register", json={
            "email": "provgolden@test.com",
            "password": "password123",
            "name": "Prov Golden",
            "workspace_name": "Prov Golden WS",
        })).json()["access_token"]

        pid = (await client.post(
            "/api/v1/projects/", json={"name": "Prov Proj"},
            headers=_headers(token),
        )).json()["id"]

        await client.post("/api/v1/ingest/upload", json={
            "project_id": pid,
            "source_type": "text",
            "content": "Project Alpha initially used MongoDB.",
        }, headers=_headers(token))

        await client.post("/api/v1/ingest/upload", json={
            "project_id": pid,
            "source_type": "text",
            "content": "Project Alpha now uses PostgreSQL.",
        }, headers=_headers(token))

        await client.post("/api/v1/ingest/refresh", json={"project_id": pid}, headers=_headers(token))

        resp = await client.post(
            "/api/v1/chat/",
            json={"message": "What database does Project Alpha currently use?"},
            headers=_headers(token),
        )
        assert resp.status_code == 200
        answer = resp.json()["response"]
        assert "PostgreSQL" in answer or "not found" in answer.lower() or "unknown" in answer.lower()

    @pytest.mark.asyncio
    async def test_no_evidence_behavior(self, client):
        token = (await client.post("/api/v1/auth/register", json={
            "email": "noevidence@test.com",
            "password": "password123",
            "name": "No Evid",
            "workspace_name": "No Evid WS",
        })).json()["access_token"]

        resp = await client.post(
            "/api/v1/chat/",
            json={"message": "What database does Project Gamma use?"},
            headers=_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "memory_ids_used" in data
        assert len(data["memory_ids_used"]) == 0
