# Phase 1R — Baseline

**Backend HEAD:** `0534efe426e42f9c03f1622dd792f052647038cc`
**Branch:** master
**Working tree:** 7 modified files, 17 untracked

## Tracked Modifications (from baseline)

| File | Nature | Impact |
|---|---|---|
| `app/main.py` | Bug fix: `async_engine` → `engine` import; added log to readiness handler | `/health/ready` was returning 503 (NameError); now returns proper DB status |
| `app/middleware/rate_limit.py` | Dev bypass: `X-E2E` header skips rate limits in non-production only | No production impact; gated by `settings.environment != "production"` |
| `frontend/tsconfig.json` | Added `"e2e"` to exclude list | No runtime impact |
| `frontend/e2e/golden-journey.spec.ts` | Updated workspace names to be unique | Test-only |
| `frontend/src/app/projects/[id]/memory/page.tsx` | Frontend feature work | UI layer |
| `frontend/src/types/api.ts` | Type definitions | Frontend-only |
| `CERTIFICATION/PRODUCTION_CERTIFICATION_REMEDIATED.md` | Certification document | Documentation |

## Backend SHA Confirmed

```
0534efe426e42f9c03f1622dd792f052647038cc
```

This matches the frozen baseline. No new backend commits. All remediation changes
are in the working tree (unstaged).

## Frontend SHA

Frontend lives in the same repository (monorepo). No separate SHA.

## Version

- Backend: production (no version tag)
- API Contract: 1.0.0 (frozen)
