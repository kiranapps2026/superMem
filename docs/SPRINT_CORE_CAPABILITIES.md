# SwarmVault WebApp — Sprint Core Capabilities Inventory

> **Forensic document** — derived entirely from source-code analysis.
> Generated: 2025-09-05
> Scope: `app/` directory (the operationalized SwarmVault Core in the webapp).

---

## 1. File Inventory

### 1.1 Entrypoint & App Wiring

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI application factory. Defines `app`, mounts all API routers under `/api/v1`, configures middleware (CORS, security headers, request-ID, rate-limit, audit persistence), health-check routes, lifespan hook (`init_db` + audit DB sink registration). |
| `app/db.py` | Database engine, session factory, `init_db()` (create_all). Provides `get_db` dependency. Also holds `async_session_factory` used by audit persistence middleware. |

### 1.2 API Routers (all under `app/api/`)

| File | Prefix | Purpose |
|------|--------|---------|
| `app/api/auth.py` | `/auth` | Registration, login, refresh token, password change, me. Creates Tenant + Workspace on registration. |
| `app/api/workspace.py` | `/workspace` | GET/PATCH workspace, list members, invite, update member role, list/accept/decline invitations. |
| `app/api/projects.py` | `/projects` | CRUD for projects within a workspace. |
| `app/api/sessions.py` | `/sessions` | List, create, get, delete (soft) chat sessions. |
| `app/api/chat.py` | `/chat` | `POST /` (single response) and `POST /stream` (SSE streaming). Orchestrates retrieval → LLM → provenance. |
| `app/api/memory.py` | `/memory` | Full CRUD + search on Memory records. Delegates to `MemoryService`. |
| `app/api/ingest.py` | `/ingest` | Content-hash-dedup ingestion upload, legacy queued job creation, sources CRUD, facts listing, decisions listing, knowledge graph query, timeline, M5 hybrid search, jobs CRUD. |
| `app/api/provenance.py` | `/provenance` | List provenance records for a workspace (filterable by session/project). |
| `app/api/feedback.py` | `/feedback` | Thumbs up/down on chat responses. |
| `app/api/api_keys.py` | `/api-keys` | CRUD + rotation for MCP server API keys. |
| `app/api/storage.py` | `/storage` | Upload/download/delete/list with content-hash dedup. Pluggable backends (local, S3, MinIO). |
| `app/api/policy.py` | `/policy` | Policy CRUD, version listing, activate version, default policy generation. |
| `app/api/audit.py` | `/audit` | Read-only audit event listing, single event, correlation trace by request_id. |
| `app/api/dashboard.py` | `/dashboard` | Workspace-level aggregated overview + per-project dashboard. |

### 1.3 Core Service Layer (M0–M5 + infrastructure)

| File | Purpose |
|------|---------|
| `app/services/connectors.py` | **M0** — Connector registry. 7 connectors: ChatGPT, Claude, Claude Code (JSONL), Generic JSON, JSONL, Markdown, Plain Text. Each implements `detect`, `validate`, `parse` returning `NormalizedConversation` / `NormalizedMessage`. Registry has auto-detection via confidence scoring. Size limits enforced (10 MB input, 100 KB/message, 10k messages). |
| `app/services/m1_session.py` | **M1** — Session understanding. Extracts topics (10 keyword categories), entities (tech stack + project names), intents (how_to, decision_making, debugging, building, review). Optional LLM summary. Outputs `SessionUnderstanding` dataclass. |
| `app/services/m2_facts.py` | **M2** — Deterministic fact + decision extraction via regex patterns. Facts are subject-predicate-object triples. Decisions are choice/commitment statements. In-message dedup via normalized key. Exports `run_m2()` used by pipeline. |
| `app/services/m3_temporal.py` | **M3** — Temporal supersession. `supersede_fact()` and `supersede_decision()` mark old current records as `historical` and create new `current` ones. `get_current_facts()` / `get_current_decisions()` for querying. |
| `app/services/m4_graph.py` | **M4** — Graph element extraction and persistence. Regex-based relationship detection (uses, connects_to, depends_on, is_a). Node classification (technology / project / entity). Dedup on existing nodes/edges. Persists via `persist_graph()`. |
| `app/services/m5_retrieval.py` | **M5** — Multi-factor retrieval and ranking. BM25 keyword scoring, recency decay (30-day half-life), graph connectivity score, authority/confidence/temporal weighting. `rank_facts()`, `rank_decisions()`, `retrieve_hybrid()`, `retrieve_for_chat()`. |
| `app/services/pipeline.py` | **Orchestrator** — Runs M0→M1→M2→M3→M4→M5 as a single async pipeline. Stages tracked on `Source` model. Content-hash dedup at entry. Inline M3 supersession in the pipeline loop. |
| `app/services/memory.py` | **MemoryService** — Governed memory API with PostgreSQL persistence. Full CRUD + search + supersede + expire + share/revoke + provenance + history + explain. Policy-gated, audit-emitting, cross-tenant isolation. In-memory cache for fast reads. `MemoryRecord` dataclass is the canonical data model. `MemoryTypeMapper` bridges canonical ↔ vault types. |
| `app/services/llm.py` | **LLM abstraction** — `LLMProvider` ABC with `AnthropicProvider`, `OpenAIProvider`, `MockProvider`. Factory `get_llm_provider()` with timeout+retry wrapper. Backward-compat `chat_completion()` function. |
| `app/services/chat_orchestrator.py` | **Chat orchestration** — `process_chat()`: retrieve via M5 → build messages → call LLM → record provenance. Confidence scoring. Returns full result dict. |
| `app/services/retrieval.py` | **Hybrid retrieval** — `retrieve_memories()` (memory-specific, hybrid vector+keyword scoring), `_hybrid_score()`, `_keyword_score()`, `_cosine_similarity()`. |
| `app/services/object_storage.py` | **Object storage** — `StorageProvider` ABC with `LocalStorageProvider`. Pluggable: S3, MinIO. Key derivation from content hash. Path traversal protection. |
| `app/services/audit/` | **Audit subsystem** — See §1.4 below. |
| `app/services/policy/` | **Policy subsystem** — See §1.5 below. |

### 1.4 Audit Subsystem (`app/services/audit/`)

| File | Purpose |
|------|---------|
| `app/services/audit/constants.py` | Effect/result/decision constants (`EFFECT_ALLOW`, `RESULT_SUCCESS`, `POLICY_DENY`, etc.), sensitive field list, audit field list. |
| `app/services/audit/service.py` | `AuditService` — emit() (sync, accumulates events) + persist(session) (async, flushes to DB). Supports multiple sinks (log, DB). Redacts sensitive fields. |
| `app/services/audit/repository.py` | `AuditRepository` — async DB operations for `AuditEvent` model. Append-only semantics (insert only). Tenant isolation + time-range filtering. |
| `app/services/audit/sink.py` | **Does not exist** — sink logic is inline in `service.py`. |

### 1.5 Policy Subsystem (`app/services/policy/`)

| File | Purpose |
|------|---------|
| `app/services/policy/engine.py` | `PolicyEngine` — core authorization engine. Evaluates structured policy rules (resource, action, effect, conditions). DENY-wins evaluation. Supports effects: allow, deny, require_confirmation, allow_with_limits, allow_redacted. Role hierarchy: owner > admin > member > viewer. `check_role_minimum()`, `default_tenant_policies()`. |
| `app/services/policy/evaluator.py` | RBAC policy generation from permission matrix. `generate_rbac_policies()` → list of policy dicts. `evaluate_rbac()` for exact-action matching. `build_auth_request()` helper. |
| `app/services/policy/repository.py` | `PolicyRepository` — loads active policies from PostgreSQL `policies` + `policy_versions` tables. In-memory caching. Fail-closed: no policies = deny-all. |
| `app/services/policy/dependencies.py` | FastAPI dependency factories: `require_policy()`, `require_policy_with_id()`. Singleton engine. Translates TenantContext → AuthorizationRequest → RBAC evaluation → 403 on deny. |

### 1.6 Middleware (`app/middleware/`)

| File | Purpose |
|------|---------|
| `app/middleware/auth.py` | JWT authentication dependency. Validates access tokens, loads user + workspace membership. |
| `app/middleware/tenancy.py` | `TenantContext` — extracts tenant/workspace/user/role from request. `get_tenant_context` dependency. |
| `app/middleware/rbac.py` | `require_min_role()` — role hierarchy check via PolicyEngine. |
| `app/middleware/rate_limit.py` | Rate limiting middleware (disabled in tests via `_disabled_for_testing`). |

### 1.7 Core Utilities

| File | Purpose |
|------|---------|
| `app/core/config.py` | Pydantic `Settings` — all env vars: DB URL, JWT secrets, LLM provider/model, CORS, storage path/backend, rate limits, etc. |
| `app/core/security.py` | Password hashing, JWT encode/decode, token expiry. |

### 1.8 Models & Schemas

| File | Purpose |
|------|---------|
| `app/models.py` | SQLAlchemy ORM models — all database tables. |
| `app/schemas.py` | Pydantic schemas for request/response validation. |

### 1.9 CLI / Scripts

**No `scripts/` directory exists in this repository.** There is no `swarmvault.py` CLI entry point, no `swarmvault_*.py` modules, no `__main__.py`, and no `cli.py`. The entire "SwarmVault Core" has been inlined into the FastAPI web application under `app/`.

The earlier forensics spec anticipated a CLI-first architecture with M0–M5 modules. The actual codebase operationalizes those modules as a backend service with a REST API.

---

## 2. Data Models

### 2.1 ORM Models (`app/models.py`)

| Table | Key Fields | Purpose |
|-------|-----------|---------|
| `tenants` | id, name, slug, plan | Top-level org unit. |
| `workspaces` | id, tenant_id, name, slug, description, deleted_at | Workspace within a tenant. |
| `users` | id, email, hashed_password, is_active, deleted_at | User accounts. |
| `workspace_members` | id, workspace_id, user_id, role (owner/admin/member/viewer) | RBAC membership. |
| `invitations` | id, workspace_id, email, role, state, expires_at | Pending workspace invites. |
| `sessions` | id, workspace_id, user_id, title, extra_metadata, deleted_at | Chat sessions. |
| `messages` | id, session_id, role, content, metadata | Individual chat messages. |
| `sources` | id, workspace_id, tenant_id, project_id, source_type, external_id, title, status, stage (M0–M5), progress, message_count, content_hash, error_message, config | Ingestion source tracking. |
| `normalized_messages` | id, source_id, session_id, message_index, external_id, role, content, extra_metadata, timestamp | M0-normalized messages. |
| `facts` | id, workspace_id, project_id, source_id, session_id, subject, predicate, object, content, confidence, authority, temporal_status (current/historical), status, deleted_at | M2-extracted facts. |
| `decisions` | id, workspace_id, project_id, source_id, session_id, content, context, confidence, authority, temporal_status, status, deleted_at | M2-extracted decisions. |
| `graph_nodes` | id, workspace_id, project_id, external_id, label, node_type, properties, temporal_status, deleted_at | M4 graph nodes. |
| `graph_edges` | id, workspace_id, project_id, source_node_id, target_node_id, relationship_type, confidence, temporal_status, source_id, deleted_at | M4 graph edges. |
| `memories` | id, tenant_id, workspace_id, user_id, agent_id, run_id, project_id, memory_type, content, extra_metadata, temporal_status, confidence, authority, deleted_at, created_at, updated_at | MemoryService-backed memories (PostgreSQL). |
| `memory_provenance` | id, workspace_id, session_id, project_id, model, provider, retrieval_method, memory_ids_used, retrieval_sources, user_message_preview, prompt_tokens, completion_tokens, total_tokens, latency_ms, confidence | Chat provenance records. |
| `message_feedback` | id, session_id, message_id, user_id, feedback (thumbs_up/down), comment | User feedback on responses. |
| `api_keys` | id, workspace_id, user_id, name, key_hash, scopes, last_used_at, expires_at | MCP API keys (hashed). |
| `policies` | id, tenant_id, name, description, status, current_version | Policy definitions. |
| `policy_versions` | id, policy_id, version, rules (JSON), status | Policy versioned rules. |
| `audit_events` | id, tenant_id, event_type, principal_id, principal_type, resource_type, resource_id, action, result_status, decision, risk, request_id, duration_ms, metadata, timestamp | Immutable audit log. |
| `ingest_jobs` | id, workspace_id, project_id, source_type, status, stage, progress, error_message, config | Legacy ingestion jobs. |
| `refresh_tokens` | id, user_id, token_hash, expires_at | JWT refresh tokens. |

### 2.2 Canonical Data Classes (in-memory / service layer)

| Class | Location | Purpose |
|-------|----------|---------|
| `MemoryRecord` | `app/services/memory.py` | Canonical memory representation with full lifecycle fields (versioning, provenance chain, permissions, temporal status, user_metadata). |
| `MemoryTypeMapper` | `app/services/memory.py` | Maps canonical memory types (WORKING, EPISODIC, SEMANTIC, PROCEDURAL, USER, TEAM, PROJECT, AGENT) to vault types. |
| `NormalizedConversation` | `app/services/connectors.py` | M0 output — normalized conversation with messages. |
| `NormalizedMessage` | `app/services/connectors.py` | M0 output — single normalized message. |
| `SessionUnderstanding` | `app/services/m1_session.py` | M1 output — summary, topics, intents, entities. |
| `Fact` (extraction) | `app/services/m2_facts.py` | M2 extraction output — subject/predicate/object triple. |
| `Decision` (extraction) | `app/services/m2_facts.py` | M2 extraction output — decision text + context. |
| `RetrievalResult` | `app/services/m5_retrieval.py` | M5 output — scored item with factor breakdown. |
| `AuthorizationRequest` | `app/services/policy/engine.py` | Policy evaluation input. |
| `PolicyDecision` | `app/services/policy/engine.py` | Policy evaluation output. |

---

## 3. Storage Architecture

### 3.1 PostgreSQL (primary, durable)

All operational state lives in PostgreSQL via SQLAlchemy ORM:

- **Multi-tenant isolation**: Every table has `workspace_id` + (where applicable) `tenant_id`. Soft delete via `deleted_at`.
- **Temporal tracking**: `temporal_status` column on facts, decisions, graph nodes/edges, and memories (values: `current`, `historical`, `expired`, `deleted`).
- **Content-hash dedup**: `sources.content_hash` (SHA-256, first 16 chars) prevents re-processing identical content.
- **Audit log**: Append-only `audit_events` table — never updated or deleted.

### 3.2 In-Memory Cache (performance optimization only)

- `MemoryService._cache`: dict of `memory_id → MemoryRecord`. Not the source of truth.
- `PolicyRepository._cache`: cached loaded policies. Timestamp-based invalidation.

### 3.3 Object Storage (files)

- Pluggable backends: local filesystem (default), S3, MinIO.
- Files keyed by content hash (`{hash[:2]}/{hash}{ext}`).
- Used for file uploads via `/api/v1/storage`.

### 3.4 No CAS / Content-Addressable Store

There is **no content-addressable storage layer** (no "CAS" in the sense of a dedup store keyed by content hash for general objects). Content hashing is used only for:
1. Ingestion dedup (`sources.content_hash`)
2. Object storage dedup keys
3. Message external IDs

---

## 4. Module Dependency Graph

```
app/main.py
  ├── app/api/* (all routers)
  │     ├── app/services/memory.py (MemoryService)
  │     │     ├── app/services/policy/engine.py (PolicyEngine)
  │     │     ├── app/services/audit/ (AuditService via emit)
  │     │     └── app/models.py (Memory ORM)
  │     ├── app/services/chat_orchestrator.py
  │     │     ├── app/services/m5_retrieval.py
  │     │     │     └── app/models.py (Fact, Decision, GraphEdge)
  │     │     ├── app/services/llm.py
  │     │     └── app/models.py (MessageProvenance)
  │     ├── app/services/pipeline.py
  │     │     ├── app/services/connectors.py (M0)
  │     │     ├── app/services/m1_session.py (M1)
  │     │     ├── app/services/m2_facts.py (M2)
  │     │     ├── app/services/m3_temporal.py (M3)
  │     │     ├── app/services/m4_graph.py (M4)
  │     │     └── app/models.py (Source, Fact, Decision, GraphNode, GraphEdge)
  │     ├── app/services/policy/evaluator.py
  │     │     └── app/services/policy/engine.py
  │     ├── app/services/policy/repository.py
  │     │     └── app/models.py (Policy, PolicyVersion)
  │     ├── app/services/audit/service.py
  │     │     └── app/services/audit/repository.py
  │     │           └── app/models.py (AuditEvent)
  │     └── app/services/object_storage.py
  │           └── app/core/config.py
  ├── app/middleware/* (auth, tenancy, rbac, rate_limit)
  └── app/services/audit/service.py (AuditService singleton)
        └── app/db.py (async_session_factory for persist)
```

### 4.1 M0–M5 Pipeline Data Flow

```
M0: connectors.normalize() → NormalizedConversation
  ↓
M1: m1_session.understand_session() → SessionUnderstanding
  ↓
M2: m2_facts.run_m2() → (facts, decisions) as dataclasses
  ↓
M3: m3_temporal.supersede_fact/decision() → marks old as historical
  ↓
M4: m4_graph.extract_graph_elements() + persist_graph() → GraphNode + GraphEdge rows
  ↓
M5: m5_retrieval.retrieve_hybrid() → ranked RetrievalResult list (at query time, no index)
```

### 4.2 Chat Data Flow

```
User message
  → retrieve_for_chat() [M5 hybrid: facts + decisions]
  → LLM provider (Anthropic/OpenAI/Mock)
  → MessageProvenance record
  → Assistant message
```

---

## 5. CLI Command Inventory

**There are no CLI commands.** No Click/Typer/argparse CLI entry points exist. All functionality is exposed via the FastAPI REST API under `/api/v1/`.

The architecture documents reference a CLI tool (`swarmvault graph query`, `swarmvault task start`, etc.) but this does not exist in the current codebase. Those capabilities are aspirational and not implemented.

---

## 6. API Endpoint Inventory

### 6.1 All Registered Routes

| Method | Path | Handler File | Auth | Purpose |
|--------|------|-------------|------|---------|
| POST | `/api/v1/auth/register` | auth | None | Register user + create tenant/workspace |
| POST | `/api/v1/auth/login` | auth | None | Login, return JWT tokens |
| POST | `/api/v1/auth/refresh` | auth | None | Refresh access token |
| POST | `/api/v1/auth/change-password` | auth | JWT | Change password |
| GET | `/api/v1/auth/me` | auth | JWT | Current user profile |
| GET | `/api/v1/workspace/` | workspace | JWT | Get workspace |
| PATCH | `/api/v1/workspace/` | workspace | JWT+admin | Update workspace |
| GET | `/api/v1/workspace/members` | workspace | JWT+member | List members |
| POST | `/api/v1/workspace/members/invite` | workspace | JWT+admin | Invite member |
| PATCH | `/api/v1/workspace/members/{id}` | workspace | JWT+admin | Update member role |
| GET | `/api/v1/workspace/invitations` | workspace | JWT | List invitations |
| POST | `/api/v1/workspace/invitations/{id}/accept` | workspace | JWT | Accept invitation |
| POST | `/api/v1/workspace/invitations/{id}/decline` | workspace | JWT | Decline invitation |
| GET | `/api/v1/projects/` | projects | JWT | List projects |
| POST | `/api/v1/projects/` | projects | JWT+member | Create project |
| GET | `/api/v1/projects/{id}` | projects | JWT | Get project |
| PATCH | `/api/v1/projects/{id}` | projects | JWT+member | Update project |
| DELETE | `/api/v1/projects/{id}` | projects | JWT+admin | Delete project |
| GET | `/api/v1/sessions/` | sessions | JWT | List sessions |
| POST | `/api/v1/sessions/` | sessions | JWT+member | Create session |
| GET | `/api/v1/sessions/{id}` | sessions | JWT | Get session |
| DELETE | `/api/v1/sessions/{id}` | sessions | JWT+owner | Soft-delete session |
| POST | `/api/v1/chat/` | chat | JWT | Send chat message (single response) |
| POST | `/api/v1/chat/stream` | chat | JWT | SSE streaming chat |
| POST | `/api/v1/memory/` | memory | JWT+policy(memory,write) | Create memory |
| GET | `/api/v1/memory/` | memory | JWT | List memories |
| GET | `/api/v1/memory/{id}` | memory | JWT+policy | Get memory |
| PATCH | `/api/v1/memory/{id}` | memory | JWT+member | Update memory |
| DELETE | `/api/v1/memory/{id}` | memory | JWT+owner+policy | Delete memory |
| POST | `/api/v1/memory/search` | memory | JWT+policy | Full-text search memories |
| POST | `/api/v1/ingest/upload` | ingest | JWT+member | Upload content for ingestion (with dedup) |
| POST | `/api/v1/ingest/` | ingest | JWT+member | Legacy: create queued ingest job |
| GET | `/api/v1/ingest/sources` | ingest | JWT | List sources |
| GET | `/api/v1/ingest/sources/{id}` | ingest | JWT | Get source detail |
| GET | `/api/v1/ingest/sources/{id}/messages` | ingest | JWT | Get normalized messages |
| GET | `/api/v1/ingest/facts` | ingest | JWT | List facts |
| GET | `/api/v1/ingest/facts/{id}` | ingest | JWT | Get fact |
| GET | `/api/v1/ingest/decisions` | ingest | JWT | List decisions |
| GET | `/api/v1/ingest/decisions/{id}` | ingest | JWT | Get decision |
| GET | `/api/v1/ingest/graph` | ingest | JWT | Get knowledge graph (nodes + edges) |
| GET | `/api/v1/ingest/timeline` | ingest | JWT | Chronological timeline |
| POST | `/api/v1/ingest/search` | ingest | JWT | M5 hybrid search |
| GET | `/api/v1/ingest/jobs` | ingest | JWT | List ingest jobs |
| GET | `/api/v1/ingest/jobs/{id}` | ingest | JWT | Get ingest job |
| GET | `/api/v1/provenance/` | provenance | JWT+member | List provenance records |
| POST | `/api/v1/feedback/` | feedback | JWT+member | Create feedback |
| GET | `/api/v1/feedback/` | feedback | JWT | List feedback |
| POST | `/api/v1/api-keys/` | api_keys | JWT+admin | Create API key |
| GET | `/api/v1/api-keys/` | api_keys | JWT+member | List API keys |
| DELETE | `/api/v1/api-keys/{id}` | api_keys | JWT+admin | Revoke API key |
| POST | `/api/v1/api-keys/{id}/rotate` | api_keys | JWT+admin | Rotate API key |
| POST | `/api/v1/storage/upload` | storage | JWT+member | Upload file |
| GET | `/api/v1/storage/` | storage | JWT+viewer | List files |
| GET | `/api/v1/storage/{key}` | storage | JWT+viewer | Download file |
| DELETE | `/api/v1/storage/{key}` | storage | JWT+admin | Delete file |
| GET | `/api/v1/storage/{key}/presign` | storage | JWT | Presigned URL |
| GET | `/api/v1/policy/` | policy | JWT | List policies |
| POST | `/api/v1/policy/` | policy | JWT+admin | Create policy |
| GET | `/api/v1/policy/{id}` | policy | JWT | Get policy |
| PATCH | `/api/v1/policy/{id}` | policy | JWT+admin | Update policy |
| GET | `/api/v1/policy/{id}/versions` | policy | JWT | List policy versions |
| POST | `/api/v1/policy/{id}/versions` | policy | JWT+admin | Create policy version |
| POST | `/api/v1/policy/{id}/versions/{v}/activate` | policy | JWT+admin | Activate version |
| POST | `/api/v1/policy/defaults` | policy | JWT+admin | Generate default policies |
| GET | `/api/v1/audit/events` | audit | JWT+admin | List audit events |
| GET | `/api/v1/audit/events/{id}` | audit | JWT+admin | Get audit event |
| GET | `/api/v1/audit/trace/{req_id}` | audit | JWT+admin | Correlation trace |
| GET | `/api/v1/dashboard/` | dashboard | JWT | Workspace overview |
| GET | `/api/v1/dashboard/projects/{id}` | dashboard | JWT | Project dashboard |
| GET | `/health/live` | main | None | Liveness probe |
| GET | `/health/ready` | main | None | Readiness probe (DB check) |
| GET | `/health` | main | None | Health check |

---

## 7. MCP Tool Inventory

**There is no MCP server implementation in this codebase.** The API keys endpoint (`/api/v1/api-keys/`) is prepared for MCP server registration, but no MCP tool definitions, MCP server, or tool-exposure layer exists.

The API key model (`ApiKey`) stores `scopes` and `name` fields designed for MCP server identity, but they are not wired to any tool-routing mechanism.

---

## 8. Frontend Redesign Plan Claims vs. Reality

The `docs/FRONTEND_REDESIGN_PLAN.md` likely claims capabilities that do not exist in the backend. Based on the actual code:

### 8.1 What the Plan Claims That Does NOT Exist

| Claimed Capability | Reality |
|--------------------|---------|
| `swarmvault` CLI with subcommands (`graph query`, `task start`, etc.) | No CLI exists. All operations are REST API. |
| MCP server with tool definitions | No MCP server. API keys endpoint exists but is unused. |
| CAS (Content-Addressable Storage) | No CAS. PostgreSQL is the primary store. Content hashing is used for dedup only. |
| Graph query language / graph traversal API | Graph endpoints return flat node+edge lists. No query language. |
| Incremental pipeline / watch mode | Pipeline is synchronous and request-driven. No file watcher or incremental mode. |
| Checkpoint / recovery | No checkpoint mechanism. Pipeline runs atomically per request. |
| Archive / backup subsystem | No backup or archive subsystem. PostgreSQL is the sole durable store. |
| Timeline as a first-class module | Timeline is a composite query in `ingest.py`, not a standalone module. |
| Dedup as a standalone service | Dedup is inline in pipeline + ingest upload (content_hash on Source). |
| Scoring/trust as a standalone service | Scoring is inline in M5 retrieval and MemoryService authority field. |
| Trace as a standalone module | Trace is a correlation query in `audit.py` (by request_id). |
| Procedures module | No procedures module. |
| Storage as a standalone module with metadata | Object storage exists but is for file uploads, not knowledge metadata. |

### 8.2 What the Core Has That the WebApp Backend Does NOT Expose

| Core Capability | Not Exposed Via |
|-----------------|-----------------|
| `MemoryService.share()` / `revoke()` — memory sharing between principals | No API endpoint |
| `MemoryService.supersede()` — version-based memory replacement | No API endpoint |
| `MemoryService.expire()` — time-based memory expiration | No API endpoint (only inline in pipeline M3) |
| `MemoryService.explain()` — full explanation with provenance + history + permissions | No API endpoint |
| `MemoryService.provenance()` — per-memory provenance chain | No API endpoint (provenance API only covers MessageProvenance for chat) |
| `MemoryService.history()` — version history per memory | No API endpoint |
| `MemoryTypeMapper` — canonical ↔ vault type mapping | Not exposed (used internally in MemoryService) |
| `MemoryRecord.user_metadata` — arbitrary user metadata on memories | Partially exposed (set on create, not separately manageable) |
| Policy version activation | Exposed (`POST /policy/{id}/versions/{v}/activate`) |
| Default policy generation | Exposed (`POST /policy/defaults`) |
| Connector registry listing | Not exposed via API |
| Policy RBAC permission matrix | Not exposed via API |
| Audit event emission programmatically | Only via internal `emit()` calls, no external trigger |

---

## 9. Key Findings

### 9.1 What "SwarmVault Core" Actually Is

The SwarmVault Core is not a separate CLI tool or library. It is the set of service modules under `app/services/` that implement the M0–M5 pipeline, memory governance, policy engine, audit logging, and retrieval. These are wired into a FastAPI application.

### 9.2 No Scripts Directory

The forensics task assumed `scripts/swarmvault.py` exists. It does not. The entire codebase is a web application.

### 9.3 M0–M5 Is Functional but Not Complete

- **M0** (normalization): 7 connectors, all functional.
- **M1** (session understanding): Regex-based, optional LLM summary. Functional.
- **M2** (fact/decision extraction): Regex-based, deterministic. Functional.
- **M3** (temporal supersession): Implemented but only used inline in pipeline. Standalone module exists.
- **M4** (graph): Extraction + persistence functional. Dedup on existing nodes/edges.
- **M5** (retrieval): Multi-factor scoring functional for facts and decisions. Memory scoring is simpler (hybrid vector+keyword in `retrieval.py`).

### 9.4 Memory Model vs. Fact/Decision Model

There are **two parallel knowledge representations**:
1. **Fact/Decision** (M2 output): Stored in `facts`/`decisions` tables, subject-predicate-object triples. Used by M5 retrieval for chat grounding.
2. **Memory** (MemoryService): Stored in `memories` table, generic content with type/scope/authority/confidence. Used by the `/memory` API.

The chat orchestrator uses M5 retrieval (facts + decisions) for grounding, NOT the Memory model. The Memory model is for direct CRUD via `/memory` endpoints.

### 9.5 Policy Engine Is Fully Wired

The Policy Engine is used by:
- `MemoryService` (every CRUD operation)
- `require_policy()` dependency (used by memory endpoints)
- `require_min_role()` dependency (used by most mutations)
- `Policy API` (for management)

Default tenant policies are generated automatically and cover memory, project, chat, ingest, tools, API keys, and admin restrictions.

### 9.6 Audit Is Eventual, Not Synchronous

Audit events are emitted synchronously (buffered in memory) but persisted asynchronously after each request via `AuditPersistenceMiddleware`. DB failures in audit persistence never block the response.

### 9.7 SSE Streaming Contract

The chat streaming endpoint (`POST /chat/stream`) emits SSE events with types: `token`, `sources`, `done`, `error`. Sources include memory_id, content preview, memory_type, and score.

---

## 10. Dependencies Between Core Modules

```
connectors (M0) ←── pipeline
    ↓
m1_session (M1) ←── pipeline
    ↓
m2_facts (M2) ←── pipeline
    ↓
m3_temporal (M3) ←── pipeline (inline), m3_temporal.py (standalone)
    ↓
m4_graph (M4) ←── pipeline
    ↓
m5_retrieval (M5) ←── chat_orchestrator, ingest search
    ↑
memory.py (MemoryService) ←── standalone, used by memory API
    ↑
llm.py ←── chat_orchestrator
policy/ ←── memory.py, rbac middleware, policy dependencies
audit/ ←── memory.py, main (persistence middleware)
object_storage.py ←── storage API
retrieval.py ←── chat API (retrieve_memories for streaming)
```

---

*End of inventory.*
