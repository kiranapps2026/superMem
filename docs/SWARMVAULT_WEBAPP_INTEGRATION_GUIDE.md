# SWARMVAULT WEBAPP INTEGRATION GUIDE

**Version:** 1.0.0
**Date:** 2026-09-05
**Application Version:** 0.1.0
**Repository SHA:** d970d6b (master)
**Documentation Status:** DRAFT — Integration patterns verified against codebase

---

## Table of Contents

1. [Integration Architecture](#1-integration-architecture)
2. [REST API Integration](#2-rest-api-integration)
3. [SSE Streaming Integration](#3-sse-streaming-integration)
4. [Conversation Ingestion](#4-conversation-ingestion)
5. [File Upload](#5-file-upload)
6. [Claude Code Integration](#6-claude-code-integration)
7. [Codex Integration](#7-codex-integration)
8. [Desktop App Integration](#8-desktop-app-integration)
9. [API Key Registration](#9-api-key-registration)
10. [MCP Server Pattern](#10-mcp-server-pattern)
11. [Webhook Pattern](#11-webhook-pattern)
12. [Integration Checklist](#12-integration-checklist)

---

## 1. Integration Architecture

### 1.1 Integration Surfaces

SwarmVault exposes multiple integration surfaces:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ AI Session  │────▶│ Connectors  │────▶│  Backend    │
│ (Claude Code│     │ (M0)        │     │  API        │
│  Codex etc) │     │             │     │             │
├─────────────┤     ├─────────────┤     ├─────────────┤
│ Browser UI  │────▶│ Frontend    │────▶│  REST API   │
│             │     │ (Next.js)   │     │             │
├─────────────┤     ├─────────────┤     ├─────────────┤
│ MCP Server  │────▶│  API Keys   │────▶│  SSE Chat   │
│ (programmatic)│   │ (Bearer JWT)│     │  API        │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 1.2 Integration Methods

| Method | Use Case | Complexity | Status |
|--------|----------|------------|--------|
| REST API | Full programmatic access | Medium | IMPLEMENTED |
| SSE Streaming | Real-time chat | Medium | IMPLEMENTED |
| File Upload | Batch ingestion | Low | IMPLEMENTED |
| API Keys | Secure external access | Low | IMPLEMENTED |
| MCP Server | AI assistant context | High | PARTIAL (backend endpoint exists, no MCP server) |
| Webhooks | Event notifications | High | PLANNED |

### 1.3 Base URL

```
Production: https://your-domain.com
Development: http://localhost:8000
Frontend:    http://localhost:3000
```

---

## 2. REST API Integration

### 2.1 Authentication

All API requests require authentication. Two methods are supported:

**Bearer JWT (browser context):**
```
Authorization: Bearer <access_token>
```

**API Key (programmatic):**
```
X-API-Key: <api_key>
```

### 2.2 API Key Creation

1. Navigate to Settings → API Keys
2. Click "Create API key"
3. Enter a name
4. Copy the key (shown only once)
5. Use the key as `X-API-Key` header in requests

### 2.3 Common Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/auth/login` | POST | Obtain JWT tokens |
| `/api/v1/auth/refresh` | POST | Refresh access token |
| `/api/v1/projects` | GET | List projects |
| `/api/v1/projects` | POST | Create project |
| `/api/v1/projects/{id}` | PATCH | Update project |
| `/api/v1/projects/{id}` | DELETE | Delete project |
| `/api/v1/ingest/upload` | POST | Upload and ingest content |
| `/api/v1/ingest/sources` | GET | List sources |
| `/api/v1/ingest/search` | GET | Semantic search |
| `/api/v1/memory/` | GET | List memories |
| `/api/v1/sessions` | GET | List sessions |
| `/api/v1/sessions/{id}/history` | GET | Session messages |
| `/api/v1/chat/stream` | POST | Streaming chat (SSE) |
| `/api/v1/workspace/members` | GET | List workspace members |

### 2.4 Python Example

```python
import httpx

BASE_URL = "http://localhost:8000"

# Authenticate
resp = httpx.post(f"{BASE_URL}/api/v1/auth/login", json={
    "email": "user@example.com",
    "password": "password123"
})
tokens = resp.json()
headers = {"Authorization": f"Bearer {tokens['access_token']}"}

# Create project
resp = httpx.post(f"{BASE_URL}/api/v1/projects", headers=headers, json={
    "name": "My Project",
    "description": "Project description"
})
project = resp.json()
```

### 2.5 cURL Example

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# List projects
curl http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer <token>"

# Ingest content
curl -X POST http://localhost:8000/api/v1/ingest/upload \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "uuid",
    "source_type": "claude-code",
    "content": "<content>",
    "title": "My Conversation"
  }'
```

---

## 3. SSE Streaming Integration

### 3.1 SSE Protocol

SwarmVault uses Server-Sent Events for real-time chat streaming. The endpoint accepts a POST and returns a `text/event-stream` response.

### 3.2 Event Format

```
event: sources
data: {"type":"sources","sources":[{"memory_id":"uuid","score":0.85}]}

event: token
data: {"type":"token","content":"Hello"}

event: done
data: {"type":"done","message_id":"uuid","session_id":"uuid","usage":{"prompt_tokens":100,"completion_tokens":50},"latency_ms":1200}

event: error
data: {"type":"error","detail":"Something went wrong"}
```

### 3.3 Python SSE Client

```python
import httpx
import json

resp = httpx.post(
    f"{BASE_URL}/api/v1/chat/stream",
    headers={"Authorization": f"Bearer {token}"},
    json={"message": "What did we discuss about authentication?"},
    timeout=None  # SSE streams don't have a fixed timeout
)

for line in resp.iter_lines():
    if line.startswith("data:"):
        event = json.loads(line[5:].strip())
        if event["type"] == "sources":
            print(f"Sources: {event['sources']}")
        elif event["type"] == "token":
            print(event["content"], end="", flush=True)
        elif event["type"] == "done":
            print(f"\nDone in {event['latency_ms']}ms")
        elif event["type"] == "error":
            print(f"Error: {event['detail']}")
```

### 3.4 JavaScript SSE Client

```javascript
const response = await fetch(
  'http://localhost:8000/api/v1/chat/stream',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message: 'What did we discuss?' }),
  }
);

const reader = response.body.getReader();
const decoder = new TextDecoder();
let buffer = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split('\n');
  buffer = lines.pop();

  for (const line of lines) {
    if (line.startsWith('data:')) {
      const event = JSON.parse(line.slice(5).trim());
      if (event.type === 'token') {
        appendToken(event.content);
      } else if (event.type === 'sources') {
        showSources(event.sources);
      } else if (event.type === 'done') {
        onComplete(event);
      }
    }
  }
}
```

---

## 4. Conversation Ingestion

### 4.1 Ingestion Pipeline

```
Raw Input → Connector (M0) → Normalized → M1-M5 Pipeline → Memory/Facts/Decisions/Graph
```

### 4.2 Supported Formats

| Format | `source_type` value | Structure |
|--------|---------------------|-----------|
| ChatGPT Export | `chatgpt` | JSON with `mapping` field |
| Claude Export | `claude` | JSON with `chat_messages` or `conversations` |
| Claude Code | `claude-code` | JSONL with user/assistant/tool/system events |
| Generic JSON | `json` | Array of `{role, content}` objects |
| JSONL | `jsonl` | Line-delimited JSON |
| Markdown | `markdown` | Markdown text |
| Plain Text | `text` | Raw text |

### 4.3 Claude Code JSONL Format

Claude Code sessions export as JSONL files where each line is a JSON event:

```jsonl
{"type":"user","message":{"role":"user","content":"What is the capital of France?"}}
{"type":"assistant","message":{"role":"assistant","content":"The capital of France is Paris."}}
{"type":"tool_use","message":{"role":"assistant","content":"I'll search for this."}}
{"type":"tool_result","message":{"role":"user","content":"Tool result..."}}
```

**Ingest with:**
```bash
curl -X POST http://localhost:8000/api/v1/ingest/upload \
  -H "Authorization: Bearer <token>" \
  -F "project_id=<uuid>" \
  -F "source_type=claude-code" \
  -F "file=@session.jsonl"
```

### 4.4 ChatGPT Format

```json
{
  "mapping": {
    "msg-1": {
      "id": "msg-1",
      "message": {
        "id": "msg-1",
        "author": {"role": "user"},
        "content": {"parts": ["Hello"]}
      }
    }
  }
}
```

### 4.5 Claude Export Format

```json
{
  "chat_messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ]
}
```

### 4.6 Deduplication

The system computes SHA-256 of input content. If the same hash is uploaded again, the existing source is returned without reprocessing. This prevents double-processing of identical content.

### 4.7 Ingestion Response

```json
{
  "id": "uuid",
  "project_id": "uuid",
  "source_type": "claude-code",
  "title": "My Conversation",
  "status": "processing",
  "message_count": 42,
  "created_at": "2026-09-05T10:00:00Z"
}
```

Poll for status:
```
GET /api/v1/ingest/sources?project_id={id}
```

---

## 5. File Upload

### 5.1 Upload via API

```bash
curl -X POST http://localhost:8000/api/v1/ingest/upload \
  -H "Authorization: Bearer <token>" \
  -F "project_id=<uuid>" \
  -F "file=@document.pdf"
```

### 5.2 Upload via Frontend

The frontend storage page at `/settings/storage` provides:
- Drag-and-drop file picker
- Upload progress bar
- Status tracking (uploading, ingested, failed)
- File size display

### 5.3 Supported File Types

| Extension | Content Type | Recommended source_type |
|-----------|-------------|------------------------|
| .txt | text/plain | text |
| .json | application/json | json |
| .jsonl | application/json | jsonl |
| .md | text/markdown | markdown |
| .csv | text/csv | text |
| .pdf | application/pdf | text (extract first) |

### 5.4 File Size Limits

- Maximum 50MB per file (content limit)
- Maximum 10MB for ingestion pipeline input

---

## 6. Claude Code Integration

### 6.1 Current Status: Infrastructure Exists — User Workflow Not Yet Exposed

The backend contains a `ClaudeCodeConnector` that can parse Claude Code JSONL session exports. This connector is registered in the connector system and available for ingestion.

**What exists:**
- `ClaudeCodeConnector` in `app/services/connectors.py`
- JSONL event parsing (user, assistant, tool_use, tool_result)
- Event type detection and normalization

**What does NOT exist (yet):**
- One-click "Export to SwarmVault" from Claude Code CLI
- Desktop application
- Automatic session capture
- Browser extension
- WebSocket/live session capture

### 6.2 Claude Code JSONL Ingest Workflow

Since no direct integration exists yet, use the REST API:

```python
import httpx

# After a Claude Code session, ingest the JSONL export
with open("/path/to/session.jsonl", "rb") as f:
    resp = httpx.post(
        "http://localhost:8000/api/v1/ingest/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("session.jsonl", f, "application/json")},
        data={
            "project_id": "your-project-uuid",
            "source_type": "claude-code"
        }
    )

print(resp.json())  # {id, status: "processing", ...}
```

### 6.3 Connecting to Claude Code (CLI)

Currently, the recommended workflow is:

1. **Export session** from Claude Code (if export feature available)
2. **Save as JSONL** file
3. **Upload via** SwarmVault UI (`/projects/{id}/ingest`) or API
4. **Process** through M0-M5 pipeline
5. **Search and retrieve** from the knowledge base

### 6.4 Event Types in Claude Code JSONL

| Event Type | Description |
|------------|-------------|
| `user` | User message (input to Claude) |
| `assistant` | Claude's response |
| `tool_use` | Claude requesting a tool |
| `tool_result` | Result returned to Claude |
| `thinking` | Extended thinking content (if visible) |
| `system` | System-level events |

---

## 7. Codex Integration

### 7.1 Current Status: NOT IMPLEMENTED

No OpenClaw Codex integration exists in the SwarmVault WebApp. There is no Codex connector, no Codex-specific ingestion format, and no UI for Codex import.

### 7.2 How It Could Work (Future)

| Component | Status | Notes |
|-----------|--------|-------|
| Codex connector | NOT IMPLEMENTED | Would parse Codex conversation format |
| Codex UI import | NOT IMPLEMENTED | Drag-and-drop or file picker |
| Codex API integration | NOT IMPLEMENTED | Would need Codex export format spec |
| Real-time capture | NOT IMPLEMENTED | Would need Codex hook/extension |

### 7.3 Generic Fallback

Codex conversations could potentially be ingested via:
- **JSON format** — if Codex exports standard JSON messages
- **Text format** — If Codex exports plain text logs

Use the `source_type: "json"` or `source_type: "text"` options as workarounds.

---

## 8. Desktop App Integration

### 8.1 Current Status: NOT IMPLEMENTED

SwarmVault is a **web application only**. There is no desktop application (Electron, Tauri, etc.).

### 8.2 Deployment Options

| Option | Status | Description |
|--------|--------|-------------|
| Self-hosted web | IMPLEMENTED | Docker compose, Uvicorn server |
| Cloud-hosted | NOT AVAILABLE | No hosted version currently |
| Desktop app | NOT IMPLEMENTED | No desktop wrapper exists |

### 8.3 Desktop Equivalent via Browser

The web application runs in any modern browser:
- Local development: `http://localhost:3000`
- Self-hosted: Deploy behind a reverse proxy (Nginx, Caddy)
- PWA: NOT configured (no manifest/service worker)

---

## 9. API Key Registration

### 9.1 Creating an API Key

1. Log in to SwarmVault
2. Go to Settings → API Keys
3. Click "Create API key"
4. Copy the key immediately (shown only once)

### 9.2 Using an API Key

```bash
curl http://localhost:8000/api/v1/projects \
  -H "X-API-Key: <your-key>"
```

### 9.3 Key Properties

| Property | Value |
|----------|-------|
| Length | 32 hex characters (128-bit) |
| Prefix display | First 8 characters |
| "Last 4" | Last 4 characters |
| Storage | SHA-256 hashed |
| Scope | Workspace-scoped |
| Rotation | Creates new key, invalidates old |

### 9.4 Permissions

- **Admin only** — API key creation and management requires admin role
- **Viewer** — Can use keys but cannot manage them

---

## 10. MCP Server Pattern

### 10.1 Current Status: PARTIAL

The backend has API endpoints for API key management (`/api/v1/api-keys/`), and the frontend API key description mentions "MCP Server" as a use case. However, **no MCP server implementation exists** in the codebase.

### 10.2 What Would a SwarmVault MCP Server Provide

| Tool | Description | Status |
|------|-------------|--------|
| `search_memories` | Semantic search across project memories | Would call GET /api/v1/ingest/search |
| `get_facts` | Retrieve extracted facts | Would call GET /api/v1/ingest/facts |
| `get_decisions` | Retrieve extracted decisions | Would call GET /api/v1/ingest/decisions |
| `list_projects` | List accessible projects | Would call GET /api/v1/projects |
| `chat` | Query project knowledge | Would call POST /api/v1/chat/stream |
| `ingest` | Import conversations | Would call POST /api/v1/ingest/upload |

### 10.3 Building a Custom MCP Server

The REST API is complete enough to build an MCP server externally:

```python
# Conceptual MCP server using SwarmVault's REST API
import mcp
from mcp.server import Server
import httpx

app = Server("swarmvault-mcp")
SWARMVAULT_URL = "http://localhost:8000"
API_KEY = "<your-api-key>"

@app.call_tool()
async def search_memories(query: str, project_id: str):
    """Search project memories semantically."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SWARMVAULT_URL}/api/v1/ingest/search",
            headers={"X-API-Key": API_KEY},
            params={"query": query, "project_id": project_id}
        )
        return resp.json()

@app.call_tool()
async def chat(message: str, project_id: str):
    """Chat with project knowledge as context."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{SWARMVAULT_URL}/api/v1/chat/stream",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json={"message": message, "project_id": project_id}
        )
        # Parse SSE events...
```

---

## 11. Webhook Pattern

### 11.1 Current Status: PLANNED

No webhook system exists. This section describes the intended pattern.

### 11.2 Intended Webhook Events

| Event | Trigger | Payload |
|-------|---------|---------|
| `ingest.completed` | Source finished processing | source_id, project_id, status |
| `ingest.failed` | Processing error | source_id, error |
| `chat.completed` | Chat response generated | session_id, message_id |
| `member.invited` | New member invitation | workspace_id, email |
| `api_key.created` | New API key | workspace_id |
| `api_key.revoked` | Key revoked | workspace_id |

### 11.3 Registration Flow (Future)

```
POST /api/v1/webhooks/
{
  "url": "https://your-app.com/webhook",
  "events": ["ingest.completed", "chat.completed"],
  "secret": "your-signing-secret"
}
```

---

## 12. Integration Checklist

### 12.1 REST API Integration

- [ ] Create account / obtain API key
- [ ] Configure base URL and auth headers
- [ ] Test authentication flow (login/refresh)
- [ ] Create or select a project
- [ ] Ingest initial content
- [ ] Verify processing completes
- [ ] Test search and retrieval
- [ ] Implement error handling

### 12.2 SSE Chat Integration

- [ ] Set up SSE client (EventSource or fetch + reader)
- [ ] Handle all event types (sources, token, done, error)
- [ ] Implement reconnection logic
- [ ] Handle token refresh during streaming
- [ ] Display sources to user
- [ ] Implement "Why this answer?" feature

### 12.3 Claude Code Integration

- [ ] Export sessions as JSONL
- [ ] Ingest via `/api/v1/ingest/upload`
- [ ] Monitor processing status
- [ ] Verify knowledge extraction
- [ ] Search and validate results

### 12.4 File Upload

- [ ] Determine supported formats
- [ ] Configure file size limits
- [ ] Implement multipart upload
- [ ] Handle upload progress
- [ ] Monitor processing status

---

## Appendix A: Error Codes Reference

| HTTP Code | SSE Event | Meaning | Action |
|-----------|-----------|---------|--------|
| 401 | — | Unauthenticated | Refresh token or re-login |
| 403 | — | Forbidden | Check RBAC role |
| 404 | — | Not found | Verify resource exists |
| 422 | — | Validation error | Check request body |
| 429 | — | Rate limited | Back off and retry |
| 500 | error | Server error | Check logs, retry later |
| 503 | error | Service unavailable | Backend down |

## Appendix B: Rate Limits

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Auth (login/register) | 5 requests | 60 seconds |
| Chat | 30 requests | 60 seconds |
| Ingest | 10 requests | 60 seconds |
| Search | 60 requests | 60 seconds |
| Generic | 100 requests | 60 seconds |

## Appendix C: CORS Configuration

- **Allowed origins:** `http://localhost:3000` (configurable)
- **Allowed methods:** GET, POST, PUT, PATCH, DELETE, OPTIONS
- **Allowed headers:** Authorization, Content-Type, X-API-Key, X-Request-ID
- **Credentials:** Enabled (cookies/Authorization header)
