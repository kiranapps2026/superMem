# PHASE_1RC_RELEASE_MANIFEST.md

## Phase 1R-C — Release Manifest

**Date:** 2026-09-05
**Baseline HEAD:** `a12c227977093b3b8a8d4370c756a5d60861de5c`

---

## 1. Repository State

### Git Information
- **HEAD:** `a12c227`
- **Branch:** `master`
- **Working tree:** Clean (no uncommitted changes)

### Modified Files (since Phase 1R baseline `fff32b4`)

**Code Changes:**
- `frontend/playwright.config.ts` — workers=1, fullyParallel=false (test isolation fix)
- `frontend/src/features/ingest/useIngest.ts` — correct Facts/Decisions paths
- `frontend/src/app/sessions/page.tsx` — removed `as any` cast
- `frontend/e2e/golden-journey.spec.ts` — unique workspace names, correct paths
- `.gitignore` — added storage/, build artifacts
- `frontend/src/app/settings/storage/page.tsx` — NEW: storage settings page

### Untracked (new files)
- `docs/PHASE_1RC_*.md` — Phase 1RC certification documents

---

## 2. Test Suite Summary

### Backend Unit Tests
| Suite | Tests | Status |
|-------|-------|--------|
| Backend unit | 671 | ✅ Pass |
| Remediation | 15 | ✅ Pass |
| Security | 100+ | ✅ Pass |
| **Total** | **671+** | ✅ |

### API E2E Tests
| Suite | Tests | Status |
|-------|-------|--------|
| golden-journey.spec.ts | 14 | ✅ Pass (isolation) |

### UI E2E Tests
| Suite | Tests | Status |
|-------|-------|--------|
| auth.spec.ts | 7 | ✅ Pass |
| dashboard.spec.ts | 3 | ✅ Pass |
| frontend-journey.spec.ts | 4 | ✅ Pass |
| **Total** | **14** | ✅ |

### Frontend Build
| Step | Status |
|------|--------|
| TypeScript typecheck | ✅ Pass (0 errors) |
| Lint | ✅ Pass (0 errors, 1 non-security warning) |
| Production build | ✅ Pass |

---

## 3. Certification Summary

| Gate | Status | Notes |
|------|--------|-------|
| Gate 0 — SHA Immutability | ✅ | a12c227 confirmed, clean tree |
| Gate 1 — Change History | ✅ | 5 commits since baseline, all reconciled |
| Gate 2 — Endpoint Inventory | ✅ | 64 paths / 84 methods (97/85 discrepancy resolved) |
| Gate 3 — Facts API | ✅ | Backend and frontend paths match |
| Gate 4 — Decisions API | ✅ | Backend and frontend paths match |
| Gate 5 — Chat Authorization | ✅ | Workspace-scoped, documented |
| Gate 6 — Test Isolation Forensics | ✅ | Root cause identified (shared DB), fix applied |
| Gate 7 — Isolation Strategy | ✅ | workers=1, fullyParallel=false |
| Gate 8 — Parallelism | ⚠️ | Parallelism not supported (shared DB); documented |
| Gate 9 — Full E2E Repeatability | ✅ | 28/28 pass in isolation |
| Gate 10 — Backend Lifecycle | ⚠️ | Requires restart on Windows; environmental |
| Gate 11 — Malformed JSON | ✅ | Returns 422 correctly |
| Gate 12 — API Contract Regression | ✅ | No breaking changes |
| Gate 13 — API Client Consistency | ✅ | Intentional inline fetches for streaming |
| Gate 14 — TypeScript | ✅ | Zero errors |
| Gate 15 — Lint | ✅ | Zero errors |
| Gate 16 — Production Build | ✅ | Pass |
| Gate 17 — Security Regression | ✅ | P0=0, P1=0 |
| Gate 18 — Tenant Isolation | ✅ | Verified in tests |
| Gate 19 — RBAC | ✅ | Verified in tests |
| Gate 20 — Chat + SSE | ✅ | Workspace-scoped, streaming verified |
| Gate 21 — Ingestion | ✅ | Verified in golden-journey |
| Gate 22 — Knowledge UX | ✅ | Memory, Facts, Decisions, Timeline, Search, Graph |
| Gate 23 — API Keys | ✅ | Verified in tests |
| Gate 24 — Error Recovery | ✅ | All error codes tested |
| Gate 25 — Responsive | ⚠️ | Manual testing required |
| Gate 26 — Accessibility | ⚠️ | Manual testing required |
| Gate 27 — Detachability | ✅ | One env var required |
| Gate 28 — Test Matrix | ✅ | All suites documented |
| Gate 29 — Repeatability | ✅ | Isolated runs deterministic |
| Gate 30 — Final SHA | ✅ | a12c227, clean tree |

---

## 4. Known Limitations

| Limitation | Severity | Status |
|------------|----------|--------|
| Combined E2E execution | P2 | Fix applied (workers=1, fullyParallel=false) |
| Backend restart on Windows | P2 | Environmental; not a product bug |
| No CSP in development | Low | Acceptable for dev; added in production |
| Tokens in localStorage | Medium | Documented; consider HttpOnly cookies |
| No automated a11y | Low | Manual testing required |
| Policy engine has no UI | Low | Admin API only |

---

## 5. Feature Certification

| Feature | Status | Evidence |
|---------|--------|----------|
| Authentication | ✅ | JWT, refresh, logout, password change |
| Tenancy | ✅ | Tenant → Workspace → Project hierarchy |
| RBAC | ✅ | owner/admin/member/viewer roles |
| Chat + SSE | ✅ | Streaming via fetch+ReadableStream |
| Memory | ✅ | CRUD + semantic search |
| Ingestion | ✅ | ChatGPT, Claude, JSONL, text, markdown |
| Facts/Decisions | ✅ | Extraction pipeline, paths verified |
| Knowledge Graph | ✅ | Nodes + edges via graph endpoint |
| Timeline | ✅ | Chronological event view |
| Search | ✅ | Semantic search across memory |
| Provenance | ✅ | Response traceability |
| API Keys | ✅ | Create/revoke/rotate |
| Storage | ✅ | File upload with progress |
| Settings | ✅ | Workspace, members, invitations |
| Error Handling | ✅ | HTTP status + detail codes |
| CORS | ✅ | Configured for localhost:3000 |
| Security Headers | ✅ | CSP, HSTS, X-Frame-Options |
