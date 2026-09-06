# PAGE_CAPABILITY_MATRIX

**Checkpoint:** ca877b1
**Updated:** 2026-09-06

| Page | User Goal | UI Feature | API | API Exists | Core Capability | Real Data | Mutation | Error Contract | Status | Decision |
|------|-----------|------------|-----|------------|----------------|-----------|----------|----------------|--------|----------|
| Login | Authenticate | Form, validation | POST /auth/login, /auth/register | Yes | M0 | Yes | No | Yes | VERIFIED | Keep |
| Dashboard | Overview + manage projects | StatCard grid, view tabs, recent activity | /api/v1/workspace, /api/v1/dashboard/, /api/v1/projects | Yes | M0-M5 | Yes | Yes (create project) | Partial | VERIFIED | Keep — redesign done |
| Projects | Browse + manage projects | Grid, search, badges, tooltips | /api/v1/projects | Yes | M0 | Yes | Yes | Partial | VERIFIED | Keep — redesign done |
| Chat | Q&A grounded in memory | Streaming SSE, evidence modal, sources panel | POST /api/v1/chat/stream | Yes | M5 | Yes | Yes | Partial | PARTIAL | Redesign |
| Search | Find knowledge across project | Search input, results list, score display | GET /api/v1/ingest/search | Yes | M5 | Yes | No | Partial | PARTIAL | Redesign |
| Memory | Browse all memories | List, filter by type | GET /api/v1/memories | Yes | M2 | Yes | No | None | PARTIAL | Redesign |
| Facts | Browse extracted facts | List, authority badges | GET /api/v1/facts | Yes | M2 | Yes | No | None | PARTIAL | Redesign |
| Decisions | Browse decisions | List, temporal status | GET /api/v1/decisions | Yes | M3 | Yes | No | None | PARTIAL | Redesign |
| Timeline | Chronological knowledge view | Timeline items, filters | GET /api/v1/timeline | Yes | M3 | Yes | No | None | PARTIAL | Redesign |
| Graph | Visualize knowledge graph | Nodes, edges, relationships | GET /api/v1/graph | Yes | M4 | Yes | No | None | PARTIAL | Redesign |
| Sessions | Browse chat sessions | Session list | GET /api/v1/sessions | Yes | M1 | Yes | No | None | PARTIAL | Redesign |
| Session Detail | Inspect session messages + extracted knowledge | Messages, memories, provenance | GET /api/v1/sessions/{id}, /history, /provenance | Yes | M1-M4 | Yes | No | None | PARTIAL | Redesign |
| Provenance | Trace answer origin | Chain view, memory links | GET /api/v1/provenance/{session_id} | Yes | M4 | Yes | No | None | PARTIAL | Redesign |
| Ingest | Upload/ingest content | Upload form, source list, job status | /api/v1/ingest/* | Yes | M0 | Yes | Yes | Partial | PARTIAL | Redesign |
| Settings - Profile | Manage user profile | Form | PATCH /api/v1/auth/me, /change-password | Yes | M0 | Yes | Yes | None | PARTIAL | Redesign |
| Settings - API Keys | Manage API keys | Key list, create form | /api/v1/api-keys/* | Yes | M0 | Yes | Yes | None | PARTIAL | Redesign |
| Settings - Storage | Manage vault storage | File list, operations | /api/v1/storage/* | Yes | M0 | Yes | Yes | None | PARTIAL | Redesign |
| Settings - Members | Manage workspace members | Member list, invitations | /api/v1/workspace/members* | Yes | M0 | Yes | Yes | None | PARTIAL | Review |

**Status values:**
- VERIFIED — Redesigned with design system, tested, matches backend
- PARTIAL — Functional but not yet redesigned or missing error states
- PROPOSED — Not yet implemented
- UNSUPPORTED — No backend support
- DEFERRED — Intentionally postponed

**Legend:**
- Design system: Dashboard ✅, Projects ✅, others ❌
- Error handling: Full ✅, Partial ⚠️, None ❌
- Responsive: Tested ✅, Not tested ❌
- Accessibility: Reviewed ✅, Not reviewed ❌
