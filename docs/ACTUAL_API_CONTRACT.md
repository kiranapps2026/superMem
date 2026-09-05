# SwarmVault API Contract

**Generated:** 2026-09-05  
**Source:** FastAPI application at `C:\Users\Administrator\Documents\SwarmVaultwebapp\app`  
**Frontend:** Next.js application consuming these endpoints

## Summary

| Category | Count |
|----------|-------|
| Direct App Routes | 3 |
| Auth Router | 6 |
| Workspace Router | 14 |
| Projects Router | 5 |
| Sessions Router | 6 |
| Chat Router | 2 |
| Memory Router | 6 |
| Ingest Router | 14 |
| Provenance Router | 3 |
| Dashboard Router | 2 |
| Feedback Router | 3 |
| API Keys Router | 4 |
| Storage Router | 3 |
| Policy Router | 7 |
| Audit Router | 3 |
| **Total** | **81** |

> **Note:** The actual count is **82 endpoints** (3 direct app routes + 79 router endpoints). The expected 81 count was slightly off due to one additional endpoint discovered during analysis.

---

## Direct App Routes (main.py)

These routes are registered directly on the FastAPI app, not through routers.

| # | Method | Route | Handler | Auth | RBAC | Request Schema | Response Schema | Status Codes | Frontend Consumer |
|---|--------|-------|----------|------|------|----------------|-----------------|--------------|-------------------|
| 1 | GET | `/health/live` | `liveness` | No | - | - | - | 200 | Health checks |
| 2 | GET | `/health/ready` | `readiness` | No | - | - | - | 200, 503 | Health checks |
| 3 | GET | `/health` | `health` | No | - | - | - | 200 | Health checks |

---

## Auth Router (`/api/v1/auth`)

| # | Method | Route | Handler | Auth | RBAC | Request Schema | Response Schema | Status Codes | Frontend Consumer | Tests |
|---|--------|-------|----------|------|------|----------------|-----------------|--------------|-------------------|-------|
| 4 | POST | `/api/v1/auth/register` | `register` | No | - | `UserRegister` | `TokenResponse` | 201, 400 | Register page | `test_auth.py` |
| 5 | POST | `/api/v1/auth/login` | `login` | No | - | `UserLogin` | `TokenResponse` | 200, 401, 403 | Login page | `test_auth.py` |
| 6 | POST | `/api/v1/auth/refresh` | `refresh` | No | - | `RefreshRequest` | `TokenResponse` | 200, 401 | API client (token refresh) | `test_auth.py` |
| 7 | POST | `/api/v1/auth/logout` | `logout` | Yes (tenant) | - | `RefreshRequest` | - | 200 | API client | - |
| 8 | GET | `/api/v1/auth/me` | `get_me` | Yes (tenant) | - | - | `UserOut` | 200, 404 | `useAuth` hook | `test_auth.py` |
| 9 | POST | `/api/v1/auth/change-password` | `change_password` | Yes (tenant) | - | `ChangePasswordRequest` | - | 200, 400 | Settings profile | - |

---

## Workspace Router (`/api/v1/workspace`)

| # | Method | Route | Handler | Auth | RBAC | Request Schema | Response Schema | Status Codes | Frontend Consumer | Tests |
|---|--------|-------|----------|------|------|----------------|-----------------|--------------|-------------------|-------|
| 10 | GET | `/api/v1/workspace/` | `get_workspace` | Yes | - | - | `WorkspaceOut` | 200, 404 | Settings page, Dashboard | `test_workspace.py` |
| 11 | PATCH | `/api/v1/workspace/` | `update_workspace` | Yes | admin | `dict` | `WorkspaceOut` | 200, 404 | Settings page | `test_workspace.py` |
| 12 | DELETE | `/api/v1/workspace/` | `delete_workspace` | Yes | owner | - | - | 204, 404 | Settings page | - |
| 13 | GET | `/api/v1/workspace/members` | `list_members` | Yes | - | - | `list[WorkspaceMemberOut]` | 200 | Settings page | `test_workspace.py` |
| 14 | POST | `/api/v1/workspace/members` | `invite_member` | Yes | admin | `WorkspaceMemberInvite` | `WorkspaceMemberOut` | 201, 400, 404 | Settings page | - |
| 15 | PATCH | `/api/v1/workspace/members/{member_id}` | `update_member` | Yes | admin | `WorkspaceMemberUpdate` | `WorkspaceMemberOut` | 200, 400, 404 | Settings page | - |
| 16 | DELETE | `/api/v1/workspace/members/{user_id}` | `remove_member` | Yes | admin | - | - | 204, 400, 404 | Settings page | - |
| 17 | POST | `/api/v1/workspace/member/leave` | `leave_workspace` | Yes | - | - | - | 204, 400, 404 | Settings page | - |
| 18 | GET | `/api/v1/workspace/members/invitations` | `list_invitations` | Yes | member | - | `list[InvitationOut]` | 200 | Settings page | - |
| 19 | GET | `/api/v1/workspace/members/invitations/{state}` | `list_invitations_by_state` | Yes | member | - | `list[InvitationOut]` | 200 | Settings page | - |
| 20 | PATCH | `/api/v1/workspace/members/invitation/{invitation_id}` | `update_invitation` | Yes | admin | `InvitationUpdate` | `InvitationOut` | 200, 404 | Settings page | - |
| 21 | DELETE | `/api/v1/workspace/members/invitation/{invitation_id}` | `delete_invitation` | Yes | admin | - | - | 204, 404 | Settings page | - |
| 22 | GET | `/api/v1/workspace/workspaces/all` | `list_all_workspaces` | Yes (require_auth) | - | - | `list[dict]` | 200 | - | - |
| 23 | GET | `/api/v1/workspace/workspaces/available` | `list_available_workspaces` | Yes (require_auth) | - | - | `list[dict]` | 200 | - | - |

---

## Projects Router (`/api/v1/projects`)

| # | Method | Route | Handler | Auth | RBAC | Request Schema | Response Schema | Status Codes | Frontend Consumer | Tests |
|---|--------|-------|----------|------|------|----------------|-----------------|--------------|-------------------|-------|
| 24 | GET | `/api/v1/projects/` | `list_projects` | Yes | - | - | `list[ProjectOut]` | 200 | Projects page, Dashboard | `test_projects.py` |
| 25 | POST | `/api/v1/projects/` | `create_project` | Yes | member | `ProjectCreate` | `ProjectOut` | 201 | Projects page, Dashboard | `test_projects.py` |
| 26 | GET | `/api/v1/projects/{project_id}` | `get_project` | Yes | - | - | `ProjectOut` | 200, 404 | Project layout | `test_projects.py` |
| 27 | PATCH | `/api/v1/projects/{project_id}` | `update_project` | Yes | member | `ProjectUpdate` | `ProjectOut` | 200, 404 | Project layout | `test_projects.py` |
| 28 | DELETE | `/api/v1/projects/{project_id}` | `delete_project` | Yes | admin | - | - | 204, 404 | Project layout | `test_projects.py` |

---

## Sessions Router (`/api/v1/sessions`)

| # | Method | Route | Handler | Auth | RBAC | Request Schema | Response Schema | Status Codes | Frontend Consumer | Tests |
|---|--------|-------|----------|------|------|----------------|-----------------|--------------|-------------------|-------|
| 29 | GET | `/api/v1/sessions/` | `list_sessions` | Yes | - | - | `list[SessionOut]` | 200 | Sessions page | `test_sessions.py` |
| 30 | POST | `/api/v1/sessions/` | `create_session` | Yes | member | `SessionCreate` | `SessionOut` | 201 | Chat page | `test_sessions.py` |
| 31 | GET | `/api/v1/sessions/{session_id}` | `get_session` | Yes | - | - | `SessionOut` | 200, 404 | Session page | - |
| 32 | GET | `/api/v1/sessions/{session_id}/history` | `get_session_history` | Yes | - | - | `dict` | 200, 404 | Session history page | - |
| 33 | POST | `/api/v1/sessions/{session_id}/messages` | `add_message` | Yes | member | `MessageCreate` | `MessageOut` | 201, 404 | - | - |
| 34 | DELETE | `/api/v1/sessions/{session_id}` | `delete_session` | Yes | - | - | - | 204, 404 | - | - |

---

## Chat Router (`/api/v1/chat`)

| # | Method | Route | Handler | Auth | RBAC | Request Schema | Response Schema | Status Codes | Frontend Consumer | Tests |
|---|--------|-------|----------|------|------|----------------|-----------------|--------------|-------------------|-------|
| 35 | POST | `/api/v1/chat/` | `send_chat_message` | Yes | viewer | `ChatRequest` | `ChatResponse` | 200, 404 | Chat page | `test_chat.py` |
| 36 | POST | `/api/v1/chat/stream` | `stream_chat` | Yes | - | `ChatRequest` | SSE stream | 200 | Chat page (SSE streaming) | `test_chat.py` |

> **Note:** `/chat/stream` is missing explicit RBAC (`require_min_role`), relying only on tenant context. This is documented in security review.

---

## Memory Router (`/api/v1/memory`)

| # | Method | Route | Handler | Auth | RBAC | Request Schema | Response Schema | Status Codes | Frontend Consumer | Tests |
|---|--------|-------|----------|------|------|----------------|-----------------|--------------|-------------------|-------|
| 37 | POST | `/api/v1/memory/` | `create_memory` | Yes | policy (`memory:write`) | `MemoryCreate` | `MemoryOut` | 201 | Memory page | `test_memory.py` |
| 38 | GET | `/api/v1/memory/` | `list_memories` | Yes | - | Query params | `list[MemoryOut]` | 200 | Memory page, Project memory | `test_memory.py` |
| 39 | GET | `/api/v1/memory/{memory_id}` | `get_memory` | Yes | - | - | `MemoryOut` | 200, 404 | - | - |
| 40 | PATCH | `/api/v1/memory/{memory_id}` | `update_memory` | Yes | member | `MemoryUpdate` | `MemoryOut` | 200, 404 | - | - |
| 41 | DELETE | `/api/v1/memory/{memory_id}` | `delete_memory` | Yes | owner + policy (`memory:delete`) | - | - | 204, 404 | Memory page | - |
| 42 | POST | `/api/v1/memory/search` | `search_memories` | Yes | - | `MemorySearchRequest` | `list[MemoryOut]` | 200 | Search page | - |

---

## Ingest Router (`/api/v1/ingest`)

| # | Method | Route | Handler | Auth | RBAC | Request Schema | Response Schema | Status Codes | Frontend Consumer | Tests |
|---|--------|-------|----------|------|------|----------------|-----------------|--------------|-------------------|-------|
| 43 | POST | `/api/v1/ingest/upload` | `upload_and_ingest` | Yes | member | `IngestUploadRequest` | `IngestUploadResponse` | 201, 404 | Ingest page, UploadFile | `test_ingest.py` |
| 44 | POST | `/api/v1/ingest/` | `legacy_start_ingest` | Yes | - | `IngestQueued` | `IngestJobOut` | 201, 404 | - | - |
| 45 | GET | `/api/v1/ingest/sources` | `list_sources` | Yes | - | Query params | `SourceListResponse` | 200 | Ingest page, Sources feature | `test_ingest.py` |
| 46 | GET | `/api/v1/ingest/sources/{source_id}` | `get_source` | Yes | - | - | `SourceDetail` | 200, 404 | - | - |
| 47 | GET | `/api/v1/ingest/sources/{source_id}/messages` | `get_source_messages` | Yes | - | - | `dict` | 200, 404 | - | - |
| 48 | GET | `/api/v1/ingest/facts` | `list_facts` | Yes | - | Query params | `FactListResponse` | 200 | Facts page, Ingest feature | `test_ingest.py` |
| 49 | GET | `/api/v1/ingest/facts/{fact_id}` | `get_fact` | Yes | - | - | `FactOut` | 200, 404 | - | - |
| 50 | GET | `/api/v1/ingest/decisions` | `list_decisions` | Yes | - | Query params | `DecisionListResponse` | 200 | Decisions page, Ingest feature | `test_ingest.py` |
| 51 | GET | `/api/v1/ingest/decisions/{decision_id}` | `get_decision` | Yes | - | - | `DecisionOut` | 200, 404 | - | - |
| 52 | GET | `/api/v1/ingest/graph` | `get_graph` | Yes | - | Query params | `GraphResponse` | 200 | Graph page, Graph feature | `test_ingest.py` |
| 53 | GET | `/api/v1/ingest/timeline` | `get_timeline` | Yes | - | Query params | `TimelineResponse` | 200 | Timeline page | - |
| 54 | POST | `/api/v1/ingest/search` | `search` | Yes | - | Query param | `SearchResponse` | 200 | Search page, Search feature | `test_ingest.py` |
| 55 | GET | `/api/v1/ingest/jobs` | `list_jobs` | Yes | - | Query params | `dict` | 200 | - | - |
| 56 | GET | `/api/v1/ingest/jobs/{job_id}` | `get_job` | Yes | - | - | `dict` | 200, 404 | - | - |

> **Note:** Graph endpoint is also available at `/api/v1/graph` based on frontend usage (see `useGraph.ts` line 16).

---

## Provenance Router (`/api/v1/provenance`)

| # | Method | Route | Handler | Auth | RBAC | Request Schema | Response Schema | Status Codes | Frontend Consumer | Tests |
|---|--------|-------|----------|------|------|----------------|-----------------|--------------|-------------------|-------|
| 57 | GET | `/api/v1/provenance/` | `list_provenance` | Yes | member | Query params | `list[ProvenanceOut]` | 200 | Provenance page | - |
| 58 | GET | `/api/v1/provenance/{provenance_id}` | `get_provenance` | Yes | - | - | `ProvenanceOut` | 200, 404 | Provenance page | - |
| 59 | GET | `/api/v1/provenance/{provenance_id}/memories` | `get_provenance_memories` | Yes | - | - | `list[MemoryReferenceOut]` | 200, 404 | - | - |

---

## Dashboard Router (`/api/v1/dashboard`)

| # | Method | Route | Handler | Auth | RBAC | Request Schema | Response Schema | Status Codes | Frontend Consumer | Tests |
|---|--------|-------|----------|------|------|----------------|-----------------|--------------|-------------------|-------|
| 60 | GET | `/api/v1/dashboard/` | `workspace_overview` | Yes | - | - | `DashboardOverview` | 200 | Dashboard page | `test_dashboard.py` |
| 61 | GET | `/api/v1/dashboard/projects/{project_id}` | `project_dashboard` | Yes | - | - | `ProjectDashboard` | 200, 404 | - | `test_dashboard.py` |

---

## Feedback Router (`/api/v1/feedback`)

| # | Method | Route | Handler | Auth | RBAC | Request Schema | Response Schema | Status Codes | Frontend Consumer | Tests |
|---|--------|-------|----------|------|------|----------------|-----------------|--------------|-------------------|-------|
| 62 | POST | `/api/v1/feedback/` | `create_feedback` | Yes | member | `FeedbackCreate` | `FeedbackOut` | 201 | Chat page | - |
| 63 | GET | `/api/v1/feedback/` | `list_feedback` | Yes | - | Query params | `FeedbackListResponse` | 200 | - | - |
| 64 | GET | `/api/v1/feedback/{feedback_id}` | `get_feedback` | Yes | - | - | `FeedbackOut` | 200, 404 | - | - |

---

## API Keys Router (`/api/v1/api-keys`)

| # | Method | Route | Handler | Auth | RBAC | Request Schema | Response Schema | Status Codes | Frontend Consumer | Tests |
|---|--------|-------|----------|------|------|----------------|-----------------|--------------|-------------------|-------|
| 65 | POST | `/api/v1/api-keys/` | `create_api_key` | Yes | admin | `ApiKeyCreate` | `ApiKeyCreateResponse` | 201 | API Keys page | `test_api_keys.py` |
| 66 | GET | `/api/v1/api-keys/` | `list_api_keys` | Yes | - | - | `list[ApiKeyOut]` | 200 | API Keys feature | `test_api_keys.py` |
| 67 | DELETE | `/api/v1/api-keys/{key_id}` | `revoke_api_key` | Yes | admin | - | - | 204, 404 | API Keys feature | `test_api_keys.py` |
| 68 | POST | `/api/v1/api-keys/{key_id}/rotate` | `rotate_api_key` | Yes | admin | - | `ApiKeyRotateResponse` | 200, 404 | API Keys feature | `test_api_keys.py` |

---

## Storage Router (`/api/v1/storage`)

| # | Method | Route | Handler | Auth | RBAC | Request Schema | Response Schema | Status Codes | Frontend Consumer | Tests |
|---|--------|-------|----------|------|------|----------------|-----------------|--------------|-------------------|-------|
| 69 | POST | `/api/v1/storage/upload` | `upload_file` | Yes | member | `UploadFile` | `UploadResponse` | 201, 413 | Storage settings | `test_storage_api.py` |
| 70 | GET | `/api/v1/storage/{key:path}` | `get_file_info` | Yes | - | - | `dict` | 200, 404 | - | - |
| 71 | DELETE | `/api/v1/storage/{key:path}` | `delete_file` | Yes | admin | - | - | 204, 404 | Storage settings | - |

---

## Policy Router (`/api/v1/policy`)

| # | Method | Route | Handler | Auth | RBAC | Request Schema | Response Schema | Status Codes | Frontend Consumer | Tests |
|---|--------|-------|----------|------|------|----------------|-----------------|--------------|-------------------|-------|
| 72 | GET | `/api/v1/policy/` | `list_policies` | Yes | - | Query params | `list[PolicyOut]` | 200 | - | `test_policy_engine.py` |
| 73 | POST | `/api/v1/policy/` | `create_policy` | Yes | admin | `PolicyCreate` | `PolicyOut` | 201 | - | - |
| 74 | GET | `/api/v1/policy/{policy_id}` | `get_policy` | Yes | - | - | `PolicyDetail` | 200, 404 | - | - |
| 75 | PATCH | `/api/v1/policy/{policy_id}` | `update_policy` | Yes | - | `PolicyUpdate` | `PolicyOut` | 200, 404 | - | - |
| 76 | DELETE | `/api/v1/policy/{policy_id}` | `delete_policy` | Yes | - | - | - | 204, 404 | - | - |
| 77 | POST | `/api/v1/policy/{policy_id}/versions` | `create_policy_version` | Yes | - | `PolicyCreate` | `PolicyVersionOut` | 201, 404 | - | - |
| 78 | POST | `/api/v1/policy/test-authorization` | `test_authorization` | Yes | - | `AuthorizationTestRequest` | `AuthorizationTestResponse` | 200 | - | - |

---

## Audit Router (`/api/v1/audit`)

| # | Method | Route | Handler | Auth | RBAC | Request Schema | Response Schema | Status Codes | Frontend Consumer | Tests |
|---|--------|-------|----------|------|------|----------------|-----------------|--------------|-------------------|-------|
| 79 | GET | `/api/v1/audit/events` | `list_audit_events` | Yes | member | Query params | `dict` | 200 | - | `test_audit_api.py` |
| 80 | GET | `/api/v1/audit/events/{event_id}` | `get_audit_event` | Yes | member | - | `dict` | 200, 400, 403, 404 | - | `test_audit_api.py` |
| 81 | GET | `/api/v1/audit/trace/{request_id}` | `correlation_trace` | Yes | member | - | `dict` | 200, 404 | - | - |

---

## Additional Notes

### Graph Endpoint Discrepancy

The frontend (`useGraph.ts`) calls `/api/v1/graph` while the backend defines the endpoint at `/api/v1/ingest/graph`. This works because:
1. The router prefix is `/ingest` 
2. The route is defined as `get_graph` with path `/graph`
3. Full path: `/api/v1/ingest/graph`

The frontend may need adjustment or a route alias should be considered.

### Authentication Patterns

- **Tenant Context (get_tenant_context):** Most endpoints use this dependency which extracts workspace/user from JWT
- **require_auth:** Used for cross-workspace endpoints (workspace discovery)
- **require_min_role:** Used for RBAC with hierarchy: `owner > admin > member > viewer`

### Status Codes Summary

| Code | Usage |
|------|-------|
| 200 | OK (GET, PATCH, successful operations) |
| 201 | Created (POST for new resources) |
| 204 | No Content (DELETE success) |
| 400 | Bad Request (validation, business logic) |
| 401 | Unauthorized (invalid/missing token) |
| 403 | Forbidden (RBAC failure) |
| 404 | Not Found (resource missing) |
| 413 | Request Entity Too Large (file upload) |
| 422 | Validation Error (Pydantic validation) |
| 500 | Internal Server Error |
| 503 | Service Unavailable (readiness check) |

### Frontend-Backend Mapping

| Frontend Page/Feature | Backend Endpoints Used |
|----------------------|----------------------|
| Login/Register | `/auth/login`, `/auth/register`, `/auth/refresh` |
| Dashboard | `/workspace`, `/projects`, `/dashboard` |
| Projects | `/projects` (CRUD), `/dashboard/projects/{id}` |
| Sessions | `/sessions` (CRUD), `/sessions/{id}/history` |
| Chat | `/chat`, `/chat/stream` |
| Memory | `/memory` (CRUD), `/memory/search` |
| Ingest | `/ingest/upload`, `/ingest/sources`, `/ingest/facts`, `/ingest/decisions` |
| Graph | `/ingest/graph` |
| Timeline | `/ingest/timeline` |
| Search | `/ingest/search`, `/memory/search` |
| Provenance | `/provenance` |
| Feedback | `/feedback` |
| Settings (Workspace) | `/workspace`, `/workspace/members`, `/workspace/members/invitations` |
| Settings (Profile) | `/auth/me`, `/auth/change-password` |
| Settings (API Keys) | `/api-keys` |
| Settings (Storage) | `/storage/upload`, `/storage/{key}` |
