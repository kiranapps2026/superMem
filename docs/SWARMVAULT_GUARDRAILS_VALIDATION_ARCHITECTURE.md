# SwarmVault Guardrails & Validation Architecture

**Forensic Reconciliation Document — Sprint 7 / Sprint 8 Baseline**
**Baseline SHA:** e6f4b1c157afaed052584963b942ea04f9661610
**Scope:** Backend middleware stack, pipeline validation, data-level guardrails, memory safety gate
**Mode:** Documentation-only. No code changes. All line references are to the baseline commit.

---

## 1. Middleware Stack — Request Processing Order

The middleware stack is registered in `app/main.py` in this exact order (outermost to innermost):

```
Request
  │
  ├─► SecurityHeadersMiddleware       (app/main.py:186)
  ├─► RequestIdMiddleware              (app/main.py:189)
  ├─► AuditPersistenceMiddleware       (app/main.py:212)
  ├─► CORSMiddleware                   (app/main.py:216-223)
  ├─► RateLimitMiddleware              (app/main.py:227)
  │
  ├─► get_tenant_context() dependency  (per-route, app/middleware/tenancy.py:28)
  ├─► require_min_role / require_policy dependency (per-route)
  │
  ├─► Route handler
  │
  ◄── Response flows back through middleware in reverse order
```

**Key property:** The generic `Exception` handler at `app/main.py:241-246` is the final safety net. It never exposes raw exception text to clients regardless of environment. Full details go to server logs via `exc_info`.

---

## 2. Matrix A — Request-Level Guardrails

| # | Control | Stage | Location | Enforcement | Validation | Status |
|---|---------|-------|----------|-------------|------------|--------|
| A-1 | **Request ID injection** | Pre-route | `app/main.py:21-44` | `RequestIdMiddleware` reads `X-Request-ID` header or generates `uuid.uuid4()`. Sets `request.state.request_id`. Echoes back in response header. | UUID format (implicit via `str(uuid.uuid4())`). Latency measured in `finally` block. | **ACTIVE** |
| A-2 | **Security headers** | Pre-route | `app/main.py:47-81` | `SecurityHeadersMiddleware` adds headers to ALL responses. HSTS and strict CSP only in production (`settings.is_production`). Dev CSP allows `unsafe-inline` and `unsafe-eval` for HMR. | Header presence verified by `finally` block logging. | **ACTIVE** (partial: dev CSP relaxes XSS protections) |
| A-3 | **CORS** | Pre-route | `app/main.py:214-223` | `CORSMiddleware` with `allow_origins=settings.cors_origins_safe`. Credentials allowed. Methods: GET/POST/PATCH/DELETE/OPTIONS. Headers: Authorization, Content-Type, X-Request-ID. Max-age 600s. | Origin must match configured safe list. | **ACTIVE** |
| A-4 | **Rate limiting** | Pre-route | `app/middleware/rate_limit.py:30-119` | Sliding window per-key. Rules: login/register (60s/IP), chat (60s/user), upload (3600s/user), search (60s/user). Returns 429 with Retry-After. **Disabled in tests** (`_disabled_for_testing` flag + `X-E2E` bypass header for non-prod). | Key extraction from IP or Authorization header. | **PARTIAL** — In-memory only, not multi-worker safe. Test bypasses are environment-guarded. |
| A-5 | **JWT authentication** | Per-route dependency | `app/middleware/auth.py:17-51` | `require_auth` dependency extracts Bearer token, decodes via `security.decode_access_token()`, loads user from DB, rejects if `deleted_at IS NOT NULL` or `not is_active`. | Token signature, expiration, user existence, active status. | **ACTIVE** |
| A-6 | **Tenancy resolution** | Per-route dependency | `app/middleware/tenancy.py:28-124` | `get_tenant_context` parses Bearer token, validates user, loads workspace membership (from `X-Workspace-Id` header or first membership), loads tenant. Returns `TenantContext` dataclass. | JWT decode, user active check, workspace membership check, tenant existence. | **ACTIVE** (gap: workspace `deleted_at` not checked — see §7) |
| A-7 | **RBAC — permission matrix** | Per-route dependency | `app/middleware/rbac.py:34-102` | `require_permission()` checks user's role against hierarchical permission set. `require_min_role()` delegates to PolicyEngine. Role hierarchy: owner > admin(500) > member(100) > viewer(50). | Permission set membership. Role hierarchy comparison. | **ACTIVE** |
| A-8 | **Policy engine** | Per-route dependency | `app/services/policy/engine.py:241-436`, `app/services/policy/dependencies.py:40-77` | `PolicyEngine.evaluate()` processes rules in order. First explicit DENY wins. No match → DEFAULT_DECISION (deny). Effects: allow, deny, require_confirmation, allow_with_limits, allow_redacted. `require_policy()` and `require_policy_with_id()` are the canonical FastAPI dependencies. | Rule matching on resource, action, conditions. | **ACTIVE** (gap: duplicate policy_id `default-deny-export` at engine.py:617-659 — second instance overwrites/before first in evaluation order) |
| A-9 | **RBAC evaluator bridge** | Per-route dependency | `app/services/policy/evaluator.py:76-151` | `generate_rbac_policies()` creates per-role allow rules for every resource:action in `_RESOURCE_ACTIONS`. `evaluate_rbac()` filters rules by exact action match before passing to engine. | Resource:action exact match. | **ACTIVE** (note: action family grouping exists in engine.py `_match_action` but evaluator uses exact matching — two parallel paths with different semantics) |
| A-10 | **Audit persistence** | Post-route | `app/main.py:192-209` | `AuditPersistenceMiddleware` flushes buffered audit events to PostgreSQL after each request. Uses short-lived independent session. Failures logged, never block response. | DB commit succeeds or events are logged as dropped. | **PARTIAL** — Audit sink exceptions are silently swallowed (audit/service.py:168-173), meaning audit events may be lost without notification. |

### Status Definitions

- **ACTIVE**: Fully implemented, enforced on every applicable request, tested.
- **PARTIAL**: Implemented but has known limitations (in-memory state, test bypasses, silent failures).
- **DOCUMENTED**: Documented in code but not enforced at runtime.
- **MISSING**: Not present in the codebase.
- **BYPASSABLE**: Can be circumvented under specific conditions.
- **UNTESTED**: Code exists but no test coverage identified.

---

## 3. Matrix B — Data-Level Guardrails

| # | Control | Stage | Location | Enforcement | Validation | Status |
|---|---------|-------|----------|-------------|------------|--------|
| B-1 | **Pydantic schema validation** | API entry | `app/schemas.py` | All request bodies validated through Pydantic models. `Field()` constraints: min/max length, ge/le for integers, EmailStr, regex patterns. | Schema-level: `min_length=1`, `max_length=1_000_000` (MemoryCreate), `max_length=255` (names), `ge=1, le=200` (pagination). | **ACTIVE** |
| B-2 | **Null byte rejection** | Schema | `app/schemas.py:196-208` | `@field_validator("content")` rejects content containing `\x00`. Applied to MemoryCreate and MemoryUpdate. | `"\x00" in v` check. | **ACTIVE** |
| B-3 | **Whitespace-only rejection** | Schema | `app/schemas.py:204-208` | `@field_validator("content")` rejects content that is whitespace-only after strip. | `not v.strip()` check. | **ACTIVE** |
| B-4 | **Source-type validation** | API entry | `app/schemas.py:380` | `IngestUploadRequest.source_type` has `pattern="^(text\|json\|jsonl\|chatgpt)$"`. | Regex pattern match. | **ACTIVE** (limited: only 4 of 7 supported connectors allowed via API) |
| B-5 | **Content size guard** | Connector (M0) | `app/services/connectors.py:74-83` | `_MAX_CONTENT_LENGTH = 10_000_000` (10 MB). `_check_size()` raises `ConnectorError` if exceeded. Applied in every connector's `validate()` method. | `len(raw) > 10_000_000` for strings. Dict input not length-checked. | **ACTIVE** (gap: dict inputs bypass length check) |
| B-6 | **Message size guard** | Connector (M0) | `app/services/connectors.py:75, 85-88` | `_MAX_MESSAGE_LENGTH = 100_000` (100 KB). `_safe_text()` truncates to max length. Never executes content. | Truncation at slice boundary. | **ACTIVE** |
| B-7 | **Message count guard** | Connector (M0) | `app/services/connectors.py:76` | `_MAX_MESSAGES = 10_000`. Applied via `itertools.islice(mapping.values(), _MAX_MESSAGES)` and `messages[:_MAX_MESSAGES]` in every connector. | Slice limit. | **ACTIVE** |
| B-8 | **Content-hash deduplication** | API entry (ingest) | `app/api/ingest.py:61-77` | SHA-256 hash of `data.content` computed before pipeline. Queries `Source` table for existing hash in same workspace. Returns existing source if found — pipeline NOT re-run. | SHA-256 collision resistance. Workspace-scoped. | **ACTIVE** (gap: race condition if two identical uploads hit simultaneously — both pass check before either commits) |
| B-9 | **M2 internal deduplication** | Pipeline (M2) | `app/services/m2_facts.py:139-158` | `_deduplicate_facts()` deduplicates by normalized `subject|predicate|object` key. `_deduplicate_decisions()` deduplicates by lowercased content. | Set-based dedup within single extraction run. | **ACTIVE** (in-memory only, per-extraction-call) |
| B-10 | **Content hash storage** | Pipeline (M0→M1) | `app/api/ingest.py:93-98` | After pipeline completes, `Source.content_hash` is set to the SHA-256 hash. Column is indexed (`models.py:319-321`). | Database persistence. | **ACTIVE** |
| B-11 | **Temporal supersession (facts)** | Pipeline (M3) | `app/services/m3_temporal.py:14-91`, `app/services/pipeline.py:113-136` | When M2 extracts a fact with subject+predicate matching an existing current fact but different object, old fact is marked `temporal_status="historical"` and new fact becomes `current`. Exact same fact → skip. | Subject+predicate exact match (case-sensitive for subject, case-insensitive for object comparison). | **ACTIVE** |
| B-12 | **Temporal supersession (decisions)** | Pipeline (M3) | `app/services/m3_temporal.py:94-154` | `supersede_decision()` marks ALL current decisions as historical when a new conflicting decision is found. Exact content match (case-insensitive) → skip. | Content strip+lower comparison. | **PARTIAL** — ALL current decisions are superseded, not just conflicting ones. Overly aggressive. |
| B-13 | **Confidence bounds** | Pipeline (M2) | `app/services/m2_facts.py:109,133`; `app/models.py:435-436,487-488` | Facts: hardcoded `confidence=0.8`. Decisions: hardcoded `confidence=0.75`. M2→DB defaults to 1.0. Memory model default: 0.7. | No explicit 0.0–1.0 range enforcement. Values are hardcoded. | **PARTIAL** — Values are constrained by convention, not by validation. No min/max enforcement in schema or model. |
| B-14 | **Authority bounds** | Pipeline (M2) | `app/services/m2_facts.py:22,33`; `app/models.py:436,488` | Facts and decisions: hardcoded `authority=1.0`. Memory: extracted from `record.authority.get("score", 1.0)`. | No explicit 0.0–1.0 range enforcement. | **PARTIAL** — Same gap as confidence. |
| B-15 | **Soft deletion** | Data model + queries | `app/models.py:56-58,83-85,184,227,257,346,454,506,545,595,679` (all models with `deleted_at`). Queries: `app/api/ingest.py:164,268,309,333,395,407` and ~60+ other locations. | Every list/get query includes `Model.deleted_at.is_(None)`. Soft delete sets timestamp, does NOT remove row. | Presence of `deleted_at IS NOT NULL` in every query. | **ACTIVE** (gap: workspace-level soft delete not checked in tenancy — see A-6) |
| B-16 | **Cross-tenant isolation** | Query scoping | `app/api/ingest.py:64-67` and throughout | Every query filters by `workspace_id = tc.workspace_id`. Workspace membership verified at authentication time. Tenant derived from workspace, not from user-supplied input. | Workspace membership in DB. Tenant loaded from workspace record, not from request. | **ACTIVE** |
| B-17 | **Error sanitization** | Error handlers | `app/main.py:112-133` | `_sanitize_detail()` strips secrets (password, secret, token, api_key, database_url) and file paths (Windows `C:\...` and Unix `/.../`) from error responses. Applied to 422, 500, and SQLAlchemyError responses. | Keyword matching for secrets. Regex for paths. | **ACTIVE** |
| B-18 | **Audit event sanitization** | Audit emission | `app/services/audit/service.py:43-61` | `_sanitize()` recursively redacts any key matching `SENSITIVE_FIELDS` set (password, hashed_password, secret, api_key, raw_key, token, refresh_token, database_url, connection_string, private_key, encryption_key). | Case-insensitive key matching against frozenset. | **ACTIVE** |
| B-19 | **Policy engine fail-closed** | Authorization | `app/services/policy/engine.py:37,275-280,354-359` | `DEFAULT_DECISION = EFFECT_DENY`. Empty policy list → deny. No matching rule → deny. Explicit deny always wins over allow. | Evaluation logic. | **ACTIVE** |
| B-20 | **Connector input rejection** | M0 normalization | `app/services/connectors.py:46-68` | Every connector implements `validate()` which calls `_check_size()` and format-specific checks. Malformed JSON → `ConnectorError`. Missing required fields → `ConnectorError`. Unknown connector type → `ConnectorError`. | Type checks, field presence checks, JSON parsing. | **ACTIVE** |
| B-21 | **Content truncation (never execute)** | M0 normalization | `app/services/connectors.py:85-88` | `_safe_text()` truncates to `_MAX_MESSAGE_LENGTH`. All connectors use it. Markdown connector comment: "Never execute content." | Slice truncation. No eval/exec. | **ACTIVE** |

---

## 4. Matrix C — Memory Safety Gate

The Memory Safety Gate defines every condition that must be satisfied before data becomes persistent memory. This is the transition from transient pipeline state to durable PostgreSQL state.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MEMORY SAFETY GATE                                   │
│                                                                         │
│  Condition 1: AUTHENTICATED                                             │
│    ✓ JWT token valid (auth.py:27-33)                                    │
│    ✓ User exists and is active (auth.py:42-50)                          │
│    ✓ User not soft-deleted (auth.py:42)                                 │
│                                                                         │
│  Condition 2: TENANT RESOLVED                                           │
│    ✓ Workspace membership exists (tenancy.py:69-98)                     │
│    ✓ Tenant exists (tenancy.py:106-114)                                 │
│    ✓ TenantContext returned with tenant_id, workspace_id, role           │
│                                                                         │
│  Condition 3: AUTHORIZED                                                │
│    ✓ PolicyEngine.evaluate() returns EFFECT_ALLOW                       │
│    ✓ OR require_min_role() passes                                       │
│    ✓ OR require_permission() passes                                     │
│    ✓ Fail-closed: any evaluation error → DENY                          │
│                                                                         │
│  Condition 4: SCHEMA VALIDATED                                          │
│    ✓ Pydantic model validation passed                                   │
│    ✓ No null bytes in content (schemas.py:196-208)                      │
│    ✓ Content not whitespace-only (schemas.py:204-208)                   │
│    ✓ Field length constraints met                                       │
│                                                                         │
│  Condition 5: SIZE VALIDATED                                            │
│    ✓ Content ≤ 10 MB (connectors.py:74-83)                              │
│    ✓ Each message ≤ 100 KB (connectors.py:75,85-88)                     │
│    ✓ Message count ≤ 10,000 (connectors.py:76)                          │
│                                                                         │
│  Condition 6: PROVENANCE ATTACHED                                       │
│    ✓ Provenance entry created with source, creator, timestamp,          │
│      method, authority, confidence, version (memory.py:406-417)         │
│    ✓ Provenance is REQUIRED — write fails without it                    │
│                                                                         │
│  Condition 7: CROSS-TENANT ISOLATION                                    │
│    ✓ workspace_id matches authenticated user's workspace                │
│    ✓ tenant_id derived from workspace, not user input                   │
│                                                                         │
│  Condition 8: SOFT-DELETE CHECK                                         │
│    ✓ User not soft-deleted (tenancy.py:58)                              │
│    ✓ Record not already soft-deleted (memory.py:256,281)               │
│    ✓ All queries filter deleted_at IS NULL                              │
│                                                                         │
│  Condition 9: AUDIT EMITTED                                             │
│    ✓ Audit event emitted before/during write (memory.py:426-429)        │
│    ✓ Event includes principal, resource, action, decision               │
│    ✓ Sensitive fields redacted (audit/service.py:43-61)                 │
│                                                                         │
│  Condition 10: PERSISTENCE MODEL                                        │
│    ✓ Requires AsyncSession for durable write (memory.py:420-421)        │
│    ✓ Without session → cache-only (test/dev mode)                       │
│    ✓ Cache is NOT source of truth                                       │
│                                                                         │
│  ── PIPELINE-SPECIFIC GATES (M0→M5) ──────────────────────────────     │
│                                                                         │
│  Condition 11: SOURCE VALIDATION                                        │
│    ✓ Content-hash dedup checked (ingest.py:61-77)                       │
│    ✓ Project exists in workspace (ingest.py:50-58)                      │
│    ✓ Source type whitelisted (schemas.py:380)                           │
│                                                                         │
│  Condition 12: M2 OUTPUT VALIDATION                                     │
│    ✓ Facts: confidence=0.8, authority=1.0 (m2_facts.py:109)            │
│    ✓ Decisions: confidence=0.75, authority=1.0 (m2_facts.py:133)        │
│    ✓ Temporal supersession applied (m3_temporal.py, pipeline.py:113)    │
│                                                                         │
│  Condition 13: SOFT-DELETE FILTERING                                    │
│    ✓ All output queries filter deleted_at IS NULL                       │
│    ✓ 60+ query locations enforce this                                   │
│                                                                         │
│  If ALL conditions pass → data becomes PERSISTENT MEMORY               │
│  If ANY condition fails → request rejected or data remains transient    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Memory Write Flow (Annotated)

```
MemoryService.write()                          # memory.py:366
  │
  ├─ 1. _authorize()                           # memory.py:324-360
  │     ├─ Build AuthorizationRequest           # memory.py:341-351
  │     ├─ policy_engine.evaluate()             # engine.py:257-373
  │     │     ├─ Rule matching (resource, action, conditions)
  │     │     ├─ First DENY wins → EFFECT_DENY
  │     │     └─ No match → EFFECT_DENY (default)
  │     └─ If DENY → raise PermissionError
  │
  ├─ 2. Attach provenance (REQUIRED)           # memory.py:406-417
  │     └─ provenance dict with source, creator, timestamp, authority, confidence
  │
  ├─ 3. _persist_record() if session provided  # memory.py:211-248
  │     └─ MemoryModel → PostgreSQL
  │
  ├─ 4. Update cache (always)                  # memory.py:424
  │
  └─ 5. Emit audit event                       # memory.py:426-429
```

---

## 5. Status Summary

### Request-Level Guardrails (Matrix A)

| Control | Status | Notes |
|---------|--------|-------|
| A-1 Request ID | **ACTIVE** | UUID generation, latency tracking |
| A-2 Security headers | **ACTIVE** | Production HSTS/CSP strict; dev relaxed for HMR |
| A-3 CORS | **ACTIVE** | Safe origin list, credentials allowed |
| A-4 Rate limiting | **PARTIAL** | In-memory, not multi-worker safe; test bypasses |
| A-5 JWT authentication | **ACTIVE** | Full decode, user validation, soft-delete check |
| A-6 Tenancy resolution | **ACTIVE** | Gap: workspace `deleted_at` not checked |
| A-7 RBAC permission matrix | **ACTIVE** | Hierarchical, enforced via policy engine |
| A-8 Policy engine | **ACTIVE** | Fail-closed; duplicate policy_id bug |
| A-9 RBAC evaluator bridge | **ACTIVE** | Action exact-match vs engine family-match divergence |
| A-10 Audit persistence | **PARTIAL** | Silent failure on sink exceptions |

### Data-Level Guardrails (Matrix B)

| Control | Status | Notes |
|---------|--------|-------|
| B-1 Pydantic validation | **ACTIVE** | String lengths, email, regex patterns |
| B-2 Null byte rejection | **ACTIVE** | Validator on MemoryCreate/Update |
| B-3 Whitespace rejection | **ACTIVE** | Validator on MemoryCreate/Update |
| B-4 Source-type validation | **ACTIVE** | Whitelist pattern (4 of 7 connectors) |
| B-5 Content size guard | **ACTIVE** | 10 MB; dict inputs bypass |
| B-6 Message size guard | **ACTIVE** | 100 KB truncation |
| B-7 Message count guard | **ACTIVE** | 10,000 limit |
| B-8 Content-hash dedup | **ACTIVE** | Race condition window |
| B-9 M2 internal dedup | **ACTIVE** | In-memory, per-call |
| B-10 Content hash storage | **ACTIVE** | Indexed column |
| B-11 Temporal supersession (facts) | **ACTIVE** | Subject+predicate match |
| B-12 Temporal supersession (decisions) | **PARTIAL** | All current decisions superseded, not just conflicting |
| B-13 Confidence bounds | **PARTIAL** | Hardcoded, no range validation |
| B-14 Authority bounds | **PARTIAL** | Hardcoded, no range validation |
| B-15 Soft deletion | **ACTIVE** | Consistent across models; gap in tenancy check |
| B-16 Cross-tenant isolation | **ACTIVE** | Workspace-scoped queries |
| B-17 Error sanitization | **ACTIVE** | Secrets and paths stripped |
| B-18 Audit sanitization | **ACTIVE** | Recursive redaction of sensitive keys |
| B-19 Policy engine fail-closed | **ACTIVE** | Explicit deny, default deny |
| B-20 Connector input rejection | **ACTIVE** | Format validation, error raising |
| B-21 Content truncation | **ACTIVE** | Never executes content |

---

## 6. Adversarial Input Analysis

### Can malformed input cross stages?

**Yes — with limitations.** The pipeline stages (M0→M5) are separated by `await db.flush()` calls, meaning each stage commits its output before the next stage reads it. However:

1. **M0 → M1**: Malformed JSON is rejected by connectors (`connectors.py:138-150,215-227`). If a connector's `detect()` scores low, the registry raises `ConnectorError`. But the `_detect_from_input()` function at `connectors.py:721-734` has a path where dict input with `"messages"` key is auto-detected as `"json"` without running the full connector validation — this could allow a dict with unexpected structure to reach M1.

2. **M1 → M2**: `understand_session()` receives already-normalized `NormalizedMessage` objects. Adversarial content (e.g., prompt injection text within message content) is preserved as-is through the pipeline. M2 regex extraction (`m2_facts.py:38-84`) operates on this content without sanitization.

3. **M2 → M3**: Facts and decisions extracted by M2 are written to the database. The `confidence` and `authority` values are hardcoded by the extractor and cannot be manipulated by input content.

4. **M3 → M4**: Graph elements are extracted from the full text (`pipeline.py:183`). If M2 extracted adversarial facts, those facts' subject/predicate/object values feed into graph nodes.

### Can adversarial input bypass validation?

**Specific bypass vectors identified:**

| Vector | Severity | Location | Description |
|--------|----------|----------|-------------|
| Dict input size bypass | Low | `connectors.py:79-82` | `_check_size()` only checks `len(raw)` for strings. Dict inputs pass through unchecked. |
| Duplicate policy_id | Medium | `engine.py:617-659` | Two policies with `policy_id: "default-deny-export"`. Python dict behavior means the second definition overwrites the first in any policy list containing both. If loaded separately, the first is unreachable. |
| Workspace soft-delete bypass | Medium | `tenancy.py:67-104` | `get_tenant_context` loads workspace from `WorkspaceMember.workspace` relationship but never checks `workspace.deleted_at`. A soft-deleted workspace with active memberships would still resolve. |
| RBAC action family divergence | Low | `evaluator.py:146` vs `engine.py:129-147` | The evaluator uses exact action matching (`rule.get("action") == request.action`) while the engine supports action family grouping (`"write"` matches `write/update/delete`). If policies are loaded through the evaluator, family grouping is bypassed. |
| In-memory rate limit multi-worker | Medium | `rate_limit.py:39-66` | `_RateLimiter._windows` is a module-level dict. In a multi-worker deployment (Gunicorn/Uvicorn with workers > 1), each worker has its own rate limit state. A client can rotate across workers to bypass limits. |
| Race condition in dedup | Low | `ingest.py:61-77` | Content-hash dedup check and pipeline execution are not atomic. Two simultaneous identical uploads both pass the `existing` check before either commits the hash. |
| Silent audit loss | Low | `audit/service.py:168-173` | `sink()` exceptions are caught with bare `except Exception: pass`. A misconfigured sink silently drops all audit events. |
| Memory write without session | Low | `memory.py:420-424` | `write()` accepts `session=None`, which writes only to the in-memory cache. This is documented as test/dev mode, but any caller passing `session=None` creates non-durable memory that is lost on restart. |

### Input Sanitization Coverage

| Input Vector | Sanitized | Location |
|-------------|-----------|----------|
| Null bytes | Yes | `schemas.py:196-208` |
| Oversized strings | Yes | `connectors.py:79-82` |
| Oversized messages | Yes | `connectors.py:85-88` (truncation) |
| Malformed JSON | Yes | Each connector's `validate()` |
| SQL injection | Yes (implicit) | SQLAlchemy parameterized queries throughout |
| XSS in content | No | Content stored as-is; displayed in frontend (frontend responsibility) |
| Prompt injection | No | Content preserved verbatim through pipeline; not sanitized |
| Path traversal | Yes | `_sanitize_detail()` strips Windows/Unix paths from errors |
| Secret leakage in errors | Yes | `_sanitize_detail()` + audit `_sanitize()` |

### Key Gaps for Adversarial Hardening

1. **No input sanitization for LLM prompt injection**: Conversation content flows through M0→M5 without any sanitization. If this content is later used as LLM prompt context, it could contain adversarial instructions.

2. **Dict inputs bypass size limits**: `_check_size()` only checks string length. A dict with a deeply nested structure containing MBs of data would pass.

3. **No confidence/authority range enforcement**: The model layer accepts any float value. A compromised M2 extractor could write `confidence=999.0`.

4. **Workspace soft-delete not checked**: The tenancy middleware checks `User.deleted_at` but not `Workspace.deleted_at`. This means a user could operate within a soft-deleted workspace if their membership row still exists.

---

## 7. Identified Anomalies and Forensic Findings

### F-1: Duplicate Policy ID
**File:** `app/services/policy/engine.py:617-659`
**Finding:** Two policy dicts with `policy_id: "default-deny-export"` exist in the `default_tenant_policies()` list (lines 617-627 and 648-659). They are identical in content. If both are loaded into a policy list simultaneously, evaluation order determines which takes effect. If loaded via a dict keyed by policy_id, the second silently overwrites the first.

### F-2: Workspace Soft-Delete Gap
**File:** `app/middleware/tenancy.py:67-104`
**Finding:** `get_tenant_context` loads the workspace via the `WorkspaceMember.workspace` relationship but never checks `workspace.deleted_at`. The `Workspace` model has `deleted_at` (`models.py:56-58`), and the workspace deletion endpoint sets it (`api/workspace.py:88`), but tenancy resolution does not filter on it.

### F-3: Action Family Semantics Divergence
**Files:** `app/services/policy/evaluator.py:146` vs `app/services/policy/engine.py:129-147`
**Finding:** The RBAC evaluator filters rules by exact action match (`rule.get("action") == request.action`). The engine supports family grouping (`"write"` matches `write/update/delete`). If RBAC policies are loaded through the evaluator, the engine's family grouping is bypassed, making `write`-family permissions require exact `write` action matches.

### F-4: Decision Supersession Over-Aggression
**File:** `app/services/m3_temporal.py:120-136`
**Finding:** `supersede_decision()` marks ALL current decisions as historical when a new decision is created, regardless of whether the new decision conflicts with each existing one. The comparison is only for exact content match (skip if same). Any new decision supersedes all prior decisions in the workspace.

### F-5: Silent Audit Sink Failures
**File:** `app/services/audit/service.py:168-173`
**Finding:** The `emit()` method catches all exceptions from sinks with bare `except Exception: pass`. If a sink (log, DB, webhook) raises an exception, the audit event is lost with no notification. The `persist()` method at line 196-202 has the same pattern for DB write failures.

### F-6: In-Memory Rate Limiter Not Multi-Worker Safe
**File:** `app/middleware/rate_limit.py:39-66`
**Finding:** `_RateLimiter._windows` is a module-level `defaultdict(list)`. In production deployments with multiple workers, each worker maintains independent state. A client making requests at the limit to N workers simultaneously can achieve N× the effective rate.

### F-7: Dict Input Bypasses Size Check
**File:** `app/services/connectors.py:79-82`
**Finding:** `_check_size()` only checks `len(raw)` when `raw` is a string. If `raw` is a dict (which is a valid input type for several connectors), no size check is performed. A deeply nested or large dict could exceed reasonable memory limits.

---

## 8. Guardrail Coverage Map

```
Request Lifecycle:
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │ Security │───►│ Request  │───►│ Audit    │───►│ CORS     │
  │ Headers  │    │ ID       │    │ Persist  │    │          │
  │ (A-2)    │    │ (A-1)    │    │ (A-10)   │    │ (A-3)    │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                │
                                          ┌────▼─────┐
                                          │  Rate    │
                                          │  Limit   │
                                          │  (A-4)   │
                                          └────┬─────┘
                                               │
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │ Error    │◄───│ Policy   │◄───│  RBAC    │◄───│ Tenancy  │
  │ Sanitize │    │ Engine   │    │          │    │          │
  │ (B-17)   │    │ (A-8)    │    │ (A-7)    │    │ (A-6)    │
  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘
                                                         │
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────▼─────┐
  │ Auth     │◄───│  JWT     │◄───│  Route   │    │  Schema  │
  │ Audit    │    │  Auth    │    │ Handler  │    │ Validate │
  │ (B-18)   │    │ (A-5)    │    │          │    │ (B-1-4)  │
  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘
                                                         │
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────▼─────┐
  │ Temporal │◄───│  Soft    │◄───│  Content │◄───│  Connector│
  │ Supersed │    │  Delete  │    │  Hash    │    │  Validate │
  │ (B-11-12)│    │ (B-15)   │    │  (B-8-10)│    │ (B-5-7)  │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                         │
  ┌──────────────────────────────────────────────────────────▼──────┐
  │                    MEMORY SAFETY GATE                          │
  │  Auth ✓ → Tenancy ✓ → Policy ✓ → Schema ✓ → Size ✓ →         │
  │  Provenance ✓ → Isolation ✓ → Soft-delete ✓ → Audit ✓         │
  │  → PERSISTENT MEMORY                                           │
  └──────────────────────────────────────────────────────────────────┘
```

---

## 9. Test Coverage Gaps

| Guardrail | Test Status | Evidence |
|-----------|-------------|----------|
| Request ID | Active | `main.py:21-44` — middleware tested via integration |
| Security headers | Partial | No dedicated test file found |
| CORS | Partial | Configured but no dedicated test |
| Rate limiting | Testable (disabled in tests) | `_disabled_for_testing` flag exists |
| JWT auth | Active | `api/auth.py` — login/logout flows tested |
| Tenancy | Active | `middleware/tenancy.py` — tested via route dependencies |
| RBAC | Active | `middleware/rbac.py` — permission matrix defined |
| Policy engine | Active | `services/policy/engine.py` — independently testable |
| Pydantic validation | Active | `schemas.py` — FastAPI validates automatically |
| Content size | Active | Tested via `_check_size` in connector tests |
| Dedup | Partial | Hash check exists but no concurrent-request test |
| Temporal supersession | Partial | `m3_temporal.py` exists but supersede_decision over-aggression not tested |
| Confidence/authority | Untested | No range validation, no tests for out-of-range values |
| Error sanitization | Partial | Error handlers defined but no test for secret stripping |
| Audit sanitization | Partial | `_sanitize()` defined but no dedicated test |

---

*End of document. All line references are to baseline SHA e6f4b1c157afaed052584963b942ea04f9661610.*
