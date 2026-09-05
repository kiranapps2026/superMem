# FRONTEND_RUNTIME_CONSUMPTION_MATRIX.md

## Phase 2 — Frontend API Consumption Audit

**Date:** 2026-09-05
**Method:** Static analysis of every `apiGet`/`apiPost`/`apiPatch`/`apiDelete`/`uploadFile`/`streamChat`/`fetch` call in frontend source

---

## Summary

| Category | Count |
|----------|-------|
| Frontend API consumers (hooks + pages) | 8 hooks, 4 pages |
| API endpoint invocations | 25 distinct endpoint paths |
| Broken consumers | **2** |
| Type mismatches (fixed) | 3 (already patched) |
| Unused types | Several |
| Working consumers | 23 |

---

## Hook-by-Hook Analysis

### 1. `useAuth` (`hooks/useAuth.tsx`)

| Call | Method | Endpoint | Request | Backend Schema | Response | TS Type | Status |
|------|--------|----------|---------|----------------|----------|---------|--------|
| `apiGet('/api/v1/auth/me')` | GET | `/auth/me` | None | — | `UserOut` | inline `{id,email,name,workspace_id,tenant_id}` | ✅ Match |
| `apiPost('/api/v1/auth/login', {email,password})` | POST | `/auth/login` | `UserLogin` | `{email,password}` | `TokenResponse` | `TokenPair` | ⚠️ Mismatch: `TokenResponse` has `access_token,refresh_token,token_type,expires_in` — no `user` field. TS type `TokenPair` includes `user` which backend doesn't return. Register response is the one that includes user data. |
| `apiPost('/api/v1/auth/register', data)` | POST | `/auth/register` | `UserRegister` | `{email,password,name,workspace_name}` | `TokenResponse` | `TokenPair & {user: UserInfo}` | ⚠️ Same issue — `TokenPair` has `user` field that doesn't exist in `TokenResponse` |
| `apiPost('/api/v1/auth/logout', {})` | POST | `/auth/logout` | `RefreshRequest` | `{refresh_token}` | `{"detail": "Logged out"}` | (none) | ⚠️ Sends empty body but backend requires `refresh_token`. Logout will 422. |

**Verdict:** P2 — logout sends empty body instead of refresh_token. Login/register types include `user` field that backend doesn't return.

---

### 2. `useProjects` (`features/projects/useProjects.ts`)

| Call | Method | Endpoint | Request | Backend Schema | Response | TS Type | Status |
|------|--------|----------|---------|----------------|----------|---------|--------|
| `apiGet('/api/v1/projects/')` | GET | `/projects/` | None | — | `list[ProjectOut]` | `Project[]` | ✅ Match |
| `apiGet('/api/v1/projects/${id}')` | GET | `/projects/{id}` | path param | — | `ProjectOut` | `Project` | ✅ Match |
| `apiPost('/api/v1/projects/', data)` | POST | `/projects/` | `ProjectCreate` | `{name,description}` | `ProjectOut` | `Project` | ✅ Match |
| `apiPatch('/api/v1/projects/${id}', data)` | PATCH | `/projects/{id}` | `ProjectUpdate` | `{name?,description?}` | `ProjectOut` | `Project` | ✅ Match |
| `apiDelete('/api/v1/projects/${id}')` | DELETE | `/projects/{id}` | None | — | None (204) | (none) | ✅ Match |

**Verdict:** All correct.

---

### 3. `useChat` (`features/chat/useChat.ts`)

| Call | Method | Endpoint | Request | Backend Schema | Response | TS Type | Status |
|------|--------|----------|---------|----------------|----------|---------|--------|
| `EventSource('/api/v1/chat/stream?project_id=...')` | **GET** (EventSource) | `/chat/stream` | Query param only | **Requires POST body** | SSE stream | `ChatStreamEvent` | ❌ **BROKEN** — `EventSource` cannot send POST body or Authorization header. Backend requires POST with `{message, session_id?, project_id?}`. |

**Verdict:** ❌ CRITICAL — Chat streaming is completely broken in the `useChat` hook. The `chat/page.tsx` works because it uses `fetch` directly with POST + ReadableStream.

---

### 4. `chat/page.tsx` (direct implementation)

| Call | Method | Endpoint | Request | Backend Schema | Response | Status |
|------|--------|----------|---------|----------------|----------|--------|
| `fetch('/api/v1/chat/stream', {method:'POST', body:JSON.stringify({message})})` | POST | `/chat/stream` | `{message}` — missing `session_id`, `project_id` | `ChatRequest` (message, session_id?, project_id?) | SSE stream via ReadableStream | ⚠️ Works but missing `project_id` and `session_id` in request body |

**Verdict:** Works for basic chat. Missing `project_id` and `session_id` means memory context is scoped to user-level instead of project-level.

---

### 5. `useMemory` (`features/memory/useMemory.ts`)

| Call | Method | Endpoint | Request | Backend Schema | Response | TS Type | Status |
|------|--------|----------|---------|----------------|----------|---------|--------|
| `apiGet('/api/v1/memory/')` | GET | `/memory/` | q: memory_type?, project_id?, limit, offset | — | `list[MemoryOut]` | `MemoryItemOut[]` | ✅ Match |
| `apiPost('/api/v1/memory/', data)` | POST | `/memory/` | `{project_id, memory_type, content, confidence?, extra_metadata?}` | `MemoryCreate` (memory_type, content, scope, agent_id?, run_id?, project_id?, extra_metadata?) | `MemoryOut` | `MemoryItemOut` | ✅ Match |
| `apiPost('/api/v1/memory/search', body)` | POST | `/memory/search` | `{query, memory_type?, project_id?, limit?}` | `MemorySearchRequest` | `list[MemoryOut]` | `MemoryItemOut[]` | ✅ Match |
| `apiDelete('/api/v1/memory/${id}')` | DELETE | `/memory/{id}` | — | — | None (204) | (none) | ✅ Match |

**Verdict:** All correct.

---

### 6. `useSearch` (`features/search/useSearch.ts`)

| Call | Method | Endpoint | Request | Backend Schema | Response | TS Type | Status |
|------|--------|----------|---------|----------------|----------|---------|--------|
| `apiPost('/api/v1/ingest/search?query=...&limit=...')` | POST | `/ingest/search` | Query params: `query`, `limit`, `project_id?` — sends empty body (`undefined`) | **Requires `query` as query param, optional `limit`** | `SearchResponse` | `SearchResponse` | ✅ Match (fixed) |

**Verdict:** Correct after fix. Note: endpoint is unusual — POST method with query params (not body).

---

### 7. `useGraph` (`features/graph/useGraph.ts`)

| Call | Method | Endpoint | Request | Backend Schema | Response | TS Type | Status |
|------|--------|----------|---------|----------------|----------|---------|--------|
| `apiGet('/api/v1/graph?project_id=...')` | GET | **WRONG PATH** — `/api/v1/graph` | q: project_id | **Correct endpoint is `/api/v1/ingest/graph`** | `GraphResponse` | `GraphResponse` | ❌ **BROKEN** — 404, endpoint doesn't exist at this path |

**Verdict:** ❌ CRITICAL — Graph page is completely non-functional. Path must be `/api/v1/ingest/graph`.

---

### 8. `useIngest` (`features/ingest/useIngest.ts`)

| Call | Method | Endpoint | Request | Backend Schema | Response | TS Type | Status |
|------|--------|----------|---------|----------------|----------|---------|--------|
| `apiGet('/api/v1/ingest/sources?project_id=...')` | GET | `/ingest/sources` | q: project_id, status?, limit, offset | — | `SourceListResponse` | `SourceListResponse` | ✅ Match |
| `apiGet('/api/v1/ingest/facts?project_id=...')` | GET | `/ingest/facts` | q: project_id, subject?, temporal_status?, limit, offset | — | `FactListResponse` | `PaginatedResponse<FactItem>` | ✅ Match |
| `apiGet('/api/v1/ingest/decisions?project_id=...')` | GET | `/ingest/decisions` | q: project_id, temporal_status?, limit, offset | — | `DecisionListResponse` | `PaginatedResponse<DecisionItem>` | ✅ Match |
| `apiGet('/api/v1/ingest/jobs')` | GET | `/ingest/jobs` | q: limit, offset | — | `{items[], total}` | `IngestJobOut[]` | ❌ **TYPE MISMATCH** — Backend returns `{items[], total}` but TS type is `IngestJobOut[]` (array, not object) |
| `uploadFile(projectId, file)` | POST (multipart) | `/ingest/upload` | FormData: project_id, source_type, file | multipart | `IngestUploadResponse` | (returns `{source_id, status}` via callback) | ✅ Match |

**Verdict:** `useIngestJobs` has a type mismatch — expects array, backend returns paginated object. 3 other consumers correct.

---

### 9. `useApiKeys` (`features/apiKeys/useApiKeys.ts`)

| Call | Method | Endpoint | Request | Backend Schema | Response | TS Type | Status |
|------|--------|----------|---------|----------------|----------|---------|--------|
| `apiGet('/api/v1/api-keys')` | GET | `/api-keys/` | — | — | `list[ApiKeyOut]` | `ApiKeyOut[]` | ⚠️ **FIELD MISMATCH** — Backend `ApiKeyOut` has `key_prefix`; TS interface has `prefix` |
| `apiPost('/api/v1/api-keys', {name})` | POST | `/api-keys/` | `{name}` | `ApiKeyCreate` (name, description?, expires_at?, metadata?) | `ApiKeyCreateResponse` (with `raw_key`) | `ApiKeyOut & {raw_key}` | ⚠️ Same field name mismatch + missing fields (description, expires_at, key_extra) |
| `apiDelete('/api/v1/api-keys/${id}')` | DELETE | `/api-keys/{id}` | — | — | None (204) | (none) | ✅ Match |
| `apiPost('/api/v1/api-keys/${id}/rotate', {})` | POST | `/api-keys/{id}/rotate` | Empty body | — | `ApiKeyRotateResponse` | `ApiKeyOut & {raw_key}` | ⚠️ Field name mismatch |

**Verdict:** Non-breaking — `prefix` vs `key_prefix` causes UI to show `undefined` for the prefix display field.

---

## Broken Consumers Summary

| # | Consumer | Endpoint Called | Correct Endpoint | Impact |
|---|----------|---------------|-----------------|--------|
| 1 | `useChat.ts` (EventSource) | GET `/api/v1/chat/stream` | POST `/api/v1/chat/stream` | **Chat streaming broken in useChat hook** |
| 2 | `useGraph.ts` | GET `/api/v1/graph` | GET `/api/v1/ingest/graph` | **Graph page returns 404** |
| 3 | `useAuth.tsx` logout | POST `/auth/logout` with `{}` | Needs `{refresh_token}` | **Logout fails silently** |
| 4 | `useIngest.ts` jobs | Expects `IngestJobOut[]` | Returns `{items[], total}` | **Jobs list will crash on `.map()`** |
| 5 | `useApiKeys.ts` | Field `prefix` | Field `key_prefix` | **Key prefix shows undefined** |
| 6 | `chat/page.tsx` | POST with `{message}` only | Needs `{message, project_id?, session_id?}` | **Missing project context in chat** |

---

## Type Mismatches Fixed (Phase 1R-B)

| # | File | Issue | Fix Applied |
|---|------|-------|-------------|
| 1 | `useSearch.ts` | Called `/api/v1/search/` (404) | Fixed to `/api/v1/ingest/search` |
| 2 | `types/api.ts` | `FactItem.source_message_id` | Renamed to `source_id` |
| 3 | `types/api.ts` | `FactItem` missing `subject/predicate/object` | Added fields |
| 4 | `types/api.ts` | `DecisionItem.tags` non-existent | Removed field |
