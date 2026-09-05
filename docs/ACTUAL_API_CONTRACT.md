# ACTUAL_API_CONTRACT.md

## Phase 1R-B — API Contract Verification

**Date:** 2026-09-05
**Method:** Source-code audit of all `app/api/*.py` + `app/main.py`
**Baseline SHA:** `4aa908d5`

---

## Verification: Endpoint Count

**Claimed (Phase 1R):** 97
**Verified (this audit):** 81
**Delta:** -16 (inflated — counted from OpenAPI docs which included deprecated/duplicate entries)

### Counting Method

Counted `@router.get/post/patch/delete/put` decorators in each router file × prefix, plus `@app.get/post/...` in `main.py`.

| Router File | Prefix | GET | POST | PATCH | DELETE | Total |
|-------------|--------|-----|------|-------|--------|-------|
| auth.py | `/auth` | 1 | 4 | 0 | 0 | 6 |
| workspace.py | `/workspace` | 5 | 4 | 3 | 2 | 14 |
| projects.py | `/projects` | 2 | 1 | 1 | 1 | 5 |
| sessions.py | `/sessions` | 3 | 2 | 0 | 1 | 6 |
| chat.py | `/chat` | 0 | 2 | 0 | 0 | 2 |
| memory.py | `/memory` | 3 | 2 | 1 | 1 | 6 |
| ingest.py | `/ingest` | 7 | 2 | 0 | 0 | 14 |
| provenance.py | `/provenance` | 3 | 0 | 0 | 0 | 3 |
| dashboard.py | `/dashboard` | 2 | 0 | 0 | 0 | 2 |
| feedback.py | `/feedback` | 2 | 1 | 0 | 0 | 3 |
| api_keys.py | `/api-keys` | 1 | 2 | 0 | 1 | 4 |
| storage.py | `/storage` | 1 | 1 | 0 | 1 | 3 |
| policy.py | `/policy` | 4 | 3 | 1 | 1 | 7 |
| audit.py | `/audit` | 3 | 0 | 0 | 0 | 3 |
| **Sub-total** | | **37** | **28** | **5** | **7** | **78** |
| main.py (direct) | `/health` | 3 | 0 | 0 | 0 | 3 |
| **Grand Total** | | **40** | **28** | **5** | **7** | **81** |

No `add_api_route()` or dynamic registration exists beyond these 81 endpoints.

---

## Complete Endpoint Inventory

### Auth Router (`/api/v1/auth`)

| # | Method | Path | Handler | Auth | RBAC | Request | Response | Status Codes |
|---|--------|------|---------|------|------|---------|----------|--------------|
| 1 | POST | `/register` | `register` | None | None | `UserRegister` (email, password, name, workspace_name) | `TokenResponse` (access_token, refresh_token, token_type, expires_in) | 201, 400 |
| 2 | POST | `/login` | `login` | None | None | `UserLogin` (email, password) | `TokenResponse` | 200, 401 |
| 3 | POST | `/refresh` | `refresh` | None | None | `RefreshRequest` (refresh_token) | `TokenResponse` | 200, 401 |
| 4 | POST | `/logout` | `logout` | Token | None | `RefreshRequest` | `{"detail": "Logged out"}` | 200 |
| 5 | GET | `/me` | `get_me` | Token | None | — | `UserOut` | 200, 404 |
| 6 | POST | `/change-password` | `change_password` | Token | None | `ChangePasswordRequest` (current_password, new_password) | `{"detail": "Password updated"}` | 200, 400 |

### Workspace Router (`/api/v1/workspace`)

| # | Method | Path | Handler | Auth | RBAC | Request | Response | Status Codes |
|---|--------|------|---------|------|------|---------|----------|--------------|
| 7 | GET | `/` | `get_workspace` | Token | None | — | `WorkspaceOut` | 200, 404 |
| 8 | PATCH | `/` | `update_workspace` | Token | admin | `dict` (name, description, slug, perm_join, perm_member_manage) | `WorkspaceOut` | 200, 404 |
| 9 | DELETE | `/` | `delete_workspace` | Token | owner | — | None | 204, 404 |
| 10 | GET | `/members` | `list_members` | Token | None | — | `list[WorkspaceMemberOut]` | 200 |
| 11 | POST | `/members` | `invite_member` | Token | admin | `WorkspaceMemberInvite` (email, role, invitation_expires, message) | `WorkspaceMemberOut` | 201, 400 |
| 12 | PATCH | `/members/{member_id}` | `update_member` | Token | admin | `WorkspaceMemberUpdate` (role, expires) | `WorkspaceMemberOut` | 200, 404, 400 |
| 13 | DELETE | `/members/{user_id}` | `remove_member` | Token | admin | — | None | 204, 400, 404, 403 |
| 14 | POST | `/member/leave` | `leave_workspace` | Token | None | — | None | 204, 400, 404 |
| 15 | GET | `/members/invitations` | `list_invitations` | Token | member | — | `list[InvitationOut]` | 200 |
| 16 | GET | `/members/invitations/{state}` | `list_invitations_by_state` | Token | member | path: state | `list[InvitationOut]` | 200 |
| 17 | PATCH | `/members/invitation/{invitation_id}` | `update_invitation` | Token | admin | `InvitationUpdate` (state, role, expires) | `InvitationOut` | 200, 404 |
| 18 | DELETE | `/members/invitation/{invitation_id}` | `delete_invitation` | Token | admin | — | None | 204, 404 |
| 19 | GET | `/workspaces/all` | `list_all_workspaces` | Token | None | — | `list[dict]` (id, name, slug, role) | 200 |
| 20 | GET | `/workspaces/available` | `list_available_workspaces` | Token | None | — | `list[dict]` (id, name, slug) | 200 |

### Projects Router (`/api/v1/projects`)

| # | Method | Path | Handler | Auth | RBAC | Request | Response | Status Codes |
|---|--------|------|---------|------|------|---------|----------|--------------|
| 21 | GET | `/` | `list_projects` | Token | None | q: workspace-scoped | `list[ProjectOut]` | 200 |
| 22 | POST | `/` | `create_project` | Token | member | `ProjectCreate` (name, description) | `ProjectOut` | 201, 404 |
| 23 | GET | `/{project_id}` | `get_project` | Token | None | path: project_id | `ProjectOut` | 200, 404 |
| 24 | PATCH | `/{project_id}` | `update_project` | Token | member | `ProjectUpdate` (name, description) | `ProjectOut` | 200, 404 |
| 25 | DELETE | `/{project_id}` | `delete_project` | Token | admin | — | None | 204, 404 |

### Sessions Router (`/api/v1/sessions`)

| # | Method | Path | Handler | Auth | RBAC | Request | Response | Status Codes |
|---|--------|------|---------|------|------|---------|----------|--------------|
| 26 | GET | `/` | `list_sessions` | Token | None | — | `list[SessionOut]` | 200 |
| 27 | POST | `/` | `create_session` | Token | member | `SessionCreate` (title, extra_metadata) | `SessionOut` | 201 |
| 28 | GET | `/{session_id}` | `get_session` | Token | None | path: session_id | `SessionOut` | 200, 404 |
| 29 | GET | `/{session_id}/history` | `get_session_history` | Token | None | path: session_id | `{session_id, title, source, messages[]}` | 200, 404 |
| 30 | POST | `/{session_id}/messages` | `add_message` | Token | member | `MessageCreate` (role, content, metadata) | `MessageOut` | 201, 404 |
| 31 | DELETE | `/{session_id}` | `delete_session` | Token | None | — | None | 204, 404 |

### Chat Router (`/api/v1/chat`)

| # | Method | Path | Handler | Auth | RBAC | Request | Response | Status Codes |
|---|--------|------|---------|------|------|---------|----------|--------------|
| 32 | POST | `/` | `send_chat_message` | Token | viewer | `ChatRequest` (message, session_id?, project_id?) | `ChatResponse` (message_id, session_id, response, model, usage, memory_ids_used) | 200, 404 |
| 33 | POST | `/stream` | `stream_chat` | Token | None | `ChatRequest` (same as above) | SSE stream (text/event-stream): `token`, `sources`, `done`, `error` events | 200 |

**SSE Event Schema:**
```json
{"type": "token", "content": "..."}
{"type": "sources", "sources": [{"memory_id", "content", "memory_type", "score"}]}
{"type": "done", "message_id", "session_id", "usage", "memory_grounded", "latency_ms"}
{"type": "error", "detail": "..."}
```

### Memory Router (`/api/v1/memory`)

| # | Method | Path | Handler | Auth | RBAC | Request | Response | Status Codes |
|---|--------|------|---------|------|------|---------|----------|--------------|
| 34 | POST | `/` | `create_memory` | Token | policy:memory.write | `MemoryCreate` (memory_type, content, scope, agent_id?, run_id?, project_id?, extra_metadata?) | `MemoryOut` | 201 |
| 35 | GET | `/` | `list_memories` | Token | None | q: memory_type?, project_id?, temporal_status?, include_deleted?, limit(1-200), offset | `list[MemoryOut]` | 200 |
| 36 | GET | `/{memory_id}` | `get_memory` | Token | None | path: memory_id | `MemoryOut` | 200, 404 |
| 37 | PATCH | `/{memory_id}` | `update_memory` | Token | member | `MemoryUpdate` (content?, memory_type?, project_id?, temporal_status?) | `MemoryOut` | 200, 404 |
| 38 | DELETE | `/{memory_id}` | `delete_memory` | Token | owner + policy:memory.delete | — | None | 204, 404 |
| 39 | POST | `/search` | `search_memories` | Token | None | `MemorySearchRequest` (query, memory_type?, project_id?, limit?) | `list[MemoryOut]` | 200 |

### Ingest Router (`/api/v1/ingest`)

| # | Method | Path | Handler | Auth | RBAC | Request | Response | Status Codes |
|---|--------|------|---------|------|------|---------|----------|--------------|
| 40 | POST | `/upload` | `upload_and_ingest` | Token | member | `IngestUploadRequest` (project_id, source_type, content, title?, config?) — multipart or JSON | `IngestUploadResponse` (source_id, session_id, status, stage, message, messages_processed, facts_created, decisions_created, graph_nodes_created, graph_edges_created) | 201, 404 |
| 41 | POST | `/` | `legacy_start_ingest` | Token | None | `IngestQueued` (project_id, source_type, config) | `IngestJobOut` | 201, 404 |
| 42 | GET | `/sources` | `list_sources` | Token | None | q: project_id?, status?, limit(1-200), offset | `SourceListResponse` (items[], total) | 200 |
| 43 | GET | `/sources/{source_id}` | `get_source` | Token | None | path: source_id | `SourceDetail` (extends SourceOut + normalized_messages[]) | 200, 404 |
| 44 | GET | `/sources/{source_id}/messages` | `get_source_messages` | Token | None | path: source_id | `{items[], total}` | 200, 404 |
| 45 | GET | `/facts` | `list_facts` | Token | None | q: project_id?, subject?, temporal_status?, limit(1-200), offset | `FactListResponse` (items[], total) | 200 |
| 46 | GET | `/facts/{fact_id}` | `get_fact` | Token | None | path: fact_id | `FactOut` | 200, 404 |
| 47 | GET | `/decisions` | `list_decisions` | Token | None | q: project_id?, temporal_status?, limit(1-200), offset | `DecisionListResponse` (items[], total) | 200 |
| 48 | GET | `/decisions/{decision_id}` | `get_decision` | Token | None | path: decision_id | `DecisionOut` | 200, 404 |
| 49 | GET | `/graph` | `get_graph` | Token | None | q: project_id?, include_historical?(bool) | `GraphResponse` (nodes[], edges[]) | 200 |
| 50 | GET | `/timeline` | `get_timeline` | Token | None | q: project_id?, limit(1-200) | `TimelineResponse` (items[], total) | 200 |
| 51 | POST | `/search` | `search` | Token | None | q: query(min_length=1), limit(1-100) | `SearchResponse` (items[], total, query) | 200, 422 |
| 52 | GET | `/jobs` | `list_jobs` | Token | None | q: limit(1-200), offset | `{items[], total}` | 200 |
| 53 | GET | `/jobs/{job_id}` | `get_job` | Token | None | path: job_id | `{id, project_id, ...}` | 200, 404 |

### Provenance Router (`/api/v1/provenance`)

| # | Method | Path | Handler | Auth | RBAC | Request | Response | Status Codes |
|---|--------|------|---------|------|------|---------|----------|--------------|
| 54 | GET | `/` | `list_provenance` | Token | member | q: session_id?, project_id?, limit(1-200), offset | `list[ProvenanceOut]` | 200 |
| 55 | GET | `/{provenance_id}` | `get_provenance` | Token | None | path: provenance_id | `ProvenanceOut` | 200, 404 |
| 56 | GET | `/{provenance_id}/memories` | `get_provenance_memories` | Token | None | path: provenance_id | `list[MemoryReferenceOut]` | 200, 404 |

### Dashboard Router (`/api/v1/dashboard`)

| # | Method | Path | Handler | Auth | RBAC | Request | Response | Status Codes |
|---|--------|------|---------|------|------|---------|----------|--------------|
| 57 | GET | `/` | `workspace_overview` | Token | None | — | `DashboardOverview` (workspace_id, total_memories, total_sources, total_sessions, total_facts, total_decisions, total_graph_nodes, total_graph_edges, recent_memories, recent_sessions, memory_types) | 200 |
| 58 | GET | `/projects/{project_id}` | `project_dashboard` | Token | None | path: project_id | `ProjectDashboard` (project_id, project_name, total_memories, total_sources, total_facts, total_decisions, total_graph_nodes, total_feedback, memory_types) | 200, 404 |

### Feedback Router (`/api/v1/feedback`)

| # | Method | Path | Handler | Auth | RBAC | Request | Response | Status Codes |
|---|--------|------|---------|------|------|---------|----------|--------------|
| 59 | POST | `/` | `create_feedback` | Token | member | `FeedbackCreate` (provenance_id?, session_id?, rating, comment?) | `FeedbackOut` | 201 |
| 60 | GET | `/` | `list_feedback` | Token | None | q: session_id?, limit(1-200), offset | `FeedbackListResponse` (items[], total) | 200 |
| 61 | GET | `/{feedback_id}` | `get_feedback` | Token | None | path: feedback_id | `FeedbackOut` | 200, 404 |

### API Keys Router (`/api/v1/api-keys`)

| # | Method | Path | Handler | Auth | RBAC | Request | Response | Status Codes |
|---|--------|------|---------|------|------|---------|----------|--------------|
| 62 | POST | `/` | `create_api_key` | Token | admin | `ApiKeyCreate` (name, description?, expires_at?, metadata?) | `ApiKeyCreateResponse` (id, name, description, key_prefix, created_at, expires_at, key_extra, raw_key) | 201 |
| 63 | GET | `/` | `list_api_keys` | Token | None | — | `list[ApiKeyOut]` | 200 |
| 64 | DELETE | `/{key_id}` | `revoke_api_key` | Token | admin | — | None | 204, 404 |
| 65 | POST | `/{key_id}/rotate` | `rotate_api_key` | Token | admin | — | `ApiKeyRotateResponse` (id, name, key_prefix, raw_key, rotated_at) | 200, 404 |

### Storage Router (`/api/v1/storage`)

| # | Method | Path | Handler | Auth | RBAC | Request | Response | Status Codes |
|---|--------|------|---------|------|------|---------|----------|--------------|
| 66 | POST | `/upload` | `upload_file` | Token | member | multipart: file, project_id, source_type | `UploadResponse` (key, url, size, content_type, sha256) | 201, 413 |
| 67 | GET | `/{key:path}` | `get_file_info` | Token | None | path: key (must start with `{workspace_id}/`) | `{key, url}` | 200, 400, 404 |
| 68 | DELETE | `/{key:path}` | `delete_file` | Token | admin | path: key | None | 204, 400, 404 |

### Policy Router (`/api/v1/policy`)

| # | Method | Path | Handler | Auth | RBAC | Request | Response | Status Codes |
|---|--------|------|---------|------|------|---------|----------|--------------|
| 69 | GET | `/` | `list_policies` | Token | None | q: status_filter?, limit(1-200) | `list[PolicyOut]` | 200 |
| 70 | POST | `/` | `create_policy` | Token | admin | `PolicyCreate` (name, description?, rules[]) | `PolicyOut` | 201 |
| 71 | GET | `/{policy_id}` | `get_policy` | Token | None | path: policy_id | `PolicyDetail` (extends PolicyOut + versions[]) | 200, 404 |
| 72 | PATCH | `/{policy_id}` | `update_policy` | Token | None | `PolicyUpdate` (name?, description?, status?) | `PolicyOut` | 200, 404 |
| 73 | DELETE | `/{policy_id}` | `delete_policy` | Token | None | — | None | 204, 404 |
| 74 | POST | `/{policy_id}/versions` | `create_policy_version` | Token | None | `PolicyCreate` (name, description?, rules[]) | `PolicyVersionOut` (version, rules, status, created_at) | 201, 404 |
| 75 | POST | `/test-authorization` | `test_authorization` | Token | None | `AuthorizationTestRequest` (resource_type, resource_id?, action, principal_id?, principal_type?, context?, requested_limits?) | `AuthorizationTestResponse` (decision, reason, policy_id, policy_version, risk, request_id) | 200 |

### Audit Router (`/api/v1/audit`)

| # | Method | Path | Handler | Auth | RBAC | Request | Response | Status Codes |
|---|--------|------|---------|------|------|---------|----------|--------------|
| 76 | GET | `/events` | `list_audit_events` | Token | member | q: principal_id?, resource_type?, action?, event_type?, decision?, result_status?, from_time?, to_time?, limit(1-500), offset | `{items[], total, limit, offset}` | 200 |
| 77 | GET | `/events/{event_id}` | `get_audit_event` | Token | member | path: event_id (UUID) | `AuditEvent dict` | 200, 400, 403, 404 |
| 78 | GET | `/trace/{request_id}` | `correlation_trace` | Token | member | path: request_id | `{request_id, event_count, events[]}` | 200, 404 |

### Health Endpoints (direct, no `/api/v1`)

| # | Method | Path | Auth | Response | Status Codes |
|---|--------|------|------|----------|--------------|
| 79 | GET | `/health/live` | None | `{"status":"alive"}` | 200 |
| 80 | GET | `/health/ready` | None | `{"status":"ready","database":"connected"}` or 503 | 200, 503 |
| 81 | GET | `/health` | None | `{"status":"ok"}` | 200 |

---

## Authentication Summary

- **Unauthenticated:** `/health/*`, `/auth/register`, `/auth/login`
- **Token-required (no RBAC):** All `/api/v1/*` except health
- **RBAC-required:**
  - `admin`: workspace update, workspace members invite/update/remove, project create/update/delete, API key create/revoke/rotate, policy create
  - `member`: chat, memory create/update, ingest upload, session create, provenance list, feedback create, member leave, storage upload
  - `viewer`: chat/stream only

---

## Error Response Format

All errors return:
```json
{
  "error": {
    "type": "error_type",
    "message": "human readable message",
    "request_id": "uuid"  // optional, when available
  }
}
```

Validation errors (422):
```json
{
  "error": {
    "type": "validation_error",
    "message": "[{loc: [...], msg: "...", type: "..."}]"
  }
}
```

---

## CORS Configuration

```python
allow_origins = settings.cors_origins_safe  # localhost in dev, configured in prod
allow_credentials = True
allow_methods = ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
allow_headers = ["Authorization", "Content-Type", "X-Request-ID"]
max_age = 600
```

---

## Rate Limiting

- In-memory sliding window
- Default: 100 req/min per IP
- Bypass: `X-E2E: true` header in non-production
