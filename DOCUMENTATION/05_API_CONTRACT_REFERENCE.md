# SwarmVault WebApp — API Contract Reference
**Version:** 1.0.0
**Date:** 2026-09-01
**Evidence base:** Repository inspection (commit 902d85e), schemas.py, 629 tests
**Base URL:** `/api/v1`

---

## Authentication

All endpoints except `/auth/*` require a valid JWT Bearer token:
```
Authorization: Bearer <access_token>
```

Token lifetime: 60 minutes. Refresh via `POST /auth/refresh`.

---

## Error Format
```json
{
  "error": {
    "type": "error_type",
    "message": "Human-readable description",
    "request_id": "uuid"
  }
}
```

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request (validation, duplicate) |
| 401 | Unauthenticated (missing/invalid/expired token) |
| 403 | Forbidden (insufficient role) |
| 404 | Not found |
| 422 | Validation error |
| 429 | Rate limited |
| 500 | Server error |
| 503 | Service unavailable |

---

## Pagination

List endpoints return:
```json
{
  "items": [...],
  "total": <int>
}
```

Query parameters:
| Param | Type | Default | Purpose |
|-------|------|---------|---------|
| limit | int | varies | Max items per page |
| offset | int | 0 | Items to skip |

**Evidence:** `FactListResponse`, `DecisionListResponse`, `SourceListResponse`, `FeedbackListResponse`, `IngestJobListResponse` schemas.

---

## Auth Endpoints

### POST /auth/register
Register a new user and create a default workspace.
- **Auth:** None required
- **Request:** `UserRegister` { email, name, password (min 8 chars), workspace_name }
- **Response:** `TokenResponse` { access_token, refresh_token, token_type, expires_in }
- **Side effects:** Creates Tenant → Workspace → User → WorkspaceMember (owner role)
- **Errors:** 400 (duplicate email), 422 (validation)
- **Evidence:** `app/api/auth.py:37-60`, test_register, test_register_duplicate_email

### POST /auth/login
Authenticate and receive tokens.
- **Auth:** None
- **Request:** `UserLogin` { email, password }
- **Response:** `TokenResponse`
- **Side effects:** None
- **Errors:** 401 (invalid credentials)
- **Evidence:** `app/api/auth.py`, test_login_success, test_login_invalid

### POST /auth/refresh
Rotate refresh token.
- **Auth:** None (refresh token in body)
- **Request:** `RefreshRequest` { refresh_token }
- **Response:** `TokenResponse`
- **Side effects:** Old refresh token revoked, new one issued
- **Errors:** 401 (invalid/expired/revoked token)
- **Evidence:** `app/api/auth.py`, test_refresh_token, test_refresh_rotation

### POST /auth/logout
Revoke refresh token.
- **Auth:** JWT required
- **Request:** None
- **Response:** 200
- **Side effects:** Refresh token marked as revoked
- **Evidence:** `app/api/auth.py`, test_logout

### POST /auth/change-password
Change user password.
- **Auth:** JWT required
- **Request:** `ChangePasswordRequest` { current_password, new_password (min 8) }
- **Response:** 200
- **Errors:** 400 (wrong current password)
- **Evidence:** `app/api/auth.py`

### GET /auth/me
Get current user profile.
- **Auth:** JWT required
- **Response:** `UserOut`
- **Evidence:** `app/api/auth.py`

---

## Workspace Endpoints

### GET /workspace
List user's workspaces.
- **Auth:** JWT required
- **Response:** `list[WorkspaceOut]`
- **Evidence:** `app/api/workspace.py`

### POST /workspace
Create workspace.
- **Auth:** JWT required
- **Request:** `WorkspaceCreate` { name, slug, description? }
- **Response:** `WorkspaceOut`
- **Evidence:** `app/api/workspace.py`

### GET /workspace/{id}
Get workspace detail.
- **Auth:** JWT required, member of workspace
- **Response:** `WorkspaceOut`
- **Errors:** 404
- **Evidence:** `app/api/workspace.py`

### PATCH /workspace/{id}
Update workspace.
- **Auth:** JWT required, owner/admin
- **Request:** `WorkspaceCreate`
- **Response:** `WorkspaceOut`
- **Evidence:** `app/api/workspace.py`

### DELETE /workspace/{id}
Soft-delete workspace.
- **Auth:** JWT required, owner only
- **Response:** 200
- **Side effects:** Sets deleted_at
- **Evidence:** `app/api/workspace.py`

### GET /workspace/{id}/members
List workspace members.
- **Auth:** JWT required, member
- **Response:** `list[WorkspaceMemberOut]`
- **Evidence:** `app/api/workspace.py`

### POST /workspace/{id}/members
Invite member.
- **Auth:** JWT required, owner/admin
- **Request:** `WorkspaceMemberInvite` { email, role?, message? }
- **Response:** `WorkspaceMemberOut`
- **Evidence:** `app/api/workspace.py`

### PATCH /workspace/{id}/members/{member_id}
Update member role.
- **Auth:** JWT required, owner/admin
- **Request:** `WorkspaceMemberUpdate` { role?, expires? }
- **Response:** `WorkspaceMemberOut`
- **Evidence:** `app/api/workspace.py`

### DELETE /workspace/{id}/members/{member_id}
Remove member.
- **Auth:** JWT required, owner/admin
- **Response:** 200
- **Evidence:** `app/api/workspace.py`

### GET /workspace/invitations
List user's invitations.
- **Auth:** JWT required
- **Response:** `list[InvitationOut]`
- **Evidence:** `app/api/workspace.py`

### PATCH /workspace/invitations/{id}
Accept/decline invitation.
- **Auth:** JWT required
- **Request:** `InvitationUpdate` { state }
- **Response:** `InvitationOut`
- **Evidence:** `app/api/workspace.py`

---

## Project Endpoints

### GET /projects
List workspace projects.
- **Auth:** JWT required, workspace member
- **Query:** limit?, offset?
- **Response:** `ProjectListResponse`
- **Evidence:** `app/api/projects.py`

### POST /projects
Create project.
- **Auth:** JWT required, workspace member
- **Request:** `ProjectCreate` { name, description? }
- **Response:** `ProjectOut`
- **Evidence:** `app/api/projects.py`

### GET /projects/{id}
Get project detail.
- **Auth:** JWT required, workspace member
- **Response:** `ProjectOut`
- **Evidence:** `app/api/projects.py`

### PATCH /projects/{id}
Update project.
- **Auth:** JWT required, member+
- **Request:** `ProjectUpdate` { name?, description? }
- **Response:** `ProjectOut`
- **Evidence:** `app/api/projects.py`

### DELETE /projects/{id}
Soft-delete project.
- **Auth:** JWT required, owner/admin
- **Response:** 200
- **Side effects:** Sets deleted_at
- **Evidence:** `app/api/projects.py`

### GET /projects/{id}/dashboard
Project statistics.
- **Auth:** JWT required, workspace member
- **Response:** `ProjectDashboard`
- **Evidence:** `app/api/dashboard.py`

---

## Session Endpoints

### GET /sessions
List workspace/project sessions.
- **Auth:** JWT required
- **Query:** project_id?, limit?, offset?
- **Response:** `SessionListResponse`
- **Evidence:** `app/api/sessions.py`

### POST /sessions
Create session.
- **Auth:** JWT required
- **Request:** `SessionCreate` { title?, metadata? }
- **Response:** `SessionOut`
- **Evidence:** `app/api/sessions.py`

### GET /sessions/{id}
Get session with messages.
- **Auth:** JWT required, owner
- **Response:** `SessionOut` with messages
- **Evidence:** `app/api/sessions.py`

### PATCH /sessions/{id}
Update session title.
- **Auth:** JWT required, owner
- **Request:** `SessionUpdate` { title? }
- **Response:** `SessionOut`
- **Evidence:** `app/api/sessions.py`

### DELETE /sessions/{id}
Soft-delete session.
- **Auth:** JWT required, owner
- **Response:** 200
- **Evidence:** `app/api/sessions.py`

### POST /sessions/{id}/messages
Add message to session.
- **Auth:** JWT required, owner
- **Request:** `MessageCreate` { role, content, metadata? }
- **Response:** `MessageOut`
- **Evidence:** `app/api/sessions.py`

---

## Chat Endpoints

### POST /chat
Send message and receive streaming response.
- **Auth:** JWT required, minimum role: viewer
- **Request:** `ChatRequest` { message (min 1 char), session_id?, project_id? }
- **Response:** SSE stream with events:
  - `token` — response token delta
  - `sources` — retrieval sources
  - `done` — completion with full metadata
  - `error` — error occurred
- **Side effects:**
  - Creates Session if no session_id
  - Stores user Message
  - Streams assistant response
  - Creates MessageProvenance record
- **Response model:** `ChatResponse` { message_id, session_id, response, model, usage, memory_ids_used, retrieval_method, retrieval_sources, latency_ms, confidence, provider }
- **Evidence:** `app/api/chat.py`, `app/services/chat_orchestrator.py`, test_chat, test_chat_sprint2

---

## Memory Endpoints

### GET /memory
List memories.
- **Auth:** JWT required
- **Query:** project_id?, memory_type?, temporal_status?, limit?, offset?
- **Response:** `MemoryListResponse`
- **Evidence:** `app/api/memory.py`

### POST /memory
Create memory.
- **Auth:** JWT required, member+
- **Request:** `MemoryCreate` { content (1–1,000,000 chars, no null bytes), memory_type?, agent_id?, run_id?, project_id?, metadata? }
- **Response:** `MemoryOut`
- **Side effects:**
  - Sets tenant_id, workspace_id from context
  - Sets temporal_status="current", confidence=0.7, authority=1.0
  - Emits audit event
  - Attaches provenance
- **Evidence:** `app/api/memory.py`, `app/services/memory.py`

### GET /memory/{id}
Get memory detail.
- **Auth:** JWT required, same workspace
- **Response:** `MemoryOut`
- **Errors:** 404
- **Evidence:** `app/api/memory.py`

### PATCH /memory/{id}
Update memory.
- **Auth:** JWT required, member+
- **Request:** `MemoryUpdate` { content?, memory_type?, project_id?, temporal_status? }
- **Response:** `MemoryOut`
- **Evidence:** `app/api/memory.py`

### DELETE /memory/{id}
Soft-delete memory.
- **Auth:** JWT required, admin+
- **Response:** 200
- **Side effects:** Sets deleted_at
- **Evidence:** `app/api/memory.py`

### GET /memory/search
Search memories.
- **Auth:** JWT required
- **Query:** query (required, min 1 char), memory_type?, limit? (1–100, default 20)
- **Request:** `MemorySearchRequest`
- **Response:** `MemorySearchResponse`
- **Evidence:** `app/api/memory.py`, `app/services/m5_retrieval.py`

### GET /memory/{id}/provenance
Get memory provenance chain.
- **Auth:** JWT required, same workspace
- **Response:** `MemoryProvenanceOut`
- **Evidence:** `app/api/memory.py`

---

## Ingestion Endpoints

### POST /ingest
Upload content for ingestion.
- **Auth:** JWT required, minimum role: member
- **Request:** `IngestUploadRequest` { project_id, source_type (text/json/jsonl/chatgpt), title?, content (1–1,000,000 chars), config? }
- **Response:** `IngestUploadResponse` { source_id, session_id, status, messages_processed, facts_created, decisions_created, graph_nodes_created, graph_edges_created, topics, entities }
- **Side effects:**
  - Creates Source record
  - Creates IngestJob record
  - Runs M0→M5 pipeline synchronously
  - Creates/updates Session
  - Creates Fact, Decision, GraphNode, GraphEdge records
- **Evidence:** `app/api/ingest.py`, `app/services/pipeline.py`

### GET /ingest/jobs
List ingestion jobs.
- **Auth:** JWT required
- **Query:** project_id?, status?, limit?, offset?
- **Response:** `IngestJobListResponse`
- **Evidence:** `app/api/ingest.py`

### GET /ingest/jobs/{id}
Get job detail.
- **Auth:** JWT required
- **Response:** `IngestJobOut`
- **Evidence:** `app/api/ingest.py`

### GET /ingest/sources
List sources.
- **Auth:** JWT required
- **Query:** project_id?, source_type?, limit?, offset?
- **Response:** `SourceListResponse`
- **Evidence:** `app/api/ingest.py`

### GET /ingest/sources/{id}
Get source with normalized messages.
- **Auth:** JWT required
- **Response:** `SourceDetail`
- **Evidence:** `app/api/ingest.py`

---

## Provenance Endpoints

### GET /provenance/{id}
Get provenance record.
- **Auth:** JWT required, same workspace
- **Response:** `ProvenanceOut`
- **Evidence:** `app/api/provenance.py`

### GET /provenance
List provenance records.
- **Auth:** JWT required
- **Query:** session_id?, project_id?, limit?, offset?
- **Response:** Paginated list
- **Evidence:** `app/api/provenance.py`

### GET /graph
Query knowledge graph.
- **Auth:** JWT required
- **Query:** project_id?, node_type?, relationship_type?, include_superseded?
- **Response:** `GraphResponse` { nodes, edges }
- **Evidence:** `app/api/provenance.py`, `app/services/m4_graph.py`

### GET /graph/neighbors/{node_id}
Get neighboring nodes.
- **Auth:** JWT required
- **Response:** `list[GraphNodeOut]`
- **Evidence:** `app/api/provenance.py`

### GET /graph/shortest-path
Find path between nodes.
- **Auth:** JWT required
- **Query:** from_node_id, to_node_id
- **Response:** `list[GraphNodeOut]` (path)
- **Evidence:** `app/api/provenance.py`

### GET /graph/stats
Graph statistics.
- **Auth:** JWT required
- **Query:** project_id?
- **Response:** Graph statistics (node/edge counts)
- **Evidence:** `app/api/provenance.py`

### GET /timeline
Get temporal timeline.
- **Auth:** JWT required
- **Query:** project_id?, item_type?, limit?, offset?
- **Response:** `TimelineResponse` { items, total }
- **Evidence:** `app/api/provenance.py`

### GET /facts
List facts.
- **Auth:** JWT required
- **Query:** project_id?, temporal_status?, limit?, offset?
- **Response:** `FactListResponse`
- **Evidence:** `app/api/provenance.py`

### GET /decisions
List decisions.
- **Auth:** JWT required
- **Query:** project_id?, temporal_status?, limit?, offset?
- **Response:** `DecisionListResponse`
- **Evidence:** `app/api/provenance.py`

---

## Dashboard Endpoints

### GET /dashboard
Workspace overview statistics.
- **Auth:** JWT required
- **Response:** `DashboardOverview` { workspace_id, total_memories, total_sources, total_sessions, total_facts, total_decisions, total_graph_nodes, total_graph_edges, recent_memories, recent_sessions, memory_types }
- **Evidence:** `app/api/dashboard.py`

---

## Feedback Endpoints

### POST /feedback
Submit feedback on a response.
- **Auth:** JWT required
- **Request:** `FeedbackCreate` { provenance_id?, session_id?, rating (thumbs_up/thumbs_down), comment? (max 2000 chars) }
- **Response:** `FeedbackOut`
- **Evidence:** `app/api/feedback.py`

### GET /feedback
List feedback.
- **Auth:** JWT required
- **Query:** session_id?, limit?, offset?
- **Response:** `FeedbackListResponse`
- **Evidence:** `app/api/feedback.py`

---

## API Key Endpoints

### GET /api-keys
List API keys.
- **Auth:** JWT required
- **Response:** `list[ApiKeyOut]` (key_hash never returned)
- **Evidence:** `app/api/api_keys.py`

### POST /api-keys
Create API key.
- **Auth:** JWT required
- **Request:** { name, description?, expires_at? }
- **Response:** `ApiKeyCreateResponse` { id, key (full key, shown once), key_prefix, ... }
- **Side effects:** key_hash stored (SHA-256), plaintext key returned once
- **Evidence:** `app/api/api_keys.py`

### DELETE /api-keys/{id}
Revoke API key.
- **Auth:** JWT required
- **Response:** 200
- **Evidence:** `app/api/api_keys.py`

---

## Storage Endpoints

### POST /storage/upload
Upload file.
- **Auth:** JWT required
- **Request:** multipart/form-data
- **Response:** Storage object reference
- **Evidence:** `app/api/storage.py`

### GET /storage/{object_id}
Download file.
- **Auth:** JWT required, same workspace
- **Response:** File content
- **Evidence:** `app/api/storage.py`

### DELETE /storage/{object_id}
Delete file.
- **Auth:** JWT required, admin+
- **Response:** 200
- **Evidence:** `app/api/storage.py`

---

## Policy Endpoints

### GET /policy
List policies.
- **Auth:** JWT required
- **Query:** tenant_id
- **Response:** Paginated list
- **Evidence:** `app/api/policy.py`

### POST /policy
Create policy.
- **Auth:** JWT required, tenant admin
- **Request:** { name, description?, rules? }
- **Response:** Policy record
- **Evidence:** `app/api/policy.py`

### PATCH /policy/{id}
Update policy.
- **Auth:** JWT required, tenant admin
- **Request:** { name?, description?, status? }
- **Response:** Policy record
- **Evidence:** `app/api/policy.py`

---

## Audit Endpoints

### GET /audit/events
List audit events.
- **Auth:** JWT required, tenant admin
- **Query:** tenant_id?, workspace_id?, principal_id?, action?, event_type?, decision?, start_time?, end_time?, limit?, offset?
- **Response:** Paginated list of AuditEvent
- **Evidence:** `app/api/audit.py`

### GET /audit/events/{id}
Get audit event detail.
- **Auth:** JWT required, tenant admin
- **Response:** AuditEvent
- **Evidence:** `app/api/audit.py`

---

## Health Endpoints

### GET /health/live
Liveness probe.
- **Auth:** None
- **Response:** `{"status": "alive"}`
- **Evidence:** `app/main.py:254-256`

### GET /health/ready
Readiness probe (checks DB).
- **Auth:** None
- **Response:** `{"status": "ready", "database": "connected"}` or 503
- **Evidence:** `app/main.py:259-271`

### GET /health
General health.
- **Auth:** None
- **Response:** `{"status": "ok"}`
- **Evidence:** `app/main.py:274-276`

---

## Security Headers (All Responses)

| Header | Value |
|--------|-------|
| X-Request-ID | UUID (per request) |
| X-Content-Type-Options | nosniff |
| X-Frame-Options | DENY |
| X-XSS-Protection | 1; mode=block |
| Referrer-Policy | strict-origin-when-cross-origin |
| Permissions-Policy | geolocation=(), microphone=(), camera=() |
| Strict-Transport-Security | max-age=31536000; includeSubDomains (production only) |
| Content-Security-Policy | Production: default-src 'self'; Dev: allows localhost |

**Evidence:** `app/main.py:47-81`
