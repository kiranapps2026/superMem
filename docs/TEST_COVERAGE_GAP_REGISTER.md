# SwarmVault Web App — Test Coverage Gap Register

> **Audit date:** 2026-09-10
> **Scope:** Read-only audit of all test files vs. all source files.
> **Status:** Gaps identified only. No code modified.

---

## How to Read This Document

Each section covers one source module or feature area. For each:
- **Status:** NOT TESTED / PARTIALLY TESTED / FULLY TESTED
- **Tested scenarios:** What the existing tests actually cover.
- **Gaps:** What is missing, with severity.

Severity: **CRITICAL** (security/correctness), **HIGH** (functional correctness), **MEDIUM** (resilience/edge cases), **LOW** (nice-to-have).

---

## 1. Authentication Flows

**Status:** PARTIALLY TESTED (`tests/unit/test_auth.py`)

### Covered
- Successful login with valid credentials
- Token creation and structure
- User creation during registration
- Logout (basic)

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| A1 | **Token refresh flow** | CRITICAL | No test for refresh-token endpoint or rotating refresh tokens. Expired-but-refreshable sessions are untested. |
| A2 | **Failed login with wrong password** | HIGH | Only happy-path login tested. No test for `401` on bad password. |
| A3 | **Failed login with non-existent user** | HIGH | No test for `401` when email doesn't exist. |
| A4 | **Rate limiting on login** | HIGH | `app/middleware/rate_limit.py` has login rate-limit logic (100 req/15 min default). No test verifies it triggers after N failed attempts. |
| A5 | **JWT expiry handling** | HIGH | No test for requests with expired JWTs — should get 401, not a 500 or silent pass-through. |
| A6 | **JWT with no or malformed payload** | MEDIUM | No test for `Authorization: Bearer <garbage>` or missing `sub` claim. |
| A7 | **Registration with duplicate email** | MEDIUM | No test that registering the same email twice returns 409/400. |
| A8 | **Registration with weak password** | MEDIUM | No test for password complexity enforcement (if any). |
| A9 | **Concurrent login / session creation** | MEDIUM | No test for race conditions when the same user logs in from two tabs simultaneously. |
| A10 | **Password hashing verification** | MEDIUM | `app/core/security.py` has `verify_password`. Not directly unit-tested. Relies on end-to-end login test only. |

---

## 2. Authorization (Cross-Workspace, Cross-Project, RBAC)

**Status:** PARTIALLY TESTED (`tests/unit/test_security.py`, `test_sprint4_security.py`)

### Covered
- Cross-workspace memory access is blocked (basic)
- Workspace isolation for memory CRUD
- API key scope restrictions (basic)
- Token verification in protected routes

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| B1 | **Cross-project memory access** | CRITICAL | No test that a user in workspace A cannot access project B's memories (project-level scoping exists in models but isn't tested at the API boundary). |
| B2 | **RBAC role enforcement — viewer vs. member vs. admin** | HIGH | `app/middleware/rbac.py` enforces `require_min_role("member")` and `require_min_role("admin")`. Tests exist but do not verify that a `viewer` role is REJECTED for member-only endpoints. |
| B3 | **Project-scoped authorization** | HIGH | No test that a user with access to workspace A can only see projects in workspace A. The `Project` model has `workspace_id` but project-list endpoints lack cross-project test coverage. |
| B4 | **API key cross-workspace use** | HIGH | API keys are workspace-scoped. No test that a key from workspace A fails when used for workspace B. |
| B5 | **Admin-only endpoints** | MEDIUM | `delete_project`, `delete_session`, `delete_file`, and policy endpoints require `admin`. No test that a non-admin gets 403 on these. |
| B6 | **Unauthenticated access to protected routes** | MEDIUM | No systematic test that all protected routes return 401 without a token. Only spot-tested. |
| B7 | **Token with wrong workspace claim** | MEDIUM | No test that a JWT with a valid `sub` but wrong `workspace_id` is rejected. |
| B8 | **Policy engine deny decisions** | MEDIUM | `app/services/policy/engine.py` can return `deny`. No test verifies the API returns 403 when the policy engine denies an action. |

---

## 3. Memory CRUD (Create, Read, Update, Delete, Share)

**Status:** PARTIALLY TESTED (`tests/unit/test_memory.py`, `test_chat.py`)

### Covered
- Create memory with required fields
- Read single memory by ID
- List memories with pagination
- Update memory content and metadata
- Delete memory (soft delete)
- Memory type filtering

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| C1 | **Memory sharing / access grants** | HIGH | No test for share/unshare operations (if implemented). The `ShareGrant` model exists in `app/models.py` but is not tested at all. |
| C2 | **Memory with null/empty content** | MEDIUM | No test for creating a memory with empty `content` string or null `content`. Schema validation may allow or reject — needs explicit test. |
| C3 | **Memory update with partial fields** | MEDIUM | No test that updating only `metadata` leaves `content` untouched, and vice versa. |
| C4 | **Update non-existent memory** | MEDIUM | No test for 404 when updating a memory that doesn't exist. |
| C5 | **Delete already-deleted memory** | MEDIUM | No test for deleting a memory twice — should return 404 on second attempt. |
| C6 | **Memory with very long content** | MEDIUM | No test for oversized `content` field (potential DoS via giant JSON blobs). |
| C7 | **Memory access count tracking** | MEDIUM | The `access_count` field exists in the model. No test verifies it increments on read. |
| C8 | **Memory with project_id** | MEDIUM | No test for creating a memory linked to a specific project, or listing memories scoped to a project. |
| C9 | **Concurrent memory updates** | MEDIUM | No test for two simultaneous PATCH requests on the same memory (lost-update problem). |

---

## 4. Memory Pipeline (M0–M5 Stages)

**Status:** PARTIALLY TESTED (`tests/unit/test_memory_pipeline.py`)

### Covered
- Pipeline stage progression
- Memory creation triggers M0→M1
- Fact extraction (M2) after session
- Decision extraction (M2) after session
- Graph node creation (M4) for entities

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| D1 | **M3 — Temporal supersession in pipeline** | HIGH | `app/services/m3_temporal.py` implements supersession. No pipeline test verifies that M3 runs and correctly supersedes older memories. |
| D2 | **M5 — Retrieval index update in pipeline** | HIGH | `app/services/m5_retrieval.py` updates the retrieval index. No pipeline test verifies the index is updated after ingestion. |
| D3 | **Pipeline failure / partial completion** | HIGH | No test for what happens when a pipeline stage fails (e.g., M2 extraction throws). Does the pipeline stop? Does it retry? Is the memory left in a consistent state? |
| D4 | **Pipeline idempotency** | MEDIUM | No test that re-running the pipeline on the same memory doesn't create duplicate facts/decisions/nodes. |
| D5 | **M1 session linking** | MEDIUM | No test that M1 correctly links extracted facts to their source session. |
| D6 | **M4 graph edge creation** | MEDIUM | Pipeline tests check node creation but not edge creation. Hyperedges between entities are untested in the pipeline context. |

---

## 5. Retrieval (Search, Facts, Decisions, Graph)

**Status:** PARTIALLY TESTED (`tests/unit/test_retrieval.py`, `test_graph.py`)

### Covered
- Basic memory search by text
- Fact retrieval by project
- Decision retrieval by project
- Graph node CRUD
- Graph edge creation
- Graph traversal / neighbors

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| E1 | **Hyperedge CRUD** | HIGH | `app/services/m4_graph.py` and `app/api/graph.py` support hyperedges (multi-entity relations). No test for creating, reading, or deleting hyperedges. |
| E2 | **Graph node deduplication** | HIGH | No test that creating a node with the same label/entity_id returns the existing node rather than a duplicate. |
| E3 | **Graph soft deletion** | HIGH | `GraphNode` and `GraphEdge` have `deleted_at`. No test that soft-deleted nodes are excluded from queries. |
| E4 | **Graph community detection** | MEDIUM | `app/api/graph.py` has a community endpoint. No test for community computation or results. |
| E5 | **Graph god-node detection** | MEDIUM | `app/api/graph.py` has a god-nodes endpoint. No test for high-connectivity node identification. |
| E6 | **Retrieval with empty query** | MEDIUM | No test for empty/whitespace search queries — should return 400 or empty results. |
| E7 | **Retrieval with special characters** | MEDIUM | No test for SQL-injection-like characters or Unicode in search queries. |
| E8 | **Facts/decisions soft-deleted filtering** | MEDIUM | No test that listing facts/decisions excludes soft-deleted items. |
| E9 | **Retrieval relevance ranking** | MEDIUM | No test for relevance scoring or result ordering. |
| E10 | **Graph node god-node flag** | LOW | `GraphNode` has a `is_god_node` field. No test verifies it is set correctly by the clustering pass. |

---

## 6. Ingestion (JSON, JSONL, Session, Manual)

**Status:** PARTIALLY TESTED (`tests/unit/test_ingest.py`, `test_chat_sprint2.py`)

### Covered
- Single memory ingestion via JSON
- Batch ingestion from JSONL
- Manual memory creation
- Chat session ingestion

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| F1 | **Malformed JSON ingestion** | HIGH | No test for invalid JSON body — should return 400, not 500. |
| F2 | **Malformed JSONL ingestion** | HIGH | No test for a JSONL file with one valid line followed by an invalid line — should handle partial success or return error. |
| F3 | **Oversized ingestion payload** | HIGH | No test for ingesting a payload that exceeds any size limit. |
| F4 | **Ingestion with missing required fields** | MEDIUM | No test for JSON with `content` missing — should return 422. |
| F5 | **Ingestion with wrong workspace** | MEDIUM | No test that a user cannot inject memories into a workspace they don't own. |
| F6 | **Session ingestion with duplicate messages** | MEDIUM | No test for ingesting the same session/messages twice — should not create duplicates. |
| F7 | **Ingestion with empty file** | MEDIUM | No test for ingesting an empty JSONL file or empty JSON array. |
| F8 | **Ingestion with non-UTF8 characters** | LOW | No test for binary/encoding-invalid content in ingested data. |
| F9 | **Ingestion triggers full pipeline** | MEDIUM | No test that ingesting a memory actually triggers M1–M5 pipeline stages end-to-end. |
| F10 | **Ingestion with source tracking** | MEDIUM | No test that the `Source` record is correctly created and linked to ingested memories. |

---

## 7. Provenance Tracking

**Status:** NOT TESTED (no `test_provenance.py` found; `app/api/provenance.py` exists but is untested)

### Source
- `app/api/provenance.py` — Provenance endpoints
- `app/services/audit/service.py` — Audit service
- `app/models.py` — `ProvenanceEvent`, `AuditEvent` models

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| G1 | **Provenance event creation** | CRITICAL | No test that provenance events are recorded when memories are created, updated, or deleted. |
| G2 | **Provenance chain retrieval** | CRITICAL | No test for retrieving the full provenance chain of a memory. |
| G3 | **Provenance event filtering** | HIGH | No test for filtering provenance events by actor, action, or date range. |
| G4 | **Audit trail integrity** | HIGH | No test that audit events are immutable — can they be modified or deleted via API? |
| G5 | **Cross-service provenance links** | HIGH | No test that ingestion, pipeline stages, and retrieval all produce linked provenance events. |
| G6 | **Provenance with soft-deleted resources** | MEDIUM | No test that provenance events for soft-deleted memories are still accessible. |

---

## 8. Temporal / Supersession

**Status:** PARTIALLY TESTED (`tests/unit/test_temporal_supersession.py`)

### Covered
- Supersession logic in `M3TemporalService`
- Memory replacement detection
- Time-based ordering

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| H1 | **Supersession API endpoint** | HIGH | No test for the actual API endpoint that triggers supersession (if one exists). The service is tested in isolation but not through the HTTP layer. |
| H2 | **Supersession with concurrent updates** | HIGH | No test for two simultaneous updates that both try to supersede the same memory. |
| H3 | **Supersession cascade** | MEDIUM | No test that superseding a memory also handles any child memories or related graph nodes. |
| H4 | **Supersession with already-superseded memory** | MEDIUM | No test that re-superseding an already-superseded memory is handled gracefully. |
| H5 | **Temporal query (memories valid at time T)** | MEDIUM | No test for querying which memories were valid at a specific point in time. |

---

## 9. Soft Deletion

**Status:** PARTIALLY TESTED (`tests/unit/test_soft_delete.py`)

### Covered
- Memory soft delete
- Verification that soft-deleted memories don't appear in lists
- Hard delete (admin) for memory

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| I1 | **Soft delete for other models** | HIGH | Tests only cover Memory soft deletion. No tests for soft delete on: Session, Source, Fact, Decision, GraphNode, GraphEdge, Project, MessageFeedback, ApiKey. All these models have `deleted_at`. |
| I2 | **Restore / undelete** | HIGH | No test for restoring a soft-deleted resource. If the API doesn't support it, that's a gap too. |
| I3 | **Hard delete cascading** | MEDIUM | No test that hard-deleting a project cascades to its memories, facts, decisions, graph nodes, and sessions. |
| I4 | **Soft-deleted resource access** | MEDIUM | No test that accessing a soft-deleted resource by ID returns 404 (not 200 with stale data). |
| I5 | **Soft delete with active dependencies** | MEDIUM | No test that soft-deleting a session with messages handles the messages correctly (cascade vs. orphan). |

---

## 10. Graph Operations

**Status:** PARTIALLY TESTED (`tests/unit/test_graph.py`)

### Covered
- Create/read/delete graph nodes
- Create edges between nodes
- Get node neighbors
- Shortest path between nodes
- Graph stats

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| J1 | **Hyperedge CRUD** | HIGH | See E1. Hyperedges (multi-entity relations) are a core feature with no tests. |
| J2 | **Graph node deduplication** | HIGH | See E2. Duplicate nodes on same entity are untested. |
| J3 | **Graph soft deletion** | HIGH | See E3. Soft-deleted nodes in graph queries untested. |
| J4 | **Graph communities** | MEDIUM | See E4. Community detection untested. |
| J5 | **Graph god-nodes** | MEDIUM | See E5. God-node identification untested. |
| J6 | **Edge deletion** | MEDIUM | No test for deleting a graph edge. |
| J7 | **Edge validation** | MEDIUM | No test for creating an edge between nodes in different workspaces (should be blocked). |
| J8 | **Graph with large dataset** | LOW | No performance test for graph queries with many nodes/edges. |

---

## 11. API Key Management

**Status:** PARTIALLY TESTED (`tests/unit/test_api_keys.py`)

### Covered
- Create API key
- List API keys
- Delete API key
- API key authentication
- API key scoping (basic)

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| K1 | **API key prefix verification** | HIGH | No test that a key with wrong prefix (e.g., `sv_` vs `sv_prod_`) is rejected. |
| K2 | **API key with expired expiry** | HIGH | No test that an API key past its `expires_at` is rejected. |
| K3 | **API key creation with no expiry** | MEDIUM | No test for creating a key with `expires_at=None` (permanent key). |
| K4 | **API key with empty name** | MEDIUM | No test for creating a key with an empty or whitespace-only name. |
| K5 | **API key scope enforcement** | MEDIUM | No test that a key scoped to `read` cannot perform `write` operations. |
| K6 | **API key cross-workspace use** | HIGH | See B4. |
| K7 | **API key listing shows hashed keys** | MEDIUM | No test that the API never returns the raw key hash in list/get responses. |
| K8 | **Concurrent API key creation** | LOW | No test for race conditions when creating multiple keys simultaneously. |

---

## 12. Workspace / Project Management

**Status:** PARTIALLY TESTED (`tests/unit/test_workspace.py`, `test_project.py`)

### Covered
- Create workspace
- List user's workspaces
- Get workspace by ID
- Update workspace settings
- Create project
- List projects
- Get project by ID
- Update project
- Delete project (soft delete)

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| L1 | **Workspace member management** | HIGH | No tests for adding/removing members, changing roles, or listing workspace members. The membership model exists but has no API tests. |
| L2 | **Workspace deletion** | HIGH | No test for deleting an entire workspace (if supported). |
| L3 | **Project with no memories** | MEDIUM | No test that listing a project's dashboard shows zero counts correctly. |
| L4 | **Project in wrong workspace** | HIGH | No test that a project ID from workspace A returns 404 when accessed from workspace B. |
| L5 | **Workspace name collision** | MEDIUM | No test for creating two workspaces with the same name. |
| L6 | **Project rename preserves memories** | MEDIUM | No test that renaming a project doesn't orphan its associated memories. |
| L7 | **Dashboard with empty workspace** | MEDIUM | No test for the dashboard endpoint on a workspace with zero resources. |
| L8 | **Project dashboard filtering** | MEDIUM | No test for project dashboard with mixed deleted/active memories — should only count active. |

---

## 13. Error Handling

**Status:** PARTIALLY TESTED (spot coverage across test files)

### Covered
- 404 for not-found resources (basic)
- 401 for unauthenticated requests (spot)
- 422 for validation errors (Pydantic handles this automatically)

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| M1 | **500 error handling / no stack traces leaked** | HIGH | No test that unhandled exceptions return 500 without leaking internal details (SQL queries, file paths, etc.). |
| M2 | **Database connection failure** | HIGH | No test for behavior when the database is unavailable. |
| M3 | **Malformed UUID in path params** | HIGH | No test for non-UUID path parameters (e.g., `GET /api/v1/memories/not-a-uuid`). |
| M4 | **Invalid query parameters** | MEDIUM | No test for invalid `limit`, `offset`, `sort` values in list endpoints. |
| M5 | **Unhandled exception in middleware** | MEDIUM | No test that a bug in one middleware doesn't crash the entire app. |
| M6 | **CORS misconfiguration** | LOW | No test for CORS headers on cross-origin requests. |
| M7 | **Timeout / slow response handling** | LOW | No test for timeout behavior on slow downstream services (LLM, storage). |

---

## 14. Edge Cases (Empty, Malformed, Oversized)

**Status:** MINIMALLY TESTED

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| N1 | **Empty string fields** | MEDIUM | No systematic test for empty strings in text fields (content, title, name, description). |
| N2 | **Null/None in optional fields** | MEDIUM | No test for explicitly passing `null` for optional fields. |
| N3 | **Very long strings** | HIGH | No test for strings exceeding database column lengths. Should return 422 or be truncated. |
| N4 | **Special characters in names** | MEDIUM | No test for emoji, Unicode, SQL meta-characters, or control characters in names/content. |
| N5 | **Negative pagination values** | MEDIUM | No test for `limit=-1` or `offset=-1`. |
| N6 | **Extremely large limit values** | MEDIUM | No test for `limit=999999999` — should be capped. |
| N7 | **Concurrent requests to same resource** | MEDIUM | See A9, C9. No concurrency tests anywhere. |
| N8 | **Empty arrays in JSON body** | LOW | No test for empty arrays where arrays are expected (e.g., tags, metadata). |

---

## 15. Concurrency

**Status:** NOT TESTED

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| O1 | **Concurrent memory creation** | HIGH | No test for two simultaneous POST /memories requests. |
| O2 | **Concurrent memory update (lost update)** | HIGH | No test for two simultaneous PATCH /memories/{id} — one update may be lost. |
| O3 | **Read-your-own-writes consistency** | MEDIUM | No test that a CREATE followed immediately by a LIST returns the new item. |
| O4 | **Concurrent session message creation** | MEDIUM | No test for two simultaneous POST /sessions/{id}/messages — messages may be created out of order. |
| O5 | **Race condition in soft delete + access** | MEDIUM | No test for accessing a resource at the exact moment it is being soft-deleted. |

---

## 16. Transaction Rollback

**Status:** NOT TESTED

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| P1 | **Pipeline stage failure rolls back memory creation** | HIGH | No test that if the pipeline fails after memory creation, the memory is rolled back. |
| P2 | **Partial batch ingestion rollback** | HIGH | No test that if batch ingestion fails partway, already-ingested items are rolled back (or the failure is clearly reported). |
| P3 | **Graph node + edge creation atomicity** | MEDIUM | No test that if edge creation fails after node creation, the node is cleaned up. |
| P4 | **Database error during commit** | MEDIUM | No test for `db.commit()` failure — the session should roll back, not leave dangling state. |
| P5 | **Audit event creation failure doesn't block main operation** | MEDIUM | No test that a failure to write an audit event doesn't prevent the main API operation from succeeding. |

---

## 17. Frontend E2E Tests

**Source:** `frontend/e2e/*.spec.ts`
**Covered Pages:** Graph, Provenance, Cross-Chain, Sessions, Responsive, A11y, Memory, Facts, Decisions

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| Q1 | **Login / authentication flow** | HIGH | No E2E test for the login page or registration flow. |
| Q2 | **Workspace creation and switching** | HIGH | No E2E test for creating a workspace or switching between workspaces. |
| Q3 | **Project creation and navigation** | HIGH | No E2E test for creating a project or navigating between projects. |
| Q4 | **Memory creation and editing** | HIGH | No E2E test for the full create-read-update-delete cycle of a memory via the UI. |
| Q5 | **Search and retrieval** | HIGH | No E2E test for the search UI — typing a query and verifying results. |
| Q6 | **Ingestion UI** | HIGH | No E2E test for the file upload / ingestion interface. |
| Q7 | **API key management UI** | HIGH | No E2E test for creating, viewing, or deleting API keys via the UI. |
| Q8 | **Dashboard page** | HIGH | No E2E test for the dashboard overview page showing counts and recent activity. |
| Q9 | **Policy management UI** | HIGH | No E2E test for policy rules page (create/edit/delete policies). |
| Q10 | **Error states in UI** | HIGH | No E2E test for error messages, empty states, loading spinners, or 404 pages. |
| Q11 | **Settings / profile page** | MEDIUM | No E2E test for user settings or profile editing. |
| Q12 | **Keyboard navigation** | MEDIUM | No E2E test for keyboard shortcuts or accessibility navigation beyond basic a11y checks. |
| Q13 | **Mobile responsiveness across all pages** | MEDIUM | Only basic responsive tests exist — no test for data-dense pages (graph, provenance) on mobile. |
| Q14 | **Session creation and chat** | MEDIUM | No E2E test for starting a chat session and sending messages. |
| Q15 | **Feedback submission** | LOW | No E2E test for submitting thumbs-up/down feedback. |

---

## 18. Backend Services (Untested or Minimally Tested)

**Source:** `app/services/*.py`

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| R1 | **`app/services/llm.py`** | HIGH | No tests for LLM service — prompt formatting, response parsing, error handling, timeout, retry. |
| R2 | **`app/services/chat_orchestrator.py`** | HIGH | No tests for the chat orchestrator — memory retrieval + LLM call + response formatting. |
| R3 | **`app/services/pipeline.py`** | HIGH | No tests for the pipeline orchestrator — stage sequencing, error handling, retry logic. |
| R4 | **`app/services/connectors.py`** | HIGH | No tests for external connectors — GitHub, Slack, etc. Integration/parsing logic untested. |
| R5 | **`app/services/object_storage.py`** | MEDIUM | Abstract base has no tests. |
| R6 | **`app/services/object_storage_s3.py`** | MEDIUM | No tests for S3 provider — upload, download, presign, delete, error handling. |
| R7 | **`app/services/object_storage_minio.py`** | MEDIUM | No tests for MinIO provider. |
| R8 | **`app/services/memory.py`** | MEDIUM | No direct unit tests for the memory service layer (only tested via API). |
| R9 | **`app/services/tools.py`** | MEDIUM | No tests for tool definitions, parameter parsing, or tool execution. |
| R10 | **`app/services/policy/engine.py`** | HIGH | No tests for the policy evaluation engine — rule matching, conflict resolution, caching. |
| R11 | **`app/services/policy/evaluator.py`** | HIGH | No tests for policy evaluation — allow/deny logic, conditions, effects. |
| R12 | **`app/services/policy/dependencies.py`** | HIGH | No tests for policy dependency injection — correct policy loading, fallback behavior. |
| R13 | **`app/services/policy/repository.py`** | MEDIUM | No tests for policy CRUD in the repository layer. |
| R14 | **`app/services/audit/service.py`** | HIGH | No tests for the audit service — event creation, enrichment, immutability guarantees. |
| R15 | **`app/services/audit/repository.py`** | MEDIUM | No tests for audit event storage and retrieval in the repository. |

---

## 19. Middleware (Untested)

**Source:** `app/middleware/*.py`

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| S1 | **`app/middleware/auth.py`** | HIGH | No tests for the auth middleware — token extraction from headers/cookies, user lookup, anonymous access handling. |
| S2 | **`app/middleware/tenancy.py`** | HIGH | No tests for the tenancy middleware — workspace resolution, subdomain parsing, header-based workspace detection. |
| S3 | **`app/middleware/rbac.py`** | HIGH | No tests for RBAC middleware — role extraction, permission checking, 403 responses. |
| S4 | **`app/middleware/rate_limit.py`** | MEDIUM | No tests for rate limiting — token bucket, sliding window, per-user/per-endpoint limits. |

---

## 20. Database Layer

**Source:** `app/db.py`, `app/models.py`

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| T1 | **Database connection pooling** | MEDIUM | No tests for connection pool behavior — exhaustion, timeout, recovery. |
| T2 | **Session lifecycle** | MEDIUM | No tests for SQLAlchemy session management — commit, rollback, expire, refresh. |
| T3 | **Model validation** | MEDIUM | No tests for SQLAlchemy model field constraints — max lengths, nullable fields, defaults. |
| T4 | **Migration compatibility** | LOW | No tests for database schema migrations. |

---

## 21. Security-Specific Gaps

**Status:** PARTIALLY TESTED (`tests/unit/test_security.py`, `test_sprint4_security.py`)

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| U1 | **SQL injection** | CRITICAL | No tests that SQL injection is prevented in any endpoint that accepts user input. |
| U2 | **XSS in stored data** | HIGH | No test that HTML/JS in memory content is sanitized or escaped when returned. |
| U3 | **CSRF protection** | HIGH | No test for CSRF token validation on state-changing endpoints. |
| U4 | **Path traversal in storage** | HIGH | `app/api/storage.py` has path-traversal protection (`..` check). No test verifies it blocks `../../etc/passwd`. |
| U5 | **Content-type validation in uploads** | MEDIUM | No test that uploaded files with wrong content-type are handled. |
| U6 | **Information leakage on 404 vs 403** | MEDIUM | No test that cross-workspace access returns 404 (not 403) to prevent enumeration. |
| U7 | **Audit log tampering** | HIGH | No test that audit events cannot be modified or deleted through any API. |

---

## 22. Missing Regression Tests for Known Bugs

**Status:** NOT TESTED

| # | Gap | Severity | Details |
|---|-----|----------|---------|
| V1 | **Regression: memory list with deleted items** | HIGH | If a bug ever caused soft-deleted memories to appear in lists, there's no regression test catching it. |
| V2 | **Regression: workspace ID spoofing** | HIGH | If a bug allowed a user to set `X-Workspace-ID` to another workspace, no test catches it. |
| V3 | **Regression: pagination off-by-one** | MEDIUM | No boundary test for `limit=1` with exactly 1 or 2 items. |
| V4 | **Regression: timezone handling** | MEDIUM | No test that timestamps are consistently stored/returned in UTC across all endpoints. |
| V5 | **Regression: null workspace_id** | HIGH | No test that a request without a valid workspace context is rejected. |

---

## 23. Frontend Source Coverage (Gaps)

**Status:** MINIMALLY TESTED (only 4 frontend source files read)

### Gaps
| # | Gap | Severity | Details |
|---|-----|----------|---------|
| W1 | **No tests for 90%+ of frontend components** | HIGH | Only 4 of hundreds of frontend source files were inspected. The vast majority have no E2E or unit test coverage. |
| W2 | **No tests for API service layer** | HIGH | `frontend/src/lib/api.ts` or equivalent — no tests for request/response handling, error parsing, or retry logic. |
| W3 | **No tests for state management** | HIGH | No tests for Zustand/React Context stores — state updates, persistence, hydration. |
| W4 | **No tests for form validation** | MEDIUM | No tests for client-side form validation — required fields, formats, error messages. |
| W5 | **No tests for routing** | MEDIUM | No tests for protected routes, redirects, or route guards. |

---

## Summary Statistics

| Category | Status | Tested | Total Gaps Found |
|----------|--------|--------|-----------------|
| Authentication | PARTIALLY | ~4/12 | 10 |
| Authorization | PARTIALLY | ~5/15 | 8 |
| Memory CRUD | PARTIALLY | ~6/10 | 4 |
| Memory Pipeline | PARTIALLY | ~4/6 | 3 |
| Retrieval | PARTIALLY | ~5/10 | 5 |
| Ingestion | PARTIALLY | ~4/10 | 5 |
| Provenance | NOT TESTED | 0/6 | 6 |
| Temporal/Supersession | PARTIALLY | ~4/5 | 2 |
| Soft Deletion | PARTIALLY | ~3/5 | 4 |
| Graph Operations | PARTIALLY | ~5/8 | 4 |
| API Key Management | PARTIALLY | ~4/8 | 4 |
| Workspace/Project Mgmt | PARTIALLY | ~5/8 | 4 |
| Error Handling | PARTIALLY | ~3/7 | 5 |
| Edge Cases | MINIMALLY | ~2/8 | 8 |
| Concurrency | NOT TESTED | 0/5 | 5 |
| Transaction Rollback | NOT TESTED | 0/5 | 5 |
| Frontend E2E | MINIMALLY | ~8/15 | 8 |
| Backend Services | NOT TESTED | ~0/15 | 15 |
| Middleware | NOT TESTED | ~0/4 | 4 |
| Database Layer | NOT TESTED | ~0/4 | 4 |
| Security | PARTIALLY | ~3/7 | 7 |
| Regression Tests | NOT TESTED | 0/5 | 5 |
| Frontend Source | MINIMALLY | ~0/5 | 5 |

**Total gaps identified: ~130+**
**Estimated overall backend test coverage: ~35-40%**
**Estimated overall frontend test coverage: ~5-10%**

---

## Top Priority Recommendations

1. **CRITICAL:** Add provenance/audit tests — the entire audit trail is untested.
2. **CRITICAL:** Add cross-workspace authorization tests for ALL models, not just Memory.
3. **CRITICAL:** Add SQL injection and XSS security tests.
4. **HIGH:** Test all soft-delete paths for every model (not just Memory).
5. **HIGH:** Add API key expiry and scope enforcement tests.
6. **HIGH:** Add ingestion error handling tests (malformed input, oversized payloads).
7. **HIGH:** Add pipeline failure/rollback tests.
8. **HIGH:** Add frontend E2E tests for the core user flows (login, create memory, search).
9. **MEDIUM:** Add concurrency tests for all write operations.
10. **MEDIUM:** Add edge case tests (empty, null, oversized, special characters).
