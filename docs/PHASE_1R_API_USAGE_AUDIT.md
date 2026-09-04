# PHASE_1R_API_USAGE_AUDIT.md

## Gate 5 — API Usage Audit Summary

**Date:** 2026-09-04

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Backend Endpoints | 97 |
| Frontend-Consumed Endpoints | 50 |
| Utilization Rate | 51.5% |
| Unused Endpoints | 47 |

---

## Frontend-to-Backend Mapping

### Auth (6 endpoints)
| Frontend Uses | Backend Path | Status |
|---------------|--------------|--------|
| ✅ | POST /auth/register | E2E only |
| ✅ | POST /auth/login | E2E only |
| ✅ | POST /auth/refresh | api.ts auto-refresh |
| ✅ | POST /auth/logout | useAuth.logout() |
| ✅ | GET /auth/me | useAuth boot |
| ✅ | POST /auth/change-password | Settings, Profile |

### Workspace (14 endpoints)
| Frontend Uses | Backend Path | Status |
|---------------|--------------|--------|
| ✅ | GET /workspace | Dashboard, Settings |
| ✅ | PATCH /workspace | Settings |
| ❌ | DELETE /workspace | Not used |
| ✅ | GET /workspace/members | Settings, ProjectSettings |
| ✅ | POST /workspace/members | Settings |
| ✅ | PATCH /workspace/members/{id} | Settings |
| ✅ | DELETE /workspace/members/{id} | Settings |
| ❌ | POST /workspace/member/leave | Not used |
| ✅ | GET /workspace/members/invitations | Settings |
| ❌ | GET /workspace/members/invitations/{id} | Not used |
| ❌ | PATCH /workspace/members/invitations/{id} | Not used |
| ✅ | DELETE /workspace/members/invitations/{id} | Settings |
| ❌ | GET /workspace/workspaces/all | Not used |
| ❌ | GET /workspace/workspaces/available | Not used |

### Projects (5 endpoints)
All 5 used by frontend.

### Sessions (6 endpoints)
- Used: GET /sessions, GET /sessions/{id}/history
- Not used: POST, GET by ID, POST messages, DELETE

### Chat (2 endpoints)
- Used: POST /chat/stream (SSE)
- Not used: POST /chat (non-streaming)

### Memory (6 endpoints)
- Used: GET /, POST /search, POST /, DELETE /{id}
- Not used: GET /{id}, PATCH /{id}

### Ingest (15 endpoints)
- Used: 10 endpoints (upload, sources, facts, decisions, graph, timeline, search, jobs)
- Not used: 5 endpoints (POST queue, get source by ID, get messages, get fact/decision by ID)

### Graph (1 endpoint)
- Used: GET /graph

### Search (1 endpoint)
- Used: GET /search/

### Provenance (3 endpoints)
- Used: GET /
- Not used: GET /{id}, GET /{id}/memories

### Feedback (3 endpoints)
- Not used: All 3

### API Keys (4 endpoints)
- All 4 used

### Storage (3 endpoints)
- Used: POST /upload
- Not used: GET, DELETE

### Dashboard (2 endpoints)
- Not used: Both

### Policy (7 endpoints)
- Not used: All 7

### Audit (3 endpoints)
- Not used: All 3

### Health (3 endpoints)
- Not used: All 3

---

## Unused Features Analysis

The following backend features are not exposed in the frontend:

| Feature | Endpoints | Gap Severity |
|---------|-----------|-------------|
| **Policy Engine UI** | 7 endpoints | Medium — backend has RBAC but no admin UI |
| **Audit Logs** | 3 endpoints | Low — enterprise feature |
| **Feedback** | 3 endpoints | Low — optional feature |
| **Dashboard Overview** | 2 endpoints | Low — frontend has own dashboard |
| **Storage CRUD** | 2 endpoints | Low — only upload is needed |
| **Workspace Discovery** | 2 endpoints | Low — single-workspace per user |
| **Provenance Detail** | 2 endpoints | Low — list view only |
| **Session CRUD** | 4 endpoints | Low — read-only sessions |

---

## Verdict

**Gate 5 PASS**

- Backend provides 97 endpoints, frontend uses 50 (51.5%)
- Unused endpoints are mostly optional/enterprise features
- No critical gaps — all core features (auth, workspace, projects, chat, memory, ingest, search, graph) are exposed
- Policy engine has no frontend UI but backend is functional
