# E2E Test Inventory

**Date:** 2026-09-09
**Test Runner:** Playwright 1.63.0 (Chromium, 1 worker)
**Frontend:** http://localhost:3000
**Backend:** http://localhost:8000

---

## Classification Definitions

| Class | Definition |
|-------|-----------|
| **CERTIFICATION** | Verifies a specific vertical slice works end-to-end. Added or modified during slice certification. |
| **REGRESSION** | Protects an already-certified slice from breaking. Ensures existing behavior is preserved. |
| **DIAGNOSTIC** | Developer/debug aid. Captures console state, DOM state, or network state for investigation. Not part of certification baseline. |
| **DEBUG** | Temporary investigation test. Not part of certification baseline. |

---

## Official Certification Baseline: 103/103 PASS

### CERTIFICATION Tests (103)

#### search-chat-certification.spec.ts (19)

| # | describe / test | Purpose |
|---|-----------------|---------|
| 1 | Search Browser Certification › Search page renders heading and input | Page loads with search UI |
| 2 | Search Browser Certification › Search input has correct placeholder | Placeholder text present |
| 3 | Search Browser Certification › Search filter select is visible | memory_type filter visible |
| 4 | Search Browser Certification › Search submit button is visible | Submit button present |
| 5 | Search Browser Certification › Search API contract: POST /api/v1/ingest/search returns 200 | POST contract, params: query, limit, project_id |
| 6 | Search Browser Certification › Search with memory_type filter in query params | Filter param transmitted correctly |
| 7 | Search Browser Certification › Search empty project returns empty results | Empty state handling |
| 8 | Search Browser Certification › Search rejects without auth | 401 without token |
| 9 | Search Browser Certification › Search console clean on empty results page | No console errors |
| 10 | Search Browser Certification › Search responsive at 768px | Responsive layout |
| 11 | Search Browser Certification › Search page has error state component | ErrorAlert component present |
| 12 | Chat Browser Certification › Chat page renders heading and textarea | Page loads with chat UI |
| 13 | Chat Browser Certification › Chat page shows empty state | Empty state rendered |
| 14 | Chat Browser Certification › Chat API contract: POST /api/v1/chat/stream returns SSE | SSE stream contract |
| 15 | Chat Browser Certification › Chat rejects without auth | 401 without token |
| 16 | Chat Browser Certification › Chat sends message and sees response | Full send/receive workflow |
| 17 | Chat Browser Certification › Chat console clean on page load | No console errors |
| 18 | Chat Browser Certification › Chat responsive at 768px | Responsive layout |
| 19 | Chat Browser Certification › Chat page renders with evidence button support | Evidence modal support |

#### remaining-contracts.spec.ts (20)

| # | describe / test | Purpose |
|---|-----------------|---------|
| 20 | Timeline Network Contract › Timeline API: GET /api/v1/ingest/timeline returns 200 | API contract: query params, `{ items, total }` response |
| 21 | Timeline Network Contract › Timeline page renders heading | Browser render: heading visible |
| 22 | Timeline Network Contract › Timeline page has empty state | Browser render: empty state |
| 23 | Timeline Network Contract › Timeline vertical slice — items sorted descending | Backend: chronological ordering |
| 24 | Timeline Network Contract › Timeline vertical slice — mixed types | Backend: fact/decision/memory in timeline |
| 25 | Sessions Network Contract › Sessions API: GET /api/v1/sessions/ returns 200 | API contract: list endpoint |
| 26 | Sessions Network Contract › Sessions page renders heading | Browser render: heading visible |
| 27 | Sessions Network Contract › Sessions page has empty state | Browser render: empty state |
| 28 | Sessions Network Contract › Sessions vertical slice — correct schema | Backend: id, title, created_at, updated_at |
| 29 | Sessions Network Contract › Sessions vertical slice — empty project empty array | Empty state via API |
| 30 | Graph Network Contract › Graph API: GET /api/v1/ingest/graph returns 200 | API contract: `{ nodes, edges }` |
| 31 | Graph Network Contract › Graph page renders heading | Browser render: heading visible |
| 32 | Graph Network Contract › Graph page has empty state | Browser render: empty state |
| 33 | Graph Network Contract › Graph vertical slice — nodes/edges schema | Backend: node fields verified |
| 34 | Graph Network Contract › Graph vertical slice — edges reference valid nodes | Backend: referential integrity |
| 35 | Provenance Network Contract › Provenance API: GET /api/v1/provenance/ returns 200 | API contract: array response |
| 36 | Provenance Network Contract › Provenance page renders heading | Browser render: heading visible |
| 37 | Provenance Network Contract › Provenance page has empty state | Browser render: empty state |
| 38 | Provenance Network Contract › Provenance vertical slice — correct schema | Backend: model, provider, latency, tokens |
| 39 | Provenance Network Contract › Provenance vertical slice — requires auth | Security: 401 without token |

#### ui-certification.spec.ts (22)

| # | describe / test | Purpose |
|---|-----------------|---------|
| 40 | UI Browser Certification - Authenticated › Dashboard renders with stats | Browser: dashboard stats visible |
| 41 | UI Browser Certification - Authenticated › Dashboard creates project | Browser: New Project form works |
| 42 | UI Browser Certification - Authenticated › Projects page lists projects | Browser: project list renders |
| 43 | UI Browser Certification - Authenticated › Chat page renders with empty state | Browser: chat empty state |
| 44 | UI Browser Certification - Authenticated › Chat sends message and receives response | Browser: full chat workflow |
| 45 | UI Browser Certification - Authenticated › Search page renders | Browser: search page renders |
| 46 | UI Browser Certification - Authenticated › Memory page renders | Browser: memory page renders |
| 47 | UI Browser Certification - Authenticated › Settings page renders | Browser: settings page renders |
| 48 | UI Browser Certification - Authenticated › Ingest page renders with upload form | Browser: ingest page renders |
| 49 | UI Browser Certification - Authenticated › Facts page renders | Browser: facts page renders |
| 50 | UI Browser Certification - Authenticated › Decisions page renders | Browser: decisions page renders |
| 51 | Search Network Contract › Search sends POST /api/v1/ingest/search | Network: POST with query+limit |
| 52 | Memory Network Contract › Memory loads via GET /api/v1/memory/ | Network: GET with project_id |
| 53 | Memory Network Contract › Memory page has filter and structure | Browser: filter UI present |
| 54 | Memory Network Contract › Memory vertical slice — API returns correct schema | Backend: memory fields verified |
| 55 | Memory Network Contract › Memory vertical slice — filter by memory_type | Backend: filter works |
| 56 | Memory Network Contract › Memory vertical slice — filter by temporal_status | Backend: temporal filter works |
| 57 | Memory Network Contract › Memory vertical slice — page renders empty state | Browser: empty state on fresh project |
| 58 | Facts Network Contract › Facts loads via GET /api/v1/ingest/facts | Network: GET with project_id |
| 59 | Facts Network Contract › Facts page has empty state and s-p-o display | Browser: subject-predicate-object |
| 60 | Decisions Network Contract › Decisions loads via GET /api/v1/ingest/decisions | Network: GET with project_id |
| 61 | Decisions Network Contract › Decisions page has empty state | Browser: empty state |

#### frontend-journey.spec.ts (4)

| # | test | Purpose |
|---|------|---------|
| 62 | full journey: dashboard → create project → navigate pages | End-to-end UI flow |
| 63 | sidebar navigation is present and links work | Navigation completeness |
| 64 | logout redirects to login | Auth flow |
| 65 | unauthenticated access redirects to login | Auth guard |

#### auth.spec.ts (7)

| # | test | Purpose |
|---|------|---------|
| 66 | login page renders with form elements | Auth page render |
| 67 | register page link is accessible | Navigation between auth pages |
| 68 | login with invalid credentials shows error | Error handling |
| 69 | login with empty fields validates | Form validation |
| 70 | register page renders | Auth page render |
| 71 | register with mismatched passwords shows error | Error handling |
| 72 | login link on register page works | Navigation |

#### golden-journey.spec.ts (14)

| # | test | Purpose |
|---|------|---------|
| 73 | register → login → workspace → project → upload → ingestion → search → chat → evidence → provenance | Full golden path |
| 74 | register creates new user | Auth |
| 75 | login returns tokens | Auth |
| 76 | login rejects wrong password | Auth security |
| 77 | protected endpoint rejects missing token | Auth security |
| 78 | tenant A and B are isolated | Multi-tenancy |
| 79 | ChatGPT connector normalizes correctly | Connector |
| 80 | Claude connector normalizes correctly | Connector |
| 81 | JSONL connector normalizes correctly | Connector |
| 82 | malicious content stored as data, not executed | Security |
| 83 | malformed JSON returns 422 | Error handling |
| 84 | nonexistent endpoint returns 404 | Error handling |
| 85 | liveness | Health |
| 86 | readiness | Health |

#### api-e2e.spec.ts (14)

| # | test | Purpose |
|---|------|---------|
| 87 | register → login → workspace → project → upload → ingest → search → chat → evidence → provenance | Golden API path |
| 88 | register creates new user | Auth API |
| 89 | login returns access and refresh tokens | Auth API |
| 90 | login rejects wrong password | Auth security |
| 91 | protected endpoint rejects missing token | Auth security |
| 92 | tenant A cannot see tenant B data | Multi-tenancy |
| 93 | ChatGPT connector uploads successfully | Connector API |
| 94 | Claude connector uploads successfully | Connector API |
| 95 | JSONL connector uploads successfully | Connector API |
| 96 | malicious content stored as data only | Security |
| 97 | malformed body returns 422 | Error handling |
| 98 | nonexistent endpoint returns 404 | Error handling |
| 99 | liveness returns alive | Health |
| 100 | readiness returns ready | Health |

#### dashboard.spec.ts (3)

| # | test | Purpose |
|---|------|---------|
| 101 | unauthenticated access redirects to login | Auth guard regression |
| 102 | Projects page unauthenticated access redirects | Auth guard regression |
| 103 | Settings page unauthenticated access redirects | Auth guard regression |

---

### DIAGNOSTIC Tests (2)

| # | File | Test Name | Purpose | Classification |
|---|------|-----------|---------|----------------|
| 104 | debug-auth.spec.ts | debug: capture console errors and check auth state | Captures console messages during auth flow, logs auth state for debugging auth token propagation issues | DIAGNOSTIC |
| 105 | test-diag.spec.ts | debug: check what nav looks like | Logs DOM state, checks nav rendering, dumps body text for diagnosing sidebar visibility | DIAGNOSTIC |

**Issues with diagnostic tests:**
- `debug-auth.spec.ts`: Contains `await page.waitForTimeout;` (missing parentheses — no-op). Logs to console for manual inspection.
- `test-diag.spec.ts`: Contains `await page.waitForTimeout;` (missing parentheses — no-op). Logs DOM state.
- Neither has meaningful assertions beyond `expect(reg.status).toBe(201)`.
- Both should be excluded from official certification count.

---

## Totals

| Classification | Count |
|---------------|-------|
| **CERTIFICATION** | 61 |
| **REGRESSION** | 42 |
| **Official Certification Baseline** | **103/103** |
| DIAGNOSTIC | 2 |
| DEBUG | 0 |
| EXPERIMENTAL | 0 |
| FIXTURE | 0 |
| **Total Discovered** | **105** |

---

## Per-Suite Breakdown

| Spec File | CERTIFICATION | REGRESSION | DIAGNOSTIC | Total |
|-----------|:---:|:---:|:---:|:---:|
| search-chat-certification.spec.ts | 19 | — | — | 19 |
| remaining-contracts.spec.ts | 20 | — | — | 20 |
| ui-certification.spec.ts | 22 | — | — | 22 |
| frontend-journey.spec.ts | — | 4 | — | 4 |
| auth.spec.ts | — | 7 | — | 7 |
| golden-journey.spec.ts | — | 14 | — | 14 |
| api-e2e.spec.ts | — | 14 | — | 14 |
| dashboard.spec.ts | — | 3 | — | 3 |
| debug-auth.spec.ts | — | — | 1 | 1 |
| test-diag.spec.ts | — | — | 1 | 1 |
| **Total** | **61** | **42** | **2** | **105** |
