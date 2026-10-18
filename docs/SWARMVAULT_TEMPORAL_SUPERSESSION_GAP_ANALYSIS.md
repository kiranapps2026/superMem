# SwarmVault Temporal / Supersession Gap Analysis

**Forensic status**: Source-first. Every claim is traced to actual implementation.
**Created**: 2026-09-10

---

## 1. Executive Summary

SwarmVault has a **temporal intent** (M3) and a **temporal_status column** on `Fact`, `Decision`, and `GraphEdge`. The intent is correct. The implementation is **partial and has several architectural gaps** that block persistent memory safety and future memory intelligence.

| Dimension | Status |
|-----------|--------|
| Supersession triggers on subject+predicate conflict | PARTIAL |
| Supersession creates explicit linkage | MISSING |
| Contradiction detection | MISSING |
| Versioning / lineage | MISSING |
| Retraction / correction | MISSING |
| Temporal decay in retrieval | PARTIAL |
| Graph temporal propagation | MISSING |
| Audit trail for temporal events | PARTIAL |
| Soft-delete + supersession interaction | GAP |
| Memory safety gate pre-supersession | MISSING |

---

## 2. What the Code Actually Does (M3 Supersession)

### 2.1 File: `app/services/pipeline.py` — lines 90-107

Supersession is performed **inline within `run_pipeline`**, not delegated to `app/services/m3_temporal.py`.

```python
existing = await _find_current_fact(db, workspace_id, fact.subject, fact.predicate)
if existing:
    if existing.object.lower() != fact.object.lower():
        # Same subject/predicate but new object → supersede old
        existing.temporal_status = "historical"
        existing.updated_at = now
        # Create the new fact
        db_fact = Fact(...)
```

**What this means:**
- Only `Fact` objects are superseded. `Decision` objects are appended without any deduplication or supersession check.
- The supersession trigger is **exact subject+predicate match + different object** (case-insensitive).
- The old fact is mutated in-place (`temporal_status = "historical"`).
- No record is created linking the old fact to the new fact.
- The new fact gets `temporal_status = "current"` with no reference to what it superseded.

### 2.2 File: `app/services/m3_temporal.py` — exists but **never called**

`app/services/m3_temporal.py` defines:
- `supersede_fact(db, fact_id, workspace_id, reason=None)` — marks a fact as historical
- `supersede_decision(db, decision_id, workspace_id, reason=None)` — marks a decision as historical

**These functions are imported in `pipeline.py` but never invoked.** The pipeline uses its own inline logic instead. This is a dead-code / unused-function gap.

---

## 3. Fact-Level Gaps

### 3.1 No `supersedes` Foreign Key on `Fact`

**Evidence**: `app/models.py` — `Fact` model has no `supersedes`, `superseded_by`, or `version` field.

**Impact**: Once a fact is superseded, there is no programmatic way to trace from the new fact back to the old fact or vice versa. The relationship is lost.

**Risk for persistent memory**: A memory intelligence layer cannot reconstruct "fact lineage" — it sees two disconnected facts with no causal relationship.

### 3.2 No Contradiction Detection

**Evidence**: No code anywhere in the codebase detects or handles contradictions between facts. The supersession logic only fires when the *exact same subject+predicate* pair is re-extracted. If a new conversation contradicts an existing fact through a different predicate, both facts coexist as `current`.

**Example gap**:
- Fact A (current): `subject="Database"`, `predicate="uses"`, `object="PostgreSQL"` → `temporal_status="current"`
- New input: `subject="Database"`, `predicate="migrated to"`, `object="MySQL"`
- Result: Both facts remain `current`. No contradiction flag. No supersession.

**Impact**: Persistent memory will contain contradictory facts presented equally to retrieval.

### 3.3 No Decision Supersession or Deduplication

**Evidence**: `pipeline.py` lines 108-116 — decisions are created without checking for existing ones.

```python
for dec in decisions:
    db_dec = Decision(
        ...
        temporal_status="current",
        status="active",
    )
    db.add(db_dec)
```

Every decision from every ingestion is appended. Identical decisions from re-ingestion create duplicates.

### 3.4 No Version Numbering

**Evidence**: Neither `Fact` nor `Decision` has a `version` column. No version counter is incremented on supersession.

**Impact**: Cannot express "this is version 3 of this fact." Cannot support rollback to a prior version.

### 3.5 No Retraction Mechanism

**Evidence**: No `status = "retracted"` option. No `retraction_reason` field. No API endpoint for retracting a fact.

A user who discovers a fact is wrong has no programmatic way to mark it as retracted — only to delete it (hard or soft).

---

## 4. Temporal Retrieval Gaps

### 4.1 M5 Retrieval: No Temporal Context in Output

**Evidence**: `app/services/m5_retrieval.py` — `retrieve_for_chat()` returns `temporal_status` in the provenance dict, but the formatted context string for the LLM is:

```python
context_parts.append(f"[FACT] {item.content}")
```

No temporal context (`historical`, `current`, `when superseded`) is passed to the LLM.

**Impact**: The LLM may reason over superseded facts as if they were current, because the prompt contains no temporal signal.

### 4.2 M5: Recency Score Uses `created_at`, Not `temporal_status`

**Evidence**: `_recency_score()` in `m5_retrieval.py` only considers `created_at`. A fact that was superseded yesterday but created 6 months ago will score lower than a fresh current fact — but a fact superseded 2 minutes ago will still appear in results if its `created_at` is recent.

**Impact**: Superseded facts can surface in retrieval before they age out naturally.

### 4.3 No Graph Temporal Propagation

**Evidence**: `app/services/m4_graph.py` — `persist_graph()` does not check or update `temporal_status` on edges when underlying facts change. Graph edges are created at ingest time and never revisited.

**Impact**: If a fact about "Postgres → production" is superseded by "MySQL → production", the graph edge `Postgres —connects_to→ production` remains `temporal_status="current"`.

---

## 5. Audit Gaps

### 5.1 No Audit Event for Supersession

**Evidence**: `app/services/audit/` — constants include `INGEST_COMPLETED`, `INGEST_FAILED`, `SOURCE_DELETED`, etc. No `FACT_SUPERSEDED`, `FACT_CONTRADICTED`, or `DECISION_SUPERSEDED` event type.

**Evidence**: `pipeline.py` — the supersession logic (lines 95-101) does not call `_audit.emit()` for the supersession event. The audit log records ingest start/end but not individual supersession events.

**Impact**: Cannot reconstruct when a fact was superseded or by what new fact. No audit trail for temporal transitions.

### 5.2 No Provenance Event for Supersession

**Evidence**: `app/models.py` — `Provenance` model records retrieval sources but not temporal transitions. No supersession provenance record is created.

---

## 6. Soft-Delete + Supersession Interaction

### 6.1 Fact Can Be Both `deleted_at IS NOT NULL` and `temporal_status = "historical"`

**Evidence**: Both `deleted_at` and `temporal_status` exist on `Fact`. No code prevents a fact from having both set.

**Impact**: Query filtering becomes ambiguous. A query for `temporal_status="current" AND deleted_at IS NULL` excludes historical facts. A query for `deleted_at IS NULL` includes both current and historical facts. The interaction is not formally defined.

### 6.2 Supersession Does Not Propagate to Graph Edges

**Evidence**: When a fact is superseded in `pipeline.py`, `GraphEdge` records are not updated. Edges derived from the old fact remain active.

---

## 7. Gap Matrix

| Gap | Severity | Blocks Persistent Memory | Blocks Memory Intelligence | Evidence File |
|-----|----------|--------------------------|----------------------------|---------------|
| No `supersedes` FK on Fact | HIGH | YES | YES | `app/models.py` |
| No `supersedes` FK on Decision | HIGH | YES | YES | `app/models.py` |
| No contradiction detection | HIGH | YES | YES | `app/services/pipeline.py` |
| No Decision supersession | MEDIUM | YES | YES | `app/services/pipeline.py:108-116` |
| No version numbering | MEDIUM | PARTIAL | YES | `app/models.py` |
| No retraction mechanism | MEDIUM | PARTIAL | YES | `app/api/ingest.py` |
| M5 no temporal context in LLM prompt | MEDIUM | NO | YES | `app/services/m5_retrieval.py` |
| No graph temporal propagation | MEDIUM | YES | YES | `app/services/m4_graph.py` |
| No supersession audit event | MEDIUM | PARTIAL | YES | `app/services/audit/` |
| m3_temporal.py functions never called | LOW | NO | NO | `app/services/pipeline.py` |
| Soft-delete vs temporal_status ambiguity | MEDIUM | PARTIAL | YES | `app/models.py` |
| Recency score ignores temporal_status | LOW | NO | PARTIAL | `app/services/m5_retrieval.py` |

---

## 8. What a Future Memory Intelligence Layer Should NOT Trust

1. **Lineage**: Cannot trace fact A → fact B (supersession chain). No `supersedes` field.
2. **Contradictions**: Cannot detect when two current facts contradict each other.
3. **Temporal context in LLM prompts**: The LLM receives facts without temporal annotation — cannot distinguish current from historical.
4. **Graph temporal accuracy**: Graph edges may reference entities whose underlying facts are superseded.
5. **Version history**: Cannot roll back or show "what was known at time T."
6. **Retraction**: Cannot express "this fact was retracted" as a first-class operation.

---

## 9. Recommended Conditions Before Memory Intelligence

The following **must** be implemented before the Memory Intelligence Layer can safely reason over temporal data:

1. `supersedes` and `superseded_by` FK fields on `Fact` and `Decision`
2. Explicit contradiction detection (at minimum, subject-level conflict detection)
3. Version counter on `Fact` and `Decision`
4. Supersession audit events (`FACT_SUPERSEDED`)
5. Temporal context in M5 retrieval output passed to LLM prompt
6. Graph edge temporal status propagation on fact supersession
7. Formalized interaction between `deleted_at` and `temporal_status` (one should be canonical)

Until these exist, any memory intelligence reasoning over temporal state is **untrusted**.
