# FRONTEND_IMPLEMENTATION_BASELINE.md

## Phase 0 — Baseline Forensics

**Date:** 2026-09-05
**Baseline SHA:** `4aa908d5`
**Certifier:** Automated

---

## 1. Git State

| Property | Value |
|----------|-------|
| HEAD SHA | `4aa908d5` |
| Branch | `master` |
| Working tree | Clean (only `tsconfig.tsbuildinfo` modified — gitignored) |
| Untracked | `.next/` build artifacts (gitignored) |

---

## 2. Service Status

| Service | URL | Status |
|---------|-----|--------|
| Backend | http://localhost:8000 | ✅ Running (`{"status":"alive"}`) |
| Frontend | http://localhost:3000 | ✅ Running (Next.js SSR response) |

---

## 3. Test Baselines

### Backend Unit Tests
```
Command: python -m pytest tests/ --tb=short -q
Result: 671 passed in 142.11s
Failures: 0
```

### Frontend TypeScript
```
Command: cd frontend && npx tsc --noEmit
Result: Clean (exit code 0)
Errors: 0
Warnings: 0
```

### Playwright E2E Tests
```
Command: cd frontend && npx playwright@1.63.0 test --reporter=list
Result: 42 passed in 46.2s
Failures: 0

Breakdown:
  api-e2e.spec.ts       14 passed
  auth.spec.ts           7 passed
  dashboard.spec.ts      3 passed
  frontend-journey.spec.ts  4 passed
  golden-journey.spec.ts   14 passed
```

---

## 4. Frontend Route Inventory

| # | Route | Page Component | Status |
|---|-------|---------------|--------|
| 1 | `/` | Redirect to `/dashboard` or `/auth/login` | ✅ |
| 2 | `/auth/login` | LoginPage | ✅ |
| 3 | `/auth/register` | RegisterPage | ✅ |
| 4 | `/dashboard` | DashboardPage | ✅ |
| 5 | `/projects` | ProjectsPage | ✅ |
| 6 | `/projects/[id]` | ProjectLayout (sidebar + content) | ✅ |
| 7 | `/projects/[id]/chat` | ChatPage (SSE streaming) | ✅ |
| 8 | `/projects/[id]/ingest` | IngestPage | ✅ |
| 9 | `/projects/[id]/memory` | MemoryPage | ✅ |
| 10 | `/projects/[id]/facts` | FactsPage | ✅ |
| 11 | `/projects/[id]/decisions` | DecisionsPage | ✅ |
| 12 | `/projects/[id]/timeline` | TimelinePage | ✅ |
| 13 | `/projects/[id]/search` | SearchPage | ✅ |
| 14 | `/projects/[id]/graph` | GraphPage | ✅ |
| 15 | `/projects/[id]/sessions` | SessionsPage | ✅ |
| 16 | `/projects/[id]/sessions/[sessionId]` | SessionDetailPage | ✅ |
| 17 | `/projects/[id]/provenance` | ProvenancePage | ✅ |
| 18 | `/projects/[id]/settings` | ProjectSettingsPage | ✅ |
| 19 | `/settings` | WorkspaceSettingsPage | ✅ |
| 20 | `/settings/api-keys` | ApiKeysPage | ✅ |
| 21 | `/settings/profile` | ProfilePage | ✅ |
| 22 | `/settings/storage` | StoragePage | ✅ |

**Total: 22 routes** (1 redirect + 21 page routes)

---

## 5. API Endpoint Inventory

| Property | Value |
|----------|-------|
| Total backend endpoints | **81** (verified from source) |
| Frontend-consumed endpoints | **~30 unique** |
| Backend-only endpoints | **51** |
| Unused/deprecated | 1 (POST `/api/v1/workspace/members/invitations` — duplicate) |

### Endpoint Breakdown by Router

| Router | Prefix | Endpoints |
|--------|--------|-----------|
| auth | `/auth` | 6 |
| workspace | `/workspace` | 14 |
| projects | `/projects` | 5 |
| sessions | `/sessions` | 6 |
| chat | `/chat` | 2 |
| memory | `/memory` | 6 |
| ingest | `/ingest` | 14 |
| provenance | `/provenance` | 3 |
| dashboard | `/dashboard` | 2 |
| feedback | `/feedback` | 3 |
| api-keys | `/api-keys` | 4 |
| storage | `/storage` | 3 |
| policy | `/policy` | 7 |
| audit | `/audit` | 3 |
| main (direct) | `/health` | 3 |
| **Total** | | **81** |

---

## 6. Frontend API Client Inventory

### lib/api.ts
- `apiGet`, `apiPost`, `apiPatch`, `apiDelete` — authenticated CRUD helpers
- `apiUpload` — multipart upload with progress
- `streamChat` — SSE streaming generator

### Feature Hooks
| Hook | File | API Endpoints Called |
|------|------|---------------------|
| `useAuth` | `hooks/useAuth.tsx` | POST `/auth/login`, `/auth/register`, `/auth/refresh`, `/auth/logout`, `/auth/me` |
| `useProjects` | `features/projects/useProjects.ts` | GET/POST `/projects/`, GET/PATCH/DELETE `/projects/{id}` |
| `useChat` | `features/chat/useChat.ts` | GET `/chat/stream`, POST `/chat/` |
| `useMemory` | `features/memory/useMemory.ts` | GET/POST/DELETE `/memory/`, POST `/memory/search` |
| `useIngest` | `features/ingest/useIngest.ts` | POST `/ingest/upload`, GET `/ingest/sources`, GET `/ingest/facts`, `/ingest/decisions`, `/ingest/graph`, `/ingest/timeline`, `/ingest/jobs` |
| `useSearch` | `features/search/useSearch.ts` | POST `/ingest/search` |
| `useGraph` | `features/graph/useGraph.ts` | GET `/ingest/graph` |
| `useApiKeys` | `features/apiKeys/useApiKeys.ts` | GET/POST/DELETE `/api-keys`, POST `/api-keys/{id}/rotate` |

---

## 7. Known Defects

| # | Defect | Severity | Status |
|---|--------|----------|--------|
| 1 | `useSearch.ts` was calling wrong endpoint path | P2 | **FIXED** (now calls POST `/ingest/search`) |
| 2 | `FactItem.source_message_id` field mismatch | P2 | **FIXED** (now `source_id`) |
| 3 | `FactItem` missing `subject/predicate/object` fields | P2 | **FIXED** (added) |
| 4 | `DecisionItem.tags` non-existent field | P2 | **FIXED** (removed) |
| 5 | `ApiKeyOut.prefix` vs backend `key_prefix` | P3 | **OPEN** (non-breaking, field name mismatch) |
| 6 | No loading/error components shared across pages | P2 | **OPEN** |
| 7 | No design system component library | P2 | **OPEN** |
| 8 | CORS localhost-only (needs prod config) | P1 | **KNOWN** (documented) |
| 9 | Token in localStorage (XSS risk) | P1 | **KNOWN** (documented) |
| 10 | No RBAC on memory CRUD, ingest, sessions, dashboard | P2 | **KNOWN** (documented) |
| 11 | `POST /ingest/` endpoint takes JSON body but path param query for search | P2 | **KNOWN** (inconsistent API design) |
| 12 | Workspace slug collision risk (no unique constraint) | P2 | **KNOWN** (documented) |

---

## 8. Known Warnings

| # | Warning | Notes |
|---|---------|-------|
| 1 | In-memory rate limiter | Resets on restart; use Redis in production |
| 2 | No CSP headers configured in non-production | SecurityHeadersMiddleware sets dev CSP with `unsafe-inline` |
| 3 | `npx playwright` resolves to Python on this host | Must use `npx playwright@1.63.0 test` explicitly |
| 4 | `.next/` artifacts not git-tracked | Build artifacts, gitignored |
| 5 | `tsconfig.tsbuildinfo` tracked but gitignored | Will appear modified after tsc runs |

---

## 9. Browser Availability

```
Browser: Chromium (via Playwright 1.63.0)
Viewport: 1440x900 (default)
Headless: Yes
```

---

## 10. Screenshot Baseline

- 28 screenshots exist in `screenshots/` (captured in Phase 1R-B)
- Screenshot capture script: `screenshot-capture.cjs`
- Format: PNG, viewport 1440x900

---

## 11. Data Limitations

- No seed data in database (fresh state per test)
- Tests create/register/clean up their own data
- Sample vault data for Phase 1R-B not yet created
- No fixture data for visual QA

---

## 12. Build Baseline

| Command | Result |
|---------|--------|
| `cd frontend && npx tsc --noEmit` | ✅ Clean |
| `cd frontend && npm run build` | Not yet run (needs running server for data) |

---

## 13. Regression Baseline

All existing tests are passing. This is the regression floor:

- Backend unit: 671/671
- API E2E: 14/14
- Frontend UI E2E: 28/28
- **Total: 699/699**
