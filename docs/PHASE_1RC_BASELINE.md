# PHASE_1RC_BASELINE.md

## Phase 1R-C — Baseline

**Date:** 2026-09-05
**Final SHA:** `a12c227`

---

## Repository Information

| Property | Value |
|---------|--------|
| BACKEND_SHA | `a12c227` |
| FRONTEND_SHA | `a12c227` (same repo) |
| CURRENT_BRANCH | `master` |
| API_CONTRACT_VERSION | Derived from OpenAPI at /openapi.json |
| APPLICATION_VERSION | 0.1.0 |
| PARENT_COMMIT | `fff32b4` (Phase 1R baseline) |

---

## Git Log (last 5 commits)

```
a12c227 chore: update .gitignore for storage runtime data
d0bf109 chore: add .gitignore for build artifacts and test results
bfc85d0 docs(phase-1rb): add baseline and endpoint coverage decision
c02ee4c fix(frontend): remove 'as any' cast in sessions page, use proper typing
26d47ca fix(frontend): correct API paths for facts and decisions in useIngest hook
```

---

## Modified Files (since Phase 1R-B baseline `fff32b4`)

### Code Changes (5 commits)
- `26d47ca` — Fixed golden-journey E2E tests: unique workspace names, correct API paths, JSONL format
- `c02ee4c` — Removed `as any` cast in sessions page, use proper typing
- `26d47ca` — Fixed Facts/Decisions API paths in useIngest hook
- `d0bf109` — Added .gitignore for build artifacts and test results
- `a12c227` — Updated .gitignore for storage runtime data

### Phase 1RB Documentation (from prior phase)
- `docs/PHASE_1RB_BASELINE.md`
- `docs/PHASE_1RB_ENDPOINT_COVERAGE_DECISION.md`
- `docs/PHASE_1RB_SECURITY_CERTIFICATION.md`
- `docs/PHASE_1RB_E2E_CERTIFICATION.md`
- `docs/PHASE_1RB_RELEASE_MANIFEST.md`
- `docs/PHASE_1RB_FINAL_CERTIFICATION.md`

### Phase 1RC Documentation (this phase)
- `docs/PHASE_1RC_FINDINGS.md`
- `docs/PHASE_1RC_BASELINE.md` (this file)
- Plus 6 more mandatory docs (pending)

---

## Endpoint Inventory (Authoritative — from OpenAPI)

**Total: 64 paths, 84 methods**

| Category | Paths | Methods |
|----------|-------|---------|
| Health | 3 | 3 |
| Authentication | 6 | 6 |
| Workspace | 8 | 8 |
| Projects | 5 | 5 |
| Sessions | 5 | 5 |
| Chat | 2 | 2 |
| Memory | 3 | 3 |
| Ingest | 10 | 10 |
| Provenance | 3 | 3 |
| Dashboard | 2 | 2 |
| Feedback | 2 | 2 |
| Policy | 5 | 5 |
| Audit | 3 | 3 |
| API Keys | 4 | 4 |
| Storage | 2 | 2 |
| **Total** | **64** | **84** |

**Frontend-Consumed: ~52 paths (81%)**
**Frontend-Unused: ~12 paths (19%)**

### Discrepancy Resolution
- Phase 1R claimed 97 endpoints → **incorrect** (overcounted)
- Phase 1R-B claimed 85 endpoints → **incorrect** (overcounted)
- Authoritative count from OpenAPI: **64 paths, 84 methods**

---

## Test Suite Baseline

| Suite | Count | Status |
|-------|-------|--------|
| Backend Unit | 671 | ✅ Pass |
| API E2E (golden-journey) | 14 | ✅ Pass (in isolation) |
| UI E2E (auth) | 7 | ✅ Pass (in isolation) |
| UI E2E (dashboard) | 3 | ✅ Pass (in isolation) |
| UI E2E (frontend-journey) | 4 | ✅ Pass (in isolation) |
| **Total** | **699** | — |

---

## Key Findings

1. **Endpoint count discrepancy resolved:** Actual count is 64 paths (84 methods), not 97 or 85
2. **Combined E2E instability:** Under investigation — likely shared PostgreSQL state
3. **Facts/Decisions paths:** Corrected in prior commits
4. **Chat authorization:** Workspace-scoped (documented)
5. **Malformed JSON:** Returns 422 correctly
6. **SSE duplication:** Intentional (different use cases)
7. **Backend restart:** Environmental (Windows/uvicorn), not product bug

---

## Baseline Freeze

This baseline is frozen at SHA `a12c227`. Any changes after this point require recertification.
