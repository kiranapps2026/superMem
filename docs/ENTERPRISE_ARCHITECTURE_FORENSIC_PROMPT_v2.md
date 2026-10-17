# SwarmVault Enterprise Architecture Forensic Prompt — Granular v2.0

**Version:** 2.0
**Date:** 2026-09-10
**Baseline SHA:** e6f4b1c157afaed052584963b942ea04f9661610
**Audience:** Principal Enterprise Architect, Distributed Systems Architect,
Memory Systems Architect, Security Architect, Data Architect, Frontend Architect,
QA Architect, Technical Documentation Authority
**Phase:** Forensic (read-only — NO code modification permitted)

================================================================================
PREAMBLE: FORENSIC DISCIPLINE
================================================================================

You are performing a repository-first architectural forensic analysis.
Your output is an authoritative, evidence-backed architecture documentation
package. Every claim must trace to a file, function, route, model, or test.
Every claim must classify implementation status with evidence.

NOTHING in this prompt authorizes modifying product code.

================================================================================
ABSOLUTE RULES
================================================================================

RULE 1 — REPOSITORY IS THE SOLE SOURCE OF TRUTH
  Read actual files. Never infer architecture from filenames alone.
  For every important statement: file, module, function, route, model,
  schema, migration, config, test, runtime dep, actual execution path.
  Documentation may aid understanding but MUST NOT override executable
  implementation without explicitly identifying the discrepancy.

RULE 2 — READ-ONLY
  Do NOT refactor, rename, alter schema, change memory algorithms, change
  frontend behavior, fix problems, or silently correct documentation.
  If something is wrong, document it as a finding with severity.

  Allowed outputs: docs, architecture diagrams, evidence tables, traceability
  matrices, documentation indexes, generated inventories, analysis artifacts.
  If a documentation-only correction is necessary, record it explicitly.

RULE 3 — STATUS CLASSIFICATION
  Every capability must be classified as exactly one of:
    IMPLEMENTED              — Working, verified in source
    PARTIALLY_IMPLEMENTED    — Partially working, has known gaps
    IMPLEMENTED_BUT_UNVERIFIED — Code exists, not confirmed functional
    DOCUMENTED_ONLY          — Only in docs, no code
    PLANNED                  — Intended, no code yet
    MISSING                  — Required, absent entirely
    BLOCKED                  — Cannot proceed due to dependency
    DEPRECATED               — Exists but being phased out
    UNKNOWN                  — Cannot determine from available evidence
  Never describe planned functionality as implemented.
  Never describe an adapter as working because docs mention it.

RULE 4 — DATA LINEAGE TRACE
  Trace every data path end-to-end:
    SOURCE → INGESTION → NORMALIZATION → M0 → M1 → M2 → M3 → M4 → M5
    → PERSISTENCE → RETRIEVAL → API → FRONTEND → USER
  For every transition: input contract, output contract, validation,
  guardrail, persistence effect, provenance effect, failure behavior,
  memory quality effect.

RULE 5 — FINDINGS ARE EVIDENCE
  Every finding must include:
    ID, Severity (P0/P1/P2/P3), Category, Title, Current behavior,
    Expected behavior, Source evidence (file:line, function, route),
    Impact, Root cause, Recommended fix, Status

================================================================================
PHASE 0 — SOURCE CONTROL BASELINE
================================================================================

Before analysis begins, establish and record:

1.  Repository root path
2.  Current Git branch
3.  Exact HEAD SHA (full 40-char)
4.  Working-tree state: modified, untracked, staged files
5.  Repository structure (top-level directories and key files)
6.  Backend root: app/ directory structure (all .py files)
7.  Frontend root: frontend/ directory structure (all .tsx/.ts/.css files)
8.  Test locations: backend tests, e2e tests, any other test directories
9.  Migration files: all files under alembic/versions/
10. Docker/deployment configuration: Dockerfile, docker-compose, k8s, etc.
11. Environment files: .env, .env.example, .env.local (paths only — NEVER contents)
12. Existing documentation: all .md files, especially under docs/

Output: docs/PHASE_BUGFIX_BASELINE.md with exact SHA, timestamp, env versions.

DO NOT continue if repository identity cannot be established.

================================================================================
PHASE 1 — COMPLETE FILE INVENTORY
================================================================================

Read EVERY source file in the repository. Build a complete inventory.

Backend (app/):
  - app/main.py              — Application construction, lifespan, middleware stack
  - app/db.py                — Engine, session, Base, init_db
  - app/core/config.py       — Settings, validators, CORS
  - app/core/security.py     — JWT, password hashing
  - app/models.py            — ALL SQLAlchemy models (read entire file)
  - app/schemas.py           — ALL Pydantic schemas (read entire file)
  - app/middleware/auth.py   — Auth dependency
  - app/middleware/tenancy.py— Tenant context dependency
  - app/middleware/rbac.py   — RBAC dependency
  - app/middleware/rate_limit.py — Rate limiter
  - app/api/*.py             — ALL API routers
  - app/services/*.py        — ALL service classes and functions
  - app/services/policy/     — Policy engine, evaluator, dependencies, repository
  - app/services/audit/      — Audit service, repository, constants
  - app/connectors/*.py      — ALL connectors
  - app/__init__.py, app/core/__init__.py, app/api/__init__.py

Frontend (frontend/):
  - frontend/package.json    — Dependencies, scripts
  - frontend/next.config.*   — Next.js configuration
  - frontend/tailwind.config.js — Tailwind configuration
  - frontend/tsconfig.json   — TypeScript configuration
  - frontend/src/app/        — Next.js App Router pages
  - frontend/src/components/ — Shared components
  - frontend/src/lib/        — Utility libraries (if present)
  - frontend/src/hooks/      — Custom hooks (if present)
  - frontend/src/contexts/   — React contexts (if present)
  - frontend/src/types/      — TypeScript types (if present)
  - frontend/public/         — Static assets
  - frontend/e2e/            — Playwright tests

Tests:
  - tests/ directory (if present)
  - frontend/e2e/ Playwright specs

Migrations:
  - alembic.ini
  - alembic/versions/*.py (all migration files)

For EACH file, read the COMPLETE content before classifying.

================================================================================
PHASE 2 — FINDING PROGRAM (Seven Parallel Disciplines)
================================================================================

Each discipline produces its own document. They share evidence but do not
overwrite each other's documents.

────────────────────────────────────────────────────────────────────────────────
DISCIPLINE A — BACKEND RUNTIME ARCHITECTURE
────────────────────────────────────────────────────────────────────────────────

Output: docs/SWARMVAULT_BACKEND_ARCHITECTURE.md

Coverage required:

A1. Application Startup
    - main.py: lifespan function, init_db call, migration runner
    - Startup order: settings → db engine → session factory → routers
    - Any async/sync mismatch in init_db (asyncio.get_event_loop in async context?)
    - Health check endpoints
    - Shutdown behavior

A2. Middleware Stack
    - Exact registration order in main.py
    - RateLimitMiddleware: path patterns, key functions, bypass conditions
    - AuthMiddleware vs TenantContext: which is actually registered?
    - CORS middleware configuration (origins, credentials, methods)
    - Any missing middleware (security headers, request ID, etc.)

A3. Router Registration
    - Which APIRouter instances are registered in main.py?
    - Which API prefixes are used?
    - Which routers exist but are NOT registered?
    - Tag consistency

A4. Authentication Architecture
    - Dual path problem: require_auth vs get_tenant_context
    - Which routes use which dependency?
    - JWT algorithm, expiration, no revocation
    - Refresh token: stored, validated, revoked?
    - Password hashing: bcrypt with default cost?
    - Token in URL or query param? (check all routers)

A5. Authorization Architecture
    - require_min_role: role hierarchy, where used, where missing
    - require_permission: defined but used?
    - require_policy: policy engine integration, where used
    - RBAC _get_permissions: correct hierarchy traversal?
    - PolicyEngine.check_role_minimum: fresh instance per call?
    - Authorization bypass vectors

A6. Tenancy Isolation
    - Workspace isolation: enforced at query level?
    - Tenant isolation: Memory.tenant_id FIX comment vs actual
    - Project isolation: workspace scoping before project scoping?
    - Cross-tenant data access prevention
    - Soft delete as tenancy boundary

A7. Database Access
    - Engine config: pool_size, max_overflow, pool_pre_ping, recycle
    - Session management: expire_on_commit=False implications
    - Transaction boundaries: which endpoints commit, which flush?
    - N+1 query patterns
    - Missing indexes

A8. Services Layer
    - Each service: class, methods, dependencies, DB access
    - MemoryService: singleton pattern, thread safety, cache invalidation
    - AuditService: singleton, register_db_sink timing
    - PolicyEngine: fresh instance per request?
    - LLM provider: get_llm_provider caching

A9. Error Handling
    - HTTPException usage consistency
    - Unhandled exception paths
    - Error information leakage (stack traces, SQL errors)
    - SSE error handling

A10. Configuration
    - Hardcoded dev defaults in source code
    - Environment variable validation
    - Missing production guards

Trace representative requests:
    POST /api/v1/auth/login
    POST /api/v1/memory/
    POST /api/v1/ingest/upload
    POST /api/v1/chat/
    GET  /api/v1/ingest/facts

For each: middleware → auth → router → validation → service → DB → response

────────────────────────────────────────────────────────────────────────────────
DISCIPLINE B — DATA, MEMORY & PERSISTENCE ARCHITECTURE
────────────────────────────────────────────────────────────────────────────────

Output: docs/SWARMVAULT_DATA_MEMORY_ARCHITECTURE.md

Coverage required:

B1. Complete Model Inventory
    For EVERY model in models.py:
    - Table name, columns (name, type, nullable, default, FK, index, unique)
    - Relationships (cascade, back_populates)
    - Soft delete support (deleted_at)
    - Tenant scoping (tenant_id column and usage)
    - Temporal fields (temporal_status, created_at, updated_at)
    - Provenance fields (if any in the model itself)

B2. Memory Model vs MemoryRecord Mismatch
    Compare Memory (SQLAlchemy model) vs MemoryRecord (dataclass):
    - Fields in MemoryRecord but NOT in Memory: importance, version, supersedes,
      superseded_by (as column), permissions, scope (as stored field)
    - Fields in Memory but NOT in MemoryRecord: embedding, run_id, agent_id
    - Metadata serialization: what goes into extra_metadata JSON column
    - MemoryTypeMapper: canonical vs vault type mapping correctness

B3. Data Lineage Per Stage
    For each pipeline stage M0–M5:
    INPUT  → What data enters (format, schema, source)
    TRANSFORMATION → What processing occurs
    OUTPUT → What data exits (format, schema, destination)
    VALIDATION → What checks are applied
    GUARDRAIL → What prevents bad data
    FAILURE MODE → What happens on error
    PERSISTENCE EFFECT → What is written to DB
    PROVENANCE EFFECT → What lineage is recorded
    MEMORY QUALITY EFFECT → How quality degrades or improves

B4. Ingestion Data Flow
    Raw input (JSON, JSONL, text, ChatGPT, Claude, Claude Code)
    → Connector (connectors.py)
    → Validation (size, format, content)
    → NormalizedConversation
    → Source record creation
    → NormalizedMessage records
    → Pipeline (M1–M5)
    → Fact/Decision/GraphNode/GraphEdge/Memory records

B5. Provenance Architecture
    - MessageProvenance model: what it captures, what it misses
    - Provenance in MemoryRecord: stored in extra_metadata
    - Source of truth for provenance: DB or cache?
    - What is NOT tracked: who approved, why, under what policy

B6. Temporal Architecture
    - temporal_status: values used, where set, where checked
    - Supersession: superseded_by_id in Fact/Decision, but NOT in Memory
    - Expiration: expires_at on ApiKey, but NOT on Memory
    - valid_from/valid_until in MemoryRecord: stored where?
    - Soft delete: deleted_at pattern across models

B7. Confidence & Authority
    - Memory.confidence: default 0.7, where set, where validated
    - Memory.authority: default 1.0, where set, where validated
    - Fact.confidence/authority: defaults 1.0, where set
    - Decision.confidence/authority: defaults 1.0, where set
    - How are these values computed? Who sets them?

B8. Deduplication
    - content_hash in Source: computed where, how, uniqueness guarantee?
    - Dedup check: race condition in ingest.py (check then insert, no lock)
    - Memory deduplication: is there any?

B9. Storage Architecture
    - PostgreSQL: what is stored where
    - Embedding storage: Memory.embedding (JSON floats), never populated?
    - File storage: object_storage.py, filesystem vs S3 vs MinIO
    - Storage path configuration

────────────────────────────────────────────────────────────────────────────────
DISCIPLINE C — PIPELINE, GUARDRAIL & VALIDATION ARCHITECTURE
────────────────────────────────────────────────────────────────────────────────

Output: docs/SWARMVAULT_GUARDRAILS_VALIDATION_ARCHITECTURE.md

Coverage required:

C1. Complete Guardrail Matrix
    Build a matrix covering EVERY stage of EVERY data flow:

    | Stage | Control | Location | Active | Partial | Missing | Bypassable | Untested |
    |-------|---------|----------|--------|---------|---------|------------|----------|

    Stages to cover:
    - HTTP request arrival
    - CORS
    - Rate limiting
    - Authentication (JWT validation)
    - Authorization (RBAC, policy engine)
    - Tenancy isolation (workspace, project, tenant)
    - Request schema validation (Pydantic)
    - Content size limits
    - Null byte checks
    - SQL injection prevention
    - Ingestion: source-type validation
    - Ingestion: JSON validation
    - Ingestion: JSONL validation
    - Ingestion: size limits
    - Normalization: message count limits
    - Normalization: message length limits
    - Pipeline: error handling per stage
    - Memory: policy check on write
    - Memory: tenant_id enforcement
    - Memory: workspace scoping
    - Retrieval: workspace scoping
    - Retrieval: user scoping
    - Retrieval: temporal filtering
    - Chat: session ownership
    - Chat: project isolation
    - Output: data leakage prevention
    - Error: information leakage prevention
    - Audit: event emission completeness

C2. Validation Gap Analysis
    For each input path:
    - What validates the input?
    - What does NOT validate?
    - What can bypass validation?

C3. Security Boundary Analysis
    Map every trust boundary:
    - Internet → API Gateway (none exists — direct FastAPI)
    - API → Auth
    - Auth → Router
    - Router → Service
    - Service → Policy Engine
    - Service → Database
    - Service → LLM Provider
    - For each: what crosses, what is checked, what is NOT checked

────────────────────────────────────────────────────────────────────────────────
DISCIPLINE D — API / CONTRACT / INTEGRATION ARCHITECTURE
────────────────────────────────────────────────────────────────────────────────

Output: docs/SWARMVAULT_API_INTEGRATION_ARCHITECTURE.md

Coverage required:

D1. Complete API Surface Inventory
    For EVERY router:
    - Prefix, all routes, HTTP methods
    - Request schemas (read from schemas.py)
    - Response schemas
    - Auth dependency used
    - RBAC dependency used
    - Policy dependency used
    - Query parameters
    - Status codes returned
    - Error responses

D2. API Route Matrix
    | Route | Method | Auth | RBAC | Policy | Schema In | Schema Out | DB Access |
    For every endpoint.

D3. Integration Verification
    For each claimed integration:
    - Claude Code integration: connector exists, but is it wired to an endpoint?
    - Codex integration: any code? any docs?
    - Universal Adapter: any code? any docs?
    - MCP: ApiKey model exists, but is there an MCP server endpoint?
    - SSE: /chat/stream exists, but is there a frontend consumer?
    - REST: all endpoints verified
    - External LLM providers: Anthropic configured, OpenAI key exists but unused?

D4. Contract Verification
    - MemoryCreate schema vs MemoryRecord dataclass: field mapping
    - MemoryOut schema vs Memory model: field mapping
    - ChatRequest vs process_chat: parameter alignment
    - IngestUploadRequest vs run_pipeline: parameter alignment
    - Any mismatches between frontend expectations and backend responses

────────────────────────────────────────────────────────────────────────────────
DISCIPLINE E — FRONTEND ARCHITECTURE
────────────────────────────────────────────────────────────────────────────────

Output: docs/SWARMVAULT_FRONTEND_ARCHITECTURE.md

Coverage required:

E1. Next.js Architecture
    - App Router vs Pages Router
    - Route structure: every page.tsx
    - Layout hierarchy
    - Server vs Client components

E2. Component Inventory
    - Every component under src/components/
    - Props, state, API calls per component
    - Which pages use which components

E3. State Management
    - Confirm: no state management library (no Redux, Zustand, etc.)
    - How is server state managed? (React cache? refetch?)
    - How is client state managed? (useState, useContext?)
    - Authentication state: how stored, how refreshed

E4. API Client
    - How are API calls made? (fetch? axios?)
    - Base URL configuration
    - Token handling (Authorization header)
    - Error handling
    - SSE consumer: does frontend consume /chat/stream?

E5. Frontend/Backend Contract Matrix
    For each important screen/feature:
    Screen → Component → API Endpoint → Backend Router → Service → Model
    Identify mismatches.

E6. Security
    - Token storage: localStorage? sessionStorage? cookie?
    - XSS vectors: innerHTML? dangerouslySetInnerHTML?
    - CSRF protection
    - Sensitive data in client-side code

────────────────────────────────────────────────────────────────────────────────
DISCIPLINE F — SECURITY, TENANCY & OPERATIONAL ARCHITECTURE
────────────────────────────────────────────────────────────────────────────────

Output: docs/SWARMVAULT_SECURITY_OPERATIONAL_ARCHITECTURE.md

Coverage required:

F1. Authentication Security
    - JWT: HS256 (acceptable but no key rotation)
    - No token revocation on logout
    - Refresh tokens: stored, no revocation list
    - Password: bcrypt (good), but no account lockout
    - No MFA support
    - No password reset flow visible

F2. Authorization Security
    - RBAC hierarchy: correct? (owner > admin > member > viewer)
    - Policy engine: default-deny or default-allow?
    - require_min_role vs require_permission: which is enforced?
    - Cross-workspace access: prevented?
    - Cross-tenant access: prevented?
    - Memory write without tenant_id (FIX comment in code)

F3. Input Security
    - SQL injection: parameterized queries? (yes, mostly)
    - SQL injection: ilike with user input (search endpoints)
    - XSS: no output encoding in frontend?
    - SSRF: no external URL fetching
    - Path traversal: no file path from user input
    - Command injection: no shell execution

F4. API Security
    - Rate limiting: in-memory (not distributed, not persistent)
    - Rate limiting: bypass via X-E2E header in non-production
    - CORS: default "*" in config
    - CORS: cors_origins_safe strips wildcard (good)
    - Security headers: none (no CSP, HSTS, X-Frame-Options)
    - Error sanitization: generic messages (good), but SSE error handler

F5. Data Security
    - Secrets in code: dev defaults in config.py (hardcoded)
    - Encryption at rest: none (plaintext passwords hashed, but data plaintext)
    - Encryption in transit: depends on deployment (not in code)
    - PII handling: email stored, no encryption

F6. Operational Security
    - Debug mode: echo=settings.debug (SQL logging in dev)
    - Health endpoints: none visible
    - Metrics: enable_metrics=False default
    - Logging: standard Python logging, no structured logging
    - No audit of admin actions (except AuditEvent model exists)

────────────────────────────────────────────────────────────────────────────────
DISCIPLINE G — MEMORY INTELLIGENCE READINESS
────────────────────────────────────────────────────────────────────────────────

Output: docs/SWARMVAULT_MEMORY_INTELLIGENCE_READINESS.md

This is the MOST IMPORTANT discipline. Determine readiness for:
  A. Persistent memory
  B. Long-term memory
  C. Memory intelligence
  D. Reasoning over memory
  E. Future autonomous memory operations

G1. Memory Record Completeness
    For each Memory record, does it contain:
    - IDENTITY: memory_id (yes, UUID)
    - SOURCE: source_id (NO — Memory has no FK to Source)
    - TIME: created_at, updated_at (yes), temporal_status (yes)
    - CONTEXT: workspace_id, project_id, user_id (yes)
    - CONFIDENCE: confidence column (yes, but default 0.7, no validation)
    - AUTHORITY: authority column (yes, but default 1.0, no validation)
    - PROVENANCE: in extra_metadata only (fragile)
    - RELATIONSHIPS: no graph edges from Memory to Facts/Decisions
    - SUPERSESSION: superseded_by in Facts/Decisions but NOT in Memory
    - CONTRADICTION: no contradiction tracking
    - SCOPE: workspace/project (yes), tenant (FIX comment only)
    - LIFECYCLE: status in metadata only, not a column
    - RETRIEVAL: embedding column (exists but empty)
    - AUDITABILITY: no audit event on memory create/update/delete

G2. Memory Readiness Scorecard
    | Capability | Ready | Partial | Missing | Evidence |
    For: Identity, Source, Time, Context, Confidence, Authority,
         Provenance, Relationships, Supersession, Contradiction,
         Scope, Lifecycle, Retrieval, Auditability

G3. Persistent Memory Boundary
    What is CURRENTLY safe for persistent memory:
    - Facts with provenance (source_id, confidence, authority)
    - Decisions with provenance (source_id, confidence, authority)
    - Sources with content_hash (dedup)
    - Graph nodes/edges with temporal_status
    What is NOT safe:
    - Memories without source tracing
    - Memories without tenant_id enforcement
    - Memories without audit trail

G4. Memory Intelligence Boundary
    What a future intelligence layer can safely consume TODAY:
    - Fact triplets (subject, predicate, object) with temporal status
    - Decision records with temporal status
    - Graph structure with temporal filtering
    - Provenance records for chat
    What it MUST NOT assume:
    - That memories have source lineage (they don't)
    - That all memories are tenant-isolated (they aren't)
    - That confidence/authority are validated (they aren't)
    - That embeddings exist (they don't — column is empty)
    - That the retrieval index is comprehensive (it isn't)

================================================================================
PHASE 3 — CROSS-AGENT DATA LINEAGE
================================================================================

Every discipline must document the complete data lineage:

SOURCE (user, file, API)
  ↓
INGESTION (connector, validation, normalization)
  ↓
M0 (NormalizedMessage in DB)
  ↓
M1 (Session understanding — what actually happens?)
  ↓
M2 (Fact/Decision extraction)
  ↓
M3 (Temporal processing)
  ↓
M4 (Graph construction)
  ↓
M5 (Retrieval index)
  ↓
PERSISTENCE (PostgreSQL)
  ↓
RETRIEVAL (hybrid search, M5)
  ↓
API (FastAPI response)
  ↓
FRONTEND (React rendering)
  ↓
USER

For each transition document:
- Input contract (schema, format)
- Output contract (schema, format)
- Validation applied
- Guardrail active
- Persistence effect
- Provenance recorded
- Failure behavior

================================================================================
PHASE 4 — SPECIFIC FORENSIC TARGETS
================================================================================

Focus analysis on these specific targets with heightened scrutiny:

F1. Dual Auth Path Inconsistency
    - app/middleware/auth.py: require_auth function
    - app/middleware/tenancy.py: get_tenant_context function
    - Which routers import from which?
    - Are both paths doing the same validation?
    - Can one path bypass what the other checks?

F2. Memory.tenant_id Enforcement Gap
    - Memory model has tenant_id column (FIX: set tenant for isolation)
    - MemoryRecord has tenant_id field
    - Where is tenant_id SET on Memory writes?
    - Where is tenant_id CHECKED on Memory reads?
    - Is cross-tenant memory access possible?

F3. Retrieval Completeness
    - Memory.embedding: column exists, but who populates it?
    - m5_retrieval.py: what does it actually retrieve?
    - retrieval.py vs services/retrieval.py: are they the same?
    - What is the candidate pool? (limit*3 = 60 for limit=20)
    - What if there are 10,000 memories? Only 60 are scored.

F4. Pipeline Completeness
    - services/pipeline.py: run_pipeline function
    - Does M1 actually do anything beyond storing messages?
    - Does M3 (temporal) actually modify anything?
    - services/m3_temporal.py: what does it do?
    - services/m2_facts.py: what does it do?
    - services/m4_graph.py: what does it do?
    - Are all stages wired end-to-end?

F5. Chat Provenance Gap
    - chat_orchestrator.py: saves MessageProvenance
    - But chat.py:flushes user+assistant messages, then commits
    - What if LLM call fails after user message is saved?
    - Is there a rollback? (No — flush happens before LLM call)
    - SSE path: same issue, but in streaming context

F6. Policy Engine Integration
    - PolicyEngine instantiated fresh in require_min_role
    - require_policy dependency: does it actually exist?
    - policy/engine.py: check_role_minimum implementation
    - policy/evaluator.py: generate_rbac_policies implementation
    - Are policies actually loaded from DB or hardcoded?

F7. Audit Completeness
    - AuditEvent model: comprehensive fields
    - audit/service.py: when are events emitted?
    - Which operations emit audit events?
    - Which do NOT?
    - Is there an audit sink configured? (register_db_sink called where?)

F8. Frontend Contract Drift
    - Frontend pages that call non-existent endpoints
    - Frontend expecting fields that backend doesn't return
    - Frontend not handling error responses
    - SSE consumer: does frontend implement EventSource?

================================================================================
PHASE 5 — SPECIFIC GAP REGISTERS
================================================================================

Build these registers as part of analysis:

REGISTER 1 — BUG_GAP_FORENSIC_INVENTORY.md
  Every bug, gap, or inconsistency found.
  Format: ID | Severity | Category | File:Line | Description | Impact | Fix

REGISTER 2 — CONTRACT_IMPLEMENTATION_RECONCILIATION.md
  Every M-ARCH contract document vs actual implementation.
  Format: Contract | Claim | Evidence | Status | Gap | Risk

REGISTER 3 — DOCUMENTATION_DRIFT_REGISTER.md
  Every place where documentation claims something the code doesn't implement.
  Format: Doc | Claim | Evidence | Status | Severity | Risk

REGISTER 4 — TEST_COVERAGE_GAP_REGISTER.md
  Every source module and whether it has tests.
  Format: Module | Tested | Test Count | Gaps | Risk

REGISTER 5 — SECURITY_FINDINGS_REGISTER.md
  Every security finding.
  Format: ID | Severity | Category | File:Line | Description | Impact | Fix

================================================================================
PHASE 6 — EVIDENCE STANDARDS
================================================================================

Every finding MUST include:
  - Exact file path (absolute or relative to repo root)
  - Exact line numbers
  - Function/class/method name
  - The actual code (quote it, don't paraphrase)
  - What it SHOULD do vs what it DOES

Every classification MUST include:
  - The evidence for IMPLEMENTED status, OR
  - The evidence for MISSING status, OR
  - The evidence for PARTIALLY_IMPLEMENTED status

================================================================================
DELIVERABLE STRUCTURE
================================================================================

After all analysis, produce these documents:

1. docs/PHASE_BUGFIX_BASELINE.md
   SHA, timestamp, environment, working tree state

2. docs/BUG_GAP_FORENSIC_INVENTORY.md
   Complete bug and gap inventory

3. docs/CONTRACT_IMPLEMENTATION_RECONCILIATION.md
   M-ARCH contracts vs implementation

4. docs/DOCUMENTATION_DRIFT_REGISTER.md
   Documentation claims vs code reality

5. docs/TEST_COVERAGE_GAP_REGISTER.md
   Test coverage gaps

6. docs/SECURITY_FINDINGS_REGISTER.md
   Security findings

7. docs/SWARMVAULT_BACKEND_ARCHITECTURE.md
   Complete backend architecture

8. docs/SWARMVAULT_DATA_MEMORY_ARCHITECTURE.md
   Data and memory architecture

9. docs/SWARMVAULT_GUARDRAILS_VALIDATION_ARCHITECTURE.md
   Guardrail matrix

10. docs/SWARMVAULT_API_INTEGRATION_ARCHITECTURE.md
    API surface and integrations

11. docs/SWARMVAULT_FRONTEND_ARCHITECTURE.md
    Frontend architecture

12. docs/SWARMVAULT_SECURITY_OPERATIONAL_ARCHITECTURE.md
    Security and operations

13. docs/SWARMVAULT_MEMORY_INTELLIGENCE_READINESS.md
    Memory readiness assessment

14. docs/FIX_PLAN_PHASE1_CRITICAL.md
    P0 fixes (safety, data integrity, auth)
    Each fix: what, where, why, how to verify

15. docs/FIX_PLAN_PHASE2_DATA_MEMORY.md
    P1 fixes (data, memory, pipeline)

16. docs/FIX_PLAN_PHASE3_RETRIEVAL_INGESTION.md
    P1 fixes (retrieval, ingestion, agents)

17. docs/FIX_PLAN_PHASE4_RELIABILITY_SCALE.md
    P2 fixes (reliability, scale, frontend)

18. docs/FIX_PLAN_PHASE5_FINAL.md
    P2/P3 fixes and final certification

================================================================================
EXECUTION PROTOCOL
================================================================================

1. Establish baseline (Phase 0)
2. Read EVERY source file (Phase 1) — no skipping
3. Run parallel analysis disciplines (Phase 2) — seven in parallel
4. Build cross-cutting lineage (Phase 3)
5. Deep-dive specific targets (Phase 4)
6. Build registers (Phase 5)
7. Write all documents (Phase 6)
8. Reconcile findings across disciplines
9. Build fix plans per phase
10. CERTIFICATION GATE: all P0 findings resolved before proceeding

================================================================================
CERTIFICATION GATE
================================================================================

Before any fix is applied:
1. All findings must be evidence-backed (file:line, function)
2. All classifications must be verified against source
3. No finding may be classified as IMPLEMENTED without code evidence
4. No fix may be applied without explicit user approval
5. Fix plans must be phase-separated (P0/P1/P2/P3)

================================================================================
END OF PROMPT
================================================================================
