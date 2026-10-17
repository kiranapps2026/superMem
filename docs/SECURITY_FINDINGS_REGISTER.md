# Security Findings Register
**Repository:** SwarmVault WebApp
**Date:** 2026-09-10
**Analyst:** Forensic Architecture Analysis

================================================================================
P0 — CRITICAL FINDINGS
================================================================================

SEC-001: Hardcoded Development Secrets in Source Code
------------------------------------------------------
**Severity:** P0 — CRITICAL
**Category:** Credential Exposure
**File:** app/core/config.py:8-9

**Finding:**
```python
_DEV_DATABASE_URL = "postgresql+asyncpg://swarmvault:swarmvault@localhost:5432/swarmvault"
_DEV_SECRET = "dev-insecure-default-change-in-production-123"
```

Database credentials and JWT secret are hardcoded in source code.
While defaults exist, they are committed to version control.

**Impact:** Anyone with repository access has database credentials.
Production deployments may accidentally use these defaults.

**Mitigation present:** config.py:70-123 validates SECRET_KEY and DATABASE_URL
in production, raising ValueError if defaults are detected.
However, the secrets are still visible in source code.

**Recommended fix:** Move defaults to .env.example only. Source code should
require environment variables with no fallback defaults.

---

SEC-002: Dual Authentication Path Inconsistency
-------------------------------------------------
**Severity:** P0 — HIGH
**Category:** Authentication
**Files:** app/middleware/auth.py, app/middleware/tenancy.py

**Finding:**
Two separate authentication implementations exist:

1. `require_auth` (auth.py:17-51): Uses OAuth2PasswordBearer, returns User
2. `get_tenant_context` (tenancy.py:28-124): Parses Authorization header manually,
   returns TenantContext

Both decode JWT, look up User, check deleted_at and is_active.
But they differ in:
- Return type (User vs TenantContext)
- Workspace resolution logic
- Error message details
- Dependency chain

**Impact:** Routers using different paths may have inconsistent behavior.
Future changes to auth logic must be duplicated across both paths.

**Evidence:**
- auth.py:12-14 — OAuth2PasswordBearer with auto_error=False
- tenancy.py:32-38 — Manual header parsing
- Both perform JWT decode, User lookup, active check independently

**Recommended fix:** Consolidate to single auth dependency that returns
TenantContext (the richer object). All routers should use this.

---

SEC-003: Memory Tenant Isolation Not Enforced
----------------------------------------------
**Severity:** P0 — HIGH
**Category:** Authorization / Data Isolation
**Files:** app/api/memory.py:96-129, app/services/memory.py:211-248

**Finding:**
Memory model has a `tenant_id` column (models.py:238-239) with a comment
"FIX: set tenant for isolation" in api/memory.py:99.

Current behavior:
- Memory writes (memory.py:96-115): tenant_id is set from tc.tenant_id
- Memory reads (memory.py:145-159): filtered by workspace_id and user_id only
- Memory reads DO NOT filter by tenant_id

**Impact:** A user with access to a workspace could potentially read memories
from another tenant if workspace_id overlaps (unlikely but architecturally unsound).

**Evidence:**
```python
# memory.py:145-148 — NO tenant_id filter
query = select(Memory).where(
    Memory.workspace_id == tc.workspace_id,
    Memory.user_id == tc.user_id,
)
```

**Recommended fix:** Add `Memory.tenant_id == tc.tenant_id` to all memory queries.

---

SEC-004: Chat Message Persistence Before LLM Call
--------------------------------------------------
**Severity:** P0 — HIGH
**Category:** Data Integrity
**File:** app/api/chat.py:58-89

**Finding:**
In send_chat_message:
1. User message is created and flushed to DB (line 63-64)
2. LLM call happens via process_chat (line 66-73)
3. Assistant message is created and committed (line 87-89)

If the LLM call fails (exception at line 66-73), the user message remains
in the database without a corresponding assistant response.

Same issue exists in stream_chat (line 146-234) where user message is
flushed at line 152-153 before the streaming LLM call.

**Impact:** Orphaned user messages create incomplete conversation records.
Provenance is incomplete — user message exists but no assistant response.

**Evidence:**
```python
# chat.py:58-64 — flush before LLM call
user_msg = Message(
    session_id=session_id,
    role="user",
    content=data.message,
)
db.add(user_msg)
await db.flush()  # <-- persisted here

result = await process_chat(...)  # <-- LLM call can fail here
```

**Recommended fix:** Use a transaction with rollback on LLM failure, or
save assistant response as NULL/placeholder and update after LLM returns.

---

SEC-005: No Token Revocation Mechanism
---------------------------------------
**Severity:** P0 — HIGH
**Category:** Authentication
**File:** app/core/security.py

**Finding:**
JWT tokens are stateless with no revocation mechanism.
Once issued, a token remains valid until its expiration time.
There is no blacklist, no token version, and no logout endpoint visible.

Refresh tokens exist (models.py:147-162) with a `revoked` column, but
there is no endpoint to revoke them, and no validation against revoked list.

**Impact:** Stolen tokens remain valid. Compromised sessions cannot be terminated.

**Evidence:**
- security.py:22-28 — make_access_token creates JWT with no revocation ID
- security.py:31-37 — decode_access_token only validates signature and expiry
- No logout endpoint in any router
- No token blacklist or revocation list

**Recommended fix:** Implement token revocation via Redis blacklist or
short-lived access tokens (15 min) with refresh token rotation.

================================================================================
P1 — HIGH FINDINGS
================================================================================

SEC-006: No Account Lockout After Failed Logins
-------------------------------------------------
**Severity:** P1 — HIGH
**Category:** Authentication
**File:** app/api/auth.py

**Finding:**
Login endpoint does not track failed attempts.
There is no account lockout mechanism, no exponential backoff,
and no alerting on repeated failures.

**Impact:** Brute force password guessing is possible.

**Recommended fix:** Track failed login attempts per account, lock after
threshold (e.g., 5 attempts in 15 minutes).

---

SEC-007: In-Memory Rate Limiter Bypass
---------------------------------------
**Severity:** P1 — HIGH
**Category:** Access Control
**File:** app/middleware/rate_limit.py:82-84

**Finding:**
```python
if settings.environment != "production":
    if request.headers.get("X-E2E") == "true":
        return await call_next(request)
```

In non-production environments, any request with header `X-E2E: true`
completely bypasses rate limiting.

**Impact:** Rate limits can be bypassed in staging/development environments.
If staging is accessible externally, this becomes a production risk.

**Recommended fix:** Remove the bypass or restrict to localhost-only environments.

---

SEC-008: No Security Headers
-----------------------------
**Severity:** P1 — HIGH
**Category:** Defense in Depth
**File:** app/main.py

**Finding:**
No security headers are configured:
- No Content-Security-Policy (CSP)
- No Strict-Transport-Security (HSTS)
- No X-Frame-Options (clickjacking protection)
- No X-Content-Type-Options (MIME sniffing protection)
- No Referrer-Policy
- No Permissions-Policy

**Impact:** XSS attacks, clickjacking, MIME sniffing, information leakage.

**Recommended fix:** Add SecurityHeadersMiddleware that sets all recommended headers.

---

SEC-009: SQL Injection via ILIKE Pattern
-----------------------------------------
**Severity:** P1 — MEDIUM
**Category:** Injection
**Files:** app/api/ingest.py:273, app/services/memory.py:282

**Finding:**
```python
# ingest.py:273
if subject:
    stmt = stmt.where(Fact.subject.ilike(f"%{subject}%"))

# memory.py:282
stmt = stmt.where(MemoryModel.content.ilike(f"%{query}%"))
```

User input is interpolated into ILIKE patterns using f-strings.
While SQLAlchemy's ilike() method parameterizes the query, the pattern
construction with f-string should be verified.

**Impact:** If ilike() does not properly escape the pattern, SQL injection
is possible via specially crafted search terms.

**Verification needed:** Confirm SQLAlchemy's ilike() properly parameterizes
the pattern argument. If it does, this is a false positive. If not, it's P0.

**Recommended fix:** Use explicit parameter binding:
```python
stmt = stmt.where(Fact.subject.ilike(f"%{subject}%"))
# Should be:
stmt = stmt.where(Fact.subject.ilike(f"%{{}}%".format(subject)))
# Or better, use concat:
from sqlalchemy import concat
stmt = stmt.where(Fact.subject.ilike(concat("%", subject, "%")))
```

---

SEC-010: No Input Sanitization for XSS
----------------------------------------
**Severity:** P1 — MEDIUM
**Category:** XSS
**Files:** frontend/src/ (all .tsx files)

**Finding:**
User-generated content (memory content, chat messages, fact content) is
rendered in the frontend without apparent sanitization.
No DOMPurify or similar sanitization library is in package.json.

**Impact:** Stored XSS if a user creates content containing JavaScript.

**Recommended fix:** Add DOMPurify or similar sanitization to all user content
rendering paths. Use textContent instead of innerHTML where possible.

---

SEC-011: Refresh Tokens Not Revoked on Logout
----------------------------------------------
**Severity:** P1 — MEDIUM
**Category:** Authentication
**Files:** app/models.py:147-162, app/api/auth.py

**Finding:**
RefreshToken model has a `revoked` column (models.py:158) but there is
no endpoint or logic to set it to True on logout.

**Impact:** Logged-out users can still use refresh tokens to get new access tokens.

**Recommended fix:** Add logout endpoint that revokes the current refresh token.

---

SEC-012: No CSRF Protection
----------------------------
**Severity:** P1 — MEDIUM
**Category:** CSRF
**Files:** app/api/ (all mutation endpoints)

**Finding:**
No CSRF tokens are implemented. All state-changing endpoints (POST, PATCH,
DELETE) accept requests without origin verification beyond CORS.

**Impact:** Cross-site request forgery attacks if user has active session.

**Mitigation present:** CORS configuration restricts origins (when properly configured).
However, CORS is not CSRF protection — same-origin requests bypass CORS.

**Recommended fix:** Implement CSRF tokens for state-changing operations, or
require custom headers (X-Requested-With) for mutations.

---

SEC-013: No Request Size Limits at Middleware Level
----------------------------------------------------
**Severity:** P1 — MEDIUM
**Category:** DoS
**Files:** app/middleware/

**Finding:**
No middleware enforces maximum request body size.
Individual endpoints may have schema limits (e.g., max_length=1_000_000),
but there is no global request size limit.

**Impact:** Large payloads can exhaust memory/CPU before reaching endpoint validation.

**Recommended fix:** Add middleware to enforce max request body size (e.g., 10MB).

---

SEC-014: Sensitive Data in Logs
--------------------------------
**Severity:** P1 — LOW
**Category:** Information Leakage
**File:** app/core/config.py:111

**Finding:**
```python
logger.debug("SECRET_KEY validated: %d chars", len(self.secret_key))
```

While the actual secret is not logged, the length is logged at DEBUG level.

**Impact:** Minor information leakage in debug logs.

**Recommended fix:** Remove or generalize the log message.

================================================================================
P2 — MEDIUM FINDINGS
================================================================================

SEC-015: No Encryption at Rest
------------------------------
**Severity:** P2 — MEDIUM
**Category:** Data Protection
**Files:** app/models.py (all models)

**Finding:**
All sensitive data is stored as plaintext in PostgreSQL:
- Passwords: hashed with bcrypt (good)
- Messages: plaintext content
- Memories: plaintext content
- Facts: plaintext content
- API keys: hashed (good)

**Impact:** Data exposure if database is compromised.

**Recommended fix:** Implement column-level encryption for sensitive fields
(content, messages, metadata) using application-level encryption.

---

SEC-016: No PII Encryption
---------------------------
**Severity:** P2 — MEDIUM
**Category:** Privacy
**Files:** app/models.py:65-94 (User model)

**Finding:**
User email and name are stored as plaintext.
No encryption or tokenization for PII fields.

**Impact:** GDPR/privacy compliance concerns.

**Recommended fix:** Encrypt PII fields or use tokenization.

---

SEC-017: No Database Connection Pool Monitoring
------------------------------------------------
**Severity:** P2 — MEDIUM
**Category:** Reliability
**File:** app/db.py:9-16

**Finding:**
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

Pool is configured but not monitored. No alerts for pool exhaustion,
connection leaks, or slow queries.

**Impact:** Production issues may go undetected until failure.

**Recommended fix:** Add pool monitoring (pool.checkedin(), pool.checkedout(),
pool.size()) with metrics export.

---

SEC-018: Debug Mode Logs SQL Queries
-------------------------------------
**Severity:** P2 — LOW
**Category:** Information Leakage
**File:** app/db.py:11

**Finding:**
```python
echo=settings.debug
```

In non-production environments, all SQL queries are logged including parameters.

**Impact:** Query patterns and data values visible in logs.

**Recommended fix:** Set echo=False in all environments except explicit debug mode.

================================================================================
P3 — LOW FINDINGS
================================================================================

SEC-019: No Password Complexity Requirements
--------------------------------------------
**Severity:** P3 — LOW
**Category:** Authentication
**File:** app/schemas.py:10

**Finding:**
```python
password: str = Field(..., min_length=8)
```

Only minimum length is enforced. No requirements for:
- Uppercase letters
- Lowercase letters
- Numbers
- Special characters

**Impact:** Users may choose weak passwords.

**Recommended fix:** Add password complexity validator.

---

SEC-020: No Session Expiration
-------------------------------
**Severity:** P3 — LOW
**Category:** Session Management
**File:** app/models.py:165-188

**Finding:**
Session model has no expiration field.
Sessions remain active indefinitely until explicitly deleted.

**Impact:** Stale sessions may remain accessible.

**Recommended fix:** Add expires_at field to Session model with cleanup job.

================================================================================
FINDING SUMMARY
================================================================================

| Severity | Count | Category Distribution |
|----------|-------|----------------------|
| P0       | 5     | Credentials (1), Auth (2), Data Isolation (1), Data Integrity (1) |
| P1       | 10    | Auth (3), Access Control (1), Defense in Depth (1), Injection (1), XSS (1), CSRF (1), DoS (1), Info Leak (1) |
| P2       | 4     | Data Protection (1), Privacy (1), Reliability (1), Info Leak (1) |
| P3       | 2     | Auth (1), Session (1) |
| Total    | 21    | |

================================================================================
COMPLIANCE NOTES
================================================================================

The following security controls are NOT present and should be noted for
compliance frameworks (SOC 2, GDPR, HIPAA as applicable):

- [ ] Encryption at rest for sensitive data
- [ ] Token revocation / logout
- [ ] Account lockout
- [ ] Audit logging for all data access
- [ ] Data retention policies
- [ ] Backup encryption
- [ ] Vulnerability scanning
- [ ] Penetration testing evidence
- [ ] Incident response plan
- [ ] Security training evidence

================================================================================
END OF SECURITY FINDINGS REGISTER
================================================================================
