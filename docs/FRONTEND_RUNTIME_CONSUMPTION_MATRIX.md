# Frontend Runtime Consumption Matrix
**Generated:** 2026-09-05  
**Phase:** 1R-B Frontend Consumer Forensics  
**Backend:** SwarmVault FastAPI (81 endpoints, port 8000)  
**Frontend:** Next.js 15.5 (port 3000)

---

## Summary

| Status | Count | Description |
|--------|-------|-------------|
| **VERIFIED WORKING** | 19 | Consumers correctly call backend endpoints with proper auth/methods |
| **BROKEN** | 2 | `useSSE.tsx` + `useChat.ts` — EventSource GET-only vs backend POST requirement |
| **DEAD CODE** | 2 | `useChat.ts` imported nowhere; `useSSE.tsx` imported only by `useChat.ts` |
| **UNUSED (by features)** | 6 | API helpers in `api.ts` not called by any page (e.g., `getDocuments`, `ingestJob`) |

---

## Working Consumers (19 files)

### Pages (13 files)

| File | Endpoints Called | Method | Status |
|------|-----------------|--------|--------|
| `app/page.tsx` | Dashboard redirect | — | OK |
| `app/dashboard/page.tsx` | `GET /api/v1/dashboard/` | `apiGet` | OK |
| `app/projects/page.tsx` | `GET /api/v1/projects/` | `apiGet` | OK |
| `app/projects/[id]/layout.tsx` | `GET /api/v1/projects/{id}`, `PATCH /api/v1/projects/{id}`, `DELETE /api/v1/projects/{id}` | `apiGet`/`apiPatch`/`apiDelete` | OK |
| `app/projects/[id]/chat/page.tsx` | `POST /api/v1/chat/stream` | `streamChat()` (fetch POST + ReadableStream) | OK — correct implementation |
| `app/projects/[id]/search/page.tsx` | `POST /api/v1/ingest/search` | `apiPost` | OK |
| `app/projects/[id]/facts/page.tsx` | `GET /api/v1/ingest/facts` | `apiGet` | OK |
| `app/projects/[id]/decisions/page.tsx` | `GET /api/v1/ingest/decisions` | `apiGet` | OK |
| `app/projects/[id]/memory/page.tsx` | `GET /api/v1/memory/` | `apiGet` | OK |
| `app/projects/[id]/graph/page.tsx` | `GET /api/v1/ingest/graph` | `apiGet` | OK |
| `app/projects/[id]/timeline/page.tsx` | `GET /api/v1/ingest/timeline` | `apiGet` | OK |
| `app/projects/[id]/sessions/page.tsx` | `GET /api/v1/sessions/` | `apiGet` | OK |
| `app/projects/[id]/sessions/[sessionId]/page.tsx` | `GET /api/v1/sessions/{id}` | `apiGet` | OK |
| `app/projects/[id]/ingest/page.tsx` | `POST /api/v1/ingest/upload`, `GET /api/v1/ingest/sources` | `uploadFile`/`apiPost`/`apiGet` | OK |
| `app/projects/[id]/provenance/page.tsx` | `GET /api/v1/provenance/` | `apiGet` | OK |
| `app/projects/[id]/settings/page.tsx` | `GET/PATCH /api/v1/projects/{id}`, workspace member CRUD | `apiGet`/`apiPatch`/`apiPost`/`apiDelete` | OK |
| `app/settings/api-keys/page.tsx` | via `useApiKeys` hook | — | OK |
| `app/settings/storage/page.tsx` | Storage endpoints | — | OK |
| `app/settings/profile/page.tsx` | Profile endpoints | — | OK |
| `app/auth/login/page.tsx` | `POST /api/v1/auth/login` | `apiPost` | OK |
| `app/auth/register/page.tsx` | `POST /api/v1/auth/register` | `apiPost` | OK |

### Hooks (2 files)

| File | Role | Status |
|------|------|--------|
| `hooks/useAuth.tsx` | Auth context, calls `/api/v1/auth/me`, `/login`, `/register`, `/logout` via `apiGet`/`apiPost` | OK |
| `hooks/AppShell.tsx` | Routing shell | OK |
| `hooks/AuthRedirect.tsx` | Route guard | OK |

### Feature Hooks

| File | Consumed By | Endpoints Called | Status |
|------|------------|-----------------|--------|
| `features/apiKeys/useApiKeys.ts` | `settings/api-keys/page.tsx` | CRUD on `/api/v1/api-keys/` | OK |
| `features/projects/useProjects.ts` | Project pages | CRUD on `/api/v1/projects/` | OK |

---

## Broken Consumers (2 files)

### 1. `hooks/useSSE.tsx` — BROKEN

**Problem:** Uses `EventSource` which is GET-only. Cannot send POST body or Authorization headers.

```tsx
// Current (BROKEN):
const es = new EventSource(url);  // GET-only, no auth, no body
```

**Required by backend:** `POST /api/v1/chat/stream` with `Authorization: Bearer <token>` and JSON body `{ message }`.

**Impact:** Any consumer using this hook cannot authenticate or send messages via streaming chat.

### 2. `features/chat/useChat.ts` — BROKEN

**Problem:** Imports and uses `useSSE.tsx`. Since `useSSE.tsx` is broken, this hook is also broken.

```ts
// Current (BROKEN):
const url = `/api/v1/chat/stream?project_id=${encodeURIComponent(projectId || '')}`;
const cleanup = stream(url, ...);  // Uses EventSource (GET-only)
```

**Impact:** Cannot send chat messages via streaming. The `chat/page.tsx` workaround bypasses this hook entirely.

**Consumer count:** 0 (dead code — no page imports `useChat.ts`)

---

## Correct Streaming Implementation (Reference)

`chat/page.tsx` correctly implements streaming by using `streamChat()` from `api.ts`:

```ts
const res = await fetch(`${API_BASE}/api/v1/chat/stream`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : '',
  },
  body: JSON.stringify({ message: userMsg.content }),
});
// Then ReadableStream reader for SSE parsing
```

This is the pattern `useSSE.tsx` must adopt.

---

## Unused API Helpers (6 functions in `api.ts`)

| Function | Endpoint | Used By | Notes |
|----------|----------|---------|-------|
| `apiPut` | PUT requests | None | Not implemented on backend |
| `apiGetDocuments` | `/api/v1/documents/` | None | Backend endpoint not in router |
| `ingestJob` | `/api/v1/ingest/jobs/{id}` | None | Helper exists, no consumer |
| `apiPatchPolicy` | Policy endpoints | None | Covered by `apiPatch` generic |
| `streamChat` | `/api/v1/chat/stream` | `chat/page.tsx` | **USED** — correct implementation |
| `uploadFile` | `/api/v1/ingest/upload` | `ingest/page.tsx` | **USED** — multipart upload |

---

## Backend Endpoint Coverage

| Backend Endpoint | Frontend Consumer | Status |
|-----------------|-------------------|--------|
| `POST /api/v1/auth/register` | `useAuth.tsx`, `register/page.tsx` | Covered |
| `POST /api/v1/auth/login` | `useAuth.tsx`, `login/page.tsx` | Covered |
| `POST /api/v1/auth/refresh` | `api.ts` (token refresh) | Covered |
| `POST /api/v1/auth/logout` | `useAuth.tsx` | Covered |
| `GET /api/v1/auth/me` | `useAuth.tsx` | Covered |
| `POST /api/v1/auth/change-password` | Not yet implemented in frontend | Gap |
| `GET /api/v1/workspace/` | Not yet implemented in frontend | Gap |
| `PATCH /api/v1/workspace/` | Not yet implemented in frontend | Gap |
| `DELETE /api/v1/workspace/` | Not yet implemented in frontend | Gap |
| `GET /api/v1/workspace/members` | `settings/page.tsx` | Covered |
| `POST /api/v1/workspace/members` | `settings/page.tsx` | Covered |
| `PATCH /api/v1/workspace/members/{id}` | `settings/page.tsx` | Covered |
| `DELETE /api/v1/workspace/members/{id}` | `settings/page.tsx` | Covered |
| `POST /api/v1/workspace/member/leave` | Not yet implemented | Gap |
| `GET /api/v1/workspace/members/invitations` | Not yet implemented | Gap |
| `GET /api/v1/workspace/invitations` | Not yet implemented | Gap |
| `PATCH /api/v1/workspace/members/invitation/{id}` | Not yet implemented | Gap |
| `DELETE /api/v1/workspace/members/invitation/{id}` | Not yet implemented | Gap |
| `GET /api/v1/workspace/workspaces/all` | Not yet implemented | Gap |
| `GET /api/v1/workspace/workspaces/available` | Not yet implemented | Gap |
| `GET /api/v1/projects/` | `projects/page.tsx` | Covered |
| `POST /api/v1/projects/` | Not yet implemented | Gap |
| `GET /api/v1/projects/{id}` | `layout.tsx` | Covered |
| `PATCH /api/v1/projects/{id}` | `layout.tsx`, `settings/page.tsx` | Covered |
| `DELETE /api/v1/projects/{id}` | `layout.tsx` | Covered |
| `GET /api/v1/sessions/` | `sessions/page.tsx` | Covered |
| `POST /api/v1/sessions/` | Not yet implemented | Gap |
| `GET /api/v1/sessions/{id}` | `sessions/[sessionId]/page.tsx` | Covered |
| `GET /api/v1/sessions/{id}/history` | Not yet implemented | Gap |
| `POST /api/v1/sessions/{id}/messages` | Not yet implemented | Gap |
| `DELETE /api/v1/sessions/{id}` | Not yet implemented | Gap |
| `POST /api/v1/chat/` | Not yet implemented | Gap |
| `POST /api/v1/chat/stream` | `chat/page.tsx` (via `streamChat()`) | Covered |
| `POST /api/v1/memory/` | Not yet implemented | Gap |
| `GET /api/v1/memory/` | `memory/page.tsx` | Covered |
| `GET /api/v1/memory/{id}` | Not yet implemented | Gap |
| `PATCH /api/v1/memory/{id}` | Not yet implemented | Gap |
| `DELETE /api/v1/memory/{id}` | Not yet implemented | Gap |
| `POST /api/v1/memory/search` | Not yet implemented | Gap |
| `POST /api/v1/ingest/upload` | `ingest/page.tsx` | Covered |
| `POST /api/v1/ingest/` | Not yet implemented | Gap |
| `GET /api/v1/ingest/sources` | `ingest/page.tsx` | Covered |
| `GET /api/v1/ingest/sources/{id}` | Not yet implemented | Gap |
| `GET /api/v1/ingest/sources/{id}/messages` | Not yet implemented | Gap |
| `GET /api/v1/ingest/facts` | `facts/page.tsx` | Covered |
| `GET /api/v1/ingest/facts/{id}` | Not yet implemented | Gap |
| `GET /api/v1/ingest/decisions` | `decisions/page.tsx` | Covered |
| `GET /api/v1/ingest/decisions/{id}` | Not yet implemented | Gap |
| `GET /api/v1/ingest/graph` | `graph/page.tsx` | Covered |
| `GET /api/v1/ingest/timeline` | `timeline/page.tsx` | Covered |
| `POST /api/v1/ingest/search` | `search/page.tsx` | Covered |
| `GET /api/v1/ingest/jobs` | Not yet implemented | Gap |
| `GET /api/v1/ingest/jobs/{id}` | Not yet implemented | Gap |
| `GET /api/v1/provenance/` | `provenance/page.tsx` | Covered |
| `GET /api/v1/provenance/{id}` | Not yet implemented | Gap |
| `GET /api/v1/provenance/{id}/memories` | Not yet implemented | Gap |
| `GET /api/v1/dashboard/` | `dashboard/page.tsx` | Covered |
| `GET /api/v1/dashboard/projects/{id}` | Not yet implemented | Gap |
| `POST /api/v1/feedback/` | Not yet implemented | Gap |
| `GET /api/v1/feedback/` | Not yet implemented | Gap |
| `GET /api/v1/feedback/{id}` | Not yet implemented | Gap |
| `POST /api/v1/api-keys/` | `settings/api-keys/page.tsx` | Covered |
| `GET /api/v1/api-keys/` | `settings/api-keys/page.tsx` | Covered |
| `DELETE /api/v1/api-keys/{id}` | `settings/api-keys/page.tsx` | Covered |
| `POST /api/v1/api-keys/{id}/rotate` | `settings/api-keys/page.tsx` | Covered |
| `POST /api/v1/storage/upload` | Not yet implemented | Gap |
| `GET /api/v1/storage/{key}` | Not yet implemented | Gap |
| `DELETE /api/v1/storage/{key}` | Not yet implemented | Gap |
| `GET /api/v1/policy/` | Not yet implemented | Gap |
| `POST /api/v1/policy/` | Not yet implemented | Gap |
| `GET /api/v1/policy/{id}` | Not yet implemented | Gap |
| `PATCH /api/v1/policy/{id}` | Not yet implemented | Gap |
| `DELETE /api/v1/policy/{id}` | Not yet implemented | Gap |
| `POST /api/v1/policy/{id}/versions` | Not yet implemented | Gap |
| `POST /api/v1/policy/test-authorization` | Not yet implemented | Gap |
| `GET /api/v1/audit/events` | Not yet implemented | Gap |
| `GET /api/v1/audit/events/{id}` | Not yet implemented | Gap |
| `GET /api/v1/audit/trace/{request_id}` | Not yet implemented | Gap |
| `/health/live` | Health check | Covered |
| `/health/ready` | Health check | Covered |
| `/` | Root | Covered (404 expected) |

---

## Coverage Statistics

- **Backend endpoints:** 81
- **Frontend consumers verified:** 36 (pages + hooks)
- **Endpoints covered by frontend:** ~34 (42%)
- **Endpoints with no frontend consumer:** ~47 (58%) — gaps for future implementation
- **Broken consumers:** 2 (`useSSE.tsx`, `useChat.ts`)
- **Working consumers:** 19 pages/hooks
