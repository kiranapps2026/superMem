# SwarmVault WebApp — Backend Implementation Reference
**Version:** 1.0.0
**Date:** 2026-09-01
**Evidence base:** Repository inspection (commit 902d85e), 629 tests

---

## 1. Repository Structure

```
SwarmVaultwebapp/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application, middleware, routes
│   ├── db.py                      # Database engine, session factory
│   ├── models.py                  # SQLAlchemy ORM models (15 tables)
│   ├── schemas.py                 # Pydantic request/response schemas
│   ├── core/
│   │   ├── config.py              # Settings (env-based, validated)
│   │   └── security.py            # JWT, password hashing
│   ├── api/                       # 14 route modules
│   │   ├── __init__.py
│   │   ├── auth.py                # Register, login, refresh, logout
│   │   ├── workspace.py           # Workspace CRUD
│   │   ├── projects.py            # Project CRUD
│   │   ├── sessions.py            # Session CRUD
│   │   ├── chat.py                # Chat with SSE streaming
│   │   ├── memory.py              # Memory CRUD, search
│   │   ├── ingest.py              # File upload, ingestion trigger
│   │   ├── provenance.py          # Provenance lookup, graph queries
│   │   ├── dashboard.py           # Workspace statistics
│   │   ├── feedback.py            # Response ratings
│   │   ├── api_keys.py            # API key CRUD
│   │   ├── storage.py             # Object storage operations
│   │   ├── policy.py              # Policy CRUD (Sprint 7)
│   │   └── audit.py               # Audit event queries
│   ├── services/                  # Business logic layer
│   │   ├── memory.py              # MemoryService
│   │   ├── pipeline.py            # M0→M5 orchestration
│   │   ├── chat_orchestrator.py   # Chat with retrieval + LLM
│   │   ├── m1_session.py          # Session understanding
│   │   ├── m2_facts.py            # Fact/decision extraction
│   │   ├── m3_temporal.py         # Temporal truth
│   │   ├── m4_graph.py            # Knowledge graph
│   │   ├── m5_retrieval.py        # BM25 + semantic retrieval
│   │   ├── retrieval.py           # Legacy retrieval
│   │   ├── llm.py                 # LLM provider abstraction
│   │   ├── connectors.py          # External source connectors
│   │   ├── tools.py               # Tool execution
│   │   ├── object_storage.py      # Storage interface
│   │   ├── object_storage_s3.py   # S3 implementation
│   │   ├── object_storage_minio.py # MinIO implementation
│   │   ├── audit/
│   │   │   ├── service.py         # AuditService (emit, persist, redact)
│   │   │   ├── repository.py      # AuditEvent DB persistence
│   │   │   └── constants.py       # Event types, redaction list
│   │   └── policy/
│   │       ├── engine.py          # PolicyEngine
│   │       ├── evaluator.py       # Rule evaluation
│   │       ├── repository.py      # Policy DB persistence
│   │       └── dependencies.py    # FastAPI dependency injection
│   ├── middleware/
│   │   ├── auth.py                # JWT extraction, user resolution
│   │   ├── tenancy.py             # Tenant context from token
│   │   ├── rbac.py                # Role-based access control
│   │   └── rate_limit.py          # Per-endpoint rate limiting
│   └── core/
│       ���── config.py              # Pydantic settings
│       └── security.py            # JWT + bcrypt
├── alembic/
│   ├── env.py                     # Migration environment
│   └── versions/                  # 11 migrations (001–011)
├── tests/
│   ├── conftest.py                # Test fixtures, DB setup
│   ├── unit/
│   │   ├── test_auth.py
│   │   ├── test_chat.py
│   │   ├── test_memory.py
│   │   ├── test_projects.py
│   │   ├── test_sessions.py
│   │   ├── test_tenancy.py
│   │   ├── test_workspace.py
│   │   ├── test_ingest.py
│   │   ├── test_pipeline.py
│   │   ├── test_services.py
│   │   ├── test_rate_limit.py
│   │   ├── test_storage.py
│   │   ├── test_api_keys.py
│   │   ├── test_provenance_explorer.py
│   │   ├── test_connectors.py
│   │   ├── test_pagination.py
│   │   ├── test_dashboard.py
│   │   ├── test_golden_dataset.py
│   │   ├── test_sprint3_e2e.py
│   │   ├── test_sprint4_e2e.py
│   │   ├── test_sprint4_golden.py
│   │   ├── test_sprint4_security.py
│   │   ├── test_sprint7_integration.py
│   │   ├── test_security_matrix.py
│   │   ├── test_security_6b.py
│   │   ├── test_authorization_audit.py
│   │   ├── test_rbac_security.py
│   │   ├── test_policy_engine.py
│   │   ├── test_policy_rbac_integration.py
│   │   ├── test_audit_api.py
│   │   ├── test_audit_service.py
│   │   ├── test_connector_security.py
│   │   ├── test_storage_security.py
│   │   ├── test_storage_api.py
│   │   ├── test_rate_limit_api.py
│   │   └── fixtures/
│   │       └── golden_dataset.py
│   └── unit/__init__.py
├── frontend/                      # Next.js application
├── requirements.txt               # Pinned dependencies
├── alembic.ini                    # Alembic configuration
├── Dockerfile                     # Multi-stage production build
├── docker-compose.yml             # App + PostgreSQL
├── .env.example                   # Environment template
├── .dockerignore                  # Image exclusions
└── DEPLOYMENT.md                  # Deployment runbook
```

---

## 2. Application Startup

### Entry Point
`app/main.py` — Defines the FastAPI application with:
1. Middleware stack (security headers, request ID, audit persistence, CORS, rate limiting)
2. API route registration (14 routers under `/api/v1/`)
3. Error handlers (validation, database, generic)
4. Health check endpoints
5. Lifespan context manager (logging setup, DB init, audit sink registration)

### Lifespan
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.environment == "development":
        setup_logging()           # Structured JSON logging
    await init_db()               # Create tables if not exist
    audit.register_db_sink()      # Wire PostgreSQL for audit events
    yield                         # App runs
    # Cleanup on shutdown
```

### Startup Sequence
1. Settings loaded from environment + `.env`
2. If production + default SECRET_KEY → ValueError (blocks startup)
3. Structured logging configured (development only)
4. Database engine created (asyncpg)
5. Tables created/verified via `init_db()`
6. Audit service registered with DB sink
7. FastAPI app starts accepting requests

---

## 3. Configuration

### Settings Class (`app/core/config.py`)
| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| app_name | str | "SwarmVault SaaS" | Application name |
| environment | str | "development" | Environment mode |
| debug | property | `environment != "production"` | Debug mode |
| is_production | property | `environment == "production"` | Production detection |
| database_url | str | postgresql+...localhost | PostgreSQL connection |
| secret_key | str | "change-me-in-production" | JWT signing key |
| algorithm | str | "HS256" | JWT algorithm |
| access_token_expire_minutes | int | 60 | Access token TTL |
| refresh_token_expire_days | int | 30 | Refresh token TTL |
| cors_origins | str | "*" | CORS origins (raw string) |
| cors_origins_list | property | ["*"] | Parsed CORS origins |
| cors_origins_safe | property | ["*"] | Production-safe CORS (no wildcard) |
| llm_provider | str | "anthropic" | LLM provider |
| llm_model | str | claude-sonnet-4-5 | LLM model |
| llm_max_tokens | int | 1024 | Max response tokens |
| llm_temperature | float | 0.7 | LLM temperature |
| llm_timeout_seconds | float | 30.0 | LLM timeout |
| llm_max_retries | int | 2 | LLM retry limit |
| llm_retry_backoff | float | 1.0 | Retry backoff factor |
| anthropic_api_key | str | "" | Anthropic API key |
| openai_api_key | str | "" | OpenAI API key |
| storage_backend | str | "filesystem" | Storage provider |
| storage_path | str | "./storage" | Filesystem storage path |
| rate_limit_login | int | 10 | Login rate limit (req/min) |
| rate_limit_chat | int | 30 | Chat rate limit |
| rate_limit_ingest | int | 5 | Ingest rate limit |
| rate_limit_search | int | 60 | Search rate limit |
| rate_limit_api | int | 100 | General API rate limit |

### Validators
- `_validate_secret_key`: Production blocks default SECRET_KEY; warns in development
- `cors_origins_list`: Parses comma-separated string or JSON array
- `cors_origins_safe`: Blocks wildcard (`*`) in production

---

## 4. Authentication

### Implementation (`app/core/security.py`)
| Function | Purpose |
|----------|---------|
| `hash_password(password)` | bcrypt hash |
| `verify_password(plain, hashed)` | bcrypt verify |
| `create_access_token(data)` | JWT encode (HS256, 60min) |
| `create_refresh_token(data)` | JWT encode (HS256, 30 days) |
| `decode_token(token)` | JWT decode + validation |

### Token Flow
```
Register/Login → access_token + refresh_token
Access token: 60 minutes, in Authorization header
Refresh token: 30 days, stored in DB (RefreshToken table)
Refresh: POST /auth/refresh → new access_token + new refresh_token (rotating)
Logout: POST /auth/logout → refresh token revoked
```

### Middleware (`app/middleware/auth.py`)
- Extracts JWT from `Authorization: Bearer <token>`
- Validates token
- Resolves user
- Attaches user to request state

---

## 5. Authorization (RBAC)

### Implementation (`app/middleware/rbac.py`)
- `require_min_role(role)` — dependency that checks user's minimum role
- Role hierarchy: owner > admin > member > viewer
- Evaluated after authentication, before service layer

### Actions
| Action | Description |
|--------|-------------|
| read | View resources |
| search | Search/query resources |
| write | Create resources |
| update | Modify resources |
| delete | Remove resources |
| execute | Run operations (e.g., ingest) |
| export | Export data |
| share | Share with others |

---

## 6. Middleware Stack

Execution order (outermost to innermost):
1. **SecurityHeadersMiddleware** — CSP, HSTS, X-Frame-Options, etc.
2. **RequestIdMiddleware** — X-Request-ID injection, latency tracking
3. **AuditPersistenceMiddleware** — Flush buffered audit events per request
4. **CORSMiddleware** — Origin validation
5. **RateLimitMiddleware** — Per-endpoint request limiting
6. **AuthMiddleware** — JWT extraction
7. **TenancyMiddleware** — Tenant context injection
8. **RBACMiddleware** — Role-based access (per-route)

---

## 7. Services

### MemoryService (`app/services/memory.py`)
The central service for memory operations. Every memory operation goes through this service, which:
1. Authenticates the user (via tenant context)
2. Checks RBAC permissions
3. Evaluates policy rules (Sprint 7)
4. Attaches provenance metadata
5. Emits audit events
6. Persists to PostgreSQL via repository

### ChatOrchestrator (`app/services/chat_orchestrator.py`)
Orchestrates the chat response pipeline:
1. Retrieves project/session context
2. Calls M5 retrieval for relevant memories
3. Builds bounded context pack
4. Calls LLM provider with context
5. Streams response (SSE)
6. Creates MessageProvenance record
7. Stores assistant message

### Pipeline (`app/services/pipeline.py`)
Orchestrates M0→M5 ingestion:
```
M0: normalize() → Source + NormalizedMessages
M1: understand_session() → session structure
M2: extract_facts() + extract_decisions() → Fact + Decision records
M3: supersede_fact() + supersede_decision() → temporal versioning
M4: extract_graph_elements() + persist_graph() → GraphNode + GraphEdge
```

### LLM Provider (`app/services/llm.py`)
Abstraction supporting:
- **AnthropicProvider** — AsyncAnthropic client
- **OpenAIProvider** — AsyncOpenAI client
- **MockProvider** — Testing/demo responses

Features: timeout, retry with backoff, graceful fallback.

### AuditService (`app/services/audit/service.py`)
- `emit(event_type, **kwargs)` — Create audit event (buffered)
- `persist(session)` — Flush buffered events to PostgreSQL
- Redacts sensitive fields before storage
- Supports correlation IDs for request tracing

---

## 8. Database

### Engine
- **SQLAlchemy 2.0** async ORM
- **asyncpg** driver
- **Alembic** migrations

### Connection (`app/db.py`)
- `async_engine` — AsyncEngine instance
- `async_session_factory` — Session factory
- `init_db()` — Create all tables (used in development/testing)

### Migrations (11 total)
| # | Migration | Purpose |
|---|-----------|---------|
| 001 | initial | Base tables (users, tenants, workspaces, sessions, messages, projects) |
| 002 | provenance | MessageProvenance table |
| 003 | sprint3_pipeline | Source, NormalizedMessage, Fact, Decision, IngestJob |
| 004 | memory_sprint4_columns | Memory model (M4 additions) |
| 005 | message_feedback | MessageFeedback table |
| 006 | temporal_graph | temporal_status on graph nodes/edges |
| 007 | api_keys | ApiKey table |
| 008 | source_content_hash | content_hash on Source for dedup |
| 009 | policy_engine | Policy, PolicyVersion tables |
| 010 | audit_events | AuditEvent table (11 indexes) |
| 011 | tenant_memory | tenant_id on Memory (P0 fix) |

---

## 9. Testing

### Test Infrastructure
- **pytest** 8.2.0 with pytest-asyncio 0.23.7
- **httpx** 0.27.0 for async HTTP testing
- Test fixtures in `tests/conftest.py` (database setup, test clients, golden dataset)
- 629 tests across 34 test files

### Test Categories
| Category | Files | Count |
|----------|-------|-------|
| Auth | test_auth.py | 11 |
| Chat | test_chat.py, test_chat_sprint2.py | — |
| Memory | test_memory.py | 5+ |
| Projects | test_projects.py | — |
| Sessions | test_sessions.py | — |
| Tenancy | test_tenancy.py | 16 |
| Workspace | test_workspace.py | — |
| Ingestion | test_ingest.py, test_pipeline.py, test_connectors.py | — |
| Security | test_security_matrix.py, test_security_6b.py, test_sprint4_security.py | 18+ |
| RBAC | test_rbac_security.py, test_authorization_audit.py | 52+ |
| Policy | test_policy_engine.py, test_policy_rbac_integration.py | 14+ |
| Storage | test_storage.py, test_storage_api.py, test_storage_security.py | — |
| Rate Limiting | test_rate_limit.py, test_rate_limit_api.py | 17+ |
| Provenance | test_provenance_explorer.py | 8+ |
| Golden Dataset | test_golden_dataset.py | — |
| E2E | test_sprint3_e2e.py, test_sprint4_e2e.py, test_sprint4_golden.py | 28+ |
| Integration | test_sprint7_integration.py | — |
| Audit | test_audit_api.py, test_audit_service.py | 28+ |

### Test Execution
```bash
python -m pytest tests/ -q --tb=short -p no:xdist
```
Baseline: 629 passed, 0 failed, 0 errors, ~155s
