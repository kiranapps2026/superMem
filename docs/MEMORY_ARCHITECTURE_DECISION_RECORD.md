# Memory Architecture Decision Record
**Phase**: M-ARCH — Memory Architecture Freeze Gate
**Status**: FROZEN — awaiting formal approval
**Created**: 2026-09-10

---

## 1. Decision Summary

This record captures the **binding architectural decisions** for SwarmVault's
memory layer, made during the M-ARCH freeze gate. These decisions are
**immutable without a new architectural review**.

---

## 2. Decisions

### DECISION-001: Canonical Memory Object

**Decision**: All knowledge in SwarmVault is represented as a single canonical
`Memory` object, with `memory_type` as a discriminator for semantic flavor.

**Alternatives considered**:
- A: Separate tables for Facts, Decisions, and Memories (current state)
- B: Single unified `memories` table with type discriminator (chosen)
- C: Document-store approach (MongoDB-style)

**Rationale for B**:
- Unified retrieval is impossible with separate tables (current gap)
- Single table simplifies consistency, indexing, and migration
- `memory_type` discriminator preserves type semantics without schema proliferation
- `extra_metadata` JSON column handles type-specific fields

**Consequences**:
- Data migration required: merge `facts` and `decisions` into `memories`
- All queries must filter by `memory_type`
- Index strategy changes (composite indexes on `(workspace_id, memory_type, temporal_status)`)

---

### DECISION-002: Lifecycle ≠ Knowledge Validity ≠ Trust

**Decision**: `status` (lifecycle), `temporal_status` (knowledge validity), and
`trust_level` (trust) are **three independent dimensions**.

**Alternatives considered**:
- A: Single `status` field encoding all three dimensions (current — conflated)
- B: Three independent dimensions (chosen)
- C: Two dimensions (lifecycle + combined validity/trust)

**Rationale for B**:
- A memory can be DELETED (lifecycle) while still being CURRENT (valid when it existed)
- A memory can be SUPERSEDED (invalidated by newer knowledge) while still being ACTIVE (not deleted)
- A memory can be VERIFIED (trusted) while being EXPIRED (time-limited)
- These dimensions are orthogonal and must be queryable independently

**Consequences**:
- All queries must specify which dimension they filter on
- UI must display three independent status indicators
- Audit events must record all three dimensions on every transition

---

### DECISION-003: Single Retrieval Service

**Decision**: Replace `m5_retrieval.py` and `retrieval.py` with one canonical
`CanonicalRetrievalService`.

**Alternatives considered**:
- A: Keep both services, add routing layer
- B: Merge into single service (chosen)
- C: Keep M5, rewrite retrieval.py to use M5

**Rationale for B**:
- Two services returning different results for the same query is unacceptable
- The divergence is a correctness bug, not a feature
- Merging preserves M5's scoring logic while adding Memory model support

**Consequences**:
- `retrieval.py` is deprecated and removed
- Both streaming and non-streaming chat use the same retrieval path
- Retrieval results are deterministic for the same query/state

---

### DECISION-004: Memory Model Included in Retrieval

**Decision**: M5 retrieval MUST query the `Memory` model in addition to `Fact`
and `Decision`.

**Alternatives considered**:
- A: Keep retrieval limited to Fact + Decision
- B: Add Memory model to retrieval (chosen)
- C: Create separate retrieval path for Memory

**Rationale for B**:
- Memory model is write-only without retrieval — violates the canonical contract
- User-created and agent-created memories must be retrievable
- Single retrieval service must cover all memory types

**Consequences**:
- `retrieve_hybrid()` queries three tables instead of two
- Memory model requires `deleted_at` column (currently missing)
- Embedding support needed for semantic retrieval of free-form content

---

### DECISION-005: Semantic Retrieval Required

**Decision**: SwarmVault MUST implement embedding-based semantic retrieval
alongside keyword (BM25) retrieval.

**Alternatives considered**:
- A: Keyword-only retrieval (current)
- B: Add semantic retrieval as primary, keyword as fallback (chosen)
- C: Hybrid scoring (both always active)

**Rationale for B**:
- Keyword-only cannot match semantically similar queries ("database" vs "PostgreSQL")
- Memory Intelligence requires semantic understanding
- LLM-grounded chat quality depends on semantic retrieval

**Consequences**:
- Embedding model must be selected and integrated
- Vector storage required (pgvector or external vector DB)
- All memory content must be embedded on creation
- Embedding dimension must be fixed and documented

---

### DECISION-006: Background Ingestion Required

**Decision**: Async background ingestion (task queue) is required before the
Memory Intelligence Layer can be implemented.

**Alternatives considered**:
- A: Keep synchronous HTTP ingestion (current)
- B: Add background task queue (chosen)
- C: Add async HTTP (fire-and-forget without queue)

**Rationale for B**:
- Synchronous ingestion blocks HTTP for pipeline duration (can be minutes)
- No retry, no progress tracking, no batch processing without a queue
- Intelligence layer needs reliable ingestion independent of HTTP request lifecycle

**Consequences**:
- Task queue dependency (Celery, RQ, or Dramatiq)
- Message broker dependency (Redis or equivalent)
- IngestJob model becomes functional (currently unused)
- API returns job ID immediately; client polls for status

---

### DECISION-007: Supersession Creates Linked Chain

**Decision**: When memory B supersedes memory A, both records MUST be updated
with FK links (`A.superseded_by = B`, `B.supersedes = A`).

**Alternatives considered**:
- A: Mark old as historical, create new with no link (current — broken)
- B: FK links in both directions (chosen)
- C: Only forward link (new → old)

**Rationale for B**:
- Forward-only links require table scans to find latest version
- Bidirectional links enable "what superseded this?" and "what did this supersede?"
- FK constraints ensure referential integrity

**Consequences**:
- `supersedes` column must be added to `memories` table
- FK constraints enforce no orphaned supersession links
- Circular supersession detection required

---

### DECISION-008: Universal Agent Event Format

**Decision**: All external agents MUST emit events in the `UniversalAgentEvent`
format before ingestion into SwarmVault.

**Alternatives considered**:
- A: Each agent has its own connector (current — fragmented)
- B: Agents emit canonical format, connectors validate (chosen)
- C: Agents write directly to API endpoints

**Rationale for B**:
- Prevents each integration from inventing its own semantics
- Connectors become validators, not transformers
- Future agents only need to produce canonical format

**Consequences**:
- All connectors must implement `to_universal_event()`
- New `/api/v1/agent/events` endpoint for direct event ingestion
- Schema validation on inbound events

---

### DECISION-009: Trust Level Gating for Intelligence

**Decision**: The Memory Intelligence Layer MAY only act on memories with
`trust_level ≥ VERIFIED`.

**Alternatives considered**:
- A: Intelligence layer acts on all memories (current — implicit, dangerous)
- B: Gate at VERIFIED (chosen)
- C: Gate at CERTIFIED (too restrictive)

**Rationale for B**:
- UNVERIFIED memories may be incorrect — acting on them produces unreliable intelligence
- CERTIFIED is too restrictive — most pipeline-extracted knowledge would be excluded
- VERIFIED requires corroboration or authoritative source — reasonable bar

**Consequences**:
- Trust level state machine must be implemented
- Intelligence layer must check trust level before action
- Pipeline-extracted memories start at UNVERIFIED

---

### DECISION-010: Memory Safety Gate

**Decision**: A memory becomes "persistent" (visible to intelligence layer, included
in retrieval, eligible for agent use) only after passing the Memory Safety Gate.

**Safety Gate Conditions** (all must be true):
1. `status` = ACTIVE
2. `temporal_status` = CURRENT
3. `confidence` ≥ configurable threshold (default 0.3)
4. `authority` ≥ configurable threshold (default 0.1)
5. Content passes content policy validation
6. Scope isolation verified (no cross-tenant leak)
7. Provenance chain complete

**Actionable Additional Conditions** (for autonomous agent use):
8. `trust_level` ≥ VERIFIED
9. No `contradicts` edges to CERTIFIED memories
10. Not flagged for human review

**Alternatives considered**:
- A: No gate — all memories immediately persistent (current)
- B: Minimal gate — only ACTIVE + CURRENT
- C: Full gate with all 10 conditions (chosen)

**Rationale for C**:
- Current state allows any content to become persistent memory
- Autonomous agents must not act on low-confidence or low-authority knowledge
- Provenance ensures auditability
- Trust level ensures reliability

---

## 3. Decisions Not Yet Made

| Decision | Options | Blocking |
|----------|---------|----------|
| Embedding model selection | OpenAI text-embedding-3, Cohere, open-source | P0 |
| Task queue technology | Celery, RQ, Dramatiq, ARQ | P0 |
| Vector database | pgvector, Pinecone, Weaviate, Qdrant | P0 |
| LLM provider for M1/M2 | Anthropic only, multi-provider with fallback | P1 |
| Memory retention policy | Time-based, size-based, tiered | P2 |
| Intelligence layer deployment | Co-located, separate service, serverless | P2 |

---

## 4. Decision Record Maintenance

This record is immutable without a new M-ARCH review cycle. Changes require:
1. Identification of why the original decision is insufficient
2. Analysis of migration path from old decision to new
3. Approval from all stakeholder roles (Architect, Security, Operations)
4. Documentation of the change in this record
