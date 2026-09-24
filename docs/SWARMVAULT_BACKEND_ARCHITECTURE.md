# SwarmVault Backend Runtime Architecture

**Document Type**: Forensic reconciliation – documentation only, no code changes
**Baseline SHA**: `e6f4b1c157afaed052584963b942ea04f9661610`
**Date**: 2026-09-10
**Agent**: Agent 1 – BACKEND RUNTIME ARCHITECTURE

---

## Table of Contents

1. [Application Startup](#1-application-startup)
2. [Router Inventory](#2-router-inventory)
3. [Service Inventory](#3-service-inventory)
4. [SQLAlchemy Models](#4-sqlalchemy-models)
5. [Middleware Stack](#5-middleware-stack)
6. [Configuration](#6-configuration)
7. [Dependency Injection](#7-dependency-injection)
8. [Authentication](#8-authentication)
9. [Authorization (RBAC)](#9-authorization-rbac)
10. [Tenancy](#10-tenancy)
11. [Database Access](#11-database-access)
12. [Background Processing](#12-background-processing)
13. [External Providers](#13-external-providers)
14. [Error Handling](#14-error-handling)
15. [Logging](#15-logging)
16. [Observability](#16-observability)
17. [Health/Readiness](#17-healthreadiness)
18. [Runtime Dependencies](#18-runtime-dependencies)
19. [Representative Request Traces](#19-representative-request-traces)

---

## 1. Application Startup

### 1.1 FastAPI App Construction (`app/main.py`)

The application is built as a standard FastAPI app. Key construction points:

- **App instance** is created with title/description metadata.
- **CORS middleware** is applied first via `CORSMiddleware`, reading allowed origins from configuration (`settings.cors_origins`). This is the only `add_middleware` call; all other middleware uses the decorator/factory pattern described below.
- **Router registration**: Multiple routers are included with distinct URL prefixes.
- **Lifespan handler** manages startup/shutdown. Startup initializes:
  - Database engine and session factory (`app/db.py`)
  - Object storage backend (`services/object_storage.py`)
  - LLM provider singleton (`services/llm.py`)
  - Memory service (`services/memory.py`)
  - Audit service (`services/audit/service.py`)
  - Policy engine (`services/policy/engine.py`)
  - Graph/repository singletons
- **Exception handlers** are registered for:
  - `RequestValidationError` (Pydantic validation failures)
  - Generic `Exception` (fail-closed catch-all)
  - `HTTPException` (standard FastAPI HTTP errors)

### 1.2 Middleware Stack Order

The middleware stack (outermost to innermost):

1. `SecurityHeadersMiddleware` – injects security headers on every response
2. `RequestIdMiddleware` – generates/propagates `X-Request-ID`
3. `AuditPersistenceMiddleware` – logs request/response pairs for audit trail
4. `RateLimitMiddleware` – per-key sliding-window rate limiting
5. *(inner) FastAPI routing + CORSMiddleware*

Each middleware is applied using the `@app.middleware("http")` decorator pattern in their respective module files.

### 1.3 Lifespan Flow

```
startup:
  ├── init_engine()        → create_async_engine(settings.database_url)
  ├── init_session_factory() → async_sessionmaker(bind=engine)
  ├── init_storage()       → ObjectStorageFactory.create()
  ├── init_llm()           → LLMProviderFactory.create()
  ├── init_memory()        → MemoryService(...)
  ├── init_audit()         → AuditService(...)
  └── init_policy()        → PolicyEngine(...)

shutdown:
  ├── dispose engine
  └── close storage client
```

---

## 2. Router Inventory

All routers live under `app/api/`. Each is an `APIRouter` with prefix, tags, and dependencies.

| Router File | Prefix | Tags | Key Dependencies |
|---|---|---|---|
| `auth.py` | `/api/v1/auth` | `auth` | – |
| `workspace.py` | `/api/v1/workspace` | `workspace` | `get_tenant_context` |
| `projects.py` | `/api/v1/projects` | `projects` | `get_tenant_context` |
| `sessions.py` | `/api/v1/sessions` | `sessions` | `get_tenant_context` |
| `chat.py` | `/api/v1/chat` | `chat` | `get_tenant_context`, `get_memory_service` |
| `memory.py` | `/api/v1/memory` | `memory` | `get_tenant_context` |
| `ingest.py` | `/api/v1/ingest` | `ingest` | `get_tenant_context` |
| `provenance.py` | `/api/v1/provenance` | `provenance` | `get_tenant_context` |
| `api_keys.py` | `/api/v1/api-keys` | `api-keys` | `get_tenant_context` |
| `policy.py` | `/api/v1/policy` | `policy` | `get_tenant_context` |
| `audit.py` | `/api/v1/audit` | `audit` | `get_tenant_context` |
| `storage.py` | `/api/v1/storage` | `storage` | `get_tenant_context` |
| `dashboard.py` | `/api/v1/dashboard` | `dashboard` | `get_tenant_context` |
| `feedback.py` | `/api/v1/feedback` | `feedback` | `get_tenant_context` |

### 2.1 Auth Router (`app/api/auth.py`)

- `POST /register` – creates User + Workspace, returns tokens
- `POST /login` – validates credentials, returns access + refresh JWT
- `POST /refresh` – rotates refresh token, returns new access token
- `POST /logout` – revokes refresh token
- `POST /forgot-password` – initiates password reset flow
- `POST /reset-password` – completes password reset via token
- `GET /me` – returns current user profile

Schemas used: `UserRegister`, `UserLogin`, `TokenResponse`, `PasswordReset`, `UserResponse`

### 2.2 Workspace Router (`app/api/workspace.py`)

- `GET /` – list user's workspaces
- `POST /` – create workspace
- `GET /{workspace_id}` – get workspace detail
- `PUT /{workspace_id}` – update workspace
- `DELETE /{workspace_id}` – soft-delete workspace
- `POST /{workspace_id}/invite` – invite user by email
- `POST /{workspace_id}/members/{user_id}/role` – change member role
- `DELETE /{workspace_id}/members/{user_id}` – remove member

Schemas used: `WorkspaceCreate`, `WorkspaceResponse`, `WorkspaceUpdate`, `InvitationCreate`, `MemberRoleUpdate`

### 2.3 Projects Router (`app/api/projects.py`)

- `GET /` – list projects in workspace
- `POST /` – create project
- `GET /{project_id}` – get project detail
- `PUT /{project_id}` – update project
- `DELETE /{project_id}` – delete project
- `GET /{project_id}/stats` – project statistics

Schemas used: `ProjectCreate`, `ProjectResponse`, `ProjectUpdate`

### 2.4 Sessions Router (`app/api/sessions.py`)

- `GET /` – list sessions in project
- `POST /` – create session
- `GET /{session_id}` – get session with messages
- `PUT /{session_id}` – update session metadata
- `DELETE /{session_id}` – delete session
- `POST /{session_id}/messages` – add message to session

Schemas used: `SessionCreate`, `SessionResponse`, `MessageCreate`, `MessageResponse`

### 2.5 Chat Router (`app/api/chat.py`)

- `POST /completions` – streaming chat completion with memory retrieval
- `POST /completions/stream` – SSE streaming endpoint
- `POST /memory/search` – semantic memory search
- `POST /memory/ingest` – trigger memory ingestion

Schemas used: `ChatRequest`, `ChatResponse`, `StreamingChatRequest`, `MemorySearchRequest`

### 2.6 Memory Router (`app/api/memory.py`)

- `GET /` – list memories
- `POST /` – create/upsert memory
- `GET /{memory_id}` – get memory detail
- `PUT /{memory_id}` – update memory
- `DELETE /{memory_id}` – delete memory
- `GET /entities` – list extracted entities
- `GET /relations` – list relations between entities

Schemas used: `MemoryCreate`, `MemoryResponse`, `MemoryUpdate`, `EntityResponse`, `RelationResponse`

### 2.7 Ingest Router (`app/api/ingest.py`)

- `POST /` – submit ingestion job
- `GET /` – list ingestion jobs
- `GET /{job_id}` – get job status
- `POST /{job_id}/cancel` – cancel running job
- `POST /{job_id}/retry` – retry failed job

Schemas used: `IngestRequest`, `IngestJobResponse`, `IngestJobStatus`

### 2.8 Provenance Router (`app/api/provenance.py`)

- `GET /sources/{source_id}/provenance` – full provenance chain for a source
- `GET /messages/{message_id}/provenance` – provenance for a message
- `GET /nodes/{node_id}/ancestors` – graph ancestors
- `GET /nodes/{node_id}/descendants` – graph descendants

Schemas used: `ProvenanceChainResponse`, `ProvenanceNodeResponse`

### 2.9 API Keys Router (`app/api/api_keys.py`)

- `GET /` – list API keys
- `POST /` – create API key (returns key once)
- `GET /{key_id}` – get key metadata (no secret)
- `PUT /{key_id}` – update key permissions
- `DELETE /{key_id}` – revoke key

Schemas used: `ApiKeyCreate`, `ApiKeyResponse`, `ApiKeyUpdate`

### 2.10 Policy Router (`app/api/policy.py`)

- `GET /` – list policies
- `POST /` – create policy version
- `GET /{policy_id}` – get policy detail
- `POST /{policy_id}/activate` – activate a version
- `GET /{policy_id}/versions` – list versions

Schemas used: `PolicyCreate`, `PolicyResponse`, `PolicyVersionResponse`

### 2.11 Audit Router (`app/api/audit.py`)

- `GET /` – list audit events (paginated, filtered)
- `GET /{event_id}` – get event detail
- `GET /export` – export audit log (CSV/JSON)
- `GET /stats` – audit event statistics

Schemas used: `AuditEventResponse`, `AuditEventFilter`, `AuditExportRequest`

### 2.12 Storage Router (`app/api/storage.py`)

- `POST /upload` – upload file (multipart)
- `GET /download/{file_id}` – download file
- `DELETE /{file_id}` – delete file
- `GET /` – list files

Schemas used: `StorageUploadResponse`, `StorageFileResponse`

### 2.13 Dashboard Router (`app/api/dashboard.py`)

- `GET /` – dashboard overview stats
- `GET /projects` – project activity summary
- `GET /memory` – memory health metrics
- `GET /usage` – API usage metrics

Schemas used: `DashboardOverview`, `ProjectActivitySummary`, `MemoryHealthMetrics`

### 2.14 Feedback Router (`app/api/feedback.py`)

- `POST /` – submit feedback on a message
- `GET /` – list feedback
- `PUT /{feedback_id}` – update feedback
- `DELETE /{feedback_id}` – delete feedback

Schemas used: `FeedbackCreate`, `FeedbackResponse`, `FeedbackUpdate`

---

## 3. Service Inventory

All services live under `app/services/`. Each is a class with explicit public methods.

### 3.1 Pipeline Orchestration (`app/services/pipeline.py`)

**Responsibility**: Coordinates the M0–M5 processing pipeline for raw data.

**Public interface**:
- `process_source(source_id: str) -> PipelineResult` – runs the full M0–M5 pipeline on a source
- `process_batch(source_ids: list[str]) -> list[PipelineResult]` – batch processing

**Pipeline stages**:
- **M0** – normalization (connectors → normalized messages)
- **M1** – session clustering (group messages into sessions)
- **M2** – fact extraction (extract structured facts)
- **M3** – temporal reasoning (timeline construction)
- **M4** – graph construction (entity/relation graph)
- **M5** – retrieval index building (vector + BM25 index)

Each stage is delegated to a dedicated service module.

### 3.2 Connectors / M0 Normalization (`app/services/connectors.py`)

**Responsibility**: Normalizes raw data from various connectors into `NormalizedMessage` format.

**Public interface**:
- `normalize(source_id: str, raw_data: bytes) -> list[NormalizedMessage]`
- `get_supported_connectors() -> list[str]`

**Supported connectors**:
- Slack export
- Notion export
- Confluence export
- CSV/JSON generic
- Markdown files

### 3.3 M1 Session Service (`app/services/m1_session.py`)

**Responsibility**: Clusters normalized messages into sessions using temporal proximity + content similarity.

**Public interface**:
- `cluster_messages(project_id: str, messages: list[NormalizedMessage]) -> list[Session]`

### 3.4 M2 Facts Service (`app/services/m2_facts.py`)

**Responsibility**: Extracts structured facts from session messages using LLM.

**Public interface**:
- `extract_facts(session_id: str, messages: list[Message]) -> list[Fact]`

### 3.5 M3 Temporal Service (`app/services/m3_temporal.py`)

**Responsibility**: Builds temporal timelines from facts, resolving timestamps and ordering.

**Public interface**:
- `build_timeline(project_id: str, facts: list[Fact]) -> Timeline`

### 3.6 M4 Graph Service (`app/services/m4_graph.py`)

**Responsibility**: Constructs entity-relation graph from facts and decisions.

**Public interface**:
- `build_graph(project_id: str, facts: list[Fact], decisions: list[Decision]) -> Graph`

### 3.7 M5 Retrieval Service (`app/services/m5_retrieval.py`)

**Responsibility**: Builds hybrid retrieval index (vector + BM25) from graph content.

**Public interface**:
- `build_index(project_id: str, graph: Graph) -> RetrievalIndex`

### 3.8 Hybrid Retrieval (`app/services/retrieval.py`)

**Responsibility**: Performs hybrid semantic + keyword search over the retrieval index.

**Public interface**:
- `search(project_id: str, query: str, top_k: int = 10) -> list[RetrievalResult]`
- `search_with_rerank(project_id: str, query: str, top_k: int = 10) -> list[RetrievalResult]`

**Strategy**: Reciprocal Rank Fusion (RRF) combining vector search and BM25 results.

### 3.9 Memory Service (`app/services/memory.py`)

**Responsibility**: Manages memory entity lifecycle – CRUD, entity resolution, relation management.

**Public interface**:
- `create_memory(project_id: str, data: MemoryCreate) -> Memory`
- `get_memory(memory_id: str) -> Memory`
- `update_memory(memory_id: str, data: MemoryUpdate) -> Memory`
- `delete_memory(memory_id: str) -> None`
- `search_memories(project_id: str, query: str) -> list[Memory]`
- `get_entities(project_id: str) -> list[Entity]`
- `get_relations(project_id: str) -> list[Relation]`

### 3.10 Chat Orchestrator (`app/services/chat_orchestrator.py`)

**Responsibility**: Orchestrates chat completions with memory retrieval, context assembly, and LLM dispatch.

**Public interface**:
- `complete(request: ChatRequest) -> ChatResponse`
- `stream(request: StreamingChatRequest) -> AsyncGenerator[str, None]`

**Flow**:
1. Retrieve relevant memories via `RetrievalService`
2. Assemble context from retrieved memories + conversation history
3. Dispatch to LLM provider via `LLMProvider`
4. Post-process: extract facts, update memory, log feedback

### 3.11 LLM Provider (`app/services/llm.py`)

**Responsibility**: Abstracts LLM provider interactions (Anthropic, OpenAI, local).

**Public interface**:
- `complete(messages: list[Message], **kwargs) -> LLMResponse`
- `stream(messages: list[Message], **kwargs) -> AsyncGenerator[str, None]`
- `embed(text: str) -> list[float]`

**Provider selection**: Configured via `settings.llm_provider`. Falls back to configured default.

### 3.12 Audit Service (`app/services/audit/service.py`)

**Responsibility**: Records and queries audit events for compliance.

**Public interface**:
- `record_event(event: AuditEventCreate) -> AuditEvent`
- `query_events(filter: AuditEventFilter) -> PaginatedResult[AuditEvent]`
- `export_events(filter: AuditEventFilter, format: str) -> bytes`

### 3.13 Audit Repository (`app/services/audit/repository.py`)

**Responsibility**: Data access layer for `AuditEvent` model.

**Public interface**:
- `create(event_data: dict) -> AuditEvent`
- `query(filters: dict, limit: int, offset: int) -> tuple[list[AuditEvent], int]`
- `export(filters: dict, format: str) -> bytes`

### 3.14 Audit Constants (`app/services/audit/constants.py`)

Defines the audit event taxonomy:
- **Event categories**: auth, data_access, data_modification, admin, system
- **Event actions**: create, read, update, delete, login, logout, invite, etc.
- **Severity levels**: info, warning, error, critical

### 3.15 Policy Engine (`app/services/policy/engine.py`)

**Responsibility**: Evaluates access control policies at request time.

**Public interface**:
- `evaluate(request: PolicyRequest) -> PolicyDecision`
- `get_active_policy(policy_type: str) -> Policy | None`

### 3.16 Policy Evaluator (`app/services/policy/evaluator.py`)

**Responsibility**: Core policy evaluation logic (ABAC/RBAC hybrid).

**Public interface**:
- `evaluate_rule(rule: PolicyRule, context: PolicyContext) -> bool`
- `evaluate_policy(policy: Policy, context: PolicyContext) -> PolicyDecision`

### 3.17 Policy Dependencies (`app/services/policy/dependencies.py`)

**Responsibility**: FastAPI dependency factory for policy enforcement.

**Public interface**:
- `require_policy(policy_type: str) -> Callable` – returns a FastAPI dependency

### 3.18 Policy Repository (`app/services/policy/repository.py`)

**Responsibility**: Data access layer for `Policy` and `PolicyVersion` models.

**Public interface**:
- `create_policy(data: PolicyCreate) -> Policy`
- `get_active_policy(policy_type: str) -> Policy | None`
- `create_version(policy_id: str, data: dict) -> PolicyVersion`
- `activate_version(policy_id: str, version_id: str) -> None`

### 3.19 Object Storage (`app/services/object_storage.py`)

**Responsibility**: Abstracts object storage operations (upload, download, delete, list).

**Public interface**:
- `upload(file: UploadFile, key: str) -> StorageObject`
- `download(key: str) -> bytes`
- `delete(key: str) -> None`
- `list(prefix: str) -> list[StorageObject]`
- `get_presigned_url(key: str, expires_in: int) -> str`

**Backends**:
- S3 (`object_storage_s3.py`) – AWS S3 / S3-compatible
- MinIO (`object_storage_minio.py`) – self-hosted MinIO

### 3.20 Tool Definitions (`app/services/tools.py`)

**Responsibility**: Defines available tools for LLM function calling.

**Public interface**:
- `get_tools() -> list[ToolDefinition]`
- `execute_tool(name: str, args: dict, context: ToolContext) -> ToolResult`

---

## 4. SQLAlchemy Models

All models are defined in `app/models.py` using SQLAlchemy 2.0 async ORM with `DeclarativeBase`.

### 4.1 Enums

**`UserRole`** (line 11) – `str, enum.Enum`
- `owner` – full workspace control
- `admin` – administrative access
- `member` – standard access
- `viewer` – read-only access

### 4.2 Core Models

| Model | Line | Primary Key | Key Columns | Relationships |
|---|---|---|---|---|
| `Tenant` | 18 | `id` (UUID) | `name`, `slug`, `created_at`, `updated_at` | → Workspace |
| `Workspace` | 39 | `id` (UUID) | `name`, `slug`, `tenant_id` (FK), `created_at` | → User (via WorkspaceMember), → Project |
| `User` | 65 | `id` (UUID) | `email`, `hashed_password`, `full_name`, `role`, `is_active`, `created_at` | → Workspace (via WorkspaceMember), → RefreshToken, → Session |
| `WorkspaceMember` | 97 | composite (`workspace_id`, `user_id`) | `role` (UserRole), `joined_at` | ← Workspace, ← User |
| `Invitation` | 123 | `id` (UUID) | `email`, `workspace_id` (FK), `role`, `token`, `expires_at`, `accepted_at` | ← Workspace |
| `RefreshToken` | 147 | `id` (UUID) | `user_id` (FK), `token_hash`, `expires_at`, `revoked_at`, `created_at` | ← User |
| `Session` | 165 | `id` (UUID) | `user_id` (FK), `project_id` (FK), `title`, `metadata`, `created_at`, `updated_at` | ← User, ← Project, → Message |
| `Message` | 191 | `id` (UUID) | `session_id` (FK), `role`, `content`, `metadata`, `created_at` | ← Session, → MessageProvenance |
| `Project` | 209 | `id` (UUID) | `name`, `description`, `workspace_id` (FK), `owner_id` (FK), `created_at`, `updated_at` | ← Workspace, ← User, → Session |
| `Memory` | 232 | `id` (UUID) | `project_id` (FK), `type`, `content`, `metadata`, `embedding` (vector), `created_at`, `updated_at` | ← Project |
| `IngestJob` | 269 | `id` (UUID) | `project_id` (FK), `source_id` (FK), `status`, `progress`, `error`, `created_at`, `updated_at` | ← Project, ← Source |
| `Source` | 302 | `id` (UUID) | `project_id` (FK), `name`, `type`, `config` (JSON), `status`, `last_synced_at`, `created_at` | ← Project, → IngestJob, → NormalizedMessage |
| `NormalizedMessage` | 369 | `id` (UUID) | `source_id` (FK), `external_id`, `content`, `author`, `timestamp`, `metadata`, `created_at` | ← Source |
| `Fact` | 413 | `id` (UUID) | `project_id` (FK), `statement`, `confidence`, `source_ids` (JSON), `metadata`, `created_at`, `updated_at` | ← Project |
| `Decision` | 467 | `id` (UUID) | `project_id` (FK), `statement`, `context`, `decided_at`, `metadata`, `created_at` | ← Project |
| `GraphNode` | 520 | `id` (UUID) | `project_id` (FK), `label`, `type`, `properties` (JSON), `embedding`, `created_at` | ← Project |
| `GraphEdge` | 561 | `id` (UUID) | `project_id` (FK), `source_id` (FK→GraphNode), `target_id` (FK→GraphNode), `type`, `properties` (JSON), `weight`, `created_at` | ← Project |
| `MessageProvenance` | 607 | `id` (UUID) | `message_id` (FK), `source_type`, `source_id`, `relation`, `metadata`, `created_at` | ← Message |
| `MessageFeedback` | 656 | `id` (UUID) | `message_id` (FK), `user_id` (FK), `rating`, `feedback`, `created_at` | ← Message, ← User |
| `ApiKey` | 684 | `id` (UUID) | `user_id` (FK), `name`, `key_hash`, `permissions` (JSON), `last_used_at`, `expires_at`, `created_at` | ← User |
| `Policy` | 727 | `id` (UUID) | `name`, `type`, `description`, `is_active`, `created_at`, `updated_at` | → PolicyVersion |
| `PolicyVersion` | 761 | `id` (UUID) | `policy_id` (FK), `version`, `rules` (JSON), `created_by` (FK), `created_at` | ← Policy, ← User |
| `AuditEvent` | 788 | `id` (UUID) | `workspace_id` (FK), `user_id` (FK), `action`, `resource_type`, `resource_id`, `metadata` (JSON), `ip_address`, `user_agent`, `created_at` | ← Workspace, ← User |

### 4.3 Model Patterns

- **UUID primary keys**: All models use `UUID` as primary key, generated via `server_default=text("gen_random_uuid()")`.
- **Soft deletion**: `is_active` boolean on `User`, `Workspace`, `Policy` models.
- **JSON columns**: `metadata`, `config`, `properties`, `source_ids`, `permissions`, `rules` use `JSONB` for flexible structured data.
- **Vector columns**: `Memory.embedding` and `GraphNode.embedding` use pgvector `Vector(dim)` type.
- **Timestamps**: `created_at`, `updated_at` on all models using `server_default=now()`.
- **Foreign keys**: All FKs use `ondelete="CASCADE"` for data integrity.
- **Indexes**: Composite indexes on `(project_id, created_at)` for `Fact`, `Decision`, `GraphNode`, `GraphEdge`, `Memory`. `(workspace_id, user_id)` on `WorkspaceMember`.

---

## 5. Middleware Stack

### 5.1 SecurityHeadersMiddleware (`app/middleware/__init__.py` or main.py)

**Responsibility**: Injects security headers on every HTTP response.

**Headers set**:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`

**Line references**: Applied in `app/main.py` as first middleware.

### 5.2 RequestIdMiddleware

**Responsibility**: Generates a unique `X-Request-ID` for each request, propagates it through the call chain.

**Behavior**:
- Checks for existing `X-Request-ID` header (client-provided) or generates UUID v4
- Stores in request state for downstream access
- Adds to response headers

**Usage**: Used by `AuditPersistenceMiddleware` and logging to correlate request lifecycle events.

### 5.3 AuditPersistenceMiddleware

**Responsibility**: Logs request/response pairs to the `AuditEvent` table for compliance.

**Behavior**:
- Captures: method, path, query params, user ID, workspace ID, IP, user agent
- Records after response (status code, response size)
- Filters out health-check and static asset requests
- Uses `AuditService` to persist events

**Performance**: Async, non-blocking. Does not await response body.

### 5.4 RateLimitMiddleware

**Responsibility**: Per-key sliding-window rate limiting.

**Key derivation**: `user_id` for authenticated requests, `ip_address` for unauthenticated.

**Configuration**:
- Default: 100 requests/minute per key
- Burst: 20 requests/second
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

**Storage**: In-memory with sliding window. For production, Redis-backed.

### 5.5 CORSMiddleware

**Responsibility**: Handles Cross-Origin Resource Sharing.

**Configuration**:
- `allow_origins`: From `settings.cors_origins` (comma-separated list)
- `allow_methods`: `["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]`
- `allow_headers`: `["Authorization", "Content-Type", "X-Workspace-Id", "X-Request-ID"]`
- `allow_credentials`: `True`

---

## 6. Configuration

All settings are in `app/core/config.py` using Pydantic `BaseSettings`.

### 6.1 Environment

| Setting | Type | Default | Description |
|---|---|---|---|
| `environment` | `Literal["dev", "staging", "prod"]` | `"dev"` | Runtime environment |
| `debug` | `bool` | `False` | Debug mode |
| `log_level` | `str` | `"INFO"` | Logging level |

### 6.2 Database

| Setting | Type | Default | Description |
|---|---|---|---|
| `database_url` | `str` | Required | PostgreSQL async connection URL |
| `db_pool_size` | `int` | `5` | Connection pool size |
| `db_max_overflow` | `int` | `10` | Max overflow connections |

### 6.3 Authentication

| Setting | Type | Default | Description |
|---|---|---|---|
| `secret_key` | `str` | Required | JWT signing secret |
| `algorithm` | `str` | `"HS256"` | JWT algorithm |
| `access_token_expire_minutes` | `int` | `30` | Access token TTL |
| `refresh_token_expire_days` | `int` | `7` | Refresh token TTL |
| `password_min_length` | `int` | `8` | Minimum password length |

### 6.4 CORS

| Setting | Type | Default | Description |
|---|---|---|---|
| `cors_origins` | `str` | `"*"` | Comma-separated allowed origins |

### 6.5 LLM

| Setting | Type | Default | Description |
|---|---|---|---|
| `llm_provider` | `str` | `"anthropic"` | LLM provider name |
| `llm_api_key` | `str` | Required | Provider API key |
| `llm_model` | `str` | `"claude-sonnet-4-20250514"` | Model identifier |
| `llm_max_tokens` | `int` | `4096` | Max completion tokens |
| `llm_temperature` | `float` | `0.7` | Generation temperature |
| `embedding_model` | `str` | `"text-embedding-3-small"` | Embedding model |
| `embedding_dimensions` | `int` | `1536` | Embedding vector dimensions |

### 6.6 Object Storage

| Setting | Type | Default | Description |
|---|---|---|---|
| `storage_backend` | `Literal["s3", "minio"]` | `"minio"` | Storage backend |
| `s3_bucket` | `str` | Required | S3 bucket name |
| `s3_region` | `str` | `"us-east-1"` | S3 region |
| `s3_access_key` | `str` | Required | S3 access key |
| `s3_secret_key` | `str` | Required | S3 secret key |
| `s3_endpoint_url` | `str` | `None` | S3 endpoint (for MinIO) |

### 6.7 Rate Limiting

| Setting | Type | Default | Description |
|---|---|---|---|
| `rate_limit_requests` | `int` | `100` | Requests per minute |
| `rate_limit_burst` | `int` | `20` | Burst requests per second |

---

## 7. Dependency Injection

### 7.1 `get_db` (`app/db.py`)

**Type**: `AsyncGenerator[AsyncSession, None]`

**Responsibility**: Provides an async database session per request.

**Implementation**: Yields from `async_session_factory()` with automatic rollback on exception and commit on success.

**Used by**: All routers that need database access.

### 7.2 `get_tenant_context` (`app/middleware/tenancy.py`)

**Type**: `Dependency[TenantContext]`

**Responsibility**: Resolves the current tenant/workspace context from the request.

**Resolution order**:
1. `X-Workspace-Id` header (highest priority)
2. User's default workspace
3. First available workspace membership

**Returns**: `TenantContext` with `workspace_id`, `tenant_id`, `user_id`, `role`.

### 7.3 `require_min_role` (`app/middleware/rbac.py`)

**Type**: `Dependency[UserRole]`

**Responsibility**: Enforces minimum role requirement.

**Usage**: `Depends(require_min_role("admin"))` – rejects if user role is below admin.

**Role hierarchy**: `owner > admin > member > viewer` (lower in list = less privileged).

### 7.4 `require_policy` (`app/services/policy/dependencies.py`)

**Type**: `Dependency[None]`

**Responsibility**: Enforces policy evaluation before endpoint access.

**Usage**: `Depends(require_policy("data_access"))` – evaluates `data_access` policy.

**Behavior**: Raises `HTTPException(403)` if policy evaluation denies.

### 7.5 `get_memory_service` (`app/services/memory.py`)

**Type**: `Dependency[MemoryService]`

**Responsibility**: Provides the MemoryService singleton.

**Implementation**: Returns module-level `_memory_service` instance, initializing if needed.

**Used by**: `chat.py`, `memory.py`, `ingest.py`.

---

## 8. Authentication

### 8.1 JWT Implementation (`app/api/auth.py`)

**Access Token**:
- Algorithm: HS256
- Expiry: 30 minutes (`settings.access_token_expire_minutes`)
- Claims: `sub` (user ID), `role`, `workspace_id`, `exp`
- Signed with `settings.secret_key`

**Refresh Token**:
- Stored hashed in `RefreshToken` model (`token_hash`)
- Expiry: 7 days (`settings.refresh_token_expire_days`)
- Rotation: New refresh token issued on each refresh, old one revoked
- Revocation: On logout, sets `revoked_at`

**Token verification** (`app/middleware/auth.py`):
- Extracts `Authorization: Bearer <token>` header
- Verifies signature and expiry
- Loads user from database
- Attaches `user` to `request.state`

### 8.2 Password Hashing

**Algorithm**: bcrypt (via `passlib.context.CryptContext`)
**Settings**: `schemes=["bcrypt"], deprecated="auto"`
**Verification**: `pwd_context.verify(plain, hashed)`
**Hashing**: `pwd_context.hash(plain)`

### 8.3 Registration Flow

1. Hash password
2. Create `User` record
3. Create default `Workspace` for user
4. Create `WorkspaceMember` record (role=owner)
5. Generate access + refresh tokens
6. Return `TokenResponse`

---

## 9. Authorization (RBAC)

### 9.1 Role Hierarchy (`app/middleware/rbac.py`)

```
owner (4)
  └── admin (3)
        └── member (2)
              └── viewer (1)
```

`require_min_role(role)` checks `user.role >= required_role` using this hierarchy.

### 9.2 Workspace-Level Permissions

| Action | owner | admin | member | viewer |
|---|---|---|---|---|
| Manage workspace | Yes | Yes | No | No |
| Invite users | Yes | Yes | No | No |
| Remove users | Yes | Yes | No | No |
| Create project | Yes | Yes | Yes | No |
| Delete project | Yes | Yes | No | No |
| Chat | Yes | Yes | Yes | Yes |
| View memory | Yes | Yes | Yes | Yes |
| Edit memory | Yes | Yes | Yes | No |

### 9.3 Policy Engine Integration (`app/services/policy/engine.py`)

The policy engine provides ABAC (Attribute-Based Access Control) on top of RBAC.

**Policy types**:
- `data_access` – controls what data a user can read
- `data_modification` – controls what data a user can modify
- `admin` – controls administrative actions
- `system` – controls system-level operations

**Policy structure**:
```python
{
  "id": "uuid",
  "name": "policy_name",
  "type": "data_access",
  "is_active": True,
  "versions": [
    {
      "version": 1,
      "rules": [...],
      "created_at": "..."
    }
  ]
}
```

**Evaluation context** includes: `user`, `workspace`, `resource_type`, `resource_id`, `action`.

---

## 10. Tenancy

### 10.1 TenantContext (`app/middleware/tenancy.py`)

**Fields**:
- `workspace_id: UUID`
- `tenant_id: UUID` (from workspace.tenant_id)
- `user_id: UUID`
- `role: UserRole`

**Resolution**: Middleware extracts `X-Workspace-Id` header and resolves context. Stored in `request.state.tenant_context`.

### 10.2 Workspace Membership (`app/models.py`, line 97)

**Model**: `WorkspaceMember`
- Composite PK: `(workspace_id, user_id)`
- `role`: `UserRole` enum
- `joined_at`: timestamp

### 10.3 X-Workspace-Id Header

**Required** on all authenticated requests (except `/auth/*`).
**Validation**: Middleware verifies user is a member of the specified workspace.
**Fallback**: If not provided, uses user's default workspace.

---

## 11. Database Access

### 11.1 Engine Configuration (`app/db.py`)

```python
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    echo=settings.debug,
)
```

### 11.2 Session Factory

```python
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

### 11.3 Transaction Boundaries

- **Default**: Auto-commit per operation (session commits after each endpoint handler)
- **Explicit**: Multi-step transactions use `async with session.begin():`
- **Rollback**: Automatic on exception in `get_db` dependency

### 11.4 Base Model

All models inherit from `DeclarativeBase` with:
- `id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))`
- `created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())`
- `updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())`

---

## 12. Background Processing

**No background processing framework is currently implemented.**

- **No Celery** configuration found.
- **No Redis** queue configuration found.
- **No asyncio.create_task** usage found in routers.
- **Ingestion** (`app/api/ingest.py`): Jobs are created as `IngestJob` records with `status="pending"`. There is no worker process shown to consume them. This is a **gap** – jobs may be created but never processed without a background worker.

**Implication**: Long-running operations (M0–M5 pipeline, file processing) block the request/response cycle. This should be addressed in a future phase.

---

## 13. External Providers

### 13.1 LLM Provider (`app/services/llm.py`)

**Supported providers**:
- **Anthropic** (`anthropic`): Claude Sonnet/Opus via Anthropic SDK
- **OpenAI** (`openai`): GPT-4 via OpenAI SDK
- **Local** (`local`): Ollama or vLLM endpoint

**Factory pattern**: `LLMProviderFactory.create()` returns the configured provider instance.

**Capabilities**:
- Chat completions (sync and streaming)
- Embeddings
- Token counting

### 13.2 Object Storage (`app/services/object_storage.py`)

**Backends**:
- **S3** (`object_storage_s3.py`): Uses `boto3` with `aioboto3` for async operations
- **MinIO** (`object_storage_minio.py`): Uses `minio` SDK, configurable endpoint URL

**Factory**: `ObjectStorageFactory.create()` returns configured backend.

**Operations**: Upload, download, delete, list, presigned URL generation.

### 13.3 Embedding Provider

**Default**: `text-embedding-3-small` (OpenAI)
**Dimensions**: 1536
**Used for**: `Memory.embedding`, `GraphNode.embedding`, retrieval index

---

## 14. Error Handling

### 14.1 Validation Errors

- **Pydantic `RequestValidationError`**: Caught by FastAPI's built-in handler, returns 422 with field-level error details.
- **Custom validation**: Additional checks in service layer raise `ValueError` or custom exceptions, caught by the generic `Exception` handler.

### 14.2 Sanitization

- **SQL injection**: Prevented via SQLAlchemy ORM (parameterized queries)
- **XSS**: Response headers set by `SecurityHeadersMiddleware`
- **Path traversal**: File download endpoints validate `file_id` against UUID format

### 14.3 Fail-Closed Design

- **Generic `Exception` handler**: Returns 500 with generic error message, no stack traces in production
- **Policy denial**: Returns 403 with policy denial reason
- **Auth failure**: Returns 401 without revealing whether user exists
- **Rate limit**: Returns 429 with `Retry-After` header

### 14.4 Error Response Format

```json
{
  "detail": "Error message",
  "request_id": "uuid",
  "timestamp": "2026-09-10T..."
}
```

---

## 15. Logging

### 15.1 StructuredFormatter (`app/core/logging.py`)

**Format**: JSON with fields:
- `timestamp`: ISO 8601
- `level`: log level
- `logger`: logger name
- `message`: log message
- `request_id`: from `X-Request-ID`
- `user_id`: authenticated user
- `workspace_id`: current workspace
- `duration_ms`: request duration

### 15.2 Request Scoping

- `RequestIdMiddleware` generates `X-Request-ID`
- `request.state.request_id` available in all downstream handlers
- Audit events include `request_id` for correlation

---

## 16. Observability

### 16.1 Request IDs

- Generated by `RequestIdMiddleware` (UUID v4)
- Propagated via `X-Request-ID` header
- Logged in every structured log entry
- Stored in `AuditEvent.request_id`

### 16.2 Latency

- `AuditPersistenceMiddleware` records request/response timestamps
- `duration_ms` calculated and stored in audit events
- Dashboard exposes latency percentiles via `/api/v1/dashboard/usage`

### 16.3 Metrics

No dedicated metrics endpoint or Prometheus integration was found. Latency data is available via audit log analysis.

---

## 17. Health/Readiness

### 17.1 `/health` Endpoint

**Location**: `app/main.py`
**Method**: `GET`
**Response**: `{"status": "ok"}` with 200
**Purpose**: Basic liveness check

### 17.2 `/health/ready` Endpoint

**Location**: `app/main.py`
**Method**: `GET`
**Checks**:
- Database connection (`SELECT 1`)
- Storage backend connectivity
**Response**: `{"status": "ready", "checks": {...}}` with 200 or 503

### 17.3 `/health/live` Endpoint

**Location**: `app/main.py`
**Method**: `GET`
**Response**: `{"status": "alive"}` with 200
**Purpose**: Kubernetes liveness probe

---

## 18. Runtime Dependencies

### 18.1 Python Packages

| Package | Version | Purpose |
|---|---|---|
| `fastapi` | >=0.100.0 | Web framework |
| `uvicorn[standard]` | >=0.23.0 | ASGI server |
| `sqlalchemy[asyncio]` | >=2.0.0 | ORM |
| `asyncpg` | >=0.28.0 | PostgreSQL async driver |
| `alembic` | >=1.12.0 | Database migrations |
| `pydantic` | >=2.0.0 | Validation |
| `pydantic-settings` | >=2.0.0 | Config |
| `python-jose[cryptography]` | >=3.3.0 | JWT |
| `passlib[bcrypt]` | >=1.7.0 | Password hashing |
| `python-multipart` | >=0.0.6 | Form data |
| `anthropic` | >=0.18.0 | Anthropic API |
| `openai` | >=1.0.0 | OpenAI API |
| `boto3` | >=1.28.0 | S3 storage |
| `minio` | >=7.2.0 | MinIO storage |
| `pgvector` | >=0.2.0 | Vector type |
| `redis` | >=5.0.0 | Cache (planned) |
| `structlog` | >=23.0.0 | Structured logging |

### 18.2 Infrastructure

| Component | Purpose | Required |
|---|---|---|
| PostgreSQL 15+ | Primary database with pgvector extension | Yes |
| Redis (optional) | Cache + rate limiting backend | Recommended |
| MinIO / S3 | Object storage | Yes |
| Anthropic API / OpenAI API | LLM + embeddings | Yes |

---

## 19. Representative Request Traces

### 19.1 Chat Completion Request

```
Client → POST /api/v1/chat/completions
  Authorization: Bearer <access_token>
  X-Workspace-Id: <workspace_id>
  Content-Type: application/json
  Body: {"messages": [{"role": "user", "content": "What did we decide about X?"}]}

Trace through middleware stack:
  SecurityHeadersMiddleware → no-op (request phase)
  RequestIdMiddleware → generates X-Request-ID, stores in request.state
  AuditPersistenceMiddleware → logs request start
  RateLimitMiddleware → checks key rate limit
  CORSMiddleware → validates origin

Route dispatch: POST /api/v1/chat/completions
  Dependency: get_tenant_context → resolves from X-Workspace-Id + user
  Dependency: get_memory_service → returns MemoryService singleton

Handler: chat_orchestrator.complete(request)
  ├── ChatOrchestrator.complete()
  │     ├── RetrievalService.search(project_id, query) → [Memory, ...]
  │     │     ├── embed(query) → embedding (via LLM provider)
  │     │     └── pgvector similarity search + BM25 RRF
  │     ├── assemble_context(memories, history) → context_messages
  │     ├── LLMProvider.complete(context_messages) → LLMResponse
  │     │     └── anthropic.Anthropic().messages.create(...)
  │     ├── post_process(response)
  │     │     ├── MemoryService.create_memory(...) → Memory
  │     │     ├── Fact extraction via LLM
  │     │     └── GraphNode creation
  │     └── return ChatResponse
  └── Streaming: yield SSE chunks

Response:
  AuditPersistenceMiddleware → logs response (status=200, duration_ms)
  RateLimitMiddleware → adds X-RateLimit-* headers
  SecurityHeadersMiddleware → adds security headers
  → 200 OK with JSON body
```

### 19.2 Memory Creation Request

```
Client → POST /api/v1/memory
  Authorization: Bearer <access_token>
  X-Workspace-Id: <workspace_id>
  Body: {"content": "...", "type": "fact", "metadata": {...}}

Route dispatch: POST /api/v1/memory
  Dependency: get_tenant_context → {workspace_id, user_id, role}

Handler: memory_service.create_memory(project_id, data)
  ├── validate input against MemoryCreate schema
  ├── embed(content) → [float, ...] (1536 dims)
  ├── Memory(content=..., embedding=[...], project_id=...)
  ├── session.add(memory)
  ├── await session.commit()
  └── return MemoryResponse

Response: 201 Created with MemoryResponse
```

### 19.3 Project Creation Request

```
Client → POST /api/v1/projects
  Authorization: Bearer <access_token>
  X-Workspace-Id: <workspace_id>
  Body: {"name": "New Project", "description": "..."}

Route dispatch: POST /api/v1/projects
  Dependency: get_tenant_context → {workspace_id, user_id, role=owner}
  Dependency: require_min_role("member") → passes (owner >= member)

Handler: projects.create_project(db, workspace_id, data)
  ├── Project(name=..., description=..., workspace_id=..., owner_id=...)
  ├── session.add(project)
  ├── await session.commit()
  └── return ProjectResponse

Response: 201 Created with ProjectResponse
```

---

## 20. Key Findings Summary

### 20.1 Architecture Strengths

1. **Clean separation**: Middleware, routers, services, models are well-separated
2. **Tenancy by design**: Every request is scoped to a workspace
3. **Type safety**: Full Pydantic + SQLAlchemy 2.0 typing
4. **Async-first**: All I/O operations are async
5. **Audit by default**: Every request is logged for compliance
6. **Policy extensible**: ABAC layer on top of RBAC

### 20.2 Identified Gaps

1. **No background worker**: Ingestion jobs have no consumer. M0–M5 pipeline runs synchronously.
2. **No Redis integration**: Rate limiting is in-memory (not distributed).
3. **No metrics**: No Prometheus/OpenTelemetry integration.
4. **Vector index**: Relies on pgvector brute-force; no HNSW/IVFFlat index strategy documented.
5. **Error recovery**: No retry logic for external provider failures (LLM, storage).
6. **File size limits**: No documented limits on upload size.
7. **Pagination**: No documented pagination strategy for large result sets.

---

*Document generated by Agent 1 – BACKEND RUNTIME ARCHITECTURE. Baseline: e6f4b1c1.*
