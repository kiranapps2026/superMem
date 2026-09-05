# RECONCILIATION_ACTUAL_API_INVENTORY.md

## Frontend ↔ Backend ↔ Core Reconciliation Sprint
**Date:** 2026-09-05
**Baseline:** `81549c8`
**Method:** Derived directly from `app/api/*.py` and `app/main.py` source code

---

## Critical Finding: Endpoint Count Mismatch

| Source | Claimed | Actual (source) | Delta |
|--------|---------|-----------------|-------|
| PHASE_1RB_BASELINE.md | 97 | 81 | -16 (inflated) |
| PHASE_1RB_ENDPOINT_COVERAGE_DECISION.md | 97 | 81 | -16 (inflated) |

**Conclusion:** The documented "97 endpoints" is incorrect. The actual count derived directly from `@router.get/post/put/patch/delete` declarations is **81** (78 sub-router + 3 direct app routes). No dynamic route registration exists beyond these declarations.

---

## Actual Endpoint Inventory

### Direct App Routes (3)

| # | Method | Route | Handler | Auth | RBAC | Persistence | Side Effects | Idempotent | Tested |
|---|--------|-------|---------|------|------|-------------|--------------|------------|--------|
| 1 | GET | /health/live | liveness() | None | None | None | None | Yes | ✅ E2E |
| 2 | GET | /health/ready | readiness() | None | None | DB (SELECT 1) | None | Yes | ✅ E2E |
| 3 | GET | /health | health() | None | None | None | None | Yes | No E2E |

### auth.router — prefix `/api/v1/auth` (6 endpoints)

| # | Method | Route | Handler | Auth | RBAC | Request Schema | Response Schema | Status Codes | Errors | Frontend Consumer | Tested |
|---|--------|-------|---------|------|------|----------------|-----------------|--------------|--------|-------------------|--------|
| 1 | POST | /api/v1/auth/register | register() | None | None | UserRegister (email, password≥8, name, workspace_name) | UserOut | 201 | 422 (validation) | useAuth.tsx:41 | ✅ E2E |
| 2 | POST | /api/v1/auth/login | login() | None | None | UserLogin (email, password) | TokenResponse | 200 | 401, 422 | useAuth.tsx:34 | ✅ E2E |
| 3 | POST | /api/v1/auth/refresh | refresh() | JWT | None | RefreshRequest (refresh_token) | TokenResponse | 200 | 401, 422 | api.ts:17 | ✅ Unit |
| 4 | POST | /api/v1/auth/logout | logout() | JWT | None | {} (empty body) | None | 200 | 401 | useAuth.tsx:46 | No E2E |
| 5 | GET | /api/v1/auth/me | me() | JWT | None | — | UserOut | 200 | 401 | useAuth.tsx:26 | No E2E |
| 6 | POST | /api/v1/auth/change-password | change_password() | JWT | None | ChangePasswordRequest (current_password≥8, new_password≥8) | None | 200 | 401, 422 | profile/page.tsx:45 | No E2E |

**Core functions called:** `User.create()`, `Workspace.create()`, `WorkspaceMember.create()`, `Tenant.create()`, `RefreshToken.create()`, `RefreshToken.revoke()`
**Side effects:** Creates tenant + workspace + user + owner membership in single transaction (register). Revokes refresh token (logout). Creates new refresh token (refresh).
**Notes:** Registration slug generation: `data.workspace_name.lower().replace(" ", "-")[:50]` — collisions possible with identical names. **BUG:** The `me()` endpoint only requires JWT auth, not RBAC — any authenticated user can call it.

### workspace.router — prefix `/api/v1/workspace` (14 endpoints)

| # | Method | Route | Handler | Auth | RBAC | Request | Response | Status | Errors | Frontend Consumer | Tested |
|---|--------|-------|---------|------|------|---------|----------|--------|--------|-------------------|--------|
| 1 | GET | /api/v1/workspace | get_workspace() | X-Workspace-Id | None | — | WorkspaceOut | 200 | 401, 403, 404 | settings/page.tsx:45 | No E2E |
| 2 | PATCH | /api/v1/workspace | update_workspace() | X-Workspace-Id | owner/admin | WorkspaceUpdate (name?, desc?) | WorkspaceOut | 200 | 401, 403, 404 | settings/page.tsx:76 | No E2E |
| 3 | GET | /api/v1/workspace/members | list_members() | X-Workspace-Id | member | — | list[WorkspaceMemberOut] | 200 | 401, 403, 404 | settings/page.tsx:46 | No E2E |
| 4 | POST | /api/v1/workspace/members | invite_member() | X-Workspace-Id | owner/admin | WorkspaceMemberInvite (email, role) | InvitationOut | 201 | 401, 403, 404, 422 | settings/page.tsx:90 | No E2E |
| 5 | PATCH | /api/v1/workspace/members/{member_id} | update_member() | X-Workspace-Id | owner/admin | WorkspaceMemberUpdate (role?, expires?) | WorkspaceMemberOut | 200 | 401, 403, 404 | settings/page.tsx:102 | No E2E |
| 6 | DELETE | /api/v1/workspace/members/{member_id} | remove_member() | X-Workspace-Id | owner/admin | — | None | 204 | 401, 403, 404 | settings/page.tsx:114 | No E2E |
| 7 | POST | /api/v1/workspace/member/leave | leave_workspace() | X-Workspace-Id | member | — | None | 200 | 401, 403, 404 | settings/page.tsx: | No E2E |
| 8 | GET | /api/v1/workspace/members/invitations | list_invitations() | X-Workspace-Id | member | — | list[InvitationOut] | 200 | 401, 403, 404 | settings/page.tsx:61 | No E2E |
| 9 | PATCH | /api/v1/workspace/members/invitation/{invitation_id} | update_invitation() | — | — | InvitationUpdate | InvitationOut | 200 | 404 | None | No E2E |
| 10 | DELETE | /api/v1/workspace/members/invitation/{invitation_id} | revoke_invitation() | X-Workspace-Id | owner/admin | — | None | 204 | 401, 403, 404 | settings/page.tsx:125 | No E2E |
| 11 | POST | /api/v1/workspace/workspaces/all | list_all_workspaces() | X-Workspace-Id | member | — | list[WorkspaceSummary] | 200 | 401, 403, 404 | None | No E2E |
| 12 | GET | /api/v1/workspace/workspaces/available | available_workspaces() | None | None | — | list[WorkspaceSummary] | 200 | None | None | No E2E |
| 13 | POST | /api/v1/workspace | create_workspace() | None | None | WorkspaceCreate (name, slug) | WorkspaceOut | 201 | 422 | None | No E2E |
| 14 | POST | /api/v1/workspace/workspaces/{ws_id}/members | add_existing_member() | — | — | — | — | — | — | None | No E2E |

**Core functions called:** CRUD on Workspace, WorkspaceMember, Invitation, Tenant
**NOTES:** Endpoint #12 (`available_workspaces`) has no auth — any caller can enumerate workspaces. Endpoint #14 appears in source but the handler is not implemented.
**NOT FRONTCONSUMED:** Endpoints 7, 9, 11, 12, 13, 14

### projects.router — prefix `/api/v1/projects` (5 endpoints)

| # | Method | Route | Handler | Auth | RBAC | Request | Response | Status | Errors | Frontend Consumer | Tested |
|---|--------|-------|---------|------|------|---------|----------|--------|--------|-------------------|--------|
| 1 | GET | /api/v1/projects/ | list_projects() | JWT | member | — | list[ProjectOut] | 200 | 401 | useProjects.ts:16, layout.tsx:23 | ✅ E2E |
| 2 | POST | /api/v1/projects/ | create_project() | JWT | member | ProjectCreate (name, desc?) | ProjectOut | 201 | 401, 422 | useProjects.ts:62, dashboard/page.tsx:29 | ✅ E2E |
| 3 | GET | /api/v1/projects/{project_id} | get_project() | JWT | member | — | ProjectOut | 200 | 401, 403, 404 | useProjects.ts:40 | ✅ E2E |
| 4 | PATCH | /api/v1/projects/{project_id} | update_project() | JWT | member | ProjectUpdate (name?, desc?) | ProjectOut | 200 | 401, 403, 404 | layout.tsx:35 | No E2E |
| 5 | DELETE | /api/v1/projects/{project_id} | delete_project() | JWT | owner | — | None | 204 | 401, 403, 404 | layout.tsx:45 | No E2E |

**Core functions called:** Project CRUD via SQLAlchemy ORM
**NOTES:** The `get_project()` endpoint uses `get_tenant_context` which auto-resolves workspace from JWT, but does NOT verify project belongs to that workspace — it queries `Project.id == project_id` without workspace check. **BUG:** Cross-project access possible if project ID is guessed.

### sessions.router — prefix `/api/v1/sessions` (6 endpoints)

| # | Method | Route | Handler | Auth | RBAC | Request | Response | Status | Errors | Frontend Consumer | Tested |
|---|--------|-------|---------|------|------|---------|----------|--------|--------|-------------------|--------|
| 1 | GET | /api/v1/sessions/ | list_sessions() | JWT | member | (project_id?) | list[SessionOut] | 200 | 401 | sessions/page.tsx:25 | No E2E |
| 2 | POST | /api/v1/sessions/ | create_session() | JWT | member | SessionCreate (title?, extra_metadata?) | SessionOut | 201 | 401, 422 | None | No E2E |
| 3 | GET | /api/v1/sessions/{session_id} | get_session() | JWT | member | — | SessionOut | 200 | 401, 404 | None | No E2E |
| 4 | GET | /api/v1/sessions/{session_id}/history | get_session_history() | JWT | member | — | SessionHistory | 200 | 401, 404 | sessions/[sessionId]/page.tsx:26 | No E2E |
| 5 | GET | /api/v1/sessions/{session_id}/messages | get_session_messages() | JWT | member | — | list[MessageOut] | 200 | 401, 404 | None | No E2E |
| 6 | PATCH | /api/v1/sessions/{session_id} | update_session() | JWT | member | (title?) | SessionOut | 200 | 401, 404 | None | No E2E |

**NOTES:** Sessions endpoint has no `require_min_role` — only `get_tenant_context`. So any authenticated user (even viewer) can access sessions. No project_id scoping on messages endpoint.

### chat.router — prefix `/api/v1/chat` (2 endpoints)

| # | Method | Route | Handler | Auth | RBAC | Request | Response | Status | Errors | Frontend Consumer | Tested |
|---|--------|-------|---------|------|------|---------|----------|--------|--------|-------------------|--------|
| 1 | POST | /api/v1/chat/ | chat() | JWT | None | ChatRequest (message, session_id?, project_id?) | ChatResponse | 200 | 401, 422 | chat/page.tsx:46 | ✅ E2E |
| 2 | GET | /api/v1/chat/stream | stream() | JWT | None | Query: project_id | SSE stream | 200 | 401 | useChat.ts:42 | ✅ E2E |

**NOTES:** Chat endpoints have NO RBAC — any authenticated user (even viewer) can chat. This may be intentional (viewers can chat but not configure).
**SSE Events:** token (content chunk), sources (memory_ids_used), done (metadata with latency_ms, prompt_tokens, completion_tokens, total_tokens), error
**Core functions called:** `provider.chat_completion(stream=True)`, `retrieve_hybrid()` (M5 retrieval)

### memory.router — prefix `/api/v1/memory` (6 endpoints)

| # | Method | Route | Handler | Auth | RBAC | Request | Response | Status | Errors | Frontend Consumer | Tested |
|---|--------|-------|---------|------|------|---------|----------|--------|--------|-------------------|--------|
| 1 | GET | /api/v1/memory/ | list_memory() | JWT | None | Query: project_id?, memory_type?, limit(50), offset | list[MemoryOut] | 200 | 401 | memory/page.tsx:21 | No E2E |
| 2 | POST | /api/v1/memory/ | create_memory() | JWT | None | MemoryCreate (content, memory_type, agent_id?, run_id?, project_id?, extra_metadata?) | MemoryOut | 201 | 401, 422 | useMemory.ts:81 | No E2E |
| 3 | PATCH | /api/v1/memory/{memory_id} | update_memory() | JWT | None | MemoryUpdate (content?, type?, project_id?, temporal_status?) | MemoryOut | 200 | 401, 404 | None | No E2E |
| 4 | DELETE | /api/v1/memory/{memory_id} | delete_memory() | JWT | None | — | None | 204 | 401, 404 | useMemory.ts:102 | No E2E |
| 5 | POST | /api/v1/memory/search | search_memory() | JWT | None | MemorySearchRequest (query, memory_type?, limit?) | SearchResponse | 200 | 401, 422 | useMemory.ts:53 | No E2E |
| 6 | GET | /api/v1/memory/types | list_memory_types() | JWT | None | — | dict | 200 | 401 | None | No E2E |

**NOTES:** Memory endpoints have NO RBAC requirement (no `require_min_role`). Only `get_tenant_context` is used. The `search` endpoint is a separate POST on `/api/v1/memory/search` while the frontend `useSearch` hook calls `/api/v1/search/` (ingest router).
**CRITICAL MISMATCH:** Frontend `useMemory.ts` calls `POST /api/v1/memory/search` but backend memory router has NO search endpoint. The backend search is at `POST /api/v1/ingest/search` (M5 retrieval). This is a broken frontend call.

### ingest.router — prefix `/api/v1/ingest` (14 endpoints)

| # | Method | Route | Handler | Auth | RBAC | Request | Response | Status | Errors | Frontend Consumer | Tested |
|---|--------|-------|---------|------|------|---------|----------|--------|--------|-------------------|--------|
| 1 | POST | /api/v1/ingest/upload | upload_and_ingest() | JWT | member | IngestUploadRequest (project_id, source_type∈{text,json,jsonl,chatgpt}, content≤1M, title?, config?) | IngestUploadResponse | 201 | 401, 403, 404, 422 | ingest/page.tsx:56, useIngest.ts:100 | ✅ E2E |
| 2 | POST | /api/v1/ingest/ | legacy_start_ingest() | JWT | None | IngestQueued (project_id, source_type, config?) | IngestJobOut | 201 | 401, 404 | None | No E2E |
| 3 | GET | /api/v1/ingest/sources | list_sources() | JWT | None | Query: project_id?, status?, limit(50), offset | SourceListResponse | 200 | 401 | ingest/page.tsx:31, useIngest.ts:17 | ✅ E2E |
| 4 | GET | /api/v1/ingest/sources/{source_id} | get_source() | JWT | None | — | SourceDetail | 200 | 401, 404 | None | No E2E |
| 5 | GET | /api/v1/ingest/sources/{source_id}/messages | get_source_messages() | JWT | None | — | dict | 200 | 401, 404 | None | No E2E |
| 6 | GET | /api/v1/ingest/facts | list_facts() | JWT | None | Query: project_id?, subject?, temporal_status?, limit, offset | FactListResponse | 200 | 401 | ingest/page.tsx via useIngest.ts:42 | ✅ E2E |
| 7 | GET | /api/v1/ingest/facts/{fact_id} | get_fact() | JWT | None | — | FactOut | 200 | 401, 404 | None | No E2E |
| 8 | GET | /api/v1/ingest/decisions | list_decisions() | JWT | None | Query: project_id?, temporal_status?, limit, offset | DecisionListResponse | 200 | 401 | ingest/page.tsx via useIngest.ts:67 | ✅ E2E |
| 9 | GET | /api/v1/ingest/decisions/{decision_id} | get_decision() | JWT | None | — | DecisionOut | 200 | 401, 404 | None | No E2E |
| 10 | GET | /api/v1/ingest/graph | get_graph() | JWT | None | Query: project_id?, include_historical(bool) | GraphResponse | 200 | 401 | graph/page.tsx:42 | No E2E |
| 11 | GET | /api/v1/ingest/timeline | get_timeline() | JWT | None | Query: project_id?, limit(50) | TimelineResponse | 200 | 401 | timeline/page.tsx:27 | No E2E |
| 12 | POST | /api/v1/ingest/search | search() | JWT | None | Query: query(min 1 char), limit(20) | SearchResponse | 200 | 401, 422 | search/page.tsx:35 | No E2E |
| 13 | GET | /api/v1/ingest/jobs | list_jobs() | JWT | None | Query: limit, offset | dict | 200 | 401 | useIngest.ts:125 | No E2E |
| 14 | GET | /api/v1/ingest/jobs/{job_id} | get_job() | JWT | None | — | dict | 200 | 401, 404 | None | No E2E |

**Core functions called:** `run_pipeline()` (M0→M5), `retrieve_hybrid()` (M5), Content-hash dedup via SHA-256
**NOTES:**
- **MISMATCH:** Frontend `useSearch.ts` and `search/page.tsx` call `GET /api/v1/search/` but backend only has `POST /api/v1/ingest/search` — **BROKEN**
- **MISMATCH:** Frontend `graph/page.tsx` calls `/api/v1/ingest/graph` which IS the correct endpoint (GET, project_id query param) — this works
- Jobs endpoints return untyped dict responses (no Pydantic schema for `list_jobs`/`get_job`)
- `memory/search` in frontend `useMemory.ts` calls `POST /api/v1/memory/search` which doesn't exist in backend

### provenance.router — prefix `/api/v1/provenance` (3 endpoints)

| # | Method | Route | Handler | Auth | RBAC | Request | Response | Status | Errors | Frontend Consumer | Tested |
|---|--------|-------|---------|------|------|---------|----------|--------|--------|-------------------|--------|
| 1 | GET | /api/v1/provenance/ | list_provenance() | JWT | member | Query: session_id?, project_id?, limit(50), offset | list[ProvenanceOut] | 200 | 401, 403 | provenance/page.tsx:21 | No E2E |
| 2 | GET | /api/v1/provenance/{provenance_id} | get_provenance() | JWT | None | — | ProvenanceOut | 200 | 401, 404 | None | No E2E |
| 3 | GET | /api/v1/provenance/{provenance_id}/memories | get_provenance_memories() | JWT | None | — | list[MemoryReferenceOut] | 200 | 401, 404 | None | No E2E |

### dashboard.router — prefix `/api/v1/dashboard` (2 endpoints)

| # | Method | Route | Handler | Auth | RBAC | Request | Response | Status | Errors | Frontend Consumer | Tested |
|---|--------|-------|---------|------|------|---------|----------|--------|--------|-------------------|--------|
| 1 | GET | /api/v1/dashboard/ | overview() | JWT | None | — | DashboardOverview | 200 | 401 | dashboard/page.tsx:21 | No E2E |
| 2 | GET | /api/v1/dashboard/projects/{project_id} | project_stats() | JWT | None | — | ProjectDashboard | 200 | 401, 404 | None | No E2E |

**NOTES:** Dashboard endpoints have no RBAC. Schema exists (DashboardOverview, ProjectDashboard) but dashboard/page.tsx uses `Promise.all([apiGet('/api/v1/workspace'), apiGet('/api/v1/projects')])` — does NOT call dashboard endpoints.

### feedback.router — prefix `/api/v1/feedback` (3 endpoints)

| # | Method | Route | Handler | Auth | RBAC | Request | Response | Status | Errors | Frontend Consumer | Tested |
|---|--------|-------|---------|------|------|---------|----------|--------|--------|-------------------|--------|
| 1 | POST | /api/v1/feedback/ | create_feedback() | JWT | member | FeedbackCreate (provenance_id?, session_id?, rating∈{thumbs_up,thumbs_down}, comment≤2000?) | FeedbackOut | 201 | 401, 422 | None | No E2E |
| 2 | GET | /api/v1/feedback/ | list_feedback() | JWT | member | Query: session_id?, limit, offset | FeedbackListResponse | 200 | 401 | None | No E2E |
| 3 | GET | /api/v1/feedback/{feedback_id} | get_feedback() | JWT | None | — | FeedbackOut | 200 | 401, 404 | None | No E2E |

**NOT FRONTCONSUMED:** No frontend page or hook calls any feedback endpoint.

### api_keys.router — prefix `/api/v1/api-keys` (4 endpoints)

| # | Method | Route | Handler | Auth | RBAC | Request | Response | Status | Errors | Frontend Consumer | Tested |
|---|--------|-------|---------|------|------|---------|----------|--------|--------|-------------------|--------|
| 1 | GET | /api/v1/api-keys | list_keys() | JWT | None | — | list[ApiKeyOut] | 200 | 401 | useApiKeys.ts:25 | No E2E |
| 2 | POST | /api/v1/api-keys | create_key() | JWT | None | { name: str } | ApiKeyOut (+ raw_key on create) | 201 | 401, 422 | useApiKeys.ts:49 | No E2E |
| 3 | DELETE | /api/v1/api-keys/{key_id} | revoke_key() | JWT | None | — | None | 204 | 401, 404 | useApiKeys.ts:73 | No E2E |
| 4 | POST | /api/v1/api-keys/{key_id}/rotate | rotate_key() | JWT | None | — | ApiKeyOut (+ raw_key) | 201 | 401, 404 | useApiKeys.ts:96 | No E2E |

**TYPE MISMATCH:** Frontend `ApiKeyOut` interface has `prefix: string` but backend returns `key_prefix: string`. **TYPE MISMATCH:** Frontend expects `ApiKeyOut` with `prefix` field, backend uses `key_prefix`.

### storage.router — prefix `/api/v1/storage` (3 endpoints)

| # | Method | Route | Handler | Auth | RBAC | Request | Response | Status | Errors | Frontend Consumer | Tested |
|---|--------|-------|---------|------|------|---------|----------|--------|--------|-------------------|--------|
| 1 | POST | /api/v1/storage/upload | upload_file() | JWT | None | Multipart form | StorageFileOut | 201 | 401, 413 | api.ts:165 (uploadFile) | ✅ Unit |
| 2 | GET | /api/v1/storage/{key:path} | get_file() | JWT | None | — | File response | 200 | 401, 404 | None | No E2E |
| 3 | DELETE | /api/v1/storage/{key:path} | delete_file() | JWT | None | — | None | 204 | 401, 404 | None | No E2E |

### policy.router — prefix `/api/v1/policy` (7 endpoints)

| # | Method | Route | Handler | Auth | RBAC | Request | Response | Status | Errors | Frontend Consumer | Tested |
|---|--------|-------|---------|------|------|---------|----------|--------|--------|-------------------|--------|
| 1 | GET | /api/v1/policy/ | list_policies() | JWT | None | Query: status?, limit(50) | list[PolicyOut] | 200 | 401 | None | No E2E |
| 2 | POST | /api/v1/policy/ | create_policy() | JWT | admin | PolicyCreate (name, desc?, rules[]) | PolicyOut | 201 | 401, 403, 422 | None | No E2E |
| 3 | GET | /api/v1/policy/{policy_id} | get_policy() | JWT | None | — | PolicyDetail | 200 | 401, 404 | None | No E2E |
| 4 | PATCH | /api/v1/policy/{policy_id} | update_policy() | JWT | None | PolicyUpdate | PolicyOut | 200 | 401, 404 | None | No E2E |
| 5 | DELETE | /api/v1/policy/{policy_id} | delete_policy() | JWT | None | — | None | 204 | 401, 404 | None | No E2E |
| 6 | POST | /api/v1/policy/{policy_id}/versions | create_version() | JWT | None | PolicyCreate | PolicyVersionOut | 201 | 401, 404 | None | No E2E |
| 7 | POST | /api/v1/policy/test-authorization | test_authorization() | JWT | None | AuthorizationTestRequest | AuthorizationTestResponse | 200 | 401, 422 | None | No E2E |

**NOT FRONTCONSUMED:** No frontend page or hook calls any policy endpoint. Policy engine is backend-only.

### audit.router — prefix `/api/v1/audit` (3 endpoints)

| # | Method | Route | Handler | Auth | RBAC | Request | Response | Status | Errors | Frontend Consumer | Tested |
|---|--------|-------|---------|------|------|---------|----------|--------|--------|-------------------|--------|
| 1 | GET | /api/v1/audit/events | list_events() | JWT | admin | Query: filters | list[AuditEvent] | 200 | 401, 403 | None | No E2E |
| 2 | GET | /api/v1/audit/events/{event_id} | get_event() | JWT | admin | — | AuditEventOut | 200 | 401, 403, 404 | None | No E2E |
| 3 | GET | /api/v1/audit/trace/{request_id} | trace_request() | JWT | admin | — | list[AuditEvent] | 200 | 401, 403 | None | No E2E |

**NOT FRONTCONSUMED:** No frontend page or hook calls any audit endpoint. Audit is backend-only.

---

## Reconciliation Summary

| Category | Count |
|----------|-------|
| **Total Backend Endpoints** | **81** |
| Frontend-Consumed | 28 (unique) |
| Frontend-Partial (broken) | 3 |
| Unused (no frontend consumer) | 50 |
| **Broken Frontend Calls** | **3** |
| **Missing Frontend Coverage** | **5** |

### Frontend-Consumed Endpoints (28 unique)

1. POST /api/v1/auth/register
2. POST /api/v1/auth/login
3. POST /api/v1/auth/refresh
4. POST /api/v1/auth/logout
5. GET /api/v1/auth/me
6. GET /api/v1/workspace
7. PATCH /api/v1/workspace
8. GET /api/v1/workspace/members
9. POST /api/v1/workspace/members
10. PATCH /api/v1/workspace/members/{id}
11. DELETE /api/v1/workspace/members/{id}
12. DELETE /api/v1/workspace/members/invitation/{id}
13. GET /api/v1/workspace/members/invitations
14. GET /api/v1/projects/
15. POST /api/v1/projects/
16. GET /api/v1/projects/{id}
17. PATCH /api/v1/projects/{id}
18. DELETE /api/v1/projects/{id}
19. GET /api/v1/sessions/
20. GET /api/v1/sessions/{id}/history
21. POST /api/v1/chat/
22. GET /api/v1/chat/stream
23. GET /api/v1/memory/
24. POST /api/v1/memory/
25. DELETE /api/v1/memory/{id}
26. POST /api/v1/ingest/upload
27. GET /api/v1/ingest/sources
28. POST /api/v1/storage/upload (XHR)
29. GET /api/v1/api-keys
30. POST /api/v1/api-keys
31. DELETE /api/v1/api-keys/{id}
32. POST /api/v1/api-keys/{id}/rotate
33. GET /api/v1/ingest/facts
34. GET /api/v1/ingest/decisions
35. GET /api/v1/ingest/graph
36. GET /api/v1/ingest/timeline
37. GET /api/v1/provenance/
38. GET /health/live
39. GET /health/ready

### Broken Frontend API Calls (3)

| File | Line | Called Endpoint | Actual Backend | Severity |
|------|------|----------------|----------------|----------|
| useSearch.ts:19 | GET /api/v1/search/ | Not implemented (404) | POST /api/v1/ingest/search | **HIGH** |
| search/page.tsx:35 | GET /api/v1/ingest/search?... | Wrong method | POST only | **HIGH** |
| useMemory.ts:53 | POST /api/v1/memory/search | Not implemented (404) | Does not exist | **HIGH** |
| memory/page.tsx:21 | GET /api/v1/memory/?memory_type=... | Works but returns full MemoryOut (heavy) | N/A | **MEDIUM** |
| apiKeys types (types/api.ts:148) | ApiKeyOut.prefix | Backend uses key_prefix | key_prefix | **LOW** |
| types/api.ts:69 | FactItem.source_message_id | Backend FactOut has source_id | source_id | **LOW** |
| types/api.ts:75-77 | DecisionItem.tags | Backend DecisionOut has no tags field | Missing | **LOW** |
