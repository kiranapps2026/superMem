# SwarmVault WebApp — API Endpoint Inventory
**Release:** `0534efe426e42f9c03f1622dd792f052647038cc`
**Base URL:** `/api/v1`
**Status:** FROZEN — for frontend integration use

---

## Global Behavior

| Aspect | Detail |
|--------|--------|
| Authentication | `Authorization: Bearer <JWT>` on all protected endpoints |
| Tenant context | Derived from JWT + `X-Workspace-Id` header (optional) |
| Content-Type | `application/json` for all non-upload endpoints |
| Error format | `{"error": {"type": "<code>", "message": "<human>", "request_id": "<uuid>"}}` |
| Timestamps | ISO 8601 UTC (`datetime` → JSON string) |
| IDs | UUID strings |

## Security Headers (every response)

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
Strict-Transport-Security: max-age=31536000; includeSubDomains (production only)
Content-Security-Policy: restrictive in production, permissive in dev
```

## Rate Limits

| Path Pattern | Limit | Window | Key |
|---|---|---|---|
| `/api/v1/auth/register` | 10 | 60s | IP |
| `/api/v1/auth/login` | 10 | 60s | IP |
| `/api/v1/chat/*` | 30 | 60s | User (or IP if unauthenticated) |
| `/api/v1/ingest/upload` | 5 | 3600s (1h) | User (or IP) |
| `/api/v1/ingest/search` | 60 | 60s | User (or IP) |

On breach: HTTP 429 with `Retry-After` header.

---

## 1. Health (no auth required)

| # | Method | Path | Purpose |
|---|---|---|---|
| 1 | GET | `/health/live` | Liveness probe — always returns `{"status":"alive"}` |
| 2 | GET | `/health/ready` | Readiness probe — checks DB connectivity, returns 503 if unavailable |
| 3 | GET | `/health` | Legacy health — returns `{"status":"ok"}` |

These are **infrastructure endpoints**. Do not expose them in the frontend UI.

---

## 2. Authentication

| # | Method | Path | Auth | RBAC | Purpose |
|---|---|---|---|---|---|
| 4 | POST | `/api/v1/auth/register` | No | No | Register new user, creates tenant + workspace |
| 5 | POST | `/api/v1/auth/login` | No | No | Obtain JWT access + refresh tokens |
| 6 | POST | `/api/v1/auth/refresh` | No | No | Refresh access token |
| 7 | POST | `/api/v1/auth/logout` | JWT | No | Revoke refresh token |
| 8 | GET | `/api/v1/auth/me` | JWT | No | Get current user profile |
| 9 | POST | `/api/v1/auth/change-password` | JWT | No | Change password |

### Auth Request/Response Schemas

**UserRegister** (request):
```json
{
  "email": "user@example.com",
  "name": "User Name",
  "password": "min 8 chars",
  "workspace_name": "My Workspace"
}
```

**UserLogin** (request):
```json
{
  "email": "user@example.com",
  "password": "password"
}
```

**RefreshRequest** (request):
```json
{
  "refresh_token": "<refresh_token_string>"
}
```

**TokenResponse** (response — used by register, login, refresh):
```json
{
  "access_token": "<jwt_string>",
  "refresh_token": "<refresh_token_string>",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**ChangePasswordRequest** (request):
```json
{
  "current_password": "old_password",
  "new_password": "new_min_8_chars"
}
```

**UserOut** (response):
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "User Name",
  "is_active": true,
  "email_verified": false,
  "created_at": "2026-01-01T00:00:00Z"
}
```

### Auth Lifecycle

1. **Register** → creates tenant, workspace, user, workspace_membership (owner role), returns tokens
2. **Login** → validates credentials, returns tokens (access: 60min, refresh: 30 days)
3. **Refresh** → exchanges refresh token for new access token
4. **Logout** → revokes refresh token in DB
5. **Me** → returns current user from JWT claims
6. **Change Password** → requires current password, sets new password

### Error Codes

| Status | Code | Condition |
|--------|------|-----------|
| 400 | validation_error | Email already exists, weak password |
| 401 | unauthorized | Invalid credentials, invalid/expired refresh token |
| 403 | forbidden | User account disabled |
| 500 | internal_error | Unexpected server error |

---

## 3. Workspace & Members

| # | Method | Path | Auth | RBAC | Purpose |
|---|---|---|---|---|---|
| 10 | GET | `/api/v1/workspace/` | JWT | — | Get current workspace |
| 11 | PATCH | `/api/v1/workspace/` | JWT | admin | Update workspace |
| 12 | DELETE | `/api/v1/workspace/` | JWT | owner | Delete workspace |
| 13 | GET | `/api/v1/workspace/members` | JWT | — | List workspace members |
| 14 | POST | `/api/v1/workspace/members` | JWT | admin | Invite member |
| 15 | PATCH | `/api/v1/workspace/members/{member_id}` | JWT | admin | Update member role |
| 16 | DELETE | `/api/v1/workspace/members/{user_id}` | JWT | admin | Remove member |
| 17 | POST | `/api/v1/workspace/member/leave` | JWT | — | Leave workspace |
| 18 | GET | `/api/v1/workspace/members/invitations` | JWT | member | List invitations |
| 19 | GET | `/api/v1/workspace/members/invitations/{state}` | JWT | member | List invitations by state |
| 20 | PATCH | `/api/v1/workspace/members/invitation/{invitation_id}` | JWT | admin | Update invitation |
| 21 | DELETE | `/api/v1/workspace/members/invitation/{invitation_id}` | JWT | admin | Delete invitation |
| 22 | GET | `/api/v1/workspace/workspaces/all` | JWT | — | List all user's workspaces |
| 23 | GET | `/api/v1/workspace/workspaces/available` | JWT | — | List available workspaces (cross-tenant) |

### Workspace Schemas

**WorkspaceOut** (response):
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "name": "Workspace Name",
  "slug": "workspace-slug",
  "description": null,
  "created_at": "2026-01-01T00:00:00Z"
}
```

**WorkspaceMemberOut** (response):
```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "user_id": "uuid",
  "user_name": "User Name",
  "user_email": "user@example.com",
  "role": "owner|admin|member|viewer",
  "joined_at": "2026-01-01T00:00:00Z",
  "invited_at": "2026-01-01T00:00:00Z",
  "expires": null
}
```

**WorkspaceMemberInvite** (request):
```json
{
  "email": "newuser@example.com",
  "role": "member",
  "message": null,
  "invitation_expires": null
}
```

**InvitationOut** (response):
```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "email": "invited@example.com",
  "role": "member",
  "state": "pending|accepted|declined|expired|revoked",
  "created_at": "2026-01-01T00:00:00Z",
  "expires_at": null
}
```

### Role Values

```
owner > admin > member > viewer
```

### Error Codes

| Status | Code | Condition |
|--------|------|-----------|
| 400 | validation_error | Self-demotion, owner cannot leave, already member |
| 401 | unauthorized | Missing/invalid JWT |
| 403 | forbidden | Insufficient role, owner removal attempted |
| 404 | not_found | Workspace/member/invitation not found |

---

## 4. Projects

| # | Method | Path | Auth | RBAC | Purpose |
|---|---|---|---|---|---|
| 24 | GET | `/api/v1/projects/` | JWT | — | List projects in workspace |
| 25 | POST | `/api/v1/projects/` | JWT | member | Create project |
| 26 | GET | `/api/v1/projects/{project_id}` | JWT | — | Get project detail |
| 27 | PATCH | `/api/v1/projects/{project_id}` | JWT | member | Update project |
| 28 | DELETE | `/api/v1/projects/{project_id}` | JWT | admin | Delete project |

### Project Schemas

**ProjectCreate** (request):
```json
{
  "name": "Project Name",
  "description": "Optional description"
}
```

**ProjectUpdate** (request):
```json
{
  "name": "New Name",
  "description": "New description"
}
```

**ProjectOut** (response):
```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "name": "Project Name",
  "description": "Optional description",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

### Error Codes

| Status | Code | Condition |
|--------|------|-----------|
| 401 | unauthorized | Missing/invalid JWT |
| 404 | not_found | Project not found or not in workspace |

---

## 5. Sessions

| # | Method | Path | Auth | RBAC | Purpose |
|---|---|---|---|---|---|
| 29 | GET | `/api/v1/sessions/` | JWT | — | List sessions in workspace |
| 30 | POST | `/api/v1/sessions/` | JWT | member | Create session |
| 31 | GET | `/api/v1/sessions/{session_id}` | JWT | — | Get session detail |
| 32 | GET | `/api/v1/sessions/{session_id}/history` | JWT | — | Get session message history |
| 33 | POST | `/api/v1/sessions/{session_id}/messages` | JWT | member | Add message to session |
| 34 | DELETE | `/api/v1/sessions/{session_id}` | JWT | — | Delete session |

### Session Schemas

**SessionCreate** (request):
```json
{
  "title": "Session Title",
  "extra_metadata": {}
}
```

**SessionOut** (response):
```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "user_id": "uuid",
  "title": "Session Title",
  "extra_metadata": {},
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

**MessageCreate** (request):
```json
{
  "role": "user|assistant|system",
  "content": "Message text",
  "metadata": {}
}
```

**MessageOut** (response):
```json
{
  "id": "uuid",
  "session_id": "uuid",
  "role": "user|assistant|system",
  "content": "Message text",
  "metadata": {},
  "created_at": "2026-01-01T00:00:00Z"
}
```

**Session History** (response — GET `/sessions/{id}/history`):
```json
{
  "session": { /* SessionOut */ },
  "messages": [ /* MessageOut[] */ ]
}
```

### Error Codes

| Status | Code | Condition |
|--------|------|-----------|
| 401 | unauthorized | Missing/invalid JWT |
| 404 | not_found | Session not found |

---

## 6. Chat (Non-Streaming)

| # | Method | Path | Auth | RBAC | Purpose |
|---|---|---|---|---|---|
| 35 | POST | `/api/v1/chat/` | JWT | viewer | Send message, receive full response |

### Chat Request/Response

**ChatRequest** (request):
```json
{
  "message": "User message text",
  "session_id": "uuid (optional — creates if omitted)",
  "project_id": "uuid (optional)"
}
```

**ChatResponse** (response):
```json
{
  "message_id": "uuid",
  "session_id": "uuid",
  "response": "AI response text",
  "model": "mock",
  "usage": {"prompt_tokens": 0, "completion_tokens": 0},
  "memory_ids_used": [],
  "retrieval_method": null,
  "retrieval_sources": [],
  "latency_ms": 150,
  "confidence": 0.95,
  "provider": "anthropic"
}
```

### Error Codes

| Status | Code | Condition |
|--------|------|-----------|
| 404 | not_found | Session not found (when session_id provided) |

---

## 7. Chat (SSE Streaming)

| # | Method | Path | Auth | RBAC | Purpose |
|---|---|---|---|---|---|
| 36 | POST | `/api/v1/chat/stream` | JWT | **NONE** | Stream chat response via SSE |

### SSE Event Types

| Event | Payload | When |
|-------|---------|------|
| `sources` | `{"type":"sources","sources":[...]}` | Retrieved memory sources sent before tokens |
| `token` | `{"type":"token","content":"text chunk"}` | Incremental text chunk |
| `done` | `{"type":"done","message_id":"...","session_id":"...","usage":{},"latency_ms":N,"memory_grounded":bool}` | Stream complete |
| `error` | `{"type":"error","detail":"message"}` | Fatal error |

### SSE Request

Same body as non-streaming `ChatRequest`:
```json
{
  "message": "User message text",
  "session_id": "uuid (optional)",
  "project_id": "uuid (optional)"
}
```

### SSE Connection

- Content-Type: `text/event-stream`
- No HTTP status body — events carry all state
- Connection stays open until `done` or `error` event
- Client disconnect triggers server-side cleanup

### Frontend SSE Handling

```
1. POST /api/v1/chat/stream with body + Authorization header
2. Read response as EventSource / ReadableStream
3. Parse each line: data: {"type":"...","..."}
4. On "token" → append content to display
5. On "sources" → render source cards
6. On "done" → finalize, save message_id
7. On "error" → show error, allow retry
```

### CONTRACT GAP: No RBAC on `/chat/stream`

`POST /chat/` requires `viewer` role. `POST /chat/stream` requires only JWT authentication. Any authenticated user in the workspace can stream, regardless of role. This is inconsistent with the non-streaming endpoint.

---

## 8. Memory

| # | Method | Path | Auth | RBAC | Purpose |
|---|---|---|---|---|---|
| 37 | POST | `/api/v1/memory/` | JWT | policy: memory:write | Create memory |
| 38 | GET | `/api/v1/memory/` | JWT | — | List user's memories |
| 39 | GET | `/api/v1/memory/{memory_id}` | JWT | — | Get specific memory |
| 40 | PATCH | `/api/v1/memory/{memory_id}` | JWT | member | Update memory |
| 41 | DELETE | `/api/v1/memory/{memory_id}` | JWT | owner + policy: memory:delete | Delete memory |
| 42 | POST | `/api/v1/memory/search` | JWT | — | Full-text search |

### Memory Schemas

**MemoryCreate** (request):
```json
{
  "content": "Memory content text",
  "memory_type": "procedural_memory",
  "agent_id": null,
  "run_id": null,
  "project_id": null,
  "extra_metadata": {}
}
```
Constraints: 1–1,000,000 chars, no null bytes, no whitespace-only.

**MemoryUpdate** (request):
```json
{
  "content": "Updated content",
  "memory_type": "episodic_memory",
  "project_id": "uuid",
  "temporal_status": "current|superseded|deprecated"
}
```
All fields optional — only provided fields are updated.

**MemoryOut** (response):
```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "user_id": "uuid",
  "agent_id": null,
  "run_id": null,
  "project_id": null,
  "memory_type": "procedural_memory",
  "content": "Memory content text",
  "extra_metadata": {},
  "temporal_status": "current",
  "confidence": 0.0,
  "authority": 0.0,
  "deleted_at": null,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

**MemorySearchRequest** (request):
```json
{
  "query": "search terms",
  "memory_type": "procedural_memory",
  "limit": 20
}
```

### List Endpoints Query Parameters

| Endpoint | Filters | Pagination |
|---|---|---|
| GET `/memory/` | `memory_type`, `project_id`, `temporal_status`, `include_deleted` | `limit` (1–200, default 50), `offset` |
| POST `/memory/search` | `memory_type` | `limit` (1–100, default 20) |
| GET `/ingest/facts` | `project_id`, `subject`, `temporal_status` | `limit` (1–200), `offset` |
| GET `/ingest/decisions` | `project_id`, `temporal_status` | `limit` (1–200), `offset` |
| GET `/ingest/timeline` | `project_id` | `limit` (1–200) |
| GET `/ingest/sources` | `project_id`, `status` | `limit` (1–200), `offset` |
| GET `/ingest/jobs` | — | `limit` (1–200), `offset` |
| GET `/feedback/` | `session_id` | `limit` (1–200), `offset` |
| GET `/provenance/` | `session_id`, `project_id` | `limit` (1–200), `offset` |

**No cursor-based pagination.** All list endpoints use offset/limit. No `total` count is returned by memory list (only by facts, decisions, timeline, sources, feedback).

---

## 9. Ingestion Pipeline

| # | Method | Path | Auth | RBAC | Purpose |
|---|---|---|---|---|---|
| 43 | POST | `/api/v1/ingest/upload` | JWT | member | Upload + ingest content |
| 44 | POST | `/api/v1/ingest/` | JWT | — | Queue ingestion job |
| 45 | GET | `/api/v1/ingest/sources` | JWT | — | List sources |
| 46 | GET | `/api/v1/ingest/sources/{source_id}` | JWT | — | Get source detail |
| 47 | GET | `/api/v1/ingest/sources/{source_id}/messages` | JWT | — | Get source messages |
| 48 | GET | `/api/v1/ingest/facts` | JWT | — | List facts |
| 49 | GET | `/api/v1/ingest/facts/{fact_id}` | JWT | — | Get fact |
| 50 | GET | `/api/v1/ingest/decisions` | JWT | — | List decisions |
| 51 | GET | `/api/v1/ingest/decisions/{decision_id}` | JWT | — | Get decision |
| 52 | GET | `/api/v1/ingest/graph` | JWT | — | Get knowledge graph |
| 53 | GET | `/api/v1/ingest/timeline` | JWT | — | Get timeline |
| 54 | POST | `/api/v1/ingest/search` | JWT | — | Full-text search |
| 55 | GET | `/api/v1/ingest/jobs` | JWT | — | List ingest jobs |
| 56 | GET | `/api/v1/ingest/jobs/{job_id}` | JWT | — | Get job status |

### Ingestion Schemas

**IngestUploadRequest** (request — multipart):
```json
{
  "project_id": "uuid",
  "source_type": "text|json|jsonl|chatgpt",
  "title": "Optional title",
  "content": "Content to ingest (up to 1M chars)",
  "config": {}
}
```

**IngestUploadResponse** (response):
```json
{
  "source_id": "uuid",
  "session_id": "uuid",
  "status": "processing|completed|failed",
  "stage": "queued|parsing|extracting|classifying|storing|completed|error",
  "messages_processed": 0,
  "facts_created": 0,
  "decisions_created": 0,
  "graph_nodes_created": 0,
  "graph_edges_created": 0,
  "topics": [],
  "entities": [],
  "message": "success"
}
```

**IngestQueued** (request):
```json
{
  "project_id": "uuid",
  "source_type": "text|json|jsonl|chatgpt",
  "config": {}
}
```

**IngestJobOut** (response):
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "workspace_id": "uuid",
  "source_type": "text|json|jsonl|chatgpt",
  "status": "queued|processing|completed|failed|cancelled",
  "stage": "queued|parsing|extracting|classifying|storing|completed|error",
  "progress": 0,
  "error_message": null,
  "estimated_records": null,
  "config": {},
  "created_at": "2026-01-01T00:00:00Z",
  "started_at": null,
  "completed_at": null
}
```

**FactOut** (response):
```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "project_id": "uuid",
  "source_id": "uuid",
  "subject": "subject",
  "predicate": "predicate",
  "object": "object",
  "content": "fact content",
  "confidence": 0.0,
  "authority": 0.0,
  "temporal_status": "current",
  "superseded_by_id": null,
  "status": "active",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

**DecisionOut** (response):
```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "project_id": "uuid",
  "source_id": "uuid",
  "content": "decision content",
  "context": "decision context",
  "confidence": 0.0,
  "authority": 0.0,
  "temporal_status": "current",
  "superseded_by_id": null,
  "status": "active",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

### Graph Response

**GraphResponse** (response):
```json
{
  "nodes": [
    {
      "id": "uuid",
      "workspace_id": "uuid",
      "project_id": "uuid",
      "external_id": null,
      "label": "Node Label",
      "node_type": "concept|entity|...",
      "properties": {},
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "edges": [
    {
      "id": "uuid",
      "workspace_id": "uuid",
      "project_id": "uuid",
      "source_node_id": "uuid",
      "target_node_id": "uuid",
      "relationship_type": "related_to",
      "properties": {},
      "confidence": 0.0,
      "temporal_status": "current",
      "source_id": "uuid",
      "created_at": "2026-01-01T00:00:00Z"
    }
  ]
}
```

### Timeline Response

**TimelineResponse** (response):
```json
{
  "items": [
    {
      "item_type": "memory|fact|decision|session|source",
      "id": "uuid",
      "title": "Item title",
      "timestamp": "2026-01-01T00:00:00Z",
      "temporal_status": "current",
      "content": "Item content preview"
    }
  ],
  "total": 10
}
```

### Search Response

**SearchResponse** (response):
```json
{
  "items": [
    {
      "item_type": "memory|fact|decision",
      "id": "uuid",
      "score": 0.95,
      "content": "result content",
      "temporal_status": "current",
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 10,
  "query": "search terms"
}
```

### Source Schemas

**SourceOut** (response):
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "workspace_id": "uuid",
  "tenant_id": "uuid",
  "source_type": "text|json|jsonl|chatgpt",
  "external_id": null,
  "title": null,
  "description": null,
  "message_count": 0,
  "status": "queued|processing|completed|failed",
  "stage": "queued|parsing|extracting|classifying|storing|completed|error",
  "progress": 0,
  "error_message": null,
  "created_at": "2026-01-01T00:00:00Z",
  "completed_at": null
}
```

**SourceDetail** (response — extends SourceOut):
```json
{
  /* all SourceOut fields */
  "normalized_messages": [
    {
      "id": "uuid",
      "source_id": "uuid",
      "session_id": "uuid",
      "message_index": 0,
      "external_id": null,
      "role": "user|assistant|system",
      "content": "message text",
      "extra_metadata": {},
      "timestamp": "2026-01-01T00:00:00Z",
      "created_at": "2026-01-01T00:00:00Z"
    }
  ]
}
```

**NormalizedMessageOut** (response):
```json
{
  "id": "uuid",
  "source_id": "uuid",
  "session_id": "uuid",
  "message_index": 0,
  "external_id": null,
  "role": "user|assistant|system",
  "content": "message text",
  "extra_metadata": {},
  "timestamp": "2026-01-01T00:00:00Z",
  "created_at": "2026-01-01T00:00:00Z"
}
```

### Error Codes

| Status | Code | Condition |
|--------|------|-----------|
| 400 | validation_error | Invalid source_type, too large |
| 401 | unauthorized | Missing/invalid JWT |
| 404 | not_found | Project, source, fact, decision, job not found |

---

## 10. Provenance

| # | Method | Path | Auth | RBAC | Purpose |
|---|---|---|---|---|---|
| 57 | GET | `/api/v1/provenance/` | JWT | member | List provenance records |
| 58 | GET | `/api/v1/provenance/{provenance_id}` | JWT | — | Get provenance detail |
| 59 | GET | `/api/v1/provenance/{provenance_id}/memories` | JWT | — | Get linked memories |

### Provenance Schemas

**ProvenanceOut** (response):
```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "project_id": null,
  "session_id": "uuid",
  "user_message_id": "uuid",
  "assistant_message_id": "uuid",
  "model": "claude-sonnet-4-5",
  "provider": "anthropic",
  "retrieval_method": "hybrid",
  "memory_ids_used": [],
  "retrieval_sources": [],
  "user_message_preview": "User asked...",
  "prompt_tokens": 100,
  "completion_tokens": 200,
  "total_tokens": 300,
  "latency_ms": 1500,
  "confidence": 0.95,
  "created_at": "2026-01-01T00:00:00Z"
}
```

**MemoryReferenceOut** (response):
```json
{
  "memory_id": "uuid",
  "content": "memory content preview",
  "memory_type": "procedural_memory",
  "confidence": 0.0,
  "authority": 0.0,
  "temporal_status": "current",
  "created_at": "2026-01-01T00:00:00Z",
  "project_id": null
}
```

---

## 11. Dashboard

| # | Method | Path | Auth | RBAC | Purpose |
|---|---|---|---|---|---|
| 60 | GET | `/api/v1/dashboard/` | JWT | — | Workspace overview statistics |
| 61 | GET | `/api/v1/dashboard/projects/{project_id}` | JWT | — | Project-specific statistics |

### Dashboard Schemas

**DashboardOverview** (response):
```json
{
  "workspace_id": "uuid",
  "total_memories": 42,
  "total_sources": 5,
  "total_sessions": 12,
  "total_facts": 30,
  "total_decisions": 8,
  "total_graph_nodes": 15,
  "total_graph_edges": 22,
  "recent_memories": 5,
  "recent_sessions": 3,
  "memory_types": {"procedural_memory": 20, "episodic_memory": 22}
}
```

**ProjectDashboard** (response):
```json
{
  "project_id": "uuid",
  "project_name": "Project Name",
  "total_memories": 42,
  "total_sources": 5,
  "total_facts": 30,
  "total_decisions": 8,
  "total_graph_nodes": 15,
  "total_graph_edges": 22,
  "total_feedback": 3,
  "memory_types": {"procedural_memory": 20, "episodic_memory": 22}
}
```

---

## 12. Feedback

| # | Method | Path | Auth | RBAC | Purpose |
|---|---|---|---|---|---|
| 62 | POST | `/api/v1/feedback/` | JWT | member | Submit feedback on response |
| 63 | GET | `/api/v1/feedback/` | JWT | — | List feedback in workspace |
| 64 | GET | `/api/v1/feedback/{feedback_id}` | JWT | — | Get specific feedback |

### Feedback Schemas

**FeedbackCreate** (request):
```json
{
  "provenance_id": "uuid",
  "session_id": "uuid",
  "rating": "thumbs_up|thumbs_down",
  "comment": "Optional comment up to 2000 chars"
}
```

**FeedbackOut** (response):
```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "user_id": "uuid",
  "provenance_id": "uuid",
  "session_id": "uuid",
  "rating": "thumbs_up",
  "comment": "Optional comment",
  "created_at": "2026-01-01T00:00:00Z"
}
```

---

## 13. API Keys

| # | Method | Path | Auth | RBAC | Purpose |
|---|---|---|---|---|---|
| 65 | POST | `/api/v1/api-keys/` | JWT | admin | Create API key |
| 66 | GET | `/api/v1/api-keys/` | JWT | — | List API keys |
| 67 | DELETE | `/api/v1/api-keys/{key_id}` | JWT | admin | Revoke API key |
| 68 | POST | `/api/v1/api-keys/{key_id}/rotate` | JWT | admin | Rotate API key |

### API Key Schemas

**ApiKeyCreate** (request):
```json
{
  "name": "My API Key",
  "description": "For service X",
  "expires_at": "2027-01-01T00:00:00Z",
  "metadata": {"purpose": "automation"}
}
```

**ApiKeyOut** (response — list endpoint, NO raw key):
```json
{
  "id": "uuid",
  "name": "My API Key",
  "description": "For service X",
  "key_prefix": "sv_abc12...",
  "expires_at": "2027-01-01T00:00:00Z",
  "last_used_at": null,
  "created_at": "2026-01-01T00:00:00Z",
  "revoked_at": null,
  "key_extra": {}
}
```

**ApiKeyCreateResponse** (response — create endpoint, includes raw key):
```json
{
  /* all ApiKeyOut fields */
  "raw_key": "sv_abc12...xxxx"  /* returned ONCE only */
}
```

**ApiKeyRotateResponse** (response):
```json
{
  "id": "uuid",
  "name": "My API Key",
  "key_prefix": "sv_xyz78...",
  "raw_key": "sv_xyz78...xxxx",  /* returned ONCE only */
  "rotated_at": "2026-01-01T00:00:00Z"
}
```

### CRITICAL: Raw key security

- `raw_key` is returned **exactly once** at creation and rotation
- `GET /api-keys/` NEVER returns the raw key
- Frontend must store the raw key securely (it cannot be re-fetched)

---

## 14. Storage

| # | Method | Path | Auth | RBAC | Purpose |
|---|---|---|---|---|---|
| 69 | POST | `/api/v1/storage/upload` | JWT | member | Upload file |
| 70 | GET | `/api/v1/storage/{key:path}` | JWT | — | Get file info (not download) |
| 71 | DELETE | `/api/v1/storage/{key:path}` | JWT | admin | Delete file |

### Storage Schemas

**UploadRequest** (request — multipart/form-data):
```
file: binary
```

**UploadResponse** (response):
```json
{
  "key": "workspace_id/filename",
  "url": "http://host/storage/workspace_id/filename",
  "size": 1024,
  "content_type": "application/pdf",
  "sha256": "hex_hash"
}
```

**FileListResponse** (response):
```json
{
  "items": [...],
  "total": 5
}
```

### Storage Security

- Keys must start with `<workspace_id>/`
- Cross-workspace access is blocked server-side
- Frontend cannot access other workspaces' files

---

## 15. Policy Engine

| # | Method | Path | Auth | RBAC | Purpose |
|---|---|---|---|---|---|
| 72 | GET | `/api/v1/policy/` | JWT | — | List policies |
| 73 | POST | `/api/v1/policy/` | JWT | admin | Create policy |
| 74 | GET | `/api/v1/policy/{policy_id}` | JWT | — | Get policy detail |
| 75 | PATCH | `/api/v1/policy/{policy_id}` | JWT | — | Update policy |
| 76 | DELETE | `/api/v1/policy/{policy_id}` | JWT | — | Delete policy |
| 77 | POST | `/api/v1/policy/{policy_id}/versions` | JWT | — | Create policy version |
| 78 | POST | `/api/v1/policy/test-authorization` | JWT | — | Test authorization rule |

---

## 16. Audit

| # | Method | Path | Auth | RBAC | Purpose |
|---|---|---|---|---|---|
| 79 | GET | `/api/v1/api/v1/audit/events` | JWT | member | List audit events |
| 80 | GET | `/api/v1/api/v1/audit/events/{event_id}` | JWT | member | Get audit event |
| 81 | GET | `/api/v1/api/v1/audit/trace/{request_id}` | JWT | member | Correlation trace |

### CONTRACT GAP: Double-prefix on audit endpoints

The audit router is declared with `prefix="/api/v1/audit"` and included under the parent `api_v1` router (prefix `/api/v1`). Actual paths are `/api/v1/api/v1/audit/events` etc. This is likely unintended — the path should be `/api/v1/audit/events`.

---

## 17. Global Error Contract

All endpoints return errors in this format:

```json
{
  "error": {
    "type": "error_code",
    "message": "Human-readable description",
    "request_id": "uuid"
  }
}
```

| HTTP Status | Error Type | When |
|---|---|---|
| 400 | `validation_error` | Bad request body, invalid parameters |
| 401 | `unauthorized` | Missing/invalid/expired JWT |
| 403 | `forbidden` | Insufficient role or policy denial |
| 404 | `not_found` | Resource not found |
| 405 | `method_not_allowed` | Wrong HTTP method |
| 409 | `conflict` | Duplicate resource, state conflict |
| 422 | `validation_error` | Pydantic validation failure |
| 429 | `rate_limit_exceeded` | Rate limit hit (includes `Retry-After` header) |
| 500 | `internal_error` | Server error (no details exposed) |
| 503 | `service_unavailable` | Database unavailable (health check) |

**What is NEVER exposed to the frontend:**
- Stack traces
- Database exception details
- Internal file paths
- SQL queries
- Passwords or password hashes
- JWT signing secret
- API key raw values (except at creation, shown once)
- Other users' data
