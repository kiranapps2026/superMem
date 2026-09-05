# PHASE_1RB_BASELINE.md

## Gate 0 — Source Immutability & Baseline

**Date:** 2026-09-04
**Final SHA:** `fff32b4ca3a2c9120107cb1153dbd3f02ba4f7a2`

---

## Repository Information

| Property | Value |
|---------|--------|
| BACKEND_SHA | `fff32b4` |
| FRONTEND_SHA | `fff32b4` (same repo) |
| CURRENT_BRANCH | `master` |
| API_CONTRACT_VERSION | 1.0 (frozen) |
| APPLICATION_VERSION | 0.1.0 |
| PARENT_COMMIT | `0534efe` (Phase 1R baseline) |

---

## Git Log (last 5 commits)

```
fff32b4 feat(phase-1rb): enterprise frontend/backend integration certification
0534efe fix(p0-p1): production readiness — security, migrations, policy engine
902d85e Sprint 7: Enterprise production hardening — begin
cd0f4ff Sprint 4 enterprise hardening: memory model, storage, rate limiting, golden dataset, security, 387/387 tests
4685270 Sprint 5: frontend, chat evidence, graph, search, golden tests — 194/194 PASS
```

---

## Modified Files (since parent 0534efe)

### Backend Changes (4 files)
- `app/main.py` — fixed `/health/ready` import (async_engine → engine)
- `app/api/audit.py` — fixed double-prefix path `/api/v1/api/v1/audit`
- `app/middleware/rate_limit.py` — added X-E2E header bypass for non-production
- `app/core/config.py` — production validators block insecure defaults

### Frontend Changes (new + modified)

**New Directories:**
- `frontend/src/app/settings/api-keys/` — API key management UI
- `frontend/src/app/settings/profile/` — User profile UI
- `frontend/src/app/projects/[id]/settings/` — Project settings UI
- `frontend/src/components/ui/` — 11 UI components
- `frontend/src/features/` — 8 feature hooks

**New Files (45+):**
- E2E tests: `auth.spec.ts`, `dashboard.spec.ts`, `frontend-journey.spec.ts`, `api-e2e.spec.ts`
- Unit tests: `tests/unit/test_remediation.py`
- Docs: 9 Phase 1R documents

**Modified Files (12):**
- `app/main.py`, `app/api/audit.py`, `app/middleware/rate_limit.py`, `app/core/config.py`
- `frontend/src/app/auth/login/page.tsx`
- `frontend/src/app/auth/register/page.tsx`
- `frontend/src/app/layout.tsx`
- `frontend/src/types/api.ts`
- `frontend/tsconfig.json`
- `frontend/playwright.config.ts`
- `frontend/e2e/golden-journey.spec.ts`

---

## Test Suite Baseline

| Suite | Expected | Source |
|-------|----------|---------|
| Backend Unit | 671 | pytest tests/ |
| Backend Remediation | 15 | pytest tests/unit/test_remediation.py |
| API E2E | 14 | playwright e2e/golden-journey.spec.ts |
| UI E2E | 14 | playwright auth + dashboard + frontend-journey |

---

## API Contract Baseline

| Property | Value |
|----------|--------|
| Total Endpoints | 97 |
| Frontend-Consumed | 50 |
| Unused | 47 |
| Contract Version | 1.0 (frozen) |

---

## Security Posture Baseline

| Control | Status |
|---------|--------|
| JWT Auth | ✅ Enabled |
| RBAC | ✅ owner/admin/member/viewer |
| Rate Limiting | ✅ Sliding window |
| Policy Engine | ✅ Fail-closed |
| CORS | ✅ Configured |
| Production Validators | ✅ Enabled |

---

## Previous Phase 1R Claims (to verify)

| Claim | Expected | Verification Method |
|-------|----------|---------------------|
| UI E2E | 14/14 | Run playwright |
| API E2E | 14/14 | Run playwright |
| Unit | 686 | Run pytest |

---

## Baseline Freeze

This baseline is frozen at SHA `fff32b4`. Any changes after this point require recertification.
