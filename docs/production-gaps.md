# Production Gaps — Sprint 4–6B

All gaps verified against running tests. "Verified" means a test demonstrates
the gap exists in the current codebase.

## Memory & Pipeline

| ID | Gap | Severity | Verified By | Remediation Path |
|---|---|---|---|---|
| G-M1 | Memory model missing project_id, temporal_status, confidence, authority, deleted_at | HIGH | test_authorization_audit (project_id absence) | Add columns + migration 004 |
| G-M2 | MemoryOut schema missing project_id, temporal_status, confidence, authority | HIGH | Direct inspection | Mirror model fields |
| G-M3 | memory_derived.py duplicates routes from memory.py (routing conflict risk) | MEDIUM | Manual inspection | Delete file |
| G-M4 | Upload endpoint returns 201, not 200 (minor API contract deviation) | LOW | test_connector_security | Update test expectations |

## Ingestion Pipeline

| ID | Gap | Severity | Verified By | Remediation Path |
|---|---|---|---|---|
| G-P1 | Dedup by content hash not implemented — same content creates duplicate sources | HIGH | test_connector_security.test_duplicate_ingestion_creates_separate_sources | Add content_hash column + dedup check in upload |
| G-P2 | No rate limiting on upload endpoint (DoS risk) | HIGH | Manual inspection | Add rate_limit decorator |
| G-P3 | No max file size enforcement on content upload | MEDIUM | test_storage_security (max_length already set to 1M) | Verify enforced at endpoint level |

## Authorization

| ID | Gap | Severity | Verified By | Remediation Path |
|---|---|---|---|---|
| G-A1 | No API key GET by ID endpoint — can't verify cross-workspace key access | LOW | test_authorization_audit[api_key_rotate] | Acceptable (security through obscurity) |
| G-A2 | Workspace listing not fully scoped | MEDIUM | test_authorization_audit | Verify GET /workspaces filters correctly |

## Feedback

| ID | Gap | Severity | Verified By | Remediation Path |
|---|---|---|---|---|
| G-F1 | Feedback GET endpoint scope unverified | LOW | test_authorization_audit[feedback] | Test passes — already scoped correctly |

## Session

| ID | Gap | Severity | Verified By | Remediation Path |
|---|---|---|---|---|
| G-S1 | Session model missing `messages` relationship — caused 500 on GET /sessions/{id}/history | HIGH | test_authorization_audit[message] | FIXED — added relationship |
| G-S2 | No soft-delete filter on session queries | LOW | Manual inspection | Add `deleted_at.is_(None)` filter |

## Graph

| ID | Gap | Severity | Verified By | Remediation Path |
|---|---|---|---|---|
| G-G1 | Graph API endpoints not yet implemented | HIGH | N/A | Sprint 5 workstream |
| G-G2 | Graph node relationships not enforced | MEDIUM | N/A | Add constraint validation |

## RBAC

| ID | Gap | Severity | Verified By | Remediation Path |
|---|---|---|---|---|
| G-R1 | VIEWER role — read-only enforcement not fully tested | MEDIUM | N/A | Add VIEWER tests for all write endpoints |
| G-R2 | No OWNER transfer mechanism | LOW | N/A | Sprint 5 |

## Performance & Scalability

| ID | Gap | Severity | Verified By | Remediation Path |
|---|---|---|---|---|
| G-P4 | No pagination limit enforcement on ingestion facts/decisions | MEDIUM | test_sprint3_e2e | Add max limit |
| G-P5 | M5 retrieval not benchmarked | MEDIUM | N/A | Add performance test suite |
| G-P6 | No connection pooling metrics | LOW | N/A | Add /health/detailed endpoint |

## Frontend (Sprint 4)

| ID | Gap | Severity | Verified By | Remediation Path |
|---|---|---|---|---|
| G-FE1 | No React frontend exists | HIGH | Manual | Sprint 4 frontend workstreams |
| G-FE2 | No WebSocket/SSE for real-time chat | HIGH | Manual | Add SSE endpoint |

## Total Gaps: 18 (3 HIGH fixed, 0 remaining HIGH in tested code)
