# ACTUAL API CONTRACT — SwarmVault WebApp

> Derived from actual backend implementation (FastAPI routers in `app/api/`).
> This is the single source of truth. Frontend consumers must match this.

## Authentication

All endpoints under `/api/v1/*` require JWT Bearer token in `Authorization` header.
Token obtained via `POST /api/v1/auth/login` or `POST /api/v1/auth/register`.
Token refresh: `POST /api/v1/auth/refresh` (public, requires refresh_token body).
Token storage: localStorage key `sv_tokens` → `{ access_token, refresh_token }`.

Token refresh is automatic — `frontend/src/lib/api.ts` handles 401 → refresh → retry.

## Error envelope

All error responses:
```json
{ "error": { "type": "string", "message": "string", "request_id": "string" } }
```

Common status codes: 400, 401, 403, 404, 422, 500.

---

## Endpoints Consumed by Frontend

### 1. Auth

| Property | Value |
|---|---|
| Base URL | `{API_BASE}/api/v1` |
| Auth | Public (register, login, refresh) / Bearer (logout, change-password, me) |

**POST /auth/register**
- Body: `{ email, password, name, workspace_name }`
- Response 201: `{ access_token, refresh_token, token_type, expires_in }`
- Consumer: Auth pages (register form)

**POST /auth/login**
- Body: `{ email, password }`
- Response 200: `{ access_token, refresh_token, token_type, expires_in }`
- Consumer: Auth pages (login form)

**POST /auth/refresh**
- Body: `{ refresh_token }`
- Response 200: `{ access_token, refresh_token, token_type, expires_in }`
- Consumer: `lib/api.ts` (automatic refresh on 401)

**POST /auth/logout**
- Auth: Bearer
- Body: `{ refresh_token }`
- Response 200: `{ detail }`
- Consumer: Settings profile page

**GET /auth/me**
- Auth: Bearer
- Response 200: `{ id, email, name, is_active, email_verified, created_at }`
- Consumer: `useAuth.tsx`

**POST /auth/change-password**
- Auth: Bearer
- Body: `{ current_password, new_password }`
- Response 200: `{ detail }`
- Consumer: Settings profile page

---

### 2. Workspace

**GET /workspace/**
- Auth: Bearer
- Response 200: `{ id, name, slug, tenant_id, description, created_at }`
- Consumer: Dashboard, layout sidebar

**PATCH /workspace/**
- Auth: Bearer (admin role)
- Body: `{ name?, description?, slug?, perm_join?, perm_member_manage? }`
- Response 200: WorkspaceOut
- Consumer: Settings page

**GET /workspace/members**
- Auth: Bearer
- Response 200: `[{ id, workspace_id, user_id, user_name, user_email, role, joined_at, invited_at, expires_at }]`
- Consumer: Settings page

**POST /workspace/members**
- Auth: Bearer (admin role)
- Body: `{ email, role?, message?, invitation_expires? }`
- Response 200: WorkspaceMemberOut
- Consumer: Settings page (invite member)

**PATCH /workspace/members/{member_id}**
- Auth: Bearer (admin role)
- Body: `{ role?, expires? }`
- Response 200: WorkspaceMemberOut
- Consumer: Settings page (change role)

**DELETE /workspace/members/{user_id}**
- Auth: Bearer (admin role)
- Response 204
- Consumer: Settings page (remove member)

---

### 3. Projects

**GET /projects/**
- Auth: Bearer
- Query: none (returns all workspace projects)
- Response 200: `[{ id, workspace_id, name, description, created_at, updated_at }]`
- Consumer: Dashboard, Projects page

**POST /projects/**
- Auth: Bearer (member role)
- Body: `{ name, description? }`
- Response 201: ProjectOut
- Consumer: Dashboard (New Project form)

**GET /projects/{project_id}**
- Auth: Bearer
- Response 200: ProjectOut
- Consumer: Project detail

**PATCH /projects/{project_id}**
- Auth: Bearer (member role)
- Body: `{ name?, description? }`
- Response 200: ProjectOut
- Consumer: Project settings

**DELETE /projects/{project_id}**
- Auth: Bearer (admin role)
- Response 204
- Consumer: Project settings

---

### 4. Sessions

**GET /sessions/**
- Auth: Bearer
- Response 200: `[{ id, workspace_id, user_id, title, extra_metadata, created_at, updated_at }]`
- Note: Backend does NOT support `project_id` query param — returns ALL workspace sessions
- Consumer: Sessions page (project-scoped via frontend filter)

**GET /sessions/{session_id}/history**
- Auth: Bearer
- Response 200: `{ session_id, title, source, messages: [{ id, role, content, created_at }] }`
- Consumer: Session detail page

**POST /sessions/{session_id}/messages**
- Auth: Bearer (member role)
- Body: `{ role, content, metadata? }`
- Response 201: MessageOut
- Consumer: Chat page (post-message)

**POST /sessions/**
- Auth: Bearer (member role)
- Body: `{ title?, extra_metadata? }`
- Response 201: SessionOut
- Consumer: Chat page (new session)

---

### 5. Chat

**POST /chat/**
- Auth: Bearer (viewer role minimum)
- Body: `{ message, session_id?, project_id? }`
- Response 200: `{ message_id, session_id, response, model, usage, memory_ids_used, retrieval_method, retrieval_sources, latency_ms, confidence, provider }`
- Consumer: Chat page (non-streaming fallback)

**POST /chat/stream**
- Auth: Bearer
- Body: `{ message, session_id?, project_id? }`
- Response: SSE stream (text/event-stream)
- Events: `token` (text chunk), `sources` (retrieved memories), `done` (final metadata), `error`
- Consumer: Chat page (streaming via `useChat.tsx` → `streamChat()` in `lib/api.ts`)

---

### 6. Memory

**GET /memory/**
- Auth: Bearer
- Query: `memory_type?, project_id?, temporal_status?, include_deleted?, limit (default 50, max 200), offset (default 0)`
- Response 200: `[{ id, content, memory_type, authority, confidence, temporal_status, created_at, ... }]`
- Consumer: Memory page

**POST /memory/search**
- Auth: Bearer
- Body: `{ query (min 1 char), memory_type?, limit (default 20, max 100) }`
- Response 200: `[{ MemoryOut }]`
- Consumer: Search within memory

---

### 7. Ingest

**POST /ingest/upload**
- Auth: Bearer (member role)
- Body: multipart/form-data: `{ project_id, source_type, title?, content, config? }`
- Response 201: `{ source_id, session_id, status, stage, messages_processed, facts_created, decisions_created, graph_nodes_created, graph_edges_created, topics, entities, message }`
- Consumer: Ingest page

**POST /ingest/**
- Auth: Bearer
- Body: `{ project_id, source_type, config? }`
- Response 201: `{ id, ... }`
- Consumer: Ingest (queue-based)

**GET /ingest/sources**
- Auth: Bearer
- Query: `project_id?, status?, limit (50), offset (0)`
- Response 200: `{ items: SourceOut[], total: number }`
- Consumer: Ingest page (sources list)

**GET /ingest/facts**
- Auth: Bearer
- Query: `project_id?, subject?, temporal_status?, limit (50), offset (0)`
- Response 200: `{ items: FactOut[], total: number }`
- Consumer: Facts page

**GET /ingest/decisions**
- Auth: Bearer
- Query: `project_id?, temporal_status?, limit (50), offset (0)`
- Response 200: `{ items: DecisionOut[], total: number }`
- Consumer: Decisions page

**GET /ingest/graph**
- Auth: Bearer
- Query: `project_id?, include_historical? (default false)`
- Response 200: `{ nodes: GraphNodeOut[], edges: GraphEdgeOut[] }`
- Consumer: Graph page

**GET /ingest/timeline**
- Auth: Bearer
- Query: `project_id?, limit (50, max 200)`
- Response 200: `{ items: TimelineItem[], total: number }`
- Consumer: Timeline page

**POST /ingest/search**
- Auth: Bearer
- Body: `{ query (min 1 char), memory_type?, limit (default 20, max 100) }`
- Response 200: `{ items: SearchResultItem[], total, query }`
- Note: This is POST despite being a search. Accepts JSON body, NOT query params.
- Consumer: Search page

---

### 8. Dashboard

**GET /dashboard/**
- Auth: Bearer
- Response 200: `{ workspace_id, total_memories, total_sources, total_sessions, total_facts, total_decisions, total_graph_nodes, total_graph_edges, recent_memories, recent_sessions, memory_types }`
- Consumer: Dashboard page

---

### 9. Provenance

**GET /provenance/**
- Auth: Bearer (member role)
- Query: `session_id?, project_id?, limit (50, max 200), offset (0)`
- Response 200: `[{ ProvenanceOut }]`
- Consumer: Provenance page

**GET /provenance/{provenance_id}**
- Auth: Bearer
- Response 200: ProvenanceOut
- Consumer: Provenance detail

**GET /provenance/{provenance_id}/memories**
- Auth: Bearer
- Response 200: `[MemoryReferenceOut]`
- Consumer: Provenance detail

---

### 10. Feedback

**POST /feedback/**
- Auth: Bearer (member role)
- Body: `{ provenance_id?, session_id?, rating, comment? }`
- Response 201: FeedbackOut
- Consumer: Chat/provenance pages

**GET /feedback/**
- Auth: Bearer
- Query: `session_id?, limit (50, max 200), offset (0)`
- Response 200: `{ items: FeedbackOut[], total }`
- Consumer: Feedback listing

---

### 11. API Keys

**POST /api-keys/**
- Auth: Bearer (admin role)
- Body: `{ name, description?, expires_at?, metadata? }`
- Response 201: `{ id, name, description, key_prefix, created_at, expires_at, key_extra }` (raw_key returned once only)
- Consumer: Settings API keys page

**GET /api-keys/**
- Auth: Bearer
- Response 200: `[ApiKeyOut]`
- Consumer: Settings API keys page

**DELETE /api-keys/{key_id}**
- Auth: Bearer (admin role)
- Response 204
- Consumer: Settings API keys page

---

### 12. Health (public)

**GET /health/live** → `{ status: "alive" }` (200)
**GET /health/ready** → `{ status: "ready", database: "connected" }` (200) or 503
**GET /health** → `{ status: "ok" }` (200)

---

## Frontend Consumer Map

| Page/Feature | Endpoints Used |
|---|---|
| Auth | POST /auth/register, POST /auth/login, POST /auth/refresh, GET /auth/me, POST /auth/logout, POST /auth/change-password |
| Dashboard | GET /dashboard/, GET /projects/, POST /projects/ |
| Projects | GET /projects/, POST /projects/ |
| Chat | POST /chat/stream, POST /chat/, POST /sessions/, GET /sessions/, POST /sessions/{id}/messages, GET /sessions/{id}/history |
| Memory | GET /memory/ |
| Search | POST /ingest/search |
| Facts | GET /ingest/facts |
| Decisions | GET /ingest/decisions |
| Graph | GET /ingest/graph |
| Timeline | GET /ingest/timeline |
| Ingest | POST /ingest/upload, GET /ingest/sources |
| Provenance | GET /provenance/, GET /provenance/{id}, GET /provenance/{id}/memories |
| Settings | PATCH /workspace/, GET /workspace/members, POST /workspace/members, PATCH /workspace/members/{id}, DELETE /workspace/members/{id}, POST /api-keys/, GET /api-keys/, DELETE /api-keys/{id}, POST /auth/change-password, POST /auth/logout |

## Canonical Data Flow

```
Page Component
  → feature hook (useProjects, useMemory, etc.) OR direct apiGet/apiPost
  → lib/api.ts (request with auto-refresh)
  → fetch() with Bearer token
  → Backend
```

Search page uses direct `fetch()` with `getToken()` — should be migrated to `apiPost` from `lib/api.ts`.
