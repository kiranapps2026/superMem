# SwarmVault Security & Operational Architecture

> Forensic read from source. Generated 2026-09-10. Do not infer from filenames.

---

## 1. Authentication Architecture

### Password Hashing (`app/core/security.py:1-50`)

- Algorithm: **bcrypt** via `passlib.context.CryptContext`
- Scheme: `bcrypt`
- Configuration: `passlib.context.CryptContext(schemes=["bcrypt"], deprecated="auto")`
- No explicit rounds parameter specified -- uses passlib default (typically 29000 rounds)
- `verify_password(plain, hashed)` returns boolean
- `hash_password(plain)` returns bcrypt hash string

### JWT Tokens (`app/core/security.py:52-100`)

- Library: `python-jose` (`jose` package)
- Algorithm: **HS256** (HMAC-SHA256), single symmetric key
- `create_access_token(data: dict, expires_delta: timedelta | None = None)`:
  - Copies input dict, adds `exp` claim
  - Encodes with `settings.secret_key` and `settings.algorithm`
  - Default expiry: 60 minutes (`access_token_expire_minutes=60`, `.env.example:16`)
- `decode_access_token(token: str)`:
  - Decodes JWT with `jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])`
  - Returns payload dict or `None` on `JWTError`
  - Does NOT verify subject claim -- caller must check `sub`
- Claims: `sub` = user_id, `exp` = expiry timestamp
- No `iat`, `aud`, `iss` claims present

### Refresh Tokens

- Stored in `refresh_tokens` table (`app/models.py:147-163`)
- Fields: `id` (UUID), `user_id` (FK), `token` (String(512), unique, indexed), `expires_at` (datetime), `revoked` (boolean, default False), `created_at`
- Max length 512 chars for token storage
- Linked to `User` via ORM relationship
- JWT-based refresh: `/api/v1/auth/refresh` endpoint accepts raw token
- No database-level check observed for refresh in `security.py` -- refresh endpoint logic is in the auth router (not read for this document)
- Revocation flag exists on model but revocation logic is in auth router

### Session Management

- No server-side session store observed
- Authentication is entirely JWT + refresh token based
- `require_auth` middleware (`app/middleware/auth.py:17-51`):
  - Extracts token from `Authorization: Bearer` header via `OAuth2PasswordBearer(auto_error=False)`
  - Decodes token via `security.decode_access_token()`
  - Checks `payload.get("sub")` for user_id
  - Queries DB for `User` where `id == user_id AND deleted_at IS NULL`
  - Returns 401 if user is `None` or `not user.is_active`
  - Returns `User` object on success

### Login/Registration Endpoints (auth router -- inferred from schemas)

- Login: POST `/api/v1/auth/login` with `{email, password}` -> returns `TokenResponse{access_token, refresh_token, token_type, expires_in}`
- Register: POST `/api/v1/auth/register` with `{email, name, password, workspace_name}` -> returns tokens
- Refresh: POST `/api/v1/auth/refresh` with `{refresh_token}` -> returns new `TokenResponse`
- Logout: POST `/api/v1/auth/logout` with `{refresh_token}` -> 204
- Me: GET `/api/v1/auth/me` -> returns `UserOut`
- Change password: POST `/api/v1/auth/change-password` with `{current_password, new_password}`

---

## 2. Authorization Architecture

### Role Hierarchy (`app/middleware/rbac.py:17-30`)

Four roles with numeric hierarchy:

| Role | Level |
|---|---|
| OWNER | 1000 |
| ADMIN | 500 |
| MEMBER | 100 |
| VIEWER | 50 |

### Permission Matrix (`app/middleware/rbac.py:34-70`)

Each role inherits permissions from lower roles:

**OWNER** (highest): workspace.read, workspace.manage, members.read, members.manage, project.read/write/delete, memory.read/write/delete, chat.use, ingest.create/read, storage.read/write, api_key.manage

**ADMIN**: workspace.read, members.read/manage, project.read/write, memory.read/write, chat.use, ingest.create/read, storage.read/write, api_key.manage

**MEMBER**: workspace.read, project.read, memory.read/write, chat.use, ingest.create/read, storage.read

**VIEWER**: workspace.read, project.read, memory.read, chat.use, ingest.read

### Authorization Enforcement Points

**Two middleware patterns:**

1. **`require_permission(*permissions)`** (`rbac.py:83-102`):
   - Simple role-hierarchy check
   - Computes effective permissions for the user's role
   - Checks if ALL requested permissions are granted
   - Returns 403 with missing permissions list

2. **`require_min_role(min_role)`** (`rbac.py:105-140`):
   - Flows through `PolicyEngine.check_role_minimum()`
   - Generates synthetic `authorize.role:check` policies for every role level
   - DENY rules for below-threshold roles, ALLOW for at-or-above
   - Deny wins over allow (policies evaluated in order, DENY rules first)

### PolicyEngine (`app/services/policy/engine.py:241-678`)

Five effect types:

| Effect | Value | Behavior |
|---|---|---|
| ALLOW | `"allow"` | Grants access |
| DENY | `"deny"` | Denies immediately (short-circuits) |
| CONFIRM | `"require_confirmation"` | Requires explicit user confirmation |
| LIMITED | `"allow_with_limits"` | Grants with constraint limits |
| REDACTED | `"allow_redacted"` | Grants with field redactions |

**Evaluation rules** (`engine.py:257-373`):
- Rules evaluated in order
- First explicit DENY wins -- immediate return
- If no rule matches: returns `DEFAULT_DECISION` (DENY) -- **fail-closed**
- Explicit deny always overrides allow
- `EFFECT_CONFIRM` returns a decision that requires external confirmation (not evaluated here -- returned to caller)
- `EFFECT_REDACTED` returns with `limits` and `redactions` fields

**Resource matching** (`_match_resource`, `engine.py:90-126`):
- `"*"` matches any resource
- `"memory"` matches resource type `memory`
- `"tool.*"` matches any tool subtype
- `"memory:project_A"` matches specific resource_id
- Hierarchical: `"memory"` matches `"memory.foo.bar"`

**Action matching** (`_match_action`, `engine.py:129-147`):
- `"write"` matches `write`, `update`, `delete`
- `"read"` matches `read`, `search`
- `"*"` matches all actions

**Fail-Closed Verification** (`engine.py:273-280, 353-360`):

```python
if not rules:
    return PolicyDecision(decision=DEFAULT_DECISION, reason="no policies configured", risk=RISK_HIGH)
# ...
if not matched:
    return PolicyDecision(decision=DEFAULT_DECISION, reason="no matching policy rule found", risk=RISK_MEDIUM)
```

Where `DEFAULT_DECISION = EFFECT_DENY` (line 37). **Unknown or missing policies always DENY.**

### Default Tenant Policies (`engine.py:442-661`)

Generated per new tenant:
- Memory: full CRUD allow (delete = MEDIUM risk)
- Project: read/write allow
- Chat: model read, source read, provenance read, feedback write
- Ingest: connector execute, source write/delete
- Tools: read allow, execute CONFIRM (MEDIUM risk)
- API keys: write/delete allow (MEDIUM risk)
- Workspace write: DENY for non-owner/admin (CRITICAL risk, condition-based)
- Bulk export: CONFIRM (HIGH risk)
- Credentials/secrets: full DENY (CRITICAL risk)
- Note: `default-deny-export` policy appears twice (lines 617-627 and 647-659) -- duplicate, second one shadows first

---

## 3. Tenancy Architecture

### TenantContext (`app/middleware/tenancy.py:12-21`)

Dataclass with:
- `tenant_id`, `tenant_name`, `tenant_plan`
- `workspace_id`, `workspace_name`
- `role` (default "viewer")
- `user_id`

### Tenant Resolution (`get_tenant_context`, `tenancy.py:28-141`)

1. Extracts `Authorization: Bearer <token>` header
2. Decodes JWT with `jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])`
3. Validates `sub` claim for user_id
4. Queries `User` where `id == user_id AND deleted_at IS NULL`
5. Checks `user.is_active`
6. **Workspace resolution** (two paths):
   - If `X-Workspace-Id` header present: verifies membership in that workspace
   - If no header: auto-selects first workspace membership
7. If no membership: 404 "No workspace membership found"
8. Queries `Tenant` from workspace's `tenant_id`
9. Returns `TenantContext` with all scoped identifiers

### Cross-Tenant Prevention

- `ApiKey` queries filter by `workspace_id == tc.workspace_id` (`api_keys.py:182,218`)
- All tenant-scoped queries use `tc.tenant_id` from context
- No client-provided tenant_id accepted for authorization
- `get_tenant_context` always resolves from the JWT token, never from query parameters
- Workspace membership verified before returning any workspace data

### Workspace Membership

- `WorkspaceMember` model links `user_id` to `workspace_id` with `role`
- Role stored as String(20), default "member"
- `expires_at` field for time-limited memberships
- Query via `select(WorkspaceMember).where(WorkspaceMember.user_id == user.id)` with eager-loaded workspace

---

## 4. API Key Architecture

### Key Format (`app/api/api_keys.py:96-98`)

```python
def _generate_key() -> str:
    return secrets.token_hex(32)  # 64-character hex string
```

### Key Hashing (`api_keys.py:84-85`)

```python
def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()  # 64-char hex digest
```

- Raw keys **never** stored; only SHA-256 hashes
- Hash stored in `ApiKey.key_hash` (String(64), unique, indexed)

### Key Storage (`app/models.py:684-721`)

| Field | Type | Purpose |
|---|---|---|
| `key_hash` | String(64), unique | SHA-256 of raw key |
| `key_prefix` | String(8) | First 8 chars for identification |
| `workspace_id` | String(36) | Owning workspace |
| `user_id` | String(36) | Creator |
| `name` | String(100) | Human label |
| `description` | Text | Optional description |
| `expires_at` | DateTime, indexed | Optional expiry |
| `revoked_at` | DateTime | Soft revocation |
| `key_extra` | JSON | Optional metadata (server name, allowed tools) |
| `last_used_at` | DateTime | Last authentication usage |

### Lifecycle Operations

- **Create** (`POST /api/v1/api-keys/`): Requires `admin` role. Returns raw key ONCE in response. Never logged.
- **List** (`GET /api/v1/api-keys/`): Returns masked list (no raw key, only prefix)
- **Revoke** (`DELETE /api/v1/api-keys/{id}`): Requires `admin` role. Sets `revoked_at` timestamp. 204 response.
- **Rotate** (`POST /api/v1/api-keys/{id}/rotate`): Requires `admin` role. Creates new key with same metadata, revokes old one. Returns new raw key ONCE.

### Authentication by API Key (`api_keys.py:266-278`)

- `authenticate_api_key(raw_key, db)`:
  - Hashes raw key, queries `ApiKey` where `key_hash == hash AND revoked_at IS NULL`
  - Checks `expires_at` against current time
  - Returns `ApiKey` or `None`
- Not integrated into main auth middleware -- separate authentication path for MCP servers

### Scoping

- Keys scoped to workspace level
- No per-key tool or action scoping in this sprint
- `key_extra` JSON field available for future scoping

### Audit Trail

- All key operations emit audit events: `api_key.created`, `api_key.revoked`, `api_key.rotated`
- Metadata includes `key_prefix` and `key_name` -- never the full raw key

---

## 5. Database Security

### Connection Pooling (`app/db.py:9-16`)

```python
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=50,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

- Pool size: 50 connections, max overflow: 20
- `pool_pre_ping=True`: validates connections before use
- `pool_recycle=3600`: recycles connections after 1 hour

### Parameterization

- All queries use SQLAlchemy ORM with parameterized queries
- No raw SQL string interpolation observed
- Foreign keys properly defined with `ForeignKey()` constraints

### Soft Delete

All major data models include `deleted_at: DateTime | None`:
- `User.deleted_at` (line 85)
- `Workspace.deleted_at` (line 56)
- `Session.deleted_at` (line 184)
- `Memory.deleted_at` (line 257)
- `Source.deleted_at` (line 347)
- `Fact.deleted_at` (line 454)
- `Decision.deleted_at` (line 506)
- `GraphNode.deleted_at` (line 547)
- `GraphEdge.deleted_at` (line 596)
- `MessageFeedback.deleted_at` (line 681)
- `ApiKey.revoked_at` (line 707) -- soft revocation

Auth middleware checks `deleted_at IS NULL` for user lookups (`auth.py:42, 58, 132; tenancy.py:58`).

### Non-Root Docker User (`Dockerfile:29,46`)

```dockerfile
groupadd -r swarmvault && useradd -r -g swarmvault -d /app swarmvault
USER swarmvault
```

Application runs as non-root `swarmvault` user in container.

---

## 6. Secret Management

### Environment Variables (`.env.example:1-46`)

| Variable | Required | Purpose |
|---|---|---|
| `secret_key` | Yes | JWT signing key |
| `database_url` | Yes | PostgreSQL connection string |
| `anthropic_api_key` | No | LLM provider |
| `openai_api_key` | No | Alternative LLM provider |
| `cors_origins` | Yes (prod) | Allowed CORS origins |

### Secret Key Generation (`.env.example:13-14`)

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Minimum 32 characters. No explicit entropy requirement enforced in config.

### Log Exposure Risk

- `SENSITIVE_FIELDS` (`audit/constants.py:90-102`) includes: `password`, `hashed_password`, `secret`, `api_key`, `raw_key`, `token`, `refresh_token`, `database_url`, `connection_string`, `private_key`, `encryption_key`
- `_sanitize()` recursively redacts these fields from all audit events
- Error handlers should not expose `secret_key` or database credentials

### Rotation Policy

- No automatic rotation observed
- Refresh tokens have expiry (30 days default)
- API keys support manual rotation
- No key rotation scheduling

---

## 7. CORS Configuration (`app/core/config.py:54-79`)

```python
cors_origins: list[str] = []
```

- Stored as list of strings, not wildcard
- Loading splits on comma and strips whitespace
- `allow_origins=cors_origins` in FastAPI CORSMiddleware
- `allow_credentials=True` (allows cookies/auth headers)
- `allow_methods=["*"]`, `allow_headers=["*"]`
- **Wildcard stripped**: Empty list means no origins allowed; must be explicitly configured
- Production requires explicit CORS_ORIGINS env var (docker-compose line 34)

### CORS Safety Notes

- `allow_credentials=True` with explicit origins (not wildcard) is safe
- Empty `cors_origins` blocks all cross-origin requests -- production must configure
- In development, if not set, defaults to empty list (blocks everything)

---

## 8. Security Headers (`app/main.py:1-80`)

```python
app.add_middleware(SecurityHeadersMiddleware)
```

SecurityHeadersMiddleware (`main.py:58-80`) adds these headers to every response:

| Header | Value | Purpose |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | Prevents MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevents clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Legacy XSS filter |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | HSTS (1 year) |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), payment=()` | Restricts browser features |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limits referrer leakage |

**Missing headers (notable gaps):**

| Header | Status | Impact |
|---|---|---|
| `Content-Security-Policy` | NOT SET | No CSP protection against XSS/injection |
| `Cache-Control` | NOT SET globally | No universal cache control |
| `Server` | NOT SET | Good -- no server version disclosure |

---

## 9. Rate Limiting (`app/middleware/rate_limit.py:1-120`)

### Rules (`rate_limit.py:30-36`)

| Path | Limit | Window | Key Type |
|---|---|---|---|
| `/api/v1/auth/login` | `rate_limit_login` (from settings) | 60s | IP |
| `/api/v1/auth/register` | `rate_limit_login` | 60s | IP |
| `/api/v1/chat/` | `rate_limit_chat` | 60s | User |
| `/api/v1/ingest/upload` | `rate_limit_ingest` | 3600s (1hr) | User |
| `/api/v1/ingest/search` | `rate_limit_search` | 60s | User |

### Implementation

- In-memory sliding window (`_RateLimiter` class)
- Thread-safe via `threading.Lock`
- Per-key timestamp lists stored in `defaultdict(list)`

### Bypass Conditions

1. **Test mode** (`rate_limit.py:42`): `_RateLimiter._disabled_for_testing = True` bypasses all limits
2. **Pytest** (`rate_limit.py:76`): `request.app.state.testing` flag bypasses
3. **E2E header** (`rate_limit.py:82-84`): `X-E2E: true` header bypasses in non-production environments
4. **Production**: ONLY the pytest bypass is gated; E2E header NOT active when `settings.environment == "production"`

### Response Headers

- `X-RateLimit-Limit`: max requests for the window
- `X-RateLimit-Remaining`: requests remaining
- `Retry-After`: window seconds on 429

### Production Readiness Note

Rate limiter is explicitly documented as in-memory: `"Production should replace with Redis-backed implementation"` (`rate_limit.py:5`). In-memory rate limiting is **not safe for multi-worker deployments** -- each worker maintains its own window.

---

## 10. Error Sanitization

### `_sanitize_detail` Pattern (inferred from middleware)

The middleware does NOT have a dedicated `_sanitize_detail` function. Error sanitization is performed at two levels:

1. **Audit redaction** (`audit/service.py:43-61`): `_sanitize()` recursively redacts `SENSITIVE_FIELDS` from event dicts
2. **HTTPException details**: Middleware returns generic messages like "Missing authorization token", "Invalid or expired token", "User not found or inactive" -- never exposes internal details

### Exception Handlers (`app/main.py:35-56`)

```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    # Logs with request_id; returns JSON {detail}
    return JSONResponse(...)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    # Logs exception info; returns generic 500
    # In debug mode, includes exc_info
```

- Unhandled exceptions return generic 500 with `request_id` for correlation
- `debug` setting controls whether exception details are exposed (`.env.example:7`)

### Path Redaction

- No path redaction observed in exception handlers
- Stack traces only exposed when `debug=true`
- Request URL and method logged via `log_request()` middleware

---

## 11. Audit Architecture

### Event Types (`audit/constants.py:11-61`)

**Policy events**: policy.request, policy.allow, policy.deny, policy.confirmation_required, policy.limited

**Memory events**: memory.read, memory.search, memory.write, memory.update, memory.delete, memory.expire, memory.share

**Tool events**: tool.request, tool.started, tool.completed, tool.failed, tool.denied

**Model events**: model.request, model.completed, model.failed

**Auth events**: auth.login, auth.logout, auth.login_failed, auth.token_refresh

**Resource events**: api_key.created/revoked/rotated, project.created/deleted, workspace.created, workspace.member_added/removed

**Data lifecycle**: ingest.started/completed/failed, source.deleted

### Schema (`audit/constants.py:64-86`)

20 canonical fields: event_id, timestamp, event_type, tenant_id, workspace_id, project_id, principal_id, principal_type, resource_type, resource_id, action, decision, policy_id, policy_version, request_id, correlation_id, result_status, duration_ms, limits, provenance_reference, metadata

### Sinks (`audit/service.py:111-180`)

**Default sink**: structured logger (`app.audit` logger, line 37) -- emits as structured JSON via `extra={"audit_event": event}`

**DB sink** (`register_db_sink`, line 146-157): Optional, uses `AuditRepository`
- Persisted via `await audit.persist(session)` at end of request
- Never raises -- failures logged, buffer cleared to prevent memory growth

**Additional sinks**: `register_sink()` allows adding arbitrary callbacks

### Redaction (`audit/service.py:43-61`)

`_sanitize()` recursively traverses event dicts:
- Keys matching `SENSITIVE_FIELDS` (case-insensitive) are replaced with `"[redacted]"`
- Nested dicts and lists are processed recursively
- Applied to every event before ANY sink receives it

### DB Persistence (`audit/repository.py:33-171`)

- `AuditRepository.save()`: Insert-only, maps AuditEventDTO to ORM model
- `AuditRepository.query()`: Filters by tenant, workspace, principal, resource, time range -- all parameterized
- `AuditRepository.count()`: Count with tenant/time filters
- `get_by_request_id()`: Correlation lookup by request ID
- `get_by_correlation_id()`: Chain correlation by correlation ID

### Model (`app/models.py:788-838`)

`AuditEvent` table with 21 fields, 6 indexes:
- Composite: `tenant_id + timestamp`, `principal_id + timestamp`, `resource_type + timestamp`, `correlation_id + timestamp`
- Single: `tenant_id`, `workspace_id`, `project_id`, `principal_id`, `resource_type`, `action`, `decision`, `event_type`, `result_status`, `request_id`, `correlation_id`, `timestamp`
- Note: `event_metadata` used instead of `metadata` because SQLAlchemy reserves `metadata` as an attribute name

---

## 12. Operational Concerns

### Health Checks

**Liveness** (`Dockerfile:52-53`): `curl -sf http://localhost:8000/health/live`

**Readiness** (`docker-compose.yml:47`): `python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/ready')"`

Readiness depends on PostgreSQL being healthy (`depends_on` with `condition: service_healthy`).

### Docker Configuration

- Multi-stage build: `python:3.12-slim` builder -> `python:3.12-slim` runtime
- Builder installs system deps (`build-essential`, `libpq-dev`) for Python package compilation
- Runtime only installs `libpq5` and `curl`
- Non-root user: `swarmvault` (uid created at build time)
- Runtime directories: `/app/storage`, `/app/logs` owned by `swarmvault`
- 2 uvicorn workers configured
- `PYTHONUNBUFFERED=1`, `PYTHONDONTWRITEBYTECODE=1`
- Migrations run at startup: `alembic upgrade head`

### Startup Sequence (`Dockerfile:60-67`)

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --log-level info --access-log --no-use-colors
```

Migrations complete before server starts. No separate migration container.

### Environment Config (from `.env.example`)

| Variable | Default | Effect |
|---|---|---|
| `environment` | `development` | Controls rate limit bypass, likely CORS behavior |
| `debug` | `false` | Controls SQL echo and exception detail exposure |
| `access_token_expire_minutes` | `60` | JWT access token lifetime |
| `refresh_token_expire_days` | `30` | Refresh token lifetime |
| `log_level` | `INFO` | Python logging level |
| `enable_metrics` | `false` | Metrics endpoint toggle |

---

## 13. Security Control Matrix

| Control | Location | Enforcement Point | Test | Failure Behavior | Bypass Risk |
|---|---|---|---|---|---|
| JWT validation | `middleware/auth.py:17-51` | `require_auth` dependency | Any auth-required endpoint | 401 "Missing/Invalid/Expired token" | None -- no bypass |
| User active check | `middleware/auth.py:45-50` | `require_auth` dependency | Any auth-required endpoint | 401 "User not found or inactive" | None |
| Tenant isolation | `middleware/tenancy.py:28-141` | `get_tenant_context` dependency | Any tenant-scoped endpoint | 401/403/404 | Low -- always from JWT |
| Role hierarchy | `middleware/rbac.py:105-140` | `require_min_role` dependency | Protected endpoints | 403 "Role required" | Low -- enforced at dependency level |
| Permission check | `middleware/rbac.py:83-102` | `require_permission` dependency | Protected endpoints | 403 "Missing permissions" | Low |
| Policy fail-closed | `services/policy/engine.py:37,276-280,353-360` | `PolicyEngine.evaluate()` | All policy decisions | DENY on unknown/missing | None by design |
| Explicit deny override | `services/policy/engine.py:310-319` | `PolicyEngine.evaluate()` | Policy evaluation | Immediate DENY | None |
| Password hashing | `core/security.py` (passlib) | Registration/password change | Password operations | Cannot verify without hash | None |
| Secret redaction | `services/audit/service.py:43-61` | `_sanitize()` before ALL sinks | All audit events | Fields replaced with `[redacted]` | Low -- new fields must be added to SENSITIVE_FIELDS |
| API key hashing | `api/api_keys.py:84-85` | Key creation/rotation | API key operations | Cannot reverse hash | None |
| Rate limiting | `middleware/rate_limit.py` | Per-route sliding window | All rate-limited routes | 429 with Retry-After | HIGH in prod -- in-memory, no Redis |
| Soft delete checks | `middleware/auth.py:42,58,132` | User queries | Auth middleware | 401 if deleted | None |
| CORS restrictions | `core/config.py:54-79` | CORSMiddleware | All cross-origin requests | Blocked if origin not whitelisted | Medium -- empty list blocks all (misconfig risk) |
| Security headers | `main.py:58-80` | SecurityHeadersMiddleware | Every response | Missing CSP (gap) | Low |
| HTTPS enforcement | HSTS header | SecurityHeadersMiddleware | Every response | Missing CSP | Medium -- no mixed-content enforcement |
| Non-root container | `Dockerfile:29,46` | Docker runtime | Container startup | Fails if port requires root | None |
| DB parameterization | SQLAlchemy ORM | All DB queries | All data operations | SQL injection if raw SQL used | Low -- ORM used consistently |
| Error sanitization | `main.py:35-56` | Exception handlers | All unhandled errors | Generic 500 with request_id | Low -- debug mode exposes details |

---

## 14. Fail-Closed Behavior Verification

### PolicyEngine Default

```python
DEFAULT_DECISION = EFFECT_DENY  # engine.py:37
```

Verified fail-closed paths:

1. **Empty policy set** (`engine.py:274-280`):
   ```python
   if not rules:
       return PolicyDecision(decision=DEFAULT_DECISION, reason="no policies configured", risk=RISK_HIGH)
   ```
   -> DENY

2. **No matching rule** (`engine.py:353-360`):
   ```python
   if not matched:
       return PolicyDecision(decision=DEFAULT_DECISION, reason="no matching policy rule found", risk=RISK_MEDIUM)
   ```
   -> DENY

3. **Unknown effect** (`engine.py:298-300`):
   ```python
   if effect not in VALID_EFFECTS:
       logger.warning("unknown effect %r in policy %s", effect, pid)
       continue
   ```
   -> Skips the rule (doesn't apply it), continues evaluation. If no other rule matches, path (2) returns DENY.

4. **RBAC role minimum** (`rbac.py:128-139`):
   ```python
   decision = engine.check_role_minimum(...)
   if decision.decision != EFFECT_ALLOW:
       raise HTTPException(status_code=403, ...)
   ```
   -> Only allows if Engine returns ALLOW; DENY and CONFIRM both produce 403

### Conclusion

The system **does deny on unknown or missing policies**. The default decision is DENY, and both empty policy sets and unmatched rules result in a DENY decision. This is verified from source code.
