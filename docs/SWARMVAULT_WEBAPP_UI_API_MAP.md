# SWARMVAULT WEBAPP UI-API MAP

**Version:** 1.0.0
**Date:** 2026-09-05
**Application Version:** 0.1.0
**Repository SHA:** d970d6b (master)
**Documentation Status:** DRAFT — Mapped from verified codebase

---

## Table of Contents

1. [Mapping Convention](#1-mapping-convention)
2. [Authentication](#2-authentication)
3. [Dashboard](#3-dashboard)
4. [Projects](#4-projects)
5. [Chat](#5-chat)
6. [Ingest](#6-ingest)
7. [Memory](#7-memory)
8. [Search](#8-search)
9. [Graph](#9-graph)
10. [Timeline](#10-timeline)
11. [Facts](#11-facts)
12. [Decisions](#12-decisions)
13. [Sessions](#13-sessions)
14. [Provenance](#15-provenance)
16. [Settings — Profile](#16-settings--profile)
17. [Settings — Members](#17-settings--members)
18. [Settings — API Keys](#18-settings--api-keys)
19. [Settings — Storage](#19-settings--storage)
20. [Summary Table](#20-summary-table)

---

## 1. Mapping Convention

Each mapping entry follows this format:

| Field | Description |
|-------|-------------|
| **Page** | Route path and page component |
| **Action** | User action that triggers the API call |
| **Method** | HTTP method |
| **Endpoint** | Backend API route |
| **Request** | Request body or params |
| **Response** | Response schema |
| **Auth** | Minimum role required |

### Legend

| Role | Level | Abbrev. |
|------|-------|---------|
| Owner | 1000 | O |
| Admin | 500 | A |
| Member | 100 | M |
| Viewer | 50 | V |
| Any authenticated | - | Auth |

---

## 2. Authentication

### 2.1 Login

| Page | `/auth/login` |
|------|---------------|

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| Sign in | POST | `/api/v1/auth/login` | `{ email, password }` | `TokenResponse` | None |

```json
// Request
{ "email": "user@example.com", "password": "password123" }

// Response (200)
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": "uuid", "email": "user@example.com", "name": "User" }
}
```

### 2.2 Registration

| Page | `/auth/register` |
|------|------------------|

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| Create account | POST | `/api/v1/auth/register` | `{ full_name, email, workspace_name, password }` | `TokenResponse` | None |

```json
// Request
{ "full_name": "User", "email": "user@example.com", "workspace_name": "My Workspace", "password": "securepass123" }

// Response (201)
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": "uuid", "email": "user@example.com", "name": "User" }
}
```

### 2.3 Refresh Token

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| Refresh access token | POST | `/api/v1/auth/refresh` | `{ refresh_token }` | `TokenResponse` | Refresh token |

### 2.4 Logout

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| Logout | POST | `/api/v1/auth/logout` | `{ refresh_token }` | 204 | Auth |

### 2.5 Password Change

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| Change password | POST | `/api/v1/auth/change-password` | `{ current_password, new_password }` | 200 | Auth |

---

## 3. Dashboard

### 3.1 Page: `/dashboard`

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| Load dashboard | GET | `/api/v1/projects` | — | `list[ProjectOut]` | Auth |
| Create project | POST | `/api/v1/projects` | `{ name, description? }` | `ProjectOut` | Auth |

```json
// Request (Create)
{ "name": "My Project", "description": "Optional description" }

// Response (201)
{
  "id": "uuid",
  "name": "My Project",
  "description": "Optional description",
  "workspace_id": "uuid",
  "created_at": "2026-09-05T10:00:00Z"
}
```

---

## 4. Projects

### 4.1 Page: `/projects`

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| List all projects | GET | `/api/v1/projects` | — | `list[ProjectOut]` | Auth |
| Create project | POST | `/api/v1/projects` | `{ name, description? }` | `ProjectOut` | Auth |

### 4.2 Page: `/projects/{id}/settings`

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| Load project | GET | `/api/v1/projects/{id}` | — | `ProjectOut` | Auth |
| Update project | PATCH | `/api/v1/projects/{id}` | `{ name?, description? }` | `ProjectOut` | M |
| Delete project | DELETE | `/api/v1/projects/{id}` | — | 204 | O |

---

## 5. Chat

### 5.1 Page: `/projects/{id}/chat`

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| Stream chat | POST | `/api/v1/chat/stream` | `{ message, session_id?, project_id? }` | `text/event-stream` | Auth |
| Get session history | GET | `/api/v1/sessions/{id}/history` | — | `SessionHistoryResponse` | Auth |

```json
// Request (Stream)
{
  "message": "What did we discuss about authentication?",
  "session_id": "uuid",
  "project_id": "uuid"
}

// SSE Events
// sources: { type: "sources", sources: [{ memory_id, score }] }
// token:   { type: "token", content: "The capital..." }
// done:    { type: "done", message_id, session_id, usage, latency_ms }
// error:   { type: "error", detail: "..." }
```

---

## 6. Ingest

### 6.1 Page: `/projects/{id}/ingest`

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| Upload content | POST | `/api/v1/ingest/upload` | `{ project_id, source_type, content?, file?, title? }` | `IngestUploadResponse` | M |
| List sources | GET | `/api/v1/ingest/sources` | `?project_id={id}&limit=50&offset=0` | `list[IngestSourceOut]` | Auth |
| Search | GET | `/api/v1/ingest/search` | `?query={text}&project_id={id}&limit=20` | `SearchResponse` | Auth |

```json
// Request (Upload text)
{
  "project_id": "uuid",
  "source_type": "claude-code",
  "content": "<jsonl content>",
  "title": "My Session"
}

// Response (201)
{
  "id": "uuid",
  "project_id": "uuid",
  "source_type": "claude-code",
  "title": "My Session",
  "status": "processing",
  "message_count": 42,
  "created_at": "2026-09-05T10:00:00Z"
}
```

### 6.2 Source Types

| Value | Description |
|-------|-------------|
| `text` | Plain text |
| `chatgpt` | ChatGPT JSON export |
| `claude` | Claude JSON export |
| `claude-code` | Claude Code JSONL |
| `json` | Generic JSON array |
| `jsonl` | JSONL format |
| `markdown` | Markdown text |

---

## 7. Memory

### 7.1 Page: `/projects/{id}/memory`

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| List memories | GET | `/api/v1/memory/` | `?project_id={id}&limit=50&offset=0` | `list[MemoryOut]` | Auth |
| Get memory | GET | `/api/v1/memory/{id}` | — | `MemoryOut` | Auth |
| Update memory | PATCH | `/api/v1/memory/{id}` | `{ tags?, status? }` | `MemoryOut` | M |
| Delete memory | DELETE | `/api/v1/memory/{id}` | — | 204 | O |

```json
// Response (MemoryOut)
{
  "id": "uuid",
  "project_id": "uuid",
  "memory_type": "semantic_memory",
  "content": "The system uses JWT authentication...",
  "temporal_status": "current",
  "confidence_score": 95,
  "authority": 0.9,
  "tags": ["auth", "jwt"],
  "created_at": "2026-09-05T10:00:00Z",
  "updated_at": "2026-09-05T10:00:00Z"
}
```

---

## 8. Search

### 8.1 Page: `/projects/{id}/search`

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| Semantic search | GET | `/api/v1/ingest/search` | `?query={text}&project_id={id}&limit=20` | `SearchResponse` | Auth |

```json
// Request
GET /api/v1/ingest/search?query=authentication+JWT&project_id=uuid&limit=20

// Response
{
  "results": [
    {
      "id": "uuid",
      "type": "memory",
      "content": "The system uses JWT authentication...",
      "relevance_score": 0.92,
      "temporal_status": "current",
      "created_at": "2026-09-05T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

## 9. Graph

### 9.1 Page: `/projects/{id}/graph`

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| Get knowledge graph | GET | `/api/v1/ingest/graph` | `?project_id={id}&include_historical=false` | `GraphResponse` | Auth |

```json
// Response
{
  "nodes": [
    { "id": "uuid", "label": "JWT", "type": "concept", "properties": {} }
  ],
  "edges": [
    { "source": "uuid", "target": "uuid", "label": "uses", "confidence": 0.95 }
  ]
}
```

---

## 10. Timeline

### 10.1 Page: `/projects/{id}/timeline`

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| Get timeline | GET | `/api/v1/ingest/timeline` | `?project_id={id}&limit=100` | `TimelineResponse` | Auth |

```json
// Response
{
  "events": [
    {
      "id": "uuid",
      "type": "memory",
      "content": "...",
      "temporal_status": "current",
      "created_at": "2026-09-05T10:00:00Z"
    }
  ]
}
```

---

## 11. Facts

### 11.1 Page: `/projects/{id}/facts`

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| List facts | GET | `/api/v1/ingest/facts` | `?project_id={id}&subject?={text}&temporal_status?={current\|superseded}` | `list[FactOut]` | Auth |

```json
// Response (FactOut)
{
  "id": "uuid",
  "project_id": "uuid",
  "subject": "SwarmVault",
  "predicate": "uses",
  "object": "PostgreSQL",
  "statement": "SwarmVault uses PostgreSQL for storage",
  "confidence_score": 95,
  "status": "current",
  "authority": 0.9,
  "created_at": "2026-09-05T10:00:00Z"
}
```

---

## 12. Decisions

### 12.1 Page: `/projects/{id}/decisions`

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| List decisions | GET | `/api/v1/ingest/decisions` | `?project_id={id}&temporal_status?={current\|superseded}` | `list[DecisionOut]` | Auth |

```json
// Response (DecisionOut)
{
  "id": "uuid",
  "project_id": "uuid",
  "content": "We decided to use PostgreSQL for persistence",
  "confidence_score": 88,
  "temporal_status": "current",
  "tags": ["architecture"],
  "created_at": "2026-09-05T10:00:00Z"
}
```

---

## 13. Sessions

### 13.1 Page: `/projects/{id}/sessions`

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| List sessions | GET | `/api/v1/sessions` | `?project_id={id}` | `list[SessionOut]` | Auth |

### 13.2 Page: `/projects/{id}/sessions/{sessionId}`

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| Get session history | GET | `/api/v1/sessions/{id}/history` | — | `SessionHistoryResponse` | Auth |

```json
// Response (SessionHistoryResponse)
{
  "session": {
    "id": "uuid",
    "project_id": "uuid",
    "title": "Discussion about auth",
    "source_type": "chat",
    "created_at": "2026-09-05T10:00:00Z"
  },
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "What is JWT?",
      "timestamp": "2026-09-05T10:00:01Z"
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "JWT stands for JSON Web Token...",
      "timestamp": "2026-09-05T10:00:02Z"
    }
  ]
}
```

---

## 15. Provenance

### 15.1 Page: `/projects/{id}/provenance`

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| List provenance | GET | `/api/v1/provenance/` | `?project_id={id}&limit=50&offset=0` | `list[ProvenanceOut]` | Auth |

```json
// Response (ProvenanceOut)
{
  "id": "uuid",
  "project_id": "uuid",
  "message_id": "uuid",
  "model": "claude-3-sonnet",
  "provider": "anthropic",
  "retrieval_method": "semantic",
  "confidence_score": 0.92,
  "memory_sources": ["uuid", "uuid"],
  "latency_ms": 1200,
  "usage": {"prompt_tokens": 100, "completion_tokens": 50},
  "created_at": "2026-09-05T10:00:00Z"
}
```

---

## 16. Settings — Profile

### 16.1 Page: `/settings` (Profile tab)

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| Get current user | — | Included in login response | — | `UserOut` | Auth |
| Change password | POST | `/api/v1/auth/change-password` | `{ current_password, new_password }` | 200 | Auth |

---

## 17. Settings — Members

### 17.1 Page: `/settings` (Members tab)

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| List members | GET | `/api/v1/workspace/members` | — | `list[WorkspaceMemberOut]` | Auth |
| Invite member | POST | `/api/v1/workspace/members` | `{ email, role }` | `WorkspaceMemberOut` | A |
| Update member role | PATCH | `/api/v1/workspace/members/{user_id}` | `{ role }` | `WorkspaceMemberOut` | A |
| Remove member | DELETE | `/api/v1/workspace/members/{user_id}` | — | 204 | A |

```json
// Response (WorkspaceMemberOut)
{
  "id": "uuid",
  "user_id": "uuid",
  "user_email": "member@example.com",
  "user_name": "Member Name",
  "role": "member",
  "joined_at": "2026-09-05T10:00:00Z"
}
```

---

## 18. Settings — API Keys

### 18.1 Page: `/settings/api-keys`

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| List API keys | GET | `/api/v1/api-keys/` | — | `list[APIKeyOut]` | A |
| Create API key | POST | `/api/v1/api-keys/` | `{ name }` | `APIKeyCreateResponse` | A |
| Revoke API key | DELETE | `/api/v1/api-keys/{id}` | — | 204 | A |
| Rotate API key | POST | `/api/v1/api-keys/{id}/rotate` | — | `APIKeyCreateResponse` | A |

```json
// Response (APIKeyCreateResponse)
{
  "id": "uuid",
  "name": "My Key",
  "key_prefix": "abc12345",
  "key_last4": "abcd",
  "created_at": "2026-09-05T10:00:00Z",
  "raw_key": "abc12345...abcd"  // SHOWN ONLY ONCE
}
```

**CRITICAL:** `raw_key` is returned only at creation/rotation and is never stored on the server. If lost, the key must be rotated.

---

## 19. Settings — Storage

### 19.1 Page: `/settings/storage`

| Action | Method | Endpoint | Request | Response | Auth |
|--------|--------|----------|---------|----------|------|
| Upload file | POST | `/api/v1/ingest/upload` | multipart: `file`, `project_id`, `source_type` | `IngestUploadResponse` | M |
| List storage files | GET | (frontend-tracked, no backend endpoint) | — | Frontend state | M |

---

## 20. Summary Table

| Page | Route | APIs Used |
|------|-------|-----------|
| Login | `/auth/login` | POST `/api/v1/auth/login` |
| Register | `/auth/register` | POST `/api/v1/auth/register` |
| Dashboard | `/dashboard` | GET/POST `/api/v1/projects` |
| Projects | `/projects` | GET `/api/v1/projects` |
| Project Settings | `/projects/{id}/settings` | GET/PATCH/DELETE `/api/v1/projects/{id}` |
| Chat | `/projects/{id}/chat` | POST `/api/v1/chat/stream`, GET `/api/v1/sessions/{id}/history` |
| Ingest | `/projects/{id}/ingest` | POST `/api/v1/ingest/upload`, GET `/api/v1/ingest/sources`, GET `/api/v1/ingest/search` |
| Memory | `/projects/{id}/memory` | GET/PATCH/DELETE `/api/v1/memory/{id}` |
| Search | `/projects/{id}/search` | GET `/api/v1/ingest/search` |
| Graph | `/projects/{id}/graph` | GET `/api/v1/ingest/graph` |
| Timeline | `/projects/{id}/timeline` | GET `/api/v1/ingest/timeline` |
| Facts | `/projects/{id}/facts` | GET `/api/v1/ingest/facts` |
| Decisions | `/projects/{id}/decisions` | GET `/api/v1/ingest/decisions` |
| Sessions | `/projects/{id}/sessions` | GET `/api/v1/sessions` |
| Session Detail | `/projects/{id}/sessions/{id}` | GET `/api/v1/sessions/{id}/history` |
| Provenance | `/projects/{id}/provenance` | GET `/api/v1/provenance/` |
| Settings — Profile | `/settings` | POST `/api/v1/auth/change-password` |
| Settings — Members | `/settings` | GET/POST/PATCH/DELETE `/api/v1/workspace/members` |
| Settings — API Keys | `/settings/api-keys` | GET/POST/DELETE `/api/v1/api-keys/`, POST `/api/v1/api-keys/{id}/rotate` |
| Settings — Storage | `/settings/storage` | POST `/api/v1/ingest/upload` |
