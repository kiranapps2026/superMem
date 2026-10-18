# SwarmVault WebApp — API Contract Gaps
**Release:** `0534efe426e42f9c03f1622dd792f052647038cc`
**Purpose:** Documents every gap preventing a detachable frontend from building the complete SwarmVault experience without guessing backend behavior.

---

## Summary

| Severity | Count | Frontend Blocking? |
|----------|-------|-------------------|
| P0 | 0 | No |
| P1 | 1 | Partially |
| P2 | 6 | No (workarounds exist) |
| P3 | 3 | No |
| **Total** | **10** | |

**Verdict: Frontend CAN be built.** No P0 gaps exist. One P1 gap (SSE RBAC) is a security inconsistency, not a missing feature. All P2/P3 gaps have frontend workarounds.

---

## Detailed Gap Register

### GAP-001: No RBAC on SSE chat endpoint
- **Severity:** P1
- **Category:** Authorization inconsistency
- **Endpoints affected:** `POST /api/v1/chat/stream`
- **Consistency:** `POST /api/v1/chat/` requires `viewer` role. `POST /api/v1/chat/stream` requires only JWT authentication.
- **Frontend impact:** A viewer-role user can use the non-streaming endpoint but NOT the streaming endpoint (if RBAC were enforced consistently). Currently, streaming works for all authenticated users. Frontend developers may not discover this inconsistency without reading backend code.
- **Workaround:** Use non-streaming endpoint for role-restricted features.
- **Root cause:** `stream_chat` handler in `app/api/chat.py` only uses `TenantContext`, does not call `require_min_role("viewer")`.
- **Recommendation:** Add `require_min_role("viewer")` to `POST /chat/stream` for consistency.
- **Backend change required:** Yes (1-line addition)

### GAP-002: Audit endpoints at wrong path (double prefix)
- **Severity:** P2
- **Category:** Path defect
- **Endpoints affected:** All `/api/v1/api/v1/audit/` endpoints (3 endpoints)
- **Consistency:** All other routers use `prefix="/xxx"` and are included under the parent `/api/v1` prefix, yielding `/api/v1/xxx`. The audit router declares `prefix="/api/v1/audit"` internally, yielding `/api/v1/api/v1/audit/...`.
- **Frontend impact:** Frontend must use the wrong-looking path `/api/v1/api/v1/audit/...` until the backend fixes the prefix. Confusing for frontend developers who see the double prefix.
- **Workaround:** Use the double-prefix path. Document it in the API contract.
- **Root cause:** `app/api/audit.py` line 35: `prefix="/api/v1/audit"` instead of `prefix="/audit"`.
- **Recommendation:** Change audit router prefix to `"/audit"`.
- **Backend change required:** Yes (1-line fix)

### GAP-003: Memory list has no total count
- **Severity:** P2
- **Category:** Pagination inconsistency
- **Endpoints affected:** `GET /api/v1/memory/`
- **Consistency:** Most list endpoints (facts, decisions, timeline, sources, feedback, jobs) return `{"items": [], "total": N}`. Memory list returns `[]` directly with no total.
- **Frontend impact:** Cannot display "Showing X of Y memories". Cannot implement proper pagination with page numbers.
- **Workaround:** Use offset-based pagination and show only the fetched count. Don't show total.
- **Root cause:** `list_memories` handler in `app/api/memory.py` returns `result.scalars().all()` directly, not wrapped in a pagination envelope.
- **Recommendation:** Wrap memory list in `{"items": [], "total": N}` envelope for consistency.
- **Backend change required:** Yes (response wrapper)

### GAP-004: No total count on sessions list
- **Severity:** P2
- **Category:** Pagination inconsistency
- **Endpoints affected:** `GET /api/v1/sessions/`
- **Consistency:** Same as GAP-003 — sessions list returns `SessionOut[]` directly with no total.
- **Frontend impact:** Cannot display total session count or proper pagination.
- **Workaround:** Same as GAP-003.
- **Root cause:** Same pattern as GAP-003.
- **Recommendation:** Wrap in pagination envelope.

### GAP-005: No total count on provenance list
- **Severity:** P2
- **Category:** Pagination inconsistency
- **Endpoints affected:** `GET /api/v1/provenance/`
- **Consistency:** Same as GAP-003.
- **Frontend impact:** Cannot paginate provenance records.
- **Workaround:** Same as GAP-003.
- **Root cause:** Same pattern as GAP-003.

### GAP-006: No file list endpoint in storage
- **Severity:** P2
- **Category:** Missing endpoint
- **Endpoints affected:** Storage domain
- **Current endpoints:** Upload (`POST`), get info (`GET /storage/{key}`), delete (`DELETE`). No `GET /storage/` to list all files.
- **Frontend impact:** Cannot display a file browser/gallery for uploaded files. Frontend must track file keys locally from upload responses.
- **Workaround:** Maintain a local list of uploaded file keys. Display using stored keys + upload response data.
- **Root cause:** No list endpoint implemented.
- **Recommendation:** Add `GET /api/v1/storage/` returning `FileListResponse`.
- **Backend change required:** Yes (new endpoint)

### GAP-007: Untyped workspace list endpoints
- **Severity:** P3
- **Category:** Undocumented response schema
- **Endpoints affected:** `GET /api/v1/workspace/workspaces/all`, `GET /api/v1/workspace/workspaces/available`
- **Consistency:** Return `list[dict]` — no Pydantic schema defined.
- **Frontend impact:** Frontend must guess the fields in the response dict.
- **Workaround:** Inspect actual response data and use defensively.
- **Root cause:** Handlers return raw dicts instead of typed schemas.
- **Recommendation:** Define `WorkspaceSummary` schema and use it in responses.

### GAP-008: No SSE cancel token
- **Severity:** P3
- **Category:** Missing lifecycle feature
- **Endpoints affected:** `POST /api/v1/chat/stream`
- **Consistency:** No server-side cancel mechanism. Client must use `AbortController`.
- **Frontend impact:** Standard pattern (AbortController), but not documented in the contract.
- **Workaround:** Use `AbortController` with `fetch()`.
- **Root cause:** No cancel endpoint implemented.
- **Recommendation:** Document AbortController usage in SSE contract (already done in `API_SSE_CONTRACT.md`).

### GAP-009: Inconsistent pagination metadata
- **Severity:** P3
- **Category:** Pagination inconsistency
- **Endpoints affected:** Multiple
- **Consistency:** Some endpoints return `{"items": [], "total": N}`, others return `[]` directly, others return `{"items": [], "total": N, "limit": M, "offset": O}`. No cursor-based pagination anywhere.
- **Frontend impact:** Frontend must handle multiple pagination patterns.
- **Workaround:** Check response shape at runtime and adapt.
- **Root cause:** Different developers implemented pagination differently across routers.
- **Recommendation:** Standardize on `{"items": [], "total": N, "limit": M, "offset": O}` envelope for all list endpoints.

### GAP-010: SSE stream error events may be missed on abrupt disconnect
- **Severity:** P3
- **Category:** Lifecycle edge case
- **Endpoints affected:** `POST /api/v1/chat/stream`
- **Consistency:** If the server crashes mid-stream, the client receives no `error` event — just a connection drop.
- **Frontend impact:** Frontend must handle both explicit error events AND connection drops.
- **Workaround:** Handle `reader.read()` returning `done` without a `done` or `error` event as an unexpected disconnect.
- **Root cause:** No graceful shutdown handler for SSE connections.
- **Recommendation:** Document in SSE contract (already done in `API_SSE_CONTRACT.md`).

---

## What is NOT a Gap

| Item | Why Not a Gap |
|------|---------------|
| No WebSocket endpoint | SSE covers real-time chat. WebSocket not needed. |
| No batch endpoints | Frontend can parallelize individual requests. |
| No field selection (`?fields=`) | Frontend receives full objects; no need for sparse fieldsets. |
| No optimistic concurrency | No concurrent editing use case identified. |
| No push notifications | Backend does not push; frontend polls or uses SSE for chat only. |
| No file download endpoint | Storage API returns file info + URL. Frontend can construct download link. |
| No sorting parameters | All list endpoints sort by `created_at desc`. If sorting is needed, it's a future feature. |
