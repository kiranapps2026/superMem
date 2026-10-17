# SwarmVault Architecture Gaps and Memory Next Layer

**Agent 4 Final Synthesis — Gap Register and Memory Intelligence Next Layer Boundary**
Generated from source code forensics against `C:\Users\Administrator\Documents\SwarmVaultwebapp`
Classification: DOCUMENTATION ONLY — no product code was modified.

---

## 1. Contradiction Register

This register documents every instance where existing documentation, frontend code, or API contracts contradict the verified backend source code.

### 1.1 Documentation vs Code Contradictions

| # | Claim in Specialist Documents | Verified Source Code | Verdict |
|---|------------------------------|---------------------|---------|
| C1 | "Alembic migrations are present but not wired into app startup" (`app/db.py:40`) | **CONTRADICTED** — `app/main.py:169` calls `init_db()` during lifespan startup, which runs `alembic upgrade head` via `loop.run_in_executor()`. Alembic IS wired in production startup. | Specialist was wrong; migrations ARE active in production path |
| C2 | "Soft delete does not affect Message/NormalizedMessage (cascade-only)" | **PARTIALLY CORRECT** — Messages use `ondelete=CASCADE`, but NormalizedMessages also use cascade. Soft delete IS supported for both via parent deletion. | No contradiction — soft delete for Messages would leave orphaned NormalizedMessages |
| C3 | "Superseded_by_id is written by M3" | **CONTRADICTED** — Column exists on Fact and Decision, but `run_pipeline()` in `pipeline.py:117` only sets `temporal_status="historical"`. `superseded_by_id` is **never written** by any code path. | Pipeline does NOT write `superseded_by_id` |
| C4 | "Memory type is consistent across DB/schema/record/mapper" | **CONTRADICTED** — Four different defaults: DB=`"procedural_memory"`, schema=`"procedural_memory"`, MemoryRecord=`"WORKING"`, mapper→`"procedural"` | Inconsistent — these will never match in type-filtered queries |
| C5 | "Vector search uses pgvector" | **CONTRADICTED** — `Memory.embedding` column is `JSON, nullable=True` (not `Vector` type). `retrieval.py` checks for `query_embedding` but it is never provided. Vector search is architecturally impossible with current schema. | Vector search is non-functional |

### 1.2 Frontend vs API Contradictions

| # | Frontend Expectation | API Behavior | Verdict |
|---|---------------------|--------------|---------|
| F1 | `GET /api/v1/memory/search` accepts `query` parameter | API accepts query and executes memory search — **CONSISTENT** | No contradiction |
| F2 | `GET /api/v1/projects/[id]/facts` loads facts for project | API checks workspace membership, queries facts for workspace — **CONSISTENT** | No contradiction |
| F3 | `GET /api/v1/projects/[id]/decisions` loads decisions | API returns decisions with same temporal filtering — **CONSISTENT** | No contradiction |
| F4 | Sidebar shows workspace context | API resolves workspace from `X-Workspace-Id` header or JWT — **CONSISTENT** | No contradiction |

**No frontend-specific contradictions found.** The frontend consistently uses the API as documented.

### 1.3 API Contract vs Implementation Contradictions

| # | Schema/Contract | Implementation | Verdict |
|---|----------------|---------------|---------|
| A1 | `MemoryUpdate` schema allows `memory_type` update | `MemoryService.update()` ignores `memory_type` (not in the updatable fields) — **CONTRADICTION** | Client cannot update type; schema suggests they can |
| A2 | `MemorySearch` schema includes `project_id` | `MemoryService.search()` does NOT filter by `project_id` — only by `workspace_id`, `user_id`, `scope` | Scope filter is incomplete |
| A3 | `Memory.share()` endpoint exists | Does NOT actually share with a user — it updates the memory's scope/permissions in JSON only, no notification, no access grant | Name implies sharing; behavior is metadata update |
| A4 | `Memory.provenance()` endpoint returns `provenance` field | Returns `record.provenance` which is a list of dicts stored in `extra_metadata` — **CONSISTENT** | No contradiction |
| A5 | `Memory.explain()` endpoint returns factors | Returns `factor_scores` from M5 multi-factor scoring — **CONSISTENT** | No contradiction |

### 1.4 Schema vs Database Contradictions

| # | Schema | Database | Verdict |
|---|--------|----------|---------|
| S1 | `Source.source_type` enum with `chatgpt`, `openai_chat`, `openai_playground`, `claude_code` | `Source.source_type` column has no ENUM constraint (String) | Schema has enum; DB does not — schema wins |
| S2 | `Memory.memory_type` default `"procedural_memory"` | DB default is `"procedural_memory"` | Consistent — but conflicting with MemoryRecord default `"WORKING"` |
| S3 | `Fact.superseded_by_id` — UUID FK | Column exists in DB, indexed, but no FK constraint | Column exists but no referential integrity |

---

## 2. Architectural Gaps

### P0 — System-Breaking (MUST FIX before production at scale)

| ID | Gap | Evidence | Risk | Required Fix |
|----|-----|----------|------|-------------|
| P0-1 | Rate limiting is in-memory only | `app/middleware/rate_limit.py:17-30` — `_rate_limiter = RateLimiter()` module-level singleton | Multi-worker deployment means each worker has independent counters; effective rate is `N * limit` | Move to Redis-backed rate limiter |
| P0-2 | No JWT/PII redaction in error responses | `app/main.py:203-211` — `_sanitize_detail()` does NOT redact token-related fields | Error responses may leak tokens/PII in `detail` field | Add JWT token redaction to sanitizer |
| P0-3 | No circuit breaker for LLM calls | `app/services/llm.py:66-78` — timeout + retry, but retry on any `Exception` | Repeated LLM outages hammer the API with failed requests | Add circuit breaker pattern for LLM calls |

### P1 — Data Integrity (MUST FIX for memory intelligence readiness)

| ID | Gap | Evidence | Risk | Required Fix |
|----|-----|----------|------|-------------|
| P1-1 | `superseded_by_id` never written | `pipeline.py:117` — only `temporal_status` updated; `m3_temporal.py:31-56` functions never called | Cannot trace supersession chain; dead column | Write `superseded_by_id` in supersession logic; remove dead m3_temporal functions |
| P1-2 | `Memory.embedding` never populated | `app/models.py:253` — `JSON, nullable=True`; no code assigns to `memory.embedding` | Vector search claims are false | Remove embedding column or implement embedding generation |
| P1-3 | Memory provenance in JSON only | `app/services/memory.py:229-241` — stored in `extra_metadata`; not linked to `message_provenance` table | Cannot query provenance chains for memory | Add `source_id` FK to Memory + provenance table |
| P1-4 | Memory `team_id` lost during persistence | `MemoryRecord.team_id` → `extra_metadata["team_id"]` — no column exists | Data loss for team-scoped memories | Add `team_id` column to Memory table |
| P1-5 | Memory `scope` not queryable | Stored in `extra_metadata["scope"]`; only used by MemoryService.cache path | Scope enforcement fails on cache miss | Add `scope` column + query filter |

### P2 — Functionality Gaps (SHOULD FIX for production readiness)

| ID | Gap | Evidence | Risk | Required Fix |
|----|-----|----------|------|-------------|
| P2-1 | No contradiction detection | No code for detecting conflicting facts/decisions | Conflicting knowledge coexists as `current` | Add contradiction detection at M3 |
| P2-2 | No memory expiry mechanism | No `expires_at` column; no scheduled cleanup | Memory accumulation without lifecycle | Add `expires_at` + scheduled TTL task |
| P2-3 | M1 output not persisted | `pipeline.py:211-213` — returned in response, not stored | Session understanding lost after ingestion | Persist to `session_metadata` JSON column |
| P2-4 | Pipeline runs synchronously | `app/api/ingest.py:81-91` — `await pipeline.run()` | Large ingestion blocks API response | Implement async pipeline with status polling |
| P2-5 | Memory type taxonomy inconsistent | 4 different defaults across DB/schema/record/mapper | Type-filtered queries return nothing | Unify: one source of truth |
| P2-6 | Confidence/authority never calibrated | `pipeline.py:129-130` — hardcoded 0.8/0.75; Memory defaults 0.7/1.0 | All memories appear equally confident | Implement LLM or rule-based calibration at M2 |
| P2-7 | No LLM validation at ingestion | M0-M2 are entirely regex-based | False facts extracted from ambiguous text | Add optional LLM validation step |
| P2-8 | GraphNode temporal_status never transitions | No code path updates `temporal_status` from `"current"` | Graph always appears fully current | Implement temporal transitions for graph entities |
| P2-9 | `MemoryUpdate` schema allows `memory_type` but service ignores it | `memory.py:272-279` — only `content`, `metadata`, `scope` updatable | Client confusion | Either implement or remove from schema |
| P2-10 | API key expiry not enforced | `app/api/api_keys.py` — expiry tracked but never checked | Expired keys remain valid | Add expiry check to auth middleware |
| P2-11 | PolicyEngine evaluates hardcoded policies | `app/services/policy/evaluator.py:76-100` — `generate_rbac_policies()` produces policies, not loaded from DB | DB `policies` table is unused | Wire PolicyEngine to read from DB or remove DB table |

### P3 — Nice-to-Have (Improves quality but not blocking)

| ID | Gap | Evidence | Risk | Required Fix |
|----|-----|----------|------|-------------|
| P3-1 | No distributed tracing | No OpenTelemetry/Jaeger | Hard to debug multi-service flows | Add distributed tracing |
| P3-2 | No metrics endpoint | `enable_metrics=False` by default | No operational visibility | Enable and instrument metrics |
| P3-3 | SSE has no timeout | FastAPI StreamingResponse — no timeout set | Slow clients hold connections open | Add read timeout + heartbeat |
| P3-4 | Token storage in localStorage | `frontend/src/lib/api.ts` — `localStorage['sv_tokens']` | XSS vulnerability | Move to httpOnly cookie |
| P3-5 | LLM call continues after client disconnect | SSE handler — `CancelledError` not propagated to LLM | Wasted LLM tokens | Cancel LLM call on client disconnect |
| P3-6 | No graceful shutdown | `app/main.py:172` — empty yield | In-flight requests may fail on restart | Drain in-flight requests before shutdown |

---

## 3. Memory Intelligence Next Layer — Readiness Boundary

### 3.1 What the Current System Can Safely Provide

| Capability | Confidence | Notes |
|------------|-----------|-------|
| **Fact retrieval** — facts marked `temporal_status="current"` | **MEDIUM** | Regex-extracted, confidence hardcoded to 0.8, no LLM validation |
| **Decision retrieval** — decisions marked `temporal_status="current"` | **MEDIUM** | Regex-extracted, confidence hardcoded to 0.75, no LLM validation |
| **Graph topology** — nodes and edges | **LOW** | Regex-extracted, no node confidence, edges at 0.8 |
| **Memory content** — user-created memories | **LOW** | Default confidence 0.7, authority 1.0; no system calibration |
| **Provenance for chat responses** — MessageProvenance chains | **HIGH** | Complete LLM metadata, memory_ids_used, token counts |
| **Temporal awareness** — current vs historical | **PARTIAL** | Works for Facts (same subject/predicate superseded); Decisions never superseded |
| **Audit trail** — append-only event log | **HIGH** | Append-only, tenant-isolated, comprehensive event types |

### 3.2 What the Next Layer Can Trust

| Trust Dimension | What Can Be Trusted | What Cannot Be Trusted |
|----------------|-------------------|----------------------|
| **Factuality** | Facts that have NOT been superseded (current temporal_status) | Default confidence values (0.8) — not LLM-calibrated |
| **Durability** | Any DB-persisted record with `deleted_at IS NULL` | Ephemeral M1 output (not persisted) |
| **Explainability** | M5 multi-factor scoring for Facts/Decisions | Memory retrieval has no multi-factor scoring |
| **Scope** | Workspace isolation enforced at service layer | Memory scope in JSON only, not queryable |
| **Provenance** | Chat response provenance (MessageProvenance table) | Memory provenance (JSON blob in metadata) |
| **Authority** | Source-linked facts/decisions (source_id FK) | Memory has no source link |

### 3.3 What the Next Layer MUST NOT Assume

| Assumption | Why It Is Unsafe | Consequence |
|-----------|-----------------|-------------|
| `confidence` on Memory is calibrated | Defaults to 0.7; pipeline never sets it | All memories appear equally confident regardless of actual quality |
| `authority` on Memory is calibrated | Defaults to 1.0; pipeline never sets it | All memories appear equally authoritative regardless of source |
| `superseded_by_id` on Fact/Decision traces supersession | Column exists but **is never written** | Cannot trace which fact replaced which |
| Vector search returns relevant results | `Memory.embedding` is never populated | Returns empty embedding results; falls back to keyword only |
| Memory scope is enforced at DB level | Scope is in JSON metadata, not queryable | Scope filtering only works in MemoryService cache path |
| Memory has a source chain | No `source_id` FK, no provenance table link | Cannot trace memory back to ingestion source |
| GraphNode temporal_status reflects reality | Never transitions from `"current"` | Graph appears fully current regardless of supersession |
| Decisions are deduplicated across batches | `pipeline.py:158-171` inserts every decision | Same decision from multiple sources accumulates |

### 3.4 Contracts That Must Exist Before Implementation

| # | Contract | Contract Shape | Responsible Module |
|---|----------|---------------|-------------------|
| C-1 | Memory Provenance Chain | Memory has `source_id` FK → Source → IngestJob | MemoryService + models |
| C-2 | Memory Confidence/Authority Calibration | M2 sets calibrated values on Memory via pipeline | Pipeline (m2 stage) |
| C-3 | Supersession Traceability | `superseded_by_id` written at supersession; Memory has `superseded_by_id` column | Pipeline + models |
| C-4 | Contradiction Registry | `contradictions` table: `fact_id`, `contradicts_fact_id`, `detected_at`, `resolution` | M3 or post-M3 |
| C-5 | Memory Expiry | `expires_at` column on Memory + scheduled cleanup task | MemoryService + scheduler |
| C-6 | Vector Embedding Contract | `Memory.embedding` populated at write time with 1536-dim vector + pgvector index | MemoryService + pgvector |
| C-7 | Memory Type Taxonomy | Single source of truth: `MemoryType` enum → DB column value | models + schemas |
| C-8 | Memory Scope Enforcement | `scope` column on Memory + RBAC check at query time | MemoryService + PolicyEngine |
| C-9 | Audit Coverage for Memory | MemoryService emits `memory.write`, `memory.update`, `memory.delete` events | MemoryService |
| C-10 | Graph Temporal Contracts | GraphNode/GraphEdge temporal_status transitions at supersession | M3 + M4 |

### 3.5 Intelligence Layer Boundary Diagram

```mermaid
graph TB
    subgraph Safe["SAFE to Consume"]
        F1["Facts: current, source-linked, M5-scored"]
        F2["Decisions: current, source-linked, M5-scored"]
        F3["Graph: deduplicated edges, workspace-scoped"]
        F4["Provenance: MessageProvenance chains"]
        F5["Audit: append-only event log"]
        M1["Memory: content text, soft-delete filtered"]
    end

    subgraph Conditional["CONDITIONALLY SAFE"]
        C1["Memory confidence — UNTRUSTED (hardcoded defaults)"]
        C2["Memory authority — UNTRUSTED (hardcoded defaults)"]
        C3["Decision dedup — IMPERFECT (no cross-batch check)"]
        C4["Graph freshness — DEGRADED (temporal_status static)"]
    end

    subgraph Unsafe["MUST NOT CONSUME"]
        U1["Memory scope from JSON — UNENFORCEABLE"]
        U2["Memory provenance from JSON — UNQUERYABLE"]
        U3["Vector embeddings — EMPTY (never populated)"]
        U4["superseded_by_id on Fact/Decision — DEAD DATA"]
        U5["Memory team_id — LOST (no column)"]
        U6["Memory expires_at — MISSING (no column)"]
    end

    INT["Memory Intelligence Layer"]

    INT --> Safe
    INT -.-> Conditional
    INT -x-> Unsafe

    style Safe fill:#9f9,stroke:#333
    style Conditional fill:#ff9,stroke:#333
    style Unsafe fill:#f99,stroke:#333
```

### 3.6 Readiness Verdict by Intelligence Capability

| Capability | Current Status | Blocker | Target |
|------------|---------------|---------|--------|
| **Fact extraction** | Regex, no LLM validation | P2-7: Add LLM validation | M2.5 stage |
| **Fact confidence** | Hardcoded 0.8 | P2-6: Implement calibration | M2.5 stage |
| **Fact supersession tracking** | temporal_status works, superseded_by_id dead | P1-1: Write superseded_by_id | M3 fix |
| **Contradiction detection** | Not implemented | P2-1: Implement detection | M3.5 stage |
| **Decision dedup** | No cross-batch dedup | P2-4: Add dedup check | Pipeline fix |
| **Memory provenance** | JSON only, not queryable | P1-3: Add source_id + table | Data migration |
| **Memory authority calibration** | Default 1.0, never set | P2-6: Implement calibration | Pipeline + API |
| **Memory confidence calibration** | Default 0.7, never set | P2-6: Implement calibration | Pipeline + API |
| **Memory expiry** | No mechanism | P2-2: Add expires_at + cleanup | Data migration |
| **Vector search** | Column exists, never populated | P1-2: Implement embeddings | M4.5 stage |
| **Graph freshness** | temporal_status static | P2-8: Implement transitions | M3 + M4 |
| **Graph node confidence** | No column | P2: Add column | Data migration |

### 3.7 Implementation Sequence for Intelligence Layer Readiness

**Phase 1 (Data Integrity — P1 fixes):**
1. Fix `superseded_by_id` writing in pipeline
2. Add `source_id` to Memory table
3. Add `scope` column to Memory table
4. Add `team_id` column to Memory table
5. Fix memory type taxonomy inconsistency
6. Implement `expires_at` column + scheduled cleanup

**Phase 2 (Quality Enhancement — P2 fixes):**
7. Implement contradiction detection
8. Implement LLM-based confidence/authority calibration
9. Implement vector embedding generation + pgvector
10. Implement graph temporal transitions
11. Persist M1 output
12. Add cross-batch decision dedup
13. Fix API key expiry enforcement

**Phase 3 (Operational Excellence — P3 improvements):**
14. Redis-backed rate limiter
15. JWT/PII redaction in errors
16. Circuit breaker for LLM calls
17. Distributed tracing
18. Metrics endpoint
19. Graceful shutdown

---

## 4. Summary Classification of All Findings

| Finding | Classification | Severity |
|---------|---------------|----------|
| `superseded_by_id` never written | **DOCUMENTED BUT IMPLEMENTED INCORRECTLY** | P1 |
| `Memory.embedding` never populated | **DOCUMENTED ONLY (non-functional)** | P1 |
| Memory type taxonomy (4 defaults) | **DOCUMENTED INCONSISTENCY** | P2 |
| Memory `team_id` lost | **IMPLEMENTED WITH DATA LOSS** | P1 |
| Memory `scope` not queryable | **IMPLEMENTED INCOMPLETE** | P2 |
| Rate limiting in-memory | **IMPLEMENTED WITH LIMITATION** | P0 |
| JWT/PII redaction missing | **MISSING** | P0 |
| Contradiction detection | **MISSING** | P2 |
| Memory expiry | **MISSING** | P2 |
| Circuit breaker for LLM | **MISSING** | P0 |
| Distributed tracing | **MISSING** | P3 |
| Metrics endpoint | **MISSING** | P3 |
| Graceful shutdown | **MISSING** | P3 |
| API key expiry enforcement | **IMPLEMENTED INCOMPLETE** | P2 |
| PolicyEngine hardcoded policies | **IMPLEMENTED WITH LIMITATION** | P2 |
| M1 output not persisted | **IMPLEMENTED WITH GAP** | P2 |
| Pipeline synchronous | **IMPLEMENTED WITH LIMITATION** | P2 |
| M3 supersession functions unused | **DEAD CODE** | Low |
| `_PERMISSIONS` dict in rbac.py | **DEAD CODE** | Low |
| AuditEvent DTO/ORM field mismatch | **INCONSISTENT** | Low |

---

*End of Document C: SWARMVAULT_ARCHITECTURE_GAPS_AND_MEMORY_NEXT_LAYER.md*
