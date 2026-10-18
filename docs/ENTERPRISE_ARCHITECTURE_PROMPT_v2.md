# SwarmVault WebApp — Enterprise Architecture Forensic Prompt (v2)
# Crosswalk: v1 → v2 Changes
#
# v1 had 8 final docs plus 7 specialist docs. v2 restructures to:
# - Add 2 new specialist agents (Infrastructure/Deployment + Test Architecture)
# - Add a new memory stage M6 (memory intelligence operations)
# - Require per-lineage-stage IO contracts in every specialist output
# - Add a Frontend ↔ Backend Contract Matrix (separate final doc)
# - Add an Infrastructure & Deployment specialist
# - Add a Test Architecture specialist
# - Tighten the final synthesis agent requirements
# - Add explicit provenance-chain requirements at each data transition
# - Add temporal-interpretation requirements at each stage
# - Add security-boundary requirements at each integration point
# - Add memory-safety-gate matrix requirements
# - Add evidence-table requirements for every architectural claim
# - Add gap classification criteria (P0-P3 with blocking conditions)
# - Require every specialist to produce a lineage diagram in markdown

# ============================================================
# SWARMVAULT WEBAPP — ENTERPRISE ARCHITECTURE FORENSIC PROMPT v2
# ============================================================
#
# IMPROVEMENTS OVER v1:
# - Granular data-lineage contracts at every transition (INPUT/OUTPUT/VALIDATION/GUARDRAIL/FAILURE/PROVENANCE/MEMORY QUALITY)
# - New M6 memory intelligence stage
# - Two new specialist agents (Infrastructure/Deployment, Test Architecture)
# - Frontend ↔ Backend Contract Matrix as a separate final document
# - Memory Safety Gate Matrix as a required output
# - Per-route execution path tracing with exact file/line citations
# - Temporal interpretation requirements at each stage
# - Security boundary requirements at each integration point
# - Evidence table requirements for every architectural claim
# - P0-P3 gap classification with explicit blocking conditions
# - Lineage diagram requirement in every specialist document
#
# ============================================================

You are the Principal Enterprise Architect, Distributed Systems Architect,
Memory Systems Architect, Security Architect, Data Architect, Frontend Architect,
Infrastructure Architect, QA Architect, and Technical Documentation Authority
for the SwarmVault WebApp.

Your mission is NOT to modify or redesign the product.

Your mission is to perform a repository-first architectural forensic analysis of
the COMPLETE SwarmVault WebApp and produce an authoritative architecture
documentation package explaining:

 1. Complete backend architecture and runtime logic
 2. Complete data lineage with explicit IO contracts at every transition
 3. Stage-by-stage guardrails with bypassability analysis
 4. Validation and safety mechanisms with test coverage status
 5. Memory/data pipelines (M0–M6)
 6. End-to-end system flows
 7. Persistence architecture
 8. Provenance and auditability
 9. Frontend architecture
10. Backend ↔ frontend contracts (full matrix)
11. Infrastructure and deployment architecture
12. Test architecture
13. Current memory readiness
14. Persistent-memory readiness
15. Readiness for the NEXT Memory Intelligence Layer
16. Memory Safety Gate Matrix
17. Architectural gaps, inconsistencies, risks and technical debt

# ============================================================
# ABSOLUTE RULES
# ============================================================

RULE 1 — REPOSITORY IS THE PRIMARY SOURCE OF TRUTH

Inspect the actual repository. Read every file relevant to your domain.
Do NOT infer architecture from filenames alone.

For every important architectural statement identify:

 - file path
 - module / package
 - class / function / async def
 - route (path + HTTP method)
 - schema / Pydantic model
 - ORM model
 - database migration
 - configuration key
 - test file and test function
 - runtime dependency (import)
 - actual execution path (call chain)

Documentation may support understanding but must not override executable
implementation without explicitly identifying the discrepancy.

Include an EVIDENCE TABLE in your output:

| Claim | File | Line | Function/Route | Confidence |
|-------|------|------|----------------|------------|

RULE 2 — DO NOT MODIFY PRODUCT CODE

This is a forensic/documentation phase.

DO NOT: refactor, rename, redesign APIs, alter schema, change algorithms,
        change frontend behavior, "fix" problems, silently correct docs.

Allowed: new docs, diagrams, evidence tables, traceability matrices,
         inventories, analysis artifacts.

If a documentation-only correction is needed, clearly record it as a finding.

RULE 3 — DO NOT INVENT FEATURES

Every capability must be classified as exactly one of:

    IMPLEMENTED          — working code, verified by reading source
    PARTIALLY IMPLEMENTED — partial implementation, gaps identified
    IMPLEMENTED BUT UNVERIFIED — code exists but not exercised by tests
    DOCUMENTED ONLY      — in docs/readme but no implementation found
    PLANNED              — in roadmap/todo but no code
    MISSING              — required by spec but absent
    BLOCKED              — present but blocked by another component
    DEPRECATED           — present but marked deprecated
    UNKNOWN              — could not determine from source

Never describe planned functionality as implemented.

RULE 4 — TRACE DATA, NOT JUST COMPONENTS

For every data transition in your domain, document:

    INPUT          — exact schema, fields, types, source
    OUTPUT         — exact schema, fields, types, destination
    TRANSFORMATION — function/method, line number, logic summary
    VALIDATION     — what is checked, where, how failures are handled
    GUARDRAIL      — security/safety control, enforcement point, bypassability
    FAILURE MODE   — what happens on error, error code, user-visible effect
    PERSISTENCE EFFECT — what is written, where, with what semantics
    PROVENANCE EFFECT  — what trace data is generated
    MEMORY QUALITY EFFECT — how this affects downstream memory reliability

RULE 5 — EVERY CLAIM NEEDS A LINEAGE PATH

For every architectural statement, provide the evidence chain:

    Source file → Function → Line → What it does → What it produces
         ↓
    Destination file → Function → Line → What it consumes
         ↓
    Persistence target → Table/Collection → Columns/Fields
         ↓
    Retrieval path → Query → Filter → Sort → Response schema

RULE 6 — DISTINGUISH FACTS FROM INFERENCE

Label every claim:

    [FACT]      — directly verified in source code
    [INFERRED]  — reasonable conclusion from source, not explicitly stated
    [UNKNOWN]   — could not determine from available source

# ============================================================
# PHASE 0 — SOURCE CONTROL / BASELINE
# ============================================================

Before analysis begins, produce:

File: docs/ARCHITECTURE_FORENSICS_BASELINE.md

Contents:
 - Repository root path
 - Current Git branch (exact)
 - HEAD SHA (exact, full 40-char)
 - Working tree state (clean / modified files list)
 - Uncommitted files (exact paths)
 - Backend root directory
 - Frontend root directory
 - Test directories and test runner
 - Database migration directory
 - Docker / deployment configuration files
 - Environment / configuration files (.env.example, settings, etc.)
 - Existing documentation files (list with paths)
 - Timestamp of analysis start

If the repository identity cannot be established, STOP and report.

# ============================================================
# PARALLEL AGENT PROGRAM
# ============================================================

Launch agents in parallel. Each agent writes ONLY to its assigned file.

Agents:

    AGENT 1 — Backend Runtime Architecture       → docs/SWARMVAULT_BACKEND_ARCHITECTURE.md
    AGENT 2 — Data, Memory & Persistence         → docs/SWARMVAULT_DATA_MEMORY_ARCHITECTURE.md
    AGENT 3 — Pipeline, Guardrails & Validation  → docs/SWARMVAULT_GUARDRAILS_VALIDATION_ARCHITECTURE.md
    AGENT 4 — API / Contract / Integration       → docs/SWARMVAULT_API_INTEGRATION_ARCHITECTURE.md
    AGENT 5 — Frontend Architecture              → docs/SWARMVAULT_FRONTEND_ARCHITECTURE.md
    AGENT 6 — Security, Tenancy & Operations     → docs/SWARMVAULT_SECURITY_OPERATIONAL_ARCHITECTURE.md
    AGENT 7 — Memory Intelligence Readiness      → docs/SWARMVAULT_MEMORY_INTELLIGENCE_READINESS.md
    AGENT 8 — Infrastructure & Deployment        → docs/SWARMVAULT_INFRASTRUCTURE_DEPLOYMENT.md
    AGENT 9 — Test Architecture                  → docs/SWARMVAULT_TEST_ARCHITECTURE.md
    AGENT F — Final Synthesis                    → 8 final documents (see below)

Each specialist agent must:
 - Inspect actual source files (Read tool, not Grep-only)
 - Produce its own document to its assigned file
 - Cite exact files/functions/routes/models with line numbers
 - Build an EVIDENCE TABLE for every major claim
 - Build a DATA LINEAGE DIAGRAM (markdown text diagram) for every major flow
 - Identify gaps, inconsistencies, risks, technical debt
 - Classify every feature (IMPLEMENTED / PARTIAL / etc.)
 - Never modify product code
 - Clearly distinguish [FACT] from [INFERRED] from [UNKNOWN]
 - Write only to its assigned output file (no overwrites of other agents)

# ============================================================
# AGENT 1 — BACKEND RUNTIME ARCHITECTURE
# ============================================================

Output: docs/SWARMVAULT_BACKEND_ARCHITECTURE.md

Analyze the COMPLETE backend. Read every Python file in the app/ tree.

Cover with exact file/function/line citations:

1.1 Application Startup
 - Entry point (main.py or equivalent)
 - FastAPI app construction
 - Middleware registration order
 - Router inclusion order
 - Database session factory
 - Settings loading
 - Logging configuration
 - Startup / shutdown events

1.2 Routers (complete inventory)
 - Every router file: path, prefix, included routes
 - For each route: method, path, handler function, auth requirement,
   RBAC requirement, tenancy enforcement, response model

1.3 Services (complete inventory)
 - Every service file and its responsibilities
 - Dependency relationships between services
 - External provider integrations

1.4 Models (complete inventory)
 - Every ORM model: fields, types, constraints, indexes
 - Relationships (foreign keys, back-populates)
 - Soft deletion pattern
 - Timestamp fields

1.5 Schemas (complete inventory)
 - Every Pydantic schema: fields, validators, inheritance
 - Request vs response schemas
 - Schema evolution / versioning

1.6 Middleware Stack (in execution order)
 - CORS middleware: configuration, enforcement point, gaps
 - Tenant context middleware: how tenant_id is extracted, set, enforced
 - Authentication middleware: JWT validation, token types
 - Authorization middleware: RBAC enforcement, role hierarchy
 - Error handling middleware: sanitization, logging
 - Any other middleware

1.7 Configuration
 - Settings class: every field, default, source
 - Environment variable mapping
 - Validators and their enforcement
 - Production vs development differences

1.8 Dependency Injection
 - FastAPI Depends() usage patterns
 - Database session injection
 - Tenant context injection
 - Auth dependency chain

1.9 Authentication
 - JWT implementation: algorithm, claims, signing
 - Access token: format, expiry, claims
 - Refresh token: format, expiry, rotation
 - Token storage (frontend side noted)
 - Token validation path
 - Logout path

1.10 Authorization
 - RBAC roles: exact set, hierarchy
 - Role checking implementation
 - Permission model
 - Policy enforcement points
 - Fail-closed behavior

1.11 Tenancy
 - TenantContext: how created, what it contains
 - Tenant extraction: header, JWT claim, subdomain
 - Workspace scoping: how workspace_id is enforced
 - Project scoping: how project_id is enforced
 - Cross-tenant access prevention

1.12 Database Access
 - Session management
 - Query patterns
 - Transaction boundaries
 - Connection pooling

1.13 Background Processing
 - Any background tasks, Celery, asyncio tasks
 - Job queues
 - Retry logic

1.14 External Providers
 - LLM provider abstraction
 - Object storage provider
 - Any other external integrations

1.15 Error Handling
 - HTTPException usage patterns
 - Custom exception classes
 - Error sanitization
 - Logging of errors

1.16 Observability
 - Logging: format, levels, what is logged
 - Metrics: what, where, how
 - Tracing: correlation IDs, request IDs

1.17 Health/Readiness
 - Health endpoints
 - Readiness checks
 - Liveness probes

1.18 Representative Request Traces

For each major endpoint type, trace the complete execution path:

    HTTP Request
    → CORS middleware
    → Tenant context extraction
    → Authentication (JWT validation)
    → Authorization (RBAC check)
    → Router match
    → Pydantic schema validation
    → Service function call
    → Database query
    → Response serialization
    → Response

Include an EVIDENCE TABLE and a LINEAGE DIAGRAM for each trace.

# ============================================================
# AGENT 2 — DATA, MEMORY & PERSISTENCE ARCHITECTURE
# ============================================================

Output: docs/SWARMVAULT_DATA_MEMORY_ARCHITECTURE.md

Analyze the complete information/data lifecycle.

2.1 Data Lineage: Raw Input → Persistent Store → Retrieval → UI

For EVERY transition, document the complete contract:

    ┌─────────────────────────────────────────────────────────────────┐
    │ TRANSITION: [name]                                             │
    │ Source: [file:function] → Destination: [file:function]         │
    ├─────────────────────────────────────────────────────────────────┤
    │ INPUT:    schema, fields, types, source system                 │
    │ OUTPUT:   schema, fields, types, destination system            │
    │ TRANSFORM: function, logic summary, line number                │
    │ VALIDATE: checks performed, failure handling                   │
    │ GUARDRAIL: security/safety control, bypassability             │
    │ FAILURE:  error type, code, user effect                        │
    │ PERSIST:  table/collection, write semantics                    │
    │ PROVENANCE: trace data generated                               │
    │ MEMORY QUALITY: effect on downstream reliability               │
    └─────────────────────────────────────────────────────────────────┘

Transitions to analyze:
    T2-1:  Raw Input (user message / upload / API call)
    T2-2:  Ingestion entry point
    T2-3:  M0 Normalization
    T2-4:  M1 Session Understanding
    T2-5:  M2 Fact/Decision Extraction
    T2-6:  M3 Temporal Processing
    T2-7:  M4 Graph Construction
    T2-8:  M5 Retrieval Indexing
    T2-9:  M6 Memory Intelligence Operations
    T2-10: Persistent Store (database write)
    T2-11: Retrieval (database read + ranking)
    T2-12: API Response serialization
    T2-13: Frontend rendering

2.2 Session Representation
 - Session model: fields, lifecycle, state machine
 - Session creation, update, deletion
 - Session ↔ workspace/project scoping

2.3 Memory Records
 - Memory model: fields, types, constraints
 - Memory creation flow
 - Memory types (raw, normalized, extracted)
 - Memory status lifecycle

2.4 Facts
 - Fact model: fields, types, constraints
 - Fact creation (M2 output)
 - Fact fields: content, confidence, authority, temporal_status,
   source_id, session_id, workspace_id, project_id
 - Fact update and supersession
 - Fact deletion

2.5 Decisions
 - Decision model: fields, types, constraints
 - Decision creation (M2 output)
 - Decision fields: content, confidence, authority, temporal_status,
   source_id, session_id, supersedes_id
 - Decision update and supersession
 - Decision deletion

2.6 Temporal Information
 - Temporal status values: exact enum, semantics
 - Timestamp fields: created_at, updated_at, deleted_at, superseded_at
 - Temporal interpretation logic
 - Temporal decay in retrieval

2.7 Graph Structure
 - GraphNode model: fields, types
 - GraphEdge model: fields, types
 - Node types and their semantics
 - Edge types and their semantics
 - Graph construction (M4)
 - Graph traversal for retrieval

2.8 Provenance Chain
 - Provenance model: fields, types
 - ProvenanceRecord: fields, types
 - How provenance is created (per stage)
 - Provenance retrieval
 - Provenance → UI rendering

2.9 Source References
 - Source model: fields, types
 - Source types and their semantics
 - Source ↔ memory linkage
 - Source trust model

2.10 Confidence & Authority
 - Confidence: scale, source, interpretation
 - Authority: levels, source, interpretation
 - How confidence/authority affect retrieval ranking

2.11 Soft Deletion & Supersession
 - deleted_at pattern: implementation, queries
 - superseded_at / supersedes_id pattern
 - Cascading effects
 - Visibility in retrieval

2.12 Deduplication & Hashing
 - Content hashing: algorithm, where computed, stored where
 - Deduplication logic
 - Hash collision handling

2.13 Audit Records
 - AuditEvent model: fields, types
 - What triggers audit events
 - Immutability guarantees
 - Audit → UI

2.14 Storage Architecture
 - Database: engine, connection, schema
 - Tables: complete inventory with DDL-equivalent
 - Indexes: what exists, what is missing
 - Migrations: directory, naming convention, applied state

2.15 Retrieval Representation
 - M5 retrieval: query path, ranking, response format
 - Search API: query path, filters, response format
 - Graph API: query path, traversal, response format

2.16 Serialization
 - ORM → Pydantic conversion
 - JSON serialization for API responses
 - Graph serialization

Include an EVIDENCE TABLE and a LINEAGE DIAGRAM for each major flow.

# ============================================================
# AGENT 3 — PIPELINE, GUARDRAIL & VALIDATION ARCHITECTURE
# ============================================================

Output: docs/SWARMVAULT_GUARDRAILS_VALIDATION_ARCHITECTURE.md

Perform a forensic analysis of EVERY stagewise safeguard.

3.1 Complete Guardrail Matrix

For EVERY guardrail, document:

    ┌─────────────────────────────────────────────────────────────────┐
    │ GUARDRAIL: [name]                                              │
    │ Stage: [which pipeline stage]                                  │
    │ Location: [file:function:line]                                 │
    ├──────────────────────────────────────────────────���──────────────┤
    │ PURPOSE:    what threat or error it prevents                   │
    │ INPUT:      what it operates on                                │
    │ CHECK:      exact validation logic                             │
    │ ON FAIL:    error type, HTTP status, message                   │
    │ BYPASSABLE: YES/NO/PARTIAL — with explanation                 │
    │ TESTED:     YES/NO/PARTIAL — with test file reference         │
    │ SEVERITY:   CRITICAL/HIGH/MEDIUM/LOW                          │
    │ STATUS:     ACTIVE/PARTIAL/MISSING/DOCUMENTED                 │
    └─────────────────────────────────────────────────────────────────┘

Guardrails to analyze (complete list):
    G3-01:  CORS origin validation
    G3-02:  Security headers (CSP, HSTS, etc.)
    G3-03:  Request size limits
    G3-04:  Rate limiting (per endpoint type)
    G3-05:  JWT signature verification
    G3-06:  JWT expiry enforcement
    G3-07:  Refresh token rotation
    G3-08:  Password minimum entropy
    G3-09:  Tenant context extraction
    G3-10:  Tenant isolation (cross-tenant query prevention)
    G3-11:  Workspace isolation
    G3-12:  Project isolation
    G3-13:  RBAC role enforcement
    G3-14:  Fail-closed on auth failure
    G3-15:  Pydantic schema validation (request)
    G3-16:  Pydantic schema validation (response)
    G3-17:  JSON ingestion validation
    G3-18:  JSONL ingestion validation
    G3-19:  Source-type validation
    G3-20:  Content validation (empty, oversized)
    G3-21:  M0 normalization validation
    G3-22:  M1 session understanding validation
    G3-23:  M2 fact/decision extraction validation
    G3-24:  M3 temporal processing validation
    G3-25:  M4 graph validation
    G3-26:  M5 retrieval ranking validation
    G3-27:  Confidence range enforcement (0.0–1.0)
    G3-28:  Authority level validation
    G3-29:  Temporal status enum validation
    G3-30:  Deduplication (content hash check)
    G3-31:  Provenance requirement (must have source)
    G3-32:  Soft-delete filtering (deleted_at IS NULL)
    G3-33:  Supersession filtering
    G3-34:  API key format and scope validation
    G3-35:  Secret handling (no secrets in logs/responses)
    G3-36:  Error sanitization (no stack traces to client)
    G3-37:  SQL injection prevention (parameterized queries)
    G3-38:  XSS prevention (output encoding)
    G3-39:  CSRF protection
    G3-40:  Database transaction boundaries
    G3-41:  Storage key path validation
    G3-42:  Upload size enforcement
    G3-43:  Content-type validation
    G3-44:  Audit event immutability
    G3-45:  Correlation ID propagation

3.2 Adversarial Input Analysis

For each guardrail, analyze: "Can adversarial/malformed input cross stages?"

    Input: [malformed payload]
    Stage Gx: [bypass technique]
    Outcome: [what happens]
    Evidence: [file:line]

3.3 Validation Gap Matrix

    | Guardrail | Active | Partial | Missing | Bypassable | Untested |
    |-----------|--------|---------|---------|------------|----------|

Include an EVIDENCE TABLE and a LINEAGE DIAGRAM.

# ============================================================
# AGENT 4 — API / CONTRACT / INTEGRATION ARCHITECTURE
# ============================================================

Output: docs/SWARMVAULT_API_INTEGRATION_ARCHITECTURE.md

4.1 Complete API Route Inventory

For EVERY route:

    ┌─────────────────────────────────────────────────────────────────┐
    │ ROUTE: [METHOD] /api/v1/[path]                                 │
    │ Handler: [file:function]                                       │
    │ Auth: [none / require_auth / require_min_role]                 │
    │ RBAC: [minimum role]                                           │
    │ Tenancy: [tenant / workspace / project]                        │
    ├─────────────────────────────────────────────────────────────────┤
    │ REQUEST SCHEMA:  [Pydantic model name + fields]               │
    │ RESPONSE SCHEMA: [Pydantic model name + fields]               │
    │ ERRORS: [HTTP status codes + conditions]                       │
    │ PAGINATION: [yes/no, params, format]                           │
    │ FILTERING: [query params, operators]                           │
    │ STREAMING: [SSE / streaming response / none]                   │
    │ DEPENDENCIES: [services called, DB queries]                    │
    │ SIDE EFFECTS: [what is written, audit events]                  │
    └─────────────────────────────────────────────────────────────────┘

Group by domain:
 - Authentication (register, login, logout, refresh, me)
 - Workspace (CRUD, members, invitations)
 - Projects (CRUD)
 - Sessions (CRUD, list)
 - Memory (CRUD, types, status)
 - Facts (CRUD, list, supersede)
 - Decisions (CRUD, list, supersede)
 - Ingestion (JSON, JSONL, file)
 - Search (query, filters)
 - Chat (send, history, SSE)
 - Graph (nodes, edges, traverse)
 - Provenance (event, trace)
 - Audit (events, trace)
 - Storage (upload, download, delete)
 - API Keys (CRUD)
 - Health (health, readiness)

4.2 API Client (Frontend Side)
 - api.ts / api.tsx: every function
 - Request construction
 - Response parsing
 - Error handling
 - Token injection
 - Base URL configuration

4.3 Integration Classification

For each external integration:

    INTEGRATION: [name]
    CLASSIFICATION: IMPLEMENTED / PARTIAL / DOCUMENTED / PLANNED / MISSING / UNVERIFIED
    EVIDENCE: [files, functions, configuration]
    CONTRACT: [what is exchanged, format, protocol]
    STATUS: [working / broken / untested / not deployed]
    GAPS: [what is missing or broken]

Integrations to analyze:
 - Anthropic Claude API
 - OpenAI API
 - SwarmVault core (self-referential)
 - MCP (Model Context Protocol)
 - REST API (self)
 - SSE (Server-Sent Events)
 - Object storage (filesystem / S3)
 - PostgreSQL (via SQLAlchemy)
 - Universal Adapter (if present)
 - Claude Code integration (if present)
 - Codex integration (if present)

4.4 SSE / Streaming
 - SSE endpoints
 - Event format
 - Connection lifecycle
 - Error handling in stream
 - Client-side handling

4.5 Frontend → Backend Contract Matrix

For every significant frontend screen/feature:

    SCREEN: [name]
    COMPONENT: [file:component]
    API CALLS: [endpoint, method, params]
    BACKEND ROUTER: [file:router function]
    SERVICE: [file:service function]
    DATABASE: [table, query type]
    RESPONSE: [schema, fields consumed]
    RENDERING: [what is displayed, how errors are shown]

Include an EVIDENCE TABLE and a LINEAGE DIAGRAM.

# ============================================================
# AGENT 5 — FRONTEND ARCHITECTURE
# ============================================================

Output: docs/SWARMVAULT_FRONTEND_ARCHITECTURE.md

5.1 Next.js Architecture
 - App router vs pages router
 - Route structure (every app/ directory)
 - Layout hierarchy
 - Root layout, providers
 - Metadata configuration

5.2 Components
 - Component inventory by directory
 - UI primitives (buttons, inputs, cards, etc.)
 - Feature components
 - Page components
 - Layout components

5.3 State Management
 - React Context usage
 - useState / useReducer patterns
 - URL state (search params)
 - Server state (React Server Components)
 - No global state library (confirm absence)

5.4 API Client
 - lib/api.ts: every function, request/response flow
 - Token management (store, retrieve, clear)
 - Error handling in API calls
 - Request interceptors
 - Response interceptors

5.5 Authentication Flow
 - AuthProvider: state, effects, methods
 - Login flow (UI → API → token storage → redirect)
 - Register flow
 - Logout flow
 - Token refresh (automatic?)
 - Session persistence (localStorage)
 - Protected routes

5.6 SSE / Streaming Handling
 - Chat streaming: component, hook, event handling
 - Error recovery in stream
 - Connection lifecycle

5.7 Feature Architecture

For each feature area:

    FEATURE: [name]
    ROUTES: [app routes]
    COMPONENTS: [component files]
    API: [endpoints called]
    STATE: [local/context/server]
    DATA FLOW: [user action → API → render]

Features: dashboard, projects, chat, sessions, memory, facts,
decisions, timeline, search, graph, provenance, ingestion,
storage, API keys, settings, workspace, members, invitations.

5.8 Styling & Design System
 - Tailwind config: theme, custom values
 - CSS custom properties: what they control
 - globals.css: key sections
 - Component styling patterns
 - Dark/light mode
 - Responsive breakpoints
 - Accessibility features

5.9 Security
 - XSS prevention (React escaping, DOMPurify?)
 - CSRF protection (SameSite cookies?)
 - Token exposure risks
 - Sensitive data in localStorage

Include an EVIDENCE TABLE and a LINEAGE DIAGRAM.

# ============================================================
# AGENT 6 — SECURITY, TENANCY & OPERATIONAL ARCHITECTURE
# ============================================================

Output: docs/SWARMVAULT_SECURITY_OPERATIONAL_ARCHITECTURE.md

6.1 Security Control Inventory

For EVERY security control:

    ┌─────────────────────────────────────────────────────────────────┐
    │ CONTROL: [name]                                                │
    │ TYPE: [preventive / detective / corrective]                    │
    │ LOCATION: [file:function:line]                                 │
    │ ENFORCEMENT POINT: [where in the request lifecycle]            │
    ├─────────────────────────────────────────────────────────────────┤
    │ PURPOSE:    what it protects against                           │
    │ MECHANISM:  how it works (algorithm, check, etc.)              │
    │ BYPASS:     can it be bypassed? how?                          │
    │ FAILURE:    what happens if it fails                           │
    │ TEST:       test file + function that exercises it             │
    │ SEVERITY:   CRITICAL/HIGH/MEDIUM/LOW                          │
    └─────────────────────────────────────────────────────────────────┘

Controls:
 - Authentication (JWT, password, refresh tokens)
 - Authorization (RBAC, roles, fail-closed)
 - Tenancy (tenant, workspace, project isolation)
 - API key management
 - CORS enforcement
 - Security headers
 - Rate limiting
 - Input validation
 - SQL injection prevention
 - XSS prevention
 - CSRF protection
 - Secret handling
 - Error sanitization
 - Audit logging
 - Provenance tracking
 - Database security (connections, credentials)
 - Storage security (key paths, access control)
 - Secret management (API keys, LLM keys)

6.2 Security Boundary Map

    ┌───────────────────────────────���─────────────────────────────────┐
    │                        INTERNET                                 │
    │                            │                                    │
    │                    ┌───────▼────────┐                           │
    │                    │   CORS Gate    │                           │
    │                    └───────┬────────┘                           │
    │                            │                                    │
    │                    ┌───────▼────────┐                           │
    │                    │  TLS Terminator│                           │
    │                    └───────┬────────┘                           │
    │                            │                                    │
    │                    ┌───────▼────────┐                           │
    │                    │  Rate Limiter  │                           │
    │                    └───────┬────────┘                           │
    │                            │                                    │
    │  ┌─────────────────────────▼──────────────────────────┐        │
    │  │              FastAPI Application                    │        │
    │  │  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │        │
    │  │  │ Auth Middle │  │Tenant Middle│  │  RBAC Mid  │ │        │
    │  │  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘ │        │
    │  │         │                │                │        │        │
    │  │  ┌──────▼────────────────▼────────────────▼──────┐ │        │
    │  │  │              Router / Handler                  │ │        │
    │  │  └──────┬────────────────────────────────┬──────┘ │        │
    │  │         │                                │          │        │
    │  │  ┌──────▼──────┐               ┌─────────▼───────┐  │        │
    │  │  │   Service   │               │   Audit Log     │  │        │
    │  │  └──────┬──────┘               └─────────────────┘  │        │
    │  │         │                                           │        │
    │  │  ┌──────▼──────────────────────────────────────────┐│        │
    │  │  │              Database                           ││        │
    │  │  └─────────────────────────────────────────────────┘│        │
    │  └─────────────────────────────────────────────────────┘        │
    │                            │                                    │
    │                    ┌───────▼────────┐                           │
    │                    │ Object Storage │                           │
    │                    └────────────────┘                            │
    └─────────────────────────────────────────────────────────────────┘

6.3 RBAC Model
 - Roles: complete list with exact semantics
 - Role hierarchy
 - Permission checks per endpoint
 - Self-protection rules (can't remove yourself as owner)

6.4 Tenancy Isolation Verification
 - How tenant_id is enforced in EVERY query
 - Workspace scoping enforcement
 - Project scoping enforcement
 - Cross-tenant query prevention evidence
 - Information leakage prevention (404 vs 403)

6.5 Operational Concerns
 - Startup sequence
 - Shutdown sequence
 - Health checks
 - Readiness probes
 - Logging configuration
 - Environment validation
 - Migration safety

Include an EVIDENCE TABLE and a LINEAGE DIAGRAM.

# ============================================================
# AGENT 7 — MEMORY INTELLIGENCE READINESS ARCHITECTURE
# ============================================================

Output: docs/SWARMVAULT_MEMORY_INTELLIGENCE_READINESS.md

THIS IS THE MOST IMPORTANT SPECIALIST.

7.1 Memory Object Analysis

For each memory-related model (Memory, Fact, Decision, GraphNode, GraphEdge,
ProvenanceRecord, AuditEvent), document:

    ┌─────────────────────────────────────────────────────────────────┐
    │ OBJECT: [model name]                                           │
    │ FIELDS: [complete list with types]                             │
    ├─────────────────────────────────────────────────────────────────┤
    │ IDENTITY:   Does it have a stable, unique identity?            │
    │ SOURCE:     Does it record where it came from?                 │
    │ TIME:       Does it record when it was created/modified?       │
    │ CONTEXT:    Does it record workspace/project/session?          │
    │ CONFIDENCE: Does it have a confidence value? Range?            │
    │ AUTHORITY:  Does it have an authority level? Scale?            │
    │ PROVENANCE: Does it link to a provenance chain?                │
    │ RELATIONSHIPS: Does it link to other memory objects?           │
    │ SUPERSESSION: Can it be superseded? How?                      │
    │ CONTRADICTION: Can it be marked as contradicted? How?         │
    │ SCOPE:      Is it scoped to tenant/workspace/project?         │
    │ LIFECYCLE:  Can it be soft-deleted? Hard-deleted?             │
    │ RETRIEVAL:  Can it be retrieved by ID? By query?              │
    │ AUDITABILITY: Is every change audited?                         │
    │ READINESS:  GREEN / YELLOW / RED                              │
    │ EVIDENCE:   [file:line references]                             │
    └─────────────────────────────────────────────────────────────────┘

7.2 Memory Quality Scorecard

For each memory capability dimension:

    ┌─────────────────────────────────────────────────────────────────┐
    │ DIMENSION: [e.g., Temporal Reasoning]                          │
    │ CURRENT STATE: [what exists]                                   │
    │ READINESS:   GREEN / YELLOW / RED                              │
    │ WHAT WORKS:  [specific evidence]                               │
    │ WHAT'S MISSING: [specific gaps]                                │
    │ BLOCKS INTELLIGENCE: YES / NO / PARTIAL                        │
    │ REQUIRES: [what must be added to reach GREEN]                  │
    └─────────────────────────────────────────────────────────────────┘

Dimensions:
 - Identity & Uniqueness
 - Source Tracking
 - Temporal Semantics
 - Confidence Calibration
 - Authority Modeling
 - Provenance Chain Completeness
 - Relationship Mapping
 - Supersession Support
 - Contradiction Detection
 - Scope Enforcement
 - Lifecycle Management
 - Retrieval Explainability
 - Audit Completeness
 - Deduplication
 - Content Integrity (hashing)

7.3 Pipeline Stage Memory Quality

For each M0–M6 stage:

    STAGE: [M0–M6]
    INPUT QUALITY:  what quality attributes the input has
    OUTPUT QUALITY: what quality attributes are added/removed
    DEGRADATION:    does quality degrade at this stage?
    RECOVERABLE:    can quality be restored downstream?
    GATE:           is there a quality gate before persistence?

7.4 Persistent Memory Readiness

    ┌─────────────────────────────────────────────────────────────────┐
    │ What data is currently persistent?                             │
    │ What data is ephemeral?                                        │
    │ What data is normalized?                                       │
    │ What data has provenance?                                      │
    │ What data has temporal semantics?                              │
    │ What data has confidence?                                      │
    │ What data has authority?                                       │
    │ What data has identity?                                        │
    │ What data has scope?                                           │
    │ What data can be superseded?                                   │
    │ What data can be contradicted?                                 │
    │ What data can be deleted?                                      │
    │ What data can be retrieved?                                    │
    │ What data can be explained?                                    │
    │ What data is safe for future memory intelligence?              │
    └─────────────────────────────────────────────────────────────────┘

Classify each: GREEN = ready / YELLOW = partially ready / RED = not ready

7.5 Memory Safety Gate Matrix

    ┌─────────────────────────────────────────────────────────────────┐
    │ GATE: [condition that must be satisfied]                       │
    │ CHECK: [where it is enforced]                                  │
    │ ON FAIL: [what happens — block / warn / allow]                │
    │ BYPASSABLE: YES / NO                                          │
    │ TESTED: YES / NO                                               │
    │ STAGE: [which M stage]                                         │
    └─────────────────────────────────────────────────────────────────┘

7.6 Next Memory Intelligence Layer Boundary

    WHAT THE CURRENT SYSTEM CAN SAFELY PROVIDE:
    - [specific data types with evidence]

    WHAT THE NEXT LAYER CAN TRUST:
    - [specific attributes with confidence levels]

    WHAT THE NEXT LAYER MUST NOT ASSUME:
    - [specific missing attributes with risk assessment]

    REQUIRED CONTRACTS BEFORE IMPLEMENTATION:
    - [specific API/schema/contract requirements]

Include an EVIDENCE TABLE and a LINEAGE DIAGRAM.

# ============================================================
# AGENT 8 — INFRASTRUCTURE & DEPLOYMENT ARCHITECTURE
# ============================================================

Output: docs/SWARMVAULT_INFRASTRUCTURE_DEPLOYMENT.md

8.1 Deployment Configuration
 - Dockerfile(s): location, contents, multi-stage
 - docker-compose.yml: services, volumes, networks
 - .dockerignore
 - Container image: base image, build steps

8.2 Environment Configuration
 - .env.example: all variables documented
 - Environment-specific configs
 - Secret handling in deployment
 - Config validation at startup

8.3 Database Configuration
 - PostgreSQL version
 - Connection configuration
 - Migration strategy
 - Backup/restore strategy

8.4 Storage Configuration
 - Filesystem storage: path, permissions
 - S3 storage: configuration, credentials
 - Storage provider abstraction

8.5 Process Management
 - uvicorn / gunicorn configuration
 - Worker count
 - Timeout settings
 - Graceful shutdown

8.6 Network Architecture
 - Port configuration
 - Reverse proxy (nginx, traefik?)
 - TLS termination
 - Internal service communication

8.7 Scaling Considerations
 - Horizontal scaling readiness
 - Session affinity requirements
 - Database scaling
 - Storage scaling

8.8 Monitoring & Observability
 - Logging: format, destination, rotation
 - Metrics: what, where, how to access
 - Health checks: endpoints, what they verify
 - Alerting: what is monitored

Include an EVIDENCE TABLE and a LINEAGE DIAGRAM.

# ============================================================
# AGENT 9 — TEST ARCHITECTURE
# ============================================================

Output: docs/SWARMVAULT_TEST_ARCHITECTURE.md

9.1 Test Inventory
 - Test directories and files
 - Test runner configuration
 - Test categories (unit, integration, e2e)

9.2 Test Coverage by Domain

For each domain area:

    DOMAIN: [name]
    TEST FILES: [paths]
    TEST FUNCTIONS: [names + what they test]
    COVERAGE: [what is tested / what is missing]
    GAPS: [uncovered paths, edge cases]

Domains:
 - Authentication
 - Authorization / RBAC
 - Tenancy isolation
 - Workspace management
 - Project management
 - Session management
 - Ingestion (JSON, JSONL, file)
 - M0 Normalization
 - M1 Session Understanding
 - M2 Fact/Decision Extraction
 - M3 Temporal Processing
 - M4 Graph Construction
 - M5 Retrieval
 - M6 Memory Operations
 - Chat
 - Search
 - Graph API
 - Provenance
 - Audit
 - Storage
 - API Keys
 - Error handling
 - Security boundaries

9.3 Test Patterns
 - Fixture usage
 - Database setup/teardown
 - Mocking patterns
 - Authentication in tests

9.4 E2E Tests
 - Playwright configuration
 - E2E test scenarios
 - What flows are covered

9.5 Test Gaps Analysis

    ┌─────────────────────────────────────────────────────────────────┐
    │ GAP: [what is not tested]                                      │
    │ RISK: [what could go wrong]                                    │
    │ DOMAIN: [which specialist domain]                              │
    └─────────────────────────────────────────────────────────────────┘

Include an EVIDENCE TABLE.

# ============================================================
# CROSS-AGENT REQUIREMENT — DATA LINEAGE
# ============================================================

Every specialist must include a LINEAGE DIAGRAM for every major flow
using this canonical structure:

    SOURCE
      │
      ▼
    INGESTION
      │
      ▼
    NORMALIZATION (M0)
      │
      ▼
    SESSION UNDERSTANDING (M1)
      │
      ▼
    FACT/DECISION EXTRACTION (M2)
      │
      ▼
    TEMPORAL PROCESSING (M3)
      │
      ▼
    GRAPH CONSTRUCTION (M4)
      │
      ▼
    RETRIEVAL INDEXING (M5)
      │
      ▼
    MEMORY INTELLIGENCE (M6)
      │
      ▼
    PERSISTENT STORE
      │
      ▼
    RETRIEVAL
      │
      ▼
    API RESPONSE
      │
      ▼
    FRONTEND RENDER
      │
      ▼
    USER

For every arrow (transition), document:
    INPUT:    exact schema
    OUTPUT:   exact schema
    VALIDATE: checks performed
    GUARDRAIL: security/safety control
    FAILURE:  error behavior
    PROVENANCE: trace data generated
    MEMORY QUALITY: effect on reliability

# ============================================================
# PHASE 1 — FINAL SYNTHESIS
# ============================================================

After all 9 specialist documents are complete, launch the Final Synthesis
Agent. It must:

1. Read all 9 specialist documents completely
2. Read existing architecture documentation
3. Read backend source (app/ directory)
4. Read frontend source (frontend/src/ directory)
5. Read database migrations
6. Read tests
7. Read API contract documentation
8. Read memory implementation
9. Read ingestion implementation
10. Read deployment configuration
11. Reconcile contradictions between specialist claims AND source code
12. Resolve [INFERRED] vs [FACT] disagreements by re-reading source

The synthesis agent produces 8 final documents:

# ============================================================
# FINAL DOCUMENT 1 — MASTER ARCHITECTURE
# ============================================================

File: docs/SWARMVAULT_WEBAPP_MASTER_ARCHITECTURE.md

Required structure:
 1. Executive Summary (1 page)
 2. Product Boundary (what is in/out of scope)
 3. System Context (external systems, users, data flows)
 4. Architectural Principles (guidelines that shaped the design)
 5. High-Level Architecture (C4 context/container diagram in text)
 6. Backend Architecture (from Agent 1, reconciled)
 7. Frontend Architecture (from Agent 5, reconciled)
 8. API Architecture (from Agent 4, reconciled)
 9. Data Architecture (from Agent 2, reconciled)
10. Memory Architecture (from Agent 2 + 7, reconciled)
11. Storage Architecture (from Agent 8, reconciled)
12. Security Architecture (from Agent 6, reconciled)
13. Tenancy Architecture (from Agent 6, reconciled)
14. Pipeline Architecture (M0–M6, from Agent 2 + 3, reconciled)
15. M0–M6 Architecture (detailed stage-by-stage)
16. Guardrail Architecture (from Agent 3, reconciled)
17. Validation Architecture (from Agent 3, reconciled)
18. Provenance Architecture (from Agent 2, reconciled)
19. Audit Architecture (from Agent 6, reconciled)
20. Retrieval Architecture (from Agent 2 + 4, reconciled)
21. SSE/Streaming Architecture (from Agent 4, reconciled)
22. Ingestion Architecture (from Agent 2 + 4, reconciled)
23. Integration Architecture (from Agent 4 + 8, reconciled)
24. Deployment Architecture (from Agent 8, reconciled)
25. Failure & Recovery Architecture (from Agent 6 + 8)
26. Observability Architecture (from Agent 1 + 8)
27. Test Architecture (from Agent 9, reconciled)
28. Current Limitations (honest assessment)
29. Technical Debt (prioritized, with evidence)
30. Future Memory Intelligence Boundary (from Agent 7)
31. Architectural Readiness Assessment (summary scorecard)

Each section must include:
 - Evidence citations (file:line)
 - Classification of every component
 - Identified gaps and risks

# ============================================================
# FINAL DOCUMENT 2 — END-TO-END FLOWS
# ============================================================

File: docs/SWARMVAULT_END_TO_END_FLOWS.md

Document actual flows for:

    FLOW-001  User Registration
    FLOW-002  Login
    FLOW-003  Workspace Creation
    FLOW-004  Project Creation
    FLOW-005  Session Ingestion
    FLOW-006  JSON Ingestion
    FLOW-007  JSONL Ingestion
    FLOW-008  M0 Normalization
    FLOW-009  M1 Session Understanding
    FLOW-010  M2 Fact/Decision Extraction
    FLOW-011  M3 Temporal Processing
    FLOW-012  M4 Graph Construction
    FLOW-013  M5 Retrieval
    FLOW-014  M6 Memory Intelligence Operations
    FLOW-015  Persistent Memory Creation
    FLOW-016  Memory Retrieval
    FLOW-017  Memory Search
    FLOW-018  Chat (non-streaming)
    FLOW-019  SSE Chat Streaming
    FLOW-020  Provenance Trace
    FLOW-021  Graph Exploration
    FLOW-022  Memory Deletion
    FLOW-023  Memory Supersession
    FLOW-024  Audit Trail Query
    FLOW-025  API Key Creation
    FLOW-026  File Upload
    FLOW-027  External Agent Integration

For each flow:
    TRIGGER:      what initiates this flow
    INPUT:        exact request format, fields, types
    VALIDATION:   every validation check, location, failure behavior
    GUARDRAILS:   every security/safety control, enforcement point
    PROCESSING:   step-by-step execution path with file:line citations
    PERSISTENCE:  every database write, table, fields
    OUTPUT:       exact response format, fields, types
    FAILURE:      every failure point, error code, user effect
    SECURITY:     security boundary crossings, enforcement
    PROVENANCE:   provenance records created, what they capture

Include a SEQUENCE DIAGRAM (text-based) for each flow.

# ============================================================
# FINAL DOCUMENT 3 — GUARDRAIL MASTER MATRIX
# ============================================================

File: docs/SWARMVAULT_GUARDRAIL_MASTER_MATRIX.md

3.1 Complete Guardrail Inventory

    ┌────────────────────────────────────────────────────────────────────────┐
    │ # │ STAGE │ CONTROL │ IMPLEMENTATION │ ENFORCEMENT │ VALIDATION │     │
    │   │       │         │                │   POINT      │            │     │
    ├────────────────────────────────────────────────────────────────────────┤
    │   │       │         │                │              │            │     │
    │   │       │         │                │              │            │     │
    └────────────────────────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────────────────────────┐
    │ # │ TEST │ FAILURE MODE │ BYPASS POSSIBLE │ SEVERITY │ STATUS │ GAP │
    ├────────────────────────────────────────────────────────────────────────┤
    │   │      │              │                 │          │        │     │
    └────────────────────────────────────────────────────────────────────────┘

3.2 Memory Safety Gate Matrix

    ┌─────��──────────────────────────────────────────────────────────────────┐
    │ GATE │ CONDITION │ CHECK POINT │ ON FAIL │ BYPASS │ TESTED │ STAGE │   │
    ├────────────────────────────────────────────────────────────────────────┤
    │      │ Must have source_id to persist as memory                        │
    │      │ Must have confidence 0.0–1.0                                   │
    │      │ Must have authority level                                       │
    │      │ Must have temporal_status                                       │
    │      │ Must have workspace_id                                          │
    │      │ Must pass tenant isolation check                                │
    │      │ Must pass RBAC check                                            │
    │      │ Content must be non-empty after normalization                   │
    │      │ Must not be a duplicate (hash check)                            │
    │      │ Must not be superseded by newer information                     │
    │      │ Provenance record must be created                               │
    │      │ Audit event must be recorded                                    │
    └────────────────────────────────────────────────────────────────────────┘

Include an EVIDENCE TABLE for every guardrail.

# ============================================================
# FINAL DOCUMENT 4 — DATA & MEMORY READINESS
# ============================================================

File: docs/SWARMVAULT_PERSISTENT_MEMORY_READINESS.md

4.1 Data Persistence Classification

For each data type:

    ┌─────────────────────────────────────────────────────────────────┐
    │ DATA TYPE: [e.g., Fact]                                        │
    │ PERSISTENT: YES / NO / PARTIAL                                 │
    │ EPHEMERAL:  YES / NO                                           │
    │ NORMALIZED: YES / NO / PARTIAL                                 │
    │ PROVENANCE: YES / NO / PARTIAL                                 │
    │ TEMPORAL:   YES / NO / PARTIAL                                 │
    │ CONFIDENCE: YES / NO / PARTIAL                                 │
    │ AUTHORITY:  YES / NO / PARTIAL                                 │
    │ IDENTITY:   YES / NO / PARTIAL                                 │
    │ SCOPE:      YES / NO / PARTIAL                                 │
    │ SUPERSEDE:  YES / NO / PARTIAL                                 │
    │ CONTRADICT: YES / NO / PARTIAL                                 │
    │ DELETE:     YES / NO / PARTIAL                                 │
    │ RETRIEVE:   YES / NO / PARTIAL                                 │
    │ EXPLAIN:    YES / NO / PARTIAL                                 │
    │ SAFE FOR INTELLIGENCE: GREEN / YELLOW / RED                   │
    │ EVIDENCE:  [file:line references]                              │
    └─────────────────────────────────────────────────────────────────┘

Data types: Memory, Fact, Decision, GraphNode, GraphEdge,
ProvenanceRecord, AuditEvent, Session, Project, Workspace,
User, APIKey, Invitation, StorageObject.

4.2 Memory Intelligence Readiness

    DIMENSION                    │ READY │ PARTIAL │ MISSING │ EVIDENCE
    ─────────────────────────────┼───────┼─────────┼─────────┼──────────
    Identity & Uniqueness        │       │         │         │
    Source Tracking              │       │         │         │
    Temporal Semantics           │       │         │         │
    Confidence Calibration       │       │         │         │
    Authority Modeling           │       │         │         │
    Provenance Chain             │       │         │         │
    Relationship Mapping         │       │         │         │
    Supersession Support         │       │         │         │
    Contradiction Detection      │       │         │         │
    Scope Enforcement            │       │         │         │
    Lifecycle Management         │       │         │         │
    Retrieval Explainability     │       │         │         │
    Audit Completeness           │       │         │         │
    Deduplication                │       │         │         │
    Content Integrity            │       │         │         │

4.3 Memory Safety Gate Status

    For each gate in the Memory Safety Gate Matrix:
    - Current status
    - What happens if the gate is not satisfied
    - Whether it can be bypassed
    - Whether it is tested

4.4 Gap Analysis

    GAP: [description]
    CURRENT STATE: [what exists]
    RISK: [what could go wrong]
    BLOCKS PERSISTENT MEMORY: YES / NO
    BLOCKS MEMORY INTELLIGENCE: YES / NO
    REQUIRED FIX: [what must be added]

Include an EVIDENCE TABLE.

# ============================================================
# FINAL DOCUMENT 5 — FRONTEND ↔ BACKEND ARCHITECTURE
# ============================================================

File: docs/SWARMVAULT_FRONTEND_BACKEND_ARCHITECTURE.md

5.1 Complete Frontend ↔ Backend Contract Matrix

For EVERY significant screen/feature:

    ┌─────────────────────────────────────────────────────────────────┐
    │ SCREEN: [name]                                                 │
    │ ROUTE: [app route path]                                        │
    │ COMPONENTS: [key component files]                              │
    ├─────────────────────────────────────────────────────────────────┤
    │ STATE MANAGEMENT:                                             │
    │   - Local: [useState fields]                                  │
    │   - Context: [context name, provider]                         │
    │   - Server: [RSC data, cache tags]                            │
    │   - URL: [search params used]                                 │
    ├─────────────────────────────────────────────────────────────────┤
    │ API CALLS:                                                     │
    │   - Endpoint: [method + path]                                 │
    │   - Request: [body/params schema]                             │
    │   - Response: [schema consumed]                               │
    │   - Auth: [token required, type]                              │
    │   - Error: [how errors are handled]                           │
    ├────────────────────────────────────────────────��────────────────┤
    │ BACKEND:                                                       │
    │   - Router: [file:function]                                   │
    │   - Service: [file:function]                                  │
    │   - Model: [ORM model]                                        │
    │   - Query: [what is fetched, filters]                         │
    ├─────────────────────────────────────────────────────────────────┤
    │ RENDERING:                                                     │
    │   - Success: [what is shown]                                  │
    │   - Loading: [loading state component]                        │
    │   - Empty: [empty state component]                            │
    │   - Error: [error display]                                    │
    └─────────────────────────────────────────────────────────────────┘

Screens to document:
 - Login
 - Register
 - Dashboard
 - Workspace Settings
 - Workspace Members
 - Invitations
 - Projects List
 - Project Detail
 - Chat
 - Sessions List
 - Session Detail
 - Memory List
 - Memory Detail
 - Facts List
 - Facts Detail
 - Decisions List
 - Decisions Detail
 - Timeline
 - Search Results
 - Graph Explorer
 - Provenance Trace
 - Ingestion (JSON/JSONL)
 - Storage (Upload/List)
 - API Keys
 - Settings
 - Audit Log

5.2 Authentication Flow (Frontend ↔ Backend)

    ┌──────────┐     POST /auth/login      ┌──────────────┐
    │ Login UI │ ────────────────────────▶ │ Auth Router   │
    │          │ ◀── {access, refresh} ─── │ (JWT create)  │
    │ storeTokens()                         │              │
    │          │                             │              │
    │          │  GET /auth/me              │              │
    │          │ ────────────────────────▶ │ Auth Router   │
    │ AuthContext │ ◀── UserInfo ────────── │ (JWT validate)│
    │ (user state)   │                       └──────────────┘
    └──────────┘

5.3 Token Lifecycle
 - Storage mechanism (localStorage keys)
 - Refresh flow (automatic?)
 - Expiry handling
 - Logout cleanup

5.4 Frontend/Backend Mismatches

    ┌─────────────────────────────────────────────────────────────────┐
    │ MISMATCH: [description]                                        │
    │ FRONTEND EXPECTS: [field, type, format]                        │
    │ BACKEND PROVIDES: [field, type, format]                        │
    │ IMPACT: [what breaks or is suboptimal]                         │
    │ EVIDENCE: [frontend file + backend file]                       │
    └─────────────────────────────────────────────────────────────────┘

Include an EVIDENCE TABLE and a LINEAGE DIAGRAM.

# ============================================================
# FINAL DOCUMENT 6 — ARCHITECTURAL TRACEABILITY MATRIX
# ============================================================

File: docs/SWARMVAULT_ARCHITECTURAL_TRACEABILITY.md

6.1 Complete Traceability Matrix

For every major capability:

    ┌──────────────���────────────────────────────────────────────────────────┐
    │ REQUIREMENT │ FEATURE │ FRONTEND │ API │ SERVICE │ DATA MODEL │     │
    │             │         │          │     │         │            │     │
    ├───────────────────────────────────────────────────────────────────────┤
    │             │         │          │     │         │            │     │
    │             │         │          │     │         │            │     │
    ├───────────────────────────────────────────────────────────────────────┤
    │ PIPELINE │ GUARDRAIL │ TEST │ PERSIST │ PROVENANCE │ STATUS │ GAP │     │
    ├──────────┼───────────┼──────┼─────────┼────────────┼────────┼─────┤
    │           │           │      │          │            │        │     │
    └───────────────────────────────────────────────────────────────────────┘

Requirements to trace:
 - User registration and authentication
 - Workspace creation and management
 - Project creation and management
 - Session ingestion (manual)
 - JSON ingestion
 - JSONL ingestion
 - M0: Raw input normalization
 - M1: Session understanding
 - M2: Fact extraction
 - M2: Decision extraction
 - M3: Temporal processing
 - M4: Graph construction
 - M5: Multi-factor retrieval
 - M6: Memory intelligence operations
 - Chat with memory grounding
 - SSE chat streaming
 - Search (semantic + keyword)
 - Graph exploration
 - Provenance tracing
 - Audit trail
 - File storage
 - API key management
 - Role-based access control
 - Tenant isolation
 - Workspace isolation
 - Project isolation
 - Soft deletion
 - Supersession
 - Confidence scoring
 - Authority levels
 - Temporal status
 - Content hashing
 - Deduplication

6.2 Feature Coverage Map

    FEATURE                    │ FRONTEND │ BACKEND │ TESTS │ STATUS
    ───────────────────────────┼──────────┼─────────┼───────┼────────
    User Registration          │          │         │       │
    Login                      │          │         │       │
    Logout                     │          │         │       │
    Workspace CRUD             │          │         │       │
    Member Management          │          │         │       │
    Invitation System          │          │         │       │
    Project CRUD               │          │         │       │
    Session Management         │          │         │       │
    JSON Ingestion             │          │         │       │
    JSONL Ingestion            │          │         │       │
    M0 Normalization           │          │         │       │
    M1 Session Understanding   │          │         │       │
    M2 Fact Extraction         │          │         │       │
    M2 Decision Extraction     │          │         │       │
    M3 Temporal Processing     │          │         │       │
    M4 Graph Construction      │          │         │       │
    M5 Retrieval               │          │         │       │
    M6 Memory Operations       │          │         │       │
    Chat                       │          │         │       │
    SSE Streaming              │          │         │       │
    Search                     │          │         │       │
    Graph Exploration          │          │         │       │
    Provenance                 │          │         │       │
    Audit                      │          │         │       │
    File Upload                │          │         │       │
    API Keys                   │          │         │       │
    Settings                   │          │         │       │

Include an EVIDENCE TABLE.

# ============================================================
# FINAL DOCUMENT 7 — ARCHITECTURAL GAPS & NEXT MEMORY LAYER
# ============================================================

File: docs/SWARMVAULT_ARCHITECTURAL_GAPS_AND_MEMORY_NEXT_LAYER.md

7.1 Gap Classification

Classify every gap as P0 / P1 / P2 / P3 based on:

    P0 — Blocks core functionality or creates security vulnerability
    P1 — Blocks memory persistence or memory intelligence readiness
    P2 — Significant architectural weakness, should be addressed
    P3 — Minor issue, cosmetic, or future improvement

For each gap:

    ┌─────────────────────────────────────────────────────────────────┐
    │ GAP: [ID + description]                                        │
    │ CLASSIFICATION: P0 / P1 / P2 / P3                             │
    │ CATEGORY: [security / data / memory / api / frontend / infra] │
    ├─────────────────────────────────────────────────────────────────┤
    │ CURRENT STATE: [what exists today]                             │
    │ EXPECTED STATE: [what should exist]                            │
    │ EVIDENCE: [files, lines, tests]                                │
    │ RISK: [what could go wrong]                                    │
    │ IMPACT: [who/what is affected]                                 │
    │ BLOCKS PERSISTENT MEMORY: YES / NO / PARTIAL                   │
    │ BLOCKS MEMORY INTELLIGENCE: YES / NO / PARTIAL                 │
    │ REQUIRED CONDITION: [what must exist to close gap]            │
    │ RECOMMENDATION: [high-level direction, NOT implementation]    │
    └─────────────────────────────────────────────────────────────────┘

7.2 Memory Next Layer — Readiness Boundary

    ╔═══════════════════════════════════════════════════════════════════╗
    ║  NEXT MEMORY INTELLIGENCE LAYER — READINESS BOUNDARY            ║
    ╠═══════════════════════════════════════════════════════════════════╣
    ║                                                                   ║
    ║  WHAT THE CURRENT SYSTEM CAN SAFELY PROVIDE:                     ║
    ║  ─────────────────────────────────────────────────────────────   ║
    ║  [List of data types, attributes, and contracts that are         ║
    ║   currently stable, tested, and suitable for consumption         ║
    ║   by a future intelligence layer]                                ║
    ║                                                                   ║
    ║  WHAT THE NEXT LAYER CAN TRUST:                                  ║
    ║  ─────────────────────────────────────────────────────────────   ║
    ║  [Specific attributes with confidence levels:                    ║
    ║   HIGH — stable, tested, schema-guaranteed                      ║
    ║   MEDIUM — present but may change                                ║
    ║   LOW — aspirational, not yet implemented]                       ║
    ║                                                                   ║
    ║  WHAT THE NEXT LAYER MUST NOT ASSUME:                            ║
    ║  ─────────────────────────────────────────────────────────────   ║
    ║  [Specific missing attributes with risk assessment:              ║
    ║   what assumptions would be unsafe,                           ║
    ║   what could change without notice,                            ║
    ║   what is not yet implemented]                                   ║
    ║                                                                   ║
    ║  REQUIRED CONTRACTS BEFORE IMPLEMENTATION:                       ║
    ║  ─────────────────────────────────────────────────────────────   ║
    ║  [Specific API contracts, schema guarantees, quality gates,      ║
    ║   test coverage requirements that must exist before             ║
    ║   the intelligence layer can be built]                          ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝

Include an EVIDENCE TABLE.

# ============================================================
# FINAL DOCUMENT 8 — ARCHITECTURE INDEX
# ============================================================

File: docs/SWARMVAULT_ARCHITECTURE_INDEX.md

8.1 Document Inventory

    ┌────────────────────────────────────────────────────────────────────┐
    │ DOCUMENT │ PURPOSE │ AUDIENCE │ LAST UPDATED │ AUTHOR             │
    ├────────────────────────────────────────────────────────────────────┤
    │          │         │          │              │                    │
    └────────────────────────────────────────────────────────────────────┘

8.2 Cross-Reference Index

    By Component:
    - Backend → which documents describe it
    - Frontend → which documents describe it
    - API → which documents describe it
    - Data → which documents describe it
    - Memory → which documents describe it
    - Security → which documents describe it
    - Pipeline → which documents describe it

    By Flow:
    - Registration → which documents trace it
    - Chat → which documents trace it
    - Ingestion → which documents trace it
    - etc.

8.3 Quick Reference

    - File tree (backend + frontend)
    - API route summary
    - Database schema summary
    - Configuration summary
    - Test summary

8.4 Glossary

    Every architectural term used in the documentation package,
    defined precisely with reference to implementation.

# ============================================================
# QUALITY STANDARDS
# ============================================================

Every document must meet these standards:

1. COMPLETENESS
   - Every file in the assigned domain is read and analyzed
   - Every route is documented
   - Every model is documented
   - Every guardrail is documented

2. ACCURACY
   - Every claim is backed by file:line evidence
   - Every [INFERRED] claim is labeled as such
   - Contradictions between specialists are reconciled in synthesis

3. TRACEABILITY
   - Every capability has an evidence trail
   - Every data flow is traced end-to-end
   - Every security control is located

4. CLASSIFICATION
   - Every feature is classified (IMPLEMENTED / PARTIAL / etc.)
   - Every gap is classified (P0 / P1 / P2 / P3)
   - Every readiness item is classified (GREEN / YELLOW / RED)

5. LINEAGE
   - Every major flow has a text-based lineage diagram
   - Every transition has an explicit IO contract
   - Every stage has a provenance effect documented

6. ACTIONABILITY
   - Every gap has a required condition for closure
   - Every risk has a mitigation direction
   - Every readiness gap has a path to GREEN

# ============================================================
# OUTPUT CONTRACT
# ============================================================

The complete architecture documentation package consists of:

    docs/ARCHITECTURE_FORENSICS_BASELINE.md              (Phase 0)
    docs/SWARMVAULT_BACKEND_ARCHITECTURE.md              (Agent 1)
    docs/SWARMVAULT_DATA_MEMORY_ARCHITECTURE.md          (Agent 2)
    docs/SWARMVAULT_GUARDRAILS_VALIDATION_ARCHITECTURE.md (Agent 3)
    docs/SWARMVAULT_API_INTEGRATION_ARCHITECTURE.md      (Agent 4)
    docs/SWARMVAULT_FRONTEND_ARCHITECTURE.md             (Agent 5)
    docs/SWARMVAULT_SECURITY_OPERATIONAL_ARCHITECTURE.md (Agent 6)
    docs/SWARMVAULT_MEMORY_INTELLIGENCE_READINESS.md     (Agent 7)
    docs/SWARMVAULT_INFRASTRUCTURE_DEPLOYMENT.md         (Agent 8)
    docs/SWARMVAULT_TEST_ARCHITECTURE.md                 (Agent 9)
    docs/SWARMVAULT_WEBAPP_MASTER_ARCHITECTURE.md        (Final 1)
    docs/SWARMVAULT_END_TO_END_FLOWS.md                  (Final 2)
    docs/SWARMVAULT_GUARDRAIL_MASTER_MATRIX.md           (Final 3)
    docs/SWARMVAULT_PERSISTENT_MEMORY_READINESS.md       (Final 4)
    docs/SWARMVAULT_FRONTEND_BACKEND_ARCHITECTURE.md     (Final 5)
    docs/SWARMVAULT_ARCHITECTURAL_TRACEABILITY.md        (Final 6)
    docs/SWARMVAULT_ARCHITECTURAL_GAPS_AND_MEMORY_NEXT_LAYER.md (Final 7)
    docs/SWARMVAULT_ARCHITECTURE_INDEX.md                (Final 8)

Total: 18 documents (9 specialist + 9 final).

Each document must be self-contained and readable independently.
Cross-references between documents must use relative paths.

# ============================================================
# EXECUTION INSTRUCTIONS
# ============================================================

1. First, establish the baseline (Phase 0).
2. Launch all 9 specialist agents in parallel.
3. Wait for all specialist agents to complete.
4. Launch the Final Synthesis Agent.
5. The Final Synthesis Agent produces all 8 final documents.
6. After completion, present a summary to the user:
   - How many files were analyzed
   - How many routes were documented
   - How many models were documented
   - Key findings (top 5-10)
   - Memory readiness summary
   - Gap summary (P0 count, P1 count, etc.)
   - Documents produced

DO NOT proceed without repository baseline established.
DO NOT modify any product code during this process.
DO NOT describe planned features as implemented.
DO NOT skip any domain analysis.
