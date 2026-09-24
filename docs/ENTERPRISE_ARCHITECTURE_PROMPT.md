# SwarmVault WebApp — Enterprise Architecture Forensic Analysis Prompt
# v2.0 (codebase-grounded, SwarmVaultwebapp)

## REPOSITORY IDENTITY (established before analysis begins)

```
REPOSITORY_ROOT  : C:\Users\Administrator\Documents\SwarmVaultwebapp
BACKEND_ROOT     : C:\Users\Administrator\Documents\SwarmVaultwebapp\app
FRONTEND_ROOT    : C:\Users\Administrator\Documents\SwarmVaultwebapp\frontend
FRONTEND_FRAMEWORK: Next.js 15 (App Router) + React 18 + Tailwind CSS 3.4
BACKEND_FRAMEWORK : FastAPI + SQLAlchemy 2.x + Alembic
STATE_MANAGEMENT  : React Context (AuthProvider) — no Redux/Zustand/Jotai
UI_LIBRARY        : Hand-rolled 15-component set (src/components/ui/) — no shadcn/ui, no Radix
```

## FRAMEWORK: You are a panel of nine specialist architects.
You DO NOT modify product code. You DO NOT invent features.
Every claim must trace to an actual file, function, route, model, migration,
test, or configuration entry.

---

## PHASE 0 — BASELINE ESTABLISHMENT

Before any analysis, record and persist:

```markdown
# File: docs/ARCHITECTURE_FORENSICS_BASELINE.md

- Git branch:       <from `git branch --show-current`>
- HEAD SHA:         <from `git rev-parse HEAD`>
- Commit date:      <from `git log -1 --format=%ci`>
- Working tree:     <clean / dirty + untracked files>
- Backend root:     app/
- Frontend root:    frontend/
- Test command:     <discover from pyproject.toml / package.json / Makefile>
- DB engine:        <from alembic.ini / app/db.py>
- Migrations count: <from `alembic/versions/` file list>
- Python version:   <from .python-version or runtime>
- Node version:     <from .nvmrc or package.json engines>
```

If baseline cannot be established (no git, no identifiable root), STOP and report.

---

## PHASE 1 — PARALLEL SPECIALIST ANALYSIS

Launch **9 parallel specialist agents** (one per domain).
Each agent writes ONLY to its own output file under `docs/`.
No agent may read another agent's output file (avoids circular contamination).

### AGENT 1 — BACKEND RUNTIME ARCHITECTURE
**Output:** `docs/SWARMVAULT_BACKEND_ARCHITECTURE.md`

Inspect and document every one of the following, with exact file/function evidence:

#### 1.1 Application Bootstrap
- Entry point: `app/main.py`
- FastAPI app construction (which middleware registered, in which order)
- Lifespan events (startup, shutdown)
- CORS configuration (origins, methods, headers)
- Exception handlers
- Static file mounting
- Root router inclusion

#### 1.2 Router / Endpoint Inventory
For every file in `app/api/`:
- Module path: `app/api/<name>.py`
- APIRouter prefix, tags
- Every route: path, method, name, dependencies, response_model
- Authentication requirement (Depends(get_current_user) etc.)
- Authorization requirement (Depends(require_role / require_permission))
- Tenancy enforcement (workspace_id filter, tenant_id injection)
- Request schema (Pydantic model)
- Response schema (Pydantic model)
- Error paths (HTTPException raises)
- Background task attachments

**Routers to cover:**
`app/api/auth.py`, `app/api/projects.py`, `app/api/sessions.py`,
`app/api/memory.py`, `app/api/ingest.py`, `app/api/chat.py`,
`app/api/provenance.py`, `app/api/feedback.py`, `app/api/audit.py`,
`app/api/storage.py`, `app/api/workspace.py`, `app/api/dashboard.py`,
`app/api/api_keys.py`, `app/api/policy.py`

#### 1.3 Service Layer
For every file in `app/services/`:
- Class/function name and purpose
- Public interface
- Dependencies injected
- Database sessions used
- External calls made (LLM APIs, object storage, etc.)
- Error handling strategy
- Return types and shapes

**Services to cover:**
`app/services/pipeline.py` (M0-M5 orchestrator),
`app/services/m1_session.py` (session understanding),
`app/services/m2_facts.py` (fact/decision extraction),
`app/services/m3_temporal.py` (temporal processing),
`app/services/m4_graph.py` (graph construction),
`app/services/m5_retrieval.py` (retrieval),
`app/services/chat_orchestrator.py` (SSE chat),
`app/services/llm.py` (LLM provider abstraction),
`app/services/memory.py` (memory operations),
`app/services/retrieval.py` (search/retrieval),
`app/services/audit/` (audit logging),
`app/services/policy/` (policy engine + evaluator + dependencies),
`app/services/connectors.py` (source adapters),
`app/services/object_storage.py`, `object_storage_s3.py`, `object_storage_minio.py`,
`app/services/tools.py` (tool runtime + registry)

#### 1.4 Data Models
From `app/models.py`, document every SQLAlchemy model:
- Table name
- Columns with types, constraints, defaults
- Primary keys, foreign keys
- Unique constraints, indexes
- Relationships (and cascade behavior)
- Soft-delete fields (`deleted_at`)
- Tenant/workspace scoping fields

Models to enumerate:
`Tenant`, `Workspace`, `User`, `WorkspaceMember`, `Invitation`,
`RefreshToken`, `Project`, `Session`, `Message`, `Source`,
`Memory`, `Fact`, `Decision`, `GraphNode`, `GraphEdge`,
`ApiKey`, `AuditEvent`, `PolicyRule`, `ToolExecution`,
`SourceContentHash`, and any others present.

#### 1.5 Authentication & Authorization Flow
- `app/api/auth.py` routes: register, login, refresh, logout, me
- Password hashing mechanism
- JWT token creation and validation
- Refresh token storage and rotation
- `app/core/security.py` functions
- `app/middleware/rbac.py` enforcement
- `app/middleware/tenancy.py` workspace/tenant injection
- API key authentication (`app/api/api_keys.py`)

#### 1.6 Middleware Stack
Order matters. List middleware in execution order:
- `app/middleware/tenancy.py` — tenant resolution
- `app/middleware/rbac.py` — role enforcement
- Any additional middleware

For each middleware document:
- Registration point (main.py)
- Execution order
- What it inspects/modifies in the request
- What it adds to the request state
- Failure behavior (does it allow or block?)

#### 1.7 Configuration
From `app/core/config.py`:
- All settings fields
- Defaults
- Environment variable sources
- Secrets handling
- Feature flags if any

#### 1.8 Database
From `app/db.py`:
- Engine creation
- Session factory
- Base class
- Dependency injection pattern (get_db)
- Transaction boundaries
- Connection pooling

#### 1.9 Background Processing
- BackgroundTasks usage in routes
- Celery/Redis/RQ if present
- Any async fire-and-forget patterns

#### 1.10 External Provider Integration
- LLM provider configuration (`app/services/llm.py`)
- Object storage backends (S3, MinIO, local)
- How providers are selected at runtime

#### 1.11 Error Handling
- Exception handlers in main.py
- HTTPException usage patterns
- Error response format consistency
- Logging configuration

#### 1.12 Request Trace
Trace a complete request end-to-end:
```
HTTP Request
→ CORS preflight (if applicable)
→ Middleware (tenancy)
→ Middleware (RBAC)
→ Authentication (Depends)
→ Authorization (Depends)
→ Router match
→ Request body validation (Pydantic)
→ Service function
→ Database session
→ Response serialization
→ HTTP response
```
Use a concrete example route (e.g., POST /api/v1/projects) and show each step.

---

### AGENT 2 — DATA, MEMORY & PERSISTENCE ARCHITECTURE
**Output:** `docs/SWARMVAULT_DATA_MEMORY_ARCHITECTURE.md`

#### 2.1 Data Model Inventory (from `app/models.py`)
For each model, document:
- Purpose in the data architecture
- Lifecycle (created by whom, when, how)
- Relationships to other models
- Fields that carry semantic meaning beyond storage

#### 2.2 Database Migrations
From `alembic/versions/`:
- 001_initial.py — baseline schema
- 002_provenance.py
- 003_sprint3_pipeline.py
- 004_add_memory_sprint4_columns.py
- 005_add_message_feedback.py
- 006_add_temporal_to_graph_nodes.py
- 007_add_api_keys.py
- 008_add_source_content_hash.py
- 009_add_policy_engine.py
- 010_add_audit_events.py
- 011_add_tenant_to_memory.py
- 012_add_invitations.py

For each migration:
- What tables/columns were added or modified
- Why (inferred from column names and context)
- What capability it enables

#### 2.3 M0–M5 Pipeline Architecture
From `app/services/pipeline.py`, `m1_session.py`, `m2_facts.py`, `m3_temporal.py`, `m4_graph.py`, `m5_retrieval.py`:

For each stage M0 through M5:

| Field | Content |
|-------|---------|
| STAGE | M0 / M1 / M2 / M3 / M4 / M5 |
| NAME | Human-readable name |
| INPUT | What data enters this stage (exact model/type) |
| TRANSFORMATION | What processing occurs (LLM calls, rules, algorithms) |
| OUTPUT | What data exits (exact model/type) |
| VALIDATION | How output is validated |
| GUARDRAIL | Safety mechanisms |
| FAILURE MODE | What happens on failure |
| PERSISTENCE EFFECT | What gets written to database |
| PROVENANCE EFFECT | What provenance is recorded |
| MEMORY QUALITY EFFECT | How this affects trustworthiness as memory |

#### 2.4 Ingestion Architecture
From `app/api/ingest.py` and `app/services/connectors.py`:
- Supported source types (chatgpt, jsonl, text, etc.)
- Upload flow (multipart form)
- File processing pipeline
- JSON validation
- JSONL parsing
- Content hash computation (source_content_hash)
- Deduplication mechanism
- Error handling for malformed input

#### 2.5 Memory Architecture
From `app/models.py` Memory model and `app/services/memory.py`:
- Memory record fields: id, content, memory_type, confidence, authority, status
- Memory types (semantic, episodic, procedural, etc.)
- Confidence scoring: how is it set? by whom? what scale?
- Authority levels: what are they? how enforced?
- Status field: what values? what transitions?
- Soft deletion
- Supersession mechanism

#### 2.6 Fact & Decision Architecture
From `app/models.py` Fact and Decision models:
- Fact fields and semantics
- Decision fields and semantics
- Relationship to sessions and sources
- Temporal properties

#### 2.7 Graph Architecture
From `app/models.py` GraphNode and GraphEdge models:
- Node types
- Edge types
- Temporal annotations
- Authority levels
- Confidence scores
- Community detection (if implemented)

#### 2.8 Provenance Architecture
From `app/models.py` and `app/api/provenance.py`:
- What is tracked
- How chain of custody is maintained
- What cannot be traced

#### 2.9 Retrieval Architecture
From `app/services/retrieval.py` and `m5_retrieval.py`:
- Search mechanisms
- Vector search (if any)
- Graph traversal
- Filtering and ranking
- Temporal filtering
- Result explanation

---

### AGENT 3 — PIPELINE, GUARDRAIL & VALIDATION ARCHITECTURE
**Output:** `docs/SWARMVAULT_GUARDRAILS_VALIDATION_ARCHITECTURE.md`

#### 3.1 Complete Guardrail Matrix

Build this table covering EVERY stage of data processing:

| # | Stage | Input Contract | Output Contract | Validation | Guardrail | Failure Mode | Status |
|---|-------|---------------|-----------------|------------|-----------|--------------|--------|
| 1 | HTTP Request | | | | | | |
| 2 | CORS | | | | | | |
| 3 | Authentication | | | | | | |
| 4 | Authorization (RBAC) | | | | | | |
| 5 | Tenancy Injection | | | | | | |
| 6 | Request Body Validation (Pydantic) | | | | | | |
| 7 | Route Handler | | | | | | |
| 8 | Service Dispatch | | | | | | |
| 9 | M0 Ingestion | | | | | | |
| 10 | M0 Validation | | | | | | |
| 11 | M1 Session Understanding | | | | | | |
| 12 | M2 Fact/Decision Extraction | | | | | | |
| 13 | M3 Temporal Processing | | | | | | |
| 14 | M4 Graph Construction | | | | | | |
| 15 | M5 Retrieval Indexing | | | | | | |
| 16 | Persistence | | | | | | |
| 17 | Retrieval | | | | | | |
| 18 | Response Serialization | | | | | | |
| 19 | Error Sanitization | | | | | | |

For each guardrail, classify as:
- **ACTIVE** — enforced in code, tested
- **PARTIAL** — exists but has gaps
- **DOCUMENTED** — documented but not enforced
- **MISSING** — not present at all
- **BYPASSABLE** — can be circumvented
- **UNTESTED** — present but no test coverage

#### 3.2 Validation Layers
Document each validation layer:
- Pydantic schemas (request/response)
- Database constraints (NOT NULL, UNIQUE, FK)
- Application-level validation
- Policy engine validation
- LLM output validation

#### 3.3 Security Headers
- CORS origins, methods, headers
- CSP headers (if present)
- HSTS (if present)
- X-Frame-Options (if present)
- Other security headers

#### 3.4 Rate Limiting
- Where is rate limiting applied?
- At what granularity (per user, per workspace, per IP)?
- What happens on limit breach?

#### 3.5 Secret Handling
- How are API keys stored?
- How are JWT secrets managed?
- Secret rotation (if any)
- Secret exposure risk in logs

#### 3.6 Adversarial Input Analysis
For each stage, answer:
- Can malformed JSON cross this stage?
- Can oversized payloads cross this stage?
- Can SQL injection reach the database?
- Can XSS reach the frontend?
- Can path traversal reach the filesystem?
- Can SSRF reach external services?

---

### AGENT 4 — API / CONTRACT / INTEGRATION ARCHITECTURE
**Output:** `docs/SWARMVAULT_API_INTEGRATION_ARCHITECTURE.md`

#### 4.1 Complete API Route Inventory
For every route in every router file, document:

| Router | Route | Method | Auth | RBAC | Tenancy | Request Schema | Response Schema | Errors |
|--------|-------|--------|------|------|---------|----------------|-----------------|--------|

#### 4.2 API Contract Analysis
- Response envelope format (is it consistent?)
- Error format (is it consistent across routers?)
- Pagination (is it used consistently?)
- Filtering (available where?)
- Sorting (available where?)

#### 4.3 SSE / Streaming
From `app/api/chat.py`:
- Endpoint: `/api/v1/chat/stream`
- Event types: token, done, error
- Connection lifecycle
- Client-side handling (`frontend/src/lib/api.ts` `streamChat`)
- Timeout handling
- Reconnection behavior

#### 4.4 External Integrations
For each integration, classify:
- Claude Code integration: **IMPLEMENTED / PARTIAL / DOCUMENTED / PLANNED / MISSING / UNVERIFIED**
- Codex integration: same classification
- Universal Adapter: same classification
- MCP server: same classification
- External LLM providers: same classification
- Object storage (S3, MinIO, local): same classification

For each integration provide:
- Evidence (file path, function)
- What it connects to
- What data flows through it
- Error handling
- Configuration

#### 4.5 Frontend-Backend Contract
For each frontend API call (`frontend/src/lib/api.ts` and inline fetches):
- Frontend caller
- API path
- Method
- Expected response shape
- Error handling
- Token refresh interaction
- Mismatches between what frontend expects and what backend returns

#### 4.6 API Versioning
- Is the API versioned? How?
- `/api/v1/` prefix evidence
- Deprecation policy (if any)
- Breaking change handling

---

### AGENT 5 — FRONTEND ARCHITECTURE
**Output:** `docs/SWARMVAULT_FRONTEND_ARCHITECTURE.md`

#### 5.1 Next.js App Router Structure
List every route with its type (page, layout) and client/server boundary:

| Route | File | 'use client'? | Purpose |
|-------|------|---------------|---------|
| / | page.tsx | Yes | Redirect |
| /auth/login | page.tsx | Yes | Login |
| /auth/register | page.tsx | Yes | Register |
| /dashboard | page.tsx | Yes | Dashboard |
| /projects | page.tsx | Yes | Projects list |
| /projects/[id] | layout.tsx | Yes | Project shell + sidebar |
| /projects/[id]/chat | page.tsx | Yes | Chat |
| /projects/[id]/ingest | page.tsx | Yes | Ingestion |
| /projects/[id]/sessions | page.tsx | Yes | Sessions list |
| /projects/[id]/sessions/[sessionId] | page.tsx | Yes | Session detail |
| /projects/[id]/memory | page.tsx | Yes | Memory |
| /projects/[id]/facts | page.tsx | Yes | Facts |
| /projects/[id]/decisions | page.tsx | Yes | Decisions |
| /projects/[id]/timeline | page.tsx | Yes | Timeline |
| /projects/[id]/search | page.tsx | Yes | Search |
| /projects/[id]/graph | page.tsx | Yes | Graph |
| /projects/[id]/provenance | page.tsx | Yes | Provenance |
| /projects/[id]/settings | page.tsx | Yes | Settings |
| /settings | page.tsx | Yes | User settings |
| /settings/profile | page.tsx | Yes | Profile |
| /settings/api-keys | page.tsx | Yes | API keys |
| /settings/storage | page.tsx | Yes | Storage config |

#### 5.2 Component Architecture
From `frontend/src/components/`:
- `Sidebar.tsx` — navigation sidebar
- `ui/` — 15 hand-rolled primitives

Document:
- Component hierarchy
- Prop interfaces
- State management (local useState vs context)
- Event flow

#### 5.3 State Management
- `useAuth` — auth state (user, loading, error, login, register, logout)
- `useTheme` — theme state
- `AppShell` — routing guard
- Per-page local state
- No global state library

#### 5.4 API Client Layer
From `frontend/src/lib/api.ts`:
- `getToken()` — token retrieval from localStorage
- `refreshAccessToken()` — refresh flow
- `request()` — generic request with auth + 401 retry
- `apiGet`, `apiPost`, `apiPatch`, `apiDelete`
- `streamChat()` — SSE streaming
- `uploadFile()` — multipart upload with progress
- Token storage format: `localStorage['sv_tokens']` = `{ access_token, refresh_token }`

#### 5.5 Authentication Flow
- Login: POST /api/v1/auth/login → store tokens → fetch /api/v1/auth/me
- Register: POST /api/v1/auth/register → store tokens → fetch /api/v1/auth/me
- Token refresh: automatic on 401
- Logout: POST /api/v1/auth/logout → clear tokens
- Session guard: AppShell redirects unauthenticated users

#### 5.6 Routing & Navigation
- AppShell provides sidebar for authenticated users
- Project layout provides sub-navigation
- Route guards (redirect logic)
- Navigation state

#### 5.7 Frontend → Backend Data Flow Matrix
For every significant screen:

| Screen | Components | State | API Calls | Backend Router | Data Model |
|--------|-----------|-------|-----------|----------------|------------|

#### 5.8 Styling Architecture
- Tailwind CSS 3.4 with custom design tokens
- CSS custom properties in `globals.css`
- Dark/light theme via `data-theme` attribute
- Token naming convention: `--sv-*`
- No CSS modules, no SCSS

#### 5.9 Frontend-Backend Mismatches
Identify any places where:
- Frontend expects a field that backend doesn't return
- Frontend sends a field that backend doesn't accept
- Frontend handles an error format backend doesn't produce
- Frontend assumes a behavior backend doesn't implement

---

### AGENT 6 — SECURITY, TENANCY & OPERATIONAL ARCHITECTURE
**Output:** `docs/SWARMVAULT_SECURITY_OPERATIONAL_ARCHITECTURE.md`

#### 6.1 Authentication Architecture
- Password hashing: algorithm, parameters
- JWT: algorithm, expiration, claims
- Refresh tokens: storage, rotation, revocation
- Session management
- "Remember me" (if present)

#### 6.2 Authorization Architecture
From `app/middleware/rbac.py` and `app/services/policy/`:
- Role definitions (OWNER, ADMIN, MEMBER, VIEWER)
- Permission model
- Policy engine: `PolicyEngine`, `PolicyEvaluator`, `PolicyRepository`
- Effect types: ALLOW, DENY, CONFIRM, LIMITED
- Confirmation flow (migration 007)
- Where authorization is checked (per-route dependency)

#### 6.3 Tenancy Architecture
From `app/middleware/tenancy.py`:
- How tenant_id is resolved from request
- How workspace_id is resolved
- How tenancy is injected into database queries
- Cross-tenant data leak prevention
- Workspace-member relationship
- Invitation flow

#### 6.4 API Key Architecture
From `app/api/api_keys.py` and `app/models.py` ApiKey model:
- Key format (prefix + secret)
- Key hashing
- Scoping (workspace-level?)
- Rotation
- Revocation
- Usage tracking

#### 6.5 Database Security
- Connection security (SSL?)
- Query parameterization (SQLAlchemy ORM — inherent protection)
- Soft delete (no hard deletes?)
- Row-level security (if any)
- Migration safety

#### 6.6 Secret Management
- Environment variables used
- .env files (document which ones exist, NOT their values)
- Secret rotation policy
- Secret in logs risk

#### 6.7 Error Handling & Information Leakage
- Do error messages expose internal state?
- Do stack traces reach the client?
- Are database errors sanitized?
- Are third-party errors sanitized?

#### 6.8 Audit Architecture
From `app/services/audit/`:
- What events are audited?
- Audit event schema
- Storage mechanism
- Immutability guarantees
- Retention policy
- Search/query capabilities

#### 6.9 Operational Concerns
- Health check endpoints
- Readiness probes
- Graceful shutdown
- Logging configuration
- Docker configuration (Dockerfile, docker-compose)
- Environment configuration
- Backup/restore (if any)

#### 6.10 Security Control Matrix

| Control | Location | Enforcement Point | Test | Failure Behavior | Bypass Risk |
|---------|----------|-------------------|------|-----------------|-------------|

---

### AGENT 7 — FRONTEND-BACKEND CONTRACT & INTEGRATION ARCHITECTURE
**Output:** `docs/SWARMVAULT_FRONTEND_BACKEND_CONTRACT.md`

#### 7.1 API Client Contract
Document the exact contract between frontend API client and backend:

For each API method (`apiGet`, `apiPost`, `apiPatch`, `apiDelete`, `streamChat`, `uploadFile`):
- Method signature
- Request format
- Response handling
- Error handling
- Token refresh integration
- Timeout behavior

#### 7.2 TypeScript Type Safety
From `frontend/src/types/api.ts`:
- Type definitions
- Are they derived from backend schemas or hand-written?
- Drift risk (do they match backend?)
- Missing types

#### 7.3 Screen-by-Screen Contract Verification
For each frontend screen, verify:
- What API calls it makes
- What data it expects
- What the backend actually returns
- Any mismatches

#### 7.4 SSE Streaming Contract
- Frontend expects: `{ type: "token"|"done"|"error", content?: string, detail?: string }`
- Backend sends: verify actual SSE event format
- Encoding: verify SSE format (data: prefix, double newline)
- Buffer handling: verify partial line handling
- Abort signal support

#### 7.5 File Upload Contract
- Frontend sends: multipart FormData with project_id, source_type, file
- Backend expects: verify actual ingest endpoint
- Progress tracking: XHR-based
- Response: { source_id, status }

#### 7.6 Authentication Contract
- Token storage: localStorage key `sv_tokens`
- Token format: `{ access_token, refresh_token }`
- Frontend sends: `Authorization: Bearer <token>` header
- 401 handling: auto-refresh, clear on failure
- Logout: POST /api/v1/auth/logout with refresh_token

#### 7.7 Error Contract
- Frontend expects: `{ detail, message }` or plain text
- Backend produces: verify actual error response format
- HTTP status codes used
- Consistency across endpoints

---

### AGENT 8 — MEMORY INTELLIGENCE READINESS ARCHITECTURE
**Output:** `docs/SWARMVAULT_MEMORY_INTELLIGENCE_READINESS.md`

This is the most critical analyst. Determine readiness for persistent memory.

#### 8.1 Data Quality Model
For each memory-capable entity (Session, Message, Memory, Fact, Decision, GraphNode, GraphEdge):

| Dimension | Session | Message | Memory | Fact | Decision | GraphNode | GraphEdge |
|-----------|---------|---------|--------|------|----------|-----------|-----------|
| Identity (stable ID) | | | | | | | |
| Source (where it came from) | | | | | | | |
| Time (when it occurred) | | | | | | | |
| Context (which workspace/project) | | | | | | | |
| Confidence (how sure) | | | | | | | |
| Authority (who decided) | | | | | | | |
| Provenance (chain of custody) | | | | | | | |
| Relationships (what connects) | | | | | | | |
| Supersession (can be replaced) | | | | | | | |
| Contradiction (can conflict) | | | | | | | |
| Scope (visible to whom) | | | | | | | |
| Lifecycle (creation → retirement) | | | | | | | |
| Retrievability (can be found) | | | | | | | |
| Explainability (why returned) | | | | | | | |
| Auditability (change log) | | | | | | | |

For each cell: **YES / NO / PARTIAL** with evidence.

#### 8.2 Pipeline Quality Assessment
For each M0-M5 stage:
- Does it produce output suitable for persistent memory?
- What quality gates exist?
- What quality gates are MISSING?
- Can adversarial or low-quality data become persistent memory?

#### 8.3 Persistent Memory Boundary
Define what "persistent memory" means for SwarmVault:
- What data is currently persistent? (survives sessions, survives projects)
- What data is ephemeral? (lost on certain operations)
- What data is normalized enough to be trusted?
- What data has sufficient provenance?

#### 8.4 Memory Intelligence Boundary
Define what a "Memory Intelligence Layer" would need:
- What can it safely consume TODAY?
- What must it NOT consume yet?
- What contracts must exist before it can operate?

#### 8.5 Trust Scoring
For each memory type, assess:
- Can it be trusted as factual?
- Can it be trusted as durable?
- Can it be trusted as explainable?
- What would raise or lower trust?

---

### AGENT 9 — DEPLOYMENT, OBSERVABILITY & TECHNICAL DEBT
**Output:** `docs/SWARMVAULT_DEPLOYMENT_DEBT_ARCHITECTURE.md`

#### 9.1 Deployment Architecture
- Dockerfile (if present)
- docker-compose (if present)
- Environment variables
- Volume mounts
- Network topology
- Process management

#### 9.2 Observability
- Logging: framework, format, destinations
- Metrics: any metrics collection?
- Tracing: any distributed tracing?
- Health endpoints
- Readiness probes

#### 9.3 Technical Debt Inventory
From code inspection, identify:
- Unused imports/dead code
- Incomplete implementations (TODO, FIXME, placeholder)
- Security vulnerabilities
- Performance concerns
- Architectural inconsistencies
- Missing error handling
- Missing tests for critical paths
- Code smells

#### 9.4 Test Architecture
- Test framework
- Test locations
- Test categories (unit, integration, e2e)
- What's tested vs what's not
- Test quality (assertions vs smoke)

---

## PHASE 2 — SYNTHESIS

After all 9 specialist documents are complete, produce:

### DOCUMENT 10: Master Architecture
**File:** `docs/SWARMVAULT_WEBAPP_MASTER_ARCHITECTURE.md`

Synthesize all specialist findings into a single coherent document with:
1. Executive Summary
2. System Context (C4 diagram in Mermaid)
3. Backend Architecture
4. Frontend Architecture
5. Data Architecture
6. Memory Architecture
7. Security Architecture
8. API Architecture
9. Pipeline Architecture (M0-M5)
10. Guardrail Architecture
11. Provenance Architecture
12. Deployment Architecture
13. Memory Intelligence Readiness
14. Technical Debt Register
15. Contradiction Register
16. Recommendations

### DOCUMENT 11: Data Lineage
**File:** `docs/SWARMVAULT_DATA_LINEAGE.md`

For each data entity, trace:
SOURCE → INGESTION → NORMALIZATION → M0 → M1 → M2 → M3 → M4 → M5 → PERSISTENCE → RETRIEVAL → API → FRONTEND → USER

With validation, guardrails, and failure modes at each transition.

### DOCUMENT 12: Contradiction Register
**File:** `docs/SWARMVAULT_CONTRADICTIONS.md`

Every documentation/code/implementation mismatch found.

---

## DELIVERABLE FORMAT

Return a summary containing:

1. **Repository:** branch, SHA, working tree status
2. **Agents executed:** count and names
3. **Documents produced:** file paths
4. **Backend coverage:** routers, services, models, migrations inspected
5. **Frontend coverage:** routes, components, API client inspected
6. **Pipeline coverage:** M0-M5 stages traced
7. **Guardrail coverage:** controls identified vs missing
8. **Memory readiness:** scorecard with evidence
9. **Memory Intelligence readiness:** what's safe to consume, what's not
10. **Critical gaps:** P0/P1/P2/P3 with evidence
11. **Contradictions found:** count and severity
12. **Tests used as evidence:** which test files informed analysis
13. **Certification:** CERTIFIED / CERTIFIED WITH LIMITATIONS / NOT CERTIFIED

---

## ABSOLUTE PROHIBITIONS

- DO NOT modify any file under `app/` or `frontend/src/`
- DO NOT modify `alembic/` or `tests/`
- DO NOT create files outside `docs/`
- DO NOT infer architecture from filenames alone — read the code
- DO NOT describe planned features as implemented
- DO NOT describe documented features as tested
- DO NOT silently resolve contradictions
- DO NOT claim completeness without evidence
