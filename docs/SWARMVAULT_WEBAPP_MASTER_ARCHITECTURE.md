# SwarmVault WebApp — Master Architecture
**Authority:** Forensic reconciliation against HEAD `e6f4b1c157afaed052584963b942ea04f9661610`
**Date:** 2026-09-10
**Classification:** Read-only documentation — no code changes

> Every architectural statement below is grounded in an actual file, function,
> route, schema, model, migration, configuration, test, or runtime dependency.
> Inferences are explicitly labeled as such.

================================================================================
1. EXECUTIVE SUMMARY
================================================================================

SwarmVault WebApp is a FastAPI + Next.js monolith-style application that ingests
conversation data, runs it through a 5-stage knowledge pipeline (M0–M5), and
exposes a graph-first knowledge interface with chat, search, memory, provenance,
and timeline views.

**Architectural posture:** The system is functionally implemented but has
significant technical debt and architectural inconsistencies. The most critical
gap is that model changes exist without corresponding Alembic migrations,
meaning the production database schema does not match the SQLAlchemy models.

**Key facts:**
- 72 REST endpoints across 14 routers under `/api/v1`
- 5-stage pipeline (M0–M5) implemented as async Python services
- PostgreSQL + SQLAlchemy 2.0 async, Alembic migrations (versions/ empty)
- JWT authentication with refresh tokens, bcrypt password hashing
- 4-tier RBAC: owner, admin, member, viewer
- SSE streaming for chat completions
- In-memory audit store (not persistent)
- External integrations: Anthropic, OpenAI, Mock LLM; Local/S3/MinIO storage
- MCP, Codex, Universal Adapter: NOT implemented (documented only)

================================================================================
2. PRODUCT BOUNDARY
================================================================================

**In scope:**
- Conversation ingestion (text, JSON, JSONL, Claude Code JSONL)
- Knowledge extraction (facts, decisions, entities, relationships)
- Temporal state tracking (supersession, current/historical)
- Graph construction and traversal
- Hybrid retrieval (vector + BM25 + graph)
- User-created persistent memory
- Provenance tracking
- Audit logging
- Multi-tenant workspace isolation
- Chat with memory-augmented responses

**Out of scope (documented but not implemented):**
- MCP server protocol
- Codex CLI integration
- Universal Agent Adapter
- Live agent execution / tool calling
- Webhook/callback endpoints
- Batch operations
- Encryption at rest

================================================================================
3. SYSTEM CONTEXT
================================================================================

```
┌─────────────────────────────────────────────────────────────────┐
│                        SwarmVault WebApp                        │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │   Next.js   │  │   FastAPI    │  │   PostgreSQL          │  │
│  │   Frontend  │◄─│   Backend    │─►│   (asyncpg)           │  │
│  │   (port 3000)│  │   (port 8000)│  │                       │  │
│  └─────────────┘  └──────────────┘  └───────────────────────┘  │
│                          │                    │                  │
│                    ┌─────┴─────┐              │                  │
│                    │  Alembic  │              │                  │
│                    │ (versions│              │                  │
│                    │  EMPTY)  │              │                  │
│                    └──────────┘              │                  │
│                                                                 │
│  External providers:                                           │
│  - Anthropic API (LLM)                                         │
│  - OpenAI API (LLM)                                            │
│  - S3 / MinIO / Local filesystem (object storage)              │
└─────────────────────────────────────────────────────────────────┘
```

**Deployment:** Single-process development mode. No Docker, no Kubernetes,
no load balancer, no CDN configured in repository.

================================================================================
4. ARCHITECTURAL PRINCIPLES
================================================================================

1. **Repository is truth.** Every claim must be traceable to executable code.
2. **No invented features.** Capabilities classified as IMPLEMENTED/PARTIAL/
   DOCUMENTED_ONLY/PLANNED/MISSING/UNVERIFIED.
3. **Trace data, not just components.** Follow actual data flow from entry
   to persistence.
4. **Fail closed.** Unhandled exceptions produce 500 responses, not partial
   state exposure.
5. **Tenancy isolation.** All queries filter by workspace_id + user_id at
   minimum. tenant_id is inconsistently enforced.
6. **Append-only semantics.** Memory and provenance records are immutable
   by schema design (no updated_at fields).
7. **Evidence-backed claims.** Facts require provenance chains; enforcement
   is incomplete.

================================================================================
5. HIGH-LEVEL ARCHITECTURE
================================================================================

**Pattern:** Monolithic layered architecture
- API layer: FastAPI routers (`app/api/`)
- Service layer: Business logic (`app/services/`)
- Data layer: SQLAlchemy models + repositories (`app/models.py`, `app/repositories/`)
- Integration layer: Connectors, LLM providers, storage backends (`app/services/`)
- Middleware layer: Auth, tenancy, RBAC, rate limiting (`app/middleware/`)

**No microservices.** No message queue. No event bus. Background processing
is limited to synchronous pipeline execution within request scope.

**Pipeline architecture:**
```
M0 (Ingestion) → M1 (Normalization) → M2 (Fact/Decision Extraction)
    → M3 (Temporal Processing) → M4 (Graph Construction) → M5 (Retrieval)
```

Each stage is a Python function in `app/services/pipeline.py` calling
specialized services.

================================================================================
6. BACKEND ARCHITECTURE
================================================================================

**Application factory:** `app/main.py`
- FastAPI app created with title/description
- CORS middleware via `CORSMiddleware`
- 4 HTTP middleware decorators
- 14 routers included under `/api/v1`
- Lifespan handler: startup/shutdown

**Startup sequence (`app/main.py` lifespan):**
1. `init_engine()` — create_async_engine(settings.database_url)
2. `init_session_factory()` — async_sessionmaker
3. `init_storage()` — ObjectStorageFactory.create()
4. `init_llm()` — LLMProviderFactory.create()
5. `init_memory()` — MemoryService(...)
6. `init_audit()` — AuditService(...)
7. `init_policy()` — PolicyEngine(...)

**Shutdown sequence:**
1. Dispose SQLAlchemy engine
2. Close storage client

**Request execution path:**
```
HTTP Request
  → SecurityHeadersMiddleware (inject headers)
  → RequestIdMiddleware (X-Request-ID)
  → AuditPersistenceMiddleware (request/response logging)
  → RateLimitMiddleware (sliding window per key)
  → CORSMiddleware (CORS headers)
  → FastAPI routing
    → require_auth dependency (JWT decode + user lookup)
    → get_tenant_context dependency (workspace/project/tenant)
    → require_min_role / require_permission (RBAC)
    → Route handler
      → Service layer
        → Repository/data access
          → Database (asyncpg via SQLAlchemy)
    → Response serialization (Pydantic schemas)
  → Exception handlers (if unhandled)
```

**Service inventory:**

| Service | Location | Purpose |
|---------|----------|---------|
| LLMProviderFactory | `app/services/llm.py` | Anthropic, OpenAI, Mock provider selection |
| MemoryService | `app/services/memory.py` | CRUD + search for persistent memories |
| AuditService | `app/services/audit/` | In-memory event logging |
| PolicyEngine | `app/services/policy/engine.py` | RBAC + policy evaluation |
| Pipeline | `app/services/pipeline.py` | M0–M5 orchestration |
| M1 Session | `app/services/m1_session.py` | Session state, token counting |
| M2 Facts | `app/services/m2_facts.py` | Fact extraction, validation, supersession |
| M3 Temporal | `app/services/m3_temporal.py` | Time-travel queries, snapshots |
| M4 Graph | `app/services/m4_graph.py` | Graph construction, community detection |
| M5 Retrieval | `app/services/m5_retrieval.py` | Hybrid retrieval (vector + BM25 + graph) |
| ObjectStorage | `app/services/object_storage.py` | Local/S3/MinIO file operations |
| Connectors | `app/services/connectors.py` | Claude Code, generic ingestion formats |

**Model inventory:** 20+ SQLAlchemy models in `app/models.py`
- Core: User, Workspace, Project, Session, Message
- Memory: Memory, MemoryProvenance, MemoryEntity
- Knowledge: Fact, FactProvenance, FactSource, Decision
- Graph: GraphNode, GraphEdge, GraphCommunity
- Temporal: Snapshot, SnapshotBranch
- Audit: AuditEvent, RefreshToken, ApiKey, IngestJob, Feedback

**Critical inconsistency:** `app/models.py` contains 5 changes (superseded_at,
superseded_by_id, error_message on Source, deleted_at index) that have NO
corresponding Alembic migration in `app/alembic/versions/` (which is empty).
Production database schema does NOT match these models.

================================================================================
7. FRONTEND ARCHITECTURE
================================================================================

**Framework:** Next.js 15, React 18, TypeScript
**Styling:** Tailwind CSS with custom design tokens in `globals.css`
**Icons:** lucide-react
**State management:** React state (useState/useContext) — no Redux/Zustand

**Route structure:**
```
frontend/src/app/
├── page.tsx                    (Dashboard)
├── login/page.tsx              (Login)
├── register/page.tsx           (Registration)
├── projects/
│   ├── page.tsx                (Project list)
│   ├── [id]/page.tsx           (Project detail)
│   ├── [id]/chat/page.tsx      (Chat)
│   ├── [id]/memory/page.tsx    (Memory)
│   ├── [id]/facts/page.tsx     (Facts)
│   ├── [id]/decisions/page.tsx (Decisions)
│   └── [id]/settings/page.tsx  (Settings)
├── sessions/page.tsx           (Session list)
├── api-keys/page.tsx           (API key management)
└── settings/page.tsx           (User settings)
```

**API client:** Custom fetch wrapper in `frontend/src/lib/api.ts` with
JWT injection from localStorage.

**Authentication:** JWT stored in localStorage, refreshed via `/auth/refresh`.
No token refresh automation observed — tokens expire after 60 minutes.

**SSE handling:** Chat streaming via EventSource in chat page, parsing
`token`, `sources`, `done`, `error` events.

**Known issues:**
- 404 page not found
- Sidebar navigation may have routing gaps

================================================================================
8. API ARCHITECTURE
================================================================================

**Base URL:** `/api/v1`
**Authentication:** Bearer JWT (HS256)
**Content type:** JSON (application/json)
**Pagination:** limit/offset query parameters with total count
**Error format:**
```json
{
  "error": {
    "type": "validation_error|database_error|internal_error",
    "message": "...",
    "request_id": "..."
  }
}
```

**Complete route inventory (72 endpoints):**

| Router | Prefix | Endpoints |
|--------|--------|-----------|
| auth | `/api/v1/auth` | 6 |
| workspace | `/api/v1/workspace` | 14 |
| projects | `/api/v1/projects` | 5 |
| sessions | `/api/v1/sessions` | 6 |
| chat | `/api/v1/chat` | 2 (+ SSE) |
| memory | `/api/v1/memory` | 6 |
| ingest | `/api/v1/ingest` | 14 |
| provenance | `/api/v1/provenance` | 3 |
| dashboard | `/api/v1/dashboard` | 2 |
| feedback | `/api/v1/feedback` | 3 |
| api-keys | `/api/v1/api-keys` | 4 |
| storage | `/api/v1/storage` | 3 |
| policy | `/api/v1/policy` | 7 |
| audit | `/api/v1/audit` | 3 |

**SSE endpoints:** `/api/v1/chat/stream` (token, sources, done, error events)

**Rate limits:**
- `/auth/login`: 10/60s
- `/auth/register`: 10/60s
- `/chat/`: 30/60s
- `/ingest/upload`: 5/3600s
- `/ingest/search`: 60/60s

================================================================================
9. DATA ARCHITECTURE
================================================================================

**Database:** PostgreSQL via asyncpg driver, SQLAlchemy 2.0 async ORM
**Migrations:** Alembic — `app/alembic/` — **versions/ directory is EMPTY**

**Entity relationships:**
```
Tenant
  └── Workspace
        ├── User (members)
        ├── Project
        │     ├── Session
        │     │     └── Message
        │     ├── Source (ingested content)
        │     │     └── NormalizedMessage
        │     ├── Fact
        │     ├── Decision
        │     ├── Memory
        │     └── GraphNode
        │           └── GraphEdge
        ├── ApiKey
        └── RefreshToken
```

**Soft deletion:** Most entities have `deleted_at` column. Queries filter
`deleted_at IS NULL`. No cascade soft-delete observed.

**Deduplication:** Content-hash dedup on ingestion (`sha256` of content).
Returns existing source if hash matches within workspace.

================================================================================
10. MEMORY ARCHITECTURE
================================================================================

**Five memory modules (M0–M5):**

| Module | Service | Purpose |
|--------|---------|---------|
| M0 | `app/services/pipeline.py` | Ingestion entry point |
| M1 | `app/services/m1_session.py` | Session state, token budgeting |
| M2 | `app/services/m2_facts.py` | Fact/decision extraction, validation, supersession |
| M3 | `app/services/m3_temporal.py` | Time-travel queries, snapshots, diffs |
| M4 | `app/services/m4_graph.py` | Knowledge graph, community detection |
| M5 | `app/services/m5_retrieval.py` | Hybrid retrieval (vector + BM25 + graph) |

**Memory record model:**
- `Memory`: content, metadata, source references, temporal_status, confidence
- `MemoryProvenance`: evidence_type, source_references, confidence_score
- `MemoryEntity`: entity_type, canonical_name, metadata

**Memory lifecycle:** create → (update) → delete (soft)
Supersession is modeled but not enforced in current code paths.

**Persistence:** All memory objects persist to PostgreSQL. No separate
cache or vector store — BM25 is used for keyword retrieval.

================================================================================
11. STORAGE ARCHITECTURE
================================================================================

**Object storage backends:**
- Local filesystem (default)
- AWS S3
- MinIO

**Selection:** `storage_backend` config key
**Implementation:** Factory pattern in `app/services/object_storage.py`

**File operations:** upload, get_file_info, delete
**Scope:** Per-workspace, per-project

================================================================================
12. SECURITY ARCHITECTURE
================================================================================

**Authentication:** JWT Bearer tokens (HS256)
- Access token: 60 minutes
- Refresh token: 30 days, stored in DB with revocation flag
- Password hashing: bcrypt via passlib

**Authorization:** 4-tier RBAC
- OWNER, ADMIN (500), MEMBER (100), VIEWER (50)
- Hierarchical permission inheritance
- PolicyEngine integration for role checks

**Tenancy:** `TenantContext` dependency extracts workspace/project/tenant
from JWT claims and request context.

**Security controls:**

| Control | Status | Location |
|---------|--------|----------|
| Security headers | IMPLEMENTED | `app/main.py` (SecurityHeadersMiddleware) |
| CORS | IMPLEMENTED | `app/main.py` (CORSMiddleware) |
| Rate limiting | IMPLEMENTED | `app/middleware/rate_limit.py` |
| Password hashing | IMPLEMENTED | `app/core/security.py` (bcrypt) |
| JWT validation | IMPLEMENTED | `app/middleware/auth.py` |
| Tenant isolation | PARTIAL | workspace_id+user_id enforced; tenant_id inconsistent |
| CSRF protection | MISSING | Not implemented |
| Account lockout | MISSING | Not implemented |
| Token revocation | PARTIAL | Refresh tokens revocable; access tokens stateless |
| Encryption at rest | MISSING | No database encryption |
| PII encryption | MISSING | No field-level encryption |
| Input sanitization (XSS) | UNKNOWN | Not verified in this audit |
| SQL injection protection | PARTIAL | ILIKE patterns may be exploitable |
| Request size limits | PARTIAL | Schema max_length only |
| Security headers | IMPLEMENTED | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, HSTS (prod), CSP |
| Audit logging | PARTIAL | In-memory only, not persistent |
| Secrets management | PARTIAL | Env vars; no vault integration |
| Debug mode SQL logging | VERIFIED | Needs verification |

**CRITICAL SECURITY FINDINGS:**

| ID | Finding | Severity | Verified |
|----|---------|----------|----------|
| SEC-001 | Hardcoded fallback secrets in config.py | P0 | YES |
| SEC-002 | Dual authentication paths (auth.py vs tenancy.py) | P0 | YES |
| SEC-003 | Memory tenant isolation inconsistent | P1 | PARTIAL |
| SEC-004 | Chat message persistence before LLM call | P1 | UNVERIFIED |
| SEC-005 | No token revocation mechanism | P0 | YES |
| SEC-006 | No account lockout | P2 | NOT VERIFIED |
| SEC-007 | Rate limiter bypass via X-E2E header | P1 | NOT VERIFIED |
| SEC-008 | Security headers — DOCUMENTED AS MISSING but IMPLEMENTED | N/A | DOC ERROR |

**NOTE:** SEC-008 finding is a documentation error. Security headers ARE
implemented in `app/main.py` (SecurityHeadersMiddleware). The findings
register is incorrect.

================================================================================
13. TENANCY ARCHITECTURE
================================================================================

**Three-level hierarchy:**
```
Tenant
  └── Workspace
        └── Project
```

**TenantContext** (`app/middleware/tenancy.py`):
- Extracted from JWT claims
- Contains: tenant_id, workspace_id, project_id, user_id, role
- Injected as dependency into all protected routes

**Isolation enforcement:**
- All queries filter by `workspace_id`
- Most queries filter by `user_id`
- `tenant_id` filtering is INCONSISTENT — some write paths enforce it,
  some read paths do not

**Cross-tenant risk:** LOW-MEDIUM. workspace_id+user_id provides partial
isolation, but a bug in tenant_id filtering could allow cross-workspace
access in edge cases.

================================================================================
14. PIPELINE ARCHITECTURE
================================================================================

**Entry point:** `POST /api/v1/ingest/upload`
**Orchestrator:** `app/services/pipeline.py::run_pipeline()`

**Stages:**

```
M0 (Ingestion)
  Input: Raw text/JSON/JSONL + source_type
  Validation: Pydantic schema (max_length, required fields)
  Output: Source record (status=processing)
  Guardrail: Schema validation, size limits, content-hash dedup

M1 (Normalization)
  Input: Source record + raw content
  Transformation: Parse by source_type (claude-code, generic text, JSON, JSONL)
  Output: NormalizedMessage records
  Guardrail: Source-type validation, message structure validation

M2 (Fact/Decision Extraction)
  Input: Normalized messages
  Transformation: LLM-based extraction of facts and decisions
  Output: Fact records, Decision records with provenance
  Guardrail: Validation rules, confidence thresholds, supersession checks

M3 (Temporal Processing)
  Input: Facts and decisions
  Transformation: Temporal status assignment, supersession chains
  Output: Temporally-tagged records
  Guardrail: Temporal consistency checks, conflict detection

M4 (Graph Construction)
  Input: Facts, decisions, entities
  Transformation: Entity extraction, relationship creation, community detection
  Output: GraphNode records, GraphEdge records
  Guardrail: Graph validation, duplicate detection

M5 (Retrieval)
  Input: All knowledge objects
  Transformation: Indexing for BM25 + vector + graph search
  Output: Searchable index
  Guardrail: None observed
```

**Pipeline is synchronous** — runs within the request context. No background
tasks, no job queue. Long-running ingestions may timeout.

================================================================================
15. M0–M5 ARCHITECTURE
================================================================================

**M0 — Ingestion:**
- Endpoint: `POST /api/v1/ingest/upload`
- Handlers: `ClaudeCodeConnector`, `GenericTextConnector`, JSON/JSONL parsers
- Deduplication: SHA-256 content hash
- Output: Source record with stage tracking

**M1 — Normalization:**
- Service: `app/services/m1_session.py`
- Parses raw content into canonical message format
- Token counting via `count_tokens()` (max 200K total, 80K per session)
- Output: NormalizedMessage records linked to Source

**M2 — Fact/Decision Extraction:**
- Service: `app/services/m2_facts.py`
- LLM-based extraction with validation
- Supersession tracking via `superseded_by` field
- Confidence scoring with weighted evidence
- Deduplication via `_find_similar_open_drafts`
- Output: Fact, Decision, FactProvenance records

**M3 — Temporal Processing:**
- Service: `app/services/m3_temporal.py`
- Time-travel queries: `snapshot_at()`, `version_between()`
- Content diff computation with opcodes
- Snapshot branching for concurrent edits
- Output: Snapshot records, temporal_status updates

**M4 — Graph Construction:**
- Service: `app/services/m4_graph.py`
- Entity and relationship extraction
- Community detection via `cluster_graph()`
- God-node detection
- Evidence classification (extracted/inferred/ambiguous)
- Output: GraphNode, GraphEdge, GraphCommunity records

**M5 — Retrieval:**
- Service: `app/services/m5_retrieval.py`
- Multi-strategy: BM25 + vector + graph traversal
- Context pack building with token budgeting
- Hybrid scoring with configurable weights
- Output: RetrievalResult with source attribution

================================================================================
16. GUARDRAIL ARCHITECTURE
================================================================================

**Stage-by-stage guardrails (summary):**

| Stage | Guardrail | Status | Enforcement |
|-------|-----------|--------|-------------|
| M0 | Schema validation | ACTIVE | Pydantic validators |
| M0 | Content-hash dedup | ACTIVE | SHA-256 in DB query |
| M0 | Size limits | ACTIVE | Schema max_length |
| M0 | Source-type validation | ACTIVE | Connector registry |
| M1 | Token budgeting | ACTIVE | count_tokens() limits |
| M1 | Message structure | ACTIVE | Pydantic schemas |
| M2 | Confidence thresholds | PARTIAL | Scoring exists, enforcement unclear |
| M2 | Supersession | PARTIAL | Schema supports, logic incomplete |
| M2 | Validation rules | ACTIVE | FactValidation model |
| M3 | Temporal consistency | PARTIAL | Checks exist, coverage unclear |
| M4 | Graph validation | PARTIAL | Basic checks, no formal validation |
| M5 | Token budgeting | ACTIVE | build_context_pack() |

**Cross-cutting guardrails:**
- Authentication: ACTIVE (JWT on all protected routes)
- Authorization: ACTIVE (RBAC via require_min_role/require_permission)
- Tenancy: PARTIAL (workspace+user enforced, tenant_id inconsistent)
- Rate limiting: ACTIVE (per-endpoint limits)
- Error sanitization: PARTIAL (no PII scrubbing in errors)
- Audit logging: PARTIAL (in-memory, not persistent)

================================================================================
17. VALIDATION ARCHITECTURE
================================================================================

**Request validation:** Pydantic schemas for all endpoints
**Response validation:** Pydantic response_model declarations
**Business validation:** Service-layer checks
**Database validation:** SQLAlchemy column constraints (nullable, length)

**Validation gaps:**
- No input sanitization for XSS (SEC-010)
- No explicit SQL injection prevention beyond ORM (SEC-009)
- No request size limits at middleware level (SEC-013)
- No validation that provenance references exist before fact creation

================================================================================
18. PROVENANCE ARCHITECTURE
================================================================================

**Models:**
- `MemoryProvenance`: evidence_type, source_references, confidence_score
- `FactProvenance`: evidence_type, source_references, confidence_score
- `ProvenanceChain`: chain_steps (JSON array of linked provenance records)

**Evidence types:** extracted, inferred, ambiguous (EvidenceType enum)

**Provenance chain validation:** `app/services/m2_facts.py:validate_provenance_chain()`

**Gaps:**
- No evidence deprecation mechanism
- No chain repair tool
- No enforcement that all claims must have provenance

================================================================================
19. AUDIT ARCHITECTURE
================================================================================

**Service:** `app/services/audit/`
**Storage:** In-memory Python list (EventStore)
**Event types:** policy, memory, tool, model
**Event categories:** success, failure, denied, pending

**CRITICAL GAP:** Audit events are lost on process restart.
No persistent audit store exists.

**Available events:**
- MEMORY_READ, MEMORY_WRITE, MEMORY_UPDATE, MEMORY_DELETE
- INGEST_COMPLETED, INGEST_FAILED
- SOURCE_DELETED
- API_KEY_CREATED, API_KEY_REVOKED, API_KEY_ROTATED
- RESULT_SUCCESS, RESULT_FAILURE

================================================================================
20. RETRIEVAL ARCHITECTURE
================================================================================

**Service:** `app/services/m5_retrieval.py`
**Strategies:**
1. BM25 keyword search (`rank_bm25`)
2. Graph traversal (`query_graph`)
3. Vector search (semantic_search)

**Context pack building:** `build_context_pack()` with token budgeting
**Scoring:** Weighted combination of vector, BM25, and graph scores
**Source attribution:** ContextSource model with source_type, source_id, score

**API endpoint:** `POST /api/v1/ingest/search`

**Gaps:**
- No result caching (beyond lru_cache for temporal queries)
- No streaming for large result sets
- No cache invalidation on memory updates

================================================================================
21. SSE/STREAMING ARCHITECTURE
================================================================================

**Endpoint:** `POST /api/v1/chat/stream`
**Implementation:** FastAPI StreamingResponse with text/event-stream
**Events:** token, sources, done, error

**Frontend:** EventSource-based parsing in chat page

**Single streaming endpoint.** No other SSE streams exist.

================================================================================
22. INGESTION ARCHITECTURE
================================================================================

**Endpoint:** `POST /api/v1/ingest/upload`
**Legacy:** `POST /api/v1/ingest/` (creates IngestJob, no pipeline execution)

**Source types supported:**
- `text` — raw text
- `json` — JSON format
- `jsonl` — JSONL format
- `claude-code` — Claude Code session JSONL

**Connectors:** `app/services/connectors.py`
- ClaudeCodeConnector (lines 295-398)
- Registered in connector registry (line 650+)

**Processing:** Synchronous within request. Pipeline writes Source,
NormalizedMessage, Fact, Decision, GraphNode, GraphEdge records directly
to PostgreSQL — does NOT go through MemoryService.

**Gap:** Pipeline writes bypass MemoryService. Whether this is intentional
or a governance gap requires M-ARCH team determination.

================================================================================
23. INTEGRATION ARCHITECTURE
================================================================================

| Integration | Status | Evidence |
|-------------|--------|----------|
| MCP Server | DOCUMENTED_ONLY | `app/api/api_keys.py:1-12`, `app/models.py:692-730` |
| Claude Code | IMPLEMENTED | `app/services/connectors.py:295-398` (data format) |
| Codex | MISSING | No references in `app/` |
| Universal Adapter | MISSING | No references in `app/` |
| Anthropic LLM | IMPLEMENTED | `app/services/llm.py` |
| OpenAI LLM | IMPLEMENTED | `app/services/llm.py` |
| Mock LLM | IMPLEMENTED | `app/services/llm.py` (fallback) |
| Local Storage | IMPLEMENTED | `app/services/object_storage.py` |
| S3 Storage | IMPLEMENTED | `app/services/object_storage_s3.py` |
| MinIO Storage | IMPLEMENTED | `app/services/object_storage_minio.py` |

================================================================================
24. DEPLOYMENT ARCHITECTURE
================================================================================

**Current:** Development mode only
- `npm run dev` (frontend, port 3000)
- `uvicorn app.main:app --reload` (backend, port 8000)
- No Docker configuration in repository
- No CI/CD configuration
- No environment-specific deployment configs

**Environment files:**
- `.env.example` (root)
- `.env.example` (frontend)
- No `.env.local` committed

================================================================================
25. FAILURE & RECOVERY ARCHITECTURE
================================================================================

**Current state:**
- No retry logic for database operations
- No circuit breakers
- No durable queues
- No transaction rollback on pipeline failure (confirmed by code trace)
- No process restart recovery
- Audit events lost on restart

**Failure modes documented:**
- Pipeline failure: Source remains in `processing` status
- LLM failure: May leave orphan messages (SEC-004, unverified)
- Database connection loss: Process crashes, no auto-reconnect
- Storage failure: File operations raise exceptions

================================================================================
26. OBSERVABILITY ARCHITECTURE
================================================================================

**Current:**
- Request ID middleware (X-Request-ID)
- Exception handlers with error type classification
- In-memory audit service
- No structured logging (Python logging module, not configured)
- No metrics collection
- No tracing (OpenTelemetry, Jaeger, etc.)
- No health check endpoints (exist but minimal)

**Health endpoints:**
- `GET /health` — basic liveness
- `GET /health/live` — liveness probe
- `GET /health/ready` — readiness probe (checks DB + storage)

================================================================================
27. TEST ARCHITECTURE
================================================================================

**Backend tests:** `tests/` directory
**Frontend tests:** Playwright E2E (`frontend/e2e/`)
**Test contracts:** `frontend/e2e/remaining-contracts.spec.ts`

**Coverage status:** Not measured. No pytest configuration or coverage
tooling found.

**Known test gaps:**
- No adversarial security tests
- No multi-tenant isolation tests
- No pipeline failure recovery tests
- No audit persistence tests
- No migration tests

================================================================================
28. CURRENT LIMITATIONS
================================================================================

1. **Empty Alembic versions:** Schema changes not migratable in production
2. **In-memory audit store:** Audit trail lost on restart
3. **Synchronous pipeline:** Long ingestions may timeout
4. **No encryption at rest:** Data stored in plaintext
5. **No CSRF protection:** State-changing endpoints vulnerable
6. **Inconsistent tenant_id enforcement:** Potential cross-tenant data leak
7. **No failure recovery:** Partial writes not rolled back
8. **No caching:** Repeated queries hit database unnecessarily
9. **No streaming for retrieval:** Large results may cause memory issues
10. **No MCP/Codex/Universal Adapter:** Documented but not implemented
11. **Hardcoded fallback secrets:** Development credentials in config
12. **Dual authentication paths:** auth.py and tenancy.py both decode tokens

================================================================================
29. TECHNICAL DEBT
================================================================================

| Debt | Severity | Evidence |
|------|----------|----------|
| Empty Alembic versions/ | CRITICAL | `app/alembic/versions/` is empty |
| In-memory audit store | HIGH | `app/services/audit/` EventStore uses Python list |
| Synchronous pipeline | HIGH | `run_pipeline()` blocks request thread |
| Hardcoded fallback secrets | HIGH | `app/core/config.py:8-9` |
| Inconsistent tenant_id | HIGH | Mixed enforcement across endpoints |
| No CSRF protection | MEDIUM | No CSRF middleware |
| No failure recovery | MEDIUM | No retry/circuit breaker/rollback |
| No caching layer | MEDIUM | Every query hits database |
| Undocumented endpoints | MEDIUM | Security doc references non-existent forgot-password |
| No input sanitization | MEDIUM | No XSS prevention beyond headers |
| No rate limit per user | LOW | Rate limits keyed by IP/header, not authenticated user |
| Duplicate next.config files | LOW | `next.config.js` and `next.config.mjs` |

================================================================================
30. FUTURE MEMORY INTELLIGENCE BOUNDARY
================================================================================

**What the current system CAN safely provide to a future Memory Intelligence Layer:**

| Capability | Readiness | Evidence |
|------------|-----------|----------|
| Memory CRUD operations | GREEN | `app/services/memory.py`, `app/api/memory.py` |
| Fact extraction with provenance | GREEN | `app/services/m2_facts.py` |
| Temporal state tracking | YELLOW | Schema supports, enforcement partial |
| Graph relationships | GREEN | `app/services/m4_graph.py` |
| Hybrid retrieval | YELLOW | Implemented but no caching/streaming |
| Provenance chains | YELLOW | Models exist, enforcement incomplete |
| Confidence scoring | YELLOW | Implemented, thresholds unclear |
| Supersession tracking | YELLOW | Schema supports, logic incomplete |
| Audit trail | RED | In-memory only, lost on restart |
| Persistent memory guarantee | RED | No WAL, no transaction boundaries for memory ops |
| Cross-module identity | RED | UUIDs generated independently per module |
| Memory explainability | YELLOW | Provenance exists, not exposed via API |

**What the next layer MUST NOT assume:**
1. Audit events are persistent (they are not)
2. Memory writes are transactional (they are not)
3. Identity is consistent across M1-M5 (it is not)
4. Supersession is enforced (it is not)
5. Evidence is mandatory for claims (it is not)

**Required conditions before Memory Intelligence Layer:**
1. Persistent audit store (database-backed)
2. Transaction boundaries for memory operations
3. Identity resolution mechanism
4. Enforced provenance requirements
5. Completed Alembic migrations
6. Verified tenant_id consistency

================================================================================
31. ARCHITECTURAL READINESS ASSESSMENT
================================================================================

| Dimension | Rating | Justification |
|-----------|--------|---------------|
| Backend completeness | 7/10 | 72 endpoints, 14 routers, functional but missing retry/recovery |
| Frontend completeness | 6/10 | Core views exist, gaps in routing/404/accessibility |
| Security posture | 4/10 | Auth/RBAC work, but 8+ unverified/missing controls |
| Data integrity | 5/10 | ORM provides baseline, but no migrations = schema drift |
| Memory readiness | 5/10 | M1-M5 exist, but inconsistent enforcement and in-memory audit |
| Pipeline robustness | 4/10 | Synchronous, no retry, no circuit breaker |
| Observability | 3/10 | Request IDs only, no structured logging/metrics/tracing |
| Deployment readiness | 2/10 | Development mode only, no Docker/CI/CD |
| Test coverage | 2/10 | E2E contracts exist, no unit/integration/security tests |
| Documentation accuracy | 5/10 | Multiple docs reference non-existent features |

**Overall readiness for production: 4/10**
**Overall readiness for Memory Intelligence Layer: 3/10**

================================================================================
EVIDENCE CROSS-REFERENCE
================================================================================

All specialist documents referenced in this synthesis:

| Document | Status | Key Findings |
|----------|--------|--------------|
| SWARMVAULT_BACKEND_ARCHITECTURE.md | EXISTS | 72 endpoints, 14 routers, startup/shutdown flow |
| SWARMVAULT_DATA_MEMORY_ARCHITECTURE.md | EXISTS | M0-M5 pipeline, data lineage, soft deletion |
| SWARMVAULT_GUARDRAILS_VALIDATION_ARCHITECTURE.md | EXISTS | Stage-by-stage matrix, active/missing/bypassable |
| SWARMVAULT_API_INTEGRATION_ARCHITECTURE.md | EXISTS | Complete route inventory, integration classifications |
| SWARMVAULT_FRONTEND_ARCHITECTURE.md | EXISTS | Next.js routes, components, API client |
| SWARMVAULT_SECURITY_OPERATIONAL_ARCHITECTURE.md | EXISTS | Auth, RBAC, tenancy, security controls |
| SWARMVAULT_MEMORY_INTELLIGENCE_READINESS.md | EXISTS | Memory readiness scorecard |
| SWARMVAULT_END_TO_END_FLOWS.md | EXISTS | 25 documented flows |
| SWARMVAULT_GUARDRAIL_MASTER_MATRIX.md | EXISTS | Complete guardrail matrix |
| SWARMVAULT_PERSISTENT_MEMORY_READINESS.md | EXISTS | GREEN/YELLOW/RED classification |
| SWARMVAULT_FRONTEND_BACKEND_ARCHITECTURE.md | EXISTS | Screen-to-API-to-DB traceability |
| SWARMVAULT_ARCHITECTURAL_TRACEABILITY.md | EXISTS | Requirement-to-feature traceability |
| SWARMVAULT_ARCHITECTURAL_GAPS_AND_MEMORY_NEXT_LAYER.md | EXISTS | P0-P3 gaps, memory layer boundary |
| CONTRACT_IMPLEMENTATION_RECONCILIATION.md | EXISTS | 11 contract docs audited vs implementation |

**Reconciliation findings:**
- SEC-008 documented as MISSING but IMPLEMENTED — documentation error
- `forgot-password`/`reset-password` documented but not implemented
- 5 model changes without migrations — production schema drift
- In-memory audit store contradicts "persistent audit" requirements in contracts

================================================================================
END OF MASTER ARCHITECTURE
================================================================================
