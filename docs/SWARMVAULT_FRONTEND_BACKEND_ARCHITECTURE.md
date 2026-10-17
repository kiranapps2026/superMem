# SwarmVault Frontend ↔ Backend Architecture

**Forensic Reconciliation Phase — Final Synthesis**
**Baseline SHA:** e6f4b1c157afaed052584963b942ea04f9661610
**Date:** 2026-09-10

---

## 1. Frontend Architecture Overview

**Framework:** Next.js 15 (App Router) + React 18 + Tailwind CSS
**Root:** `frontend/src/app/`
**API Client:** `frontend/src/lib/api.ts` — single HTTP client with interceptors
**State Management:** No external state management library (no Redux/Zustand/Jotai). Uses React useState + useEffect + Context.
**Auth Storage:** `localStorage['sv_tokens']` — stores access_token + refresh_token as JSON
**Design System:** SwarmVault design tokens in `globals.css` — CSS custom properties for surfaces, borders, text, semantic colors, authority levels, motion tokens

---

## 2. Route → Component → API → Backend → Database Matrix

### 2.1 Authentication

| Screen | Route | Component | State | API Call | Backend Router | Service | Database |
|--------|-------|-----------|-------|----------|---------------|---------|----------|
| Login | `/login` | `LoginForm` (form) | `{email, password, error, loading}` | `POST /api/v1/auth/login` | `auth.py:80-150` | AuthService | users, refresh_tokens |
| Register | `/register` | `RegisterForm` (form) | `{email, name, password, error, loading}` | `POST /api/v1/auth/register` | `auth.py:1-80` | AuthService | users, refresh_tokens |
| Token refresh | (background) | `api.ts` interceptor | `tokens` in localStorage | `POST /api/v1/auth/refresh` | `auth.py` | AuthService | refresh_tokens |

**Auth flow:**
1. User enters credentials → `LoginForm` submits
2. `api.ts` calls `POST /api/v1/auth/login`
3. Response: `{access_token, refresh_token, user}`
4. Tokens stored in `localStorage['sv_tokens']`
5. Subsequent requests: `Authorization: Bearer <access_token>` header
6. On 401: interceptor attempts refresh via `POST /api/v1/auth/refresh`
7. On refresh failure: redirect to `/login`

---

### 2.2 Dashboard

| Screen | Route | Component | State | API Call | Backend Router | Service | Database |
|--------|-------|-----------|-------|----------|---------------|---------|----------|
| Dashboard | `/` | `DashboardPage` | `{stats, recentActivity, loading}` | `GET /api/v1/dashboard/stats` | `dashboard.py` | DashboardService | Multiple (aggregated) |

**Data returned:** Workspace stats, recent sessions, memory count, fact count, decision count.

---

### 2.3 Workspace

| Screen | Route | Component | State | API Call | Backend Router | Service | Database |
|--------|-------|-----------|-------|----------|---------------|---------|----------|
| Workspace list | `/workspaces` | `WorkspaceList` | `{workspaces, loading}` | `GET /api/v1/workspaces` | `workspaces.py` | WorkspaceService | workspaces |
| Workspace detail | `/workspaces/[id]` | `WorkspaceDetail` | `{workspace, projects, loading}` | `GET /api/v1/workspaces/[id]` | `workspaces.py` | WorkspaceService | workspaces, projects |

**Workspace context:** `X-Workspace-Id` header sent with every API request. Resolved from JWT or explicit header.

---

### 2.4 Projects

| Screen | Route | Component | State | API Call | Backend Router | Service | Database |
|--------|-------|-----------|-------|----------|---------------|---------|----------|
| Project list | `/projects` | `ProjectList` | `{projects, loading}` | `GET /api/v1/projects` | `projects.py` | ProjectService | projects |
| Project detail | `/projects/[id]` | `ProjectPage` | `{project, activeTab, loading}` | `GET /api/v1/projects/[id]` | `projects.py` | ProjectService | projects |
| Create project | Modal on ProjectList | `CreateProjectModal` | `{name, description, error}` | `POST /api/v1/projects` | `projects.py` | ProjectService | projects |

**Project layout:** Tabbed interface with sub-routes:
- `/projects/[id]` → Overview
- `/projects/[id]/chat` → Chat
- `/projects/[id]/sessions` → Sessions
- `/projects/[id]/memory` → Memory
- `/projects/[id]/facts` → Facts
- `/projects/[id]/decisions` → Decisions
- `/projects/[id]/timeline` → Timeline
- `/projects/[id]/graph` → Graph
- `/projects/[id]/provenance` → Provenance
- `/projects/[id]/search` → Search
- `/projects/[id]/ingest` → Ingestion
- `/projects/[id]/storage` → Storage
- `/projects/[id]/api-keys` → API Keys
- `/projects/[id]/settings` → Settings

---

### 2.5 Chat

| Screen | Route | Component | State | API Call | Backend Router | Service | Database |
|--------|-------|-----------|-------|----------|---------------|---------|----------|
| Chat | `/projects/[id]/chat` | `ChatPage` | `{messages, input, loading, streaming}` | `POST /api/v1/chat/stream` (SSE) | `chat.py` | ChatOrchestrator | sessions, normalized_messages, memories, message_provenance |
| SSE events | (stream) | `useSSE` hook | `{tokens, sources, done, error}` | Streaming SSE | `chat.py` | ChatOrchestrator | — |

**Chat flow:**
1. User types message → `ChatPage` submits
2. `POST /api/v1/chat/stream` with SSE response
3. SSE events: `token` (partial response), `sources` (evidence), `done`, `error`
4. Frontend appends tokens to message, shows sources in collapsible panel
5. On `done`: final message persisted, provenance recorded

---

### 2.6 Sessions

| Screen | Route | Component | State | API Call | Backend Router | Service | Database |
|--------|-------|-----------|-------|----------|---------------|---------|----------|
| Session list | `/projects/[id]/sessions` | `SessionList` | `{sessions, loading}` | `GET /api/v1/sessions/?project_id=` | `sessions.py` | SessionService | sessions |
| Session detail | `/projects/[id]/sessions/[session_id]` | `SessionDetail` | `{session, messages, loading}` | `GET /api/v1/sessions/{id}/history` | `sessions.py` | SessionService | normalized_messages |

---

### 2.7 Memory

| Screen | Route | Component | State | API Call | Backend Router | Service | Database |
|--------|-------|-----------|-------|----------|---------------|---------|----------|
| Memory list | `/projects/[id]/memory` | `MemoryList` | `{memories, filter, loading}` | `GET /api/v1/memory/?project_id=&type=` | `memory.py` | MemoryService | memories |
| Create memory | Button on MemoryList | `CreateMemoryModal` | `{content, type, metadata, error}` | `POST /api/v1/memory` | `memory.py` | MemoryService | memories |
| Memory detail | (modal) | `MemoryDetail` | `{memory, provenance}` | `GET /api/v1/memory/{id}` | `memory.py` | MemoryService | memories |
| Delete memory | Button | (inline) | — | `DELETE /api/v1/memory/{id}` | `memory.py` | MemoryService | memories |
| Share memory | Button | (inline) | — | `POST /api/v1/memory/{id}/share` | `memory.py` | MemoryService | memories |

**Memory type badges:**
- semantic → blue
- episodic → green
- procedural → purple
- working → gray

**Temporal status badges:**
- current → green "ACTIVE"
- historical → yellow "SUPERSEDED"
- archived → gray "ARCHIVED"

---

### 2.8 Facts

| Screen | Route | Component | State | API Call | Backend Router | Service | Database |
|--------|-------|-----------|-------|----------|---------------|---------|----------|
| Facts list | `/projects/[id]/facts` | `FactsList` | `{facts, loading}` | `GET /api/v1/ingest/facts?project_id=` | `ingest.py` | IngestService | facts |
| Fact detail | (inline expand) | `FactItem` | `{fact, expanded}` | (included in list) | — | — | — |

**Display:** Triple format `subject → predicate → object` in monospace. Confidence and authority as percentages. Evidence badge: "PROVEN" if source_id exists, else "INGESTED".

---

### 2.9 Decisions

| Screen | Route | Component | State | API Call | Backend Router | Service | Database |
|--------|-------|-----------|-------|----------|---------------|---------|----------|
| Decisions list | `/projects/[id]/decisions` | `DecisionsList` | `{decisions, loading}` | `GET /api/v1/ingest/decisions?project_id=` | `ingest.py` | IngestService | decisions |

**Display:** Context (quoted), confidence badge, temporal status, authority %, superseded indicator.

---

### 2.10 Timeline

| Screen | Route | Component | State | API Call | Backend Router | Service | Database |
|--------|-------|-----------|-------|----------|---------------|---------|----------|
| Timeline | `/projects/[id]/timeline` | `TimelineView` | `{events, loading}` | `GET /api/v1/ingest/timeline?project_id=&limit=100` | `ingest.py` | IngestService | facts, decisions, memories |

**Display:** Vertical timeline with dot markers. Type-specific icons. Each event shows timestamp, type label, temporal badge, title/content.

---

### 2.11 Search

| Screen | Route | Component | State | API Call | Backend Router | Service | Database |
|--------|-------|-----------|-------|----------|---------------|---------|----------|
| Search | `/projects/[id]/search` | `SearchView` | `{query, results, loading, page}` | `POST /api/v1/ingest/search?query=&memory_type=` | `ingest.py` | IngestService | facts, decisions, memories |

**Display:** Results show item_type badge, temporal status, score %, content (3-line clamp). Client-side pagination.

---

### 2.12 Graph

| Screen | Route | Component | State | API Call | Backend Router | Service | Database |
|--------|-------|-----------|-------|----------|---------------|---------|----------|
| Graph | `/projects/[id]/graph` | `GraphView` | `{nodes, edges, selectedNode, loading}` | `GET /api/v1/ingest/graph?project_id=` | `ingest.py` | IngestService | graph_nodes, graph_edges |

**Display:** Two-column layout. Node list (left) + detail panel (right). Node type color mapping. Properties as formatted JSON.

---

### 2.13 Provenance

| Screen | Route | Component | State | API Call | Backend Router | Service | Database |
|--------|-------|-----------|-------|----------|---------------|---------|----------|
| Provenance | `/projects/[id]/provenance` | `ProvenanceView` | `{records, loading}` | `GET /api/v1/provenance/?project_id=` | `provenance.py` | ProvenanceService | message_provenance |

**Display:** Model/provider badge, latency, tokens, retrieval method, confidence, memory source IDs (truncated).

---

### 2.14 Ingestion

| Screen | Route | Component | State | API Call | Backend Router | Service | Database |
|--------|-------|-----------|-------|----------|---------------|---------|----------|
| Ingest | `/projects/[id]/ingest` | `IngestView` | `{sourceType, content, title, uploading, result}` | `POST /ingest/upload` | `ingest.py` | IngestService | sources, normalized_messages, facts, decisions, graph_nodes, graph_edges |

**Flow:**
1. Select source type (text, JSON, JSONL, ChatGPT)
2. Paste content or upload file
3. Submit → `POST /ingest/upload`
4. Show pipeline result: facts extracted, decisions extracted, graph created
5. Navigate to related views (facts, decisions, graph)

---

### 2.15 Storage

| Screen | Route | Component | State | API Call | Backend Router | Service | Database |
|--------|-------|-----------|-------|----------|---------------|---------|----------|
| Storage | `/projects/[id]/storage` | `StorageView` | `{sources, loading}` | `GET /ingest/sources?project_id=` | `ingest.py` | IngestService | sources |

**Display:** List of ingested sources with content hash, status, stage, message count, created date.

---

### 2.16 API Keys

| Screen | Route | Component | State | API Call | Backend Router | Service | Database |
|--------|-------|-----------|-------|----------|---------------|---------|----------|
| API Keys | `/projects/[id]/api-keys` | `ApiKeysView` | `{keys, loading}` | `GET /api/v1/api-keys`, `POST /api/v1/api-keys`, `DELETE /api/v1/api-keys/{id}` | `api_keys.py` | APIKeyService | api_keys |

---

### 2.17 Settings

| Screen | Route | Component | State | API Call | Backend Router | Service | Database |
|--------|-------|-----------|-------|----------|---------------|---------|----------|
| Settings | `/projects/[id]/settings` | `SettingsView` | `{project, saving}` | `PATCH /api/v1/projects/[id]` | `projects.py` | ProjectService | projects |

---

## 3. Frontend/Backend Contract Analysis

### 3.1 API Client Architecture

**File:** `frontend/src/lib/api.ts`

```
Architecture:
  • Single fetch-based client
  • Base URL from NEXT_PUBLIC_API_URL env var
  • Interceptors:
    - Request: adds Authorization header (Bearer token from localStorage)
    - Request: adds X-Workspace-Id header (from state/context)
    - Response: on 401 → attempt refresh token
    - Response: on 403/404/500 → error handling
  • No request deduplication
  • No offline support
  • No retry logic
  • SSE: uses EventSource API for streaming
```

### 3.2 Frontend/Backend Mismatches

| # | Frontend Expectation | Backend Behavior | Mismatch | Severity |
|---|---------------------|-----------------|----------|---------|
| M1 | `GET /api/v1/memory/` accepts `project_id` filter | MemoryService.list() does NOT filter by project_id | Frontend sends project_id, backend ignores it | MEDIUM |
| M2 | `MemoryUpdate` schema allows `memory_type` update | MemoryService.update() ignores memory_type | Client thinks it can update type | LOW |
| M3 | Memory type filter works | Memory type column has 4 inconsistent defaults | Filter may return nothing | MEDIUM |
| M4 | SSE provides `done` event | SSE handler expects `done` event | Consistent — no mismatch | None |
| M5 | Search returns scored results | M5 returns multi-factor scores | Consistent | None |
| M6 | Chat shows source evidence | MessageProvenance provides source chain | Consistent | None |
| M7 | Token in localStorage | JWT validation on every request | Works but localStorage has XSS risk | MEDIUM |
| M8 | project_id scopes all data | Workspace isolation is primary, project is secondary | Consistent | None |

---

## 4. Frontend Security Architecture

| Control | Implementation | Location | Risk |
|---------|---------------|----------|------|
| Token storage | localStorage | `api.ts` — `localStorage['sv_tokens']` | XSS vulnerability — tokens accessible to JS |
| Auth headers | Bearer token in Authorization header | `api.ts` interceptor | Standard — safe if HTTPS |
| CORS | Backend CORSMiddleware | `main.py` | Backend-enforced |
| Input validation | React controlled inputs + Pydantic backend | Components + schemas | Double validation — safe |
| XSS prevention | React escapes all render output | Component JSX | Safe — React auto-escapes |
| CSRF | None (token-based auth, no cookies) | N/A | Not applicable — JWT in header, not cookie |
| Content Security Policy | **NOT CONFIGURED** | `next.config.js` | No script/style restrictions — relies on React escaping only |

---

## 5. Frontend State Management

**No external state management library.** Uses:
- `useState` for local component state
- `useEffect` for data fetching
- React Context for auth/workspace context
- `localStorage` for token persistence
- URL params for routing state

**State flow:**
1. Auth state: derived from `localStorage['sv_tokens']` + Context
2. Workspace state: from JWT claims + Context
3. Project state: from URL params (`[id]`)
4. UI state: local `useState` in each component

---

## 6. Frontend Component Architecture

```
src/app/
  layout.tsx              — Root layout (sidebar, header, auth provider)
  page.tsx                — Landing/redirect
  login/
    page.tsx              — Login form
  register/
    page.tsx              — Register form
  workspaces/
    page.tsx              — Workspace list
    [id]/
      page.tsx            — Workspace detail + project list
  projects/
    [id]/
      page.tsx            — Project shell (tabs)
      chat/
        page.tsx          — Chat with SSE streaming
      sessions/
        page.tsx          — Session list
        [sessionId]/
          page.tsx        — Session detail + message history
      memory/
        page.tsx          — Memory list + create
      facts/
        page.tsx          — Fact list
      decisions/
        page.tsx        — Decision list
      timeline/
        page.tsx          — Timeline view
      graph/
        page.tsx          — Graph visualization
      provenance/
        page.tsx          — Provenance records
      search/
        page.tsx          — Search interface
      ingest/
        page.tsx          — Upload/ingest interface
      storage/
        page.tsx          — Source storage list
      api-keys/
        page.tsx          — API key management
      settings/
        page.tsx          — Project settings

src/components/
  ui/                     — Reusable UI primitives (buttons, cards, badges, etc.)
  Sidebar.tsx             — Navigation sidebar
  Header.tsx              — Top header bar
  Pagination.tsx          — Pagination component
  Collapsible.tsx         — Collapsible sections
  ProviderBadge.tsx       — LLM provider badges
  MemoryTypeBadge.tsx     — Memory type badges

src/lib/
  api.ts                  — HTTP client + interceptors
  types.ts                — TypeScript type definitions
  utils.ts                — Utility functions
```

---

## 7. Backend ↔ Frontend Contract Summary

| API Endpoint | Method | Request Schema | Response Schema | Frontend Consumer | Status |
|-------------|--------|---------------|----------------|-------------------|--------|
| `/api/v1/auth/register` | POST | UserCreate | UserResponse | RegisterForm | Consistent |
| `/api/v1/auth/login` | POST | LoginRequest | TokenResponse | LoginForm | Consistent |
| `/api/v1/auth/refresh` | POST | (none) | TokenResponse | api.ts interceptor | Consistent |
| `/api/v1/projects` | GET | — | ProjectList | ProjectList | Consistent |
| `/api/v1/projects` | POST | ProjectCreate | ProjectResponse | CreateProjectModal | Consistent |
| `/api/v1/projects/[id]` | GET | — | ProjectResponse | ProjectPage | Consistent |
| `/api/v1/memory/` | GET | — | MemoryList | MemoryList | Consistent |
| `/api/v1/memory` | POST | MemoryCreate | MemoryResponse | CreateMemoryModal | Consistent |
| `/api/v1/memory/{id}` | GET | — | MemoryResponse | MemoryDetail | Consistent |
| `/api/v1/memory/{id}` | DELETE | — | — | MemoryList (delete button) | Consistent |
| `/api/v1/memory/{id}/share` | POST | — | MemoryResponse | — (not implemented in UI) | Inconsistent |
| `/api/v1/sessions/` | GET | — | SessionList | SessionList | Consistent |
| `/api/v1/sessions/{id}/history` | GET | — | MessageList | SessionDetail | Consistent |
| `/api/v1/chat/stream` | POST | ChatRequest | SSE stream | ChatPage | Consistent |
| `/api/v1/ingest/facts` | GET | — | FactList | FactsList | Consistent |
| `/api/v1/ingest/decisions` | GET | — | DecisionList | DecisionsList | Consistent |
| `/api/v1/ingest/timeline` | GET | — | TimelineResponse | TimelineView | Consistent |
| `/api/v1/ingest/graph` | GET | — | GraphResponse | GraphView | Consistent |
| `/api/v1/ingest/search` | POST | SearchRequest | SearchResponse | SearchView | Consistent |
| `/api/v1/ingest/upload` | POST | IngestUploadRequest | IngestResponse | IngestView | Consistent |
| `/api/v1/ingest/sources` | GET | — | SourceList | StorageView | Consistent |
| `/api/v1/provenance/` | GET | — | ProvenanceList | ProvenanceView | Consistent |
| `/api/v1/api-keys` | GET | — | APIKeyList | ApiKeysView | Consistent |
| `/api/v1/api-keys` | POST | APIKeyCreate | APIKeyResponse | ApiKeysView | Consistent |
| `/api/v1/api-keys/{id}` | DELETE | — | — | ApiKeysView | Consistent |
| `/api/v1/dashboard/stats` | GET | — | DashboardStats | DashboardPage | Consistent |
| `/health` | GET | — | HealthResponse | — (not called by frontend) | N/A |

---

## 8. Frontend Data Flow Diagrams

### 8.1 Chat Flow

```
User types message
  ↓
ChatPage.handleSubmit()
  ↓
api.ts.post('/api/v1/chat/stream', {message, session_id, project_id})
  ↓
Backend: ChatOrchestrator.process_chat()
  ↓  SSE stream
useSSE hook receives events:
  • token → append to message display
  • sources → show in collapsible panel
  • done → finalize message, update history
  • error → show error, enable retry
  ↓
Message persisted in session history
  ↓
Provenance record created
```

### 8.2 Ingestion Flow

```
User selects source type + pastes content
  ↓
IngestView.handleSubmit()
  ↓
api.ts.post('/ingest/upload', {source_type, content, title, project_id})
  ↓
Backend: IngestAPI.upload_source()
  ↓
Pipeline: M0 → M1 → M2 → M3 → M4 → M5
  ↓
Response: {source_id, facts_count, decisions_count, graph_nodes_count}
  ↓
Frontend: show result, offer navigation to facts/decisions/graph
  ↓
User navigates to /projects/[id]/facts → GET /api/v1/ingest/facts
```

### 8.3 Memory Flow

```
User clicks "Create Memory"
  ↓
CreateMemoryModal opens
  ↓
User enters content, selects type, adds metadata
  ↓
api.ts.post('/api/v1/memory', {content, memory_type, metadata, project_id})
  ↓
Backend: MemoryService.write()
  ↓
Memory record created
  ↓
Response: MemoryResponse with id, content, type, temporal_status
  ↓
Frontend: memory appears in MemoryList
  ↓
Memory list refreshes: GET /api/v1/memory/?project_id=
```

---

## 9. Frontend Architecture Gaps

| # | Gap | Evidence | Impact | Severity |
|---|-----|----------|--------|----------|
| F1 | Token storage in localStorage | `api.ts` — `localStorage['sv_tokens']` | XSS vulnerability — any script can read tokens | HIGH |
| F2 | No CSP configured | `next.config.js` — no CSP headers | No script/style restriction beyond React escaping | MEDIUM |
| F3 | No request deduplication | `api.ts` — each hook calls API independently | Duplicate requests on rapid navigation | LOW |
| F4 | No offline support | No service worker, no IndexedDB | App unusable without network | LOW |
| F5 | No retry logic | `api.ts` — single attempt per request | Transient failures cause errors | LOW |
| F6 | Client-side pagination on search | `search/page.tsx` — slices results array | All results loaded, pagination is cosmetic | LOW |
| F7 | No loading skeletons | Some views show spinners, no skeleton states | Perceived performance degradation | LOW |
| F8 | SSE no timeout | `useSSE` hook — no read timeout | Slow clients hold connections open | MEDIUM |
| F9 | Token refresh race condition | Multiple 401s → multiple refresh requests | Possible token invalidation | LOW |

---

*End of Document: SWARMVAULT_FRONTEND_BACKEND_ARCHITECTURE.md*
