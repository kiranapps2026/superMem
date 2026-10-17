# SwarmVault Memory Intelligence Readiness Architecture
**Agent 7 — Forensic Reconciliation Specialist**
**Baseline SHA**: e6f4b1c157afaed052584963b942ea04f9661610
**Phase**: M-ARCH Forensic Reconciliation
**Status**: Documentation-only — no code changes

---

## 1. MEMORY READINESS SCORECARD

| Capability | Ready | Partial | Missing | Evidence |
|------------|-------|---------|--------|----------|
| **Identity** | | GREEN | | `Memory.id` (UUID), `Fact.id`, `Decision.id`, `GraphNode.id` all present. `Memory` has `agent_id`, `run_id`, `user_id`. But no global `memory_id` cross-references `Fact`/`Decision` to `Memory` — they are separate tables. |
| **Source** | GREEN | | | `Source.content_hash` (SHA-256) at `app/models.py:319`. `Source` FK from `Fact.source_id` (`app/models.py:426`), `Decision.source_id` (`app/models.py:482`), `GraphEdge.source_id` (`app/models.py:585`). `MessageProvenance.source_id` chain via `memory_ids_used` (`app/models.py:633`). |
| **Time** | GREEN | | | `created_at`, `updated_at` on all models. `temporal_status` on Fact (`app/models.py:438`), Decision (`app/models.py:490`), GraphNode (`app/models.py:548`), GraphEdge (`app/models.py:584`), Memory (`app/models.py:254`). `deleted_at` on all. 30-day exponential decay in M5 (`app/services/m5_retrieval.py:69-79`). |
| **Context** | GREEN | | | `project_id`, `workspace_id`, `tenant_id` on all knowledge models. `session_id` on Fact/Decision/GraphEdge. `MessageProvenance.project_id`, `session_id` (`app/models.py:618-621`). `Memory.extra_metadata` JSON for arbitrary context (`app/models.py:252`). |
| **Confidence** | GREEN | | | `Fact.confidence` (default 1.0, `app/models.py:435`), `Decision.confidence` (default 1.0, `app/models.py:488`), `GraphEdge.confidence` (default 1.0, `app/models.py:582`), `Memory.confidence` (default 0.7, `app/models.py:255`). M5 uses confidence as a scoring factor (`app/services/m5_retrieval.py:141`). |
| **Authority** | GREEN | | | `Fact.authority` (default 1.0, `app/models.py:436`), `Decision.authority` (default 1.0, `app/models.py:489`), `GraphEdge.confidence` proxy, `Memory.authority` (default 1.0, `app/models.py:256`). M5 uses authority as a scoring factor (`app/services/m5_retrieval.py:140`). |
| **Provenance** | GREEN | | | `MessageProvenance` model with `memory_ids_used`, `retrieval_sources`, `user_message_preview` (`app/models.py:607-653`). `MemoryRecord.provenance` list in MemoryService (`app/services/memory.py:109-111`). `Source` → `NormalizedMessage` chain (`app/models.py:350-401`). Pipeline records `source_id` on every Fact/Decision/GraphEdge. |
| **Relationships** | GREEN | | | `GraphNode`/`GraphEdge` models with `relationship_type`, `source_node_id`, `target_node_id` (`app/models.py:520-604`). M4 extraction with regex patterns for `uses`, `connects_to`, `depends_on`, `is_a` (`app/services/m4_graph.py:14-39`). M5 graph context scoring via `_graph_context_score` (`app/services/m5_retrieval.py:82-97`). |
| **Supersession** | YELLOW | | | `temporal_status` field on all knowledge models. `superseded_by_id` on Fact (`app/models.py:440`) and Decision (`app/models.py:493`). M3 inline supersession in pipeline (`app/services/pipeline.py:112-137`). **GAP**: No `supersedes` column on Memory. No bidirectional FK links (DECISION-007). Pipeline supersession is inline and does NOT update `superseded_by_id` on the old fact (`app/services/pipeline.py:118` sets `temporal_status` but not `superseded_by_id`). |
| **Contradiction** | | | RED | No contradiction detection anywhere in the codebase. No `contradicts` edges on GraphEdge. No algorithm to detect conflicting facts. DECISION-010 condition 9 mentions "No `contradicts` edges to CERTIFIED memories" but no such edge type exists. |
| **Scope** | GREEN | | | Tenant → Workspace → Project hierarchy enforced. `Memory.tenant_id` + `workspace_id` + `project_id` (`app/models.py:238-249`). Cross-tenant isolation in MemoryService (`app/services/memory.py:483-489`). Policy engine for authorization (`app/services/memory.py:324-361`). |
| **Lifecycle** | YELLOW | | | `status` field on Fact (`app/models.py:443`), Decision (`app/models.py:495`), Memory (`MemoryRecord.status`, `app/services/memory.py:116`). `deleted_at` on all models. Soft delete via MemoryService (`app/services/memory.py:779-797`). `expire()` method (`app/services/memory.py:803-828`). **GAP**: `status` on Fact/Decision conflates lifecycle with temporal validity (DECISION-002 violation). Memory model has no `status` column — only `temporal_status` and `deleted_at`. |
| **Retrieval** | YELLOW | | | M5 multi-factor scoring (keyword + authority + confidence + recency + temporal + graph) (`app/services/m5_retrieval.py:100-154`). `retrieval.py` hybrid (vector + keyword) for Memory model only (`app/services/retrieval.py:61-121`). **GAP**: Two divergent retrieval services (DECISION-003). M5 does NOT include Memory model (`app/services/m5_retrieval.py:224-225`). No semantic embeddings populated. |
| **Auditability** | GREEN | | | `AuditEvent` model with 15+ indexed fields (`app/models.py:788-837`). MemoryService emits audit events for all operations (`app/services/memory.py:980-1013`). Ingest audit in API (`app/api/ingest.py:100-114`). Chat provenance via `MessageProvenance` (`app/services/chat_orchestrator.py:122-139`). **GAP**: No audit events for memory lifecycle transitions (DECISION-010 condition 7). |
| **Trust** | | | RED | No `trust_level` field on any model. No trust state machine. DECISION-009 requires `trust_level ≥ VERIFIED` for intelligence layer, but the field does not exist. Pipeline does not set any trust level. |

**Summary: 7 GREEN, 4 YELLOW, 3 RED out of 15 capabilities.**

---

## 2. PERSISTENT MEMORY READINESS

### What is Currently Persistent

| Data | Persistent | Storage | Evidence |
|------|-----------|---------|----------|
| **Sources** | YES | PostgreSQL `sources` | `app/models.py:302-366`. Content hash, status, stage, progress, error_message. |
| **Normalized Messages** | YES | PostgreSQL `normalized_messages` | `app/models.py:369-410`. Full content, role, timestamp, metadata. |
| **Facts** | YES | PostgreSQL `facts` | `app/models.py:413-464`. Subject, predicate, object, content, confidence, authority, temporal_status. |
| **Decisions** | YES | PostgreSQL `decisions` | `app/models.py:467-517`. Content, context, confidence, authority, temporal_status. |
| **Graph Nodes** | YES | PostgreSQL `graph_nodes` | `app/models.py:520-558`. Label, node_type, properties, temporal_status. |
| **Graph Edges** | YES | PostgreSQL `graph_edges` | `app/models.py:561-604`. Relationship_type, confidence, temporal_status, source FK. |
| **Memories** | YES | PostgreSQL `memories` | `app/models.py:232-266`. Content, memory_type, embedding (JSON), temporal_status, confidence, authority. |
| **Sessions** | YES | PostgreSQL `sessions` | `app/models.py:165-188`. Title, metadata, user FK. |
| **Audit Events** | YES | PostgreSQL `audit_events` | `app/models.py:788-837`. Append-only, 15+ indexed fields. |
| **Provenance** | YES | PostgreSQL `message_provenance` | `app/models.py:607-653`. Per-chat-response tracking. |

### Provenance Status

| Entity | Has Provenance | Completeness | Evidence |
|--------|---------------|-------------|----------|
| Source → Message | YES | Complete | `Source.normalized_messages` cascade (`app/models.py:350-354`). Each message has `source_id`. |
| Fact → Source | YES | Complete | `Fact.source_id` FK (`app/models.py:426`). Pipeline sets it (`app/services/pipeline.py:120`). |
| Decision → Source | YES | Complete | `Decision.source_id` FK (`app/models.py:482`). Pipeline sets it (`app/services/pipeline.py:159`). |
| GraphEdge → Source | YES | Complete | `GraphEdge.source_id` FK (`app/models.py:585`). M4 sets it (`app/services/m4_graph.py:187`). |
| Memory → Provenance | PARTIAL | MemoryRecord.provenance list exists but NOT in DB model | `MemoryRecord.provenance` is a Python list (`app/services/memory.py:109`), stored in `Memory.extra_metadata` JSON, not a separate table. |
| Chat → Provenance | YES | Complete | `MessageProvenance.memory_ids_used` + `retrieval_sources` (`app/models.py:633-637`). |

### Temporal Semantics

| Entity | temporal_status | superseded_by_id | Supersession Logic | Evidence |
|--------|----------------|------------------|-------------------|----------|
| Fact | YES | YES | M3 inline in pipeline (`app/services/pipeline.py:112-137`) + standalone M3 (`app/services/m3_temporal.py:14-91`) | `app/models.py:438`, `app/models.py:440` |
| Decision | YES | YES | M3 inline in pipeline + standalone M3 (`app/services/m3_temporal.py:94-154`) | `app/models.py:490`, `app/models.py:493` |
| GraphNode | YES | NO | Only `temporal_status`, no supersession | `app/models.py:548` |
| GraphEdge | YES | NO | Only `temporal_status`, no supersession | `app/models.py:584` |
| Memory | YES | NO | Only `temporal_status` column. No `supersedes` or `superseded_by` columns. | `app/models.py:254` |

### GREEN/YELLOW/RED Summary

| Area | Status | Notes |
|------|--------|-------|
| Source persistence | GREEN | Full chain: content, hash, status, stage, messages |
| Fact persistence | GREEN | Complete with temporal_status, superseded_by_id |
| Decision persistence | GREEN | Complete with temporal_status, superseded_by_id |
| Graph persistence | GREEN | Nodes and edges with temporal_status |
| Memory persistence | YELLOW | Persists but NOT in retrieval (DECISION-004 gap) |
| Provenance chain | GREEN | Source → Fact/Decision/GraphEdge → MessageProvenance |
| Provenance for Memory | YELLOW | In extra_metadata JSON, not a dedicated chain |
| Temporal semantics | YELLOW | Fact/Decision have full temporal; Memory/GraphNode/GraphEdge partial |
| Supersession lineage | YELLOW | Fact/Decision have `superseded_by_id` but pipeline doesn't set it. No bidirectional links (DECISION-007). Memory has none. |
| Contradiction tracking | RED | None exists |
| Trust level | RED | No field, no state machine |
| Semantic retrieval | RED | No embedding infrastructure (DECISION-005) |
| Background ingestion | RED | Synchronous only (DECISION-006) |

---

## 3. MEMORY INTELLIGENCE READINESS

### What the Current System CAN Safely Provide TODAY

1. **Multi-factor retrieval scoring** — M5 provides keyword relevance, authority, confidence, recency, temporal status, and graph context scores. These are real, computed values that an intelligence layer can trust as input features. (`app/services/m5_retrieval.py:37-97`)

2. **Temporal truth management** — Facts and decisions carry `temporal_status` (current/historical), `created_at`, `updated_at`. An intelligence layer can safely filter on `temporal_status == "current"` to get the latest knowledge. (`app/services/m3_temporal.py:14-91`)

3. **Graph connectivity** — Knowledge graph with entity nodes and typed relationships (uses, connects_to, depends_on, is_a). Graph context scoring is computed per retrieval. (`app/services/m4_graph.py:14-39`)

4. **Provenance chains** — Every fact/decision carries `source_id` → `Source` → `NormalizedMessage`. Chat responses carry `MessageProvenance` with `memory_ids_used` and `retrieval_sources`. (`app/models.py:607-653`)

5. **Confidence and authority scores** — Every extracted fact/decision carries these numeric values. They are used in M5 scoring. An intelligence layer can use them as reliability indicators. (`app/services/m5_retrieval.py:128-143`)

6. **Scope isolation** — Tenant → Workspace → Project hierarchy with `tenant_id`, `workspace_id`, `project_id` on all knowledge models. Cross-tenant isolation enforced in MemoryService. (`app/services/memory.py:483-489`)

7. **Soft deletion** — `deleted_at` on all major models. Intelligence layer can safely exclude `deleted_at IS NOT NULL` records. (`app/models.py:257`, `app/models.py:454`)

8. **Content hashing** — SHA-256 content hash on `Source` for deduplication. Intelligence layer can use this for duplicate detection. (`app/api/ingest.py:61-77`)

### What a Future Intelligence Layer CANNOT Safely Assume

1. **Unified memory identity** — Facts, Decisions, and Memories are in separate tables. An intelligence layer cannot query "all knowledge" with a single query. It must query three separate tables and merge results. (DECISION-001 gap)

2. **Memory model is retrievable** — M5 retrieval (`retrieve_hybrid`) only queries Fact and Decision. Memory records are invisible to retrieval. An intelligence layer that depends on M5 results will miss all user-created and agent-created memories. (`app/services/m5_retrieval.py:224-225`)

3. **Semantic retrieval works** — No embedding infrastructure exists. The `Memory.embedding` column accepts JSON but is never populated. An intelligence layer that expects semantic similarity search will get no results. (DECISION-005 gap)

4. **Supersession is bidirectional** — When a fact is superseded, only `temporal_status` is changed. The `superseded_by_id` field is NOT updated by the pipeline. An intelligence layer that follows supersession chains will find broken links. (`app/services/pipeline.py:112-137`)

5. **Trust levels are meaningful** — No `trust_level` field exists. An intelligence layer cannot gate actions on trust level. (DECISION-009 gap)

6. **Memory Safety Gate is enforced** — No gate implementation exists. Any content with `status=active` and `temporal_status=current` is immediately persistent and retrievable. (DECISION-010 gap)

7. **Ingestion is reliable** — Synchronous ingestion blocks HTTP for the entire pipeline. No retry, no progress tracking for long operations. An intelligence layer that depends on ingestion completing will experience HTTP timeouts. (DECISION-006 gap)

8. **Contradiction detection** — No algorithm exists to identify conflicting facts. An intelligence layer cannot rely on contradiction signals. (DECISION-010 condition 9)

### Reference: 10 Binding Decisions

| Decision | Title | Intelligence Layer Impact |
|----------|-------|---------------------------|
| DECISION-001 | Canonical Memory Object | Intelligence layer MUST NOT assume a single table for all knowledge. Three separate queries required. |
| DECISION-002 | Lifecycle ≠ Validity ≠ Trust | Intelligence layer MUST filter by specific dimension. Cannot use `status` alone. |
| DECISION-003 | Single Retrieval Service | Intelligence layer MUST NOT call both M5 and retrieval.py — they diverge. Only M5 is the canonical path. |
| DECISION-004 | Memory in Retrieval | Intelligence layer MUST NOT expect Memory records in M5 results. They are excluded until implemented. |
| DECISION-005 | Semantic Retrieval | Intelligence layer MUST NOT assume embedding-based similarity works. Only keyword + BM25 scoring is functional. |
| DECISION-006 | Background Ingestion | Intelligence layer MUST NOT assume ingestion completes within HTTP timeout. Synchronous blocking is current behavior. |
| DECISION-007 | Supersession Chain | Intelligence layer MUST NOT follow `superseded_by_id` links — they are not populated by the pipeline. |
| DECISION-008 | Universal Agent Event Format | Intelligence layer MUST NOT expect agent events in canonical format. No `/api/v1/agent/events` endpoint exists. |
| DECISION-009 | Trust Level Gating | Intelligence layer MUST NOT check `trust_level` — the field does not exist. No gating is enforced. |
| DECISION-010 | Memory Safety Gate | Intelligence layer MUST NOT assume any content filtering. All content passes through immediately. |

---

## 4. DECISION RECONCILIATION

### DECISION-001: Canonical Memory Object

| Field | Value |
|-------|-------|
| **Decision** | Single unified `memories` table with `memory_type` discriminator |
| **Current Implementation** | Three separate tables: `facts`, `decisions`, `memories` |
| **Gap** | Data migration not performed. Queries must union three tables. |
| **Impact on Memory Intelligence** | CRITICAL — Intelligence layer cannot perform "all knowledge" queries. Must merge results from three tables with different schemas. |
| **Required Condition** | Migration script to merge `facts` and `decisions` into `memories` with `memory_type` discriminator. All queries must filter by `(workspace_id, memory_type, temporal_status)`. |

### DECISION-002: Lifecycle ≠ Knowledge Validity ≠ Trust

| Field | Value |
|-------|-------|
| **Decision** | `status` (lifecycle), `temporal_status` (validity), `trust_level` (trust) are three independent dimensions |
| **Current Implementation** | Fact/Decision have both `status` and `temporal_status` but `status` is always "active" (set at creation, never changed). Memory model has only `temporal_status` and `deleted_at` — no `status` column. No `trust_level` anywhere. |
| **Gap** | Three dimensions not properly modeled. `status` on Fact/Decision is vestigial. Memory lacks `status`. No `trust_level` exists. |
| **Impact on Memory Intelligence** | HIGH — Intelligence layer cannot distinguish "deleted but was true when active" from "always false". Cannot gate on trust. |
| **Required Condition** | Add `status` column to Memory model. Add `trust_level` column to all knowledge models. Implement state machine for each dimension. Audit events must record all three on every transition. |

### DECISION-003: Single Retrieval Service

| Field | Value |
|-------|-------|
| **Decision** | Replace `m5_retrieval.py` and `retrieval.py` with one `CanonicalRetrievalService` |
| **Current Implementation** | Two services exist and diverge. `m5_retrieval.py` queries Fact + Decision only. `retrieval.py` queries Memory only with hybrid vector+keyword. |
| **Gap** | `retrieval.py` is not deprecated or removed. Both services return different results for the same query scope. |
| **Impact on Memory Intelligence** | HIGH — Intelligence layer cannot trust retrieval results. Must choose between two services with different coverage and scoring. |
| **Required Condition** | Remove `retrieval.py`. Merge Memory model queries into M5. Unified scoring across all memory types. Both streaming and non-streaming chat use the same path. |

### DECISION-004: Memory Model Included in Retrieval

| Field | Value |
|-------|-------|
| **Decision** | M5 retrieval MUST query the `Memory` model |
| **Current Implementation** | `retrieve_hybrid()` in `m5_retrieval.py:211-242` only calls `rank_facts()` and `rank_decisions()`. Memory is explicitly excluded: "Note: Memory model has no deleted_at column, so memory ranking is deferred" (`app/services/m5_retrieval.py:224-225`). |
| **Gap** | Memory model IS missing `deleted_at` column — this is the stated blocker. But Memory model DOES have `deleted_at` (`app/models.py:257`). The comment is stale/incorrect. |
| **Impact on Memory Intelligence** | CRITICAL — User-created and agent-created memories are invisible to retrieval. Chat context never includes them. |
| **Required Condition** | Add `rank_memories()` to M5. Include Memory in `retrieve_hybrid()`. The `deleted_at` column already exists — the blocker comment is stale. |

### DECISION-005: Semantic Retrieval Required

| Field | Value |
|-------|-------|
| **Decision** | Embedding-based semantic retrieval alongside keyword (BM25) |
| **Current Implementation** | `retrieval.py` has `_cosine_similarity()` (`app/services/retrieval.py:22-32`) and `_hybrid_score()` (`app/services/retrieval.py:45-58`) but no embedding infrastructure populates `Memory.embedding`. No embedding model selected. No vector storage. |
| **Gap** | Embedding column exists (JSON) but is never written to. No model selected. No vector index. |
| **Impact on Memory Intelligence** | CRITICAL — Semantic queries ("database" vs "PostgreSQL") fail. Only exact keyword matches work. |
| **Required Condition** | Select embedding model. Integrate embedding generation on memory creation. Add vector index (pgvector or external). Populate `Memory.embedding` for all existing records. |

### DECISION-006: Background Ingestion Required

| Field | Value |
|-------|-------|
| **Decision** | Async background ingestion via task queue |
| **Current Implementation** | `run_pipeline()` is synchronous, called directly from the HTTP handler (`app/api/ingest.py:80-91`). `IngestJob` model exists (`app/models.py:269-297`) but is only used for the legacy endpoint. No task queue dependency. |
| **Gap** | Pipeline runs synchronously in HTTP request thread. No retry, no progress tracking, no batch processing. |
| **Impact on Memory Intelligence** | HIGH — Intelligence layer cannot reliably ingest large conversations. HTTP timeouts will occur. No way to track ingestion progress. |
| **Required Condition** | Add task queue (Celery/RQ/Dramatiq). IngestJob becomes functional. API returns job ID immediately. Client polls for status. Pipeline runs in worker process. |

### DECISION-007: Supersession Creates Linked Chain

| Field | Value |
|-------|-------|
| **Decision** | Bidirectional FK links: `A.superseded_by = B`, `B.supersedes = A` |
| **Current Implementation** | `superseded_by_id` column exists on Fact (`app/models.py:440`) and Decision (`app/models.py:493`) but is NEVER populated by the pipeline. Pipeline only sets `temporal_status = "historical"` (`app/services/pipeline.py:118, 135`). M3 functions DO set `superseded_by` but only in the standalone functions, not in the pipeline. Memory model has NO `supersedes` or `superseded_by` columns. |
| **Gap** | `superseded_by_id` not populated. No bidirectional links. No `supersedes` column on Memory. No circular supersession detection. |
| **Impact on Memory Intelligence** | HIGH — Intelligence layer cannot trace supersession chains. "What superseded this?" requires table scans. Memory has no lineage at all. |
| **Required Condition** | Update pipeline to set `superseded_by_id` on old fact. Add `supersedes` column to Memory. Add FK constraints. Implement circular supersession detection. |

### DECISION-008: Universal Agent Event Format

| Field | Value |
|-------|-------|
| **Decision** | All external agents emit events in `UniversalAgentEvent` format |
| **Current Implementation** | Each connector transforms its own format into `NormalizedConversation`. No canonical agent event format. No `/api/v1/agent/events` endpoint. Connectors are transformers, not validators. |
| **Gap** | No `UniversalAgentEvent` schema. No agent event ingestion endpoint. Each new agent requires a new connector. |
| **Impact on Memory Intelligence** | MEDIUM — Intelligence layer depends on agent-generated memories. Without canonical format, each agent integration is custom work. |
| **Required Condition** | Define `UniversalAgentEvent` schema. Create `/api/v1/agent/events` endpoint. All connectors implement `to_universal_event()`. Schema validation on inbound events. |

### DECISION-009: Trust Level Gating for Intelligence

| Field | Value |
|-------|-------|
| **Decision** | Intelligence layer MAY only act on memories with `trust_level ≥ VERIFIED` |
| **Current Implementation** | No `trust_level` field exists on any model. No trust state machine. Pipeline does not assign trust levels. |
| **Gap** | Entire trust system missing. No field, no states, no transitions. |
| **Impact on Memory Intelligence** | CRITICAL — Intelligence layer cannot distinguish reliable from unreliable memories. All memories are treated equally. |
| **Required Condition** | Add `trust_level` column to all knowledge models. Implement trust state machine (UNVERIFIED → VERIFIED → CERTIFIED). Pipeline-extracted memories start at UNVERIFIED. Intelligence layer checks before action. |

### DECISION-010: Memory Safety Gate

| Field | Value |
|-------|-------|
| **Decision** | 10-condition gate before memory becomes persistent/actionable |
| **Current Implementation** | No gate implementation. Any content with `status=active` and `temporal_status=current` is immediately persistent. No confidence threshold check. No authority threshold check. No content policy validation. No scope verification. No provenance chain verification. |
| **Gap** | All 10 conditions unimplemented. |
| **Impact on Memory Intelligence** | CRITICAL — Intelligence layer may act on low-confidence, low-authority, or incorrect memories. No safety net. |
| **Required Condition** | Implement all 10 conditions: (1) ACTIVE status, (2) CURRENT temporal, (3) confidence ≥ 0.3, (4) authority ≥ 0.1, (5) content policy validation, (6) scope isolation, (7) provenance chain, (8) trust_level ≥ VERIFIED, (9) no contradiction edges, (10) not flagged for review. |

---

## 5. NEXT MEMORY INTELLIGENCE LAYER — READINESS BOUNDARY

### What the Current System CAN Safely Provide Today

**Data the intelligence layer can consume without risk:**

1. **Fact and Decision records with `temporal_status="current"`** — These are the most mature knowledge objects. They carry confidence, authority, source provenance, and temporal validity. (`app/services/m3_temporal.py:157-178`)

2. **Graph connectivity scores** — M5 computes graph context scores per retrieval. The intelligence layer can use these as authority signals. (`app/services/m5_retrieval.py:82-97`)

3. **Multi-factor retrieval rankings** — M5 provides scored results with per-factor breakdowns. The intelligence layer can use the composite score and individual factors. (`app/services/m5_retrieval.py:128-143`)

4. **MessageProvenance chains** — Every chat response has a provenance record linking to the memories used. The intelligence layer can trace how knowledge influenced responses. (`app/models.py:607-653`)

5. **Source → Message → Fact/Decision chain** — Full provenance from raw conversation to extracted knowledge. (`app/models.py:302-410`)

6. **Tenant/Workspace/Project scope** — All knowledge is scoped. The intelligence layer can safely filter by scope. (`app/models.py:238-249`)

7. **Soft deletion state** — `deleted_at` filtering is reliable. (`app/models.py:257`)

### What the Next Layer CAN Trust

| Trust Boundary | What Can Be Trusted | Evidence |
|---------------|-------------------|----------|
| **Fact/Decision retrieval results** | M5 scores are deterministic for the same query/state | `app/services/m5_retrieval.py:100-208` — same inputs → same scores |
| **Temporal status** | `temporal_status="current"` means not yet superseded | M3 inline supersession works (`app/services/pipeline.py:112-137`) |
| **Confidence/authority values** | Numeric scores from M2 extraction | `app/services/m5_retrieval.py:131-132` uses them directly |
| **Provenance chains** | Source → extraction → retrieval chain is complete for Fact/Decision | `Fact.source_id` → `Source` → `NormalizedMessage` |
| **Scope isolation** | Cross-tenant access is blocked | `app/services/memory.py:483-489` |
| **Graph structure** | Nodes and edges are deduplicated by `(workspace_id, external_id)` | `app/services/m4_graph.py:131-137` |
| **Content hashing** | SHA-256 hash prevents duplicate ingestion | `app/api/ingest.py:61-77` |

### What the Next Layer MUST NOT Assume

| Assumption | Why It Is Unsafe | Required Fix |
|------------|-----------------|-------------|
| **All knowledge is in one table** | Facts, Decisions, and Memories are in separate tables with different schemas | DECISION-001: Merge into single `memories` table |
| **Memory records are retrievable** | M5 only queries Fact and Decision — Memory is excluded | DECISION-004: Add Memory to M5 retrieval |
| **Semantic search works** | No embedding infrastructure exists; `Memory.embedding` is never populated | DECISION-005: Implement embedding generation + vector index |
| **Supersession chains are complete** | `superseded_by_id` is not populated by the pipeline; Memory has no supersession columns | DECISION-007: Populate FK links, add columns to Memory |
| **Trust levels exist** | No `trust_level` field on any model | DECISION-009: Add trust_level + state machine |
| **Content is safety-filtered** | No gate implementation; any content becomes persistent immediately | DECISION-010: Implement Memory Safety Gate |
| **Ingestion completes reliably** | Synchronous HTTP ingestion blocks for pipeline duration; no retry | DECISION-006: Background task queue |
| **Contradictions are detected** | No contradiction detection algorithm exists | New decision required |
| **Agent events follow a format** | No canonical agent event format; each connector is custom | DECISION-008: Define UniversalAgentEvent |
| **Retrieval is deterministic across services** | `m5_retrieval.py` and `retrieval.py` diverge | DECISION-003: Merge into single service |

### Contracts That MUST Exist Before Implementation

| Contract | Purpose | Status |
|----------|---------|--------|
| **Canonical Memory Contract** | Single table schema, type discriminator, lifecycle dimensions | Defined (`docs/CANONICAL_MEMORY_CONTRACT.md`) — NOT implemented |
| **Canonical Retrieval Contract** | Single retrieval service covering all memory types | Defined (`docs/CANONICAL_RETRIEVAL_CONTRACT.md`) — NOT implemented |
| **Derived State Contract** | How pipeline output maps to memory model | Defined (`docs/DERIVED_STATE_CONTRACT.md`) — NOT implemented |
| **Memory Safety Gate Contract** | 10-condition gate implementation | Defined (DECISION-010) — NOT implemented |
| **Memory Identity Contract** | Cross-reference between Fact/Decision/Memory tables | Defined (`docs/MEMORY_IDENTITY_CONTRACT.md`) — NOT implemented |
| **Temporal Knowledge State Contract** | Temporal supersession with bidirectional links | Defined (`docs/TEMPORAL_KNOWLEDGE_STATE_CONTRACT.md`) — Partially implemented |
| **Provenance Evidence Contract** | Complete provenance chain requirements | Defined (`docs/PROVENANCE_EVIDENCE_CONTRACT.md`) — Partially implemented |
| **Memory Write Authority Matrix** | Who can write what memory type | Defined (`docs/MEMORY_WRITE_AUTHORITY_MATRIX.md`) — Partially implemented (policy engine exists) |

---

## 6. KEY ARCHITECTURAL FINDINGS

### Finding 1: Memory Model Is Write-Only

The `Memory` model (`app/models.py:232-266`) has full schema support: `tenant_id`, `workspace_id`, `user_id`, `agent_id`, `run_id`, `project_id`, `memory_type`, `content`, `embedding`, `temporal_status`, `confidence`, `authority`, `deleted_at`. The MemoryService (`app/services/memory.py`) can write to it. The API endpoints (`app/api/memory.py`) can create, read, update, delete, and search Memory records.

**But**: M5 retrieval (`app/services/m5_retrieval.py:224-225`) explicitly excludes Memory from retrieval. Chat orchestration (`app/services/chat_orchestrator.py:59-65`) calls `retrieve_for_chat()` which calls `retrieve_hybrid()` which only returns Fact and Decision results. **Memory records are written but never read by the system that needs them most — the chat context.**

### Finding 2: Pipeline Supersession Is Incomplete

The pipeline (`app/services/pipeline.py:112-137`) supersedes facts by setting `temporal_status = "historical"` but does NOT update `superseded_by_id` on the old record. The standalone M3 functions (`app/services/m3_temporal.py`) DO set `superseded_by` on the new record but NOT on the old record (only `temporal_status`). Neither direction of the bidirectional link (DECISION-007) is consistently populated.

### Finding 3: Two Retrieval Services Diverged

`m5_retrieval.py` (M5) queries Fact + Decision with multi-factor scoring. `retrieval.py` queries Memory with hybrid vector+keyword scoring. They use different scoring formulas, different candidate pools, and return different result types. The chat orchestrator uses M5 (`app/services/chat_orchestrator.py:16`), so Memory records are never in chat context. The Memory API search (`app/api/memory.py:264-302`) uses MemoryService.search which uses its own ILIKE-based query. **Three different retrieval paths, three different result sets.**

### Finding 4: MemoryService Has Correct Architecture But Missing DB Columns

MemoryService (`app/services/memory.py`) implements the correct architectural pattern: policy engine → authorization → provenance → persistence → audit. The `MemoryRecord` dataclass has `supersedes`, `superseded_by`, `version`, `status`, `scope`, `permissions` — all the fields DECISION-001 and DECISION-002 require. But the `Memory` ORM model (`app/models.py:232-266`) only persists a subset: `memory_type` (mapped), `content`, `confidence`, `authority`, `temporal_status`, `deleted_at`. The rest are stuffed into `extra_metadata` JSON. **The service layer is ready; the DB schema is not.**

### Finding 5: Trust Level Is the Biggest Gap

No `trust_level` field exists anywhere. DECISION-009 requires it. DECISION-010 condition 8 requires `trust_level ≥ VERIFIED` for autonomous agent use. The certification document (`docs/MEMORY_INTELLIGENCE_READINESS_CERTIFICATION.md`) lists it as P0 criterion 8. Without it, the intelligence layer cannot implement any reliability gating.

### Finding 6: Contradiction Detection Is Entirely Absent

There is no algorithm, no edge type, no data structure for contradiction detection anywhere in the codebase. DECISION-010 condition 9 references "No `contradicts` edges to CERTIFIED memories" but the `contradicts` relationship type does not exist in `GraphEdge.relationship_type` enumeration (`app/services/m4_graph.py:14-39`). This is a completely new capability that must be designed and implemented.

---

## 7. CERTIFICATION READINESS

**Current Status: NOT CERTIFIED — 0/8 P0 criteria met**

| P0 Criterion | Status | Evidence |
|-------------|--------|----------|
| 1. Single canonical memory table | NOT MET | Three tables: facts, decisions, memories |
| 2. Unified retrieval service | NOT MET | Two services: m5_retrieval.py + retrieval.py |
| 3. Memory model in retrieval | NOT MET | Memory excluded from M5 (`app/services/m5_retrieval.py:224`) |
| 4. Embedding infrastructure | NOT MET | No model, no vector index, no population |
| 5. Background ingestion worker | NOT MET | Synchronous HTTP only |
| 6. `supersedes` FK constraints | NOT MET | Column exists on Fact/Decision but not populated; absent on Memory |
| 7. Memory Safety Gate enforced | NOT MET | No implementation |
| 8. Trust level field + state machine | NOT MET | No field exists |

**P1 Criteria: 0/7 met**
**P2 Criteria: 0/5 met**

**Intelligence Layer Implementation MUST NOT begin until P0 certification is achieved.**

---

*Document produced by Agent 7 — Memory Intelligence Readiness Architecture. Read-only analysis. No code modified.*
