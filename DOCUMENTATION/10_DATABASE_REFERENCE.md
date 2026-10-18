# SwarmVault WebApp — Database Reference
**Version:** 1.0.0
**Date:** 2026-09-01
**Evidence base:** Repository inspection (commit 902d85e), app/models.py

---

## 1. Technology Stack

- **ORM:** SQLAlchemy 2.0+ (async)
- **Dialect:** `postgresql+asyncpg`
- **Connection pool:** NOT ESTABLISHED IN AVAILABLE SOURCE (NullPool used in tests)
- **Migrations:** NOT ESTABLISHED IN AVAILABLE SOURCE (Alembic? Manual schema?)
- **UUID primary keys:** All tables use `String(36)` with `uuid.uuid4()`
- **Timezone:** All datetime columns use `DateTime(timezone=True)` with UTC defaults

---

## 2. Schema Overview (14 Tables)

| Table | Primary Purpose | Soft Delete |
|-------|----------------|-------------|
| tenants | Top-level organization | No |
| users | User accounts | Yes (`deleted_at`) |
| workspaces | Workspace containers | Yes (`deleted_at`) |
| workspace_members | User-workspace membership with role | No |
| invitations | Pending workspace invitations | No |
| refresh_tokens | JWT refresh token storage | No (revoked flag) |
| sessions | Chat sessions | Yes (`deleted_at`) |
| messages | Chat messages within sessions | No |
| projects | Project containers | Yes (`deleted_at`) |
| memories | Curated knowledge (main data) | Yes (`deleted_at`) |
| ingest_jobs | Document ingestion jobs | No |
| sources | Ingested documents/conversations | Yes (`deleted_at`) |
| normalized_messages | Extracted messages from sources | No |
| facts | Extracted factual statements (M2) | Yes (`deleted_at`) |
| decisions | Extracted decisions (M2) | No |
| graph_nodes | Knowledge graph nodes (M4) | Yes (`deleted_at`) |
| graph_edges | Knowledge graph edges (M4) | Yes (`deleted_at`) |
| audit_events | Audit log entries | No |
| api_keys | API key storage (hashed) | No |
| provenance | LLM interaction provenance | No |

---

## 3. Detailed Table Definitions

### 3.1 tenants
Top-level organization. Each tenant can have multiple workspaces.

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| id | String(36) | PK, UUID | uuid4() |
| name | String(255) | NOT NULL | — |
| slug | String(100) | UNIQUE, NOT NULL | — |
| plan | String(50) | NOT NULL | "free" |
| created_at | DateTime(tz) | NOT NULL | utcnow() |
| updated_at | DateTime(tz) | NOT NULL | utcnow() |

**Relationships:** workspaces → Workspace[]

### 3.2 users
User accounts. Users belong to tenants via workspace memberships.

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| id | String(36) | PK, UUID | uuid4() |
| email | String(255) | UNIQUE, INDEXED, NOT NULL | — |
| name | String(255) | NOT NULL | — |
| hashed_password | String(255) | NULLABLE | — |
| is_active | Boolean | NOT NULL | True |
| email_verified | Boolean | NOT NULL | False |
| created_at | DateTime(tz) | NOT NULL | utcnow() |
| deleted_at | DateTime(tz) | NULLABLE, INDEXED | — |

**Relationships:** memberships → WorkspaceMember[], sessions → Session[], refresh_tokens → RefreshToken[]

### 3.3 workspaces
Workspace containers within a tenant.

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| id | String(36) | PK, UUID | uuid4() |
| tenant_id | String(36) | FK → tenants.id, NOT NULL | — |
| name | String(255) | NOT NULL | — |
| slug | String(100) | NOT NULL | — |
| description | Text | NULLABLE | — |
| created_at | DateTime(tz) | NOT NULL | utcnow() |
| updated_at | DateTime(tz) | NOT NULL | utcnow() |
| deleted_at | DateTime(tz) | NULLABLE, INDEXED | — |

**Relationships:** tenant → Tenant, members → WorkspaceMember[] (cascade delete-orphan)

**Composite indexes:** `uq_workspace_tenant_slug` — unique per tenant

### 3.4 workspace_members
User-role mapping within a workspace.

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| id | String(36) | PK, UUID | uuid4() |
| workspace_id | String(36) | FK → workspaces.id, NOT NULL | — |
| user_id | String(36) | FK → users.id, NOT NULL | — |
| role | String(20) | NOT NULL | "member" |
| invited_at | DateTime(tz) | NULLABLE | — |
| joined_at | DateTime(tz) | NULLABLE | — |
| expires_at | DateTime(tz) | NULLABLE | — |

**Roles:** owner, admin, member, viewer

**Relationships:** workspace → Workspace, user → User

### 3.5 invitations
Pending workspace invitations.

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| id | String(36) | PK, UUID | uuid4() |
| workspace_id | String(36) | FK → workspaces.id, NOT NULL | — |
| email | String(255) | NOT NULL | — |
| role | String(20) | NOT NULL | "member" |
| state | String(20) | NOT NULL | "pending" |
| message | Text | NULLABLE | — |
| created_at | DateTime(tz) | NOT NULL | utcnow() |
| expires_at | DateTime(tz) | NULLABLE | — |
| responded_at | DateTime(tz) | NULLABLE | — |

**States:** pending, accepted, declined

### 3.6 refresh_tokens
JWT refresh token storage.

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| id | String(36) | PK, UUID | uuid4() |
| user_id | String(36) | FK → users.id, NOT NULL | — |
| token | String(512) | UNIQUE, INDEXED, NOT NULL | — |
| expires_at | DateTime(tz) | NOT NULL | — |
| revoked | Boolean | NOT NULL | False |
| created_at | DateTime(tz) | NOT NULL | utcnow() |

**Relationships:** user → User

### 3.7 sessions
Chat sessions within a workspace.

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| id | String(36) | PK, UUID | uuid4() |
| workspace_id | String(36) | FK → workspaces.id, NOT NULL | — |
| user_id | String(36) | FK → users.id, NOT NULL | — |
| title | String(255) | NULLABLE | — |
| metadata | JSON | NULLABLE | — |
| created_at | DateTime(tz) | NOT NULL | utcnow() |
| updated_at | DateTime(tz) | NOT NULL | utcnow() |
| deleted_at | DateTime(tz) | NULLABLE, INDEXED | — |

**Relationships:** user → User, messages → Message[] (cascade delete-orphan)

### 3.8 messages
Chat messages within sessions.

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| id | String(36) | PK, UUID | uuid4() |
| session_id | String(36) | FK → sessions.id, NOT NULL | — |
| role | String(20) | NOT NULL | — |
| content | Text | NOT NULL | — |
| metadata | JSON | NULLABLE | — |
| created_at | DateTime(tz) | NOT NULL | utcnow() |

**Roles:** user, assistant, system

**Relationships:** session → Session

### 3.9 projects
Project containers within a workspace.

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| id | String(36) | PK, UUID | uuid4() |
| workspace_id | String(36) | FK → workspaces.id, NOT NULL | — |
| name | String(255) | NOT NULL | — |
| description | Text | NULLABLE | — |
| created_at | DateTime(tz) | NOT NULL | utcnow() |
| updated_at | DateTime(tz) | NOT NULL | utcnow() |
| deleted_at | DateTime(tz) | NULLABLE, INDEXED | — |

### 3.10 memories
Curated knowledge records. The primary data table.

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| id | String(36) | PK, UUID | uuid4() |
| tenant_id | String(36) | FK → tenants.id, NOT NULL, INDEXED | — |
| workspace_id | String(36) | FK → workspaces.id, NOT NULL, INDEXED | — |
| user_id | String(36) | FK → users.id, NULLABLE | — |
| agent_id | String(36) | NULLABLE | — |
| run_id | String(36) | NULLABLE | — |
| project_id | String(36) | FK → projects.id, NULLABLE, INDEXED | — |
| memory_type | String(50) | NOT NULL | "procedural_memory" |
| content | Text | NOT NULL | — |
| metadata | JSON | NULLABLE | — |
| embedding | JSON | NULLABLE | — |
| temporal_status | String(50) | NOT NULL, INDEXED | "current" |
| confidence | Float | NOT NULL | 0.7 |
| authority | Float | NOT NULL | 1.0 |
| deleted_at | DateTime(tz) | NULLABLE, INDEXED | — |
| created_at | DateTime(tz) | NOT NULL | utcnow() |
| updated_at | DateTime(tz) | NOT NULL | utcnow() |

**Memory types:** procedural_memory, episodic_memory, semantic_memory

**Temporal statuses:** current, historical, superseded

**Relationships:** tenant → Tenant

### 3.11 ingest_jobs
Document ingestion job tracking.

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| id | String(36) | PK, UUID | uuid4() |
| project_id | String(36) | NOT NULL | — |
| workspace_id | String(36) | FK → workspaces.id, NOT NULL | — |
| source_type | String(50) | NOT NULL | — |
| status | String(20) | NOT NULL | "queued" |
| stage | String(50) | NULLABLE | — |
| progress | Integer | NOT NULL | 0 |
| error_message | Text | NULLABLE | — |
| estimated_records | Integer | NULLABLE | — |
| config | JSON | NULLABLE | — |
| created_at | DateTime(tz) | NOT NULL | utcnow() |
| started_at | DateTime(tz) | NULLABLE | — |
| completed_at | DateTime(tz) | NULLABLE | — |

**Statuses:** queued, processing, completed, failed

### 3.12 sources
Ingested documents/conversations (M0 input).

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| id | String(36) | PK, UUID | uuid4() |
| project_id | String(36) | NOT NULL | — |
| workspace_id | String(36) | FK → workspaces.id, NOT NULL | — |
| tenant_id | String(36) | NOT NULL | — |
| source_type | String(50) | NOT NULL | — |
| external_id | String(255) | NULLABLE, INDEXED | — |
| content_hash | String(64) | NULLABLE, INDEXED | — |
| title | String(500) | NULLABLE | — |
| description | Text | NULLABLE | — |
| raw_content_path | String | NULLABLE | — |
| message_count | Integer | NOT NULL | 0 |
| status | String(20) | NOT NULL | "queued" |
| stage | String(50) | NULLABLE | — |
| progress | Integer | NOT NULL | 0 |
| error_message | Text | NULLABLE | — |
| config | JSON | NULLABLE | — |
| started_at | DateTime(tz) | NULLABLE | — |
| completed_at | DateTime(tz) | NULLABLE | — |
| created_at | DateTime(tz) | NOT NULL | utcnow() |
| updated_at | DateTime(tz) | NOT NULL | utcnow() |
| deleted_at | DateTime(tz) | NULLABLE, INDEXED | — |

**Source types:** text, json, jsonl, chatgpt, slack, discord, and others

**Relationships:** normalized_messages → NormalizedMessage[], facts → Fact[], decisions → Decision[], graph_edges → GraphEdge[]

**Composite indexes:** `ix_sources_workspace_tenant` (workspace_id, tenant_id), `ix_sources_project_status` (project_id, status)

### 3.13 normalized_messages
Individual messages from ingested sources (M0 output / M1 input).

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| id | String(36) | PK, UUID | uuid4() |
| source_id | String(36) | FK → sources.id, NOT NULL | — |
| session_id | String(36) | FK → sessions.id, NULLABLE | — |
| message_index | Integer | NOT NULL | — |
| external_id | String(255) | NULLABLE, INDEXED | — |
| role | String(20) | NOT NULL | — |
| content | Text | NOT NULL | — |
| metadata | JSON | NULLABLE | — |
| timestamp | DateTime(tz) | NULLABLE | — |
| created_at | DateTime(tz) | NOT NULL | utcnow() |

**Unique constraints:** `uq_normalized_msg_source_idx` (source_id, message_index), `uq_normalized_msg_source_ext` (source_id, external_id)

### 3.14 facts
Extracted factual statements (M2 output).

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| id | String(36) | PK, UUID | uuid4() |
| workspace_id | String(36) | FK → workspaces.id, NOT NULL | — |
| project_id | String(36) | NULLABLE | — |
| source_id | String(36) | FK → sources.id, NULLABLE | — |
| session_id | String(36) | FK → sessions.id, NULLABLE | — |
| subject | String(500) | NOT NULL | — |
| predicate | String(100) | NOT NULL | — |
| object | String(500) | NOT NULL | — |
| content | Text | NOT NULL | — |
| confidence | Float | NOT NULL | 1.0 |
| authority | Float | NOT NULL | 1.0 |
| temporal_status | String(20) | NOT NULL | "current" |
| superseded_by_id | String(36) | NULLABLE, INDEXED | — |
| status | String(20) | NOT NULL | "active" |
| metadata | JSON | NULLABLE | — |
| created_at | DateTime(tz) | NOT NULL | utcnow() |
| updated_at | DateTime(tz) | NOT NULL | utcnow() |
| deleted_at | DateTime(tz) | NULLABLE, INDEXED | — |

**Relationships:** source → Source

**Composite indexes:** `ix_facts_workspace_project` (workspace_id, project_id), `ix_facts_subject` (subject), `ix_facts_temporal_status` (temporal_status)

### 3.15 decisions
Extracted decision records (M2 output).

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| id | String(36) | PK, UUID | uuid4() |
| workspace_id | String(36) | FK → workspaces.id, NOT NULL | — |
| project_id | String(36) | NULLABLE | — |
| source_id | String(36) | FK → sources.id, NULLABLE | — |
| session_id | String(36) | FK → sessions.id, NULLABLE | — |
| content | Text | NOT NULL | — |
| context | Text | NULLABLE | — |
| confidence | Float | NOT NULL | 1.0 |
| authority | Float | NOT NULL | 1.0 |
| temporal_status | String(20) | NOT NULL | "current" |
| superseded_by_id | String(36) | NULLABLE, INDEXED | — |
| status | String(20) | NOT NULL | "active" |
| metadata | JSON | NULLABLE | — |
| created_at | DateTime(tz) | NOT NULL | utcnow() |
| updated_at | DateTime(tz) | NOT NULL | utcnow() |
| deleted_at | DateTime(tz) | NULLABLE, INDEXED | — |

**Relationships:** source → Source

**Composite indexes:** `ix_decisions_workspace_project` (workspace_id, project_id), `ix_decisions_temporal_status` (temporal_status)

### 3.16 graph_nodes
Knowledge graph nodes (M4 output).

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| id | String(36) | PK, UUID | uuid4() |
| workspace_id | String(36) | FK → workspaces.id, NOT NULL | — |
| project_id | String(36) | NULLABLE | — |
| external_id | String(255) | NULLABLE, INDEXED | — |
| label | String(500) | NOT NULL | — |
| node_type | String(50) | NOT NULL | "entity" |
| properties | JSON | NULLABLE | — |
| created_at | DateTime(tz) | NOT NULL | utcnow() |
| updated_at | DateTime(tz) | NOT NULL | utcnow() |
| deleted_at | DateTime(tz) | NULLABLE, INDEXED | — |
| temporal_status | String(20) | NOT NULL | "current" |

**Node types:** entity, concept, event

**Unique constraints:** `uq_graph_node_ws_ext` (workspace_id, external_id) — one external_id per workspace

**Composite indexes:** `ix_graph_nodes_workspace` (workspace_id, temporal_status), `ix_graph_nodes_workspace_type` (workspace_id, node_type)

### 3.17 graph_edges
Knowledge graph edges (M4 output).

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| id | String(36) | PK, UUID | uuid4() |
| workspace_id | String(36) | FK → workspaces.id, NOT NULL | — |
| project_id | String(36) | NULLABLE | — |
| source_node_id | String(36) | FK → graph_nodes.id, NOT NULL | — |
| target_node_id | String(36) | FK → graph_nodes.id, NOT NULL | — |
| relationship_type | String(100) | NOT NULL | — |
| properties | JSON | NULLABLE | — |
| confidence | Float | NOT NULL | 1.0 |
| temporal_status | String(20) | NOT NULL | "current" |
| source_id | String(36) | FK → sources.id, NULLABLE, INDEXED | — |
| created_at | DateTime(tz) | NOT NULL | utcnow() |
| updated_at | DateTime(tz) | NOT NULL | utcnow() |
| deleted_at | DateTime(tz) | NULLABLE, INDEXED | — |

**Composite indexes:** `ix_graph_edges_workspace` (workspace_id, temporal_status)

---

## 4. Foreign Key Map

```
tenants
  ├─▶ workspaces.tenant_id
  │     ├─▶ workspace_members.workspace_id
  │     ├─▶ sessions.workspace_id
  │     ├─▶ projects.workspace_id
  │     ├─▶ ingest_jobs.workspace_id
  │     ├─▶ sources.workspace_id
  │     ├─▶ facts.workspace_id
  │     ├─▶ decisions.workspace_id
  │     ├─▶ graph_nodes.workspace_id
  │     └─▶ graph_edges.workspace_id

users
  ├─▶ workspace_members.user_id
  ├─▶ sessions.user_id
  ├─▶ refresh_tokens.user_id
  └─▶ memories.user_id

workspaces
  └─▶ (FK from workspace_id columns)

sources
  ├─▶ normalized_messages.source_id
  ├─▶ facts.source_id
  ├─▶ decisions.source_id
  └─▶ graph_edges.source_id

sessions
  ├─▶ messages.session_id
  └─▶ facts.session_id / decisions.session_id / normalized_messages.session_id

projects
  ├─▶ memories.project_id
  ├─▶ ingest_jobs.project_id
  ├─▶ sources.project_id
  ├─▶ facts.project_id
  ├─▶ decisions.project_id
  └─▶ graph_nodes.project_id / graph_edges.project_id

graph_nodes
  └─▶ graph_edges.source_node_id, target_node_id
```

---

## 5. Index Strategy

### Single-Column Indexes
| Table | Column | Purpose |
|-------|--------|---------|
| users | email | Login lookups |
| users | deleted_at | Soft-delete filtering |
| memories | tenant_id | Tenant-scoped queries |
| memories | workspace_id | Workspace-scoped queries |
| memories | project_id | Project-scoped queries |
| memories | temporal_status | Status filtering |
| memories | deleted_at | Soft-delete filtering |
| refresh_tokens | token | Token validation |
| sources | external_id | Dedup / source linking |
| sources | content_hash | Dedup |
| sources | deleted_at | Soft-delete filtering |
| facts | superseded_by_id | Supersession chains |
| facts | subject | Subject search |
| facts | temporal_status | Status filtering |
| facts | deleted_at | Soft-delete filtering |
| decisions | superseded_by_id | Supersession chains |
| decisions | temporal_status | Status filtering |
| decisions | deleted_at | Soft-delete filtering |
| graph_nodes | external_id | Source linking |
| graph_nodes | deleted_at | Soft-delete filtering |
| graph_nodes | temporal_status | Status filtering |
| graph_edges | source_id | Source linking |
| graph_edges | deleted_at | Soft-delete filtering |
| graph_edges | temporal_status | Status filtering |

### Composite Indexes
| Table | Columns | Purpose |
|-------|---------|---------|
| workspaces | tenant_id, slug | Unique workspace slug per tenant |
| sources | workspace_id, tenant_id | Tenant-scoped source queries |
| sources | project_id, status | Project status lookups |
| facts | workspace_id, project_id | Project-scoped fact queries |
| decisions | workspace_id, project_id | Project-scoped decision queries |
| graph_nodes | workspace_id, temporal_status | Live graph queries |
| graph_nodes | workspace_id, node_type | Type-filtered graph queries |
| graph_edges | workspace_id, temporal_status | Live edge queries |

---

## 6. Soft Delete Pattern

**Soft delete** is used extensively. Every query must include:
```sql
WHERE deleted_at IS NULL
```

Tables with soft delete: users, workspaces, sessions, projects, memories, sources, facts, decisions, graph_nodes, graph_edges

Tables without soft delete: tenants, workspace_members, invitations, refresh_tokens, ingest_jobs, normalized_messages, messages, audit_events, api_keys, provenance

### Soft Delete Query Pattern
```python
# Correct
result = await db.execute(
    select(Memory).where(
        Memory.tenant_id == tenant_id,
        Memory.deleted_at.is_(None)
    )
)

# Wrong — would return soft-deleted records
result = await db.execute(
    select(Memory).where(Memory.tenant_id == tenant_id)
)
```

---

## 7. Temporal / Supersession Pattern

Facts and decisions support temporal tracking via:
- `temporal_status`: "current", "historical", "superseded"
- `superseded_by_id`: points to the record that supersedes this one
- `confidence`: float for uncertainty
- `authority`: float for trust level

This enables "memory with provenance" — knowing when a fact was valid and when it was updated.

---

## 8. Embedding Storage

Memory embeddings are stored as JSON arrays in the `embedding` column (Memory model):
```python
embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
```

This is application-level storage. The actual vector search is delegated to the SwarmVault graph backend.
