# PHASE_1R_API_CONTRACT_DIFF.md

## Phase 1R — API Contract Diff & Freeze

**Date:** 2026-09-04

---

## Contract Freeze Summary

This document records the full API surface agreement between the detachable frontend
and the FastAPI backend at baseline `0534efe426e42f9c03f1622dd792f052647038cc`.

---

## 1. Base URL

```
http://localhost:8000           (development)
{NEXT_PUBLIC_API_URL}           (production — frontend env var)
```

All paths prefixed with `/api/v1`.

---

## 2. Authentication

```
POST /api/v1/auth/register      — create user + workspace → TokenResponse
POST /api/v1/auth/login         — login → TokenResponse
POST /api/v1/auth/logout        — revoke refresh token
POST /api/v1/auth/refresh       — refresh access token → TokenResponse
GET  /api/v1/auth/me            — current user → UserOut
POST /api/v1/auth/change-password — change password
```

**Token format:** Bearer JWT in `Authorization` header.
**Storage:** `localStorage` key `sv_tokens` → `{access_token, refresh_token}`
**Auto-refresh:** Frontend intercepts 401 → calls `/refresh` → retries

---

## 3. Workspace

```
GET  /api/v1/workspace/                  — current workspace → WorkspaceOut
PATCH /api/v1/workspace/                 — update workspace → WorkspaceOut
GET  /api/v1/workspace/members           — list members → WorkspaceMemberOut[]
POST /api/v1/workspace/members           — invite member → WorkspaceMemberOut
PATCH /api/v1/workspace/members/{id}     — update member role → WorkspaceMemberOut
DELETE /api/v1/workspace/members/{id}    — remove member
GET  /api/v1/workspace/members/invitations — list invitations → InvitationOut[]
DELETE /api/v1/workspace/members/invitation/{id} — revoke invitation
```

---

## 4. Projects

```
GET  /api/v1/projects                    — list projects → ProjectOut[]
POST /api/v1/projects/                   — create project → ProjectOut
GET  /api/v1/projects/{id}               — get project → ProjectOut
PATCH /api/v1/projects/{id}              — update project → ProjectOut
DELETE /api/v1/projects/{id}             — delete project
```

---

## 5. Sessions

```
GET  /api/v1/sessions                    — list sessions → SessionOut[]
GET  /api/v1/sessions/{id}/history       — session with messages → SessionHistory
```

---

## 6. Chat

```
POST /api/v1/chat/stream                  — SSE chat stream
  Events: token, sources, done, error
```

**Request:**
```json
{ "message": "string", "session_id": "string?", "project_id": "string?" }
```

**SSE Events:**
```json
{"type": "token", "content": "chunk"}
{"type": "sources", "sources": [{ "memory_id": "...", "content": "...", "memory_type": "...", "score": 0.95 }]}
{"type": "done", "message_id": "...", "session_id": "...", "usage": {...}, "latency_ms": 123, "memory_grounded": true}
{"type": "error", "detail": "..."}
```

---

## 7. Memory

```
GET  /api/v1/memory/                     — list memory items → MemoryItemOut[]
                                                ?project_id=&limit=&offset=&memory_type=
POST /api/v1/memory/search               — semantic search → MemoryItemOut[]
POST /api/v1/memory/                     — create memory item → MemoryItemOut
DELETE /api/v1/memory/{id}               — delete memory item
```

---

## 8. Ingestion

```
POST /api/v1/ingest/upload               — upload conversation → IngestUploadResponse
                                                multipart or JSON body
GET  /api/v1/ingest/sources              — list sources → SourceListResponse
                                                ?project_id=&limit=
GET  /api/v1/ingest/facts                — list facts → FactListResponse
                                                ?project_id=
GET  /api/v1/ingest/decisions            — list decisions → DecisionListResponse
                                                ?project_id=
GET  /api/v1/ingest/graph                — knowledge graph → GraphResponse
                                                ?project_id=&include_historical=
GET  /api/v1/ingest/timeline             — timeline → TimelineResponse
                                                ?project_id=&limit=
POST /api/v1/ingest/search               — search → SearchResponse
GET  /api/v1/ingest/jobs                 — list ingest jobs → IngestJobOut[]
```

---

## 9. Search (legacy)

```
GET  /api/v1/search/                     — search → SearchResponse
                                                ?q=&limit=&project_id=
```

**Note:** Frontend uses both `/api/v1/ingest/search` (POST) and `/api/v1/search/` (GET).
These may return different data — contract should consolidate.

---

## 10. Graph (dedicated)

```
GET  /api/v1/graph                       — graph → GraphResponse
                                                ?project_id=
```

**Note:** Same shape as `/api/v1/ingest/graph`. Frontend uses the dedicted endpoint via `useGraph` hook.

---

## 11. Provenance

```
GET  /api/v1/provenance/                 — list provenance records → ProvenanceOut[]
                                                ?project_id=
GET  /api/v1/provenance/{id}             — single record → ProvenanceOut
GET  /api/v1/provenance/{id}/memories    — linked memories → MemoryReferenceOut[]
```

---

## 12. API Keys

```
POST /api/v1/api-keys                    — create key → ApiKeyCreateResponse (includes raw_key)
GET  /api/v1/api-keys                    — list keys → ApiKeyOut[]
DELETE /api/v1/api-keys/{id}             — revoke key
POST /api/v1/api-keys/{id}/rotate        — rotate key → ApiKeyRotateResponse (includes raw_key)
```

---

## 13. Feedback (not used by frontend)

```
POST /api/v1/feedback/                   — create feedback → FeedbackOut
GET  /api/v1/feedback/                   — list feedback → FeedbackListResponse
GET  /api/v1/feedback/{id}               — get feedback → FeedbackOut
```

---

## 14. Health

```
GET  /health/live                        — liveness probe
GET  /health/ready                       — readiness probe (checks DB)
GET  /health                             — combined health
```

---

## 15. Error Response Format

All errors return:
```json
{ "detail": "string" }
```

Or for validation errors:
```json
{ "detail": [{ "loc": ["body", "field"], "msg": "...", "type": "..." }] }
```

Frontend maps HTTP status codes to user-friendly messages in `src/lib/errors.ts`.

---

## 16. Type Contract Changes

**No breaking changes detected.** Frontend types in `src/types/api.ts` align with backend schemas.

**Known drift (non-breaking):**
- `FactItem` — frontend page uses local interface with different field names than shared type
- `useSSE` hook — exists but unused (chat uses inline fetch+ReadableStream)

---

## Contract Freeze

This contract is frozen. Any backend changes to the above paths, request/response shapes,
or status codes require:
1. Updating this document
2. Updating `frontend/src/types/api.ts`
3. Updating affected feature hooks
4. Re-running Gate 5-6 verification

**Frozen at:** 2026-09-04
**Backend baseline:** `0534efe426e42f9c03f1622dd792f052647038cc`
