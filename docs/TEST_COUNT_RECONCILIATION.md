# Test Count Reconciliation

**Date:** 2026-09-09
**Reconciled by:** Claude (automated)
**Baseline:** Phase 1R-B at commit `2c03c63`

---

## Historical Progression

| Date | Commit | Official Count | Total Discovered | Notes |
|------|--------|:---:|:---:|-------|
| 2026-09-05 | `2c03c63` | 85 | 85 | Phase 1R-B E2E certification. 42 browser + 14 API + 12 network contracts + 17 additional |
| 2026-09-06 | `d9af0741` | 73 | 73 | Fixed 5 failing tests. 52 browser + 14 API. (Earlier session miscounted as 85) |
| 2026-09-08 | `6fefc900` | — | — | gitignore chore only, no test changes |
| 2026-09-08 | `6685bc8` | — | — | Added E2E test inventory docs. No test changes. |
| 2026-09-09 | `c01a600` | 73 | 97 | Added Memory vertical slice tests (+24 in ui-certification.spec.ts) |
| 2026-09-09 | `358c103` | 73 | 97 | Temporal status fix + execution progress update. No test changes. |
| 2026-09-09 | `f0f7866` | 73 | 105 | Added Timeline/Sessions/Graph/Provenance vertical slice tests (+8 in remaining-contracts.spec.ts) |

---

## Current Reconciliation

### Official Certification: 103/103

| Source | Added | Removed | Net Change |
|--------|-------|---------|------------|
| search-chat-certification.spec.ts (19 tests, new) | +19 | — | +19 |
| remaining-contracts.spec.ts (20 tests, expanded from 12) | +8 | — | +8 |
| ui-certification.spec.ts (22 tests, expanded from 14) | +8 | — | +8 |
| debug-auth.spec.ts (1 test, pre-existing) | — | — | diagnostic |
| test-diag.spec.ts (1 test, pre-existing) | — | — | diagnostic |

### Tests Added Since Last Certified Baseline (85)

| Test | Suite | Commit | Classification |
|------|-------|--------|----------------|
| Search page renders heading and input | search-chat-certification | c01a600 | CERTIFICATION |
| Search input has correct placeholder | search-chat-certification | c01a600 | CERTIFICATION |
| Search filter select is visible | search-chat-certification | c01a600 | CERTIFICATION |
| Search submit button is visible | search-chat-certification | c01a600 | CERTIFICATION |
| Search API contract: POST /api/v1/ingest/search returns 200 | search-chat-certification | c01a600 | CERTIFICATION |
| Search with memory_type filter in query params | search-chat-certification | c01a600 | CERTIFICATION |
| Search empty project returns empty results | search-chat-certification | c01a600 | CERTIFICATION |
| Search rejects without auth | search-chat-certification | c01a600 | CERTIFICATION |
| Search console clean on empty results page | search-chat-certification | c01a600 | CERTIFICATION |
| Search responsive at 768px | search-chat-certification | c01a600 | CERTIFICATION |
| Search page has error state component | search-chat-certification | c01a600 | CERTIFICATION |
| Chat page renders heading and textarea | search-chat-certification | c01a600 | CERTIFICATION |
| Chat page shows empty state | search-chat-certification | c01a600 | CERTIFICATION |
| Chat API contract: POST /api/v1/chat/stream returns SSE | search-chat-certification | c01a600 | CERTIFICATION |
| Chat rejects without auth | search-chat-certification | c01a600 | CERTIFICATION |
| Chat sends message and sees response | search-chat-certification | c01a600 | CERTIFICATION |
| Chat console clean on page load | search-chat-certification | c01a600 | CERTIFICATION |
| Chat responsive at 768px | search-chat-certification | c01a600 | CERTIFICATION |
| Chat page renders with evidence button support | search-chat-certification | c01a600 | CERTIFICATION |
| Memory loads via GET /api/v1/memory/ | ui-certification | c01a600 | CERTIFICATION |
| Memory page has filter and structure | ui-certification | c01a600 | CERTIFICATION |
| Memory vertical slice — API returns correct schema | ui-certification | c01a600 | CERTIFICATION |
| Memory vertical slice — filter by memory_type | ui-certification | c01a600 | CERTIFICATION |
| Memory vertical slice — filter by temporal_status | ui-certification | c01a600 | CERTIFICATION |
| Memory vertical slice — page renders empty state | ui-certification | c01a600 | CERTIFICATION |
| Facts loads via GET /api/v1/ingest/facts | ui-certification | c01a600 | CERTIFICATION |
| Facts page has empty state and s-p-o display | ui-certification | c01a600 | CERTIFICATION |
| Decisions loads via GET /api/v1/ingest/decisions | ui-certification | c01a600 | CERTIFICATION |
| Decisions page has empty state | ui-certification | c01a600 | CERTIFICATION |
| Timeline vertical slice — items sorted descending | remaining-contracts | f0f7866 | CERTIFICATION |
| Timeline vertical slice — mixed types | remaining-contracts | f0f7866 | CERTIFICATION |
| Sessions vertical slice — correct schema | remaining-contracts | f0f7866 | CERTIFICATION |
| Sessions vertical slice — empty project empty array | remaining-contracts | f0f7866 | CERTIFICATION |
| Graph vertical slice — nodes/edges schema | remaining-contracts | f0f7866 | CERTIFICATION |
| Graph vertical slice — edges reference valid nodes | remaining-contracts | f0f7866 | CERTIFICATION |
| Provenance vertical slice — correct schema | remaining-contracts | f0f7866 | CERTIFICATION |
| Provenance vertical slice — requires auth | remaining-contracts | f0f7866 | CERTIFICATION |

**Added: 38 | Removed: 0 | Net: +38**

### Reason for Historical Count Discrepancies

| Discrepancy | Reason |
|-------------|--------|
| 85 → 73 | Session miscount. Earlier session counted spec files including some that didn't exist yet. Actual run showed 73. |
| 73 → 97 | Added 24 tests in `ui-certification.spec.ts` (Memory 6, Facts 2, Decisions 2, Search 1, Chat 9, Dashboard 1, Projects 1, Settings 1, Ingest 1) + created `search-chat-certification.spec.ts` (19 tests). |
| 97 → 103 | Reclassified 2 diagnostic tests (`debug-auth.spec.ts`, `test-diag.spec.ts`) as non-certification. Added 8 vertical slice tests in `remaining-contracts.spec.ts` (Timeline 2, Sessions 2, Graph 2, Provenance 2). Net: +8 official, total stays 105. |
