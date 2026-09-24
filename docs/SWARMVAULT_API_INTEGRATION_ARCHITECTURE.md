# SwarmVault WebApp Backend API Surface — Forensic Audit

**Generated:** 2026-09-10
**Scope:** `app/` directory — FastAPI backend
**Classification:** Read-only forensic inventory

---

## 1. Router Files and Prefixes

| Router File | Prefix | Tags | File:Line |
|-------------|--------|------|-----------|
| `app/api/auth.py` | `/auth` | auth | line 25 |
| `app/api/workspace.py` | `/workspace` | workspace | line 16 |
| `app/api/projects.py` | `/projects` | projects | line 12 |
| `app/api/sessions.py` | `/sessions` | sessions | line 12 |
| `app/api/chat.py` | `/chat` | chat | line 25 |
| `app/api/memory.py` | `/memory` | memory | line 47 |
| `app/api/ingest.py` | `/ingest` | ingest | line 29 |
| `app/api/provenance.py` | `/provenance` | provenance | line 13 |
| `app/api/dashboard.py` | `/dashboard` | dashboard | line 18 |
| `app/api/feedback.py` | `/feedback` | feedback | line 19 |
| `app/api/api_keys.py` | `/api-keys` | api-keys | line 43 |
| `app/api/storage.py` | `/storage` | storage | line 26 |
| `app/api/policy.py` | `/policy` | policy | line 25 |
| `app/api/audit.py` | `/audit` | audit | line 35 |

**Root:** All routers included under `api_v1` with prefix `/api/v1` (see `app/main.py` line 141).

---

## 2. Complete Route Inventory

### 2.1 Auth Router (`/api/v1/auth`)

| Path | Method | Handler | Auth | RBAC | File:Line |
|------|--------|---------|------|------|-----------|
| `/register` | POST | `register` | None | — | `app/api/auth.py:37` |
| `/login` | POST | `login` | None | — | `app/api/auth.py:105` |
| `/refresh` | POST | `refresh` | None | — | `app/api/auth.py:152` |
| `/logout` | POST | `logout` | Bearer | Tenant | `app/api/auth.py:212` |
| `/me` | GET | `get_me` | Bearer | Tenant | `app/api/auth.py:231` |
| `/change-password` | POST | `change_password` | Bearer | Tenant | `app/api/auth.py:245` |

### 2.2 Workspace Router (`/api/v1/workspace`)

| Path | Method | Handler | Auth | RBAC | File:Line |
|------|--------|---------|------|------|-----------|
| `/` | GET | `get_workspace` | Bearer | Tenant | `app/api/workspace.py:26` |
| `/` | PATCH | `update_workspace` | Bearer | admin | `app/api/workspace.py:43` |
| `/` | DELETE | `delete_workspace` | Bearer | owner | `app/api/workspace.py:72` |
| `/members` | GET | `list_members` | Bearer | Tenant | `app/api/workspace.py:95` |
| `/members` | POST | `invite_member` | Bearer | admin | `app/api/workspace.py:128` |
| `/members/{member_id}` | PATCH | `update_member` | Bearer | admin | `app/api/workspace.py:195` |
| `/members/{user_id}` | DELETE | `remove_member` | Bearer | admin | `app/api/workspace.py:246` |
| `/member/leave` | POST | `leave_workspace` | Bearer | Tenant | `app/api/workspace.py:280` |
| `/members/invitations` | GET | `list_invitations` | Bearer | member | `app/api/workspace.py:308` |
| `/members/invitations/{state}` | GET | `list_invitations_by_state` | Bearer | member | `app/api/workspace.py:322` |
| `/members/invitation/{invitation_id}` | PATCH | `update_invitation` | Bearer | admin | `app/api/workspace.py:341` |
| `/members/invitation/{invitation_id}` | DELETE | `delete_invitation` | Bearer | admin | `app/api/workspace.py:372` |
| `/workspaces/all` | GET | `list_all_workspaces` | Bearer | Auth | `app/api/workspace.py:396` |
| `/workspaces/available` | GET | `list_available_workspaces` | Bearer | Auth | `app/api/workspace.py:426` |

### 2.3 Projects Router (`/api/v1/projects`)

| Path | Method | Handler | Auth | RBAC | File:Line |
|------|--------|---------|------|------|-----------|
| `/` | GET | `list_projects` | Bearer | Tenant | `app/api/projects.py:22` |
| `/` | POST | `create_project` | Bearer | member | `app/api/projects.py:36` |
| `/{project_id}` | GET | `get_project` | Bearer | Tenant | `app/api/projects.py:54` |
| `/{project_id}` | PATCH | `update_project` | Bearer | member | `app/api/projects.py:73` |
| `/{project_id}` | DELETE | `delete_project` | Bearer | admin | `app/api/projects.py:102` |

### 2.4 Sessions Router (`/api/v1/sessions`)

| Path | Method | Handler | Auth | RBAC | File:Line |
|------|--------|---------|------|------|-----------|
| `/` | GET | `list_sessions` | Bearer | Tenant | `app/api/sessions.py:19` |
| `/` | POST | `create_session` | Bearer | member | `app/api/sessions.py:34` |
| `/{session_id}` | GET | `get_session` | Bearer | Tenant | `app/api/sessions.py:53` |
| `/{session_id}/history` | GET | `get_session_history` | Bearer | Tenant | `app/api/sessions.py:73` |
| `/{session_id}/messages` | POST | `add_message` | Bearer | member | `app/api/sessions.py:112` |
| `/{session_id}` | DELETE | `delete_session` | Bearer | Tenant | `app/api/sessions.py:144` |

### 2.5 Chat Router (`/api/v1/chat`)

| Path | Method | Handler | Auth | RBAC | File:Line |
|------|--------|---------|------|------|-----------|
| `/` | POST | `send_chat_message` | Bearer | viewer | `app/api/chat.py:28` |
| `/stream` | POST | `stream_chat` | Bearer | viewer | `app/api/chat.py:109` |

**SSE Streaming:** `/stream` returns `text/event-stream` with events: `token`, `sources`, `done`, `error` (see `app/api/chat.py:115-121`).

### 2.6 Memory Router (`/api/v1/memory`)

| Path | Method | Handler | Auth | RBAC | File:Line |
|------|--------|---------|------|------|-----------|
| `/` | POST | `create_memory` | Bearer | Policy | `app/api/memory.py:78` |
| `/` | GET | `list_memories` | Bearer | Tenant | `app/api/memory.py:132` |
| `/{memory_id}` | GET | `get_memory` | Bearer | Tenant | `app/api/memory.py:163` |
| `/{memory_id}` | PATCH | `update_memory` | Bearer | member | `app/api/memory.py:194` |
| `/{memory_id}` | DELETE | `delete_memory` | Bearer | owner + Policy | `app/api/memory.py:240` |
| `/search` | POST | `search_memories` | Bearer | Tenant | `app/api/memory.py:265` |

### 2.7 Ingest Router (`/api/v1/ingest`)

| Path | Method | Handler | Auth | RBAC | File:Line |
|------|--------|---------|------|------|-----------|
| `/upload` | POST | `upload_and_ingest` | Bearer | member | `app/api/ingest.py:37` |
| `/` | POST | `legacy_start_ingest` | Bearer | — | `app/api/ingest.py:126` |
| `/sources` | GET | `list_sources` | Bearer | Tenant | `app/api/ingest.py:160` |
| `/sources/{source_id}` | GET | `get_source` | Bearer | Tenant | `app/api/ingest.py:199` |
| `/sources/{source_id}/messages` | GET | `get_source_messages` | Bearer | Tenant | `app/api/ingest.py:230` |
| `/facts` | GET | `list_facts` | Bearer | Tenant | `app/api/ingest.py:263` |
| `/facts/{fact_id}` | GET | `get_fact` | Bearer | Tenant | `app/api/ingest.py:307` |
| `/decisions` | GET | `list_decisions` | Bearer | Tenant | `app/api/ingest.py:329` |
| `/decisions/{decision_id}` | GET | `get_decision` | Bearer | Tenant | `app/api/ingest.py:367` |
| `/graph` | GET | `get_graph` | Bearer | Tenant | `app/api/ingest.py:389` |
| `/timeline` | GET | `get_timeline` | Bearer | Tenant | `app/api/ingest.py:435` |
| `/search` | POST | `search` | Bearer | Tenant | `app/api/ingest.py:505` |
| `/jobs` | GET | `list_jobs` | Bearer | Tenant | `app/api/ingest.py:548` |
| `/jobs/{job_id}` | GET | `get_job` | Bearer | Tenant | `app/api/ingest.py:589` |

### 2.8 Provenance Router (`/api/v1/provenance`)

| Path | Method | Handler | Auth | RBAC | File:Line |
|------|--------|---------|------|------|-----------|
| `/` | GET | `list_provenance` | Bearer | member | `app/api/provenance.py:16` |
| `/{provenance_id}` | GET | `get_provenance` | Bearer | Tenant | `app/api/provenance.py:67` |
| `/{provenance_id}/memories` | GET | `get_provenance_memories` | Bearer | Tenant | `app/api/provenance.py:106` |

### 2.9 Dashboard Router (`/api/v1/dashboard`)

| Path | Method | Handler | Auth | RBAC | File:Line |
|------|--------|---------|------|------|-----------|
| `/` | GET | `workspace_overview` | Bearer | Tenant | `app/api/dashboard.py:25` |
| `/projects/{project_id}` | GET | `project_dashboard` | Bearer | Tenant | `app/api/dashboard.py:122` |

### 2.10 Feedback Router (`/api/v1/feedback`)

| Path | Method | Handler | Auth | RBAC | File:Line |
|------|--------|---------|------|------|-----------|
| `/` | POST | `create_feedback` | Bearer | member | `app/api/feedback.py:26` |
| `/` | GET | `list_feedback` | Bearer | Tenant | `app/api/feedback.py:48` |
| `/{feedback_id}` | GET | `get_feedback` | Bearer | Tenant | `app/api/feedback.py:82` |

### 2.11 API Keys Router (`/api/v1/api-keys`)

| Path | Method | Handler | Auth | RBAC | File:Line |
|------|--------|---------|------|------|-----------|
| `/` | POST | `create_api_key` | Bearer | admin | `app/api/api_keys.py:104` |
| `/` | GET | `list_api_keys` | Bearer | Tenant | `app/api/api_keys.py:155` |
| `/{key_id}` | DELETE | `revoke_api_key` | Bearer | admin | `app/api/api_keys.py:170` |
| `/{key_id}/rotate` | POST | `rotate_api_key` | Bearer | admin | `app/api/api_keys.py:206` |

### 2.12 Storage Router (`/api/v1/storage`)

| Path | Method | Handler | Auth | RBAC | File:Line |
|------|--------|---------|------|------|-----------|
| `/upload` | POST | `upload_file` | Bearer | member | `app/api/storage.py:58` |
| `/{key:path}` | GET | `get_file_info` | Bearer | Tenant | `app/api/storage.py:113` |
| `/{key:path}` | DELETE | `delete_file` | Bearer | admin | `app/api/storage.py:131` |

### 2.13 Policy Router (`/api/v1/policy`)

| Path | Method | Handler | Auth | RBAC | File:Line |
|------|--------|---------|------|------|-----------|
| `/` | GET | `list_policies` | Bearer | Tenant | `app/api/policy.py:110` |
| `/` | POST | `create_policy` | Bearer | admin | `app/api/policy.py:126` |
| `/{policy_id}` | GET | `get_policy` | Bearer | Tenant | `app/api/policy.py:158` |
| `/{policy_id}` | PATCH | `update_policy` | Bearer | — | `app/api/policy.py:201` |
| `/{policy_id}` | DELETE | `delete_policy` | Bearer | — | `app/api/policy.py:231` |
| `/{policy_id}/versions` | POST | `create_policy_version` | Bearer | — | `app/api/policy.py:251` |
| `/test-authorization` | POST | `test_authorization` | Bearer | Tenant | `app/api/policy.py:290` |

### 2.14 Audit Router (`/api/v1/audit`)

| Path | Method | Handler | Auth | RBAC | File:Line |
|------|--------|---------|------|------|-----------|
| `/events` | GET | `list_audit_events` | Bearer | member | `app/api/audit.py:74` |
| `/events/{event_id}` | GET | `get_audit_event` | Bearer | member | `app/api/audit.py:131` |
| `/trace/{request_id}` | GET | `correlation_trace` | Bearer | member | `app/api/audit.py:162` |

---

## 3. Request/Response Schemas

**Primary location:** `app/schemas.py`

Key schema groups:

| Category | Schemas | File:Line |
|----------|---------|-----------|
| Auth | `UserRegister`, `UserLogin`, `TokenResponse`, `RefreshRequest`, `ChangePasswordRequest`, `UserOut` | `app/schemas.py:7-44` |
| Workspace | `WorkspaceCreate`, `WorkspaceOut`, `WorkspaceMemberOut`, `WorkspaceMemberInvite`, `InvitationOut` | `app/schemas.py:47-104` |
| Projects | `ProjectCreate`, `ProjectUpdate`, `ProjectOut` | `app/schemas.py:106-126` |
| Sessions | `SessionCreate`, `SessionOut`, `MessageCreate`, `MessageOut` | `app/schemas.py:129-163` |
| Chat | `ChatRequest`, `ChatResponse` | `app/schemas.py:166-184` |
| Memory | `MemoryCreate`, `MemoryUpdate`, `MemoryOut`, `MemorySearchRequest`, `MemoryReferenceOut` | `app/schemas.py:187-261` |
| Ingest | `IngestUploadRequest`, `IngestUploadResponse`, `IngestJobOut`, `SourceOut`, `SourceDetail` | `app/schemas.py:264-358` |
| Facts/Decisions | `FactOut`, `DecisionOut`, `GraphNodeOut`, `GraphEdgeOut`, `TimelineItem`, `SearchResultItem` | `app/schemas.py:402-519` |
| Feedback | `FeedbackCreate`, `FeedbackOut`, `FeedbackListResponse` | `app/schemas.py:531-554` |
| Dashboard | `DashboardOverview`, `ProjectDashboard` | `app/schemas.py:560-583` |
| API Keys | `ApiKeyOut` | `app/schemas.py:589-602` |

---

## 4. External Integration Points

### 4.1 LLM Providers

**Location:** `app/services/llm.py`

| Provider | Config Key | Default | Status | File:Line |
|----------|------------|---------|--------|-----------|
| Anthropic | `llm_provider=anthropic` | Yes | IMPLEMENTED | `app/services/llm.py:43` |
| OpenAI | `llm_provider=openai` | No | IMPLEMENTED | `app/services/llm.py:95` |
| Mock | fallback | — | IMPLEMENTED | `app/services/llm.py:144` |

**Configuration:**
- `llm_model`: `claude-sonnet-4-5-20250929` (default) — see `app/core/config.py:37`
- `anthropic_api_key`, `openai_api_key`: `app/core/config.py:43-44`
- Timeout/retry: `app/services/llm.py:248-291`

### 4.2 Object Storage

**Location:** `app/services/object_storage.py`

| Backend | Config Key | Default | Status | File:Line |
|---------|------------|---------|--------|-----------|
| Local | `storage_backend=filesystem` | Yes | IMPLEMENTED | `app/services/object_storage.py:58` |
| S3 | `storage_backend=s3` | No | IMPLEMENTED | `app/services/object_storage_s3.py:14` |
| MinIO | `storage_backend=minio` | No | IMPLEMENTED | `app/services/object_storage_minio.py:14` |

**Configuration:** `app/core/config.py:61-68`

### 4.3 Database

- **Engine:** PostgreSQL (async via `asyncpg`) — `app/db.py`
- **ORM:** SQLAlchemy 2.0 async — `app/models.py`
- **Migration:** Alembic — `app/alembic/`

---

## 5. SSE/Streaming Endpoints

| Endpoint | Type | Events | File:Line |
|----------|------|--------|-----------|
| `/api/v1/chat/stream` | SSE | `token`, `sources`, `done`, `error` | `app/api/chat.py:109-274` |

**Implementation:** `StreamingResponse` with `text/event-stream` media type (see `app/api/chat.py:267-274`).

---

## 6. Authentication Mechanism

**Type:** JWT Bearer Tokens

| Component | Location | Details |
|----------|----------|---------|
| Algorithm | `app/core/config.py:27` | `HS256` |
| Access Token Expiry | `app/core/config.py:28` | 60 minutes |
| Refresh Token Expiry | `app/core/config.py:29` | 30 days |
| Secret Key | `app/core/config.py:26` | From env, min 32 chars |
| Password Hashing | `app/core/security.py:6` | Bcrypt |

**Token Endpoints:**
- `POST /api/v1/auth/register` — creates tenant + workspace + user + tokens
- `POST /api/v1/auth/login` — issues tokens
- `POST /api/v1/auth/refresh` — refreshes access token
- `POST /api/v1/auth/logout` — revokes refresh token

**Dependency:** `require_auth` in `app/middleware/auth.py:17`

---

## 7. MCP Integration Status

**Classification:** DOCUMENTED_ONLY

### Evidence:
- `app/models.py:693` — `ApiKey` model exists with comment "API key for MCP server registration"
- `app/api/api_keys.py:1-12` — docstring explicitly mentions "MCP server registration"
- No MCP protocol implementation found in `app/` (no `model-context-protocol`, no MCP server/client code)
- API keys can be created/rotated but are not wired to any MCP protocol handler

### Status: DOCUMENTED_ONLY

The API key infrastructure (`app/api/api_keys.py:104-260`) is designed for MCP server registration but no actual MCP protocol implementation exists. The `ApiKey` model stores key hash, prefix, expiration, and metadata — ready for MCP but not connected.

**File citations:**
- `app/api/api_keys.py:1-12` (docstring)
- `app/models.py:692-730` (ApiKey model)

---

## 8. Claude Code Integration Status

**Classification:** IMPLEMENTED (Data Format)

### Evidence:
- `app/services/connectors.py:295-398` — `ClaudeCodeConnector` class
- Parses Claude Code session JSONL format (`type: user|assistant|system|summary`)
- Handles tool_use events, message content blocks
- Part of the connector registry for ingestion pipeline

### What Works:
- Ingestion of Claude Code session exports via `/api/v1/ingest/upload`
- Supported source types: `claude-code` (JSONL)
- Normalizes Claude Code events to canonical message format

### What Does NOT Work:
- No live API connection to Claude Code
- No MCP-like tool execution bridge
- No session state management for Claude Code agents
- No code execution or tool calling infrastructure

### Status: IMPLEMENTED (Data Format Only)

**File citations:**
- `app/services/connectors.py:295` (ClaudeCodeConnector)
- `app/services/connectors.py:650` (registered in registry)

---

## 9. Codex Integration Status

**Classification:** MISSING

### Evidence:
- No `codex` references in `app/` directory
- No Codex-specific connector, API endpoint, or service
- No Codex CLI integration

### Status: MISSING

---

## 10. Universal Adapter Status

**Classification:** MISSING

### Evidence:
- No `universal.adapter` or `universal_adapter` references in `app/`
- No adapter framework for generic agent integration

### Status: MISSING

---

## 11. REST API Completeness

### Coverage Analysis

| Feature | Endpoints | Completeness |
|---------|-----------|--------------|
| Authentication | 6 | Complete (register, login, refresh, logout, me, password) |
| Multi-tenancy | 14 | Complete (workspace, members, invitations) |
| Projects | 5 | Complete (CRUD + list) |
| Sessions | 6 | Complete (CRUD + history + messages) |
| Chat | 2 | Complete (sync + streaming) |
| Memory | 6 | Complete (CRUD + list + search) |
| Ingestion | 14 | Complete (upload, sources, facts, decisions, graph, timeline, search, jobs) |
| Provenance | 3 | Complete (list, get, expand memories) |
| Dashboard | 2 | Complete (workspace + project) |
| Feedback | 3 | Complete (create, list, get) |
| API Keys | 4 | Complete (create, list, revoke, rotate) |
| Storage | 3 | Complete (upload, get info, delete) |
| Policy | 7 | Complete (CRUD + versions + test) |
| Audit | 3 | Complete (events list, get, trace) |

**Total:** 72 documented endpoints across 14 routers.

### Gaps Observed:
1. No webhook or callback endpoints
2. No batch operation endpoints (bulk memory create, bulk delete)
3. No pagination metadata in list responses beyond `total`/`limit`/`offset`
4. No OpenAPI schema for tool definitions
5. No agent registration or lifecycle endpoints

---

## 12. Error Handling Patterns

### 12.1 Global Exception Handlers

**Location:** `app/main.py:230-246`

| Handler | Status Code | Type | File:Line |
|---------|-------------|------|-----------|
| `RequestValidationError` | 422 | validation_error | `app/main.py:230` |
| `SQLAlchemyError` | 500 | database_error | `app/main.py:235` |
| `Exception` (catch-all) | 500 | internal_error | `app/main.py:241` |

### 12.2 Error Response Schema

**Location:** `app/main.py:124-133`

```python
{
  "error": {
    "type": "validation_error|database_error|internal_error",
    "message": "...",
    "request_id": "..."
  }
}
```

### 12.3 HTTPException Usage

Pattern: `raise HTTPException(status_code=404, detail="...")`

Used throughout routers for:
- 400: Bad request / validation
- 401: Unauthorized (missing/invalid token)
- 403: Forbidden (RBAC denial)
- 404: Resource not found
- 422: Validation error
- 429: Rate limit exceeded
- 413: Payload too large

### 12.4 Rate Limiting

**Location:** `app/middleware/rate_limit.py`

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/v1/auth/login` | 10 | 60s |
| `/api/v1/auth/register` | 10 | 60s |
| `/api/v1/chat/` | 30 | 60s |
| `/api/v1/ingest/upload` | 5 | 3600s |
| `/api/v1/ingest/search` | 60 | 60s |

### 12.5 Audit Logging

**Location:** `app/services/audit/`

All write operations emit audit events:
- `MEMORY_READ`, `MEMORY_WRITE`, `MEMORY_UPDATE`, `MEMORY_DELETE`
- `INGEST_COMPLETED`, `INGEST_FAILED`
- `API_KEY_CREATED`, `API_KEY_REVOKED`, `API_KEY_ROTATED`

---

## Summary Classification Table

| Integration | Status | Evidence |
|-------------|--------|----------|
| MCP Server | DOCUMENTED_ONLY | `app/api/api_keys.py:1-12`, `app/models.py:692-730` |
| Claude Code | IMPLEMENTED | `app/services/connectors.py:295-398` (data format only) |
| Codex | MISSING | No references in `app/` |
| Universal Adapter | MISSING | No references in `app/` |
| LLM Providers | IMPLEMENTED | `app/services/llm.py` (Anthropic, OpenAI, Mock) |
| Object Storage | IMPLEMENTED | `app/services/object_storage*.py` (Local, S3, MinIO) |
| REST API | COMPLETE | 72 endpoints across 14 routers |

---

## Appendix: Health Check Endpoints

| Path | Handler | File:Line |
|------|---------|-----------|
| `/health` | `health` | `app/main.py:276` |
| `/health/live` | `liveness` | `app/main.py:255` |
| `/health/ready` | `readiness` | `app/main.py:260` |

---

*End of forensic audit.*
