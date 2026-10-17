# SwarmVault End-to-End System Flows

**Forensic Reconciliation Phase — Final Synthesis**
**Baseline SHA:** e6f4b1c157afaed052584963b942ea04f9661610
**Date:** 2026-09-10

---

## FLOW-001: User Registration

**Trigger:** User submits registration form with email, password, name
**Source:** `app/api/auth.py:1-80` — `POST /api/v1/auth/register`

| Step | Component | Action | Validation | Guardrail | Failure | Persistence | Provenance |
|------|-----------|--------|------------|-----------|---------|-------------|------------|
| 1 | Frontend `/register` | Collect email, password, name | Client: email format, password length | None | Validation error shown | None | None |
| 2 | API Router | Receive `UserCreate` schema | Pydantic: email format, password min 8 chars, name required | Schema validation | 422 if invalid | None | None |
| 3 | Auth Service | `create_user()` | Check email uniqueness via DB query | Unique constraint on `users.email` | 409 if exists | None | None |
| 4 | Security Core | `hash_password(plain)` | bcrypt via passlib | Password never stored plain | 500 on hashing failure | None | None |
| 5 | DB | INSERT into `users` | ORM validation | Unique email constraint | IntegrityError → 409 | User record created | user_id generated |
| 6 | Auth Service | `create_access_token(user_id)` | JWT with 60min expiry | Secret key from env | 500 if misconfigured | None | JWT claims: sub=user_id |
| 7 | Auth Service | `create_refresh_token(user_id)` | Random token, 30-day expiry | Stored hashed in `refresh_tokens` | 500 on DB error | RefreshToken record | token hash stored |
| 8 | Response | Return tokens + user | None | None | 500 | None | None |

**Security boundary:** HTTPS required. Password hashed before storage. JWT signed with server secret. Refresh token stored hashed.

---

## FLOW-002: Login

**Trigger:** User submits login form with email, password
**Source:** `app/api/auth.py:80-150` — `POST /api/v1/auth/login`

| Step | Component | Action | Validation | Guardrail | Failure | Persistence | Provenance |
|------|-----------|--------|------------|-----------|---------|-------------|------------|
| 1 | Frontend `/login` | Collect email, password | Client validation | None | Error shown | None | None |
| 2 | API Router | Receive `LoginRequest` schema | Pydantic validation | Schema | 422 | None | None |
| 3 | Auth Service | Query user by email | Email exists | None | 401 "Invalid credentials" | None | None |
| 4 | Security Core | `verify_password(plain, hashed)` | bcrypt comparison | Timing-safe via passlib | 401 on mismatch | None | None |
| 5 | Auth Middleware | Check `user.is_active` | Active check | Soft-delete check | 401 "Inactive" | None | None |
| 6 | Auth Service | Create access + refresh tokens | JWT + random | Expiry enforced | 500 | RefreshToken record | JWT claims |
| 7 | Response | Return tokens + user profile | None | None | 500 | None | None |

**Failure behavior:** Always returns generic "Invalid credentials" — does not reveal whether email exists or password is wrong.

---

## FLOW-003: Workspace Creation

**Trigger:** Authenticated user creates workspace
**Source:** `app/api/workspaces.py` — `POST /api/v1/workspaces`

| Step | Component | Action | Validation | Guardrail | Failure | Persistence | Provenance |
|------|-----------|--------|------------|-----------|---------|-------------|------------|
| 1 | Frontend | POST with name, description | Required fields | Auth required | 401 | None | None |
| 2 | Auth Middleware | Extract JWT, validate, get user | Token valid, user active | Fail-closed | 401/403 | None | user_id in context |
| 3 | Workspace Service | Create workspace with owner_id | Name uniqueness per user | None | 409 | Workspace record | owner_id, created_at |
| 4 | RBAC | Grant owner role to creator | Role assignment | PolicyEngine | 403 if policy denies | Role record | role=owner |
| 5 | Audit | Log workspace creation | None | Audit always fires | None | AuditEvent | workspace_id, user_id |

---

## FLOW-004: Project Creation

**Trigger:** Authenticated user creates project in workspace
**Source:** `app/api/projects.py` — `POST /api/v1/projects`

| Step | Component | Action | Validation | Guardrail | Failure | Persistence | Provenance |
|------|-----------|--------|------------|-----------|---------|-------------|------------|
| 1 | Frontend | POST name, description, workspace_id | Required fields | Auth + workspace membership | 401/403 | None | None |
| 2 | Tenancy Middleware | Resolve workspace from header/JWT | Workspace exists, user is member | Cross-tenant isolation | 404/403 | None | workspace_id in context |
| 3 | Project Service | Create project | Name unique per workspace | None | 409 | Project record | workspace_id FK |
| 4 | Audit | Log project creation | None | Audit | None | AuditEvent | project_id |

---

## FLOW-005: Session Ingestion (Raw Text)

**Trigger:** User uploads conversation text via ingest endpoint
**Source:** `app/api/ingest.py:38` — `POST /ingest/upload`

```
INPUT
  • project_id: UUID
  • source_type: "text" | "json" | "jsonl" | "chatgpt"
  • content: str (max 1MB)
  • title: str
  • config: dict (optional)

PROCESSING PIPELINE (M0 → M5):
  ↓
M0: Connector.parse() → List[NormalizedMessage]
  • 6 connectors: text, json, jsonl, chatgpt, openai_chat, openai_playground
  • Each: detect() → validate() → parse()
  • Output: structured messages with role, content, timestamp, metadata
  ↓
M1: Session Understanding
  • Extracts session metadata, participants, topics
  • Output: session_summary dict
  ↓
M2: Fact/Decision Extraction
  • Regex patterns for "X is Y", "decided to X", "agreed that X"
  • Output: List[Fact], List[Decision]
  ↓
M3: Temporal Processing
  • Same-subject/predicate supersession
  • Sets temporal_status="historical" on superseded facts
  ↓
M4: Graph Construction
  • Entity extraction, relationship typing
  • Creates GraphNode + GraphEdge
  ↓
M5: Retrieval Preparation
  • Multi-factor scoring computation
  • No embedding generation

PERSISTENCE:
  • Source record (content_hash dedup check)
  • NormalizedMessage records
  • Fact records (with source_id, confidence, authority)
  • Decision records (with source_id, confidence, authority)
  • GraphNode + GraphEdge records
  • M1 output: NOT persisted (returned in response only)
```

**Validation chain:**
- Schema: `IngestUploadRequest` (Pydantic)
- Content hash: SHA-256, checked against existing Sources
- Size: max 1MB
- Duplicate: same hash + workspace → skip
- Auth: minimum role "member"
- Tenancy: workspace membership required

**Guardrails:**
- Duplicate detection prevents re-processing
- Max content size enforced
- Null byte check on content
- Source type validation

**Failure modes:**
- Invalid source_type → 400
- Content too large → 422
- Duplicate → 200 with "already processed" status
- Pipeline failure → error recorded in Source.error_message

---

## FLOW-006: JSON Ingestion

**Trigger:** User uploads JSON-formatted conversation
**Source:** `app/services/connectors.py` — `JSONConnector`

Same flow as FLOW-005 but with `source_type="json"`.
- Connector: `JSONConnector.detect()` → matches JSON array/object structure
- `validate()`: checks for `messages` array or `conversations` array
- `parse()`: normalizes to List[NormalizedMessage]

**Additional validation:**
- JSON parse error → 400 with detail
- Missing expected keys → warning in normalized messages

---

## FLOW-007: JSONL Ingestion

**Trigger:** User uploads JSONL-formatted conversation
**Source:** `app/services/connectors.py` — `JSONLConnector`

Same flow as FLOW-005 but with `source_type="jsonl"`.
- Connector: `JSONLConnector.detect()` → line-by-line JSON detection
- `validate()`: each line must be valid JSON
- `parse()`: each line → NormalizedMessage

**Additional validation:**
- Line parse error → warning, skip line
- Empty lines → skipped

---

## FLOW-008: M0 Normalization

**Trigger:** Raw content enters pipeline via `run_pipeline()`
**Source:** `app/services/pipeline.py:32-75`

```
INPUT: Raw string or dict content + source_type

PROCESSING:
  1. ConnectorRegistry.detect(content, source_type) → connector class
  2. connector.validate(content) → bool
  3. connector.parse(content) → List[NormalizedMessage]
     Each NormalizedMessage:
       • role: "user" | "assistant" | "system"
       • content: str
       • timestamp: datetime | None
       • metadata: dict (model, provider, tokens, etc.)

OUTPUT: List[NormalizedMessage] + session_metadata dict

VALIDATION:
  • Connector.validate() must pass
  • Each message must have role and content
  • Null bytes stripped from content

FAILURE: ValidationError → pipeline aborts, error recorded

PERSISTENCE: None at M0 stage. Messages stored after full pipeline completes.

PROVENANCE: Each NormalizedMessage inherits source_id from parent Source record.
```

---

## FLOW-009: M1 Session Understanding

**Trigger:** After M0 produces NormalizedMessages
**Source:** `app/services/pipeline.py:75-95`

```
INPUT: List[NormalizedMessage] + session metadata

PROCESSING:
  • Extracts participants (unique roles)
  • Identifies conversation topics (from content)
  • Counts messages, estimates duration
  • Detects language
  • Identifies agent model from metadata

OUTPUT: session_summary dict
  {
    "participants": [...],
    "message_count": int,
    "topics": [...],
    "duration_seconds": int,
    "language": str,
    "agent_model": str
  }

VALIDATION: None beyond M0 output validity

FAILURE: Returns empty/default summary. Pipeline continues.

PERSISTENCE: **NOT PERSISTED** — returned in API response only. Lost after ingestion completes.

PROVENANCE: Derived from NormalizedMessage metadata. No explicit provenance tracking.
```

**GAP:** M1 output is ephemeral. Future memory intelligence cannot access session understanding without re-processing.

---

## FLOW-010: M2 Fact/Decision Extraction

**Trigger:** After M1 completes
**Source:** `app/services/pipeline.py:95-170`

```
INPUT: List[NormalizedMessage]

FACT EXTRACTION:
  • Regex patterns:
    - "X is Y" / "X was Y"
    - "X has Y"
    - "X uses Y"
    - "X depends on Y"
  • For each match:
    - subject, predicate, object extracted
    - confidence = 0.8 (hardcoded)
    - authority = 0.75 (hardcoded)
    - source_id = parent Source
    - temporal_status = "current"

DECISION EXTRACTION:
  • Regex patterns:
    - "decided to X"
    - "agreed that X"
    - "we will X"
    - "resolved to X"
  • For each match:
    - content = full match text
    - context = surrounding message
    - confidence = 0.75 (hardcoded)
    - authority = 0.75 (hardcoded)

OUTPUT: List[Fact], List[Decision]

VALIDATION:
  • Non-empty subject/predicate/object for facts
  • Non-empty content for decisions

FAILURE: No match → empty lists. Pipeline continues.

PERSISTENCE: Records inserted after full M2-M5 pipeline completes.

PROVENANCE: Each Fact/Decision carries source_id → Source → IngestJob chain.
```

**GAP:** Confidence/authority are hardcoded, not LLM-calibrated. All facts appear equally reliable.

---

## FLOW-011: M3 Temporal Processing

**Trigger:** After M2 extracts Facts and Decisions
**Source:** `app/services/pipeline.py:112-137`, `app/services/m3_temporal.py`

```
INPUT: List[Fact], List[Decision] (all with temporal_status="current")

PROCESSING:
  1. Group facts by (subject, predicate)
  2. For each group with >1 facts:
     a. Sort by created_at
     b. Mark all but latest as temporal_status="historical"
     c. **NOTE: superseded_by_id is NEVER written** (gap P1-1)
  3. Decisions: same grouping logic
  4. **NOTE: m3_temporal.py functions exist but are NEVER called by pipeline**

OUTPUT: List[Fact] (with updated temporal_status), List[Decision]

VALIDATION:
  • Same (subject, predicate) pairs identified
  • Sorted chronologically

FAILURE: Empty groups → no changes

PERSISTENCE: Fact.temporal_status updated in DB batch

PROVENANCE: Supersession tracked via temporal_status only. No chain links.
```

**GAP:** `superseded_by_id` column exists on Fact and Decision models but is never populated. The M3 temporal module (`m3_temporal.py`) has standalone supersession functions that are never called by the pipeline. Dead code with incomplete implementation.

---

## FLOW-012: M4 Graph Construction

**Trigger:** After M3 completes
**Source:** `app/services/m4_graph.py`

```
INPUT: List[NormalizedMessage], List[Fact], List[Decision]

PROCESSING:
  1. Entity extraction from content:
     • Named entities (ORG, PERSON, TECH via regex)
     • Concepts from fact subjects/objects
  2. Deduplication:
     • Same label + same node_type → single GraphNode
     • Hash-based dedup on (label, node_type)
  3. Relationship creation:
     • From fact predicates: "is_a", "uses", "connects_to", "depends_on"
     • From decision context: "relates_to"
  4. GraphEdge creation:
     • source_node_id, target_node_id
     • relationship_type
     • confidence (from parent fact)
     • source_id (from parent Source)

OUTPUT: List[GraphNode], List[GraphEdge]

VALIDATION:
  • Node label non-empty
  • Node type in allowed set
  • Edge endpoints exist

FAILURE: No entities found → empty graph

PERSISTENCE: GraphNode + GraphEdge records inserted

PROVENANCE: Each GraphEdge carries source_id → Source chain.
```

**GAP:** GraphNode.temporal_status is set but never transitions from "current". Graph appears fully current regardless of supersession.

---

## FLOW-013: M5 Retrieval Preparation

**Trigger:** After M4 completes
**Source:** `app/services/m5_retrieval.py`, `app/services/retrieval.py`

```
INPUT: workspace_id, query text, optional filters

PROCESSING (M5 — canonical retrieval):
  1. Keyword search on Fact + Decision content (ILIKE)
  2. Authority score weighting
  3. Confidence score weighting
  4. Recency score (exponential decay, 30-day half-life)
  5. Temporal status filter (current preferred)
  6. Graph context score (neighbor boost)
  7. Multi-factor ranking: sum of weighted scores

OUTPUT: List[RankedItem] with scores

NOTE: Memory model is EXCLUDED from M5 retrieval (DECISION-004 gap)
NOTE: No embedding/semantic search (DECISION-005 gap)

PERSISTENCE: None — retrieval is computed at query time

PROVENANCE: Each result carries source_id, confidence, authority, temporal_status
```

---

## FLOW-014: Persistent Memory Creation

**Trigger:** User or agent creates memory record
**Source:** `app/api/memory.py:78` — `POST /api/v1/memory`

```
INPUT:
  • content: str (max 1MB)
  • memory_type: "semantic" | "episodic" | "procedural" | "working"
  • project_id: UUID
  • agent_id: str (optional)
  • run_id: str (optional)
  • extra_metadata: dict (optional)
  • confidence: float (default 0.7)
  • authority: float (default 1.0)

PROCESSING:
  1. Schema validation (MemoryCreate)
  2. Null byte check
  3. Whitespace-only check
  4. MemoryService.write():
     a. Create Memory record
     b. Attach provenance (list of dicts → extra_metadata)
     c. Emit audit event

OUTPUT: MemoryResponse with id, content, type, temporal_status, confidence, authority

VALIDATION:
  • Pydantic schema
  • Null bytes rejected
  • Whitespace-only rejected
  • Workspace membership checked

FAILURE:
  • Validation error → 422
  • Not in workspace → 403
  • DB error → 500

PERSISTENCE: Memory record in PostgreSQL

PROVENANCE: Stored in Memory.extra_metadata["provenance"] as JSON list. NOT linked to Source table.
```

**GAP:** Memory has no `source_id` FK. Provenance is JSON-only, not queryable.

---

## FLOW-015: Memory Retrieval

**Trigger:** User requests memories for project/workspace
**Source:** `app/api/memory.py` — `GET /api/v1/memory/`

```
INPUT:
  • project_id (optional filter)
  • memory_type (optional filter)
  • scope (optional filter)
  • include_deleted (default false)

PROCESSING:
  1. Tenancy resolution (workspace from JWT/header)
  2. MemoryService.list():
     a. Query Memory by workspace_id
     b. Filter by temporal_status != "deleted"
     c. Filter by memory_type if provided
     d. Filter by scope if provided (JSON field — partial)
  3. Pagination

OUTPUT: List[MemoryResponse] with pagination

VALIDATION:
  • Workspace membership
  • Schema compliance

FAILURE:
  • No workspace → 401
  • Not a member → 403

PERSISTENCE: Read-only from Memory table

PROVENANCE: extra_metadata.provenance returned in response
```

**GAP:** `project_id` filter in schema but not implemented in service. Scope filter only works in MemoryService cache path.

---

## FLOW-016: Search

**Trigger:** User searches knowledge base
**Source:** `app/api/ingest.py` — `POST /ingest/search`

```
INPUT:
  • query: str
  • project_id: UUID
  • memory_type: str (optional)
  • limit: int (default 10)

PROCESSING:
  1. Tenancy resolution
  2. Keyword search on:
     • Fact.content (ILIKE)
     • Decision.content (ILIKE)
     • Memory.content (ILIKE) — via separate retrieval.py service
  3. **NOTE: No semantic/vector search** (gap P1-2)
  4. Results merged and deduplicated

OUTPUT: SearchResponse with items, total

VALIDATION:
  • Query non-empty
  • Project membership

FAILURE:
  • Empty query → 422
  • Project not found → 404
```

---

## FLOW-017: Chat

**Trigger:** User sends message in chat interface
**Source:** `app/services/chat_orchestrator.py:25` — `process_chat()`

```
INPUT:
  • message: str
  • session_id: UUID (optional, creates new if missing)
  • project_id: UUID

PROCESSING:
  1. Get/create session
  2. M5 retrieval: find relevant facts/decisions for query
  3. Assemble context:
     a. System prompt
     b. Retrieved facts/decisions (M5 results)
     c. Chat history from session
  4. LLM call: Anthropic messages.create()
     a. Context messages
     b. User message
  5. Post-process:
     a. Create memory from response
     b. Extract new facts via LLM
     c. Create graph nodes
  6. Persist:
     a. User message → NormalizedMessage
     b. Assistant response → NormalizedMessage
     c. Memory record
     d. MessageProvenance record

OUTPUT: ChatResponse with content, session_id, sources

VALIDATION:
  • Auth required
  • Project membership
  • Message non-empty

FAILURE:
  • LLM timeout → 504
  • LLM error → 500 with retry

PERSISTENCE:
  • Session messages
  • Memory record
  • MessageProvenance
  • New facts/decisions from LLM extraction

PROVENANCE: MessageProvenance records memory_ids_used, retrieval_sources, model, latency, tokens.
```

---

## FLOW-018: SSE Chat Streaming

**Trigger:** User sends message, requests streaming response
**Source:** `app/api/chat.py` — `POST /api/v1/chat/stream`

```
INPUT: Same as FLOW-017

PROCESSING:
  1. Same as FLOW-017 steps 1-3
  2. LLM streaming: anthropic.Anthropic().messages.stream()
  3. Yield SSE events:
     a. {"type": "token", "content": "..."}
     b. {"type": "sources", "data": [...]} (on completion)
     c. {"type": "done"}
     d. {"type": "error", "detail": "..."} (on failure)
  4. On completion:
     a. Persist full response
     b. Create memory
     c. Extract facts
     d. Create provenance

OUTPUT: StreamingResponse with SSE events

VALIDATION: Same as FLOW-017

FAILURE:
  • Client disconnect → CancelledError (NOT propagated to LLM — gap P3-5)
  • LLM error → error event streamed, partial response persisted

PERSISTENCE: Same as FLOW-017 (after stream completes)

PROVENANCE: Same as FLOW-017

GAP: No read timeout on streaming response. Slow clients hold connections open.
```

---

## FLOW-019: Provenance

**Trigger:** User requests provenance for a chat response
**Source:** `app/api/provenance.py` — `GET /api/v1/provenance/`

```
INPUT:
  • project_id: UUID
  • session_id: UUID (optional)
  • message_id: UUID (optional)

PROCESSING:
  1. Query MessageProvenance records
  2. Filter by project_id, session_id
  3. Return with:
     • model, provider
     • latency_ms, token counts
     • memory_ids_used (list of UUIDs)
     • retrieval_sources (list of dicts)
     • user_message_preview (truncated)

OUTPUT: List[ProvenanceOut]

VALIDATION:
  • Project membership
  • Session ownership

FAILURE:
  • No provenance records → empty list
```

---

## FLOW-020: Graph Exploration

**Trigger:** User views knowledge graph for project
**Source:** `app/api/ingest.py` — `GET /ingest/graph`

```
INPUT:
  • project_id: UUID

PROCESSING:
  1. Query GraphNode + GraphEdge for workspace
  2. Build adjacency structure
  3. Return nodes + edges

OUTPUT: GraphResponse {nodes: [...], edges: [...]}

VALIDATION:
  • Project membership

FAILURE:
  • No graph data → empty lists

PERSISTENCE: Read-only from graph_nodes + graph_edges

PROVENANCE: Each edge carries source_id
```

---

## FLOW-021: Memory Deletion

**Trigger:** User deletes memory record
**Source:** `app/api/memory.py` — `DELETE /api/v1/memory/{id}`

```
INPUT: memory_id: UUID

PROCESSING:
  1. Auth + tenancy check
  2. MemoryService.delete():
     a. Set deleted_at = now()
     b. Emit audit event
  3. Soft delete — record remains in DB

OUTPUT: 204 No Content

VALIDATION:
  • Memory exists
  • User has access to workspace

FAILURE:
  • Not found → 404
  • No access → 403

PERSISTENCE: deleted_at set on Memory record

PROVENANCE: Audit event with memory_id, user_id, action="delete"
```

---

## FLOW-022: Supersession

**Trigger:** New fact supersedes existing fact (same subject+predicate)
**Source:** `app/services/pipeline.py:112-137`

```
INPUT: List[Fact] with same (subject, predicate), sorted by created_at

PROCESSING:
  1. Group by (subject, predicate)
  2. For each group:
     a. Latest fact → temporal_status = "current"
     b. Earlier facts → temporal_status = "historical"
     c. **NOTE: superseded_by_id is NOT updated** (gap P1-1)

OUTPUT: Updated Fact list

VALIDATION:
  • Same (subject, predicate) pairs
  • Chronological ordering

FAILURE: No supersession pairs → no changes

PERSISTENCE: Fact.temporal_status batch update

PROVENANCE: temporal_status change is tracked. No chain links via superseded_by_id.
```

---

## FLOW-023: Audit

**Trigger:** Any auditable action (login, create, update, delete, ingest, chat)
**Source:** `app/services/audit/service.py`

```
INPUT: AuditEvent data (action, resource_type, resource_id, user_id, metadata)

PROCESSING:
  1. _sanitize() — redact sensitive fields
  2. Create AuditEvent record
  3. Persist to PostgreSQL

OUTPUT: AuditEvent record

VALIDATION:
  • Required fields: action, resource_type, user_id
  • Metadata size limits

FAILURE:
  • DB error → logged, not blocking (audit failure doesn't fail the request)

PERSISTENCE: Append-only audit_events table

PROVENANCE: Each audit event is immutable. No UPDATE/DELETE allowed.
```

---

## FLOW-024: API Key Creation

**Trigger:** User creates API key
**Source:** `app/api/api_keys.py` — `POST /api/v1/api-keys`

```
INPUT:
  • name: str
  • expires_at: datetime (optional)

PROCESSING:
  1. Generate random token (64 chars)
  2. Hash token (bcrypt)
  3. Store hashed token in APIKey record
  4. Return raw token ONCE (never stored)

OUTPUT: APIKeyResponse with raw_token (shown once)

VALIDATION:
  • Name required
  • User has permission

FAILURE:
  • Permission denied → 403

PERSISTENCE: APIKey record with hashed token

PROVENANCE: API key has no source chain. No audit event recorded (gap P2-11).

GAP: API key expiry is stored but never enforced in auth middleware.
```

---

## FLOW-025: External Agent Integration

**Trigger:** External agent (Claude Code, Codex, MCP) sends event
**Source:** NOT IMPLEMENTED

```
STATUS: DOCUMENTED ONLY

No `/api/v1/agent/events` endpoint exists.
No Universal Adapter implementation found.
No MCP server integration found.
No Claude Code or Codex connector found.

DOCUMENTATION references exist but source code does not.
Classification: DOCUMENTED ONLY / MISSING
```

---

## Summary: Flow Coverage

| Flow | Status | Key Gap |
|------|--------|---------|
| FLOW-001 Registration | IMPLEMENTED | None |
| FLOW-002 Login | IMPLEMENTED | None |
| FLOW-003 Workspace Creation | IMPLEMENTED | None |
| FLOW-004 Project Creation | IMPLEMENTED | None |
| FLOW-005 Session Ingestion | IMPLEMENTED | Pipeline synchronous |
| FLOW-006 JSON Ingestion | IMPLEMENTED | Same as 005 |
| FLOW-007 JSONL Ingestion | IMPLEMENTED | Same as 005 |
| FLOW-008 M0 Normalization | IMPLEMENTED | 6 connectors working |
| FLOW-009 M1 Session Understanding | IMPLEMENTED BUT UNVERIFIED | Output not persisted |
| FLOW-010 M2 Fact/Decision Extraction | IMPLEMENTED | Confidence hardcoded |
| FLOW-011 M3 Temporal Processing | IMPLEMENTED INCOMPLETE | superseded_by_id never written |
| FLOW-012 M4 Graph Construction | IMPLEMENTED | temporal_status static |
| FLOW-013 M5 Retrieval | IMPLEMENTED | Memory excluded, no vector |
| FLOW-014 Memory Creation | IMPLEMENTED | No source_id FK |
| FLOW-015 Memory Retrieval | PARTIALLY IMPLEMENTED | project_id filter broken |
| FLOW-016 Search | IMPLEMENTED | No semantic search |
| FLOW-017 Chat | IMPLEMENTED | LLM-only fact extraction |
| FLOW-018 SSE Streaming | IMPLEMENTED | No timeout, no cancel |
| FLOW-019 Provenance | IMPLEMENTED | Memory provenance in JSON only |
| FLOW-020 Graph Exploration | IMPLEMENTED | Static temporal_status |
| FLOW-021 Memory Deletion | IMPLEMENTED | Soft delete only |
| FLOW-022 Supersession | IMPLEMENTED INCOMPLETE | superseded_by_id never written |
| FLOW-023 Audit | IMPLEMENTED | No memory lifecycle events |
| FLOW-024 API Key Creation | IMPLEMENTED | Expiry not enforced |
| FLOW-025 External Agent Integration | DOCUMENTED ONLY | No source code |

---

*End of Document: SWARMVAULT_END_TO_END_FLOWS.md*
