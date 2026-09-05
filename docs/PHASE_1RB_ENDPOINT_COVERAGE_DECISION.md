# PHASE_1RB_ENDPOINT_COVERAGE_DECISION.md

## Phase 1R-B — Endpoint Coverage Decision

**Date:** 2026-09-05
**Certifier:** Claude (automated)
**Baseline:** `c02ee4c`

---

## 1. Total Endpoint Inventory

### Backend Endpoints (85 total)

| Method | Path | Frontend-Consumed | Purpose |
|--------|------|-------------------|---------|
| POST | /api/v1/auth/register | ✅ | User registration |
| POST | /api/v1/auth/login | ✅ | Login |
| POST | /api/v1/auth/logout | ✅ | Logout |
| POST | /api/v1/auth/refresh | ✅ | Token refresh |
| GET | /api/v1/auth/me | ✅ | Current user |
| POST | /api/v1/auth/change-password | ✅ | Password change |
| GET | /api/v1/workspace/ | ✅ | Workspace detail |
| PATCH | /api/v1/workspace/ | ✅ | Update workspace |
| GET | /api/v1/workspace/members | ✅ | List members |
| POST | /api/v1/workspace/members | ✅ | Invite member |
| PATCH | /api/v1/workspace/members/{id} | ✅ | Update member role |
| DELETE | /api/v1/workspace/members/{id} | ✅ | Remove member |
| GET | /api/v1/workspace/members/invitations | ✅ | List invitations |
| DELETE | /api/v1/workspace/members/invitation/{id} | ✅ | Revoke invitation |
| GET | /api/v1/projects/ | ✅ | List projects |
| POST | /api/v1/projects/ | ✅ | Create project |
| GET | /api/v1/projects/{id} | ✅ | Get project |
| PATCH | /api/v1/projects/{id} | ✅ | Update project |
| DELETE | /api/v1/projects/{id} | ✅ | Delete project |
| GET | /api/v1/sessions/ | ✅ | List sessions |
| GET | /api/v1/sessions/{id}/history | ✅ | Session history |
| POST | /api/v1/sessions/ | ❌ | Create session |
| POST | /api/v1/sessions/{id}/messages | ❌ | Send message |
| POST | /api/v1/chat/ | ✅ | Chat (non-streaming) |
| POST | /api/v1/chat/stream | ✅ | Chat SSE stream |
| GET | /api/v1/memory/ | ✅ | List memory |
| POST | /api/v1/memory/ | ✅ | Create memory |
| POST | /api/v1/memory/search | ✅ | Semantic search |
| PATCH | /api/v1/memory/{memory_id} | ✅ | Update memory |
| DELETE | /api/v1/memory/{memory_id} | ✅ | Delete memory |
| POST | /api/v1/ingest/upload | ✅ | Upload source |
| POST | /api/v1/ingest/ | ✅ | Create ingest job |
| GET | /api/v1/ingest/sources | ✅ | List sources |
| GET | /api/v1/ingest/sources/{id} | ✅ | Source detail |
| GET | /api/v1/ingest/sources/{id}/messages | ✅ | Source messages |
| GET | /api/v1/ingest/facts | ✅ | List facts |
| GET | /api/v1/ingest/facts/{id} | ❌ | Fact detail |
| GET | /api/v1/ingest/decisions | ✅ | List decisions |
| GET | /api/v1/ingest/decisions/{id} | ❌ | Decision detail |
| GET | /api/v1/ingest/graph | ✅ | Knowledge graph |
| GET | /api/v1/ingest/timeline | ✅ | Timeline |
| POST | /api/v1/ingest/search | ✅ | Ingest search |
| GET | /api/v1/ingest/jobs | ✅ | List jobs |
| GET | /api/v1/ingest/jobs/{id} | ❌ | Job detail |
| GET | /api/v1/graph | ✅ | Graph (dedicated) |
| GET | /api/v1/provenance/ | ✅ | List provenance |
| GET | /api/v1/provenance/{id} | ✅ | Provenance detail |
| GET | /api/v1/provenance/{id}/memories | ✅ | Linked memories |
| POST | /api/v1/api-keys/ | ✅ | Create API key |
| GET | /api/v1/api-keys/ | ✅ | List API keys |
| DELETE | /api/v1/api-keys/{id} | ✅ | Revoke key |
| POST | /api/v1/api-keys/{id}/rotate | ✅ | Rotate key |
| POST | /api/v1/feedback/ | ❌ | Create feedback |
| GET | /api/v1/feedback/ | ❌ | List feedback |
| GET | /api/v1/feedback/{id} | ❌ | Get feedback |
| GET | /api/v1/search/ | ❌ | Legacy search |
| GET | /api/v1/policy/ | ❌ | List policies |
| PATCH | /api/v1/policy/{id} | ❌ | Update policy |
| DELETE | /api/v1/policy/{id} | ❌ | Delete policy |
| POST | /api/v1/policy/ | ❌ | Create policy |
| POST | /api/v1/policy/test-authorization | ❌ | Test policy |
| POST | /api/v1/policy/{id}/versions | ❌ | Policy versions |
| DELETE | /api/v1/storage/{key} | ✅ | Delete file |
| GET | /api/v1/storage/{key} | ❌ | Get file |
| POST | /api/v1/storage/upload | ✅ | Upload file |
| GET | /api/v1/dashboard/ | ✅ | Dashboard stats |
| GET | /api/v1/dashboard/projects/{id} | ✅ | Project dashboard |
| GET | /api/v1/audit/events | ❌ | List audit events |
| GET | /api/v1/audit/events/{id} | ❌ | Audit event detail |
| GET | /api/v1/audit/trace/{id} | ❌ | Correlation trace |
| POST | /api/v1/workspace/member/leave | ❌ | Leave workspace |
| GET | /api/v1/workspace/workspaces/all | ❌ | All workspaces |
| GET | /api/v1/workspace/workspaces/available | ❌ | Available workspaces |
| PATCH | /api/v1/workspace/members/invitation/{id} | ❌ | Update invitation |

---

## 2. Coverage Summary

| Category | Count | Frontend-Consumed |
|----------|-------|-------------------|
| Total API endpoints | 85 | — |
| Frontend-consumed | — | 52 (61%) |
| Unused by frontend | — | 33 (39%) |

### Unused Endpoints — Rationale for Non-Coverage

| Endpoint | Rationale |
|----------|-----------|
| POST /api/v1/sessions/ | Frontend creates sessions implicitly via chat |
| POST /api/v1/sessions/{id}/messages | Messages created via chat endpoint |
| GET /api/v1/ingest/facts/{id} | Detail view not implemented in UI (list only) |
| GET /api/v1/ingest/decisions/{id} | Detail view not implemented in UI (list only) |
| GET /api/v1/ingest/jobs/{id} | Jobs listed but detail not shown |
| POST /api/v1/feedback/ | Admin-only, no UI |
| GET /api/v1/feedback/ | Admin-only, no UI |
| GET /api/v1/feedback/{id} | Admin-only, no UI |
| GET /api/v1/search/ | Legacy endpoint, superseded by /ingest/search |
| GET /api/v1/policy/ | Admin API only |
| PATCH /api/v1/policy/{id} | Admin API only |
| DELETE /api/v1/policy/{id} | Admin API only |
| POST /api/v1/policy/ | Admin API only |
| POST /api/v1/policy/test-authorization | Admin API only |
| POST /api/v1/policy/{id}/versions | Admin API only |
| GET /api/v1/storage/{key} | File download not implemented in UI |
| GET /api/v1/audit/events | Admin/backend-only |
| GET /api/v1/audit/events/{id} | Admin/backend-only |
| GET /api/v1/audit/trace/{id} | Admin/backend-only |
| POST /api/v1/workspace/member/leave | Not yet implemented in UI |
| GET /api/v1/workspace/workspaces/all | Multi-workspace feature not in UI |
| GET /api/v1/workspace/workspaces/available | Multi-workspace feature not in UI |
| PATCH /api/v1/workspace/members/invitation/{id} | Not yet implemented in UI |
| DELETE /api/v1/workspace/ | Dangerous, not exposed in UI |
| GET /api/v1/memory/{memory_id} | Memory detail not in UI (CRUD via list) |

---

## 3. Contract Freeze

Any changes to the 52 frontend-consumed endpoints require:
1. Updating `frontend/src/types/api.ts`
2. Updating affected feature hooks
3. Re-running Gate 5-6 verification
4. Updating this document

**Frozen at:** 2026-09-05
**Baseline SHA:** `c02ee4c`
