# PHASE_1R_API_ENDPOINT_INVENTORY.md

## Gate 5 — API Usage Audit

**Date:** 2026-09-04

---

## Backend API Endpoints (FastAPI)

### Auth (`/api/v1/auth`)
| Method | Path | Response Model | Frontend Used |
|--------|------|----------------|----------------|
| POST | `/register` | TokenResponse | E2E only |
| POST | `/login` | TokenResponse | E2E only |
| POST | `/refresh` | TokenResponse | Yes (api.ts) |
| POST | `/logout` | None | Yes (useAuth) |
| GET | `/me` | UserOut | Yes (useAuth) |
| POST | `/change-password` | — | Yes (Settings, Profile) |

### Workspace (`/api/v1/workspace`)
| Method | Path | Response Model | Frontend Used |
|--------|------|----------------|----------------|
| GET | `/` | WorkspaceOut | Yes (Dashboard, Settings) |
| PATCH | `/` | WorkspaceOut | Yes (Settings) |
| DELETE | `/` | — | No |
| GET | `/members` | list[WorkspaceMemberOut] | Yes (Settings, ProjectSettings) |
| POST | `/members` | WorkspaceMemberOut | Yes (Settings) |
| PATCH | `/members/{member_id}` | WorkspaceMemberOut | Yes (Settings) |
| DELETE | `/members/{user_id}` | — | Yes (Settings) |
| POST | `/member/leave` | — | No |
| GET | `/members/invitations` | list[InvitationOut] | Yes (Settings) |
| GET | `/members/invitations/{invitation_id}` | InvitationOut | No |
| PATCH | `/members/invitation/{invitation_id}` | InvitationOut | No |
| DELETE | `/members/invitation/{invitation_id}` | — | Yes (Settings) |
| GET | `/workspaces/all` | list[WorkspaceOut] | No |
| GET | `/workspaces/available` | list[WorkspaceOut] | No |

### Projects (`/api/v1/projects`)
| Method | Path | Response Model | Frontend Used |
|--------|------|----------------|----------------|
| GET | `/` | list[ProjectOut] | Yes (Projects, Dashboard) |
| POST | `/` | ProjectOut | Yes (Dashboard, useProjects) |
| GET | `/{project_id}` | ProjectOut | Yes (ProjectLayout, useProject) |
| PATCH | `/{project_id}` | ProjectOut | Yes (ProjectLayout, useUpdateProject) |
| DELETE | `/{project_id}` | — | Yes (ProjectLayout, useDeleteProject) |

### Sessions (`/api/v1/sessions`)
| Method | Path | Response Model | Frontend Used |
|--------|------|----------------|----------------|
| GET | `/` | list[SessionOut] | Yes (SessionsPage) |
| POST | `/` | SessionOut | No |
| GET | `/{session_id}` | SessionOut | No |
| GET | `/{session_id}/history` | SessionHistory | Yes (SessionDetailPage) |
| POST | `/{session_id}/messages` | MessageOut | No |
| DELETE | `/{session_id}` | — | No |

### Chat (`/api/v1/chat`)
| Method | Path | Response Model | Frontend Used |
|--------|------|----------------|----------------|
| POST | `/` | ChatResponse | No (mock only) |
| POST | `/stream` | SSE | Yes (ChatPage, useChat) |

### Memory (`/api/v1/memory`)
| Method | Path | Response Model | Frontend Used |
|--------|------|----------------|----------------|
| POST | `/` | MemoryOut | Yes (useCreateMemory) |
| GET | `/` | list[MemoryOut] | Yes (MemoryPage, useMemoryList) |
| GET | `/{memory_id}` | MemoryOut | No |
| PATCH | `/{memory_id}` | MemoryOut | No |
| DELETE | `/{memory_id}` | — | Yes (useDeleteMemory) |
| POST | `/search` | list[MemoryOut] | Yes (useMemorySearch) |

### Ingest (`/api/v1/ingest`)
| Method | Path | Response Model | Frontend Used |
|--------|------|----------------|----------------|
| POST | `/upload` | IngestUploadResponse | Yes (IngestPage, StoragePage) |
| POST | `/` | IngestJobOut | No |
| GET | `/sources` | SourceListResponse | Yes (IngestPage, useSources) |
| GET | `/sources/{source_id}` | SourceDetail | No |
| GET | `/sources/{source_id}/messages` | — | No |
| GET | `/facts` | FactListResponse | Yes (FactsPage, useFacts) |
| GET | `/facts/{fact_id}` | — | No |
| GET | `/decisions` | DecisionListResponse | Yes (DecisionsPage, useDecisions) |
| GET | `/decisions/{decision_id}` | — | No |
| GET | `/graph` | GraphResponse | Yes (GraphPage, useGraph) |
| GET | `/timeline` | TimelineResponse | Yes (TimelinePage) |
| POST | `/search` | SearchResponse | Yes (SearchPage) |
| GET | `/jobs` | list[IngestJobOut] | Yes (useIngestJobs) |
| GET | `/jobs/{job_id}` | IngestJobOut | No |

### Graph (`/api/v1/graph`)
| Method | Path | Response Model | Frontend Used |
|--------|------|----------------|----------------|
| GET | `/` | GraphResponse | Yes (useGraph) |

### Search (`/api/v1/search`)
| Method | Path | Response Model | Frontend Used |
|--------|------|----------------|----------------|
| GET | `/?q=&limit=&project_id=` | SearchResponse | Yes (useSearch) |

### Provenance (`/api/v1/provenance`)
| Method | Path | Response Model | Frontend Used |
|--------|------|----------------|----------------|
| GET | `/` | list[ProvenanceOut] | Yes (ProvenancePage) |
| GET | `/{provenance_id}` | ProvenanceOut | No |
| GET | `/{provenance_id}/memories` | list[MemoryReferenceOut] | No |

### Feedback (`/api/v1/feedback`)
| Method | Path | Response Model | Frontend Used |
|--------|------|----------------|----------------|
| POST | `/` | FeedbackOut | No |
| GET | `/` | FeedbackListResponse | No |
| GET | `/{feedback_id}` | FeedbackOut | No |

### API Keys (`/api/v1/api-keys`)
| Method | Path | Response Model | Frontend Used |
|--------|------|----------------|----------------|
| POST | `/` | ApiKeyCreateResponse | Yes (useCreateKey) |
| GET | `/` | list[ApiKeyOut] | Yes (ApiKeysPage, useApiKeys) |
| DELETE | `/{key_id}` | — | Yes (useRevokeKey) |
| POST | `/{key_id}/rotate` | ApiKeyRotateResponse | Yes (useRotateKey) |

### Storage (`/api/v1/storage`)
| Method | Path | Response Model | Frontend Used |
|--------|------|----------------|----------------|
| POST | `/upload` | UploadResponse | Yes (StoragePage, uploadFile) |
| GET | `/{key:path}` | dict | No |
| DELETE | `/{key:path}` | — | No |

### Dashboard (`/api/v1/dashboard`)
| Method | Path | Response Model | Frontend Used |
|--------|------|----------------|----------------|
| GET | `/` | DashboardOverview | No |
| GET | `/projects/{project_id}` | ProjectDashboard | No |

### Policy (`/api/v1/policy`)
| Method | Path | Response Model | Frontend Used |
|--------|------|----------------|----------------|
| GET | `/` | list[PolicyOut] | No |
| POST | `/` | PolicyOut | No |
| GET | `/{policy_id}` | PolicyDetail | No |
| PATCH | `/{policy_id}` | PolicyOut | No |
| DELETE | `/{policy_id}` | — | No |
| POST | `/{policy_id}/versions` | PolicyVersionOut | No |
| POST | `/test-authorization` | AuthorizationTestResponse | No |

### Audit (`/api/v1/audit`)
| Method | Path | Response Model | Frontend Used |
|--------|------|----------------|----------------|
| GET | `/events` | AuditEventList | No |
| GET | `/events/{event_id}` | AuditEvent | No |
| GET | `/trace/{request_id}` | — | No |

### Health
| Method | Path | Response Model | Frontend Used |
|--------|------|----------------|----------------|
| GET | `/health/live` | — | No |
| GET | `/health/ready` | — | No |
| GET | `/health` | — | No |

---

## Backend Endpoint Summary

| Category | Total Endpoints | Used by Frontend | Not Used |
|----------|-----------------|-------------------|-----------|
| Auth | 6 | 5 | 1 |
| Workspace | 14 | 10 | 4 |
| Projects | 5 | 5 | 0 |
| Sessions | 6 | 2 | 4 |
| Chat | 2 | 1 | 1 |
| Memory | 6 | 4 | 2 |
| Ingest | 15 | 10 | 5 |
| Graph | 1 | 1 | 0 |
| Search | 1 | 1 | 0 |
| Provenance | 3 | 1 | 2 |
| Feedback | 3 | 0 | 3 |
| API Keys | 4 | 4 | 0 |
| Storage | 3 | 1 | 2 |
| Dashboard | 2 | 0 | 2 |
| Policy | 7 | 0 | 7 |
| Audit | 3 | 0 | 3 |
| Health | 3 | 0 | 3 |
| **TOTAL** | **97** | **50** | **47** |

**Frontend utilization: 51.5% (50 of 97 endpoints)**

---

## Frontend API Usage Summary

### Direct API Client (`src/lib/api.ts`)
- `apiGet`, `apiPost`, `apiPatch`, `apiDelete` — wrapper around `fetch` with JWT auth
- `streamChat` — SSE via `fetch` + ReadableStream
- `uploadFile` — multipart via XMLHttpRequest (for progress events)

### Feature Hooks
| Hook | Endpoints Used |
|------|----------------|
| `useAuth` | /auth/me, /auth/login, /auth/register, /auth/logout, /auth/change-password |
| `useProjects` | GET /, POST /, GET /{id}, PATCH /{id}, DELETE /{id} |
| `useChat` | POST /chat/stream |
| `useMemory` | GET /, POST /search, POST /, DELETE /{id} |
| `useSources` | GET /ingest/sources |
| `useFacts` | GET /ingest/facts |
| `useDecisions` | GET /ingest/decisions |
| `useUploadFile` | POST /ingest/upload, POST /storage/upload |
| `useIngestJobs` | GET /ingest/jobs |
| `useGraph` | GET /graph |
| `useSearch` | GET /search/ |
| `useApiKeys` | GET /api-keys, POST /api-keys, DELETE /api-keys/{id}, POST /api-keys/{id}/rotate |

### Page-Specific API Calls
| Page | Endpoints Used |
|------|----------------|
| Dashboard | GET /workspace, GET /projects, POST /projects |
| Settings | GET/PATCH /workspace, GET/POST/PATCH/DELETE /workspace/members, GET/DELETE /workspace/members/invitations, POST /auth/change-password |
| Project Layout | GET /projects/{id}, PATCH /projects/{id}, DELETE /projects/{id} |
| Chat | POST /chat/stream |
| Ingest | GET /ingest/sources, POST /ingest/upload |
| Sessions | GET /sessions, GET /sessions/{id}/history |
| Memory | GET /memory/ |
| Facts | GET /ingest/facts |
| Decisions | GET /ingest/decisions |
| Timeline | GET /ingest/timeline |
| Search | GET /ingest/search |
| Graph | GET /ingest/graph |
| Provenance | GET /provenance/ |
| Profile | PATCH /auth/me, POST /auth/change-password |
| API Keys | GET/POST/DELETE /api-keys, POST /api-keys/{id}/rotate |
| Storage | POST /storage/upload |

---

## Type Safety Issues Found

### `as any` Usage (1 instance)
```
frontend\src\app\projects\[id]\sessions\page.tsx:44
{(metaFor(s) as any).source || 'chat'}
```

This is a minor type gap — `metaFor(s)` returns `extra_metadata` which is typed as `Record<string, unknown>`. The code assumes it has a `.source` property.

### No `<any>` Type Assertions
No usage of TypeScript's `<any>` cast syntax found.

### No `Record<string, any>` Found
No explicit `Record<string, any>` type annotations in the frontend codebase.

---

## SSE / Streaming Usage

| Endpoint | Protocol | Frontend Implementation |
|----------|----------|------------------------|
| POST /chat/stream | SSE (text/event-stream) | `fetch` + ReadableStream (ChatPage), not useSSE hook |
| GET /api/v1/memory/ | SSE (if streaming) | Not used — standard REST |
| GET /api/v1/search/ | SSE (if streaming) | Not used — standard REST |

**Note:** The `useSSE` hook in `src/hooks/useSSE.tsx` exists but is NOT used by the chat implementation. The chat page uses `fetch` + ReadableStream directly. This is a discrepancy — the hook exists but isn't utilized.

---

## API Contract Summary

- **Backend defines**: 97 endpoints
- **Frontend consumes**: 50 endpoints (51.5%)
- **Unused by frontend**: 47 endpoints
- **Type safety**: 1 `as any` cast, no loose any types
- **Streaming**: Only `/chat/stream` uses SSE, implemented via fetch+ReadableStream (not the useSSE hook)
