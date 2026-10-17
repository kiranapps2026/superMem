# SwarmVault WebApp — Enterprise Architecture Forensic Analysis
# Improved / Granular Prompt v2

## REPOSITORY IDENTITY (to be established by the analyst before Phase 0)

Repository root: `C:\Users\Administrator\Documents\SwarmVaultwebapp`
Backend root:   `C:\Users\Administrator\Documents\SwarmVaultwebapp\app\`
Frontend root:  `C:\Users\Administrator\Documents\SwarmVaultwebapp\frontend\`
Test root:      `C:\Users\Administrator\Documents\SwarmVaultwebapp\tests\`
Migration dir:  `C:\Users\Administrator\Documents\SwarmVaultwebapp\alembic\versions\`

**THIS REPOSITORY HAS NO GIT.** There is no `.git` directory.
Working-tree status: ALL FILES ARE UNTRACKED. No branch. No HEAD SHA.
Record this truthfully in the baseline document. Do not fabricate a SHA.

---

## YOUR ROLE

You are the Principal Enterprise Architect, Distributed Systems Architect,
Memory Systems Architect, Security Architect, Data Architect, Frontend
Architect, QA Architect, and Technical Documentation Authority for the
SwarmVault WebApp.

Your mission is NOT to modify or redesign the product.

Your mission is to perform a **repository-first architectural forensic analysis**
of the COMPLETE SwarmVault WebApp and produce an authoritative architecture
documentation package.

---

## ABSOLUTE RULES

### RULE 1 — REPOSITORY IS THE PRIMARY SOURCE OF TRUTH

Inspect the actual repository. Read every file listed below. Do NOT infer
architecture from filenames alone.

For every important architectural statement, identify:

- file path
- module / package
- class / dataclass / function
- route path + HTTP method
- Pydantic schema (request/response)
- SQLAlchemy model
- Alembic migration revision
- configuration variable
- test class / test function
- runtime dependency (requirements.txt or package.json)
- actual execution path (call chain)

Documentation may support understanding but **must not override executable
implementation** without explicitly identifying the discrepancy as a finding.

### RULE 2 — DO NOT MODIFY PRODUCT CODE

This is a documentation/forensic phase. DO NOT:

- refactor production code
- rename production modules
- redesign APIs
- alter database schema
- change memory algorithms
- change frontend behavior
- silently "fix" architectural problems

If something is wrong, document it as a finding in the contradiction register.

Allowed changes: new architecture documentation files, diagrams, evidence
tables, traceability matrices, documentation indexes, generated inventories,
analysis artifacts. Only.

### RULE 3 — DO NOT INVENT FEATURES

Every capability must be classified as exactly one of:

| Classification | Meaning |
|----------------|---------|
| IMPLEMENTED | Executable code exists, tested or not |
| PARTIALLY IMPLEMENTED | Code exists but incomplete |
| IMPLEMENTED BUT UNVERIFIED | Code exists, no test coverage |
| DOCUMENTED ONLY | Mentioned in docs, no executable found |
| PLANNED | Design exists, no code |
| MISSING | Referenced but no code found |
| BLOCKED | Code exists but cannot function as designed |
| DEPRECATED | Code exists but marked obsolete |
| UNKNOWN | Insufficient evidence to classify |

Never describe planned functionality as implemented.
Never describe an adapter as working because documentation mentions it.

### RULE 4 — TRACE DATA, NOT JUST COMPONENTS

The central architectural question is:

```
WHERE DOES DATA ENTER?
      ↓
HOW IS IT NORMALIZED?
      ↓
HOW IS IT VALIDATED?
      ↓
HOW IS IT EXTRACTED?
      ↓
HOW IS IT TEMPORALLY INTERPRETED?
      ↓
HOW IS IT REPRESENTED?
      ↓
HOW IS IT SCORED?
      ↓
HOW IS IT STORED?
      ↓
HOW IS IT RETRIEVED?
      ↓
HOW IS IT PRESENTED?
      ↓
CAN IT BECOME PERSISTENT MEMORY?
      ↓
CAN A FUTURE MEMORY INTELLIGENCE LAYER TRUST IT?
```

Trace the actual implementation for every data path.

---

## PHASE 0 — SOURCE CONTROL / BASELINE

Before analysis begins, record:

1. Repository root path.
2. Git branch: **"none — no .git directory present"**
3. Git HEAD SHA: **"N/A — untracked repository"**
4. Working-tree state: **"All files untracked"**
5. Uncommitted files: **all files in repository**
6. Repository structure: complete file tree (depth 3 minimum).
7. Backend root path.
8. Frontend root path.
9. Test directories.
10. Migration files (all `alembic/versions/*.py`).
11. Docker/deployment files: `Dockerfile`, `docker-compose.yml`, `.env.example`.
12. Configuration files: `requirements.txt`, frontend `package.json`, `tsconfig.json`, `alembic.ini`.
13. Existing documentation: README, DEPLOYMENT, any `docs/` directory.

**Create:** `docs/ARCHITECTURE_FORENSICS_BASELINE.md`

Include: timestamp, repository root, branch, SHA (or N/A), working-tree state,
backend root, frontend root, file counts by directory.

**Do NOT continue if the repository identity cannot be established.**
In this case, record: "Repository is unversioned (no Git). All analysis
is based on working-tree state as of [timestamp]."

---

## PARALLEL AGENT PROGRAM

Launch **minimum 7 parallel specialist agents**, each writing ONLY to its
assigned output file. Plus 1 final synthesis agent.

### AGENT EXECUTION CONTRACT

Each specialist agent MUST:

1. Read every source file listed in its coverage section.
2. Produce a document with the exact structure defined below.
3. Cite exact file paths, function names, class names, route paths, model
   field names, schema field names, migration filenames.
4. Classify every capability with the 9-tier classification system.
5. Identify gaps, inconsistencies, and contradictions.
6. Write ONLY to its assigned output file — never overwrite another agent's file.

---

## AGENT 1 — BACKEND RUNTIME ARCHITECTURE
**Output file:** `docs/SWARMVAULT_BACKEND_ARCHITECTURE.md`

### Files to read (mandatory):

| File | What to extract |
|------|----------------|
| `app/main.py` | App construction, lifespan, router inclusion, middleware stack, error handlers, security headers, structured logging, health endpoints |
| `app/db.py` | Engine config (pool_size, max_overflow, pool_pre_ping, pool_recycle), session factory, init_db, alembic wiring |
| `app/core/config.py` | Every Settings field, defaults, validators, is_production, cors_origins_safe, rate limit defaults, LLM config, storage config |
| `app/core/security.py` | hash_password, verify_password, make_access_token, decode_access_token, token expiry |
| `app/middleware/auth.py` | require_auth, OAuth2PasswordBearer config, token validation flow |
| `app/middleware/tenancy.py` | TenantContext dataclass, get_tenant_context flow (JWT decode → user lookup → workspace lookup → tenant lookup), X-Workspace-Id header handling |
| `app/middleware/rbac.py` | Role hierarchy, _PERMISSIONS dict, require_permission, require_min_role, PolicyEngine integration |
| `app/middleware/rate_limit.py` | RateLimitRule list, _RateLimiter sliding window, key_func variants, X-E2E bypass |
| `app/api/auth.py` | All routes, request/response schemas, token refresh flow |
| `app/api/workspace.py` | All routes, schema usage |
| `app/api/projects.py` | All routes, schema usage |
| `app/api/sessions.py` | All routes |
| `app/api/chat.py` | All routes, SSE streaming endpoint |
| `app/api/memory.py` | All routes, CRUD operations |
| `app/api/ingest.py` | All routes, upload endpoint, dedup logic |
| `app/api/provenance.py` | All routes |
| `app/api/dashboard.py` | All routes, aggregation queries |
| `app/api/feedback.py` | All routes |
| `app/api/api_keys.py` | All routes, key creation/rotation |
| `app/api/storage.py` | All routes |
| `app/api/policy.py` | All routes |
| `app/api/audit.py` | All routes |

### Sections required:

#### 1.1 Application Startup
- Lifespan sequence: what happens at startup, in what order
- `init_db()` call: does it block? Is it awaited? What happens on migration failure?
- Audit service `register_db_sink()`: when does it fire?
- Logging setup: only in development? What about production logging?

#### 1.2 FastAPI Application Construction
- App title, version, docs URL
- Middleware stack order (which wraps which?)
- Router inclusion: prefix, tags, which routers mount where
- CORS configuration: origins parsing, allow_credentials interaction
- Exception handlers: RequestValidationError, SQLAlchemyError, generic 500

#### 1.3 Router Inventory
For EACH router, list:
- File path
- Router prefix
- All route decorators: `@router.METHOD(path, ...)`
- Response model
- Status code (if not 200)
- Dependencies injected (auth, tenancy, RBAC, DB)
- Request body schema

#### 1.4 Service Layer Inventory
For EACH service file:
- File path
- Classes defined
- Key methods and their signatures
- Dependencies (other services, repositories, external APIs)
- Error handling approach

#### 1.5 Middleware Stack
For EACH middleware:
- File path
- Class name
- Dispatch method behavior
- What it adds/modifies (headers, state, errors)
- Order of execution

#### 1.6 Authentication Flow
Trace: incoming request → OAuth2PasswordBearer → decode_access_token →
user lookup → User object returned. Note every failure point.

#### 1.7 Authorization Flow
Trace: TenantContext → Role check → _get_permissions OR PolicyEngine.
Note: there are TWO authorization paths (static _PERMISSIONS dict AND
PolicyEngine). Document which endpoints use which.

#### 1.8 Tenancy Flow
Trace: X-Workspace-Id header → WorkspaceMember lookup → Tenant lookup →
TenantContext construction. Note the fallback path when no X-Workspace-Id.

#### 1.9 Database Access
- Engine configuration: pool_size=50, max_overflow=20, pool_pre_ping=True, pool_recycle=3600
- Session factory: expire_on_commit=False
- get_db dependency: yields AsyncSession
- Transaction boundaries: are there explicit transactions? commit/rollback?

#### 1.10 Background Processing
- Is there any background task processing? (check for BackgroundTasks, Celery, RQ, etc.)
- Pipeline execution: is it synchronous within the request? Or async?

#### 1.11 External Providers
- LLM provider: Anthropic (configurable), model name, timeout, retries
- Object storage: filesystem (default), S3, MinIO backends
- No other external integrations in the backend

#### 1.12 Error Handling
- RequestValidationError handler
- SQLAlchemyError handler
- Generic exception handler
- _sanitize_detail function: what it redacts, what it misses

#### 1.13 Observability
- Structured logging: JSON format, fields emitted
- X-Request-ID middleware
- Security headers middleware
- No metrics endpoint (enable_metrics=False by default)
- No tracing (no OpenTelemetry, no Jaeger)

#### 1.14 Health/Readiness
- Check for /health, /health/live, /health/ready endpoints
- If none exist, document as MISSING

#### 1.15 Lifecycle/Shutdown
- Lifespan: startup → yield → (no shutdown cleanup)
- No graceful shutdown handlers
- No signal handlers

#### 1.16 Runtime Dependencies
- requirements.txt: list every package with version
- Note: no pyproject.toml, no setup.py

---

## AGENT 2 — DATA, MEMORY & PERSISTENCE ARCHITECTURE
**Output file:** `docs/SWARMVAULT_DATA_MEMORY_ARCHITECTURE.md`

### Files to read (mandatory):

| File | What to extract |
|------|----------------|
| `app/models.py` | EVERY model: fields, types, defaults, indexes, relationships, cascade rules, soft-delete fields |
| `app/schemas.py` | EVERY Pydantic schema: fields, validators, defaults, from_attributes |
| `alembic/versions/001_initial.py` | Initial schema |
| `alembic/versions/002_provenance.py` | Provenance tables |
| `alembic/versions/003_sprint3_pipeline.py` | Pipeline tables |
| `alembic/versions/004_add_memory_sprint4_columns.py` | Memory columns |
| `alembic/versions/005_add_message_feedback.py` | Feedback table |
| `alembic/versions/006_add_temporal_to_graph_nodes.py` | Temporal on graph |
| `alembic/versions/007_add_api_keys.py` | API keys |
| `alembic/versions/008_add_source_content_hash.py` | Content hash |
| `alembic/versions/009_add_policy_engine.py` | Policy tables |
| `alembic/versions/010_add_audit_events.py` | Audit events |
| `alembic/versions/011_add_tenant_to_memory.py` | Tenant FK on memory |
| `alembic/versions/012_add_invitations.py` | Invitations |
| `app/services/pipeline.py` | M0-M4 execution, data transformations |
| `app/services/connectors.py` | normalize() function, source type handling |
| `app/services/m1_session.py` | Session understanding |
| `app/services/m2_facts.py` | Fact/decision extraction |
| `app/services/m3_temporal.py` | Temporal supersession |
| `app/services/m4_graph.py` | Graph construction |
| `app/services/m5_retrieval.py` | M5 retrieval |
| `app/services/memory.py` | MemoryRecord dataclass, MemoryService, MemoryTypeMapper, _persist_record |
| `app/services/retrieval.py` | Retrieval service |
| `app/services/audit/service.py` | Audit event emission |
| `app/services/audit/constants.py` | Audit event types |
| `app/services/audit/repository.py` | Audit persistence |

### Sections required:

#### 2.1 Data Model Inventory
For EACH table, document:
- Model class name
- Table name
- Primary key type
- Foreign keys (target table + column)
- Soft-delete field (`deleted_at`)
- Timestamp fields (`created_at`, `updated_at`)
- JSON fields (name + what they store)
- Indexes defined (name + columns)
- Unique constraints
- Cascade rules
- Relationships (back_populates, cascade)

Tables to cover:
Tenant, Workspace, User, WorkspaceMember, Invitation, RefreshToken,
Session, Message, Project, Memory, IngestJob, Source, NormalizedMessage,
Fact, Decision, GraphNode, GraphEdge, MessageProvenance, MessageFeedback,
ApiKey, Policy, PolicyVersion, AuditEvent

#### 2.2 Data Lineage — Full Trace
Trace: Raw Input → M0 → M1 → M2 → M3 → M4 → Persistent Store → Retrieval → API → Frontend

For EACH transition document:

**INPUT**
- Source (which table/file/API)
- Schema/format
- Volume expectations

**TRANSFORMATION**
- Function/method that performs it
- Logic description
- Fields added/removed/transformed

**OUTPUT**
- Target (which table/object)
- Schema/format
- Completeness guarantee

**VALIDATION**
- What is validated
- Where validation occurs
- What happens on validation failure

**GUARDRAIL**
- Security/isolation check
- Authorization check
- Dedup check

**FAILURE MODE**
- What happens if this stage fails
- Is partial output preserved?
- Is the source marked as failed?

**PERSISTENCE EFFECT**
- What is written to DB
- What is NOT written
- Transaction boundaries

**PROVENANCE EFFECT**
- What provenance data is recorded
- What links are created

**MEMORY QUALITY EFFECT**
- Does this stage add confidence?
- Does it add authority?
- Does it add temporal status?
- Does it enable supersession?

#### 2.3 Memory Model Analysis
Focus on the Memory table AND the MemoryRecord dataclass:

**Memory table fields:**
- id, tenant_id, workspace_id, user_id, agent_id, run_id, project_id
- memory_type (default "procedural_memory")
- content (Text, max_length 1_000_000 in schema)
- metadata (JSON)
- embedding (JSON, nullable)
- temporal_status (default "current")
- confidence (default 0.7)
- authority (default 1.0)
- deleted_at (soft delete)
- created_at, updated_at

**MemoryRecord dataclass fields:**
- memory_id, memory_type, scope
- tenant_id, workspace_id, project_id, team_id, user_id, agent_id, run_id
- subject, predicate, value, content
- authority (dict), confidence (float), importance (float)
- created_at, updated_at, valid_from, valid_until, expires_at
- version, supersedes, superseded_by
- provenance (list of dicts)
- permissions (dict)
- status
- user_metadata

**ANALYZE:** Which MemoryRecord fields actually get persisted? Which are
lost during _persist_record? Which are never populated?

#### 2.4 Temporal Semantics
- temporal_status field: what values are possible? Where are they set?
- superseded_by_id: where is it written? Is there a supersede operation?
- valid_from / valid_until in MemoryRecord: are they persisted?
- expires_at in MemoryRecord: is it persisted?

#### 2.5 Soft Deletion
- Which tables have deleted_at?
- Is deleted_at used consistently?
- Are deleted records excluded from queries?
- Is there any hard delete? (CASCADE delete on relationships)

#### 2.6 Deduplication
- content_hash on Source: how computed? Where checked?
- Is there message-level dedup?
- Is there memory-level dedup?

#### 2.7 Provenance Architecture
- MessageProvenance table: every field, what it records
- ProvenanceCreate/ProvenanceOut schemas
- How provenance links to messages, sessions, memory
- What is NOT recorded (e.g., no prompt template version, no system prompt)

#### 2.8 Audit Architecture
- AuditEvent table: every field
- AuditEventDTO vs AuditEvent mapping
- AuditService: register_db_sink, emit methods
- What events are emitted? Where?
- What is NOT audited?

#### 2.9 Storage Architecture
- Object storage backends: filesystem, S3, MinIO
- What is stored (raw content paths? uploaded files?)
- Storage paths configuration

---

## AGENT 3 — PIPELINE, GUARDRAIL & VALIDATION ARCHITECTURE
**Output file:** `docs/SWARMVAULT_GUARDRAILS_VALIDATION_ARCHITECTURE.md`

### Files to read (mandatory):

| File | What to extract |
|------|----------------|
| `app/middleware/auth.py` | Auth guardrail |
| `app/middleware/tenancy.py` | Tenancy guardrail |
| `app/middleware/rbac.py` | Authorization guardrail |
| `app/middleware/rate_limit.py` | Rate limit guardrail |
| `app/main.py` | Security headers, error sanitization, CORS |
| `app/core/security.py` | Password hashing, JWT validation |
| `app/core/config.py` | SECRET_KEY validation, CORS safety, dev/production guards |
| `app/schemas.py` | Every field_validator, Field constraints |
| `app/services/pipeline.py` | Pipeline error handling, stage boundaries |
| `app/services/connectors.py` | normalize() validation |
| `app/services/policy/engine.py` | Policy engine enforcement |
| `app/services/policy/evaluator.py` | RBAC policy generation |
| `app/api/ingest.py` | Content hash dedup, project scope check |
| `app/api/auth.py` | Login rate limiting, password verification |
| `app/api/memory.py` | Memory write validation |
| `tests/unit/test_security_6b.py` | Security test evidence |
| `tests/unit/test_connector_security.py` | Connector security tests |
| `tests/unit/test_storage_security.py` | Storage security tests |
| `tests/unit/test_rate_limit.py` | Rate limit tests |
| `tests/unit/test_rbac_security.py` | RBAC tests |
| `tests/unit/test_authorization_audit.py` | Authorization audit tests |
| `tests/unit/test_policy_engine.py` | Policy engine tests |
| `tests/unit/test_tenancy.py` | Tenancy isolation tests |

### Sections required:

#### 3.1 Guardrail Matrix
Build a table with these columns:

| Stage | Input | Output | Validation | Guardrail | Failure Mode | Classification |
|-------|-------|--------|------------|-----------|--------------|----------------|
| ... | ... | ... | ... | ... | ... | IMPLEMENTED/PARTIAL/MISSING/... |

Stages to cover:
- CORS preflight
- Security headers
- Request ID injection
- Rate limiting
- Authentication (JWT decode)
- User active check
- Tenancy resolution (X-Workspace-Id)
- Authorization (RBAC / Policy Engine)
- Schema validation (Pydantic)
- Content validation (null bytes, length)
- Source validation (source_type pattern)
- Content hash dedup
- Project scope check
- Password hashing
- Token refresh
- Error sanitization
- Soft delete filtering
- Tenant isolation in queries

For EACH guardrail:
- ACTIVE: code enforces it at runtime
- PARTIAL: code exists but has gaps
- DOCUMENTED: mentioned in docs but not enforced in code
- MISSING: no code, no docs
- BYPASSABLE: can be circumvented
- UNTESTED: no test coverage

#### 3.2 Validation Inventory
For EACH validation point:
- What is validated (field, format, range, type)
- Where (schema, service, middleware)
- On failure (error message, status code, side effects)

#### 3.3 Security Controls Inventory
For EACH control:
- CONTROL name
- LOCATION (file:line)
- ENFORCEMENT POINT (middleware, dependency, schema)
- FAILURE BEHAVIOR (what happens if it fails)
- BYPASS RISK (can it be circumvented?)
- TEST (which test file covers it)

#### 3.4 Adversarial Input Analysis
For each input path, answer:
- Can a malformed JSON body bypass schema validation?
- Can a missing tenant header access another workspace's data?
- Can a viewer role write memory? (check _PERMISSIONS)
- Can an expired token access the API?
- Can SQL injection occur? (SQLAlchemy parameterized?)
- Can XSS payloads reach the frontend unsanitized?
- Can path traversal occur in file storage?

---

## AGENT 4 — API / CONTRACT / INTEGRATION ARCHITECTURE
**Output file:** `docs/SWARMVAULT_API_INTEGRATION_ARCHITECTURE.md`

### Files to read (mandatory):

| File | What to extract |
|------|----------------|
| `app/api/auth.py` | All endpoints, schemas, flows |
| `app/api/workspace.py` | All endpoints |
| `app/api/projects.py` | All endpoints |
| `app/api/sessions.py` | All endpoints |
| `app/api/chat.py` | SSE streaming endpoint |
| `app/api/memory.py` | CRUD + search |
| `app/api/ingest.py` | Upload + source/fact/decision/graph CRUD |
| `app/api/provenance.py` | Provenance endpoints |
| `app/api/dashboard.py` | Dashboard aggregations |
| `app/api/feedback.py` | Feedback CRUD |
| `app/api/api_keys.py` | Key management |
| `app/api/storage.py` | Storage endpoints |
| `app/api/policy.py` | Policy CRUD |
| `app/api/audit.py` | Audit query endpoints |
| `app/schemas.py` | ALL schemas — map to endpoints |
| `frontend/src/lib/api.ts` | API client: base URL, auth flow, REST helpers, SSE helper |
| `frontend/src/hooks/useSSE.tsx` | SSE streaming implementation |
| `frontend/src/types/api.ts` | ALL frontend TypeScript interfaces |
| `frontend/src/features/chat/useChat.ts` | Chat hook: API calls, state management |
| `frontend/src/features/projects/useProjects.ts` | Projects hook |
| `frontend/src/features/memory/useMemory.ts` | Memory hook |
| `frontend/src/features/ingest/useIngest.ts` | Ingest hook |
| `frontend/src/features/search/useSearch.ts` | Search hook |
| `frontend/src/features/graph/useGraph.ts` | Graph hook |
| `frontend/src/features/apiKeys/useApiKeys.ts` | API keys hook |

### Sections required:

#### 4.1 Complete API Route Inventory
For EACH endpoint, document:
- Method + path
- Request body schema (Pydantic model)
- Query parameters
- Response schema
- Authentication required (yes/no)
- Authorization required (which permission/role)
- Status codes returned
- SSE streaming (yes/no)

#### 4.2 Frontend ↔ Backend Contract Matrix
For EACH frontend feature hook:

| Frontend Hook | API Calls | Backend Route | Request Schema | Response Schema | Mismatch? |
|---------------|-----------|---------------|----------------|-----------------|-----------|
| useChat | POST /api/v1/chat/stream | chat.py | ChatRequest | ChatStreamEvent | ... |
| ... | ... | ... | ... | ... | ... |

For EVERY mismatch found:
- What the frontend expects (TypeScript interface field)
- What the API returns (Pydantic schema field)
- Severity: CRITICAL (missing required field) / WARNING (extra field ignored) / INFO (cosmetic)

#### 4.3 SSE/Streaming Contract
- Endpoint: POST /api/v1/chat/stream
- Content-Type: text/event-stream
- Event format: `data: {JSON}`
- Event types: token, done, error, sources
- Frontend parsing: useSSE.tsx line-by-line parsing
- Error handling in stream
- AbortController support

#### 4.4 Authentication Contract
- Login: POST /api/v1/auth/login → TokenResponse
- Refresh: POST /api/v1/auth/refresh → TokenResponse
- Frontend: stores in localStorage as `sv_tokens`
- Token refresh: automatic on 401, clears on failure
- Logout: clears localStorage

#### 4.5 Integration Classification
For each potential integration, classify:

| Integration | Classification | Evidence | Gap |
|-------------|---------------|----------|-----|
| Claude Code | ... | ... | ... |
| Codex | ... | ... | ... |
| MCP server | ... | ... | ... |
| Universal Adapter | ... | ... | ... |
| REST API | IMPLEMENTED | 14 routers | — |
| SSE streaming | IMPLEMENTED | chat/stream endpoint | — |

---

## AGENT 5 — FRONTEND ARCHITECTURE
**Output file:** `docs/SWARMVAULT_FRONTEND_ARCHITECTURE.md`

### Files to read (mandatory):

| File | What to extract |
|------|----------------|
| `frontend/package.json` | Dependencies, scripts, Next.js version |
| `frontend/next.config.js` | Next.js config |
| `frontend/tsconfig.json` | Path aliases, strict mode |
| `frontend/tailwind.config.js` | Theme config |
| `frontend/postcss.config.js` | PostCSS plugins |
| `frontend/src/app/layout.tsx` | Root layout: ThemeProvider, AuthProvider, AppShell |
| `frontend/src/app/page.tsx` | Landing/redirect page |
| `frontend/src/app/globals.css` | Design tokens, CSS custom properties, animations |
| `frontend/src/hooks/AppShell.tsx` | Auth-gated shell |
| `frontend/src/hooks/AuthRedirect.tsx` | Auth redirect component |
| `frontend/src/hooks/useAuth.tsx` | Auth state management |
| `frontend/src/hooks/useTheme.tsx` | Theme management |
| `frontend/src/hooks/useSSE.tsx` | SSE hook |
| `frontend/src/lib/api.ts` | API client |
| `frontend/src/lib/errors.ts` | Error formatting |
| `frontend/src/types/api.ts` | ALL TypeScript interfaces |
| `frontend/src/components/Sidebar.tsx` | Sidebar navigation |
| `frontend/src/components/ui/*.tsx` | ALL UI primitives |
| `frontend/src/features/chat/useChat.ts` | Chat feature |
| `frontend/src/features/projects/useProjects.ts` | Projects feature |
| `frontend/src/features/memory/useMemory.ts` | Memory feature |
| `frontend/src/features/ingest/useIngest.ts` | Ingest feature |
| `frontend/src/features/search/useSearch.ts` | Search feature |
| `frontend/src/features/graph/useGraph.ts` | Graph feature |
| `frontend/src/features/apiKeys/useApiKeys.ts` | API keys feature |
| EACH page.tsx in `frontend/src/app/` | All 21 page components |

### Sections required:

#### 5.1 Next.js Architecture
- App Router (not Pages Router)
- Route structure (complete tree)
- Client vs Server components (which are `'use client'`)
- Layout hierarchy
- Metadata configuration

#### 5.2 Route Inventory
For EACH route:

| Route | Page File | Client/Server | Key State | API Calls | Description |
|-------|-----------|--------------|-----------|-----------|-------------|
| / | page.tsx | Client | auth redirect | — | Landing |
| /auth/login | auth/login/page.tsx | Client | login form | POST /auth/login | Login |
| ... | ... | ... | ... | ... | ... |

#### 5.3 State Management
- No external state library (no Redux, Zustand, etc.)
- State is in:
  - React Context (useAuth, useTheme)
  - Local component state (useState)
  - Custom hooks (useChat, useProjects, etc.)
  - localStorage (tokens, theme)
- Document every piece of global state

#### 5.4 Component Architecture
- UI primitives: 15 custom components (no shadcn/ui, no Radix)
- Layout: Sidebar + AppShell
- Feature organization: `src/features/` per domain
- Each feature hook returns: `{ data, loading, error, reload }`

#### 5.5 API Client
- Base URL from NEXT_PUBLIC_API_URL
- Token management: localStorage key `sv_tokens`
- Auto-refresh on 401
- REST helpers: apiGet, apiPost, apiPatch, apiDelete
- SSE: useSSE hook with AbortController
- uploadFile: XMLHttpRequest with progress

#### 5.6 Authentication Flow (Frontend)
- useAuth: state, login, register, logout, token refresh
- AuthProvider: wraps app, stores tokens
- AppShell: redirects unauthenticated to /auth/login
- Token format: { access_token, refresh_token }
- Storage: localStorage.sv_tokens

#### 5.7 Theme Architecture
- useTheme: dark/light/system
- localStorage: sv_theme
- data-theme attribute on <html>
- CSS custom properties in globals.css

#### 5.8 Frontend Route → Component → API → Backend Domain → Data Model Matrix

| Screen | Component(s) | State Source | API Call(s) | Backend Router | Service | DB Model(s) |
|--------|--------------|-------------|-------------|----------------|---------|-------------|
| Login | auth/login/page.tsx | useState (form) | POST /api/v1/auth/login | auth.py | — | User |
| Dashboard | dashboard/page.tsx | useState | GET /api/v1/dashboard/overview | dashboard.py | — | Memory, Source, Session, Fact, Decision, GraphNode, GraphEdge |
| Projects | /projects | projects/page.tsx | useProjects | GET /api/v1/projects/ | projects.py | — | Project |
| Chat | /projects/[id]/chat | chat/page.tsx | useChat, useSSE | POST /api/v1/chat/stream (SSE) | chat.py | chat_orchestrator | Message, MessageProvenance |
| Memory | /projects/[id]/memory | memory/page.tsx | useMemory | GET/POST/DELETE /api/v1/memory/ | memory.py | MemoryService | Memory |
| Facts | /projects/[id]/facts | facts/page.tsx | useState | GET /api/v1/ingest/facts | ingest.py | — | Fact |
| Decisions | /projects/[id]/decisions | decisions/page.tsx | useState | GET /api/v1/ingest/decisions | ingest.py | — | Decision |
| Timeline | /projects/[id]/timeline | timeline/page.tsx | useState | GET /api/v1/ingest/timeline | ingest.py | — | Mixed |
| Search | /projects/[id]/search | search/page.tsx | useSearch | POST /api/v1/ingest/search | ingest.py | m5_retrieval | Mixed |
| Graph | /projects/[id]/graph | graph/page.tsx | useGraph | GET /api/v1/ingest/graph | ingest.py | m4_graph | GraphNode, GraphEdge |
| Provenance | /projects/[id]/provenance | provenance/page.tsx | useState | GET /api/v1/provenance/ | provenance.py | — | MessageProvenance |
| Ingest | /projects/[id]/ingest | ingest/page.tsx | useIngest | POST /api/v1/ingest/upload | ingest.py | pipeline | Source, NormalizedMessage, Fact, Decision, GraphNode, GraphEdge |
| Sessions | /projects/[id]/sessions | sessions/page.tsx | useState | GET /api/v1/sessions/ | sessions.py | — | Session, Message |
| API Keys | /settings/api-keys | api-keys/page.tsx | useApiKeys | GET/POST/DELETE /api/v1/api-keys/ | api_keys.py | — | ApiKey |
| Storage | /settings/storage | storage/page.tsx | useState | GET/POST /api/v1/storage/ | storage.py | object_storage | Storage backend |
| Profile | /settings/profile | profile/page.tsx | useState | GET/PATCH /api/v1/auth/me | auth.py | — | User |
| Settings | /settings | settings/page.tsx | useState | — | — | — | — |

---

## AGENT 6 — SECURITY, TENANCY & OPERATIONAL ARCHITECTURE
**Output file:** `docs/SWARMVAULT_SECURITY_OPERATIONAL_ARCHITECTURE.md`

### Files to read (mandatory):

| File | What to extract |
|------|----------------|
| `app/core/security.py` | Password hashing (bcrypt), JWT (HS256), token expiry |
| `app/core/config.py` | SECRET_KEY validation, dev defaults, production guards |
| `app/middleware/auth.py` | JWT decode, user lookup, inactive user rejection |
| `app/middleware/tenancy.py` | Workspace isolation, tenant lookup |
| `app/middleware/rbac.py` | Role hierarchy, permission sets, two auth paths |
| `app/middleware/rate_limit.py` | Sliding window, in-memory, Redis gap |
| `app/main.py` | CORS config, security headers, error sanitization, CSP |
| `app/models.py` | ApiKey model (key_hash, key_prefix), RefreshToken model |
| `app/services/policy/engine.py` | PolicyEngine, check_role_minimum, effects |
| `app/services/policy/evaluator.py` | RBAC policy generation |
| `app/services/policy/repository.py` | Policy persistence |
| `app/api/api_keys.py` | Key creation, rotation, revocation |
| `app/services/audit/service.py` | Audit emission |
| `app/services/audit/constants.py` | Event type constants |
| `app/services/audit/repository.py` | Audit DB sink |
| `Dockerfile` | Multi-stage build, non-root user, port exposure |
| `docker-compose.yml` | Postgres, app service, ports, volumes |
| `alembic/versions/010_add_audit_events.py` | Audit table creation |
| `tests/unit/test_security_6b.py` | Security test evidence |
| `tests/unit/test_rbac_security.py` | RBAC test evidence |
| `tests/unit/test_connector_security.py` | Connector security |
| `tests/unit/test_storage_security.py` | Storage security |
| `tests/unit/test_rate_limit.py` | Rate limit tests |
| `tests/unit/test_authorization_audit.py` | Auth audit tests |

### Sections required:

#### 6.1 Authentication Architecture
- Mechanism: JWT HS256 via python-jose
- Access token: expiry from config (default 60 min)
- Refresh token: stored in DB (RefreshToken table), expiry 30 days, revocable
- Password hashing: bcrypt via passlib
- Token storage: localStorage (frontend) — NOT httpOnly cookie
- **FINDING: localStorage token storage is XSS-vulnerable**

#### 6.2 Authorization Architecture
- Two parallel auth paths:
  1. Static `_PERMISSIONS` dict in rbac.py → `require_permission()`
  2. PolicyEngine → `require_min_role()`
- Which endpoints use which? Document for every endpoint.
- Role hierarchy: owner > admin(500) > member(100) > viewer(50)
- Permission sets per role

#### 6.3 Tenancy Architecture
- Tenant hierarchy: Tenant → Workspace → Project
- TenantContext: tenant_id, workspace_id, role, user_id
- X-Workspace-Id header: optional, falls back to first membership
- Multi-workspace users: which workspace is active?
- Tenant isolation: enforced at query level?

#### 6.4 API Key Architecture
- ApiKey model: key_hash (SHA-256), key_prefix (first 8 chars)
- Creation: raw key shown once, never stored
- Rotation: new key created, old revoked
- Revocation: sets revoked_at
- Expiry: expires_at field
- Last used: last_used_at tracking

#### 6.5 Rate Limiting
- In-memory sliding window
- Not distributed-safe (will not work with multiple workers)
- X-E2E bypass header in non-production
- Rules: login(10/min), chat(30/min), ingest(5/hr), search(60/min)

#### 6.6 Security Headers
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: geolocation=(), microphone=(), camera=()
- HSTS: production only
- CSP: production vs development (dev allows unsafe-inline/unsafe-eval)

#### 6.7 CORS
- Default: wildcard "*"
- Production: must be explicit list (cors_origins_safe strips wildcard)
- allow_credentials: True (implied by Bearer auth)
- **FINDING: cors_origins defaults to "*" — verify FastAPI CORS middleware config**

#### 6.8 Error Sanitization
- _sanitize_detail: redacts password/secret/token/api_key/database_url
- Redacts Windows paths and Unix paths
- Does NOT redact: SQL errors, stack traces, internal model names
- Error format: `{"error": {"type": "...", "message": "...", "request_id": "..."}}`

#### 6.9 Audit Architecture
- AuditEvent table: 22 fields
- Append-only (no UPDATE, no DELETE from application)
- event_metadata (JSON) for arbitrary data
- Indexed: tenant+timestamp, principal+timestamp, resource_type, correlation_id
- AuditService.register_db_sink() at startup
- Constants: event types, result statuses

#### 6.10 Docker/Deployment
- Multi-stage Dockerfile: python:3.12-slim ��� swarmvault user
- Exposes port 8000
- Runs: alembic upgrade head && uvicorn app.main:app
- docker-compose: postgres:16-alpine + app
- Volumes: postgres_data, app_storage, app_logs
- No health check in docker-compose

#### 6.11 Secrets Management
- .env files (gitignored)
- SECRET_KEY: dev default is insecure
- anthropic_api_key: empty default
- No secret rotation mechanism
- No vault integration

#### 6.12 Security Control Inventory
For EACH control:
- CONTROL
- LOCATION
- ENFORCEMENT POINT
- TEST
- FAILURE BEHAVIOR
- BYPASS RISK

---

## AGENT 7 — MEMORY INTELLIGENCE READINESS ARCHITECTURE
**Output file:** `docs/SWARMVAULT_MEMORY_INTELLIGENCE_READINESS.md`

### Files to read (mandatory):

| File | What to extract |
|------|----------------|
| `app/models.py` | Memory model (all fields), Fact, Decision, GraphNode, GraphEdge |
| `app/schemas.py` | MemoryOut, MemoryCreate, MemoryUpdate, MemorySearchRequest, MemoryReferenceOut |
| `app/services/memory.py` | MemoryRecord dataclass, MemoryService, MemoryTypeMapper, _persist_record |
| `app/services/pipeline.py` | Pipeline stages, what gets extracted |
| `app/services/m1_session.py` | Session understanding output |
| `app/services/m2_facts.py` | Fact/decision extraction, fields populated |
| `app/services/m3_temporal.py` | Supersession logic |
| `app/services/m4_graph.py` | Graph node/edge creation |
| `app/services/m5_retrieval.py` | Retrieval scoring |
| `app/services/chat_orchestrator.py` | Memory usage in chat, provenance |
| `app/api/memory.py` | Memory CRUD, search endpoint |
| `app/services/policy/engine.py` | Policy enforcement on memory |
| `app/services/audit/constants.py` | Memory audit events |
| `tests/unit/test_memory.py` | Memory tests |
| `tests/unit/test_golden_dataset.py` | Golden dataset tests |

### Sections required:

#### 7.1 Current Memory Model — Field-by-Field Analysis

For EACH field in the Memory table, answer:

| Field | EXISTS? | PERSISTED? | VALIDATED? | USED? | TESTED? | TRUSTWORTHY? |
|-------|---------|------------|------------|-------|---------|-------------|
| id | YES | YES | YES (UUID) | YES | ? | HIGH |
| tenant_id | YES | YES | YES (FK) | YES | ? | HIGH |
| workspace_id | YES | YES | YES (FK) | YES | ? | HIGH |
| user_id | YES | YES | YES (FK) | YES | ? | HIGH |
| agent_id | YES | YES | NO | ? | ? | LOW |
| run_id | YES | YES | NO | ? | ? | LOW |
| project_id | YES | YES (nullable) | NO | ? | ? | MEDIUM |
| memory_type | YES | YES | YES (max_length=50) | YES | ? | MEDIUM |
| content | YES | YES | YES (min=1, max=1M, no null bytes) | YES | ? | HIGH |
| metadata | YES | YES | NO | ? | ? | LOW |
| embedding | YES | YES (nullable) | NO | NEVER POPULATED | NO | NOT TRUSTWORTHY |
| temporal_status | YES | YES | YES (default="current") | YES | ? | MEDIUM |
| confidence | YES | YES | YES (float) | YES | ? | MEDIUM |
| authority | YES | YES | YES (float) | YES | ? | MEDIUM |
| deleted_at | YES | YES | NO | ? | ? | MEDIUM |

#### 7.2 MemoryRecord vs Memory Model Gap Analysis

The MemoryRecord dataclass has fields that DO NOT persist to the DB:
- scope → NOT persisted (only implicit via memory_type mapping)
- subject, predicate, value → NOT persisted (only content is saved)
- importance → NOT persisted
- valid_from, valid_until, expires_at → NOT persisted
- version → NOT persisted
- supersedes, superseded_by → NOT persisted (superseded_by_id exists on Fact/Decision but not Memory)
- provenance (list of dicts) → NOT persisted
- permissions (dict) → NOT persisted
- user_metadata → mapped to metadata partially

**DOCUMENT THIS AS A FINDING.**

#### 7.3 Memory Type Taxonomy
- Canonical types in MemoryTypeMapper: WORKING, EPISODIC, SEMANTIC, PROCEDURAL, USER, TEAM, PROJECT, AGENT
- Vault types: working, episodic, semantic, procedural, user, team, project, agent
- Actual DB values: default is "procedural_memory"
- **FINDING: Default memory_type is "procedural_memory" but MemoryTypeMapper maps "PROCEDURAL" → "procedural". Mismatch with underscore.**

#### 7.4 Memory Confidence & Authority
- Default confidence: 0.7 (Memory model), 0.7 (MemoryRecord)
- Default authority: 1.0 (Memory model), dict with "score" key (MemoryRecord)
- Who sets these values? The Memory API (user-provided) or pipeline?
- Are they ever adjusted by the system?
- **FINDING: Pipeline does not set confidence/authority on Memory records. Only Facts/Decisions get these from extraction.**

#### 7.5 Memory Scope
- Memory is scoped to: tenant_id + workspace_id + user_id + project_id (optional)
- MemoryTypeMapper has scope mapping but scope is NOT a column in the Memory table
- **FINDING: Scope is defined in MemoryRecord but not persisted. Memory is only user-scoped via user_id.**

#### 7.6 Memory Lifecycle
- Created: via API (user/system)
- Updated: via PATCH /api/v1/memory/{id}
- Deleted: soft delete (deleted_at)
- Expired: NO expiration mechanism in the Memory model
- Superseded: NO supersession for Memory (only Fact/Decision have superseded_by_id)

#### 7.7 Memory Retrieval
- M5 retrieval: retrieve_for_chat, retrieve_hybrid
- What indexes exist? (no embedding index, no full-text search index)
- Scoring: how are results ranked?
- Context window: memory_limit=5 default

#### 7.8 Memory Safety Gate Matrix

| Condition | Current State | Required for Persistent Memory |
|-----------|--------------|-------------------------------|
| Identity (unique ID) | YES (UUID) | PASS |
| Source (who created it) | PARTIAL (user_id only) | Need agent_id, run_id populated |
| Time (created_at) | YES | PASS |
| Context (workspace, project) | YES | PASS |
| Confidence score | YES (default 0.7) | Need pipeline-populated values |
| Authority score | YES (default 1.0) | Need pipeline-populated values |
| Provenance chain | NO (not persisted) | MUST implement |
| Relationships | NO (Memory has no graph edges) | Need graph integration |
| Supersession | NO (Memory has no superseded_by) | Need supersession mechanism |
| Contradiction detection | NO | Need contradiction tracking |
| Scope hierarchy | PARTIAL (no scope column) | Need scope + permissions |
| Lifecycle (expiry) | NO | Need expires_at or lifecycle policy |
| Retrievability | YES (M5) | PASS |
| Explainability | PARTIAL (provenance table links to messages) | Need memory-specific provenance |
| Auditability | PARTIAL (memory audit events exist) | Need full audit trail |

#### 7.9 Memory Intelligence Readiness

Answer these questions with evidence:

1. **Can the current system produce persistent memory?**
   - YES, partially. Memory records are persisted to PostgreSQL.
   - BUT: they lack provenance, authority chains, supersession, and contradiction detection.

2. **Can a future intelligence layer trust current Memory records?**
   - NO, not without additional contracts.
   - Reasons: no provenance chain, no source tracking beyond user_id, no confidence calibration, no contradiction handling.

3. **What can a future layer safely consume TODAY?**
   - Memory content (text)
   - Temporal status (current/superseded)
   - Confidence and authority (though default-valued)
   - Workspace/project scoping

4. **What must NOT be assumed?**
   - That confidence/authority were set by the system (they default to 0.7/1.0)
   - That memory has a provenance chain
   - That memory can be superseded
   - That contradictions are tracked
   - That embeddings exist (they don't — column is nullable and never populated)

5. **What contracts must exist before a Memory Intelligence Layer can operate?**
   - Provenance contract: every memory must have a source chain
   - Authority contract: confidence/authority must be set by extraction, not default
   - Supersession contract: memory must support versioning
   - Contradiction contract: conflicting memories must be detectable
   - Scope contract: memory must have explicit scope + permissions
   - Lifecycle contract: memory must have expiry or archival policy

---

## CROSS-AGENT REQUIREMENT — DATA LINEAGE

Every specialist must include a data lineage section tracing their domain
through this canonical pipeline:

```
SOURCE (user input, file upload, API call)
  ↓
INGESTION (API validation, dedup, auth check)
  ↓
NORMALIZATION (M0: connectors.normalize)
  ↓
M1 (session understanding)
  ↓
M2 (fact/decision extraction)
  ↓
M3 (temporal supersession)
  ↓
M4 (graph construction)
  ↓
M5 (retrieval at query time)
  ↓
PERSISTENT STORE (PostgreSQL)
  ↓
RETRIEVAL (M5 hybrid search)
  ↓
API RESPONSE (Pydantic schema)
  ↓
FRONTEND RENDERING (React component)
  ↓
USER
```

For EACH transition, document:
- Input contract (schema, format)
- Output contract (schema, format)
- Validation applied
- Guardrail enforced
- Persistence effect
- Provenance recorded
- Failure behavior

---

## FINAL SYNTHESIS AGENT

After all seven specialist documents are complete, launch a final
Architecture Synthesis Agent.

### Its mandate:

1. Read ALL seven specialist documents.
2. Read the backend source files listed above.
3. Read the frontend source files listed above.
4. Read ALL Alembic migrations.
5. Read ALL test files listed above.
6. Read `app/main.py` for the complete application wiring.
7. Read `app/services/pipeline.py` for the complete pipeline.
8. Reconcile contradictions between specialist claims and actual source code.
9. Resolve classification disagreements.
10. Produce the final document package.

### FINAL DOCUMENT 1 — MASTER ARCHITECTURE
**Output file:** `docs/SWARMVAULT_WEBAPP_MASTER_ARCHITECTURE.md`

Required sections (31 total):
1. Executive Summary
2. Product Boundary (what SwarmVault IS and IS NOT)
3. System Context (external systems, no diagrams of non-existent components)
4. Architectural Principles (derived from code, not aspirational)
5. High-Level Architecture
6. Backend Architecture (with file:line citations)
7. Frontend Architecture (with file:line citations)
8. API Architecture (complete route table)
9. Data Architecture (complete model inventory)
10. Memory Architecture (field-by-field analysis)
11. Storage Architecture (filesystem/S3/MinIO)
12. Security Architecture (every control)
13. Tenancy Architecture (tenant→workspace→project hierarchy)
14. Pipeline Architecture (M0-M4 with actual function calls)
15. M0-M5 Architecture (stage-by-stage)
16. Guardrail Architecture (complete matrix)
17. Validation Architecture (every validation point)
18. Provenance Architecture (what is recorded, what is missing)
19. Audit Architecture (events, sinks, gaps)
20. Retrieval Architecture (M5, indexes, scoring)
21. SSE/Streaming Architecture (chat stream)
22. Ingestion Architecture (upload, dedup, pipeline trigger)
23. Integration Architecture (actual vs documented)
24. Deployment Architecture (Docker, compose, env)
25. Failure & Recovery Architecture (what fails, what recovers)
26. Observability Architecture (logging, no metrics, no tracing)
27. Test Architecture (test files, coverage gaps)
28. Current Limitations (evidence-backed)
29. Technical Debt (with severity)
30. Future Memory Intelligence Boundary (what can/cannot be trusted)
31. Architectural Readiness Assessment (per capability)

### FINAL DOCUMENT 2 — END-TO-END FLOWS
**Output file:** `docs/SWARMVAULT_END_TO_END_FLOWS.md`

For EACH flow, document with exact file:line citations:

| Flow | Trigger | Input | Validation | Guardrails | Processing | Persistence | Output | Failure | Security Boundary |
|------|---------|-------|------------|------------|------------|-------------|--------|---------|-------------------|
| FLOW-001 User Registration | POST /auth/register | UserRegister schema | Pydantic validation | Rate limit, CORS | User + Workspace + Membership created | 3 DB inserts | TokenResponse | Duplicate email | No auth required |
| FLOW-002 Login | POST /auth/login | UserLogin schema | Pydantic | Rate limit (10/min) | Password verify → JWT create | RefreshToken insert | TokenResponse | Invalid creds | No auth required |
| FLOW-003 Workspace Creation | POST /workspaces/ | WorkspaceCreate | Schema + tenancy | Auth, RBAC | Tenant lookup → Workspace create | Workspace + Member | WorkspaceOut | 404 tenant | Auth required |
| FLOW-004 Project Creation | POST /projects/ | ProjectCreate | Schema + workspace scope | Auth, tenancy, RBAC | Project create | Project insert | ProjectOut | 404 workspace | Auth required |
| FLOW-005 Session Ingestion | POST /ingest/upload | IngestUploadRequest | Schema, project check, content hash | Auth, tenancy, RBAC, dedup | Pipeline M0-M4 | Source + Session + Messages + Facts + Decisions + Graph | IngestUploadResponse | Pipeline error | Auth required, member+ |
| FLOW-006 JSON Ingestion | (part of FLOW-005) | source_type="json" | normalize() | Same as FLOW-005 | connectors.normalize → M0 | Same | Same | Parse error | Same |
| FLOW-007 JSONL Ingestion | (part of FLOW-005) | source_type="jsonl" | normalize() | Same as FLOW-005 | connectors.normalize → M0 | Same | Same | Parse error | Same |
| FLOW-008 M0 Normalization | pipeline.py | raw_content | source_type validation | Auth context | connectors.normalize() | Source + NormalizedMessage | conversation object | Unsupported type | Internal |
| FLOW-009 M1 Session Understanding | pipeline.py | NormalizedMessages | Message count check | — | understand_session() | Session.extra_metadata | topics, entities, intents | LLM error | Internal |
| FLOW-010 M2 Fact/Decision Extraction | pipeline.py | messages + M1 context | — | — | extract_facts(), extract_decisions() | Fact + Decision rows | facts, decisions | LLM error | Internal |
| FLOW-011 M3 Temporal Processing | pipeline.py | Facts + Decisions | temporal_status default | — | supersede_fact(), supersede_decision() | Updated temporal_status | superseded records | — | Internal |
| FLOW-012 M4 Graph Construction | pipeline.py | entities + relationships | — | — | extract_graph_elements(), persist_graph() | GraphNode + GraphEdge rows | graph nodes/edges | Duplicate external_id | Internal |
| FLOW-013 M5 Retrieval | GET /memory/search or chat | query string | min_length=1 | Auth, tenancy | retrieve_hybrid() or retrieve_for_chat() | None (read-only) | SearchResponse or chat context | No results | Auth required |
| FLOW-014 Persistent Memory Creation | POST /memory/ | MemoryCreate | Schema validation (null bytes, length) | Auth, tenancy, RBAC | MemoryService._persist_record() | Memory insert | MemoryOut | DB error | Auth required |
| FLOW-015 Memory Retrieval | GET /memory/ | query params | — | Auth, tenancy | MemoryService.search() | None (read-only) | Paginated MemoryOut | Empty result | Auth required |
| FLOW-016 Search | POST /ingest/search | SearchRequest | Schema | Auth, tenancy | M5 hybrid search | None (read-only) | SearchResponse | No matches | Auth required |
| FLOW-017 Chat | POST /chat/ | ChatRequest | Schema | Auth, tenancy, RBAC, rate limit | process_chat() | MessageProvenance insert | ChatResponse | LLM error | Auth required |
| FLOW-018 SSE Chat Streaming | POST /chat/stream | ChatRequest | Schema | Auth, tenancy, rate limit | process_chat() + SSE | MessageProvenance | SSE events | Stream error | Auth required |
| FLOW-019 Provenance | GET /provenance/{id} | path param | — | Auth, tenancy | DB lookup | None | ProvenanceOut | 404 | Auth required |
| FLOW-020 Graph Exploration | GET /ingest/graph | query params | — | Auth, tenancy | DB query | None | GraphResponse | Empty | Auth required |
| FLOW-021 Memory Deletion | DELETE /memory/{id} | path param | — | Auth, tenancy, RBAC | soft delete (deleted_at) | deleted_at set | 204 | Already deleted | Auth + memory.delete |
| FLOW-022 Supersession | (internal, M3) | Fact/Decision | — | — | supersede_*() | superseded_by_id set | Updated record | ��� | Internal |
| FLOW-023 Audit | GET /audit/events | query params | — | Auth, tenancy, RBAC | DB query | None | Paginated AuditEventOut | Empty | Auth + admin |
| FLOW-024 API Key Creation | POST /api-keys/ | ApiKeyCreate | Schema | Auth, tenancy | Hash key, store prefix | ApiKey insert | ApiKeyOut (key shown once) | — | Auth required |
| FLOW-025 External Agent Integration | N/A | — | — | — | — | — | — | — | NOT IMPLEMENTED |

### FINAL DOCUMENT 3 — GUARDRAIL MASTER MATRIX
**Output file:** `docs/SWARMVAULT_GUARDRAIL_MASTER_MATRIX.md`

Complete matrix with columns:
- Stage (which pipeline stage or request phase)
- Control name
- Implementation (file:line)
- Enforcement point (middleware/dependency/schema/service)
- Validation logic
- Test coverage (test file:function)
- Failure mode (what happens on failure)
- Bypass possibility (yes/no/how)
- Severity (CRITICAL/HIGH/MEDIUM/LOW)
- Current status (ACTIVE/PARTIAL/MISSING/BYPASSABLE)

Plus special section: **MEMORY SAFETY GATE MATRIX**
- Conditions required before information becomes persistent memory
- Which are satisfied, which are not

### FINAL DOCUMENT 4 — PERSISTENT MEMORY READINESS
**Output file:** `docs/SWARMVAULT_PERSISTENT_MEMORY_READINESS.md`

For each question:
1. What data is currently persistent? → List tables, volumes
2. What data is ephemeral? → In-memory cache, SSE streams
3. What data is normalized? → NormalizedMessage, pipeline output
4. What data has provenance? → MessageProvenance, MessageFeedback, AuditEvent
5. What data has temporal semantics? → temporal_status on Fact, Decision, GraphNode, GraphEdge, Memory
6. What data has confidence? → Fact, Decision, Memory, GraphEdge
7. What data has authority? → Fact, Decision, Memory
8. What data has identity? → All tables have UUID PKs
9. What data has scope? → tenant_id, workspace_id, project_id on most tables
10. What data can be superseded? → Fact, Decision only (superseded_by_id). NOT Memory.
11. What data can be contradicted? → NOT tracked anywhere
12. What data can be deleted? → All tables have soft delete. Some have CASCADE.
13. What data can be retrieved? → All via API endpoints
14. What data can be explained? → ProvenanceExplorer for messages. NOT for memories.
15. What data is safe for future memory intelligence? → GREEN/YELLOW/RED per data type

Then:
- GREEN = ready
- YELLOW = partially ready
- RED = not ready

### FINAL DOCUMENT 5 — FRONTEND ↔ BACKEND ARCHITECTURE
**Output file:** `docs/SWARMVAULT_FRONTEND_BACKEND_ARCHITECTURE.md`

For EACH frontend screen:

| Screen | Route | Components | State | API Endpoint(s) | Backend Router | Service | DB Model(s) | Response → UI |
|--------|-------|-----------|-------|-----------------|----------------|---------|-------------|---------------|
| Login | /auth/login | login/page.tsx | useState (form) | POST /api/v1/auth/login | auth.py | — | User, RefreshToken | TokenPair → store in localStorage |
| Dashboard | /dashboard | dashboard/page.tsx | useState | GET /api/v1/dashboard/overview | dashboard.py | — | Memory, Source, Session, Fact, Decision, GraphNode, GraphEdge | DashboardOverview → StatCards |
| Projects | /projects | projects/page.tsx | useProjects | GET /api/v1/projects/ | projects.py | — | Project | Project[] → Card list |
| Chat | /projects/[id]/chat | chat/page.tsx | useChat, useSSE | POST /api/v1/chat/stream (SSE) | chat.py | chat_orchestrator | Message, MessageProvenance | SSE tokens → message list |
| Memory | /projects/[id]/memory | memory/page.tsx | useMemory | GET/POST/DELETE /api/v1/memory/ | memory.py | MemoryService | Memory | MemoryItemOut → list |
| Facts | /projects/[id]/facts | facts/page.tsx | useState | GET /api/v1/ingest/facts | ingest.py | — | Fact | FactItem[] → table |
| Decisions | /projects/[id]/decisions | decisions/page.tsx | useState | GET /api/v1/ingest/decisions | ingest.py | — | Decision | DecisionItem[] → table |
| Timeline | /projects/[id]/timeline | timeline/page.tsx | useState | GET /api/v1/ingest/timeline | ingest.py | — | Mixed | TimelineItem[] → list |
| Search | /projects/[id]/search | search/page.tsx | useSearch | POST /api/v1/ingest/search | ingest.py | m5_retrieval | Mixed | SearchResultItem[] → list |
| Graph | /projects/[id]/graph | graph/page.tsx | useGraph | GET /api/v1/ingest/graph | ingest.py | m4_graph | GraphNode, GraphEdge | GraphResponse → visualization |
| Provenance | /projects/[id]/provenance | provenance/page.tsx | useState | GET /api/v1/provenance/ | provenance.py | — | MessageProvenance | ProvenanceOut → detail |
| Ingest | /projects/[id]/ingest | ingest/page.tsx | useIngest | POST /api/v1/ingest/upload | ingest.py | pipeline | Source, NormalizedMessage, Fact, Decision, GraphNode, GraphEdge | IngestUploadResponse → status |
| Sessions | /projects/[id]/sessions | sessions/page.tsx | useState | GET /api/v1/sessions/ | sessions.py | — | Session, Message | Session[] → list |
| Session Detail | /projects/[id]/sessions/[sessionId] | [sessionId]/page.tsx | useState | GET /api/v1/sessions/{id} | sessions.py | — | Session, Message | SessionHistory → messages |
| API Keys | /settings/api-keys | api-keys/page.tsx | useApiKeys | GET/POST/DELETE /api/v1/api-keys/ | api_keys.py | — | ApiKey | ApiKeyOut → list |
| Storage | /settings/storage | storage/page.tsx | useState | GET/POST /api/v1/storage/ | storage.py | object_storage | Storage backend | StorageOut → list |
| Profile | /settings/profile | profile/page.tsx | useState | GET/PATCH /api/v1/auth/me | auth.py | — | User | UserOut → form |
| Settings | /settings | settings/page.tsx | useState | — | — | — | — | — |

---

## AGENT 6 — SECURITY, TENANCY & OPERATIONAL ARCHITECTURE
**Output file:** `docs/SWARMVAULT_SECURITY_OPERATIONAL_ARCHITECTURE.md`

(Same as above — included in the comprehensive section above)

### Sections required:
- 6.1 through 6.12 as detailed above

---

## AGENT 7 — MEMORY INTELLIGENCE READINESS ARCHITECTURE
**Output file:** `docs/SWARMVAULT_MEMORY_INTELLIGENCE_READINESS.md`

(Same as above — included in the comprehensive section above)

### Sections required:
- 7.1 through 7.9 as detailed above

---

## FINAL SYNTHESIS AGENT

After all seven specialist documents are complete, launch a final
Architecture Synthesis Agent.

### Its mandate:
1. Read ALL seven specialist documents
2. Read all backend source files
3. Read all frontend source files
4. Read ALL Alembic migrations
5. Read ALL test files
6. Reconcile contradictions between specialist claims and source code
7. Resolve classification disagreements
8. Produce the final document package

### Documents produced by synthesis:

1. **SWARMVAULT_WEBAPP_MASTER_ARCHITECTURE.md** — 31 sections (detailed above)
2. **SWARMVAULT_END_TO_END_FLOWS.md** — 25 flows with complete traceability
3. **SWARMVAULT_GUARDRAIL_MASTER_MATRIX.md** — Complete control catalog + Memory Safety Gate Matrix
4. **SWARMVAULT_PERSISTENT_MEMORY_READINESS.md** — 15 questions answered with GREEN/YELLOW/RED
5. **SWARMVAULT_FRONTEND_BACKEND_ARCHITECTURE.md** — Complete screen-to-DB mapping
6. **SWARMVAULT_ARCHITECTURAL_TRACEABILITY.md** — Requirement-to-test traceability
7. **SWARMVAULT_ARCHITECTURAL_GAPS_AND_MEMORY_NEXT_LAYER.md** — P0-P3 gaps + readiness boundary
8. **SWARMVAULT_ARCHITECTURE_DOCUMENTATION_INDEX.md** — Document inventory

### MANDATORY DIAGRAMS (Mermaid)

1. System Context
2. Container Architecture
3. Backend Runtime (with actual class names)
4. Frontend Architecture
5. Data Flow (with actual function names)
6. M0-M5 Pipeline
7. Persistent Memory Pipeline
8. Retrieval Pipeline
9. Authentication/Authorization Flow
10. Ingestion Flow
11. Chat/SSE Flow
12. Provenance Flow
13. Frontend ↔ Backend Flow
14. Future Memory Intelligence Boundary

---

## FINAL CERTIFICATION

Choose exactly one:

1. **ARCHITECTURE DOCUMENTATION CERTIFIED**
2. **ARCHITECTURE DOCUMENTATION CERTIFIED WITH LIMITATIONS**
3. **ARCHITECTURE DOCUMENTATION NOT CERTIFIED**

---

## OUTPUT FORMAT SUMMARY

Return:

1. Repository identity (path, git status)
2. Agents executed (count + names)
3. Documents produced (count + filenames)
4. Backend coverage (modules inspected)
5. Frontend coverage (routes/components inspected)
6. Pipeline coverage (M0-M5 stages traced)
7. Guardrail coverage (controls identified)
8. Memory readiness conclusion (GREEN/YELLOW/RED per dimension)
9. Memory Intelligence readiness conclusion
10. Critical architectural gaps (P0 count)
11. Contradictions found (count)
12. Tests used as evidence (count)
13. Certification status
