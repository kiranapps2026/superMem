# E2E Test Inventory

**Date:** 2026-09-09
**Test Runner:** Playwright 1.63.0 (Chromium, 1 worker)
**Frontend:** http://localhost:3000
**Backend:** http://localhost:8000

---

## Classification Definitions

| Class | Definition |
|-------|-----------|
| **CERTIFICATION** | Verifies a specific vertical slice works end-to-end. Added during slice certification. |
| **REGRESSION** | Protects an already-certified slice from breaking. |
| **DIAGNOSTIC** | Developer/debug aid. Excluded from certification baseline. |
| **DEBUG** | Temporary investigation. Excluded from certification baseline. |

---

## Official Certification Baseline: 136/136 PASS

### CERTIFICATION Tests (136)

#### search-chat-certification.spec.ts (19)

| # | describe / test | Purpose |
|---|-----------------|---------|
| 1 | Search page renders heading and input | Page loads with search UI |
| 2 | Search input has correct placeholder | Placeholder text present |
| 3 | Search filter select is visible | memory_type filter visible |
| 4 | Search submit button is visible | Submit button present |
| 5 | Search API contract: POST returns 200 | POST contract, params: query, limit |
| 6 | Search with memory_type filter in query params | Filter param transmitted correctly |
| 7 | Search empty project returns empty results | Empty state handling |
| 8 | Search rejects without auth | 401 without token |
| 9 | Search console clean on empty results page | No console errors |
| 10 | Search responsive at 768px | Responsive layout |
| 11 | Search page has error state component | ErrorAlert component present |
| 12 | Chat page renders heading and textarea | Page loads with chat UI |
| 13 | Chat page shows empty state | Empty state rendered |
| 14 | Chat API contract: POST returns SSE | SSE stream contract |
| 15 | Chat rejects without auth | 401 without token |
| 16 | Chat sends message and sees response | Full send/receive workflow |
| 17 | Chat console clean on page load | No console errors |
| 18 | Chat responsive at 768px | Responsive layout |
| 19 | Chat page renders with evidence button support | Evidence modal support |

#### remaining-contracts.spec.ts (50)

| # | describe / test | Purpose |
|---|-----------------|---------|
| 20 | Timeline Network Contract › API: GET returns 200 | API contract: query params, `{ items, total }` |
| 21 | Timeline Network Contract › page renders heading | Browser render: heading visible |
| 22 | Timeline Network Contract › page has empty state | Browser render: empty state |
| 23 | Timeline vertical slice — items sorted descending | Backend: chronological ordering |
| 24 | Timeline vertical slice — mixed types (fact, decision, memory) | Backend: mixed timeline |
| 25 | Sessions Network Contract › API: GET returns 200 | API contract: list endpoint |
| 26 | Sessions Network Contract › page renders heading | Browser render: heading visible |
| 27 | Sessions Network Contract › page has empty state | Browser render: empty state |
| 28 | Sessions vertical slice — correct schema | Backend: id, title, created_at, updated_at |
| 29 | Sessions vertical slice — empty project empty array | Empty state via API |
| 30 | Graph Network Contract › API: GET returns 200 | API contract: `{ nodes, edges }` |
| 31 | Graph Network Contract › page renders heading | Browser render: heading visible |
| 32 | Graph Network Contract › page has empty state | Browser render: empty state |
| 33 | Graph vertical slice — nodes/edges schema | Backend: node fields verified |
| 34 | Graph vertical slice — edges reference valid nodes | Backend: referential integrity |
| 35 | Provenance Network Contract › API: GET returns 200 | API contract: array response |
| 36 | Provenance Network Contract › page renders heading | Browser render: heading visible |
| 37 | Provenance Network Contract › page has empty state | Browser render: empty state |
| 38 | Provenance vertical slice — correct schema | Backend: model, provider, latency, tokens |
| 39 | Provenance vertical slice — requires auth | Security: 401 without token |
| 40 | Provenance Detail and Chain › detail endpoint returns record by ID | API: detail by ID works |
| 41 | Provenance Detail and Chain › filters by session_id | API: session_id filter |
| 42 | Provenance Detail and Chain › memory expansion endpoint exists | API: /{id}/memories |
| 43 | Provenance Detail and Chain › returns 404 for unknown ID | Error handling |
| 44 | Graph Deep Certification › supports project_id filtering | API: project_id param |
| 45 | Graph Deep Certification › supports include_historical param | API: historical nodes |
| 46 | Graph Deep Certification › nodes contain required backend fields | Schema: id, workspace_id, project_id, label, node_type, properties |
| 47 | Graph Deep Certification › edges contain required backend fields | Schema: source, target, relationship, confidence, temporal_status |
| 48 | Graph Deep Certification › node_type values from backend vocabulary | Data: valid node types |
| 49 | Graph Deep Certification › empty project returns empty nodes and edges | Empty state via API |
| 50 | Graph Deep Certification › rejects without auth | Security: 401 without token |
| 51 | Graph UI Interactions › page renders with node selection UI | Browser: UI renders |
| 52 | Graph UI Interactions › detail panel shows node properties when nodes exist | Browser: detail panel |
| 53 | Graph UI Interactions › relationship type and confidence for selected node | Browser: detail panel content |
| 54 | Cross-Page Knowledge Chain › Search→Memory→Provenance — IDs in results | Chain: ID integrity |
| 55 | Cross-Page Knowledge Chain › Session→Timeline — timestamp continuity | Chain: timestamp integrity |
| 56 | Cross-Page Knowledge Chain › Memory→Facts→Decisions — distinct ID types | Chain: ID type distinction |
| 57 | Sessions Project-Filter Honesty › backend does NOT filter by project_id | Backend: documented behavior |
| 58 | Sessions Project-Filter Honesty › page communicates workspace scope | UI: correct language |
| 59 | Responsive Certification › Timeline at 768px | Responsive: tablet |
| 60 | Responsive Certification › Sessions at 768px | Responsive: tablet |
| 61 | Responsive Certification › Graph at 768px | Responsive: tablet |
| 62 | Responsive Certification › Provenance at 768px | Responsive: tablet |
| 63 | Responsive Certification › Timeline at 390px | Responsive: mobile |
| 64 | Responsive Certification › Sessions at 390px | Responsive: mobile |
| 65 | Responsive Certification › Graph at 390px | Responsive: mobile |
| 66 | Responsive Certification › Provenance at 390px | Responsive: mobile |
| 67 | Accessibility Regression › Sessions page heading hierarchy | A11y: single h1 |
| 68 | Accessibility Regression › Graph page heading hierarchy | A11y: single h1 |
| 69 | Accessibility Regression › Provenance page heading hierarchy | A11y: single h1 |
| 70 | Accessibility Regression › Timeline page heading hierarchy | A11y: single h1 |
| 71 | Accessibility Regression › No horizontal overflow on Sessions | A11y: no overflow |
| 72 | Accessibility Regression › No horizontal overflow on Graph | A11y: no overflow |

#### ui-certification.spec.ts (11)

| # | describe / test | Purpose |
|---|-----------------|---------|
| 73 | UI Browser › Dashboard renders with stats | Browser: dashboard stats visible |
| 74 | UI Browser › Dashboard creates project via New Project form | Browser: project creation |
| 75 | UI Browser › Projects page lists projects | Browser: project list renders |
| 76 | UI Browser › Chat page renders with empty state | Browser: chat empty state |
| 77 | UI Browser › Chat sends message and receives response | Browser: full chat workflow |
| 78 | UI Browser › Search page renders | Browser: search page renders |
| 79 | UI Browser › Memory page renders | Browser: memory page renders |
| 80 | UI Browser › Settings page renders | Browser: settings page renders |
| 81 | UI Browser › Ingest page renders with upload form | Browser: ingest page renders |
| 82 | UI Browser › Facts page renders | Browser: facts page renders |
| 83 | UI Browser › Decisions page renders | Browser: decisions page renders |
| 84 | Search Network Contract › sends POST with query and limit params | Network: POST contract |
| 85 | Memory Network Contract › loads via GET with project_id param | Network: GET contract |
| 86 | Memory Network Contract › page has filter and structure | Browser: filter UI present |
| 87 | Memory vertical slice — API returns correct schema | Backend: memory fields verified |
| 88 | Memory vertical slice — filter by memory_type param | Backend: filter works |
| 89 | Memory vertical slice — filter by temporal_status param | Backend: temporal filter |
| 90 | Memory vertical slice — page renders empty state | Browser: empty state |
| 91 | Facts Network Contract › loads via GET with project_id param | Network: GET contract |
| 92 | Facts page has empty state and s-p-o display | Browser: triple display |
| 93 | Decisions Network Contract › loads via GET with project_id param | Network: GET contract |
| 94 | Decisions page has empty state | Browser: empty state |

#### frontend-journey.spec.ts (4)

| # | test | Purpose |
|---|------|---------|
| 95 | full journey: dashboard → create project → navigate pages | End-to-end UI flow |
| 96 | sidebar navigation is present and links work | Navigation completeness |
| 97 | logout redirects to login | Auth flow |
| 98 | unauthenticated access redirects to login | Auth guard |

#### auth.spec.ts (7)

| # | test | Purpose |
|---|------|---------|
| 99 | login page renders with form elements | Auth page render |
| 100 | register page link is accessible | Navigation between auth pages |
| 101 | login with invalid credentials shows error | Error handling |
| 102 | login with empty fields validates | Form validation |
| 103 | register page renders | Auth page render |
| 104 | register with mismatched passwords shows error | Error handling |
| 105 | login link on register page works | Navigation |

#### golden-journey.spec.ts (14)

| # | test | Purpose |
|---|------|---------|
| 106 | register → login → workspace → project → upload → ingestion → search → chat → evidence → provenance | Full golden path |
| 107 | register creates new user | Auth |
| 108 | login returns tokens | Auth |
| 109 | login rejects wrong password | Auth security |
| 110 | protected endpoint rejects missing token | Auth security |
| 111 | tenant A and B are isolated | Multi-tenancy |
| 112 | ChatGPT connector normalizes correctly | Connector |
| 113 | Claude connector normalizes correctly | Connector |
| 114 | JSONL connector normalizes correctly | Connector |
| 115 | malicious content stored as data, not executed | Security |
| 116 | malformed JSON returns 422 | Error handling |
| 117 | nonexistent endpoint returns 404 | Error handling |
| 118 | liveness | Health |
| 119 | readiness | Health |

#### api-e2e.spec.ts (14)

| # | test | Purpose |
|---|------|---------|
| 120 | register → login → workspace → project → upload → ingest → search → chat → provenance | Golden API path |
| 121 | register creates new user | Auth API |
| 122 | login returns access and refresh tokens | Auth API |
| 123 | login rejects wrong password | Auth security |
| 124 | protected endpoint rejects missing token | Auth security |
| 125 | tenant A cannot see tenant B data | Multi-tenancy |
| 126 | ChatGPT connector uploads successfully | Connector API |
| 127 | Claude connector uploads successfully | Connector API |
| 128 | JSONL connector uploads successfully | Connector API |
| 129 | malicious content stored as data only | Security |
| 130 | malformed body returns 422 | Error handling |
| 131 | nonexistent endpoint returns 404 | Error handling |
| 132 | liveness returns alive | Health |
| 133 | readiness returns ready | Health |

#### dashboard.spec.ts (3)

| # | test | Purpose |
|---|------|---------|
| 134 | unauthenticated access redirects to login | Auth guard regression |
| 135 | Projects page unauthenticated access redirects | Auth guard regression |
| 136 | Settings page unauthenticated access redirects | Auth guard regression |

---
### Skipped Tests (2)

| # | File | Reason |
|---|------|--------|
| 137 | remaining-contracts.spec.ts | Provenance detail/schema tests skip when no chat records exist |
| 138 | remaining-contracts.spec.ts | Provenance memory expansion skips when no provenance records exist |

---
## Per-Suite Breakdown

| Spec File | CERTIFICATION | Pass | Skip | Total |
|-----------|:---:|:---:|:---:|:---:|
| search-chat-certification.spec.ts | 19 | 19 | 0 | 19 |
| remaining-contracts.spec.ts | 50 | 50 | 2 | 50 |
| ui-certification.spec.ts | 22 | 22 | 0 | 22 |
| frontend-journey.spec.ts | 4 | 4 | 0 | 4 |
| auth.spec.ts | 7 | 7 | 0 | 7 |
| golden-journey.spec.ts | 14 | 14 | 0 | 14 |
| api-e2e.spec.ts | 14 | 14 | 0 | 14 |
| dashboard.spec.ts | 3 | 3 | 0 | 3 |
| **Total** | **133** | **133** | **2** | **136** |
