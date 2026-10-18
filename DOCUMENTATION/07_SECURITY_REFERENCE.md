# SwarmVault WebApp — Security Reference
**Version:** 1.0.0
**Date:** 2026-09-01
**Evidence base:** Repository inspection (commit 902d85e), config.py, security.py, middleware/

---

## 1. Authentication

### Token System
- **Algorithm:** HS256 (HMAC-SHA256)
- **Access token lifetime:** 60 minutes
- **Refresh token:** Separate longer-lived token (lifetime NOT ESTABLISHED IN AVAILABLE SOURCE)
- **Secret key:** `settings.secret_key` (length validated in config — NOT ESTABLISHED IN AVAILABLE SOURCE)
- **JWT library:** python-jose (jose.jwt)

### Password Handling
- **Hashing:** bcrypt via passlib CryptContext
- **Minimum password length:** 8 characters (enforced in schema)
- **Verification:** `passlib.context.CryptContext.verify()`
- **No complexity rules enforced in schema** (only min length)

### JWT Claims
The JWT payload contains at minimum:
- `sub` — user ID
- `exp` — expiration timestamp (timezone-aware UTC)
- `type` — "access" or "refresh" (NOT confirmed)

---

## 2. Authorization

### Role Hierarchy
| Role | Description |
|------|-------------|
| owner | Full workspace control, can delete workspace |
| admin | Member management, can edit resources |
| member | Can create/edit resources |
| viewer | Read-only access |

### Role Enforcement
- **Workspace level** — Roles apply per workspace
- **Resource level** — Operations check the caller's role in the workspace
- **Policy system** — Tenant-scoped policies exist but NOT ESTABLISHED IN AVAILABLE SOURCE as actively enforced in route handlers

### Evidence
- `app/schemas.py:79` — `WorkspaceMemberUpdate.role: Literal["owner", "admin", "member", "viewer"]`
- `app/models.py` — WorkspaceMember.role column
- `app/middleware/tenancy.py` — TenantContext

---

## 3. Tenancy

### Multi-Tenancy Model
SwarmVault uses a **hierarchical tenant isolation** model:

```
Tenant
 └─▶ Workspace[] (belongs to one tenant)
      └─▶ Project[] (belongs to one workspace)
           └─▶ All data (Memory, Fact, Decision, Source, etc.)
```

### Tenant Context
- **Middleware:** `app/middleware/tenancy.py`
- **Context object:** `TenantContext` — populated from JWT claims
- **Extraction:** `get_tenant_context()` dependency function
- **Fields:** tenant_id, workspace_id, user_id

### Data Isolation
Every database query is scoped by:
1. `tenant_id` — top-level isolation
2. `workspace_id` — workspace-level isolation
3. `user_id` — user-level filtering where applicable

### Cross-Tenant Protection
- Tests verify tenant isolation (`test_cross_tenant_isolation` patterns)
- Graph queries verify cross-tenant isolation (`test_graph_cross_tenant_isolation`)
- Row-level security NOT ESTABLISHED IN AVAILABLE SOURCE (application-level filtering only)

---

## 4. Security Headers

All responses include these headers (set in `app/main.py:47-81`):

| Header | Value | Purpose |
|--------|-------|---------|
| X-Request-ID | UUID | Request correlation |
| X-Content-Type-Options | nosniff | Prevent MIME sniffing |
| X-Frame-Options | DENY | Prevent clickjacking |
| X-XSS-Protection | 1; mode=block | XSS filter (legacy browsers) |
| Referrer-Policy | strict-origin-when-cross-origin | Limit referrer leakage |
| Permissions-Policy | geolocation=(), microphone=(), camera=() | Feature policy |
| Strict-Transport-Security | max-age=31536000; includeSubDomains | HTTPS enforcement (prod) |
| Content-Security-Policy | Production: default-src 'self'; Dev: relaxed | Prevent XSS via CSP |

### CSP Differences (Dev vs Prod)
- **Production:** Strict `default-src 'self'`
- **Development:** Allows localhost for hot-reload and API proxy

---

## 5. Input Validation

### Schema-Level (Pydantic)
- `EmailStr` — Validates email format
- `Field(min_length=N)` — String minimum length
- `Field(max_length=N)` — String maximum length
- `Field(ge=N)` — Numeric minimum (for limit params)
- `Literal["..."]` — Enumerated values
- `field_validator` — Custom validation (e.g., null byte check, whitespace-only check)

### Custom Validators
| Validator | Target | Purpose |
|-----------|--------|---------|
| `no_null_bytes` | MemoryCreate.content | Prevents null bytes |
| `strip_whitespace_only` | MemoryCreate.content | Prevents whitespace-only content |
| `source_type pattern` | IngestUploadRequest | Restricts to text/json/jsonl/chatgpt |
| `rating pattern` | FeedbackCreate | Restricts to thumbs_up/thumbs_down |

### Evidence
- `app/schemas.py:196-208` — MemoryCreate validators
- `app/schemas.py:380` — `IngestUploadRequest.source_type` pattern
- `app/schemas.py:535` — `FeedbackCreate.rating` pattern

---

## 6. Audit Logging

### Audit Events
- **Table:** `audit_events`
- **Tracked actions:** Memory create/update/delete, project create/update/delete, and other sensitive operations
- **Payload:** Actor (user), action, resource type, resource ID, workspace_id, timestamp, metadata (JSON)
- **Access:** Restricted to tenant admin

### Audit API
- `GET /audit/events` — List with filters: tenant_id, workspace_id, principal_id, action, event_type, decision, time range
- `GET /audit/events/{id}` — Single event detail
- **Auth:** JWT + tenant admin role required

---

## 7. API Keys

### Creation
- **Endpoint:** `POST /api-keys`
- **Response:** Full key returned ONCE (shown to user immediately)
- **Storage:** SHA-256 hash stored in database
- **Display:** `key_prefix` (first N chars) shown in list views
- **Raw key NEVER exposed after creation**

### Revocation
- `DELETE /api-keys/{id}` marks key as revoked
- Revoked keys cannot authenticate

### Evidence
- `app/schemas.py:589-602` — ApiKeyOut (key_prefix, no raw key)
- `app/api/api_keys.py`

---

## 8. Provenance

### Message Provenance
Every assistant response is tracked with:
- Model used
- Provider
- Retrieval method (hybrid/keyword/semantic)
- Memory IDs used
- Retrieval sources (detailed)
- User message reference
- Token counts (prompt, completion, total)
- Latency (ms)
- Confidence score

### Provenance API
- `GET /provenance/{id}` — Single provenance record
- `GET /provenance` — List with filters (session_id, project_id)
- **Schema:** `ProvenanceOut`, `ProvenanceCreate`

### Evidence
- `app/schemas.py:296-330` — Provenance schemas
- `app/api/provenance.py`

---

## 9. Secrets Management

### What Is NOT in the Repository
Per CLAUDE.md:
- `.openclaw/credentials/`
- `.openclaw/secrets/`
- `OpenClawBot/secrets/`
- `OpenClawBot/.env`
- `.openclaw/state/`
- `.openclaw/logs/`
- `.openclaw/data/`
- `.openclaw/workspace-attestations/`

### Configuration Approach
- Settings loaded from environment via Pydantic Settings
- `settings.secret_key` — JWT signing key
- `settings.algorithm` — JWT algorithm (default "HS256")
- `settings.access_token_expire_minutes` — Token lifetime
- `settings.database_url` — Database connection
- Database URL NOT ESTABLISHED IN AVAILABLE SOURCE (not in config.py)
- `.env` file used for development (NOT READ per rules)

---

## 10. Row-Level vs Application-Level Security

**Application-level security only — NO database-level row-level security (RLS) detected in available code.**

All data isolation is enforced by:
1. Middleware extracting tenant context from JWT
2. Route handlers scoping queries by tenant_id/workspace_id
3. Role checks in route handlers before mutations

**Risk:** If a route handler forgets to scope by tenant_id, cross-tenant data could leak. Tests exist to catch this but are not a compile-time guarantee.

---

## 11. CSRF Protection

NOT ESTABLISHED IN AVAILABLE SOURCE as actively implemented.
- API uses Bearer tokens (not cookies), so CSRF is less of a concern
- No CSRF middleware found in available code
- No double-submit cookie pattern observed
