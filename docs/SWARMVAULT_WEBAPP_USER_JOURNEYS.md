# SWARMVAULT WEBAPP USER JOURNEYS

**Version:** 1.0.0
**Date:** 2026-09-05
**Application Version:** 0.1.0
**Repository SHA:** d970d6b (master)
**Documentation Status:** DRAFT — Journeys verified against codebase

---

## Table of Contents

1. [Journey Conventions](#1-journey-conventions)
2. [Journey J1: First-Time User — Registration to First Chat](#2-journey-j1-first-time-user--registration-to-first-chat)
3. [Journey J2: Ingest a Claude Code Session](#3-journey-j2-ingest-a-claude-code-session)
4. [Journey J3: Search and Retrieve Knowledge](#4-journey-j3-search-and-retrieve-knowledge)
5. [Journey J4: Team Workspace — Invite Members](#5-journey-j4-team-workspace--invite-members)
6. [Journey J5: Manage API Keys for External Access](#6-journey-j5-manage-api-keys-for-external-access)
7. [Journey J6: Explore Knowledge Graph](#7-journey-j6-explore-knowledge-graph)
8. [Journey J7: Track Decisions Over Time](#8-journey-j7-track-decisions-over-time)
9. [Journey J8: Chat with Memory-Grounded Responses](#9-journey-j8-chat-with-memory-grounded-responses)
10. [Journey J9: View Provenance of AI Answers](#10-journey-j9-view-provenance-of-ai-answers)
11. [Journey J10: Upload and Manage Files](#11-journey-j10-upload-and-manage-files)

---

## 1. Journey Conventions

### 1.1 Notation

| Symbol | Meaning |
|--------|---------|
| **→** | Click/navigate to |
| **[field]** | Enter text in field |
| **{api}** | API call made behind the scenes |
| **[select]** | Choose from dropdown |
| **[OK]** | Confirm dialog |
| *(description)* | Developer note about what happens |

### 1.2 Roles

- **Owner** — Full control
- **Admin** — Member management, API keys
- **Member** — Content creation
- **Viewer** — Read-only

### 1.3 Preconditions

- Backend running on port 8000
- Frontend running on port 3000
- PostgreSQL accessible
- LLM provider configured (for chat)

---

## 2. Journey J1: First-Time User — Registration to First Chat

**Role:** New user (no account)
**Duration:** ~3 minutes
**Preconditions:** Backend running, browser open

### Steps

| Step | Action | Page | API Call | Expected Result |
|------|--------|------|----------|-----------------|
| 1 | Navigate to `http://localhost:3000` | `/` | — | Auto-redirect to `/auth/login` |
| 2 | Click "Create one" | `/auth/register` | — | Registration form displayed |
| 3 | Enter full name: "Alice Chen" | `/auth/register` | — | Field populated |
| 4 | Enter email: `alice@example.com` | `/auth/register` | — | Field populated |
| 5 | Enter workspace name: "Alice Workspace" | `/auth/register` | — | Field populated |
| 6 | Enter password (8+ chars) | `/auth/register` | — | Field populated |
| 7 | Confirm password | `/auth/register` | — | Field populated |
| 8 | Click "Create account" | → `/dashboard` | `POST /api/v1/auth/register` | 201, tokens stored, redirected |
| 9 | View dashboard | `/dashboard` | `GET /api/v1/projects` | Empty project list |
| 10 | Click "New Project" | — | — | Form appears |
| 11 | Enter name: "My Knowledge Base" | — | — | Field populated |
| 12 | Click "Create" | → Project detail | `POST /api/v1/projects` | 201, project created |
| 13 | Click "Chat" in sidebar | `/projects/{id}/chat` | — | Chat page loads |
| 14 | Type "Hello, what can you help me with?" | `/projects/{id}/chat` | — | Message in composer |
| 15 | Click Send (or press Enter) | — | `POST /api/v1/chat/stream` (SSE) | Streams response |

### Expected Outcomes
- Account created with Owner role
- Workspace "Alice Workspace" created
- Project "My Knowledge Base" created
- JWT tokens in localStorage
- Chat session started

### Error Paths
| Error | Cause | Resolution |
|-------|-------|------------|
| 409 Conflict | Email already registered | Use different email |
| 422 Validation | Weak password | Use 8+ characters |
| 500 Server | Backend error | Check server logs |

---

## 3. Journey J2: Ingest a Claude Code Session

**Role:** Existing user (member or above)
**Duration:** ~5 minutes
**Preconditions:** Logged in, project exists

### Steps

| Step | Action | Page | API Call | Expected Result |
|------|--------|------|----------|-----------------|
| 1 | Click project in sidebar | `/projects/{id}` | — | Project context active |
| 2 | Click "Ingest" | `/projects/{id}/ingest` | — | Ingest form loads |
| 3 | Select source type: "Claude Code" | Ingest form | — | Dropdown set to `claude-code` |
| 4 | Enter title: "Auth Implementation Discussion" | Ingest form | — | Title set |
| 5 | Open file picker, select `session.jsonl` | Ingest form | — | File selected |
| 6 | Click "Upload & Process" | — | `POST /api/v1/ingest/upload` | 201, source created with `status: processing` |
| 7 | Wait for processing | Ingest page | (M0-M5 pipeline) | Status changes to `completed` |
| 8 | Navigate to Memory | `/projects/{id}/memory` | `GET /api/v1/memory/?project_id={id}` | Memory items displayed |
| 9 | Navigate to Facts | `/projects/{id}/facts` | `GET /api/v1/ingest/facts` | Facts extracted |
| 10 | Navigate to Decisions | `/projects/{id}/decisions` | `GET /api/v1/ingest/decisions` | Decisions extracted |

### Expected Outcomes
- Source processed through M0-M5 pipeline
- Memory items populated
- Facts and decisions extracted
- Knowledge graph updated

### Error Paths
| Error | Cause | Resolution |
|-------|-------|------------|
| 400 Bad Request | Invalid JSONL format | Check file format |
| 413 Content Too Large | File > 10MB | Reduce file size |
| 404 Not Found | Project doesn't exist | Verify project ID |

---

## 4. Journey J3: Search and Retrieve Knowledge

**Role:** Existing user (any authenticated role)
**Duration:** ~2 minutes
**Preconditions:** At least one source ingested and processed

### Steps

| Step | Action | Page | API Call | Expected Result |
|------|--------|------|----------|-----------------|
| 1 | Click project in sidebar | `/projects/{id}` | — | Project context active |
| 2 | Click "Search" | `/projects/{id}/search` | — | Search page loads |
| 3 | Type "authentication mechanism" in search box | Search page | — | Query entered |
| 4 | Press Enter | Search page | `GET /api/v1/ingest/search?query=...` | Results displayed |
| 5 | Review results | Search page | — | Cards with relevance scores |
| 6 | Click a result | — | — | (Detail view) |
| 7 | Navigate to Memory | `/projects/{id}/memory` | `GET /api/v1/memory/?project_id={id}` | Full memory list |

### Expected Outcomes
- Search returns relevant results with scores
- Results show memory, fact, or decision type
- Relevance scores indicate match quality

### Error Paths
| Error | Cause | Resolution |
|-------|-------|------------|
| Empty results | No ingested content | Ingest sources first |
| Low scores | Weak semantic match | Try different query terms |

---

## 5. Journey J4: Team Workspace — Invite Members

**Role:** Workspace Owner or Admin
**Duration:** ~3 minutes
**Preconditions:** Logged in as owner/admin, workspace exists

### Steps

| Step | Action | Page | API Call | Expected Result |
|------|--------|------|----------|-----------------|
| 1 | Click "Settings & Members" in sidebar | `/settings` | — | Settings page loads |
| 2 | Navigate to Members tab | Members tab | `GET /api/v1/workspace/members` | Member list displayed |
| 3 | Enter email: `bob@example.com` | Members tab | — | Email entered |
| 4 | Select role: "Member" | Members tab | — | Role selected |
| 5 | Click "Invite" | Members tab | `POST /api/v1/workspace/members` | Bob added to list |
| 6 | Bob receives invitation | — | — | Bob can now log in and access workspace |
| 7 | Verify member in list | Members tab | — | Bob listed with "member" badge |

### Expected Outcomes
- Bob added to workspace with Member role
- Bob can access workspace after logging in
- Bob sees workspace projects

### Error Paths
| Error | Cause | Resolution |
|-------|-------|------------|
| 403 | Not admin/owner | Use admin account |
| 409 | Already a member | User already in workspace |
| 422 | Invalid email | Check email format |

---

## 6. Journey J5: Manage API Keys for External Access

**Role:** Workspace Admin or Owner
**Duration:** ~2 minutes
**Preconditions:** Logged in as admin/owner

### Steps

| Step | Action | Page | API Call | Expected Result |
|------|--------|------|----------|-----------------|
| 1 | Click "Settings & Members" in sidebar | `/settings` | — | Settings page loads |
| 2 | Navigate to "API Keys" | `/settings/api-keys` | `GET /api/v1/api-keys/` | Key list displayed |
| 3 | Click "Create API key" | API Keys page | — | Form appears |
| 4 | Enter name: "CI/CD Pipeline" | API Keys page | — | Name entered |
| 5 | Click "Create" | API Keys page | `POST /api/v1/api-keys/` | Key created, raw key shown |
| 6 | Copy raw key (shown once) | API Keys page | — | Key copied to clipboard |
| 7 | Use key in external service | — | — | Key authenticates requests |
| 8 | Navigate back to API Keys | `/settings/api-keys` | `GET /api/v1/api-keys/` | Key listed (masked) |

### Expected Outcomes
- API key created with 32-char hex value
- Key appears in list with prefix shown
- External service can authenticate with key

### Error Paths
| Error | Cause | Resolution |
|-------|-------|------------|
| 403 | Not admin | Use admin/owner account |

---

## 7. Journey J6: Explore Knowledge Graph

**Role:** Existing user (any authenticated role)
**Duration:** ~3 minutes
**Preconditions:** Sources ingested, graph data available

### Steps

| Step | Action | Page | API Call | Expected Result |
|------|--------|------|----------|-----------------|
| 1 | Click project in sidebar | `/projects/{id}` | — | Project context active |
| 2 | Click "Graph" | `/projects/{id}/graph` | `GET /api/v1/ingest/graph?project_id={id}` | Graph renders |
| 3 | View nodes and edges | Graph page | — | Entities and relationships visible |
| 4 | Click a node | Graph page | — | Node detail panel opens |
| 5 | Toggle "Include historical" | Graph page | `GET /api/v1/ingest/graph?include_historical=true` | Historical nodes appear |
| 6 | Click another node | Graph page | — | Different entity details |

### Expected Outcomes
- Graph renders with nodes and edges
- Node click shows properties
- Historical toggle reveals superseded entities

### Error Paths
| Error | Cause | Resolution |
|-------|-------|------------|
| Empty graph | No ingested content | Ingest sources first |
| Slow rendering | Large graph | Use filters |

---

## 8. Journey J7: Track Decisions Over Time

**Role:** Existing user (any authenticated role)
**Duration:** ~2 minutes
**Preconditions:** Sources ingested with decisions

### Steps

| Step | Action | Page | API Call | Expected Result |
|------|--------|------|----------|-----------------|
| 1 | Click project in sidebar | `/projects/{id}` | — | Project context active |
| 2 | Click "Decisions" | `/projects/{id}/decisions` | `GET /api/v1/ingest/decisions?project_id={id}` | Decision list |
| 3 | View current decisions | Decisions page | — | "current" tab active |
| 4 | Click "superseded decisions" tab | Decisions page | `GET /api/v1/ingest/decisions?temporal_status=superseded` | Superseded decisions |
| 5 | Review decision details | Decisions page | — | Confidence, temporal status, tags |

### Expected Outcomes
- Current decisions shown in "current" tab
- Superseded decisions in separate tab
- Confidence scores color-coded

---

## 9. Journey J8: Chat with Memory-Grounded Responses

**Role:** Existing user (any authenticated role)
**Duration:** ~5 minutes
**Preconditions:** Sources ingested and processed

### Steps

| Step | Action | Page | API Call | Expected Result |
|------|--------|------|----------|-----------------|
| 1 | Click project in sidebar | `/projects/{id}` | — | Project context active |
| 2 | Click "Chat" | `/projects/{id}/chat` | — | Chat page loads |
| 3 | Type: "What authentication system do we use?" | Chat page | — | Message in composer |
| 4 | Click Send | — | `POST /api/v1/chat/stream` | SSE stream begins |
| 5 | Watch streaming response | Chat page | — | `sources` event → `token` events → `done` |
| 6 | Review sources panel | Chat page | — | Retrieved memories displayed |
| 7 | Click "Why this answer?" | Evidence modal | — | Provenance details shown |

### Expected Outcomes
- Response streams in real-time
- Sources panel shows relevant memories
- Evidence modal shows provenance chain

### SSE Event Flow
```
sources → token (chunks) → token → ... → done
```

---

## 10. Journey J9: View Provenance of AI Answers

**Role:** Existing user (any authenticated role)
**Duration:** ~2 minutes
**Preconditions:** At least one chat response generated

### Steps

| Step | Action | Page | API Call | Expected Result |
|------|--------|------|----------|-----------------|
| 1 | Go to Chat | `/projects/{id}/chat` | — | Chat page loads |
| 2 | Find an assistant message | Chat page | — | Message with "Why this answer?" button |
| 3 | Click "Why this answer?" | Evidence modal | — | Modal opens |
| 4 | Review evidence trail | Evidence modal | — | Source memories, scores shown |
| 5 | Navigate to Provenance page | `/projects/{id}/provenance` | `GET /api/v1/provenance/` | Full provenance history |

### Expected Outcomes
- Evidence modal shows answer + source chain
- Provenance page shows full audit trail
- Memory source IDs linkable

---

## 11. Journey J10: Upload and Manage Files

**Role:** Existing user (member or above)
**Duration:** ~3 minutes
**Preconditions:** Logged in, storage access

### Steps

| Step | Action | Page | API Call | Expected Result |
|------|--------|------|----------|-----------------|
| 1 | Click "Settings" in sidebar | `/settings` | — | Settings page loads |
| 2 | Click "Storage" tab | `/settings/storage` | — | Storage page loads |
| 3 | Click file picker | Storage page | — | File dialog opens |
| 4 | Select `.jsonl` file | Storage page | — | File selected |
| 5 | Watch upload progress | Storage page | `POST /api/v1/ingest/upload` | Progress bar fills |
| 6 | Verify file listed | Storage page | — | File with status "ingested" |

### Expected Outcomes
- File uploaded successfully
- Status shows "ingested"
- Content available via search/memory

---

## Appendix: Journey Quick Reference

| ID | Journey | Entry Point | Duration | Min Role |
|----|---------|-------------|----------|----------|
| J1 | First-Time Registration → First Chat | `/` | 3 min | None |
| J2 | Ingest Claude Code Session | `/projects/{id}/ingest` | 5 min | Member |
| J3 | Search and Retrieve Knowledge | `/projects/{id}/search` | 2 min | Auth |
| J4 | Team Workspace — Invite Members | `/settings` | 3 min | Admin |
| J5 | Manage API Keys | `/settings/api-keys` | 2 min | Admin |
| J6 | Explore Knowledge Graph | `/projects/{id}/graph` | 3 min | Auth |
| J7 | Track Decisions Over Time | `/projects/{id}/decisions` | 2 min | Auth |
| J8 | Chat with Memory-Grounded Responses | `/projects/{id}/chat` | 5 min | Auth |
| J9 | View Provenance | `/projects/{id}/provenance` | 2 min | Auth |
| J10 | Upload and Manage Files | `/settings/storage` | 3 min | Member |
