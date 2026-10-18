# FRONTEND_CORE_CAPABILITY_MATRIX.md

## Phase 2B — Core Capability Proof

**Date:** 2026-09-05
**Method:** Tracing UI → API → backend handler → Core function → storage for each feature

---

## Legend

- **A** = Verified Core capability (exists in `app/services/` or `app/core/`)
- **B** = Verified WebApp/backend capability (exists in `app/api/` or `app/services/`)
- **C** = Presentation/composition capability (frontend-only logic)
- **D** = Unsupported/future (no backend implementation)

---

## Feature-by-Feature Trace

### 1. Search
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | `search/page.tsx` | ✅ |
| Hook | `useSearch.ts` | ✅ |
| API | `POST /api/v1/ingest/search` | ✅ B |
| Backend Handler | `ingest.py:search()` | ✅ |
| Core Function | `M5 retrieval: retrieve_hybrid()` | ✅ A |
| Storage | PostgreSQL (Memory, Fact, Decision tables) | ✅ A |
| **Classification** | **A** — Full pipeline implemented |
| **Known Issues** | ⚠️ `search/page.tsx` uses GET request, backend requires POST with query params |

### 2. Chat
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | `chat/page.tsx` | ✅ |
| Hook | `useChat.ts` (uses `useSSE.tsx`) | ❌ Broken — EventSource cannot POST |
| API | `POST /api/v1/chat/stream` | ✅ B |
| Backend Handler | `chat.py:stream_chat()` | ✅ |
| Core Function | `process_chat()` → `retrieve_memories()` → LLM provider | ✅ A |
| Storage | PostgreSQL (Message, Session tables) | ✅ A |
| **Classification** | **B** (page.tsx works, hook broken) |
| **Known Issues** | ❌ `useChat.ts` uses EventSource (GET) — streaming broken. `chat/page.tsx` works via direct `fetch()` POST. Missing `project_id`/`session_id` in request. |

### 3. Memory
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | `memory/page.tsx` | ✅ |
| Hook | `useMemory.ts` | ✅ |
| API | `GET/POST/DELETE /api/v1/memory/*` | ✅ B |
| Backend Handler | `memory.py:*` | ✅ |
| Core Function | `MemoryService.write/read/update/delete/search` | ✅ A |
| Storage | PostgreSQL (Memory table) + AuditService | ✅ A |
| **Classification** | **A** — Full CRUD with policy enforcement |
| **Known Issues** | None |

### 4. Facts
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | `facts/page.tsx` | ⚠️ Wrong local type |
| API | `GET /api/v1/ingest/facts` | ✅ B |
| Backend Handler | `ingest.py:list_facts()` | ✅ |
| Core Function | Pipeline M3 (fact extraction) | ✅ A |
| Storage | PostgreSQL (Fact table) | ✅ A |
| **Classification** | **A** |
| **Known Issues** | ⚠️ `facts/page.tsx` uses local `FactItem` with `statement` field — backend returns `content`, `subject`, `predicate`, `object`. Rendered data will be wrong. |

### 5. Decisions
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | `decisions/page.tsx` | ⚠️ Wrong local type |
| API | `GET /api/v1/ingest/decisions` | ✅ B |
| Backend Handler | `ingest.py:list_decisions()` | ✅ |
| Core Function | Pipeline M3 (decision extraction) | ✅ A |
| Storage | PostgreSQL (Decision table) | ✅ A |
| **Classification** | **A** |
| **Known Issues** | ⚠️ `decisions/page.tsx` uses local `DecisionItem` with `tags: string[]` — backend has no `tags` field. Will render empty tags section. |

### 6. Timeline
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | `timeline/page.tsx` | ✅ |
| API | `GET /api/v1/ingest/timeline` | ✅ B |
| Backend Handler | `ingest.py:get_timeline()` | ✅ |
| Core Function | Aggregates Fact + Decision + Memory timestamps | ✅ A |
| Storage | PostgreSQL (multiple tables) | ✅ A |
| **Classification** | **A** |
| **Known Issues** | None |

### 7. Sessions
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | `sessions/page.tsx`, `sessions/[sessionId]/page.tsx` | ✅ |
| API | `GET/POST/DELETE /api/v1/sessions/*` | ✅ B |
| Backend Handler | `sessions.py:*` | ✅ |
| Core Function | Session CRUD via SQLAlchemy | ✅ B |
| Storage | PostgreSQL (Session, Message tables) | ✅ A |
| **Classification** | **B** — Direct ORM, no special Core service |
| **Known Issues** | None |

### 8. Graph
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | `graph/page.tsx` | ✅ |
| Hook | `useGraph.ts` | ❌ Wrong endpoint path |
| API | `GET /api/v1/ingest/graph` | ✅ B |
| Backend Handler | `ingest.py:get_graph()` | ✅ |
| Core Function | Pipeline M4 (graph extraction) | ✅ A |
| Storage | PostgreSQL (GraphNode, GraphEdge tables) | ✅ A |
| **Classification** | **A** |
| **Known Issues** | ❌ `useGraph.ts` calls `/api/v1/graph` (404). `graph/page.tsx` correctly calls `/api/v1/ingest/graph`. Hook broken, page works. |

### 9. Provenance
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | `provenance/page.tsx` | ✅ |
| API | `GET /api/v1/provenance/*` | ✅ B |
| Backend Handler | `provenance.py:*` | ✅ |
| Core Function | `MessageProvenance` model + `AuditService` | ✅ B |
| Storage | PostgreSQL (MessageProvenance table) | ✅ A |
| **Classification** | **B** |
| **Known Issues** | None |

### 10. Sources / Upload
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | `ingest/page.tsx` | ✅ |
| Hook | `useIngest.ts` | ✅ |
| API | `POST /api/v1/ingest/upload` | ✅ B |
| Backend Handler | `ingest.py:upload_and_ingest()` | ✅ |
| Core Function | Pipeline M0→M5 (`run_pipeline`) | ✅ A |
| Storage | PostgreSQL (Source, NormalizedMessage) + file storage | ✅ A |
| **Classification** | **A** — Full ingestion pipeline |
| **Known Issues** | ⚠️ `useIngestJobs` type mismatch (expects array, gets `{items, total}`) |

### 11. Projects
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | `projects/page.tsx`, layout | ✅ |
| Hook | `useProjects.ts` | ✅ |
| API | `GET/POST/PATCH/DELETE /api/v1/projects/*` | ✅ B |
| Backend Handler | `projects.py:*` | ✅ |
| Core Function | Project ORM CRUD | ✅ B |
| Storage | PostgreSQL (Project table) | ✅ A |
| **Classification** | **B** |
| **Known Issues** | None |

### 12. Dashboard
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | `dashboard/page.tsx` | ✅ |
| API | `GET /api/v1/dashboard/` | ✅ B |
| Backend Handler | `dashboard.py:workspace_overview()` | ✅ |
| Core Function | Aggregate queries across Memory, Source, Session, Fact, Decision, GraphNode, GraphEdge | ✅ B |
| Storage | PostgreSQL (multiple tables) | ✅ A |
| **Classification** | **B** |
| **Known Issues** | None |

### 13. API Keys
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | `settings/api-keys/page.tsx` | ✅ |
| Hook | `useApiKeys.ts` | ⚠️ Field name mismatch |
| API | `GET/POST/DELETE/POST-rotate /api/v1/api-keys/*` | ✅ B |
| Backend Handler | `api_keys.py:*` | ✅ |
| Core Function | SHA-256 key hashing, `_generate_key()` | ✅ B |
| Storage | PostgreSQL (ApiKey table) | ✅ A |
| **Classification** | **B** |
| **Known Issues** | ⚠️ `prefix` vs `key_prefix` field name mismatch |

### 14. Storage
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | `settings/storage/page.tsx` | ✅ |
| API | `POST/GET/DELETE /api/v1/storage/*` | ✅ B |
| Backend Handler | `storage.py:*` | ✅ |
| Core Function | `get_storage_provider()`, content-hash dedup | ✅ A |
| Storage | Local filesystem (configurable) + PostgreSQL metadata | ✅ A |
| **Classification** | **A** |
| **Known Issues** | None |

### 15. Settings / Profile
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | `settings/page.tsx`, `settings/profile/page.tsx` | ✅ |
| API | `GET/PATCH /api/v1/workspace/`, `POST /api/v1/auth/change-password` | ✅ B |
| Backend Handler | `workspace.py:*`, `auth.py:change_password` | ✅ |
| Core Function | ORM updates + bcrypt password hashing | ✅ B |
| Storage | PostgreSQL (User, Workspace tables) | ✅ A |
| **Classification** | **B** |
| **Known Issues** | None |

### 16. Operations (Board, Agents, Claims, Tasks, Supervisor, Signals, Schedules)
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | Not implemented | — |
| API | Not implemented | — |
| Backend | Not implemented | — |
| Core | Partially (Task, Claim models exist) | ⚠️ |
| **Classification** | **D** — No API, no UI, no verified Core service |
| **Decision** | **DEFER** — Not in Phase 1 scope |

### 17. Trust / Knowledge Trust
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | Not implemented as separate page | — |
| API | Confidence/authority on Facts, Provenance | ✅ B |
| Backend | Fact.confidence, Fact.authority, Provenance.confidence | ✅ |
| Core | Pipeline confidence scoring | ✅ A |
| **Classification** | **C** — Data exists, no dedicated trust page |

### 18. Context Packs
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | Not implemented | — |
| API | Not implemented | — |
| Backend | Not implemented | — |
| Core | Not implemented | — |
| **Classification** | **D** — No implementation |
| **Decision** | **DEFER** |

### 19. Conflicts
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | Not implemented | — |
| API | Not implemented | — |
| Backend | Not implemented | — |
| Core | Not implemented | — |
| **Classification** | **D** — No implementation |
| **Decision** | **DEFER** |

### 20. Procedures
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | Not implemented | — |
| API | Not implemented | — |
| Backend | Not implemented | — |
| Core | Not implemented | — |
| **Classification** | **D** — No implementation |
| **Decision** | **DEFER** |

### 21. Checkpoints
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | Not implemented | — |
| API | Not implemented | — |
| Backend | Not implemented | — |
| Core | Not implemented | — |
| **Classification** | **D** — No implementation |
| **Decision** | **DEFER** |

### 22. Watcher / Sync
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | Not implemented | — |
| API | Not implemented | — |
| Backend | Not implemented | — |
| Core | Not implemented | — |
| **Classification** | **D** — No implementation |
| **Decision** | **DEFER** |

### 23. Usage / System Health
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | Not implemented | — |
| API | `/health/*` only | ⚠️ B (limited) |
| Backend | Health checks only | ⚠️ B (limited) |
| Core | Structured logging exists | ✅ B |
| **Classification** | **B** (limited) |
| **Decision** | **DEFER** full system health page — health endpoints exist but no usage metrics API |

### 24. Recovery / Archive / Lifecycle
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | Not implemented | — |
| API | Soft-delete on most endpoints | ✅ B |
| Backend | `deleted_at` soft-delete pattern | ✅ B |
| Core | No recovery/restore operations | ⚠️ |
| **Classification** | **C** — Soft-delete exists, no restore/recovery API |
| **Decision** | **DEFER** recovery UI |

### 25. Authentication
| Layer | Component/Function | Verdict |
|-------|-------------------|---------|
| UI | Login/Register pages | ✅ |
| API | `/auth/login`, `/auth/register`, `/auth/refresh`, `/auth/logout`, `/auth/me` | ✅ B |
| Backend | JWT HS256, bcrypt, RefreshToken model | ✅ A |
| Core | `app/core/security.py` | ✅ A |
| Storage | PostgreSQL (User, RefreshToken tables) | ✅ A |
| **Classification** | **A** |
| **Known Issues** | ⚠️ Logout sends empty body instead of refresh_token |

---

## Capability Classification Summary

| Classification | Features |
|----------------|----------|
| **A** (Verified Core) | Search, Chat, Memory, Facts, Decisions, Timeline, Graph, Sources/Upload, Storage, Authentication |
| **B** (Verified Backend) | Sessions, Provenance, Projects, Dashboard, API Keys, Settings, Policies (API exists), Audit (API exists) |
| **C** (UI Composition) | Knowledge Trust (data exists, no dedicated page), Recovery (soft-delete only) |
| **D** (Unsupported/Future) | Operations, Context Packs, Conflicts, Procedures, Checkpoints, Watcher/Sync, System Health (full), Recovery UI, Storage/Recovery, Archive/Lifecycle, Board, Agents, Claims, Tasks, Supervisor, Signals, Schedules, Usage |

---

## Navigation Mapping to Capabilities

| Navigation Item (from redesign plan) | Capability | Decision |
|---------------------------------------|-----------|----------|
| Command Center | Dashboard API ✅ | **IMPLEMENT** |
| Projects | Projects API ✅ | **IMPLEMENT** |
| What Changed | Timeline API ✅ | **IMPLEMENT** |
| Chat | Chat/SSE API ✅ | **IMPLEMENT (fix hook)** |
| Knowledge Search | Search API ✅ | **IMPLEMENT (fix method)** |
| Memory | Memory API ✅ | **IMPLEMENT (fix types)** |
| Facts | Facts API ✅ | **IMPLEMENT (fix types)** |
| Decisions | Decisions API ✅ | **IMPLEMENT (fix types)** |
| Conflicts | ❌ No API | **DEFER** |
| Procedures | ❌ No API | **DEFER** |
| Timeline | Timeline API ✅ | **IMPLEMENT** |
| Context Packs | ❌ No API | **DEFER** |
| Sessions | Sessions API ✅ | **IMPLEMENT** |
| Graph | Graph API ✅ | **IMPLEMENT (fix path)** |
| Sources | Sources API ✅ | **IMPLEMENT** |
| Upload | Upload API ✅ | **IMPLEMENT** |
| Sync | ❌ No async API | **DEFER** |
| Watcher | ❌ No API | **DEFER** |
| Checkpoints | ❌ No API | **DEFER** |
| Board | ❌ No API | **DEFER** |
| Agents | ❌ No API | **DEFER** |
| Claims | ❌ No API | **DEFER** |
| Tasks | ❌ No API | **DEFER** |
| Supervisor | ❌ No API | **DEFER** |
| Signals | ❌ No API | **DEFER** |
| Schedules | ❌ No API | **DEFER** |
| Usage | ❌ No metrics API | **DEFER** |
| Provenance | Provenance API ✅ | **IMPLEMENT** |
| Knowledge Trust | Data exists, no API | **DEFER** (use provenance data) |
| Evidence | Provenance/memories API ✅ | **IMPLEMENT** |
| System Health | Health only | **DEFER** (no usage metrics) |
| Knowledge Health | ❌ No API | **DEFER** |
| Storage & Recovery | Storage API ✅ | **IMPLEMENT** |
| Archive / Lifecycle | ❌ No API | **DEFER** |
| Diagnostics | ❌ No API | **DEFER** |
| Settings | Workspace/settings API ✅ | **IMPLEMENT** |
| Memory (settings) | Change-password API ✅ | **IMPLEMENT** |
| Retrieval (settings) | ❌ No settings API | **DEFER** |
| Retention (settings) | ❌ No settings API | **DEFER** |
| Policies | Policy API ✅ | **IMPLEMENT** |
| Redaction | ❌ No API | **DEFER** |
| Appearance | Frontend-only | **C — IMPLEMENT** |
| Developer | ❌ No API | **DEFER** |
| Profile | Change-password API ✅ | **IMPLEMENT** |
