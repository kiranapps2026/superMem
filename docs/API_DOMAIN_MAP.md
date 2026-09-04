# SwarmVault WebApp — API Domain Map
**Release:** `0534efe426e42f9c03f1622dd792f052647038cc`

Groups the 78 API endpoints into logical domains for frontend consumption.

---

## Domain: AUTH (6 endpoints)

| Method | Path | Purpose | Auth | Frontend Use |
|---|---|---|---|---|
| POST | `/api/v1/auth/register` | Create account | None | Registration page |
| POST | `/api/v1/auth/login` | Obtain JWT | None | Login form |
| POST | `/api/v1/auth/refresh` | Refresh access token | None (uses refresh token) | Token refresh logic |
| POST | `/api/v1/auth/logout` | Revoke refresh token | JWT | Logout button |
| GET | `/api/v1/auth/me` | Current user profile | JWT | User menu, profile |
| POST | `/api/v1/auth/change-password` | Change password | JWT | Settings page |

**Dependencies:** None (creates tenant + workspace on register)
**Security boundary:** Rate-limited on login/register (10/min per IP)
**Lifecycle:** Register → login → refresh → use → logout

---

## Domain: WORKSPACE (14 endpoints)

| Method | Path | Purpose | Auth | RBAC | Frontend Use |
|---|---|---|---|---|---|
| GET | `/api/v1/workspace/` | Current workspace | JWT | — | Workspace header/settings |
| PATCH | `/api/v1/workspace/` | Update workspace | JWT | admin | Workspace settings |
| DELETE | `/api/v1/workspace/` | Delete workspace | JWT | owner | Danger zone settings |
| GET | `/api/v1/workspace/members` | List members | JWT | — | Members page |
| POST | `/api/v1/workspace/members` | Invite member | JWT | admin | Members page → invite |
| PATCH | `/api/v1/workspace/members/{id}` | Update member | JWT | admin | Members page → role change |
| DELETE | `/api/v1/workspace/members/{user_id}` | Remove member | JWT | admin | Members page → remove |
| POST | `/api/v1/workspace/member/leave` | Leave workspace | JWT | — | Settings → leave |
| GET | `/api/v1/workspace/members/invitations` | List invitations | JWT | member | Invitations page |
| GET | `/api/v1/workspace/members/invitations/{state}` | Filter invitations | JWT | member | Invitations page |
| PATCH | `/api/v1/workspace/members/invitation/{id}` | Accept/reject | JWT | admin | Invitation management |
| DELETE | `/api/v1/workspace/members/invitation/{id}` | Cancel invitation | JWT | admin | Invitation management |
| GET | `/api/v1/workspace/workspaces/all` | All user workspaces | JWT | — | Workspace switcher |
| GET | `/api/v1/workspace/workspaces/available` | Available to join | JWT | — | Workspace discovery |

**Dependencies:** Auth (JWT required)
**Security boundary:** Admin/owner gates on mutations
**Lifecycle:** Create (via register) → invite → join → manage → leave/delete

---

## Domain: PROJECTS (5 endpoints)

| Method | Path | Purpose | Auth | RBAC | Frontend Use |
|---|---|---|---|---|---|
| GET | `/api/v1/projects/` | List projects | JWT | — | Project list, sidebar |
| POST | `/api/v1/projects/` | Create project | JWT | member | New project dialog |
| GET | `/api/v1/projects/{id}` | Get project | JWT | — | Project detail |
| PATCH | `/api/v1/projects/{id}` | Update project | JWT | member | Project settings |
| DELETE | `/api/v1/projects/{id}` | Delete project | JWT | admin | Danger zone |

**Dependencies:** Workspace membership
**Security boundary:** Workspace-scoped
**Lifecycle:** Create → view → update → delete

---

## Domain: SESSIONS (6 endpoints)

| Method | Path | Purpose | Auth | RBAC | Frontend Use |
|---|---|---|---|---|---|
| GET | `/api/v1/sessions/` | List sessions | JWT | — | Session list |
| POST | `/api/v1/sessions/` | Create session | JWT | member | New session |
| GET | `/api/v1/sessions/{id}` | Get session | JWT | — | Session header |
| GET | `/api/v1/sessions/{id}/history` | Get messages | JWT | — | Chat history |
| POST | `/api/v1/sessions/{id}/messages` | Add message | JWT | member | Send message (legacy) |
| DELETE | `/api/v1/sessions/{id}` | Delete session | JWT | — | Session management |

**Dependencies:** Workspace membership
**Security boundary:** Workspace-scoped
**Lifecycle:** Create → chat → history → delete

---

## Domain: CHAT (2 endpoints)

| Method | Path | Purpose | Auth | RBAC | Frontend Use |
|---|---|---|---|---|---|
| POST | `/api/v1/chat/` | Send + receive (blocking) | JWT | viewer | Simple chat |
| POST | `/api/v1/chat/stream` | SSE streaming | JWT | **NONE** | Streaming chat (preferred) |

**Dependencies:** Workspace membership, optional project_id for memory retrieval
**Security boundary:** Workspace-scoped
**CONTRACT GAP:** `/chat/stream` has no RBAC while `/chat/` requires viewer role
**Lifecycle:** Send → receive sources → stream tokens → done

---

## Domain: MEMORY (6 endpoints)

| Method | Path | Purpose | Auth | RBAC | Frontend Use |
|---|---|---|---|---|---|
| POST | `/api/v1/memory/` | Create memory | JWT | policy: memory:write | Manual memory entry |
| GET | `/api/v1/memory/` | List memories | JWT | — | Memory list |
| GET | `/api/v1/memory/{id}` | Get memory | JWT | — | Memory detail/edit |
| PATCH | `/api/v1/memory/{id}` | Update memory | JWT | member | Memory edit |
| DELETE | `/api/v1/memory/{id}` | Delete memory | JWT | owner + policy: memory:delete | Memory delete |
| POST | `/api/v1/memory/search` | Full-text search | JWT | — | Search bar |

**Dependencies:** Workspace membership
**Security boundary:** Workspace + user-scoped (users see only their own memories)
**Lifecycle:** Create → read → update → search → delete

---

## Domain: INGESTION (14 endpoints)

| Method | Path | Purpose | Auth | RBAC | Frontend Use |
|---|---|---|---|---|---|
| POST | `/api/v1/ingest/upload` | Upload + ingest file | JWT | member | File upload |
| POST | `/api/v1/ingest/` | Queue ingestion job | JWT | — | Batch ingest |
| GET | `/api/v1/ingest/sources` | List sources | JWT | — | Source list |
| GET | `/api/v1/ingest/sources/{id}` | Get source | JWT | — | Source detail |
| GET | `/api/v1/ingest/sources/{id}/messages` | Get source messages | JWT | — | Source messages view |
| GET | `/api/v1/ingest/facts` | List facts | JWT | — | Facts page |
| GET | `/api/v1/ingest/facts/{id}` | Get fact | JWT | — | Fact detail |
| GET | `/api/v1/ingest/decisions` | List decisions | JWT | — | Decisions page |
| GET | `/api/v1/ingest/decisions/{id}` | Get decision | JWT | — | Decision detail |
| GET | `/api/v1/ingest/graph` | Knowledge graph | JWT | — | Graph visualization |
| GET | `/api/v1/ingest/timeline` | Timeline | JWT | — | Timeline view |
| POST | `/api/v1/ingest/search` | Full-text search | JWT | — | Universal search |
| GET | `/api/v1/ingest/jobs` | List jobs | JWT | — | Ingestion status |
| GET | `/api/v1/ingest/jobs/{id}` | Get job | JWT | — | Job detail |

**Dependencies:** Workspace + project membership
**Security boundary:** Workspace + project-scoped
**Lifecycle:** Upload → process → view facts/decisions/graph → search

---

## Domain: PROVENANCE (3 endpoints)

| Method | Path | Purpose | Auth | RBAC | Frontend Use |
|---|---|---|---|---|---|
| GET | `/api/v1/provenance/` | List provenance | JWT | member | Provenance list |
| GET | `/api/v1/provenance/{id}` | Get provenance | JWT | — | Provenance detail |
| GET | `/api/v1/provenance/{id}/memories` | Linked memories | JWT | — | Memory sources in chat |

**Dependencies:** Workspace membership
**Security boundary:** Workspace-scoped
**Lifecycle:** Created automatically per chat response → displayed in chat → drilled into

---

## Domain: DASHBOARD (2 endpoints)

| Method | Path | Purpose | Auth | RBAC | Frontend Use |
|---|---|---|---|---|---|
| GET | `/api/v1/dashboard/` | Workspace overview | JWT | — | Dashboard home |
| GET | `/api/v1/dashboard/projects/{id}` | Project overview | JWT | — | Project dashboard |

**Dependencies:** Workspace membership
**Security boundary:** Workspace-scoped
**Lifecycle:** Stateless statistics

---

## Domain: FEEDBACK (3 endpoints)

| Method | Path | Purpose | Auth | RBAC | Frontend Use |
|---|---|---|---|---|---|
| POST | `/api/v1/feedback/` | Submit feedback | JWT | member | Thumbs up/down on response |
| GET | `/api/v1/feedback/` | List feedback | JWT | — | Feedback history |
| GET | `/api/v1/feedback/{id}` | Get feedback | JWT | — | Feedback detail |

**Dependencies:** Workspace membership
**Security boundary:** Workspace-scoped

---

## Domain: API KEYS (4 endpoints)

| Method | Path | Purpose | Auth | RBAC | Frontend Use |
|---|---|---|---|---|---|
| POST | `/api/v1/api-keys/` | Create key | JWT | admin | API key management |
| GET | `/api/v1/api-keys/` | List keys | JWT | — | API key list |
| DELETE | `/api/v1/api-keys/{id}` | Revoke key | JWT | admin | Revoke key |
| POST | `/api/v1/api-keys/{id}/rotate` | Rotate key | JWT | admin | Rotate key |

**Dependencies:** Workspace membership
**Security boundary:** Admin-only mutations; raw key shown once only
**Lifecycle:** Create → list → rotate → revoke

---

## Domain: STORAGE (3 endpoints)

| Method | Path | Purpose | Auth | RBAC | Frontend Use |
|---|---|---|---|---|---|
| POST | `/api/v1/storage/upload` | Upload file | JWT | member | File upload |
| GET | `/api/v1/storage/{key:path}` | File info | JWT | — | File list/detail |
| DELETE | `/api/v1/storage/{key:path}` | Delete file | JWT | admin | File deletion |

**Dependencies:** Workspace membership
**Security boundary:** Key path must start with `<workspace_id>/`
**Lifecycle:** Upload → list → delete

---

## Domain: POLICY (7 endpoints)

| Method | Path | Purpose | Auth | RBAC | Frontend Use |
|---|---|---|---|---|---|
| GET | `/api/v1/policy/` | List policies | JWT | — | Policy list (admin UI) |
| POST | `/api/v1/policy/` | Create policy | JWT | admin | Policy creation |
| GET | `/api/v1/policy/{id}` | Get policy | JWT | — | Policy detail |
| PATCH | `/api/v1/policy/{id}` | Update policy | JWT | — | Policy editing |
| DELETE | `/api/v1/policy/{id}` | Delete policy | JWT | — | Policy deletion |
| POST | `/api/v1/policy/{id}/versions` | New version | JWT | — | Policy versioning |
| POST | `/api/v1/policy/test-authorization` | Test rule | JWT | — | Policy testing UI |

**Dependencies:** Workspace membership
**Security boundary:** Tenant-scoped (not workspace)
**Lifecycle:** Create → version → update → delete → test

---

## Domain: AUDIT (3 endpoints)

| Method | Path | Purpose | Auth | RBAC | Frontend Use |
|---|---|---|---|---|---|
| GET | `/api/v1/api/v1/audit/events` | List events | JWT | member | Audit log viewer |
| GET | `/api/v1/api/v1/audit/events/{id}` | Get event | JWT | member | Event detail |
| GET | `/api/v1/api/v1/audit/trace/{request_id}` | Correlation trace | JWT | member | Request tracing |

**CONTRACT GAP:** Paths are `/api/v1/api/v1/audit/...` (double prefix). Should be `/api/v1/audit/...`.
**Dependencies:** Workspace membership
**Security boundary:** Workspace-scoped

---

## Domain: HEALTH (3 endpoints)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/health/live` | None | Liveness probe |
| GET | `/health/ready` | None | Readiness probe (checks DB) |
| GET | `/health` | None | Legacy health |

**Note:** These are infrastructure endpoints. Do not expose in frontend UI directly.
