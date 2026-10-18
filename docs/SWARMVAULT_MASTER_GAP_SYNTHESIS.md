# SwarmVault Master Gap Synthesis

**Purpose**: Unified cross-reference of all architectural gap analyses.
**Forensic status**: Source-first. All claims traced to actual implementation.
**Created**: 2026-09-10

---

## 1. Document Index

| Document | Scope |
|----------|-------|
| `SWARMVAULT_TEMPORAL_SUPERSESSION_GAP_ANALYSIS.md` | M3 temporal processing, supersession, contradiction detection, audit gaps |
| `SWARMVAULT_RETRIEVAL_GAP_ANALYSIS.md` | M5 retrieval architecture, memory model visibility, semantic search, graph traversal |
| `SWARMVAULT_INGESTION_AGENT_INTEGRATION_GAP_ANALYSIS.md` | Background ingestion, IngestJob processing, external agent integration, connectors, SSE |
| `SWARMVAULT_CLOUD_SCALE_STATE_GAP_ANALYSIS.md` | Horizontal scaling, distributed state, rate limiting, transaction atomicity, observability |
| `SWARMVAULT_SECURITY_RBAC_GAP_ANALYSIS.md` | RBAC enforcement gaps, policy engine gaps, auth bypass risks, input validation |

---

## 2. Cross-Gap Interaction Map

### 2.1 How Gaps Compound

```
CLOUD SCALE                    INGESTION                    TEMPORAL                    RETRIEVAL
─────────────────              ─────────────────           ─────────────────           ─────────────────
No distributed rate limiter    No background worker         No supersession FK          Memory model not in M5
  → ingestion DDoS possible      → sync HTTP blocking         → no lineage tracking       → persistent memory
  → per-instance limits          → no retry                   → contradictions visible     invisible to retrieval
                                 → no progress tracking       → no audit trail            → keyword-only search

No graceful shutdown            IngestJob never               No graph temporal           No graph-neighbor
  → orphaned pipeline state      processed                     propagation                 traversal
  → partial writes on kill       → stale IngestJob records     → stale graph edges         → flat retrieval only

No distributed cache            Markdown connector            No retraction               No semantic/embedding
  → memory cache not shared      incomplete                    mechanism                   retrieval
  → cold starts per instance     → markdown ingestion broken   → no correction path        → no semantic match

No circuit breaker              Two divergent retrieval        Recency score ignores       No retrieval
  → LLM outage = total           services                      temporal_status             explainability
    chat failure                  → inconsistent results        → historical facts rank     → factor breakdown
                                                               high if recently created    not returned
```

### 2.2 Critical Path Dependencies

**Persistent Memory depends on ALL of these being resolved**:
1. Ingestion must be atomic (cloud scale: transaction rollback) → prevents orphaned memory records
2. Memory model must be retrievable (retrieval: M5 gap) → otherwise memory is write-only
3. Supersession must be tracked (temporal: FK fields) → otherwise lineage is lost
4. Background worker must exist (ingestion: IngestJob gap) → otherwise ingestion blocks retrieval

**Memory Intelligence depends on ALL of these being resolved**:
1. Semantic retrieval must exist (retrieval: embedding gap) → otherwise intelligence is keyword-only
2. Graph-neighbor traversal must exist (retrieval: graph gap) → otherwise reasoning is flat
3. Contradiction detection must exist (temporal: detection gap) → otherwise intelligence cannot resolve conflicts
4. Retrieval explainability must exist (retrieval: factor gap) → otherwise intelligence cannot audit its reasoning
5. RBAC must be enforced at all gates (security: RBAC gap) → otherwise intelligence can access unauthorized data

---

## 3. Unified Gap Register

| # | Gap | Source Document | Severity | Blocks Persistent Memory | Blocks Memory Intelligence | Blocks Scale |
|---|-----|----------------|----------|--------------------------|----------------------------|-------------|
| 1 | Memory model not in M5 retrieval | RETRIEVAL | CRITICAL | YES | YES | NO |
| 2 | No background ingestion worker | INGESTION | CRITICAL | YES | YES | YES |
| 3 | No semantic/embedding retrieval | RETRIEVAL | HIGH | NO | YES | NO |
| 4 | No contradiction detection | TEMPORAL | HIGH | YES | YES | NO |
| 5 | No `supersedes` FK on Fact/Decision | TEMPORAL | HIGH | YES | YES | NO |
| 6 | Two divergent retrieval services | RETRIEVAL | HIGH | YES | YES | NO |
| 7 | No distributed rate limiting | CLOUD SCALE | HIGH | NO | NO | YES |
| 8 | IngestJob never processed | INGESTION | HIGH | YES | YES | YES |
| 9 | No transaction rollback on pipeline failure | CLOUD SCALE | HIGH | NO | YES | NO |
| 10 | No graph temporal propagation | TEMPORAL | MEDIUM | YES | YES | NO |
| 11 | No graph-neighbor traversal in M5 | RETRIEVAL | MEDIUM | PARTIAL | YES | NO |
| 12 | No retrieval explainability in API | RETRIEVAL | MEDIUM | NO | YES | NO |
| 13 | No Decision supersession/dedup | TEMPORAL | MEDIUM | YES | YES | NO |
| 14 | No version numbering | TEMPORAL | MEDIUM | PARTIAL | YES | NO |
| 15 | No retraction mechanism | TEMPORAL | MEDIUM | PARTIAL | YES | NO |
| 16 | No supersession audit event | TEMPORAL | MEDIUM | PARTIAL | YES | NO |
| 17 | No WebSocket / bidirectional streaming | INGESTION | MEDIUM | NO | NO | NO |
| 18 | No circuit breaker on LLM calls | CLOUD SCALE | MEDIUM | NO | PARTIAL | YES |
| 19 | No graceful shutdown | CLOUD SCALE | MEDIUM | NO | NO | YES |
| 20 | No policy engine refresh | CLOUD SCALE | MEDIUM | PARTIAL | PARTIAL | YES |
| 21 | No distributed cache | CLOUD SCALE | MEDIUM | NO | NO | YES |
| 22 | Historical facts not filtered at retrieval | RETRIEVAL | MEDIUM | PARTIAL | YES | NO |
| 23 | No temporal context in LLM prompt | TEMPORAL | MEDIUM | NO | YES | NO |
| 24 | Soft-delete vs temporal_status ambiguity | TEMPORAL | MEDIUM | PARTIAL | YES | NO |
| 25 | No Markdown connector completion | INGESTION | MEDIUM | NO | NO | NO |
| 26 | No OpenAI provider / provider fallback | INGESTION | MEDIUM | NO | PARTIAL | NO |
| 27 | No MCP / Codex / Universal Adapter impl | INGESTION | LOW | NO | NO | NO |
| 28 | No metrics export | CLOUD SCALE | LOW | NO | NO | PARTIAL |
| 29 | No distributed tracing | CLOUD SCALE | LOW | NO | NO | PARTIAL |
| 30 | Hardcoded connector size limits | INGESTION | LOW | NO | NO | NO |

---

## 4. P0 — Must Fix Before Any Memory Intelligence

| # | Gap | Why P0 |
|---|-----|--------|
| 1 | Memory model not in M5 | Persistent memory is write-only without retrieval |
| 2 | No background ingestion worker | Blocks async processing, retry, progress tracking |
| 3 | No semantic retrieval | Memory intelligence cannot match semantically similar queries |
| 4 | No contradiction detection | Intelligence layer cannot reason over conflicting facts |
| 5 | No `supersedes` FK | No lineage, no rollback, no trust in temporal transitions |
| 6 | Two divergent retrieval services | Inconsistent results between streaming and non-streaming chat |
| 7 | No transaction rollback | Partial pipeline failure creates orphaned memory records |

## 5. P1 — Must Fix Before Persistent Memory is Trustworthy

| # | Gap | Why P1 |
|---|-----|--------|
| 8 | No graph temporal propagation | Stale graph edges mislead retrieval and visualization |
| 9 | No graph-neighbor traversal | Intelligence layer cannot reason over relationships |
| 10 | No Decision supersession | Duplicate decisions accumulate without dedup |
| 11 | No version numbering | Cannot express fact versioning or rollback |
| 12 | No supersession audit event | Cannot reconstruct temporal transitions |
| 13 | No graceful shutdown | Orphaned state on deploy/restart |
| 14 | No distributed rate limiting | Concurrent instances allow unlimited requests |
| 15 | No circuit breaker on LLM | LLM outage = total chat failure |

## 6. P2 — Should Fix for Operational Maturity

| # | Gap | Why P2 |
|---|-----|--------|
| 16 | No policy engine refresh | Stale policies across rolling deployments |
| 17 | No retrieval explainability | Cannot debug or audit retrieval quality |
| 18 | No retraction mechanism | Cannot express "this fact was wrong" |
| 19 | No WebSocket streaming | No bidirectional real-time channel |
| 20 | No connection pool tuning | Unpredictable behavior under concurrent load |
| 21 | No idempotency keys | Retry creates duplicate records |
| 22 | Historical facts not filtered | Confusing search results with mixed temporal states |

## 7. P3 — Nice to Have

| # | Gap | Why P3 |
|---|-----|--------|
| 23 | No metrics export | No operational visibility |
| 24 | No distributed tracing | No cross-service request tracing |
| 25 | No Markdown connector completion | Low usage format |
| 26 | No MCP/Codex integration | Future integration, not blocking |
| 27 | Hardcoded connector limits | Configurable but not urgent |
| 28 | No OpenAI provider fallback | Anthropic works; fallback is enhancement |

---

## 5. Next Memory Intelligence Layer — Readiness Boundary

### 5.1 What the Current System Can Safely Provide TODAY

| Capability | Ready? | Evidence |
|------------|--------|----------|
| Fact storage with confidence + authority | YES | `app/models.py:Fact`, `pipeline.py` |
| Decision storage with confidence + authority | YES | `app/models.py:Decision`, `pipeline.py` |
| Temporal status (current/historical) | PARTIAL | Fact/Decision have `temporal_status`; supersession works for subject+predicate matches only |
| Graph nodes and edges | YES | `app/models.py:GraphNode/GraphEdge`, `m4_graph.py` |
| Provenance chain (retrieval) | PARTIAL | `MessageProvenance` tracks retrieval sources; supersession provenance missing |
| Audit events | PARTIAL | Ingest events logged; supersession events missing |
| Soft deletion | YES | `deleted_at` on all major models |
| Multi-factor retrieval scoring | YES | `m5_retrieval.py` — keyword, recency, authority, confidence, temporal, graph |
| Content-hash deduplication | YES | `ingest.py` — SHA-256 content hash |
| Scope isolation (workspace/project) | YES | `TenantContext` middleware, workspace_id on all models |
| RBAC authorization | PARTIAL | `require_min_role` middleware; policy engine exists but refresh gap |
| LLM-grounded chat | YES | `chat_orchestrator.py` — M5 retrieval → LLM → provenance |

### 5.2 What the Next Layer Can Trust

The Memory Intelligence Layer can safely consume:
- **Fact content, confidence, authority** — these are stored and persisted
- **Decision content, confidence, authority** — same
- **Graph topology** — nodes and edges are persisted with workspace isolation
- **Retrieval scores** — M5 multi-factor scoring is functional
- **Provenance for retrieval** — `MessageProvenance` records which memories were used
- **Source metadata** — `Source` model tracks ingestion origin, content hash, status
- **Session context** — `Session` model links facts/decisions to conversation sessions
- **Temporal status (current)** — for facts that have not been superseded

### 5.3 What the Next Layer MUST NOT Assume

The Memory Intelligence Layer **must not** assume:

1. **Complete temporal lineage**: No `supersedes` FK means the chain from fact A → fact B → fact C is not programmatically traceable. The layer cannot ask "what did we believe before this?"
2. **Contradiction-free facts**: Two current facts can contradict each other. The layer cannot assume consistency.
3. **All memory types are retrievable**: The `Memory` model (Sprint 8) is write-only from M5's perspective. User-created memories are invisible to retrieval.
4. **Semantic matching**: Retrieval is keyword-only. "PostgreSQL" and "our database" are not matched.
5. **Graph-complete retrieval**: Graph edges are counted in scoring but not traversed. Connected facts are not automatically included.
6. **Temporal accuracy in LLM prompts**: The LLM receives facts without temporal annotation. It cannot distinguish current from historical.
7. **Atomic ingestion**: Partial pipeline failures leave orphaned records. The layer cannot assume all facts in a workspace are valid.
8. **Consistent retrieval across channels**: Streaming and non-streaming chat use different retrieval services.
9. **Global rate limiting**: Rate limits are per-instance. The layer cannot assume a fixed global QPS ceiling.
10. **Policy consistency**: Policies are loaded once at startup. Rolling deployments serve stale policies until restart.

### 5.4 Required Contracts Before Implementation

The following contracts must exist before the Memory Intelligence Layer can be implemented safely:

| Contract | Required By | Blocks |
|----------|-------------|-------|
| Unified retrieval interface (M5 + Memory model) | Gap #1 | All intelligence retrieval |
| Semantic embedding interface | Gap #3 | Semantic reasoning |
| Supersession lineage API (`supersedes`/`superseded_by`) | Gap #5 | Temporal reasoning |
| Contradiction detection API | Gap #4 | Conflict resolution |
| Graph traversal API (neighbor expansion) | Gap #11 | Relational reasoning |
| Retrieval explainability API (factor breakdown) | Gap #12 | Auditable reasoning |
| Temporal context in LLM prompt contract | Gap #23 | Temporally-aware responses |
| Atomic ingestion guarantee | Gap #9 | Data trust |
| Background ingestion contract (status/progress) | Gap #2 | Async intelligence |
| Policy refresh contract | Gap #20 | Consistent authorization |

---

## 6. Remediation Priority Summary

```
P0 (blocks everything):
├── [1] Include Memory model in M5 retrieval
├── [2] Implement background ingestion worker
├── [3] Add semantic/embedding retrieval
├── [4] Implement contradiction detection
├── [5] Add supersedes FK on Fact/Decision
├── [6] Unify retrieval services (streaming + non-streaming)
└── [7] Add transaction rollback for pipeline failures

P1 (blocks persistent memory trust):
├── [8] Propagate temporal status to graph edges
├── [9] Add graph-neighbor traversal to M5
├── [10] Implement Decision supersession/dedup
├── [11] Add version numbering to Fact/Decision
├── [12] Add supersession audit events
├── [13] Implement graceful shutdown
├── [14] Add distributed rate limiting
└── [15] Add circuit breaker for LLM calls

P2 (operational maturity):
├── [16] Add policy engine refresh mechanism
├── [17] Return retrieval factor breakdown in API
├── [18] Add fact retraction mechanism
├── [19] Add WebSocket streaming option
├── [20] Tune database connection pool
├── [21] Add idempotency keys to ingestion
└── [22] Filter historical facts by default in search

P3 (enhancement):
├── [23] Add metrics export (Prometheus)
├── [24] Add distributed tracing (OpenTelemetry)
├── [25] Complete Markdown connector
├── [26] Implement MCP/Codex adapters
├── [27] Make connector limits configurable
└── [28] Add OpenAI provider with fallback
```

---

## 7. Traceability to Source

| Gap Category | Primary Source Files |
|-------------|---------------------|
| Temporal/Supersession | `app/services/pipeline.py`, `app/services/m3_temporal.py`, `app/models.py` |
| Retrieval | `app/services/m5_retrieval.py`, `app/services/retrieval.py`, `app/services/chat_orchestrator.py` |
| Ingestion/Integration | `app/api/ingest.py`, `app/services/connectors.py`, `app/services/llm.py`, `app/services/memory.py` |
| Cloud Scale | `app/db.py`, `app/main.py`, `app/middleware/rate_limit.py`, `app/services/policy/engine.py` |
| Security/RBAC | `app/middleware/auth.py`, `app/middleware/rbac.py`, `app/services/policy/engine.py`, `app/core/security.py`, `app/models.py` |
