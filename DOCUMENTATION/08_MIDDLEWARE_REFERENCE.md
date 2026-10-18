# SwarmVault WebApp — Middleware & Request Pipeline
**Version:** 1.0.0
**Date:** 2026-09-01
**Evidence base:** Repository inspection (commit 902d85e), app/middleware/

---

## 1. Request Pipeline

```
Incoming Request
     │
     ▼
 ┌─────────────────────────────────┐
 │ Security Headers Middleware    │  Adds CSP, HSTS, etc.
 └──────────────┬──────────────────┘
                │
                ▼
 ┌─────────────────────────────────┐
 │ CORS Middleware                │  Handles OPTIONS preflight
 └──────────────┬──────────────────┘
                │
                ▼
 ┌─────────────────────────────────┐
 │ Request ID Middleware          │  Generates X-Request-ID
 └──────────────┬──────────────────┘
                │
                ▼
 ┌─────────────────────────────────┐
 │ Rate Limit Middleware          │  Checks request rate limits
 └──────────────┬──────────────────┘
                │
                ▼
 ┌─────────────────────────────────┐
 │ Auth / RBAC Middleware         │  Validates JWT, loads role
 └──────────────┬──────────────────┘
                │
                ▼
 ┌─────────────────────────────────┐
 │ Tenant Context Middleware      │  Resolves tenant + workspace
 └──────────────┬──────────────────┘
                │
                ▼
          Route Handler
```

---

## 2. Security Headers Middleware

**File:** `app/main.py`

Adds headers to all responses. Production vs Development differ:

| Header | Production | Development |
|--------|-----------|-------------|
| X-Content-Type-Options | nosniff | nosniff |
| X-Frame-Options | DENY | DENY |
| X-XSS-Protection | 1; mode=block | 1; mode=block |
| Referrer-Policy | strict-origin-when-cross-origin | strict-origin-when-cross-origin |
| Permissions-Policy | geolocation=(), microphone=(), camera=() | geolocation=(), microphone=(), camera=() |
| Strict-Transport-Security | max-age=31536000; includeSubDomains | Not set |
| Content-Security-Policy | default-src 'self' | Relaxed (localhost allowed) |
| X-Request-ID | UUID per request | UUID per request |

---

## 3. CORS Middleware

**File:** `app/main.py`

- **Origin source:** `settings.cors_origins` (comma-separated string or JSON list)
- **Default:** `"*"` (allow all origins — dev default)
- **Production enforcement:** `cors_origins_safe` property raises ValueError if wildcard remains in production
- **Credentials:** Allowed (Vary: Origin header present)
- **Methods:** GET, POST, PUT, DELETE, OPTIONS
- **Headers:** Authorization, Content-Type, X-Workspace-Id, X-Request-Id

### CORS Configuration Flow
```
settings.cors_origins = "*" (dev)
    │
    ▼
cors_origins_list property
    │  Parses comma-separated or JSON
    │  Returns ["*"] for wildcard
    ▼
cors_origins_safe property
    │  Production: strips "*", raises if empty
    │  Dev: returns as-is
    ▼
Middleware origin check
```

---

## 4. Request ID Middleware

**File:** `app/main.py`

- Generates UUID per request via `uuid.uuid4()`
- Set as `X-Request-ID` response header
- Available in request state for logging correlation

---

## 5. Rate Limiting

**File:** `app/middleware/rate_limit.py`

### Configuration (per settings)
| Setting | Default | Applies to |
|---------|---------|-----------|
| rate_limit_login | 10 req/min | POST /auth/login |
| rate_limit_chat | 30 req/min | POST /chat |
| rate_limit_ingest | 5 req/min | POST /ingest |
| rate_limit_search | 60 req/min | GET /memory/search |
| rate_limit_api | 100 req/min | All other authenticated endpoints |

### Mechanism
NOT ESTABLISHED IN AVAILABLE SOURCE — likely token bucket or sliding window per key.
**Evidence:** `app/core/config.py` has rate_limit_* settings; `app/middleware/rate_limit.py` exists.

---

## 6. RBAC Middleware

**File:** `app/middleware/rbac.py`

Role hierarchy enforced at middleware or route-depends level:
| Role | Can |
|------|-----|
| owner | Everything including delete workspace |
| admin | Member management, edit resources |
| member | Create and edit own resources |
| viewer | Read-only |

### Evidence
- `app/middleware/rbac.py` exists
- `app/middleware/tenancy.py` — role is loaded into TenantContext
- `app/schemas.py:79` — WorkspaceMemberUpdate.role Literal

---

## 7. Tenant Context Middleware

**File:** `app/middleware/tenancy.py`

### Input
Two sources for workspace identity:
1. **JWT Bearer token** — Required, contains user_id (sub claim)
2. **X-Workspace-Id header** — Optional, overrides default workspace selection

### Processing
1. Extract JWT from `Authorization: Bearer <token>`
2. Decode JWT (HS256 with secret_key)
3. Extract `sub` claim as user_id
4. Query User (must exist, not deleted, is_active=True)
5. If X-Workspace-Id header present:
   - Verify user is member of that workspace
   - 403 if not a member
6. If no X-Workspace-Id:
   - Select first workspace membership
   - 404 if none
7. Load Tenant for workspace.tenant_id
8. Return `TenantContext` with full resolution

### TenantContext Output
| Field | Type | Source |
|-------|------|--------|
| tenant_id | str | Tenant.id |
| tenant_name | str \| None | Tenant.name |
| tenant_plan | str \| None | Tenant.plan |
| workspace_id | str \| None | Workspace.id |
| workspace_name | str \| None | Workspace.name |
| role | str | WorkspaceMember.role |
| user_id | str \| None | JWT sub claim |

### Error Conditions
| Condition | Status | Detail |
|-----------|--------|--------|
| No Bearer token | 401 | "Missing authorization token" |
| Invalid/expired JWT | 401 | "Invalid or expired token" |
| Missing sub claim | 401 | "Invalid token payload" |
| User not found or inactive | 401 | "User not found or inactive" |
| Not a member (X-Workspace-Id) | 403 | "You are not a member of this workspace" |
| No workspace membership | 404 | "No workspace membership found" |
| Workspace not found | 404 | "Workspace not found" |
| Tenant not found | 404 | "Tenant not found" |

### Default Workspace Selection
When no X-Workspace-Id is provided, the system selects the user's **first** workspace membership (ordered by query, no explicit sort).

---

## 8. Cross-Tenant Protection

### Tests Verified
- `test_cross_tenant_isolation` — Users cannot access other tenants' memories
- `test_graph_cross_tenant_isolation` — Graph queries scoped to tenant
- Multiple cross-tenant test patterns exist in test suite

### Implementation
Application-level filtering in route handlers:
- Every query includes tenant_id filter
- Every query includes workspace_id filter
- User ID included where user ownership matters

### Gap
No database-level RLS enforcement. Isolation is entirely in application code.

---

## 9. LLM Integration

### Configuration
| Setting | Default |
|---------|---------|
| llm_provider | anthropic |
| llm_model | claude-sonnet-4-5-20250929 |
| llm_max_tokens | 1024 |
| llm_temperature | 0.7 |
| llm_timeout_seconds | 30.0 |
| llm_max_retries | 2 |
| llm_retry_backoff | 1.0 |
| anthropic_api_key | "" |
| openai_api_key | "" |
| swarmvault_url | http://localhost:8000 |
| swarmvault_api_key | "" |

### SwarmVault Integration
The webapp calls out to a SwarmVault instance at `swarmvault_url` with `swarmvault_api_key`. This is the "graph-first" backend mentioned in CLAUDE.md.
