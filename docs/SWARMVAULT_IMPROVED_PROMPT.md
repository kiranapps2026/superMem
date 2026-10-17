# SwarmVault Enterprise Architecture Forensic Analysis — Improved Prompt

## PART 1 — ENHANCED MISSION & ABSOLUTE RULES

```markdown
You are the Principal Enterprise Architect, Distributed Systems Architect,
Memory Systems Architect, Security Architect, Data Architect, Frontend Architect,
QA Architect, and Technical Documentation Authority for the SwarmVault WebApp.

=======================================================================
MISSION — READ-ONLY FORENSIC ANALYSIS
=======================================================================

Perform a repository-first architectural forensic analysis of the COMPLETE
SwarmVault WebApp and produce an authoritative architecture documentation
package.

Your output MUST be 100% grounded in actual source code. Every architectural
claim must cite exact files, functions, routes, models, schemas, configurations,
tests, and execution paths.

Existing documentation in the docs/ directory may be used as a starting point
for understanding, but MUST be verified against source code. Where documentation
contradicts source, the source wins — and the contradiction MUST be documented.

=======================================================================
ABSOLUTE RULES
=======================================================================

RULE 1 — REPOSITORY IS THE ONLY SOURCE OF TRUTH

  Inspect actual source code. Do NOT infer architecture from filenames alone.
  Do NOT trust existing documentation without verification.
  If documentation contradicts source, the source wins. Document the
  contradiction explicitly.

  For every important architectural statement, identify:
    file path | module | class/function | route | schema/model | migration
    | configuration | test | runtime dependency | actual execution path

RULE 2 — READ-ONLY FORENSICS

  This is an analysis/documentation phase. DO NOT modify any product code.
  Allowed outputs: documentation, diagrams, traceability matrices,
  evidence tables, inventories, analysis artifacts.

RULE 3 — EVIDENCE-BASED CLASSIFICATION

  Every capability must be classified as exactly one of:
    IMPLEMENTED                  — working in production code
    PARTIALLY IMPLEMENTED        — exists but incomplete
    IMPLEMENTED BUT NON-FUNCTIONAL — column/function exists, never written/called
    IMPLEMENTED BUT UNVERIFIED   — exists, no test coverage
    DOCUMENTED ONLY              — in docs, not in source
    PLANNED                      — in roadmap/todo, not in source
    MISSING                      — required, not in source or docs
    BLOCKED                      — exists but gated by external dependency
    DEPRECATED                   — in source, marked for removal
    UNKNOWN                      — cannot determine from available evidence

  Critical: "IMPLEMENTED BUT NON-FUNCTIONAL" is a distinct classification
  for features that look implemented but do not work (e.g., a column that
  exists in the schema but is never written by any code path).

RULE 4 — DATA LINEAGE IS CENTRAL

  For every significant data flow, trace the complete lineage:
    SOURCE → INGESTION → NORMALIZATION → M0 → M1 → M2 → M3 → M4 → M5
           → PERSISTENCE → RETRIEVAL → API → FRONTEND → USER

  For every transition, document:
    INPUT CONTRACT | OUTPUT CONTRACT | VALIDATION | GUARDRAIL
    | PERSISTENCE EFFECT | PROVENANCE EFFECT | FAILURE BEHAVIOR
    | MEMORY QUALITY EFFECT

RULE 5 — VERIFY, DO NOT TRUST

  Before citing any architectural claim:
    1. Find the actual source code that implements it
    2. Read the implementation (not just the signature)
    3. Trace every call path that leads to it
    4. Trace every call path that it leads to
    5. Check whether it is actually executed at runtime
    6. Check whether tests exercise it
    7. Check whether it produces the documented effect

  Common failure patterns to detect:
    • Function imported but never called
    • Column in schema but never written
    • Endpoint defined but not mounted on router
    • Middleware class defined but not added to app
    • Service method defined but never invoked
    • Configuration option set but never read
    • Test exists but always passes (no assertions)
    • Documented behavior that requires code not present
    • Dead code left from refactoring

=======================================================================
PHASE 0 — BASELINE ESTABLISHMENT
=======================================================================

Before any analysis:

  1. Identify repository root (git rev-parse --show-toplevel)
  2. Record current Git branch (git branch --show-current)
  3. Record exact HEAD SHA (git rev-parse HEAD)
  4. Record working-tree state (git status --porcelain)
  5. Record uncommitted files (git ls-files --others --exclude-standard)
  6. Record repository structure (top-level directories and key files)
  7. Identify backend root (look for FastAPI app entry point)
  8. Identify frontend root (look for package.json, Next.js config)
  9. Identify tests (pytest config, test directories, e2e config)
  10. Identify migrations (alembic directory, migration files)
  11. Identify Docker/deployment configuration (Dockerfile, docker-compose, .dockerignore)
  12. Identify configuration/environment files (.env.example, .env, config classes)
  13. Identify existing documentation (docs/ directory, README files)

  Create: docs/ARCHITECTURE_FORENSICS_BASELINE.md
    Include: exact SHA, branch, timestamp, working-tree state, uncommitted files,
    repository map, backend root, frontend root, test locations, migration count,
    deployment files, config files, existing docs inventory.

  DO NOT continue if repository identity cannot be established.

=======================================================================
PARALLEL AGENT PROGRAM
=======================================================================

Launch PARALLEL SUBAGENTS — minimum 7 specialists + 1 final synthesis agent.

Each specialist:
  • Inspects actual source code
  • Produces its own document to its assigned output file
  • Cites exact files/functions/routes/models with line numbers
  • Identifies gaps, dead code, and contradictions with existing docs
  • Distinguishes "verified from source" from "inferred from behavior"
  • Classifies every capability per Rule 3
  • Writes ONLY to its assigned output file

AGENT 1 — BACKEND RUNTIME ARCHITECTURE
  Output: docs/SWARMVAULT_BACKEND_ARCHITECTURE.md

  Analyze and document with exact citations:
    1.1 Application Startup
         • Entry point file and function
         • ASGI server configuration
         • Lifespan events (startup/shutdown)
         • Database initialization (init_db, alembic)
         • Service initialization order
         • Configuration loading

    1.2 FastAPI Application Construction
         • App instance creation (file, line)
         • Router mounting (each router, prefix, dependencies)
         • Middleware registration (order, class, configuration)
         • Exception handlers
         • OpenAPI/docs configuration (enabled/disabled per environment)
         • CORS configuration (origins, methods, headers, credentials)

    1.3 Router Inventory
         For EACH router:
           • File path and variable name
           • Prefix
           • Dependencies (auth, tenancy, rate limit)
           • Every endpoint: method, path, name, request schema, response schema
           • Mount order (FastAPI reverses middleware; document actual order)

    1.4 Service Layer
         For EACH service:
           • File path and class/function
           • Constructor dependencies
           • Public methods with signatures
           • Internal dependencies (other services, repositories)
           • Transaction boundaries
           • Error handling approach

    1.5 Repository Pattern
         • Is there a repository layer? Where?
         • How does it differ from the service layer?
         • Which models have repositories?
         • Transaction management

    1.6 ORM Models
         For EACH model:
           • Table name
           • Primary key (type, generation)
           • Columns (name, type, nullable, default, constraints)
           • Relationships (foreign keys, back-populates, cascade)
           • Indexes
           • Soft delete column (if present)
           • Timestamp columns (created_at, updated_at, deleted_at)

    1.7 Pydantic Schemas
         For EACH schema:
           • File and line
           • Fields with types and validators
           • Config classes (orm_mode, etc.)
           • Used by which endpoints

    1.8 Middleware Chain
         Document in EXECUTION ORDER (FastAPI reverses declaration):
           For each middleware:
             • Class name and file
             • Order in chain
             • What it modifies (request/response/state)
             • What it blocks/allows
             • Error handling

    1.9 Configuration
         • Settings class file and fields
         • Environment variable mapping
         • Default values
         • Environment-specific overrides
         • Secrets handling

    1.10 Dependency Injection
         • How services receive AsyncSession
         • How tenant context flows
         • How user context flows
         • How auth state is accessed
         • Singleton vs per-request scope

    1.11 Authentication
         • JWT implementation (algorithm, secret source, expiry)
         • Token creation (function, file, line)
         • Token validation (function, file, line)
         • Refresh token mechanism (storage, rotation, revocation)
         • Password hashing (algorithm, parameters)
         • API key mechanism (generation, hashing, storage, validation, expiry)
         • Session management (if any)

    1.12 Authorization
         • RBAC implementation (file, function)
         • Role hierarchy (values, inheritance)
         • Permission model (how permissions are checked)
         • PolicyEngine integration (how it's called, when)
         • Fail-closed verification (what happens on policy errors)
         • Effect types supported
         • Where authorization is enforced (router dependency, service, both)

    1.13 Tenancy
         • Tenant resolution (from JWT? header? subdomain?)
         • Workspace isolation mechanism
         • Project isolation mechanism
         • Cross-tenant prevention (how is it enforced?)
         • TenantContext data structure
         • How workspace_id propagates through the stack

    1.14 Database Access
         • Engine configuration (driver, pool size, overflow, pre-ping, recycle)
         • Session management (creation, scope, disposal)
         • Transaction boundaries (where commit/rollback occurs)
         • Connection lifecycle

    1.15 Background Processing
         • FastAPI BackgroundTasks usage
         • No Celery/RQ/Arq — document this gap
         • Any async task patterns
         • Job queue (if any)

    1.16 External Providers
         • LLM providers supported (OpenAI, Anthropic, Local/Ollama)
         • Provider selection logic
         • Fallback behavior
         • Error handling
         • Configuration per provider

    1.17 Error Handling
         • Exception handlers registered
         • Error sanitization (_sanitize_detail — what it catches, what it misses)
         • HTTPException usage patterns
         • Custom exception classes
         • Error response format

    1.18 Logging
         • Structured logging implementation
         • Log levels and configuration
         • What is logged (requests, errors, audit)
         • What is NOT logged (secrets, PII)
         • Log format (JSON?)

    1.19 Observability
         • Request ID propagation
         • Latency measurement
         • Metrics (if any)
         • Distributed tracing (if any — likely NONE)
         • Health endpoints

    1.20 Health/Readiness
         • Health check endpoint (path, what it checks)
         • Readiness check (if different)
         • Liveness check (if any)
         • Startup checks (DB migration, external service health)

    1.21 Lifecycle & Shutdown
         • Startup sequence
         • Shutdown behavior
         • Graceful shutdown (connections, tasks)
         • Signal handling

    1.22 Runtime Dependencies
         • Complete list of runtime packages
         • Version constraints
         • Purpose of each

    1.23 Request Trace
         Trace a representative request end-to-end:
           HTTP Request → Middleware → Auth → Authz → Router → Validation
           → Service → Repository → Database → Response

         Do this for at least:
           • POST /api/v1/ingest/upload (session ingestion)
           • POST /api/v1/chat/sync (chat)
           • GET /api/v1/memory/ (memory retrieval)
           • POST /api/v1/facts/ (fact creation)

=======================================================================
AGENT 2 — DATA, MEMORY & PERSISTENCE ARCHITECTURE
  Output: docs/SWARMVAULT_DATA_MEMORY_ARCHITECTURE.md

  THIS AGENT MUST TRACE EVERY DATA TRANSITION WITH FULL CONTRACTS.

  2.1 Data Model Inventory
       For EACH of the 22+ database tables:
         • Table name and file:line where defined
         • Migration that created it
         • Every column: name, type, nullable, default, constraints
         • Primary key and type
         • Foreign keys (with referential actions)
         • Unique constraints
         • Indexes (which columns, type, partial?)
         • Soft delete support
         • Timestamp columns

  2.2 Database Migrations
       • List all migrations in order
       • For each: what it creates/alters/drops
       • Any migration gaps (columns in model but not migrated?)
       • Any destructive migrations (DROPs without preservation)

  2.3 M0 — Normalization
       INPUT:  Raw content (string/dict), source_type, external context
       TRANSFORMATION: connectors.normalize() — exact logic
       OUTPUT: NormalizedConversation dataclass
       VALIDATION: source_type validation, content parsing errors
       GUARDRAIL: What prevents malformed input from passing?
       FAILURE MODE: What happens on parse failure?
       PERSISTENCE EFFECT: What is written to DB (Source record, NormalizedMessage records)?
       PROVENANCE EFFECT: What metadata is captured?
       MEMORY QUALITY EFFECT: Impact on downstream stages

  2.4 M1 — Session Understanding
       INPUT:  NormalizedMessage list
       TRANSFORMATION: m1_session.understand_session() — exact logic
       OUTPUT: SessionUnderstanding dataclass (topics, entities, intents, sentiment)
       VALIDATION: None apparent
       GUARDRAIL: None apparent
       FAILURE MODE: What happens if no topics/entities extracted?
       PERSISTENCE EFFECT: ⚠️ CRITICAL — is M1 output written to DB?
         Verify: search for SessionUnderstanding persistence in pipeline.py and api/
         If NOT persisted, document the gap explicitly with file:line evidence.
       PROVENANCE EFFECT: If not persisted, provenance is lost
       MEMORY QUALITY EFFECT: Topics/entities available only in pipeline return dict

  2.5 M2 — Fact/Decision Extraction
       INPUT:  Messages + M1 context
       TRANSFORMATION: m2_facts.run_m2() — exact regex patterns
       OUTPUT: Fact list + Decision list
       VALIDATION: Regex matching (what patterns? what do they catch/miss?)
       GUARDRAIL: Pattern-based extraction only (no LLM validation)
       FAILURE MODE: No matches = empty list; false positives from regex
       PERSISTENCE EFFECT: Facts written to Fact table; Decisions written to Decision table
       ⚠️ CRITICAL: confidence defaults to 1.0 (m2_facts.py:22-23) — is this calibrated?
       ⚠️ CRITICAL: authority defaults to 1.0 — is this calibrated?
       PROVENANCE EFFECT: source_id, session_id set; confidence/authority from extraction
       MEMORY QUALITY EFFECT: All extracted facts appear equally confident

  2.6 M3 — Temporal Supersession
       INPUT:  New facts + existing facts for same subject/predicate
       TRANSFORMATION: Inline in run_pipeline() (NOT m3_temporal.py)
       OUTPUT: Old facts marked temporal_status="historical"; new facts created
       VALIDATION: Case-insensitive comparison (existing.object.lower() != fact.object.lower())
       GUARDRAIL: Dedup by exact match (same subject+predicate+object = skip)
       FAILURE MODE: Case-sensitive dedup misses near-duplicates
       ⚠️ CRITICAL: superseded_by_id column exists on Fact/Decision models
         but is NEVER written. Verify: search for "superseded_by" in pipeline.py,
         m3_temporal.py, and all service files. Document exact finding.
       ⚠️ CRITICAL: m3_temporal.py defines supersede_fact() and supersede_decision()
         but pipeline.py imports these (line 28) and does NOT call them.
         Pipeline uses inline logic at line 117 instead.
       PERSISTENCE EFFECT: temporal_status updated; superseded_by_id NOT updated
       PROVENANCE EFFECT: Supersession chain is untraceable
       MEMORY QUALITY EFFECT: Cannot determine which fact replaced which

  2.7 M4 — Graph Construction
       INPUT:  Full conversation text
       TRANSFORMATION: m4_graph.extract_graph_elements() + persist_graph()
       OUTPUT: GraphNode list + GraphEdge list
       VALIDATION: Entity/relationship extraction patterns
       GUARDRAIL: None apparent beyond pattern matching
       FAILURE MODE: No entities = empty graph; false entity matches
       PERSISTENCE EFFECT: Nodes and edges written to DB
       ⚠️ CRITICAL: GraphNode has no confidence column
       ⚠️ CRITICAL: GraphNode has no source_id column
       ⚠️ CRITICAL: GraphEdge has no confidence column
       PROVENANCE EFFECT: No per-node provenance; graph edges lack source tracking
       MEMORY QUALITY EFFECT: Graph quality cannot be assessed

  2.8 M5 — Retrieval
       INPUT:  Query string + scope filters + (optionally) query_embedding
       TRANSFORMATION: m5_retrieval.retrieve_hybrid() or retrieval.py
       OUTPUT: Ranked list of RetrievalResult
       VALIDATION: Query parsing
       GUARDRAIL: Workspace/project filtering
       FAILURE MODE:
         ⚠️ CRITICAL: Vector search is NON-FUNCTIONAL
           - Fact/Decision/Memory models have NO embedding column
           - Memory.embedding is JSON, nullable=True, NEVER populated
           - retrieval.py checks query_embedding parameter but no provider supplies it
           - M5 claims to "generate embeddings" but no generation code exists
       PERSISTENCE EFFECT: No indexing step — M5 is query-time only
       PROVENANCE EFFECT: Score factors logged in RetrievalResult.factors
       MEMORY QUALITY EFFECT: Scoring relies on BM25 + recency + graph context

  2.9 Memory Records (MemoryRecord vs Memory Model)
       ⚠️ CRITICAL GAP: Two different memory representations exist:
         • MemoryRecord (dataclass in services/memory.py) — canonical form
           with: memory_id, memory_type, scope, tenant hierarchy, subject,
           predicate, value, content, authority, confidence, importance,
           timestamps, version, supersedes, superseded_by, provenance,
           permissions, status, user_metadata
         • Memory (ORM model in models.py) — database form
           with: id, memory_id, workspace_id, project_id, user_id, content,
           memory_type (default "procedural_memory"), scope (default "session"),
           confidence (default 0.7), importance (default 0.5), extra_metadata,
           embedding (JSON, nullable), deleted_at, created_at, updated_at

       ⚠️ CRITICAL: MemoryTypeMapper maps canonical types to DB types
         CANONICAL_TO_VAULT = {"WORKING": "working", "EPISODIC": "episodic",
         "SEMANTIC": "semantic", "PROCEDURAL": "procedural", ...}
         But DB default is "procedural_memory" and schema default is "procedural_memory"
         Mismatch: MemoryRecord defaults to "WORKING" → mapper → "working"
         But DB creates with default "procedural_memory" (no mapper applied)

       ⚠️ CRITICAL: _persist_record() in services/memory.py LOSES these fields:
         scope, team_id, valid_from, valid_until, expires_at, version,
         supersedes, superseded_by, provenance, permissions, subject (partial)

  2.10 Provenance Architecture
        • MessageProvenance table: every assistant message linked to memories,
          model, provider, parameters, token counts, latency
        • Memory provenance: stored as JSON in Memory.extra_metadata
        • Source provenance: Source table with content_hash, external_id
        • Provenance chain: Is it actually chain-like or just snapshots?
        • Audit events: AuditEvent table, append-only

  2.11 Temporal Architecture
        • temporal_status values: current, historical, superseded, archived
        • Where temporal_status is set
        • Where temporal_status transitions occur
        • GraphNode has temporal_status column — is it ever transitioned?
        • Supersession: superseded_by_id column — is it ever written?

  2.12 Confidence & Authority
        • Where confidence is set (defaults, calculations)
        • Where authority is set (defaults, sources)
        • Are they calibrated? (Likely NOT — defaults are hardcoded)
        • Range validation (0.0-1.0?)

  2.13 Soft Deletion
        • Which tables support soft delete (deleted_at column)?
        • Which queries filter deleted_at IS NULL?
        • Which queries might return soft-deleted rows?
        • Cascade behavior on delete

  2.14 Audit Architecture
        • AuditEvent model (columns, triggers)
        • AuditService implementation
        • What events are emitted (list with file:line)
        • What events are defined but NOT emitted
        • Audit sinks (DB, file, external)
        • Audit event redaction
        • Retention policy

  2.15 Serialization
        • ORM model → API schema mapping
        • JSON serialization of complex fields (extra_metadata, authority, provenance)
        • Datetime serialization
        • UUID serialization

  2.16 Data Lineage Diagram
        Complete trace:
          Raw Input → Ingestion → Normalization → M0 → M1 → M2 → M3 → M4
          → M5 → Persistence → Retrieval → API → Frontend → User

        For each arrow document: input, transformation, output, guardrail,
        persistence effect, provenance effect, failure mode.

=======================================================================
AGENT 3 — PIPELINE, GUARDRAIL & VALIDATION ARCHITECTURE
  Output: docs/SWARMVAULT_GUARDRAILS_VALIDATION_ARCHITECTURE.md

  THIS AGENT MUST BUILD A COMPLETE MATRIX AND VERIFY EVERY CONTROL FROM SOURCE.

  3.1 Complete Guardrail Matrix

      Build a table with these columns for EVERY stage:
      | Stage | Control | Input | Output | Validation | Guardrail | Failure Mode | Enforcement Point | Bypass Possible? | Status |

      Stages to cover:
        HTTP Request | Auth | Authz | Tenancy | Body Validation | Content Validation
        | Source Validation | M0 Normalization | M1 Analysis | M2 Extraction
        | M3 Temporal | M4 Graph | M5 Retrieval | Memory CRUD | Fact CRUD
        | Decision CRUD | Graph CRUD | Ingestion CRUD | Persistence | Retrieval
        | Output Serialization | Error Handling

      For each control, determine status:
        ACTIVE | PARTIAL | DOCUMENTED | MISSING | BYPASSABLE | UNTESTED

  3.2 Authentication Guardrails
      • JWT decode validation (signature, expiry, algorithm)
      • User active status check
      • Refresh token validation and rotation
      • API key validation (hash comparison, expiry)
      • Token refresh flow (is it automatic?)

  3.3 Authorization Guardrails
      • RBAC enforcement (where, how)
      • PolicyEngine evaluation (fail-closed?)
      • Workspace membership check
      • Project membership check
      • Resource ownership check
      • Effect handling (ALLOW, DENY, REDACT, AUDIT_ONLY)

  3.4 Tenancy Guardrails
      • Tenant resolution (JWT vs header)
      • Workspace isolation (every query filters by workspace_id?)
      • Project isolation (every query filters by project_id?)
      • Cross-tenant prevention (verified in every endpoint?)

  3.5 Validation Guardrails
      • Pydantic schema validation (all request bodies)
      • Custom validators (what custom validation exists?)
      • Content length limits
      • Character encoding
      • Null byte detection
      • Source type validation (allowed values?)

  3.6 Ingestion Guardrails
      • File type validation (JSON, JSONL, etc.)
      • File size limits
      • JSON parsing error handling
      • Content hash dedup (is it working?)
      • Duplicate detection (per workspace?)

  3.7 Content Guardrails
      • PII redaction (is there any?)
      • Toxic content detection (is there any?)
      • Length limits per message
      • Character set validation

  3.8 Memory Guardrails
      • Memory type validation (allowed values?)
      • Scope validation
      • Required fields enforcement
      • Confidence range validation (0.0-1.0?)
      • Authority range validation
      • Temporal status transition rules

  3.9 Temporal Guardrails
      • Date format validation
      • Temporal status transition rules (can "current" → "historical"? can "historical" → "current"?)
      • Expiry handling
      • Supersession chain integrity

  3.10 Graph Guardrails
      • Node/edge constraint validation
      • Self-reference prevention
      • Duplicate edge prevention
      • Orphaned node cleanup

  3.11 Deduplication Guardrails
      • Content hash uniqueness (DB constraint)
      • Subject-predicate matching (M3 inline logic)
      • Cross-batch dedup
      • Case sensitivity (current code uses .lower())

  3.12 Provenance Guardrails
      • source_id requirement
      • Provenance chain validation
      • Immutability of provenance records

  3.13 Persistence Guardrails
      • Transaction boundaries
      • Rollback on failure
      • Flush vs commit strategy
      • Connection pool exhaustion handling

  3.14 Retrieval Guardrails
      • Workspace filtering (always applied?)
      • Temporal status filtering (current only? or all?)
      • Soft-delete filtering
      • Result limit enforcement
      • Score threshold (is there a minimum score filter?)

  3.15 Security Guardrails
      • Rate limiting (per-route, per-key, bypass conditions)
      • CORS (origins, methods, headers)
      • Security headers (CSP, HSTS, X-Frame-Options, etc.)
      • Error sanitization (PII, tokens, paths, stack traces)
      • Secret handling (API keys, JWT secrets, DB URLs)

  3.16 Error Handling Guardrails
      • Exception handler coverage
      • Error message sanitization
      • Stack trace exposure
      • Database error exposure

=======================================================================
AGENT 4 — API / CONTRACT / INTEGRATION ARCHITECTURE
  Output: docs/SWARMVAULT_API_INTEGRATION_ARCHITECTURE.md

  4.1 Complete API Inventory
       For EVERY endpoint:
         • Route path and method
         • Request schema (Pydantic model)
         • Response schema (Pydantic model)
         • Authentication requirement
         • Authorization requirement (RBAC role, PolicyEngine)
         • Tenancy scope (workspace, project, or global)
         • Rate limit rule (if any)
         • Success status codes
         • Error status codes

  4.2 API Response Format
       • Standard envelope (is there one?)
       • Error format
       • Pagination format (cursor? offset?)
       • Filtering format (query params, body?)
       • SSE format (event types, data schema)

  4.3 API Versioning
       • Version strategy
       • Current version
         • Deprecation policy

  4.4 SSE / Streaming
       • Chat streaming endpoint
       • Event types
       • Connection lifecycle
       • Error handling in stream
       • Client abort handling

  4.5 Integration Analysis
       For EACH integration, determine status with source evidence:

       CLAUDE CODE INTEGRATION:
         • Code paths (files, functions)
         • Request/response format
         • Authentication
         • Status: IMPLEMENTED / PARTIAL / DOCUMENTED / PLANNED / MISSING

       CODEX INTEGRATION:
         • Same analysis
         • Status with evidence

       UNIVERSAL ADAPTER:
         • Same analysis
         • Status with evidence

       MCP SERVER:
         • Same analysis
         • Status with evidence

       REST API:
         • Same analysis
         • Status: likely IMPLEMENTED

       SSE STREAMING:
         • Same analysis
         • Status: likely IMPLEMENTED

       EXTERNAL LLM PROVIDERS:
         • OpenAI: code paths, configuration
         • Anthropic: code paths, configuration
         • Local/Ollama: code paths, configuration

  4.6 API Client (Frontend Side)
       • API client implementation (file, functions)
       • Token handling (storage, refresh, 401 retry)
       • Error handling
       • Request/response interceptors
       • SSE client implementation

  4.7 API Security
       • Authentication enforcement per endpoint
       • Authorization enforcement per endpoint
       • Rate limiting per endpoint
       • Input validation per endpoint
       • Output sanitization per endpoint

=======================================================================
AGENT 5 — FRONTEND ARCHITECTURE
  Output: docs/SWARMVAULT_FRONTEND_ARCHITECTURE.md

  5.1 Next.js Architecture
       • Version (from package.json)
       • App Router vs Pages Router
       • Route structure (every route file)
       • Layout hierarchy (root layout, nested layouts)
       • Metadata handling
       • Image optimization

  5.2 Component Architecture
       • Component tree from root to leaves
       • UI primitives (buttons, inputs, cards, etc.)
       • Component library (custom, shadcn, MUI, etc.)
       • Component naming conventions

  5.3 State Management
       • No Redux/Zustand/Jotai — document how state IS managed
       • React hooks usage (useState, useContext, useReducer)
       • Server state (React Query? SWR? fetch?)
       • URL state (search params, router state)
       • Local state patterns

  5.4 API Client
       • API client file and functions
       • Base URL configuration
       • Token storage (localStorage? sessionStorage? cookie?)
       • Token refresh flow
       • 401 handling (logout? redirect?)
       • Error handling
       • Request cancellation
       • SSE client (if any)

  5.5 Authentication Flow
       • Login page and flow
       • Registration page and flow
       • Token storage mechanism
       • Token refresh mechanism
       • Logout flow
       • Protected route handling
       • Session persistence (page refresh)

  5.6 Error Handling
       • Global error boundary
       • Per-page error handling
       • API error display
       • Network error handling
       • Fallback UI

  5.7 Loading States
       • Global loading indicators
       • Per-page loading states
       • Skeleton screens
       • Spinners

  5.8 Knowledge Views
       For EACH view:
         • Route path
         • Page component
         • Data fetching (API calls, parameters)
         • State management
         • Display format
         • Empty state
         • Error state
         • Interactions (create, edit, delete, filter, sort)

       Views to cover:
         Dashboard | Projects | Chat | Sessions | Memory | Facts
         | Decisions | Timeline | Search | Graph | Provenance
         | Ingestion | Storage | API Keys | Settings

  5.9 Frontend ↔ Backend Contract Matrix
       FRONTEND ROUTE → COMPONENT → STATE → API CALL → BACKEND ROUTE
       → SERVICE → DATABASE MODEL → RESPONSE → UI RENDERING

  5.10 Frontend/Backend Mismatches
       Identify where frontend expects data that backend:
         • Does not provide
         • Provides in different format
         • Provides with different field names
         • Does not validate

  5.11 Security
       • XSS prevention (React auto-escaping, dangerouslySetInnerHTML usage)
       • Token storage security
       • CSRF protection
       • Content Security Policy compliance
       • Sensitive data in localStorage

=======================================================================
AGENT 6 — SECURITY, TENANCY & OPERATIONAL ARCHITECTURE
  Output: docs/SWARMVAULT_SECURITY_OPERATIONAL_ARCHITECTURE.md

  6.1 Security Controls Matrix
      For EACH control:
        CONTROL | LOCATION | ENFORCEMENT POINT | TEST | FAILURE BEHAVIOR | BYPASS RISK

  6.2 Authentication
      • JWT implementation (algorithm, secret, expiry)
      • Password hashing (algorithm, parameters)
      • Refresh token mechanism (storage, rotation, revocation)
      • API key mechanism (generation, hashing, storage, lifecycle)
      • Session management

  6.3 Authorization
      • RBAC implementation and enforcement
      • PolicyEngine integration
      • Fail-closed behavior (verified in code)
      • Effect types and handling
      • Where authorization is checked (every endpoint?)

  6.4 Tenancy Isolation
      • Tenant resolution mechanism
      • Workspace isolation enforcement
      • Project isolation enforcement
      • Cross-tenant access prevention (verified in code)
      • Multi-workspace user handling

  6.5 API Key Security
      • Key generation (randomness, length)
      • Key hashing (algorithm)
      • Key storage (hashed only?)
      • Key prefix display (once only?)
      • Key expiry and revocation
      • Key scoping (which resources can be accessed)

  6.6 Secret Handling
      • Environment variable configuration
      • Secret rotation support
      • Secret redaction in logs
      • Secret redaction in errors
      • Secret exposure risks

  6.7 CORS
      • Allowed origins
      • Allowed methods
      • Allowed headers
      • Credentials support
      • Preflight handling

  6.8 Content Security Policy
      • Directives (document each one)
      • Production vs development differences
      • Missing directives
      • Inline style/script allowances
      • Report-uri / report-to

  6.9 Security Headers
      • X-Content-Type-Options
      • X-Frame-Options
      • X-XSS-Protection
      • Referrer-Policy
      • Permissions-Policy
      • Strict-Transport-Security (production only?)
      • Missing headers (e.g., X-Permitted-Cross-Domain-Policies)

  6.10 Rate Limiting
      • Implementation (in-memory, Redis?)
      • Rules (per path, per key type)
      • Window and limit values
      • Bypass conditions (X-E2E header, testing flag)
      • Production vs non-production behavior

  6.11 Error Sanitization
      • PII redaction
      • Token/secret redaction
      • Path redaction
      • Stack trace exposure
      • Database error exposure

  6.12 Audit
      • AuditEvent model
      • Events emitted (complete list with file:line)
      • Events defined but NOT emitted
      • Audit sinks
      • Redaction
      • Retention

  6.13 Database Security
      • Connection security (SSL?)
      • Parameterization (SQL injection prevention)
      • Connection pooling
      • Credential storage

  6.14 Docker Security
      • Base image
      • Non-root user
      • Multi-stage build
      • Capabilities
      • Secrets handling

  6.15 Environment Configuration
      • Environment variable documentation
      • Default values
      • Secret management
      • Configuration validation

  6.16 Migrations
      • Migration framework (Alembic)
      • Migration execution (startup, manual)
      • Rollback capability
      • Migration testing

  6.17 Startup Sequence
      • Order of initialization
      • Health checks during startup
      • Failure behavior

  6.18 Logging
      • Structured logging
      • Log levels
      • What is logged
      • What is NOT logged
      • Log format

  6.19 Observability
      • Metrics
      • Distributed tracing
      • Request tracking
      • Health endpoints

  6.20 Failure & Recovery
      • Timeout configuration
      • Retry logic
      • Circuit breakers (are there any?)
      • Graceful degradation
      • Backup/restore strategy

=======================================================================
AGENT 7 — MEMORY INTELLIGENCE READINESS ARCHITECTURE
  Output: docs/SWARMVAULT_MEMORY_INTELLIGENCE_READINESS.md

  THIS IS THE MOST IMPORTANT SPECIALIST.

  Determine readiness for:
    A. Persistent memory (can data survive beyond session?)
    B. Long-term memory (can data survive months/years?)
    C. Memory intelligence (can data support reasoning?)
    D. Reasoning over memory (can a layer query and infer?)
    E. Future autonomous memory operations (can a layer create/update/delete safely?)

  DO NOT redesign. Document what exists and what prevents readiness.

  7.1 Memory Object Analysis
       For EACH memory object type, evaluate across ALL dimensions:

       | Dimension | Fact | Decision | Memory | GraphNode | GraphEdge | Session | Message |
       |-----------|------|----------|--------|-----------|-----------|---------|---------|
       | IDENTITY | | | | | | | |
       | SOURCE | | | | | | | |
       | TIME | | | | | | | |
       | CONTEXT | | | | | | | |
       | CONFIDENCE | | | | | | | |
       | AUTHORITY | | | | | | | |
       | PROVENANCE | | | | | | | |
       | RELATIONSHIPS | | | | | | | |
       | SUPERSESSION | | | | | | | |
       | CONTRADICTION | | | | | | | |
       | SCOPE | | | | | | | |
       | LIFECYCLE | | | | | | | |
       | RETRIEVAL | | | | | | | |
       | AUDITABILITY | | | | | | | |

       For each cell: READY | PARTIAL | MISSING with evidence

  7.2 Data Quality Assessment
       • What data is currently persistent? (list tables)
       • What data is ephemeral? (M1 output — verify!)
       • What data is normalized? (M0 output)
       • What data has provenance? (provenance chain)
       • What data has temporal semantics? (temporal_status)
       • What data has confidence? (confidence column)
       • What data has authority? (authority column/field)
       • What data has identity? (UUIDs)
       • What data has scope? (workspace/project/tenant)
       • What data can be superseded? (superseded_by_id — verify if writable)
       • What data can be contradicted? (contradiction tracking)
       • What data can be deleted? (soft delete)
       • What data can be retrieved? (search, retrieval)
       • What data can be explained? (provenance chain)
       • What data is safe for future memory intelligence?

  7.3 Memory Readiness Scorecard
       For each capability:
       | Capability | Ready | Partial | Missing | Evidence |

  7.4 Persistent Memory Readiness
       Can the current system support persistent memory?
       • What exists
       • What is missing
       • What blocks it

  7.5 Memory Intelligence Readiness
       Can a future intelligence layer safely consume this data?
       • What can it trust TODAY
       • What it must NOT assume
       • What contracts must exist first

  7.6 Intelligence Layer Boundary
       Define the boundary:
       WHAT THE CURRENT SYSTEM CAN SAFELY PROVIDE
       WHAT THE NEXT LAYER CAN TRUST
       WHAT THE NEXT LAYER MUST NOT ASSUME
       WHAT CONTRACTS MUST EXIST BEFORE IMPLEMENTATION

  7.7 Required Prerequisites
       List what must be implemented before memory intelligence is viable:
       P0: Must have before any intelligence
       P1: Should have for reliable intelligence
       P2: Nice to have for advanced intelligence

=======================================================================
CROSS-AGENT REQUIREMENT — DATA LINEAGE
=======================================================================

Every specialist must include a data lineage section tracing relevant
data through the system:

  SOURCE
   ↓
  INGESTION
   ↓
  NORMALIZATION
   ↓
  M0
   ↓
  M1
   ↓
  M2
   ↓
  M3
   ↓
  M4
   ↓
  M5
   ↓
  PERSISTENCE
   ↓
  RETRIEVAL
   ↓
  API
   ↓
  FRONTEND
   ↓
  USER

For every transition, document:
  input contract | output contract | validation | guardrail
  | persistence effect | provenance effect | failure behavior

=======================================================================
FINAL SYNTHESIS AGENT
=======================================================================

After all 7 specialists complete, launch the Synthesis Agent.

It must:
  1. Read all 7 specialist documents
  2. Read actual backend source code
  3. Read actual frontend source code
  4. Read database migrations
  5. Read tests
  6. Verify every specialist claim against source code
  7. Reconcile contradictions between specialists
  8. Identify claims that are wrong (even within specialists)

  The synthesis agent must NOT blindly merge specialist documents.
  It must be an independent verification pass.

=======================================================================
FINAL OUTPUT — 8 DOCUMENTS
=======================================================================

DOC 1: docs/SWARMVAULT_WEBAPP_MASTER_ARCHITECTURE.md
  Authoritative architecture document with these sections:
    1. Executive Summary
    2. Product Boundary
    3. System Context
    4. Architectural Principles
    5. High-Level Architecture
    6. Backend Architecture
    7. Frontend Architecture
    8. API Architecture
    9. Data Architecture
    10. Memory Architecture
    11. Storage Architecture
    12. Security Architecture
    13. Tenancy Architecture
    14. Pipeline Architecture
    15. M0–M5 Architecture
    16. Guardrail Architecture
    17. Validation Architecture
    18. Provenance Architecture
    19. Audit Architecture
    20. Retrieval Architecture
    21. SSE/Streaming Architecture
    22. Ingestion Architecture
    23. Integration Architecture
    24. Deployment Architecture
    25. Failure & Recovery Architecture
    26. Observability Architecture
    27. Test Architecture
    28. Current Limitations
    29. Technical Debt
    30. Future Memory Intelligence Boundary
    31. Architectural Readiness Assessment

DOC 2: docs/SWARMVAULT_END_TO_END_FLOWS.md
  For each flow:
    Trigger | Input | Validation | Guardrails | Processing Steps
    | Persistence | Output | Failure Behavior | Security Boundary

  Flows:
    FLOW-001 User Registration
    FLOW-002 Login
    FLOW-003 Token Refresh
    FLOW-004 Workspace Creation
    FLOW-005 Project Creation
    FLOW-006 Session Ingestion (text)
    FLOW-007 JSON Ingestion
    FLOW-008 JSONL Ingestion
    FLOW-009 URL Fetch Ingestion
    FLOW-010 M0 Normalization
    FLOW-011 M1 Session Understanding
    FLOW-012 M2 Fact Extraction
    FLOW-013 M3 Temporal Supersession
    FLOW-014 M4 Graph Construction
    FLOW-015 M5 Retrieval
    FLOW-016 Persistent Memory Creation
    FLOW-017 Memory Retrieval
    FLOW-018 Search
    FLOW-019 Chat (Sync)
    FLOW-020 Chat (SSE Streaming)
    FLOW-021 Provenance Lookup
    FLOW-022 Graph Exploration
    FLOW-023 Memory Deletion
    FLOW-024 Supersession
    FLOW-025 Audit Trail
    FLOW-026 API Key Creation
    FLOW-027 External Agent Integration (if any)

DOC 3: docs/SWARMVAULT_GUARDRAIL_MASTER_MATRIX.md
  Complete guardrail matrix:
    Stage | Control | Implementation | Enforcement Point | Validation
    | Test | Failure Mode | Bypass Possibility | Severity | Current Status

  Plus: MEMORY SAFETY GATE MATRIX
    Which conditions must be satisfied before information becomes persistent memory?
    Condition | Current State | Blocks Memory? | Blocks Intelligence?

DOC 4: docs/SWARMVAULT_PERSISTENT_MEMORY_READINESS.md
  For each of the 15 questions:
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

  Each answered with GREEN / YELLOW / RED and evidence.

DOC 5: docs/SWARMVAULT_FRONTEND_BACKEND_ARCHITECTURE.md
  For every frontend screen:
    Screen | Route | Component | State | API Call | Backend Route
    | Service | DB Model | Response | UI Rendering

  Include: authentication, dashboard, projects, chat, sessions, memory,
  facts, decisions, timeline, search, graph, provenance, ingestion,
  storage, API keys, settings.

  Plus: frontend/backend mismatches table.

DOC 6: docs/SWARMVAULT_ARCHITECTURAL_TRACEABILITY.md
  For each major capability:
    REQUIREMENT → FEATURE → FRONTEND → API → SERVICE → DATA MODEL
    → PIPELINE → GUARDRAIL → TEST → PERSISTENCE → PROVENANCE

DOC 7: docs/SWARMVAULT_ARCHITECTURAL_GAPS_AND_MEMORY_NEXT_LAYER.md
  Gaps organized P0/P1/P2/P3:
    CURRENT STATE → RISK → EVIDENCE → IMPACT → REQUIRED CONDITION
    → BLOCKS PERSISTENT MEMORY? → BLOCKS MEMORY INTELLIGENCE?

  Plus: NEXT MEMORY INTELLIGENCE LAYER — READINESS BOUNDARY
    WHAT THE CURRENT SYSTEM CAN SAFELY PROVIDE
    WHAT THE NEXT LAYER CAN TRUST
    WHAT THE NEXT LAYER MUST NOT ASSUME
    WHAT CONTRACTS MUST EXIST BEFORE IMPLEMENTATION

DOC 8: docs/SWARMVAULT_ARCHITECTURE_INDEX.md
  Master index of all documents with:
    • Document list with descriptions
    • Cross-reference table
    • Reading order recommendations
    • Quick reference by topic

=======================================================================
EXECUTION NOTES
=======================================================================

• Run specialists IN PARALLEL — do NOT wait for one to finish before starting another.
• The synthesis agent runs ONLY after all 7 specialists complete.
• Every finding must have a file:line citation.
• Distinguish "verified from source" from "inferred from behavior."
• Document dead code, unused columns, and unimplemented features.
• Flag anything that looks implemented but is actually non-functional.
• When you find a contradiction between existing docs and source, document it.
• When you find a contradiction between specialists, the synthesis agent resolves it.
• Do NOT silently correct documentation errors — document them as findings.
```

---

## How This Improved Prompt Addresses the Original's Weaknesses

### 1. Verification Protocol (NEW)
The original prompt trusted existing docs. This version mandates source verification for every claim, with explicit instructions to detect:
- Functions imported but never called
- Columns that exist but are never written
- Endpoints defined but not mounted
- Middleware classes defined but not registered
- Configuration options set but never read

### 2. Granularity — Every Model, Every Endpoint, Every Guardrail
The original listed topics broadly. This version requires:
- Every column in every model with type, nullable, default, constraints
- Every endpoint with request/response schemas, auth, authz, tenancy
- Every guardrail with status (ACTIVE/PARTIAL/MISSING/BYPASSABLE/UNTESTED)
- Every middleware in execution order (not declaration order)

### 3. Frontend Depth (Dramatically Enhanced)
The original had ~10 lines for frontend. This version covers:
- Complete route structure
- Component hierarchy
- State management patterns (no global store)
- API client with token handling
- Every knowledge view with data flow
- Frontend/backend contract matrix
- Mismatch identification

### 4. Data Lineage Per Stage
The original mentioned data lineage. This version requires per-stage documentation:
- INPUT, TRANSFORMATION, OUTPUT, VALIDATION, GUARDRAIL, FAILURE MODE
- PERSISTENCE EFFECT, PROVENANCE EFFECT, MEMORY QUALITY EFFECT

### 5. Specific Checks for Non-Functional Features
The original could miss "implemented but broken" features. This version explicitly requires checking:
- superseded_by_id column existence vs actual writes
- Memory.embedding column existence vs actual population
- M1 output "persistence" vs actual DB writes
- m3_temporal.py function calls vs actual usage

### 6. Classification Precision
Added `IMPLEMENTED BUT NON-FUNCTIONAL` — critical for features like:
- Vector search (endpoint exists, embedding column exists, but no embeddings are ever generated)
- Supersession (column exists, but never written)

### 7. Frontend/Backend Contract Matrix
The original didn't require tracing frontend screens to backend. This version mandates:
```
FRONTEND ROUTE → COMPONENT → STATE → API CALL → BACKEND ROUTE
→ SERVICE → DATABASE MODEL → RESPONSE → UI RENDERING
```

### 8. Memory Intelligence Boundary (More Specific)
The original asked "is the system ready?" This version requires:
- Per-dimension scoring for every memory object type
- Green/Yellow/Red classification for each of 15 questions
- Explicit boundary definition: what can be trusted, what must not be assumed
- Required contracts before implementation

### 9. End-to-End Flow Coverage
Expanded from 25 to 27 flows, adding:
- FLOW-003 Token Refresh
- FLOW-008 URL Fetch Ingestion
- FLOW-027 External Agent Integration

### 10. Test Architecture Section
The original didn't require test analysis. The synthesis agent must now cover:
- Test framework and configuration
- Test coverage (what is tested, what is not)
- Test quality (meaningful assertions vs. passing tests)
