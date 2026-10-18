# Gate 6: Database Test Isolation Forensics

**Date:** 2026-09-05
**Project:** SwarmVault WebApp
**Location:** `C:\Users\Administrator\Documents\SwarmVaultwebapp`
**Status:** CRITICAL — Multiple interlocking root causes identified

---

## Executive Summary

Three interlocking root causes explain all three failure modes (combined E2E suite failures, backend requiring restarts, database pollution between suites):

1. **E2E tests write to the production database with zero isolation** — Playwright tests hit the live FastAPI backend on port 8000, which connects to `swarmvault` (the development database). There is no test database, no transaction rollback, and no cleanup between test runs.

2. **Connection pool exhaustion under parallel E2E execution** — The global async engine uses default pool settings (size=5, max_overflow=10). Playwright's default worker count (CPU core count, often 8+) creates concurrent request floods that exhaust the pool, causing `TimeoutError` and connection failures that require backend restarts.

3. **Playwright webServer only starts the frontend** — The `npm run dev` command only launches Next.js on port 3000. The FastAPI backend on port 8000 is expected to already be running externally. If it crashes, Playwright's `reuseExistingServer: true` won't restart it, requiring manual intervention.

---

## Finding 1: No Test Database Exists for E2E Tests

### Evidence

**`app/core/config.py` (line 8, 23):**
```python
_DEV_DATABASE_URL = "postgresql+asyncpg://swarmvault:swarmvault@localhost:5432/swarmvault"
database_url: str = _DEV_DATABASE_URL  # No TEST_DATABASE_URL setting exists
```

**`app/db.py` (line 9):**
```python
engine = create_async_engine(settings.database_url, echo=settings.debug)
```
A single global engine is created at module import time using the development database URL.

**`tests/conftest.py` (lines 23-24):** The unit test suite DOES use a separate test database:
```python
TEST_DATABASE_URL = "postgresql+asyncpg://swarmvault:swarmvault@localhost:5432/swarmvault_test"
```
But this is a hardcoded constant in the test fixtures only — the running backend server has no awareness of it.

### Impact

All Playwright E2E tests (`api-e2e.spec.ts`, `golden-journey.spec.ts`, `frontend-journey.spec.ts`, `auth.spec.ts`, `dashboard.spec.ts`) make real HTTP requests to `http://localhost:8000`. Every `register`, `login`, `project` creation, and `ingest/upload` writes permanent records to the **development database**.

There is no teardown, no transaction wrapping, and no database reset between Playwright test files or test runs.

---

## Finding 2: E2E Tests Share State Across All Suites

### Evidence

**`frontend/playwright.config.ts` (line 6-8):**
```typescript
fullyParallel: true,        // All test files run in parallel
workers: process.env.CI ? 1 : undefined,  // undefined = use all CPU cores (often 8+)
retries: process.env.CI ? 2 : 0,
```

**`frontend/e2e/api-e2e.spec.ts` (line 3):**
```typescript
const BASE = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:8000';
```

**`frontend/e2e/golden-journey.spec.ts` (line 3):**
```typescript
const BASE = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:8000';
```

**`frontend/e2e/frontend-journey.spec.ts` (line 4):**
```typescript
const API = 'http://localhost:8000';
```

All E2E tests call the same backend instance. Since they all write to the same database:

- **`api-e2e.spec.ts`** registers users with `tenant.slug` derived from workspace names like `WS-${Date.now()}-${random}`. Multiple workers can produce colliding timestamps.
- **`golden-journey.spec.ts`** registers users with workspace names like `Golden-WS-${Date.now()}`. Same collision risk.
- **`auth.spec.ts`** and **`dashboard.spec.ts`** also create real records.

### Impact

When running individually, each spec file's data doesn't conflict with itself. When run together in parallel:

- Race conditions on unique constraints (`tenants.slug` is `unique=True` at `app/models.py:25`)
- Database accumulates test data across runs
- Search results become polluted with data from other test workers
- Rate limiter accumulates state across requests (though `X-E2E: true` bypasses this for non-production)

---

## Finding 3: Tenant Slug Collision Risk

### Evidence

**`app/api/auth.py` (line 47-48):**
```python
slug = data.workspace_name.lower().replace(" ", "-")[:50]
tenant = Tenant(name=data.workspace_name, slug=slug)
```

**`app/models.py` (line 25):**
```python
slug: Mapped[str] = mapped_column(String(100), unique=True)
```

The `tenants.slug` column has a unique constraint. The E2E tests use `Date.now()` for workspace name suffixes:

- `api-e2e.spec.ts`: `WS-${Date.now()}-${Math.random().toString(36).slice(2, 4)}`
- `golden-journey.spec.ts`: `Golden-WS-${Date.now()}`
- `frontend-journey.spec.ts`: `E2E-WS-${suffix}` (suffix from `Date.now().toString(36) + random`)

With parallel workers, two workers can call `Date.now()` in the same millisecond, producing identical slugs → `IntegrityError` on the unique constraint → 500 error → test failure.

---

## Finding 4: Connection Pool Exhaustion

### Evidence

**`app/db.py` (line 9-12):**
```python
engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
```

Default pool settings: `pool_size=5`, `max_overflow=10` (SQLAlchemy defaults for async engines).

**`app/main.py` (lines 192-209):** The `AuditPersistenceMiddleware` opens a **new session per request**:
```python
class AuditPersistenceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        try:
            from app.db import async_session_factory
            async with async_session_factory() as session:
                await audit.persist(session)
                await session.commit()
        except Exception:
            pass
        return response
```

**Playwright parallel execution:** With `workers: undefined`, a machine with 8 CPU cores spawns 8 workers. Each worker runs tests sequentially, but multiple workers make concurrent requests. A single E2E spec like `api-e2e.spec.ts` makes ~15 API calls per test. With 8 workers, that's potentially 120+ concurrent connections against a pool of 15 (5 + 10 overflow).

Additionally, long-running operations (chat calls that invoke LLM with `llm_timeout_seconds: 30.0`, ingest processing) hold connections for extended periods.

### Impact

- `TimeoutError: Pool exhausted` after the 15th concurrent connection
- Backend becomes unresponsive for new requests
- Playwright tests timeout with connection errors
- Backend process must be restarted to clear hung connections

---

## Finding 5: Backend Not Managed by Playwright

### Evidence

**`frontend/playwright.config.ts` (lines 21-26):**
```typescript
webServer: process.env.CI ? undefined : {
    command: 'npm run dev',       // Only starts Next.js frontend
    url: 'http://localhost:3000',
    reuseExistingServer: true,    // Won't restart a crashed server
    timeout: 30000,
},
```

**`frontend/package.json` (line 9):**
```json
"dev": "next dev --port 3000"
```

**`app/main.py`:** There is no `__main__` block. The FastAPI app is launched externally (likely via uvicorn from the Dockerfile command `uvicorn app.main:app --host 0.0.0.0 --port 8000`).

### Impact

1. **Backend crash requires manual restart:** If the FastAPI process crashes (pool exhaustion, DB connection loss, OOM), Playwright won't restart it because `webServer` only manages the frontend.

2. **`reuseExistingServer: true` masks failures:** If the backend is in a bad state (corrupted pool, stale connections), Playwright reuses it rather than restarting.

3. **No health check gating:** Playwright doesn't wait for `http://localhost:8000/health/ready` before running tests. If the backend is slow to start or unhealthy, tests fail immediately.

4. **No backend restart on test failure:** Unlike the frontend (which Playwright can restart), the backend is an external dependency.

---

## Finding 6: Global Singleton AuditService Buffer

### Evidence

**`app/main.py` (line 160):**
```python
audit = AuditService()  # Module-level singleton
```

**`app/services/audit/service.py` (lines 132-176):**
```python
class AuditService:
    def __init__(self):
        self._sinks: list[EventSink] = []
        self._buffer: list[AuditEvent] = []  # In-memory buffer, never persisted unless persist() called
```

**`app/main.py` (line 160, same module import):**
```python
audit = AuditService()
audit.register_db_sink()
```

The `AuditService` is a module-level singleton with an in-memory event buffer. The `AuditPersistenceMiddleware` flushes this buffer after each request. However:

1. If the middleware's session creation fails (pool exhaustion), events accumulate in memory
2. If the backend process is under heavy load, the buffer grows unbounded
3. On backend restart, all buffered events are lost
4. The `_rate_limiter._windows.clear()` in `tests/conftest.py:21` only applies to unit tests, not the running server

### Impact

- Memory leak under sustained load (buffer grows if persist() fails)
- Audit trail loss on backend restart
- Inconsistent audit state between test runs

---

## Finding 7: asyncio.get_event_loop() Deprecation

### Evidence

**`app/db.py` (line 36):**
```python
async def init_db():
    import asyncio
    loop = asyncio.get_event_loop()  # DEPRECATED in Python 3.10+
    cfg = _alembic_config()
    await loop.run_in_executor(None, lambda: command.upgrade(cfg, "head"))
```

**`app/main.py` (line 169):**
```python
await init_db()  # Called during app startup lifespan
```

`asyncio.get_event_loop()` is deprecated and can raise `DeprecationWarning` or `RuntimeError` in Python 3.12+ when there's no running event loop. The correct pattern is `asyncio.get_running_loop()`.

### Impact

- On Python 3.12 (the Dockerfile uses `python:3.12-slim`), this can fail with `RuntimeError: There is no current event loop in thread 'MainThread'` if called outside of an async context
- This causes the FastAPI lifespan to fail, preventing the app from starting
- When the app fails to start, Playwright tests hit connection errors
- This is a likely contributor to "backend requires restarts" — the backend may fail to start cleanly

---

## Finding 8: Unit Test Fixture Isolation (Contrast — This Works Correctly)

### Evidence

**`tests/conftest.py` (lines 41-83):**
```python
@pytest_asyncio.fixture(scope="session", autouse=True)
def _apply_migrations():
    _run_alembic_migrations(TEST_DATABASE_URL)  # Test DB, not dev DB
    yield
    command.downgrade(cfg, "base")  # Teardown: drop all tables

@pytest_asyncio.fixture(scope="session")
async def _engine():
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(_engine):
    connection = await _engine.connect()
    transaction = await connection.begin()    # New transaction per test
    session = AsyncSession(bind=connection, expire_on_commit=False)
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()          # Clean rollback
        await connection.close()
```

The unit tests use a **separate test database** (`swarmvault_test`), **NullPool** (no connection pooling), and **transaction rollback** per test. This is correctly isolated.

The E2E tests have **none** of these protections — they share the dev database, the production pool, and have no transaction wrapping.

---

## Finding 9: Frontend E2E Tests Create Real Database Records

### Evidence

**`frontend/e2e/frontend-journey.spec.ts` (lines 6-49):**
```typescript
async function registerAndLogin(page) {
    const suffix = Date.now().toString(36) + Math.random().toString(36).slice(2, 5);
    const email = `e2e-${suffix}@test.com`;
    const workspaceName = `E2E-WS-${suffix}`;
    // ... registers via fetch() to the real API
}
```

**`frontend/e2e/auth.spec.ts` (lines 35-52):**
```typescript
test('register with mismatched passwords shows error', async ({ page }) => {
    await page.goto(`${FRONTEND}/auth/register`);
    await page.fill('input[placeholder="Acme Corp"]', 'Test WS');
    // ... this may or may not submit, but other tests do register
});
```

The frontend-journey tests use Playwright's browser automation (filling forms, clicking buttons) to register real users. The auth.spec.ts tests navigate to real pages. Both write to the development database.

---

## Finding 10: Windows-Specific Considerations

1. **`asyncio.get_event_loop()` on Python 3.12/Windows:** More likely to fail on Windows due to different thread/proactor policies. The ProactorEventLoop on Windows handles subprocesses differently.

2. **Process spawning:** Playwright spawns `npm run dev` as a child process. On Windows, this uses `cmd /c` which has different signal handling than Unix. Killing the process may not clean up child processes (node).

3. **No file locking issues for SQLite:** Since PostgreSQL is used (not SQLite), Windows file locking is not a factor here. However, if someone tried to switch to SQLite for tests, the `aiofiles`/asyncpg access patterns would fail on Windows due to file locking.

---

## Root Cause Summary

| Failure Mode | Root Cause | Finding |
|---|---|---|
| Combined E2E suite failures | Connection pool exhaustion + tenant slug collisions | #4, #3 |
| Backend requiring restarts | `asyncio.get_event_loop()` crash + pool exhaustion + no health check gating | #7, #4, #5 |
| Database pollution between suites | E2E tests write to dev DB with no isolation | #1, #2, #9 |
| Stale state between test files | No test database, no cleanup, global singleton | #6, #1 |

---

## Recommended Remediation (Priority Order)

### P0 — Immediate (unblocks combined test runs)

1. **Create a test database URL setting:**
   - Add `TEST_DATABASE_URL` to `app/core/config.py`
   - Add `test` environment detection
   - Backend reads the test DB URL when in test mode

2. **Add `app.state.testing` flag and use it:**
   - The RateLimitMiddleware already checks `app.state.testing` (line 76)
   - Set this flag when the backend starts in test mode
   - This disables rate limiting AND signals test mode to all middleware

3. **Fix `asyncio.get_event_loop()` in `app/db.py`:**
   ```python
   # Replace:
   loop = asyncio.get_event_loop()
   # With:
   loop = asyncio.get_running_loop()
   ```
   Or better, make `init_db()` fully async without `run_in_executor`.

### P1 — Short-term (enables reliable E2E)

4. **Configure Playwright to start the backend:**
   - Change `webServer.command` to start BOTH frontend and backend:
     ```
     "cmd /c uvicorn app.main:app --host 0.0.0.0 --port 8000 && cd frontend && npm run dev"
     ```
   - Or use a script that starts both processes
   - Set `reuseExistingServer: false` for E2E runs

5. **Add a health check gate:**
   - In Playwright config, add a `beforeStart` or custom wait for `http://localhost:8000/health/ready`
   - Wait for 200 before running tests

6. **Reduce Playwright workers for E2E:**
   - Set `workers: 1` or `workers: 2` for E2E tests (they share a database)
   - Keep `fullyParallel: true` for UI parallelism within a spec

### P2 — Medium-term (proper isolation)

7. **Create a dedicated test database:**
   - Run migrations against `swarmvault_test` at backend test startup
   - Drop/recreate between test runs

8. **Add transaction wrapping for E2E:**
   - Wrap each Playwright test's database writes in a transaction
   - Rollback after each test (requires backend-side test hook)

9. **Add unique workspace slug generation:**
   - Replace `Date.now()` with UUID-based slugs in E2E tests
   - Or add a backend endpoint for test-mode registration that auto-generates unique slugs

10. **Increase connection pool or configure pool_pre_ping:**
    - Add `pool_pre_ping=True` to detect stale connections
    - Increase `pool_size` for test environments
    - Consider `poolclass=NullPool` for test mode

---

## Affected Files

| File | Issue |
|---|---|
| `app/core/config.py` | Missing `TEST_DATABASE_URL` and test environment mode |
| `app/db.py` | `asyncio.get_event_loop()` deprecation, no test DB support |
| `app/main.py` | Module-level singleton `audit` buffer, no test mode flag, no `__main__` |
| `app/middleware/rate_limit.py` | Checks `app.state.testing` but it's never set |
| `frontend/playwright.config.ts` | Only starts frontend, not backend; `reuseExistingServer: true`; unlimited workers |
| `frontend/e2e/api-e2e.spec.ts` | Writes to real DB, timestamp-based slugs |
| `frontend/e2e/golden-journey.spec.ts` | Writes to real DB, timestamp-based slugs |
| `frontend/e2e/frontend-journey.spec.ts` | Writes to real DB via browser automation |
| `frontend/e2e/auth.spec.ts` | May create real records |
| `frontend/e2e/dashboard.spec.ts` | Reads from real DB |
| `app/api/auth.py` | Slug collision vulnerability on `tenants.slug` unique constraint |
| `app/models.py` | `Tenant.slug` has `unique=True` but no collision handling |
| `app/services/audit/service.py` | In-memory buffer without overflow protection |
| `tests/conftest.py` | Correctly isolated unit tests (contrast with E2E) |
