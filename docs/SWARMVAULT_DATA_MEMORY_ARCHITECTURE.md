# SwarmVault Data & Memory Architecture

**Forensic Reconciliation Phase — Agent 2: Data, Memory & Persistence**
**Baseline SHA:** e6f4b1c157afaed052584963b942ea04f9661610

---

## 1. Data Entry Points

All external data enters the system through two primary channels:

### 1.1 Upload / Ingestion Endpoint

- **File:** `app/api/ingest.py:38` — `POST /ingest/upload`
- **Schema:** `IngestUploadRequest` (`app/schemas.py:377`) — accepts `project_id`, `source_type` (text|json|jsonl|chatgpt), `content` (max 1 MB), `title`, `config`
- **Flow:** Authenticated user (minimum role: member) uploads raw conversation text. The endpoint computes a SHA-256 content hash, checks for duplicates against existing `Source` records with the same hash in the workspace, and if not a duplicate, calls `run_pipeline()` (`app/services/pipeline.py:32`).

### 1.2 Legacy Ingest Job Queue

- **File:** `app/api/ingest.py:118` — `POST /ingest/`
- **Schema:** `IngestQueued` (`app/schemas.py:265`) — creates a queued `IngestJob` record with no immediate processing. This is a backward-compatible endpoint.

### 1.3 Chat Endpoint

- **File:** `app/services/chat_orchestrator.py:25` — `process_chat()`
- **Schema:** `ChatRequest` (`app/schemas.py:167`) — user message, optional `session_id` and `project_id`
- **Flow:** User message is sent; M5 retrieval finds relevant facts/decisions; LLM is called with memory context; response and provenance are persisted.

### 1.4 Memory API (Direct Write)

- **File:** `app/api/memory.py:78` — `POST /memory/`
- **Schema:** `MemoryCreate` (`app/schemas.py:188`) — `content` (max 1 MB), `memory_type` (default: `procedural_memory`), `agent_id`, `run_id`, `project_id`, `extra_metadata`
- **Validators:** No null bytes (`schemas.py:197`), no whitespace-only content (`schemas.py:205`)
- **Flow:** Creates a `MemoryRecord`, calls `MemoryService.write()` which attaches provenance, persists to PostgreSQL, and emits audit events.

---

## 2. M0 — Conversation Normalization

**File:** `app/services/connectors.py`

### INPUT

- **Source:** Raw conversation data (`str` or `dict`) from ingestion upload.
- **Format detection:** Explicit `source_type` or automatic detection via `ConnectorRegistry.detect()`.

### TRANSFORMATION

Six connectors implement the `BaseConnector` interface (`connectors.py:53`), each with `detect()`, `validate()`, and `parse()` methods:

| Connector | Name | Detection | Input Format |
|-----------|------|-----------|--------------|
| `ChatGPTConnector` | `chatgpt` | `"mapping"` field, confidence 0.95 | JSON with `mapping` dict |
| `ClaudeConnector` | `claude` | `"chat_messages"` or `"conversations"` field, confidence 0.95 | JSON with `chat_messages` array or `conversations` list |
| `ClaudeCodeConnector` | `claude-code` | JSONL with event types (`user`, `assistant`, `system`, `summary`), confidence 0.9 | JSONL string |
| `GenericJSONConnector` | `json` | Array of `{role, content}` objects, confidence 0.9 | JSON array or `{messages: [...]}` |
| `JSONLConnector` | `jsonl` | Each line is valid JSON, confidence 0.9 | JSONL string |
| `MarkdownConnector` | `markdown` | `.md` extension or `#` heading prefix, confidence 0.8 | Markdown text |
| `TextConnector` | `text` | Fallback, confidence 0.1 | Plain text (paragraph alternation) |

### OUTPUT

`NormalizedConversation` (`connectors.py:33`): a dataclass containing `source_type`, `external_id`, `title`, `created_at`, `updated_at`, and a list of `NormalizedMessage` dataclasses.

`NormalizedMessage` (`connectors.py:23`): `external_id`, `role`, `content`, `timestamp`, `metadata` dict.

### VALIDATION

- Size guard: `_MAX_CONTENT_LENGTH = 10_000_000` (10 MB), `_MAX_MESSAGE_LENGTH = 100_000` (100 KB per message), `_MAX_MESSAGES = 10_000` (`connectors.py:74-76`).
- Each connector validates structural requirements (required fields) and raises `ConnectorError` on malformed input (`connectors.py:46`).
- Content is truncated via `_safe_text()` — never executed (`connectors.py:85`).

### GUARDRAIL

- Input size limits prevent resource exhaustion.
- Content is never evaluated as code (plain text truncation only).
- JSON parsing errors are caught and reported as `ConnectorError`.

### FAILURE MODE

`ConnectorError` is raised for any parsing or validation failure. The pipeline (`app/services/pipeline.py:215`) catches this, marks the `Source.status = "failed"` and `source.error_message = str(exc)`, then re-raises.

### PERSISTENCE EFFECT

- A `Source` record is created with `status="processing"` and `stage="M0"` (`pipeline.py:52-66`).
- After successful normalization, `NormalizedMessage` rows are persisted (one per message, `pipeline.py:82-95`), each with `source_id`, `session_id`, `message_index`, `external_id`, `role`, `content`, `extra_metadata`, `timestamp`.
- Source progress advances to 25%, stage "M1".

### PROVENANCE EFFECT

- The `Session` created at pipeline start (`pipeline.py:70-77`) stores `extra_metadata = {"source_id": source_id, "pipeline": "sprint3"}`, linking the session back to the source.

### MEMORY QUALITY EFFECT

- Determines the quality of all downstream extraction. Bad normalization (truncated content, wrong role assignment) cascades through M1-M4.
- Content hashing via `_content_hash()` (`connectors.py:108`) generates SHA-256-based external IDs for deduplication.

### EPISTEMIC CLASSIFICATION

**DERIVED** — Normalized messages are derived representations of raw source content. The raw content path is not stored in the database (`Source.raw_content_path` is nullable and unused in the pipeline), but the `Source.title` and `Source.content_hash` anchor the normalization to its origin.

---

## 3. M1 — Session Understanding

**File:** `app/services/m1_session.py`

### INPUT

- **Source:** List of `NormalizedMessage` objects (from M0 output, loaded in-memory within the pipeline).

### TRANSFORMATION

`understand_session()` (`m1_session.py:87`) performs deterministic analysis without an LLM by default:

- **Topic detection** (`m1_session.py:62`): Regex-based keyword matching against a 10-topic taxonomy (database, architecture, deployment, api, auth, testing, frontend, backend, performance, security). Topics are matched against the concatenated content of all messages.
- **Entity extraction** (`m1_session.py:30`): Regex patterns detect technology names (PostgreSQL, React, etc.), project names (multi-word capitalized sequences after "project"/"initiative"), and decision keywords ("we decided", "we chose", etc.).
- **Intent classification** (`m1_session.py:111`): Pattern-based detection of `how_to`, `decision_making`, `debugging`, `building`, `review` intents.
- **Summary generation**: Optional `summary_llm` callable. If provided, generates an LLM-based summary from the first 4000 characters of content (`m1_session.py:124-129`). Falls back to empty string on failure.

### OUTPUT

`SessionUnderstanding` dataclass (`m1_session.py:18`): `summary` (str), `topics` (list[str]), `intents` (list[str]), `entities_mentioned` (list[str]), `message_count` (int), `participants` (list[str]), `language` (str, default "en"), `confidence` (float).

### VALIDATION

- Empty message list returns `SessionUnderstanding(confidence=0.5)`.
- Confidence is set to 1.0 if entities were found, 0.5 otherwise (`m1_session.py:139`).

### GUARDRAIL

- No external API calls unless `summary_llm` is explicitly passed.
- LLM call is wrapped in try/except; failures are silent (empty summary).

### FAILURE MODE

- Returns a valid `SessionUnderstanding` with low confidence (0.5) rather than raising exceptions.
- `summary_llm` failure produces empty summary, does not stop pipeline.

### PERSISTENCE EFFECT

- M1 output is **not directly persisted** to the database. The `topics` and `entities_mentioned` are returned in the pipeline result dict (`pipeline.py:211-212`) and exposed via the `IngestUploadResponse` schema (`schemas.py:397-399`). They are available in the API response but not stored in a dedicated table.

### PROVENANCE EFFECT

- None. M1 results are ephemeral pipeline outputs, not persisted entities.

### MEMORY QUALITY EFFECT

- Topics and entities inform downstream retrieval ranking and can be used for project classification, but the lack of persistence means M1 data is lost after the ingestion response.

### EPISTEMIC CLASSIFICATION

**EPHEMERAL** — Session understanding exists only in the pipeline execution context and the API response. It is not stored in the database.

---

## 4. M2 — Fact and Decision Extraction

**File:** `app/services/m2_facts.py`

### INPUT

- **Source:** List of objects with `.content` attribute (NormalizedMessage objects from M0, or any message-like objects).

### TRANSFORMATION

`run_m2()` (`m2_facts.py:163`) concatenates all message content and applies regex-based extraction:

**Fact extraction** (`m2_facts.py:87`): Four regex patterns match subject-predicate-object triples:
- `X uses Y / X runs on Y / X built with Y` → predicate "uses"
- `X is Y / X are Y` → predicate "is"
- `X supports Y / X handles Y` → predicate "supports"

Each match produces a `Fact` dataclass with `subject`, `predicate`, `object`, `content` (formatted as "subject predicate object"), `confidence=0.8`.

**Decision extraction** (`m2_facts.py:115`): Four regex patterns match decision statements:
- "we decided/selected/will use..." → captures choice text
- "decision: ..." pattern
- "we are using/switched to..." pattern
- "we chose/selected..." pattern

Each match produces a `Decision` dataclass with `content`, `context` (first 500 chars of source text), `confidence=0.75`.

**Deduplication** (`m2_facts.py:139,151`): Facts are deduplicated by normalized subject|predicate|object key. Decisions are deduplicated by content.lower().strip().

### OUTPUT

Tuple of `(list[Fact], list[Decision])` — dataclass instances (not ORM models).

### VALIDATION

- Subject length > 2, object length > 1 for facts.
- Choice text length > 3 for decisions.
- Deduplication removes exact matches within the same extraction run.

### GUARDRAIL

- Pure regex extraction — no LLM dependency, no external calls.
- Deterministic output for the same input.

### FAILURE MODE

- Empty or no matches → empty lists returned, pipeline continues.
- No exception paths for extraction failure.

### PERSISTENCE EFFECT

- Facts and decisions are persisted in the pipeline (`pipeline.py:108-171`) as `Fact` and `Decision` ORM models.
- Each record stores: `workspace_id`, `project_id`, `source_id`, `session_id`, `subject`/`content`, `confidence=0.8`, `authority=1.0`, `temporal_status="current"`, `status="active"`.

### PROVENANCE EFFECT

- Each `Fact` and `Decision` links back to its `source_id` and `session_id`, creating a chain from the original ingested conversation through to the extracted knowledge.

### MEMORY QUALITY EFFECT

- Confidence of 0.8 for facts, 0.75 for decisions — these moderate values reflect regex-based extraction uncertainty.
- No confidence degradation over time unless superseded by M3.
- M3 temporal supersession runs inline in the pipeline (`pipeline.py:113-136`): if an existing current fact matches the same subject+predicate with a different object, the old fact is marked `temporal_status="historical"` and a new current fact is created.

### EPISTEMIC CLASSIFICATION

**DERIVED** — Facts and decisions are extracted interpretations of conversation content. They carry `confidence` and `authority` fields reflecting this derivation.

---

## 5. M3 — Temporal Supersession

**File:** `app/services/m3_temporal.py`

### INPUT

- **Source:** Database session, workspace_id, and new fact/decision data from M2 extraction (inline in pipeline) or explicit `supersede_fact()`/`supersede_decision()` calls.

### TRANSFORMATION

Two functions implement temporal truth management:

- `supersede_fact()` (`m3_temporal.py:14`): Queries for existing current facts with matching `(workspace_id, subject, predicate)`. If found with a different `object`, marks them as `temporal_status="historical"` and creates a new current fact.
- `supersede_decision()` (`m3_temporal.py:94`): Queries for all current decisions in a workspace. If any existing decision's content differs (case-insensitive), marks them as `temporal_status="historical"` and creates a new current decision.

**In the pipeline**, M3 is handled inline (`pipeline.py:113-136`): for each extracted fact, `_find_current_fact()` checks for existing matches. If the object differs, the existing fact is marked historical and a new one is created. If identical, it is skipped (deduplication). For decisions, the pipeline does NOT perform supersession — it always creates new Decision records without checking for existing conflicts.

### OUTPUT

- `supersede_fact()` returns `{"superseded": [old_fact_ids], "created": new_fact_id}`.
- `supersede_decision()` returns `{"superseded": [old_decision_ids], "created": new_decision_id}`.
- In the pipeline, the return values are not captured; the function is used for its side effects on the database.

### VALIDATION

- Only operates on `temporal_status="current"` records with `deleted_at IS NULL`.
- Same-object comparison uses case-insensitive equality to avoid unnecessary supersession.

### GUARDRAIL

- Never touches deleted records (`deleted_at IS NULL` filter).
- No cascading deletes — superseded records remain in the database with `temporal_status="historical"`.

### FAILURE MODE

- No matching current records → no supersession, new record created normally.
- No exception paths.

### PERSISTENCE EFFECT

- Updates existing records: `temporal_status = "historical"`, `updated_at = now`.
- Creates new records with `temporal_status = "current"`, `superseded_by_id` is NOT set on the old record (only `temporal_status` changes). The `superseded_by_id` field exists on the model (`models.py:440`) but is not populated by M3.

### PROVENANCE EFFECT

- The `source_id` on the new fact/decision links the supersession event to the originating source.

### MEMORY QUALITY EFFECT

- Implements temporal truth: only the most recent fact/decision is considered "current" in retrieval.
- Historical records remain queryable (for audit/timeline) but receive a 0.3 temporal bonus vs 1.0 in M5 scoring.

### EPISTEMIC CLASSIFICATION

**DERIVED** — Supersession is a derivation operation on existing derived facts/decisions. It manages the temporal validity of knowledge.

---

## 6. M4 — Graph Construction

**File:** `app/services/m4_graph.py`

### INPUT

- **Source:** Concatenated text of all messages from the conversation (retrieved from M0-normalized messages, `pipeline.py:183`).

### TRANSFORMATION

`extract_graph_elements()` (`m4_graph.py:49`) applies four regex relationship patterns to the full text:

| Pattern | Relationship Type |
|---------|------------------|
| `X uses/runs on/built with/powered by Y` | `uses` |
| `X connects to/integrates with/talks to Y` | `connects_to` |
| `X depends on/relies on Y` | `depends_on` |
| `X is a/is an/is the Y` | `is_a` |

For each match:
- Source and target labels are normalized (whitespace collapsed, truncated to 500 chars).
- Nodes are classified via `_classify_node()` (`m4_graph.py:85`): "technology" (matches known tech keywords), "project" (multi-word capitalized), or "entity" (default).
- Self-referential edges (source == target) and short labels (< 2 chars) are skipped.

### OUTPUT

Tuple of `(nodes_list, edges_list)` — lists of dicts with keys matching GraphNode/GraphEdge fields.

### VALIDATION

- Label length >= 2 characters.
- Source label != target label (case-insensitive).

### GUARDRAIL

- Pure regex extraction — no LLM dependency.
- Deduplication within extraction: each unique label becomes one node; duplicate edges are skipped.

### FAILURE MODE

- Empty or no matches → empty lists, pipeline continues.
- No exception paths for extraction.

### PERSISTENCE EFFECT

`persist_graph()` (`m4_graph.py:102`) writes to the database:
- **GraphNode records** (`models.py:520`): `workspace_id`, `project_id`, `external_id` (label), `label`, `node_type`, `properties={"source": "m4_extraction"}`, `temporal_status="current"`.
- **GraphEdge records** (`models.py:561`): `workspace_id`, `project_id`, `source_node_id`, `target_node_id`, `relationship_type`, `confidence=0.8`, `temporal_status="current"`, `source_id`.
- Node deduplication uses `external_id` (label) within the workspace (`m4_graph.py:130-155`).
- Edge deduplication checks for existing current edges with the same source, target, relationship type (`m4_graph.py:165-176`).

### PROVENANCE EFFECT

- Each `GraphEdge` stores `source_id`, linking the edge to the originating source document.
- Nodes are not directly linked to source_id (only via edges).

### MEMORY QUALITY EFFECT

- Graph connectivity contributes to M5 retrieval scoring (graph context factor, 10% weight for facts, 0% for decisions).
- Node classification enables filtered graph queries (`node_type` filter on GraphNode).

### EPISTEMIC CLASSIFICATION

**DERIVED** — Graph nodes and edges are extracted relationships from conversation content.

---

## 7. M5 — Multi-Factor Retrieval and Ranking

**File:** `app/services/m5_retrieval.py`

### INPUT

- **Source:** Database query parameters: `workspace_id`, `query` string, optional `project_id`, `limit`.
- **Data:** All current facts and decisions in the workspace (not deleted, not historical unless specifically filtered).

### TRANSFORMATION

`retrieve_hybrid()` (`m5_retrieval.py:211`) runs two retrievers in parallel and merges results:

**Fact ranking** (`rank_facts()`, `m5_retrieval.py:100`):
1. Fetches up to `limit * 3` fact candidates from the database.
2. For each fact, computes six scoring factors:
   - `keyword`: BM25-inspired term frequency (25% weight) — `_bm25_score()` (`m5_retrieval.py:37`)
   - `recency`: Exponential decay with 30-day half-life (15% weight) — `_recency_score()` (`m5_retrieval.py:69`)
   - `authority`: Fact's authority field (15% weight)
   - `confidence`: Fact's confidence field (15% weight)
   - `temporal`: 1.0 for current, 0.3 for historical (20% weight)
   - `graph`: Logarithmic scaling of graph edge connections (10% weight) — `_graph_context_score()` (`m5_retrieval.py:82`)

**Decision ranking** (`rank_decisions()`, `m5_retrieval.py:157`):
1. Same as facts but without the graph factor (decisions don't have direct graph connections).
2. Weights: keyword 25%, recency 15%, authority 15%, confidence 15%, temporal 30%.

**Merging**: Results are combined and sorted by final score descending, truncated to `limit`.

### OUTPUT

`list[RetrievalResult]` — each containing `item` (ORM model), `item_type` ("fact"/"decision"), `score` (float 0-1), and `factors` (dict of individual factor scores).

### VALIDATION

- Empty query → `_bm25_score()` returns 0.0, all results score purely on other factors.
- No deleted or soft-deleted records are considered.

### GUARDRAIL

- Fetches `limit * 3` candidates for re-ranking, ensuring a diverse pool.
- All scores are bounded between 0 and 1.

### FAILURE MODE

- No candidates → empty list returned.
- Graph context score queries the database for each candidate (N+1 queries for graph connections). This is a performance concern for large result sets.

### PERSISTENCE EFFECT

- M5 is a **query-time** operation. No data is written to the database during retrieval.
- Results are returned as in-memory objects and used by `chat_orchestrator.py` to build context for the LLM.

### PROVENANCE EFFECT

- `retrieve_for_chat()` (`m5_retrieval.py:245`) builds a provenance list for each result, recording `type`, `id`, `source_id`, `session_id`, `temporal_status`, `confidence`, and `score`.
- This provenance is returned to the chat orchestrator and stored in `MessageProvenance.retrieval_sources` (`models.py:636`).

### MEMORY QUALITY EFFECT

- M5 scoring directly determines which facts/decisions are surfaced to the LLM for chat responses.
- Temporal bonus (0.3x for historical) ensures outdated knowledge is deprioritized but not completely excluded.
- Recency decay ensures older knowledge gradually loses relevance.

### EPISTEMIC CLASSIFICATION

**AUTHORITATIVE** — M5 retrieves from the authoritative store (PostgreSQL) and applies transparent, deterministic scoring. The scoring factors are all derived from persisted metadata.

---

## 8. Hybrid Vector + Keyword Retrieval (Memory Model)

**File:** `app/services/retrieval.py`

### INPUT

- **Source:** `Memory` ORM records from the database, filtered by `workspace_id`, optional `user_id`, optional `memory_type`.
- **Query:** User's search string, optional pre-computed `query_embedding` (list of floats).

### TRANSFORMATION

`retrieve_memories()` (`retrieval.py:61`):
1. Fetches `limit * 3` candidate `Memory` records from PostgreSQL.
2. For each candidate, computes `_hybrid_score()` (`retrieval.py:45`):
   - `vector_weight * cosine_similarity(embedding, query_embedding) + keyword_weight * _keyword_score(content, query)`
   - Default weights: vector 0.6, keyword 0.4.
   - If no `query_embedding` is provided, falls back to keyword-only scoring.
3. `_cosine_similarity()` (`retrieval.py:22`) uses numpy for vector comparison.
4. `_keyword_score()` (`retrieval.py:35`) uses simple word-set overlap ratio.

### OUTPUT

`list[tuple[Memory, float]]` — Memory model instances paired with relevance scores, sorted descending.

### VALIDATION

- Empty embedding vectors → cosine similarity returns 0.0.
- No query words → keyword score returns 0.0.
- Graceful fallback: if embeddings are absent, keyword-only scoring is used.

### GUARDRAIL

- No pgvector dependency — embeddings are stored as JSON lists of floats in `Memory.embedding` (`models.py:253`) and compared in Python via numpy.
- `limit * 3` candidate pool ensures diversity before re-ranking.

### FAILURE MODE

- No candidates → empty list.
- numpy import failure would break this module (but numpy is a hard dependency).

### PERSISTENCE EFFECT

- Read-only operation. No database writes.
- Embeddings must be pre-computed and stored in `Memory.embedding` for vector search to work.

### PROVENANCE EFFECT

- None. This retrieval method does not build provenance chains (unlike M5's `retrieve_for_chat()`).

### MEMORY QUALITY EFFECT

- Hybrid scoring combines semantic similarity (embeddings) with keyword matching, providing better recall than either method alone.
- Vector search enables fuzzy matching; keyword search ensures precision on exact terms.

### EPISTEMIC CLASSIFICATION

**AUTHORITATIVE** — Reads directly from the PostgreSQL source of truth.

---

## 9. Pipeline Orchestrator (M0→M5)

**File:** `app/services/pipeline.py`

### INPUT

- **Source:** `run_pipeline()` accepts `workspace_id`, `tenant_id`, `project_id`, `user_id`, `source_type`, `raw_content` (str or dict), `title`, `config`.

### TRANSFORMATION

Sequential execution of M0→M1→M2→M3→M4:

1. **M0** (`pipeline.py:48`): Calls `connectors.normalize()` to produce a `NormalizedConversation`.
2. **Source creation** (`pipeline.py:52-66`): Creates `Source` record with `status="processing"`, `stage="M0"`.
3. **Session creation** (`pipeline.py:70-77`): Creates a `Session` linked to the source.
4. **Message persistence** (`pipeline.py:82-95`): Persists each `NormalizedMessage` with `source_id` and `session_id`.
5. **M1** (`pipeline.py:102`): Calls `understand_session()` — results stored in pipeline return dict only.
6. **M2** (`pipeline.py:108`): Calls `extract_facts_and_decisions()` — persists Fact and Decision records.
7. **M3** (`pipeline.py:113-136`): Inline supersession for facts (checks existing, marks historical if object changed). Decisions are NOT superseded inline.
8. **M4** (`pipeline.py:182-192`): Calls `extract_graph_elements()` then `persist_graph()`.
9. **Completion** (`pipeline.py:194-199`): Updates `Source` to `status="completed"`, `stage="M5"`, `progress=100`.

### OUTPUT

Dict with: `source_id`, `session_id`, `status`, `stage`, `messages_processed`, `facts_created`, `decisions_created`, `graph_nodes_created`, `graph_edges_created`, `topics`, `entities`.

### VALIDATION

- M0 normalization failure → caught by try/except, Source marked failed.
- Project existence is verified before pipeline start (`ingest.py:50-58`).

### GUARDRAIL

- Content hash deduplication in the API layer prevents re-processing identical content (`ingest.py:61-77`).
- Source progress tracking provides visibility into pipeline stage.
- Exception handling at the top level ensures Sources are always marked with a terminal status.

### FAILURE MODE

- Any exception → `Source.status = "failed"`, `Source.error_message = str(exc)`, exception re-raised.
- Partial completion: messages and facts/decisions created before the failure remain in the database (no rollback).

### PERSISTENCE EFFECT

Creates/updates these records in order:
1. `Source` (created first, updated throughout)
2. `Session` (created at M0 completion)
3. `NormalizedMessage` (one per message)
4. `Fact` (from M2 extraction + M3 supersession)
5. `Decision` (from M2 extraction)
6. `GraphNode` (from M4 extraction)
7. `GraphEdge` (from M4 extraction)

### PROVENANCE EFFECT

- Each created record links back to `source_id` and `session_id`.
- The `Session.extra_metadata` stores `{"source_id": source_id, "pipeline": "sprint3"}`.

### MEMORY QUALITY EFFECT

- The pipeline is the primary data creation path for the knowledge graph.
- Pipeline failures leave partial state — there is no transaction rollback across the full pipeline.

### EPISTEMIC CLASSIFICATION

**DERIVED** — All output entities are derived from the input raw content through the M0-M4 transformations.

---

## 10. Memory Model

### 10.1 MemoryRecord (Canonical)

**File:** `app/services/memory.py:62` — `MemoryRecord` dataclass

Fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `memory_id` | str | uuid4 | Unique identifier |
| `memory_type` | str | "WORKING" | Canonical type (WORKING\|EPISODIC\|SEMANTIC\|PROCEDURAL\|USER\|TEAM\|PROJECT\|AGENT) |
| `scope` | str | "USER" | Canonical scope (USER\|TEAM\|PROJECT\|WORKSPACE\|TENANT) |
| `tenant_id` | str\|None | None | Tenant hierarchy |
| `workspace_id` | str\|None | None | Workspace hierarchy |
| `project_id` | str\|None | None | Project hierarchy |
| `team_id` | str\|None | None | Team hierarchy |
| `user_id` | str\|None | None | User ownership |
| `agent_id` | str\|None | None | Agent identity |
| `run_id` | str\|None | None | Run/execution identity |
| `subject` | str | "" | Subject line |
| `predicate` | str | "" | Predicate |
| `value` | Any | None | Value |
| `content` | str\|None | None | Free-form content |
| `authority` | dict | {} | Authority metadata |
| `confidence` | float | 0.7 | Confidence score |
| `importance` | float | 0.5 | Importance score |
| `created_at` | str | now | ISO 8601 timestamp |
| `updated_at` | str | now | ISO 8601 timestamp |
| `valid_from` | str\|None | None | Validity start |
| `valid_until` | str\|None | None | Validity end |
| `expires_at` | str\|None | None | Expiration timestamp |
| `version` | int | 1 | Version number |
| `supersedes` | str\|None | None | ID of superseded record |
| `superseded_by` | str\|None | None | ID of superseding record |
| `provenance` | list[dict] | [] | Provenance chain entries |
| `permissions` | dict | {} | Permission grants |
| `status` | str | "active" | active\|superseded\|expired\|deleted |
| `user_metadata` | dict | {} | User-provided metadata |

### 10.2 MemoryTypeMapper

**File:** `app/services/memory.py:127` — `MemoryTypeMapper` class

Bidirectional mapping between canonical memory types and SwarmVault storage types:

| Canonical | Vault (DB) |
|-----------|------------|
| WORKING | working |
| EPISODIC | episodic |
| SEMANTIC | semantic |
| PROCEDURAL | procedural_memory |
| USER | user |
| TEAM | team |
| PROJECT | project |
| AGENT | agent |

Scope mapping: USER→user, TEAM→team, PROJECT→project, WORKSPACE→workspace, TENANT→tenant.

### 10.3 Memory ORM Model

**File:** `app/models.py:232` — `Memory` class

PostgreSQL table `memories` with columns:
- `id` (String(36), UUID primary key)
- `tenant_id` (String(36), ForeignKey tenants.id, indexed)
- `workspace_id` (String(36), ForeignKey workspaces.id, indexed)
- `user_id` (String(36), ForeignKey users.id)
- `agent_id` (String(36), nullable)
- `run_id` (String(36), nullable)
- `project_id` (String(36), ForeignKey projects.id, nullable, indexed)
- `memory_type` (String(50), default "procedural_memory")
- `content` (Text)
- `extra_metadata` (JSON, nullable) — stores provenance, permissions, versioning, user_metadata
- `embedding` (JSON, nullable) — list of floats for vector search
- `temporal_status` (String(50), default "current", indexed)
- `confidence` (Float, default 0.7)
- `authority` (Float, default 1.0)
- `deleted_at` (DateTime, nullable, indexed)
- `created_at`, `updated_at` (DateTime with auto-update)

### 10.4 Persistence Mapping

When `MemoryRecord` is persisted to PostgreSQL (`memory.py:211-248`):
- `memory_type` is mapped via `MemoryTypeMapper.to_vault_type()`.
- `content` = `record.content` or `record.subject` (fallback).
- `extra_metadata` = merged dict containing provenance, permissions, versioning info, and `user_metadata`.
- `tenant_id` is set from `record.tenant_id` or falls back to `record.workspace_id` (`memory.py:215`).

### 10.5 Soft Deletion

- `Memory.deleted_at` is set to the current datetime on soft delete (`memory.py:789`).
- `temporal_status` is set to "deleted".
- All read queries filter `deleted_at IS NULL` (`memory.py:257` in `_load_from_db`, `memory.py:281` in `_db_search`).

### EPISTEMIC CLASSIFICATION

**AUTHORITATIVE** — The Memory model is the authoritative store for agent-created memories. It is the source of truth for memory CRUD operations, governed by the Policy Engine and Audit Service.

---

## 11. Provenance Chain

### 11.1 MessageProvenance

**File:** `app/models.py:607` — `MessageProvenance` class

PostgreSQL table `message_provenance` — one record per chat response.

Columns:

| Column | Type | Description |
|--------|------|-------------|
| `id` | String(36) | UUID primary key |
| `workspace_id` | String(36) | Workspace scope |
| `project_id` | String(36), nullable | Project scope |
| `session_id` | String(36), nullable | Session reference |
| `user_message_id` | String(36), nullable | The user's message |
| `assistant_message_id` | String(36), nullable | The assistant's response |
| `model` | String(100) | LLM model used |
| `provider` | String(50) | LLM provider |
| `retrieval_method` | String(50), default "hybrid" | How memory was retrieved |
| `memory_ids_used` | JSON, nullable | List of Memory/Fact/Decision IDs used |
| `retrieval_sources` | JSON, nullable | Detailed source info with scores |
| `user_message_preview` | String(500), nullable | First 500 chars of user message |
| `prompt_tokens` | Integer, default 0 | Token count |
| `completion_tokens` | Integer, default 0 | Token count |
| `total_tokens` | Integer, default 0 | Token count |
| `latency_ms` | Integer, nullable | Response latency |
| `confidence` | Float, nullable | Confidence score |
| `created_at` | DateTime | Timestamp |

### 11.2 Provenance in MemoryRecord

Each `MemoryRecord.provenance` entry (`memory.py:110`) is a dict containing:
- `source`: provenance source identifier (e.g., "memory_service", "supersede", "api")
- `source_id`: ID of the originating entity
- `creator`: principal_id that created the record
- `created_at`: ISO 8601 timestamp
- `method`: creation method (e.g., "direct_write", "supersede", "api_create")
- `authority`: authority metadata at creation time
- `confidence`: confidence at creation time
- `version`: version at creation time
- `supersedes`: ID of superseded record (if applicable)

### 11.3 Provenance in Chat Flow

**File:** `app/services/chat_orchestrator.py:122-139`

After every chat response:
1. M5 retrieval results are converted to `retrieval_sources` list (memory_id, content preview, item_type, score).
2. `MessageProvenance` is created with `memory_ids_used`, `retrieval_sources`, `user_message_preview`, token counts, latency, confidence.
3. The provenance record is persisted to PostgreSQL.

### 11.4 Provenance in Memory CRUD

- **Write** (`memory.py:406-417`): Every write appends a provenance entry with source, creator, timestamp, method, authority, confidence, version, supersedes.
- **Update** (`memory.py:656-662`): Appends a provenance entry with method "update" and version info.
- **Supersede** (`memory.py:721`): Calls `write()` with provenance source "supersede" and source_id of the old record.
- **Read** (`memory.py:834-842`): Returns the full provenance list without modification.
- **Explain** (`memory.py:862-891`): Returns record details, provenance chain, version history, and permissions.

### EPISTEMIC CLASSIFICATION

**AUTHORITATIVE** — Provenance records are append-only audit trails. They are never modified or deleted after creation.

---

## 12. Audit Persistence

### 12.1 AuditService (Emit → Buffer → Persist)

**File:** `app/services/audit/service.py`

Three-phase architecture:

1. **Emit** (`service.py:158`): Synchronous. Creates an `AuditEvent`, sanitizes sensitive fields, dispatches to all registered sinks, and appends to the in-memory buffer.
2. **Buffer**: Events accumulate in `self._buffer` (list of `AuditEvent` objects) between persist calls.
3. **Persist** (`service.py:180`): Async. Called at the end of each request. Flushes all buffered events to PostgreSQL via `AuditRepository`. Clears the buffer regardless of success/failure.

### 12.2 AuditEvent DTO

**File:** `app/services/audit/service.py:64` — `AuditEvent` class

Uses `__slots__` for memory efficiency. Canonical fields (defined in `constants.py:64`):

`event_id`, `timestamp`, `event_type`, `tenant_id`, `workspace_id`, `project_id`, `principal_id`, `principal_type`, `resource_type`, `resource_id`, `action`, `decision`, `policy_id`, `policy_version`, `request_id`, `correlation_id`, `result_status`, `duration_ms`, `limits`, `provenance_reference`, `metadata`.

### 12.3 AuditEvent ORM Model

**File:** `app/models.py:788` — `AuditEvent` class

PostgreSQL table `audit_events` with indexed columns for `tenant_id`, `workspace_id`, `project_id`, `principal_id`, `resource_type`, `resource_id`, `action`, `decision`, `event_type`, `result_status`, `timestamp`, `correlation_id`.

Key constraints:
- Append-only from the application perspective (no update/delete operations in the repository).
- Sensitive fields must never be stored — enforced by `_sanitize()` (`service.py:43`).
- `event_metadata` field (not `metadata`, because SQLAlchemy reserves that name) stores arbitrary metadata.

### 12.4 AuditRepository

**File:** `app/services/audit/repository.py`

- `save()` (`repository.py:42`): Inserts a new `AuditEvent` record. Never updates or deletes.
- `query()` (`repository.py:78`): Filters by tenant, workspace, principal, resource, event type, decision, result status, time range. Returns ordered list.
- `count()` (`repository.py:130`): Counts events matching filters.
- `get_by_request_id()` (`repository.py:150`): Correlation lookup.
- `get_by_correlation_id()` (`repository.py:158`): Full correlation chain retrieval.

### 12.5 Sensitive Field Redaction

**File:** `app/services/audit/constants.py:90` — `SENSITIVE_FIELDS`

Frozenset of field names that are automatically redacted to `"[redacted]"`: password, hashed_password, secret, api_key, raw_key, token, refresh_token, database_url, connection_string, private_key, encryption_key.

Redaction is recursive — sensitive keys in nested dicts/lists are also redacted (`service.py:43-61`).

### 12.6 Event Taxonomy

**File:** `app/services/audit/constants.py`

| Category | Event Types |
|----------|-------------|
| Policy | `policy.request`, `policy.allow`, `policy.deny`, `policy.confirmation_required`, `policy.limited` |
| Memory | `memory.read`, `memory.search`, `memory.write`, `memory.update`, `memory.delete`, `memory.expire`, `memory.share` |
| Tool | `tool.request`, `tool.started`, `tool.completed`, `tool.failed`, `tool.denied` |
| Model | `model.request`, `model.completed`, `model.failed` |
| Auth | `auth.login`, `auth.logout`, `auth.login_failed`, `auth.token_refresh` |
| Resource | `api_key.created`, `api_key.revoked`, `api_key.rotated`, `project.created`, `project.deleted`, `workspace.created`, `workspace.member_added`, `workspace.member_removed` |
| Data Lifecycle | `ingest.started`, `ingest.completed`, `ingest.failed`, `source.deleted` |

### 12.7 Audit Flow in MemoryService

**File:** `app/services/memory.py:980-1013` — `_emit_audit()`

Every MemoryService operation (read, write, search, update, delete, expire, share, revoke) emits audit events via this method:
1. Records operation start time.
2. After authorization and operation completion, calls `_emit_audit()` with event type, principal, resource, result status, and duration.
3. Maps result status to canonical constants (success→RESULT_SUCCESS, denied→RESULT_DENIED, not_found→RESULT_FAILURE).
4. Calls `self._audit.emit()` which buffers the event for later DB persistence.

### 12.8 Audit Flow in Chat Orchestrator

**File:** `app/services/chat_orchestrator.py` — No explicit audit emission.

Chat responses only create `MessageProvenance` records. Audit events for chat operations would need to be added at the API router level.

### EPISTEMIC CLASSIFICATION

**AUTHORITATIVE** — Audit events are immutable append-only records. They serve as the system's authoritative accountability log.

---

## 13. Soft Deletion Pattern

### 13.1 Implementation

Soft deletion is implemented via `deleted_at` datetime columns across the following models:

| Model | Table | deleted_at column | Index |
|-------|-------|-------------------|-------|
| `Workspace` | workspaces | Yes | No |
| `User` | users | Yes | No |
| `Session` | sessions | Yes | No |
| `Project` | projects | Yes | No |
| `Source` | sources | Yes | No |
| `NormalizedMessage` | normalized_messages | No | — |
| `Fact` | facts | Yes | No |
| `Decision` | decisions | Yes | No |
| `GraphNode` | graph_nodes | Yes | No |
| `GraphEdge` | graph_edges | Yes | No |
| `Memory` | memories | Yes | Yes (indexed) |
| `MessageFeedback` | message_feedback | Yes | No |
| `ApiKey` | api_keys | `revoked_at` | Yes |

### 13.2 Query Pattern

All list/detail endpoints filter with `Model.deleted_at.is_(None)`:
- `app/api/ingest.py:164` — Source listing
- `app/api/ingest.py:269` — Fact listing
- `app/api/ingest.py:334` — Decision listing
- `app/api/ingest.py:397` — Graph node listing
- `app/api/ingest.py:408` — Graph edge listing
- `app/api/memory.py:156` — Memory listing
- `app/services/memory.py:257` — Memory read
- `app/services/memory.py:281` — Memory search

### 13.3 MemoryService Delete

**File:** `app/services/memory.py:728-797`

The `delete()` method performs soft deletion:
1. Loads the record (from DB or cache).
2. Cross-tenant isolation check (before policy check — defense in depth).
3. Policy authorization check.
4. Sets `record.status = "deleted"` and `record.updated_at = now`.
5. If session provided, sets `model.deleted_at = now`, `model.updated_at = now`, `model.temporal_status = "deleted"`.
6. Emits audit event.

### 13.4 Graph/Timeline with include_deleted

- `GET /ingest/graph` accepts `include_historical` query param (`ingest.py:386`) — defaults to False, showing only `temporal_status="current"` nodes/edges.
- `GET /memory/` accepts `include_deleted` query param (`memory.py:139`) — defaults to False.

### EPISTEMIC CLASSIFICATION

**DERIVED** — Soft deletion is a lifecycle operation on derived data. The deletion flag is a governance layer on top of the underlying data.

---

## 14. Serialization

### 14.1 ORM → Pydantic

All API responses use Pydantic models with `Config: from_attributes = True` for ORM-to-schema conversion:

- `SourceOut`, `SourceDetail` (`schemas.py:336-374`)
- `NormalizedMessageOut` (`schemas.py:361`)
- `FactOut` (`schemas.py:403`)
- `DecisionOut` (`schemas.py:430`)
- `GraphNodeOut`, `GraphEdgeOut` (`schemas.py:455-484`)
- `MemoryOut` (`schemas.py:225`)
- `ProvenanceOut` (`schemas.py:308`)
- `IngestJobOut` (`schemas.py:271`)
- `UserOut`, `WorkspaceOut`, `ProjectOut`, `SessionOut`, `MessageOut` (`schemas.py:35-161`)
- `FeedbackOut` (`schemas.py:538`)

### 14.2 JSON Fields

Models use SQLAlchemy `JSON` type for flexible metadata storage:
- `Session.extra_metadata` (aliased as `metadata` column, `models.py:176`)
- `Message.extra_metadata` (aliased, `models.py:202`)
- `Source.config` (`models.py:332`)
- `Fact.extra_metadata` (aliased, `models.py:444`)
- `Decision.extra_metadata` (aliased, `models.py:497`)
- `GraphNode.properties` (`models.py:537`)
- `GraphEdge.properties` (`models.py:580`)
- `Memory.extra_metadata` (`models.py:252`) — stores provenance, permissions, versioning
- `Memory.embedding` (`models.py:253`) — JSON list of floats
- `MessageProvenance.memory_ids_used` (`models.py:633`)
- `MessageProvenance.retrieval_sources` (`models.py:636`)
- `IngestJob.config` (`models.py:287`)
- `AuditEvent.limits` (`models.py:821`)
- `AuditEvent.event_metadata` (`models.py:823`)
- `ApiKey.key_extra` (`models.py:710`)
- `PolicyVersion.rules` (`models.py:773`)

### 14.3 Dataclass Serialization

Service-layer dataclasses (not exposed via API directly):
- `NormalizedConversation`, `NormalizedMessage` (`connectors.py:22-41`)
- `SessionUnderstanding` (`m1_session.py:18`)
- `Fact`, `Decision` (M2 dataclasses, `m2_facts.py:16-34`)
- `MemoryRecord` (`memory.py:62`)
- `RetrievalResult` (`m5_retrieval.py:29`)
- `AuditEvent` (DTO, `audit/service.py:64`)

### 14.4 API Key Hashing

**File:** `app/models.py:697` — `ApiKey.key_hash`

API keys are stored as SHA-256 hashes (`String(64)`). The raw key is never persisted. `key_prefix` (first 8 chars) is stored for display purposes.

### EPISTEMIC CLASSIFICATION

**AUTHORITATIVE** — Serialization formats are the authoritative wire format for all data exchange.

---

## 15. Retrieval Representation

### 15.1 M5 Retrieval (Facts + Decisions)

**File:** `app/services/m5_retrieval.py`

- **Search space:** All non-deleted facts and decisions in the workspace.
- **Scoring:** Six-factor weighted scoring (BM25 keyword, recency, authority, confidence, temporal status, graph connectivity).
- **Result format:** `RetrievalResult` dataclass with `item`, `item_type`, `score`, `factors`.
- **Chat context format** (`retrieve_for_chat()`, `m5_retrieval.py:245`): Returns `context` (formatted string with `[FACT]`/`[DECISION]` prefixes), `results`, `provenance` list, `query`.

### 15.2 Hybrid Memory Retrieval

**File:** `app/services/retrieval.py`

- **Search space:** `Memory` records in the workspace, optionally filtered by `user_id` and `memory_type`.
- **Scoring:** `vector_weight * cosine_similarity + keyword_weight * word_overlap`. Default: 0.6 vector, 0.4 keyword.
- **Result format:** `list[tuple[Memory, float]]` — ORM model + score.

### 15.3 Combined Search Endpoint

**File:** `app/api/ingest.py:497` — `POST /ingest/search`

Uses `retrieve_hybrid()` (M5) which combines facts and decisions. Memory records are not included in this endpoint — M5 only retrieves from the Fact and Decision tables.

### 15.4 Memory Search Endpoint

**File:** `app/api/memory.py:264` — `POST /memory/search`

Uses `MemoryService.search()` which does ILIKE-based keyword search on `Memory.content`. Does NOT use M5 multi-factor scoring or vector search.

### 15.5 Chat Retrieval

**File:** `app/services/chat_orchestrator.py:59`

Uses `retrieve_for_chat()` (M5) to get facts and decisions. Memory records (from the Memory API) are NOT currently included in chat context. The `memory_ids_used` in `MessageProvenance` references fact/decision IDs, not Memory IDs.

### EPISTEMIC CLASSIFICATION

**AUTHORITATIVE** — Retrieval reads from the authoritative PostgreSQL store with transparent, deterministic scoring algorithms.

---

## 16. Complete Data Model Summary

### 16.1 Entity Relationship (Core)

```
Tenant (1) ──→ (N) Workspace (1) ──→ (N) Project
                    │                    │
                    │                    │
              (N) Session ──→ (N) Message
                    │
                    │
              (N) Source ──→ (N) NormalizedMessage
                    │
              ├──→ (N) Fact
              ├──→ (N) Decision
              └──→ (N) GraphEdge
                        │
                        │
              GraphNode (1) ──→ (N) GraphEdge ──→ (N) GraphNode

Memory (standalone, linked via workspace_id + project_id + user_id)
MessageProvenance (linked via session_id, user_message_id, assistant_message_id)
AuditEvent (linked via tenant_id, workspace_id, project_id, request_id, correlation_id)
```

### 16.2 Database Tables

| Table | Model | Primary Key | Key Indexes |
|-------|-------|-------------|-------------|
| `tenants` | Tenant | id (uuid) | slug (unique) |
| `workspaces` | Workspace | id (uuid) | tenant_id |
| `workspace_members` | WorkspaceMember | id (uuid) | workspace_id, user_id |
| `invitations` | Invitation | id (uuid) | — |
| `refresh_tokens` | RefreshToken | id (uuid) | token (unique, indexed) |
| `users` | User | id (uuid) | email (unique, indexed) |
| `sessions` | Session | id (uuid) | workspace_id, user_id, deleted_at |
| `messages` | Message | id (uuid) | session_id |
| `projects` | Project | id (uuid) | workspace_id, deleted_at |
| `memories` | Memory | id (uuid) | tenant_id, workspace_id, project_id, temporal_status, deleted_at |
| `sources` | Source | id (uuid) | external_id, content_hash, workspace_id+tenant_id, project_id+status, deleted_at |
| `normalized_messages` | NormalizedMessage | id (uuid) | source_id+message_index (unique), source_id+external_id (unique) |
| `facts` | Fact | id (uuid) | workspace_id+project_id, subject, temporal_status, superseded_by_id, deleted_at |
| `decisions` | Decision | id (uuid) | workspace_id+project_id, temporal_status, superseded_by_id, deleted_at |
| `graph_nodes` | GraphNode | id (uuid) | workspace_id+temporal_status, workspace_id+external_id (unique), workspace_id+node_type, deleted_at |
| `graph_edges` | GraphEdge | id (uuid) | source_node_id+target_node_id, workspace_id+temporal_status, source_id, deleted_at |
| `message_provenance` | MessageProvenance | id (uuid) | — |
| `message_feedback` | MessageFeedback | id (uuid) | — |
| `ingest_jobs` | IngestJob | id (uuid) | — |
| `api_keys` | ApiKey | id (uuid) | key_hash (unique, indexed), expires_at, workspace_id, user_id |
| `policies` | Policy | id (uuid) | tenant_id, status |
| `policy_versions` | PolicyVersion | id (uuid) | policy_id, policy_id+version (unique) |
| `audit_events` | AuditEvent | id (uuid) | tenant_id+timestamp, principal_id+timestamp, resource_type+timestamp, correlation_id+timestamp, event_type, result_status, decision, timestamp |

### 16.3 Unique Constraints

| Table | Constraint | Columns |
|-------|-----------|---------|
| `normalized_messages` | `uq_normalized_msg_source_idx` | source_id + message_index |
| `normalized_messages` | `uq_normalized_msg_source_ext` | source_id + external_id |
| `graph_nodes` | `uq_graph_node_ws_ext` | workspace_id + external_id |
| `policy_versions` | `uq_policy_version` | policy_id + version |

### 16.4 Composite Indexes

| Table | Index | Columns |
|-------|-------|---------|
| `sources` | `ix_sources_workspace_tenant` | workspace_id + tenant_id |
| `sources` | `ix_sources_project_status` | project_id + status |
| `facts` | `ix_facts_workspace_project` | workspace_id + project_id |
| `facts` | `ix_facts_subject` | subject |
| `facts` | `ix_facts_temporal_status` | temporal_status |
| `decisions` | `ix_decisions_workspace_project` | workspace_id + project_id |
| `decisions` | `ix_decisions_temporal_status` | temporal_status |
| `graph_nodes` | `ix_graph_nodes_workspace` | workspace_id + temporal_status |
| `graph_nodes` | `ix_graph_nodes_workspace_type` | workspace_id + node_type |
| `graph_edges` | `ix_graph_edges_source_target` | source_node_id + target_node_id |
| `graph_edges` | `ix_graph_edges_workspace` | workspace_id + temporal_status |
| `audit_events` | `ix_audit_events_tenant_timestamp` | tenant_id + timestamp |
| `audit_events` | `ix_audit_events_principal_timestamp` | principal_id + timestamp |
| `audit_events` | `ix_audit_events_resource_timestamp` | resource_type + timestamp |
| `audit_events` | `ix_audit_events_correlation` | correlation_id + timestamp |
| `api_keys` | `ix_api_keys_workspace` | workspace_id |
| `api_keys` | `ix_api_keys_user` | user_id |
| `policies` | `ix_policies_tenant_id` | tenant_id |
| `policies` | `ix_policies_status` | status |

---

## 17. Epistemic Classification Summary

| Entity | Classification | Justification |
|--------|---------------|---------------|
| `Tenant`, `Workspace`, `Project`, `User`, `Session` | **AUTHORITATIVE** | User-created, governance-layer entities |
| `Message` | **AUTHORITATIVE** | User-created chat messages |
| `Source` | **DERIVED** | Represents an ingested document; content is derived from external input |
| `NormalizedMessage` | **DERIVED** | Derived from Source content via M0 normalization |
| `Fact` | **DERIVED** | Extracted via M2 regex patterns from conversation content |
| `Decision` | **DERIVED** | Extracted via M2 regex patterns from conversation content |
| `GraphNode` | **DERIVED** | Extracted via M4 regex patterns |
| `GraphEdge` | **DERIVED** | Extracted via M4 regex patterns |
| `Memory` | **AUTHORITATIVE** | Agent-created memories via MemoryService; governed by Policy Engine |
| `MessageProvenance` | **AUTHORITATIVE** | Append-only audit trail for chat responses |
| `AuditEvent` | **AUTHORITATIVE** | Immutable append-only accountability log |
| `SessionUnderstanding` | **EPHEMERAL** | M1 output not persisted to database |
| `IngestJob` | **AUTHORITATIVE** | Queued job record for ingestion tracking |

---

## 18. Key Architectural Observations

### 18.1 Dual Retrieval Systems

The system has two separate retrieval mechanisms that do not share results:
- **M5** (`m5_retrieval.py`): Multi-factor scoring on Facts and Decisions only. Used by chat.
- **Hybrid retrieval** (`retrieval.py`): Vector + keyword on Memory records only. Used by memory search API.

The chat orchestrator does NOT include Memory records in its context — only Facts and Decisions from M5.

### 18.2 Memory Model vs. Fact/Decision Model

The `Memory` table (`models.py:232`) is a separate knowledge store from `Fact`/`Decision` (`models.py:413,467`). They share `workspace_id` and `project_id` scoping but have different schemas, lifecycles, and retrieval paths. The pipeline (M0-M5) creates Fact/Decision/Graph records; Memory records are created via the Memory API or `MemoryService.write()`.

### 18.3 Pipeline State is Not Transactional

The pipeline (`pipeline.py`) does not use database transactions across M0-M5. If a failure occurs mid-pipeline, partial state (messages, facts, decisions) remains in the database. The Source record tracks progress but cannot roll back created records.

### 18.4 Temporal Supersession Gap

- Facts: Supersession is handled both inline in the pipeline (`pipeline.py:113-136`) and via the standalone `m3_temporal.supersede_fact()` function.
- Decisions: Supersession is NOT handled inline in the pipeline. The `m3_temporal.supersede_decision()` function exists but is never called from the pipeline. Decisions accumulate without temporal management during ingestion.

### 18.5 Cross-Tenant Isolation

Isolation is enforced at multiple layers:
- **Database queries**: All list endpoints filter by `workspace_id` from the tenant context.
- **Service layer**: `MemoryService` checks `tenant_id` on loaded records before allowing operations (`memory.py:483`, `memory.py:625`, `memory.py:755`).
- **Policy Engine**: RBAC policies evaluate tenant/workspace/project scope.

The `Memory` model uniquely stores both `tenant_id` and `workspace_id` directly (`models.py:238-243`), while Fact/Decision/Graph models store only `workspace_id` (tenant isolation relies on workspace membership).

---

*Document produced by Agent 2: Data, Memory & Persistence Architecture. Documentation-only — no code changes.*
