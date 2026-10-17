# SwarmVault Retrieval Architecture Gap Analysis

**Forensic status**: Source-first. Every claim traced to actual implementation.
**Created**: 2026-09-10

---

## 1. Executive Summary

SwarmVault's M5 retrieval (`app/services/m5_retrieval.py`) is a multi-factor scoring system that operates **only on `Fact` and `Decision` database rows**. It does not retrieve `Memory` model records, does not use vector embeddings, does not traverse graph neighbors, and does not surface `Source` provenance records at query time. Additionally, freshly created facts are not immediately queryable within the same pipeline transaction.

| Dimension | Status |
|-----------|--------|
| Fact retrieval (M5) | IMPLEMENTED |
| Decision retrieval (M5) | IMPLEMENTED |
| Memory model retrieval | MISSING from M5 |
| Semantic / embedding retrieval | MISSING |
| Graph-neighbor retrieval | MISSING |
| Fresh fact visibility within same transaction | GAP |
| Retrieval explainability | PARTIAL |
| Retrieval caching | MISSING |
| Retrieval observability | PARTIAL |
| Cross-session retrieval | PARTIAL |
| Provenance chain in retrieval output | PARTIAL |
| Temporal filtering at retrieval time | PARTIAL |

---

## 2. M5 Architecture (What Exists)

### 2.1 File: `app/services/m5_retrieval.py`

M5 implements two retrieval functions:

**`rank_facts()`** (lines 65-105):
- Queries all `Fact` rows for the workspace (with optional project filter)
- Loads up to `limit * 3` candidates into memory
- Scores each using 6 factors: keyword (BM25-inspired), recency, authority, confidence, temporal_status, graph connectivity
- Weights: keyword 25%, recency 15%, authority 15%, confidence 15%, temporal 20%, graph 10%
- Returns top `limit` results

**`rank_decisions()`** (lines 108-150):
- Same pattern as `rank_facts` but with temporal weight 30% (decisions are more time-sensitive)
- No graph factor (decisions have no graph edges)

**`retrieve_hybrid()`** (lines 153-180):
- Calls both rankers and merges by final score
- Returns combined sorted list

**`retrieve_for_chat()`** (lines 183-220):
- Calls `retrieve_hybrid`
- Formats results into context string: `[FACT] content` or `[DECISION] content`
- Builds provenance chain with source_id, session_id, temporal_status, confidence, score

### 2.2 Retrieval Used By

| Consumer | File | Function Called |
|----------|------|----------------|
| Chat (non-streaming) | `app/services/chat_orchestrator.py` | `retrieve_for_chat()` |
| SSE chat stream | `app/api/chat.py` | `retrieve_memories()` (different service) |
| Search API | `app/api/ingest.py` | `retrieve_hybrid()` |
| Timeline API | `app/api/ingest.py` | Direct DB queries (not M5) |

---

## 3. Critical Gaps

### 3.1 Memory Model Not Retrievable via M5

**Evidence**: `retrieve_hybrid()` in `m5_retrieval.py` only queries `Fact` and `Decision`. The `Memory` model (Sprint 8) is never included.

**Evidence**: The code contains a comment acknowledging this:
```python
# Note: Memory model has no deleted_at column, so memory ranking
# is deferred until that model is updated.
```

**Impact**: User-created memories (WORKING, EPISODIC, SEMANTIC types) are stored in PostgreSQL but **never surfaced by M5 retrieval**. They are invisible to chat context and search.

**Impact for persistent memory**: The entire Memory Service layer (Sprint 8) writes to a table that M5 cannot read. Persistent memory is write-only from a retrieval perspective.

### 3.2 Two Different Retrieval Services

**Evidence**: `app/api/chat.py` imports `from app.services.retrieval import retrieve_memories` for the SSE stream, while `app/services/chat_orchestrator.py` imports `from app.services.m5_retrieval import retrieve_for_chat` for non-streaming chat.

**Evidence**: `app/services/retrieval.py` exists as a separate file from `app/services/m5_retrieval.py`.

**Gap**: Two retrieval paths exist. They may return different results for the same query. There is no guarantee of consistency between streaming and non-streaming chat.

### 3.3 No Semantic / Embedding Retrieval

**Evidence**: No vector database, no embedding model, no embedding generation anywhere in the codebase. M5 uses only BM25-style keyword matching.

**Impact**: Retrieval cannot match semantically similar queries. "database technology" will not match "PostgreSQL" unless the exact words overlap. This is a fundamental gap for conversational memory retrieval.

### 3.4 No Graph-Neighbor Retrieval

**Evidence**: `_graph_context_score()` in `m5_retrieval.py` counts graph edges **per fact ID** as a relevance factor. It does not traverse the graph to find related facts.

**Impact**: If fact A is relevant and fact B is connected to fact A via a graph edge, fact B will not be retrieved even if it's highly relevant to the query. Retrieval is flat, not graph-aware.

### 3.5 Fresh Facts Not Visible Within Same Transaction

**Evidence**: `run_pipeline()` in `pipeline.py` creates Fact rows with `db.add(db_fact)` and `await db.flush()`. The flush makes rows visible within the transaction. However, the ingestion endpoint (`ingest.py`) commits only at the end of the HTTP request. If another concurrent request runs M5 retrieval during the same ingestion, it will not see the new facts until commit.

**Evidence**: More critically, the `IngestJob` background job system (`app/models.py` has `IngestJob` model) is never actually processed. There is no background worker. The "legacy" `/ingest/` endpoint creates `IngestJob` records that are never consumed.

**Impact**: No async ingestion. Every ingestion blocks the HTTP request for the full M0-M4 pipeline duration.

### 3.6 No Retrieval Caching

**Evidence**: `retrieve_hybrid()` executes fresh SQL queries every call. No cache layer exists between the API and the database for retrieval results.

**Impact**: Repeated identical queries hit the database. At scale, this creates unnecessary load.

### 3.7 Retrieval Explainability: Partial

**Evidence**: `retrieve_for_chat()` returns factor breakdowns in the provenance dict:
```python
provenance.append({
    "type": "fact",
    "id": str(item.id),
    "score": r.score,
})
```

But `RetrievalResult.factors` (the detailed per-factor breakdown) is **not included in the API response**. The API returns only the final score.

**Impact**: Cannot explain *why* a fact was retrieved. Cannot debug retrieval quality. Cannot tune weights based on observed behavior.

### 3.8 No Temporal Filtering at Retrieval Time

**Evidence**: `rank_facts()` and `rank_decisions()` include `temporal_status == "current"` as a scoring factor (bonus multiplier) but do not filter out historical facts. Historical facts can appear in results if they score high enough on other factors.

**Evidence**: The `/ingest/graph` endpoint has `include_historical` parameter. The search endpoint does not.

**Impact**: A user searching for "database technology" may see both the current fact ("uses PostgreSQL") and a historical fact ("uses MySQL") — with no clear visual distinction in the search results.

### 3.9 No Source Filtering at Retrieval Time

**Evidence**: M5 retrieves facts by workspace (and optionally project). It does not filter by `source_id`, `source_type`, or ingestion batch.

**Impact**: Cannot restrict retrieval to facts from trusted sources. Cannot exclude facts from a specific failed ingestion.

---

## 4. Retrieval Gap Matrix

| Gap | Severity | Blocks Persistent Memory | Blocks Memory Intelligence | Evidence |
|-----|----------|--------------------------|----------------------------|----------|
| Memory model not in M5 | CRITICAL | YES | YES | `m5_retrieval.py:retrieve_hybrid` |
| Two divergent retrieval services | HIGH | YES | YES | `chat.py`, `chat_orchestrator.py` |
| No semantic/embedding retrieval | HIGH | NO | YES | No embedding code found |
| No graph-neighbor traversal | MEDIUM | PARTIAL | YES | `m5_retrieval.py:_graph_context_score` |
| No background ingestion worker | HIGH | YES | YES | `app/api/ingest.py:legacy_start_ingest` |
| No retrieval caching | LOW | NO | NO | `m5_retrieval.py` |
| No factor breakdown in API response | MEDIUM | NO | YES | `m5_retrieval.py:retrieve_for_chat` |
| Historical facts not filtered | MEDIUM | PARTIAL | YES | `m5_retrieval.py:rank_facts` |
| No source-level filtering | LOW | PARTIAL | PARTIAL | `m5_retrieval.py` |

---

## 5. What a Future Memory Intelligence Layer Must Not Assume

1. **Do not assume M5 returns all memory types**: Facts and decisions only. Memory model records are invisible.
2. **Do not assume semantic search exists**: Retrieval is keyword-only. A memory intelligence layer cannot rely on semantic matching.
3. **Do not assume retrieval is deterministic**: Two chat paths (streaming vs non-streaming) use different retrieval services.
4. **Do not assume graph traversal**: Graph edges are counted but not traversed at retrieval time.
5. **Do not assume fresh facts are immediately queryable**: Pipeline flush vs commit semantics matter.
6. **Do not assume retrieval factors are auditable**: Factor breakdowns are computed but not returned to callers.

---

## 6. Required Conditions Before Memory Intelligence Can Trust Retrieval

1. **Memory model must be included in M5 retrieval** — or a unified retrieval interface must abstract over all memory types.
2. **Single retrieval service** — both streaming and non-streaming chat must use the same retrieval path.
3. **Semantic/embedding layer** — either vector DB integration or LLM-based semantic scoring.
4. **Graph-neighbor expansion** — retrieve facts connected to high-scoring facts via graph edges.
5. **Temporal filtering as a first-class parameter** — callers must be able to request `current_only=true`.
6. **Retrieval explainability in API response** — factor breakdown must be returned, not just final score.
7. **Background ingestion worker** — async pipeline execution so retrieval can see fresh facts without blocking.
