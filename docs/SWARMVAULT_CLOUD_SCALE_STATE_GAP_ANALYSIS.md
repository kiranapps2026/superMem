# SwarmVault Cloud-Scale State Gap Analysis

**Forensic status**: Source-first. Every claim traced to actual implementation.
**Created**: 2026-09-10

---

## 1. Executive Summary

SwarmVault is architected as a single-process FastAPI application with PostgreSQL as the sole persistence layer. There is no horizontal scaling support, no distributed state management, no caching layer, no read replicas, no sharding, and no multi-node coordination. This is appropriate for a single-tenant or small-team deployment but creates fundamental blockers for enterprise scale.

| Dimension | Status |
|-----------|--------|
| Horizontal scaling (multiple app instances) | NOT SUPPORTED |
| Distributed session affinity | MISSING |
| Shared cache (Redis/Memcached) | MISSING |
| Database connection pooling | PARTIAL (SQLAlchemy default) |
| Read replicas | MISSING |
| Database sharding | MISSING |
| Rate limiting | PARTIAL (in-memory, not distributed) |
| Background task distribution | MISSING |
| Distributed locking | MISSING |
| Event sourcing | MISSING |
| CQRS | MISSING |
| Idempotency keys | MISSING |
| Optimistic concurrency | MISSING |
| Pessimistic concurrency | MISSING |
| Health/readiness checks | PARTIAL |
| Graceful shutdown | PARTIAL |
| Circuit breaker | MISSING |
| Bulkhead pattern | MISSING |
| Request timeout | PARTIAL (schema-level only) |
| Payload size limits | PARTIAL (connector-level only) |
| Distributed tracing | MISSING |
| Metrics export | MISSING |

---

## 2. Application-Level State

### 2.1 In-Memory State Is Not Shared Across Instances

**Evidence**: Multiple components hold in-memory state that is lost on restart and not shared across instances:

| Component | State | Location | Shared? |
|-----------|-------|----------|---------|
| Policy Engine | Loaded policies | `app/services/policy/engine.py` | NO |
| LLM Provider | Provider instance | `app/services/llm.py` | NO |
| Memory Service Cache | `_cache: dict[str, MemoryRecord]` | `app/services/memory.py` | NO |
| Rate Limiter | In-memory counter | `app/middleware/rate_limit.py` | NO |
| Audit Service | Event buffer | `app/services/audit/` | NO |
| Connector Registry | Class references | `app/services/connectors.py` | NO |

**Impact**: Deploying 2+ instances of the app results in:
- Different policy state per instance (stale policies if re-loaded)
- Rate limiting that counts per-instance, not globally (each instance allows its own limit)
- Memory cache that is cold on each instance
- Audit events that may be lost if instance crashes before flush

### 2.2 Policy Engine Is Loaded Once at Startup

**Evidence**: `app/services/policy/engine.py` — policies are loaded from database at engine initialization. No refresh mechanism. No policy version tracking.

**Impact**: If policies are updated in the database, running instances continue serving stale policies until restart.

---

## 3. Rate Limiting

### 3.1 In-Memory Implementation

**Evidence**: `app/middleware/rate_limit.py` — uses an in-memory dictionary with TTL-based expiration.

```python
class RateLimiter:
    def __init__(self):
        self._requests: dict[str, list[float]] = {}
```

**Gaps**:
- Per-instance only — 10 requests/minute limit is per-app-instance, not global
- No Redis backing
- No distributed coordination
- Memory leak potential (stale entries not cleaned on shutdown)
- No burst allowance configuration
- No per-user vs per-IP differentiation visible in source

### 3.2 No Rate Limit on Ingestion Endpoint

**Evidence**: `app/api/ingest.py` — `upload_and_ingest()` does not apply rate limiting. The 10MB content limit is the only protection.

**Impact**: A single user can submit unlimited concurrent ingestion requests, each running the full pipeline synchronously.

---

## 4. Database Access Patterns

### 4.1 No Connection Pool Configuration Visible

**Evidence**: `app/db.py` — creates engine with:
```python
engine = create_async_engine(settings.database_url)
```

No explicit pool size, pool timeout, pool recycle, or overflow configuration. SQLAlchemy defaults apply (pool_size=5, max_overflow=10).

**Impact**: Under concurrent load, connection acquisition may timeout. No monitoring of pool saturation.

### 4.2 No Transaction Boundary Management

**Evidence**: `run_pipeline()` uses `db.flush()` throughout but does not manage transaction boundaries explicitly. The caller (`ingest.py`) does `await db.commit()` only at the end.

**Gap**: If the pipeline fails at M4 (after M0-M3 have flushed), the earlier stages are NOT rolled back. Partial state persists in the database.

**Evidence**: `pipeline.py` — on exception, only `source.status = "failed"` is set. Earlier-created `Session`, `NormalizedMessage`, `Fact`, `Decision` records are not deleted.

### 4.3 No Optimistic or Pessimistic Locking

**Evidence**: No `with_for_update()`, no version columns, no optimistic concurrency control anywhere in the codebase.

**Impact**: Concurrent ingestion of the same content could create duplicate records despite the content-hash dedup (which checks only after the fact).

---

## 5. Health and Readiness

### 5.1 Health Endpoint

**Evidence**: `app/api/dashboard.py` — has a health check endpoint. No detailed component health (database, LLM provider, policy engine).

### 5.2 No Readiness Probe

**Evidence**: No `/ready` endpoint that checks database connectivity, policy engine readiness, and LLM provider availability before accepting traffic.

### 5.3 No Liveness Probe with Dependency Check

**Evidence**: Health check does not verify:
- Database connection pool availability
- LLM provider API key validity
- Policy engine state
- Disk space for PostgreSQL
- Memory usage

---

## 6. Graceful Shutdown

### 6.1 No Shutdown Handler

**Evidence**: `app/main.py` — no `@app.on_event("shutdown")` handler registered.

**Impact**: On SIGTERM (container stop, deploy, scale-down):
- In-flight HTTP requests are terminated immediately
- In-memory audit events are lost
- Memory cache is not flushed
- No drain period for in-flight ingestion jobs

### 6.2 No Startup Health Check

**Evidence**: No `@app.on_event("startup")` handler that verifies database connectivity before accepting traffic.

---

## 7. Observability

### 7.1 Structured Logging

**Evidence**: Python `logging` module is used. No structured JSON logging configuration visible. No log level configuration via environment variables visible in `app/core/config.py`.

### 7.2 No Metrics Export

**Evidence**: No Prometheus metrics, no OpenTelemetry, no StatsD. No `/metrics` endpoint.

### 7.3 No Distributed Tracing

**Evidence**: No OpenTelemetry, no Jaeger, no Zipkin integration. Request tracing is limited to `request_id` in audit events.

### 7.4 Timing in chat_orchestrator

**Evidence**: `chat_orchestrator.py` records `latency_ms` but only stores it in `MessageProvenance`. No histogram, no percentile tracking, no alerting.

---

## 8. Deployment Architecture

### 8.1 No Docker Compose Multi-Service Config

**Evidence**: No `docker-compose.yml` found. Only single-service Dockerfile implied.

### 8.2 No Horizontal Scaling Configuration

**Evidence**: No load balancer config, no sticky session configuration, no session affinity, no shared session store.

### 8.3 No Environment-Based Configuration Validation

**Evidence**: `app/core/config.py` — settings are loaded but no validation that required settings (database URL, API keys) are present at startup.

---

## 9. Cloud-Scale Gap Matrix

| Gap | Severity | Blocks Scale | Blocks Persistent Memory | Evidence |
|-----|----------|-------------|--------------------------|----------|
| No distributed rate limiting | HIGH | YES | NO | `app/middleware/rate_limit.py` |
| No background task queue | HIGH | YES | YES | No Celery/RQ dependency |
| No connection pool tuning | MEDIUM | YES | NO | `app/db.py` |
| No transaction rollback on pipeline failure | HIGH | NO | YES | `app/services/pipeline.py` |
| No optimistic/pessimistic locking | MEDIUM | YES | PARTIAL | `app/models.py` |
| No distributed cache | MEDIUM | YES | NO | `app/services/memory.py:_cache` |
| No graceful shutdown | MEDIUM | YES | NO | `app/main.py` |
| No startup health check | MEDIUM | YES | NO | `app/main.py` |
| No metrics export | LOW | PARTIAL | NO | No metrics library |
| No distributed tracing | LOW | PARTIAL | NO | No tracing library |
| Policy engine no refresh | MEDIUM | YES | PARTIAL | `app/services/policy/engine.py` |
| No idempotency keys | MEDIUM | YES | NO | `app/api/ingest.py` |
| No circuit breaker on LLM calls | MEDIUM | YES | NO | `app/services/chat_orchestrator.py` |

---

## 10. What a Future Memory Intelligence Layer Must Not Assume

1. **Do not assume rate limiting is global**: It is per-instance. Concurrent instances each allow their own limit.
2. **Do not assume policy consistency across instances**: Policies loaded at startup are not refreshed.
3. **Do not assume ingestion is atomic**: Partial pipeline failure leaves orphaned records.
4. **Do not assume graceful degradation under load**: No circuit breaker, no bulkhead, no timeout on LLM calls.
5. **Do not assume observability**: No metrics, no distributed traces, no structured logs by default.

---

## 11. Required Conditions Before Enterprise Scale

1. **Distributed rate limiting** — Redis-backed rate limiter
2. **Background task queue** — Celery or equivalent with Redis broker
3. **Connection pool configuration** — explicit pool sizing and monitoring
4. **Transaction atomicity for pipeline** — rollback on failure, or compensating deletes
5. **Concurrency control** — optimistic locking or advisory locks for concurrent ingestion
6. **Graceful shutdown** — drain period, in-flight request completion
7. **Startup health check** — verify dependencies before accepting traffic
8. **Policy engine refresh** — periodic policy reload or change notification
9. **Idempotency keys** — for safe retry of ingestion and chat requests
10. **Structured logging** — JSON output with correlation IDs
