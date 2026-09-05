# FRONTEND_RUNTIME_CONSUMPTION_MATRIX.md

## Phase 1R-B — Frontend Consumer Audit

**Date:** 2026-09-05
**Auditor:** Claude (automated)
**Final SHA:** `4aa908d5`

This document maps every frontend consumer (page, hook, component) to its backend API endpoint(s) and classifies the health of each consumer.

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Consumer works correctly at runtime |
| ⚠️ | Consumer has a defect but has a workaround |
| ❌ | Consumer is broken with no working path |

---

## 1. Authentication (`hooks/useAuth.tsx`)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| login | POST | /auth/login | ✅ | — |
| register | POST | /auth/register | ✅ | — |
| me (on mount) | GET | /auth/me | ✅ | — |
| logout | POST | /auth/logout | ⚠️ | Sends `{}` instead of `{refresh_token}`. Server-side revocation fails. Client clears localStorage correctly. |
| change-password | POST | /auth/change-password | ✅ | — |

**Defects:** 1 (P2)

---

## 2. Projects (`features/projects/useProjects.ts`)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| list | GET | /projects/ | ✅ | — |
| get | GET | /projects/{id} | ✅ | — |
| create | POST | /projects/ | ✅ | — |
| update | PATCH | /projects/{id} | ✅ | — |
| delete | DELETE | /projects/{id} | ✅ | — |

**Defects:** 0

---

## 3. Chat Streaming — Two Implementations

### 3a. `chat/page.tsx` (CORRECT)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| stream | POST | /chat/stream | ✅ | Uses `fetch()` + `ReadableStream`. Sends POST body `{message}` and `Authorization: Bearer` header. |

### 3b. `useSSE.tsx` + `useChat.ts` (BROKEN)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| stream | GET (EventSource) | /chat/stream | ❌ | `EventSource` is GET-only. Cannot send POST body or auth headers. Backend requires POST. |
| (inherited) | — | — | ❌ | `useChat.ts` imports `useSSE`. Both are broken. No component currently uses `useChat`. |

**Defects:** 2 (P0)

---

## 4. Memory (`features/memory/useMemory.ts`)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| list | GET | /memory/ | ✅ | — |
| search | POST | /memory/search | ✅ | — |
| create | POST | /memory/ | ✅ | — |
| delete | DELETE | /memory/{id} | ✅ | — |

**Defects:** 0

---

## 5. Search

### 5a. `features/search/useSearch.ts`

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| search | POST | /ingest/search | ✅ | — |

### 5b. `search/page.tsx`

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| search | GET (direct fetch) | /ingest/search | ✅ | Uses `fetch()` directly with query params. Works. (Note: does NOT use `useSearch` hook.) |

**Defects:** 0

---

## 6. Graph

### 6a. `features/graph/useGraph.ts`

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| load | GET | /graph | ❌ | Wrong path. Backend has it at `/ingest/graph`. Returns 404. |

### 6b. `graph/page.tsx`

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| load | GET | /ingest/graph | ✅ | Calls correct path directly. |

**Defects:** 1 (P1)

---

## 7. Ingest (`features/ingest/useIngest.ts`)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| sources | GET | /ingest/sources | ✅ | — |
| facts | GET | /ingest/facts | ✅ | — |
| decisions | GET | /ingest/decisions | ✅ | — |
| upload (file) | POST | /ingest/upload | ✅ | — |
| upload (text) | POST | /ingest/upload | ✅ | — |
| jobs | GET | /ingest/jobs | ⚠️ | Expects `IngestJobOut[]` (array). Backend returns `{items, total}` (paginated). No page renders this. |

**Defects:** 1 (P1 — latent)

---

## 8. API Keys (`features/apiKeys/useApiKeys.ts`)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| list | GET | /api-keys | ✅ | — |
| create | POST | /api-keys | ✅ | — |
| revoke | DELETE | /api-keys/{id} | ✅ | — |
| rotate | POST | /api-keys/{id}/rotate | ✅ | — |

**Type Issue:** `ApiKeyOut` has `prefix` field, backend returns `key_prefix`. Display masks with `undefined••••••`.

**Defects:** 1 (P2 — cosmetic)

---

## 9. Facts Page (`projects/[id]/facts/page.tsx`)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| load | GET | /ingest/facts | ⚠️ | Works (data returned). Local `FactItem` type has `statement` (backend uses `content`), `authority` as string (backend number). Content renders blank. |

**Defects:** 1 (P2)

---

## 10. Decisions Page (`projects/[id]/decisions/page.tsx`)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| load | GET | /ingest/decisions | ⚠️ | Works (data returned). Local `DecisionItem` has `tags: string[]` (doesn't exist in backend). Tags never render. |

**Defects:** 1 (P2)

---

## 11. Timeline (`projects/[id]/timeline/page.tsx`)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| load | GET | /ingest/timeline | ✅ | — |

**Defects:** 0

---

## 12. Sessions (`projects/[id]/sessions/page.tsx`)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| list | GET | /sessions | ✅ | — |

### Session Detail (`projects/[id]/sessions/[sessionId]/page.tsx`)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| history | GET | /sessions/{id}/history | ✅ | — |

**Defects:** 0

---

## 13. Provenance (`projects/[id]/provenance/page.tsx`)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| list | GET | /provenance/ | ✅ | — |

**Defects:** 0

---

## 14. Memory Page (`projects/[id]/memory/page.tsx`)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| list (filtered) | GET | /memory/ | ✅ | — |
| list (all) | GET | /memory/ | ✅ | — |

**Defects:** 0

---

## 15. Ingest Page (`projects/[id]/ingest/page.tsx`)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| sources | GET | /ingest/sources | ✅ | — |
| upload (file) | POST | /ingest/upload | ✅ | — |
| upload (text) | POST | /ingest/upload | ✅ | — |

**Defects:** 0

---

## 16. Dashboard (`dashboard/page.tsx`)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| workspace | GET | /workspace | ✅ | — |
| projects | GET | /projects/ | ✅ | — |
| create project | POST | /projects/ | ✅ | — |

**Defects:** 0

---

## 17. Settings — Workspace (`settings/page.tsx`)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| workspace | GET | /workspace | ✅ | — |
| update workspace | PATCH | /workspace | ✅ | — |
| members | GET | /workspace/members | ✅ | — |
| invite member | POST | /workspace/members | ✅ | — |
| update member | PATCH | /workspace/members/{id} | ✅ | — |
| remove member | DELETE | /workspace/members/{id} | ✅ | — |
| invitations | GET | /workspace/members/invitations | ✅ | — |
| revoke invitation | DELETE | /workspace/members/invitation/{id} | ✅ | — |
| change-password | POST | /auth/change-password | ✅ | — |

**Defects:** 0

---

## 18. Settings — Project (`projects/[id]/settings/page.tsx`)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| project (via hook) | GET | /projects/{id} | ✅ | — |
| update project | PATCH | /projects/{id} | ✅ | — |
| delete project | DELETE | /projects/{id} | ✅ | — |
| members | GET | /workspace/members | ✅ | — |

**Defects:** 0

---

## 19. Settings — Profile (`settings/profile/page.tsx`)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| update profile | PATCH | /auth/me | ✅ | — |
| change-password | POST | /auth/change-password | ✅ | — |

**Defects:** 0

---

## 20. Settings — API Keys (`settings/api-keys/page.tsx`)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| (via useApiKeys hook) | — | — | ⚠️ | Same field name issue as #8 (`prefix` vs `key_prefix`) |

**Defects:** 1 (P2 — cosmetic)

---

## 21. Settings — Storage (`settings/storage/page.tsx`)

| API Call | Method | Endpoint | Status | Issue |
|----------|--------|----------|--------|-------|
| me (for workspace_id) | GET | /auth/me | ✅ | — |
| upload (via `uploadFile`) | POST | /storage/upload | ✅ | — |
| delete | (client-side only) | — | ⚠️ | No backend delete for raw uploads. Removes from UI list only. |

**Defects:** 1 (P3 — feature gap)

---

## 22. Sidebar (`components/Sidebar.tsx`)

No API calls. Pure navigation component. Uses `useAuth` for user state and logout.

**Defects:** 0

---

## Summary Matrix

| Feature | Consumers | Defects | Severity |
|---------|-----------|---------|----------|
| Auth | 1 hook | 1 | P2 (logout body) |
| Projects | 1 hook + 2 pages | 0 | — |
| Chat (page) | 1 page | 0 | ✅ Works |
| Chat (hook) | 1 hook + useSSE | 2 | P0 (EventSource) |
| Memory | 1 hook + 1 page | 0 | — |
| Search | 1 hook + 1 page | 0 | ✅ Both work |
| Graph (hook) | 1 hook | 1 | P1 (wrong path) |
| Graph (page) | 1 page | 0 | ✅ Works |
| Ingest | 1 hook + 1 page | 1 | P1 (jobs type) |
| Facts | 1 page | 1 | P2 (type mismatch) |
| Decisions | 1 page | 1 | P2 (tags field) |
| Timeline | 1 page | 0 | — |
| Sessions | 2 pages | 0 | — |
| Provenance | 1 page | 0 | — |
| Dashboard | 1 page | 0 | — |
| Settings | 4 pages | 0 | — |
| API Keys | 1 hook + 1 page | 1 | P2 (field name) |
| Storage | 1 page | 1 | P3 (no delete) |
| Sidebar | 1 component | 0 | — |
| **TOTAL** | | **9** | 2 P0, 2 P1, 4 P2, 1 P3 |

---

## Runtime Status by Page

| Page Route | Status | Notes |
|------------|--------|-------|
| /auth/login | ✅ | Register, login, password change all work |
| /auth/register | ✅ | — |
| /dashboard | ✅ | Workspace + projects load correctly |
| /projects | ✅ | Project CRUD works |
| /projects/{id}/chat | ✅ | Streaming works (uses direct fetch) |
| /projects/{id}/ingest | ✅ | Upload + source list works |
| /projects/{id}/memory | ✅ | Memory list + filter works |
| /projects/{id}/facts | ⚠️ | Data loads but content renders blank (type mismatch) |
| /projects/{id}/decisions | ⚠️ | Data loads but tags never show (non-existent field) |
| /projects/{id}/timeline | ✅ | — |
| /projects/{id}/search | ✅ | Works (uses direct fetch) |
| /projects/{id}/graph | ✅ | Works (uses correct path) |
| /projects/{id}/sessions | ✅ | — |
| /projects/{id}/sessions/{id} | ✅ | — |
| /projects/{id}/provenance | ✅ | — |
| /projects/{id}/settings | ✅ | — |
| /settings | ✅ | Workspace, members, invitations all work |
| /settings/profile | ✅ | — |
| /settings/api-keys | ⚠️ | Keys display with masked prefix showing `undefined` |
| /settings/storage | ⚠️ | Upload works, delete is UI-only |
| / | ✅ | Redirects correctly |
