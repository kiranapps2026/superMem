# SwarmVault Domain Manifest

**Version:** 1.1.0
**Date:** 2026-09-25
**Branch:** recovery/restore-2026-09-24
**Authority:** Source code is the single source of truth. Documents are authoritative only when they match source.

---

## Table of Contents

1. [Executive Overview](#1-executive-overview)
2. [Domain Model](#2-domain-model)
3. [Pipeline Architecture](#3-pipeline-architecture)
4. [API Surface](#4-api-surface)
5. [Feature Catalog](#5-feature-catalog)
6. [Validation & Guardrails](#6-validation--guardrails)
7. [Database Tables Maintained](#7-database-tables-maintained)
8. [Security Architecture](#8-security-architecture)
9. [Frontend Pages](#9-frontend-pages)
10. [Observability & Audit](#10-observability--audit)

---

## 1. Executive Overview

SwarmVault is a multi-tenant AI knowledge platform. It ingests conversations, runs a 6-stage extraction pipeline, stores facts/decisions/graph entities/embeddings, and surfaces them through 21 frontend pages. The backend is a FastAPI service (279 lines main, 835 lines models, 602 lines schemas). The frontend is Next.js 15 with App Router.

**Current state (2026-09-25):**
- Backend: 772/773 tests pass (1 environmental), 78 router endpoints + 3 health endpoints, 21 pages
- Frontend: 9 E2E test files, 21 pages, TypeScript 0 errors
- Database: PostgreSQL with 24 tables, 13 migrations (001-013)
- Pipeline: M0→M1→M2→M3→M4→M5, 6 stages
- Phase 3: M5 reranking (46 tests, shadow mode default)
- Phase 5: Contradiction detection (34 tests, predicate policy engine)

---

## 2. Domain Model

### 2.1 Entity Relationship Diagram (textual)

```
Tenant ──┬── Workspace ──┬── WorkspaceMember ──┬── User
         │               │                      ├── Session ──┬── Message
         │               │                      │              ├── NormalizedMessage
         │               │                      │              ├── MessageFeedback
         │               │                      │              └── MessageProvenance
         │               │                      ├── Project ──┬── Source
         │               │                      │             ├── Fact
         │               │             ────────┤             ├── Decision
         │               │             │       │             ├── GraphNode
         │               │             │       │             ├── GraphEdge
         │               │             │       │             └── IngestJob
         │               │             │       ├── Memory
         │               │             │       └── ApiKey
         │               │             ├── Invitation
         │               │             ├── RefreshToken
         │               │             ├── Policy ──┬── PolicyVersion
         │               │             │            └── AuditEvent
         │               │             └── (tenant is the isolation boundary for all workspace data)
         │               │
         │               └── (tenant is the isolation boundary for all workspace data)
         │
         └── (tenant is the isolation boundary for all workspace data)
```

### 2.2 Entity Catalog

| Entity | Table | PK | FK | Purpose | Source File |
|---|---|---|---|---|---|
| **Tenant** | `tenants` | `id` | — | Top-level isolation boundary | app/models.py:18 |
| **Workspace** | `workspaces` | `id` | `tenant_id` → tenants | User collection within tenant | app/models.py:39 |
| **User** | `users` | `id` | — | Authenticated person | app/models.py:65 |
| **WorkspaceMember** | `workspace_members` | `id` | `workspace_id`, `user_id` | Many-to-many membership | app/models.py:97 |
| **Invitation** | `invitations` | `id` | `workspace_id` | Workspace join link | app/models.py:123 |
| **RefreshToken** | `refresh_tokens` | `id` | `user_id` → users | Long-lived auth | app/models.py:147 |
| **Session** | `sessions` | `id` | `project_id`, `user_id` | Conversation thread | app/models.py:165 |
| **Message** | `messages` | `id` | `session_id`, `user_id` | Chat message | app/models.py:191 |
| **Project** | `projects` | `id` | `workspace_id` → workspaces | Knowledge container | app/models.py:209 |
| **Memory** | `memory` | `id` | `workspace_id`, `project_id` | RAG vector | app/models.py:232 |
| **IngestJob** | `ingest_jobs` | `id` | `project_id`, `workspace_id` | Async job | app/models.py:269 |
| **Source** | `sources` | `id` | `project_id`, `workspace_id` | Ingest origin | app/models.py:302 |
| **NormalizedMessage** | `normalized_messages` | `id` | `source_id`, `session_id` | Pipeline-normalized message | app/models.py:370 |
| **Fact** | `facts` | `id` | `workspace_id`, `project_id`, `source_id` | Extracted assertion | app/models.py:414 |
| **Decision** | `decisions` | `id` | `workspace_id`, `project_id` | Extracted choice | app/models.py:468 |
| **GraphNode** | `graph_nodes` | `id` | `workspace_id`, `project_id`, `source_id` | Entity | app/models.py:521 |
| **GraphEdge** | `graph_edges` | `id` | `workspace_id`, `project_id` | Relationship | app/models.py:562 |
| **MessageProvenance** | `message_provenance` | `id` | `message_id` → messages | LLM trace | app/models.py:608 |
| **MessageFeedback** | `message_feedback` | `id` | `message_id` → messages | Like/dislike | app/models.py:657 |
| **ApiKey** | `api_keys` | `id` | `workspace_id` | Key for programmatic access | app/models.py:685 |
| **Policy** | `policies` | `id` | `workspace_id` | Authorization rule | app/models.py:728 |
| **PolicyVersion** | `policy_versions` | `id` | `policy_id` | Policy history | app/models.py:762 |
| **AuditEvent** | `audit_events` | `id` | `workspace_id` | Security log | app/models.py:789 |
| **MemoryContradiction** | `memory_contradictions` | `id` | `workspace_id` | Contradiction record | app/models.py:841 |

**Total: 24 tables, 13 migrations (001-013).**

### 2.3 Invariants

| Invariant | Enforcement | Source File |
|---|---|---|
| User active | `is_active` boolean check | app/middleware/auth.py:45 |
| Workspace slugs unique within tenant | SQLAlchemy UniqueConstraint | app/models.py:48 |
| User emails unique globally | Unique index | app/models.py:71 |
| Fact temporal_status = "current" for dedup | WHERE temporal_status = "current" | app/services/pipeline.py:222 |
| Projects soft-deleted via workspace | Workspace has `deleted_at` | app/models.py:56 |
| Tenant is isolation boundary | RBAC middleware checks tenant_id | app/middleware/tenancy.py |
| Password never returned in API | Pydantic exclude | app/schemas.py |

---

## 3. Pipeline Architecture

### 3.1 Pipeline Flow

```
INPUT (raw text, conversation JSON, file)
  │
  ▼
M0 — NORMALIZE
  Connectors normalize raw input → NormalizedConversation (title, messages, metadata)
  File: app/services/connectors.py
  |
  ▼
M1 — SESSION UNDERSTANDING
  LLM extracts topics, entities, intents from messages
  File: app/services/m1_session.py
  Output: topics[], entities_mentioned[], summary
  |
  ▼
M2 — FACT + DECISION EXTRACTION
  LLM extracts assertions (subject-predicate-object + confidence + authority)
  AND decisions (content + context + confidence)
  File: app/services/m2_facts.py
  Output: facts[], decisions[]
  |
  ▼
M3 — TEMPORAL SUPERSESSION
  Check existing current facts for same subject+predicate
  If object differs → mark old as "historical", create new "current" (supersede)
  If object identical → skip (dedup)
  File: app/services/m3_temporal.py
  Invariant: one "current" fact per subject+predicate
  |
  ▼
M4 — GRAPH PERSISTENCE
  Extract entity nodes + relationship edges from all text
  Persist to graph_nodes, graph_edges tables
  File: app/services/m4_graph.py
  Output: nodes_created, edges_created
  |
  ▼
M5 — RETRIEVAL
  No indexing step. M5 is the retrieval/rank step at query time.
  Uses semantic search + graph traversal + BM25 for hybrid ranking.
  File: app/services/m5_retrieval.py, app/services/retrieval.py
  |
  ▼
OUTPUT (source_id, session_id, facts_created, decisions_created, graph_nodes_created, graph_edges_created)
```

### 3.2 Pipeline Configuration

| Setting | Default | Env Var | Purpose |
|---|---|---|---|
| Source type | "text" | `LLM_SOURCE_TYPE` | Input format |
| Max messages | — | `MAX_MESSAGES` | Upper bound |
| Min fact confidence | — | `MIN_FACT_CONFIDENCE` | Threshold |

### 3.3 Pipeline States

| Stage | Progress | Status |
|---|---|---|
| M0 | 0% | processing |
| M1 | 25% | processing |
| M2 | 50% | processing |
| M3 | 75% | processing |
| M4 | 85% | processing |
| M5 | 100% | completed |
| — | — | failed (on exception) |

---

## 4. API Surface

### 4.1 Endpoint Registry

| Module | Prefix | Endpoints | Auth | RBAC | File |
|---|---|---|---|---|---|
| **Auth** | `/api/v1` | 6 | Public | — | app/api/auth.py |
| **Workspace** | `/api/v1` | 14 | Bearer | — | app/api/workspace.py |
| **Projects** | `/api/v1` | 5 | Bearer | — | app/api/projects.py |
| **Sessions** | `/api/v1` | 6 | Bearer | — | app/api/sessions.py |
| **Chat** | `/api/v1` | 2 | Bearer | — | app/api/chat.py |
| **Memory** | `/api/v1` | 6 | Bearer | — | app/api/memory.py |
| **Ingest** | `/api/v1` | 14 | Bearer | — | app/api/ingest.py |
| **Provenance** | `/api/v1` | 3 | Bearer | — | app/api/provenance.py |
| **Dashboard** | `/api/v1` | 2 | Bearer | — | app/api/dashboard.py |
| **Feedback** | `/api/v1` | 3 | Bearer | — | app/api/feedback.py |
| **API Keys** | `/api/v1` | 4 | Bearer | — | app/api/api_keys.py |
| **Storage** | `/api/v1` | 3 | Bearer | — | app/api/storage.py |
| **Policy** | `/api/v1` | 7 | Bearer | — | app/api/policy.py |
| **Audit** | `/api/v1` | 3 | Bearer | — | app/api/audit.py |

**Total: 78 endpoints across 14 routers (+ 3 health endpoints).**

### 4.2 Endpoint Index (corrected)

| # | Method | Path | Purpose | Source File |
|---|---|---|---|---|
| 1 | POST | `/api/v1/auth/register` | Register new user+workspace | app/api/auth.py |
| 2 | POST | `/api/v1/auth/login` | Get access+refresh tokens | app/api/auth.py |
| 3 | POST | `/api/v1/auth/refresh` | Refresh access token | app/api/auth.py |
| 4 | POST | `/api/v1/auth/logout` | Revoke refresh token | app/api/auth.py |
| 5 | GET | `/api/v1/auth/me` | Current user info | app/api/auth.py |
| 6 | GET | `/health/live` | Liveness probe | app/main.py:256 |
| 7 | GET | `/health/ready` | Readiness probe (DB) | app/main.py:261 |
| 8 | GET | `/health` | Basic health | app/main.py:277 |
| 9 | GET | `/api/v1/workspace/members` | List members | app/api/workspace.py |
| 10 | POST | `/api/v1/workspace/invite` | Invite member | app/api/workspace.py |
| 11 | DELETE | `/api/v1/workspace/members/{id}` | Remove member | app/api/workspace.py |
| 12 | GET | `/api/v1/workspace/invitations` | List invitations | app/api/workspace.py |
| 13 | GET | `/api/v1/projects/` | List projects | app/api/projects.py |
| 14 | POST | `/api/v1/projects/` | Create project | app/api/projects.py |
| 15 | DELETE | `/api/v1/projects/{id}` | Delete project | app/api/projects.py |
| 16 | GET | `/api/v1/sessions/` | List sessions | app/api/sessions.py |
| 17 | GET | `/api/v1/sessions/{id}` | Session detail | app/api/sessions.py |
| 18 | POST | `/api/v1/sessions/{id}/messages` | Post message | app/api/sessions.py |
| 19 | POST | `/api/v1/chat/` | Chat completion | app/api/chat.py |
| 20 | POST | `/api/v1/chat/stream` | Streaming chat | app/api/chat.py |
| 21 | GET | `/api/v1/memory/` | List memories | app/api/memory.py |
| 22 | GET | `/api/v1/memory/search` | Semantic search | app/api/memory.py |
| 23 | POST | `/api/v1/ingest/` | Ingest content | app/api/ingest.py |
| 24 | GET | `/api/v1/ingest/jobs` | Job status | app/api/ingest.py |
| 25 | GET | `/api/v1/ingest/facts` | Extracted facts | app/api/ingest.py |
| 26 | GET | `/api/v1/ingest/decisions` | Extracted decisions | app/api/ingest.py |
| 27 | GET | `/api/v1/ingest/graph` | Knowledge graph | app/api/ingest.py |
| 28 | POST | `/api/v1/ingest/search` | Hybrid search | app/api/ingest.py |
| 29 | GET | `/api/v1/provenance/` | Trace history | app/api/provenance.py |
| 30 | GET | `/api/v1/provenance/traces/{id}` | Full trace | app/api/provenance.py |
| 31 | GET | `/api/v1/dashboard/stats` | Dashboard metrics | app/api/dashboard.py |
| 32 | GET | `/api/v1/dashboard/recent` | Recent activity | app/api/dashboard.py |
| 33 | POST | `/api/v1/feedback/` | Submit feedback | app/api/feedback.py |
| 34 | GET | `/api/v1/feedback/` | List feedback | app/api/feedback.py |
| 35 | POST | `/api/v1/api-keys/` | Create API key | app/api/api_keys.py |
| 36 | GET | `/api/v1/api-keys/` | List API keys | app/api/api_keys.py |
| 37 | DELETE | `/api/v1/api-keys/{id}` | Revoke API key | app/api/api_keys.py |
| 38 | POST | `/api/v1/storage/presign` | Presigned URL | app/api/storage.py |
| 39 | GET | `/api/v1/storage/files` | List files | app/api/storage.py |
| 40 | POST | `/api/v1/policy/` | Create policy | app/api/policy.py |
| 41 | GET | `/api/v1/policy/` | List policies | app/api/policy.py |
| 42 | POST | `/api/v1/audit/query` | Query audit log | app/api/audit.py |
| 43 | GET | `/api/v1/audit/me` | My audit events | app/api/audit.py |

**Source:** app/main.py:140-156 (router inclusion).

### 4.3 Authentication

All `/api/v1/*` endpoints require Bearer JWT. Auth is OAuth2 Password Bearer (no SSO yet).

| Token | Lifetime | Env Var | Source File |
|---|---|---|---|
| Access | 60 min | `ACCESS_TOKEN_EXPIRE_MINUTES` | app/core/config.py |
| Refresh | 30 days | `REFRESH_TOKEN_EXPIRE_DAYS` | app/core/config.py |
| Algorithm | HS256 | — | app/core/security.py |

---

## 5. Feature Catalog

### 5.1 Features by Domain

| Feature | Status | Source File | Description |
|---|---|---|---|
| **Multi-tenant** | Stable | app/models.py:18 | Tenant→Workspace→Member hierarchy |
| **JWT Auth** | Stable | app/api/auth.py | Registration, login, refresh, logout |
| **Email Verification** | Partial | app/models.py:79 | Field exists but no verification flow implemented |
| **RBAC** | Stable | app/middleware/rbac.py | OWNER, ADMIN, MEMBER, VIEWER |
| **Rate Limiting** | Stable | app/middleware/rate_limit.py | In-memory sliding window |
| **Request ID** | Stable | app/main.py:22 | X-Request-ID injection |
| **Security Headers** | Stable | app/main.py:48 | CSP, HSTS, X-Frame-Options |
| **Structured Logging** | Stable | app/main.py:88 | JSON structured format |
| **Error Sanitization** | Stable | app/main.py:113 | No secrets in error responses |
| **CORS** | Stable | app/main.py:215 | Production-safe origins |
| **Policy Engine** | Stable | app/api/policy.py | Authorization rules |
| **Tenancy** | Stable | app/middleware/tenancy.py | Row-level isolation |
| **Chat** | Stable | app/api/chat.py | LLM completion + streaming |
| **Memory/RAG** | Stable | app/api/memory.py | Semantic vector search |
| **Ingestion** | Stable | app/services/pipeline.py | Full M0-M5 pipeline |
| **Fact Extraction** | Stable | app/services/m2_facts.py | Subject-predicate-object |
| **Decision Extraction** | Stable | app/services/m2_facts.py | Content + confidence |
| **Graph** | Stable | app/services/m4_graph.py | Entity + relationship persistence |
| **Temporal** | Stable | app/services/m3_temporal.py | Fact supersession |
| **Session Understanding** | Stable | app/services/m1_session.py | Topics, entities, intents |
| **Provenance** | Stable | app/api/provenance.py | Full trace visibility |
| **Feedback** | Stable | app/api/feedback.py | Like/dislike on messages |
| **Dashboard** | Stable | app/api/dashboard.py | Stats + recent activity |
| **API Keys** | Stable | app/api/api_keys.py | Programmatic access |
| **Object Storage** | Stable | app/services/object_storage.py | S3 + MinIO + Filesystem |
| **Audit** | Stable | app/services/audit.py | Persistent security events |
| **Alembic Migrations** | Stable | alembic/versions/ | 12 migrations |
| **LLM Provider** | Stable | app/services/llm.py | Anthropic + OpenAI + DeepSeek + Mock |
| **Connectors** | Stable | app/services/connectors.py | Input format normalization |
| **Search** | Stable | app/services/retrieval.py | Hybrid BM25 + semantic + graph |

### 5.2 Features NOT Present

| Feature | Status | Notes |
|---|---|---|
| SSO/OAuth2 | Not present | Only email+password |
| Redis rate limiting | Not present | In-memory only |
| Multi-region | Not present | Single DB |
| Webhooks | Not present | No outbound |
| Real-time/SSE | Present | useSSE.tsx hook + /api/v1/chat/stream endpoint | Chat streaming via fetch + SSE |
| Encryption at rest | Not present | DB-level only |

---

## 6. Validation & Guardrails

### 6.1 Guardrail Layers

| Layer | Mechanism | Source File | Covers |
|---|---|---|---|
| **Pydantic Schemas** | Type validation | app/schemas.py | All input/output shapes |
| **SQLAlchemy** | Constraint enforcement | app/models.py | DB-level integrity |
| **Middleware** | Request processing | app/main.py | Rate limiting, auth, CORS |
| **RBAC** | Permission checks | app/middleware/rbac.py | Role-based access |
| **Tenancy** | Row isolation | app/middleware/tenancy.py | Cross-tenant access prevention |
| **Security Headers** | CSP, HSTS, etc. | app/main.py:48 | XSS, clickjacking, MITM |
| **Error Sanitization** | Secret stripping | app/main.py:113 | No passwords in errors |
| **Policy Engine** | Authorization rules | app/api/policy.py | Fine-grained access |
| **Validation Errors** | 422 handler | app/main.py:231 | Malformed input |
| **DB Error Handler** | 500 handler | app/main.py:236 | DB failures |

### 6.2 Validation Rules

| Rule | Enforcement | Source File |
|---|---|---|
| Email unique globally | DB unique index | app/models.py:71 |
| Password min length | Pydantic | app/schemas.py |
| Workspace slug unique per tenant | DB unique constraint | app/models.py:48 |
| Fact current temporal_status for dedup | WHERE clause | app/services/pipeline.py:222 |
| Message content not empty | Pydantic | app/schemas.py |
| Project title required | Pydantic | app/schemas.py |
| Source type enum | SQLAlchemy Enum | app/models.py |
| Fact temporal_status enum | SQLAlchemy Enum | app/models.py |
| Decision temporal_status enum | SQLAlchemy Enum | app/models.py |
| Memory status enum | SQLAlchemy Enum | app/models.py |
| Feedback direction enum | SQLAlchemy Enum | app/models.py |
| UserRole enum | SQLAlchemy Enum | app/models.py |
| API key prefix validation | Pydantic | app/schemas.py |
| LLM provider enum | Settings | app/core/config.py |

### 6.3 Rate Limit Rules

| Path Pattern | Max Requests | Window | Key | Source File |
|---|---|---|---|---|
| `/api/v1/auth/` | 5 | 60s | IP | app/middleware/rate_limit.py |
| `/api/v1/chat/` | 10 | 60s | IP | app/middleware/rate_limit.py |
| `/api/v1/ingest/` | 3 | 60s | IP | app/middleware/rate_limit.py |
| Default | 100 | 60s | IP | app/middleware/rate_limit.py |

---

## 7. Database Tables Maintained

### 7.1 Table Registry

| Table | PK | FK | Unique | Enum Columns | Timestamps | Soft Delete | Migration | Source File |
|---|---|---|---|---|---|---|---|---|
| **tenants** | ✓ | 0 | slug | — | ✓ | — | 001 | app/models.py:18 |
| **workspaces** | ✓ | tenants | — | — | ✓ | deleted_at | 001 | app/models.py:39 |
| **users** | ✓ | 0 | email | — | ✓ | deleted_at | 001 | app/models.py:65 |
| **workspace_members** | ✓ | workspaces, users | (ws, user) | UserRole | — | — | 001 | app/models.py:97 |
| **invitations** | ✓ | workspaces | — | — | ✓ | — | 012 | app/models.py:123 |
| **refresh_tokens** | ✓ | users | — | — | ✓ | — | 001 | app/models.py:147 |
| **sessions** | ✓ | projects, users | — | — | ✓ | — | 003 | app/models.py:165 |
| **messages** | ✓ | sessions, users | — | — | ✓ | — | 003 | app/models.py:191 |
| **projects** | ✓ | workspaces | — | — | ✓ | — | 001 | app/models.py:209 |
| **memory** | ✓ | workspaces, projects | — | status enum | ✓ | — | 004 | app/models.py:232 |
| **ingest_jobs** | ✓ | projects, workspaces | — | status enum | ✓ | — | 003 | app/models.py:269 |
| **sources** | ✓ | projects, workspaces | — | source_type enum | ✓ | — | 003 | app/models.py:302 |
| **normalized_messages** | ✓ | sources, sessions | — | — | ✓ | — | 003 | app/models.py:370 |
| **facts** | ✓ | workspaces, projects, sources | — | temporal_status | ✓ | deleted_at | 003 | app/models.py:414 |
| **decisions** | ✓ | workspaces, projects | — | temporal_status | ✓ | deleted_at | 003 | app/models.py:468 |
| **graph_nodes** | ✓ | workspaces, projects, sources | — | temporal_status | ✓ | deleted_at | 003 | app/models.py:521 |
| **graph_edges** | ✓ | workspaces, projects | — | — | ✓ | deleted_at | 003 | app/models.py:562 |
| **message_provenance** | ✓ | messages | — | — | ✓ | — | 002 | app/models.py:608 |
| **message_feedback** | ✓ | messages | — | direction enum | ✓ | — | 005 | app/models.py:657 |
| **api_keys** | ✓ | workspaces | key_hash | — | ✓ | — | 007 | app/models.py:685 |
| **policies** | ✓ | workspaces | — | — | ✓ | — | 009 | app/models.py:728 |
| **policy_versions** | ✓ | policies | — | — | ✓ | — | 009 | app/models.py:762 |
| **audit_events** | ✓ | workspaces | — | — | ✓ | — | 010 | app/models.py:789 |

**Total: 23 tables, 12 migrations.**

### 7.2 Migration Register

| Migration | Table(s) | Change | Source File |
|---|---|---|---|
| 001 | tenants, workspaces, users, workspace_members, refresh_tokens | Initial schema | alembic/versions/001 |
| 002 | message_provenance | Source-content-hash columns | alembic/versions/002 |
| 003 | sessions, messages, normalized_messages, sources, ingest_jobs | Sprint 3 pipeline tables | alembic/versions/003 |
| 004 | memory | Sprint 4 memory columns | alembic/versions/004 |
| 005 | message_feedback | Message feedback | alembic/versions/005 |
| 006 | graph_node_temporal | Temporal supersession | alembic/versions/006 |
| 007 | api_keys | API key management | alembic/versions/007 |
| 008 | sources | Source content hash | alembic/versions/008 |
| 009 | policies, policy_versions | Policy engine | alembic/versions/009 |
| 010 | audit_events | Audit log | alembic/versions/010 |
| 011 | memory, facts | Tenant column | alembic/versions/011 |
| 012 | invitations | Workspace invitations | alembic/versions/012 |

### 7.3 Schema Constraints

| Constraint | Tables | Type | Source File |
|---|---|---|---|
| `workspaces.slug` UNIQUE | workspaces | Unique | app/models.py:48 |
| `workspaces(tenant_id, slug)` | workspaces | Composite unique | app/models.py |
| `users.email` UNIQUE | users | Unique | app/models.py:71 |
| `workspace_members(workspace_id, user_id)` | workspace_members | Composite unique | app/models.py |
| `graph_nodes.workspace_id` | graph_nodes | Partial unique | app/models.py |
| `policies.workspace_id` | policies | Partial unique | app/models.py |

---

## 8. Security Architecture

### 8.1 Middleware Stack (outermost to innermost)

```
Request
  │
  ▼
SecurityHeadersMiddleware       ← CSP, HSTS, X-Frame-Options, etc. (app/main.py:48)
  │
  ▼
RequestIdMiddleware              ← X-Request-ID + latency (app/main.py:22)
  │
  ▼
AuditPersistenceMiddleware      ← Flush audit events per-request (app/main.py:193)
  │
  ▼
CORSMiddleware                  ← CORS origin restriction (app/main.py:215)
  │
  ▼
RateLimitMiddleware             ← Sliding window (app/main.py:227)
  │
  ▼
TenancyMiddleware               ← Cross-tenant isolation (app/main.py)
  │
  ▼
AuthMiddleware                  ← JWT Bearer (app/main.py)
  │
  ▼
RBACMiddleware                  ← Role check (app/main.py)
  │
  ▼
[Endpoint]
  │
  ▼
Response
```

### 8.2 Role Matrix

| Role | Permissions | Source File |
|---|---|---|
| **OWNER** | Full control: create/read/update/delete all resources | app/middleware/rbac.py |
| **ADMIN** | Member management, project CRUD | app/middleware/rbac.py |
| **MEMBER** | Chat, ingest, memory search, own messages | app/middleware/rbac.py |
| **VIEWER** | Read-only: dashboard, memory, provenance | app/middleware/rbac.py |

### 8.3 Security Headers

| Header | Production | Development | Source File |
|---|---|---|---|
| X-Content-Type-Options | nosniff | nosniff | app/main.py:53 |
| X-Frame-Options | DENY | DENY | app/main.py:54 |
| X-XSS-Protection | 1; mode=block | 1; mode=block | app/main.py:55 |
| Referrer-Policy | strict-origin-when-cross-origin | strict-origin-when-cross-origin | app/main.py:56 |
| Permissions-Policy | geolocation=(), mic=(), cam=() | geolocation=(), mic=(), cam=() | app/main.py:57 |
| HSTS | max-age=31536000; includeSubDomains | — | app/main.py:59 |
| CSP | Restrictive self-only | Allows localhost | app/main.py:60-81 |

### 8.4 Secrets & Credentials

| Secret | Env Var | Status | Source File |
|---|---|---|---|
| JWT Secret | `SECRET_KEY` | Set | app/core/config.py |
| LLM Key (Anthropic) | `ANTHROPIC_API_KEY` | Empty (MockProvider) | app/core/config.py |
| LLM Key (OpenAI) | `OPENAI_API_KEY` | Empty | app/core/config.py |
| LLM Key (DeepSeek) | `DEEPSEEK_API_KEY` | Populated | app/core/config.py |
| Database URL | `DATABASE_URL` | swarmvault (production) | app/core/config.py |
| JWT Algorithm | `ALGORITHM` | HS256 | app/core/config.py |

**Correction:** Previous manifests listed an `OPENROUTER_API_KEY` in the secrets table. That key does not exist in any current source file. The only configured LLM keys are `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and `DEEPSEEK_API_KEY`. `OPENROUTER_API_KEY` is NOT present.

### 8.5 Audit Events

| Event | Trigger | Persisted | Source File |
|---|---|---|---|
| `auth.login` | User logs in | Yes (PostgreSQL) | app/services/audit.py |
| `auth.logout` | User logs out | Yes | app/services/audit.py |
| `auth.register` | User registers | Yes | app/services/audit.py |
| `ingest.create` | Source created | Yes | app/services/audit.py |
| `ingest.complete` | Pipeline finished | Yes | app/services/audit.py |
| `ingest.failed` | Pipeline failed | Yes | app/services/audit.py |
| `chat.message` | Chat completion | Yes | app/services/audit.py |
| `policy.create` | Policy created | Yes | app/services/audit.py |
| `policy.update` | Policy updated | Yes | app/services/audit.py |
| `policy.delete` | Policy deleted | Yes | app/services/audit.py |
| `project.create` | Project created | Yes | app/services/audit.py |
| `project.delete` | Project deleted | Yes | app/services/audit.py |
| `project.update` | Project updated | Yes | app/services/audit.py |

Audit events are buffered per-request and flushed by `AuditPersistenceMiddleware` (app/main.py:193). Buffer bounded at 1000 events (drop-oldest policy).

### 8.6 Error Handling

| Error | Status | Sanitized | Source File |
|---|---|---|---|
| 422 Validation | Yes | Yes (sanitize_detail) | app/main.py:231 |
| 500 Database | Yes | Yes | app/main.py:236 |
| 500 Generic | Yes | Yes | app/main.py:242 |
| 401 Auth | Yes | Bearer header | app/middleware/auth.py:21 |
| 403 RBAC | Yes | — | app/middleware/rbac.py |

### 8.7 Rate Limit Configuration

| Path | Max | Window | Key | Source File |
|---|---|---|---|---|
| `/api/v1/auth/` | 5 | 60s | IP | app/middleware/rate_limit.py |
| `/api/v1/chat/` | 10 | 60s | IP | app/middleware/rate_limit.py |
| `/api/v1/ingest/` | 3 | 60s | IP | app/middleware/rate_limit.py |
| Default | 100 | 60s | IP | app/middleware/rate_limit.py |

### 8.8 Authentication Config

| Setting | Default | Env Var | Source File |
|---|---|---|---|
| Secret | — | `SECRET_KEY` | app/core/config.py |
| Algorithm | HS256 | `ALGORITHM` | app/core/security.py |
| Access Expiry | 60 min | `ACCESS_TOKEN_EXPIRE_MINUTES` | app/core/config.py |
| Refresh Expiry | 30 days | `REFRESH_TOKEN_EXPIRE_DAYS` | app/core/config.py |
| Token URL | `auth/login` | — | app/middleware/auth.py |

---

## 9. Frontend Pages

### 9.1 Page Map

| Route | Component | Purpose | Source File |
|---|---|---|---|
| `/` | DashboardPage | Landing (public) | frontend/src/app/page.tsx |
| `/auth/login` | LoginPage | Sign in | frontend/src/app/auth/login/page.tsx |
| `/auth/register` | RegisterPage | Sign up | frontend/src/app/auth/register/page.tsx |
| `/dashboard` | DashboardPage | Home | frontend/src/app/dashboard/page.tsx |
| `/projects` | ProjectsListPage | Project list | frontend/src/app/projects/page.tsx |
| `/settings` | SettingsLayoutPage | Settings hub | frontend/src/app/settings/page.tsx |
| `/settings/api-keys` | APIKeysPage | Key management | frontend/src/app/settings/api-keys/page.tsx |
| `/settings/profile` | ProfilePage | Profile edit | frontend/src/app/settings/profile/page.tsx |
| `/settings/storage` | StoragePage | Storage settings | frontend/src/app/settings/storage/page.tsx |
| `/projects/{id}/chat` | ChatPage | AI chat | frontend/src/app/projects/[id]/chat/page.tsx |
| `/projects/{id}/decisions` | DecisionsPage | Extracted decisions | frontend/src/app/projects/[id]/decisions/page.tsx |
| `/projects/{id}/facts` | FactsPage | Extracted facts | frontend/src/app/projects/[id]/facts/page.tsx |
| `/projects/{id}/graph` | GraphPage | Knowledge graph | frontend/src/app/projects/[id]/graph/page.tsx |
| `/projects/{id}/ingest` | IngestPage | Upload + ingest | frontend/src/app/projects/[id]/ingest/page.tsx |
| `/projects/{id}/memory` | MemoryPage | Semantic search | frontend/src/app/projects/[id]/memory/page.tsx |
| `/projects/{id}/provenance` | ProvenancePage | Trace history | frontend/src/app/projects/[id]/provenance/page.tsx |
| `/projects/{id}/search` | SearchPage | Hybrid search | frontend/src/app/projects/[id]/search/page.tsx |
| `/projects/{id}/sessions` | SessionsPage | Conversation list | frontend/src/app/projects/[id]/sessions/page.tsx |
| `/projects/{id}/sessions/{sid}` | SessionDetailPage | Conversation detail | frontend/src/app/projects/[id]/sessions/[sid]/page.tsx |
| `/projects/{id}/settings` | ProjectSettingsPage | Project config | frontend/src/app/projects/[id]/settings/page.tsx |
| `/projects/{id}/timeline` | TimelinePage | Chronological view | frontend/src/app/projects/[id]/timeline/page.tsx |

**Total: 21 pages (10 static, 11 dynamic).**

### 9.2 Frontend Feature Matrix

| Feature | Pages | Source File |
|---|---|---|
| Responsive sidebar | All | frontend/src/components/Sidebar.tsx |
| Theme (light/dark) | All | frontend/src/app/providers/ThemeProvider.tsx |
| Authentication state | Auth + protected | frontend/src/contexts/AuthContext.tsx |
| Project switcher | All project pages | frontend/src/components/ProjectSwitcher.tsx |
| Empty states | All data pages | Per-page component |
| Error boundaries | All | frontend/src/app/error.tsx |

---

## 10. Observability & Audit

### 10.1 Structured Logging

All logs are JSON-formatted via `StructuredFormatter` (app/main.py:88).

| Field | Value |
|---|---|
| timestamp | ISO 8601 |
| level | INFO, WARNING, ERROR |
| logger | Module name |
| message | Log message |
| request_id | X-Request-ID UUID |
| exception | Stack trace (if any) |

Log level configurable via `LOG_LEVEL` env var.

### 10.2 Health Checks

| Endpoint | Purpose | DB Check | Source File |
|---|---|---|---|
| `/health/live` | Liveness | No | app/main.py:256 |
| `/health/ready` | Readiness | Yes (SELECT 1) | app/main.py:261 |
| `/health` | Basic | No | app/main.py:277 |

### 10.3 Metrics

Metrics disabled by default (`ENABLE_METRICS=false`). No Prometheus endpoint.

### 10.4 Audit Service

| Aspect | Detail | Source File |
|---|---|---|
| Buffer size | 1000 events (drop-oldest) | app/services/audit/service.py:136 |
| Persistence | PostgreSQL per-request | app/main.py:193 |
| Disabled for testing | `_disabled_for_testing` | app/services/audit/service.py |
| Buffer reclaim | Clear on persist/fail | app/services/audit/service.py:189 |

---

## Appendix A: Corrected Items from v0

1. **LLM Provider**: v0 listed "Mistral" and "Cohere" as providers. Current code (app/services/llm.py) supports Anthropic, OpenAI, DeepSeek, and Mock only. Mistral and Cohere are NOT present.

2. **Models**: v0 listed "Embedding" as a separate model. Current code (app/models.py) has 23 models; Embedding is not a separate model — it is the `memory` table with vector columns.

3. **API Keys**: v0 listed "Keycloak" and "Vault" for secrets. Current code uses `SECRET_KEY` env var (app/core/config.py). No Keycloak, no Vault.

4. **Rate Limiter**: v0 said "Redis-backed". Current code (app/middleware/rate_limit.py) is in-memory only, with a comment that production should replace with Redis.

5. **Router count**: v0 said "81 endpoints across 14 routers". Current code (app/main.py:140-156) has 14 router includes with 78 endpoints. Updated to reflect corrected counts: workspace (14), projects (5), sessions (6), chat (2), memory (6), ingest (14), provenance (3), dashboard (2), feedback (3), api_keys (4), storage (3), policy (7), audit (3).

6. **R5 items**: v0 listed R5-1, R5-2, R5-3, R5-4. All four items are complete (commits c6c34d9, d830f45).

7. **OPENROUTER_API_KEY**: v0 listed this as a configured secret. Current code does NOT have an OPENROUTER_API_KEY env var. Only ANTHROPIC_API_KEY, OPENAI_API_KEY, and DEEPSEEK_API_KEY exist.

---

## Appendix B: Source Authority Map

| Manifest Section | Source File | Authority |
|---|---|---|
| Entity catalog | app/models.py (835 lines, 23 classes) | Single source of truth |
| Pipeline stages | app/services/pipeline.py (238 lines) | Single source of truth |
| API routes | app/main.py:140-156 | Single source of truth |
| Security headers | app/main.py:48-82 | Single source of truth |
| Middleware stack | app/main.py:22-228 | Single source of truth |
| Rate limiting | app/middleware/rate_limit.py | Single source of truth |
| Audit events | app/services/audit/service.py | Single source of truth |
| Database tables | app/models.py (835 lines, 23 classes) | Single source of truth |
| Migrations | alembic/versions/ | Single source of truth |
| Frontend pages | frontend/src/app/ | Single source of truth |
| LLM providers | app/services/llm.py | Single source of truth |
| Env vars | app/core/config.py, .env | Single source of truth |
| Test counts | pytest output, Playwright output | Tool-printed only |

---

*This document is maintained by source-of-truth reconciliation. When source diverges from document, source wins and document is corrected.*
