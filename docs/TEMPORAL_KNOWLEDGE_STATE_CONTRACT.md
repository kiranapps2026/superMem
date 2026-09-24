# Temporal & Knowledge State Contract
**Phase**: M-ARCH — Memory Architecture Freeze Gate
**Status**: PROPOSED — requires review and approval before implementation
**Created**: 2026-09-10

---

## 1. Purpose

This contract separates **three orthogonal dimensions** that the current codebase
conflates:

1. **Lifecycle** — whether a memory exists in the active dataset
2. **Knowledge validity** — whether the information is believed to be true
3. **Trust level** — whether an autonomous agent may act on it

Currently, `temporal_status` and `status` are used interchangeably. This contract
defines them as independent axes with formal state machines.

---

## 2. Lifecycle State Machine

Controlled by: `status` column + `deleted_at` column

```
                    ┌─────────────┐
                    │   ACTIVE    │ ← Default for all new memories
                    └──────┬──────┘
                           │ soft_delete()
                           ▼
                    ┌─────────────┐
                    │   DELETED   │ ← Hidden from all queries
                    └──────┬──────┘
                           │ purge()
                           ▼
                    ┌─────────────┐
                    │  PURGED     │ ← Physically removed (or tombstone)
                    └─────────────┘

                    ┌─────────────┐
                    │   ACTIVE    │
                    └──────┬──────┘
                           │ archive()
                           ▼
                    ┌─────────────┐
                    │  ARCHIVED   │ ← Retained but excluded from retrieval
                    └─────────────┘
                           │ restore()
                           ▼
                    ┌─────────────┐
                    │   ACTIVE    │ ← Can return from ARCHIVED
                    └─────────────┘
```

**Rules**:
- ACTIVE → DELETED: Any actor with `memory:delete` permission
- ACTIVE → ARCHIVED: Any actor with `memory:archive` permission
- DELETED → PURGED: Admin only, after retention period
- ARCHIVED → ACTIVE: Any actor with `memory:restore` permission
- DELETED → ACTIVE: NOT ALLOWED (must create new memory instead)
- PURGED is terminal — no recovery

**Query behavior**:
- ACTIVE: Included in all queries
- ARCHIVED: Excluded from retrieval, included in audit
- DELETED: Excluded from all queries unless `include_deleted=true` (admin only)
- PURGED: Not queryable

---

## 3. Knowledge Validity State Machine

Controlled by: `temporal_status` column

```
                    ┌─────────────┐
                    │  CURRENT    │ ← Default — believed to be true
                    └──────┬──────┘
                           │ supersede()
                           ▼
                    ┌─────────────┐
                    │ SUPERSEDED  │ ← Known to be replaced by newer knowledge
                    └──────┬──────┘
                           │ invalidate()
                           ▼
                    ┌─────────────┐
                    │ INVALIDATED │ ← Known to be false or retracted
                    └─────────────┘

                    ┌─────────────��
                    │  CURRENT    │
                    └──────┬──────┘
                           │ expire()
                           ▼
                    ┌─────────────┐
                    │   EXPIRED   │ ← Time-limited knowledge that reached its end
                    └─────────────┘
```

**Rules**:
- CURRENT → SUPERSEDED: When a new memory with same identity is created
- CURRENT → INVALIDATED: When a trusted source explicitly retracts
- CURRENT → EXPIRED: When `expires_at` is reached (automatic)
- SUPERSEDED → INVALIDATED: If the superseding memory is itself invalidated
- Any non-CURRENT state → CURRENT: NOT ALLOWED (must create new memory)

**Query behavior**:
- CURRENT: Included in retrieval, included in LLM context
- SUPERSEDED: Excluded from retrieval by default (`include_superseded=false`), included in audit/timeline
- INVALIDATED: Never included in retrieval, flagged in audit
- EXPIRED: Excluded from retrieval after expiry date, included in audit

---

## 4. Trust Level State Machine

Controlled by: `extra_metadata.trust_level`

```
                    ┌─────────────┐
                    │ UNVERIFIED  │ ← Default for pipeline-extracted memories
                    └──────┬──────┘
                           │ human_review() / certify()
                           ▼
                    ┌─────────────┐
                    │  OBSERVED   │ ← Seen in multiple independent sources
                    └──────┬──────┘
                           │ corroborate()
                           ▼
                    ┌─────────────┐
                    │  VERIFIED   │ ← Confirmed by authoritative source
                    └──────┬──────┘
                           │ intelligence_certify()
                           ▼
                    ┌─────────────┐
                    │  CERTIFIED  │ ← Safe for autonomous agent action
                    └─────────────┘
```

**Rules**:
- UNVERIFIED → OBSERVED: Same fact observed in 2+ independent sources
- OBSERVED → VERIFIED: Confirmed by a trusted authority (human or high-authority source)
- VERIFIED → CERTIFIED: Passes intelligence layer validation
- Any level → UNVERIFIED: If source authority drops or contradiction detected
- CERTIFIED → any lower level: If retracted or contradicted

**Query behavior**:
- UNVERIFIED: Included in retrieval with low weight penalty
- OBSERVED: Included in retrieval with moderate weight
- VERIFIED: Included in retrieval with high weight
- CERTIFIED: Included in retrieval with maximum weight; safe for autonomous agent use
- Minimum trust level for autonomous agent action: **VERIFIED**
- Minimum trust level for persistent memory promotion: **OBSERVED**

---

## 5. Relationship Predicates (Canonical)

These define the typed relationships between memory objects:

| Predicate | Subject | Object | Meaning | Bidirectional? |
|-----------|---------|--------|---------|----------------|
| `supersedes` | Newer memory | Older memory | Newer replaces older | YES — `superseded_by` |
| `superseded_by` | Older memory | Newer memory | Older replaced by newer | YES — `supersedes` |
| `contradicts` | Memory A | Memory B | A and B cannot both be true | YES — symmetric |
| `supports` | Memory A | Memory B | A provides evidence for B | NO — directional |
| `confirms` | Memory A | Memory B | A independently confirms B | NO — directional |
| `refutes` | Memory A | Memory B | A provides counter-evidence for B | NO — directional |
| `retracts` | Memory A | Memory B | A formally withdraws B | YES — `retracted_by` |
| `retracted_by` | Memory B | Memory A | B was withdrawn by A | YES — `retracts` |
| `derives_from` | Memory A | Memory B | A was synthesized from B | NO — directional |
| `references` | Memory A | Memory B | A mentions or cites B | NO — directional |

**Storage**:
- `supersedes` / `superseded_by`: Stored as FK columns on the memory record
- All others: Stored as `GraphEdge` records in `graph_edges` table
- `contradicts` edges: Must be bidirectional (two edges, A→B and B→A)

---

## 6. Current Implementation vs. Contract

### 6.1 What Exists

| Feature | Current State | Contract Requirement | Gap |
|---------|--------------|---------------------|-----|
| `temporal_status` column | FACT, DECISION, GraphNode, GraphEdge, Memory models | CURRENT, SUPERSEDED, EXPIRED, INVALIDATED | PARTIAL — "historical" used instead of "SUPERSEDED" |
| `status` column | FACT, DECISION, Memory models | ACTIVE, DELETED, ARCHIVED | PARTIAL — no ARCHIVED state |
| `deleted_at` column | Most models | Soft delete | YES — implemented |
| `superseded_by_id` on Fact | Column exists, indexed | FK to memories.id | PARTIAL — not a proper FK constraint |
| `superseded_by_id` on Decision | Column exists, indexed | FK to memories.id | PARTIAL — not a proper FK constraint |
| `supersedes` column | DOES NOT EXIST | FK to memories.id | MISSING |
| `version` column | DOES NOT EXIST | Monotonic counter | MISSING |
| `trust_level` | DOES NOT EXIST | In extra_metadata | MISSING |
| `expires_at` | DOES NOT EXIST | Auto-expiry | MISSING |
| `valid_from` / `valid_until` | DOES NOT EXIST | Temporal validity window | MISSING |
| Contradiction detection | DOES NOT EXIST | Automatic + manual | MISSING |
| Supersession audit event | DOES NOT EXIST | EVENT_TYPE = "memory.superseded" | MISSING |
| Graph edge temporal propagation | DOES NOT EXIST | Update edges when facts superseded | MISSING |
| Retraction mechanism | DOES NOT EXIST | API endpoint + status transition | MISSING |

### 6.2 "historical" vs. "SUPERSEDED"

**Current**: `pipeline.py` sets `temporal_status = "historical"` on superseded facts.
**Contract**: Value should be `"SUPERSEDED"`.

This is a **data migration issue**, not a logic issue. The meaning is correct;
the string value needs normalization.

### 6.3 `superseded_by_id` is Not a Foreign Key

**Current**: `superseded_by_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)`
**Problem**: No `ForeignKey` constraint. The database will accept any string, including
UUIDs that don't reference existing records.

**Contract**: Must become:
```python
superseded_by: Mapped[str | None] = mapped_column(
    String(36), ForeignKey("memories.id"), nullable=True, index=True
)
```

---

## 7. State Transition Rules

### 7.1 Allowed Transitions

| From | To | Trigger | Actor | Requires |
|------|----|---------|-------|----------|
| ACTIVE | DELETED | soft_delete() | Owner/Admin | `memory:delete` |
| ACTIVE | ARCHIVED | archive() | Owner/Admin | `memory:archive` |
| CURRENT | SUPERSEDED | supersede() | Pipeline/Intelligence | New memory with same identity |
| CURRENT | EXPIRED | expire() | System | `expires_at` reached |
| CURRENT | INVALIDATED | invalidate() | Admin/Trusted | Explicit retraction |
| UNVERIFIED | OBSERVED | corroborate() | System | 2+ independent sources |
| OBSERVED | VERIFIED | verify() | Human/Authority | Trusted source confirmation |
| VERIFIED | CERTIFIED | certify() | Intelligence Layer | Validation pass |
| Any | UNVERIFIED | downgrade() | System | Contradiction / authority drop |

### 7.2 Forbidden Transitions

| From | To | Reason |
|------|----|--------|
| DELETED | ACTIVE | Must create new memory instead |
| PURGED | any | Terminal state |
| SUPERSEDED | CURRENT | Must create new memory instead |
| INVALIDATED | CURRENT | Must create new memory instead |
| CERTIFIED | UNVERIFIED | Only → VERIFIED or → INVALIDATED |

---

## 8. Memory Safety Gate

A memory object may become **persistent** (visible to the intelligence layer) only
when ALL of the following are true:

1. `status` = ACTIVE
2. `temporal_status` = CURRENT
3. `confidence` ≥ 0.3 (configurable threshold)
4. `authority` ≥ 0.1 (configurable threshold)
5. Content passes content policy validation
6. Scope isolation is verified (no cross-tenant leak)
7. Provenance chain is complete (source → extraction → enrichment)

A memory object may become **actionable** (safe for autonomous agent use) only when
ALL of the above PLUS:

8. `trust_level` ≥ VERIFIED
9. No `contradicts` edges to CERTIFIED memories
10. Not flagged for human review

---

## 9. Audit Requirements

Every state transition MUST produce an audit event:

| Transition | Audit Event Type | Required Fields |
|-----------|-----------------|----------------|
| ACTIVE → DELETED | `memory.deleted` | memory_id, actor, reason |
| ACTIVE → ARCHIVED | `memory.archived` | memory_id, actor, reason |
| CURRENT → SUPERSEDED | `memory.superseded` | memory_id, superseded_by_id, actor |
| CURRENT → EXPIRED | `memory.expired` | memory_id, expires_at |
| CURRENT → INVALIDATED | `memory.invalidated` | memory_id, reason, actor |
| UNVERIFIED → OBSERVED | `memory.corroborated` | memory_id, source_count |
| OBSERVED → VERIFIED | `memory.verified` | memory_id, authority |
| VERIFIED → CERTIFIED | `memory.certified` | memory_id, validation_result |

**Current gap**: Only `INGEST_COMPLETED` and `INGEST_FAILED` events exist. No
memory lifecycle events are emitted.

---

## 10. Implementation Roadmap

| Phase | Change | Risk |
|-------|--------|------|
| 1 | Rename "historical" → "SUPERSEDED" in pipeline | LOW — data migration |
| 2 | Add `supersedes` FK column | MEDIUM — new FK constraint |
| 3 | Add `version` column | LOW — new column, default 1 |
| 4 | Add `trust_level` to extra_metadata | LOW — JSON field |
| 5 | Separate lifecycle from validity in query filters | MEDIUM — behavior change |
| 6 | Add `expires_at` + auto-expiry job | MEDIUM — background task |
| 7 | Implement contradiction detection | HIGH — new algorithm |
| 8 | Implement trust level state machine | HIGH — new logic |
| 9 | Add audit events for all transitions | MEDIUM — new event types |
