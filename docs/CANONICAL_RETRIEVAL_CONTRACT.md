# Canonical Retrieval Contract
**Phase**: M-ARCH — Memory Architecture Freeze Gate
**Status**: PROPOSED — requires review and approval before implementation
**Created**: 2026-09-10

---

## 1. Purpose

This contract defines **one canonical retrieval architecture** for SwarmVault.
Currently, the codebase has **two independent retrieval implementations** that
can return different results for the same query:

| Service | File | Used By |
|---------|------|---------|
| M5 retrieval | `app/services/m5_retrieval.py` | Non-streaming chat, search API |
| Legacy retrieval | `app/services/retrieval.py` | SSE streaming chat |

This contract replaces both with a single, unified retrieval pipeline.

---

## 2. Canonical Retrieval Pipeline

```
User/Agent Query
       │
       ▼
┌─────────────────┐
│ Query Parse     │  Extract: query text, filters, scope, temporal constraints
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Authorization   │  Verify caller may search this scope
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Candidate Gen   │  Generate candidates from multiple sources in parallel
│                 │
│  ┌───────────┐  │
│  │ Lexical   │  │  BM25 keyword matching across all memory types
│  └───────────┘  │
│  ┌───────────┐  │
│  │ Semantic  │  │  Embedding similarity (when embeddings exist)
│  └───────────┘  │
│  ┌───────────┐  │
│  │ Graph     │  │  Neighbor traversal from high-scoring nodes
│  └───────────┘  │
│  ┌───────────┐  │
│  │ Temporal  │  │  Time-window filtering, recency scoring
│  └───────────┘  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Dedup           │  Remove duplicate memory_ids, keep highest-scored
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Temporal Filter │  Exclude SUPERSEDED, INVALIDATED, EXPIRED by default
│                 │  Include if include_superseded=true
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Authorization   │  Re-check per-memory access (object-level)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Rerank          │  Multi-factor scoring:
│                 │  keyword × 0.25 + semantic × 0.20 + recency × 0.15
│                 │  + authority × 0.15 + confidence × 0.10
│                 │  + temporal_bonus × 0.10 + graph × 0.05
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Evidence Select │  Select top N, include full provenance chain
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Context Pack    │  Format for LLM consumption with provenance metadata
└────────┬────────┘
         │
         ▼
   LLM / Agent
```

---

## 3. Candidate Generation

### 3.1 Lexical (BM25)

**Source**: `app/services/m5_retrieval.py:_bm25_score()`
**Scope**: All memory types (FACT, DECISION, EPISODIC, SEMANTIC, PROCEDURAL, WORKING)
**Index**: Database `ILIKE` with subject/content fields (to be replaced by full-text index)

### 3.2 Semantic (Embedding)

**Source**: Not implemented
**Scope**: All memory types with populated `embedding` column
**Index**: Vector database or pgvector
**Status**: PLANNED — `embedding` column exists on `Memory` model but is never populated

### 3.3 Graph

**Source**: Not implemented (current `_graph_context_score` counts edges but doesn't traverse)
**Scope**: Memories that are graph nodes or connected to graph nodes
**Index**: `graph_edges` table traversal
**Status**: PLANNED

### 3.4 Temporal

**Source**: `app/services/m5_retrieval.py:_recency_score()`
**Scope**: All memory types
**Index**: `created_at`, `valid_from`, `valid_until`, `temporal_status`

---

## 4. Multi-Factor Scoring

### 4.1 Current Weights (from `m5_retrieval.py`)

| Factor | Fact Weight | Decision Weight |
|--------|------------|-----------------|
| Keyword | 0.25 | 0.25 |
| Recency | 0.15 | 0.15 |
| Authority | 0.15 | 0.15 |
| Confidence | 0.15 | 0.15 |
| Temporal | 0.20 | 0.30 |
| Graph | 0.10 | 0.00 (not applied) |

### 4.2 Proposed Unified Weights

| Factor | Weight | Notes |
|--------|--------|-------|
| Semantic similarity | 0.25 | When embeddings available; falls back to keyword |
| Keyword relevance | 0.20 | BM25 or full-text |
| Recency | 0.15 | Exponential decay, 30-day half-life |
| Authority | 0.15 | Source authority score |
| Confidence | 0.10 | Extraction/creation confidence |
| Temporal status | 0.10 | CURRENT=1.0, SUPERSEDED=0.3, INVALIDATED=0.0 |
| Graph connectivity | 0.05 | Number of connected edges (log-scaled) |

**Change**: Semantic factor replaces keyword as primary when embeddings exist.
Graph factor reduced from 0.10 to 0.05 (neighbor expansion handled in candidate gen, not scoring).

---

## 5. Retrieval Scope

### 5.1 Memory Types Included

| Memory Type | Currently Retrieved | Contract Requirement |
|-------------|---------------------|---------------------|
| FACT | YES (via M5) | YES |
| DECISION | YES (via M5) | YES |
| EPISODIC | NO | YES |
| SEMANTIC | NO | YES |
| PROCEDURAL | NO | YES |
| WORKING | NO | YES (with expiry filter) |

### 5.2 Temporal Filtering

| Parameter | Default | Description |
|-----------|---------|-------------|
| `include_superseded` | false | Include SUPERSEDED memories |
| `include_invalidated` | false | Include INVALIDATED memories |
| `include_expired` | false | Include EXPIRED memories |
| `include_archived` | false | Include ARCHIVED memories |
| `include_deleted` | false | Include DELETED (admin only) |
| `min_trust_level` | UNVERIFIED | Minimum trust level required |
| `min_confidence` | 0.0 | Minimum confidence threshold |
| `min_authority` | 0.0 | Minimum authority threshold |
| `temporal_window` | null | Restrict to memories within time window |

---

## 6. Context Pack Format

The retrieval result MUST include a formatted context pack for LLM consumption:

```json
{
  "query": "original query string",
  "memories": [
    {
      "memory_id": "uuid",
      "memory_type": "FACT",
      "content": "fact content",
      "temporal_status": "CURRENT",
      "confidence": 0.9,
      "authority": 0.8,
      "score": 0.85,
      "provenance": {
        "source_type": "conversation",
        "source_id": "uuid",
        "extracted_at": "2026-09-10T..."
      }
    }
  ],
  "context_text": "[FACT] Database uses PostgreSQL\n[DECISION] Chose PostgreSQL for ACID compliance\n",
  "total_candidates": 150,
  "returned": 10,
  "filtered_by_temporal": 23,
  "filtered_by_scope": 0,
  "latency_ms": 45
}
```

---

## 7. Retrieval Explainability

Every retrieval result MUST include a factor breakdown for each returned memory:

```json
{
  "factors": {
    "semantic": 0.82,
    "keyword": 0.65,
    "recency": 0.91,
    "authority": 0.80,
    "confidence": 0.70,
    "temporal": 1.0,
    "graph": 0.30
  },
  "final_score": 0.78
}
```

**Current gap**: Factor breakdowns are computed in `RetrievalResult.factors` but
not returned in API responses.

---

## 8. Single Service Requirement

The contract requires **one** retrieval service:

```python
# Canonical — replaces both m5_retrieval.py and retrieval.py
class CanonicalRetrievalService:
    async def retrieve(
        self,
        query: str,
        *,
        workspace_id: str,
        user_id: str,
        project_id: str | None = None,
        memory_types: list[MemoryType] | None = None,
        limit: int = 20,
        include_superseded: bool = False,
        include_invalidated: bool = False,
        min_confidence: float = 0.0,
        min_authority: float = 0.0,
        include_factors: bool = False,
    ) -> RetrievalResult:
        ...
```

Both streaming and non-streaming chat MUST call this service. No exceptions.

---

## 9. Current Retrieval Services — Disposition

| Service | File | Disposition |
|---------|------|-------------|
| M5 retrieval | `app/services/m5_retrieval.py` | **Merge into canonical** — scoring logic preserved |
| Legacy retrieval | `app/services/retrieval.py` | **Deprecate** — functionality absorbed into canonical |
| `retrieve_memories()` | `app/services/retrieval.py` | **Deprecate** — replace with canonical.retrieve() |
| `retrieve_for_chat()` | `app/services/m5_retrieval.py` | **Deprecate** — replace with canonical.retrieve() |
| `retrieve_hybrid()` | `app/services/m5_retrieval.py` | **Deprecate** — replace with canonical.retrieve() |

---

## 10. Implementation Requirements

| Requirement | Priority | Effort |
|-------------|----------|--------|
| Include Memory model in retrieval | P0 | MEDIUM |
| Unify retrieval into single service | P0 | MEDIUM |
| Add semantic/embedding candidate gen | P0 | HIGH |
| Add graph-neighbor candidate gen | P1 | HIGH |
| Return factor breakdown in API | P1 | LOW |
| Add temporal filtering parameters | P1 | LOW |
| Add trust level filtering | P1 | MEDIUM |
| Add context pack formatting | P1 | LOW |
| Add retrieval caching | P2 | MEDIUM |
| Add retrieval observability (latency histograms) | P2 | LOW |
