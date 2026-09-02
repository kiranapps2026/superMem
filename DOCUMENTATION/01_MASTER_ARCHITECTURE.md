# SwarmVault WebApp — Master Architecture
**Version:** 1.0.0
**Date:** 2026-09-01
**Evidence base:** Repository inspection (commit 902d85e), 629 tests, 11 migrations, certification artifacts

---

## 1. System Identity

### 1.1 Product Name
**SwarmVault WebApp**

### 1.2 Purpose
SwarmVault WebApp is a multi-tenant SaaS application that captures, processes, stores, and retrieves organizational knowledge from cloud/Claude sessions, documents, decisions, and agent activity. It converts scattered conversations into durable, queryable, evidence-backed organizational memory.

### 1.3 Problem Solved
Organizations lose knowledge when sessions end, people change, or agents restart. SwarmVault preserves that knowledge as structured, retrievable, auditable intelligence — not just document archives.

### 1.4 Target Users
- Knowledge workers who need to retrieve organizational knowledge
- Teams using Claude/cloud sessions for work
- Agents that need persistent context across sessions
- Administrators managing organizational memory

### 1.5 Product Boundaries
**SwarmVault WebApp provides:**
- Multi-tenant knowledge capture and retrieval
- Conversation ingestion and intelligence extraction (M0–M5)
- Chat with evidence-backed, provenance-tracked responses
- Knowledge graph construction and traversal
- Temporal fact management (current vs. superseded truth)
- API key management for external agent integration
- Audit logging of all sensitive operations

**SwarmVault WebApp does NOT provide (based on available evidence):**
- Email/Slack/calendar integration (NOT ESTABLISHED IN AVAILABLE SOURCE)
- Document authoring (Google Docs/Sheets/Slides) (NOT ESTABLISHED IN AVAILABLE SOURCE)
- Video conferencing (NOT ESTABLISHED IN AVAILABLE SOURCE)
- Public-facing marketing site (NOT ESTABLISHED — only a single landing page exists)
- User-facing billing/subscription management (NOT ESTABLISHED IN AVAILABLE SOURCE)

### 1.6 System Boundaries
```
┌─────────────────────────────────────────────────────────┐
│                    SwarmVault WebApp                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ Frontend │  │ Backend  │  │ PostgreSQL Database  │  │
│  │ (Next.js)│  │ (FastAPI)│  │                      │  │
│  └────┬─────┘  └────┬─────┘  └──────────────────────┘  │
│       │             │                                    │
│  ┌────┴─────────────┴──────────────────────────────┐    │
│  │              SwarmVault Core Engine              │    │
│  │  M0 → M1 → M2 → M3 → M4 → M5 Pipeline          │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  External:                                              │
│  - LLM Provider (Anthropic Claude / OpenAI)             │
│  - Object Storage (filesystem / S3 / MinIO)             │
│  - Telegram (NOT ESTABLISHED IN AVAILABLE SOURCE)       │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Product Architecture

### 2.1 Request Flow
```
User
 │
 ▼
Frontend (Next.js)
 │
 ▼
API Layer (FastAPI, /api/v1/*)
 │
 ├─▶ Authentication Middleware (JWT)
 │
 ├─▶ Tenancy Middleware (tenant context from token)
 │
 ├─▶ RBAC Middleware (role-based access)
 │
 ├─▶ Rate Limiting Middleware (per-endpoint)
 │
 ▼
Service Layer
 │
 ├─▶ MemoryService      — memory CRUD with provenance + audit
 ├─▶ Pipeline           — M0→M5 ingestion
 ├─▶ ChatOrchestrator   — LLM + retrieval + provenance
 ├─▶ M2FactsService     — fact extraction
 ├─▶ M3TemporalService  — temporal truth
 ├─▶ M4GraphService     — knowledge graph
 ├─▶ M5RetrievalService — BM25 + semantic retrieval
 ├─▶ AuditService       — event emission + persistence
 ├─▶ PolicyEngine       — authorization decisions
 ├─▶ LLMProvider        — Anthropic/OpenAI/Mock abstraction
 ├─▶ StorageProvider    — filesystem/S3/MinIO abstraction
 └─▶ ConnectorsService  — external source ingestion
 │
 ▼
Repository Layer
 │
 ├─▶ SQLAlchemy Async ORM
 │
 ▼
PostgreSQL (source of truth for all durable data)
 │
 ├─▶ tenants, workspaces, users
 ├─▶ projects, sessions, messages
 ├─▶ memories, facts, decisions
 ├─▶ graph_nodes, graph_edges
 ├─▶ message_provenance
 ├─▶ ingest_jobs, sources, normalized_messages
 ├─▶ api_keys, policies, policy_versions
 ├─▶ audit_events, message_feedback
 └─▶ refresh_tokens, invitations, workspace_members
 │
 ▼
File Storage (./storage/ — UUID-named directories)
```

### 2.2 Memory Pipeline (M0–M5)
```
Raw Input (conversation JSON/JSONL, document)
 │
 ▼
M0: Normalization
    - Parse input format
    - Redact secrets (API keys, passwords, tokens)
    - Deduplicate by content hash
    - Store as Source + NormalizedMessage records
 │
 ▼
M1: Session Understanding
    - Identify exchange structure
    - Preserve conversation context
    - Handle multi-exchange sessions
    - Compress/resume support
 │
 ▼
M2: Fact & Decision Extraction
    - Extract subject-predicate-object facts
    - Extract decision records
    - Assign confidence and authority scores
    - Store as Fact and Decision records
 │
 ▼
M3: Temporal Truth
    - Assign temporal_status (current/superseded/historical)
    - Detect contradictions across sources
    - Version facts via supersedes/superseded_by
    - Mark stale facts
 │
 ▼
M4: Knowledge Graph
    - Create GraphNode for entities
    - Create GraphEdge for relationships
    - Link to Source for provenance
    - Support traversal queries
 │
 ▼
M5: Retrieval & Intelligence
    - BM25 keyword search
    - Semantic retrieval (optional embeddings)
    - Reranking
    - Deduplication
    - Conflict detection
    - Score and rank results
 │
 ▼
Indexed Knowledge
    - Stored in PostgreSQL
    - Ready for retrieval
    - Provenance attached
```

### 2.3 Chat Response Flow
```
User submits message
 │
 ▼
ChatOrchestrator
 │
 ├─▶ Retrieve context (project, session, memories)
 ├─▶ M5 RetrievalService.search() — find relevant memories
 ├─▶ Build context pack (bounded, with provenance)
 │
 ▼
LLM Provider
 │
 ├─▶ Send prompt + retrieved context
 ├─▶ Stream response (SSE)
 │
 ▼
Response
 │
 ├─▶ Store assistant message
 ├─▶ Create MessageProvenance record
 │   - memory_ids_used
 │   - retrieval_sources
 │   - model, provider, tokens, latency
 │
 ▼
User sees response with source citations
```

---

## 3. Multi-Tenant Architecture

### 3.1 Hierarchy
```
Tenant (top-level organization)
 └── Workspace (collaborative space)
      ├── Project (knowledge container)
      │    ├── Session (conversation)
      │    │    ├── Message (user/assistant turn)
      │    │    └── MessageProvenance (response evidence)
      │    ├── Source (ingested document/conversation)
      │    │    ├── NormalizedMessage
      │    │    ├── Fact
      │    │    └── Decision
      │    ├── Memory
      │    ├── GraphNode
      │    └── GraphEdge
      └── WorkspaceMember (user + role)
```

### 3.2 Tenant Isolation Model
- Every memory, fact, decision, graph node/edge, source carries `tenant_id`
- Every query filters by `tenant_id` or `workspace_id` (which implies tenant)
- Cross-tenant access is blocked at the repository and API layer
- Provenance records carry `workspace_id` for scoping
- Audit events carry `tenant_id` for compliance

**Evidence:** `test_tenant_b_cannot_list_tenant_a_memories`, `test_tenant_b_cannot_read_tenant_a_memory_by_id`, `test_cross_tenant_project_blocked`, and 14 additional cross-tenant tests.

### 3.3 Roles
| Role | Description |
|------|-------------|
| owner | Full workspace control |
| admin | Administrative access |
| member | Read/write access |
| viewer | Read-only access |

**Evidence:** `UserRole` enum in `app/models.py:11-16`, RBAC middleware in `app/middleware/rbac.py`, 52 RBAC tests.

### 3.4 Authorization Boundaries
- Tenant → Workspace → Project → Session → Memory
- RBAC evaluated at workspace level
- Policy engine provides additional rule-based authorization (Sprint 7)
- All authorization decisions logged to audit

---

## 4. Backend Architecture

### 4.1 Framework
- **FastAPI** 0.111.0 — async Python web framework
- **Uvicorn** 0.30.0 — ASGI server (2 workers in production)
- **SQLAlchemy** 2.0.30 — async ORM with asyncpg
- **Alembic** 1.13.1 — database migrations
- **Pydantic** 2.7.1 / pydantic-settings 2.2.1 — validation and config
- **python-jose** 3.3.0 — JWT tokens
- **passlib[bcrypt]** 1.7.4 — password hashing

### 4.2 Application Structure
```
app/
├── __init__.py
├── main.py                    # FastAPI app, middleware, routes, lifespan
├── db.py                      # Database engine, session factory, init_db
├── models.py                  # SQLAlchemy ORM models (15 tables)
├── schemas.py                 # Pydantic request/response schemas
├── core/
│   ├── __init__.py
│   ├── config.py              # Settings (environment, CORS, LLM, storage)
│   └── security.py            # JWT encode/decode, password hashing
├── api/
│   ├── __init__.py            # Router registration
│   ├── auth.py                # POST /register, /login, /refresh, /logout
│   ├── workspace.py           # Workspace CRUD
│   ├── projects.py            # Project CRUD
│   ├── sessions.py            # Session CRUD
│   ├── chat.py                # POST /chat (SSE streaming)
│   ├── memory.py              # Memory CRUD, search, provenance
│   ├── ingest.py              # POST /ingest (file upload)
│   ├── provenance.py          # Provenance lookup
│   ├── dashboard.py           # Dashboard stats
│   ├── feedback.py            # Thumbs up/down on responses
│   ├── api_keys.py            # API key management
│   ├── storage.py             # Object storage operations
│   ├── policy.py              # Policy CRUD (Sprint 7)
│   └── audit.py               # Audit event querying
├── services/
│   ├── memory.py              # MemoryService (auth + policy + provenance + audit)
│   ├── pipeline.py            # M0→M5 ingestion pipeline
│   ├── chat_orchestrator.py   # Chat with retrieval + LLM + provenance
│   ├── m1_session.py          # M1: session understanding
│   ├── m2_facts.py            # M2: fact/decision extraction
│   ├── m3_temporal.py         # M3: temporal truth
│   ├── m4_graph.py            # M4: knowledge graph
│   ├── m5_retrieval.py        # M5: BM25 + semantic retrieval
│   ├── retrieval.py           # Legacy retrieval
│   ├── llm.py                 # LLM provider abstraction (Anthropic/OpenAI/Mock)
│   ├── connectors.py          # External source connectors
│   ├── tools.py               # Tool execution framework
│   ├── object_storage.py      # Storage provider interface
│   ├── object_storage_s3.py   # AWS S3 provider
│   ├── object_storage_minio.py # MinIO provider
│   ├── audit/
│   │   ├── __init__.py
│   │   ├── service.py          # AuditService (emit, persist, redaction)
│   │   ├── repository.py       # AuditEvent persistence
│   │   └── constants.py        # Event types, actions, sensitive fields
│   └── policy/
│       ├── __init__.py
│       ├── engine.py           # PolicyEngine
│       ├── evaluator.py        # Rule evaluation
│       ├── repository.py       # Policy persistence
│       └── dependencies.py     # FastAPI dependency injection
├── middleware/
│   ├── __init__.py
│   ├── auth.py                 # JWT token extraction + user resolution
│   ├── tenancy.py              # Tenant context from token
│   ├── rbac.py                 # Role-based access control
│   └── rate_limit.py           # Per-endpoint rate limiting (in-memory)
```

### 4.3 Services
| Service | File | Purpose |
|---------|------|---------|
| MemoryService | `app/services/memory.py` | Memory CRUD with auth, policy, provenance, audit |
| ChatOrchestrator | `app/services/chat_orchestrator.py` | Orchestrates retrieval + LLM + provenance |
| Pipeline | `app/services/pipeline.py` | M0→M5 ingestion orchestration |
| M1Session | `app/services/m1_session.py` | Session understanding |
| M2Facts | `app/services/m2_facts.py` | Fact/decision extraction |
| M3Temporal | `app/services/m3_temporal.py` | Temporal truth processing |
| M4Graph | `app/services/m4_graph.py` | Knowledge graph construction |
| M5Retrieval | `app/services/m5_retrieval.py` | BM25 + semantic retrieval |
| LLMProvider | `app/services/llm.py` | Anthropic/OpenAI/Mock with retry/fallback |
| AuditService | `app/services/audit/service.py` | Event emission, redaction, correlation |
| PolicyEngine | `app/services/policy/engine.py` | Rule-based authorization |
| Connectors | `app/services/connectors.py` | External source ingestion |

### 4.4 Middleware Stack (order of execution)
1. SecurityHeadersMiddleware — CSP, HSTS, X-Frame-Options
2. RequestIdMiddleware — X-Request-ID, latency measurement
3. AuditPersistenceMiddleware — flush audit events per request
4. CORSMiddleware — origin validation, credentials
5. RateLimitMiddleware — per-endpoint request limiting
6. AuthMiddleware — JWT extraction, user resolution
7. TenancyMiddleware — tenant context injection
8. RBACMiddleware — role-based authorization

### 4.5 API Router Registration
```
/api/v1/
├── /auth           — auth.router
├── /workspace      — workspace.router
├── /projects       — projects.router
├── /sessions       — sessions.router
├── /chat           — chat.router
├── /memory         — memory.router
├── /ingest         — ingest.router
├── /provenance     — provenance.router
├── /dashboard      — dashboard.router
├── /feedback       — feedback.router
├── /api-keys       — api_keys.router
├── /storage        — storage.router
├── /policy         — policy.router
└── /audit          — audit.router
```

**Evidence:** `app/main.py:139-155`, `app/api/__init__.py:1-2`

### 4.6 Background Processing
**NOT ESTABLISHED IN AVAILABLE SOURCE** — No worker process, task queue, or background job system was found in the repository. The ingestion pipeline (M0–M5) runs synchronously within the API request context. There is no Celery, RQ, or similar task queue.

---

## 5. Frontend Architecture

### 5.1 Framework
- **Next.js** (App Router) — React framework with file-based routing
- **TypeScript** — type safety
- **Tailwind CSS** — styling

**Evidence:** `frontend/package.json`, `frontend/tailwind.config.js`, `frontend/next.config.*`

### 5.2 Routing Structure
```
frontend/src/app/
├── page.tsx                    # Landing page
├── layout.tsx                  # Root layout
├── auth/
│   ├── login/page.tsx          # Login form
│   └── register/page.tsx       # Registration form
├── dashboard/page.tsx          # Workspace dashboard
├── settings/page.tsx           # User settings
└── projects/[id]/
    ├── layout.tsx              # Project layout (sidebar)
    ├── chat/page.tsx           # Chat with SSE
    ├── memory/page.tsx         # Memory view
    ├── search/page.tsx         # Search
    ├── facts/page.tsx          # Facts view
    ├── decisions/page.tsx      # Decisions view
    ├── timeline/page.tsx       # Timeline view
    ├── graph/page.tsx          # Knowledge graph
    ├── provenance/page.tsx     # Provenance explorer
    ├── ingest/page.tsx         # File upload/ingestion
    ├── sessions/page.tsx       # Session list
    └── sessions/[sessionId]/page.tsx  # Individual session
```

### 5.3 Components and Hooks
| Component/Hook | File | Purpose |
|----------------|------|---------|
| Sidebar | `components/Sidebar.tsx` | Project navigation sidebar |
| useSSE | `hooks/useSSE.tsx` | Server-Sent Events for chat streaming |
| useAuth | `hooks/useAuth.tsx` | Authentication state management |

### 5.4 API Communication
- **API client:** `frontend/src/lib/api.ts` — centralized HTTP client
- **Types:** `frontend/src/types/api.ts` — TypeScript interfaces for API responses
- **Authentication:** Bearer token in Authorization header
- **Chat:** SSE streaming via `useSSE` hook

---

## 6. Data Architecture

### 6.1 Entity Relationship Summary
```
tenants
  └─▶ workspaces (tenant_id FK)
        ├─▶ workspace_members (workspace_id FK, user_id FK)
        ├─▶ projects (workspace_id FK)
        │    ├─▶ sessions (workspace_id FK, user_id FK)
        │    │    ├─▶ messages (session_id FK)
        │    │    │    └─▶ message_provenance (user_message_id, assistant_message_id FK)
        │    │    └─▶ message_feedback (session_id FK, provenance_id FK)
        │    ├─▶ sources (workspace_id FK)
        │    │    ├─▶ normalized_messages (source_id FK)
        │    │    ├─▶ facts (source_id FK)
        │    │    ├─▶ decisions (source_id FK)
        │    │    └─▶ graph_edges (source_id FK)
        │    ├─▶ memories (workspace_id FK, tenant_id FK, project_id FK)
        │    ├─▶ graph_nodes (workspace_id FK)
        │    └─▶ graph_edges (workspace_id FK)
        └─▶ invitations (workspace_id FK)

users
  ├─▶ workspace_members (user_id FK)
  ├─▶ sessions (user_id FK)
  ├─▶ refresh_tokens (user_id FK)
  ├─▶ api_keys (user_id FK, workspace_id FK)
  └─▶ message_feedback (user_id FK)

tenants
  ├─▶ policies (tenant_id FK)
  └─▶ audit_events (tenant_id FK)
```

### 6.2 Table Reference

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| tenants | Organizations | id, name, slug, plan |
| workspaces | Collaborative spaces | id, tenant_id, name, slug, deleted_at |
| users | User accounts | id, email, hashed_password, is_active |
| workspace_members | Role assignments | id, workspace_id, user_id, role |
| projects | Knowledge containers | id, workspace_id, name, deleted_at |
| sessions | Conversations | id, workspace_id, user_id, title, metadata |
| messages | Chat turns | id, session_id, role, content, metadata |
| memories | Extracted/persisted knowledge | id, tenant_id, workspace_id, project_id, content, temporal_status, confidence, authority |
| sources | Ingested documents/conversations | id, project_id, workspace_id, tenant_id, source_type, content_hash, status |
| normalized_messages | Parsed message records | id, source_id, session_id, message_index, role, content |
| facts | Extracted factual statements | id, workspace_id, project_id, source_id, subject, predicate, object, confidence, temporal_status, superseded_by_id |
| decisions | Extracted decisions | id, workspace_id, project_id, source_id, content, context, confidence, temporal_status |
| graph_nodes | Knowledge graph entities | id, workspace_id, project_id, label, node_type, properties, temporal_status |
| graph_edges | Knowledge graph relationships | id, workspace_id, source_node_id, target_node_id, relationship_type, confidence, source_id |
| message_provenance | Chat response evidence | id, workspace_id, session_id, model, provider, memory_ids_used, retrieval_sources, tokens, latency |
| message_feedback | User ratings | id, workspace_id, user_id, rating, comment |
| ingest_jobs | Ingestion job tracking | id, project_id, workspace_id, source_type, status, stage, progress |
| api_keys | MCP server credentials | id, workspace_id, user_id, key_hash, key_prefix, expires_at, revoked_at |
| policies | Authorization policies | id, tenant_id, name, status, current_version |
| policy_versions | Versioned policy rules | id, policy_id, version, rules |
| audit_events | Append-only audit log | id, tenant_id, workspace_id, principal_id, action, decision, event_type, timestamp |
| refresh_tokens | JWT refresh tokens | id, user_id, token, expires_at, revoked |
| invitations | Workspace invitations | id, workspace_id, email, role, state |

### 6.3 Indexes (20 total)
| Table | Index |
|-------|-------|
| users | email (unique) |
| memories | tenant_id, workspace_id, project_id, temporal_status, deleted_at |
| sources | ix_sources_workspace_tenant (workspace_id, tenant_id), ix_sources_project_status (project_id, status), external_id, content_hash |
| facts | ix_facts_workspace_project, ix_facts_subject, ix_facts_temporal_status |
| decisions | ix_decisions_workspace_project, ix_decisions_temporal_status |
| graph_nodes | ix_graph_nodes_workspace (workspace_id, temporal_status), ix_graph_nodes_workspace_type, unique (workspace_id, external_id) |
| graph_edges | ix_graph_edges_source_target, ix_graph_edges_workspace (workspace_id, temporal_status) |
| api_keys | ix_api_keys_workspace, ix_api_keys_user, key_hash (unique) |
| policies | ix_policies_tenant_id, ix_policies_status |
| policy_versions | ix_policy_versions_policy_id, unique (policy_id, version) |
| audit_events | ix_audit_events_tenant_timestamp, ix_audit_events_principal_timestamp, ix_audit_events_resource_timestamp, ix_audit_events_correlation, timestamp |
| refresh_tokens | token (unique) |

**Evidence:** `app/models.py` (all `__table_args__` blocks), migrations 001–011

### 6.4 Key Design Patterns
- **UUID primary keys** — all tables use `String(36)` UUIDs
- **Soft deletes** — `deleted_at` column (not hard deletes) on: workspaces, users, sessions, projects, memories, sources, facts, decisions, graph_nodes, graph_edges, message_feedback
- **Temporal tracking** — `temporal_status` column (current/superseded/historical) on: memories, facts, decisions, graph_nodes, graph_edges
- **JSON metadata** — `extra_metadata` JSON column on: Memory, Source, NormalizedMessage, Fact, Decision, GraphNode, GraphEdge, Session, Message, IngestJob
- **Embedding storage** — Memory.embedding stores vector embeddings as JSON

---

## 7. Memory Architecture (M0–M5)

### 7.1 Overview
SwarmVault's intelligence layer processes raw input through six stages (M0–M5), transforming unstructured conversations into structured, queryable, evidence-backed knowledge.

### 7.2 M0 — Normalization & Deduplication
- **Input:** Raw conversation JSON/JSONL, documents
- **Processing:** Parse format, redact secrets (API keys, passwords, tokens), deduplicate by content hash
- **Output:** Source record + NormalizedMessage records
- **Tables:** `sources`, `normalized_messages`
- **Service:** `app/services/pipeline.py` (M0 stage)
- **Deduplication key:** `content_hash` (SHA-256, stored in Source.content_hash)
- **Evidence:** Migration 008 (`008_add_source_content_hash`), test_content_dedup_golden

### 7.3 M1 — Session Understanding
- **Input:** Normalized messages
- **Processing:** Identify exchange structure, preserve conversation context, handle multi-exchange sessions
- **Output:** Session-linked message records
- **Tables:** `sessions`, `normalized_messages`
- **Service:** `app/services/m1_session.py`
- **Evidence:** test_full_pipeline_golden_conversation

### 7.4 M2 — Fact & Decision Extraction
- **Input:** Normalized messages
- **Processing:** Extract subject-predicate-object facts, extract decision records, assign confidence (0.0–1.0) and authority (0.0–1.0) scores
- **Output:** Fact records, Decision records
- **Tables:** `facts`, `decisions`
- **Service:** `app/services/m2_facts.py`
- **Schema:** Fact{subject, predicate, object, content, confidence, authority, temporal_status}
- **Evidence:** test_search_finds_golden_facts

### 7.5 M3 — Temporal Truth
- **Input:** Facts and decisions
- **Processing:** Assign temporal_status (current/superseded/historical), detect contradictions, version via supersedes chain, mark stale facts
- **Output:** Versioned facts and decisions
- **Tables:** `facts`, `decisions` (temporal_status, superseded_by_id columns)
- **Service:** `app/services/m3_temporal.py`
- **Evidence:** test_facts_temporal_status_filtering, test_temporal_status

### 7.6 M4 — Knowledge Graph
- **Input:** Facts, entities from messages
- **Processing:** Create GraphNode for entities, GraphEdge for relationships, link to Source for provenance
- **Output:** GraphNode and GraphEdge records
- **Tables:** `graph_nodes`, `graph_edges`
- **Service:** `app/services/m4_graph.py`
- **Evidence:** test_graph_query, test_neighbors, test_shortest_path, test_graph_stats

### 7.7 M5 — Retrieval & Intelligence
- **Input:** Indexed memories, facts, graph
- **Processing:** BM25 keyword search, optional semantic retrieval (embeddings), reranking, deduplication, conflict detection
- **Output:** Ranked results with provenance
- **Tables:** `memories` (embedding column)
- **Service:** `app/services/m5_retrieval.py`
- **Evidence:** test_search_memories, test_m5_retrieval_returns_results, test_hybrid_score

---

## 8. Security Architecture

### 8.1 Authentication
- **JWT HS256** — Access tokens (60 min expiry) and refresh tokens (30 day expiry)
- **Password hashing** — bcrypt via passlib
- **Token refresh** — Rotating refresh tokens; old tokens revoked on refresh
- **Logout** — Refresh token marked as revoked
- **Evidence:** `app/core/security.py`, 11 auth tests

### 8.2 Authorization (RBAC)
- **4 roles:** owner, admin, member, viewer
- **8 actions:** read, search, write, update, delete, execute, export, share
- **Deny-by-default:** No implicit permissions
- **Policy engine:** Additional rule-based authorization (Sprint 7)
- **Evidence:** `app/middleware/rbac.py`, `app/services/policy/`, 52 RBAC tests, 14 policy tests

### 8.3 Tenant Isolation
- **tenant_id** on all knowledge tables (memories, facts, decisions, graph, sources)
- **workspace_id** scoping on all queries
- **Cross-tenant access blocked** at repository and API layer
- **14 dedicated cross-tenant tests** verify isolation
- **Evidence:** Migration 011, test_tenant_b_cannot_* (14 tests)

### 8.4 Secrets Management
- **SECRET_KEY** — From environment only; validated at startup (production blocks default)
- **Database credentials** — From environment
- **LLM credentials** — From environment (Anthropic/OpenAI)
- **API keys** — Stored as key_hash (SHA-256), never plaintext
- **Sensitive field redaction** — Audit events never store passwords, tokens, secrets
- **Evidence:** `app/core/config.py` validators, `app/services/audit/constants.py` redaction list, test_credentials_not_leaked

### 8.5 Security Headers
| Header | Value |
|--------|-------|
| X-Content-Type-Options | nosniff |
| X-Frame-Options | DENY |
| X-XSS-Protection | 1; mode=block |
| Referrer-Policy | strict-origin-when-cross-origin |
| Permissions-Policy | geolocation=(), microphone=(), camera=() |
| Strict-Transport-Security | max-age=31536000; includeSubDomains (production only) |
| Content-Security-Policy | default-src 'self'; script-src 'self'; etc. (production + dev variants) |

**Evidence:** `app/main.py:47-81` SecurityHeadersMiddleware

### 8.6 CORS
- Configurable origins (comma-separated string or JSON list)
- Production blocks wildcard (`*`) with credentials
- Allow methods: GET, POST, PATCH, DELETE, OPTIONS
- Allow headers: Authorization, Content-Type, X-Request-ID
- **Evidence:** `app/main.py:215-223`, `app/core/config.py` cors_origins_safe property

### 8.7 Input Security
- **SQL injection:** Prevented via parameterized queries (SQLAlchemy ORM)
- **XSS:** Content stored as text, not rendered
- **Prompt injection:** Stored as data, never executed as instructions
- **Oversized input:** Rejected by Pydantic schema validation
- **Path traversal:** Stored as data, never executed as filesystem operations
- **Evidence:** test_security_matrix (18 tests)

---

## 9. Deployment Architecture

### 9.1 Components
```
┌─────────────────────────────────────────────────────────────────────┐
│                        Host / VPS                                   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Docker Compose                            │  │
│  │                                                              │  │
│  │  ┌──────────────┐    ┌──────────────────────────────────┐   │  │
│  │  │   Postgres   │    │        SwarmVault App            │   │  │
│  │  │   16-alpine  │    │    python:3.12-slim              │   │  │
│  │  │  :5432       │◄───│    non-root user (swarmvault)    │   │  │
│  │  │              │    │    2 uvicorn workers              │   │  │
│  │  │  Volume:     │    │    port 8000                      │   │  │
│  │  │  pg_data     │    │                                  │   │  │
│  │  └──────────────┘    └──────────────────────────────────┘   │  │
│  │                                                              │  │
│  │  Volumes:                                                    │  │
│  │  - postgres_data (persistent DB)                             │  │
│  │  - app_storage (uploaded files)                              │  │
│  │  - app_logs (application logs)                               │  │
│  │                                                              │  │
│  │  Network: swarmvault (isolated)                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Optional: Reverse proxy (nginx/caddy) — NOT IN REPOSITORY         │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 Artifacts
| Artifact | Purpose |
|----------|---------|
| Dockerfile | Multi-stage build: builder (compile deps) → runtime (minimal image) |
| docker-compose.yml | Orchestrates PostgreSQL + App with health checks |
| .dockerignore | Prevents secrets/storage/logs from entering image |
| .env.example | Template for all environment variables |
| DEPLOYMENT.md | Runbook: deploy, upgrade, backup, restore, rollback, troubleshoot |

### 9.3 Health Checks
- **Liveness:** `GET /health/live` — always returns 200 if process is running
- **Readiness:** `GET /health/ready` — checks database connectivity; returns 503 if DB unavailable

### 9.4 Persistence Boundaries
| Data | Location | Persistence |
|------|----------|-------------|
| All knowledge (memories, facts, decisions, graph) | PostgreSQL | Durable |
| Provenance records | PostgreSQL | Durable |
| Audit events | PostgreSQL | Durable |
| Uploaded files | `./storage/` (filesystem) | Durable (volume) |
| Session state | PostgreSQL | Durable |
| Cache | In-memory | Ephemeral (rebuilt from DB) |

**Evidence:** `app/main.py:254-276`, `docker-compose.yml` volumes

---

## 10. Data Lifecycle

```
Raw Input (conversation JSON/JSONL)
 │
 ▼
[M0] Normalization
    - Parse format
    - Redact secrets
    - Deduplicate by content hash
    → Source + NormalizedMessage stored in PostgreSQL
 │
 ▼
[M1] Session Understanding
    - Identify exchanges
    - Preserve context
    → Linked to Session records
 │
 ▼
[M2] Fact & Decision Extraction
    - Extract subject-predicate-object facts
    - Extract decisions
    - Assign confidence/authority
    → Fact + Decision records in PostgreSQL
 │
 ▼
[M3] Temporal Truth
    - Assign temporal_status
    - Detect contradictions
    - Version via supersedes chain
    → Versioned facts/decisions
 │
 ▼
[M4] Knowledge Graph
    - Create GraphNode entities
    - Create GraphEdge relationships
    - Link to Source for provenance
    → Graph in PostgreSQL
 │
 ▼
[M5] Retrieval & Intelligence
    - BM25 keyword search
    - Optional semantic search (embeddings)
    - Rerank, deduplicate, detect conflicts
    → Indexed for retrieval
 │
 ▼
INDEXED KNOWLEDGE
    - Stored in PostgreSQL (source of truth)
    - Ready for chat retrieval
    - Provenance attached
    - Temporal status maintained
 │
 ▼
RETRIEVAL (on chat query)
    - M5 search finds relevant memories
    - Context pack built (bounded, with provenance)
    → Sent to LLM
 │
 ▼
LLM RESPONSE
    - Streamed to user (SSE)
    - Provenance recorded (memory_ids, sources, model, tokens)
    → MessageProvenance stored
 │
 ▼
EVIDENCE-BACKED ANSWER
    - User sees response with source citations
    - Can trace: Answer → Memory → Fact/Decision → Source → Original conversation
```

---

## 11. Architectural Boundaries

| Layer | Belongs To | Responsibility |
|-------|-----------|----------------|
| Frontend (Next.js) | SwarmVault WebApp | User interface, API consumption, SSE |
| Backend (FastAPI) | SwarmVault WebApp | API, auth, orchestration, business logic |
| M0–M5 Pipeline | SwarmVault Core Engine | Intelligence extraction and processing |
| PostgreSQL | Infrastructure | Persistent data store |
| File Storage | Infrastructure | Uploaded file persistence |
| LLM Providers | External | Anthropic Claude, OpenAI |
| Object Storage (S3/MinIO) | External | Scalable file storage |

**Key boundary:** The M0–M5 intelligence pipeline (`app/services/m*.py`) is the SwarmVault Core Engine. The WebApp wraps it with multi-tenant SaaS concerns (auth, RBAC, tenancy, audit, API, UI).

---

## 12. Capability Map

| Capability | Backend Service | API Router | DB Tables | Frontend Page | Test Evidence |
|------------|----------------|------------|-----------|---------------|---------------|
| Authentication | security.py | auth.py | users, refresh_tokens | login, register | 11 auth tests |
| Multi-tenant workspaces | memory.py, workspace.py | workspace.py | tenants, workspaces, workspace_members | dashboard | 16 tenancy tests |
| Projects | memory.py | projects.py | projects | projects/[id]/* | test_projects |
| Sessions | m1_session.py | sessions.py | sessions, messages | sessions/, sessions/[id] | test_sessions |
| Chat with retrieval | chat_orchestrator.py | chat.py | messages, message_provenance | projects/[id]/chat | test_chat, test_chat_sprint2 |
| Memory CRUD | memory.py | memory.py | memories | projects/[id]/memory | test_memory |
| Memory search | m5_retrieval.py | memory.py | memories | projects/[id]/search | test_search_memories |
| Ingestion | pipeline.py, connectors.py | ingest.py | ingest_jobs, sources, normalized_messages | projects/[id]/ingest | test_ingest |
| Facts | m2_facts.py | (via memory/search) | facts | projects/[id]/facts | test_search_finds_golden_facts |
| Decisions | m2_facts.py | (via memory/search) | decisions | projects/[id]/decisions | — |
| Timeline | m3_temporal.py | (via memory) | facts, decisions | projects/[id]/timeline | test_temporal_status |
| Knowledge graph | m4_graph.py | provenance.py | graph_nodes, graph_edges | projects/[id]/graph | test_graph_query |
| Provenance | chat_orchestrator.py | provenance.py | message_provenance | projects/[id]/provenance | test_provenance_explorer |
| Feedback | — | feedback.py | message_feedback | (in chat) | 4 feedback tests |
| API keys | — | api_keys.py | api_keys | — | test_api_keys |
| Policy engine | policy/engine.py | policy.py | policies, policy_versions | — | test_policy_engine |
| Audit | audit/service.py | audit.py | audit_events | — | 28 audit tests |
| Dashboard | memory.py | dashboard.py | (aggregates) | dashboard | test_dashboard |
| Storage | object_storage*.py | storage.py | (filesystem/S3) | — | test_storage |

---

## 13. Terminology Glossary

| Term | Definition | First Appearance |
|------|-----------|-----------------|
| Tenant | Top-level organization boundary; all data is scoped to a tenant | `models.py:18` Tenant |
| Workspace | Collaborative space within a tenant; members have roles | `models.py:39` Workspace |
| Project | Knowledge container within a workspace; groups sessions, memories, sources | `models.py:209` Project |
| Session | Conversation context within a project | `models.py:165` Session |
| Message | Individual turn in a conversation (user or assistant) | `models.py:191` Message |
| Memory | Extracted or persisted knowledge unit; the primary retrievable artifact | `models.py:232` Memory |
| Fact | Extracted factual statement in subject-predicate-object form | `models.py:413` Fact |
| Decision | Extracted decision record with context and confidence | `models.py:467` Decision |
| Source | Ingested conversation or document (M0 input) | `models.py:302` Source |
| NormalizedMessage | Individual parsed message from an ingested source | `models.py:369` NormalizedMessage |
| Provenance | Evidence chain linking a chat response to its source memories and retrieval method | `models.py:607` MessageProvenance |
| GraphNode | Entity in the knowledge graph | `models.py:520` GraphNode |
| GraphEdge | Relationship between graph nodes | `models.py:561` GraphEdge |
| Temporal Status | Whether a fact/memory is current, superseded, or historical | Column on Memory, Fact, Decision |
| Confidence | Numeric score (0.0–1.0) of extraction certainty | Column on Memory, Fact, Decision |
| Authority | Numeric score (0.0–1.0) of source trustworthiness | Column on Memory, Fact, Decision |
| M0 | Normalization: parse, redact, deduplicate raw input | `services/pipeline.py` |
| M1 | Session understanding: identify exchanges, preserve context | `services/m1_session.py` |
| M2 | Fact/decision extraction from normalized messages | `services/m2_facts.py` |
| M3 | Temporal truth: versioning, supersession, stale detection | `services/m3_temporal.py` |
| M4 | Knowledge graph: entities, relationships, traversal | `services/m4_graph.py` |
| M5 | Retrieval: BM25, semantic search, reranking, deduplication | `services/m5_retrieval.py` |
| Context Pack | Bounded set of retrieved memories with provenance, sent to LLM | ChatOrchestrator |
| Content Hash | SHA-256 hash for deduplication of ingested content | Source.content_hash |
| API Key | SHA-256 hashed credential for external MCP server access | `models.py:684` ApiKey |
| Policy | Rule-based authorization definition (Sprint 7) | `models.py:727` Policy |
| Audit Event | Append-only record of a security-relevant action | `models.py:788` AuditEvent |

---

## 14. Source Traceability

| Architectural Claim | Evidence Source | Location |
|---------------------|----------------|----------|
| FastAPI backend | Source code | `app/main.py` |
| Multi-tenant with tenant_id | Source code + tests | `app/models.py:238`, migration 011, 14 cross-tenant tests |
| 4 RBAC roles | Source code + tests | `app/models.py:11-16`, `app/middleware/rbac.py`, 52 RBAC tests |
| JWT HS256 auth | Source code + tests | `app/core/security.py`, 11 auth tests |
| M0–M5 pipeline | Source code + tests | `app/services/m*.py`, test_golden_dataset, test_pipeline |
| BM25 + semantic retrieval | Source code + tests | `app/services/m5_retrieval.py`, test_m5_retrieval_returns_results |
| Knowledge graph | Source code + tests | `app/services/m4_graph.py`, test_graph_query |
| Temporal truth | Source code + tests | `app/services/m3_temporal.py`, test_facts_temporal_status_filtering |
| Provenance tracking | Source code + tests | `app/services/chat_orchestrator.py`, test_provenance_explorer |
| Audit logging | Source code + tests | `app/services/audit/`, 28 audit tests |
| Policy engine | Source code + tests | `app/services/policy/`, test_policy_engine |
| Security headers | Source code | `app/main.py:47-81` |
| PostgreSQL persistence | Source code + migrations | `app/db.py`, 11 migrations |
| Docker deployment | Artifacts | Dockerfile, docker-compose.yml, DEPLOYMENT.md |
| Next.js frontend | Source code | `frontend/src/` (24 source files) |
| SSE chat streaming | Source code | `app/api/chat.py`, `frontend/src/hooks/useSSE.tsx` |
| In-memory rate limiting | Source code + tests | `app/middleware/rate_limit.py`, 17 rate limit tests |
| Secret redaction | Source code + tests | `app/services/audit/constants.py`, test_security_matrix |
| Soft deletes | Source code | `deleted_at` column on 10+ tables |
| UUID primary keys | Source code | All models use `String(36)` UUID |
| No background worker | Source inspection | No Celery/RQ/worker found in repository |
| Object storage (S3/MinIO) | Source code | `app/services/object_storage_s3.py`, `object_storage_minio.py` (stubs) |
| Telegram integration | NOT ESTABLISHED | No Telegram code found in WebApp repository |
