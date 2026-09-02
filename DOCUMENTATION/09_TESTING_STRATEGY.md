# SwarmVault WebApp — Comprehensive Testing Strategy
**Version:** 1.0.0
**Date:** 2026-09-01
**Evidence base:** Repository inspection (commit 902d85e), tests/unit/

---

## 1. Test Architecture

### Tooling
- **Framework:** pytest
- **Async testing:** pytest-asyncio
- **HTTP client:** httpx (AsyncClient, ASGITransport)
- **Test runner script:** `run_tests.py` (supports `--all`, `--tier-1`, etc.)
- **Coverage:** NOT ESTABLISHED IN AVAILABLE SOURCE (pytest-cov possibly present)

### Test Database
- **URL:** `postgresql+asyncpg://swarmvault:swarmvault@localhost:5432/swarmvault_test`
- **Fixture scope:** session (shared engine, schema created/dropped once)
- **Isolation:** Each test wrapped in transaction that rolls back (zero DB leakage)
- **Rate limiter:** Disabled for all tests via `_rate_limiter._disabled_for_testing = True`

### Test Organization
```
tests/
├── conftest.py                          # Shared fixtures (db, client, auth)
├── unit/
│   ├── test_auth.py                     # Authentication flows
│   ├── test_chat.py                     # Chat/chat completion
│   ├── test_chat_sprint2.py             # Sprint 2 chat features
│   ├── test_memory.py                   # Memory CRUD
│   ├── test_sessions.py                 # Session management
│   ├── test_projects.py                 # Project CRUD
│   ├── test_workspace.py                # Workspace management
│   ├── test_ingest.py                   # Ingestion pipeline
│   ├── test_provenance_explorer.py      # Provenance tracking
│   ├── test_dashboard.py                # Dashboard endpoints
│   ├── test_api_keys.py                 # API key management
│   ├── test_audit_api.py                # Audit API
│   ├── test_audit_service.py            # Audit service logic
│   ├── test_authorization_audit.py      # Authorization audit
│   ├── test_connector_security.py       # Connector security
│   ├── test_connectors.py               # Connector integrations
│   ├── test_golden_dataset.py           # Golden dataset tests
│   ├── test_pagination.py               # Pagination
│   ├── test_pipeline.py                 # Pipeline processing
│   ├── test_policy_engine.py            # Policy engine
│   ├── test_policy_rbac_integration.py  # Policy + RBAC integration
│   ├── test_rate_limit.py               # Rate limiting
│   ├── test_rate_limit_api.py           # Rate limit API
│   ├── test_rbac_security.py            # RBAC security tests
│   ├── test_security_6b.py              # Security tests (sprint 6b)
│   ├── test_security_matrix.py          # Security matrix tests
│   ├── test_services.py                 # Service layer
│   ├── test_sprint3_e2e.py              # Sprint 3 end-to-end
│   ├── test_sprint4_e2e.py              # Sprint 4 end-to-end
│   ├── test_sprint4_golden.py           # Sprint 4 golden tests
│   ├── test_sprint4_security.py         # Sprint 4 security
│   ├── test_sprint7_integration.py      # Sprint 7 integration
│   ├── test_storage.py                  # Storage backend
│   ├── test_storage_api.py              # Storage API
│   ├── test_storage_security.py         # Storage security
│   ├── test_tenancy.py                  # Multi-tenancy
│   └── fixtures/                         # Test fixtures
│       ├── __init__.py
│       └── (fixture files)
├── fixtures/                            # Top-level fixtures
└── __init__.py
```

### Test Count
- **Total tests:** ~959 collected
- **Passing:** ~829
- **Must fix/skip/xfail:** ~130

---

## 2. Test Tiers

| Tier | Name | Description | Cost | Speed |
|------|------|-------------|------|-------|
| 1 | Pure | Unit tests, no external dependencies | Free | < 30s |
| 2 | Recorded Contracts | API contract tests with recorded responses | Free | < 1min |
| 3 | Live API | Tests against live Google APIs | Free | Slow |
| 4 | Model Evals | Evaluations using Claude API | **Tokens** | Slow |

### Tier 1 (Pure)
- Auth flows (register, login, token validation)
- Memory CRUD operations
- Session management
- Project CRUD
- Workspace management
- Tenant isolation
- Cross-tenant protection
- RBAC role checks
- Input validation
- Pagination
- Rate limiting

### Tier 3 (Live API)
- Google Workspace integrations (Drive, Sheets, Docs, etc.)
- Requires configured credentials
- Tests against real Google APIs

### Tier 4 (Model Evals)
- Engine changes
- LLM output evaluation
- **Cannot run when engine changes affect operator selection**
- **On Sonnet, cached by content hash**

---

## 3. Key Test Suites

### Auth Tests (test_auth.py)
- User registration with valid data
- Registration with duplicate email → 409
- Login with valid credentials → 200 + tokens
- Login with invalid credentials → 401
- Token refresh flow
- Invalid token rejection
- Token expiry handling

### Memory Tests (test_memory.py)
- Create memory (authenticated)
- Get memory by ID
- List memories with pagination
- Update memory
- Delete memory (soft delete)
- Memory type filtering
- Project-scoped memory queries
- Cross-tenant isolation

### Session Tests (test_sessions.py)
- Create session
- List user sessions
- Add messages to session
- Session soft delete
- Cross-tenant session isolation

### Project Tests (test_projects.py)
- Create project in workspace
- List projects
- Get project by ID
- Update project
- Delete project (soft)
- Cross-workspace project isolation

### Workspace Tests (test_workspace.py)
- Create workspace
- List user workspaces
- Invite member
- Update member role
- Remove member
- Workspace member enumeration

### Ingest Tests (test_ingest.py)
- Upload text file
- Upload JSON file
- Upload JSONL file
- Upload ChatGPT export
- Job status polling
- Cross-tenant job isolation

### Provenance Tests (test_provenance_explorer.py)
- Track LLM interaction provenance
- Query provenance by session
- Query provenance by project
- Provenance schema validation

### Dashboard Tests (test_dashboard.py)
- Get dashboard stats
- Memory counts by type
- Source counts by status
- Cross-tenant dashboard isolation

### API Key Tests (test_api_keys.py)
- Create API key (returns full key once)
- List API keys
- Revoke API key
- Use revoked key → 401
- Key prefix display (no raw key exposure)

### Security Tests
- `test_security_6b.py` — Sprint 6b security
- `test_security_matrix.py` — Security matrix coverage
- `test_connector_security.py` — Connector auth
- `test_storage_security.py` — Storage access controls
- `test_sprint4_security.py` — Sprint 4 security

### Tenancy Tests (test_tenancy.py)
- Multi-tenant data isolation
- Cross-tenant read protection
- Cross-tenant write protection
- Tenant context from JWT
- Workspace switching via X-Workspace-Id

### RBAC Tests
- `test_rbac_security.py` — Role enforcement
- `test_authorization_audit.py` — Authorization logging
- `test_policy_rbac_integration.py` — Policy engine + RBAC

### Golden Dataset Tests (test_golden_dataset.py)
- Known correct outputs
- Regression testing against expected results

### Sprint Integration Tests
- `test_sprint3_e2e.py` — Sprint 3 full pipeline
- `test_sprint4_e2e.py` — Sprint 4 features
- `test_sprint4_golden.py` — Sprint 4 golden outputs
- `test_sprint7_integration.py` — Sprint 7 integration

---

## 4. Cross-Tenant Isolation Tests

Multiple test files verify that data does not leak across tenants:

| Test File | What It Checks |
|-----------|---------------|
| test_tenancy.py | General tenant isolation |
| test_memory.py | Memory not visible to other tenant |
| test_sessions.py | Sessions not visible to other tenant |
| test_projects.py | Projects not visible to other tenant |
| test_chat.py | Chat history not visible to other tenant |
| test_ingest.py | Ingest jobs not visible to other tenant |
| test_graph_cross_tenant_isolation | Graph queries scoped to tenant |

### Isolation Mechanism
All route handlers must include `tenant_id` (from TenantContext) in every query. Tests create two tenants, perform operations in one, then verify the other tenant sees empty results.

---

## 5. E2E Test Scenarios

### E2E Flow 1: Onboarding
1. Register new user
2. Create workspace (auto-created on register)
3. Upload a document
4. View ingested memories
5. Chat with knowledge base
6. View provenance of chat

### E2E Flow 2: Team Workspace
1. Create tenant
2. Invite member via email
3. Member accepts invitation
4. Member uploads documents
5. Owner views team memories
6. Admin changes member role

### E2E Flow 3: Project Isolation
1. Create project in workspace
2. Upload documents to project
3. Query memories scoped to project
4. Cross-project data isolation verified

### E2E Flow 4: Memory Lifecycle
1. Ingest document → Source created
2. Normalized messages extracted
3. Facts extracted
4. Decisions extracted
5. Graph nodes/edges created
6. Memories queried via chat

---

## 6. Sprint-Aligned Test Coverage

| Sprint | Key Test Files | Coverage Area |
|--------|---------------|---------------|
| 1 | test_auth, test_workspace | Auth + workspace |
| 2 | test_chat_sprint2, test_memory | Chat + memory CRUD |
| 3 | test_sprint3_e2e, test_pipeline | Full ingestion pipeline |
| 4 | test_sprint4_e2e, test_sprint4_golden, test_sprint4_security | Core features |
| 5 | test_provenance_explorer | Provenance tracking |
| 6 | test_security_6b, test_security_matrix, test_connector_security, test_storage_security | Security |
| 7 | test_sprint7_integration | Sprint 7 features |

---

## 7. Test Data Models (from fixtures)

### User
```python
{
    "id": UUID string,
    "email": str,
    "name": str,
    "is_active": bool,
    "email_verified": bool,
    "created_at": datetime (UTC)
}
```

### Workspace
```python
{
    "id": UUID string,
    "tenant_id": UUID string,
    "name": str,
    "slug": str,
    "description": str | None,
    "created_at": datetime (UTC)
}
```

### Memory
```python
{
    "id": UUID string,
    "tenant_id": UUID string,
    "workspace_id": UUID string,
    "user_id": UUID string,
    "agent_id": UUID string | None,
    "run_id": UUID string | None,
    "project_id": UUID string | None,
    "memory_type": str (default "procedural_memory"),
    "content": str,
    "metadata": dict | None,
    "embedding": list[float] | None,
    "temporal_status": str (default "current"),
    "confidence": float (default 0.7),
    "authority": float (default 1.0),
    "deleted_at": datetime | None,
    "created_at": datetime (UTC),
    "updated_at": datetime (UTC)
}
```

### Source
```python
{
    "id": UUID string,
    "project_id": UUID string,
    "workspace_id": UUID string,
    "tenant_id": UUID string,
    "source_type": str,
    "external_id": str | None,
    "content_hash": str | None,
    "title": str | None,
    "description": str | None,
    "raw_content_path": str | None,
    "message_count": int (default 0),
    "status": str (default "queued"),
    "stage": str | None,
    "progress": int (default 0),
    "error_message": str | None,
    "config": dict | None,
    "started_at": datetime | None,
    "completed_at": datetime | None
}
```

### Fact (M2 output)
```python
{
    "id": UUID string,
    "workspace_id": UUID string,
    "project_id": UUID string | None,
    "source_id": UUID string | None,
    "session_id": UUID string | None,
    "subject": str,
    "predicate": str,
    "object": str,
    "content": str,
    "confidence": float (default 1.0),
    "authority": float (default 1.0),
    "temporal_status": str (default "current"),
    "superseded_by_id": UUID string | None,
    "status": str (default "active")
}
```

### Decision (M2 output)
```python
{
    "id": UUID string,
    "workspace_id": UUID string,
    "project_id": UUID string | None,
    "source_id": UUID string | None,
    "session_id": UUID string | None,
    "content": str,
    "context": str | None,
    "confidence": float (default 1.0),
    "authority": float (default 1.0),
    "temporal_status": str (default "current"),
    "superseded_by_id": UUID string | None,
    "status": str (default "active")
}
```

### GraphNode (M4 output)
```python
{
    "id": UUID string,
    "workspace_id": UUID string,
    "project_id": UUID string | None,
    "external_id": str | None,
    "label": str,
    "node_type": str (default "entity"),
    "properties": dict | None,
    "temporal_status": str (default "current")
}
```

### GraphEdge (M4 output)
```python
{
    "id": UUID string,
    "workspace_id": UUID string,
    "project_id": UUID string | None,
    "source_node_id": UUID string,
    "target_node_id": UUID string,
    "relationship_type": str,
    "properties": dict | None,
    "confidence": float (default 1.0),
    "temporal_status": str (default "current"),
    "source_id": UUID string | None
}
```

### Provenance
```python
{
    "id": UUID string,
    "session_id": UUID string | None,
    "project_id": UUID string | None,
    "model_used": str,
    "provider": str,
    "retrieval_method": str (hybrid/keyword/semantic),
    "memory_ids_used": list[str],
    "retrieval_sources": list[dict],
    "user_message_id": UUID string | None,
    "prompt_tokens": int,
    "completion_tokens": int,
    "total_tokens": int,
    "latency_ms": float,
    "confidence_score": float
}
```

### ApiKey
```python
{
    "id": UUID string,
    "key_prefix": str (displayed, not raw key),
    "name": str,
    "last_used_at": datetime | None,
    "revoked": bool,
    "created_at": datetime (UTC)
}
```

---

## 8. Test Execution Commands

```bash
# Run tier 1 only (fast, pure unit tests)
python run_tests.py --tier-1

# Run tier 1 + 2 (includes recorded contracts)
python run_tests.py --tier-1 --tier-2

# Run all tiers including live API and model evals
python run_tests.py --all

# Run specific test file
pytest tests/unit/test_auth.py -v

# Run specific test
pytest tests/unit/test_auth.py::test_login_success -v

# Run with coverage
python run_tests.py --all --coverage

# Run in background (non-blocking)
nohup python run_tests.py --all > test_run.log 2>&1 &
```

---

## 9. Known Test Gaps (Areas Without Dedicated Test Files)

| Area | Gap |
|------|-----|
| Frontend | No frontend tests in backend repo (separate frontend/ directory) |
| Connectors | test_connectors.py exists but coverage may be limited |
| Frontend only | Chat UI, memory creation UI, ingestion upload UI, graph visualization |
| Policy Engine | test_policy_engine.py exists but rule coverage uncertain |
| Form submissions | NOT APPLICABLE (OpenClawBot concern, not webapp) |
| Provider config | test_services.py may cover but NOT ESTABLISHED IN AVAILABLE SOURCE |

---

## 10. Test Health Metrics

| Metric | Value |
|--------|-------|
| Total tests collected | ~959 |
| Currently passing | ~829 |
| Need attention (skip/xfail/fail) | ~130 |
| Target before Stage 0 | 0 (all fixed, skipped, or xfailed with reasons) |
| Tier 1 execution time target | < 30s |
| CI gate | Tier 1 only, all green |
