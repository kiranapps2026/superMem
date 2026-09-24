# SwarmVault Backend Architecture Manifest

**Version:** 1.0.0
**Date:** 2026-09-24
**Branch:** recovery/restore-2026-09-24
**Authority:** Source code is the single source of truth. This document is authoritative only when it matches source.

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Application Bootstrap](#2-application-bootstrap)
3. [Database Layer](#3-database-layer)
4. [LLM Provider Abstraction](#4-llm-provider-abstraction)
5. [Ingestion Pipeline (M0-M5)](#5-ingestion-pipeline-m0-m5)
6. [Middleware Stack](#6-middleware-stack)
7. [Tenancy & Isolation](#7-tenancy--isolation)
8. [Security & Authentication](#8-security--authentication)
9. [Configuration Management](#9-configuration-management)
10. [Observability & Audit](#10-observability--audit)
11. [Service Layer Map](#11-service-layer-map)
12. [Data Flow Diagrams](#12-data-flow-diagrams)
13. [API Contract](#13-api-contract)

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SwarmVault Backend                                │
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────┐  │
│  │   FastAPI    │───▶│  Middleware  │───▶│          Router Layer        │  │
│  │   App        │    │   Stack       │    │  (14 routers, 81 endpoints)  │  │
│  └──────────────┘    └──────────────┘    └──────────────────────────────┘  │
│         │                    │                       │                     │
│         │                    │                       ▼                     │
│         │                    │              ┌────────────────────┐        │
│         │                    │              │  Service Layer     │        │
│         │                    │              │  (14 services)     │        │
│         │                    │              └────────────────────┘        │
│         │                    │                       │                     │
│         │                    │                       ▼                     │
│         │                    │              ┌────────────────────┐        │
│         │                    │              │  Repository Layer  │        │
│         │                    │              │  (SQLAlchemy ORM)  │        │
│         │                    │              └────────────────────┘        │
│         │                    │                       │                     │
│         └────────────────────┴───────────────────────┘                     │
│                              │                                             │
│                              ▼                                             │
│                   ┌────────────────────┐                                   │
│                   │   PostgreSQL DB    │                                   │
│                   │  (23 tables)       │                                   │
│                   └────────────────────┘                                   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         LLM Providers                                  │  │
│  │   Anthropic │ OpenAI │ DeepSeek │ Mock (fallback)                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Object Storage                                     │  │
│  │   Filesystem (default) │ MinIO │ S3                                     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.1 Framework & Runtime

| Component | Technology | Version | Source File |
|---|---|---|---|
| Web Framework | FastAPI | Latest | app/main.py:1 |
| ASGI Server | uvicorn | — | .env |
| ORM | SQLAlchemy 2.0 (async) | — | app/db.py:5 |
| Database | PostgreSQL + asyncpg | — | app/db.py:9 |
| Migrations | Alembic | 12 migrations | alembic/versions/ |
| Auth | JWT (python-jose) | HS256 | app/core/security.py |
| LLM SDK | anthropic, openai | — | app/services/llm.py |
| Settings | pydantic-settings | — | app/core/config.py |
| Object Storage | boto3 (S3/MinIO) | — | app/services/object_storage.py |
| Testing | pytest + Playwright | — | tests/, frontend/e2e/ |

### 1.2 Layer Responsibilities

| Layer | Responsibility | Source |
|---|---|---|
| **Middleware** | Request pre/post processing | app/main.py:22-228 |
| **Routers** | HTTP endpoint definitions | app/api/*.py |
| **Services** | Business logic orchestration | app/services/*.py |
| **Repositories** | Database access (SQLAlchemy) | app/models.py |
| **Schemas** | Pydantic validation | app/schemas.py |

---

## 2. Application Bootstrap

### 2.1 Entry Point: `app/main.py` (279 lines)

```
FastAPI(app)
  │
  ├── Middleware (registered in order)
  │   ├── SecurityHeadersMiddleware
  │   ├── RequestIdMiddleware
  │   ├── AuditPersistenceMiddleware
  │   ├── CORSMiddleware
  │   ├── RateLimitMiddleware
  │   ├── TenancyMiddleware
  │   └── RBACMiddleware
  │
  ├── Error Handlers
  │   ├── 422 ValidationError → sanitized
  │   ├── 500 SQLAlchemyError → sanitized
  │   └── 500 Exception → sanitized
  │
  ├── API Routers (14 routers, 81 endpoints)
  │   ├── auth.router
  │   ├── workspace.router
  │   ├── projects.router
  │   ├── sessions.router
  │   ├── chat.router
  │   ├── memory.router
  │   ├── ingest.router
  │   ├── provenance.router
  │   ├── dashboard.router
  │   ├── feedback.router
  │   ├── api_keys.router
  │   ├── storage.router
  │   ├── policy.router
  │   └── audit.router
  │
  └── Health Endpoints
      ├── GET /health/live
      ├── GET /health/ready
      └── GET /health
```

### 2.2 Lifespan

| Phase | Action | Source File |
|---|---|---|
| Startup | `setup_logging()` (dev only) | app/main.py:168 |
| Startup | `await init_db()` — apply migrations | app/main.py:169 |
| Startup | `audit.register_db_sink()` — wire DB persistence | app/main.py:170 |
| Runtime | `yield` — serve requests | app/main.py:173 |
| Shutdown | Engine disposal (SQLAlchemy) | app/db.py |

---

## 3. Database Layer

### 3.1 Engine Configuration (`app/db.py`, 46 lines)

| Parameter | Value | Purpose |
|---|---|---|
| Driver | asyncpg | Async PostgreSQL |
| Pool Size | 50 | Max persistent connections |
| Max Overflow | 20 | Burst capacity |
| Pool Pre-Ping | True | Detect stale connections |
| Pool Recycle | 3600s | Force reconnect every hour |
| Echo | debug mode only | SQL logging |
| Expire on Commit | False | Keep objects after commit |

### 3.2 Session Management

```python
# app/db.py
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
```

Each request gets a fresh `AsyncSession` via FastAPI dependency injection. `AuditPersistenceMiddleware` creates a separate short-lived session for audit writes (atomic with respect to request transaction).

### 3.3 Base Model

```python
# app/db.py
class Base(DeclarativeBase):
    pass
```

All 23 models inherit from `Base`. UUID primary keys are auto-generated via `uuid.uuid4()` default.

### 3.4 Migration System

| Aspect | Detail | Source File |
|---|---|---|
| Config | `alembic.ini` at project root | alembic.ini |
| Env | `alembic/env.py` (async) | alembic/env.py |
| Versions | 12 migrations (001-012) | alembic/versions/ |
| Init | `init_db()` runs `upgrade head` | app/db.py:40 |
| Init runs at | Lifespan startup | app/main.py:169 |

---

## 4. LLM Provider Abstraction

### 4.1 Provider Hierarchy

```
LLMProvider (protocol base)
  │
  ├── AnthropicProvider    (Anthropic SDK, messages.create)
  ├── OpenAIProvider       (OpenAI SDK, chat.completions.create)
  ├── DeepSeekProvider     (OpenAI SDK, custom base_url)
  └── MockProvider         (Deterministic, no API key needed)
```

### 4.2 Provider Interface

| Method | Signature | Purpose |
|---|---|---|
| `chat_completion` | `(messages, model, max_tokens, temperature, stream) → dict \| AsyncIterator` | Core completion |
| `aclose` | `() → None` | Cleanup client resources |

### 4.3 Provider Selection Logic

| Priority | Provider | Condition | Source File |
|---|---|---|---|
| 1 | Anthropic | `llm_provider=anthropic` AND `anthropic_api_key` set | app/services/llm.py:292 |
| 2 | OpenAI | `llm_provider=openai` AND `openai_api_key` set | app/services/llm.py:294 |
| 3 | DeepSeek | `llm_provider=deepseek` AND `deepseek_api_key` set | app/services/llm.py:296 |
| 4 | Mock | No key configured | app/services/llm.py:299 |

### 4.4 Timeout & Retry Wrapper

| Setting | Default | Env Var | Source File |
|---|---|---|---|
| Timeout | 30s | `LLM_TIMEOUT_SECONDS` | app/core/config.py:40 |
| Max Retries | 2 | `LLM_MAX_RETRIES` | app/core/config.py:41 |
| Backoff | 1.0s exponential | `LLM_RETRY_BACKOFF` | app/core/config.py:42 |

All live providers are wrapped with `_with_timeout_and_retry()`. On final failure, returns error dict (never raises).

### 4.5 MockProvider Behavior

| Scenario | Response | Source File |
|---|---|---|
| Memory context present | `[Mock AI] Answer based on ingested memory: {context}` | app/services/llm.py:227 |
| No memory | `[Mock AI] I received your message: "{user_msg}". Set a real LLM_API_KEY...` | app/services/llm.py:230 |
| Stream | Yields words with spaces | app/services/llm.py:234-238 |

---

## 5. Ingestion Pipeline (M0-M5)

### 5.1 Pipeline Orchestrator

**File:** `app/services/pipeline.py` (238 lines)
**Entry:** `run_pipeline(db, *, workspace_id, tenant_id, project_id, user_id, source_type, raw_content, title, config)`

### 5.2 Stage Detail

| Stage | Name | Input | Output | File | Lines |
|---|---|---|---|---|---|
| M0 | Normalize | Raw text/JSON/file | `NormalizedConversation` (title, messages, metadata) | app/services/connectors.py | 760 |
| M1 | Session Understanding | Messages list | `topics[]`, `entities_mentioned[]`, `summary` | app/services/m1_session.py | 139 |
| M2 | Fact + Decision Extraction | Messages list | `facts[]`, `decisions[]` | app/services/m2_facts.py | 177 |
| M3 | Temporal Supersession | Facts | Deduped/superseded facts | app/services/m3_temporal.py | 202 |
| M4 | Graph Persistence | All text | `nodes_created`, `edges_created` | app/services/m4_graph.py | 192 |
| M5 | Retrieval | Query | Hybrid-ranked results | app/services/m5_retrieval.py | 294 |

### 5.3 Pipeline State Machine

| Stage | Progress % | Source Status | Source Field |
|---|---|---|---|
| M0 | 0% | `processing` | `source.stage = "M0"` |
| M1 | 25% | `processing` | `source.stage = "M1"` |
| M2 | 50% | `processing` | `source.stage = "M2"` |
| M3 | 75% | `processing` | `source.stage = "M3"` |
| M4 | 85% | `processing` | `source.stage = "M4"` |
| M5 | 100% | `completed` | `source.stage = "M5"`, `source.status = "completed"` |
| — | — | `failed` | On exception: `source.status = "failed"`, `source.error_message` |

### 5.4 Fact Dedup Logic (M3 inline)

```
For each extracted fact (subject, predicate, object):
  existing = SELECT * FROM facts
             WHERE workspace_id = ?
               AND subject = ?
               AND predicate = ?
               AND temporal_status = 'current'
               AND deleted_at IS NULL

  IF existing:
    IF existing.object != fact.object (case-insensitive):
      existing.temporal_status = 'historical'
      CREATE new fact with temporal_status = 'current'
    ELSE:
      SKIP (exact duplicate)
  ELSE:
    CREATE new fact with temporal_status = 'current'
```

**Invariant:** One "current" fact per (workspace_id, subject, predicate).

---

## 6. Middleware Stack

### 6.1 Registration Order (outermost first)

```
Request
  │
  ▼
[1] SecurityHeadersMiddleware  ← app/main.py:187
  │   Adds: CSP, HSTS, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy
  │
  ▼
[2] RequestIdMiddleware         ← app/main.py:189
  │   Adds: X-Request-ID header, measures latency_ms
  │
  ▼
[3] AuditPersistenceMiddleware  ← app/main.py:213
  │   After each request: flush buffered audit events to PostgreSQL
  │   Uses independent session (atomic wrt request transaction)
  │
  ▼
[4] CORSMiddleware              ← app/main.py:217
  │   allow_origins: cors_origins_safe (never wildcard with credentials)
  │   allow_methods: GET, POST, PATCH, DELETE, OPTIONS
  │
  ▼
[5] RateLimitMiddleware         ← app/main.py:228
  │   In-memory sliding window per IP
  │
  ▼
[6] TenancyMiddleware           ← app/middleware/tenancy.py
  │   Injects TenantContext from JWT
  │
  ▼
[7] AuthMiddleware              ← app/middleware/auth.py
  │   Validates Bearer JWT, loads User
  │
  ▼
[8] RBACMiddleware              ← app/middleware/rbac.py
  │   Checks role permissions
  │
  ▼
[Endpoint Handler]
  │
  ▼
Response
```

---

## 7. Tenancy & Isolation

### 7.1 TenantContext

```python
# app/middleware/tenancy.py
@dataclass
class TenantContext:
    tenant_id: str
    tenant_name: str | None = None
    tenant_plan: str | None = None
    workspace_id: str | None = None
    workspace_name: str | None = None
    role: str = "viewer"
    user_id: str | None = None
```

### 7.2 Isolation Boundaries

| Boundary | Mechanism | Enforcement |
|---|---|---|
| Tenant → Workspace | FK `workspaces.tenant_id` | DB-level |
| Workspace → Projects | FK `projects.workspace_id` | DB-level |
| Workspace → Members | FK `workspace_members.workspace_id` | DB-level |
| Cross-tenant access | RBAC middleware checks `tenant_id` match | Middleware |
| Row-level | All queries filter by `workspace_id` or `tenant_id` | Service layer |

### 7.3 Multi-Workspace Support

Users can belong to multiple workspaces via `WorkspaceMember`. The active workspace is resolved from the JWT token or request context. All data operations are scoped to `workspace_id`.

---

## 8. Security & Authentication

### 8.1 JWT Configuration

| Setting | Default | Env Var | Source File |
|---|---|---|---|
| Secret Key | dev-insecure-default (warned) | `SECRET_KEY` | app/core/config.py:26 |
| Algorithm | HS256 | `ALGORITHM` | app/core/config.py:27 |
| Access Token Expiry | 60 minutes | `ACCESS_TOKEN_EXPIRE_MINUTES` | app/core/config.py:28 |
| Refresh Token Expiry | 30 days | `REFRESH_TOKEN_EXPIRE_DAYS` | app/core/config.py:29 |
| Token URL | `auth/login` | — | app/middleware/auth.py:13 |

### 8.2 JWT Validation

| Check | Implementation | Source File |
|---|---|---|
| Token presence | `auto_error=False`, manual 401 | app/middleware/auth.py:21 |
| Signature | `security.decode_access_token()` | app/middleware/auth.py:27 |
| Payload `sub` | User ID extraction | app/middleware/auth.py:34 |
| User active | `user.is_active` check | app/middleware/auth.py |

### 8.3 Password Security

| Aspect | Implementation | Source File |
|---|---|---|
| Hashing | passlib context (bcrypt) | app/core/security.py |
| Min length | Pydantic validation | app/schemas.py |
| Never returned | Pydantic `exclude=True` | app/schemas.py |

### 8.4 Refresh Tokens

| Aspect | Detail | Source File |
|---|---|---|
| Storage | `refresh_tokens` table | app/models.py:147 |
| Lifetime | 30 days | app/core/config.py:29 |
| Revocation | Logout deletes token | app/api/auth.py |
| Rotation | New refresh on use | app/api/auth.py |

### 8.5 API Key Authentication

| Aspect | Detail | Source File |
|---|---|---|
| Storage | `api_keys` table with `key_hash` | app/models.py:685 |
| Format | `sv_` prefix + random bytes | app/api/api_keys.py |
| Hashing | SHA-256 | app/models.py |
| Revocation | Delete row | app/api/api_keys.py |

---

## 9. Configuration Management

### 9.1 Settings Class

**File:** `app/core/config.py` (166 lines)
**Class:** `Settings(BaseSettings)` with `env_file=".env"`

### 9.2 Configuration Categories

| Category | Settings | Source File |
|---|---|---|
| **App** | `app_name`, `environment`, `debug` | app/core/config.py:14-15 |
| **Database** | `database_url` | app/core/config.py:23 |
| **Auth** | `secret_key`, `algorithm`, `access_token_expire_minutes`, `refresh_token_expire_days` | app/core/config.py:26-29 |
| **CORS** | `cors_origins` (string) | app/core/config.py:33 |
| **LLM** | `llm_provider`, `llm_model`, `llm_max_tokens`, `llm_temperature`, `llm_timeout_seconds`, `llm_max_retries`, `llm_retry_backoff` | app/core/config.py:36-42 |
| **LLM Keys** | `anthropic_api_key`, `openai_api_key`, `deepseek_api_key` | app/core/config.py:43-45 |
| **SwarmVault** | `swarmvault_url`, `swarmvault_api_key` | app/core/config.py:48-49 |
| **Observability** | `log_level`, `enable_metrics` | app/core/config.py:52-53 |
| **Rate Limits** | `rate_limit_login`, `rate_limit_chat`, `rate_limit_ingest`, `rate_limit_search`, `rate_limit_api` | app/core/config.py:56-60 |
| **Storage** | `storage_backend`, `storage_path`, `s3_endpoint`, `s3_access_key`, `s3_secret_key`, `s3_bucket`, `s3_region` | app/core/config.py:63-69 |

### 9.3 Validators

| Validator | Purpose | Source File |
|---|---|---|
| `_validate_secret_key` | Reject insecure defaults in production, warn in dev | app/core/config.py:71-113 |
| `_validate_database_url` | Reject dev DB URL in production | app/core/config.py:115-124 |

### 9.4 Properties

| Property | Returns | Source File |
|---|---|---|
| `debug` | `environment != "production"` | app/core/config.py:17-20 |
| `is_production` | `environment == "production"` | app/core/config.py:144-146 |
| `cors_origins_list` | Parsed list from string/JSON | app/core/config.py:126-142 |
| `cors_origins_safe` | Strips wildcard, enforces localhost in dev | app/core/config.py:148-163 |

---

## 10. Observability & Audit

### 10.1 Structured Logging

**File:** `app/main.py:88-107`
**Format:** JSON via `StructuredFormatter`

| Field | Value | Always Present |
|---|---|---|
| `timestamp` | ISO 8601 | Yes |
| `level` | INFO, WARNING, ERROR | Yes |
| `logger` | Module name (e.g. `app.main`) | Yes |
| `message` | Log message | Yes |
| `request_id` | X-Request-ID UUID | Yes |
| `exception` | Stack trace | On error only |

Enabled only in development (`environment != "production"`).

### 10.2 Health Checks

| Endpoint | Method | DB Check | Response | Source File |
|---|---|---|---|---|
| `/health/live` | GET | No | `{"status": "alive"}` | app/main.py:256 |
| `/health/ready` | GET | Yes (`SELECT 1`) | `{"status": "ready", "database": "connected"}` or 503 | app/main.py:261 |
| `/health` | GET | No | `{"status": "ok"}` | app/main.py:277 |

### 10.3 Audit Service

**File:** `app/services/audit/service.py` (305 lines)
**Singleton:** `audit = AuditService()` at `app/main.py:161`

| Aspect | Detail | Source File |
|---|---|---|
| Buffer size | 1000 events max | app/services/audit/service.py:136 |
| Drop policy | Oldest first (drop-oldest) | app/services/audit/service.py:177-178 |
| Persistence | PostgreSQL per-request | app/main.py:193 |
| Session | Independent short-lived (atomic) | app/main.py:203-207 |
| Failure policy | Log warning, clear buffer, never block response | app/main.py:209 |
| Disabled for tests | `_disabled_for_testing` flag | app/services/audit/service.py |

### 10.4 Request ID & Latency

| Field | Source | Source File |
|---|---|---|
| `X-Request-ID` | Client header or UUID | app/main.py:26 |
| `latency_ms` | `time.monotonic()` delta | app/main.py:35 |
| Logged in | Structured log + response header | app/main.py:36-45, 33 |

---

## 11. Service Layer Map

| Service | File | Lines | Dependencies | Purpose |
|---|---|---|---|---|
| **LLM** | app/services/llm.py | 401 | app/core/config.py | Provider abstraction, timeout/retry |
| **Pipeline** | app/services/pipeline.py | 238 | m1, m2, m3, m4, connectors | M0-M5 orchestration |
| **Connectors** | app/services/connectors.py | 760 | — | Input format normalization |
| **M1 Session** | app/services/m1_session.py | 139 | llm | Topic/entity/intent extraction |
| **M2 Facts** | app/services/m2_facts.py | 177 | llm | Fact + decision extraction |
| **M3 Temporal** | app/services/m3_temporal.py | 202 | models | Fact supersession |
| **M4 Graph** | app/services/m4_graph.py | 192 | models | Entity/edge persistence |
| **M5 Retrieval** | app/services/m5_retrieval.py | 294 | memory, retrieval | Hybrid search for chat |
| **Memory** | app/services/memory.py | 1045 | models, llm | Vector embeddings, CRUD |
| **Retrieval** | app/services/retrieval.py | 121 | models | BM25 + semantic + graph |
| **Chat Orchestrator** | app/services/chat_orchestrator.py | 152 | llm, m5, models | End-to-end chat flow |
| **Audit** | app/services/audit.py | 305 | models | Event buffering, persistence |
| **Object Storage** | app/services/object_storage.py | 141 | s3, minio | Unified storage interface |
| **Object Storage S3** | app/services/object_storage_s3.py | 84 | boto3 | AWS S3 backend |
| **Object Storage MinIO** | app/services/object_storage_minio.py | 85 | boto3 | MinIO backend |
| **Tools** | app/services/tools.py | 473 | llm | Function calling tools |

---

## 12. Data Flow Diagrams

### 12.1 Chat Flow

```
User sends message (POST /api/v1/chat/)
  │
  ▼
AuthMiddleware.validate_token()
  │
  ▼
TenancyMiddleware.resolve_tenant()
  │
  ▼
chat.router → chat_orchestrator.process_chat()
  │
  ├─▶ [1] M5 Retrieval (retrieve_for_chat)
  │     ├─ Semantic search (memory table)
  │     ├─ Graph traversal (graph_nodes, graph_edges)
  │     └─ BM25 keyword search
  │     → context_block, memory_ids_used
  │
  ├─▶ [2] Build LLM messages
  │     └─ System prompt + memory context + user message
  │
  ├─▶ [3] LLM Provider call
  │     └─ get_llm_provider() → Anthropic/OpenAI/DeepSeek/Mock
  │     └─ Wrapped with timeout (30s) + retry (2x exponential backoff)
  │     → llm_result { content, model, provider, usage }
  │
  ├─▶ [4] Confidence scoring
  │     └─ base 0.7 (with memory) or 0.5 (without)
  │     └─ + length bonus (max 0.3)
  │
  └─▶ [5] Provenance record
        └─ MessageProvenance model (workspace, session, model, provider, retrieval, tokens, latency, confidence)
        └─ db.add() + db.flush()

  ← Response: { response, session_id, model, usage, memory_ids_used, retrieval_method, latency_ms, confidence, provider }
```

### 12.2 Ingestion Flow

```
User uploads content (POST /api/v1/ingest/)
  │
  ▼
Auth + Tenancy validation
  │
  ▼
ingest.router → run_pipeline(db, ...)
  │
  ├─▶ [M0] normalize() → NormalizedConversation
  │     └─ Create Source (status=processing, stage=M0)
  │     └─ Create Session
  │     └─ Persist NormalizedMessages
  │     └─ Progress: 25%
  │
  ├─▶ [M1] understand_session(messages)
  │     └─ topics[], entities_mentioned[], summary
  │     └─ Progress: 50%
  │
  ├─▶ [M2] extract_facts_and_decisions(messages)
  │     └─ facts[] (subject-predicate-object + confidence + authority)
  │     └─ decisions[] (content + context + confidence)
  │     └─ Progress: 75%
  │
  ├─▶ [M3] Inline temporal check
  │     └─ For each fact: SELECT current fact WHERE subject=?, predicate=?
  │     └─ If different object: mark old as "historical", create new "current"
  │     └─ If same object: skip (dedup)
  │     └─ Progress: 85%
  │
  ├─▶ [M4] extract_graph_elements + persist_graph()
  │     └─ Nodes: entities from text
  │     └─ Edges: relationships from text
  │     └─ Progress: 100%
  │
  └─▶ [M5] (implicit — retrieval at query time, no indexing step)
        └─ Source.status = "completed"
        └─ Source.completed_at = now

  ← Response: { source_id, session_id, status, stage, messages_processed, facts_created, decisions_created, graph_nodes_created, graph_edges_created, topics, entities }
```

### 12.3 Auth Flow

```
POST /api/v1/auth/register
  └─ Hash password → Create User + Workspace + WorkspaceMember(OWNER) → Return tokens

POST /api/v1/auth/login
  └─ Verify password → Create access_token (60min) + refresh_token (30d) → Return both

POST /api/v1/auth/refresh
  └─ Validate refresh_token → Create new access_token → Return

POST /api/v1/auth/logout
  └─ Delete refresh_token → Return 204

GET /api/v1/auth/me
  └─ Decode access_token → Return User (exclude password)
```

### 12.4 Frontend API Flow

```
Browser → api.ts (fetch wrapper)
  │
  ├─ Attach Bearer token from localStorage (sv_tokens)
  ├─ Auto-refresh on 401 (POST /api/v1/auth/refresh)
  ├─ Clear tokens on refresh failure
  └─ Return parsed JSON or throw on non-2xx
```

---

## 13. API Contract

### 13.1 Error Response Shape

```json
{
  "error": {
    "type": "validation_error | database_error | internal_error | ...",
    "message": "Human-readable (sanitized)",
    "request_id": "UUID (if available)"
  }
}
```

All error messages pass through `_sanitize_detail()` which strips:
- Passwords, secrets, tokens, API keys, database URLs
- Windows paths (`C:\...`)
- Unix paths (`/path/...`)

### 13.2 Pagination

List endpoints return paginated results. See `app/schemas.py` for `PaginationParams` and `PaginatedResponse`.

### 13.3 Rate Limit Headers

| Header | Value | Source File |
|---|---|---|
| `X-RateLimit-Limit` | Max requests | app/middleware/rate_limit.py |
| `X-RateLimit-Remaining` | Remaining requests | app/middleware/rate_limit.py |
| `X-RateLimit-Reset` | Window end timestamp | app/middleware/rate_limit.py |

### 13.4 CORS Configuration

| Environment | Behavior | Source File |
|---|---|---|
| Production | Explicit origins only (no wildcard) | app/main.py:59-71 |
| Development | localhost:3000, localhost:8000, 127.0.0.1:3000 | app/main.py:72-81 |
| Credentials | Always `allow_credentials=True` | app/main.py:220 |

---

## Appendix A: Architecture Decisions

| ADR | Decision | Rationale | Source File |
|---|---|---|---|
| ADR-001 | FastAPI over Flask | Async-native, auto-docs, type hints | app/main.py |
| ADR-002 | SQLAlchemy 2.0 async | Modern async ORM, connection pooling | app/db.py |
| ADR-003 | PostgreSQL | JSON support, asyncpg driver, reliability | app/db.py |
| ADR-004 | JWT (not sessions) | Stateless, works across services | app/core/security.py |
| ADR-005 | Provider abstraction | Swappable LLM backends | app/services/llm.py |
| ADR-006 | In-memory rate limiter | Simple, no Redis dependency | app/middleware/rate_limit.py |
| ADR-007 | MockProvider fallback | Tests run without API keys | app/services/llm.py:196 |
| ADR-008 | M5 at query time | No index build step, simpler pipeline | app/services/pipeline.py |
| ADR-009 | Audit buffer + flush | Avoids per-event DB round-trips | app/services/audit/service.py |
| ADR-010 | Independent audit session | Audit writes atomic wrt request | app/main.py:203 |

---

## Appendix B: Source Authority Map

| Manifest Section | Source File | Lines | Authority |
|---|---|---|---|
| System architecture | app/main.py | 279 | Single source of truth |
| Database layer | app/db.py | 46 | Single source of truth |
| LLM providers | app/services/llm.py | 401 | Single source of truth |
| Pipeline | app/services/pipeline.py | 238 | Single source of truth |
| Middleware | app/main.py | 22-228 | Single source of truth |
| Tenancy | app/middleware/tenancy.py | 140 | Single source of truth |
| Auth | app/middleware/auth.py | 51 | Single source of truth |
| RBAC | app/middleware/rbac.py | 140 | Single source of truth |
| Rate limiting | app/middleware/rate_limit.py | 119 | Single source of truth |
| Config | app/core/config.py | 166 | Single source of truth |
| Audit | app/services/audit/service.py | 305 | Single source of truth |
| Security | app/core/security.py | 37 | Single source of truth |
| Models | app/models.py | 838 | Single source of truth |
| Schemas | app/schemas.py | 602 | Single source of truth |
| Chat orchestrator | app/services/chat_orchestrator.py | 152 | Single source of truth |
| Retrieval | app/services/m5_retrieval.py | 294 | Single source of truth |
| Memory service | app/services/memory.py | 1045 | Single source of truth |

---

*This document is maintained by source-of-truth reconciliation. When source diverges from document, source wins and document is corrected.*
