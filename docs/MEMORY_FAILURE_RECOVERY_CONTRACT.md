# Memory Failure Recovery Contract
**Phase**: M-ARCH — Memory Architecture Freeze Gate
**Status**: PROPOSED — requires review and approval before implementation
**Created**: 2026-09-10

---

## 1. Purpose

This contract defines how SwarmVault behaves when components fail, how it
recovers from failures, and what guarantees it provides about memory integrity
under failure conditions.

---

## 2. Failure Taxonomy

### 2.1 By Component

| Component | Failure Mode | Impact |
|-----------|-------------|--------|
| PostgreSQL | Unavailable | All reads/writes fail — total outage |
| PostgreSQL | Connection pool exhaustion | New requests queue; existing transactions complete |
| PostgreSQL | Partial write (mid-transaction) | Orphaned records — pipeline stages without parent |
| LLM Provider | Timeout | Chat responses fail; ingestion M1/M2 fails |
| LLM Provider | Auth failure | Same as timeout |
| LLM Provider | Rate limit | Chat responses degraded; ingestion queued/failed |
| Policy Engine | Stale policies | Authorization may be wrong (deny or allow incorrectly) |
| Memory Service Cache | Corrupt | Falls back to DB — no data loss |
| Rate Limiter | Reset on restart | Burst of requests allowed after restart |
| Audit Buffer | Lost on crash | Audit events missing for in-flight operations |
| Ingestion Pipeline | Exception at M2/M3/M4 | Partial state — Source exists but no facts/decisions |
| SSE Connection | Client disconnect | Stream terminates; partial message may be persisted |

### 2.2 By Severity

| Severity | Definition | Examples |
|----------|-----------|---------|
| P0 — Critical | Data loss or security breach | DB corruption, auth bypass |
| P1 — High | Service unavailable or data inconsistency | LLM outage, partial pipeline failure |
| P2 — Medium | Degraded service, recoverable | Rate limiter reset, stale cache |
| P3 — Low | Minor inconvenience | Slow retrieval, missing embeddings |

---

## 3. Current Failure Handling

### 3.1 Pipeline Failure (Current)

```python
# app/services/pipeline.py — exception handler
except Exception as exc:
    source.status = "failed"
    source.error_message = str(exc)
    await db.flush()
    raise
```

**Problems**:
1. Only the `Source` record is marked failed — earlier-created records persist:
   - `Session` record exists with no messages
   - `NormalizedMessage` records exist with no facts
   - Partial M2 facts may exist with no M3/M4 enrichment
2. No compensating delete for orphaned records
3. No retry mechanism
4. The exception propagates to the HTTP response — no graceful degradation

### 3.2 LLM Failure (Current)

```python
# app/services/chat_orchestrator.py
provider = get_llm_provider()
result = await provider.chat_completion(...)
```

**Problems**:
1. No timeout at the LLM call level (only config-level `llm_timeout_seconds`)
2. No circuit breaker — repeated failures accumulate
3. No fallback provider
4. Error propagates to user as 500

### 3.3 Database Failure (Current)

```python
# app/db.py
engine = create_async_engine(settings.database_url)
```

**Problems**:
1. No connection pool monitoring
2. No retry on connection failure
3. No circuit breaker
4. No graceful degradation (returns 503 only if FastAPI handles it)

---

## 4. Required Recovery Mechanisms

### 4.1 Pipeline Atomicity

**Problem**: Pipeline failure at M2 leaves Source + Session + NormalizedMessages
but no Facts/Decisions/Graph.

**Solution — Option A: Transaction Rollback** (Preferred)

```python
async def run_pipeline(db, ...):
    async with db.begin() as transaction:
        # All M0-M4 operations within this transaction
        source = ...
        session = ...
        messages = ...
        facts = ...
        decisions = ...
        graph = ...
    # Commit happens here — all or nothing
```

**Solution — Option B: Compensating Deletes** (Fallback)

```python
except Exception as exc:
    # Delete orphaned records created before failure point
    await db.execute(delete(NormalizedMessage).where(NormalizedMessage.source_id == source_id))
    await db.execute(delete(Session).where(Session.id == session_id))
    source.status = "failed"
    source.error_message = str(exc)
    await db.commit()
    raise
```

### 4.2 LLM Circuit Breaker

```python
class LLMCircuitBreaker:
    FAILURE_THRESHOLD = 5
    RECOVERY_TIMEOUT = 60  # seconds

    def __init__(self):
        self.failures = 0
        self.last_failure = None
        self.state = "closed"  # closed | open | half-open

    async def call(self, provider, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure > self.RECOVERY_TIMEOUT:
                self.state = "half-open"
            else:
                raise LLMUnavailableError("Circuit breaker open")
        try:
            result = await provider.chat_completion(*args, **kwargs)
            self.failures = 0
            self.state = "closed"
            return result
        except Exception:
            self.failures += 1
            self.last_failure = time.time()
            if self.failures >= self.FAILURE_THRESHOLD:
                self.state = "open"
            raise
```

### 4.3 Retry with Backoff

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
)
async def call_llm_with_retry(provider, messages, **kwargs):
    return await provider.chat_completion(messages, **kwargs)
```

**Retry policy**:
- LLM calls: 3 attempts, exponential backoff (1s, 2s, 4s)
- Database writes: 2 attempts, no backoff (transaction will rollback)
- External API calls: 3 attempts, exponential backoff

### 4.4 Graceful Shutdown

```python
# app/main.py

@app.on_event("shutdown")
async def shutdown():
    """Graceful shutdown with drain period."""
    # 1. Stop accepting new requests (handled by load balancer)
    # 2. Wait for in-flight requests to complete (max 30s)
    # 3. Flush audit buffer
    await audit_service.flush()
    # 4. Close LLM provider connections
    await provider.aclose()
    # 5. Dispose database connections
    await engine.dispose()
```

### 4.5 Audit Buffer Persistence

```python
class AuditService:
    def __init__(self):
        self._buffer: list[AuditEvent] = []
        self._flush_interval = 5  # seconds

    async def emit(self, event):
        self._buffer.append(event)
        if len(self._buffer) >= self._flush_threshold:
            await self.flush()

    async def flush(self):
        if not self._buffer:
            return
        # Batch insert to database
        await self._repo.bulk_create(self._buffer)
        self._buffer.clear()

    async def flush_on_shutdown(self):
        """Final flush — guaranteed delivery."""
        while self._buffer:
            try:
                await self.flush()
            except Exception:
                await asyncio.sleep(1)  # Retry on failure
```

---

## 5. Memory Integrity Guarantees

### 5.1 Guarantees Provided Today

| Guarantee | Level | Evidence |
|-----------|-------|----------|
| No duplicate facts (same subject+predicate+object) | STRONG | Content hash dedup + supersession logic |
| No cross-tenant data leakage | STRONG | `TenantContext` middleware on all endpoints |
| Audit trail for ingestion | STRONG | `AuditEvent` records for ingest start/end |
| Soft-delete preservation | STRONG | `deleted_at` column, never hard-deleted via API |
| Refresh token revocation | STRONG | `RefreshToken.revoked` flag |
| API key hashing | STRONG | SHA-256 hash, never plaintext |

### 5.2 Guarantees NOT Provided Today

| Guarantee | Level | Risk |
|-----------|-------|------|
| Pipeline atomicity | NONE | Partial state on failure |
| Retrieval consistency across instances | NONE | Per-instance caches/rate limits |
| LLM availability | NONE | No circuit breaker, no fallback |
| Graceful shutdown | NONE | No shutdown handler |
| Audit completeness | NONE | Buffer lost on crash |
| Memory cache coherence | NONE | Per-instance cache |
| Idempotent ingestion | NONE | Retry creates duplicates |
| Rate limit global consistency | NONE | Per-instance counters |

---

## 6. Recovery Procedures

### 6.1 Orphaned Pipeline Records

**Detection**:
```sql
SELECT s.id FROM sources s
WHERE s.status = 'failed'
  AND EXISTS (SELECT 1 FROM sessions ss WHERE ss.id = s.id)
  AND NOT EXISTS (SELECT 1 FROM facts f WHERE f.source_id = s.id);
```

**Recovery**:
1. Identify failed sources
2. Delete orphaned `NormalizedMessage`, `Session` records
3. Optionally re-queue for ingestion

### 6.2 Stale Facts (After Supersession Bug)

**Detection**:
```sql
SELECT f.id FROM facts f
WHERE f.temporal_status = 'historical'
  AND f.superseded_by_id IS NULL;
```

**Recovery**: Facts marked `historical` without `superseded_by_id` need manual
review or re-ingestion.

### 6.3 Partial Graph State

**Detection**:
```sql
SELECT ge.id FROM graph_edges ge
WHERE NOT EXISTS (SELECT 1 FROM graph_nodes gn WHERE gn.id = ge.source_node_id)
   OR NOT EXISTS (SELECT 1 FROM graph_nodes gn WHERE gn.id = ge.target_node_id);
```

**Recovery**: Delete orphaned edges, re-run M4 for affected sources.

### 6.4 Cache Poisoning

**Detection**: Unusual cache hit rate or stale data patterns.
**Recovery**: Restart instances (clears in-memory caches).

---

## 7. Monitoring Requirements

| Metric | Alert Threshold | Action |
|--------|----------------|--------|
| Pipeline failure rate | > 5% of ingestions | Page on-call |
| LLM error rate | > 10% of chat requests | Page on-call |
| Database connection pool saturation | > 80% | Scale up or investigate |
| Audit buffer size | > 1000 events | Flush or investigate |
| Memory cache hit rate | < 50% | Tune cache size |
| Rate limit rejection rate | > 20% | Check for abuse or tune limits |
| Orphaned pipeline records | Any | Auto-remediation job |

---

## 8. Implementation Requirements

| Requirement | Priority | Effort |
|-------------|----------|--------|
| Pipeline transaction atomicity | P0 | MEDIUM |
| LLM circuit breaker | P1 | MEDIUM |
| LLM retry with backoff | P1 | LOW |
| Graceful shutdown handler | P1 | LOW |
| Audit buffer persistence on shutdown | P1 | MEDIUM |
| Compensating deletes for partial pipeline | P0 | MEDIUM |
| Idempotency key support | P1 | MEDIUM |
| Orphaned record detection job | P2 | MEDIUM |
| Monitoring/alerting setup | P2 | HIGH |
