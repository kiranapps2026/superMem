# SwarmVault Frontend API Consumption Matrix

**Generated:** 2026-09-05  
**Frontend source tree:** `C:/Users/Administrator/Documents/SwarmVaultwebapp/frontend/`  
**Backend source tree:** `C:/Users/Administrator/Documents/SwarmVaultwebapp/app/`

---

## Table of Contents

1. [API Utility Layer](#1-api-utility-layer)
2. [Authentication Flow](#2-authentication-flow)
3. [Page-Level API Calls](#3-page-level-api-calls)
4. [Feature Hook API Calls](#4-feature-hook-api-calls)
5. [Complete Call Inventory](#5-complete-call-inventory)
6. [URL/Route Correctness Assessment](#6-urlroute-correctness-assessment)
7. [Request Body Schema Assessment](#7-request-body-schema-assessment)
8. [Response Handling Assessment](#8-response-handling-assessment)
9. [Gap Analysis: Backend Endpoints Not Used](#9-gap-analysis-backend-endpoints-not-used)
10. [Error Handling Analysis](#10-error-handling-analysis)
11. [Authentication & Token Management](#11-authentication--token-management)
12. [Summary Statistics](#12-summary-statistics)

---

## 1. API Utility Layer

### 1.1 `frontend/src/lib/api.ts` — Central HTTP Client

**File:** `C:/Users/Administrator/Documents/SwarmVaultwebapp/frontend/src/lib/api.ts`

This is the single source of truth for HTTP. All pages and hooks should import from here.

| Function | Method | Auth | Notes |
|----------|--------|------|-------|
| `getToken()` | — | — | Reads `sv_tokens` from localStorage, returns `access_token` |
| `refreshAccessToken()` | POST `/api/v1/auth/refresh` | No (uses refresh token in body) | Auto-triggered on 401; replaces `access_token` and `refresh_token` in localStorage |
| `clearTokens()` | — | — | Removes `sv_tokens` from localStorage |
| `storeTokens(tokens)` | — | — | Saves `{ access_token, refresh_token }` to localStorage |
| `request<T>(path, options)` | Varies | Bearer token auto-injected | Core wrapper: adds auth header, auto-refreshes on 401, parses errors |
| `apiGet<T>(path)` | GET | Yes | Thin wrapper around `request` |
| `apiPost<T>(path, body)` | POST | Yes | JSON-serializes body |
| `apiPatch<T>(path, body)` | PATCH | Yes | JSON-serializes body |
| `apiDelete<T>(path)` | DELETE | Yes | |
| `streamChat(message, signal)` | POST `/api/v1/chat/stream` | Bearer token inline | SSE generator; yields tokens, handles `done`/`error` events |
| `uploadFile(projectId, file, onProgress)` | POST `/api/v1/ingest/upload` | Bearer token inline | XHR with progress events; multipart/form-data |

**Key behaviors of `request()`:**
- Injects `Authorization: Bearer <token>` header
- Adds `credentials: 'include'` (cookies)
- On 401: attempts token refresh, retries once; clears tokens on failure
- On error: parses `detail`/`message` from JSON error responses
- Returns `undefined` for 204 responses

---

## 2. Authentication Flow

### 2.1 `frontend/src/hooks/useAuth.tsx`

| # | Method | URL | Body | When |
|---|--------|-----|------|-------|
| A1 | GET | `/api/v1/auth/me` | — | On mount (AuthProvider `useEffect`) |
| A2 | POST | `/api/v1/auth/login` | `{ email, password }` | User submits login form |
| A3 | POST | `/api/v1/auth/register` | `{ email, password, name, workspace_name }` | User submits register form |
| A4 | POST | `/api/v1/auth/logout` | `{ refresh_token }` | User clicks logout (fire-and-forget) |

**Token flow:**
1. Login/Register returns `TokenPair` (`access_token`, `refresh_token`, `token_type`, `expires_in`, `user`)
2. Stored in `localStorage` key `sv_tokens` as JSON
3. Every API request via `request()` reads the token and injects `Authorization: Bearer <token>`
4. On 401, `refreshAccessToken()` calls POST `/api/v1/auth/refresh` with `{ refresh_token }`, stores new tokens, retries original request
5. On logout, calls `/api/v1/auth/logout` (ignores errors), then `clearTokens()`

**Assessment:** Token management is correct. The refresh flow handles the full cycle (401 → refresh → retry → clear on double failure).

---

## 3. Page-Level API Calls

### 3.1 `frontend/src/app/dashboard/page.tsx`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| D1 | GET | `/api/v1/workspace` | — | 21 |
| D2 | GET | `/api/v1/projects` | — | 21 |
| D3 | POST | `/api/v1/projects` | `{ name, description }` | 29 |

**Assessment:**
- D1, D2: Parallel `Promise.all` on mount when `user` is set. Correct URLs.
- D3: **MINOR ISSUE** — URL is `/api/v1/projects` (no trailing slash). The backend defines the route as `/projects/` (with slash via router prefix). FastAPI redirects `/projects` → `/projects/` by default, so this works in practice, but the canonical path should be `/api/v1/projects/`.
- Error handling: `alert()` for create; `.finally()` for loading state.

### 3.2 `frontend/src/app/projects/page.tsx`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| P1 | GET | `/api/v1/projects` | — | 16 |

**Assessment:** Same trailing-slash issue as D2. Otherwise correct.

### 3.3 `frontend/src/app/projects/[id]/layout.tsx` (Project Layout)

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| L1 | GET | `/api/v1/projects/${projectId}` | — | 23 |
| L2 | PATCH | `/api/v1/projects/${projectId}` | `{ name?, description? }` | 35 |
| L3 | DELETE | `/api/v1/projects/${projectId}` | — | 45 |

**Assessment:** All correct. L2 only sends changed fields. L3 redirects to `/projects` on success.

### 3.4 `frontend/src/app/projects/[id]/chat/page.tsx`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| C1 | POST | `/api/v1/chat/stream` | `{ message }` | 46 |

**Assessment:** Uses raw `fetch()` (NOT the `api.ts` helpers). Correctly sends POST with JSON body and Bearer token. Handles SSE inline by reading `res.body.getReader()`.  
**ISSUE:** Does NOT send `project_id` in the request body. The backend `ChatRequest` schema accepts `project_id?: string | null` — it is optional, so the call works, but project-specific memory grounding is lost.  
**ISSUE:** No 401 token refresh — if the token expires during chat, the user gets a raw error with no recovery.  
**ISSUE:** Error handling in SSE parsing has an empty `catch {}` block (line 137) that silently swallows JSON parse errors.

### 3.5 `frontend/src/app/projects/[id]/ingest/page.tsx`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| I1 | GET | `/api/v1/ingest/sources?project_id=...&limit=50` | — | 31 |
| I2 | POST | `/api/v1/ingest/upload` | `{ project_id, source_type, content, title? }` | 56 |
| I3 | POST | `/api/v1/ingest/upload` (multipart) | FormData: `project_id`, `source_type`, `file` | via `uploadFile()` → line 165 of api.ts |

**Assessment:**
- I1: Correct URL, correct query params. Note: uses `any[]` for response type instead of `SourceListResponse`.
- I2: Correct body shape for the JSON-based ingest endpoint.
- I3: Correct multipart upload. The `source_type` is auto-detected from file extension (`.json` → `chatgpt`, `.jsonl` → `jsonl`, else `text`).

### 3.6 `frontend/src/app/projects/[id]/sessions/page.tsx`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| S1 | GET | `/api/v1/sessions` | — | 25 |

**Assessment:** Correct. Returns list of sessions for current user. The UI expects `SessionListItem` with `extra_metadata` field — the backend `SessionOut` schema includes this. However, the type is local to this file, not imported from `types/api.ts`.

### 3.7 `frontend/src/app/projects/[id]/sessions/[sessionId]/page.tsx`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| S2 | GET | `/api/v1/sessions/${sessionId}/history` | — | 26 |

**Assessment:** Correct URL and method. The response shape matches the backend's ad-hoc dict return (with `session_id`, `title`, `source`, `messages`).

### 3.8 `frontend/src/app/projects/[id]/memory/page.tsx`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| M1 | GET | `/api/v1/memory/?limit=50&offset=...&project_id=...` | — | 21-28 |
| M1b | GET | (same + `&memory_type=...`) | — | 23 |

**Assessment:** Correct URL, correct query params. Response shape matches `MemoryItemOut` from `types/api.ts`.

### 3.9 `frontend/src/app/projects/[id]/facts/page.tsx`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| F1 | GET | `/api/v1/ingest/facts?project_id=...` | — | 28 |

**Assessment:**
- URL is correct.
- **SCHEMA ISSUE:** This page defines its own local `FactItem` interface with fields `statement`, `predicate` (string), `authority` (string), `status` (string), `confidence` (number). The backend `FactOut` schema (from `types/api.ts`) has different fields: `content` (not `statement`), no `predicate` field, `temporal_status` (not `status`), `confidence` (number), `authority` (number). The frontend will silently fail to display data correctly because the field names don't match.
- Specifically:
  - Backend returns `content`; frontend reads `f.statement` → will be `undefined`
  - Backend returns `temporal_status`; frontend reads `f.status` → will be `undefined`
  - Backend returns `authority: float`; frontend expects `f.authority: string` → will display a number as text

### 3.10 `frontend/src/app/projects/[id]/decisions/page.tsx`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| Dc1 | GET | `/api/v1/ingest/decisions?project_id=...` | — | 28 |

**Assessment:**
- URL is correct.
- The local `DecisionItem` interface has `content`, `temporal_status`, `confidence`, `tags`, `created_at`, `updated_at` — this matches the backend `DecisionItem` from `types/api.ts`. **Correct.**

### 3.11 `frontend/src/app/projects/[id]/timeline/page.tsx`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| T1 | GET | `/api/v1/ingest/timeline?project_id=...&limit=100` | — | 27 |

**Assessment:** Correct URL and params. Response shape matches `TimelineResponse` from `types/api.ts`.

### 3.12 `frontend/src/app/projects/[id]/search/page.tsx`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| Sr1 | GET | `/api/v1/ingest/search?query=...&limit=20&project_id=...` | — | 34-36 |

**Assessment:**
- **ROUTING BUG:** The URL is `/api/v1/ingest/search` which IS the correct backend path.
- **METHOD BUG:** Uses GET method, but the backend defines this as `POST /ingest/search`. The `query` parameter is sent as a query string, but the backend expects it as a `Query(...)` parameter. Actually, looking more carefully, the backend does accept `query` as a query parameter (`query: str = Query(..., min_length=1)`), so GET should work IF the endpoint accepted GET. But the route is only registered for POST. **This will return 405 Method Not Allowed.**
- **Note:** The `useSearch.ts` hook has the same issue but with a DIFFERENT wrong path: it calls `/api/v1/search/` (missing the `ingest` prefix).

### 3.13 `frontend/src/app/projects/[id]/graph/page.tsx`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| G1 | GET | `/api/v1/ingest/graph?project_id=...&include_historical=...` | — | 42 |

**Assessment:** URL is correct. This page does NOT use the `useGraph` hook — it calls the API directly.

### 3.14 `frontend/src/app/projects/[id]/provenance/page.tsx`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| Pv1 | GET | `/api/v1/provenance/?project_id=...` | — | 21 |

**Assessment:** Correct URL. Note: the `?` before `project_id` is unnecessary (there are no path segments after `/provenance/`), but harmless.

### 3.15 `frontend/src/app/settings/page.tsx`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| St1 | GET | `/api/v1/workspace` | — | 44 |
| St2 | GET | `/api/v1/workspace/members` | — | 45 |
| St3 | GET | `/api/v1/workspace/members/invitations` | — | 61 |
| St4 | PATCH | `/api/v1/workspace` | `{ name, description }` | 76 |
| St5 | POST | `/api/v1/workspace/members` | `{ email, role }` | 90 |
| St6 | PATCH | `/api/v1/workspace/members/{memberId}` | `{ role }` | 102 |
| St7 | DELETE | `/api/v1/workspace/members/{memberId}` | — | 114 |
| St8 | DELETE | `/api/v1/workspace/members/invitation/{id}` | — | 125 |
| St9 | POST | `/api/v1/auth/change-password` | `{ current_password, new_password }` | 195 |

**Assessment:** All URLs correct. St5 sends `{ email, role }` which matches `WorkspaceMemberInvite` schema. The backend also accepts `invitation_expires` and `message` as optional fields.

### 3.16 `frontend/src/app/settings/profile/page.tsx`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| Pr1 | PATCH | `/api/v1/auth/me` | `{ name }` | 34 |
| Pr2 | POST | `/api/v1/auth/change-password` | `{ current_password, new_password }` | 45 |

**Assessment:** Correct.

### 3.17 `frontend/src/app/settings/api-keys/page.tsx`

Uses hooks from `useApiKeys.ts` (see section 4.5).

### 3.18 `frontend/src/app/settings/storage/page.tsx`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| Stor1 | GET | `/api/v1/auth/me` | — | 34 |
| Stor2 | POST | `/api/v1/ingest/upload` (multipart) | FormData via `uploadFile()` | 61 |

**Assessment:**
- Stor1: **LOGIC BUG** — Fetches `/api/v1/auth/me` to get `workspace_id`, then stores it in `projectId` state. The variable is named `projectId` but holds a workspace ID. This is then passed to `uploadFile()` as `projectId`, which sends it as the `project_id` form field. The backend's ingest/upload endpoint expects a real project UUID, not a workspace UUID. Uploads will fail with "Project not found" (404).

### 3.19 `frontend/src/app/settings/members/page.tsx` and `project/page.tsx`

These don't exist as separate files. The settings page (`settings/page.tsx`) handles workspace members, and `projects/[id]/settings/page.tsx` handles project-level settings.

### 3.20 `frontend/src/app/projects/[id]/settings/page.tsx`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| Ps1 | GET | `/api/v1/workspace/members` | — | 45 |
| (others) | — | via hooks `useProject`, `useUpdateProject`, `useDeleteProject` | — | — |

Uses the hooks from `useProjects.ts` (L1, L2, L3 above).

---

## 4. Feature Hook API Calls

### 4.1 `frontend/src/features/chat/useChat.ts`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| Ch1 | SSE (EventSource GET) | `/api/v1/chat/stream?project_id=...` | — | 42-43 |

**CRITICAL ISSUE:** This hook uses `useSSE` which creates an `EventSource`. EventSource only supports GET requests and **cannot send a request body**. The backend `/api/v1/chat/stream` endpoint is a `POST` that expects `{ message }` in the JSON body. This means:
1. The request method will be GET (not POST) → 405 error
2. The `message` content is never sent to the backend
3. The `project_id` is sent as a query parameter, which the backend doesn't read (it reads `data.project_id` from the POST body)

**However**, this hook does NOT appear to be used by any page component. The `chat/page.tsx` has its own inline SSE implementation that correctly uses `fetch()` POST. The `useChat` hook is exported but appears to be dead code or planned for future use.

### 4.2 `frontend/src/features/projects/useProjects.ts`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| Prj1 | GET | `/api/v1/projects/` | — | 16 |
| Prj2 | GET | `/api/v1/projects/${id}` | — | 40 |
| Prj3 | POST | `/api/v1/projects/` | `{ name, description }` | 62 |
| Prj4 | PATCH | `/api/v1/projects/${id}` | `{ name?, description? }` | 83 |
| Prj5 | DELETE | `/api/v1/projects/${id}` | — | 104 |

**Assessment:** All correct (note the trailing slashes — this hook uses them correctly).

### 4.3 `frontend/src/features/memory/useMemory.ts`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| Mem1 | GET | `/api/v1/memory/?limit=...&offset=...&project_id=...` | — | 28 |
| Mem2 | POST | `/api/v1/memory/search` | `{ query, limit, project_id }` | 53 |
| Mem3 | POST | `/api/v1/memory/` | `{ project_id, memory_type, content, confidence?, extra_metadata? }` | 81 |
| Mem4 | DELETE | `/api/v1/memory/${id}` | — | 102 |

**Assessment:** All correct.

### 4.4 `frontend/src/features/search/useSearch.ts`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| Srch1 | GET | `/api/v1/search/?q=...&limit=...&project_id=...` | — | 19 |

**ROUTING BUG:** The path is `/api/v1/search/` — this does NOT exist on the backend. The correct path is `/api/v1/ingest/search`. This hook will get 404 errors.  
**METHOD BUG:** Uses GET method. The backend endpoint is POST-only.

### 4.5 `frontend/src/features/graph/useGraph.ts`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| Gr1 | GET | `/api/v1/graph?project_id=...` | — | 16 |

**ROUTING BUG:** The path is `/api/v1/graph` — this does NOT exist. The correct path is `/api/v1/ingest/graph`. This hook will get 404 errors.

### 4.6 `frontend/src/features/ingest/useIngest.ts`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| Ing1 | GET | `/api/v1/ingest/sources?project_id=...` | — | 17 |
| Ing2 | GET | `/api/v1/ingest/facts?project_id=...` | — | 42 |
| Ing3 | GET | `/api/v1/ingest/decisions?project_id=...` | — | 67 |
| Ing4 | GET | `/api/v1/ingest/jobs` | — | 125 |

**Assessment:** All correct.

### 4.7 `frontend/src/features/apiKeys/useApiKeys.ts`

| # | Method | URL | Body | Line |
|---|--------|-----|------|------|
| AK1 | GET | `/api/v1/api-keys` | — | 25 |
| AK2 | POST | `/api/v1/api-keys` | `{ name }` | 49 |
| AK3 | DELETE | `/api/v1/api-keys/${id}` | — | 73 |
| AK4 | POST | `/api/v1/api-keys/${id}/rotate` | `{}` | 96 |

**Assessment:**
- AK1, AK3: Correct.
- AK2: Sends `{ name }`. The backend `ApiKeyCreate` schema also accepts `description`, `expires_at`, `metadata` — these are optional so the minimal body is fine.
- AK4: Sends `{}` (empty body). The backend `rotate_api_key` endpoint accepts no body parameters. Correct.

---

## 5. Complete Call Inventory

| # | File | Line | Method | URL | Body | Correct? |
|---|------|------|--------|-----|------|----------|
| 1 | `lib/api.ts` | 17 | POST | `/api/v1/auth/refresh` | `{ refresh_token }` | YES |
| 2 | `hooks/useAuth.tsx` | 26 | GET | `/api/v1/auth/me` | — | YES |
| 3 | `hooks/useAuth.tsx` | 34 | POST | `/api/v1/auth/login` | `{ email, password }` | YES |
| 4 | `hooks/useAuth.tsx` | 41 | POST | `/api/v1/auth/register` | `{ email, password, name, workspace_name }` | YES |
| 5 | `hooks/useAuth.tsx` | 46 | POST | `/api/v1/auth/logout` | `{ refresh_token }` | YES |
| 6 | `app/dashboard/page.tsx` | 21 | GET | `/api/v1/workspace` | — | YES |
| 7 | `app/dashboard/page.tsx` | 21 | GET | `/api/v1/projects` | — | TRAILING SLASH |
| 8 | `app/dashboard/page.tsx` | 29 | POST | `/api/v1/projects` | `{ name, description }` | TRAILING SLASH |
| 9 | `app/projects/page.tsx` | 16 | GET | `/api/v1/projects` | — | TRAILING SLASH |
| 10 | `projects/[id]/layout.tsx` | 23 | GET | `/api/v1/projects/${id}` | — | YES |
| 11 | `projects/[id]/layout.tsx` | 35 | PATCH | `/api/v1/projects/${id}` | `{ name?, description? }` | YES |
| 12 | `projects/[id]/layout.tsx` | 45 | DELETE | `/api/v1/projects/${id}` | — | YES |
| 13 | `projects/[id]/chat/page.tsx` | 46 | POST | `/api/v1/chat/stream` | `{ message }` | YES (missing project_id) |
| 14 | `features/chat/useChat.ts` | 42 | SSE GET | `/api/v1/chat/stream?project_id=...` | — | **BROKEN** (EventSource can't POST body) |
| 15 | `projects/[id]/ingest/page.tsx` | 31 | GET | `/api/v1/ingest/sources?project_id=...` | — | YES |
| 16 | `projects/[id]/ingest/page.tsx` | 56 | POST | `/api/v1/ingest/upload` | `{ project_id, source_type, content, title? }` | YES |
| 17 | `lib/api.ts` | 165 | POST | `/api/v1/ingest/upload` | multipart FormData | YES |
| 18 | `projects/[id]/sessions/page.tsx` | 25 | GET | `/api/v1/sessions` | — | YES |
| 19 | `projects/[id]/sessions/[sessionId]/page.tsx` | 26 | GET | `/api/v1/sessions/${id}/history` | — | YES |
| 20 | `projects/[id]/memory/page.tsx` | 21-28 | GET | `/api/v1/memory/?limit=50&offset=...&project_id=...` | — | YES |
| 21 | `features/memory/useMemory.ts` | 28 | GET | `/api/v1/memory/?limit=...&offset=...&project_id=...` | — | YES |
| 22 | `features/memory/useMemory.ts` | 53 | POST | `/api/v1/memory/search` | `{ query, limit, project_id }` | YES |
| 23 | `features/memory/useMemory.ts` | 81 | POST | `/api/v1/memory/` | `{ project_id, memory_type, content, confidence?, extra_metadata? }` | YES |
| 24 | `features/memory/useMemory.ts` | 102 | DELETE | `/api/v1/memory/${id}` | — | YES |
| 25 | `projects/[id]/facts/page.tsx` | 28 | GET | `/api/v1/ingest/facts?project_id=...` | — | YES (SCHEMA MISMATCH) |
| 26 | `projects/[id]/decisions/page.tsx` | 28 | GET | `/api/v1/ingest/decisions?project_id=...` | — | YES |
| 27 | `projects/[id]/timeline/page.tsx` | 27 | GET | `/api/v1/ingest/timeline?project_id=...&limit=100` | — | YES |
| 28 | `projects/[id]/search/page.tsx` | 34-36 | **GET** | `/api/v1/ingest/search?query=...&limit=...&project_id=...` | — | **BROKEN** (should be POST) |
| 29 | `features/search/useSearch.ts` | 19 | **GET** | `/api/v1/search/?q=...` | — | **BROKEN** (wrong path + method) |
| 30 | `projects/[id]/graph/page.tsx` | 42 | GET | `/api/v1/ingest/graph?project_id=...&include_historical=...` | — | YES |
| 31 | `features/graph/useGraph.ts` | 16 | GET | `/api/v1/graph?project_id=...` | — | **BROKEN** (wrong path) |
| 32 | `projects/[id]/provenance/page.tsx` | 21 | GET | `/api/v1/provenance/?project_id=...` | — | YES |
| 33 | `settings/profile/page.tsx` | 34 | PATCH | `/api/v1/auth/me` | `{ name }` | YES |
| 34 | `settings/profile/page.tsx` | 45 | POST | `/api/v1/auth/change-password` | `{ current_password, new_password }` | YES |
| 35 | `settings/page.tsx` | 44 | GET | `/api/v1/workspace` | — | YES |
| 36 | `settings/page.tsx` | 45 | GET | `/api/v1/workspace/members` | — | YES |
| 37 | `settings/page.tsx` | 61 | GET | `/api/v1/workspace/members/invitations` | — | YES |
| 38 | `settings/page.tsx` | 76 | PATCH | `/api/v1/workspace` | `{ name, description }` | YES |
| 39 | `settings/page.tsx` | 90 | POST | `/api/v1/workspace/members` | `{ email, role }` | YES |
| 40 | `settings/page.tsx` | 102 | PATCH | `/api/v1/workspace/members/${id}` | `{ role }` | YES |
| 41 | `settings/page.tsx` | 114 | DELETE | `/api/v1/workspace/members/${user_id}` | — | YES |
| 42 | `settings/page.tsx` | 125 | DELETE | `/api/v1/workspace/members/invitation/${id}` | — | YES |
| 43 | `settings/page.tsx` | 195 | POST | `/api/v1/auth/change-password` | `{ current_password, new_password }` | YES |
| 44 | `features/apiKeys/useApiKeys.ts` | 25 | GET | `/api/v1/api-keys` | — | YES |
| 45 | `features/apiKeys/useApiKeys.ts` | 49 | POST | `/api/v1/api-keys` | `{ name }` | YES |
| 46 | `features/apiKeys/useApiKeys.ts` | 73 | DELETE | `/api/v1/api-keys/${id}` | — | YES |
| 47 | `features/apiKeys/useApiKeys.ts` | 96 | POST | `/api/v1/api-keys/${id}/rotate` | `{}` | YES |
| 48 | `settings/storage/page.tsx` | 34 | GET | `/api/v1/auth/me` | — | YES (logic bug — see §3.18) |
| 49 | `lib/api.ts` | 165 | POST | `/api/v1/ingest/upload` | multipart FormData | YES |

---

## 6. URL/Route Correctness Assessment

### 6.1 Correct URLs (35 of 49 unique routes)

Most frontend calls correctly match the backend router definitions. The pattern `/api/v1/<router>/<endpoint>` is consistently used.

### 6.2 Broken URLs (3 routes)

| Frontend Call | Expected Backend | Issue |
|---------------|-----------------|-------|
| `features/search/useSearch.ts:19` — `GET /api/v1/search/` | `POST /api/v1/ingest/search` | **Missing `/ingest` prefix AND wrong method** |
| `features/graph/useGraph.ts:16` — `GET /api/v1/graph` | `GET /api/v1/ingest/graph` | **Missing `/ingest` prefix** |
| `features/chat/useChat.ts:42` — `GET /api/v1/chat/stream` (via EventSource) | `POST /api/v1/chat/stream` | **EventSource can only do GET; backend requires POST** |

### 6.3 Trailing Slash Inconsistencies (cosmetic, FastAPI handles redirect)

| Frontend Call | Canonical Path | Impact |
|---------------|---------------|--------|
| `GET /api/v1/projects` (dashboard, projects page) | `GET /api/v1/projects/` | None — FastAPI redirects |
| `POST /api/v1/projects` (dashboard) | `POST /api/v1/projects/` | None — FastAPI redirects |

### 6.4 Search Page Method Bug

The `search/page.tsx` (line 34-36) and `useSearch.ts` (line 19) both use **GET** for `/api/v1/ingest/search`, but the backend route is `@router.post("/search")`. GET requests to a POST-only endpoint return **405 Method Not Allowed**.

The `golden-journey.spec.ts` E2E test correctly uses POST (line 124):
```
const search = await apiRequest('POST', `/api/v1/ingest/search?query=SwarmVault&limit=20`, token);
```

---

## 7. Request Body Schema Assessment

### 7.1 Login/Register

| Field | Frontend Sends | Backend Expects | Match? |
|-------|---------------|-----------------|--------|
| Register: `email` | string | `UserRegister.email: str` | YES |
| Register: `password` | string | `UserRegister.password: str` | YES |
| Register: `name` | string | `UserRegister.name: str` | YES |
| Register: `workspace_name` | string | `UserRegister.workspace_name: str` | YES |
| Login: `email` | string | `UserLogin.email: str` | YES |
| Login: `password` | string | `UserLogin.password: str` | YES |
| Logout: `refresh_token` | from localStorage | `RefreshRequest.refresh_token: str` | YES |

### 7.2 Projects

| Field | Frontend Sends | Backend Expects | Match? |
|-------|---------------|-----------------|--------|
| Create: `name` | string (required) | `ProjectCreate.name: str` | YES |
| Create: `description` | string (optional) | `ProjectCreate.description?: str` | YES |
| Update: `name?` | string (if changed) | `ProjectUpdate.name?: str` | YES |
| Update: `description?` | string | `ProjectUpdate.description?: str \| None` | YES |

### 7.3 Chat

| Field | Frontend Sends | Backend Expects | Match? |
|-------|---------------|-----------------|--------|
| Stream: `message` | string | `ChatRequest.message: str` | YES |
| Stream: `project_id` | NOT SENT (query param in useChat, absent in chat/page) | `ChatRequest.project_id?: str \| null` | MISSING (optional, so works) |

### 7.4 Ingest/Upload

| Field | Frontend Sends | Backend Expects | Match? |
|-------|---------------|-----------------|--------|
| JSON: `project_id` | string | `IngestUploadRequest.project_id: str` | YES |
| JSON: `source_type` | string | `IngestUploadRequest.source_type: str` | YES |
| JSON: `content` | string | `IngestUploadRequest.content: str` | YES |
| JSON: `title?` | string (optional) | `IngestUploadRequest.title?: str \| None` | YES |
| Multipart: `project_id` | string | Same | YES |
| Multipart: `source_type` | string (auto-detected from ext) | Same | YES |
| Multipart: `file` | File object | Same | YES |

### 7.5 Memory

| Field | Frontend Sends | Backend Expects | Match? |
|-------|---------------|-----------------|--------|
| Create: `project_id` | string | `MemoryCreate.project_id?: str` | YES |
| Create: `memory_type` | string | `MemoryCreate.memory_type: str` | YES |
| Create: `content` | string | `MemoryCreate.content: str` | YES |
| Create: `confidence?` | number | `MemoryCreate.confidence?: float` | YES |
| Create: `extra_metadata?` | Record | `MemoryCreate.extra_metadata?: dict` | YES |
| Search: `query` | string | `MemorySearchRequest.query: str` | YES |
| Search: `limit?` | number | `MemorySearchRequest.limit?: int` | YES |
| Search: `project_id?` | string \| null | `MemorySearchRequest.project_id?: str \| null` | YES |

### 7.6 Workspace/Members

| Field | Frontend Sends | Backend Expects | Match? |
|-------|---------------|-----------------|--------|
| Invite: `email` | string | `WorkspaceMemberInvite.email: str` | YES |
| Invite: `role` | string | `WorkspaceMemberInvite.role: str` | YES |
| Update member: `role` | string | `WorkspaceMemberUpdate.role?: str` | YES |
| Workspace PATCH: `{ name, description }` | dict | `dict` (accepts `name`, `description`, `slug`, `perm_join`, `perm_member_manage`) | YES |

### 7.7 API Keys

| Field | Frontend Sends | Backend Expects | Match? |
|-------|---------------|-----------------|--------|
| Create: `name` | string | `ApiKeyCreate.name: str (min_length=1)` | YES |
| Rotate: body | `{}` (empty) | No body expected | YES |

### 7.8 Schema Mismatches

| Issue | Frontend | Backend | Severity |
|-------|----------|---------|----------|
| Facts page uses `statement` | `FactItem { statement, predicate: string, authority: string, status: string }` | `FactItem { content, temporal_status, confidence: float, authority: float }` | **HIGH** — data won't render |
| Facts page reads `f.status` | Expects string `status` field | Backend returns `temporal_status` | **HIGH** — temporal status badges won't show |
| Facts page reads `f.predicate` | Expects `predicate: string` | Backend has no `predicate` on `FactOut` (it's on the `Fact` model but not in `FactOut`) | **MEDIUM** — will show `undefined` |
| Facts page reads `f.authority` as string | Expects `authority: string` | Backend returns `confidence: number` and `authority: number` | **MEDIUM** — authority badge shows wrong field |

---

## 8. Response Handling Assessment

### 8.1 Correct Response Handling

Most hooks follow the pattern:
```typescript
try {
  const data = await apiGet<Type>(url);
  setItems(data);
} catch (err) {
  setError(err instanceof Error ? err.message : '...');
} finally {
  setLoading(false);
}
```

This correctly handles the `Response` object returned by the `request()` wrapper.

### 8.2 Streaming Response Handling (SSE)

**In `chat/page.tsx` (lines 82-139):** Manual SSE parsing via `reader.read()`. Handles:
- `token` events → appends content
- `sources` events → stores sources array
- `done` events → finalizes message with metadata
- `error` events → displays error in message

**In `useSSE.ts` (lines 20-23):** EventSource-based approach. Handles same events but:
- No auth token support (EventSource doesn't allow custom headers)
- No 401 handling
- Cannot send request body (POST endpoints unreachable)

### 8.3 Streaming via `api.ts` `streamChat()`

The `streamChat` function (lines 87-136 of api.ts) correctly:
- Sends POST with auth header
- Reads streaming response body
- Parses SSE `data:` lines
- Yields `event.content` for `token` events
- Returns on `done` events
- Throws on `error` events

---

## 9. Gap Analysis: Backend Endpoints Not Used

### 9.1 Endpoints the Frontend Completely Ignores

| Backend Endpoint | Purpose | Frontend Status |
|-----------------|---------|-----------------|
| `GET /api/v1/dashboard/` | Workspace-level aggregated overview (counts, recent activity) | **NOT USED** — dashboard page manually fetches workspace + projects |
| `GET /api/v1/dashboard/projects/{id}` | Project-level dashboard | **NOT USED** |
| `POST /api/v1/chat/` | Non-streaming chat (full response at once) | **NOT USED** by UI (E2E tests use it) |
| `POST/GET /api/v1/feedback/` | Thumbs up/down on chat responses | **NOT USED** |
| `GET /api/v1/audit/events` | Audit log listing | **NOT USED** |
| `GET /api/v1/audit/events/{id}` | Single audit event | **NOT USED** |
| `GET /api/v1/audit/trace/{request_id}` | Correlation trace | **NOT USED** |
| `GET /api/v1/policy/` | List policies | **NOT USED** |
| `POST /api/v1/policy/` | Create policy | **NOT USED** |
| `GET /api/v1/policy/{id}` | Get policy with versions | **NOT USED** |
| `PATCH /api/v1/policy/{id}` | Update policy | **NOT USED** |
| `DELETE /api/v1/policy/{id}` | Delete policy | **NOT USED** |
| `POST /api/v1/policy/{id}/versions` | New policy version | **NOT USED** |
| `POST /api/v1/policy/test-authorization` | Test authorization | **NOT USED** |
| `GET /api/v1/storage/{key:path}` | Get file presigned URL | **NOT USED** |
| `DELETE /api/v1/storage/{key:path}` | Delete file | **NOT USED** |
| `GET /api/v1/workspace/workspaces/all` | List all user workspaces | **NOT USED** |
| `GET /api/v1/workspace/workspaces/available` | List joinable workspaces | **NOT USED** |
| `POST /api/v1/member/leave` | Leave workspace | **NOT USED** |
| `POST /api/v1/sessions/` | Create session | **NOT USED** |
| `GET /api/v1/sessions/{id}` | Get single session | **NOT USED** |
| `POST /api/v1/sessions/{id}/messages` | Add message to session | **NOT USED** |
| `DELETE /api/v1/sessions/{id}` | Delete session | **NOT USED** |
| `GET /api/v1/memory/{id}` | Get single memory | **NOT USED** |
| `PATCH /api/v1/memory/{id}` | Update memory | **NOT USED** |
| `GET /api/v1/ingest/sources/{id}` | Source detail with messages | **NOT USED** |
| `GET /api/v1/ingest/sources/{id}/messages` | Source normalized messages | **NOT USED** |
| `GET /api/v1/ingest/facts/{id}` | Single fact | **NOT USED** |
| `GET /api/v1/ingest/decisions/{id}` | Single decision | **NOT USED** |
| `GET /api/v1/ingest/jobs/{id}` | Single job detail | **NOT USED** |
| `GET /api/v1/provenance/{id}` | Single provenance record | **NOT USED** |
| `GET /api/v1/provenance/{id}/memories` | Provenance memory expansion | **NOT USED** |

### 9.2 Impact

- **High-value missing:** Dashboard overview (`GET /api/v1/dashboard/`) would give the dashboard page a single-call data load instead of two parallel calls.
- **Low-value missing:** Audit, policy, storage file retrieval are admin features not yet exposed in the UI.
- **Acceptable gaps:** Single-item GET endpoints (facts/{id}, decisions/{id}, etc.) are less critical for a list-first UI pattern.

---

## 10. Error Handling Analysis

### 10.1 Centralized Error Handler (`lib/api.ts`)

The `request()` function:
- Catches non-OK responses
- Parses `detail`/`message` from JSON error bodies
- Falls back to raw text or `HTTP {status}`
- Attaches `.status` property to the thrown error
- Throws a proper `Error` object

**Strength:** Single point of error formatting. All `apiGet`/`apiPost`/etc. callers get consistent errors.

### 10.2 Page-Level Error Handling

| Page | Pattern | Issues |
|------|---------|--------|
| Dashboard | `alert()` on create error; `.catch()` silent on load | Inconsistent; no user-friendly error display |
| Projects | `.catch(() => setLoading(false))` — silent | No error message shown to user |
| Chat | Inline error in message stream | Good — user sees the error in context |
| Ingest | `alert()` on error | Better than silent, but not ideal UX |
| Memory | `setError()` + conditional render | Good |
| Facts/Decisions/Timeline | `catch {}` (empty) + `finally { setLoading(false) }` | **No error display at all** |
| Search | `catch {}` (empty) | **No error display at all** |
| Graph | `catch {}` (empty) | **No error display at all** |
| Provenance | `catch {}` (empty) | **No error display at all** |
| Settings | `showMessage('error', ...)` | Good — toast-like message |
| Profile | `showMessage('error', ...)` | Good |
| API Keys | `setError()` from hook | Good |
| Storage | `alert()` on error | Acceptable |

### 10.3 SSE Error Handling

- `useSSE.ts`: `onerror` fires for connection drops; `error` event from server. But no reconnection logic.
- `chat/page.tsx`: Empty `catch {}` on JSON parse (line 137) — silently drops malformed SSE events.

### 10.4 Token Refresh Error Handling

- 401 triggers refresh via `refreshAccessToken()`
- If refresh fails: `clearTokens()` → user is logged out
- If retry also returns 401: `clearTokens()` again
- **Missing:** No redirect to login page after token clearance. The user sees stale UI until they navigate.

### 10.5 Network Error Handling

`lib/errors.ts` defines `isNetworkError()` which checks for `'Failed to fetch'` / `'NetworkError'` strings. However, this utility is **not imported or used anywhere** in the codebase. Network errors are treated the same as API errors (via the `request()` throw).

---

## 11. Authentication & Token Management

### 11.1 Token Storage

- **Location:** `localStorage` key `sv_tokens`
- **Shape:** `{ access_token: string, refresh_token: string }`
- **Risk:** XSS can steal tokens. No httpOnly cookie protection.

### 11.2 Token Refresh Flow

```
Request → 401 → refreshAccessToken() → POST /api/v1/auth/refresh
  → Success: retry original request with new token
  → Failure: clearTokens() → user unauthenticated
```

### 11.3 SSE Auth Issue

The `useSSE.ts` hook creates `EventSource(url)` — **no Authorization header can be set**. The backend's `/api/v1/chat/stream` endpoint requires authentication. This means:
- The SSE hook (useChat) cannot authenticate
- The chat/page.tsx inline implementation correctly passes the token in the `fetch()` headers — this is the only working chat path

### 11.4 CORS

Backend CORS config (`main.py` lines 216-223):
```python
allow_origins=cors_origins_safe
allow_credentials=True
allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
allow_headers=["Authorization", "Content-Type", "X-Request-ID"]
```

The frontend sends `credentials: 'include'` on every request. The CORS config allows credentials. **No CORS issues expected.**

### 11.5 Rate Limiting

Backend has `RateLimitMiddleware`. E2E tests bypass it with `X-E2E: true` header. The frontend does NOT send this header, so it is subject to rate limiting in production.

---

## 12. Summary Statistics

### 12.1 API Call Count

| Category | Count |
|----------|-------|
| Total unique API calls across all pages/hooks | 49 |
| Correct URL + method + body | 35 |
| Trailing slash issue (cosmetic) | 3 |
| Wrong URL path | 2 (`useSearch`, `useGraph`) |
| Wrong HTTP method | 2 (`search/page.tsx` GET instead of POST, `useChat` SSE GET instead of POST) |
| Missing request body field | 1 (`chat` missing `project_id`) |
| Schema mismatch (response fields) | 1 (`facts/page.tsx` wrong field names) |
| Logic bug (wrong variable used) | 1 (`storage/page.tsx` uses workspace_id as project_id) |

### 12.2 Backend Endpoints

| Metric | Count |
|--------|-------|
| Total backend API routes | 82 (79 under `/api/v1`, 3 health) |
| Frontend calls at least one endpoint from each of these routers | 10 of 14 (auth, workspace, projects, sessions, chat, memory, ingest, provenance, api-keys) |
| Backend routers completely unused by frontend | 4 (dashboard, feedback, policy, audit) |
| Backend routes called by frontend | ~25 |
| Backend routes NOT called by frontend | ~54 |

### 12.3 Code Quality

| Metric | Count |
|--------|-------|
| Dead/unused hooks | 1 (`useChat.ts` — uses broken SSE pattern) |
| Direct `fetch()` calls (bypassing api.ts) | 3 (chat/page.tsx, search/page.tsx, storage/page.tsx) |
| Duplicate API call implementations | 2 (chat streaming in both page.tsx and useChat.ts) |
| Local type definitions duplicating `types/api.ts` | 3 (facts, decisions, sessions pages define local types) |
| Error handlers that silently swallow errors | 7 (facts, decisions, timeline, search, graph, provenance pages) |
| Pages using centralized `formatApiError()` | 0 (defined but never imported) |

---

## Critical Bugs Summary

| # | Bug | File | Impact |
|---|-----|------|--------|
| 1 | **Search returns 405** — uses GET on POST-only endpoint | `search/page.tsx:34`, `useSearch.ts:19` | Search is completely broken |
| 2 | **Graph hook returns 404** — wrong URL path | `useGraph/useGraph.ts:16` | Graph hook is broken (graph/page.tsx works because it calls the correct URL directly) |
| 3 | **Chat hook broken** — EventSource can't POST body | `features/chat/useChat.ts:42` | Hook is dead code; chat/page.tsx works via direct fetch |
| 4 | **Facts page type mismatch** — reads `statement`/`status`/`authority:string` instead of `content`/`temporal_status`/`confidence:number` | `projects/[id]/facts/page.tsx:8-16` | Facts won't render correctly |
| 5 | **Storage page logic bug** — uses `workspace_id` where `project_id` is expected | `settings/storage/page.tsx:37` | Uploads fail with "Project not found" |
| 6 | **Chat missing project_id** — not sent in request body | `projects/[id]/chat/page.tsx:52` | Chat works but without project-specific memory grounding |
| 7 | **No re-authentication after token expiry** — after `clearTokens()`, UI doesn't redirect to login | `lib/api.ts:54-57` | User sees stale empty state |
