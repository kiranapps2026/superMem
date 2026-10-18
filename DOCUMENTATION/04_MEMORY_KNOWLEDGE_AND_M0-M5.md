# SwarmVault WebApp — Memory, Knowledge & M0–M5 Reference
**Version:** 1.0.0
**Date:** 2026-09-01
**Evidence base:** Repository inspection (commit 902d85e), test_golden_dataset, m0–m5 service files

---

## 1. Memory Overview

In SwarmVault, **memory** is the primary retrievable knowledge unit. It is not a raw conversation log. Memory is structured knowledge extracted from conversations and documents, enriched with confidence, authority, temporal status, and provenance.

### What Memory Is
- A text content unit (`memories.content`, Text column)
- Scoped to a tenant, workspace, and optionally a project
- Tagged with a `memory_type` (default: `procedural_memory`)
- Scored with `confidence` (0.0–1.0) and `authority` (0.0–1.0)
- Tracked with `temporal_status` (current / superseded / historical)
- Optionally embedded for semantic search (`memories.embedding`, JSON array)
- Always accompanied by provenance (source session, user, timestamp)

### What Creates Memory
1. **Direct creation** — User or agent creates memory via API (`POST /api/v1/memory`)
2. **Ingestion pipeline** — M0–M5 pipeline extracts memories from uploaded conversations
3. **Chat extraction** — (NOT ESTABLISHED IN AVAILABLE SOURCE) — Whether chat responses automatically create memories is not verified in the current codebase

### How Memory Is Stored
- **Table:** `memories` (PostgreSQL)
- **Columns:** id, tenant_id, workspace_id, user_id, agent_id, run_id, project_id, memory_type, content, metadata (JSON), embedding (JSON[]), temporal_status, confidence, authority, deleted_at, created_at, updated_at
- **Indexes:** tenant_id, workspace_id, project_id, temporal_status, deleted_at

### How Memory Is Retrieved
1. **BM25 search** — Keyword matching on content
2. **Semantic search** — Cosine similarity on embedding vectors (optional)
3. **Reranking** — Combined score ranking
4. **Temporal filtering** — Current facts by default

### How Temporal Status Works
- **current** — Active, valid knowledge
- **superseded** — Replaced by a newer version (superseded_by_id points to new version)
- **historical** — Archived, no longer active

### Provenance
Every memory carries implicit provenance through:
- `source_id` (if from ingestion)
- `session_id` (if from chat)
- `user_id` (creator)
- `metadata` JSON (additional context)

---

## 2. The M0–M5 Intelligence Pipeline

The M0–M5 pipeline is the core intelligence engine. It transforms raw, unstructured input into structured, queryable, evidence-backed knowledge.

### Pipeline Orchestration
**File:** `app/services/pipeline.py`
**Function:** `run_pipeline(db, workspace_id, tenant_id, project_id, user_id, source_type, raw_content, title, config)`

```
async def run_pipeline(...) -> dict[str, Any]:
    # M0: Normalize
    conversation = normalize(raw_content, source_type=source_type)
    source = Source(...)
    session = Session(...)

    # M1: Session understanding
    for msg in conversation.messages:
        understand_session(msg)

    # M2: Extract facts + decisions
    facts = extract_facts(normalized_messages)
    decisions = extract_decisions(normalized_messages)

    # M3: Temporal processing
    supersede_fact(existing_facts, new_facts)
    supersede_decision(existing_decisions, new_decisions)

    # M4: Knowledge graph
    nodes, edges = extract_graph_elements(facts, messages)
    persist_graph(nodes, edges, source_id)

    return result
```

---

## 3. M0 — Normalization & Deduplication

### Purpose
Transform raw input (conversation JSON/JSONL, documents) into a normalized, deduplicated, secret-redacted format ready for intelligence extraction.

### Implementation
| Component | Location |
|-----------|----------|
| Orchestrator | `app/services/pipeline.py` (lines 47–65) |
| Connector/normalizer | `app/services/connectors.py` — `normalize()` function |
| Model | `app/models.py:302-367` Source, `:369-411` NormalizedMessage |

### Input Formats
- Conversation JSON/JSONL
- (Other formats NOT ESTABLISHED IN AVAILABLE SOURCE)

### Processing Steps
1. **Parse** — Normalize raw content into structured conversation format
2. **Redact** — Remove secrets (API keys, passwords, tokens, private keys, database URLs)
3. **Deduplicate** — Compute SHA-256 content hash; skip if hash already exists for same workspace
4. **Persist** — Create Source record + NormalizedMessage records

### Secret Redaction Patterns
The system redacts these patterns during normalization:
- `api_key` / `apikey` patterns
- Password fields
- Bearer tokens
- Private key headers (RSA, EC, PKCS)
- Database connection strings
- Generic credential patterns

### Output
```
Source (id, project_id, workspace_id, tenant_id, source_type, content_hash, status, message_count)
 └─▶ NormalizedMessage[] (id, source_id, message_index, role, content, metadata)
```

### Deduplication
- **Key:** `content_hash` (SHA-256)
- **Scope:** Per workspace
- **Behavior:** If `content_hash` already exists for the workspace, the source is not re-processed
- **Index:** `ix_sources_workspace_tenant` on (workspace_id, tenant_id), unique index on `content_hash`

### Evidence
- Migration 008 (`008_add_source_content_hash.py`) — added content_hash column + index
- `test_content_dedup_golden` — verifies duplicate detection
- `test_connectors.py` — verifies normalization

---

## 4. M1 — Session Understanding

### Purpose
Identify conversation structure (exchanges, turns), preserve context, and link messages to sessions.

### Implementation
| Component | Location |
|-----------|----------|
| Service | `app/services/m1_session.py` |
| Model | `app/models.py:165-188` Session, `:191-207` Message |

### Processing
1. Identify message roles (user/assistant/system)
2. Identify exchange boundaries (user→assistant pairs)
3. Preserve conversation context and ordering
4. Handle multi-exchange sessions
5. Link messages to created Session record

### Output
```
Session (id, workspace_id, user_id, title, metadata)
 └─▶ Message[] (id, session_id, role, content, metadata, message_index)
```

### Evidence
- `test_full_pipeline_golden_conversation` — verifies M1 produces correct session structure

---

## 5. M2 — Fact & Decision Extraction

### Purpose
Extract structured knowledge from normalized messages: factual statements (subject-predicate-object) and decisions.

### Implementation
| Component | Location |
|-----------|----------|
| Service | `app/services/m2_facts.py` |
| Model | `app/models.py:413-465` Fact, `:467-518` Decision |

### Fact Extraction
Uses regex pattern matching to extract subject-predicate-object triples:
```
Patterns:
- "X uses Y", "X runs on Y", "X is built with Y"
- "X is Y", "X are Y"
- (Additional patterns in FACT_PATTERNS list)
```

**Fact Schema:**
| Field | Type | Purpose |
|-------|------|---------|
| subject | String(500) | Entity the fact describes |
| predicate | String(100) | Relationship type |
| object | String(500) | Value/entity |
| content | Text | Full text representation |
| confidence | Float | 0.0–1.0 extraction certainty |
| authority | Float | 0.0–1.0 source trust |
| temporal_status | String | current / superseded / historical |
| superseded_by_id | String(36) | FK to newer version |
| source_id | String(36) | FK to Source |
| workspace_id | String(36) | FK to Workspace |

### Decision Extraction
Pattern matching for decision indicators:
```
Patterns:
- "we decided to..."
- "the decision is..."
- "we will..."
- "let's go with..."
```

**Decision Schema:**
| Field | Type | Purpose |
|-------|------|---------|
| content | Text | Decision statement |
| context | Text | Surrounding context |
| confidence | Float | 0.0–1.0 |
| authority | Float | 0.0–1.0 |
| temporal_status | String | current / superseded / historical |
| source_id | String(36) | FK to Source |

### Evidence
- `test_search_finds_golden_facts` — verifies fact extraction
- `test_content_dedup_golden` — golden dataset with known facts

---

## 6. M3 — Temporal Truth

### Purpose
Manage the lifecycle of facts and decisions over time: versioning, supersession, and stale detection.

### Implementation
| Component | Location |
|-----------|----------|
| Service | `app/services/m3_temporal.py` |
| Model | `app/models.py:413-518` Fact and Decision (temporal_status, superseded_by_id) |

### Temporal Status Lifecycle
```
                    ┌─────────────┐
                    │   current   │ ← Active, valid knowledge
                    └──────┬──────┘
                           │ New version discovered / contradiction detected
                           ▼
                    ┌─────────────┐
                    │ superseded  │ ← Replaced by newer version
                    └──────┬──────┘
                           │ Archived (no longer relevant)
                           ▼
                    ┌─────────────┐
                    │  historical │ ← Preserved for audit
                    └─────────────┘
```

### Supersession Mechanism
1. New fact contradicts existing fact (same subject/predicate)
2. Existing fact marked `temporal_status = "superseded"`
3. Existing fact's `superseded_by_id` set to new fact's ID
4. New fact marked `temporal_status = "current"`

### Contradiction Detection
- Same subject + predicate across different sources
- Conflicting object values
- Temporal overlap (both marked as current)

### Retrieval Behavior
- Default: Only `temporal_status = "current"` facts retrieved
- Historical/superseded available on explicit request
- Graph queries exclude superseded nodes by default

### Evidence
- `test_facts_temporal_status_filtering` — verifies current-only retrieval
- `test_temporal_status` — verifies status transitions
- `test_consolidate` — verifies consolidation behavior

---

## 7. M4 — Knowledge Graph

### Purpose
Construct and maintain a knowledge graph of entities and relationships extracted from conversations.

### Implementation
| Component | Location |
|-----------|----------|
| Service | `app/services/m4_graph.py` |
| Model | `app/models.py:520-604` GraphNode, GraphEdge |

### GraphNode
| Field | Type | Purpose |
|-------|------|---------|
| workspace_id | String(36) | Tenant scoping |
| project_id | String(36) | Project grouping |
| external_id | String(255) | External reference |
| label | String(500) | Display name |
| node_type | String(50) | Entity type (default: "entity") |
| properties | JSON | Additional attributes |
| temporal_status | String | current / superseded / historical |
| deleted_at | DateTime | Soft delete |

### GraphEdge
| Field | Type | Purpose |
|-------|------|---------|
| workspace_id | String(36) | Tenant scoping |
| source_node_id | String(36) | FK to GraphNode |
| target_node_id | String(36) | FK to GraphNode |
| relationship_type | String(100) | Relationship label |
| properties | JSON | Additional attributes |
| confidence | Float | 0.0–1.0 |
| temporal_status | String | current / superseded / historical |
| source_id | String(36) | FK to Source (provenance) |

### Graph Operations
| Operation | Description |
|-----------|-------------|
| neighbors | Find all nodes connected to a given node |
| shortest_path | Find shortest path between two nodes |
| graph_stats | Count nodes/edges by type |
| query | Filtered graph query (by workspace, project, temporal status) |

### Indexes
- `ix_graph_nodes_workspace` on (workspace_id, temporal_status)
- `ix_graph_nodes_workspace_type` on (workspace_id, node_type)
- `ix_graph_edges_source_target` on (source_node_id, target_node_id)
- `ix_graph_edges_workspace` on (workspace_id, temporal_status)
- Unique constraint: (workspace_id, external_id)

### Evidence
- `test_graph_query` — verifies graph queries
- `test_neighbors` — verifies neighbor traversal
- `test_shortest_path` — verifies path finding
- `test_graph_stats` — verifies statistics
- `test_graph_cross_tenant_isolation` — verifies tenant isolation

---

## 8. M5 — Retrieval & Intelligence

### Purpose
Find relevant memories for a user query using BM25 keyword search, optional semantic search, and reranking.

### Implementation
| Component | Location |
|-----------|----------|
| Service | `app/services/m5_retrieval.py` |
| Legacy | `app/services/retrieval.py` |
| Model | `app/models.py:232-267` Memory (content, embedding) |

### Retrieval Pipeline
```
Query
 │
 ▼
┌─────────────────────────────────────┐
│ M5 RetrievalService.search()        │
│                                     │
│ 1. BM25 keyword search              │
│    - Full-text on memories.content   │
│    - Scoped by tenant_id/workspace_id│
│    - Filtered by temporal_status     │
│                                     │
│ 2. Semantic search (optional)        │
│    - Query embedding generated       │
│    - Cosine similarity against       │
│      Memory.embedding vectors        │
│                                     │
│ 3. Reranking                         │
│    - Combine BM25 + semantic scores  │
│    - Weight by confidence/authority  │
│                                     │
│ 4. Deduplication                     │
│    - Collapse similar results        │
│                                     │
│ 5. Conflict detection                │
│    - Surface contradictory facts     │
│                                     │
│ 6. Return ranked results             │
│    - With provenance metadata        │
└─────────────────────────────────────┘
```

### Retrieval Parameters
| Parameter | Purpose |
|-----------|---------|
| query | User's search query |
| workspace_id | Scope to workspace |
| project_id | Scope to project (optional) |
| limit | Max results |
| include_superseded | Include temporal_status=superseded |
| semantic | Enable semantic search (requires embeddings) |

### Scoring Factors
1. **BM25 score** — Keyword relevance
2. **Semantic similarity** — Embedding cosine similarity (if enabled)
3. **Confidence** — Memory confidence score (weighting factor)
4. **Authority** — Memory authority score (weighting factor)
5. **Recency** — Not explicitly implemented in available code

### Evidence
- `test_m5_retrieval_returns_results` — verifies retrieval returns results
- `test_hybrid_score` — verifies scoring
- `test_search_memories` — verifies search endpoint
- `test_search_finds_golden_facts` — verifies fact discovery

---

## 9. Complete Knowledge Lifecycle

```
RAW CONVERSATION (JSON/JSONL, document)
 │
 │ User uploads via POST /api/v1/ingest
 ▼
[NORMALIZATION — M0]
 │  • Parse format
 │  • Redact secrets (API keys, passwords, tokens, private keys)
 │  • Compute SHA-256 content hash
 │  • Deduplicate (skip if hash exists)
 ▼
SOURCE RECORD (sources table)
 NORMALIZED MESSAGES (normalized_messages table)
 │
 │ Pipeline continues
 ▼
[SESSION UNDERSTANDING — M1]
 │  • Identify exchanges (user↔assistant pairs)
 │  • Preserve conversation context
 │  • Link to Session record
 ▼
SESSION (sessions table)
 MESSAGES (messages table)
 │
 │ Intelligence extraction
 ▼
[FACT & DECISION EXTRACTION — M2]
 │  • Regex pattern matching for subject-predicate-object
 │  • Decision pattern matching
 │  • Assign confidence (0.0–1.0)
 │  • Assign authority (0.0–1.0)
 ▼
FACTS (facts table)
 DECISIONS (decisions table)
 │
 │ Temporal processing
 ▼
[TEMPORAL TRUTH — M3]
 │  • Assign temporal_status (current/superseded/historical)
 │  • Detect contradictions (same subject+predicate, different objects)
 │  • Supersede older facts (set superseded_by_id)
 │  • Mark stale knowledge
 ▼
VERSIONED FACTS & DECISIONS
 │
 │ Graph construction
 ▼
[KNOWLEDGE GRAPH — M4]
 │  • Create GraphNode for entities
 │  • Create GraphEdge for relationships
 │  • Link to Source for provenance
 │  • Assign confidence to edges
 ▼
GRAPH NODES & EDGES
 │
 │ Indexing (M5 is query-time, not batch)
 ▼
[INDEXED KNOWLEDGE — PostgreSQL]
 │  • All tables populated
 │  • Indexes built
 │  • Ready for retrieval
 ▼
[RETRIEVAL — M5 (query-time)]
 │  • User asks question via chat or search
 │  • BM25 + semantic search on memories
 │  • Rerank by confidence/authority
 │  • Deduplicate
 │  • Detect conflicts
 ▼
RANKED MEMORIES WITH PROVENANCE
 │
 │ Chat response
 ▼
[LLM GROUNDING]
 │  • Context pack built (bounded memories + provenance)
 │  • Sent to LLM (Anthropic/OpenAI)
 │  • Response streamed via SSE
 ▼
RESPONSE
 │  • Assistant message stored
 │  • MessageProvenance recorded
 │    (model, provider, memory_ids, sources, tokens, latency)
 ▼
EVIDENCE-BACKED ANSWER
 │
 │ User can trace:
 ▼
ANSWER → MEMORY → FACT/DECISION → SOURCE → ORIGINAL CONVERSATION
```

---

## 10. Memory Types

| Type | Description | Default |
|------|-------------|---------|
| procedural_memory | How-to knowledge, processes, procedures | Yes (default) |
| declarative_memory | Factual knowledge, facts, data | No |
| episodic_memory | Event-based knowledge, conversations | No |
| semantic_memory | Conceptual knowledge, relationships | No |

**Evidence:** `app/models.py:250` — `memory_type: Mapped[str] = mapped_column(String(50), default="procedural_memory")`

**Note:** The type system exists in the schema but the current implementation uses only the default `procedural_memory`. Other types are NOT ESTABLISHED IN AVAILABLE SOURCE as actively used.

---

## 11. Authority & Confidence

### Confidence (0.0–1.0)
- Represents extraction certainty
- Set by M2 extraction (default 1.0 for pattern-matched, 0.7 for memories)
- Used in M5 retrieval ranking

### Authority (0.0–1.0)
- Represents source trustworthiness
- Default 1.0 (maximum trust)
- Could be adjusted based on source quality

### Usage in Retrieval
Both scores factor into M5 ranking:
- Higher confidence → higher rank
- Higher authority → higher rank

---

## 12. Provenance in the Knowledge Lifecycle

Every piece of knowledge carries its provenance chain:
```
Memory
 └─▶ source_id → Source
      └─▶ workspace_id → Workspace → Tenant
      └─▶ project_id → Project
      └─▶ normalized_messages → NormalizedMessage[]
           └─▶ source_id (circular reference)

Fact
 └─▶ source_id → Source
      └─▶ provenance chain above

Decision
 └─▶ source_id → Source
      └─▶ provenance chain above

GraphEdge
 └─▶ source_id → Source
      └─▶ provenance chain above

ChatResponse (MessageProvenance)
 └─▶ memory_ids_used → Memory[]
 └─▶ retrieval_sources → detailed source metadata
 └─▶ user_message_id → Message
 └─▶ assistant_message_id → Message
```

---

## 13. Key Differences: Memory vs. Fact vs. Decision

| Dimension | Memory | Fact | Decision |
|-----------|--------|------|----------|
| Created by | User, agent, ingestion | M2 extraction | M2 extraction |
| Structure | Free text | Subject-predicate-object | Statement + context |
| Scoring | confidence, authority | confidence, authority | confidence, authority |
| Temporal | temporal_status | temporal_status, superseded_by_id | temporal_status, superseded_by_id |
| Provenance | source_id, session_id, user_id | source_id | source_id |
| Graph | Not in graph | Can become graph nodes | Can become graph nodes |
| Retrieval | BM25 + semantic | Via memory search | Via memory search |

---

## 14. Implementation Notes

### M0 Secret Redaction
The M0 normalization step (in `connectors.py`) redacts:
- API keys (various formats: `api_key=...`, `API_KEY: ...`, etc.)
- Passwords
- Bearer/JWT tokens
- Private key blocks (RSA, EC, PKCS#8)
- Database URLs
- Generic credential patterns

Redacted content is replaced with `[REDACTED]`.

### M5 is Query-Time, Not Batch
Unlike M0–M4 which run during ingestion, M5 operates at query time:
- No separate indexing step
- BM25 search runs against PostgreSQL `memories.content`
- Semantic search requires pre-computed embeddings in `memories.embedding`
- Reranking happens per-query

### Embeddings
- Stored as JSON array in `memories.embedding`
- Optional — not all memories have embeddings
- Used for semantic similarity search in M5
- Embedding model NOT ESTABLISHED IN AVAILABLE SOURCE (which model generates embeddings)

### No Background Workers
The entire M0–M5 pipeline runs synchronously within the API request context. There is no task queue, no worker process, no background job system. This means:
- Ingestion blocks the HTTP response until complete
- Large files may cause timeouts
- No retry mechanism for failed pipeline stages (except at the job level via IngestJob.status)
