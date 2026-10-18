# SwarmVault Architecture Documentation Index
**Phase**: M-ARCH — Memory Architecture Freeze Gate
**Created**: 2026-09-10

---

## Document Map

### Forensic Gap Analysis (Phase 1)

| # | Document | Scope | Lines |
|---|----------|-------|-------|
| 1 | `SWARMVAULT_TEMPORAL_SUPERSESSION_GAP_ANALYSIS.md` | M3 temporal, supersession, contradictions, audit | 212 |
| 2 | `SWARMVAULT_RETRIEVAL_GAP_ANALYSIS.md` | M5 retrieval, memory visibility, semantic search | 182 |
| 3 | `SWARMVAULT_INGESTION_AGENT_INTEGRATION_GAP_ANALYSIS.md` | Background jobs, connectors, SSE, external agents | 262 |
| 4 | `SWARMVAULT_CLOUD_SCALE_STATE_GAP_ANALYSIS.md` | Horizontal scaling, distributed state, observability | 241 |
| 5 | `SWARMVAULT_MASTER_GAP_SYNTHESIS.md` | Cross-gap interaction map, unified register, priority matrix | 266 |

### Architecture Freeze Contracts (Phase M-ARCH)

| # | Document | Purpose |
|---|----------|---------|
| 6 | `CANONICAL_MEMORY_CONTRACT.md` | Defines the canonical memory object, type variants, and identity |
| 7 | `TEMPORAL_KNOWLEDGE_STATE_CONTRACT.md` | Separates lifecycle, knowledge validity, and trust as orthogonal dimensions |
| 8 | `PROVENANCE_EVIDENCE_CONTRACT.md` | Provenance chain model, evidence requirements by trust level |
| 9 | `CANONICAL_RETRIEVAL_CONTRACT.md` | Single retrieval pipeline replacing two divergent services |
| 10 | `UNIVERSAL_AGENT_EVENT_CONTRACT.md` | Canonical event format for all external agents |
| 11 | `MEMORY_WRITE_AUTHORITY_MATRIX.md` | Who may perform which operations on memory objects |
| 12 | `DERIVED_STATE_CONTRACT.md` | Authoritative vs derived vs ephemeral data classification |
| 13 | `MEMORY_FAILURE_RECOVERY_CONTRACT.md` | Failure modes, recovery mechanisms, integrity guarantees |
| 14 | `MEMORY_IDENTITY_CONTRACT.md` | Memory identity system (memory_id, content_hash, lineage) |
| 15 | `MEMORY_ARCHITECTURE_DECISION_RECORD.md` | 10 binding architectural decisions with rationale |
| 16 | `MEMORY_INTELLIGENCE_READINESS_CERTIFICATION.md` | Certification status, gate criteria, process |

---

## Reading Order

### For Architects
1. `MEMORY_INTELLIGENCE_READINESS_CERTIFICATION.md` — current state
2. `MEMORY_ARCHITECTURE_DECISION_RECORD.md` — binding decisions
3. `CANONICAL_MEMORY_CONTRACT.md` — canonical object definition
4. `CANONICAL_RETRIEVAL_CONTRACT.md` — retrieval architecture
5. `TEMPORAL_KNOWLEDGE_STATE_CONTRACT.md` — temporal model
6. `SWARMVAULT_MASTER_GAP_SYNTHESIS.md` — gap analysis

### For Security Architects
1. `MEMORY_WRITE_AUTHORITY_MATRIX.md` — authority model
2. `PROVENANCE_EVIDENCE_CONTRACT.md` — audit requirements
3. `SWARMVAULT_TEMPORAL_SUPERSESSION_GAP_ANALYSIS.md` — security gaps
4. `MEMORY_FAILURE_RECOVERY_CONTRACT.md` — failure modes

### For Backend Engineers
1. `CANONICAL_MEMORY_CONTRACT.md` — schema requirements
2. `CANONICAL_RETRIEVAL_CONTRACT.md` — service requirements
3. `UNIVERSAL_AGENT_EVENT_CONTRACT.md` — integration requirements
4. `DERIVED_STATE_CONTRACT.md` — data classification
5. `MEMORY_FAILURE_RECOVERY_CONTRACT.md` — error handling

### For Frontend Engineers
1. `CANONICAL_RETRIEVAL_CONTRACT.md` — API contract for retrieval
2. `MEMORY_WRITE_AUTHORITY_MATRIX.md` — permission model
3. `MEMORY_IDENTITY_CONTRACT.md` — ID handling in UI

### For Operations
1. `MEMORY_FAILURE_RECOVERY_CONTRACT.md` — monitoring, recovery procedures
2. `DERIVED_STATE_CONTRACT.md` — backup requirements
3. `SWARMVAULT_CLOUD_SCALE_STATE_GAP_ANALYSIS.md` — scaling limitations

---

## Key Findings Summary

### What the System Can Do Today (Production Ready)
- Chat with LLM (streaming and non-streaming)
- Ingest conversations from 6 formats
- Extract facts and decisions with confidence/authority
- Multi-factor retrieval of Facts and Decisions
- Knowledge graph visualization
- Provenance tracking for chat responses
- Audit logging for ingestion events
- RBAC authorization
- Soft deletion
- API key management

### What Blocks Memory Intelligence
| Blocker | Document | Contract |
|---------|----------|----------|
| No canonical memory identity | CANONICAL_MEMORY_CONTRACT.md | DECISION-001 |
| Two divergent retrieval services | CANONICAL_RETRIEVAL_CONTRACT.md | DECISION-003 |
| Memory model not retrievable | CANONICAL_RETRIEVAL_CONTRACT.md | DECISION-004 |
| No semantic retrieval | CANONICAL_RETRIEVAL_CONTRACT.md | DECISION-005 |
| No background ingestion | DERIVED_STATE_CONTRACT.md | DECISION-006 |
| No supersession lineage | TEMPORAL_KNOWLEDGE_STATE_CONTRACT.md | DECISION-007 |
| No agent event format | UNIVERSAL_AGENT_EVENT_CONTRACT.md | DECISION-008 |
| No trust level system | MEMORY_WRITE_AUTHORITY_MATRIX.md | DECISION-009 |
| No memory safety gate | MEMORY_INTELLIGENCE_READINESS_CERTIFICATION.md | DECISION-010 |

### Current Certification Status
```
MEMORY INTELLIGENCE READINESS: NOT CERTIFIED
P0 Criteria: 0 / 8 passed
P1 Criteria: 0 / 7 passed
Current WebApp: Production Ready (with operational caveats)
```

---

## Source Files Referenced

| Source File | Referenced In |
|-------------|---------------|
| `app/models.py` | All contracts |
| `app/schemas.py` | CANONICAL_MEMORY_CONTRACT, CANONICAL_RETRIEVAL_CONTRACT |
| `app/services/pipeline.py` | TEMPORAL, RETRIEVAL, INGESTION gap docs |
| `app/services/m5_retrieval.py` | RETRIEVAL gap doc, CANONICAL_RETRIEVAL_CONTRACT |
| `app/services/retrieval.py` | RETRIEVAL gap doc |
| `app/services/memory.py` | CANONICAL_MEMORY_CONTRACT |
| `app/services/connectors.py` | INGESTION gap doc, UNIVERSAL_AGENT_EVENT_CONTRACT |
| `app/services/chat_orchestrator.py` | RETRIEVAL gap doc |
| `app/services/m3_temporal.py` | TEMPORAL gap doc |
| `app/services/m4_graph.py` | TEMPORAL gap doc |
| `app/services/m2_facts.py` | CANONICAL_MEMORY_CONTRACT |
| `app/services/llm.py` | INGESTION gap doc |
| `app/services/policy/engine.py` | SECURITY gap doc, AUTHORITY MATRIX |
| `app/core/config.py` | CLOUD_SCALE gap doc |
| `app/api/ingest.py` | RETRIEVAL, INGESTION gap docs |
| `app/api/chat.py` | RETRIEVAL gap doc |
| `app/main.py` | CLOUD_SCALE gap doc |
| `app/middleware/rate_limit.py` | CLOUD_SCALE gap doc |
| `app/db.py` | CLOUD_SCALE gap doc |
| `app/middleware/auth.py` | SECURITY gap doc |
| `app/services/audit/` | TEMPORAL, PROVENANCE gap docs |
