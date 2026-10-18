# Provenance & Evidence Contract
**Phase**: M-ARCH — Memory Architecture Freeze Gate
**Status**: PROPOSED — requires review and approval before implementation
**Created**: 2026-09-10

---

## 1. Purpose

Provenance is the **complete, immutable record of how a memory came to exist**.
It answers: *Who said what, when, in what context, through what process, and
with what evidence?*

This contract defines the provenance data model, the evidence chain, and the
requirements for any memory object to be considered trustable by an autonomous
agent or intelligence layer.

---

## 2. Provenance Chain Model

Every memory MUST carry a `provenance` field: a JSON array of provenance events,
ordered chronologically, from origin to current state.

### 2.1 Provenance Event Schema

```json
{
  "event_type": "ingest|extract|supersede|invalidate|certify|retract|derive|reference",
  "timestamp": "2026-09-10T12:00:00Z",
  "actor": {
    "type": "user|agent|pipeline|system|intelligence",
    "id": "uuid",
    "name": "display name"
  },
  "source": {
    "type": "conversation|document|api|agent_tool|intelligence",
    "id": "source_id or null",
    "reference": "URL, file path, or external identifier",
    "content_hash": "sha256 hash of source content"
  },
  "transformation": {
    "stage": "M0|M1|M2|M3|M4|M5|INTELLIGENCE",
    "operation": "normalize|summarize|extract|supersede|rank|synthesize",
    "input_ref": "reference to input memory or source",
    "output_ref": "reference to output memory"
  },
  "evidence": {
    "confidence": 0.85,
    "authority": 0.9,
    "source_count": 1,
    "corroborating_ids": ["memory_id_1", "memory_id_2"],
    "contradicting_ids": ["memory_id_3"]
  },
  "metadata": {
    "model": "claude-sonnet-4-5-20250929",
    "prompt_hash": "sha256 of extraction prompt",
    "session_id": "session uuid",
    "turn_id": "agent turn uuid"
  }
}
```

### 2.2 Provenance Event Types

| Event Type | Trigger | Actor | Source |
|-----------|---------|-------|--------|
| `ingest` | Raw content enters system | User/Agent | Conversation, document, API call |
| `extract` | M2 extracts fact/decision from message | Pipeline (M2) | Normalized message |
| `summarize` | M1 produces session summary | Pipeline (M1) | Conversation messages |
| `normalize` | M0 normalizes raw format | Pipeline (M0) | Raw connector output |
| `supersede` | New memory replaces old one | Pipeline/Intelligence | Existing memory |
| `invalidate` | Memory marked as false | Admin/Intelligence | Trusted source |
| `certify` | Intelligence layer certifies memory | Intelligence Layer | Verification result |
| `retract` | Memory formally withdrawn | Admin/Author | Retraction reason |
| `derive` | Memory synthesized from others | Intelligence Layer | Source memories |
| `reference` | Memory cites or links to another | Any | Related memory |

---

## 3. Evidence Requirements by Trust Level

| Trust Level | Minimum Provenance Events | Minimum Source Count | Required Evidence |
|-------------|--------------------------|---------------------|-------------------|
| UNVERIFIED | 1 (ingest) | 1 | Content hash, source reference |
| OBSERVED | 2+ (independent ingests) | 2 | Corroborating source IDs, no contradictions |
| VERIFIED | 3+ (with authority) | 1 (high-authority) | Authoritative source, confidence ≥ 0.8 |
| CERTIFIED | Full chain | 2+ | Passes intelligence validation, no contradictions, human review optional |

---

## 4. Provenance Storage

### 4.1 Per-Memory Provenance

Stored in `extra_metadata.provenance` on the memory record itself:
- Contains the full chain from origin to current state
- Immutable — new events are appended, never modified
- Limited to last 50 events (older events archived to `provenance_archive` table)

### 4.2 Retrieval Provenance

Stored in `message_provenance` table (`app/models.py:MessageProvenance`):
- Records which memories were used for a specific chat response
- Includes retrieval method, scores, latency
- Links to user message and assistant message

### 4.3 Audit Provenance

Stored in `audit_events` table (`app/models.py:AuditEvent`):
- Append-only record of all state transitions
- Includes actor, action, resource, decision, policy_id
- Never modified — only inserted

### 4.4 Source Provenance

Stored in `sources` table (`app/models.py:Source`):
- Content hash for deduplication
- External ID for original reference
- Connector type for origin tracking
- Status/stage for pipeline tracking

---

## 5. Current Provenance Gaps

### 5.1 What Exists

| Component | Evidence |
|-----------|----------|
| Source content hash | `app/models.py:Source.content_hash` |
| Source → Fact linkage | `Fact.source_id` FK |
| Source → Decision linkage | `Decision.source_id` FK |
| Message → Session linkage | `Message.session_id` FK |
| Session → Source linkage | `Session.extra_metadata.source_id` |
| Retrieval provenance | `MessageProvenance` table |
| Audit events | `AuditEvent` table |
| Fact → superseded_by | `Fact.superseded_by_id` (string, not FK) |

### 5.2 What Is Missing

| Gap | Severity | Impact |
|-----|----------|--------|
| No provenance chain on Memory model | HIGH | Cannot trace how a memory was created |
| No provenance events for supersession | HIGH | Cannot audit temporal transitions |
| No provenance events for invalidation | HIGH | Cannot audit retractions |
| `superseded_by_id` is not a FK | HIGH | Provenance chain may reference non-existent memories |
| No `supersedes` field | HIGH | Cannot trace forward lineage |
| No corroboration tracking | MEDIUM | Cannot prove OBSERVED trust level |
| No contradiction provenance | MEDIUM | Cannot record when contradictions are detected |
| No model/version in provenance | MEDIUM | Cannot reproduce extraction with same model |
| No prompt hash in provenance | MEDIUM | Cannot verify extraction consistency |

---

## 6. Provenance Verification Rules

### 6.1 Chain Completeness

A memory's provenance chain is **complete** if:
1. It contains at least one `ingest` event
2. The `ingest` event has a non-null `source.content_hash`
3. Every `extract` event references a valid `input_ref` (message or source ID)
4. Every `supersede` event references a valid `superseded_by` memory ID

### 6.2 Chain Integrity

A memory's provenance chain is **intact** if:
1. Events are in chronological order (non-decreasing timestamps)
2. No event references a memory ID from outside the same workspace
3. No event has a null `actor.id` unless it is a `system` event
4. `supersedes` / `superseded_by` references form a valid chain (no cycles)

### 6.3 Chain Trust

A memory's provenance chain is **trusted** if:
1. All source content hashes verify against stored hash
2. No `contradicts` edges to memories with higher trust level
3. Confidence ≥ authority threshold for the trust level
4. All actors in the chain are authorized for their actions

---

## 7. Evidence Retention

| Evidence Type | Retention | Deletion Rule |
|---------------|-----------|---------------|
| Memory provenance | Permanent | Never deleted (append-only) |
| Audit events | Permanent | Never deleted (append-only) |
| Source records | 7 years | Soft-delete only |
| Retrieval provenance | Permanent | Never deleted |
| Graph edges | Same as referenced memory | Deleted with memory |

---

## 8. Audit Event Types for Memory Operations

```python
# Memory lifecycle
MEMORY_CREATED = "memory.created"
MEMORY_READ = "memory.read"
MEMORY_UPDATED = "memory.updated"
MEMORY_DELETED = "memory.deleted"
MEMORY_ARCHIVED = "memory.archived"
MEMORY_RESTORED = "memory.restored"

# Knowledge validity transitions
MEMORY_SUPERSEDED = "memory.superseded"
MEMORY_INVALIDATED = "memory.invalidated"
MEMORY_EXPIRED = "memory.expired"
MEMORY_CONTRADICTED = "memory.contradicted"

# Trust level transitions
MEMORY_CORROBORATED = "memory.corroborated"
MEMORY_VERIFIED = "memory.verified"
MEMORY_CERTIFIED = "memory.certified"
MEMORY_DOWNGRADED = "memory.downgraded"

# Retrieval
MEMORY_SEARCHED = "memory.searched"
MEMORY_RETRIEVED = "memory.retrieved"
MEMORY_USED_IN_CONTEXT = "memory.used_in_context"

# Agent actions
MEMORY_AGENT_WRITE = "memory.agent_write"
MEMORY_AGENT_READ = "memory.agent_read"
```

**Current state**: Only `MEMORY_READ` and `MEMORY_SEARCH` exist in
`app/services/audit/constants.py`. All others are missing.

---

## 9. Implementation Requirements

| Contract Requirement | Current Status | Implementation Effort |
|---------------------|----------------|----------------------|
| Provenance chain on Memory model | MISSING | HIGH — schema change |
| Provenance events for all transitions | PARTIAL | HIGH — new event emitters |
| `superseded_by` as proper FK | MISSING | MEDIUM — migration |
| `supersedes` FK column | MISSING | MEDIUM — migration |
| Chain completeness validation | MISSING | MEDIUM — validation logic |
| Chain integrity validation | MISSING | MEDIUM — validation logic |
| Chain trust verification | MISSING | HIGH — verification logic |
| Content hash verification | PARTIAL | LOW — extend existing |
| Audit events for memory ops | PARTIAL | MEDIUM — new constants + emitters |
