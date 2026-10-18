# PAGE CAPABILITY MATRIX

For each page: User Goal, User Actions, Core Capability, WebApp Endpoint, Endpoint Verified, Response Verified, Real Data, Empty State, Error State, Partial State, Mutation, Mutation Verified, Browser Verified, Decision.

> "Endpoint Verified" = confirmed in backend code (not just documentation).
> "Response Verified" = TypeScript interface matches actual response fields.
> "Browser Verified" = Playwright test exercises the page.

---

## Auth Pages (Login, Register)

| Property | Value |
|---|---|
| Page | `/auth/login`, `/auth/register` |
| User Goal | Authenticate to access workspace |
| User Action | Enter email/password, click submit |
| Core Capability | JWT authentication with workspace creation on register |
| WebApp Endpoint | POST /auth/login, POST /auth/register |
| Endpoint Verified | YES (14 golden-journey tests pass) |
| Response Verified | YES |
| Real Data | YES (golden-journey test creates + logs in) |
| Empty State | N/A |
| Error State | YES (invalid credentials → 401, wrong password test) |
| Partial State | N/A |
| Mutation | YES (register creates user + workspace) |
| Mutation Verified | YES |
| Browser Verified | YES (14 tests in golden-journey) |
| Decision | **KEEP** |

---

## Dashboard

| Property | Value |
|---|---|
| Page | `/dashboard` |
| User Goal | Overview of workspace activity |
| User Action | View stats, switch tabs, create projects |
| Core Capability | DashboardSummary aggregation |
| WebApp Endpoint | GET /dashboard/, GET /projects/, POST /projects/ |
| Endpoint Verified | YES |
| Response Verified | YES (all 11 fields typed in api.ts) |
| Real Data | YES (golden-journey: upload → dashboard reflects data) |
| Empty State | YES (no projects → empty state with prompt) |
| Error State | YES (ErrorAlert + loading fallback) |
| Partial State | YES (stats load independently from projects) |
| Mutation | YES (create project) |
| Mutation Verified | PARTIAL (manual API, no dedicated test) |
| Browser Verified | YES (unauthenticated redirect test) |
| Decision | **KEEP** — recent redesign needs browser certification with auth |

---

## Projects List

| Property | Value |
|---|---|
| Page | `/projects` |
| User Goal | Browse and manage projects |
| User Action | View projects, create new project, navigate to project |
| Core Capability | Project CRUD, workspace-scoped listing |
| WebApp Endpoint | GET /projects/, POST /projects/ |
| Endpoint Verified | YES |
| Response Verified | YES |
| Real Data | YES |
| Empty State | YES |
| Error State | YES (ErrorAlert) |
| Partial State | N/A |
| Mutation | YES (create project) |
| Mutation Verified | PARTIAL |
| Browser Verified | YES (unauthenticated redirect) |
| Decision | **KEEP** — redesign done, needs auth browser cert |

---

## Project Layout (sub-pages)

| Property | Value |
|---|---|
| Page | `/projects/{id}/` (layout wrapper) |
| User Goal | Navigate between project sub-pages |
| User Action | Click nav links, view project name in sidebar |
| Core Capability | Project-scoped navigation |
| WebApp Endpoint | GET /projects/{id} (via API) |
| Endpoint Verified | YES |
| Response Verified | YES |
| Real Data | YES |
| Empty State | N/A |
| Error State | N/A |
| Partial State | N/A |
| Mutation | N/A |
| Mutation Verified | N/A |
| Browser Verified | YES (layout renders in golden-journey) |
| Decision | **KEEP** |

---

## Settings

| Property | Value |
|---|---|
| Page | `/settings` (workspace + profile tabs) |
| User Goal | Manage workspace, members, API keys, profile |
| User Action | Edit workspace, invite members, manage keys, change password |
| Core Capability | Workspace PATCH, member CRUD, API key CRUD, password change |
| WebApp Endpoint | PATCH /workspace/, GET/POST/PATCH/DELETE /workspace/members/*, POST/GET/DELETE /api-keys/*, POST /auth/change-password |
| Endpoint Verified | YES (all backend endpoints confirmed) |
| Response Verified | YES |
| Real Data | YES |
| Empty State | YES (no members, no API keys) |
| Error State | YES (ErrorAlert) |
| Partial State | N/A |
| Mutation | YES (multiple) |
| Mutation Verified | PARTIAL |
| Browser Verified | YES (redirect test) |
| Decision | **KEEP** — redesign done, needs auth browser cert |

---

## Chat

| Property | Value |
|---|---|
| Page | `/projects/{id}/chat` |
| User Goal | Have AI-assisted conversation with memory retrieval |
| User Action | Type message, send, receive streaming response |
| Core Capability | SSE chat streaming with M5 retrieval |
| WebApp Endpoint | POST /chat/stream, POST /chat/, POST /sessions/, GET /sessions/ |
| Endpoint Verified | YES (golden-journey: chat → response → provenance) |
| Response Verified | YES (ChatResponse typed) |
| Real Data | YES (golden-journey exercises full chat flow) |
| Empty State | PARTIAL (no "start a conversation" state) |
| Error State | PARTIAL (stream error handling exists) |
| Partial State | YES (loading states present) |
| Mutation | YES (creates messages + sessions) |
| Mutation Verified | YES |
| Browser Verified | PARTIAL (API tested, not UI flow) |
| Decision | **MODIFY** — needs UI browser cert, canonical chat consolidation |

---

## Memory

| Property | Value |
|---|---|
| Page | `/projects/{id}/memory` |
| User Goal | Browse all memories in project |
| User Action | View memories, search within memories |
| Core Capability | Memory listing + semantic search |
| WebApp Endpoint | GET /memory/, POST /memory/search |
| Endpoint Verified | YES |
| Response Verified | YES |
| Real Data | YES (after ingest) |
| Empty State | YES (EmptyState component) |
| Error State | YES (ErrorAlert) |
| Partial State | YES |
| Mutation | N/A (read-only) |
| Mutation Verified | N/A |
| Browser Verified | NO (no dedicated test) |
| Decision | **MODIFY** — redesign + browser cert needed |

---

## Search

| Property | Value |
|---|---|
| Page | `/projects/{id}/search` |
| User Goal | Find memories, facts, and decisions |
| User Action | Enter query, filter by type, view results |
| Core Capability | M5 hybrid retrieval (semantic + BM25 + entity + temporal) |
| WebApp Endpoint | POST /ingest/search |
| Endpoint Verified | YES |
| Response Verified | YES (SearchResponse typed) |
| Real Data | YES (golden-journey: search returns results) |
| Empty State | YES |
| Error State | YES |
| Partial State | YES |
| Mutation | N/A |
| Mutation Verified | N/A |
| Browser Verified | NO (no dedicated test) |
| Decision | **MODIFY** — redesign done, needs auth browser cert + API-EXPAND (memory_type filter not in frontend) |

---

## Facts

| Property | Value |
|---|---|
| Page | `/projects/{id}/facts` |
| User Goal | Browse extracted facts |
| User Action | View facts with temporal/authority status |
| Core Capability | Fact listing with filtering |
| WebApp Endpoint | GET /ingest/facts |
| Endpoint Verified | YES |
| Response Verified | YES (FactItem typed) |
| Real Data | YES (after ingest) |
| Empty State | YES |
| Error State | YES |
| Partial State | YES |
| Mutation | N/A |
| Mutation Verified | N/A |
| Browser Verified | NO |
| Decision | **KEEP** — new implementation, needs browser cert |

---

## Decisions

| Property | Value |
|---|---|
| Page | `/projects/{id}/decisions` |
| User Goal | Browse extracted decisions |
| User Action | View decisions with confidence and status |
| Core Capability | Decision listing with temporal/authority metadata |
| WebApp Endpoint | GET /ingest/decisions |
| Endpoint Verified | YES |
| Response Verified | YES (DecisionItem typed) |
| Real Data | YES |
| Empty State | YES |
| Error State | YES |
| Partial State | YES |
| Mutation | N/A |
| Mutation Verified | N/A |
| Browser Verified | NO |
| Decision | **KEEP** — new implementation, needs browser cert |

---

## Timeline

| Property | Value |
|---|---|
| Page | `/projects/{id}/timeline` |
| User Goal | View chronological knowledge events |
| User Action | Scroll through timeline, view event details |
| Core Capability | Time-ordered listing of memories, facts, decisions |
| WebApp Endpoint | GET /ingest/timeline |
| Endpoint Verified | YES |
| Response Verified | YES (TimelineItem typed) |
| Real Data | YES |
| Empty State | YES |
| Error State | YES |
| Partial State | YES |
| Mutation | N/A |
| Mutation Verified | N/A |
| Browser Verified | NO |
| Decision | **KEEP** — new implementation, needs browser cert |

---

## Graph (Knowledge Graph)

| Property | Value |
|---|---|
| Page | `/projects/{id}/graph` |
| User Goal | Visualize knowledge graph |
| User Action | Browse nodes, click to see relationships |
| Core Capability | Graph node/edge listing with adjacency |
| WebApp Endpoint | GET /ingest/graph |
| Endpoint Verified | YES |
| Response Verified | YES (GraphResponse, GraphNode, GraphEdge typed) |
| Real Data | YES (after ingest) |
| Empty State | YES |
| Error State | YES |
| Partial State | YES |
| Mutation | N/A |
| Mutation Verified | N/A |
| Browser Verified | NO |
| Decision | **KEEP** — redesign done, needs browser cert |

---

## Provenance

| Property | Value |
|---|---|
| Page | `/projects/{id}/provenance` |
| User Goal | Trace memory lineage |
| User Action | View provenance chains, linked memories |
| Core Capability | Provenance tracking + memory references |
| WebApp Endpoint | GET /provenance/, GET /provenance/{id}, GET /provenance/{id}/memories |
| Endpoint Verified | YES |
| Response Verified | PARTIAL (ProvidenceOut not fully typed) |
| Real Data | YES |
| Empty State | YES |
| Error State | YES |
| Partial State | YES |
| Mutation | N/A |
| Mutation Verified | N/A |
| Browser Verified | NO |
| Decision | **DEFER** — redesign deferred, types incomplete |

---

## Sessions

| Property | Value |
|---|---|
| Page | `/projects/{id}/sessions` |
| User Goal | Browse conversation sessions |
| User Action | View session list, navigate to session detail |
| Core Capability | Session listing |
| WebApp Endpoint | GET /sessions/ |
| Endpoint Verified | YES |
| Response Verified | PARTIAL (no source/message_count in SessionOut — frontend infers from extra_metadata) |
| Real Data | YES |
| Empty State | YES |
| Error State | YES |
| Partial State | YES |
| Mutation | N/A |
| Mutation Verified | N/A |
| Browser Verified | NO |
| Decision | **API-EXPAND** — backend SessionOut needs source + message_count fields; or frontend needs to use extra_metadata correctly |

---

## Session Detail

| Property | Value |
|---|---|
| Page | `/projects/{id}/sessions/{sessionId}` |
| User Goal | Read full conversation |
| User Action | View messages, navigate back |
| Core Capability | Session message history |
| WebApp Endpoint | GET /sessions/{id}/history |
| Endpoint Verified | YES |
| Response Verified | PARTIAL (ad-hoc dict response, no formal schema) |
| Real Data | YES |
| Empty State | N/A |
| Error State | YES |
| Partial State | N/A |
| Mutation | N/A |
| Mutation Verified | N/A |
| Browser Verified | NO |
| Decision | **API-EXPAND** — needs formal response schema on backend |

---

## Ingest

| Property | Value |
|---|---|
| Page | `/projects/{id}/ingest` |
| User Goal | Import conversations |
| User Action | Paste content, select source type, upload |
| Core Capability | Content upload with M0-M5 processing pipeline |
| WebApp Endpoint | POST /ingest/upload, GET /ingest/sources |
| Endpoint Verified | YES (golden-journey: upload → processing) |
| Response Verified | YES |
| Real Data | YES |
| Empty State | YES |
| Error State | YES |
| Partial State | YES (source list loads independently) |
| Mutation | YES (upload triggers processing pipeline) |
| Mutation Verified | YES |
| Browser Verified | NO (UI flow not tested) |
| Decision | **KEEP** — needs browser cert with UI |

---

## API Keys

| Property | Value |
|---|---|
| Page | `/settings/api-keys` |
| User Goal | Manage programmatic access |
| User Action | Create, view, rotate, delete API keys |
| Core Capability | API key CRUD with admin RBAC |
| WebApp Endpoint | POST/GET/DELETE /api-keys/, POST /api-keys/{id}/rotate |
| Endpoint Verified | YES |
| Response Verified | YES |
| Real Data | N/A (no test data) |
| Empty State | YES |
| Error State | YES |
| Partial State | N/A |
| Mutation | YES |
| Mutation Verified | NO |
| Browser Verified | NO |
| Decision | **DEFER** — admin-only feature, low priority for initial certification |

---

## Feedback

| Property | Value |
|---|---|
| Page | N/A (embedded in chat/provenance) |
| User Goal | Provide feedback on memory quality |
| User Action | Thumbs up/down, add comment |
| Core Capability | Feedback submission |
| WebApp Endpoint | POST /feedback/ |
| Endpoint Verified | YES |
| Response Verified | YES |
| Real Data | N/A |
| Empty State | N/A |
| Error State | YES |
| Partial State | N/A |
| Mutation | YES |
| Mutation Verified | NO |
| Browser Verified | NO |
| Decision | **DEFER** — not yet surfaced in UI |

---

## Audit / Operations / Storage / Policy

| Property | Value |
|---|---|
| Page | Not yet implemented |
| User Goal | N/A |
| Core Capability | Audit trail, storage management, policy management |
| WebApp Endpoint | GET /audit/events, POST/DELETE /storage/upload, CRUD /policy/ |
| Endpoint Verified | YES |
| Response Verified | PARTIAL |
| Real Data | N/A |
| Decision | **DEFER** — admin-only, no UI yet |
