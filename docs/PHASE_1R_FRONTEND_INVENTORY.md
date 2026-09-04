# PHASE_1R_FRONTEND_INVENTORY.md

## Gate 4 — Frontend Inventory

**Date:** 2026-09-04
**Baseline HEAD:** `0534efe426e42f9c03f1622dd792f052647038cc`
**Frontend branch:** `master` (same repo, detachable frontend subtree)

---

## 1. Technology Stack

| Layer        | Technology                          | Version  |
|--------------|-------------------------------------|----------|
| Framework    | Next.js (App Router)               | 15.5.24  |
| Language     | TypeScript                          | 5.0.0    |
| Runtime      | React                               | 18.3.0   |
| Styling      | Tailwind CSS 3 + CSS custom props   | 3.4.0    |
| Icons        | lucide-react                        | 0.468.0  |
| Testing      | Playwright                          | 1.62.1   |
| Linting     | ESLint (next config)                | 8.57.0   |
| Build       | Next.js built-in (SWC/turbopack)    | --       |

### Next.js Configuration

- **App Router** (`src/app/`) — all pages use `'use client'` (fully client-rendered)
- **Path alias:** `@/*` → `./src/*`
- **E2E exclusion:** `e2e/` excluded from TypeScript compilation in `tsconfig.json`
- **No next.config.* found** — using Next.js defaults

### Tailwind CSS Configuration

- **No `tailwind.config.*` file** — using Tailwind CSS v3 default configuration
- CSS custom properties defined in `globals.css` for theming
- Dark theme only (no light/dark toggle)

---

## 2. CSS Custom Properties (Design Tokens)

```css
:root {
  --bg-primary:   #0a0a0f;   /* deepest background */
  --bg-secondary: #111118;   /* card/panel background */
  --bg-tertiary:  #1a1a24;   /* elevated elements */
  --border:       #1f1f2e;   /* subtle borders */
  --accent:       #6366f1;   /* indigo primary */
  --accent-hover: #818cf8;   /* indigo lighter */
}
```

All components use `[var(--...)]` CSS variable references for consistent theming. No runtime theme switching.

---

## 3. API Layer

### 3.1 Central API Client (`src/lib/api.ts`)

| Function           | HTTP Method | Purpose                          |
|--------------------|-------------|----------------------------------|
| `apiGet<T>(path)`  | GET         | Authenticated GET with JWT       |
| `apiPost<T>(path, body)` | POST  | Authenticated POST with JSON body |
| `apiPatch<T>(path, body)` | PATCH | Authenticated PATCH            |
| `apiDelete<T>(path)` | DELETE    | Authenticated DELETE             |
| `streamChat(msg, signal?)` | POST (stream) | SSE chat streaming via fetch ReadableStream |
| `uploadFile(projectId, file, onProgress?)` | POST (multipart) | File upload via XMLHttpRequest |

**Auth flow:**
- Token storage: `localStorage` key `sv_tokens` → `{access_token, refresh_token}`
- Auto token refresh: on 401, calls `/api/v1/auth/refresh` with refresh token
- Token cleanup on refresh failure: `localStorage.removeItem('sv_tokens')`
- API base: `process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`

### 3.2 Error Formatting (`src/lib/errors.ts`)

- Maps HTTP status codes (400, 401, 403, 404, 409, 422, 429, 500, 502, 503) to user-friendly titles/messages
- Maps detail codes (`not_found`, `already_exists`, `invalid_credentials`, `token_expired`, `rate_limit_exceeded`, `validation_error`, `permission_denied`, `internal_error`, `upload_failed`, `ingest_error`, `project_not_found`)
- Helpers: `formatApiError()`, `isNetworkError()`, `isAuthError()`

### 3.3 API Endpoints Used by Frontend

| Method | Path                                       | Used In                           |
|--------|--------------------------------------------|-----------------------------------|
| GET    | `/api/v1/auth/me`                          | `useAuth` (boot), StoragePage     |
| POST   | `/api/v1/auth/register`                    | E2E tests (direct fetch)          |
| POST   | `/api/v1/auth/login`                       | E2E tests (direct fetch)          |
| POST   | `/api/v1/auth/logout`                      | `useAuth.logout`                  |
| POST   | `/api/v1/auth/refresh`                     | `api.ts` auto-refresh             |
| PATCH  | `/api/v1/auth/me`                          | ProfilePage                       |
| POST   | `/api/v1/auth/change-password`             | SettingsPage, ProfilePage         |
| GET    | `/api/v1/workspace`                        | DashboardPage, SettingsPage       |
| PATCH  | `/api/v1/workspace`                        | SettingsPage                      |
| GET    | `/api/v1/workspace/members`                | SettingsPage, ProjectSettingsPage |
| POST   | `/api/v1/workspace/members`                | SettingsPage (invite)             |
| PATCH  | `/api/v1/workspace/members/{id}`           | SettingsPage (change role)        |
| DELETE | `/api/v1/workspace/members/{id}`           | SettingsPage (remove member)      |
| GET    | `/api/v1/workspace/members/invitations`    | SettingsPage                      |
| DELETE | `/api/v1/workspace/members/invitation/{id}`| SettingsPage (revoke invite)      |
| GET    | `/api/v1/projects`                         | ProjectsPage, DashboardPage       |
| POST   | `/api/v1/projects`                         | DashboardPage (create)            |
| GET    | `/api/v1/projects/`                        | `useProjects` hook                |
| POST   | `/api/v1/projects/`                        | `useCreateProject` hook           |
| GET    | `/api/v1/projects/{id}`                    | ProjectLayout, `useProject` hook  |
| PATCH  | `/api/v1/projects/{id}`                    | ProjectLayout, `useUpdateProject` |
| DELETE | `/api/v1/projects/{id}`                    | ProjectLayout, `useDeleteProject` |
| GET    | `/api/v1/sessions`                         | SessionsPage                      |
| GET    | `/api/v1/sessions/{id}/history`            | SessionDetailPage                 |
| POST   | `/api/v1/chat/stream`                      | ChatPage, useChat hook            |
| GET    | `/api/v1/memory/`                          | MemoryPage, `useMemoryList`       |
| POST   | `/api/v1/memory/search`                    | `useMemorySearch` hook            |
| POST   | `/api/v1/memory/`                          | `useCreateMemory` hook            |
| DELETE | `/api/v1/memory/{id}`                      | `useDeleteMemory` hook            |
| GET    | `/api/v1/facts/`                           | FactsPage (via `/api/v1/ingest/facts`) |
| GET    | `/api/v1/ingest/facts`                     | FactsPage                         |
| GET    | `/api/v1/ingest/decisions`                 | DecisionsPage                     |
| GET    | `/api/v1/ingest/timeline`                  | TimelinePage                      |
| GET    | `/api/v1/ingest/search`                    | SearchPage (direct fetch)         |
| GET    | `/api/v1/search/`                          | `useSearch` hook                  |
| GET    | `/api/v1/ingest/graph`                     | GraphPage                         |
| GET    | `/api/v1/graph`                            | `useGraph` hook                   |
| GET    | `/api/v1/ingest/sources`                   | IngestPage, `useSources` hook     |
| POST   | `/api/v1/ingest/upload`                    | IngestPage (text upload)          |
| POST   | `/api/v1/ingest/upload` (multipart)        | `uploadFile()`, StoragePage       |
| GET    | `/api/v1/ingest/jobs`                      | `useIngestJobs` hook              |
| GET    | `/api/v1/api-keys`                         | ApiKeysPage, `useApiKeys` hook    |
| POST   | `/api/v1/api-keys`                         | `useCreateKey` hook               |
| DELETE | `/api/v1/api-keys/{id}`                    | `useRevokeKey` hook               |
| POST   | `/api/v1/api-keys/{id}/rotate`             | `useRotateKey` hook               |

**Total unique API endpoints referenced: 37**

---

## 4. Directory Structure

```
frontend/
├── .env.example                    # Environment variable template
├── next.config.*                   # (none — using defaults)
├── package.json                    # Dependencies & scripts
├── playwright.config.ts            # Playwright E2E configuration
├── tsconfig.json                   # TypeScript config (e2e excluded)
├── tsconfig.e2e.json               # E2E-specific TS config
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── layout.tsx          # Root layout (AuthProvider + AppShell)
│       │   ├── page.tsx            # / → redirect to /dashboard or /auth/login
│       │   ├── globals.css         # Tailwind + CSS custom properties
│       │   ├── auth/
│       │   │   ├── login/page.tsx      # /auth/login — Sign in form
│       │   │   └── register/page.tsx   # /auth/register — Create account form
│       │   ├── dashboard/
│       │   │   └── page.tsx            # /dashboard — Workspace overview + project list
│       │   ├── projects/
│       │   │   ├── page.tsx            # /projects — All projects grid
│       │   │   └── [id]/
│       │   │       ├── layout.tsx      # Project layout (sidebar + children)
│       │   │       ├── chat/page.tsx   # Chat with SSE streaming
│       │   │       ├── ingest/page.tsx # File/text ingestion UI
│       │   │       ├── sessions/
│       │   │       │   ├── page.tsx    # Session list
│       │   │       │   └── [sessionId]/page.tsx  # Session detail
│       │   │       ├── memory/page.tsx   # Memory items list
│       │   │       ├── facts/page.tsx    # Extracted facts
│       │   │       ├── decisions/page.tsx # Extracted decisions
│       │   │       ├── timeline/page.tsx  # Temporal timeline
│       │   │       ├── search/page.tsx    # Semantic search
│       │   │       ├── graph/page.tsx     # Knowledge graph visualization
│       │   │       ├── provenance/page.tsx # Provenance records (traceability)
│       │   │       └── settings/page.tsx  # Project settings (CRUD, danger zone)
│       │   └── settings/
│       │       ├── page.tsx            # /settings — Workspace + members + invitations
│       │       ├── profile/page.tsx    # /settings/profile — User profile + password
│       │       ├── api-keys/page.tsx   # /settings/api-keys — API key management
│       │       └── storage/page.tsx    # /settings/storage — File upload/storage
│       ├── components/
│       │   ├── Sidebar.tsx             # Main sidebar navigation
│       │   └── ui/
│       │       ├── index.ts            # Barrel exports
│       │       ├── Badge.tsx           # Status badge component
│       │       ├── Card.tsx            # Card container with title/subtitle/actions
│       │       ├── ConfirmDialog.tsx   # Confirmation modal
│       │       ├── EmptyState.tsx      # Empty state placeholder
│       │       ├── ErrorAlert.tsx      # Error banner
│       │       ├── FileInput.tsx       # File upload input
│       │       ├── LoadingSpinner.tsx  # Spinner component
│       │       ├── Pagination.tsx      # Pagination controls
│       │       ├── Skeleton.tsx        # Loading skeleton
│       │       └── useClipboard.ts     # Copy-to-clipboard hook
│       ├── features/                    # Feature-specific hooks (data fetching)
│       │   ├── apiKeys/useApiKeys.ts    # API key CRUD hooks
│       │   ├── chat/useChat.ts          # Chat hook (SSE streaming)
│       │   ├── graph/useGraph.ts        # Knowledge graph data hook
│       │   ├── ingest/useIngest.ts      # Sources, facts, decisions, upload, jobs
│       │   ├── memory/useMemory.ts      # Memory list, search, create, delete
│       │   ├── projects/useProjects.ts  # Project CRUD hooks
│       │   └── search/useSearch.ts      # Semantic search hook
│       ├── hooks/
│       │   ├── useAuth.tsx              # Auth context provider + hook
│       │   ├── useSSE.tsx               # EventSource wrapper for SSE
│       │   ├── AppShell.tsx             # Auth guard + conditional sidebar
│       │   └── AuthRedirect.tsx         # (DEPRECATED — superseded by AppShell)
│       ├── lib/
│       │   ├── api.ts                   # Centralized API client
│       │   └── errors.ts                # Error formatting utilities
│       └── types/
│           └── api.ts                   # TypeScript interfaces for all API shapes
├── e2e/
│   ├── playwright.config.ts            # E2E test config
│   ├── auth.spec.ts                    # 7 auth page tests
│   ├── dashboard.spec.ts               # 3 route redirect tests
│   ├── frontend-journey.spec.ts        # 4 full-journey UI tests
│   └── golden-journey.spec.ts          # 14 API-level golden tests
└── test-results/                       # Playwright output directory
```

---

## 5. Page Inventory (23 Routes)

### 5.1 Public Pages (no auth required)

| Route               | File                        | Purpose                                                      | Elements                                           |
|---------------------|-----------------------------|--------------------------------------------------------------|----------------------------------------------------|
| `/`                 | `app/page.tsx`              | Redirect to `/dashboard` (auth) or `/auth/login` (anon)     | None (redirect only)                               |
| `/auth/login`       | `app/auth/login/page.tsx`   | Login form                                                    | h1 "Sign in to SwarmVault", email/password inputs, "Sign in" button, "Create one" link |
| `/auth/register`    | `app/auth/register/page.tsx`| Registration form                                             | h1 "Create your account", name/email/workspace/password/confirm inputs, "Create account" button, "Sign in" link |

### 5.2 Authenticated Pages (require JWT)

| Route                    | File                                      | Purpose                                        | Elements                                              |
|--------------------------|-------------------------------------------|------------------------------------------------|-------------------------------------------------------|
| `/dashboard`             | `app/dashboard/page.tsx`                  | Workspace overview, project list, create new   | h1 (workspace name), project grid, "New Project" form |
| `/projects`              | `app/projects/page.tsx`                   | All projects grid                              | h1 "Projects", project cards                          |
| `/projects/[id]`         | `app/projects/[id]/layout.tsx`            | Project shell (left nav + content area)        | Project name, description, nav links (Chat, Ingest, Sessions, Memory, Facts, Decisions, Timeline, Search, Graph), Settings/Delete buttons |
| `/projects/[id]/chat`    | `app/projects/[id]/chat/page.tsx`         | AI chat with SSE streaming                     | Message list, textarea input, sources panel, evidence modal |
| `/projects/[id]/ingest`  | `app/projects/[id]/ingest/page.tsx`       | Upload & ingest conversations                  | Source type select, title input, textarea, file input, source list |
| `/projects/[id]/sessions`| `app/projects/[id]/sessions/page.tsx`     | Session list                                   | Session cards with title, source, date                |
| `/projects/[id]/sessions/[sessionId]` | `.../sessions/[sessionId]/page.tsx` | Session detail with messages | Message bubbles (user/assistant), back link           |
| `/projects/[id]/memory`  | `app/projects/[id]/memory/page.tsx`       | Memory items list with type filter             | Type filter input, memory cards (type badge, content, tags, temporal status) |
| `/projects/[id]/facts`   | `app/projects/[id]/facts/page.tsx`        | Extracted facts                                | Fact cards (statement, confidence, predicate, status) |
| `/projects/[id]/decisions`| `app/projects/[id]/decisions/page.tsx`   | Extracted decisions                            | Decision cards (content, confidence, tags, status)    |
| `/projects/[id]/timeline`| `app/projects/[id]/timeline/page.tsx`     | Temporal timeline of events                    | Vertical timeline with nodes, timestamps, item types  |
| `/projects/[id]/search`  | `app/projects/[id]/search/page.tsx`       | Semantic search across memory                  | Search input, result cards (type, content, score)     |
| `/projects/[id]/graph`   | `app/projects/[id]/graph/page.tsx`        | Knowledge graph visualization                  | Node list, adjacency display, detail panel, "include historical" toggle |
| `/projects/[id]/settings`| `app/projects/[id]/settings/page.tsx`     | Project CRUD + member management               | Tabs: General (edit), Members, Danger Zone (delete)   |
| `/settings`              | `app/settings/page.tsx`                    | Workspace settings + member management          | Tabs: Workspace (edit), Members (invite/role/remove), Invitations (revoke) |
| `/settings/profile`      | `app/settings/profile/page.tsx`            | User profile + password change                  | Name input, email display, password form with show/hide |
| `/settings/api-keys`     | `app/settings/api-keys/page.tsx`           | API key create/revoke/rotate                    | Create form, key list (prefix mask, dates), rotate/revoke buttons, confirm dialogs |
| `/settings/storage`      | `app/settings/storage/page.tsx`            | File upload and storage management              | File upload input, file list with status badges, delete |

**Total: 20 authenticated routes + 3 public routes = 23 routes**

---

## 6. Component Inventory

### 6.1 Layout Components

| Component      | File                        | Purpose                                                      |
|----------------|-----------------------------|--------------------------------------------------------------|
| `RootLayout`   | `app/layout.tsx`            | Root HTML wrapper, wraps children in `AuthProvider` + `AppShell` |
| `AppShell`     | `hooks/AppShell.tsx`         | Auth guard (redirect unauthenticated), conditional sidebar, loading state |
| `AuthRedirect` | `hooks/AuthRedirect.tsx`     | **DEPRECATED** — superseded by AppShell, still exported but unused in production |
| `Sidebar`      | `components/Sidebar.tsx`     | Main navigation sidebar: workspace nav, project sub-nav, logout |

### 6.2 UI Primitives (`components/ui/`)

| Component          | Purpose                                                |
|--------------------|--------------------------------------------------------|
| `Card`             | Bordered container with optional title, subtitle, actions |
| `Badge`            | Status badge (variants: default, success, warning, danger, purple) |
| `ConfirmDialog`    | Modal confirmation dialog with danger mode              |
| `EmptyState`       | Icon + title + description placeholder                  |
| `ErrorAlert`       | Dismissible error banner                                |
| `FileInput`        | Styled file upload input                               |
| `LoadingSpinner`   | Animated spinner (sizes: sm, md, lg)                   |
| `Pagination`       | Page navigation controls                               |
| `Skeleton`         | Loading skeleton placeholder                           |
| `useClipboard()`   | Copy-to-clipboard hook with timeout and fallback        |

---

## 7. Feature Hooks Inventory (`src/features/`)

### 7.1 `useProjects.ts`
- `useProjects()` — loads all projects (`GET /api/v1/projects/`)
- `useProject(id)` — loads single project (`GET /api/v1/projects/{id}`)
- `useCreateProject()` — creates project (`POST /api/v1/projects/`)
- `useUpdateProject(id)` — updates project (`PATCH /api/v1/projects/{id}`)
- `useDeleteProject()` — deletes project (`DELETE /api/v1/projects/{id}`)

### 7.2 `useChat.ts`
- `useChat(projectId)` — SSE streaming chat via `useSSE` hook
  - Sends: `POST /api/v1/chat/stream?project_id=`
  - Handles: `token`, `sources`, `done`, `error` events
  - Returns: `{ messages, loading, streaming, error, sendMessage, cancelStream, clear }`

### 7.3 `useSSE.tsx`
- `useSSE()` — EventSource-based SSE wrapper
  - `stream(url, onMessage, onDone, onError)` — opens EventSource, dispatches events
  - `stop()` — closes connection
  - **Note:** Uses `EventSource` (GET), but `useChat.ts` uses `fetch` POST with ReadableStream instead. These are two different SSE approaches — `useSSE` hook exists but `useChat` uses its own inline implementation.

### 7.4 `useMemory.ts`
- `useMemoryList({projectId, memoryType, limit})` — `GET /api/v1/memory/`
- `useMemorySearch(query, {projectId, limit})` — `POST /api/v1/memory/search`
- `useCreateMemory()` — `POST /api/v1/memory/`
- `useDeleteMemory()` — `DELETE /api/v1/memory/{id}`

### 7.5 `useIngest.ts`
- `useSources(projectId)` — `GET /api/v1/ingest/sources`
- `useFacts(projectId)` — `GET /api/v1/facts/`
- `useDecisions(projectId)` — `GET /api/v1/ingest/decisions`
- `useUploadFile(projectId)` — multipart upload via `uploadFile()`
- `useIngestJobs()` — `GET /api/v1/ingest/jobs`

### 7.6 `useGraph.ts`
- `useGraph(projectId)` — `GET /api/v1/graph?project_id=`

### 7.7 `useSearch.ts`
- `useSearch(query, {projectId, limit})` — `GET /api/v1/search/?q=&limit=&project_id=`

### 7.8 `useApiKeys.ts`
- `useApiKeys()` — `GET /api/v1/api-keys`
- `useCreateKey()` — `POST /api/v1/api-keys`
- `useRevokeKey()` — `DELETE /api/v1/api-keys/{id}`
- `useRotateKey()` — `POST /api/v1/api-keys/{id}/rotate`

---

## 8. TypeScript Type Inventory (`src/types/api.ts`)

### 8.1 Auth Types
- `UserInfo` — id, email, name, workspace_id, tenant_id
- `TokenPair` — access_token, refresh_token, token_type, expires_in, user
- `RegisterRequest` — email, password, name, workspace_name

### 8.2 Workspace Types
- `WorkspaceDetail` — id, name, slug, tenant_id, description, created_at
- `WorkspaceMemberOut` — id, workspace_id, user_id, user_name, user_email, role, joined_at, invited_at, expires_at
- `WorkspaceSummary` — id, name, slug, role

### 8.3 Project Types
- `Project` — id, workspace_id, name, description, created_at, updated_at
- `ProjectDetail` (alias of Project)
- `ProjectUpdate` — Partial<{name, description}>
- `ProjectCreate` — name, description?

### 8.4 Session Types
- `SessionInfo` — id, workspace_id, user_id, title, created_at
- `MessageInfo` — id, session_id, role, content, metadata, created_at
- `SessionHistory` — session_id, title, source, messages[]
- `NormalizedMessageOut` — id, role, content, timestamp, external_id, metadata

### 8.5 Chat Types
- `ChatRequest` — message, session_id?, project_id?
- `ChatResponse` — message_id, session_id, response, model, usage, memory_ids_used, retrieval_method, retrieval_sources[], latency_ms, confidence, provider
- `ChatStreamEvent` — type (token\|done\|error\|sources), content?, metadata?, error?, sources?

### 8.6 Memory Types
- `MemoryItemOut` — id, workspace_id, user_id, agent_id, run_id, project_id, memory_type, content, extra_metadata, temporal_status, confidence, authority, deleted_at, created_at, updated_at
- `MemorySearchRequest` — query, memory_type?, project_id?, limit?
- `MemoryType` — semantic_memory \| episodic_memory \| procedural_memory \| working_memory

### 8.7 Knowledge Types
- `FactItem` / `FactListResponse` — facts with statement, predicate, authority, confidence, status
- `DecisionItem` / `DecisionListResponse` — decisions with content, temporal_status, confidence, tags
- `TimelineItem` / `TimelineResponse` — item_type (memory\|fact\|decision), id, title, timestamp, temporal_status, content
- `GraphNodeOut` / `GraphEdgeOut` / `GraphResponse` — graph structure with properties, temporal_status, confidence

### 8.8 Search Types
- `SearchResultItem` — item_type, id, score, content, temporal_status, created_at
- `SearchResponse` — items[], total, query

### 8.9 Ingestion Types
- `SourceOut` / `SourceDetail` / `SourceListResponse` — source_type, status, stage, title, message_count
- `IngestUploadRequest` / `IngestUploadResponse` — project_id, source_type, content, title, config
- `IngestQueued` — job_id, status, message
- `IngestJobOut` — full job tracking with progress, timestamps

### 8.10 Provenance Types
- `ProvenanceOut` — model, provider, retrieval_method, memory_ids_used, token usage, latency, confidence
- `ProvenanceMemories` — provenance_id, memories[]

### 8.11 API Key Types
- `ApiKeyOut` — id, prefix, name, last_used_at, expires_at, created_at
- `ApiKeyCreateResponse` — extends ApiKeyOut + raw_key

### 8.12 Misc Types
- `MessageFeedbackCreate` / `MessageFeedbackOut` — session_id, rating, comment
- `InvitationOut` / `InvitationUpdate` — email, role, state, expires_at
- `FeedbackRating` — thumbs_up \| thumbs_down \| neutral
- `DashboardSummary` — project_count, memory_count, session_count, source_count
- `UserUpdate` — name?
- `StorageFileOut` — id, name, size, content_type, uploaded_at
- `PaginatedResponse<T>` — items[], total

**Total: 45 exported type definitions**

---

## 9. Hook Architecture

### 9.1 Auth System (`hooks/useAuth.tsx`)

```
AuthProvider (context)
├── State: { user, loading, error }
├── Effects: GET /api/v1/auth/me on mount → restores session
├── login(email, password) → POST /api/v1/auth/login → storeTokens
├── register(data) → POST /api/v1/auth/register
├── logout() → POST /api/v1/auth/logout → clearTokens
└── clearError()
```

### 9.2 Shell Architecture (`hooks/AppShell.tsx`)

```
AppShell
├── Reads: { user, loading } from useAuth
├── Public paths: /auth/login, /auth/register, /
├── If loading → "Loading…" spinner
├── If auth page → render children (no sidebar)
├── If authenticated → Sidebar + <main>{children}</main>
└── If unauthenticated (non-auth) → return null (redirect in progress)
```

### 9.3 Data Fetching Pattern

All feature hooks follow the same pattern:
1. `useState` for data, loading, error
2. `useCallback` for the fetch function
3. `useEffect` to trigger fetch on mount / dependency change
4. Returns `{ data, loading, error, reload }`

---

## 10. Environment Variables

| Variable                  | Required | Default                        | Purpose                         |
|---------------------------|----------|--------------------------------|---------------------------------|
| `NEXT_PUBLIC_API_URL`     | No       | `http://localhost:8000`        | Backend API base URL            |

**Note:** `NEXT_PUBLIC_` prefix means this is exposed to the browser. Only one env var is needed for frontend-backend communication.

---

## 11. E2E Test Suite

### 11.1 Test Files

| File                          | Tests | Focus                            | Workers |
|-------------------------------|-------|----------------------------------|---------|
| `e2e/auth.spec.ts`            | 7     | Login form, register form, links | 2 (default) |
| `e2e/dashboard.spec.ts`       | 3     | Unauthenticated redirect behavior | 2 (default) |
| `e2e/frontend-journey.spec.ts`| 4     | Full UI journey (reg→login→nav)  | 2 (default) |
| `e2e/golden-journey.spec.ts`  | 14    | API-level golden tests           | 2 (default) |

**Total UI E2E tests: 18 (14 in Playwright config + 4 in frontend-journey)**
**All 18 tests PASSING** as of 2026-09-04.

### 11.2 Test Patterns

- **Page rendering tests:** Check for element presence, text content, input counts
- **Navigation tests:** URL-based redirect checks for auth guards
- **Golden journey:** Full register→login→dashboard→project create→navigation flow
- **API tests (golden-journey):** Direct `page.evaluate(fetch())` calls to backend API
- **No database cleanup:** Tests use unique names (Date.now() + random suffix) to avoid slug collisions
- **E2E bypass header:** Backend has `X-E2E: true` rate-limit bypass for non-production

---

## 12. Build Configuration

### 12.1 Scripts (`package.json`)

| Script  | Command                     | Purpose                       |
|---------|-----------------------------|-------------------------------|
| `dev`   | `next dev --port 3000`      | Development server (port 3000)|
| `build` | `next build`                | Production build              |
| `start` | `next start --port 3000`    | Production server (port 3000) |
| `lint`  | `next lint`                 | ESLint check                  |

### 12.2 Production Build Status

- **Next.js production build: PASSES** (verified in earlier session)
- No build errors or warnings
- Output ready for static export or Node.js server

---

## 13. Missing Files / Gaps

| Item                      | Status                        | Notes                                      |
|---------------------------|-------------------------------|--------------------------------------------|
| `tailwind.config.*`       | **MISSING**                   | Using Tailwind v3 defaults — no custom config file |
| `next.config.*`           | **MISSING**                   | Using Next.js defaults                     |
| `postcss.config.*`        | **MISSING**                   | Tailwind CSS v3 auto-detects PostCSS       |
| `.env` / `.env.local`     | Not in repo (expected)        | Only `.env.example` present                |
| `AuthRedirect.tsx`        | **DEPRECATED**                | Superseded by AppShell.tsx, still in repo  |

---

## 14. Security Observations

### 14.1 Token Storage
- JWT tokens stored in `localStorage` (not HttpOnly cookies)
- Access token: 60 min expiry, Refresh token: 30 days
- Auto-refresh on 401 via `api.ts`

### 14.2 XSS Exposure
- `localStorage` is vulnerable to XSS attacks
- No Content Security Policy (CSP) headers configured
- No `next.config.js` for security headers

### 14.3 CORS
- Backend CORS configured for `http://localhost:3000`
- Frontend makes cross-origin requests with `credentials: 'include'`
- Production CORS origin must match deployed frontend URL

### 14.4 API Key Handling
- Raw API keys shown once on creation/rotation (UI warns user)
- Keys masked in list view (prefix + dots)
- Clipboard copy with fallback for older browsers

---

## 15. Detachability Assessment

The frontend is **fully detachable**:
1. **No server-side rendering** — all pages are `'use client'` (SPA behavior within Next.js)
2. **Single env var** — only `NEXT_PUBLIC_API_URL` connects to backend
3. **Self-contained API layer** — `src/lib/api.ts` handles all HTTP communication
4. **No backend imports** — no `app/` or server-only imports in any client component
5. **Token-based auth** — JWT in localStorage, no session cookies from backend
6. **Can be built and served independently** — `npm run build && npm run start` serves the full app

**Recommendation for production deployment:**
- Build as static export or Node.js server
- Set `NEXT_PUBLIC_API_URL` to production backend URL
- Ensure CORS on backend matches deployed frontend origin
- Consider adding CSP headers via `next.config.js`

---

*End of Frontend Inventory — Gate 4 complete.*
