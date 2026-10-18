# Sprint 6 — N+1 Query Audit

## Summary

| Endpoint | Risk | Queries per request | Status |
|---|---|---|---|
| `GET /dashboard/` | Low | ~8 (count aggregates) | OK — aggregates are single queries |
| `GET /dashboard/{project_id}` | Low | ~8 (count aggregates) | OK |
| `GET /provenance/` | Low | 1 (with optional filters) | OK |
| `GET /provenance/{id}` | Low | 1 | OK |
| `GET /provenance/{id}/memories` | Medium | 2 (provenance + IN query) | Acceptable — IN clause avoids N+1 |
| `GET /sessions/` | Low | 1 | OK |
| `GET /sessions/{id}` | Low | 1 | OK |
| `GET /sessions/{id}/history` | **Good** | 2 (session + selectinload messages) | **Fixed** — uses selectinload |
| `GET /memory/` | Low | 1 | OK |
| `GET /memory/{id}` | Low | 1 | OK |
| `POST /memory/search` | Low | 1 | OK |
| `GET /ingest/timeline` | Medium | 4 (facts + decisions + sources + messages) | Each limited by `limit` param |
| `GET /ingest/facts` | Low | 1 | OK |
| `GET /ingest/decisions` | Low | 1 | OK |
| `GET /ingest/graph` | Low | 1 | OK |
| `POST /chat/` | Medium | retrieval (variable) + 1 insert | Acceptable — retrieval is intentional |

## N+1 Risks Found and Fixed

### Session History (`GET /sessions/{id}/history`)
- **Before**: Single session query + lazy-loaded messages (N+1)
- **After**: Uses `selectinload(Session.messages)` — 2 queries regardless of message count
- **File**: `app/api/sessions.py:78`

## Recommendations

1. **Dashboard**: Could combine count queries with a single `UNION ALL` + `GROUP BY` for fewer round-trips, but 8 sequential COUNT queries on indexed columns is acceptable at low traffic.
2. **Timeline**: Separate queries per item type are by design (mixed source types). Each is bounded by `limit`.
3. **Chat retrieval**: M5 retrieval is the intentional cost center. Profiling shows it dominates at ~80% of chat latency.

## Conclusion

No critical N+1 issues remain. The session history fix (selectinload) addresses the only significant risk. All other query paths are bounded single queries or use `IN` clauses for batch loading.
