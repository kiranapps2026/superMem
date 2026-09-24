# Memory Identity Contract
**Phase**: M-ARCH — Memory Architecture Freeze Gate
**Status**: PROPOSED — requires review and approval before implementation
**Created**: 2026-09-10

---

## 1. Purpose

This contract defines the **identity system** for memory objects in SwarmVault.
Every memory must have a stable, unique, immutable identity that persists across
the entire lifecycle — from creation through supersession, invalidation, and
potential deletion.

---

## 2. Identity Components

Every memory object carries **two identity values**:

| Component | Type | Mutability | Purpose |
|-----------|------|------------|---------|
| `memory_id` | UUID (v4) | **Immutable** | Primary key — never changes |
| `content_hash` | SHA-256 hex | **Immutable** | Content identity — for deduplication |

---

## 3. memory_id (Primary Identity)

### 3.1 Generation

```python
import uuid

memory_id = str(uuid.uuid4())  # UUID v4
```

- Generated at object creation time
- Never reused, even after deletion
- Assigned before any other fields
- Used as FK target by all referencing objects

### 3.2 Immutability Rules

| Operation | memory_id changes? | Why/Why Not |
|-----------|-------------------|-------------|
| CREATE | N/A (new) | First assignment |
| READ | No | Identity is stable |
| UPDATE | No | Identity is identity |
| SUPERSEDE | No | New memory gets new ID; old retains its ID |
| INVALIDATE | No | Identity is stable |
| DELETE | No | Soft-delete doesn't change identity |
| ARCHIVE | No | Archive doesn't change identity |
| RESTORE | No | Restore doesn't change identity |
| EXPIRATION | No | Expiry doesn't change identity |

### 3.3 Identity Scope

A `memory_id` is unique **globally** across the entire SwarmVault instance.
There is no scoping by tenant, workspace, or project for the ID itself — scope
is enforced by separate FK columns (`tenant_id`, `workspace_id`, `project_id`).

---

## 4. content_hash (Content Identity)

### 4.1 Generation

```python
import hashlib

def compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
```

- Computed from the **full raw content** before any transformation
- Used for deduplication at ingestion time
- Stored on the `Source` record
- Used to detect duplicate ingests

### 4.2 Where content_hash Is Used

| Model | Field | Purpose |
|-------|-------|---------|
| `Source` | `content_hash` | Dedup across all sources in workspace |
| `Memory` (proposed) | `content_hash` | Dedup across all memories |

### 4.3 Deduplication Logic

```python
# Ingestion dedup (current)
existing = await db.execute(
    select(Source).where(
        Source.workspace_id == workspace_id,
        Source.content_hash == content_hash,
    )
)
if existing.scalar_one_or_none():
    return "duplicate — reuse existing source"

# Memory dedup (proposed)
existing = await db.execute(
    select(Memory).where(
        Memory.workspace_id == workspace_id,
        Memory.content_hash == content_hash,
        Memory.temporal_status == "current",
    )
)
if existing.scalar_one_or_none():
    return "duplicate — link to existing memory"
```

**Current gap**: Memory deduplication does not exist. Multiple users/agents can
create identical memories in the same workspace.

---

## 5. Lineage Identity

### 5.1 Supersession Chain

When memory B supersedes memory A:

```
A.memory_id ──(supersedes)──▶ B.memory_id
B.supersedes ──▶ A.memory_id
A.superseded_by ──▶ B.memory_id
```

The chain is:
```
C ──supersedes──▶ B ──supersedes──▶ A
```

**Query**: "What is the latest version of this fact?"
```sql
SELECT * FROM memories
WHERE subject = 'Database' AND predicate = 'uses'
  AND temporal_status = 'current';
```

**Query**: "What was the previous version?"
```sql
SELECT * FROM memories
WHERE id = (SELECT supersedes FROM memories WHERE id = 'B');
```

### 5.2 Derivation Chain

When intelligence layer synthesizes memory D from memories B and C:

```
B ──(derives_from)──▶ D
C ──(derives_from)──▶ D
D.provenance = [
  {"event_type": "derive", "input_ref": "B", ...},
  {"event_type": "derive", "input_ref": "C", ...},
]
```

**Current**: `derives_from` does not exist as a structured field. It would be
stored in `provenance` events.

### 5.3 Contradiction Chain

When memory B contradicts memory A:

```
A ──(contradicts)──▶ B  (graph edge, bidirectional)
B ──(contradicts)──▶ A  (graph edge, bidirectional)
```

Stored as two `GraphEdge` records with `relationship_type = "contradicts"`.

---

## 6. Identity in Graph

### 6.1 GraphNode ↔ Memory Identity

```
Memory (memory_id) ──1:1──▶ GraphNode (external_id = memory_id)
```

**Current**: GraphNode has `external_id` which can reference a `source_id` or
`session_id`. It does NOT currently reference `memory_id`.

**Contract**: GraphNode.external_id MAY reference memory_id when the node
represents a fact, decision, or memory object.

### 6.2 GraphEdge ↔ Memory Identity

```
GraphEdge (source_node_id) ──▶ GraphNode ──▶ Memory
GraphEdge (target_node_id) ──▶ GraphNode ──▶ Memory
```

Edges represent relationships between memories via their graph node representations.

---

## 7. Identity in Provenance

### 7.1 Provenance References

Every provenance event MUST reference identities:

```json
{
  "event_type": "supersede",
  "transformation": {
    "input_ref": "memory_id_of_old_fact",
    "output_ref": "memory_id_of_new_fact"
  }
}
```

### 7.2 Provenance Completeness

A memory's provenance is **complete** when:
1. First event is `ingest` with a valid `source_id`
2. All `extract` events reference valid `source_id` or `message_id`
3. All `supersede` events reference valid `supersedes` memory IDs
4. Chain has no gaps (every event links to a previous event)

---

## 8. Identity Verification

### 8.1 Content Hash Verification

On retrieval, the system MAY verify that `content_hash` matches the current content:

```python
def verify_content_hash(content: str, expected_hash: str) -> bool:
    return hashlib.sha256(content.encode("utf-8")).hexdigest() == expected_hash
```

**Current**: Not implemented. Content hash is computed at ingestion only.

### 8.2 Identity Immutability Check

```python
def assert_identity_immutable(memory: Memory, field: str):
    """Raise if an identity field is being modified."""
    if field in ("memory_id", "content_hash"):
        raise IdentityMutationError(f"Cannot modify {field}")
```

**Current**: No such check exists. SQLAlchemy will allow updates to any column.

---

## 9. Cross-System Identity

### 9.1 SwarmVault Internal → External

| SwarmVault ID | External System | Mapping |
|---------------|----------------|---------|
| `memory_id` | Agent session | `agent.memory_id` in UniversalAgentEvent |
| `session_id` | Claude Code conversation | `source.external_id` |
| `source_id` | Original file/API | `source.external_id` + `source.content_hash` |

### 9.2 External → SwarmVault Internal

| External ID | SwarmVault ID | Mapping |
|-------------|--------------|---------|
| Claude Code message index | `normalized_messages.external_id` | Set by connector |
| ChatGPT message ID | `normalized_messages.external_id` | Set by connector |
| API request ID | `audit_events.request_id` | Set by middleware |

---

## 10. Implementation Requirements

| Requirement | Priority | Effort |
|-------------|----------|--------|
| Add `content_hash` to `memories` table | P1 | LOW |
| Implement content hash verification | P2 | LOW |
| Add identity immutability enforcement | P1 | LOW |
| Link GraphNode.external_id to memory_id | P1 | MEDIUM |
| Implement memory dedup by content_hash | P1 | MEDIUM |
| Add `supersedes` FK column to memories | P0 | MEDIUM |
| Document cross-system identity mapping | P2 | LOW |
