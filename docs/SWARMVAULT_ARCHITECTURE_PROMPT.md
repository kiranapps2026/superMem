# SwarmVault WebApp — Enterprise Architecture Forensic Analysis Prompt (v2)

## ROLE

You are the Principal Enterprise Architect for the SwarmVault WebApp.

Your mission is NOT to modify or redesign the product.

Your mission is to perform a repository-first architectural forensic analysis and produce an authoritative architecture documentation package explaining:

1. Complete backend architecture and runtime logic (file-level, line-level)
2. Stage-by-stage guardrails with enforcement point analysis
3. Validation and safety mechanisms (concrete, not generic)
4. Memory/data pipelines (M0-M5 with explicit contracts)
5. End-to-end system flows (traceable from HTTP request to DB row)
6. Persistence architecture (tables, indexes, constraints, migrations)
7. Provenance and auditability (append-only, never-update invariants)
8. Frontend architecture (page-level, component-level)
9. Backend-to-frontend contracts (request/response, SSE events, error shapes)
10. Current memory readiness (what exists today, verifiable)
11. Persistent-memory readiness (what is safe to persist, verifiable)
12. Readiness for the NEXT Memory Intelligence Layer (boundary definition)
13. Architectural gaps, inconsistencies, risks and technical debt (risk-classified)

============================================================
ABSOLUTE RULES (NON-NEGOTIABLE)
============================================================

RULE 1 — REPOSITORY IS THE PRIMARY SOURCE OF TRUTH

Inspect the actual repository files. Do NOT infer architecture from filenames alone.

For every important architectural claim, you MUST provide an evidence citation in this exact format:

  EVIDENCE: `app/main.py` line 142 — `api_v1.include_router(chat.router)`

If you cannot produce a file:line citation, the claim does not exist.

Documentation may support understanding but must NOT override executable implementation without explicitly identifying the discrepancy with a `[DISCREPANCY]` tag.

------------------------------------------------------------

RULE 2 — DO NOT MODIFY PRODUCT CODE

This is an architecture/documentation forensic phase.

Allowed: writing `.md` files to `docs/` only.
Prohibited: any modification to files outside `docs/`.

If something is wrong, document it as a finding with severity.

------------------------------------------------------------

RULE 3 — DO NOT INVENT FEATURES

Every capability must be classified as exactly one of:

  IMPLEMENTED           — verified in source code with file:line evidence
  PARTIALLY_IMPL        — some elements exist, some do not
  IMPLEMENTED_UNVERIFIED — code exists but behavior is not exercised by tests
  DOCUMENTED_ONLY       — mentioned in docs/ but not in product code
  PLANNED               — referenced as future work
  MISSING               — required but absent from both code and docs
  BLOCKED               — exists but cannot function due to a dependency gap
  DEPRECATED            — exists but marked for removal
  UNKNOWN               — insufficient evidence to classify

Every classification must have an EVIDENCE citation. Never describe planned functionality as implemented.

------------------------------------------------------------

RULE 4 — FILE:LINE EVIDENCE FORMAT

Every architectural claim must cite evidence using this exact format:

  EVIDENCE: `<relative-path>` line `<N>` — `<relevant code snippet or description>`

Examples:

  EVIDENCE: `app/models.py` line 232 — `class Memory(Base): __tablename__ = "memories"`
  EVIDENCE: `app/main.py` line 192 — `app.add_middleware(AuditPersistenceMiddleware)`
  EVIDENCE: `app/api/chat.py` line 109 — `@router.post("/stream")` → SSE StreamingResponse

For multi-line evidence spans, use:

  EVIDENCE: `app/models.py` lines 232–266 — `class Memory(Base)` definition including all columns

If you find two conflicting implementations, cite both and label the conflict:

  CONFLICT: `app/main.py` line 18 vs line 17 — `AuditService` imported twice (duplicate import)

------------------------------------------------------------

RULE 5 — DATA TRACEABILITY FROM ENTRY TO PERSISTENCE

For every data type (Memory, Fact, Decision, GraphNode, GraphEdge, Source, NormalizedMessage, AuditEvent, Provenance), trace the complete path:

  ENTRY POINT          → which router, which function, which line
  VALIDATION           → which Pydantic schema, which field validators, which lines
  AUTH CHECK           → which middleware/dependency, which line
  AUTHORIZATION        → which RBAC/policy check, which line
  SERVICE LAYER        → which service function, which lines
  PIPELINE STAGE       → M0-M5 stage, which function, which lines
  PERSISTENCE          → which ORM model, which columns, which lines
  RETRIEVAL PATH       → which query, which filters, which lines
  API RESPONSE         → which schema, which serializer, which lines
  FRONTEND RECEIPT     → which component, which state handler, which lines
  PROVENANCE ATTACHED  → yes/no, which mechanism, which lines

This is the mandatory deliverable for AGENT 2.

============================================================
PHASE 0 — SOURCE CONTROL BASELINE
============================================================

Step 0.1: Run these commands and record exact output:

  git rev-parse --abbrev-ref HEAD          # current branch
  git rev-parse HEAD                       # exact SHA
  git status --short                       # working tree state
  git log --oneline -5                     # recent history

Step 0.2: Map the repository structure:

  Backend root:        `app/`
  Frontend root:       `frontend/`
  Tests:               search for `test_*.py`, `*_test.py`, `*.spec.ts`
  Migrations:          search for `alembic/`, `migrations/`, `*_migration*.sql`
  Docker:              search for `Dockerfile`, `docker-compose*`, `.dockerignore`
  Env config:          search for `.env`, `.env.example`, `config.py`, `settings.py`
  Existing docs:       `docs/` directory listing

Step 0.3: Create baseline document:

  FILE: `docs/ARCHITECTURE_FORENSICS_BASELINE.md`

  Required sections:
  - Repository identity (remote URL, branch, HEAD SHA, timestamp)
  - Working tree state (M, A, ?? files with descriptions)
  - Backend structure tree (directories with file counts)
  - Frontend structure tree (directories with file counts)
  - Test inventory (file paths and approximate test count)
  - Migration inventory (file paths)
  - Deployment configuration inventory (file paths)
  - Existing documentation inventory (file paths)

If the baseline cannot be established (e.g., not a git repo), STOP and report the blocker.

============================================================
PARALLEL AGENT PROGRAM
============================================================

Launch 7 specialist agents IN PARALLEL. Each writes to its own file.

NO specialist may read another specialist's output file during analysis.
The final synthesis agent reads all 7 and reconciles.

Each specialist agent must follow this procedure:
  1. Read all relevant source files (do NOT skip any)
  2. Build an internal evidence table with file:line citations
  3. Classify every capability (IMPLEMENTED, PARTIALLY_IMPL, etc.)
  4. Identify gaps with severity ratings
  5. Write ONLY to its assigned output file
  6. Do NOT modify any file outside docs/

============================================================
AGENT 1 — BACKEND RUNTIME ARCHITECTURE
============================================================

TARGET: `app/` directory

MANDATORY FILE READS (do not skip any):
  app/main.py                    (complete — application construction, middleware stack)
  app/core/config.py             (complete — settings, environment)
  app/db.py                      (complete — engine, session factory, init_db)
  app/api/auth.py                (complete — authentication router)
  app/api/workspace.py           (complete)
  app/api/projects.py            (complete)
  app/api/sessions.py            (complete)
  app/api/chat.py                (complete)
  app/api/memory.py              (complete)
  app/api/ingest.py              (complete)
  app/api/provenance.py          (complete)
  app/api/dashboard.py           (complete)
  app/api/feedback.py            (complete)
  app/api/api_keys.py            (complete)
  app/api/storage.py             (complete)
  app/api/policy.py              (complete)
  app/api/audit.py               (complete)
  app/middleware/tenancy.py      (complete — TenantContext)
  app/middleware/rbac.py         (complete — RBAC)
  app/middleware/auth.py         (complete — JWT)
  app/middleware/rate_limit.py   (complete — RateLimitMiddleware)
  app/services/memory.py         (complete)
  app/services/pipeline.py       (complete)
  app/services/chat_orchestrator.py (complete)
  app/services/llm.py            (complete)
  app/services/policy/engine.py  (complete)
  app/services/policy/dependencies.py (complete)
  app/services/audit/service.py  (complete)
  app/services/audit/repository.py (complete)

SPECIFIC REQUIREMENTS:

1. APPLICATION STARTUP (main.py)
   - Document the `@asynccontextmanager` lifespan function with exact line numbers
   - Document every `app.add_middleware()` call in registration order (outermost to innermost)
   - Document every `api_v1.include_router()` call with exact route prefixes
   - Document `settings` conditions that toggle behavior (e.g., `settings.is_production` at line 58)

2. MIDDLEWARE STACK (execution order)
   Trace the exact order a request passes through:
   a. SecurityHeadersMiddleware   (main.py line 186)
   b. RequestIdMiddleware          (main.py line 189)
   c. AuditPersistenceMiddleware   (main.py line 212)
   d. CORSMiddleware               (main.py line 216)
   e. RateLimitMiddleware          (main.py line 226)
   f. Router-level dependencies    (tenancy, rbac, policy)
   Document what each middleware does, what it adds to request.state, and what it can short-circuit.

3. ROUTER INVENTORY
   For each router file, document:
   - Router prefix (e.g., `APIRouter(prefix="/memory")`)
   - Every endpoint with method, path, response_model, status_code
   - Every Depends() chain (tenancy → rbac → policy → service)
   - Every HTTPException raised and under what conditions

4. SERVICE LAYER
   For each service file, document:
   - Class name and __init__ signature
   - Every public method with exact signature
   - Dependencies injected (e.g., AuditService)
   - Database access patterns (raw SQL vs ORM)
   - Error handling strategy

5. DEPENDENCY INJECTION PATTERN
   Document the exact pattern used:
   - `Annotated[TenantContext, Depends(get_tenant_context)]`
   - `ms: MemoryService = Depends(get_memory_service)` (singleton pattern)
   - `_: None = Depends(require_min_role("owner"))` (RBAC as dependency)
   - `_: None = Depends(require_policy("memory", "write"))` (policy engine as dependency)

6. AUTHENTICATION & AUTHORIZATION CHAIN
   Trace the complete chain for a protected endpoint:
   JWT decode → TenantContext extraction → RBAC role check → Policy engine evaluation → Service execution

7. TENANCY MODEL
   Document the Tenant → Workspace → Project hierarchy with exact foreign keys from models.py:
   - Memory: tenant_id (line 238), workspace_id (line 241)
   - Fact: workspace_id (line 422) — NOTE: no tenant_id column
   - Decision: workspace_id (line 475) — NOTE: no tenant_id column
   - GraphNode: workspace_id (line 529) — NOTE: no tenant_id column
   - GraphEdge: workspace_id (line 570) — NOTE: no tenant_id column
   Identify which models have tenant_id and which rely on workspace_id lookup only.

8. DATABASE ACCESS
   Document:
   - Engine type (asyncpg via SQLAlchemy async)
   - Session management pattern (get_db dependency)
   - Transaction boundaries (where commit/rollback occur)
   - The singleton pattern for services that creates their own AuditService

9. ERROR HANDLING
   Document:
   - The 3 exception handlers in main.py (lines 230, 235, 242)
   - The _sanitize_detail function (line 112) and what it redacts
   - The rollback pattern in chat.py (line 76)

10. OBSERVABILITY
    Document:
    - StructuredFormatter (line 87) — JSON log format
    - RequestIdMiddleware latency measurement (line 34)
    - AuditEvent model fields that enable tracing (request_id, correlation_id)

OUTPUT FILE: `docs/SWARMVAULT_BACKEND_ARCHITECTURE.md`

Required sections (use these exact headings):
  1. Application Startup & Lifespan
  2. Middleware Stack (ordered execution)
  3. Router Inventory (table: prefix, file, endpoints)
  4. Service Layer Inventory (table: service, file, methods)
  5. Dependency Injection Map
  6. Authentication & Authorization Chain
  7. Tenancy & Multi-Tenancy Architecture
  8. Database Access Architecture
  9. Error Handling & Sanitization
  10. Observability & Logging
  11. Health & Readiness Endpoints
  12. Runtime Dependencies
  13. Identified Gaps (table: gap, severity, evidence, impact)

============================================================
AGENT 2 — DATA, MEMORY & PERSISTENCE ARCHITECTURE
============================================================

TARGET: `app/models.py`, `app/schemas.py`, `app/services/pipeline.py`, `app/services/memory.py`, `app/services/m1_session.py`, `app/services/m2_facts.py`, `app/services/m3_temporal.py`, `app/services/m4_graph.py`, `app/services/m5_retrieval.py`

MANDATORY FILE READS:
  app/models.py                   (complete — all ORM models)
  app/schemas.py                  (complete — all Pydantic schemas)
  app/services/pipeline.py        (complete — M0 orchestration)
  app/services/m1_session.py      (complete — M1)
  app/services/m2_facts.py        (complete — M2)
  app/services/m3_temporal.py     (complete — M3)
  app/services/m4_graph.py        (complete — M4)
  app/services/m5_retrieval.py    (complete — M5)
  app/services/retrieval.py       (complete — retrieval orchestrator)
  app/services/memory.py          (complete — MemoryService)

SPECIFIC REQUIREMENTS:

1. MODEL INVENTORY (models.py)
   For each ORM model, document:
   - Class name, __tablename__, primary key type (UUID string, line number)
   - Every column: name, SQL type, nullable, default, index, unique constraint
   - Every relationship: target model, back_populates, cascade rules
   - Every __table_args__: Index, UniqueConstraint with column list

   Special attention:
   - Memory.embedding column (line 253) — JSON array of floats, nullable
   - Memory.temporal_status default "current" (line 254), indexed
   - Source.content_hash SHA-256 (line 319), indexed for dedup
   - Source.deleted_at (line 347) — soft delete for ingestion sources
   - NormalizedMessage unique constraints (lines 405-411)
   - AuditEvent model (lines 786-835) — all indexed columns, the append-only invariant

2. SCHEMA INVENTORY (schemas.py)
   For each Pydantic schema, document:
   - Class name, base class, Config.from_attributes setting
   - Every field with type, Field() constraints (min_length, max_length, ge, le, pattern, default)
   - Every @field_validator with validation logic

   Special attention:
   - MemoryCreate.content validators (lines 196-208): no null bytes, no whitespace-only
   - ChatRequest.message max_length=50_000 (line 168)
   - IngestUploadRequest.source_type pattern (line 380): ^(text|json|jsonl|chatgpt)$
   - MemoryCreate.memory_type default="procedural_memory" (line 190)

3. M0 PIPELINE ENTRY (pipeline.py)
   Document the run_pipeline function signature and flow:
   - How raw_content becomes a Source record
   - How source_type determines parser selection
   - How NormalizedMessage records are created
   - The M0→M1 handoff (what data passes between stages)

4. M1 SESSION UNDERSTANDING (m1_session.py)
   Document:
   - Input: NormalizedMessage list
   - Output: session_id assignment, title extraction
   - The role classification logic (user/assistant/system detection)

5. M2 FACT/EXTRACTION (m2_facts.py)
   Document:
   - Input: NormalizedMessage list with session context
   - Output: Fact and Decision records
   - The extraction mechanism (LLM-based? rule-based?)
   - Confidence and authority assignment
   - The subject-predicate-object triple structure for Facts

6. M3 TEMPORAL PROCESSING (m3_temporal.py)
   Document:
   - temporal_status values: "current", "historical", "superseded"
   - How temporal_status is assigned
   - Supersession logic (superseded_by_id chain)

7. M4 GRAPH CONSTRUCTION (m4_graph.py)
   Document:
   - How GraphNode and GraphEdge are created from extracted facts
   - Node types: "entity" (default)
   - Relationship types extracted
   - Confidence propagation to edges
   - The external_id mechanism for dedup

8. M5 RETRIEVAL (m5_retrieval.py, retrieval.py)
   Document:
   - retrieve_hybrid function signature and scoring
   - The multi-factor retrieval strategy
   - retrieve_memories function (used by chat.py)
   - How temporal_status affects retrieval

9. DATA LINEAGE TABLE
   Create a complete lineage table with these columns:

   | Stage | Input Contract | Output Contract | Validation | Guardrail | Persistence | Provenance | Failure Mode |
   |-------|---------------|----------------|------------|-----------|-------------|------------|--------------|

   For each stage M0-M5:
   - What triggers it (API endpoint)
   - What input it receives (exact data structure)
   - What validation occurs
   - What output it produces (exact ORM models created)
   - What happens on failure (rollback, partial write, etc.)

10. SOFT DELETE & SUPERSESSION
    Document:
    - Which models have deleted_at (Memory, Session, Source, Fact, Decision, GraphNode, GraphEdge, User, Workspace)
    - Which models have superseded_by_id (Fact, Decision)
    - The .deleted_at.is_(None) filter pattern used in queries
    - The cascade="all, delete-orphan" relationships

11. DEDUPLICATION
    Document:
    - Source.content_hash dedup (ingest.py line 62)
    - NormalizedMessage unique constraints (source_id + message_index, source_id + external_id)
    - GraphNode unique constraint (workspace_id + external_id)

12. INDEX INVENTORY
    List every Index and UniqueConstraint from models.py with:
    - Index name
    - Columns
    - Model
    - Purpose (e.g., tenant isolation, temporal filtering, dedup)

OUTPUT FILE: `docs/SWARMVAULT_DATA_MEMORY_ARCHITECTURE.md`

Required sections:
  1. ORM Model Inventory (table for each model)
  2. Pydantic Schema Inventory (table for each schema)
  3. M0–M5 Pipeline Detail (per-stage analysis)
  4. Data Lineage Matrix
  5. Soft Delete & Supersession Architecture
  6. Deduplication Architecture
  7. Index & Constraint Inventory
  8. Embedding Architecture (Memory.embedding column)
  9. Identified Gaps (table: gap, severity, evidence, impact)

============================================================
AGENT 3 — PIPELINE, GUARDRAIL & VALIDATION ARCHITECTURE
============================================================

TARGET: All middleware, all router dependencies, all schema validators, all service-level checks

MANDATORY FILE READS:
  app/main.py                    (middleware stack, error handlers)
  app/middleware/tenancy.py      (TenantContext, get_tenant_context)
  app/middleware/rbac.py         (require_min_role, role checks)
  app/middleware/auth.py         (JWT decode, token validation)
  app/middleware/rate_limit.py   (RateLimitMiddleware)
  app/services/policy/engine.py  (policy evaluation)
  app/services/policy/dependencies.py (require_policy)
  app/services/policy/repository.py (policy persistence)
  app/schemas.py                 (all Pydantic validators)
  app/api/auth.py                (authentication endpoints)
  app/api/chat.py                (chat endpoints)
  app/api/memory.py              (memory endpoints)
  app/api/ingest.py              (ingestion endpoints)

SPECIFIC REQUIREMENTS:

1. GUARDRAIL INVENTORY TABLE
   Build a table with these exact columns:

   | # | Guardrail | Type | Location (file:line) | Active | Bypassable | Test Coverage | Severity |
   |---|-----------|------|---------------------|--------|-----------|---------------|----------|

   Guardrail Types:
   - AUTH: authentication required
   - RBAC: role-based access control
   - POLICY: policy engine evaluation
   - TENANCY: tenant isolation enforcement
   - SCHEMA: Pydantic validation
   - RATE: rate limiting
   - SECURITY: security headers, CORS
   - SANITIZATION: error detail redaction
   - SIZE: content length limits
   - DEDUP: content hash deduplication
   - SOFT_DELETE: deleted_at filtering

   For each guardrail, document:
   - The exact file and line where it is enforced
   - Whether it can be bypassed (e.g., by calling a different endpoint)
   - Whether tests exist for it

2. VALIDATION CHAIN PER ENDPOINT
   For each API endpoint, trace the complete validation chain:

   Example format:
   ```
   POST /api/v1/memory/
     [1] RateLimitMiddleware        — app/main.py line 226
     [2] SecurityHeadersMiddleware   — app/main.py line 186
     [3] RequestIdMiddleware         — app/main.py line 189
     [4] AuditPersistenceMiddleware  — app/main.py line 212
     [5] CORSMiddleware              — app/main.py line 216
     [6] get_tenant_context()        — app/middleware/tenancy.py line X
     [7] require_policy("memory", "write") — app/services/policy/dependencies.py line X
     [8] MemoryCreate schema         — app/schemas.py line 188 (content: min_length=1, max_length=1_000_000)
     [9] MemoryCreate.no_null_bytes  — app/schemas.py line 196
     [10] MemoryCreate.strip_whitespace_only — app/schemas.py line 203
     [11] MemoryService.write()      — app/services/memory.py line X
   ```

3. FAILURE MODE ANALYSIS
   For each pipeline stage, document:
   - What happens if input is malformed
   - What happens if the LLM provider fails
   - What happens if the database is unavailable
   - What happens if audit persistence fails (note: it never blocks the response per main.py line 202)

4. CROSS-STAGE INJECTION ANALYSIS
   Analyze whether malformed or adversarial input can cross stages:
   - Can a crafted JSON payload bypass M0 normalization?
   - Can a large content payload cause OOM in M2 extraction?
   - Can a missing session_id break M1→M2 handoff?
   - Can a tenant_id mismatch bypass tenancy isolation?

5. POLICY ENGINE ANALYSIS
   Document:
   - Policy model (app/models.py line 725) — tenant-scoped, versioned
   - PolicyVersion model (app/models.py line 762) — versioned rule sets
   - require_policy dependency (app/services/policy/dependencies.py)
   - The fail-closed behavior (does policy failure deny or allow?)
   - Policy evaluation order

6. RATE LIMITING ANALYSIS
   Document:
   - RateLimitMiddleware class (app/middleware/rate_limit.py)
   - What limits are enforced
   - The _disabled_for_testing flag
   - Whether limits are per-user, per-workspace, or global

7. ERROR SANITIZATION
   Document the _sanitize_detail function (app/main.py line 112):
   - What strings trigger redaction ("password", "secret", "token", "api_key", "database_url")
   - The regex patterns for path redaction
   - Whether SQLAlchemy errors are fully sanitized

8. SECURITY HEADER INVENTORY
   Document every header set by SecurityHeadersMiddleware:
   - X-Content-Type-Options: nosniff (app/main.py line 52)
   - X-Frame-Options: DENY (app/main.py line 53)
   - X-XSS-Protection: 1; mode=block (app/main.py line 54)
   - Referrer-Policy: strict-origin-when-cross-origin (app/main.py line 55)
   - Permissions-Policy: geolocation=(), microphone=(), camera=() (app/main.py line 56)
   - Strict-Transport-Security: production only (app/main.py line 58)
   - Content-Security-Policy: different for production vs dev (app/main.py lines 60-79)

9. CORS CONFIGURATION
   Document:
   - Origin source: settings.cors_origins_safe (app/main.py line 215)
   - Allowed methods (app/main.py line 220)
   - Allowed headers (app/main.py line 221)
   - max_age (app/main.py line 222)

10. API KEY SECURITY
    Document:
    - ApiKey.key_hash (SHA-256, app/models.py line 698) — raw key never stored
    - ApiKey.key_prefix (8 chars, app/models.py line 701) — for identification
    - ApiKey.revoked_at nullable (app/models.py line 709) — soft revocation
    - The hashing mechanism in the API key creation endpoint

OUTPUT FILE: `docs/SWARMVAULT_GUARDRAILS_VALIDATION_ARCHITECTURE.md`

Required sections:
  1. Guardrail Inventory (table with all columns)
  2. Endpoint Validation Chains (per-endpoint trace)
  3. Failure Mode Analysis (per-stage)
  4. Cross-Stage Injection Analysis
  5. Policy Engine Architecture
  6. Rate Limiting Architecture
  7. Error Sanitization Architecture
  8. Security Headers Inventory
  9. CORS Configuration
  10. API Key Security
  11. Identified Gaps (table: gap, severity, evidence, impact)

============================================================
AGENT 4 — API / CONTRACT / INTEGRATION ARCHITECTURE
============================================================

TARGET: All API routers in app/api/, all frontend API calls

MANDATORY FILE READS:
  app/api/auth.py                (complete)
  app/api/workspace.py           (complete)
  app/api/projects.py            (complete)
  app/api/sessions.py            (complete)
  app/api/chat.py                (complete)
  app/api/memory.py              (complete)
  app/api/ingest.py              (complete)
  app/api/provenance.py          (complete)
  app/api/dashboard.py           (complete)
  app/api/feedback.py            (complete)
  app/api/api_keys.py            (complete)
  app/api/storage.py             (complete)
  app/api/policy.py              (complete)
  app/api/audit.py               (complete)
  frontend/src/lib/api.ts        (or equivalent API client)
  frontend/src/app/**/page.tsx   (all page components that make API calls)

SPECIFIC REQUIREMENTS:

1. API SURFACE INVENTORY
   For each router, create a table:

   | Method | Path | Request Schema | Response Schema | Auth | RBAC | Policy | Line |
   |--------|------|---------------|-----------------|------|------|--------|------|

   Complete this for ALL endpoints across ALL routers.

2. SSE STREAMING CONTRACT
   Document the SSE contract in app/api/chat.py:
   - Event types: "token", "sources", "done", "error" (lines 183, 184, 250, 260)
   - Data format: `data: {json}\n\n` (line 106)
   - Headers: Cache-Control: no-cache, X-Accel-Buffering: no (lines 272-273)
   - The latency_ms measurement (line 233)
   - The memory_grounded flag (line 256)
   - How the frontend consumes this (find the SSE consumer in frontend code)

3. ERROR RESPONSE FORMAT
   Document the standardized error format from app/main.py:
   ```json
   {
     "error": {
       "type": "<error_type>",
       "message": "<sanitized_message>",
       "request_id": "<uuid>"
     }
   }
   ```
   Trace where each error_type value is generated.

4. AUTHENTICATION FLOW
   Document the complete auth flow:
   - POST /api/v1/auth/register → UserRegister schema → User creation → Workspace creation → TokenResponse
   - POST /api/v1/auth/login → UserLogin schema → JWT creation → TokenResponse
   - POST /api/v1/auth/refresh → RefreshRequest → new TokenResponse
   - POST /api/v1/auth/change-password → ChangePasswordRequest → password update
   - The JWT dependency chain (find the get_current_user or equivalent)

5. TENANT CONTEXT PROPAGATION
   Document how tenant_id flows from JWT → TenantContext → every query:
   - get_tenant_context() returns TenantContext with tenant_id, workspace_id, user_id
   - Every query filters by workspace_id (and tenant_id where present)
   - Identify queries that filter by workspace_id but NOT tenant_id (potential gap)

6. INTEGRATION CLASSIFICATION
   For each external integration, classify:

   | Integration | Classification | Evidence | File:Line |
   |-------------|---------------|----------|-----------|
   | LLM Provider | IMPLEMENTED | get_llm_provider() | app/services/llm.py |
   | S3 Storage | IMPLEMENTED | object_storage_s3.py | app/services/ |
   | MinIO Storage | IMPLEMENTED | object_storage_minio.py | app/services/ |
   | MCP Server | PARTIAL | api_keys router | app/api/api_keys.py |
   | Claude Code | DOCUMENTED_ONLY | search docs/ | — |
   | Codex | DOCUMENTED_ONLY | search docs/ | — |

7. FRONTEND-BACKEND CONTRACT MATRIX
   For each frontend page, document:
   - Page path
   - API endpoints called
   - Request shape
   - Expected response shape
   - Error handling
   - SSE usage

   Example:
   ```
   /projects/[id]/chat
     → POST /api/v1/chat/         (ChatRequest → ChatResponse)
     → POST /api/v1/chat/stream   (ChatRequest → SSE events)
     → GET  /api/v1/sessions/     (list sessions)
   ```

OUTPUT FILE: `docs/SWARMVAULT_API_INTEGRATION_ARCHITECTURE.md`

Required sections:
  1. API Surface Inventory (complete endpoint table)
  2. SSE Streaming Contract
  3. Error Response Format
  4. Authentication Flow
  5. Tenant Context Propagation
  6. Integration Classification
  7. Frontend-Backend Contract Matrix
  8. Identified Gaps (table: gap, severity, evidence, impact)

============================================================
AGENT 5 — FRONTEND ARCHITECTURE
============================================================

TARGET: frontend/src/ directory

MANDATORY FILE READS:
  frontend/src/app/layout.tsx                    (root layout)
  frontend/src/app/page.tsx                      (home/redirect)
  frontend/src/app/auth/login/page.tsx           (login page)
  frontend/src/app/auth/register/page.tsx        (register page)
  frontend/src/app/dashboard/page.tsx            (dashboard)
  frontend/src/app/projects/page.tsx             (projects list)
  frontend/src/app/projects/[id]/layout.tsx      (project layout)
  frontend/src/app/projects/[id]/chat/page.tsx   (chat)
  frontend/src/app/projects/[id]/sessions/page.tsx (sessions)
  frontend/src/app/projects/[id]/sessions/[sessionId]/page.tsx (session detail)
  frontend/src/app/projects/[id]/memory/page.tsx (memory)
  frontend/src/app/projects/[id]/facts/page.tsx  (facts)
  frontend/src/app/projects/[id]/decisions/page.tsx (decisions)
  frontend/src/app/projects/[id]/timeline/page.tsx (timeline)
  frontend/src/app/projects/[id]/graph/page.tsx  (graph)
  frontend/src/app/projects/[id]/search/page.tsx (search)
  frontend/src/app/projects/[id]/provenance/page.tsx (provenance)
  frontend/src/app/projects/[id]/ingest/page.tsx (ingest)
  frontend/src/app/projects/[id]/settings/page.tsx (project settings)
  frontend/src/app/settings/page.tsx            (user settings)
  frontend/src/app/settings/api-keys/page.tsx   (API keys)
  frontend/src/app/settings/storage/page.tsx    (storage settings)
  frontend/src/components/Sidebar.tsx           (sidebar navigation)
  frontend/src/lib/api.ts                       (API client — if exists)

SPECIFIC REQUIREMENTS:

1. ROUTE INVENTORY
   Document every app router page with:
   - Exact route path (e.g., `/projects/[id]/chat`)
   - Component name
   - Layout used (root vs project layout)
   - Authentication requirement (is there a guard?)

2. STATE MANAGEMENT
   Document:
   - How auth state is stored (context, localStorage, cookies?)
   - How project/session state is managed
   - How SSE streams are managed (event source lifecycle)
   - How loading/error states are handled

3. API CLIENT
   Document:
   - Base URL configuration
   - Auth header injection (Authorization: Bearer)
   - Request/response interceptors
   - Error handling strategy

4. SSE CONSUMPTION
   Find the code that consumes the SSE stream from POST /api/v1/chat/stream:
   - How EventSource is created
   - How events are parsed (token, sources, done, error)
   - How the stream is terminated
   - Error recovery behavior

5. COMPONENT HIERARCHY
   For each major view, document the component tree:
   - Page component
   - Child components
   - Shared components (Sidebar, etc.)

6. FRONTEND-BACKEND MISMATCHES
   Identify:
   - Endpoints called by frontend that don't exist in backend
   - Fields expected in responses that aren't in schemas
   - Fields sent in requests that aren't in schemas
   - SSE event types consumed but not produced
   - Error shapes not matching the backend error format

OUTPUT FILE: `docs/SWARMVAULT_FRONTEND_ARCHITECTURE.md`

Required sections:
  1. Route Inventory
  2. Layout Architecture
  3. State Management
  4. API Client Configuration
  5. SSE Consumption
  6. Component Hierarchy (per-page)
  7. Frontend-Backend Mismatches
  8. Identified Gaps (table: gap, severity, evidence, impact)

============================================================
AGENT 6 — SECURITY, TENANCY & OPERATIONAL ARCHITECTURE
============================================================

TARGET: Auth, tenancy, RBAC, policy engine, audit, security middleware, API keys, database security

MANDATORY FILE READS:
  app/main.py                    (security headers, CORS, error sanitization)
  app/middleware/auth.py          (JWT handling)
  app/middleware/tenancy.py       (tenant isolation)
  app/middleware/rbac.py          (role checks)
  app/middleware/rate_limit.py    (rate limiting)
  app/models.py                   (UserRole enum, ApiKey, AuditEvent)
  app/schemas.py                  (password/API key schemas)
  app/services/policy/engine.py   (policy evaluation)
  app/services/policy/dependencies.py (policy enforcement)
  app/services/audit/service.py   (audit emission)
  app/services/audit/repository.py (audit persistence)
  app/services/audit/constants.py (audit event types)

SPECIFIC REQUIREMENTS:

1. AUTHENTICATION ARCHITECTURE
   - Document the JWT mechanism (find the actual JWT encode/decode)
   - Token types: access_token, refresh_token
   - RefreshToken model (app/models.py line 147) — revocation, expiration
   - Password handling: hashed_password column (app/models.py line 75), is hashing visible?
   - Email verification flow

2. RBAC ARCHITECTURE
   - UserRole enum values: OWNER, ADMIN, MEMBER, VIEWER (app/models.py line 11)
   - require_min_role dependency (app/middleware/rbac.py)
   - Role checks per endpoint (find all Depends(require_min_role(...)))
   - WorkspaceMember model (app/models.py line 97) — role column
   - Invitation model (app/models.py line 123) — state machine

3. TENANCY ISOLATION
   - Tenant → Workspace → Project hierarchy
   - tenant_id presence per model (compare across all models)
   - workspace_id presence per model
   - The TenantContext mechanism (app/middleware/tenancy.py)
   - Whether every query filters by tenant_id (not just workspace_id)

4. POLICY ENGINE
   - Policy model structure (app/models.py line 725)
   - PolicyVersion model (app/models.py line 762)
   - Rule structure (JSON column)
   - require_policy dependency chain
   - Fail-closed behavior: does policy evaluation deny on error?

5. API KEY SECURITY
   - Creation flow (find the endpoint)
   - key_hash mechanism (SHA-256, app/models.py line 698)
   - key_prefix for identification (app/models.py line 701)
   - Revocation via revoked_at (app/models.py line 709)
   - Expiration via expires_at (app/models.py line 706)
   - key_extra metadata (app/models.py line 711)

6. AUDIT ARCHITECTURE
   - AuditEvent model (app/models.py line 789) — all fields
   - Append-only invariant (line 792: "never updated")
   - AuditService.emit() — synchronous vs async
   - AuditPersistenceMiddleware — when events are flushed (app/main.py line 192)
   - Sensitive field exclusion (line 796: "must never be stored")
   - Correlation/tracing via request_id and correlation_id
   - INGEST_COMPLETED, INGEST_FAILED, etc. constants

7. DATA SECURITY
   - Soft delete vs hard delete
   - deleted_at indexing (which models have it)
   - Supersession via superseded_by_id
   - Content hashing for dedup (Source.content_hash)
   - Embedding as JSON (not encrypted)

8. SECURITY HEADER ANALYSIS
   - Complete header list from SecurityHeadersMiddleware
   - Production vs development differences
   - CSP directives and what they allow/block

9. DEPLOYMENT SECURITY
   - CORS origin source (settings.cors_origins_safe)
   - Swagger UI disabled in production (app/main.py line 181)
   - Environment-based behavior toggles

10. SECURITY GAP ANALYSIS
    Identify:
    - Models missing tenant_id (Fact, Decision, GraphNode, GraphEdge)
    - Unhashed sensitive fields (if any)
    - Missing CSP directives
    - Weak rate limiting (if any)
    - Audit gaps (actions not audited)

OUTPUT FILE: `docs/SWARMVAULT_SECURITY_OPERATIONAL_ARCHITECTURE.md`

Required sections:
  1. Authentication Architecture
  2. RBAC Architecture
  3. Tenancy Isolation Analysis
  4. Policy Engine Architecture
  5. API Key Security
  6. Audit Architecture
  7. Data Security (soft delete, supersession, hashing)
  8. Security Headers
  9. Deployment Security
  10. Security Gap Analysis (table: gap, severity, evidence, impact, CVE-like reference)

============================================================
AGENT 7 — MEMORY INTELLIGENCE READINESS ARCHITECTURE
============================================================

TARGET: Memory data structures, pipeline outputs, retrieval, provenance

MANDATORY FILE READS:
  app/models.py                   (Memory, Fact, Decision, GraphNode, GraphEdge, Source, MessageProvenance)
  app/schemas.py                  (MemoryCreate, MemoryUpdate, MemoryOut, MemorySearchRequest)
  app/services/memory.py          (MemoryService — write, read, update, delete, search)
  app/services/m5_retrieval.py    (retrieval logic)
  app/services/retrieval.py       (retrieval orchestrator)
  app/services/pipeline.py        (pipeline orchestration)
  app/services/chat_orchestrator.py (chat + memory integration)

SPECIFIC REQUIREMENTS:

1. MEMORY MODEL READINESS ANALYSIS
   For each field in the Memory model (app/models.py lines 232-266), assess readiness:

   | Field | Type | Memory Intelligence Requirement | Ready? | Evidence |
   |-------|------|--------------------------------|--------|----------|
   | id | String(36) UUID | Unique identity | YES | models.py line 235 |
   | tenant_id | String(36) FK | Multi-tenant scope | YES | models.py line 238 |
   | workspace_id | String(36) FK | Workspace scope | YES | models.py line 241 |
   | user_id | String(36) FK | User attribution | YES | models.py line 244 |
   | agent_id | String(36) nullable | Agent attribution | PARTIAL | models.py line 245 (nullable, no FK) |
   | run_id | String(36) nullable | Execution run attribution | PARTIAL | models.py line 246 (nullable, no FK) |
   | project_id | String(36) FK nullable | Project scope | YES | models.py line 247 |
   | memory_type | String(50) | Memory classification | PARTIAL | models.py line 250 (free text, no enum) |
   | content | Text | Actual memory content | YES | models.py line 251 |
   | metadata | JSON nullable | Extended metadata | PARTIAL | models.py line 252 (unstructured) |
   | embedding | JSON nullable | Vector representation | PARTIAL | models.py line 253 (nullable, no dimension enforcement) |
   | temporal_status | String(50) | Temporal validity | PARTIAL | models.py line 254 (free text: "current"/"historical"/"superseded") |
   | confidence | Float default 0.7 | Certainty level | YES | models.py line 255 |
   | authority | Float default 1.0 | Trust level | YES | models.py line 256 |
   | deleted_at | DateTime nullable | Soft delete | YES | models.py line 257 |
   | created_at | DateTime | Creation timestamp | YES | models.py line 258 |
   | updated_at | DateTime | Update timestamp | YES | models.py line 261 |

2. MEMORY TYPE TAXONOMY
   Document all memory_type values found in the codebase:
   - "procedural_memory" (default in MemoryCreate, app/schemas.py line 190)
   - Search for other hardcoded values
   - Assess: is there an enum? No — it's free text (GAP)

3. FACT MODEL READINESS
   For Fact model (app/models.py lines 414-465):
   - subject, predicate, object: RDF-style triple structure
   - confidence, authority: same as Memory
   - temporal_status, superseded_by_id: same as Memory
   - session_id: links to chat session
   - GAP: no tenant_id column (only workspace_id)
   - GAP: no embedding column for semantic search

4. DECISION MODEL READINESS
   For Decision model (app/models.py lines 468-518):
   - content, context: decision text and context
   - confidence, authority: same as Memory
   - temporal_status, superseded_by_id: same as Memory
   - GAP: no tenant_id column
   - GAP: no embedding column
   - GAP: no structured decision type (e.g., "architectural", "operational", "tactical")

5. GRAPH MODEL READINESS
   For GraphNode (app/models.py lines 521-558) and GraphEdge (app/models.py lines 562-605):
   - node_type: String(50) default "entity" — free text, not enum
   - properties: JSON — unstructured
   - confidence on edges only (not nodes)
   - temporal_status on edges only (not nodes)
   - source_id on edges (provenance link)
   - GAP: nodes lack confidence, authority, temporal_status
   - GAP: no embedding for nodes

6. PROVENANCE READINESS
   For MessageProvenance model (app/models.py lines 608-654):
   - Full LLM call traceability (model, provider, tokens, latency)
   - memory_ids_used: JSON list — which memories informed the response
   - retrieval_sources: JSON list — raw source data
   - user_message_preview: String(500) — truncated for privacy
   - confidence: nullable float
   - GAP: no correlation to specific Fact/Decision records used
   - GAP: no link to the retrieval scoring method

7. RETRIEVAL READINESS
   For M5 retrieval (app/services/m5_retrieval.py):
   - retrieve_hybrid: multi-factor scoring
   - retrieve_memories: used by chat.py for context
   - Document what factors are scored
   - Document the scoring threshold (0.1 in chat.py line 171)
   - GAP: no BM25/keyword search component visible
   - GAP: no reranking step visible

8. MEMORY SERVICE ANALYSIS
   For MemoryService (app/services/memory.py):
   - write(): creates Memory with provenance
   - read(): retrieves with authorization
   - update(): modifies with provenance
   - delete(): soft delete
   - search(): full-text search
   - Document the MemoryRecord dataclass/namedtuple
   - Document the provenance attachment mechanism
   - Document the audit emission pattern

9. MEMORY WRITE AUTHORITY
   Document who can write memories:
   - POST /api/v1/memory/ requires require_policy("memory", "write")
   - Memory is created with user_id from TenantContext
   - agent_id and run_id from request body
   - GAP: no verification that agent_id/run_id are valid
   - GAP: no rate limiting on memory writes

10. MEMORY SAFETY GATE ANALYSIS
    Define the conditions that must be met before a memory becomes "persistent":
    a. Must have tenant_id, workspace_id, user_id — YES
    b. Must have content — YES (validated)
    c. Must have confidence — YES (default 0.7)
    d. Must have authority — YES (default 1.0)
    e. Must have temporal_status — YES (default "current")
    f. Must have provenance — PARTIAL (created_at only, no source tracking)
    g. Must have retrieval path — PARTIAL (full-text search only, no vector)
    h. Must be auditable — PARTIAL (creation audited, updates not clearly traced)

11. MEMORY INTELLIGENCE BOUNDARY
    Define the boundary between what exists today and what a future intelligence layer needs:

    CAN SAFELY CONSUME TODAY:
    - Memory.content with confidence/authority
    - Fact.subject-predicate-object triples with confidence/authority
    - Decision.content with confidence/authority
    - Graph nodes and edges with confidence
    - Provenance records for LLM responses
    - Temporal status for time-aware queries

    MUST NOT ASSUME (missing capabilities):
    - Vector embeddings (nullable, not populated)
    - Memory type taxonomy (free text, not enum)
    - Structured agent attribution (agent_id nullable, no validation)
    - Contradiction detection (no mechanism found)
    - Memory consolidation/merge (no mechanism found)
    - Automatic supersession (requires manual update)
    - Cross-workspace memory sharing (by design, but no cross-reference mechanism)

OUTPUT FILE: `docs/SWARMVAULT_MEMORY_INTELLIGENCE_READINESS.md`

Required sections:
  1. Memory Model Field-by-Field Readiness
  2. Memory Type Taxonomy
  3. Fact Model Readiness
  4. Decision Model Readiness
  5. Graph Model Readiness
  6. Provenance Readiness
  7. Retrieval Readiness
  8. Memory Service Analysis
  9. Memory Write Authority
  10. Memory Safety Gate Analysis
  11. Memory Intelligence Boundary Definition
  12. Identified Gaps (table: gap, severity, evidence, impact)

============================================================
CROSS-AGENT REQUIREMENT — DATA LINEAGE
============================================================

Every specialist must include a DATA LINEAGE section documenting the complete path of data through their domain.

Use this canonical structure for every data type:

  SOURCE (entry)
    ↓ app/api/ingest.py POST /upload (line 38)
    ↓ IngestUploadRequest validation (app/schemas.py line 377)
    ↓ content_hash dedup (app/api/ingest.py line 62)
    ↓ run_pipeline() (app/services/pipeline.py)
      ↓ M0: Source creation (app/models.py line 302)
      ↓ M0: NormalizedMessage creation (app/models.py line 370)
      ↓ M1: Session understanding (app/services/m1_session.py)
      ↓ M2: Fact/Decision extraction (app/services/m2_facts.py)
      ↓ M3: Temporal processing (app/services/m3_temporal.py)
      ↓ M4: Graph construction (app/services/m4_graph.py)
    ↓ Source.status = "completed"
    ↓ PERSISTENCE: PostgreSQL
    ↓ RETRIEVAL: M5 hybrid search
    ↓ API: GET /api/v1/ingest/search
    ↓ FRONTEND: search results display

For every transition, document:
  - INPUT CONTRACT: exact data structure
  - OUTPUT CONTRACT: exact data structure
  - VALIDATION: what is checked
  - GUARDRAIL: what prevents bad data
  - PERSISTENCE: what is written
  - PROVENANCE: what trace is left
  - FAILURE BEHAVIOR: what happens on error

============================================================
CROSS-AGENT REQUIREMENT — EVIDENCE CROSS-REFERENCES
============================================================

When Agent 1 finds a fact that Agent 2 also needs, do NOT copy the analysis.
Instead, use this reference format:

  CROSS-REF: AGENT-2 — see `app/models.py` line 238 for Memory.tenant_id
  CROSS-REF: AGENT-4 — see `app/api/memory.py` line 78 for the create endpoint
  CROSS-REF: AGENT-6 — see `app/models.py` line 11 for UserRole enum

The synthesis agent will resolve these into a unified document.

============================================================
CROSS-AGENT REQUIREMENT — GAP CLASSIFICATION
============================================================

All agents must use this unified gap severity system:

  P0 — CRITICAL: Data loss, security breach, or system failure possible
  P1 — HIGH: Functional impairment, data inconsistency, or security weakness
  P2 — MEDIUM: Missing capability, technical debt, or maintainability risk
  P3 — LOW: Nice-to-have, documentation gap, or minor inconsistency

Each gap entry must contain:
  - GAP ID (e.g., GAP-A1-001)
  - Severity (P0-P3)
  - Category (SECURITY, DATA, PIPELINE, API, FRONTEND, OBSERVABILITY)
  - Description (one sentence)
  - Evidence (file:line citations)
  - Impact (what breaks or degrades)
  - Blocks persistent memory? (YES/NO/PARTIAL)
  - Blocks memory intelligence? (YES/NO/PARTIAL)

============================================================
FINAL SYNTHESIS AGENT
============================================================

After all 7 specialist documents are written, launch the Architecture Synthesis Agent.

It must:
  1. Read all 7 specialist documents
  2. Read all source files (same list as specialists)
  3. Read existing docs/ files for cross-reference
  4. Resolve all CROSS-REF references
  5. Reconcile contradictions against source code
  6. Unify gap classifications
  7. Produce 8 final documents

The synthesis agent must NOT blindly merge specialist claims. Where specialists disagree, the source code is the tiebreaker.

============================================================
FINAL DOCUMENT 1 — MASTER ARCHITECTURE
============================================================

FILE: `docs/SWARMVAULT_WEBAPP_MASTER_ARCHITECTURE.md`

Required sections (exact headings):
  1. Executive Summary (≤500 words, key findings only)
  2. Repository Baseline (branch, SHA, working tree state)
  3. Product Boundary (what is in scope, what is out of scope)
  4. System Context (external dependencies, integrations)
  5. Architectural Principles (derived from actual code patterns)
  6. High-Level Architecture Diagram (textual, Mermaid, or ASCII)
  7. Backend Architecture (from AGENT 1, reconciled)
  8. Frontend Architecture (from AGENT 5, reconciled)
  9. API Architecture (from AGENT 4, reconciled)
  10. Data Architecture (from AGENT 2, reconciled)
  11. Memory Architecture (from AGENT 7, reconciled)
  12. Storage Architecture (PostgreSQL, indexes, constraints)
  13. Security Architecture (from AGENT 6, reconciled)
  14. Tenancy Architecture (from AGENT 1 + AGENT 6, reconciled)
  15. Pipeline Architecture (M0-M5, from AGENT 2 + AGENT 3)
  16. M0–M5 Architecture Detail (per-stage contracts)
  17. Guardrail Architecture (from AGENT 3, reconciled)
  18. Validation Architecture (from AGENT 3, reconciled)
  19. Provenance Architecture (from AGENT 2 + AGENT 6)
  20. Audit Architecture (from AGENT 6)
  21. Retrieval Architecture (from AGENT 7)
  22. SSE/Streaming Architecture (from AGENT 4)
  23. Ingestion Architecture (from AGENT 2 + AGENT 4)
  24. Integration Architecture (from AGENT 4)
  25. Deployment Architecture (from Phase 0)
  26. Failure & Recovery Architecture (from AGENT 3)
  27. Observability Architecture (from AGENT 1 + AGENT 6)
  28. Test Architecture (from Phase 0 test inventory)
  29. Current Limitations (consolidated gap list)
  30. Technical Debt (consolidated gap list, prioritized)
  31. Future Memory Intelligence Boundary (from AGENT 7)
  32. Architectural Readiness Assessment (overall)

Every section must include EVIDENCE citations. Every claim must be backed by source code.

============================================================
FINAL DOCUMENT 2 — END-TO-END FLOWS
============================================================

FILE: `docs/SWARMVAULT_END_TO_END_FLOWS.md`

Document these flows with exact file:line citations for every step:

  FLOW-001 User Registration
    Trigger: POST /api/v1/auth/register
    → UserRegister validation (app/schemas.py line 7)
    → User creation (app/api/auth.py)
    → Workspace creation (app/api/workspace.py)
    → JWT generation
    → TokenResponse
    → Audit event emission
    → Frontend: store tokens, redirect to dashboard

  FLOW-002 Login
    Trigger: POST /api/v1/auth/login
    → UserLogin validation
    → JWT generation
    → RefreshToken creation (app/models.py line 147)
    → TokenResponse

  FLOW-003 Workspace Creation
  FLOW-004 Project Creation
  FLOW-005 Session Ingestion (create session via chat)
  FLOW-006 JSON Ingestion
  FLOW-007 JSONL Ingestion
  FLOW-008 ChatGPT Ingestion
  FLOW-009 M0 Normalization
  FLOW-010 M1 Session Understanding
  FLOW-011 M2 Fact/Decision Extraction
  FLOW-012 M3 Temporal Processing
  FLOW-013 M4 Graph Construction
  FLOW-014 M5 Retrieval Indexing
  FLOW-015 Persistent Memory Creation (API)
  FLOW-016 Memory Retrieval (search)
  FLOW-017 Memory Update
  FLOW-018 Memory Soft Delete
  FLOW-019 Chat (non-streaming)
  FLOW-020 Chat (SSE streaming)
  FLOW-021 Provenance Recording
  FLOW-022 Graph Exploration
  FLOW-023 Timeline Query
  FLOW-024 Fact Query
  FLOW-025 Decision Query
  FLOW-026 Feedback Submission
  FLOW-027 API Key Creation
  FLOW-028 API Key Revocation
  FLOW-029 Audit Event Emission
  FLOW-030 Policy Evaluation

For each flow, document:
  TRIGGER (endpoint or UI action)
  INPUT (exact request body or UI state)
  VALIDATION (schemas, middleware)
  AUTHORIZATION (RBAC, policy)
  PROCESSING (service calls, pipeline stages)
  PERSISTENCE (database writes)
  OUTPUT (response, SSE events, UI update)
  FAILURE BEHAVIOR (error response, rollback, user message)
  SECURITY BOUNDARY (what is checked at each layer)
  PROVENANCE (what is logged/audited)

============================================================
FINAL DOCUMENT 3 — GUARDRAIL MASTER MATRIX
============================================================

FILE: `docs/SWARMVAULT_GUARDRAIL_MASTER_MATRIX.md`

Consolidate all guardrails from AGENT 3 into a single matrix:

  | # | Guardrail | Type | Endpoint(s) | Enforcement Point | File:Line | Active | Bypassable | Test | Severity |
  |---|-----------|------|-------------|-------------------|-----------|--------|-----------|------|----------|

Plus a separate section:

  MEMORY SAFETY GATE MATRIX

  For each condition that must be satisfied before information becomes persistent memory:

  | Condition | Gate | Enforcement | File:Line | Status |
  |-----------|------|-------------|-----------|--------|
  | Content not null/empty | Schema | MemoryCreate validator | schemas.py:196 | Active |
  | Content no null bytes | Schema | MemoryCreate.validator | schemas.py:198 | Active |
  | Tenant isolation | Query filter | Memory.tenant_id == tc.tenant_id | memory.py:146 | Active |
  | Workspace isolation | Query filter | Memory.workspace_id == tc.workspace_id | memory.py:147 | Active |
  | User isolation | Query filter | Memory.user_id == tc.user_id | memory.py:148 | Active |
  | Write authorization | Policy | require_policy("memory", "write") | memory.py:83 | Active |
  | Delete authorization | RBAC + Policy | require_min_role("owner") + require_policy | memory.py:245-246 | Active |
  | Provenance attachment | Service | MemoryService.write provenance param | memory.py:115 | Active |
  | Audit emission | Service | AuditService.emit | memory.py:110-116 | Active |

============================================================
FINAL DOCUMENT 4 — DATA & MEMORY READINESS
============================================================

FILE: `docs/SWARMVAULT_PERSISTENT_MEMORY_READINESS.md`

For each data type, answer these questions with YES/NO/PARTIAL and evidence:

  1. What data is currently persistent?           → YES: Memory, Fact, Decision, GraphNode, GraphEdge, Source, AuditEvent
  2. What data is ephemeral?                      → PARTIAL: SSE stream events, LLM context
  3. What data is normalized?                     → YES: NormalizedMessage
  4. What data has provenance?                    → PARTIAL: MessageProvenance (LLM calls only), Source (content_hash)
  5. What data has temporal semantics?            → YES: temporal_status on Memory, Fact, Decision, GraphEdge
  6. What data has confidence?                    → YES: Memory.confidence, Fact.confidence, Decision.confidence, GraphEdge.confidence
  7. What data has authority?                     → YES: Memory.authority, Fact.authority, Decision.authority
  8. What data has identity?                      → YES: all models have UUID id
  9. What data has scope?                         → PARTIAL: tenant_id missing on Fact, Decision, GraphNode, GraphEdge
  10. What data can be superseded?                → YES: Fact.superseded_by_id, Decision.superseded_by_id
  11. What data can be contradicted?              → NO: no contradiction detection mechanism found
  12. What data can be deleted?                   → YES: soft delete via deleted_at on most models
  13. What data can be retrieved?                 → YES: all via API endpoints
  14. What data can be explained?                 → PARTIAL: provenance for LLM calls, not for memory creation
  15. What data is safe for future memory intelligence? → PARTIAL: see boundary definition

Then classify each data type:
  GREEN = fully ready
  YELLOW = partially ready (list what's missing)
  RED = not ready (list what's blocking)

============================================================
FINAL DOCUMENT 5 — FRONTEND ↔ BACKEND ARCHITECTURE
============================================================

FILE: `docs/SWARMVAULT_FRONTEND_BACKEND_ARCHITECTURE.md`

For every frontend page, create a trace:

  PAGE: /projects/[id]/memory
  COMPONENT: MemoryPage (frontend/src/app/projects/[id]/memory/page.tsx)
  STATE: memories[], loading, error
  API CALLS:
    GET /api/v1/memory/?project_id=<id>&limit=50
    → MemoryService.list (app/api/memory.py line 132)
    → select(Memory).where(...) (app/api/memory.py line 145)
    → MemoryOut response model (app/schemas.py line 225)
  BACKEND DOMAIN: Memory CRUD
  DATA MODEL: Memory (app/models.py line 232)
  FRONTEND RENDERING: table/list of MemoryOut items
  ERROR HANDLING: HTTPException 404 → error state
  AUTH: require_min_role("viewer") implicit via global auth guard

Do this for ALL pages:
  /dashboard, /projects, /projects/[id]/chat, /projects/[id]/sessions,
  /projects/[id]/sessions/[sessionId], /projects/[id]/memory,
  /projects/[id]/facts, /projects/[id]/decisions, /projects/[id]/timeline,
  /projects/[id]/graph, /projects/[id]/search, /projects/[id]/provenance,
  /projects/[id]/ingest, /projects/[id]/settings, /settings, /settings/api-keys,
  /settings/storage, /settings/profile, /auth/login, /auth/register

Include authentication requirements per page:
  - Public: /auth/login, /auth/register
  - Authenticated: /dashboard, /projects
  - Workspace member: /projects/[id]/*
  - Owner-only: /projects/[id]/settings (if applicable)

============================================================
FINAL DOCUMENT 6 — ARCHITECTURAL TRACEABILITY MATRIX
============================================================

FILE: `docs/SWARMVAULT_ARCHITECTURAL_TRACEABILITY.md`

Create a traceability matrix mapping requirements to implementation:

  | Requirement | Frontend | API Router | Service | Data Model | Pipeline | Guardrail | Test | Persistence | Provenance |
  |-------------|----------|------------|---------|------------|----------|-----------|------|-------------|------------|

For each major capability:
  1. User authentication → trace to auth router, JWT middleware, User model, login tests
  2. Workspace creation → trace to workspace router, Workspace model, tenancy
  3. Memory creation → trace to memory router, MemoryService, Memory model, memory tests
  4. Chat streaming → trace to chat router, chat_orchestrator, Message model, SSE tests
  5. Ingestion pipeline → trace to ingest router, pipeline.py, Source/NormalizedMessage/Fact/Decision/GraphNode models
  6. Fact retrieval → trace to ingest router, m5_retrieval, Fact model
  7. Graph visualization → trace to ingest router, m4_graph, GraphNode/GraphEdge models
  8. Provenance tracking → trace to provenance router, MessageProvenance model, audit service
  9. Audit logging → trace to AuditPersistenceMiddleware, AuditService, AuditEvent model
  10. Policy enforcement → trace to require_policy, Policy/PolicyVersion models

============================================================
FINAL DOCUMENT 7 — ARCHITECTURAL GAPS & NEXT MEMORY LAYER
============================================================

FILE: `docs/SWARMVAULT_ARCHITECTURAL_GAPS_AND_MEMORY_NEXT_LAYER.md`

SECTION 1: GAP REGISTER

Consolidate all gaps from all agents into a unified register:

  | ID | Severity | Category | Description | Evidence | Impact | Blocks Persistent Memory | Blocks Memory Intelligence |
  |----|----------|----------|-------------|----------|--------|--------------------------|----------------------------|

SECTION 2: PRIORITIZED GAP ANALYSIS

Group by severity:
  P0 gaps (must fix before production at scale)
  P1 gaps (must fix for full functionality)
  P2 gaps (should fix for maintainability)
  P3 gaps (nice to have)

For each P0/P1 gap, provide:
  CURRENT STATE → description with evidence
  RISK → what could go wrong
  EVIDENCE → file:line citations
  IMPACT → functional, security, or data integrity consequence
  REQUIRED CONDITION → what must be true to close the gap
  BLOCKS PERSISTENT MEMORY → YES/NO/PARTIAL with explanation
  BLOCKS MEMORY INTELLIGENCE → YES/NO/PARTIAL with explanation

SECTION 3: NEXT MEMORY INTELLIGENCE LAYER — READINESS BOUNDARY

This is NOT an implementation plan. It is a contract defining:

  WHAT THE CURRENT SYSTEM CAN SAFELY PROVIDE:
  - UUID-based identity for all memory objects
  - Tenant/workspace/project scoping
  - Confidence and authority scores
  - Temporal status tracking (current/historical/superseded)
  - Provenance for LLM-generated responses
  - Soft deletion
  - Full-text search
  - Graph representation of knowledge

  WHAT THE NEXT LAYER CAN TRUST:
  - Memory.content is the authoritative text
  - Memory.confidence reflects extraction certainty
  - Memory.authority reflects source trust
  - temporal_status reflects validity state
  - superseded_by_id creates a valid chain
  - AuditEvent provides append-only history
  - MessageProvenance provides LLM call traceability

  WHAT THE NEXT LAYER MUST NOT ASSUME:
  - Embeddings are populated (Memory.embedding is nullable, not enforced)
  - Memory types are standardized (free text, not enum)
  - Agent attribution is complete (agent_id is nullable)
  - Contradictions are detected (no mechanism exists)
  - Memories are consolidated (no merge mechanism)
  - Cross-workspace references are valid (by design, isolated)
  - Retrieval is exhaustive (M5 may miss relevant items)
  - Confidence scores are calibrated (default 0.7/1.0, not learned)

  WHAT CONTRACTS MUST EXIST BEFORE IMPLEMENTATION:
  - Memory type enum must be defined and enforced
  - Embedding dimension and model must be specified
  - Agent and run ID validation must be implemented
  - Contradiction detection algorithm must be specified
  - Memory consolidation rules must be defined
  - Cross-workspace sharing policy must be explicit
  - Retrieval exhaustiveness guarantee must be specified

============================================================
FINAL DOCUMENT 8 — ARCHITECTURE INDEX
============================================================

FILE: `docs/SWARMVAULT_ARCHITECTURE_INDEX.md`

Master index of all architecture documents:

  | Document | Purpose | Location | Key Findings | Cross-References |
  |----------|---------|----------|-------------|------------------|
  | ARCHITECTURE_FORENSICS_BASELINE.md | Repository baseline | docs/ | Branch, SHA, file inventory | All documents |
  | SWARMVAULT_BACKEND_ARCHITECTURE.md | Backend runtime | docs/ | Middleware stack, router inventory | AGENT-2, AGENT-3, AGENT-4 |
  | SWARMVAULT_DATA_MEMORY_ARCHITECTURE.md | Data & persistence | docs/ | M0-M5 pipeline, model inventory | AGENT-1, AGENT-2, AGENT-7 |
  | SWARMVAULT_GUARDRAILS_VALIDATION_ARCHITECTURE.md | Guardrails | docs/ | Per-endpoint validation chains | AGENT-1, AGENT-3, AGENT-6 |
  | SWARMVAULT_API_INTEGRATION_ARCHITECTURE.md | API contracts | docs/ | Endpoint inventory, SSE contract | AGENT-1, AGENT-4, AGENT-5 |
  | SWARMVAULT_FRONTEND_ARCHITECTURE.md | Frontend | docs/ | Route map, component hierarchy | AGENT-4, AGENT-5 |
  | SWARMVAULT_SECURITY_OPERATIONAL_ARCHITECTURE.md | Security | docs/ | Auth, RBAC, tenancy, audit | AGENT-1, AGENT-6 |
  | SWARMVAULT_MEMORY_INTELLIGENCE_READINESS.md | Memory readiness | docs/ | Field-by-field analysis | AGENT-2, AGENT-7 |
  | SWARMVAULT_WEBAPP_MASTER_ARCHITECTURE.md | Unified view | docs/ | Consolidated architecture | All documents |
  | SWARMVAULT_END_TO_END_FLOWS.md | Flow traces | docs/ | 30 documented flows | AGENT-1, AGENT-2, AGENT-4 |
  | SWARMVAULT_GUARDRAIL_MASTER_MATRIX.md | Guardrail matrix | docs/ | Complete guardrail table | AGENT-3 |
  | SWARMVAULT_PERSISTENT_MEMORY_READINESS.md | Memory readiness | docs/ | GREEN/YELLOW/RED classification | AGENT-7 |
  | SWARMVAULT_FRONTEND_BACKEND_ARCHITECTURE.md | Contract traces | docs/ | Per-page API contracts | AGENT-4, AGENT-5 |
  | SWARMVAULT_ARCHITECTURAL_TRACEABILITY.md | Traceability | docs/ | Requirement → implementation | All agents |
  | SWARMVAULT_ARCHITECTURAL_GAPS_AND_MEMORY_NEXT_LAYER.md | Gaps + boundary | docs/ | Prioritized gaps, intelligence boundary | All agents |

Each entry includes:
  - Document title
  - Purpose (one sentence)
  - Location (file path)
  - Key findings (bullet list)
  - Cross-references (which other documents reference this)
  - Evidence sources (which source files are most cited)

============================================================
OUTPUT FORMAT REQUIREMENTS
============================================================

1. All documents must be in Markdown format.
2. Every claim must have an EVIDENCE citation: `file:line` — description.
3. Every capability must be classified: IMPLEMENTED, PARTIALLY_IMPL, IMPLEMENTED_UNVERIFIED, DOCUMENTED_ONLY, PLANNED, MISSING, BLOCKED, DEPRECATED, UNKNOWN.
4. Evidence tables must be used where appropriate (Markdown tables).
5. Gap analysis must use the unified severity system (P0-P3).
6. Documents must be self-contained and readable independently.
7. All documents must reference the baseline SHA.
8. Cross-references between documents must use the format: `CROSS-REF: <DOCUMENT> — <section>`.

============================================================
DELIVERABLES CHECKLIST
============================================================

PHASE 0:
  - [ ] docs/ARCHITECTURE_FORENSICS_BASELINE.md

SPECIALIST AGENTS (parallel):
  - [ ] AGENT 1 — docs/SWARMVAULT_BACKEND_ARCHITECTURE.md
  - [ ] AGENT 2 — docs/SWARMVAULT_DATA_MEMORY_ARCHITECTURE.md
  - [ ] AGENT 3 — docs/SWARMVAULT_GUARDRAILS_VALIDATION_ARCHITECTURE.md
  - [ ] AGENT 4 — docs/SWARMVAULT_API_INTEGRATION_ARCHITECTURE.md
  - [ ] AGENT 5 — docs/SWARMVAULT_FRONTEND_ARCHITECTURE.md
  - [ ] AGENT 6 — docs/SWARMVAULT_SECURITY_OPERATIONAL_ARCHITECTURE.md
  - [ ] AGENT 7 — docs/SWARMVAULT_MEMORY_INTELLIGENCE_READINESS.md

SYNTHESIS (sequential, after specialists):
  - [ ] docs/SWARMVAULT_WEBAPP_MASTER_ARCHITECTURE.md
  - [ ] docs/SWARMVAULT_END_TO_END_FLOWS.md
  - [ ] docs/SWARMVAULT_GUARDRAIL_MASTER_MATRIX.md
  - [ ] docs/SWARMVAULT_PERSISTENT_MEMORY_READINESS.md
  - [ ] docs/SWARMVAULT_FRONTEND_BACKEND_ARCHITECTURE.md
  - [ ] docs/SWARMVAULT_ARCHITECTURAL_TRACEABILITY.md
  - [ ] docs/SWARMVAULT_ARCHITECTURAL_GAPS_AND_MEMORY_NEXT_LAYER.md
  - [ ] docs/SWARMVAULT_ARCHITECTURE_INDEX.md

Total: 16 documents.

============================================================
SUCCESS CRITERIA
============================================================

1. Every architectural claim has an EVIDENCE citation in `file:line` format.
2. Every capability is classified with evidence.
3. Every gap has a severity (P0-P3), evidence, and impact assessment.
4. The memory readiness assessment is grounded in actual model fields (not assumptions).
5. The next memory intelligence layer boundary is defined by what exists today, not what is planned.
6. No product code was modified during the analysis.
7. All documents are consistent with each other and with the source code.
8. The synthesis agent reconciled all contradictions, using source code as tiebreaker.
9. The traceability matrix covers all major capabilities.
10. The end-to-end flows cover all user-facing operations.

============================================================
BEGIN
============================================================

Start with PHASE 0 — establish the baseline.
Then launch the 7 specialist agents in parallel.
Then proceed with the final synthesis agent.
