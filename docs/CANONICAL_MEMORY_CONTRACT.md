# Canonical Memory Contract
**Phase**: M-ARCH — Memory Architecture Freeze Gate
**Status**: PROPOSED — requires review and approval before implementation
**Created**: 2026-09-10

---

## 1. Purpose

This contract resolves the identity crisis in SwarmVault's memory layer. The
codebase currently contains **five overlapping representations** of "memory":

| Representation | Location | Status |
|----------------|----------|--------|
| `MemoryRecord` (dataclass) | `app/services/memory.py` | Sprint 8 — canonical service layer |
| `Memory` (ORM model) | `app/models.py:232` | Sprint 8 — PostgreSQL table `memories` |
| `Fact` (ORM model) | `app/models.py` | Sprint 2 — M2 extraction output |
| `Decision` (ORM model) | `app/models.py` | Sprint 2 — M2 extraction output |
| `MemoryCandidate` (implied) | M2 pipeline (`m2_facts.py`) | Pipeline intermediate — not persisted as separate type |

Without a contract, these drift into separate concepts. With this contract, they
become **typed variants of a single canonical memory object**.

---

## 2. Canonical Definition

**Memory** is any piece of structured or unstructured knowledge that SwarmVault
has determined is worth retaining, retrieving, and reasoning about.

Every memory object, regardless of type, MUST carry:

| Field | Type | Purpose |
|-------|------|---------|
| `memory_id` | UUID (str) | Globally unique identifier |
| `memory_type` | enum | WORKING, EPISODIC, SEMANTIC, PROCEDURAL, FACT, DECISION |
| `scope` | enum | USER, TEAM, PROJECT, WORKSPACE, TENANT |
| `tenant_id` | UUID (str) | Top-level tenancy — NEVER NULL |
| `workspace_id` | UUID (str) | Workspace boundary — NEVER NULL |
| `project_id` | UUID (str) | Optional project scoping — NULLABLE |
| `user_id` | UUID (str) | Owning/creating user — NULLABLE (agent-created) |
| `agent_id` | UUID (str) | Creating agent — NULLABLE |
| `run_id` | UUID (str) | Agent run/turn — NULLABLE |
| `content` | Text | The knowledge payload — NEVER NULL |
| `subject` | str | Structured subject (for triples) — NULLABLE for free-form |
| `predicate` | str | Structured predicate — NULLABLE for free-form |
| `object` | str | Structured object — NULLABLE for free-form |
| `confidence` | float [0.0, 1.0] | Extraction/creation confidence |
| `authority` | float [0.0, 1.0] | Source authority score |
| `importance` | float [0.0, 1.0] | Relative importance for retrieval ranking |
| `temporal_status` | enum | CURRENT, SUPERSEDED, EXPIRED, INVALIDATED |
| `status` | enum | ACTIVE, DELETED, ARCHIVED |
| `version` | int | Monotonically increasing version counter |
| `supersedes` | UUID | Points to the memory this one replaces |
| `superseded_by` | UUID | Points to the memory that replaced this one |
| `provenance` | JSON | Provenance chain (list of dicts) |
| `extra_metadata` | JSON | Arbitrary typed metadata |
| `valid_from` | datetime | When this memory became valid |
| `valid_until` | datetime | When this memory ceased to be valid |
| `expires_at` | datetime | When this memory should be automatically expired |
| `created_at` | datetime | Insertion timestamp |
| `updated_at` | datetime | Last modification timestamp |
| `deleted_at` | datetime | Soft-delete timestamp — NULLABLE |
| `content_hash` | str | SHA-256 of content — for deduplication |

---

## 3. Type Variants

The `memory_type` field determines the semantic flavor of the memory. These are
**not separate tables or separate models** — they are variants of the same
canonical object with type-specific constraints.

### 3.1 FACT

```
memory_type = "FACT"
```

A structured triple: `subject — predicate — object`.

**Required**: `subject`, `predicate`, `object`
**Optional**: `content` (human-readable rendering of the triple)
**M2 output**: Produced by `extract_facts()` in `app/services/m2_facts.py`
**M5 input**: Retrieved by `rank_facts()` in `app/services/m5_retrieval.py`
**Deduplication**: Subject+predicate match triggers supersession check
**Supersession**: YES — when same subject+predicate pair is re-extracted with different object

### 3.2 DECISION

```
memory_type = "DECISION"
```

A recorded choice, commitment, or resolution made during a conversation.

**Required**: `content`
**Optional**: `context` (why the decision was made)
**M2 output**: Produced by `extract_decisions()` in `app/services/m2_facts.py`
**M5 input**: Retrieved by `rank_decisions()` in `app/services/m5_retrieval.py`
**Deduplication**: NONE CURRENTLY — every decision is appended (GAP)
**Supersession**: NOT CURRENTLY IMPLEMENTED (GAP)

### 3.3 EPISODIC

```
memory_type = "EPISODIC"
```

A specific event, conversation, or experience tied to a particular time and context.

**Required**: `content`, `valid_from`
**Optional**: `run_id`, `session_id`
**Source**: M0 normalized messages, chat sessions
**M5 input**: NOT CURRENTLY RETRIEVED (GAP — Memory model excluded from M5)

### 3.4 SEMANTIC

```
memory_type = "SEMANTIC"
```

Generalized knowledge extracted from multiple episodes — not tied to a specific event.

**Required**: `content`
**Optional**: `subject` (concept label)
**Source**: M2/M3 generalization, intelligence layer synthesis
**M5 input**: NOT CURRENTLY RETRIEVED (GAP)

### 3.5 PROCEDURAL

```
memory_type = "PROCEDURAL"
```

A skill, workflow, or "how-to" pattern.

**Required**: `content`
**Optional**: `subject` (skill name)
**Source**: M2 extraction, user annotation, agent learning
**M5 input**: NOT CURRENTLY RETRIEVED (GAP)

### 3.6 WORKING

```
memory_type = "WORKING"
```

Short-lived, session-scoped memory. Intended to expire.

**Required**: `content`, `expires_at`
**Optional**: `session_id`, `run_id`
**Source**: Active session context, agent scratchpad
**M5 input**: NOT CURRENTLY RETRIEVED (GAP)

---

## 4. Current vs. Proposed Mapping

### 4.1 Current State (Source-of-Truth from Codebase)

| Concept | Current Table | Current Columns | Current Type Field |
|---------|--------------|-----------------|-------------------|
| Fact | `facts` | subject, predicate, object, content, confidence, authority, temporal_status, superseded_by_id, status, deleted_at | N/A (separate table) |
| Decision | `decisions` | content, context, confidence, authority, temporal_status, superseded_by_id, status, deleted_at | N/A (separate table) |
| Memory | `memories` | memory_type, content, confidence, authority, temporal_status, deleted_at, embedding, extra_metadata | `memory_type` (lowercase: "procedural_memory") |
| MemoryRecord | N/A (dataclass) | Full canonical set | `memory_type` (uppercase: "WORKING") |

### 4.2 Proposed Unified Schema

**Option A: Single Table (Recommended)**

Merge `facts`, `decisions`, and `memories` into a single `memories` table with
`memory_type` discriminator. This is the approach this contract recommends.

```
Table: memories
├── id (PK)
├── tenant_id (FK → tenants)
├── workspace_id (FK → workspaces)
├── project_id (FK → projects, nullable)
├── user_id (FK → users, nullable)
├── agent_id (nullable)
├── run_id (nullable)
├── memory_type (enum: FACT, DECISION, EPISODIC, SEMANTIC, PROCEDURAL, WORKING)
├── content (TEXT)
├── subject (nullable)
├── predicate (nullable)
├── object (nullable)
├── context (nullable)
├── confidence (float, default 0.7)
├── authority (float, default 1.0)
├── importance (float, default 0.5)
├── temporal_status (enum: CURRENT, SUPERSEDED, EXPIRED, INVALIDATED, default CURRENT)
├── status (enum: ACTIVE, DELETED, ARCHIVED, default ACTIVE)
├── version (int, default 1)
├── supersedes (FK → memories.id, nullable)
├── superseded_by (FK → memories.id, nullable)
├── provenance (JSON, nullable)
├── extra_metadata (JSON, nullable)
├── embedding (JSON, nullable)
├── content_hash (str, nullable, indexed)
├── valid_from (datetime, nullable)
├── valid_until (datetime, nullable)
├── expires_at (datetime, nullable)
├── created_at (datetime)
├── updated_at (datetime)
├── deleted_at (datetime, nullable)
└── Indexes: (workspace_id, memory_type, temporal_status), (tenant_id, workspace_id, project_id), (content_hash), (subject), (temporal_status)
```

**Option B: Separate Tables (Current — Do Not Change Yet)**

Keep `facts`, `decisions`, and `memories` as separate tables but unify their
retrieval interface. This is the transitional approach.

### 4.3 MemoryRecord ↔ ORM Mapping

`MemoryRecord` in `app/services/memory.py` is the **service-layer canonical
representation**. It maps to the `Memory` ORM model via `_persist_record()` and
`_model_to_record()`.

**Current gap**: `MemoryRecord` uses uppercase memory types (`WORKING`) while
the `Memory` ORM uses lowercase (`procedural_memory`). The `MemoryTypeMapper`
bridges this gap but the mapping is incomplete and inconsistent.

**Contract resolution**: All canonical representations use uppercase enum values.
The ORM stores lowercase strings for backward compatibility. The mapper is the
**sole** translation point. No other code should compare or assign memory types
directly.

---

## 5. MemoryCandidate (Pipeline Intermediate)

During M2 extraction, `extract_facts_and_decisions()` in `app/services/m2_facts.py`
produces intermediate objects that are immediately persisted as `Fact` or `Decision`
rows. There is no intermediate "MemoryCandidate" model in the database.

**Contract**: The pipeline's intermediate representations (`Fact`, `Decision` data
classes within `m2_facts.py`) are **not** durable memory objects. They become
durable only after passing M3 validation and M4 graph enrichment. The transition
point is the `db.add()` call in `run_pipeline()`.

---

## 6. Memory Identity

Every memory object MUST have a stable, immutable `memory_id`. This ID is:

- Assigned at creation (UUID v4)
- Never reused
- Never changed
- The sole reference point for all relationships (supersedes, provenance, graph edges)

**Critical**: The `supersedes` and `superseded_by` fields reference `memory_id`.
This creates a doubly-linked list of memory versions within the same canonical
object lineage.

---

## 7. Memory Type Enum (Canonical)

```python
class MemoryType(str, enum.Enum):
    FACT = "FACT"
    DECISION = "DECISION"
    EPISODIC = "EPISODIC"
    SEMANTIC = "SEMANTIC"
    PROCEDURAL = "PROCEDURAL"
    WORKING = "WORKING"
```

**Storage format**: Uppercase string in `extra_metadata.memory_type`.
**ORM format**: Lowercase string in `memories.memory_type` column (legacy).
**API format**: Uppercase string in JSON responses.

---

## 8. Memory Scope Enum (Canonical)

```python
class MemoryScope(str, enum.Enum):
    USER = "USER"
    TEAM = "TEAM"
    PROJECT = "PROJECT"
    WORKSPACE = "WORKSPACE"
    TENANT = "TENANT"
```

**Visibility rules**:
- TENANT: Visible to all users in the tenant
- WORKSPACE: Visible to all members of the workspace
- PROJECT: Visible to all members of the project
- TEAM: Visible to team members only
- USER: Visible to the owning user only

**Default**: USER for personally created memories, WORKSPACE for pipeline-extracted facts/decisions.

---

## 9. Memory Lifecycle vs. Knowledge Validity

These are **orthogonal** dimensions that are currently conflated:

| Dimension | Values | Column | Independent? |
|-----------|--------|--------|-------------|
| Lifecycle (deletion) | ACTIVE, DELETED, ARCHIVED | `status` + `deleted_at` | YES |
| Knowledge validity | CURRENT, SUPERSEDED, EXPIRED, INVALIDATED | `temporal_status` | YES |
| Trust level | UNVERIFIED, OBSERVED, VERIFIED, CERTIFIED | `extra_metadata.trust_level` | YES |

**Current conflation**: When a fact is superseded, `temporal_status` is set to
`"historical"` and `status` remains `"active"`. These should be independent.

**Contract**:
- `status` controls visibility (deleted = hidden from all queries)
- `temporal_status` controls knowledge validity (superseded = known to be outdated)
- `extra_metadata.trust_level` controls whether the intelligence layer may act on it

---

## 10. MemoryCandidate vs. Memory

| | MemoryCandidate | Memory |
|--|-----------------|--------|
| Persisted | NO | YES |
| Has memory_id | NO | YES |
| Has provenance | NO | YES |
| Has confidence | MAYBE | YES |
| Has authority | MAYBE | YES |
| Retrievable | NO | YES |
| M5 input | NO | YES |
| Audit logged | NO | YES |

**Contract**: A MemoryCandidate becomes a Memory **only** after:
1. Passing M3 temporal validation (supersession check)
2. Passing M4 graph enrichment (optional but recommended)
3. Receiving a `memory_id` (UUID assigned at `db.add()`)
4. Being persisted to PostgreSQL

---

## 11. Implementation Impact

This contract requires:

| Change | Scope | Migration Required |
|--------|-------|-------------------|
| Unify `facts` + `decisions` + `memories` into single table | HIGH | YES — data migration |
| Add `supersedes`/`superseded_by` FK fields | MEDIUM | YES — new columns |
| Add `version` field | MEDIUM | YES — new column |
| Add `content_hash` to all memory types | LOW | YES — new column + backfill |
| Normalize `memory_type` values | LOW | YES — data migration |
| Add `trust_level` to `extra_metadata` | LOW | NO — JSON field exists |
| Separate `status` from `temporal_status` logic | MEDIUM | NO — columns exist, logic change |
| Unify M5 retrieval over all types | HIGH | NO — query change only |

---

## 12. Open Questions

1. Should `MemoryCandidate` become a first-class ORM model, or remain a pipeline-internal dataclass?
2. Should the `embedding` column on `Memory` be populated by M2 or by a future intelligence layer?
3. Should `superseded_by_id` on `Fact`/`Decision` become proper FK constraints pointing to `memories.id`?
4. Should `importance` be pipeline-computed or user/agent-assigned?
