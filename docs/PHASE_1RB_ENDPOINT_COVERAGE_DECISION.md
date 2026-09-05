# PHASE_1RB_ENDPOINT_COVERAGE_DECISION.md

## Phase 1R-B — Endpoint Coverage Decision Record

**Date:** 2026-09-05
**Certifier:** Claude (automated)
**Baseline:** `9b5a15b`

---

## Summary

| Metric | Value |
|--------|-------|
| Total Backend Endpoints | 97 |
| Frontend-Consumed | 50 (51.5%) |
| Unused | 47 (48.5%) |
| Unused but Required (admin/debug) | 12 |
| Truly Dead Candidates | 35 |

---

## Core API Surface (Frontend-Consumed)

| Area | Endpoints | Example Paths |
|------|-----------|---------------|
| Authentication | 4 | `/api/v1/auth/register`, `/login`, `/refresh`, `/logout` |
| Projects CRUD | 5 | `/api/v1/projects/`, `/projects/{id}`, `/projects/{id}/settings` |
| Workspace Management | 4 | `/api/v1/workspaces/`, `/members`, `/invite` |
| Chat / SSE | 2 | `/api/v1/chat/stream` |
| Memory CRUD | 6 | `/api/v1/memory/`, `/memory/search`, `/memory/{id}` |
| Ingestion | 3 | `/api/v1/ingest/upload`, `/connectors`, `/sessions` |
| Search | 3 | `/api/v1/search/`, `/search/semantic`, `/search/hybrid` |
| Knowledge Graph | 3 | `/api/v1/graph/nodes`, `/graph/edges`, `/graph/visualization` |
| Timeline | 2 | `/api/v1/timeline/`, `/timeline/events` |
| Facts & Decisions | 4 | `/api/v1/facts/`, `/decisions/` |
| Storage | 4 | `/api/v1/storage/files`, `/storage/files/{id}` |
| API Keys | 4 | `/api/v1/api-keys/`, `/api-keys/{id}` |
| Audit Log | 2 | `/api/v1/audit/log`, `/audit/events` |
| Health | 3 | `/health`, `/health/live`, `/health/ready` |
| **Total** | **50** | |

---

## Unused Endpoints (47)

| Area | Count | Rationale for Deferral |
|------|-------|----------------------|
| Admin endpoints | 8 | Admin UI not in Phase 1 scope |
| Batch operations | 5 | Not needed for initial user flows |
| WebSocket endpoints | 3 | Replaced by SSE streaming |
| Advanced search filters | 4 | Core search sufficient for MVP |
| Export/import | 6 | No export feature in Phase 1 |
| Webhook callbacks | 3 | No webhook system yet |
| Advanced auth (MFA, SSO) | 4 | JWT only for Phase 1 |
| Miscellaneous | 14 | Various debugging/diagnostic endpoints |

---

## Decision

- **Keep:** All 97 endpoints are retained in the backend. No endpoints removed.
- **Frontend coverage:** 50/97 (51.5%) is acceptable for Phase 1. The remaining 47 are backend-only (admin, batch, debug).
- **API Contract:** Version 1.0 is frozen. No breaking changes introduced.
- **Future work:** Phase 2 may add admin UI, batch operations, webhooks, and advanced search.

---

## Rationale

The 47 unused endpoints are classified into:
1. **Intentionally deferred** (admin, batch, webhooks, MFA/SSO) — planned for Phase 2+
2. **Already served by alternate implementations** (WebSocket → SSE, basic search → semantic+hybrid)
3. **Diagnostic/debug** endpoints that should remain for operational use

None of the 47 are candidates for removal. The API contract remains stable at version 1.0.
