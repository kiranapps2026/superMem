# SwarmVault WebApp — Canonical Memory Model

> **Status:** Architecture reference
> **Date:** 2026-09-10
> **Scope:** Defines the unified memory object that resolves the current fragmentation across `Memory`, `Fact`, `Decision`, `GraphNode`, `GraphEdge`, and `Source` tables.

---

## Table of Contents

1. [Current Memory Entity Inventory](#section-1-current-memory-entity-inventory)
2. [The Canonical Memory Object](#section-2-the-canonical-memory-object)
3. [Current → Canonical Mapping](#section-3-current--canonical-mapping)
4. [Gap Analysis](#section-4-gap-analysis)

---

## Section 1: Current Memory Entity Inventory

### 1.1 Memory (`memories`)

**File:** `app/models.py` lines 232–267
**Created by:** `MemoryService.write()` in `app/services/memory.py`
**Purpose:** Generic, governed memory store. The only memory entity that flows through the Policy Engine (Sprint 8). Used for working, episodic, semantic, procedural, user, team, project, and agent memories.

| Column | Type | Nullable | Default | Indexed |
|---|---|---|---|---|
| `id` | String(36) | No | uuid4 PK | — |
| `tenant_id` | String(36) FK `tenants.id` | No | — | Yes |
| `workspace_id` | String(36) FK `workspaces.id` | No | — | Yes |
| `user_id` | String(36) FK `users.id` | No | — | — |
| `agent_id` | String(36) | Yes | — | — |
| `run_id` | String(36) | Yes | — | — |
| `project_id` | String(36) FK `projects.id` | Yes | — | Yes |
| `memory_type` | String(50) | No | `"procedural_memory"` | — |
| `content` | Text | No | — | — |
| `metadata` | JSON | Yes | — | — |
| `embedding` | JSON | Yes | — | — |
| `temporal_status` | String(50) | No | `"current"` | Yes |
| `confidence` | Float | No | 0.7 | — |
| `authority` | Float | No | 1.0 | — |
| `deleted_at` | DateTime | Yes | — | Yes |
| `created_at` | DateTime | No | utcnow | — |
| `updated_at` | DateTime | No | utcnow (onupdate) | — |

**Relationships:**
- Belongs to `Tenant` (FK `tenant_id`)
- Scoped by `Workspace` (FK `workspace_id`)
- Optionally scoped by `Project` (FK `project_id`)
- Optionally linked to `User` (FK `user_id`)

**Key characteristics:**
- Has `embedding` column for vector search — the only memory entity with native embedding storage
- Has `agent_id` and `run_id` for agent-run traceability
- `memory_type` is a free string (default `"procedural_memory"`); actual taxonomy is enforced by `MemoryTypeMapper` in the service layer, not the DB
- `metadata` stores arbitrary user/system fields; the service layer packs `predicate`, `value`, `scope`, `authority` (dict), `importance`, `permissions`, `provenance`, `version`, `supersedes`, `superseded_by` into it
- No `subject` column — subject is derived from `content[:100]` at read time (`memory.py` line 306)

---

### 1.2 Fact (`facts`)

**File:** `app/models.py` lines 413–464
**Created by:** `pipeline.py` lines 108–154 (M2 extraction); `m2_facts.py` provides the extraction logic
**Purpose:** Subject-predicate-object triples extracted from conversations by deterministic pattern matching. Implements temporal truth via M3 supersession.

| Column | Type | Nullable | Default | Indexed |
|---|---|---|---|---|
| `id` | String(36) | No | uuid4 PK | — |
| `workspace_id` | String(36) FK `workspaces.id` | No | — | — |
| `project_id` | String(36) | Yes | — | — |
| `source_id` | String(36) FK `sources.id` | Yes | — | — |
| `session_id` | String(36) FK `sessions.id` | Yes | — | — |
| `subject` | String(500) | No | — | Yes |
| `predicate` | String(100) | No | — | — |
| `object` | String(500) | No | — | — |
| `content` | Text | No | — | — |
| `confidence` | Float | No | 1.0 | — |
| `authority` | Float | No | 1.0 | — |
| `temporal_status` | String(20) | No | `"current"` | Yes |
| `superseded_by_id` | String(36) | Yes | — | Yes |
| `status` | String(20) | No | `"active"` | — |
| `metadata` | JSON | Yes | — | — |
| `created_at` | DateTime | No | utcnow | — |
| `updated_at` | DateTime | No | utcnow (onupdate) | — |
| `deleted_at` | DateTime | Yes | — | — |

**Relationships:**
- FK `source_id` → `Source` (back_populates `facts`)
- No FK back-reference from `superseded_by_id` → `Fact.id` (it's a plain column, not a relationship)

**Key characteristics:**
- `content` is a human-readable reconstruction: `"{subject} {predicate} {object}"` (`m2_facts.py` line 103)
- `confidence` is hardcoded to `0.8` during extraction (`m2_facts.py` line 109)
- `authority` defaults to `1.0` but is never set during extraction
- `superseded_by_id` points to the Fact that replaced this one (M3 supersession)
- `temporal_status` values: `"current"`, `"historical"`
- `status` values: `"active"`, `"superseded"`, `"deleted"` (though deleted is handled by `deleted_at`)
- Deduplication in `pipeline.py` line 113: checks for existing fact with same `workspace_id + subject + predicate + temporal_status="current"`

---

### 1.3 Decision (`decisions`)

**File:** `app/models.py` lines 467–517
**Created by:** `pipeline.py` lines 156–171 (M2 extraction)
**Purpose:** Extracted commitment/choice statements from conversations.

| Column | Type | Nullable | Default | Indexed |
|---|---|---|---|---|
| `id` | String(36) | No | uuid4 PK | — |
| `workspace_id` | String(36) FK `workspaces.id` | No | — | — |
| `project_id` | String(36) | Yes | — | — |
| `source_id` | String(36) FK `sources.id` | Yes | — | — |
| `session_id` | String(36) FK `sessions.id` | Yes | — | — |
| `content` | Text | No | — | — |
| `context` | Text | Yes | — | — |
| `confidence` | Float | No | 1.0 | — |
| `authority` | Float | No | 1.0 | — |
| `temporal_status` | String(20) | No | `"current"` | — |
| `superseded_by_id` | String(36) | Yes | — | Yes |
| `status` | String(20) | No | `"active"` | — |
| `metadata` | JSON | Yes | — | — |
| `created_at` | DateTime | No | utcnow | — |
| `updated_at` | DateTime | No | utcnow (onupdate) | — |
| `deleted_at` | DateTime | Yes | — | — |

**Relationships:**
- FK `source_id` → `Source` (back_populates `decisions`)

**Key characteristics:**
- Structurally nearly identical to `Fact` but lacks `subject`, `predicate`, `object`
- Has `context` column (first 500 chars of source text) that `Fact` lacks
- `content` is the decision text; `context` is the surrounding conversation
- No deduplication in pipeline — every extracted decision is persisted (`pipeline.py` line 157)
- `confidence` hardcoded to `0.75` during extraction (`m2_facts.py` line 134)

---

### 1.4 GraphNode (`graph_nodes`)

**File:** `app/models.py` lines 520–558
**Created by:** `m4_graph.py` `persist_graph()` lines 102–192
**Purpose:** Entities extracted from conversation text and stored as nodes in the knowledge graph.

| Column | Type | Nullable | Default | Indexed |
|---|---|---|---|---|
| `id` | String(36) | No | uuid4 PK | — |
| `workspace_id` | String(36) FK `workspaces.id` | No | — | — |
| `project_id` | String(36) | Yes | — | — |
| `external_id` | String(255) | Yes | — | Yes |
| `label` | String(500) | No | — | — |
| `node_type` | String(50) | No | `"entity"` | — |
| `properties` | JSON | Yes | — | — |
| `created_at` | DateTime | No | utcnow | — |
| `updated_at` | DateTime | No | utcnow (onupdate) | — |
| `deleted_at` | DateTime | Yes | — | — |
| `temporal_status` | String(20) | No | `"current"` | — |

**Relationships:**
- Referenced by `GraphEdge.source_node_id` and `GraphEdge.target_node_id`
- Unique constraint: `(workspace_id, external_id)` — nodes are de-duplicated by label within a workspace

**Key characteristics:**
- `label` is the normalized entity name (max 500 chars, whitespace-collapsed)
- `node_type` is classified by keyword matching: `"technology"`, `"project"`, or `"entity"` (`m4_graph.py` lines 85–98)
- `properties` stores arbitrary attributes; at creation it's set to `{"source": "m4_extraction"}` (`m4_graph.py` line 147)
- `external_id` stores the entity label for de-duplication lookups
- **No `confidence` or `authority` columns** — graph nodes have no confidence tracking
- **No `tenant_id`** — only `workspace_id`
- **No `source_id`** — provenance is lost at node creation (only edges carry `source_id`)

---

### 1.5 GraphEdge (`graph_edges`)

**File:** `app/models.py` lines 561–604
**Created by:** `m4_graph.py` `persist_graph()` lines 156–189
**Purpose:** Relationships between graph nodes, extracted from conversation text.

| Column | Type | Nullable | Default | Indexed |
|---|---|---|---|---|
| `id` | String(36) | No | uuid4 PK | — |
| `workspace_id` | String(36) FK `workspaces.id` | No | — | — |
| `project_id` | String(36) | Yes | — | — |
| `source_node_id` | String(36) FK `graph_nodes.id` | No | — | Yes (composite) |
| `target_node_id` | String(36) FK `graph_nodes.id` | No | — | Yes (composite) |
| `relationship_type` | String(100) | No | — | — |
| `properties` | JSON | Yes | — | — |
| `confidence` | Float | No | 1.0 | — |
| `temporal_status` | String(20) | No | `"current"` | — |
| `source_id` | String(36) FK `sources.id` | Yes | — | Yes |
| `created_at` | DateTime | No | utcnow | — |
| `updated_at` | DateTime | No | utcnow (onupdate) | — |
| `deleted_at` | DateTime | Yes | — | — |

**Relationships:**
- FK `source_node_id` → `GraphNode`
- FK `target_node_id` → `GraphNode`
- FK `source_id` → `Source` (back_populates `graph_edges`)

**Key characteristics:**
- `confidence` is hardcoded to `0.8` (`m4_graph.py` line 184)
- `relationship_type` values: `"uses"`, `"connects_to"`, `"depends_on"`, `"is_a"` (defined in `m4_graph.py` lines 14–38)
- `temporal_status` is set but **no supersession logic exists for edges** — old edges are never marked historical
- **No `tenant_id`** — only `workspace_id`
- **No `authority` column** — unlike Facts and Decisions

---

### 1.5 Source (`sources`)

**File:** `app/models.py` lines 302–366
**Created by:** `pipeline.py` line 52
**Purpose:** Represents an ingested conversation or document (M0 input). The root provenance anchor for all pipeline outputs.

| Column | Type | Nullable | Default | Indexed |
|---|---|---|---|---|
| `id` | String(36) | No | uuid4 PK | — |
| `project_id` | String(36) | No | — | — |
| `workspace_id` | String(36) FK `workspaces.id` | No | — | Yes (composite w/ tenant) |
| `tenant_id` | String(36) | No | — | Yes (composite w/ workspace) |
| `source_type` | String(50) | No | — | — |
| `external_id` | String(255) | Yes | — | Yes |
| `content_hash` | String(64) | Yes | — | Yes |
| `title` | String(500) | Yes | — | — |
| `description` | Text | Yes | — | — |
| `raw_content_path` | String | Yes | — | — |
| `message_count` | Integer | No | 0 | — |
| `status` | String(20) | No | `"queued"` | — |
| `stage` | String(50) | Yes | — | — |
| `progress` | Integer | No | 0 | — |
| `error_message` | Text | Yes | — | — |
| `config` | JSON | Yes | — | — |
| `started_at` | DateTime | Yes | — | — |
| `completed_at` | DateTime | Yes | — | — |
| `created_at` | DateTime | No | utcnow | — |
| `updated_at` | DateTime | No | utcnow (onupdate) | — |
| `deleted_at` | DateTime | Yes | — | — |

**Relationships:**
- Has many `NormalizedMessage` (cascade delete)
- Has many `Fact` (back_populates `source`)
- Has many `Decision` (back_populates `source`)
- Has many `GraphEdge` (back_populates `graph_edges`)

**Key characteristics:**
- Tracks pipeline progress via `stage` (M0→M5) and `progress` (0–100)
- `content_hash` enables idempotent re-ingestion
- Not a "memory" per se, but the **provenance root** for all extracted memory entities

---

### 1.6 Supporting Entities (Not Primary Memory, But Part of the Provenance Chain)

#### Session (`sessions`)

**File:** `app/models.py` lines 165–188
**Purpose:** Groups messages into a conversational session. Acts as a logical container for message-level provenance.

| Column | Type | Nullable |
|---|---|---|
| `id` | String(36) PK | No |
| `workspace_id` | String(36) FK | No |
| `user_id` | String(36) FK | No |
| `title` | String(255) | Yes |
| `metadata` | JSON | Yes |
| `created_at` | DateTime | No |
| `updated_at` | DateTime | No |
| `deleted_at` | DateTime | Yes |

#### Message (`messages`)

**File:** `app/models.py` lines 191–206
**Purpose:** Individual chat message within a session. Raw content that feeds into M2 extraction.

| Column | Type | Nullable |
|---|---|---|
| `id` | String(36) PK | No |
| `session_id` | String(36) FK | No |
| `role` | String(20) | No |
| `content` | Text | No |
| `metadata` | JSON | Yes |
| `created_at` | DateTime | No |

#### MessageProvenance (`message_provenance`)

**File:** `app/models.py` lines 607–653
**Purpose:** Full provenance tracking for every chat response. Records which memories were retrieved to generate a response.

| Column | Type | Nullable |
|---|---|---|
| `id` | String(36) PK | No |
| `workspace_id` | String(36) FK | No |
| `project_id` | String(36) | Yes |
| `session_id` | String(36) FK | Yes |
| `user_message_id` | String(36) FK `messages.id` | Yes |
| `assistant_message_id` | String(36) FK `messages.id` | Yes |
| `model` | String(100) | No |
| `provider` | String(50) | No |
| `retrieval_method` | String(50) | No (default `"hybrid"`) |
| `memory_ids_used` | JSON | Yes |
| `retrieval_sources` | JSON | Yes |
| `user_message_preview` | String(500) | Yes |
| `prompt_tokens` | Integer | No (default 0) |
| `completion_tokens` | Integer | No (default 0) |
| `total_tokens` | Integer | No (default 0) |
| `latency_ms` | Integer | Yes |
| `confidence` | Float | Yes |
| `created_at` | DateTime | No |

#### AuditEvent (`audit_events`)

**File:** `app/models.py` lines 788–837
**Purpose:** Append-only audit log for all memory operations. Never updated after creation.

| Column | Type | Nullable |
|---|---|---|
| `id` | String(36) PK | No |
| `tenant_id` | String(36) FK | Yes |
| `workspace_id` | String(36) | Yes |
| `project_id` | String(36) | Yes |
| `principal_id` | String(36) | Yes |
| `principal_type` | String(20) | Yes |
| `resource_type` | String(50) | Yes |
| `resource_id` | String(36) | Yes |
| `action` | String(50) | Yes |
| `decision` | String(20) | Yes |
| `policy_id` | String(36) | Yes |
| `policy_version` | Integer | Yes |
| `request_id` | String(36) | Yes |
| `correlation_id` | String(36) | Yes |
| `event_type` | String(50) | No |
| `result_status` | String(20) | No |
| `duration_ms` | Integer | Yes |
| `limits` | JSON | Yes |
| `provenance_reference` | String(255) | Yes |
| `event_metadata` | JSON | Yes |
| `timestamp` | DateTime | No |

---

## Section 2: The Canonical Memory Object

### 2.1 Design Principles

The canonical memory object must:

1. **Unify without erasing** — Preserve the semantic distinctions between facts, decisions, graph elements, and generic memories while providing a single access path.
2. **Be persistence-agnostic** — The canonical form exists independently of whether it is stored in PostgreSQL, a graph DB, a vector store, or a file.
3. **Carry its own provenance** — Every memory record must be self-describing regarding its origin, authority, and derivation chain.
4. **Separate temporal validity from lifecycle** — A fact can be historically true (`temporal_status="historical"`) while still being an active, non-deleted record (`status="active"`).
5. **Support supersession natively** — The version chain and supersession links are first-class fields, not ad-hoc columns on individual tables.
6. **Enable contradiction tracking** — When facts contradict each other, both should remain accessible with an explicit contradiction link.

### 2.2 Canonical Schema

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CANONICAL MEMORY OBJECT                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │  IDENTITY                                                     │    │
│  │  ─────────────────────────────────────────────────────────── │    │
│  │  memory_id    : UUID (primary key)                            │    │
│  │  version      : integer (monotonically increasing)            │    │
│  │  memory_type  : enum                                       │    │
│  │                  WORKING | EPISODIC | SEMANTIC | PROCEDURAL   │    │
│  │                  | FACT | DECISION | GRAPH_NODE | GRAPH_EDGE  │    │
│  │                  | SOURCE | SESSION | MESSAGE                 │    │
│  │  content_variant : enum                                       │    │
│  │                  FREE_TEXT | SPO_TRIPLE | DECISION_TEXT       │    │
│  │                  | GRAPH_ELEMENT | CONVERSATION_TURN          │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │  SCOPE (tenant hierarchy)                                     │    │
│  │  ─────────────────────────────────────────────────────────── │    │
│  │  tenant_id    : UUID                                          │    │
│  │  workspace_id : UUID                                          │    │
│  │  project_id   : UUID (nullable)                               │    │
│  │  team_id      : UUID (nullable)                               │    │
│  │  user_id      : UUID (nullable)                               │    │
│  │  agent_id     : UUID (nullable)                               │    │
│  │  run_id       : UUID (nullable)                               │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌───────────────────────────────────────────────────────���───────┐    │
│  │  CONTENT REPRESENTATION                                        │    │
│  │  ─────────────────────────────────────────────────────────── │    │
│  │  subject   : string  (for SPO triples)                        │    │
│  │  predicate : string  (for SPO triples)                        │    │
│  │  value     : any     (for SPO triples / graph targets)         │    │
│  │  content   : text    (free-form content, always present)       │    │
│  │  context   : text    (surrounding conversation, optional)      │    │
│  │                                                                 │    │
│  │  ┌───────────────── GRAPH-SPECIFIC ────────────────────┐      │    │
│  │  │  graph_label      : string  (node/edge label)        │      │    │
│  │  │  graph_node_type  : string  (entity/technology/etc)  │      │    │
│  │  │  graph_rel_type   : string  (uses/depends_on/etc)    │      │    │
│  │  │  source_node_id   : UUID    (for edges)              │      │    │
│  │  │  target_node_id   : UUID    (for edges)              │      │    │
│  │  │  graph_properties : JSON    (arbitrary attributes)   │      │    │
│  │  └─────────────────────────────────────────────────────┘      │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │  PROVENANCE CHAIN                                              │    │
│  │  ─────────────────────────────────────────────────────────── │    │
│  │  source_id          : UUID  (→ Source.id, the ingestion root) │    │
│  │  session_id         : UUID  (→ Session.id)                     │    │
│  │  provenance         : list[{                                   │    │
│  │      source, source_id, creator, created_at,                   │    │
│  │      method, authority, confidence, version                    │    │
│  │  }]                                                            │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │  CONFIDENCE & AUTHORITY                                        │    │
│  │  ─────────────────────────────────────────────────────────── │    │
│  │  confidence : float  [0.0, 1.0]                                │    │
│  │  authority  : dict{ score: float, source: string,              │    │
│  │                      creator: string, ... }                    │    │
│  │  importance : float  [0.0, 1.0]                                │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │  TEMPORAL VALIDITY  (separate from lifecycle)                  │    │
│  │  ─────────────────────────────────────────────────────────── │    │
│  │  valid_from : datetime  (when this became true)                │    │
│  │  valid_until: datetime  (when this stopped being true)         │    │
│  │  expires_at : datetime  (soft expiry for TTL memories)         │    │
│  │  temporal_status : enum                                        │    │
│  │                  CURRENT | HISTORICAL | PROJECTED | REVOKED    │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │  LIFECYCLE STATE                                               │    │
│  │  ─────────────────────────────────────────────────────────── │    │
│  │  status    : enum                                              │    │
│  │              ACTIVE | SUPERSEDED | EXPIRED | DELETED           │    │
│  │  deleted_at : datetime (nullable)                              │    │
│  │  created_at : datetime                                         │    │
│  │  updated_at : datetime                                         │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │  SUPERSESSION CHAIN                                            │    │
│  │  ─────────────────────────────────────────────────────────── │    │
│  │  supersedes    : UUID  (this record replaces this older one)  │    │
│  │  superseded_by  : UUID  (this record was replaced by this)    │    │
│  │  version        : integer                                      │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │  CONTRADICTION LINKS                                           ���    │
│  │  ─────────────────────────────────────────────────────────── │    │
│  │  contradictions : list[UUID]  (other memory_ids this conflicts│    │
│  │                               with — bidirectional link)      │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │  PERMISSIONS                                                   │    │
│  │  ─────────────────────────────────────────────────────────── │    │
│  │  permissions : dict{ principal_id → { read, write, share } }  │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │  EMBEDDING METADATA                                            │    │
│  │  ─────────────────────────────────────────────────────────── │    │
│  │  embedding         : list[float]  (vector embedding)           │    │
│  │  embedding_model   : string       (model used to generate)     │    │
│  │  embedding_created : datetime     (when embedding was computed)│    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Field Definitions

#### Identity

| Field | Type | Description |
|---|---|---|
| `memory_id` | UUID | Primary key. Globally unique. |
| `version` | integer | Monotonically increasing. Starts at 1. Incremented on every supersession. |
| `memory_type` | enum | The cognitive/structural type (see taxonomy below). |
| `content_variant` | enum | How to interpret the content fields (SPO triple, free text, graph element, etc.). |

**Type Taxonomy:**

```
FACT              — A subject-predicate-object statement of fact
DECISION          — A recorded choice or commitment
GRAPH_NODE        — An entity in the knowledge graph
GRAPH_EDGE        — A relationship between graph nodes
SOURCE            — An ingested conversation/document (ingestion root)
SESSION           — A conversational session
MESSAGE           — A single message within a session
WORKING           — Volatile, short-lived memory (agent scratch)
EPISODIC          — Event-based memory (what happened)
SEMANTIC          — Abstracted knowledge (generalized from episodes)
PROCEDURAL        — How-to / process memory
USER              — User-specific persistent memory
TEAM              — Team-shared memory
PROJECT           — Project-scoped memory
AGENT             — Agent-internal memory
```

**Content Variant Taxonomy:**

| Variant | Used Fields | Applicable Memory Types |
|---|---|---|
| `FREE_TEXT` | `content` | MEMORY, SOURCE, SESSION, MESSAGE |
| `SPO_TRIPLE` | `subject`, `predicate`, `value` | FACT |
| `DECISION_TEXT` | `content`, `context` | DECISION |
| `GRAPH_ELEMENT` | `graph_label`, `graph_node_type`, `graph_rel_type`, `source_node_id`, `target_node_id`, `graph_properties` | GRAPH_NODE, GRAPH_EDGE |
| `CONVERSATION_TURN` | `content`, `role` (in metadata) | MESSAGE |

#### Scope

The tenant hierarchy is a strict tree:

```
Tenant
 └── Workspace(s)
      └── Project(s)  (optional)
           └── Team(s)  (optional)
                └── User(s)
```

All memory records belong to exactly one `tenant_id`. `workspace_id` is always present. `project_id`, `team_id`, and `user_id` are optional.

#### Content Representation

For facts, the canonical form stores the SPO triple in dedicated fields AND reconstructs `content` as `"{subject} {predicate} {value}"`. This means a Fact can be queried both as structured data (SPO) and as full-text (content).

For graph nodes, `graph_label` maps to the current `label` field, `graph_node_type` maps to `node_type`, and `graph_properties` maps to `properties`.

For graph edges, `source_node_id` and `target_node_id` reference other canonical memory records of type `GRAPH_NODE`.

#### Provenance Chain

The `provenance` list is an append-only chain of provenance entries. Each entry records:

```json
{
  "source": "m2_extraction" | "m4_extraction" | "memory_service" | "user_input" | ...,
  "source_id": "UUID of the originating entity (Source.id for pipeline outputs)",
  "creator": "principal_id that created this record",
  "created_at": "ISO8601 timestamp",
  "method": "direct_write | supersede | pipeline | api_write",
  "authority": {"score": float, "source": string, "creator": string},
  "confidence": float,
  "version": integer
}
```

For pipeline-extracted records, the first provenance entry always points to the `Source` that ingested the conversation.

#### Confidence & Authority

- `confidence` (float, 0.0–1.0): How certain the system is about the accuracy of this memory. Set by the extraction stage (e.g., 0.8 for facts, 0.75 for decisions). User-authored memories default to 1.0.
- `authority` (dict): Multi-field authority descriptor:
  - `score` (float): Numeric authority score. Default 1.0.
  - `source` (string): Origin description (e.g., `"m2_extraction"`, `"user_provided"`).
  - `creator` (string): Who/what created this record.
- `importance` (float, 0.0–1.0): Retrieval ranking weight. Not currently stored in any ORM model.

#### Temporal Validity vs. Lifecycle

These are **two independent axes**:

| Axis | Field | Values | Meaning |
|---|---|---|---|
| **Temporal validity** | `temporal_status` | CURRENT, HISTORICAL, PROJECTED, REVOKED | Is this fact still true right now? |
| **Lifecycle** | `status` | ACTIVE, SUPERSEDED, EXPIRED, DELETED | Is this record still part of the active dataset? |

A record can be `temporal_status="historical"` AND `status="active"` — it is historically accurate but has been replaced by a newer fact.

A record can be `temporal_status="current"` AND `status="expired"` — it was true but the memory itself has expired (TTL).

#### Supersession Chain

```
Record A (version=1, supersedes=null, superseded_by=B)
    └── superseded by ──► Record B (version=2, supersedes=A, superseded_by=C)
                              └── superseded by ──► Record C (version=3, ...)
```

The chain is traversable in both directions via `supersedes` (backward) and `superseded_by` (forward).

#### Contradiction Links

The `contradictions` field is a list of `memory_id` values that this record directly contradicts. This is distinct from supersession:

- **Supersession**: "This fact replaced that fact because the world changed."
- **Contradiction**: "This fact and that fact cannot both be true simultaneously."

Currently, no contradiction tracking exists in any ORM model or service.

#### Permissions

Per-record ACL: `permissions[principal_id] → { read: bool, write: bool, share: bool }`. Currently implemented only in the `MemoryService` in-memory cache (`memory.py` line 113, 931, 970). Not persisted to PostgreSQL — stored only in the `metadata` JSON blob as an ad-hoc field.

#### Embedding Metadata

| Field | Type | Currently Stored Where |
|---|---|---|
| `embedding` | list[float] | `Memory.embedding` (JSON column) |
| `embedding_model` | string | NOT stored anywhere |
| `embedding_created` | datetime | NOT stored anywhere |

Only the `Memory` table has an `embedding` column. Facts, Decisions, and GraphNodes do not have embedding support.

---

## Section 3: Current → Canonical Mapping

### 3.1 Memory → Canonical

| Canonical Field | Maps From | Notes |
|---|---|---|
| `memory_id` | `Memory.id` | Direct mapping |
| `version` | **LOST** | Not stored in `Memory` table. Implicitly 1. Stored in `metadata.version` but not surfaced by `_model_to_record()` |
| `memory_type` | `Memory.memory_type` | Direct mapping; `MemoryTypeMapper` handles canonical↔vault translation |
| `content_variant` | **LOST** | No variant indicator; always treated as `FREE_TEXT` |
| `tenant_id` | `Memory.tenant_id` | Direct mapping |
| `workspace_id` | `Memory.workspace_id` | Direct mapping |
| `project_id` | `Memory.project_id` | Direct mapping |
| `team_id` | **LOST** | Not in ORM model. Present in `MemoryRecord` but not persisted |
| `user_id` | `Memory.user_id` | Direct mapping |
| `agent_id` | `Memory.agent_id` | Direct mapping |
| `run_id` | `Memory.run_id` | Direct mapping |
| `subject` | Derived from `content[:100]` | Not stored directly. Computed in `_model_to_record()` at `memory.py` line 306 |
| `predicate` | `metadata.predicate` | Packed into JSON blob at write time (`memory.py` line 230) |
| `value` | `metadata.value` | Packed into JSON blob at write time |
| `content` | `Memory.content` | Direct mapping |
| `context` | **LOST** | Not in `Memory` table. Only present in `Decision.context` |
| `source_id` | **LOST** | Not in `Memory` table. Facts/Decisions/Edges have it; Memory does not |
| `session_id` | **LOST** | Not in `Memory` table |
| `provenance` | `metadata.provenance` | Packed into JSON blob. Append-only in service, but overwritten on each `_persist_record()` call (see Gap Analysis) |
| `confidence` | `Memory.confidence` | Direct mapping (default 0.7 vs 1.0 for facts) |
| `authority` | `Memory.authority` (float) / `metadata.authority` (dict) | Inconsistent: ORM stores float; service expects dict. `_model_to_record` reconstructs dict from float + metadata |
| `importance` | `metadata.importance` | Packed into JSON blob. Not in ORM columns |
| `valid_from` | **LOST** | Not stored anywhere |
| `valid_until` | **LOST** | Not stored anywhere |
| `expires_at` | **LOST** | Not stored anywhere (though `expire()` method exists) |
| `temporal_status` | `Memory.temporal_status` | Direct mapping |
| `status` | Derived from `temporal_status` | `_model_to_record()` inverts: `temporal_status="current"` → `status="active"` |
| `deleted_at` | `Memory.deleted_at` | Direct mapping |
| `supersedes` | `metadata.supersedes` | Packed into JSON blob |
| `superseded_by` | `metadata.superseded_by` | Packed into JSON blob |
| `contradictions` | **LOST** | Not stored anywhere |
| `permissions` | `metadata.permissions` | Packed into JSON blob. Service-layer only, never persisted to dedicated columns |
| `embedding` | `Memory.embedding` | Direct mapping |
| `embedding_model` | **LOST** | Not stored anywhere |
| `embedding_created` | **LOST** | Not stored anywhere |

### 3.2 Fact → Canonical

| Canonical Field | Maps From | Notes |
|---|---|---|
| `memory_id` | `Fact.id` | Direct mapping |
| `version` | **LOST** | Not stored. Always 1. |
| `memory_type` | Derived: `"FACT"` | Not in ORM. Must be inferred from table membership |
| `content_variant` | Derived: `"SPO_TRIPLE"` | Not in ORM |
| `tenant_id` | **LOST** | Facts have `workspace_id` but no `tenant_id`. Must be looked up via workspace |
| `workspace_id` | `Fact.workspace_id` | Direct mapping |
| `project_id` | `Fact.project_id` | Direct mapping |
| `team_id` | **LOST** | Not in ORM |
| `user_id` | **LOST** | Not in ORM |
| `agent_id` | **LOST** | Not in ORM |
| `run_id` | **LOST** | Not in ORM |
| `subject` | `Fact.subject` | Direct mapping |
| `predicate` | `Fact.predicate` | Direct mapping |
| `value` | `Fact.object` | Renamed: ORM calls it `object`, canonical calls it `value` |
| `content` | `Fact.content` | Direct mapping |
| `context` | **LOST** | Not in Fact table (present in Decision only) |
| `source_id` | `Fact.source_id` | Direct mapping |
| `session_id` | `Fact.session_id` | Direct mapping |
| `provenance` | **LOST** | Not stored. `source_id` is a FK but no provenance chain is maintained |
| `confidence` | `Fact.confidence` | Direct mapping (default 1.0 in ORM, 0.8 at extraction) |
| `authority` | `Fact.authority` | Direct mapping (float, always 1.0) |
| `importance` | **LOST** | Not stored |
| `valid_from` | **LOST** | Not stored |
| `valid_until` | **LOST** | Not stored |
| `expires_at` | **LOST** | Not stored |
| `temporal_status` | `Fact.temporal_status` | Direct mapping |
| `status` | `Fact.status` | Direct mapping |
| `deleted_at` | `Fact.deleted_at` | Direct mapping |
| `supersedes` | **LOST** | Not stored. Only `superseded_by_id` (forward link) exists |
| `superseded_by` | `Fact.superseded_by_id` | Forward link only. No backward link. |
| `contradictions` | **LOST** | Not stored anywhere |
| `permissions` | `Fact.metadata` (ad-hoc) | Could be in JSON but no enforcement |
| `embedding` | **LOST** | No embedding column |
| `embedding_model` | **LOST** | Not stored |
| `embedding_created` | **LOST** | Not stored |

### 3.3 Decision → Canonical

| Canonical Field | Maps From | Notes |
|---|---|---|
| `memory_id` | `Decision.id` | Direct mapping |
| `version` | **LOST** | Not stored |
| `memory_type` | Derived: `"DECISION"` | Not in ORM |
| `content_variant` | Derived: `"DECISION_TEXT"` | Not in ORM |
| `tenant_id` | **LOST** | No `tenant_id` column |
| `workspace_id` | `Decision.workspace_id` | Direct mapping |
| `project_id` | `Decision.project_id` | Direct mapping |
| `team_id` | **LOST** | Not in ORM |
| `user_id` | **LOST** | Not in ORM |
| `agent_id` | **LOST** | Not in ORM |
| `run_id` | **LOST** | Not in ORM |
| `subject` | **LOST** | Not in ORM |
| `predicate` | **LOST** | Not in ORM |
| `value` | **LOST** | Not in ORM |
| `content` | `Decision.content` | Direct mapping |
| `context` | `Decision.context` | Direct mapping (this is one field Decisions have that Facts lack) |
| `source_id` | `Decision.source_id` | Direct mapping |
| `session_id` | `Decision.session_id` | Direct mapping |
| `provenance` | **LOST** | Not stored |
| `confidence` | `Decision.confidence` | Direct mapping |
| `authority` | `Decision.authority` | Direct mapping (float, always 1.0) |
| `importance` | **LOST** | Not stored |
| `valid_from` | **LOST** | Not stored |
| `valid_until` | **LOST** | Not stored |
| `expires_at` | **LOST** | Not stored |
| `temporal_status` | `Decision.temporal_status` | Direct mapping |
| `status` | `Decision.status` | Direct mapping |
| `deleted_at` | `Decision.deleted_at` | Direct mapping |
| `supersedes` | **LOST** | Not stored |
| `superseded_by` | `Decision.superseded_by_id` | Forward link only |
| `contradictions` | **LOST** | Not stored |
| `permissions` | `Decision.metadata` (ad-hoc) | Could be in JSON but no enforcement |
| `embedding` | **LOST** | No embedding column |

### 3.4 GraphNode → Canonical

| Canonical Field | Maps From | Notes |
|---|---|---|
| `memory_id` | `GraphNode.id` | Direct mapping |
| `version` | **LOST** | Not stored |
| `memory_type` | Derived: `"GRAPH_NODE"` | Not in ORM |
| `content_variant` | Derived: `"GRAPH_ELEMENT"` | Not in ORM |
| `tenant_id` | **LOST** | No `tenant_id` column |
| `workspace_id` | `GraphNode.workspace_id` | Direct mapping |
| `project_id` | `GraphNode.project_id` | Direct mapping |
| `team_id` | **LOST** | Not in ORM |
| `user_id` | **LOST** | Not in ORM |
| `agent_id` | **LOST** | Not in ORM |
| `run_id` | **LOST** | Not in ORM |
| `subject` | `GraphNode.label` | Semantic equivalent |
| `predicate` | **LOST** | Not applicable |
| `value` | **LOST** | Not applicable |
| `content` | `GraphNode.label` | Used as content equivalent |
| `context` | **LOST** | Not in ORM |
| `source_id` | **LOST** | Not in ORM — provenance is lost at node level |
| `session_id` | **LOST** | Not in ORM |
| `provenance` | **LOST** | Not stored |
| `confidence` | **LOST** | No `confidence` column |
| `authority` | **LOST** | No `authority` column |
| `importance` | **LOST** | Not stored |
| `valid_from` | **LOST** | Not stored |
| `valid_until` | **LOST** | Not stored |
| `expires_at` | **LOST** | Not stored |
| `temporal_status` | `GraphNode.temporal_status` | Direct mapping |
| `status` | **LOST** | No `status` column — `temporal_status` is the only lifecycle indicator |
| `deleted_at` | `GraphNode.deleted_at` | Direct mapping |
| `supersedes` | **LOST** | Not stored |
| `superseded_by` | **LOST** | Not stored |
| `contradictions` | **LOST** | Not stored |
| `permissions` | `GraphNode.properties` (ad-hoc) | Could be in JSON but no enforcement |
| `embedding` | **LOST** | No embedding column |
| `graph_label` | `GraphNode.label` | Direct mapping |
| `graph_node_type` | `GraphNode.node_type` | Direct mapping |
| `graph_properties` | `GraphNode.properties` | Direct mapping |

### 3.5 GraphEdge → Canonical

| Canonical Field | Maps From | Notes |
|---|---|---|
| `memory_id` | `GraphEdge.id` | Direct mapping |
| `version` | **LOST** | Not stored |
| `memory_type` | Derived: `"GRAPH_EDGE"` | Not in ORM |
| `content_variant` | Derived: `"GRAPH_ELEMENT"` | Not in ORM |
| `tenant_id` | **LOST** | No `tenant_id` column |
| `workspace_id` | `GraphEdge.workspace_id` | Direct mapping |
| `project_id` | `GraphEdge.project_id` | Direct mapping |
| `team_id` | **LOST** | Not in ORM |
| `user_id` | **LOST** | Not in ORM |
| `agent_id` | **LOST** | Not in ORM |
| `run_id` | **LOST** | Not in ORM |
| `subject` | `GraphEdge.source_node_id` (resolved to label) | Indirect — requires node lookup |
| `predicate` | `GraphEdge.relationship_type` | Semantic equivalent |
| `value` | `GraphEdge.target_node_id` (resolved to label) | Indirect — requires node lookup |
| `content` | **LOST** | No content column |
| `context` | **LOST** | Not in ORM |
| `source_id` | `GraphEdge.source_id` | Direct mapping |
| `session_id` | **LOST** | Not in ORM |
| `provenance` | **LOST** | Not stored |
| `confidence` | `GraphEdge.confidence` | Direct mapping (default 1.0, set to 0.8 at creation) |
| `authority` | **LOST** | No `authority` column |
| `importance` | **LOST** | Not stored |
| `valid_from` | **LOST** | Not stored |
| `valid_until` | **LOST** | Not stored |
| `expires_at` | **LOST** | Not stored |
| `temporal_status` | `GraphEdge.temporal_status` | Direct mapping |
| `status` | **LOST** | No `status` column |
| `deleted_at` | `GraphEdge.deleted_at` | Direct mapping |
| `supersedes` | **LOST** | Not stored |
| `superseded_by` | **LOST** | Not stored |
| `contradictions` | **LOST** | Not stored |
| `permissions` | `GraphEdge.properties` (ad-hoc) | Could be in JSON but no enforcement |
| `embedding` | **LOST** | No embedding column |
| `source_node_id` | `GraphEdge.source_node_id` | Direct mapping |
| `target_node_id` | `GraphEdge.target_node_id` | Direct mapping |
| `graph_rel_type` | `GraphEdge.relationship_type` | Direct mapping |
| `graph_properties` | `GraphEdge.properties` | Direct mapping |

### 3.6 MemoryRecord vs. Memory ORM: Field Divergence

The `MemoryRecord` dataclass (`memory.py` lines 61–119) and the `Memory` ORM model (`models.py` lines 232–267) are **not in alignment**:

**Fields in MemoryRecord but NOT in the Memory ORM model:**
- `scope` — stored in `metadata.scope` only
- `team_id` — not persisted at all
- `subject` — derived from `content[:100]` at read time, not stored
- `predicate` — stored in `metadata.predicate`
- `value` — stored in `metadata.value`
- `importance` — stored in `metadata.importance`
- `valid_from` — not persisted
- `valid_until` — not persisted
- `expires_at` — not persisted (though `expire()` method exists)
- `supersedes` — stored in `metadata.supersedes`
- `superseded_by` — stored in `metadata.superseded_by`
- `provenance` — stored in `metadata.provenance`
- `permissions` — stored in `metadata.permissions`
- `user_metadata` — stored as `metadata.user_metadata`

**Fields in the Memory ORM model but NOT in MemoryRecord:**
- `embedding` — `MemoryRecord` has no `embedding` field
- `embedding_model` — not in either (gap in both)
- `embedding_created` — not in either (gap in both)

**Fields that exist in BOTH but with type mismatches:**
- `authority`: `MemoryRecord` expects `dict[str, Any]`, ORM stores `Float`. The `_persist_record()` method flattens dict→float (`memory.py` line 224), and `_model_to_record()` reconstructs float→dict (`memory.py` line 307). Information is lost in both directions.

---

## Section 4: Gap Analysis

### 4.1 What Is Lost Between Extraction and Persistence

#### M2 Fact Extraction (`m2_facts.py`) → `Fact` table (`pipeline.py`)

| Lost Field | Where It Exists | Where It Is Lost |
|---|---|---|
| `metadata` (dict) | `Fact.metadata` dataclass field (`m2_facts.py` line 24) | Never written to ORM — `pipeline.py` does not set `metadata` on `Fact()` |
| `authority` | `Fact.authority` dataclass field (default 1.0) | Written to ORM as float, but extraction never sets it (always 1.0) |
| Dedup key (SPO normalized) | Computed in `_deduplicate_facts()` | Used only at extraction time; no persistent dedup index beyond the DB unique constraint on `(workspace_id, subject, predicate, temporal_status)` |
| Extraction method | Implicit (regex pattern match) | Not recorded in `metadata` or `provenance` |

#### M2 Decision Extraction → `Decision` table

| Lost Field | Where It Exists | Where It Is Lost |
|---|---|---|
| `metadata` (dict) | `Decision.metadata` dataclass field (`m2_facts.py` line 34) | Never written to ORM |
| Extraction context | `Decision.context` dataclass field | Written to ORM as `context` — **this one IS preserved** |
| `authority` | `Decision.authority` dataclass field | Written to ORM but always 1.0 |

#### M4 Graph Extraction (`m4_graph.py`) → `GraphNode`/`GraphEdge` tables

| Lost Field | Where It Exists | Where It Is Lost |
|---|---|---|
| Node confidence | Not extracted | `persist_graph()` hardcodes `confidence=0.8` at `m4_graph.py` line 184 for edges; nodes have no confidence at all |
| Node authority | Not extracted | No `authority` column on `GraphNode` or `GraphEdge` |
| Edge provenance chain | `source_id` is set | Only a single `source_id` FK — no provenance list. If the source is updated, the edge's provenance doesn't track the change |
| Node provenance | **Not captured** | `GraphNode` has no `source_id` FK. Provenance is entirely lost at node level |
| Node importance | Not extracted | No column |
| Edge `context` | Not extracted | No column |
| Extraction patterns used | Known (4 relationship types) | Not recorded in `properties` |

#### MemoryService `MemoryRecord` → `Memory` ORM (`_persist_record`)

| Lost Field | Where It Exists | Where It Is Lost |
|---|---|---|
| `scope` | `MemoryRecord.scope` | Packed into `metadata.scope` but not a first-class column |
| `team_id` | `MemoryRecord.team_id` | Never written to ORM at all |
| `subject` | `MemoryRecord.subject` | Not a column; derived from `content[:100]` at read time |
| `predicate` | `MemoryRecord.predicate` | Packed into `metadata.predicate` |
| `value` | `MemoryRecord.value` | Packed into `metadata.value` |
| `importance` | `MemoryRecord.importance` | Packed into `metadata.importance` |
| `valid_from` | `MemoryRecord.valid_from` | Never persisted |
| `valid_until` | `MemoryRecord.valid_until` | Never persisted |
| `expires_at` | `MemoryRecord.expires_at` | Never persisted (though `expire()` sets `temporal_status`) |
| `supersedes` | `MemoryRecord.supersedes` | Packed into `metadata.supersedes` |
| `superseded_by` | `MemoryRecord.superseded_by` | Packed into `metadata.superseded_by` |
| `provenance` (list) | `MemoryRecord.provenance` | Packed into `metadata.provenance`, but `_persist_record()` overwrites the entire `metadata` dict on each write — provenance chain is **destroyed on update** |
| `permissions` | `MemoryRecord.permissions` | Packed into `metadata.permissions` — service-layer only, no DB-level enforcement |
| `user_metadata` | `MemoryRecord.user_metadata` | Packed as `metadata.user_metadata` inside the metadata blob |
| `authority` (dict) | `MemoryRecord.authority` | Flattened to float in `_persist_record()` line 224; reconstructed imperfectly in `_model_to_record()` line 307 |

### 4.2 The Provenance Overwrite Bug

The most critical gap: `_persist_record()` at `memory.py` lines 228–246 builds a **fresh** `meta` dict on every write:

```python
meta: dict[str, Any] = {
    "predicate": record.predicate,
    "value": record.value,
    "scope": record.scope,
    ...
}
for k, v in user_meta.items():
    meta.setdefault(k, v)
if user_meta:
    meta["user_metadata"] = user_meta
model.extra_metadata = meta
```

This means:
1. The `provenance` list from `record.provenance` is written to `metadata.provenance`
2. On the next update, a **new** `meta` dict is constructed from the in-memory `record`
3. If the record was loaded from DB via `_model_to_record()`, the provenance list is **reconstructed** from `metadata.provenance` — but if any fields were added to `MemoryRecord` after the initial write, they won't be in the stored metadata
4. Any provenance entries appended between the initial write and an update are **lost** because the fresh `meta` dict only contains `record.provenance` at the time of the update call

### 4.3 Structural Fragmentation Summary

| Capability | Memory | Fact | Decision | GraphNode | GraphEdge |
|---|---|---|---|---|---|
| Tenant-scoped | Yes | No | No | No | No |
| Project-scoped | Yes | Yes | Yes | Yes | Yes |
| User-scoped | Yes | No | No | No | No |
| Agent-scoped | Yes | No | No | No | No |
| Run-scoped | Yes | No | No | No | No |
| SPO triple | Via metadata | Native | No | No | No |
| Free text content | Native | Native | Native | Via label | No |
| Confidence | Yes (default 0.7) | Yes (default 1.0) | Yes (default 1.0) | **No** | Yes (default 1.0) |
| Authority | Float (default 1.0) | Float (default 1.0) | Float (default 1.0) | **No** | **No** |
| Importance | Via metadata | No | No | No | No |
| Embedding | Yes | **No** | **No** | **No** | **No** |
| Temporal status | Yes | Yes | Yes | Yes | Yes |
| Lifecycle status | Via temporal | Yes | Yes | **No** (only temporal) | **No** (only temporal) |
| Supersession | Via metadata | Forward only | Forward only | **No** | **No** |
| Version | Via metadata | **No** | **No** | **No** | **No** |
| Provenance chain | Via metadata | **No** | **No** | **No** | Partial (source_id only) |
| Permissions | Via metadata | **No** | **No** | **No** | **No** |
| Policy enforcement | Yes (Sprint 8) | **No** | **No** | **No** | **No** |
| Contradiction tracking | **No** | **No** | **No** | **No** | **No** |
| Temporal validity dates | **No** | **No** | **No** | **No** | **No** |

### 4.4 Recommended Consolidation Path

The fragmentation can be resolved by:

1. **Adding a `memory_type` discriminator to all memory tables** — Currently only `Memory` has a type column. `Fact`, `Decision`, `GraphNode`, and `GraphEdge` are identified solely by table membership.

2. **Moving SPO fields into `metadata` for non-Fact entities** — Or adding `subject`/`predicate`/`value` columns to `Memory` and deprecating the dedicated `Fact` table.

3. **Adding `tenant_id` to `Fact`, `Decision`, `GraphNode`, `GraphEdge`** — Currently these tables only have `workspace_id`, making cross-workspace queries require a workspace lookup.

4. **Adding `confidence` and `authority` to `GraphNode`** — Currently graph nodes have neither.

5. **Adding `source_id` to `GraphNode`** — Currently only edges carry provenance to their source ingestion.

6. **Replacing ad-hoc metadata packing with dedicated columns** — The current pattern of packing canonical fields into `metadata` JSON blobs makes queries slow and schema evolution fragile.

7. **Implementing a single `MemoryRecord` → ORM persistence path** — The current `_persist_record()` method writes to `Memory` only. Fact and Decision writes bypass `MemoryService` entirely (`pipeline.py` writes them directly). Graph writes bypass it too (`m4_graph.py` writes directly).

---

*End of document.*
