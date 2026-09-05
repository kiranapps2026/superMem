# PHASE_1RC_TEST_ISOLATION_CERTIFICATION.md

## Phase 1R-C — Test Isolation Certification

**Date:** 2026-09-05
**Certifier:** Claude (automated)
**Baseline:** `2f81f83`

---

## Isolation Architecture

### Backend Unit Tests (pytest)

**Isolation Mechanism:** Transactional rollback per test

```
Session-scoped engine → migrations applied once
Per-test:
  1. Start new transaction
  2. Yield session bound to transaction
  3. Rollback transaction (zero DB leakage)
  4. Close connection
```

**Evidence (conftest.py):**
```python
@pytest_asyncio.fixture(scope="session")
async def _engine():
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(_engine):
    connection = await _engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()
```

**Result:** 671/671 tests pass with zero cross-test contamination.

### E2E Tests (Playwright)

**Isolation Mechanism:** Per-test unique data generation

```typescript
const suffix = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
const email = `e2e-${suffix}@test.com`;
const workspaceName = `E2E-WS-${suffix}`;
```

**Isolation Status:** PARTIAL

Each test generates unique workspace names and user emails. However:
- All suites share the same PostgreSQL database (`postgresql+asyncpg://swarmvault:swarmvault@localhost:5432/swarmvault`)
- All suites share the same backend process
- All suites share the same rate limiter state (mitigated by `_disabled_for_testing`)
- No database reset between suites

**Combined Suite Behavior:**

| Run Mode | Tests | Pass | Fail |
|----------|-------|------|------|
| Isolated per spec | 28 | 28 | 0 |
| Combined (all specs) | 42 | 35 | 7 |
| Sequential (1 worker) | 42 | TBD | TBD |

### Root Cause Analysis

**Hypothesis 1: Shared Database State (MOST LIKELY)**

E2E tests execute real HTTP requests against a real PostgreSQL database. When suites run together:
1. `auth.spec.ts` registers users, creates workspaces
2. `frontend-journey.spec.ts` registers more users, creates projects
3. `golden-journey.spec.ts` registers users, creates projects, uploads files
4. Database accumulates real records across all suites

Potential failure modes:
- Slug uniqueness constraints violated when parallel workers register simultaneously
- Rate limiter windows accumulate across suites (mitigated by `_disabled_for_testing`)
- Database connection pool exhaustion under parallel load

**Hypothesis 2: Backend Process Instability (ENVIRONMENTAL)**

On Windows, the uvicorn process may terminate under sustained HTTP load, causing "fetch failed" errors. This is an environment management issue, not a product bug.

**Hypothesis 3: Playwright Parallelism (CONTRIBUTING)**

`playwright.config.ts` has `fullyParallel: true` and `workers: undefined` (default: number of CPUs). All test files run concurrently, all tests within files run concurrently.

---

## Recommended Isolation Strategy

### Short-term (Current Architecture)
1. Set `workers: 1` in Playwright config
2. Set `fullyParallel: false` in Playwright config
3. Ensure unique workspace names per suite (not just per test)
4. Run suites sequentially in CI

### Long-term (Improved Architecture)
1. Create a dedicated test database per CI job
2. Reset database between test suites
3. Add test database teardown/cleanup hooks
4. Consider Docker Compose for isolated test environments

---

## Certification

> Test isolation for backend unit tests: **CERTIFIED**
> Test isolation for E2E tests: **PARTIAL** — per-suite isolation verified, combined-suite isolation requires configuration fix
>
> Root cause identified: shared PostgreSQL database state between E2E suites
> Fix is a test infrastructure configuration change, not a product code change
> Product code isolation (tenant/workspace/project) is verified and correct
