"""
SWARMVAULT WEBAPP — ARCHITECTURAL CONTRACT RECONCILIATION PROMPT
Version: 3.0 — Contract↔Code Audit Phase
================================================================

PURPOSE
-------
This is a RECONCILIATION/AUDIT phase, not an open-ended architecture-discovery phase.

Forensic findings, gap analyses, M-ARCH contracts, and binding architecture
decisions already exist in docs/. This phase determines EXACTLY what those
decisions mean against the current codebase at HEAD e6f4b1c157afaed052584963b942ea04f9661610.

The output is a CONTRACT IMPLEMENTATION READINESS assessment: what the
current code delivers, what it does NOT deliver, and what must change before
the next Memory Intelligence implementation phase can begin.

================================================================
SHA INTEGRITY GATE — MANDATORY
================================================================

BEFORE any analysis begins, record:

    BASELINE SHA  = e6f4b1c157afaed052584963b942ea04f9661610
    STARTING SHA  = <record git rev-parse HEAD at start of this phase>
    ENDING SHA    = <record git rev-parse HEAD at end of this phase>
    WORKTREE      = <git status output>

RULE: ENDING SHA must equal STARTING SHA.
This phase produces DOCUMENTATION ONLY.
No production code changes are authorized.

Allowed actions:
  - Read source files
  - Execute read-only diagnostics
  - Inspect schemas and database metadata
  - Run existing tests (read-only)
  - Create forensic documentation in docs/
  - Create architecture matrices
  - Create evidence tables

NOT allowed:
  - Migrations
  - Model changes
  - Endpoint changes
  - Service refactors
  - Retrieval algorithm changes
  - New queues, adapters, or dependencies
  - Configuration changes
  - Test modifications to make failures pass
  - Any git commit or push

If you discover something that "should be fixed," document it as a finding.
Do NOT fix it.

================================================================
CONTRACT→CODE MAPPING — MANDATORY
================================================================

The 11 M-ARCH contracts are the architectural authority.
Every contract must be mapped against the current codebase.

Build this matrix:

| Contract | Decision | Current Code Location | Current Status | Gap | Required Change | Dependencies | Breaking? | Test Required |
|----------|----------|----------------------|----------------|-----|-----------------|--------------|-----------|---------------|

Contract mapping rules:
  1. "Current Code Location" must be an exact file:function citation
  2. "Current Status" must be one of:
       IMPLEMENTED — Code exists, tested, matches contract
       PARTIAL — Code exists but does not fully match contract
       UNVERIFIED — Code exists but cannot confirm matches contract
       DOCUMENTED — Mentioned in docs, no code found
       PLANNED — Mentioned as planned, no code
       MISSING — Required by contract, no code found
       BLOCKED — Blocked by dependency
       CONTRADICTED — Code contradicts contract
       NO LONGER APPLICABLE — Contract superseded by later decision
  3. "Gap" must describe the specific delta between contract and code
  4. "Breaking?" must be YES/NO/PARTIAL — does closing this gap break existing behavior?
  5. "Test Required" must be YES/NO — is there a test that validates this contract?

The 11 M-ARCH contracts to map (verify exact text from wiki):
  1. CANONICAL MEMORY — Single canonical memory object
  2. MEMORY IDENTITY — Immutable memory_id, lifecycle states
  3. TEMPORAL KNOWLEDGE STATE — Three temporal dimensions
  4. PROVENANCE EVIDENCE — Complete evidence chain
  5. RETRIEVAL — One unified retrieval pipeline
  6. UNIVERSAL AGENT EVENT — Canonical event format
  7. WRITE AUTHORITY — 12×6 authorization matrix
  8. DERIVED STATE — All derived state is rebuildable
  9. FAILURE RECOVERY — Transactional safety, retry, idempotency
  10. SCOPE ISOLATION — Tenant → Workspace → Project boundaries
  11. PERSISTENCE GUARANTEES — Write durability, read consistency

For each contract, the mapping must answer:
  - What in the current codebase IMPLEMENTS this contract?
  - What in the current codebase CONTRADICTS this contract?
  - What is MISSING from the codebase that the contract requires?
  - What TESTS exist that validate this contract?
  - What is the GAP between contract intent and code reality?

================================================================
VERIFICATION STATUS FOR ALL PRELIMINARY FINDINGS
================================================================

The following 41 findings were identified during preliminary review.
For EACH finding, verify against current HEAD and classify:

  CONFIRMED           — Finding matches current code
  CONTRADICTED        — Finding contradicts current code
  PARTIALLY CONFIRMED — Finding partially matches, with specific deltas
  NO LONGER APPLICABLE — Code has changed, finding is stale
  UNVERIFIED          — Cannot determine from available evidence

1.  app/main.py: duplicate AuditService import
2.  app/main.py: AuditService as module-level singleton
3.  app/main.py: lifespan calls audit.register_db_sink()
4.  app/main.py: AuditPersistenceMiddleware uses async_session_factory directly
5.  app/main.py: RequestIdMiddleware references 'response' before assignment
6.  app/services/memory.py: tenant_id fallback to workspace_id (line ~215)
7.  app/services/memory.py: tenant_id read from model (line ~300)
8.  app/services/memory.py: MemoryRecord as canonical model
9.  app/services/memory.py: MemoryTypeMapper type mapping
10. app/services/memory.py: DB + in-memory cache dual store
11. app/services/pipeline.py: M0-M5 sequential in single transaction
12. app/services/pipeline.py: M3 handled inline (not via m3_temporal service)
13. app/services/m3_temporal.py: supersede_fact + supersede_decision functions
14. app/services/m2_facts.py: Regex-based extraction (no LLM)
15. app/services/m5_retrieval.py: BM25 + exponential recency decay
16. app/services/retrieval.py: Hybrid vector+keyword (numpy cosine)
17. app/services/connectors.py: Size guards (10MB/100KB/10K messages)
18. app/services/connectors.py: Multiple connector classes
19. app/services/connectors.py: SHA-256 content hash (16-char)
20. app/services/connectors.py: msg-{idx}-{hash} external ID format
21. app/middleware/rate_limit.py: In-memory sliding window
22. app/middleware/rate_limit.py: _disabled_for_testing flag
23. app/middleware/rbac.py: Role hierarchy OWNER > ADMIN > MEMBER > VIEWER
24. app/middleware/rbac.py: Permission matrix per role
25. app/models.py: Memory.embedding (JSON floats, no pgvector)
26. app/models.py: Memory has temporal_status, confidence, authority
27. app/models.py: Fact/Decision have superseded_by_id
28. app/models.py: Source.content_hash column (migration 008)
29. app/models.py: Policy + PolicyVersion models
30. app/models.py: MessageProvenance tracks retrieval details
31. app/services/audit/service.py: emit() sync + persist() async pattern
32. app/services/audit/service.py: Events accumulate in buffer
33. app/api/memory.py: MemoryService singleton
34. app/api/memory.py: require_policy("memory", "write")
35. app/api/chat.py: process_chat → retrieve → LLM → provenance
36. app/api/chat.py: Default model claude-sonnet-4-5-20250929
37. app/api/auth.py: register creates tenant → workspace → user → membership
38. app/api/auth.py: Refresh tokens stored in DB
39. app/api/ingest.py: Content-hash deduplication
40. app/services/llm.py: Provider abstraction
41. app/services/object_storage*.py: S3 and MinIO backends

For each finding, document:
  - Verdict (CONFIRMED / CONTRADICTED / PARTIALLY CONFIRMED / NO LONGER APPLICABLE / UNVERIFIED)
  - Exact current code evidence (file:line)
  - Delta from original finding (if PARTIALLY CONFIRMED or CONTRADICTED)
  - Impact on architecture analysis

================================================================
AUTHORITATIVE / DERIVED / EPHEMERAL CLASSIFICATION
================================================================

For every data object produced by the M0-M5 pipeline, classify its
epistemic status:

  AUTHORITATIVE — The source system's own representation of reality.
                   Cannot be derived from other data in the system.
                   Example: raw conversation text, user-created Memory records.

  DERIVED       — Computed or extracted from authoritative data.
                   Can be rebuilt from upstream authoritative sources.
                   Example: Facts extracted via regex, Graph edges from Facts.

  EPHEMERAL     — Transient computation result, not stored persistently.
                   Example: Retrieval ranking scores, BM25 scores.

For every stage of M0-M5, document:
  - Stage name and file location
  - Input contract (schema, source)
  - Output object(s)
  - Classification (AUTHORITATIVE / DERIVED / EPHEMERAL)
  - Persistence behavior
  - Rebuildability
  - Failure effect on downstream stages

================================================================
MEMORY INTELLIGENCE READINESS — PER-CAPABILITY ANALYSIS
================================================================

For every capability, require ALL of these fields:

  Capability: <name>
  Current implementation: <exact code location and behavior>
  Evidence: <file:line citations>
  Failure mode: <what breaks if this is wrong>
  Security boundary: <what access controls apply>
  Persistence behavior: <how/when/where it is stored>
  Replay behavior: <can it be regenerated from source data?>
  Known limitation: <what the current code does NOT handle>
  Can Intelligence trust it?: <YES / PARTIAL / NO>
  Why / why not: <specific technical reason>
  Required contract: <what the intelligence layer needs to assume>
  Required implementation phase: <MI-1 through MI-N or "N/A">

Capabilities to analyze:
  1. Record identity (UUID, immutability)
  2. Source attribution (content_hash, source_id linkage)
  3. Temporal ordering (created_at, updated_at, valid_from, valid_until)
  4. Context scope (tenant, workspace, project, user)
  5. Confidence scores (0.0-1.0, computed vs defaulted)
  6. Authority scores (0.0-1.0, computed vs defaulted)
  7. Provenance chain (per-record, per-response, audit)
  8. Relationship graph (nodes, edges, types, direction)
  9. Supersession (old→new replacement, temporal_status)
  10. Contradiction detection (conflicting facts)
  11. Scope isolation (cross-tenant prevention)
  12. Lifecycle management (create, read, update, soft-delete)
  13. Retrieval quality (ranking, relevance, explainability)
  14. Audit trail (complete event history)
  15. Embedding semantics (vector meaning, index availability)

================================================================
CONFLICT RESOLUTION PROTOCOL
================================================================

When specialist agents produce contradictory findings, the synthesis
agent must produce a CONFLICT RECORD — not a compromise.

Format for every conflict:

  CONFLICT C-XXX
  ==============
  Subject: <one-line description>
  Source: Agent N vs Agent M

  Agent N finding:
    <exact quote or summary of finding>

  Agent M finding:
    <exact quote or summary of finding>

  Source evidence:
    <exact file:line citations from the actual codebase>

  Authoritative determination:
    <which agent is correct, and why — based on code, not opinion>

  Impact:
    <which contracts, decisions, or implementation plans are affected>

  Architecture decision affected:
    <specific M-ARCH contract or binding decision>

  Required resolution:
    <what must change in documentation, code, or contracts>

Resolution priority:
  1. Executable source code wins over documentation
  2. Database schema wins over model code (schema is ground truth)
  3. Migration history wins over current schema (shows intent)
  4. Test expectations win over implementation (tests define contract)
  5. Most recent binding decision wins over earlier decisions

================================================================
IMPLEMENTATION DEPENDENCY GRAPH
================================================================

Produce a directed dependency graph of the implementation work required
to reach full M-ARCH contract compliance.

Format per node:

  NODE: <implementation task name>
  PREREQUISITES: [list of node names]
  CURRENT STATE: <what exists today>
  REQUIRED CHANGES: <specific code/model/migration changes>
  MIGRATION RISK: <data migration complexity>
  TEST REQUIREMENTS: <what must be validated>
  ROLLBACK STRATEGY: <how to revert if needed>
  BLOCKS: [list of downstream nodes]
  CONTRACT: <M-ARCH contract(s) this implements>

Example structure:

                 ┌─────────────────────┐
                 │   MEMORY IDENTITY   │
                 │  (immutable UUID)   │
                 └──────────┬──────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
  │  CANONICAL    │ │  PROVENANCE   │ │   TEMPORAL    │
  │   MEMORY      │ │   CHAIN       │ │   STATUS      │
  └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                   ┌───────────────┐
                   │  SAFETY GATE  │
                   │  (write auth) │
                   └───────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
  │ UNIFIED       │ │  EMBEDDING    │ │    GRAPH      │
  │ RETRIEVAL     │ │  PIPELINE     │ │   ENRICHMENT  │
  └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                   ┌───────────────┐
                   │  CONTEXT PACK │
                   │   BUILDER     │
                   └───────┬───────┘
                           │
                           ▼
                   ┌───────────────┐
                   │ AGENT EVENT   │
                   │    LAYER      │
                   └───────────────┘

================================================================
CERTIFICATION GATE
================================================================

At the conclusion of all analysis, produce a certification:

CONTRACT IMPLEMENTATION READINESS CERTIFICATION
================================================

Outcome (select ONE):

  [A] IMPLEMENTATION READY
      All contracts are internally consistent, source-mapped,
      dependency-ordered, and implementation boundaries are unambiguous.

  [B] IMPLEMENTATION READY WITH LIMITATIONS
      Minor unresolved issues exist but do not affect the next
      authorized implementation phase.

  [C] IMPLEMENTATION NOT READY
      One or more contracts conflict, canonical ownership is unresolved,
      or implementation dependencies are ambiguous.

Supporting evidence:
  - Contracts verified: X / 11
  - Contracts with gaps: X
  - Conflicts identified: X
  - Conflicts resolved: X
  - Unresolved conflicts: X
  - Test coverage for contracts: X / 11
  - Breaking changes required: YES / NO / PARTIAL

================================================================
EXECUTION MODEL — THREE CONTROLLED PASSES
================================================================

PASS A — Architecture / Data
  Agents: 1 (Backend), 2 (Data/Memory), 3 (Guardrails)
  Focus: Backend runtime, data lifecycle, pipeline guardrails
  Output: 3 specialist documents

PASS B — Interfaces / Security
  Agents: 4 (API), 5 (Frontend), 6 (Security)
  Focus: API contracts, frontend architecture, security controls
  Output: 3 specialist documents
  Input: Uses PASS A outputs for context

PASS C — Intelligence Readiness
  Agent: 7 (Memory Intelligence Readiness)
  Focus: Can a future MI layer trust the current data?
  Output: 1 specialist document
  Input: Uses PASS A + PASS B outputs

FINAL — Architecture Synthesis
  Reads all 7 specialist documents + existing docs + source
  Produces 7 final documents:
    1. SWARMVAULT_WEBAPP_MASTER_ARCHITECTURE.md
    2. SWARMVAULT_END_TO_END_FLOWS.md
    3. SWARMVAULT_GUARDRAIL_MASTER_MATRIX.md
    4. SWARMVAULT_PERSISTENT_MEMORY_READINESS.md
    5. SWARMVAULT_FRONTEND_BACKEND_ARCHITECTURE.md
    6. SWARMVAULT_ARCHITECTURAL_TRACEABILITY.md
    7. SWARMVAULT_ARCHITECTURAL_GAPS_AND_MEMORY_NEXT_LAYER.md
  Plus the mandatory Contract→Code matrix
  Plus the implementation dependency graph
  Plus the CONTRACT IMPLEMENTATION READINESS certification

================================================================
PARALLEL AGENT PROGRAM (THREE-PASS MODEL)
================================================================

PASS A — Launch agents 1, 2, 3 in parallel:

AGENT 1 — BACKEND RUNTIME ARCHITECTURE
  Output: docs/SWARMVAULT_BACKEND_ARCHITECTURE.md
  Sections:
    1. Application Startup (main.py lifespan, middleware order)
    2. Router Inventory (14 routers, exact endpoints)
    3. Service Layer (all services, initialization pattern)
    4. Repository Pattern (direct queries vs repositories)
    5. Model Layer (all models, columns, relationships, indexes)
    6. Middleware Stack (order, purpose, configuration)
    7. Configuration (settings, env handling)
    8. Dependency Injection (get_db, get_tenant_context, etc.)
    9. Authentication (JWT, refresh tokens, password hashing)
    10. Authorization (RBAC, Policy Engine integration)
    11. Tenancy (TenantContext, workspace membership)
    12. Database Access (AsyncSession, transaction boundaries)
    13. Background Processing (none — verify)
    14. External Providers (LLM, object storage)
    15. Error Handling (validation, sanitization, fail-closed)
    16. Logging (structured logs, request scoping)
    17. Observability (request IDs, latency)
    18. Health/Readiness (/health/live, /health/ready)
    19. Lifecycle/Shutdown
    20. Runtime Dependencies
  Include: representative request traces with exact function calls
  Cite: exact file paths and line numbers for every claim

AGENT 2 — DATA, MEMORY & PERSISTENCE ARCHITECTURE
  Output: docs/SWARMVAULT_DATA_MEMORY_ARCHITECTURE.md
  Sections:
    1. Data Entry Points (all sources of data entering the system)
    2. M0 Normalization (connectors, NormalizedConversation)
    3. M1 Session Understanding (session.py topics, entities)
    4. M2 Fact/Decision Extraction (regex patterns, confidence)
    5. M3 Temporal Processing (supersession, temporal_status)
    6. M4 Graph Construction (GraphNode, GraphEdge)
    7. M5 Retrieval (BM25, recency, graph context, hybrid)
    8. Memory Model (MemoryRecord, MemoryTypeMapper, scopes)
    9. Memory Service (CRUD, cache, cross-tenant isolation)
    10. Provenance (MessageProvenance, MemoryRecord.provenance)
    11. Audit (AuditService, emit→buffer→persist)
    12. Persistence Architecture (PostgreSQL, soft deletion)
    13. Serialization (Pydantic, JSON metadata)
    14. Retrieval Representation (RetrievalResult, scoring)
  For every M0-M5 stage document:
    INPUT → TRANSFORMATION → OUTPUT →
    VALIDATION → GUARDRAIL → FAILURE MODE →
    PERSISTENCE EFFECT → PROVENANCE EFFECT →
    MEMORY QUALITY EFFECT →
    AUTHORITATIVE / DERIVED / EPHEMERAL

AGENT 3 — PIPELINE, GUARDRAIL & VALIDATION ARCHITECTURE
  Output: docs/SWARMVAULT_GUARDRAILS_VALIDATION_ARCHITECTURE.md
  Sections:
    1. Request-Level Guardrails Matrix
       (request ID, security headers, CORS, rate limit, auth, tenancy, RBAC, policy)
    2. Data-Level Guardrails Matrix
       (schema validation, size guards, source-type validation, dedup,
        content hash, temporal supersession, confidence bounds,
        soft deletion, cross-tenant isolation, error sanitization)
    3. Memory Safety Gate Matrix
       (conditions required before data becomes persistent memory)
    4. Adversarial Input Analysis
       (can malformed/adversarial input cross stages?)
    5. Error Path Analysis
       (is the error handler itself a vulnerability surface?)
  For every guardrail:
    ACTIVE / PARTIAL / DOCUMENTED / MISSING / BYPASSABLE / UNTESTED

PASS B — After PASS A completes, launch agents 4, 5, 6:

AGENT 4 — API / CONTRACT / INTEGRATION ARCHITECTURE
  Output: docs/SWARMVAULT_API_INTEGRATION_ARCHITECTURE.md
  Sections:
    1. Route Inventory (every endpoint, method, auth, schema)
    2. Authentication Flow (register, login, refresh, logout)
    3. Workspace/Project Flow
    4. Session Flow
    5. Chat Flow (including SSE)
    6. Memory Flow (CRUD, search)
    7. Ingestion Flow (upload, dedup, pipeline trigger)
    8. Source/Fact/Decision/Graph Flow
    9. Provenance Flow
    10. Storage Flow
    11. API Key Flow
    12. Policy Flow
    13. Audit Flow
    14. Integration Classification
        (Claude Code, Codex, Universal Adapter, MCP, REST, SSE,
         external LLM providers, S3, MinIO)
        For each: IMPLEMENTED / PARTIAL / UNVERIFIED / DOCUMENTED /
                  PLANNED / MISSING / BLOCKED
    15. Error Contracts (format, status codes)
  Include: frontend→API→backend→DB trace for each endpoint

AGENT 5 — FRONTEND ARCHITECTURE
  Output: docs/SWARMVAULT_FRONTEND_ARCHITECTURE.md
  Sections:
    1. Next.js Architecture (App Router, layouts, server/client)
    2. Component Architecture
    3. State Management
    4. API Client
    5. Authentication Flow
    6. Knowledge Views (all screens)
    7. SSE Handling
    8. Security
    9. Responsive Architecture
  Include matrix:
    Screen → Component → State → API Endpoint → Backend Router →
    Service → Database Model → Response → UI Rendering
  Identify frontend/backend mismatches

AGENT 6 — SECURITY, TENANCY & OPERATIONAL ARCHITECTURE
  Output: docs/SWARMVAULT_SECURITY_OPERATIONAL_ARCHITECTURE.md
  Sections:
    1. Authentication Deep Dive (JWT, refresh, password)
    2. Authorization Deep Dive (RBAC, Policy Engine, fail-closed)
    3. Tenancy Isolation (hierarchy, enforcement, cross-tenant prevention)
    4. Security Headers (CSP, HSTS, etc.)
    5. CORS Configuration
    6. Error Sanitization
    7. Audit & Provenance
    8. Database Security
    9. Secret Handling (API keys, tokens)
    10. Rate Limiting
    11. Deployment Security (Docker, env)
    12. Operational (health, logging, migrations)
  For every control:
    CONTROL | LOCATION | ENFORCEMENT POINT | TEST | FAILURE BEHAVIOR | BYPASS RISK

PASS C — After PASS A+B complete:

AGENT 7 — MEMORY INTELLIGENCE READINESS ARCHITECTURE
  Output: docs/SWARMVAULT_MEMORY_INTELLIGENCE_READINESS.md
  THIS IS THE MOST IMPORTANT SPECIALIST.
  Sections:
    1. Current Memory Implementation
    2. Provenance Chain Analysis
    3. Confidence & Authority Assessment
    4. Temporal Semantics Analysis
    5. Graph Relationships Assessment
    6. Scope & Isolation Assessment
    7. Lifecycle Analysis
    8. Retrieval Explainability
    9. MEMORY READINESS SCORECARD
       (15 capabilities with: Current implementation, Evidence,
        Failure mode, Security boundary, Persistence behavior,
        Replay behavior, Known limitation, Can Intelligence trust it?,
        Why/why not, Required contract, Required implementation phase)
    10. PERSISTENT MEMORY READINESS
    11. MEMORY INTELLIGENCE READINESS
        CAN TRUST:
          - List with evidence
        CANNOT TRUST YET:
          - List with evidence
    12. NEXT MEMORY INTELLIGENCE LAYER — BOUNDARY
        What the current system can safely provide
        What the next layer can trust
        What the next layer must not assume
        What contracts must exist before implementation

FINAL — Architecture Synthesis Agent
  Reads all 7 specialist documents
  Reads existing docs/ (all M-ARCH contracts, gap analyses, decisions)
  Reads backend source (app/)
  Reads frontend source (frontend/)
  Reads migrations (alembic/versions/)
  Reads tests (tests/)
  Reads deployment config
  Reconciles contradictions against source code
  Produces 7 final documents + Contract→Code matrix + dependency graph + certification

================================================================
OUTPUT DOCUMENTS
================================================================

FINAL DOCUMENT 1 — docs/SWARMVAULT_WEBAPP_MASTER_ARCHITECTURE.md
  31 required sections (Executive Summary through Architectural Readiness Assessment)

FINAL DOCUMENT 2 — docs/SWARMVAULT_END_TO_END_FLOWS.md
  25 flows (FLOW-001 through FLOW-025)
  Each: Trigger → Input → Validation → Guardrails → Processing →
        Persistence → Output → Failure behavior → Security boundary

FINAL DOCUMENT 3 — docs/SWARMVAULT_GUARDRAIL_MASTER_MATRIX.md
  Complete guardrail matrix + MEMORY SAFETY GATE MATRIX

FINAL DOCUMENT 4 — docs/SWARMVAULT_PERSISTENT_MEMORY_READINESS.md
  15 capabilities classified GREEN / YELLOW / RED

FINAL DOCUMENT 5 — docs/SWARMVAULT_FRONTEND_BACKEND_ARCHITECTURE.md
  Screen → Component → State → API → Backend → DB → Response → UI matrix

FINAL DOCUMENT 6 — docs/SWARMVAULT_ARCHITECTURAL_TRACEABILITY.md
  REQUIREMENT → FEATURE → FRONTEND → API → SERVICE →
  DATA MODEL → PIPELINE → GUARDRAIL → TEST → PERSISTENCE → PROVENANCE

FINAL DOCUMENT 7 — docs/SWARMVAULT_ARCHITECTURAL_GAPS_AND_MEMORY_NEXT_LAYER.md
  P0/P1/P2/P3 gaps + NEXT MEMORY INTELLIGENCE LAYER READINESS BOUNDARY

MANDATORY ADDITIONAL OUTPUTS:
  docs/SWARMVAULT_CONTRACT_CODE_MATRIX.md    — 11 M-ARCH contracts vs code
  docs/SWARMVAULT_IMPLEMENTATION_DEPENDENCY_GRAPH.md
  docs/SWARMVAULT_CONTRACT_IMPLEMENTATION_READINESS_CERTIFICATION.md

================================================================
DOCUMENT FORMAT REQUIREMENTS
================================================================

Every document must:
  1. Start with: Document name, version, date, baseline SHA
  2. Include a table of contents
  3. Use consistent heading hierarchy (##, ###, ####)
  4. Include exact file paths and line numbers for ALL claims
  5. Use code blocks for exact code citations
  6. Use tables for all matrices
  7. Include numbered Findings section
  8. Include Recommendations section (documentation only — never code changes)
  9. Include Verification section with test file references
  10. End with Open Questions section

Classification key for every capability:
  [IMPLEMENTED] / [PARTIAL] / [UNVERIFIED] / [DOCUMENTED] /
  [PLANNED] / [MISSING] / [BLOCKED] / [CONTRADICTED] /
  [NO LONGER APPLICABLE] / [UNKNOWN]

SHA integrity gate footer on every document:
  Baseline SHA: e6f4b1c157afaed052584963b942ea04f9661610
  Verified against: <git rev-parse HEAD at time of writing>

================================================================
KNOWN M-ARCH CONTRACTS TO VERIFY
================================================================

The following contracts exist in docs/. Read each one and map against code:

  CANONICAL_MEMORY_CONTRACT.md
  MEMORY_IDENTITY_CONTRACT.md
  TEMPORAL_KNOWLEDGE_STATE_CONTRACT.md
  PROVENANCE_EVIDENCE_CONTRACT.md
  CANONICAL_RETRIEVAL_CONTRACT.md
  UNIVERSAL_AGENT_EVENT_CONTRACT.md
  MEMORY_WRITE_AUTHORITY_MATRIX.md
  DERIVED_STATE_CONTRACT.md
  MEMORY_FAILURE_RECOVERY_CONTRACT.md

Additional reference documents:
  MEMORY_ARCHITECTURE_DECISION_RECORD.md
  MEMORY_INTELLIGENCE_READINESS_CERTIFICATION.md
  SWARMVAULT_MASTER_GAP_SYNTHESIS.md
  SWARMVAULT_ARCHITECTURAL_GAPS_AND_MEMORY_NEXT_LAYER.md

Read all of these before beginning analysis. They are the contracts
against which the codebase must be reconciled.

================================================================
BEGIN RECONCILIATION
================================================================

Step 1: Record START SHA
Step 2: Read all M-ARCH contract documents from docs/
Step 3: Read all existing analysis documents from docs/
Step 4: Launch PASS A agents (1, 2, 3) in parallel
Step 5: After PASS A, launch PASS B agents (4, 5, 6) in parallel
Step 6: After PASS B, launch PASS C agent (7)
Step 7: Launch final Architecture Synthesis agent
Step 8: Record END SHA
Step 9: Verify END SHA == START SHA
Step 10: If SHA matches, produce CONTRACT IMPLEMENTATION READINESS certification
"""
