# EXECUTE_IMPLEMENTATION.md

## Phase 2 — Implementation Plan (Execution-Ready)

**Date:** 2026-09-05
**Status:** PLAN — awaiting approval

---

## Overview

This document is the execution-ready plan derived from the 6 analysis documents:
1. `FRONTEND_RUNTIME_CONSUMPTION_MATRIX.md` — all broken consumers
2. `FRONTEND_CORE_CAPABILITY_MATRIX.md` — all features categorized A/B/C/D
3. `USER_VALUE_MATRIX.md` — all 22 user values mapped
4. `ACTUAL_API_CONTRACT.md` — exact request/response schemas
5. `FRONTEND_BACKEND_INTEGRATION_CERTIFICATION.md` — full certification
6. `PHASE_1RB_FINAL_CERTIFICATION.md` — certification with limitations

**Total broken consumers:** 9
**Total deferred capabilities:** 10
**Estimated effort:** 2-3 developer days

---

## Implementation Checklist

### Critical (P1) — Blocking chat and graph

- [ ] **Fix useSSE.tsx** — Replace EventSource with fetch+ReadableStream to support POST with auth headers
- [ ] **Fix useGraph.ts** — Change path from `/api/v1/graph` to `/api/v1/ingest/graph`

### High (P2) — Broken pages and data

- [ ] **Fix useAuth.tsx logout** — Include `refresh_token` in request body
- [ ] **Fix search/page.tsx** — Change from GET to POST method
- [ ] **Fix facts/page.tsx** — Replace local `FactItem` interface with shared type or correct fields
- [ ] **Fix decisions/page.tsx** — Remove non-existent `tags` field from local `DecisionItem`
- [ ] **Fix useIngest.ts jobs** — Change type from `IngestJobOut[]` to `{items: IngestJobOut[], total: number}`
- [ ] **Fix types/api.ts ApiKeyOut** — Rename `prefix` to `key_prefix`

### Medium (P3) — Improvements

- [ ] **Fix chat/page.tsx** — Add `project_id` and `session_id` to chat request body
- [ ] **Improve error handling** — Replace `catch {}` with proper error display in page components
- [ ] **Implement missing frontend pages** — Policies, Audit, Members, Invitations, System Health

### Deferred — No backend implementation

- [ ] Operations (Board, Agents, Claims, Tasks, Supervisor, Signals, Schedules)
- [ ] Context Packs
- [ ] Conflicts
- [ ] Procedures
- [ ] Checkpoints
- [ ] Watcher/Sync
- [ ] Archive/Lifecycle
- [ ] Diagnostics
- [ ] Retrieval/Retention settings

---

## Fix Details

### Fix 1: useSSE.tsx — Replace EventSource with fetch+ReadableStream

**File:** `frontend/src/hooks/useSSE.tsx`
**Change:** Replace `EventSource` (GET-only, no auth) with `fetch()` POST + `ReadableStream` reader
**Pattern:** Match `chat/page.tsx` pattern (lines 46-139)

### Fix 2: useGraph.ts — Fix endpoint path

**File:** `frontend/src/features/graph/useGraph.ts`
**Change:** Line 16: `/api/v1/graph` → `/api/v1/ingest/graph`

### Fix 3: useAuth.tsx — Fix logout body

**File:** `frontend/src/hooks/useAuth.tsx`
**Change:** Line 46: `apiPost('/api/v1/auth/logout', {})` → `apiPost('/api/v1/auth/logout', { refresh_token: getRefreshToken() })`

### Fix 4: search/page.tsx — Change to POST

**File:** `frontend/src/app/projects/[id]/search/page.tsx`
**Change:** Replace `fetch()` GET with POST matching backend signature

### Fix 5: facts/page.tsx — Fix local type

**File:** `frontend/src/app/projects/[id]/facts/page.tsx`
**Change:** Replace local `FactItem` interface with correct backend fields: `content` (not `statement`), add `subject`, `predicate`, `object`, `source_id`, fix `authority` type to `number`

### Fix 6: decisions/page.tsx — Fix local type

**File:** `frontend/src/app/projects/[id]/decisions/page.tsx`
**Change:** Remove `tags: string[]` from local `DecisionItem` interface

### Fix 7: useIngest.ts jobs — Fix response type

**File:** `frontend/src/features/ingest/useIngest.ts`
**Change:** Change return type or destructure `data.items` from paginated response

### Fix 8: types/api.ts — Fix ApiKeyOut field

**File:** `frontend/src/types/api.ts`
**Change:** Rename `prefix: string` to `key_prefix: string` in `ApiKeyOut`

### Fix 9: chat/page.tsx — Add project context

**File:** `frontend/src/app/projects/[id]/chat/page.tsx`
**Change:** Add `project_id` and `session_id` to request body

---

## Execution Order

1. Fixes 2, 8 — Trivial (1-line path/field changes) — do first
2. Fix 1 — Medium (replace EventSource pattern) — do second
3. Fixes 3, 4, 9 — Simple method/body changes — do third
4. Fixes 5, 6, 7 — Type changes — do fourth
5. Error handling improvements — do last
