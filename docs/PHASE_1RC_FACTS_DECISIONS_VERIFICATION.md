# Phase 1RC — Gates 3 & 4: Facts & Decisions API Verification

**Date:** 2026-09-05
**Scope:** Backend ingest endpoints + frontend API client + page components
**Backend router:** `app/api/ingest.py`
**Frontend hooks:** `frontend/src/features/ingest/useIngest.ts`
**Frontend pages:** `frontend/src/app/projects/[id]/facts/page.tsx`, `decisions/page.tsx`
**Type definitions:** `frontend/src/types/api.ts`

---

## 1. Backend Facts API

| Attribute | Value |
|-----------|-------|
| **Router file** | `app/api/ingest.py` |
| **Router prefix** | `/ingest` (mounted under `/api/v1` in `app/main.py:148`) |
| **Auth dependency** | `TenantContext` only — requires valid JWT but no role check |
| **Effective minimum role** | Any authenticated user (viewer+) |

### Endpoints

| Method | Path | Handler | Response Schema | Query Params |
|--------|------|---------|-----------------|--------------|
| `GET` | `/api/v1/ingest/facts` | `list_facts` (line 255) | `FactListResponse` | `project_id?`, `subject?`, `temporal_status?`, `limit` (default 50), `offset` (default 0) |
| `GET` | `/api/v1/ingest/facts/{fact_id}` | `get_fact` (line 299) | `FactOut` | — |

### FactOut schema (backend)

```python
class FactOut(BaseModel):
    id: str
    workspace_id: str
    project_id: str | None
    source_id: str | None        # ← note: "source_id", not "source_message_id"
    subject: str                  # ← main display field
    predicate: str
    object: str                   # ← secondary display field
    content: str                  # ← full text
    confidence: float
    authority: float
    temporal_status: str
    superseded_by_id: str | None
    status: str
    created_at: datetime
    updated_at: datetime
```

---

## 2. Backend Decisions API

| Attribute | Value |
|-----------|-------|
| **Router file** | `app/api/ingest.py` |
| **Router prefix** | `/ingest` (mounted under `/api/v1`) |
| **Auth dependency** | `TenantContext` only — requires valid JWT but no role check |
| **Effective minimum role** | Any authenticated user (viewer+) |

### Endpoints

| Method | Path | Handler | Response Schema | Query Params |
|--------|------|---------|-----------------|--------------|
| `GET` | `/api/v1/ingest/decisions` | `list_decisions` (line 321) | `DecisionListResponse` | `project_id?`, `temporal_status?`, `limit` (default 50), `offset` (default 0) |
| `GET` | `/api/v1/ingest/decisions/{decision_id}` | `get_decision` (line 359) | `DecisionOut` | — |

### DecisionOut schema (backend)

```python
class DecisionOut(BaseModel):
    id: str
    workspace_id: str
    project_id: str | None
    source_id: str | None        # ← note: "source_id"
    content: str                  # ← main display field
    context: str | None
    confidence: float
    authority: float
    temporal_status: str
    superseded_by_id: str | None
    status: str
    created_at: datetime
    updated_at: datetime
```

**Key observation:** There is no `tags` field on `DecisionOut` in the backend schema.

---

## 3. Frontend API Client Verification

### useIngest.ts paths

| Hook | URL Called | Backend Match? |
|------|-----------|----------------|
| `useFacts(projectId)` | `/api/v1/ingest/facts?project_id=...` | ✅ MATCH |
| `useDecisions(projectId)` | `/api/v1/ingest/decisions?project_id=...` | ✅ MATCH |

Both hooks cast the response to `PaginatedResponse<FactItem>` / `PaginatedResponse<DecisionItem>` which has `{ items, total }` — matches backend `FactListResponse` / `DecisionListResponse`.

### Frontend types in `frontend/src/types/api.ts`

**FactItem (types/api.ts, line 64):**
```typescript
export interface FactItem {
  id: string; workspace_id: string; project_id: string | null;
  content: string; source_message_id: string | null;  // ← mismatch: backend has "source_id"
  temporal_status: string; confidence: number; authority: number;
  created_at: string; updated_at: string;
}
// Missing from backend FactOut: subject, predicate, object, superseded_by_id, status
// Extra field not in backend: source_message_id (backend is "source_id")
```

**DecisionItem (types/api.ts, line 72):**
```typescript
export interface DecisionItem {
  id: string; workspace_id: string; project_id: string | null;
  content: string; temporal_status: string;
  confidence: number; tags: string[];  // ← mismatch: backend has NO "tags" field
  created_at: string; updated_at: string;
}
// Missing from backend DecisionOut: context, authority, superseded_by_id, status, source_id
// Extra field not in backend: tags
```

---

## 4. Frontend Page Components — Field-Level Mismatches

### Facts page (`frontend/src/app/projects/[id]/facts/page.tsx`)

| Frontend field used | Backend field exists? | Issue |
|---------------------|----------------------|-------|
| `f.statement` | ❌ No (`subject` exists instead) | **MISMATCH** — page renders `undefined` |
| `f.predicate` | ✅ Yes | OK |
| `f.confidence` | ✅ Yes (float) | OK |
| `f.status` | ✅ Yes | OK |
| `f.authority` | ✅ Yes (float) | OK — but page uses as string display (line 51: `{f.authority}`) |
| `f.id` | ✅ Yes | OK |
| `f.content` | ✅ Yes | Not used in page |

The page defines its own local `FactItem` interface (line 8-16) instead of importing from `@/types/api`. This local interface uses `statement` which does not exist in the backend response. The page will render `undefined` for the fact text.

### Decisions page (`frontend/src/app/projects/[id]/decisions/page.tsx`)

| Frontend field used | Backend field exists? | Issue |
|---------------------|----------------------|-------|
| `d.content` | ✅ Yes | OK |
| `d.temporal_status` | ✅ Yes | OK |
| `d.confidence` | ✅ Yes (float) | OK |
| `d.tags` | ❌ **No** (`tags` not in DecisionOut) | **MISMATCH** — `d.tags` will always be `undefined` (the page guards with `d.tags?.length > 0` so it won't crash, but tags never render) |
| `d.id` | ✅ Yes | OK |
| `d.created_at` | ✅ Yes | OK |
| `d.updated_at` | ✅ Yes (in interface, not used in page) | OK |

---

## 5. Frontend Pages Referencing Facts/Decisions

| File | Nature of Reference |
|------|---------------------|
| `frontend/src/app/projects/[id]/facts/page.tsx` | Fetches and displays facts |
| `frontend/src/app/projects/[id]/decisions/page.tsx` | Fetches and displays decisions |
| `frontend/src/app/projects/[id]/layout.tsx` | Sidebar nav links to `/projects/[id]/facts` and `/projects/[id]/decisions` |
| `frontend/src/components/Sidebar.tsx` | Project-level nav links to facts/decisions |
| `frontend/src/features/ingest/useIngest.ts` | `useFacts` and `useDecisions` hooks |
| `frontend/src/types/api.ts` | `FactItem` and `DecisionItem` type definitions |
| `frontend/src/app/projects/[id]/search/page.tsx` | Placeholder text mentions "facts, decisions" (no API calls) |
| `frontend/src/app/projects/[id]/settings/page.tsx` | Danger zone text mentions "facts, decisions" (no API calls) |

---

## 6. OpenAPI / Swagger

- **No OpenAPI spec file** exists in the repository.
- FastAPI auto-generates interactive docs at `/docs` and `/redoc` when not in production (`app/main.py:181-182`).
- The ingest endpoints are automatically included in the auto-generated OpenAPI schema since they use FastAPI decorators with proper Pydantic response models.

---

## 7. Reconciliation Table

| # | Backend Path | Method | Frontend Path | Frontend Method | Match? | Required Fix |
|---|-------------|--------|---------------|-----------------|--------|-------------|
| 1 | `/api/v1/ingest/facts` | GET | `/api/v1/ingest/facts` | GET | ✅ **MATCH** | None |
| 2 | `/api/v1/ingest/facts/{fact_id}` | GET | Not called by any page | — | ⚠️ **NO CONSUMER** | Optional: add detail view |
| 3 | `/api/v1/ingest/decisions` | GET | `/api/v1/ingest/decisions` | GET | ✅ **MATCH** | None |
| 4 | `/api/v1/ingest/decisions/{decision_id}` | GET | Not called by any page | — | ⚠️ **NO CONSUMER** | Optional: add detail view |

---

## 8. Schema Mismatch Summary

### Facts — 3 mismatches found

| Issue | Backend | Frontend Page | Frontend Types |
|-------|---------|---------------|----------------|
| **Display field name** | `subject` | Uses `statement` (undefined) | Uses `content` (exists in backend) |
| **Missing fields in page interface** | Has `subject`, `predicate`, `object`, `superseded_by_id`, `status` | Page interface lacks all of these | Types interface lacks `subject`, `predicate`, `object`, `superseded_by_id`, `status` |
| **Field name mismatch** | `source_id` | Not referenced | Uses `source_message_id` (wrong name) |

### Decisions — 1 critical mismatch found

| Issue | Backend | Frontend Page | Frontend Types |
|-------|---------|---------------|----------------|
| **Non-existent field** | No `tags` field | Uses `d.tags` (always undefined, guarded but useless) | Has `tags: string[]` (doesn't exist in backend) |
| **Missing fields** | Has `context`, `authority`, `superseded_by_id`, `status`, `source_id` | Not referenced | Types interface lacks all of these |

---

## 9. Required Fixes

### Fix 1 — Facts page: replace `statement` with `content` (or `subject`)

**File:** `frontend/src/app/projects/[id]/facts/page.tsx`

The local `FactItem` interface uses `statement` which doesn't exist in the backend response. Replace with `content` (or `subject` for the predicate-style display).

**Current (line 9):**
```typescript
interface FactItem {
  id: string;
  statement: string;       // ← WRONG: backend has no "statement"
  predicate: string | null;
  authority: string;       // ← should be number
  confidence: number;
  status: string;
  created_at: string;
}
```

**Should be:**
```typescript
interface FactItem {
  id: string;
  subject: string;
  predicate: string | null;
  object: string;
  content: string;
  confidence: number;
  authority: number;
  temporal_status: string;
  status: string;
  created_at: string;
  updated_at: string;
}
```

And line 46: `f.statement` → `f.content` (or `f.subject`)

### Fix 2 — Facts page: `authority` type

**File:** `frontend/src/app/projects/[id]/facts/page.tsx` line 12

Change `authority: string` to `authority: number` to match backend.

### Fix 3 — DecisionItem types: remove `tags`, add missing fields

**File:** `frontend/src/types/api.ts` lines 72-78

Remove `tags: string[]` and add `context`, `authority`, `superseded_by_id`, `status`, `source_id`.

### Fix 4 — FactItem types: fix `source_message_id`, add missing fields

**File:** `frontend/src/types/api.ts` lines 64-69

Rename `source_message_id` → `source_id` and add `subject`, `predicate`, `object`, `superseded_by_id`, `status`.

### Fix 5 — Decisions page: remove `tags` rendering

**File:** `frontend/src/app/projects/[id]/decisions/page.tsx` lines 52-56

The `d.tags?.length > 0` block will never render anything since `tags` doesn't exist in the backend. Either remove it or await a backend schema change that adds tags.

---

## 10. Gate Results

| Gate | Criteria | Result |
|------|----------|--------|
| **Gate 3** — Backend API paths verified | All 4 endpoints exist at expected paths with correct methods and schemas | ✅ PASS |
| **Gate 4** — Frontend API client verified | URL paths match backend, but **3 schema mismatches** exist between frontend types/pages and backend schemas | ⚠️ CONDITIONAL PASS (paths match, types need fixing) |

**Blocking issues before merge:**
1. Facts page uses non-existent `statement` field → renders undefined text
2. Decisions page references non-existent `tags` field → tags never display
3. `FactItem` type in `types/api.ts` has `source_message_id` instead of `source_id`
