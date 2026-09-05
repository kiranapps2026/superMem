# Phase 1RC — Change History Reconciliation

**Date:** 2026-09-05
**Reconciled From:** `0534efe` (Phase 1R baseline) to `a12c227` (current HEAD)
**Total Commits:** 7 (6 post-baseline + 1 baseline)
**Interpreter:** Gate 1 Change History Reconciliation

---

## Commit-by-Commit Change History

### Commit 1: `fff32b4` — feat(phase-1rb): enterprise frontend/backend integration certification

**Date:** 2026-09-04  
**Author:** Dev  
**Significance:** Major feature commit — the entire Phase 1RB certification work

#### Files Changed (65 files, +7966/-445 lines)

**Backend files modified (4):**
- `app/api/audit.py`
- `app/core/config.py`
- `app/main.py`
- `app/middleware/rate_limit.py`

**New frontend directories:**
- `frontend/src/app/settings/api-keys/` — API key management UI
- `frontend/src/app/settings/profile/` — User profile UI
- `frontend/src/app/projects/[id]/settings/` — Project settings UI
- `frontend/src/components/ui/` — 11 UI components (Badge, Card, ConfirmDialog, EmptyState, ErrorAlert, FileInput, LoadingSpinner, Pagination, Skeleton, index, useClipboard)
- `frontend/src/features/` — 8 feature hooks (apiKeys, chat, graph, ingest, memory, projects, search, sessions)

**New test files:**
- `frontend/e2e/api-e2e.spec.ts` — 305 lines
- `frontend/e2e/auth.spec.ts` — 59 lines
- `frontend/e2e/dashboard.spec.ts` — 35 lines
- `frontend/e2e/frontend-journey.spec.ts` — 102 lines
- `frontend/e2e/golden-journey.spec.ts` — 12 lines (modifications)
- `tests/unit/test_remediation.py` — 238 lines
- `frontend/playwright.config.ts` — 6 lines modified
- `frontend/tsconfig.json` — 5 lines modified
- `frontend/tsconfig.e2e.json` — 15 lines new
- `frontend/test-results/.last-run.json` — 4 lines new
- `frontend/.env.example` — 5 lines new

**Documentation (17 new docs):**
- `docs/PHASE_1R_BASELINE.md` — 35 lines
- `docs/API_CONTRACT_FREEZE.md` — 399 lines
- `docs/API_CONTRACT_GAPS.md` — 138 lines
- `docs/API_DOMAIN_MAP.md` — 248 lines
- `docs/API_ENDPOINT_INVENTORY.md` — 1092 lines
- `docs/API_SSE_CONTRACT.md` — 209 lines
- `docs/BACKEND_FRONTEND_READINESS_CERTIFICATION.md` — 281 lines
- `docs/FRONTEND_API_COVERAGE_MATRIX.md` — 116 lines
- `docs/PHASE_1R_API_CONTRACT_DIFF.md` — 236 lines
- `docs/PHASE_1R_API_ENDPOINT_INVENTORY.md` — 272 lines
- `docs/PHASE_1R_API_USAGE_AUDIT.md` — 127 lines
- `docs/PHASE_1R_FINAL_CERTIFICATION.md` — 236 lines
- `docs/PHASE_1R_FINDINGS.md` — 334 lines
- `docs/PHASE_1R_FRONTEND_INVENTORY.md` — 549 lines
- `docs/PHASE_1R_RELEASE_MANIFEST.md` — 204 lines
- `docs/PHASE_1R_TYPE_CONTRACT_VERIFICATION.md` — 93 lines
- `RELEASE_CERTIFICATION_FINAL.md` — 467 lines (modified)
- `CERTIFICATION/PRODUCTION_CERTIFICATION_REMEDIATED.md` — 487 lines (modified)

**Frontend source modifications:**
- `frontend/src/app/auth/login/page.tsx` — 4 lines
- `frontend/src/app/auth/register/page.tsx` — 19 lines
- `frontend/src/app/layout.tsx` — 11 lines
- `frontend/src/app/projects/[id]/memory/page.tsx` — 11 lines
- `frontend/src/components/ui/useClipboard.ts` — 33 lines (already existed before, modified)
- `frontend/src/types/api.ts` — 57 lines modified
- `frontend/src/hooks/AppShell.tsx` — 47 lines new
- `frontend/src/hooks/AuthRedirect.tsx` — 32 lines new
- `frontend/src/lib/errors.ts` — 99 lines new
- `frontend/src/features/apiKeys/useApiKeys.ts` — 110 lines new
- `frontend/src/features/chat/useChat.ts` — 94 lines new
- `frontend/src/features/graph/useGraph.ts` — 28 lines new
- `frontend/src/features/ingest/useIngest.ts` — 137 lines new
- `frontend/src/features/memory/useMemory.ts` — 113 lines new
- `frontend/src/features/projects/useProjects.ts` — 115 lines new
- `frontend/src/features/search/useSearch.ts` — 31 lines new

#### Backend Impact

**1. Audit prefix fix (`app/api/audit.py`):**
- **Before:** `router = APIRouter(prefix="/api/v1/audit", tags=["audit"])`
- **After:** `router = APIRouter(prefix="/audit", tags=["audit"])`
- **Root cause:** Audit router was defining a double prefix because `app/main.py` already includes it under `api_v1 = APIRouter(prefix="/api/v1")`. The `/api/v1/audit` prefix on the router itself + the `/api/v1` prefix from the parent `api_v1` router resulted in `/api/v1/api/v1/audit`.
- **Fix:** Changed to `/audit` so the full path becomes `/api/v1/audit` via parent router composition.
- **Impact:** Breaking API path change. All clients using `/api/v1/audit/...` or `/api/v1/api/v1/audit/...` must reconcile.

**2. Health/readiness fix (`app/main.py`):**
- **Before:** `from app.db import async_engine` then `async with async_engine.connect()`
- **After:** `from app.db import engine` then `async with engine.connect()`
- **Root cause:** `async_engine` doesn't exist in `app/db.py`; `engine` is the async engine instance. This was causing a `NameError` on `/health/ready` endpoint, always returning 503.
- **Additional change:** Added logging of failure reason: `logger.warning("readiness check failed: %s", exc)`
- **Impact:** `/health/ready` now works correctly. Health checks and load balancer probes that rely on this endpoint will now function properly.

**3. CORS changes (`app/core/config.py`):**
- **Before:** Only stripped `*` in production; dev returned whatever `cors_origins_list` contained.
- **After:** Always strips `*` when `allow_credentials=True`. Production raises `ValueError` if no explicit origins. Dev falls back to `["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"]`.
- **Impact:** Prevents reflected-origin attacks. Dev environments can no longer accidentally expose to arbitrary origins. Production fails fast if `CORS_ORIGINS` is not configured.

**4. Rate limiter E2E bypass (`app/middleware/rate_limit.py`):**
- **Before:** Only bypassed rate limits when `app.state.testing` was True (set in pytest conftest).
- **After:** Added `X-E2E: true` header bypass for non-production environments. External e2e test suites (Playwright) can now pass rate limits.
- **Security gating:** `if settings.environment != "production"` — NEVER active in production.
- **Impact:** Playwright e2e tests can now run without hitting rate limits. No production exposure.

#### Frontend Impact

**New directories and components (new in this commit):**
- 11 UI components in `frontend/src/components/ui/`
- 8 feature hooks in `frontend/src/features/`
- 3 settings pages (api-keys, profile, project settings)
- `AppShell.tsx` and `AuthRedirect.tsx` hooks
- `errors.ts` error handling library
- `playwright.config.ts` and `tsconfig.e2e.json` for e2e testing

**Modified pages:**
- Login and register pages (likely styling/validation improvements)
- Layout page (AppShell integration)
- Memory page (11 lines modified)

**New types/API client changes:**
- `types/api.ts` extended with new response types
- `lib/errors.ts` added for consistent error handling

#### API Impact

**Audit API path change (breaking):**
- Old path: `/api/v1/api/v1/audit/events`, `/api/v1/api/v1/audit/events/{id}`, `/api/v1/api/v1/audit/trace/{req_id}`
- New path: `/api/v1/audit/events`, `/api/v1/audit/events/{id}`, `/api/v1/audit/trace/{req_id}`

**Total endpoints documented:** 97 total, 50 frontend-consumed, 47 unused. API Contract Version 1.0 (frozen).

**New documentation files cover:**
- Full API contract freeze
- API contract gaps
- API domain map
- Full endpoint inventory (1092 lines)
- SSE contract details
- API usage audit

#### Database Impact

No database schema changes in this commit. The audit events are persisted to existing tables via `audit.register_db_sink()` which writes to the `audit_events` table created in migration 010. The `AuditPersistenceMiddleware` in `app/main.py` uses `async_session_factory` to persist events after each request.

#### Security Impact

**Positive changes:**
1. Audit path fix — was exposing `/api/v1/api/v1/audit` (double-prefix) which was a routing anomaly; now cleanly exposed at `/api/v1/audit`.
2. CORS hardened — wildcard origins never allowed with credentials, production requires explicit origin list.
3. Rate limiter bypass gated to non-production only (`settings.environment != "production"`).
4. Health endpoint now works — previously always returned 503 due to NameError.

**No regressions:** All security controls remain intact. RBAC, policy engine, JWT auth, security headers unchanged.

#### Test Impact

**New test suites added:**
- E2E: `api-e2e.spec.ts` (14 tests), `auth.spec.ts` (7 tests), `dashboard.spec.ts` (3 tests), `frontend-journey.spec.ts` (4 tests)
- Unit: `test_remediation.py` (15 tests)
- Modified: `golden-journey.spec.ts`

**Test configuration additions:**
- `playwright.config.ts` — E2E runner config
- `tsconfig.e2e.json` — TypeScript config for e2e tests
- `test-results/.last-run.json` — Test result tracking

---

### Commit 2: `d1ad825` — fix(e2e): golden-journey tests - unique workspace names, correct API paths, JSONL format

**Date:** 2026-09-05  
**Author:** Dev  
**Significance:** Critical E2E test fixes for golden-journey

#### Files Changed
- `frontend/e2e/golden-journey.spec.ts` — 45 insertions, 38 deletions

#### Backend Impact
None. Pure test fix.

#### Frontend Impact
None. Test infrastructure only.

#### API Impact
None. Tests now use correct API paths.

#### Database Impact
None.

#### Security Impact
None.

#### Test Impact

**5 specific fixes applied:**

1. **Unique workspace names:** Replaced static workspace names (`'Golden Workspace'`, `'Auth Workspace'`, etc.) with dynamically generated unique names using `Date.now().toString(36) + Math.random().toString(36).slice(2, 6)`. This prevents test collisions when running multiple test instances concurrently or when previous test data hasn't been cleaned up. Previously, `Date.now()` with `Math.random()` had a subtle collision window where two tests started in the same millisecond could get the same name.

2. **Ingest/jobs path fix:** Changed `/ingest/?project_id=` to `/ingest/jobs?project_id=`. The old path was hitting the ingest root endpoint which likely returns a different response or 404. The correct endpoint for listing ingest jobs is `/api/v1/ingest/jobs`.

3. **Ingest/search method fix:** Changed from `GET /api/v1/ingest/search?project_id=` to `POST /api/v1/ingest/search?query=SwarmVault&limit=20`. The search endpoint expects a POST with query parameters, not a GET with JSON body. Also removed the `project_id` parameter — search operates at the workspace level (scoped by JWT), not project level.

4. **JSONL connector format fix:** Changed `makeJSONLConversation()` from returning a single JSON array string to returning newline-delimited JSON (NDJSON). The connector backend expects newline-delimited format (`JSON.stringify(m).join('\n')`), not a wrapped JSON array. Also renamed `type` field to `role` to match the connector's expected format.

5. **Tenant isolation test fix:** Removed incorrect expectations:
   - Removed: B searching A's data via `/ingest/search?project_id=` (incorrect — search is workspace-scoped, not project-scoped)
   - Removed: B chatting with A's context via `/api/v1/chat/` with A's project_id (incorrect — chat scopes by JWT workspace_id)
   - Added explanatory comments explaining that workspace-scoped operations correctly return the caller's own workspace data, which is the expected behavior — not a cross-tenant leak.

**Impact on test reliability:** These fixes address fundamental correctness issues that would have caused flaky or incorrect test results. The golden journey is the primary integration test validating the full pipeline.

---

### Commit 3: `26d47ca` — fix(frontend): correct API paths for facts and decisions in useIngest hook

**Date:** 2026-09-05  
**Author:** Dev  
**Significance:** Frontend API path correction for facts/decisions endpoints

#### Files Changed
- `frontend/src/features/ingest/useIngest.ts` — 2 insertions, 2 deletions

#### Backend Impact
None. Backend unchanged.

#### Frontend Impact

**Two path corrections in the ingest hook:**

1. **`useFacts` hook:** Changed `/api/v1/facts/` to `/api/v1/ingest/facts`
   - The facts endpoint is mounted under the ingest router at `/api/v1/ingest/facts`
   - The old path `/api/v1/facts/` would return 404

2. **`useDecisions` hook:** Changed `/api/v1/decisions/` to `/api/v1/ingest/decisions`
   - The decisions endpoint is mounted under the ingest router at `/api/v1/ingest/decisions`
   - The old path `/api/v1/decisions/` would return 404

**Root cause:** When the backend ingest API was structured, facts and decisions were placed under the `/ingest` prefix (alongside `/ingest/upload`, `/ingest/search`, `/ingest/jobs`, `/ingest/sources`). The frontend hook was incorrectly using standalone paths.

**Impact:** These hooks would have been returning 404 errors. Any page using `useFacts()` or `useDecisions()` (e.g., the memory page, ingest page) would show "Failed to load facts/decisions" errors.

#### API Impact
None. API paths unchanged. This is a frontend-only correction.

#### Database Impact
None.

#### Security Impact
None.

#### Test Impact
No new tests added. The E2E golden journey tests in `d1ad825` test the API paths via direct API calls, not through these hooks. Unit tests for these hooks would need to be added to verify the fix.

---

### Commit 4: `c02ee4c` — fix(frontend): remove 'as any' cast in sessions page, use proper typing

**Date:** 2026-09-05  
**Author:** Dev  
**Significance:** TypeScript type safety improvement

#### Files Changed
- `frontend/src/app/projects/[id]/sessions/page.tsx` — 1 insertion, 1 deletion

#### Backend Impact
None.

#### Frontend Impact

**Single line change in sessions page:**

- **Before:** `(metaFor(s) as any).source`
- **After:** `(metaFor(s) as Record<string, unknown> | undefined)?.['source']`

**Impact:** Replaces unsafe `as any` cast with a properly typed `Record<string, unknown> | undefined` access. This improves TypeScript strictness and prevents silent type errors. The optional chaining (`?.`) also adds null-safety.

**Type system improvement:** Part of the broader Phase 1RB goal of removing `as any` casts and establishing proper TypeScript contracts between frontend and backend.

#### API Impact
None.

#### Database Impact
None.

#### Security Impact
None.

#### Test Impact
None.

---

### Commit 5: `bfc85d0` — docs(phase-1rb): add baseline and endpoint coverage decision

**Date:** 2026-09-05  
**Author:** Dev  
**Significance:** Phase 1RB baseline documentation

#### Files Changed
- `docs/PHASE_1RB_BASELINE.md` — 116 lines new
- `docs/PHASE_1RB_ENDPOINT_COVERAGE_DECISION.md` — 143 lines new

#### Backend Impact
None. Documentation only.

#### Frontend Impact
None.

#### API Impact
None.

#### Database Impact
None.

#### Security Impact
None.

#### Test Impact
None.

#### Documentation Content

**PHASE_1RB_BASELINE.md:**
- Freezes the Phase 1RB baseline at SHA `fff32b4`
- Documents repository info, parent commit (`0534efe`), API Contract Version 1.0
- Lists all modified files since parent
- Documents test suite expectations (671 unit + 15 remediation + 28 E2E)
- Documents API contract baseline (97 endpoints, 50 frontend-consumed, 47 unused)
- Documents security posture baseline
- Documents previous Phase 1R claims for verification

**PHASE_1RB_ENDPOINT_COVERAGE_DECISION.md:**
- Documents the decision on endpoint coverage approach
- Likely addresses which of the 47 unused endpoints should be implemented, deprecated, or documented as intentional gaps

---

### Commit 6: `d0bf109` — chore: add .gitignore for build artifacts and test results

**Date:** 2026-09-05  
**Author:** Dev  
**Significance:** Repository hygiene — comprehensive .gitignore and certification docs

#### Files Changed
- `.gitignore` — 37 lines modified
- `docs/PHASE_1RB_E2E_CERTIFICATION.md` — 92 lines new
- `docs/PHASE_1RB_FINAL_CERTIFICATION.md` — 91 lines new
- `docs/PHASE_1RB_RELEASE_MANIFEST.md` — 128 lines new
- `docs/PHASE_1RB_SECURITY_CERTIFICATION.md` — 79 lines new

#### .gitignore Changes

**Added sections:**
1. **Dependencies:** `node_modules/`, `.venv/`, `venv/`, `env/`
2. **Build outputs:** `.next/`, `out/`, `dist/`, `build/`
3. **Test artifacts:** `frontend/test-results/`, `frontend/playwright-report/`, `frontend/tsconfig.tsbuildinfo`
4. **IDE:** `.idea/`, `.vscode/`, `*.swp`, `*.swo`
5. **OS:** `Thumbs.db`, `.DS_Store`
6. **Environment:** `.env`, `.env.local`, `.env.*.local`
7. **Removed:** `*.egg-info/`, `.pytest_cache/`, `node_modules/` (duplicate), `*.db`, `storage/` (moved to next commit)

**Impact:** Prevents committing build artifacts, IDE configs, test results, and environment files. The `.next/`, `dist/`, `build/` entries prevent committing compiled frontend assets.

#### Documentation Impact

Four new Phase 1RB certification documents:
- **E2E Certification:** Documents E2E test results and procedures
- **Final Certification:** Overall Phase 1RB certification summary
- **Release Manifest:** Release artifact inventory
- **Security Certification:** Security control verification

---

### Commit 7: `a12c227` — chore: update .gitignore for storage runtime data

**Date:** 2026-09-05  
**Author:** Dev  
**Significance:** Final .gitignore fix — add storage directory

#### Files Changed
- `.gitignore` — 3 insertions

#### .gitignore Change

**Added:** `storage/` under a new "Runtime data" section.

**Impact:** The `storage/` directory contains runtime data (uploaded files, processed content, etc.). This was in the original `.gitignore` from the 0534efe commit but got lost in the restructuring in `d0bf109`. This commit restores it.

**Root cause:** The `d0bf109` commit rewrote the `.gitignore` with a more structured format but accidentally omitted `storage/`. This could have led to runtime data (potentially large files or sensitive data) being accidentally committed.

---

## Cross-Cutting Concerns

### Audit Prefix Changes

| Commit | Change | Path Before | Path After |
|--------|--------|-------------|------------|
| `fff32b4` | Fixed double-prefix | `/api/v1/api/v1/audit/...` | `/api/v1/audit/...` |

**Root cause:** The audit router defined its own `/api/v1` prefix, but `app/main.py` includes it under an `api_v1` router that already has the `/api/v1` prefix. This created a double prefix.

**Affected endpoints:**
- `GET /api/v1/audit/events` (was `/api/v1/api/v1/audit/events`)
- `GET /api/v1/audit/events/{id}` (was `/api/v1/api/v1/audit/events/{id}`)
- `GET /api/v1/audit/trace/{req_id}` (was `/api/v1/api/v1/audit/trace/{req_id}`)

### CORS Changes

| Commit | Aspect | Before | After |
|--------|--------|--------|-------|
| `fff32b4` | Wildcard handling | Stripped `*` only in production | Always strips `*` when credentials enabled |
| `fff32b4` | Production enforcement | Returned empty list if no origins | Raises `ValueError` — fails fast |
| `fff32b4` | Dev fallback | Whatever was in `cors_origins_list` | Localhost variants only |

### Rate Limiter Changes

| Commit | Aspect | Before | After |
|--------|--------|--------|-------|
| `fff32b4` | Test bypass | `app.state.testing` only | Added `X-E2E: true` header bypass for non-production |
| `fff32b4` | Production gating | N/A | Explicit `settings.environment != "production"` guard |

### Health/Readiness Changes

| Commit | Aspect | Before | After |
|--------|--------|--------|-------|
| `fff32b4` | Import | `async_engine` (non-existent) | `engine` (correct) |
| `fff32b4` | Error logging | Silent 503 | Logs warning with exception details |

### Facts/Decisions Path Changes

| Commit | Aspect | Before | After |
|--------|--------|--------|-------|
| `26d47ca` | Facts path | `/api/v1/facts/` | `/api/v1/ingest/facts` |
| `26d47ca` | Decisions path | `/api/v1/decisions/` | `/api/v1/ingest/decisions` |

### SSE Changes

No SSE changes in this range. The SSE contract is documented in `docs/API_SSE_CONTRACT.md` (added in `fff32b4`) but no implementation changes.

### Test Fixture Handling

| Commit | Change |
|--------|--------|
| `fff32b4` | Added `tests/unit/test_remediation.py` (15 tests) |
| `fff32b4` | Added `frontend/playwright.config.ts`, `tsconfig.e2e.json`, `test-results/.last-run.json` |
| `d1ad825` | Fixed golden-journey fixture issues: unique workspace names, correct JSONL format, correct API paths |

### Database Initialization

No database initialization changes in this range. The `app/main.py` `lifespan()` function calls `init_db()` and `audit.register_db_sink()` on startup — both existed before and were unchanged. The audit `register_db_sink()` was moved from inline code to a method call in `fff32b4`.

---

## Summary Table

| Commit | Type | Files | Backend | Frontend | API | Database | Security | Test |
|--------|------|-------|---------|----------|-----|----------|----------|------|
| `fff32b4` | feat | 65 (+7966/-445) | ✅ | ✅ | ✅ | - | ✅ | ✅ |
| `d1ad825` | fix(e2e) | 1 (+45/-38) | - | - | - | - | - | ✅ |
| `26d47ca` | fix(frontend) | 1 (+2/-2) | - | ✅ | ✅ | - | - | - |
| `c02ee4c` | fix(frontend) | 1 (+1/-1) | - | ✅ | - | - | - | - |
| `bfc85d0` | docs | 2 (new) | - | - | - | - | - | - |
| `d0bf109` | chore+docs | 5 | - | - | - | - | - | - |
| `a12c227` | chore | 1 (+3) | - | - | - | - | - | - |

---

## Open Items and Risks

1. **Audit API path migration:** Any external clients (documentation, SDKs, integrations) referencing the old double-prefix path `/api/v1/api/v1/audit` need updating. The API contract documentation in `fff32b4` should already reflect this, but consumers outside this repo may not have been updated.

2. **Facts/Decisions paths:** The `26d47ca` fix in `useIngest.ts` is correct for the current backend, but these paths are not visible in the golden-journey E2E tests (which don't exercise the facts/decisions UI hooks directly). Manual verification recommended.

3. **Tenant isolation test correction (`d1ad825`):** The removed test assertions for B searching A's data and B chatting with A's context were actually incorrect tests — the behavior they tested was correct (workspace-scoped operations return the caller's own data). However, this means there is no explicit E2E test verifying cross-tenant isolation at the search and chat level. This should be covered by unit tests in `test_security_matrix.py`.

4. **Rate limiter in-memory state:** The `_RateLimiter` uses in-memory state (`defaultdict(list)`). This is not shared across multiple worker processes. In production with multiple workers, rate limiting will be per-worker, not global. The doc comment acknowledges this ("Production should replace with Redis-backed implementation").

5. **47 unused endpoints:** `PHASE_1RB_ENDPOINT_COVERAGE_DECISION.md` documents the decision, but the unused endpoints remain in the codebase. These should either be implemented, documented as intentional, or removed to reduce attack surface.

6. **`storage/` directory:** The `a12c227` commit re-adds `storage/` to `.gitignore`. This directory contains runtime data. The `.gitignore` had lost this entry in the `d0bf109` rewrite — any files that were staged but not committed during that window could have been accidentally committed if not caught.

7. **`CERTIFICATION/` directory duplicates:** Both `0534efe` and `fff32b4` created certification documents. There are now `CERTIFICATION/PRODUCTION_CERTIFICATION.md` (from 0534efe) and `RELEASE_CERTIFICATION_FINAL.md` (from fff32b4) plus `docs/PHASE_1R_FINAL_CERTIFICATION.md`. These may contain overlapping or conflicting information.

---

## Recommendations

1. **Add E2E test coverage for facts/decisions hooks** — the golden journey tests verify API paths directly but don't exercise the frontend hooks.
2. **Add cross-tenant E2E test** — verify tenant A cannot access tenant B's search results or chat context via the UI hooks.
3. **Review 47 unused endpoints** — decide on implement/deprecate/remove for each.
4. **Consolidate certification documents** — resolve overlap between `CERTIFICATION/` and `docs/` directories.
5. **Add Redis rate limiter** for production deployment to ensure consistent rate limiting across workers.

---

*End of Phase 1RC Change History Reconciliation*
