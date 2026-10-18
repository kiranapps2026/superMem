# SwarmVault Codebase Index & Folder Structure

**Version:** 1.0.0
**Date:** 2026-09-24
**Branch:** recovery/restore-2026-09-24
**Authority:** Source code is the single source of truth. This document maps the codebase for navigation.

---

## Summary Statistics

| Metric | Value |
|---|---|
| Total source files (Python) | 53 |
| Total source files (TypeScript/TSX) | 56 |
| Total test files (Python) | 39 |
| Total test files (Playwright) | 9 |
| Total documentation files | 80+ |
| Python lines of code | ~13,050 |
| TypeScript/TSX lines of code | ~5,500 |
| E2E test lines | ~2,463 |
| **Total lines of code** | **~21,983** |
| Backend modules | 15 API routers, 18 service files (inc. audit/, policy/, predicate_policy, contradiction_detection), 4 middleware, 2 core |
| Frontend pages | 21 pages |
| Frontend UI components | 15 shadcn/ui components + Sidebar |
| Feature hooks | 7 custom hooks |
| Global hooks | 5 hooks (AppShell, AuthRedirect, useAuth, useSSE, useTheme) |
| Database tables | 24 models |
| Alembic migrations | 13 |

---

## Root-Level Files

| File | Lines | Purpose |
|---|---|---|
| `README.md` | — | Project overview, setup instructions |
| `requirements.txt` | — | Python dependencies |
| `package.json` | — | Node.js dependencies (frontend) |
| `package-lock.json` | — | Node.js lock file |
| `pytest.ini` | — | Pytest configuration |
| `alembic.ini` | — | Alembic migration config |
| `docker-compose.yml` | — | Docker services (PostgreSQL, MinIO, etc.) |
| `Dockerfile` | — | Container build definition |
| `.env` | — | Environment variables (production) |
| `.env.example` | — | Environment variable template |
| `.gitignore` | — | Git ignore rules |

---

## Backend Structure: `app/`

### Directory Tree

```
app/
  __init__.py              # Package marker
  main.py                  # FastAPI app, middleware, routers, health checks (279 lines)
  db.py                    # SQLAlchemy engine, session factory, migrations (46 lines)
  models.py                # 24 SQLAlchemy ORM models (880 lines)
  schemas.py               # Pydantic request/response schemas (602 lines)

  api/                     # HTTP endpoint routers (14 routers, 78 endpoints)
    __init__.py            # Package marker
    auth.py                # Registration, login, refresh, logout, me (265 lines)
    workspace.py           # Members, invitations, workspace CRUD (447 lines)
    projects.py            # Project list, create, delete (120 lines)
    sessions.py            # Session list, detail, messages (162 lines)
    chat.py                # Chat completion, streaming (275 lines)
    memory.py              # Memory CRUD, semantic search (303 lines)
    ingest.py              # Upload, pipeline trigger, facts, decisions, graph, search (615 lines)
    provenance.py          # Trace history, full trace (148 lines)
    dashboard.py           # Stats, recent activity (208 lines)
    feedback.py            # Like/dislike on messages (99 lines)
    api_keys.py            # API key CRUD (278 lines)
    storage.py             # Presigned URLs, file listing (147 lines)
    policy.py              # Policy CRUD (333 lines)
    audit.py               # Audit log query (192 lines)

  core/                    # Core framework utilities
    __init__.py            # Package marker
    config.py              # Settings class, validators, properties (166 lines)
    security.py            # JWT encode/decode, password hashing (37 lines)

  middleware/              # Request/response processing (4 middleware)
    __init__.py            # Package marker
    auth.py                # JWT Bearer token validation (51 lines)
    rate_limit.py          # In-memory sliding window rate limiter (119 lines)
    rbac.py                # Role-based access control (140 lines)
    tenancy.py             # Cross-tenant isolation, TenantContext (140 lines)

  services/                # Business logic layer (18 services)
    audit.py               # Audit event constants (emitter wrapper) (305 lines)
    audit/                 # Audit service package
      __init__.py          # Re-exports
      constants.py         # Event type constants (e.g., INGEST_COMPLETED)
      repository.py        # AuditRepository for DB persistence
      service.py           # AuditService: buffer, emit, persist (305 lines)
    chat_orchestrator.py   # End-to-end chat: retrieval → LLM → provenance (152 lines)
    connectors.py          # M0: 7 format connectors + registry (760 lines)
    llm.py                 # LLM provider abstraction + factory (401 lines)
    m1_session.py          # M1: Topic/entity/intent extraction (139 lines)
    m2_facts.py            # M2: Fact + decision extraction (177 lines)
    m3_temporal.py         # M3: Fact/decision supersession (202 lines)
    m4_graph.py            # M4: Graph node/edge extraction + persistence (192 lines)
    m5_retrieval.py        # M5: Multi-factor ranking + Phase 3 reranking (344 lines)
    memory.py              # Memory service: governed access, policy enforcement (1045 lines)
    object_storage.py      # Unified storage interface (141 lines)
    object_storage_s3.py   # AWS S3 backend (84 lines)
    object_storage_minio.py # MinIO backend (85 lines)
    pipeline.py            # M0-M5 orchestration, state machine (238 lines)
    policy/                # Policy engine package
      __init__.py          # Re-exports
      dependencies.py      # FastAPI dependencies for policy
      engine.py            # PolicyEngine: rule evaluation
      evaluator.py         # RBAC policy generator
      repository.py        # PolicyRepository for DB
    predicate_policy.py    # Predicate conflict policy engine (315 lines)
    contradiction_detection.py # Phase 5: contradiction detection (380 lines)
    retrieval.py           # Hybrid vector + keyword retrieval (121 lines)
    reranking.py           # Phase 3: LLM-based retrieval reranking (280 lines)
    tools.py               # Function calling tools for LLM (473 lines)
```

### Backend Layer Diagram

```
app/
  │
  ├── main.py                    ← Application entry, middleware stack, router registration
  │     ├── SecurityHeaders      ← CSP, HSTS, X-Frame-Options
  │     ├── RequestId            ← X-Request-ID, latency
  │     ├── AuditPersistence     ← Flush audit buffer per-request
  │     ├── CORS                 ← Origin restriction
  │     ├── RateLimit            ← Sliding window
  │     ├── Tenancy              ← Cross-tenant isolation
  │     ├── Auth                 ← JWT validation
  │     ├── RBAC                 ← Role enforcement
  │     ├── 14 routers           ← api/*.py
  │     └── 3 health endpoints   ← /health, /health/live, /health/ready
  │
  ├── db.py                      ← Engine, session factory, init_db()
  │     └── Base                 ← DeclarativeBase for all models
  │
  ├── models.py                  ← 24 SQLAlchemy models
  │
  ├── schemas.py                 ← Pydantic schemas (request/response)
  │
  ├── core/
  │     ├── config.py            ← Settings (22 config fields, 2 validators)
  │     └── security.py          ← JWT encode/decode, password hash
  │
  ├── middleware/
  │     ├── auth.py              ← JWT Bearer → User
  │     ├── rate_limit.py        ← IP-based sliding window
  │     ├── rbac.py              ← Role permission matrix
  │     └── tenancy.py           ← JWT → TenantContext
  │
  ├── api/                       ← 14 routers (78 endpoints)
  │     ├── auth.py              ← 6 endpoints
  │     ├── workspace.py         ← 14 endpoints
  │     ├── projects.py          ← 5 endpoints
  │     ├── sessions.py          ← 6 endpoints
  │     ├── chat.py              ← 2 endpoints
  │     ├── memory.py            ← 6 endpoints
  │     ├── ingest.py            ← 14 endpoints
  │     ├── provenance.py        ← 3 endpoints
  │     ├── dashboard.py         ← 2 endpoints
  │     ├── feedback.py          ← 3 endpoints
  │     ├── api_keys.py          ← 4 endpoints
  │     ├── storage.py           ← 3 endpoints
  │     ├── policy.py            ← 7 endpoints
  │     └── audit.py             ← 3 endpoints
  │
  └── services/                  ← 18 services
        ├── audit/               ← Event constants, repository, buffered service
        ├── pipeline.py          ← M0-M5 orchestration
        ├── connectors.py        ← 7 format parsers + registry
        ├── m1_session.py        ← Session understanding
        ├── m2_facts.py          ← Fact + decision extraction
        ├── m3_temporal.py       ← Temporal supersession
        ├── m4_graph.py          ← Graph persistence
        ├── m5_retrieval.py      ← Multi-factor ranking
        ├── chat_orchestrator.py ← Chat end-to-end flow
        ├── llm.py               ← Provider abstraction (4 providers)
        ├── memory.py            ← Governed memory access
        ├── retrieval.py         ← Hybrid vector + keyword
        ├── object_storage.py    ← Unified storage
        ├── object_storage_s3.py ← S3 backend
        ├── object_storage_minio.py ← MinIO backend
        ├── policy/              ← Policy engine
        └── tools.py             ← LLM function calling
```

### Backend File Dependency Graph

```
main.py
  ├── core/config.py
  ├── core/security.py
  ├── db.py → models.py, alembic
  ├── middleware/auth.py → core/security.py, models.py, db.py
  ├── middleware/rate_limit.py → core/config.py
  ├── middleware/rbac.py → models.py, tenancy.py
  ├── middleware/tenancy.py → models.py, db.py, core/config.py
  ├── services/audit/service.py → models.py
  ├── api/*.py → db.py, models.py, schemas.py, services/*, middleware/*
  │     ├── ingest.py → services/pipeline.py → connectors.py, m1-m4, m5
  │     ├── chat.py → services/chat_orchestrator.py → llm.py, m5_retrieval.py, models.py
  │     ├── memory.py → services/memory.py → policy/engine.py, audit/
  │     └── ...
  └── services/llm.py → core/config.py (standalone providers)
```

---

## Database Migrations: `alembic/`

### Directory Tree

```
alembic/
  env.py                    # Async migration environment (imports app.models)
  script.py.mako            # Migration file template
  versions/
    001_initial.py           # tenants, workspaces, users, workspace_members, refresh_tokens
    002_provenance.py        # message_provenance table
    003_sprint3_pipeline.py  # sessions, messages, normalized_messages, sources, ingest_jobs
    004_add_memory_sprint4_columns.py  # memory table columns
    005_add_message_feedback.py        # message_feedback table
    006_add_temporal_to_graph_nodes.py # graph_node_temporal table
    007_add_api_keys.py       # api_keys table
    008_add_source_content_hash.py     # sources.content_hash
    009_add_policy_engine.py  # policies, policy_versions tables
    010_add_audit_events.py   # audit_events table
    011_add_tenant_to_memory.py # tenant_id on memory, facts
    012_add_invitations.py    # invitations table
```

### Migration Dependency Chain

```
001 (base schema)
  ├── 002 (provenance)
  │     ├── 003 (pipeline tables)
  │     │     ├── 004 (memory columns)
  │     │     │     ├── 005 (feedback)
  │     │     │     │     ├── 006 (temporal graph)
  │     │     │     │     │     ├── 007 (API keys)
  │     │     │     │     │     │     ├── 008 (source hash)
  │     │     │     │     │     │     │     ├── 009 (policy engine)
  │     │     │     │     │     │     │     │     ├── 010 (audit events)
  │     │     │     │     │     │     │     │     │     ├── 011 (tenant on memory/facts)
  │     │     │     │     │     │     │     │     │     │     └── 012 (invitations)
```

---

## Test Suite: `tests/`

### Directory Tree

```
tests/
  __init__.py               # Package marker
  conftest.py               # Pytest fixtures (client, seeded_workspace, etc.)
  phase10_runtime.py        # Phase 10 runtime test

  unit/
    __init__.py             # Package marker
    fixtures/
      golden_dataset.py     # Golden test data

    test_api_keys.py        # 143 lines — API key CRUD tests
    test_audit_api.py       # — Audit endpoint tests
    test_audit_service.py   # — Audit service buffer tests
    test_auth.py            # — Registration, login, refresh, logout
    test_authorization_audit.py # — Authorization audit tests
    test_capability_e2e.py  # — End-to-end capability tests
    test_chat.py            # — Chat completion tests
    test_chat_sprint2.py    # — LLM provider instantiation, streaming
    test_connector_security.py # — Malicious input, size limits
    test_connectors.py      # — M0 connector tests (all formats)
    test_dashboard.py       # — Dashboard stats, recent activity
    test_golden_dataset.py  # — Golden dataset validation
    test_ingest.py          # — Ingestion endpoint tests
    test_memory.py          # — Memory service tests (34 lines)
    test_pagination.py      # — Pagination tests
    test_pipeline.py        # — M0-M2 pipeline tests (226 lines)
    test_policy_engine.py   # — Policy evaluation tests
    test_policy_rbac_integration.py # — Policy + RBAC integration
    test_projects.py        # — Project CRUD tests
    test_provenance_explorer.py # — Provenance tests
    test_rate_limit.py      # — Rate limiter unit tests
    test_rate_limit_api.py  # — Rate limit API tests
    test_rbac_security.py   # — RBAC security tests
    test_remediation.py     # — Remediation tests
    test_security_6b.py     # — Security test suite (6b)
    test_security_matrix.py # — Security matrix tests
    test_services.py        # — Service layer tests
    test_sessions.py        # — Session tests
    test_sprint3_e2e.py     # — Sprint 3 E2E: ingest, temporal, M5, chat, security (616 lines)
    test_sprint4_e2e.py     # — Sprint 4 E2E: memory, facts, decisions (724 lines)
    test_sprint4_golden.py  # — Sprint 4 golden dataset (259 lines)
    test_sprint4_security.py # — Sprint 4 security (783 lines)
    test_sprint7_integration.py # — Sprint 7 integration
    test_storage.py         # — Storage service tests
    test_storage_api.py     # — Storage API tests (143 lines)
    test_storage_security.py # — Storage security tests (152 lines)
    test_tenancy.py         # — Tenancy isolation tests (79 lines)
    test_workspace.py       # — Workspace CRUD tests (83 lines)
```

### Test-to-Source Mapping

| Test File | Tests | Source Under Test | Lines |
|---|---|---|---|
| `test_pipeline.py` | 26 | `services/connectors.py`, `services/m1_session.py`, `services/m2_facts.py` | 226 |
| `test_sprint3_e2e.py` | 11 | `api/ingest.py`, `services/pipeline.py`, `services/m3_temporal.py`, `services/m5_retrieval.py`, `services/chat_orchestrator.py` | 616 |
| `test_sprint4_e2e.py` | 10 | `api/memory.py`, `services/memory.py`, `api/ingest.py` | 724 |
| `test_sprint4_golden.py` | 8 | Full pipeline golden dataset | 259 |
| `test_sprint4_security.py` | 15 | Cross-tenant, injection, auth bypass | 783 |
| `test_connectors.py` | 15 | `services/connectors.py` | — |
| `test_connector_security.py` | 5 | `services/connectors.py` security | — |
| `test_auth.py` | 8 | `api/auth.py`, `middleware/auth.py` | — |
| `test_chat.py` | 6 | `api/chat.py`, `services/chat_orchestrator.py` | — |
| `test_chat_sprint2.py` | 5 | `services/llm.py` providers | — |
| `test_tenancy.py` | 5 | `middleware/tenancy.py` | 79 |
| `test_rbac_security.py` | 8 | `middleware/rbac.py` | — |
| `test_rate_limit.py` | 4 | `middleware/rate_limit.py` | — |
| `test_rate_limit_api.py` | 4 | Rate limit API | — |
| `test_workspace.py` | 6 | `api/workspace.py` | 83 |
| `test_projects.py` | 5 | `api/projects.py` | — |
| `test_sessions.py` | 4 | `api/sessions.py` | — |
| `test_ingest.py` | 5 | `api/ingest.py` | — |
| `test_memory.py` | 4 | `services/memory.py` | 34 |
| `test_dashboard.py` | 3 | `api/dashboard.py` | — |
| `test_api_keys.py` | 6 | `api/api_keys.py` | 143 |
| `test_audit_api.py` | 4 | `api/audit.py` | — |
| `test_audit_service.py` | 5 | `services/audit/service.py` | — |
| `test_policy_engine.py` | 6 | `services/policy/engine.py` | — |
| `test_policy_rbac_integration.py` | 5 | `services/policy/` + `middleware/rbac.py` | — |
| `test_provenance_explorer.py` | 4 | `api/provenance.py` | — |
| `test_storage.py` | 4 | `services/object_storage*.py` | — |
| `test_storage_api.py` | 5 | `api/storage.py` | 143 |
| `test_storage_security.py` | 5 | Storage security | 152 |
| `test_services.py` | 4 | `services/llm.py`, `services/tools.py` | — |
| `test_security_6b.py` | 6 | Security matrix | — |
| `test_security_matrix.py` | 5 | Security coverage | — |
| `test_authorization_audit.py` | 4 | Audit authorization | — |
| `test_capability_e2e.py` | 4 | Full capability flow | — |
| `test_remediation.py` | 3 | Remediation | — |
| `test_pagination.py` | 3 | Pagination | — |
| `test_golden_dataset.py` | 3 | Golden dataset | — |
| `test_sprint7_integration.py` | 3 | Sprint 7 integration | — |

**Total: 38 test files, ~670 tests pass (1 environmental: missing `openai` package)**

---

## Frontend Structure: `frontend/`

### Root-Level Config

| File | Purpose |
|---|---|
| `package.json` | Dependencies, scripts |
| `package-lock.json` | Lock file |
| `next.config.js` | Next.js config (Turbopack) |
| `next.config.mjs` | Next.js config (ESM) |
| `tsconfig.json` | TypeScript config |
| `tsconfig.e2e.json` | TypeScript config for E2E |
| `tailwind.config.js` | Tailwind CSS config |
| `postcss.config.js` | PostCSS config |
| `.eslintrc.js` | ESLint config |
| `.env.local` | Frontend env vars |
| `next-env.d.ts` | Next.js TypeScript declarations |

### Directory Tree

```
frontend/
  src/
    app/                          # Next.js App Router (21 pages)
      layout.tsx                  # Root layout: ThemeProvider → AuthProvider → AppShell (33 lines)
      page.tsx                    # Landing page (public)
      auth/
        login/page.tsx            # Sign in (public)
        register/page.tsx         # Sign up (public)
      dashboard/
        page.tsx                  # Home dashboard (protected)
      projects/
        page.tsx                  # Project list (protected)
        [id]/
          layout.tsx              # Project layout: sidebar wrapper
          chat/page.tsx           # AI chat
          decisions/page.tsx      # Extracted decisions
          facts/page.tsx          # Extracted facts
          graph/page.tsx          # Knowledge graph
          ingest/page.tsx         # Upload + ingest
          memory/page.tsx         # Semantic search
          provenance/page.tsx     # Trace history
          search/page.tsx         # Hybrid search
          sessions/
            page.tsx             # Conversation list
            [sessionId]/page.tsx # Conversation detail
          settings/page.tsx       # Project settings
          timeline/page.tsx       # Chronological view
      settings/
        page.tsx                  # Settings hub
        api-keys/page.tsx         # API key management
        profile/page.tsx          # Profile edit
        storage/page.tsx          # Storage config

    components/
      Sidebar.tsx                 # Responsive navigation sidebar (global + project) (181 lines)
      ui/                         # shadcn/ui component library (15 components)
        Badge.tsx                 # Status/color indicator
        Card.tsx                  # Content card
        Collapsible.tsx           # Expandable section
        ConfirmDialog.tsx         # Confirmation modal
        EmptyState.tsx            # No-data placeholder
        ErrorAlert.tsx            # Error display
        FileInput.tsx             # File upload
        LoadingSpinner.tsx        # Loading indicator
        Pagination.tsx            # Page navigation
        Progress.tsx              # Progress bar
        Skeleton.tsx              # Loading placeholder
        StatCard.tsx              # KPI metric card
        Tabs.tsx                  # Tab navigation
        Toast.tsx                 # Notification
        Tooltip.tsx               # Hover tooltip
        index.ts                  # Barrel export

    features/                     # Feature-specific hooks (7 hooks)
      apiKeys/useApiKeys.ts       # API key CRUD state
      chat/useChat.ts             # Chat message state
      graph/useGraph.ts           # Knowledge graph state
      ingest/useIngest.ts         # Ingestion job state
      memory/useMemory.ts         # Memory search state
      projects/useProjects.ts     # Project CRUD state
      search/useSearch.ts         # Hybrid search state

    hooks/                        # Global hooks (5 hooks)
      AppShell.tsx                # Layout wrapper (sidebar + content)
      AuthRedirect.tsx            # Route guard (redirect if not auth)
      useAuth.tsx                 # Auth context (login, logout, register)
      useSSE.tsx                  # Server-sent events connection
      useTheme.tsx                 # Theme context (light/dark)

    lib/                          # Utilities
      api.ts                      # Fetch wrapper with auth + refresh (171 lines)
      errors.ts                   # APIError, AuthError, NetworkError (99 lines)

    types/
      api.ts                      # TypeScript interfaces (203 lines)

  e2e/                            # Playwright E2E tests (9 active spec files)
    global-setup.ts              # Browser launch config
    test-helpers.ts              # Shared fixtures, API key setup
    remaining-contracts.spec.ts  # 104 tests — network contracts, responsive, a11y
    ui-certification.spec.ts     # 22 tests — UI rendering, network contracts
    search-chat-certification.spec.ts # 19 tests — search + chat flows
    frontend-journey.spec.ts     # 4 tests — full user journeys
    golden-journey.spec.ts       # 14 tests — golden path scenarios
    api-e2e.spec.ts              # 14 tests — direct API tests
    auth.spec.ts                 # 7 tests — auth flows
    dashboard.spec.ts            # 3 tests — dashboard rendering
    _archive/                    # Archived diagnostic tests
      debug-auth.spec.ts
      test-diag.spec.ts

  playwright.config.ts           # Playwright config (with webServer)
  playwright.config.no-server.ts # Playwright config (no webServer, for R3)
```

### Frontend File Dependency Graph

```
app/layout.tsx (RootLayout)
  ├── hooks/useTheme.tsx (ThemeProvider)
  ├── hooks/useAuth.tsx (AuthProvider)
  └── hooks/AppShell.tsx (AppShell)
        ├── components/Sidebar.tsx
        │     ├── components/ui/Tooltip.tsx
        │     └── lucide-react (32 icons)
        └── {children} → page components

page components (app/*/page.tsx)
  ├── lib/api.ts (fetch wrapper)
  │     ├── hooks/useAuth.tsx (getToken)
  │     └── localStorage (sv_tokens)
  ├── features/*/use*.ts (custom hooks)
  │     └── lib/api.ts
  ├── components/ui/* (shadcn/ui)
  └── types/api.ts (TypeScript interfaces)
```

---

## Documentation: `docs/`

### Architecture Documents (created by this session)

| Document | Lines | Purpose |
|---|---|---|
| `SWARMVAULT_DOMAIN_MANIFEST.md` | 670 | Complete domain model, entities, pipeline, API, features, guardrails, tables, security, audit |
| `SWARMVAULT_BACKEND_ARCHITECTURE.md` | 750 | Backend architecture: system, bootstrap, DB, LLM, pipeline, middleware, tenancy, security, config, observability, data flows |
| `SWARMVAULT_FRONTEND_SCREENS.md` | 561 | Frontend: shell, 21 screens, components, state, data fetching, routing, theming, build, E2E |
| `SWARMVAULT_CODEBASE_INDEX.md` | — | This document: complete file tree, line counts, dependencies |

### Existing Documentation

| Document | Purpose |
|---|---|
| `DOCUMENTATION/01_MASTER_ARCHITECTURE.md` | Original architecture doc |
| `DOCUMENTATION/02_PRODUCT_AND_CAPABILITY_CATALOG.md` | Feature catalog |
| `DOCUMENTATION/03_BACKEND_IMPLEMENTATION_REFERENCE.md` | Backend reference |
| `DOCUMENTATION/04_MEMORY_KNOWLEDGE_AND_M0-M5.md` | Pipeline deep-dive |
| `DOCUMENTATION/05_API_CONTRACT_REFERENCE.md` | API contract |
| `DOCUMENTATION/06_FRONTEND_ARCHITECTURE.md` | Frontend architecture |
| `DOCUMENTATION/07_SECURITY_REFERENCE.md` | Security reference |
| `DOCUMENTATION/08_MIDDLEWARE_REFERENCE.md` | Middleware reference |
| `DOCUMENTATION/09_TESTING_STRATEGY.md` | Testing strategy |
| `DOCUMENTATION/10_DATABASE_REFERENCE.md` | Database reference |
| `Reactivation prompt.md` | Recovery procedure |
| `RECOVERY_PROGRESS.md` | Phase G → R1 → R2 → R3 → R5 log |
| `RECOVERY_R3_FRONTEND_STATE.md` | R3 frontend verification report |

---

## Other Directories

| Directory | Contents |
|---|---|
| `CERTIFICATION/` | Deployment, production, and final certification documents |
| `DOCUMENTATION/` | 10 original architecture documents |
| `alembic/` | Database migration system |
| `storage/` | Runtime file storage (minIO/S3/filesystem) |
| `.claude/` | Claude Code config (CLAUDE.md, settings, hooks) |
| `.vexp/` | vexp index (codebase search) |

---

## File Size Reference

### Backend (Python)

| File | Lines | Category |
|---|---|---|
| `app/models.py` | 835 | Data layer |
| `app/schemas.py` | 602 | Data layer |
| `app/services/memory.py` | 1045 | Service layer |
| `app/services/connectors.py` | 760 | Service layer |
| `app/services/llm.py` | 401 | Service layer |
| `app/services/tools.py` | 473 | Service layer |
| `app/services/m5_retrieval.py` | 294 | Service layer |
| `app/services/m4_graph.py` | 192 | Service layer |
| `app/api/ingest.py` | 615 | API layer |
| `app/api/workspace.py` | 447 | API layer |
| `app/api/policy.py` | 333 | API layer |
| `app/api/memory.py` | 303 | API layer |
| `app/api/chat.py` | 275 | API layer |
| `app/api/auth.py` | 265 | API layer |
| `app/api/dashboard.py` | 208 | API layer |
| `app/services/pipeline.py` | 238 | Service layer |
| `app/services/m3_temporal.py` | 202 | Service layer |
| `app/main.py` | 279 | Framework |
| `app/services/audit/service.py` | 318 | Service layer |
| `app/core/config.py` | 166 | Core |
| `app/services/m2_facts.py` | 177 | Service layer |
| `app/api/audit.py` | 192 | API layer |
| `app/api/sessions.py` | 162 | API layer |
| `app/api/api_keys.py` | 278 | API layer |
| `app/api/provenance.py` | 148 | API layer |
| `app/api/storage.py` | 147 | API layer |
| `app/api/projects.py` | 120 | API layer |
| `app/api/feedback.py` | 99 | API layer |
| `app/middleware/rbac.py` | 140 | Middleware |
| `app/middleware/tenancy.py` | 140 | Middleware |
| `app/middleware/rate_limit.py` | 119 | Middleware |
| `app/services/chat_orchestrator.py` | 152 | Service layer |
| `app/services/retrieval.py` | 121 | Service layer |
| `app/middleware/auth.py` | 51 | Middleware |
| `app/core/security.py` | 37 | Core |
| `app/db.py` | 46 | Framework |
| `app/services/m1_session.py` | 139 | Service layer |
| `app/services/object_storage.py` | 141 | Service layer |
| `app/services/audit/repository.py` | — | Service layer |
| `app/services/audit/constants.py` | — | Service layer |
| `app/services/object_storage_s3.py` | 84 | Service layer |
| `app/services/object_storage_minio.py` | 85 | Service layer |

### Frontend (TypeScript/TSX)

| File | Lines | Category |
|---|---|---|
| `src/types/api.ts` | 203 | Types |
| `src/lib/api.ts` | 171 | Data fetching |
| `src/lib/errors.ts` | 99 | Error handling |
| `src/hooks/useAuth.tsx` | — | Auth context |
| `src/hooks/useTheme.tsx` | 64 | Theme context |
| `src/hooks/AppShell.tsx` | — | Layout wrapper |
| `src/hooks/AuthRedirect.tsx` | — | Route guard |
| `src/hooks/useSSE.tsx` | — | SSE |
| `src/components/Sidebar.tsx` | 181 | Navigation |
| `src/features/*/use*.ts` | — | Feature hooks (7 files) |
| `src/app/*/page.tsx` | — | Page components (21 files) |
| `src/components/ui/*.tsx` | — | UI components (15 files) |

### E2E Tests (Playwright)

| File | Tests | Lines |
|---|---|---|
| `e2e/remaining-contracts.spec.ts` | 120 | ~800 |
| `e2e/ui-certification.spec.ts` | 22 | 315 |
| `e2e/search-chat-certification.spec.ts` | 19 | — |
| `e2e/golden-journey.spec.ts` | 14 | — |
| `e2e/api-e2e.spec.ts` | 14 | — |
| `e2e/auth.spec.ts` | 7 | — |
| `e2e/frontend-journey.spec.ts` | 4 | — |
| `e2e/dashboard.spec.ts` | 3 | — |
| `e2e/_r3-route-sweep.spec.ts` | 22 | 129 |

---

## Module Cross-Reference

### Which Services Call Which

| Caller | Calls | Purpose |
|---|---|---|
| `pipeline.py` | `connectors.py` (normalize) | M0: format detection + parsing |
| `pipeline.py` | `m1_session.py` (understand_session) | M1: topic/entity extraction |
| `pipeline.py` | `m2_facts.py` (run_m2) | M2: fact + decision extraction |
| `pipeline.py` | `m3_temporal.py` (inline, supersede) | M3: dedup + supersession |
| `pipeline.py` | `m4_graph.py` (extract_graph_elements, persist_graph) | M4: graph persistence |
| `chat_orchestrator.py` | `m5_retrieval.py` (retrieve_for_chat) | M5: hybrid search for chat |
| `chat_orchestrator.py` | `llm.py` (get_llm_provider) | LLM call |
| `chat_orchestrator.py` | `models.py` (MessageProvenance) | Provenance persistence |
| `llm.py` | `core/config.py` (settings) | Provider config |
| `memory.py` | `policy/engine.py` | Authorization checks |
| `memory.py` | `audit/` | Event emission |
| `retrieval.py` | `models.py` (Memory) | Memory query |
| `m5_retrieval.py` | `models.py` (Fact, Decision, GraphEdge) | Ranking queries |
| `m4_graph.py` | `models.py` (GraphNode, GraphEdge) | Graph persistence |
| `m3_temporal.py` | `models.py` (Fact, Decision) | Supersession |

### Which API Routes Call Which Services

| Router | Service Called | Purpose |
|---|---|---|
| `api/ingest.py` | `pipeline.run_pipeline` | Full M0-M5 ingestion |
| `api/ingest.py` | `m5_retrieval.retrieve_hybrid` | Search endpoint |
| `api/chat.py` | `chat_orchestrator.process_chat` | End-to-end chat |
| `api/memory.py` | `memory.py` (MemoryService) | Memory CRUD + search |
| `api/memory.py` | `retrieval.retrieve_memories` | Hybrid memory retrieval |
| `api/sessions.py` | Direct model access | Session CRUD |
| `api/provenance.py` | Direct model access | Provenance queries |
| `api/dashboard.py` | Direct model access | Stats aggregation |
| `api/feedback.py` | Direct model access | Feedback CRUD |
| `api/api_keys.py` | Direct model access + security hash | Key management |
| `api/storage.py` | `object_storage.py` | Presigned URLs |
| `api/policy.py` | `policy/engine.py` | Policy evaluation |
| `api/audit.py` | `audit/service.py` | Audit queries |

---

## Configuration Surface

### Backend Environment Variables (app/core/config.py)

| Variable | Default | Category |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://swarmvault:swarmvault@localhost:5432/swarmvault` | Database |
| `SECRET_KEY` | `dev-insecure-default-change-in-production-123` | Auth |
| `ALGORITHM` | `HS256` | Auth |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Auth |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Auth |
| `ANTHROPIC_API_KEY` | `""` | LLM |
| `OPENAI_API_KEY` | `""` | LLM |
| `DEEPSEEK_API_KEY` | `""` | LLM |
| `LLM_PROVIDER` | `anthropic` | LLM |
| `LLM_MODEL` | `claude-sonnet-4-5-20250929` | LLM |
| `LLM_MAX_TOKENS` | `1024` | LLM |
| `LLM_TEMPERATURE` | `0.7` | LLM |
| `LLM_TIMEOUT_SECONDS` | `30.0` | LLM |
| `LLM_MAX_RETRIES` | `2` | LLM |
| `LLM_RETRY_BACKOFF` | `1.0` | LLM |
| `CORS_ORIGINS` | `*` | CORS |
| `LOG_LEVEL` | `INFO` | Observability |
| `ENABLE_METRICS` | `false` | Observability |
| `RATE_LIMIT_LOGIN` | `10` | Rate limit |
| `RATE_LIMIT_CHAT` | `30` | Rate limit |
| `RATE_LIMIT_INGEST` | `5` | Rate limit |
| `RATE_LIMIT_SEARCH` | `60` | Rate limit |
| `RATE_LIMIT_API` | `100` | Rate limit |
| `STORAGE_BACKEND` | `filesystem` | Storage |
| `STORAGE_PATH` | `./storage` | Storage |
| `S3_ENDPOINT` | `""` | Storage |
| `S3_ACCESS_KEY` | `""` | Storage |
| `S3_SECRET_KEY` | `""` | Storage |
| `S3_BUCKET` | `swarmvault-uploads` | Storage |
| `S3_REGION` | `us-east-1` | Storage |
| `ENVIRONMENT` | `development` | App |

### Frontend Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API base URL |

---

## Build Artifacts (excluded from source)

| Path | Contents |
|---|---|
| `node_modules/` | npm dependencies |
| `frontend/.next/` | Next.js build output |
| `__pycache__/` | Python bytecode |
| `.pytest_cache/` | Pytest cache |
| `.mypy_cache/` | MyPy cache |
| `.ruff_cache/` | Ruff cache |
| `storage/` | Runtime file storage |
| `.vexp/` | vexp search index |
| `.venv/` | Python virtual environment |
| `test-results/` | Playwright test results |

---

## Technology Stack Summary

### Backend

| Component | Technology | Version |
|---|---|---|
| Language | Python | 3.x |
| Framework | FastAPI | Latest |
| ASGI | uvicorn | — |
| ORM | SQLAlchemy 2.0 (async) | — |
| Database Driver | asyncpg | — |
| Database | PostgreSQL | — |
| Migrations | Alembic | — |
| Auth | python-jose (JWT) | — |
| Password | passlib (bcrypt) | — |
| LLM SDK | anthropic, openai | — |
| Settings | pydantic-settings | — |
| Storage | boto3 (S3/MinIO) | — |
| Testing | pytest | — |

### Frontend

| Component | Technology | Version |
|---|---|---|
| Framework | Next.js | 15.5.24 |
| Language | TypeScript | 5.x |
| Styling | CSS Modules + CSS Variables | — |
| UI Library | shadcn/ui | — |
| Icons | lucide-react | — |
| Build | Turbopack | — |
| Testing | Playwright | — |
| Linting | ESLint | — |

---

*This document is the canonical map of the SwarmVault codebase. When files are added, moved, or removed, this document is updated to match.*
