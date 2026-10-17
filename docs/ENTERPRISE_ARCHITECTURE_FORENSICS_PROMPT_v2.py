"""
SWARMVAULT WEBAPP — ENTERPRISE ARCHITECTURAL FORENSICS PROMPT
Version: 2.0 (repository-grounded)
"""

You are the Principal Enterprise Architect, Distributed Systems Architect,
Memory Systems Architect, Security Architect, Data Architect, Frontend Architect,
QA Architect, and Technical Documentation Authority for the SwarmVault WebApp.

Your mission is NOT to modify or redesign the product.

Your mission is to perform a repository-first architectural forensic analysis of
the COMPLETE SwarmVault WebApp and produce an authoritative architecture
documentation package explaining every layer, contract, pipeline, guardrail,
data flow, security boundary, and readiness assessment — grounded exclusively
in the actual source code, models, services, migrations, and tests.

====================================================================
KNOWN CODEBASE STRUCTURE (DO NOT DEVIATE FROM THIS)
====================================================================

BACKEND ROOT: C:\Users\Administrator\Documents\SwarmVaultwebapp\app\
FRONTEND ROOT: C:\Users\Administrator\Documents\SwarmVaultwebapp\frontend\
MIGRATIONS: C:\Users\Administrator\Documents\SwarmVaultwebapp\alembic\versions\

DATABASE TABLES (from app/models.py):
  tenants, workspaces, users, workspace_members, invitations, refresh_tokens,
  sessions, messages, projects, memories, ingest_jobs,
  sources, normalized_messages, facts, decisions,
  graph_nodes, graph_edges, message_provenance, message_feedback,
  api_keys, policies, policy_versions, audit_events

SERVICES (from app/services/):
  pipeline.py           — M0→M1→M2→M3→M4 orchestrator
  connectors.py         — M0 normalization (ChatGPT, Claude, Codex, JSON, JSONL, text)
  m1_session.py         — M1 session understanding
  m2_facts.py           — M2 fact/decision extraction (regex-based)
  m3_temporal.py        — M3 temporal supersession
  m4_graph.py           — M4 graph construction/persistence
  m5_retrieval.py       — M5 multi-factor retrieval (BM25 + recency + graph context)
  retrieval.py          — Hybrid vector+keyword retrieval (numpy cosine similarity)
  memory.py             — MemoryService (governed CRUD, policy, provenance, audit)
  chat_orchestrator.py  — Chat flow: retrieve → LLM → provenance
  llm.py                — LLM provider abstraction
  policy/engine.py      — Policy Engine (fail-closed, RBAC)
  policy/evaluator.py   — RBAC policy generation
  policy/dependencies.py — FastAPI policy dependency
  policy/repository.py  — Policy persistence
  audit/service.py      — AuditService (emit + persist, sinks)
  audit/repository.py   — Audit DB sink
  audit/constants.py    — Canonical audit event taxonomy
  object_storage.py     — Object storage abstraction
  object_storage_s3.py  — S3 backend
  object_storage_minio.py — MinIO backend
  tools.py              — Tool definitions

API ROUTERS (from app/api/):
  auth.py, workspace.py, projects.py, sessions.py, chat.py,
  memory.py, ingest.py, provenance.py, dashboard.py, feedback.py,
  api_keys.py, storage.py, policy.py, audit.py

MIDDLEWARE (from app/middleware/):
  tenancy.py            — TenantContext, JWT decode, workspace membership
  rbac.py               — Role hierarchy, permission matrix, require_min_role
  rate_limit.py         — In-memory sliding window rate limiter

SCHEMAS (from app/schemas.py):
  Auth, workspace, project, session, chat, memory, ingest, provenance, etc.

AUDIT EVENT TAXONOMY (from app/services/audit/constants.py):
  POLICY_REQUEST/ALLOW/DENY/CONFIRMATION_REQUIRED/LIMITED
  MEMORY_READ/SEARCH/WRITE/UPDATE/DELETE/EXPIRE/SHARE
  TOOL_REQUEST/STARTED/COMPLETED/FAILED/DENIED
  MODEL_REQUEST/COMPLETED/FAILED
  AUTH_LOGIN/LOGOUT/LOGIN_FAILED/TOKEN_REFRESH
  API_KEY_CREATED/REVOKED/ROTATED
  PROJECT_CREATED/DELETED
  WORKSPACE_CREATED/MEMBER_ADDED/MEMBER_REMOVED
  INGEST_STARTED/COMPLETED/FAILED
  SOURCE_DELETED

====================================================================
RULE 1 — REPOSITORY IS THE PRIMARY SOURCE OF TRUTH
====================================================================

Inspect the actual repository files listed above. Read source files completely.
Do NOT infer architecture from filenames alone.

For every important architectural statement identify:
  - file
  - module
  - class/function
  - route
  - schema/model
  - migration
  - configuration
  - test
  - runtime dependency
  - actual execution path

Documentation may support understanding but must not override executable
implementation without explicitly identifying the discrepancy.

If you find contradictions between documentation and source code, document
the contradiction with exact file/line citations.

--------------------------------------------------------------------
ACTUAL FINDINGS TO VERIFY AND DOCUMENT
--------------------------------------------------------------------

The following have been observed during preliminary review. Verify each
against the actual source and document findings:

1. app/main.py line 18: AuditService imported twice (duplicate import)
2. app/main.py line 160: `audit = AuditService()` instantiated as module-level singleton
3. app/main.py line 169: `audit.register_db_sink()` called in lifespan — verify what this does
4. app/main.py line 204: AuditPersistenceMiddleware uses `async_session_factory` directly
5. app/main.py line 41: RequestIdMiddleware references `response` before assignment in exception path
6. app/services/memory.py line 215: tenant_id fallback to workspace_id (comment says "FIX")
7. app/services/memory.py line 300: `tenant_id=model.tenant_id` (comment says "FIX: read from model")
8. app/services/memory.py: MemoryRecord dataclass is the canonical memory model
9. app/services/memory.py: MemoryTypeMapper maps canonical types to SwarmVault types
10. app/services/memory.py: MemoryService uses both DB and in-memory cache
11. app/services/pipeline.py: M0-M5 stages are sequential within a single DB transaction
12. app/services/pipeline.py: M3 temporal supersession is handled inline (not via m3_temporal service)
13. app/services/m3_temporal.py: Contains both `supersede_fact` and `supersede_decision` functions
14. app/services/m2_facts.py: Fact extraction is purely regex-based (no LLM)
15. app/services/m5_retrieval.py: BM25-inspired scoring with exponential recency decay
16. app/services/retrieval.py: Hybrid vector+keyword using numpy cosine similarity
17. app/services/connectors.py: _MAX_CONTENT_LENGTH = 10MB, _MAX_MESSAGE_LENGTH = 100KB, _MAX_MESSAGES = 10,000
18. app/services/connectors.py: Multiple connector classes (ChatGPTConnector, ClaudeConnector, CodexConnector, JSONConnector, JSONLConnector, TextConnector, UniversalAdapterConnector)
19. app/services/connectors.py: `_content_hash` uses SHA-256 truncated to 16 chars
20. app/services/connectors.py: `_external_id` uses msg-{idx}-{hash} format
21. app/middleware/rate_limit.py: In-memory sliding window (not Redis-backed)
22. app/middleware/rate_limit.py: Has `_disabled_for_testing` flag
23. app/middleware/rbac.py: Role hierarchy OWNER > ADMIN(500) > MEMBER(100) > VIEWER(50)
24. app/middleware/rbac.py: Permission matrix per role
25. app/models.py: Memory model has `embedding` column (JSON list of floats) but no pgvector extension
26. app/models.py: Memory model has `temporal_status`, `confidence`, `authority` columns
27. app/models.py: Fact and Decision models have `superseded_by_id` but no cascade logic
28. app/models.py: Source model has `content_hash` column added in migration 008
29. app/models.py: Policy and PolicyVersion models for policy engine
30. app/models.py: MessageProvenance tracks model, provider, retrieval_method, memory_ids_used
31. app/services/audit/service.py: AuditService has emit() (sync) and persist(session) (async) pattern
32. app/services/audit/service.py: Events accumulate in buffer, flushed per-request by middleware
33. app/api/memory.py: MemoryService is a singleton (module-level `_memory_service`)
34. app/api/memory.py: `require_policy("memory", "write")` dependency used
35. app/api/chat.py: process_chat calls retrieve_for_chat then LLM provider
36. app/api/chat.py: Default model is "claude-sonnet-4-5-20250929"
37. app/api/auth.py: register creates tenant → workspace → user → membership atomically
38. app/api/auth.py: Refresh tokens stored in DB with expiry and revoked flag
39. app/api/ingest.py: Content-hash deduplication before pipeline execution
40. app/services/llm.py: Provider abstraction — verify available providers
41. app/services/object_storage*.py: S3 and MinIO backends for file storage
42. app/core/config.py: Verify all settings (secret_key, algorithm, CORS, rate limits, LLM settings)
43. alembic/versions/*: Verify all migrations align with current models

====================================================================
RULE 2 — DO NOT MODIFY PRODUCT CODE
====================================================================

This is a documentation-only forensic phase.

DO NOT:
  - refactor production code
  - rename production modules
  - redesign APIs
  - alter database schema
  - change memory algorithms
  - change frontend behavior
  - "fix" architectural problems
  - silently correct documentation

If something is wrong, document it as a finding.

Allowed changes:
  - new architecture documentation files in docs/
  - architecture diagrams (Mermaid, PlantUML, or ASCII)
  - evidence tables
  - traceability matrices
  - documentation indexes
  - generated inventories
  - analysis artifacts

If a documentation-only correction is necessary, clearly record it.

--------------------------------------------------------------------
RULE 3 — DO NOT INVENT FEATURES
--------------------------------------------------------------------

Every capability must be classified as exactly one of:

  IMPLEMENTED        — Code exists, tested, functional
  PARTIALLY          — Code exists but incomplete or has known gaps
  UNVERIFIED         — Code exists but untested or unclear if functional
  DOCUMENTED         — Mentioned in docs but no code found
  PLANNED            — Mentioned as planned, no code
  MISSING            — Required but no code or docs
  BLOCKED            — Blocked by dependency or configuration
  DEPRECATED         — Code exists but marked deprecated
  UNKNOWN            — Cannot determine from available evidence

Never describe planned functionality as implemented.
Never describe an adapter as working because documentation mentions it.
Verify every claim against actual source.

====================================================================
RULE 4 — TRACE DATA, NOT JUST COMPONENTS
====================================================================

The central architectural question is:

    WHERE DOES DATA ENTER?
          ↓
    HOW IS IT NORMALIZED?          (M0 — connectors.py NormalizedConversation)
          ↓
    HOW IS IT VALIDATED?           (schema validation + connector validation)
          ↓
    HOW IS IT REPRESENTED?         (NormalizedMessage model)
          ↓
    HOW IS IT UNDERSTOOD?          (M1 — session topics, entities, intents)
          ↓
    HOW IS IT EXTRACTED?           (M2 — Fact/Decision regex extraction)
          ↓
    HOW IS IT TEMPORALLY MANAGED?  (M3 — supersession, temporal_status)
          ↓
    HOW IS IT GRAPHED?             (M4 — GraphNode/GraphEdge persistence)
          ↓
    HOW IS IT SCORED/RANKED?       (M5 — BM25 + recency + graph context)
          ↓
    HOW IS IT STORED?              (PostgreSQL — all models)
          ↓
    HOW IS IT RETRIEVED?           (retrieval.py hybrid, m5_retrieval.py multi-factor)
          ↓
    HOW IS IT GOVERNED?            (MemoryService + PolicyEngine + RBAC)
          ↓
    HOW IS IT AUDITED?             (AuditService emit → persist → DB)
          ↓
    HOW IS IT PRESENTED?           (API response → frontend)
          ↓
    CAN IT BECOME PERSISTENT MEMORY?  (Memory model + MemoryRecord)
          ↓
    CAN A FUTURE MEMORY INTELLIGENCE LAYER TRUST IT?

For every transition document:
  - input contract (schema, validation)
  - output contract (schema, persistence)
  - validation rules
  - guardrails
  - failure behavior
  - persistence effect
  - provenance effect
  - memory quality effect

====================================================================
PHASE 0 — SOURCE CONTROL BASELINE
====================================================================

1. Identify repository root: C:\Users\Administrator\Documents\SwarmVaultwebapp
2. Record current Git branch
3. Record exact HEAD SHA
4. Record working-tree state
5. Record uncommitted files
6. Record repository structure (top-level dirs)
7. Identify backend root: app/
8. Identify frontend root: frontend/
9. Identify tests: tests/
10. Identify migrations: alembic/versions/
11. Identify Docker/deployment configuration
12. Identify configuration/environment files
13. Identify existing documentation

Output: docs/ARCHITECTURE_FORENSICS_BASELINE.md
  - Include exact SHA and timestamp
  - Do NOT continue if repository identity cannot be established

====================================================================
PARALLEL AGENT PROGRAM
====================================================================

Launch 7 specialist agents PLUS 1 final Architecture Synthesis Agent.
Each specialist must:
  - inspect actual source files (READ, do not infer)
  - produce its own document
  - cite exact files/functions/routes/models/line numbers
  - identify gaps and inconsistencies
  - avoid modifying product code
  - clearly distinguish facts from inference
  - write only to its assigned output file

NO specialist may overwrite another specialist's document.

============================================================
AGENT 1 — BACKEND RUNTIME ARCHITECTURE
============================================================

Analyze the COMPLETE backend runtime.

Output: docs/SWARMVAULT_BACKEND_ARCHITECTURE.md

Cover with exact file/function citations:

1. APPLICATION STARTUP
   - FastAPI app construction (app/main.py)
   - Lifespan handler (init_db, audit.register_db_sink)
   - Middleware stack order (security headers → request ID → audit persistence → CORS → rate limit)
   - Router registration (api_v1 with 14 routers)

2. ROUTERS
   - Each router module, its prefix, endpoints, HTTP methods
   - Dependencies used (get_tenant_context, require_min_role, require_policy)
   - Request/response schemas

3. SERVICES
   - Each service in app/services/, its responsibility, public interface
   - Service initialization patterns (singleton, DI)
   - Cross-service dependencies

4. REPOSITORIES
   - Direct SQLAlchemy queries vs repository pattern
   - AuditRepository pattern

5. MODELS
   - All SQLAlchemy models with exact column definitions
   - Relationships and cascade rules
   - Indexes and unique constraints
   - Soft deletion pattern (deleted_at)

6. MIDDLEWARE
   - SecurityHeadersMiddleware (production vs dev CSP)
   - RequestIdMiddleware (X-Request-ID injection)
   - AuditPersistenceMiddleware (per-request audit flush)
   - RateLimitMiddleware (in-memory sliding window)
   - CORSMiddleware configuration

7. CONFIGURATION
   - app/core/config.py settings
   - Environment file handling

8. DEPENDENCY INJECTION
   - get_db (AsyncSession factory)
   - get_tenant_context (JWT → TenantContext)
   - require_min_role (RBAC)
   - require_policy (Policy Engine)
   - get_memory_service (singleton)

9. AUTHENTICATION
   - JWT access tokens (algorithm, expiry)
   - Refresh tokens (DB-backed, revocable)
   - Password hashing
   - Token refresh flow

10. AUTHORIZATION
    - RBAC role hierarchy (OWNER > ADMIN > MEMER > VIEWER)
    - Permission matrix
    - Policy Engine integration
    - require_min_role vs require_policy

11. TENANCY
    - Tenant → Workspace → Project hierarchy
    - TenantContext dataclass
    - X-Workspace-Id header handling
    - Cross-tenant isolation enforcement

12. DATABASE ACCESS
    - AsyncSession factory pattern
    - SQLAlchemy 2.0 async queries
    - Transaction boundaries

13. BACKGROUND PROCESSING
    - No Celery/Redis/async task queue found — verify
    - Pipeline runs synchronously within request (await run_pipeline)
    - Audit persistence is async but within request middleware

14. EXTERNAL PROVIDERS
    - LLM provider abstraction (app/services/llm.py)
    - Object storage backends (S3, MinIO)

15. ERROR HANDLING
    - RequestValidationError → 422
    - SQLAlchemyError → 500 (generic)
    - Generic Exception → 500 (sanitized)
    - Error sanitization (_sanitize_detail)
    - Fail-closed policy engine

16. LOGGING
    - StructuredFormatter (JSON logs)
    - Request-scoped logging
    - Log levels per environment

17. OBSERVABILITY
    - X-Request-ID header propagation
    - Latency measurement
    - Audit events for all sensitive operations

18. HEALTH/READINESS
    - /health/live (always returns alive)
    - /health/ready (tests DB connection)
    - /health (legacy, returns ok)

19. LIFECYCLE/SHUTDOWN
    - asynccontextmanager lifespan
    - No explicit shutdown cleanup observed

20. RUNTIME DEPENDENCIES
    - FastAPI, SQLAlchemy async, Pydantic, python-jose, numpy
    - No message queue, no cache server, no task runner

Trace representative request paths:
  POST /api/v1/ingest/upload → middleware chain → auth → tenancy → RBAC →
    project validation → content-hash dedup → run_pipeline → audit emit → response

  POST /api/v1/chat/ → middleware → auth → tenancy → RBAC →
    session creation → process_chat → retrieve → LLM → provenance → audit → response

  POST /api/v1/memory/ → middleware → auth → tenancy → require_policy →
    MemoryService.write → authorize → provenance → persist → cache → audit → response

============================================================
AGENT 2 — DATA, MEMORY & PERSISTENCE ARCHITECTURE
============================================================

Analyze the COMPLETE information/data lifecycle.

Output: docs/SWARMVAULT_DATA_MEMORY_ARCHITECTURE.md

1. DATA ENTRY POINTS
   - User registration (creates tenant, workspace, user, membership)
   - Chat messages (user → assistant)
   - Ingestion upload (raw text/JSON/JSONL)
   - API key creation
   - Policy creation
   - Feedback submission
   - Source deletion

2. M0 — NORMALIZATION (connectors.py)
   - NormalizedConversation dataclass
   - NormalizedMessage dataclass
   - Connector interface (detect, validate, parse)
   - Available connectors (verify which are implemented)
   - Size guards (_MAX_CONTENT_LENGTH, _MAX_MESSAGE_LENGTH, _MAX_MESSAGES)
   - Content hashing (SHA-256 → 16-char)
   - External ID generation

3. M1 — SESSION UNDERSTANDING (m1_session.py)
   - Topic extraction
   - Entity mention extraction
   - Intent classification
   - UnderstandSessionResult dataclass

4. M2 — FACT/DECISION EXTRACTION (m2_facts.py)
   - Regex-based extraction (no LLM)
   - Fact patterns (uses, is, supports predicates)
   - Decision patterns (decided/chose/will/selected)
   - Deduplication logic
   - Confidence/authority defaults

5. M3 — TEMPORAL PROCESSING (m3_temporal.py)
   - Supersession logic (same subject+predicate → mark old as historical)
   - Temporal status values: current, historical, expired
   - superseded_by_id linkage
   - Decision supersession
   - Note: pipeline.py also handles M3 inline (verify consistency)

6. M4 — GRAPH CONSTRUCTION (m4_graph.py)
   - GraphNode creation
   - GraphEdge creation
   - Relationship types
   - Source linkage
   - Workspace/project scoping

7. M5 — RETRIEVAL (m5_retrieval.py, retrieval.py)
   - BM25-inspired scoring
   - Exponential recency decay (30-day half-life)
   - Graph context scoring (logarithmic)
   - Hybrid vector+keyword (numpy cosine)
   - Multi-factor ranking
   - Memory.embedding column (JSON floats, no pgvector)

8. MEMORY MODEL (models.py Memory table)
   - Columns: id, tenant_id, workspace_id, user_id, agent_id, run_id,
     project_id, memory_type, content, extra_metadata (JSON),
     embedding (JSON list of floats), temporal_status, confidence,
     authority, deleted_at, created_at, updated_at
   - MemoryRecord canonical dataclass (memory.py)
   - MemoryTypeMapper (canonical ↔ vault type mapping)
   - Memory scopes: WORKING, EPISODIC, SEMANTIC, PROCEDURAL, USER, TEAM, PROJECT, AGENT

9. MEMORY SERVICE (memory.py)
   - MemoryService singleton
   - write() → authorize → provenance → persist → cache
   - read() → authorize → load from DB/cache → cross-tenant check
   - search() → authorize → DB search with ILIKE
   - update() → authorize → load → update → persist
   - delete() → soft delete (deleted_at)
   - In-memory cache as fast-read layer only

10. PROVENANCE (models.py MessageProvenance)
    - Per-chat-response provenance record
    - Fields: model, provider, retrieval_method, memory_ids_used,
      retrieval_sources, prompt_tokens, completion_tokens, latency_ms, confidence
    - Provenance chain in MemoryRecord.provenance list

11. AUDIT (audit/service.py, audit/constants.py)
    - AuditEvent dataclass with 20 canonical fields
    - emit() → accumulates in buffer, writes to sinks
    - persist(session) → flushes buffer to PostgreSQL
    - Sinks: structured log, DB (audit_events table)
    - Sensitive field redaction

12. PERSISTENCE ARCHITECTURE
    - PostgreSQL via SQLAlchemy async
    - All writes use AsyncSession + flush/commit
    - Soft deletion via deleted_at (no hard deletes observed)
    - No migration for audit_events table found — verify
    - Embeddings stored as JSON (not pgvector)

13. SERIALIZATION
    - Pydantic schemas for API (app/schemas.py)
    - JSON for metadata columns
    - ISO-8601 timestamps with timezone

14. RETRIEVAL REPRESENTATION
    - MemoryRecord dataclass (in-memory canonical)
    - Memory model (PostgreSQL)
    - RetrievalResult dataclass (m5_retrieval.py)

For every stage document:
  INPUT → TRANSFORMATION → OUTPUT → VALIDATION → GUARDRAIL →
  FAILURE MODE → PERSISTENCE EFFECT → PROVENANCE EFFECT → MEMORY QUALITY EFFECT

============================================================
AGENT 3 — PIPELINE, GUARDRAIL & VALIDATION ARCHITECTURE
============================================================

Perform a forensic analysis of EVERY stagewise safeguard.

Output: docs/SWARMVAULT_GUARDRAILS_VALIDATION_ARCHITECTURE.md

Build complete matrices:

MATRIX A — REQUEST-LEVEL GUARDRAILS

| Stage | Control | Location | Enforcement | Test | Status |
|-------|---------|----------|-------------|------|--------|
| Request ID | X-Request-ID injection / generation | main.py RequestIdMiddleware | Per-request | Unknown | ACTIVE |
| Security headers | CSP, HSTS, X-Frame-Options, etc. | main.py SecurityHeadersMiddleware | Per-request | Unknown | ACTIVE |
| CORS | allow_origins, credentials, methods | main.py CORSMiddleware | Per-request | Unknown | ACTIVE |
| Rate limit | Per-path sliding window | middleware/rate_limit.py | Per-request | test_rate_limit.py | ACTIVE |
| Auth | JWT decode + user lookup | middleware/tenancy.py get_tenant_context | Per-request | test_auth.py | ACTIVE |
| Tenancy | Workspace membership check | middleware/tenancy.py | Per-request | test_tenancy.py | ACTIVE |
| RBAC | Role hierarchy check | middleware/rbac.py require_min_role | Per-request | test_rbac_security.py | ACTIVE |
| Policy | Policy Engine evaluation | services/policy/ | Per-request | test_policy_engine.py | ACTIVE |

MATRIX B — DATA-LEVEL GUARDRAILS

| Stage | Control | Location | Enforcement | Test | Status |
|-------|---------|----------|-------------|------|--------|
| Schema validation | Pydantic models | app/schemas.py | Per-request | test_ingest.py | ACTIVE |
| Content size | _MAX_CONTENT_LENGTH (10MB) | connectors.py | M0 | test_connector_security.py | ACTIVE |
| Message size | _MAX_MESSAGE_LENGTH (100KB) | connectors.py | M0 | test_connector_security.py | ACTIVE |
| Message count | _MAX_MESSAGES (10,000) | connectors.py | M0 | Unknown | ACTIVE |
| Source-type validation | Connector detect/validate | connectors.py | M0 | test_connectors.py | ACTIVE |
| Deduplication | SHA-256 content hash | ingest.py + models.py | M0 pre-check | test_ingest.py | ACTIVE |
| Content hash storage | Source.content_hash column | models.py | M0 post | Unknown | ACTIVE |
| Temporal supersession | subject+predicate match | pipeline.py + m3_temporal.py | M3 | test_pipeline.py | PARTIAL |
| Confidence bounds | Float column 0.0-1.0 | models.py Fact/Decision/Memory | Schema | Unknown | PARTIAL |
| Authority bounds | Float column 0.0-1.0 | models.py Fact/Decision/Memory | Schema | Unknown | PARTIAL |
| Soft deletion | deleted_at timestamp | All models | All stages | test_sprint4_e2e.py | ACTIVE |
| Cross-tenant isolation | tenant_id check after DB load | memory.py read() | Memory read | Unknown | ACTIVE |
| Error sanitization | _sanitize_detail, _sanitize | main.py, audit/service.py | Error paths | Unknown | ACTIVE |

MATRIX C — MEMORY SAFETY GATES

Document which conditions MUST be satisfied before information becomes
persistent memory:

| Gate | Condition | Enforcement | Location | Status |
|------|-----------|-------------|----------|--------|
| Authentication | Valid JWT token | tenancy.py | All /api/v1/* | ACTIVE |
| Authorization | Policy Engine allow | policy/dependencies.py | Memory routes | ACTIVE |
| Tenancy | Tenant + workspace scope | tenancy.py | All routes | ACTIVE |
| Provenance | Provenance chain attached | memory.py write() | Memory write | ACTIVE |
| Schema | Pydantic validation | schemas.py | All routes | ACTIVE |
| Validation | Connector validate() | connectors.py | M0 | ACTIVE |
| Size guard | Max content/message limits | connectors.py | M0 | ACTIVE |
| Dedup | Content hash check | ingest.py | Pre-M0 | ACTIVE |
| Soft delete filter | deleted_at IS NULL | All queries | All reads | ACTIVE |
| Audit | Audit event emitted | audit/service.py | All ops | ACTIVE |
| Confidence | Float 0.0-1.0 | models.py schema | Persistence | PARTIAL |
| Temporal | temporal_status set | models.py | Persistence | PARTIAL |
| Scope | tenant/workspace/project IDs | memory.py | Memory ops | ACTIVE |
| Persistence | DB session provided | memory.py | Memory write | ACTIVE |

For every guardrail determine:
  ACTIVE / PARTIAL / DOCUMENTED / MISSING / BYPASSABLE / UNTESTED

Pay particular attention to:
  - Can malformed input cross stages?
  - Can adversarial input bypass validation?
  - Are there any unvalidated entry points?
  - Is the error handler itself a vulnerability surface?

============================================================
AGENT 4 — API / CONTRACT / INTEGRATION ARCHITECTURE
============================================================

Analyze the COMPLETE backend API surface.

Output: docs/SWARMVAULT_API_INTEGRATION_ARCHITECTURE.md

1. ROUTE INVENTORY
   For each router, list every endpoint:
     - path, method, auth requirement, RBAC level, policy requirement
     - request schema, response schema
     - success status codes, error status codes
     - pagination, filtering, sorting

2. AUTHENTICATION FLOW
   - POST /api/v1/auth/register → tenant + workspace + user + tokens
   - POST /api/v1/auth/login → access + refresh tokens
   - POST /api/v1/auth/refresh → new access token
   - POST /api/v1/auth/logout → token revocation

3. WORKSPACE/PROJECT FLOW
   - Workspace CRUD, member management, invitations
   - Project CRUD within workspace

4. SESSION FLOW
   - Session CRUD, message listing

5. CHAT FLOW
   - POST /api/v1/chat/ → create session → process → provenance → response
   - SSE streaming endpoint (verify existence)

6. MEMORY FLOW
   - POST /api/v1/memory/ → write with policy check
   - GET /api/v1/memory/{id} → read with cross-tenant check
   - GET /api/v1/memory/ → search with ILIKE
   - PATCH /api/v1/memory/{id} → update
   - DELETE /api/v1/memory/{id} → soft delete

7. INGESTION FLOW
   - POST /api/v1/ingest/upload → dedup → pipeline → source record
   - Content-hash deduplication mechanism

8. SOURCE/FACT/DECISION/GROPH FLOW
   - Source listing, detail, deletion
   - Fact listing with filters
   - Decision listing
   - Graph exploration

9. PROVENANCE FLOW
   - Provenance record access

10. STORAGE FLOW
    - Object storage CRUD (S3/MinIO)

11. API KEY FLOW
    - Key creation with hash storage
    - Key revocation
    - Key prefix display

12. POLICY FLOW
    - Policy CRUD, versioning

13. AUDIT FLOW
    - Audit event querying

14. INTEGRATION CLASSIFICATION

For each integration, verify actual implementation:

| Integration | Status | Evidence | Notes |
|-------------|--------|----------|-------|
| Claude Code | IMPLEMENTED/PARTIAL/... | File/function | Via chat API + LLM provider |
| Codex | IMPLEMENTED/PARTIAL/... | File/function | Via chat API + LLM provider |
| Universal Adapter | IMPLEMENTED/PARTIAL/... | File/function | Connectors.py has UniversalAdapterConnector |
| MCP | IMPLEMENTED/PARTIAL/... | File/function | API keys for MCP server registration |
| REST | IMPLEMENTED | FastAPI routers | All /api/v1/* routes |
| SSE | IMPLEMENTED/PARTIAL/... | File/function | Verify streaming endpoint |
| External LLM providers | IMPLEMENTED | llm.py | Provider abstraction |
| S3 storage | IMPLEMENTED | object_storage_s3.py | S3 backend |
| MinIO storage | IMPLEMENTED | object_storage_minio.py | MinIO backend |

15. ERROR CONTRACTS
    - Standard error format: {"error": {"type": "...", "message": "..."}}
    - Status codes: 200, 201, 400, 401, 403, 404, 422, 500, 503
    - request_id in error responses

============================================================
AGENT 5 — FRONTEND ARCHITECTURE
============================================================

Analyze the frontend (Next.js application).

Output: docs/SWARMVAULT_FRONTEND_ARCHITECTURE.md

1. NEXT.JS ARCHITECTURE
   - App Router vs Pages Router
   - Route structure (app/ directory)
   - Layout hierarchy
   - Server vs Client components

2. COMPONENT ARCHITECTURE
   - UI primitives
   - Page components
   - Feature components
   - Shared components

3. STATE MANAGEMENT
   - No external state library (no Redux/Zustand/etc.)
   - React state, context, URL state
   - Server state (React Server Components)

4. API CLIENT
   - How frontend calls backend
   - Authentication header handling
   - Error handling

5. AUTHENTICATION FLOW
   - Login page → token storage
   - Token refresh
   - Logout
   - Protected routes

6. KNOWLEDGE VIEWS
   - Dashboard
   - Projects list/detail
   - Chat interface
   - Sessions list/detail
   - Memory list/detail/search
   - Facts list
   - Decisions list
   - Timeline view
   - Graph visualization
   - Provenance explorer
   - Ingestion UI
   - Storage browser
   - API keys management
   - Settings
   - Policy management

7. SSE HANDLING
   - Streaming chat responses
   - Error handling for streams

8. SECURITY
   - Token storage (localStorage? cookies?)
   - XSS prevention
   - CSRF handling
   - CORS interaction

9. RESPONSIVE ARCHITECTURE
   - Breakpoints
   - Mobile adaptations

10. FRONTEND/BACKEND CONTRACT MATRIX

For each important screen:
  Screen → Component → State → API Endpoint → Backend Router →
  Service → Database Model → Response → UI Rendering

11. FRONTEND/BACKEND MISMATCHES
    Identify any mismatches between what the frontend expects
    and what the backend actually provides.

============================================================
AGENT 6 — SECURITY, TENANCY & OPERATIONAL ARCHITECTURE
============================================================

Analyze security and operational boundaries.

Output: docs/SWARMVAULT_SECURITY_OPERATIONAL_ARCHITECTURE.md

1. AUTHENTICATION DEEP DIVE
   - JWT algorithm (HS256 via python-jose)
   - Token expiry (access + refresh)
   - Refresh token rotation (verify if implemented)
   - Password hashing (passlib context)
   - Secret key configuration

2. AUTHORIZATION DEEP DIVE
   - RBAC role hierarchy
   - Permission matrix
   - Policy Engine rules
   - Fail-closed behavior
   - Deny-overrides-allow

3. TENANCY ISOLATION
   - Tenant → Workspace → Project hierarchy
   - TenantContext propagation
   - Cross-tenant access prevention
   - Workspace membership enforcement
   - Project scoping within workspace

4. SECURITY HEADERS
   - Production vs dev CSP differences
   - HSTS (production only)
   - X-Frame-Options, X-Content-Type-Options, etc.

5. CORS
   - Allowed origins (settings.cors_origins_safe)
   - Credentials allowed
   - Methods and headers

6. ERROR SANITIZATION
   - _sanitize_detail in main.py
   - _sanitize in audit/service.py
   - What leaks in production vs debug

7. AUDIT & PROVENANCE
   - What is audited (complete event list from constants.py)
   - Audit persistence model (emit → buffer → persist per request)
   - Provenance tracking per chat response
   - Audit event schema

8. DATABASE SECURITY
   - Connection handling
   - No SQL injection vectors observed (SQLAlchemy parameterized)
   - Soft deletion vs hard deletion

9. SECRET HANDLING
   - API key hashing (SHA-256, key_prefix for display)
   - Refresh token storage
   - JWT secret key

10. RATE LIMITING
    - In-memory implementation (not distributed-safe)
    - Per-path rules
    - Test bypass mechanism

11. DEPLOYMENT SECURITY
    - Docker configuration
    - Environment variable handling
    - Production flag effects (Swagger disabled, stricter CSP)

12. OPERATIONAL
    - Health checks (live/ready/legacy)
    - Logging configuration
    - No metrics/observability beyond request latency
    - No backup/restore documentation found
    - Migration management (Alembic)

For every control document:
  CONTROL | LOCATION | ENFORCEMENT POINT | TEST | FAILURE BEHAVIOR | BYPASS RISK

============================================================
AGENT 7 — MEMORY INTELLIGENCE READINESS ARCHITECTURE
============================================================

THIS IS THE MOST IMPORTANT SPECIALIST.

Determine how ready the current SwarmVault data architecture is for:
  A. persistent memory
  B. long-term memory
  C. memory intelligence
  D. reasoning over memory
  E. future autonomous memory operations

Do NOT redesign the memory layer. Analyze what exists.

Output: docs/SWARMVAULT_MEMORY_INTELLIGENCE_READINESS.md

1. CURRENT MEMORY IMPLEMENTATION
   - Memory model columns and their semantics
   - MemoryRecord canonical model
   - MemoryTypeMapper type system
   - Memory scopes (WORKING/EPISODIC/SEMANTIC/PROCEDURAL/USER/TEAM/PROJECT/AGENT)
   - MemoryService CRUD operations
   - In-memory cache vs PostgreSQL

2. PROVENANCE CHAIN
   - MemoryRecord.provenance list
   - MessageProvenance per chat response
   - Audit event chain
   - Source linkage (source_id on Fact/Decision)

3. CONFIDENCE & AUTHORITY
   - Confidence column (0.0-1.0)
   - Authority column (0.0-1.0)
   - How set during extraction (M2 defaults)
   - How used during retrieval (M5)

4. TEMPORAL SEMANTICS
   - temporal_status: current/historical
   - created_at, updated_at timestamps
   - superseded_by_id linkage
   - valid_from/valid_until in MemoryRecord (not in DB model?)

5. GRAPH RELATIONSHIPS
   - GraphNode/GraphEdge models
   - Relationship types
   - Source linkage
   - Workspace/project scoping
   - Temporal status on graph elements

6. SCOPE & ISOLATION
   - Tenant → Workspace → Project → User
   - Memory.tenant_id column (added in migration 011)
   - Cross-tenant isolation in MemoryService.read()

7. LIFECYCLE
   - Creation (pipeline, direct write)
   - Update (MemoryService.update)
   - Deletion (soft delete via deleted_at)
   - Supersession (M3 temporal)

8. RETRIEVAL EXPLAINABILITY
   - M5 multi-factor scoring
   - RetrievalResult with factor breakdown
   - Provenance tracking of what was used

9. MEMORY READINESS SCORECARD

Create a detailed scorecard:

| Capability | Current State | Evidence | Ready? | Gap |
|------------|---------------|----------|--------|-----|
| Identity | UUID primary keys | models.py | YES | — |
| Source | Source linkage, content_hash | Source model | YES | — |
| Time | created_at, updated_at | All models | YES | — |
| Context | workspace_id, project_id, metadata | Memory model | YES | — |
| Confidence | Float column | Memory/Fact/Decision | PARTIAL | M2 uses static defaults |
| Authority | Float column | Memory/Fact/Decision | PARTIAL | M2 uses static defaults |
| Provenance | Provenance list, MessageProvenance | memory.py, models.py | YES | — |
| Relationships | GraphNode/GraphEdge | models.py | YES | — |
| Supersession | superseded_by_id, temporal_status | models.py, m3_temporal.py | PARTIAL | Only for Facts, not Memories |
| Contradiction | temporal_status flip | m3_temporal.py | PARTIAL | Subject+predicate only |
| Scope | tenant/workspace/project | Memory model | YES | — |
| Lifecycle | created/updated/deleted | All models | YES | — |
| Retrieval | Hybrid + M5 scoring | retrieval.py, m5_retrieval.py | PARTIAL | No pgvector, no BM25 index |
| Auditability | AuditService + events | audit/service.py | YES | — |
| Embeddings | JSON float arrays | Memory.embedding | PARTIAL | No pgvector, no index |

10. PERSISTENT MEMORY READINESS
    What is ready for persistent memory TODAY:
      - UUID identity ✓
      - Source provenance ✓
      - Temporal timestamps ✓
      - Scope isolation ✓
      - Soft deletion ✓
      - Audit trail ✓
      - Confidence/authority fields ✓

    What is NOT ready:
      - No memory consolidation/forgetting
      - No importance decay
      - No memory type lifecycle (working → long-term)
      - No contradiction detection beyond subject+predicate
      - No memory quality scoring
      - No automated supersession for Memory records (only Fact/Decision)

11. MEMORY INTELLIGENCE READINESS
    What a future intelligence layer CAN safely consume:
      - All persistent records with identity, time, scope
      - Provenance chains
      - Graph relationships
      - Temporal status
      - Confidence/authority scores (even if static)

    What it should NOT assume:
      - Confidence scores reflect actual extraction quality (they're defaults)
      - Authority reflects source reliability (not computed)
      - Temporal status is always accurate (M3 only handles Facts)
      - Graph is complete (only M4 entities, not all concepts)
      - Embeddings are semantically meaningful (no pgvector, no index)
      - Retrieval ranking is optimal (BM25 without IDF, no index)

12. NEXT MEMORY INTELLIGENCE LAYER — BOUNDARY

Define the boundary:
  CAN TRUST:
    - Record identity and persistence guarantees
    - Temporal ordering
    - Scope isolation
    - Provenance chains (when present)
    - Graph structure (when present)
    - Soft deletion semantics

  CANNOT TRUST YET:
    - Confidence/authority as quality signals (static defaults)
    - Temporal truth (only Facts have supersession)
    - Retrieval quality (no BM25 index, no pgvector)
    - Memory consolidation (no working→long-term promotion)
    - Contradiction detection (limited to subject+predicate)
    - Memory importance/decay (no model)
    - Cross-memory reasoning (no explicit relationship types)

============================================================
FINAL SYNTHESIS AGENT
============================================================

After all seven specialist documents are complete, launch a final
Architecture Synthesis Agent that:

1. Reads all seven specialist documents
2. Reads existing architecture documentation (if any)
3. Reads backend source files
4. Reads frontend source files
5. Reads all database migrations
6. Reads all tests
7. Reads API contract documentation
8. Reads memory implementation
9. Reads ingestion implementation
10. Reads deployment configuration

It must reconcile contradictions against source code.
It must NOT blindly merge specialist claims.

Produce 7 final documents:

FINAL DOCUMENT 1 — MASTER ARCHITECTURE
  docs/SWARMVAULT_WEBAPP_MASTER_ARCHITECTURE.md

  Required sections:
  1. Executive Summary
  2. Product Boundary
  3. System Context
  4. Architectural Principles
  5. High-Level Architecture
  6. Backend Architecture (FastAPI, services, models)
  7. Frontend Architecture (Next.js, components, routing)
  8. API Architecture (routes, schemas, contracts)
  9. Data Architecture (models, relationships, constraints)
  10. Memory Architecture (MemoryRecord, types, scopes, service)
  11. Storage Architecture (PostgreSQL, object storage)
  12. Security Architecture (auth, RBAC, policy engine, headers)
  13. Tenancy Architecture (tenant → workspace → project)
  14. Pipeline Architecture (M0-M5 stages)
  15. M0–M5 Architecture (each stage detail)
  16. Guardrail Architecture (per-stage controls)
  17. Validation Architecture (schema, size, content, semantic)
  18. Provenance Architecture (per-response, per-memory, audit)
  19. Audit Architecture (events, sinks, persistence)
  20. Retrieval Architecture (hybrid, multi-factor, ranking)
  21. SSE/Streaming Architecture
  22. Ingestion Architecture (connectors, dedup, pipeline)
  23. Integration Architecture (LLM, storage, external)
  24. Deployment Architecture (Docker, env, health)
  25. Failure & Recovery Architecture
  26. Observability Architecture (logging, request IDs, latency)
  27. Test Architecture (unit tests, e2e tests, fixtures)
  28. Current Limitations
  29. Technical Debt
  30. Future Memory Intelligence Boundary
  31. Architectural Readiness Assessment

FINAL DOCUMENT 2 — END-TO-END FLOWS
  docs/SWARMVAULT_END_TO_END_FLOWS.md

  Document actual flows with exact file/function citations:
  FLOW-001 User Registration
  FLOW-002 Login
  FLOW-003 Workspace Creation
  FLOW-004 Project Creation
  FLOW-005 Session Ingestion
  FLOW-006 JSON Ingestion
  FLOW-007 JSONL Ingestion
  FLOW-008 M0 Normalization
  FLOW-009 M1 Session Understanding
  FLOW-010 M2 Fact/Decision Extraction
  FLOW-011 M3 Temporal Processing
  FLOW-012 M4 Graph Construction
  FLOW-013 M5 Retrieval
  FLOW-014 Persistent Memory Creation
  FLOW-015 Memory Retrieval
  FLOW-016 Search
  FLOW-017 Chat
  FLOW-018 SSE Chat Streaming
  FLOW-019 Provenance
  FLOW-020 Graph Exploration
  FLOW-021 Memory Deletion
  FLOW-022 Supersession
  FLOW-023 Audit
  FLOW-024 API Key Creation
  FLOW-025 External Agent Integration

  For each:
    Trigger → Input → Validation → Guardrails → Processing →
    Persistence → Output → Failure behavior → Security boundary

FINAL DOCUMENT 3 — GUARDRAIL MASTER MATRIX
  docs/SWARMVAULT_GUARDRAIL_MASTER_MATRIX.md

  Complete matrix of every guardrail:
    stage, control, implementation, enforcement point,
    validation, test, failure mode, bypass possibility,
    severity, current status

  Include MEMORY SAFETY GATE MATRIX

FINAL DOCUMENT 4 — PERSISTENT MEMORY READINESS
  docs/SWARMVAULT_PERSISTENT_MEMORY_READINESS.md

  For each data capability:
    1. What data is currently persistent?
    2. What data is ephemeral?
    3. What data is normalized?
    4. What data has provenance?
    5. What data has temporal semantics?
    6. What data has confidence?
    7. What data has authority?
    8. What data has identity?
    9. What data has scope?
    10. What data can be superseded?
    11. What data can be contradicted?
    12. What data can be deleted?
    13. What data can be retrieved?
    14. What data can be explained?
    15. What data is safe for future memory intelligence?

  Classify each: GREEN = ready / YELLOW = partially ready / RED = not ready

FINAL DOCUMENT 5 — FRONTEND/BACKEND ARCHITECTURE
  docs/SWARMVAULT_FRONTEND_BACKEND_ARCHITECTURE.md

  For every important frontend screen:
    Screen → Component → State → API → Backend Router → Service →
    Database → Response → UI Rendering

  Include all views: auth, dashboard, projects, chat, sessions,
  memory, facts, decisions, timeline, search, graph, provenance,
  ingestion, storage, API keys, settings

  Include frontend/backend mismatches.

FINAL DOCUMENT 6 — ARCHITECTURAL TRACEABILITY MATRIX
  docs/SWARMVAULT_ARCHITECTURAL_TRACEABILITY.md

  Trace:
    REQUIREMENT → FEATURE → FRENDEND → API → SERVICE →
    DATA MODEL → PIPELINE → GUARDRAIL → TEST → PERSISTENCE → PROVENANCE

  Every important capability must have an evidence trail.

FINAL DOCUMENT 7 — ARCHITECTURAL GAPS & NEXT MEMORY LAYER
  docs/SWARMVAULT_ARCHITECTURAL_GAPS_AND_MEMORY_NEXT_LAYER.md

  Separate findings into P0/P1/P2/P3.

  For each gap:
    CURRENT STATE → RISK → EVIDENCE → IMPACT →
    REQUIRED CONDITION →
    BLOCKS PERSISTENT MEMORY? (YES/NO/PARTIAL) →
    BLOCKS MEMORY INTELLIGENCE? (YES/NO/PARTIAL)

  Then provide:
    "NEXT MEMORY INTELLIGENCE LAYER — READINESS BOUNDARY"

    This is NOT an implementation plan. It is a boundary definition:
    - WHAT THE CURRENT SYSTEM CAN SAFELY PROVIDE
    - WHAT THE NEXT LAYER CAN TRUST
    - WHAT THE NEXT LAYER MUST NOT ASSUME
    - WHAT CONTRACTS MUST EXIST BEFORE IMPLEMENTATION

============================================================
DOCUMENT FORMAT REQUIREMENTS
============================================================

Every document must:
  1. Start with a metadata header (document name, version, date, author)
  2. Include a table of contents
  3. Use consistent heading hierarchy (##, ###, ####)
  4. Include exact file paths and line numbers for all claims
  5. Use code blocks for exact code citations
  6. Use tables for matrices
  7. Include a "Findings" section with numbered issues
  8. Include a "Recommendations" section (documentation only)
  9. Include a "Verification" section with test file references
  10. End with an "Open Questions" section for unknowns

Classification key for every capability:
  [IMPLEMENTED] / [PARTIAL] / [UNVERIFIED] / [DOCUMENTED] /
  [PLANNED] / [MISSING] / [BLOCKED] / [DEPRECATED] / [UNKNOWN]

====================================================================
BEGIN FORENSIC ANALYSIS
====================================================================

Start with Phase 0 (baseline), then launch all 7 specialist agents in parallel,
then launch the final synthesis agent.

Do not proceed to synthesis until all 7 specialist documents exist.
"""
