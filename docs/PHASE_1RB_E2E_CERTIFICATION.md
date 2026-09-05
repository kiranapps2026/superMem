# PHASE_1RB_E2E_CERTIFICATION.md

## Phase 1R-B — E2E Certification

**Date:** 2026-09-05
**Certifier:** Claude (automated)
**Baseline:** `81549c8`
**Browser:** Chromium (Playwright)
**Workers:** 1 (sequential, required for DB consistency)

---

## Test Suite Summary

| Suite | File | Tests | Pass | Fail | Status |
|-------|------|-------|------|------|--------|
| Auth Pages | auth.spec.ts | 7 | 7 | 0 | ✅ |
| Dashboard | dashboard.spec.ts | 3 | 3 | 0 | ✅ |
| Frontend UI Journey | frontend-journey.spec.ts | 4 | 4 | 0 | ✅ |
| Golden Journey (API) | golden-journey.spec.ts | 14 | 14 | 0 | ✅ |
| **Total UI E2E** | | **28** | **28** | **0** | **✅** |

---

## Per-Test Evidence

### auth.spec.ts (7/7 PASS)
1. login page renders with form elements ✅
2. register page link is accessible ✅
3. login with invalid credentials shows error ✅
4. login with empty fields validates ✅
5. register page renders ✅
6. register with mismatched passwords shows error ✅
7. login link on register page works ✅

### dashboard.spec.ts (3/3 PASS)
1. unauthenticated access redirects to login ✅
2. Projects page unauthenticated access redirects ✅
3. Settings page unauthenticated access redirects ✅

### frontend-journey.spec.ts (4/4 PASS)
1. full journey: dashboard → create project → navigate pages ✅
2. sidebar navigation is present and links work ✅
3. logout redirects to login ✅
4. unauthenticated access redirects to login ✅

### golden-journey.spec.ts (14/14 PASS)
1. register → login → workspace → project → upload → ingestion → search → chat → evidence → provenance ✅
2. register creates new user ✅
3. login returns tokens ✅
4. login rejects wrong password ✅
5. protected endpoint rejects missing token ✅
6. tenant A and B are isolated ✅
7. ChatGPT connector normalizes correctly ✅
8. Claude connector normalizes correctly ✅
9. JSONL connector normalizes correctly ✅
10. malicious content stored as data, not executed ✅
11. malformed JSON returns 422 ✅
12. nonexistent endpoint returns 404 ✅
13. liveness ✅
14. readiness ✅

---

## Known Issues

- **Rate limiting in combined runs:** When running auth.spec + dashboard + frontend-journey + golden-journey together, the X-E2E header is required to bypass rate limits. Without it, connector tests fail with 429 after 20 preceding API calls.
- **UV_HANDLE_CLOSING warnings:** Windows-specific libuv assertion in Playwright. Does not affect test results. Cosmetic only.

---

## Certification

> E2E certification is **PASS**.
> All 28 Playwright tests pass against backend at SHA `81549c8`.

---
**Signatures:**

| Role | Approver | Date |
|------|----------|------|
| QA Automation | Claude | 2026-09-05 |
| E2E Lead | — | — |
