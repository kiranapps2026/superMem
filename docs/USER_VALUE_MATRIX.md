# USER_VALUE_MATRIX.md

## Phase 2C — User Value vs. Buildable Verification

**Date:** 2026-09-05
**Method:** Mapped each user-requested value to verified buildable backend+frontend unit

---

## Verified User Value Units

| # | User Value | Backend Unit | Frontend Unit | Verified? |
|---|-----------|-------------|---------------|-----------|
| 1 | Search project memory | POST /api/v1/ingest/search | SearchPage + useSearch | ⚠️ SearchPage uses GET (wrong method) |
| 2 | Chat with AI (streaming) | POST /api/v1/chat/stream (SSE) | ChatPage (direct fetch) + useChat (EventSource) | ❌ useChat hook broken — EventSource cannot POST |
| 3 | Memory CRUD | GET/POST/DELETE /api/v1/memory/* | MemoryPage + useMemory | ✅ |
| 4 | Facts viewer | GET /api/v1/ingest/facts | FactsPage | ⚠️ Wrong local type (statement vs content/subject/predicate/object) |
| 5 | Decisions viewer | GET /api/v1/ingest/decisions | DecisionsPage | ⚠️ Wrong local type (includes tags which don't exist) |
| 6 | Timeline view | GET /api/v1/ingest/timeline | TimelinePage | ✅ |
| 7 | Knowledge graph | GET /api/v1/ingest/graph | GraphPage + useGraph | ❌ useGraph calls /api/v1/graph (404) |
| 8 | Session history | GET /api/v1/sessions/* | SessionsPage | ✅ |
| 9 | Source ingestion | POST /api/v1/ingest/upload | IngestPage + useIngest | ✅ |
| 10 | Provenance tracing | GET /api/v1/provenance/* | ProvenancePage | ✅ |
| 11 | Project management | GET/POST/PATCH/DELETE /api/v1/projects/* | ProjectsPage + useProjects | ✅ |
| 12 | Dashboard overview | GET /api/v1/dashboard/ | DashboardPage | ✅ |
| 13 | API key management | GET/POST/DELETE /api/v1/api-keys/* | ApiKeysPage + useApiKeys | ⚠️ Field name mismatch (prefix vs key_prefix) |
| 14 | Workspace settings | PATCH/GET /api/v1/workspace/* | SettingsPage | ✅ |
| 15 | Auth (login/register/logout) | POST /api/v1/auth/* | Login/Register pages + useAuth | ⚠️ Logout sends empty body |
| 16 | Password change | POST /api/v1/auth/change-password | ProfilePage | ✅ |
| 17 | File storage | POST/GET/DELETE /api/v1/storage/* | StoragePage | ✅ |
| 18 | Policy management | GET/POST/PATCH/DELETE /api/v1/policy/* | (no UI page) | ⚠️ API exists, no frontend page |
| 19 | Audit trail | GET /api/v1/audit/* | (no UI page) | ⚠️ API exists, no frontend page |
| 20 | Member management | GET/POST/PATCH/DELETE /api/v1/workspace/members | (no UI page) | ⚠️ API exists, no frontend page |
| 21 | Invitation management | GET/PATCH/DELETE /api/v1/workspace/members/invitation/* | (no UI page) | ⚠️ API exists, no frontend page |
| 22 | Authorization testing | POST /api/v1/policy/test-authorization | (no UI page) | ⚠️ API exists, no frontend page |

## Broken Value Units (require fix)

| # | Value | Break Location | Fix Required |
|---|-------|---------------|-------------|
| 1 | Chat streaming via hooks | `useSSE.tsx` — EventSource (GET) vs POST endpoint | Replace EventSource with fetch+ReadableStream in useSSE |
| 2 | Graph via useGraph hook | `useGraph.ts` — calls `/api/v1/graph` instead of `/api/v1/ingest/graph` | Fix path to `/api/v1/ingest/graph` |
| 3 | Facts rendering | `facts/page.tsx` local `FactItem` with wrong fields | Use shared types or fix local interface |
| 4 | Decisions rendering | `decisions/page.tsx` local `DecisionItem` with `tags` | Use shared types or fix local interface |
| 5 | Logout | `useAuth.tsx` sends `{}` to logout endpoint | Send `{refresh_token}` in body |
| 6 | Search page | `search/page.tsx` uses GET | Change to POST with query params |
| 7 | Jobs list | `useIngest.ts` expects array, gets `{items, total}` | Fix type or destructure response |
| 8 | API key prefix display | `useApiKeys.ts` + `types/api.ts` field `prefix` vs `key_prefix` | Rename field in shared types |
| 9 | Chat context | `chat/page.tsx` sends only `{message}`, missing `project_id`/`session_id` | Add project_id and session_id to request body |
