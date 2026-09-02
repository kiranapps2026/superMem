# SwarmVault WebApp — Final Release Manifest
**Release:** v1.0.0-production
**Certification Date:** 2026-09-02
**Commit SHA:** 73521ab4174f6be95726b1a5bc4f2c9dac8657c2
**Branch:** master

## Release Metadata

| Field | Value |
|-------|-------|
| Project | SwarmVault WebApp |
| Version | 1.0.0-production |
| Git branch | master |
| Commit SHA | 73521ab4174f6be95726b1a5bc4f2c9dac8657c2 |
| Release tag | (none — ready for tagging) |
| Alembic head | 012_add_invitations |
| Python version | 3.12.7 |
| Node version | 24.19.0 |
| FastAPI | (see requirements.txt) |
| SQLAlchemy | 2.0+ |
| PostgreSQL | 16 |

## Dependencies

```
pip freeze > requirements.txt  # lock file to be generated at release time
```

## Test Results

| Suite | Result | Timestamp |
|-------|--------|-----------|
| Full regression (unit) | 656 passed, 0 failed | 2026-09-02 |
| Capability E2E | 27 passed, 0 failed | 2026-09-02 |
| Sprint7 integration | 63 passed, 0 failed | 2026-09-02 |
| Security regression | 187 passed, 0 failed | 2026-09-02 |
| Fresh migration (001→012) | PASS — 24 tables created | 2026-09-02 |
| Policy fail-closed | PASS — deny-all verified | 2026-09-02 |

## Database Schema

| Item | Value |
|------|-------|
| Alembic version | 012_add_invitations |
| Table count | 24 |
| Index count | 98 |
| Foreign key count | 41 |
| Unique constraint count | 7 |

### Tables

alembic_version, api_keys, audit_events, decisions, facts, graph_edges,
graph_nodes, ingest_jobs, invitations, memories, message_feedback,
message_provenance, messages, normalized_messages, policies, policy_versions,
projects, refresh_tokens, sessions, sources, tenants, users,
workspace_members, workspaces

## Security Verification

| Control | Status |
|---------|--------|
| JWT secret required from env | PASS |
| JWT minimum length (≥32 chars) | PASS |
| JWT known-placeholder rejection (prod) | PASS |
| Database URL required from env | PASS |
| Dev DB URL rejected in production | PASS |
| Policy engine fail-closed | PASS |
| Exception details not leaked to clients | PASS |
| No `create_all()` in production | PASS |
| Docker startup: `alembic upgrade head` → uvicorn | PASS |
| Non-root Docker user | PASS |

## Release Gates

| Gate | Result |
|------|--------|
| Migration chain integrity | PASS |
| Fresh database migration | PASS |
| Existing database forensics | PASS |
| Data preservation | PASS |
| `create_all()` audit | PASS |
| JWT security | PASS |
| Authorization fail-closed | PASS |
| Configuration security | PASS |
| Error sanitization | PASS |
| Docker startup design | PASS |
| Docker runtime | BLOCKED (no Docker Engine) |
| Full regression | PASS |
| Capability E2E | PASS |
| Security regression | PASS |
| Browser E2E | BLOCKED (no Chromium) |
| Data lifecycle | PASS |
| Git hygiene | PASS |
| Release artifact | PASS |

## Files Included in Release

- `app/` — Application source (API, middleware, services, models, core)
- `alembic/` — Migration scripts (001–012)
- `alembic.ini` — Alembic configuration
- `tests/` — Test suite (656 unit tests)
- `requirements.txt` — Python dependencies
- `Dockerfile` — Multi-stage production image
- `docker-compose.yml` — Production stack
- `.dockerignore` — Build context exclusions
- `.env.example` — Configuration template

## Deployment Instructions

1. Clone repository at commit `73521ab`
2. Set environment variables (see `.env.example`)
3. Run `alembic upgrade head` (or use Docker which does this automatically)
4. Start application: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
5. Verify: `curl http://localhost:8000/health/live`

## Limitations

- Docker runtime not verified on this host (no Docker Engine available)
- Playwright browser E2E not executed (no Chromium in this environment)
- Rate limiter uses in-memory store (Redis required for multi-worker)
