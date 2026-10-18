# Architecture Runtime Reconciliation

## The Observed Contradiction

**Documentation claim**: "local-first / single-operator" knowledge vault
**Backend reality**: Full multi-tenant workspace with members, invitations, API keys, RBAC, policy engine, audit logs

**Root cause**: Multiple product iterations were never reconciled in documentation.

---

## Capability Classification

### Classification Key
- **A** — Core authoritative capability (backed by database + policies + enforced at runtime)
- **B** — WebApp implementation capability (exists in code, runtime-enforced, not yet exercised in tests)
- **C** — Presentation-only concept (UI-only, no runtime significance)
- **D** — Legacy/dead capability (code exists, not enforced, will be removed)
- **E** — Future/unverified capability (planned, not implemented)

---

### Core Identity Model

| Capability | Classification | Evidence |
|---|---|---|
| User + JWT authentication | **A** | `users` table, `create_access_token`, `verify_password` — full auth pipeline |
| User registration creates workspace | **A** | `/auth/register` creates user + workspace atomically |
| Email/password auth | **A** | `UserLogin` schema, `authenticate_user` dependency |
| JWT refresh tokens | **A** | `/auth/refresh` endpoint, 30-day expiry |
| Password change | **A** | `/auth/change-password` with current password validation |
| Email verification flag | **A** | `UserOut.is_active`, `email_verified` fields |

### Core Vault Ownership

| Capability | Classification | Evidence |
|---|---|---|
| Tenant → Workspace → Project hierarchy | **A** | `TenantContext` resolves `tenant_id` → `workspace_id` from JWT claims |
| Workspace as primary isolation boundary | **A** | ALL data queries filter by `workspace_id` from tenant context |
| Project scoping (optional) | **A** | `project_id` query param on ingest/search endpoints |
| Row-level security (RLS) | **B** | Enforced via `workspace_id` in queries, not PostgreSQL RLS policies |
| Cross-workspace data leakage prevention | **A** | `get_tenant_context` ensures user can only access their workspace |

### WebApp Authentication

| Capability | Classification | Evidence |
|---|---|---|
| Login form with email/password | **A** | `/auth/login` endpoint, frontend login page |
| Registration form | **A** | `/auth/register` creates user + workspace |
| Token storage in localStorage | **A** | `localStorage.getItem('sv_tokens')` in `lib/api.ts` |
| Auto token refresh on 401 | **A** | `request()` function in `lib/api.ts` |
| Logout | **A** | `/auth/logout` + `clearTokens()` |

### WebApp Workspace Model

| Capability | Classification | Evidence |
|---|---|---|
| Workspace display name | **A** | `WorkspaceDetail.name` in sidebar + dashboard |
| Workspace description | **A** | `PATCH /workspace/` with description field |
| Workspace switching | **B** | `/workspaces/all` endpoint exists; no UI for switching yet |
| Multi-workspace support | **A** | User can belong to multiple workspaces |
| Single active workspace | **A** | `TenantContext` resolves one workspace per request |

### Members

| Capability | Classification | Evidence |
|---|---|---|
| Member listing | **A** | `GET /workspace/members` → `WorkspaceMemberOut[]` |
| Member invitation by email | **A** | `POST /workspace/members` with email + role |
| Role assignment (owner/admin/member/viewer) | **A** | `WorkspaceMemberInvite.role`, `WorkspaceMemberUpdate.role` |
| Role hierarchy enforcement | **A** | `require_min_role()` dependency, `PolicyEngine.check_role_minimum()` |
| Member removal | **A** | `DELETE /workspace/members/{user_id}` with self-remove/owner protection |
| Role changes | **A** | `PATCH /workspace/members/{member_id}` |
| Leave workspace | **A** | `POST /workspace/member/leave` |
| Invitation state management | **A** | `InvitationUpdate.state` (pending/accepted/declined/expired/revoked) |
| Invitation expiry | **A** | `invitation_expires` field on invite |

### Invitations

| Capability | Classification | Evidence |
|---|---|---|
| Email invitation flow | **A** | InvitationOut schema, member invitation endpoint |
| Invitation states | **A** | `pending`, `accepted`, `declined`, `expired`, `revoked` |
| Invitation listing | **A** | `GET /workspace/members/invitations` |
| Invitation by state filter | **A** | `GET /workspace/members/invitations/{state}` |

### API Keys

| Capability | Classification | Evidence |
|---|---|---|
| API key creation | **A** | `POST /api-keys/` with name, expires_at, metadata |
| API key listing | **A** | `GET /api-keys/` returns `ApiKeyOut[]` |
| API key rotation | **A** | `POST /api-keys/{id}/rotate` returns new raw_key |
| API key deletion | **A** | `DELETE /api-keys/{id}` |
| Raw key returned once | **A** | `ApiKeyCreateResponse.raw_key` — only returned at creation |
| Admin-only key management | **A** | `require_min_role("admin")` on all key endpoints |

### Authorization Checks

| Capability | Classification | Evidence |
|---|---|---|
| JWT-based auth | **A** | `get_tenant_context` dependency |
| Role-based access (owner>admin>member>viewer) | **A** | `require_min_role()` — numeric hierarchy 1000>500>100>50 |
| Policy engine | **A** | `PolicyEngine`, `require_policy("resource", "action")` |
| Fine-grained resource policies | **A** | `/policy/` CRUD + `/policy/test-authorization` |
| Audit logging | **A** | `/audit/events`, `/audit/trace/{request_id}` |

### Database Schema

| Capability | Classification | Evidence |
|---|---|---|
| Multi-tenant schema (tenant, workspace, project) | **A** | SQLAlchemy models: `Tenant`, `Workspace`, `WorkspaceMember`, `Project` |
| Memory storage (procedural only) | **A** | `Memory` model, `MemoryOut` schema |
| Session/message storage | **A** | `Session`, `Message` models |
| Source storage | **A** | `Source` model with `extra_metadata` JSON |
| Knowledge graph (nodes, edges) | **A** | `GraphNode`, `GraphEdge` models |
| Provenance tracking | **A** | `Provenance` model |
| Feedback | **A** | `Feedback` model |
| API keys | **A** | `ApiKey` model with prefix hashing |
| Audit events | **A** | `AuditEvent` model |
| Policies + versions | **A** | `Policy`, `PolicyVersion`, `PolicyRule` models |

### Frontend Account/Workspace Usage

| Capability | Classification | Evidence |
|---|---|---|
| Login/register forms | **A** | `/auth/login`, `/auth/register` pages |
| Workspace display in sidebar | **A** | `WorkspaceDetail` fetched on dashboard load |
| Member management UI | **A** | Settings page with member list + invite form |
| API key management UI | **A** | Settings → API Keys tab |
| Workspace switching | **E** | Backend endpoint exists; no UI implemented |
| Multi-workspace selector | **E** | Backend supports it; frontend assumes single workspace |

---

## Reconciliation Summary

### What the documentation says vs. what exists

| Document Claim | Actual State | Classification |
|---|---|---|
| "Local-first / single-operator" | Multi-tenant workspace with members | **D** (documentation is stale) |
| "Sprint 1 — fastapi + sqlalchemy" | Production-grade multi-tenant SaaS | **D** (docs are outdated) |
| "Workspace as primary isolation" | Confirmed — enforced at all layers | **A** |
| "RBAC with roles" | Confirmed — numeric hierarchy with policy engine | **A** |
| "Members and invitations" | Confirmed — full invite/accept/decline flow | **A** |
| "API keys for programmatic access" | Confirmed — creation, rotation, deletion | **A** |

### What to do

1. **Do NOT remove** workspace/member/RBAC features — they are **A** (authoritative)
2. **Do NOT redesign** navigation around workspace unless user requests it
3. **Update documentation** to reflect the actual multi-tenant architecture
4. **Frontend is under-leveraging** the workspace model — currently shows only single workspace

### Why the contradiction exists

The README describes Sprint 1 (initial scaffold). The code evolved through:
- Sprint 1: Basic FastAPI scaffold
- Phase 1R-A: Multi-tenant auth + workspace
- Phase 1R-B: Full RBAC, policies, audit, API keys, features

Documentation was never updated between sprints. This is a documentation debt issue, not an architecture issue.
