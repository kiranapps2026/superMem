# PHASE_0_BASELINE.md
## Memory Intelligence + Execution Integrity Layer — Phase 0 Baseline Certification
**Certified:** 2026-09-25 | **Certifier:** Claude Opus 5 (Anthropic)

---

## 1. Baseline Capture

| Item | Result |
|---|---|
| Git tag | `pre-memory-intelligence-baseline` present |
| pytest | 671 passed, 1 failed (known ENVIRONMENTAL: `openai` package missing) |
| `npm run build` | SUCCESS — 21 routes |
| `tsc --noEmit` | 0 errors |
| `npm run lint` | 0 errors, 3 warnings (pre-existing `react-hooks/exhaustive-deps`) |
| Alembic current | `012_add_invitations (head)` |
| Environment | Python 3.12.10, Node v24.21.0, npm 11.19.0, PostgreSQL 16.10 |

### Row Counts (Phase 0 Reference)

| Table | Count |
|---|---|
| memories | 0 |
| facts | 36 |
| decisions | 0 |
| graph_nodes | 36 |
| graph_edges | 18 |

These counts are the reference for all later phases. Any decrease (other than soft-delete) must be explained.

### .env Configuration Verified

| Variable | Value | Status |
|---|---|---|
| `RATE_LIMIT_INGEST` | Default 5 (config.py) | Documented |
| `CORS_ORIGINS` | `http://localhost:3000` | Documented |
| `STORAGE_BACKEND` | `filesystem` | Documented |

## 2. Executive Verdict

**GATE 0 — PASS**

All baseline checks pass. The known 1 test failure (missing `openai` package) is ENVIRONMENTAL, not a code defect. The system is ready for Phase 1.

## 3. Findings

| # | Severity | Description |
|---|---|---|
| F-0-1 | ENV | `openai` Python package not installed — 1 unit test fails. Optional dependency. |
| F-0-2 | P3 | 3 ESLint warnings are pre-existing `react-hooks/exhaustive-deps` issues, non-blocking. |
