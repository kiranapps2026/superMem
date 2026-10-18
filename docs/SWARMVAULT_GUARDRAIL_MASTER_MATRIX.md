# SwarmVault Guardrail Master Matrix

**Forensic Reconciliation Phase — Final Synthesis**
**Baseline SHA:** e6f4b1c157afaed052584963b942ea04f9661610
**Date:** 2026-09-10

---

## Part 1: Complete Guardrail Matrix

| Stage | Control | Implementation | Enforcement Point | Validation | Test | Failure Mode | Bypass Risk | Severity | Status |
|-------|---------|---------------|-------------------|------------|------|-------------|-------------|----------|--------|
| **Ingress** | CORS origin whitelist | `CORSMiddleware` in `main.py` | Every cross-origin request | Origin header check | Integration test | Blocked if origin not in list | Medium — empty list blocks all (misconfig risk) | HIGH | ACTIVE |
| **Ingress** | Security headers | `SecurityHeadersMiddleware` | Every response | Header injection | Unit test | Missing CSP (gap) | Low | MEDIUM | PARTIAL |
| **Ingress** | HTTPS enforcement | HSTS header | Every response | None | None | No mixed-content enforcement | Medium — HTTP still works | MEDIUM | PARTIAL |
| **Auth** | JWT validation | `require_auth` dependency | All authenticated routes | Token decode + expiry check | Auth tests | 401 "Missing/Invalid/Expired token" | None | HIGH | ACTIVE |
| **Auth** | User active check | `require_auth` dependency | All authenticated routes | `user.is_active` flag | Auth tests | 401 "User not found or inactive" | None | HIGH | ACTIVE |
| **Auth** | Soft-delete check | `require_auth` dependency | All authenticated routes | `user.deleted_at IS NULL` | Auth tests | 401 if deleted | None | HIGH | ACTIVE |
| **Auth** | Refresh token validation | `/api/v1/auth/refresh` | Token refresh flow | Token hash lookup, expiry, not revoked | Auth tests | 401 if invalid/revoked/expired | None | HIGH | ACTIVE |
| **Auth** | Password hashing | `hash_password()` in `core/security.py` | Registration, password change | bcrypt via passlib | Unit test | Cannot verify without hash | None | HIGH | ACTIVE |
| **Auth** | API key hashing | `api_keys.py:84-85` | API key creation/rotation | bcrypt hash stored, raw shown once | API key tests | Cannot reverse hash | None | HIGH | ACTIVE |
| **Auth** | API key expiry | `APIKey.expires_at` column | **NOT ENFORCED** | Expiry tracked but never checked | None | Expired keys remain valid | HIGH | P0 | MISSING |
| **Auth** | Rate limiting | `RateLimitMiddleware` | Per-route sliding window | Per-IP counter | Unit test | 429 with Retry-After | HIGH in prod — in-memory, no Redis | HIGH | ACTIVE (PROD: PARTIAL) |
| **Auth** | Error sanitization | `_sanitize_detail()` in `main.py` | All unhandled errors | Removes sensitive fields | Error tests | Generic 500 with request_id | Low — debug mode exposes details | HIGH | ACTIVE |
| **Auth** | JWT/PII redaction | **NOT IMPLEMENTED** | Error responses | None | None | Error responses may leak tokens/PII | HIGH | P0 | MISSING |
| **RBAC** | Role minimum check | `require_min_role` dependency | Protected endpoints | Role hierarchy evaluation | RBAC tests | 403 "Role required" | Low — enforced at dependency level | HIGH | ACTIVE |
| **RBAC** | Permission check | `require_permission` dependency | Protected endpoints | Permission evaluation | RBAC tests | 403 "Missing permissions" | Low | HIGH | ACTIVE |
| **RBAC** | Policy fail-closed | `PolicyEngine.evaluate()` | All policy decisions | Empty policy set → DENY | Policy tests | DENY on unknown/missing | None by design | HIGH | ACTIVE |
| **RBAC** | Explicit deny override | `PolicyEngine.evaluate()` | Policy evaluation | Explicit DENY effects | Policy tests | Immediate DENY | None | HIGH | ACTIVE |
| **RBAC** | PolicyEngine hardcoded | `generate_rbac_policies()` | Policy evaluation | Hardcoded policies only | None | DB `policies` table unused | Low | MEDIUM | PARTIAL |
| **Tenancy** | Workspace isolation | `get_tenant_context` dependency | All tenant-scoped endpoints | JWT/header → workspace membership | Tenancy tests | 401/403/404 | Low — always from JWT | HIGH | ACTIVE |
| **Tenancy** | Cross-tenant prevention | Every query filters by workspace_id | All data access | Workspace_id in every query | Tenancy tests | Row not visible to other tenants | Low | HIGH | ACTIVE |
| **Tenancy** | Project isolation | Project membership check | Project-scoped endpoints | Project membership query | Project tests | 403 if not a member | Low | HIGH | ACTIVE |
| **Validation** | Request schema validation | Pydantic schemas | Every endpoint | Type checking, required fields | Schema tests | 422 with detail | None | HIGH | ACTIVE |
| **Validation** | Content size limit | Pydantic `max_length` | Upload endpoints | Max 1MB | Upload tests | 422 | None | HIGH | ACTIVE |
| **Validation** | Null byte rejection | Schema validators | Memory creation, upload | `"\x00" not in content` | Validation tests | 422 | None | MEDIUM | ACTIVE |
| **Validation** | Whitespace rejection | Schema validators | Memory creation | `content.strip() != ""` | Validation tests | 422 | None | MEDIUM | ACTIVE |
| **Validation** | Source type validation | Connector registry | Ingestion | `source_type` in allowed set | Connector tests | 400 | None | MEDIUM | ACTIVE |
| **Ingestion** | Content hash dedup | SHA-256 check in ingest API | Upload endpoint | Hash compared against existing Sources | Dedup tests | 200 "already processed" | None | MEDIUM | ACTIVE |
| **Ingestion** | Duplicate detection | Content hash + workspace | Upload endpoint | Same hash in same workspace | Dedup tests | Skip re-processing | None | MEDIUM | ACTIVE |
| **Ingestion** | JSON validation | JSONConnector.validate() | JSON upload | JSON parse + structure check | Connector tests | 400 | None | MEDIUM | ACTIVE |
| **Ingestion** | JSONL validation | JSONLConnector.validate() | JSONL upload | Per-line JSON parse | Connector tests | Warning + skip bad lines | None | LOW | ACTIVE |
| **Normalization** | Connector detection | ConnectorRegistry.detect() | Pipeline M0 | Auto-detect or explicit type | Connector tests | Falls back to text connector | None | MEDIUM | ACTIVE |
| **Normalization** | Role validation | NormalizedMessage schema | M0 output | role in allowed set | Pipeline tests | Defaults to "user" | None | LOW | ACTIVE |
| **Memory** | Memory type validation | MemoryCreate schema | Memory creation | Type in allowed set | Memory tests | 422 | None | MEDIUM | ACTIVE |
| **Memory** | Scope enforcement | MemoryService cache path | Memory queries | Scope filter in cache | Memory tests | Only works in cache path | HIGH | P1 | PARTIAL |
| **Memory** | Memory Safety Gate | **NOT IMPLEMENTED** | Memory creation | None | None | All content becomes persistent memory | HIGH | P0 | MISSING |
| **Memory** | Confidence defaults | Hardcoded in pipeline | M2 extraction | None | None | All facts have confidence=0.8 | HIGH | P2 | MISSING |
| **Memory** | Authority defaults | Hardcoded in pipeline | M2 extraction | None | None | All facts have authority=0.75 | HIGH | P2 | MISSING |
| **Memory** | Trust level gating | **NOT IMPLEMENTED** | Memory operations | None | None | No trust-based filtering | HIGH | P1 | MISSING |
| **Temporal** | Supersession tracking | temporal_status update | M3 pipeline | Same (subject, predicate) detection | Temporal tests | temporal_status="historical" | None | MEDIUM | ACTIVE (INCOMPLETE) |
| **Temporal** | superseded_by_id writing | **NOT IMPLEMENTED** | M3 pipeline | None | None | Column never populated | HIGH | P1 | MISSING |
| **Temporal** | Contradiction detection | **NOT IMPLEMENTED** | M3 pipeline | None | None | Conflicting facts coexist | HIGH | P2 | MISSING |
| **Graph** | Node deduplication | Hash-based dedup | M4 pipeline | (label, node_type) hash | Graph tests | Duplicate nodes prevented | None | MEDIUM | ACTIVE |
| **Graph** | Edge validation | Source/target node check | M4 pipeline | Nodes must exist | Graph tests | Edge not created | None | MEDIUM | ACTIVE |
| **Graph** | Graph temporal transitions | **NOT IMPLEMENTED** | M4 pipeline | None | None | temporal_status static | MEDIUM | P2 | MISSING |
| **Retrieval** | Temporal filtering | temporal_status="current" filter | M5 retrieval | Excludes historical | Retrieval tests | Historical facts excluded | None | MEDIUM | ACTIVE |
| **Retrieval** | Soft-delete filtering | deleted_at IS NULL | M5 retrieval | Excludes soft-deleted | Retrieval tests | Deleted records excluded | None | MEDIUM | ACTIVE |
| **Retrieval** | Multi-factor scoring | M5 weighted scoring | Retrieval queries | Authority + confidence + recency + graph | Retrieval tests | Score computed | None | MEDIUM | ACTIVE |
| **Retrieval** | Memory in retrieval | **NOT IMPLEMENTED** | M5 retrieval | None | None | Memory records invisible to M5 | HIGH | P1 | MISSING |
| **Retrieval** | Vector search | **NOT FUNCTIONAL** | Memory retrieval | None | None | Embedding column never populated | HIGH | P1 | NON-FUNCTIONAL |
| **Security** | Secret handling | Environment variables | Configuration | .env not committed | Config tests | Secrets in env only | None | HIGH | ACTIVE |
| **Security** | CORS restrictions | CORSMiddleware origins list | All CORS requests | Origin whitelist | CORS tests | Blocked if not whitelisted | Medium | HIGH | ACTIVE |
| **Security** | CSP headers | **NOT CONFIGURED** | Every response | None | None | No script/style restrictions | HIGH | P3 | MISSING |
| **Security** | DB parameterization | SQLAlchemy ORM | All DB queries | ORM prevents raw SQL injection | DB tests | SQL injection if raw SQL used | Low | HIGH | ACTIVE |
| **Security** | Non-root container | Dockerfile USER directive | Container runtime | Fails if port requires root | Container tests | Fails at startup | None | HIGH | ACTIVE |
| **Audit** | Audit event emission | AuditService | All auditable actions | Always fires, never blocks | Audit tests | Audit failure doesn't fail request | Low | MEDIUM | ACTIVE |
| **Audit** | Secret redaction | _sanitize() | All audit events | SENSITIVE_FIELDS list | Audit tests | Fields replaced with [redacted] | Low | MEDIUM | ACTIVE |
| **Audit** | Append-only | No UPDATE/DELETE on audit_events | Audit table | Application enforces | DB tests | Immutable by design | None | HIGH | ACTIVE |
| **Audit** | Memory lifecycle audit | **PARTIALLY IMPLEMENTED** | Memory operations | Only write events | None | No delete/update/supersession events | MEDIUM | P2 | PARTIAL |
| **Operational** | Database migrations | Alembic + init_db() | Startup | `alembic upgrade head` | Migration tests | Migrations run on startup | None | HIGH | ACTIVE |
| **Operational** | Health check | `/health` endpoint | Load balancer probes | DB connectivity check | Health tests | 200/503 | None | HIGH | ACTIVE |
| **Operational** | Error recovery | Retry on LLM calls | LLM service | Timeout + retry | None | Wastes tokens on persistent failure | MEDIUM | P0 | PARTIAL |
| **Operational** | Graceful shutdown | **NOT IMPLEMENTED** | Shutdown | Empty lifespan yield | None | In-flight requests may fail | MEDIUM | P3 | MISSING |
| **Operational** | Circuit breaker | **NOT IMPLEMENTED** | LLM calls | None | None | Repeated failures hammer API | HIGH | P0 | MISSING |
| **Operational** | Distributed tracing | **NOT IMPLEMENTED** | All requests | None | None | Hard to debug multi-service | LOW | P3 | MISSING |

---

## Part 2: Memory Safety Gate Matrix

This matrix defines which conditions MUST be satisfied before information becomes persistent memory.

| Gate | Condition | Current Status | Implementation Location | Gap |
|------|-----------|---------------|------------------------|-----|
| G-1 | Content is non-empty, non-whitespace | ACTIVE | `schemas.py` validators | None |
| G-2 | Content contains no null bytes | ACTIVE | `schemas.py:197` | None |
| G-3 | User is authenticated | ACTIVE | `require_auth` dependency | None |
| G-4 | User has workspace membership | ACTIVE | `get_tenant_context` | None |
| G-5 | Content size ≤ 1MB | ACTIVE | Pydantic max_length | None |
| G-6 | Memory type is valid | ACTIVE | Schema enum validation | None |
| G-7 | **Trust level ≥ threshold** | **MISSING** | No trust_level field exists | DECISION-009 — field not implemented |
| G-8 | **Content passes safety filter** | **MISSING** | No content safety check | DECISION-010 — no safety gate |
| G-9 | **Confidence above minimum** | **MISSING** | No minimum confidence check | P2-6 — defaults always pass |
| G-10 | **Authority above minimum** | **MISSING** | No minimum authority check | P2-6 — defaults always pass |
| G-11 | **Duplicate detection** | **PARTIAL** | Only at Source level, not Memory level | Same content → new Memory record |
| G-12 | **Provenance recorded** | **PARTIAL** | Stored in extra_metadata JSON | Not linked to Source table |
| G-13 | **Rate limit check** | **PARTIAL** | In-memory only, not distributed | Multi-worker bypass possible |

**Memory Safety Gate Verdict:** Gates G-1 through G-6 are active. Gates G-7 through G-13 are missing or partial. **Any content that passes authentication and basic schema validation immediately becomes persistent memory with no additional safety checks.**

---

## Part 3: Stage-by-Stage Adversarial Input Analysis

| Stage | Malformed Input | Expected Behavior | Actual Behavior | Bypassable? |
|-------|----------------|-------------------|-----------------|-------------|
| CORS | Missing Origin header | Allowed (same-origin) | Allowed | No |
| CORS | Invalid Origin | Blocked | Blocked | No |
| Auth | Expired JWT | 401 | 401 | No |
| Auth | Tampered JWT signature | 401 | 401 | No |
| Auth | Missing token | 401 | 401 | No |
| Auth | Valid token + inactive user | 401 | 401 | No |
| Auth | Valid token + deleted user | 401 | 401 | No |
| Rate Limit | Burst of requests | 429 after limit | 429 per worker | YES — multi-worker bypass |
| Schema | Oversized content | 422 | 422 | No |
| Schema | Null bytes in content | 422 | 422 | No |
| Schema | Wrong memory_type | 422 | 422 | No |
| Ingestion | Invalid JSON | 400 | 400 | No |
| Ingestion | Duplicate content | Skip | Skip (dedup works) | No |
| Pipeline | Empty message list | Empty facts/decisions | Empty facts/decisions | No |
| Pipeline | Regex false positive | Extracted fact | Extracted fact (no LLM validation) | YES — false facts persist |
| Memory | Whitespace-only content | 422 | 422 | No |
| Memory | XSS in content | Stored as-is | Stored as-is (React escapes on render) | No — frontend escapes |
| Memory | SQL injection in content | Parameterized | Safe (ORM) | No |
| Memory | Oversized metadata | No limit | Stored as-is | YES — metadata size unchecked |
| Audit | Sensitive field in metadata | Redacted | Redacted (SENSITIVE_FIELDS) | No |

---

## Part 4: Security Control Summary

| Control Category | Controls Active | Controls Partial | Controls Missing | Overall Rating |
|-----------------|----------------|-----------------|-----------------|----------------|
| Authentication | 5 | 1 (API key expiry) | 1 (JWT/PII redaction) | B+ |
| Authorization | 4 | 1 (hardcoded policies) | 0 | B+ |
| Tenancy | 3 | 0 | 0 | A |
| Input Validation | 6 | 0 | 0 | A- |
| Ingestion Guardrails | 4 | 0 | 0 | B+ |
| Memory Guardrails | 3 | 2 (scope, audit) | 3 (trust, safety, calibration) | C+ |
| Temporal Guardrails | 1 | 1 (superseded_by_id partial) | 1 (contradiction) | C |
| Graph Guardrails | 2 | 0 | 1 (temporal transitions) | B- |
| Retrieval Guardrails | 3 | 0 | 2 (Memory in M5, vector search) | C+ |
| Security Headers | 2 | 1 (HSTS partial) | 1 (CSP) | C+ |
| Operational | 2 | 2 (rate limit, error recovery) | 2 (circuit breaker, graceful shutdown) | C |
| Audit | 3 | 1 (memory lifecycle) | 0 | B |

---

*End of Document: SWARMVAULT_GUARDRAIL_MASTER_MATRIX.md*
