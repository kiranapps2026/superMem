# SwarmVault Persistent Memory Readiness

**Forensic Reconciliation Phase — Final Synthesis**
**Baseline SHA:** e6f4b1c157afaed052584963b942ea04f9661610
**Date:** 2026-09-10

---

## 1. What Data Is Currently Persistent?

| Data Type | Persistent | Storage | Evidence |
|-----------|-----------|---------|----------|
| **Sources** | YES | PostgreSQL `sources` table | `app/models.py:302-366` — content_hash, status, stage, progress |
| **Normalized Messages** | YES | PostgreSQL `normalized_messages` table | `app/models.py:369-410` — full content, role, timestamp |
| **Facts** | YES | PostgreSQL `facts` table | `app/models.py:413-464` — subject, predicate, object, confidence, authority, temporal_status |
| **Decisions** | YES | PostgreSQL `decisions` table | `app/models.py:467-517` — content, context, confidence, authority, temporal_status |
| **Graph Nodes** | YES | PostgreSQL `graph_nodes` table | `app/models.py:520-558` — label, node_type, properties |
| **Graph Edges** | YES | PostgreSQL `graph_edges` table | `app/models.py:561-604` — relationship_type, confidence, temporal_status |
| **Memories** | YES | PostgreSQL `memories` table | `app/models.py:232-266` — content, memory_type, confidence, authority, temporal_status |
| **Sessions** | YES | PostgreSQL `sessions` table | `app/models.py:165-188` — title, metadata, user FK |
| **Audit Events** | YES | PostgreSQL `audit_events` table | `app/models.py:788-837` — append-only, 15+ indexed fields |
| **Provenance** | YES | PostgreSQL `message_provenance` table | `app/models.py:607-653` — per-chat-response tracking |
| **API Keys** | YES | PostgreSQL `api_keys` table | Hashed tokens, expiry tracked |
| **Refresh Tokens** | YES | PostgreSQL `refresh_tokens` table | Hashed tokens, revocation flag |
| **Ingest Jobs** | YES | PostgreSQL `ingest_jobs` table | Queued ingestion jobs |
| **Roles/Permissions** | YES | PostgreSQL `roles`, `permissions`, `user_roles` tables | RBAC system |
| **M1 Session Understanding** | NO | Ephemeral (returned in response only) | `pipeline.py:75-95` — returned, not persisted |

---

## 2. What Data Is Ephemeral?

| Data Type | Where It Lives | Lifetime | Evidence |
|-----------|---------------|----------|----------|
| M1 session understanding | API response only | Until response delivered | `pipeline.py:75-95` — not persisted |
| LLM streaming chunks | SSE stream | Until stream completes | `chat_orchestrator.py` — yielded, not stored |
| Rate limit counters | In-memory singleton | Until process restart | `rate_limit.py:17-30` — module-level `_rate_limiter` |
| JWT tokens | Client localStorage | Until expiry or logout | Frontend `localStorage['sv_tokens']` |
| Access token context | Request state | Per-request | `TenantContext` from dependency |

---

## 3. What Data Is Normalized?

| Data Type | Normalized | Format | Evidence |
|-----------|-----------|--------|----------|
| Raw conversation text | YES | NormalizedMessage (role, content, timestamp, metadata) | `connectors.py` — 6 connectors normalize to common schema |
| JSON uploads | YES | NormalizedMessage | JSONConnector |
| JSONL uploads | YES | NormalizedMessage | JSONLConnector |
| ChatGPT exports | YES | NormalizedMessage | ChatGPTConnector |
| OpenAI Chat exports | YES | NormalizedMessage | OpenAIChatConnector |
| OpenAI Playground exports | YES | NormalizedMessage | OpenAIPlaygroundConnector |
| Facts | YES | Structured (subject, predicate, object) | Pipeline M2 — regex extraction |
| Decisions | YES | Structured (content, context) | Pipeline M2 — regex extraction |
| Graph entities | YES | GraphNode (label, type, properties) | Pipeline M4 |
| Graph relationships | YES | GraphEdge (type, confidence, source/target) | Pipeline M4 |

---

## 4. What Data Has Provenance?

| Data Type | Has Provenance | Chain | Evidence |
|-----------|---------------|-------|----------|
| Source → Message | YES | Source → NormalizedMessage (FK) | `app/models.py:350-354` |
| Fact → Source | YES | Fact.source_id → Source | `app/models.py:426`, `pipeline.py:120` |
| Decision → Source | YES | Decision.source_id → Source | `app/models.py:482`, `pipeline.py:159` |
| GraphEdge → Source | YES | GraphEdge.source_id → Source | `app/models.py:585`, `m4_graph.py:187` |
| Chat → Provenance | YES | MessageProvenance.memory_ids_used + retrieval_sources | `app/models.py:607-653` |
| Memory → Provenance | PARTIAL | In extra_metadata JSON only, no Source FK | `memory.py:109-111` — Python list stored as JSON |
| Audit events | YES | Append-only with user_id, action, resource_id | `app/models.py:788-837` |

---

## 5. What Data Has Temporal Semantics?

| Data Type | temporal_status | created_at | updated_at | deleted_at | Evidence |
|-----------|----------------|-----------|-----------|-----------|----------|
| Fact | YES | YES | YES | YES | `app/models.py:438-454` |
| Decision | YES | YES | YES | YES | `app/models.py:490-505` |
| GraphNode | YES | YES | YES | YES | `app/models.py:548` |
| GraphEdge | YES | YES | YES | YES | `app/models.py:584` |
| Memory | YES | YES | YES | YES | `app/models.py:254` |
| Source | NO (has `status` instead) | YES | YES | YES | `app/models.py:319` |
| NormalizedMessage | NO | YES | NO | YES (via parent) | `app/models.py:395` |
| Session | NO | YES | YES | YES | `app/models.py:175` |
| AuditEvent | NO (immutable) | YES | NO | NO | `app/models.py:820` |

---

## 6. What Data Has Confidence?

| Data Type | confidence Field | Default | Source | Evidence |
|-----------|-----------------|---------|--------|----------|
| Fact | YES | 1.0 | Hardcoded 0.8 in pipeline, DB default 1.0 | `app/models.py:435`, `pipeline.py:129` |
| Decision | YES | 1.0 | Hardcoded 0.75 in pipeline, DB default 1.0 | `app/models.py:488`, `pipeline.py:130` |
| GraphEdge | YES | 1.0 | From parent fact confidence | `app/models.py:582` |
| Memory | YES | 0.7 | Default, never calibrated | `app/models.py:255` |
| Source | NO | — | — | `app/models.py:319` |
| Message | NO | — | — | `app/models.py:395` |

**GAP:** Confidence is hardcoded in pipeline, not LLM-calibrated. All facts appear equally confident.

---

## 7. What Data Has Authority?

| Data Type | authority Field | Default | Source | Evidence |
|-----------|----------------|---------|--------|----------|
| Fact | YES | 1.0 | Hardcoded 0.75 in pipeline, DB default 1.0 | `app/models.py:436`, `pipeline.py:129` |
| Decision | YES | 1.0 | Hardcoded 0.75 in pipeline, DB default 1.0 | `app/models.py:489`, `pipeline.py:130` |
| GraphEdge | NO (uses confidence proxy) | — | — | `app/models.py:582` |
| Memory | YES | 1.0 | Default, never calibrated | `app/models.py:256` |
| Source | NO | — | — | `app/models.py:319` |

**GAP:** Authority is hardcoded, not source-calibrated.

---

## 8. What Data Has Identity?

| Data Type | Primary Key | Type | Additional Identity | Evidence |
|-----------|-------------|------|-------------------|----------|
| Source | id | UUID | content_hash (SHA-256) | `app/models.py:319` |
| NormalizedMessage | id | UUID | role + timestamp + source_id | `app/models.py:395` |
| Fact | id | UUID | (subject, predicate, object) | `app/models.py:426` |
| Decision | id | UUID | content hash | `app/models.py:482` |
| GraphNode | id | UUID | label + node_type | `app/models.py:530` |
| GraphEdge | id | UUID | (source_node, target_node, relationship_type) | `app/models.py:570` |
| Memory | id | UUID | agent_id + run_id | `app/models.py:238` |
| Session | id | UUID | title + user_id | `app/models.py:175` |
| AuditEvent | id | UUID | action + resource_type + timestamp | `app/models.py:820` |
| MessageProvenance | id | UUID | session_id + timestamp | `app/models.py:618` |

**GAP:** No unified memory identity. Facts, Decisions, and Memories are in separate tables with no cross-reference.

---

## 9. What Data Has Scope?

| Data Type | Scope Dimensions | Enforcement | Evidence |
|-----------|-----------------|-------------|----------|
| Source | tenant_id, workspace_id, project_id | Query filter | `app/models.py:306-310` |
| NormalizedMessage | tenant_id, workspace_id, project_id | Query filter | `app/models.py:372-376` |
| Fact | tenant_id, workspace_id, project_id, session_id | Query filter | `app/models.py:418-424` |
| Decision | tenant_id, workspace_id, project_id, session_id | Query filter | `app/models.py:471-477` |
| GraphNode | tenant_id, workspace_id, project_id | Query filter | `app/models.py:525-529` |
| GraphEdge | tenant_id, workspace_id, project_id | Query filter | `app/models.py:565-569` |
| Memory | tenant_id, workspace_id, project_id | Query filter + JSON scope | `app/models.py:238-249` |
| Session | tenant_id, workspace_id, project_id | Query filter | `app/models.py:168-172` |

---

## 10. What Data Can Be Superseded?

| Data Type | Supersession Mechanism | superseded_by_id | Evidence |
|-----------|----------------------|-----------------|----------|
| Fact | temporal_status="historical" when same (subject, predicate) appears later | YES (column exists, **never written**) | `app/models.py:440`, `pipeline.py:112-137` |
| Decision | temporal_status="historical" when same context superseded | YES (column exists, **never written**) | `app/models.py:493`, `pipeline.py:112-137` |
| GraphNode | temporal_status="historical" | NO | `app/models.py:548` |
| GraphEdge | temporal_status="historical" | NO | `app/models.py:584` |
| Memory | temporal_status="historical" | NO | `app/models.py:254` |

**GAP:** `superseded_by_id` columns exist on Fact and Decision but are never written by any code path. Supersession is tracked only via `temporal_status`, not via chain links.

---

## 11. What Data Can Be Contradicted?

| Data Type | Contradiction Mechanism | Evidence |
|-----------|------------------------|----------|
| Fact | **NOT IMPLEMENTED** | No contradiction detection code exists |
| Decision | **NOT IMPLEMENTED** | No contradiction detection code exists |
| GraphEdge | **NOT IMPLEMENTED** | No "contradicts" relationship type |
| Memory | **NOT IMPLEMENTED** | No contradiction detection code exists |

---

## 12. What Data Can Be Deleted?

| Data Type | Deletion Mechanism | Evidence |
|-----------|-------------------|----------|
| Fact | Soft delete (parent Source deleted_at) | `app/models.py:454` — deleted_at column |
| Decision | Soft delete (parent Source deleted_at) | `app/models.py:505` — deleted_at column |
| GraphNode | Soft delete | `app/models.py:558` — deleted_at column |
| GraphEdge | Soft delete | `app/models.py:604` — deleted_at column |
| Memory | Soft delete (deleted_at) | `app/models.py:257` — deleted_at column |
| Source | Soft delete (deleted_at) | `app/models.py:322` — deleted_at column |
| Session | Soft delete (deleted_at) | `app/models.py:188` — deleted_at column |
| AuditEvent | **CANNOT BE DELETED** | Append-only — no DELETE in application code |
| API Key | Hard delete (revoked flag + actual delete) | `app/api/api_keys.py` |

---

## 13. What Data Can Be Retrieved?

| Data Type | Retrieval Mechanism | Evidence |
|-----------|-------------------|----------|
| Facts | M5 retrieval (keyword + scoring) | `m5_retrieval.py:rank_facts()` |
| Decisions | M5 retrieval (keyword + scoring) | `m5_retrieval.py:rank_decisions()` |
| GraphNodes | Direct query | `app/api/ingest.py` — graph endpoint |
| GraphEdges | Direct query | `app/api/ingest.py` — graph endpoint |
| Memories | MemoryService.list() | `memory.py` — workspace-scoped query |
| Sources | Direct query | `app/api/ingest.py` — sources endpoint |
| Sessions | Direct query | `app/api/sessions.py` — session history |
| Provenance | Direct query | `app/api/provenance.py` — MessageProvenance records |
| Audit Events | Direct query (admin only) | `app/api/audit.py` — filtered by workspace |

---

## 14. What Data Can Be Explained?

| Data Type | Explainability Mechanism | Evidence |
|-----------|------------------------|----------|
| Facts | M5 factor scores (keyword, authority, confidence, recency, temporal, graph) | `m5_retrieval.py:100-154` |
| Decisions | M5 factor scores | `m5_retrieval.py:100-154` |
| Memories | factor_scores via MemoryService.explain() | `memory.py` — returns score breakdown |
| Chat responses | MessageProvenance (memory_ids_used, retrieval_sources) | `app/models.py:607-653` |
| Graph relationships | Direct query — source_id chain | `app/models.py:585` — each edge has source_id |

---

## 15. What Data Is Safe for Future Memory Intelligence?

| Data Type | Safety Rating | Why | What Must Be Fixed First |
|-----------|--------------|-----|------------------------|
| **Facts (current)** | YELLOW | Regex-extracted, confidence hardcoded, no LLM validation | Confidence calibration, LLM validation |
| **Decisions (current)** | YELLOW | Regex-extracted, confidence hardcoded, no LLM validation | Confidence calibration, LLM validation |
| **Graph Nodes/Edges** | YELLOW | Regex-extracted, temporal_status static | Temporal transitions, node confidence |
| **Memories (user-created)** | YELLOW | User-authored content, no source chain | Source chain, scope enforcement |
| **Chat Provenance** | GREEN | Complete LLM metadata, memory_ids_used, token counts | None |
| **Audit Trail** | GREEN | Append-only, tenant-isolated, comprehensive | None |
| **Temporal Status** | GREEN | current/historical classification works for Facts | None |
| **Scope Isolation** | GREEN | Tenant → Workspace → Project enforced | None |
| **Soft Deletion** | GREEN | deleted_at on all major models | None |
| **Content Hashing** | GREEN | SHA-256 on Source for dedup | None |
| **Source Chain** | GREEN | Fact/Decision/GraphEdge → Source → NormalizedMessage | None |
| **Supersession (temporal_status)** | YELLOW | Works for grouping, but superseded_by_id is dead | Fix superseded_by_id writing |
| **Memory provenance** | RED | JSON-only in extra_metadata, not queryable | Add source_id FK + provenance table |
| **Memory confidence/authority** | RED | Defaults never calibrated | Implement calibration at M2 |
| **Vector embeddings** | RED | Column never populated | Implement embedding generation |
| **Contradiction detection** | RED | Not implemented | Add detection algorithm |
| **Trust levels** | RED | No field exists | Add trust_level column + state machine |

---

## 16. GREEN/YELLOW/RED Summary

| Area | Status | Notes |
|------|--------|-------|
| Source persistence | GREEN | Full chain: content, hash, status, stage, messages |
| Fact persistence | GREEN | Complete with temporal_status, superseded_by_id column |
| Decision persistence | GREEN | Complete with temporal_status, superseded_by_id column |
| Graph persistence | GREEN | Nodes and edges with temporal_status |
| Memory persistence | YELLOW | Persists but excluded from retrieval, no source chain |
| Provenance chain (Source→Knowledge) | GREEN | Fact/Decision/GraphEdge all carry source_id |
| Provenance chain (Memory) | YELLOW | In extra_metadata JSON, not queryable |
| Provenance chain (Chat) | GREEN | MessageProvenance complete with memory_ids_used |
| Temporal semantics (Fact/Decision) | GREEN | temporal_status + superseded_by_id column |
| Temporal semantics (Memory/Graph) | YELLOW | temporal_status exists but static |
| Supersession lineage | YELLOW | temporal_status works, superseded_by_id is dead column |
| Contradiction tracking | RED | None exists |
| Trust level | RED | No field, no state machine |
| Semantic retrieval | RED | No embedding infrastructure |
| Confidence calibration | RED | Hardcoded defaults |
| Authority calibration | RED | Hardcoded defaults |
| Background ingestion | RED | Synchronous only |
| Memory Safety Gate | RED | No implementation |
| Audit coverage | GREEN | Append-only, comprehensive event types |
| Scope isolation | GREEN | Tenant → Workspace → Project hierarchy |

---

## 17. Persistent Memory Readiness Verdict

### What CAN become persistent memory TODAY (safely):

1. **Facts** with `temporal_status="current"` — have source chain, confidence, authority, temporal status, scope isolation
2. **Decisions** with `temporal_status="current"` — same as facts
3. **Chat provenance** — complete LLM metadata, memory_ids_used, retrieval_sources
4. **Audit events** — append-only, immutable, tenant-isolated
5. **User-created memories** — content is user-authored, has temporal_status, confidence, authority
6. **Graph knowledge** — nodes and edges with source chains

### What CANNOT safely become persistent memory TODAY:

1. **Memory with JSON provenance** — not queryable, no source chain
2. **Memory with hardcoded confidence/authority** — not calibrated
3. **Facts with dead superseded_by_id** — cannot trace supersession chains
4. **Graph with static temporal_status** — cannot determine freshness
5. **Memories with JSON-only scope** — not enforced at DB level
6. **Any content without trust_level** — no quality gate before persistence

### What the Memory Safety Gate should enforce (before implementation):

```
BEFORE persistence:
  1. Content passes safety filter (toxicity, PII detection)
  2. Confidence ≥ minimum threshold (calibrated, not default)
  3. Authority ≥ minimum threshold (source-calibrated)
  4. Trust level ≥ threshold (when implemented)
  5. Not a duplicate of existing memory (dedup check)
  6. Provenance chain established (source_id FK)
  7. Scope is queryable (column, not JSON)
  8. Rate limit check (distributed, not in-memory)
```

---

*End of Document: SWARMVAULT_PERSISTENT_MEMORY_READINESS.md*
