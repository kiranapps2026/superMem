# SwarmVault WebApp — Frontend API Coverage Matrix
**Release:** `0534efe426e42f9c03f1622dd792f052647038cc`
**Purpose:** Maps every frontend UI capability to backend API endpoints.

Legend:
- `YES` — endpoint exists, schema is clear, frontend can implement
- `GAP` — endpoint exists but contract is incomplete
- `MISS` — no endpoint exists
- `N/A` — not a frontend concern

---

| # | UI Capability | Endpoint | Method | Request | Response | Auth | RBAC | SSE | Pagination | Frontend-Ready | Gap | Severity |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Registration | `/api/v1/auth/register` | POST | UserRegister | TokenResponse | No | No | No | No | YES | — | — |
| 2 | Login | `/api/v1/auth/login` | POST | UserLogin | TokenResponse | No | No | No | No | YES | — | — |
| 3 | Token refresh | `/api/v1/auth/refresh` | POST | RefreshRequest | TokenResponse | No | No | No | No | YES | — | — |
| 4 | Logout | `/api/v1/auth/logout` | POST | RefreshRequest | {"detail"} | JWT | No | No | No | YES | — | — |
| 5 | Current user | `/api/v1/auth/me` | GET | — | UserOut | JWT | No | No | No | YES | — | — |
| 6 | Change password | `/api/v1/auth/change-password` | POST | ChangePasswordRequest | {"detail"} | JWT | No | No | No | YES | — | — |
| 7 | Get workspace | `/api/v1/workspace/` | GET | — | WorkspaceOut | JWT | No | No | No | YES | — | — |
| 8 | Update workspace | `/api/v1/workspace/` | PATCH | dict | WorkspaceOut | JWT | admin | No | No | YES | — | — |
| 9 | Delete workspace | `/api/v1/workspace/` | DELETE | — | 204 | JWT | owner | No | No | YES | — | — |
| 10 | List members | `/api/v1/workspace/members` | GET | — | WorkspaceMemberOut[] | JWT | No | No | No | YES | — | — |
| 11 | Invite member | `/api/v1/workspace/members` | POST | WorkspaceMemberInvite | WorkspaceMemberOut | JWT | admin | No | No | YES | — | — |
| 12 | Update member role | `/api/v1/workspace/members/{id}` | PATCH | WorkspaceMemberUpdate | WorkspaceMemberOut | JWT | admin | No | No | YES | — | — |
| 13 | Remove member | `/api/v1/workspace/members/{user_id}` | DELETE | — | 204 | JWT | admin | No | No | YES | — | — |
| 14 | Leave workspace | `/api/v1/workspace/member/leave` | POST | — | — | JWT | No | No | No | YES | — | — |
| 15 | List invitations | `/api/v1/workspace/members/invitations` | GET | — | InvitationOut[] | JWT | member | No | No | YES | — | — |
| 16 | Filter invitations | `/api/v1/workspace/members/invitations/{state}` | GET | — | InvitationOut[] | JWT | member | No | No | YES | — | — |
| 17 | Update invitation | `/api/v1/workspace/members/invitation/{id}` | PATCH | InvitationUpdate | InvitationOut | JWT | admin | No | No | YES | — | — |
| 18 | Cancel invitation | `/api/v1/workspace/members/invitation/{id}` | DELETE | — | 204 | JWT | admin | No | No | YES | — | — |
| 19 | All workspaces | `/api/v1/workspace/workspaces/all` | GET | — | dict[] | JWT | No | No | No | YES | Response schema is generic dict | P3 |
| 20 | Available workspaces | `/api/v1/workspace/workspaces/available` | GET | — | dict[] | JWT | No | No | No | YES | Response schema is generic dict | P3 |
| 21 | List projects | `/api/v1/projects/` | GET | — | ProjectOut[] | JWT | No | No | No | YES | — | — |
| 22 | Create project | `/api/v1/projects/` | POST | ProjectCreate | ProjectOut | JWT | member | No | No | YES | — | — |
| 23 | Get project | `/api/v1/projects/{id}` | GET | — | ProjectOut | JWT | No | No | No | YES | — | — |
| 24 | Update project | `/api/v1/projects/{id}` | PATCH | ProjectUpdate | ProjectOut | JWT | member | No | No | YES | — | — |
| 25 | Delete project | `/api/v1/projects/{id}` | DELETE | — | 204 | JWT | admin | No | No | YES | — | — |
| 26 | List sessions | `/api/v1/sessions/` | GET | — | SessionOut[] | JWT | No | No | No | YES | — | — |
| 27 | Create session | `/api/v1/sessions/` | POST | SessionCreate | SessionOut | JWT | member | No | No | YES | — | — |
| 28 | Get session | `/api/v1/sessions/{id}` | GET | — | SessionOut | JWT | No | No | No | YES | — | — |
| 29 | Session history | `/api/v1/sessions/{id}/history` | GET | — | {session, messages[]} | JWT | No | No | No | YES | — | — |
| 30 | Add message (legacy) | `/api/v1/sessions/{id}/messages` | POST | MessageCreate | MessageOut | JWT | member | No | No | YES | — | — |
| 31 | Delete session | `/api/v1/sessions/{id}` | DELETE | — | 204 | JWT | No | No | No | YES | — | — |
| 32 | Send chat (blocking) | `/api/v1/chat/` | POST | ChatRequest | ChatResponse | JWT | viewer | No | No | YES | — | — |
| 33 | Send chat (SSE) | `/api/v1/chat/stream` | POST | ChatRequest | text/event-stream | JWT | **NONE** | YES | No | YES | No RBAC — P1 gap | P1 |
| 34 | Create memory | `/api/v1/memory/` | POST | MemoryCreate | MemoryOut | JWT | policy | No | No | YES | — | — |
| 35 | List memories | `/api/v1/memory/` | GET | — | MemoryOut[] | JWT | No | No | limit/offset | YES | — | — |
| 36 | Get memory | `/api/v1/memory/{id}` | GET | — | MemoryOut | JWT | No | No | No | YES | — | — |
| 37 | Update memory | `/api/v1/memory/{id}` | PATCH | MemoryUpdate | MemoryOut | JWT | member | No | No | YES | — | — |
| 38 | Delete memory | `/api/v1/memory/{id}` | DELETE | — | 204 | JWT | owner+policy | No | No | YES | — | — |
| 39 | Search memories | `/api/v1/memory/search` | POST | MemorySearchRequest | MemoryOut[] | JWT | No | No | limit | YES | — | — |
| 40 | Upload + ingest | `/api/v1/ingest/upload` | POST | multipart | IngestUploadResponse | JWT | member | No | No | YES | — | — |
| 41 | Queue ingestion | `/api/v1/ingest/` | POST | IngestQueued | IngestJobOut | JWT | No | No | No | YES | — | — |
| 42 | List sources | `/api/v1/ingest/sources` | GET | — | SourceListResponse | JWT | No | No | limit/offset+total | YES | — | — |
| 43 | Get source | `/api/v1/ingest/sources/{id}` | GET | — | SourceDetail | JWT | No | No | No | YES | — | — |
| 44 | Source messages | `/api/v1/ingest/sources/{id}/messages` | GET | — | {items[], total} | JWT | No | No | No | YES | — | — |
| 45 | List facts | `/api/v1/ingest/facts` | GET | — | FactListResponse | JWT | No | No | limit/offset+total | YES | — | — |
| 46 | Get fact | `/api/v1/ingest/facts/{id}` | GET | — | FactOut | JWT | No | No | No | YES | — | — |
| 47 | List decisions | `/api/v1/ingest/decisions` | GET | — | DecisionListResponse | JWT | No | No | limit/offset+total | YES | — | — |
| 48 | Get decision | `/api/v1/ingest/decisions/{id}` | GET | — | DecisionOut | JWT | No | No | No | YES | — | — |
| 49 | Knowledge graph | `/api/v1/ingest/graph` | GET | — | GraphResponse | JWT | No | No | No | YES | — | — |
| 50 | Timeline | `/api/v1/ingest/timeline` | GET | — | TimelineResponse | JWT | No | No | limit+total | YES | — | — |
| 51 | Full-text search | `/api/v1/ingest/search` | POST | query,limit | SearchResponse | JWT | No | No | total | YES | — | — |
| 52 | List jobs | `/api/v1/ingest/jobs` | GET | — | {items[], total} | JWT | No | No | limit/offset | YES | — | — |
| 53 | Get job | `/api/v1/ingest/jobs/{id}` | GET | — | IngestJobOut | JWT | No | No | No | YES | — | — |
| 54 | List provenance | `/api/v1/provenance/` | GET | — | ProvenanceOut[] | JWT | member | No | limit/offset | YES | — | — |
| 55 | Get provenance | `/api/v1/provenance/{id}` | GET | — | ProvenanceOut | JWT | No | No | No | YES | — | — |
| 56 | Provenance memories | `/api/v1/provenance/{id}/memories` | GET | — | MemoryReferenceOut[] | JWT | No | No | No | YES | — | — |
| 57 | Workspace dashboard | `/api/v1/dashboard/` | GET | — | DashboardOverview | JWT | No | No | No | YES | — | — |
| 58 | Project dashboard | `/api/v1/dashboard/projects/{id}` | GET | — | ProjectDashboard | JWT | No | No | No | YES | — | — |
| 59 | Submit feedback | `/api/v1/feedback/` | POST | FeedbackCreate | FeedbackOut | JWT | member | No | No | YES | — | — |
| 60 | List feedback | `/api/v1/feedback/` | GET | — | FeedbackListResponse | JWT | No | No | limit/offset+total | YES | — | — |
| 61 | Get feedback | `/api/v1/feedback/{id}` | GET | — | FeedbackOut | JWT | No | No | No | YES | — | — |
| 62 | Create API key | `/api/v1/api-keys/` | POST | ApiKeyCreate | ApiKeyCreateResponse | JWT | admin | No | No | YES | raw_key shown once | P2 |
| 63 | List API keys | `/api/v1/api-keys/` | GET | — | ApiKeyOut[] | JWT | No | No | No | YES | — | — |
| 64 | Revoke API key | `/api/v1/api-keys/{key_id}` | DELETE | — | 204 | JWT | admin | No | No | YES | — | — |
| 65 | Rotate API key | `/api/v1/api-keys/{key_id}/rotate` | POST | — | ApiKeyRotateResponse | JWT | admin | No | No | YES | raw_key shown once | P2 |
| 66 | Upload file | `/api/v1/storage/upload` | POST | multipart | UploadResponse | JWT | member | No | No | YES | — | — |
| 67 | File info | `/api/v1/storage/{key:path}` | GET | — | {key, url} | JWT | No | No | No | YES | No list endpoint | P2 |
| 68 | Delete file | `/api/v1/storage/{key:path}` | DELETE | — | 204 | JWT | admin | No | No | YES | — | — |
| 69 | List policies | `/api/v1/policy/` | GET | — | PolicyOut[] | JWT | No | No | limit | YES | — | — |
| 70 | Create policy | `/api/v1/policy/` | POST | PolicyCreate | PolicyOut | JWT | admin | No | No | YES | — | — |
| 71 | Get policy | `/api/v1/policy/{id}` | GET | — | PolicyDetail | JWT | No | No | No | YES | — | — |
| 72 | Update policy | `/api/v1/policy/{id}` | PATCH | PolicyUpdate | PolicyOut | JWT | No | No | No | YES | — | — |
| 73 | Delete policy | `/api/v1/policy/{id}` | DELETE | — | 204 | JWT | No | No | No | YES | — | — |
| 74 | Create version | `/api/v1/policy/{id}/versions` | POST | — | PolicyVersionOut | JWT | No | No | No | YES | — | — |
| 75 | Test authorization | `/api/v1/policy/test-authorization` | POST | AuthTestRequest | AuthTestResponse | JWT | No | No | No | YES | — | — |
| 76 | Audit events | `/api/v1/api/v1/audit/events` | GET | — | {items[], total, limit, offset} | JWT | member | No | limit/offset+total | YES | Double-prefix path | P2 |
| 77 | Audit event detail | `/api/v1/api/v1/audit/events/{id}` | GET | — | dict | JWT | member | No | No | YES | Double-prefix path | P2 |
| 78 | Correlation trace | `/api/v1/api/v1/audit/trace/{request_id}` | GET | — | dict | JWT | member | No | No | YES | Double-prefix path | P2 |

---

## Coverage Summary

| Category | Count | Frontend-Ready | With Gaps |
|---|---|---|---|
| Authentication | 6 | 6 | 0 |
| Workspace | 14 | 14 | 0 |
| Projects | 5 | 5 | 0 |
| Sessions | 6 | 6 | 0 |
| Chat (blocking) | 1 | 1 | 0 |
| Chat (SSE) | 1 | 1 | 1 (RBAC gap) |
| Memory | 6 | 6 | 0 |
| Ingestion | 14 | 14 | 0 |
| Provenance | 3 | 3 | 0 |
| Dashboard | 2 | 2 | 0 |
| Feedback | 3 | 3 | 0 |
| API Keys | 4 | 4 | 0 |
| Storage | 3 | 3 | 1 (no list endpoint) |
| Policy | 7 | 7 | 0 |
| Audit | 3 | 3 | 3 (double-prefix) |
| Health | 3 | 0 | 3 (infra only) |
| **Total** | **81** | **78** | **9 gaps** |
