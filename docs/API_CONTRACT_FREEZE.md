# SwarmVault WebApp — API Contract Freeze
**Version:** 1.0.0
**Release:** `0534efe426e42f9c03f1622dd792f052647038cc`
**Base URL:** `/api/v1`
**Status:** FROZEN

---

## Purpose

This document is the **authoritative contract** between the SwarmVault backend and any independently built frontend. Frontend developers must implement against this contract and must not infer undocumented backend behavior.

Changes to this contract require a formal change proposal with backward compatibility analysis.

---

## 1. Base Configuration

| Setting | Value | Notes |
|---------|-------|-------|
| API Base URL | `{host}/api/v1` | Configure per environment |
| Docs URL | `{host}/docs` | Disabled in production |
| Redoc URL | `{host}/redoc` | Disabled in production |
| Content-Type | `application/json` | All endpoints except file upload |
| Auth Header | `Authorization: Bearer <access_token>` | Every protected endpoint |
| Workspace Header | `X-Workspace-Id: <workspace_id>` | Optional — overrides default workspace from JWT |

## 2. Authentication

### Token Lifecycle

```
Register/Login → access_token (60 min) + refresh_token (30 days)
     ↓
Use access_token in Authorization header
     ↓
Before expiry: POST /auth/refresh → new access_token
     ↓
Logout: POST /auth/logout → refresh_token revoked
```

### Storage Recommendation

Store `access_token` in memory (variable). Store `refresh_token` in `httpOnly` cookie or secure storage. Never use plain `localStorage` in production.

### Token Format

- `access_token`: JWT signed with HS256
- `refresh_token`: Opaque string stored in database
- `token_type`: always `"bearer"`
- `expires_in`: seconds until access token expires (default 3600)

### Expiration Handling

- 401 response → attempt refresh
- Refresh fails → redirect to login
- Frontend should proactively refresh at 80% of `expires_in`

## 3. Error Contract

All errors follow this structure:

```json
{
  "error": {
    "type": "error_code",
    "message": "Human-readable description",
    "request_id": "uuid"
  }
}
```

| HTTP | Type | Meaning | Retryable |
|------|------|---------|-----------|
| 400 | `validation_error` | Bad request body | No |
| 401 | `unauthorized` | Missing/invalid/expired token | Yes (after refresh) |
| 403 | `forbidden` | Insufficient role or policy | No |
| 404 | `not_found` | Resource not found | No |
| 405 | `method_not_allowed` | Wrong HTTP method | No |
| 409 | `conflict` | Duplicate or state conflict | No |
| 422 | `validation_error` | Schema validation failure | No |
| 429 | `rate_limit_exceeded` | Rate limit hit | Yes (after Retry-After) |
| 500 | `internal_error` | Server error | Yes (after backoff) |
| 503 | `service_unavailable` | DB unavailable | Yes (after backoff) |

**Headers to check:**
- `Retry-After` on 429 responses
- `X-Request-ID` on all responses (for support correlation)

## 4. Pagination

Two pagination models are used:

### Offset/Limit (most endpoints)

```
GET /endpoint?limit=20&offset=0
```

Response includes `total` count where noted (facts, decisions, timeline, sources, feedback, jobs).

### No Pagination (memory list)

`GET /memory/` returns all results within the `limit` cap (max 200). No `total` field.

### Inconsistent Totals

| Endpoint | Returns `total` |
|---|---|
| GET /ingest/facts | YES |
| GET /ingest/decisions | YES |
| GET /ingest/timeline | YES |
| GET /ingest/sources | YES |
| GET /feedback/ | YES |
| GET /ingest/jobs | YES |
| GET /memory/ | NO |
| GET /memory/search | NO |
| GET /sessions/ | NO |
| GET /provenance/ | NO |

**Frontend must handle both patterns.**

## 5. SSE / Chat Streaming

### Endpoint

```
POST /api/v1/chat/stream
Content-Type: application/json
Accept: text/event-stream
```

### Events

| Event | When | Payload |
|-------|------|---------|
| `sources` | Before text streaming | `{"type":"sources","sources":[...]}` |
| `token` | During text streaming | `{"type":"token","content":"..."}` |
| `done` | Stream complete | `{"type":"done","message_id":"...","session_id":"...","usage":{},"latency_ms":N,"memory_grounded":bool}` |
| `error` | Stream failure | `{"type":"error","detail":"..."}` |

### Frontend Implementation

Use `fetch()` with `ReadableStream` reader. Do NOT use `EventSource` (requires GET, this is POST).

Cancellation: use `AbortController`.

## 6. File Upload

```
POST /api/v1/storage/upload
Content-Type: multipart/form-data
Body: file=<binary>
```

Response:
```json
{
  "key": "workspace_id/filename",
  "url": "http://host/storage/...",
  "size": 1024,
  "content_type": "application/pdf",
  "sha256": "hex_hash"
}
```

**Rate limit:** 5 uploads per hour per user.

## 7. CORS

### Development
```
Access-Control-Allow-Origin: *
Allow-Credentials: true
```

### Production
```
Access-Control-Allow-Origin: <configured origins only>
Allow-Credentials: true
Methods: GET, POST, PATCH, DELETE, OPTIONS
Headers: Authorization, Content-Type, X-Request-ID
Max-Age: 600
```

**Production requirement:** `CORS_ORIGINS` must be set to specific origins (no wildcard). If unset, startup fails.

### Preflight
OPTIONS requests are handled automatically by CORSMiddleware. Frontend should not need to handle CORS preflight manually.

## 8. Rate Limiting

Rate limits are applied per-client (authenticated: per-user; unauthenticated: per-IP).

| Path | Limit | Window |
|------|-------|--------|
| `/api/v1/auth/register` | 10 | 60s |
| `/api/v1/auth/login` | 10 | 60s |
| `/api/v1/chat/*` | 30 | 60s |
| `/api/v1/ingest/upload` | 5 | 3600s (1h) |
| `/api/v1/ingest/search` | 60 | 60s |

On 429: `Retry-After` header tells seconds to wait.

## 9. Security Headers

Every response includes:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

In production only:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: restrictive (no unsafe-inline/eval)
```

In development:
```
Content-Security-Policy: permissive (allows unsafe-inline/eval, localhost websockets)
```

## 10. Health Endpoints

| Endpoint | Auth | Purpose | Frontend Use |
|----------|------|---------|-------------|
| GET /health/live | No | Liveness probe | Infrastructure only |
| GET /health/ready | No | Readiness probe (checks DB) | Infrastructure only |
| GET /health | No | Legacy health | Infrastructure only |

**Do not expose these in the UI.** They are for load balancers and orchestrators.

## 11. ID Format

All IDs are UUID strings. Example: `"550e8400-e29b-41d4-a716-446655440000"`

Frontend should treat IDs as opaque strings. Do not assume integer IDs.

## 12. Timestamp Format

All timestamps are ISO 8601 UTC strings:
```
"2026-01-01T00:00:00Z"
```

Frontend should parse with a robust ISO 8601 parser. Do not assume local time.

## 13. Enumerated Values

### Roles
```
owner > admin > member > viewer
```

### Memory Types
```
procedural_memory (default)
episodic_memory
semantic_memory
```

### Temporal Status
```
current
superseded
deprecated
```

### Feedback Rating
```
thumbs_up
thumbs_down
```

### Ingestion Source Types
```
text
json
jsonl
chatgpt
```

### Ingestion Status
```
queued
processing
completed
failed
cancelled
```

### Ingestion Stage
```
queued
parsing
extracting
classifying
storing
completed
error
```

### Chat Message Role
```
user
assistant
system
```

### Policy Effect
```
allow
deny
require_confirmation
allow_with_limits
allow_redacted
```

### Policy Status
```
active
inactive
draft
```

### Invitation State
```
pending
accepted
declined
expired
revoked
```

## 14. Known Contract Gaps

| # | Gap | Severity | Impact on Frontend |
|---|---|---|---|
| 1 | `/chat/stream` has no RBAC (unlike `/chat/` which requires viewer) | P1 | Any authenticated user can stream; inconsistent with non-streaming |
| 2 | Audit endpoints at `/api/v1/api/v1/audit/...` (double prefix) | P2 | Frontend must use wrong path until backend fixes |
| 3 | `GET /memory/` returns no `total` count | P2 | Frontend cannot show "Showing X of Y" for memory list |
| 4 | `GET /sessions/` returns no `total` count | P2 | Frontend cannot show total session count |
| 5 | `GET /provenance/` returns no `total` count | P2 | Frontend cannot paginate provenance reliably |
| 6 | No file list endpoint in storage | P2 | Frontend must track uploaded file keys locally |
| 7 | `GET /workspace/workspaces/all` returns `list[dict]` (untyped) | P3 | Frontend must handle dynamic dict fields |
| 8 | `GET /workspace/workspaces/available` returns `list[dict]` (untyped) | P3 | Frontend must handle dynamic dict fields |
| 9 | No SSE cancel endpoint — frontend must use AbortController | P3 | Standard pattern, but undocumented |

### Non-Gaps (frontend concerns, not contract issues)

| Item | Assessment |
|------|------------|
| SSE token granularity | Server controls chunk size — frontend must handle any chunk size |
| Retrieval quality | Backend controls relevance — frontend displays what it receives |
| LLM provider selection | Backend-controlled via config |
| Memory temporal supersession | Backend-enforced via `temporal_status` — frontend displays status |

## 15. Versioning

- Current API version: **v1**
- All endpoints are prefixed with `/api/v1`
- Breaking changes require a new version prefix (`/api/v2`)
- Deprecated endpoints will return a `Deprecation` header before removal
- Minimum 6-month deprecation notice for breaking changes

## 16. Stability Classification

| Classification | Meaning | Frontend Use |
|---------------|---------|-------------|
| **FROZEN** | Contract is stable, will not change without version bump | Safe for production UI |
| **STABLE** | Contract is unlikely to change, minor additions possible | Safe for production UI |
| **PROVISIONAL** | Contract may change, not for production | Internal/testing only |
| **INTERNAL** | Backend-only, not for frontend consumption | Do not use |
| **DEPRECATED** | Will be removed | Do not use |

### Endpoint Stability

| Endpoint | Classification |
|----------|---------------|
| All AUTH endpoints | FROZEN |
| All WORKSPACE endpoints | FROZEN |
| All PROJECT endpoints | FROZEN |
| All SESSION endpoints | FROZEN |
| POST /chat/ | FROZEN |
| POST /chat/stream | FROZEN |
| All MEMORY endpoints | FROZEN |
| All INGESTION endpoints | FROZEN |
| All PROVENANCE endpoints | FROZEN |
| All DASHBOARD endpoints | FROZEN |
| All FEEDBACK endpoints | FROZEN |
| All API KEYS endpoints | FROZEN |
| All STORAGE endpoints | FROZEN |
| All POLICY endpoints | STABLE (admin features, may evolve) |
| All AUDIT endpoints | STABLE (double-prefix to be fixed) |
| All HEALTH endpoints | FROZEN (infrastructure only) |
