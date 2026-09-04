# PHASE_1R_TYPE_CONTRACT_VERIFICATION.md

## Gate 6 — Type Contract Verification

**Date:** 2026-09-04

---

## Type Safety Audit Results

### `as any` Casts (1 found)

**File:** `frontend/src/app/projects/[id]/sessions/page.tsx:44`
```tsx
{(metaFor(s) as any).source || 'chat'}
```
**Analysis:** `extra_metadata` is typed as `Record<string, unknown>`. Accessing `.source` requires an `as any` cast. Low severity — only affects display text, no data corruption.

### `<any>` Type Assertions (0 found)
None in the codebase. Clean.

### `Record<string, any>` (0 found)
No loose type annotations. Clean.

---

## Type Contract Alignment: Frontend vs Backend

### Verified Type Matches

| Frontend Type | Backend Model | Status |
|---------------|---------------|--------|
| `TokenPair` | `TokenResponse` | OK |
| `UserInfo` | `UserOut` | OK |
| `Project` | `ProjectOut` | OK |
| `MemoryItemOut` | `MemoryOut` | OK |
| `FactItem` | `FactListResponse.item` | OK (minor: uses `statement` vs `content`) |
| `DecisionItem` | `DecisionListResponse.item` | OK |
| `SessionHistory` | inline in sessions.py | OK |
| `ChatStreamEvent` | SSE event shapes | OK |
| `ApiKeyOut` | `ApiKeyOut` | OK |
| `GraphResponse` | `GraphResponse` | OK |

### Minor Type Gap: Facts

**Frontend** (`types/api.ts`):
```ts
export interface FactItem {
  id: string; workspace_id: string; project_id: string | null;
  content: string; source_message_id: string | null;
  temporal_status: string; confidence: number; authority: number;
  created_at: string; updated_at: string;
}
```

**Frontend page** (`facts/page.tsx`) uses its own interface:
```ts
interface FactItem {
  id: string;
  statement: string;      // vs content in types/api.ts
  predicate: string | null;
  authority: string;      // vs number in types/api.ts
  confidence: number;
  status: string;         // vs temporal_status in types/api.ts
  created_at: string;
}
```

**Assessment:** The page-level type has different field names (`statement` vs `content`, `authority` as string vs number). This is a contract drift — either the backend sends different shapes or the page interface is stale. The page renders correctly because it accesses `f.statement`, `f.confidence`, `f.status`, `f.authority` which match the page's local interface, not the shared `types/api.ts` one.

**Recommendation:** Align `FactItem` in `types/api.ts` with the backend response shape.

---

## Inline Fetch vs Typed API Client

Two pages bypass the typed `api.ts` client and use raw `fetch`:

| File | Line | Reason |
|------|------|--------|
| `projects/[id]/chat/page.tsx` | 46 | SSE streaming with ReadableStream |
| `projects/[id]/search/page.tsx` | 34 | Direct fetch (could use apiGet) |

The chat page's inline fetch is acceptable (SSE streaming with ReadableStream requires direct fetch). The search page could use `apiGet` from `api.ts`.

---

## Verdict

**Gate 6 PASS with minor findings:**
1. One `as any` cast (low severity)
2. FactItem type drift between page and shared types (medium — should align)
3. Two inline fetch calls (1 acceptable, 1 could use typed client)
