# SwarmVault Background Ingestion & Agent Integration Gap Analysis

**Forensic status**: Source-first. Every claim traced to actual implementation.
**Created**: 2026-09-10

---

## 1. Executive Summary

SwarmVault has the **data model** for background ingestion (`IngestJob`) and **external integrations** (Claude Code connector, LLM provider abstraction, Memory Service API layer), but the **execution infrastructure** for background processing and the **actual wiring** for external agent integration are substantially incomplete.

| Dimension | Status |
|-----------|--------|
| Background ingestion worker | MISSING |
| IngestJob model | IMPLEMENTED |
| IngestJob processing | MISSING — model exists, never consumed |
| Async pipeline execution | MISSING |
| Claude Code connector (M0) | IMPLEMENTED |
| ChatGPT connector (M0) | IMPLEMENTED |
| Claude connector (M0) | IMPLEMENTED |
| Generic JSON connector (M0) | IMPLEMENTED |
| JSONL connector (M0) | IMPLEMENTED |
| Markdown connector (M0) | PARTIAL |
| LLM provider abstraction | PARTIAL |
| Anthropic provider | IMPLEMENTED |
| OpenAI provider | UNKNOWN |
| MCP integration | DOCUMENTED ONLY |
| Codex integration | DOCUMENTED ONLY |
| Universal Adapter | DOCUMENTED ONLY |
| SSE streaming chat | IMPLEMENTED |
| WebSocket chat | MISSING |
| External agent write API | DOCUMENTED ONLY |
| Webhook ingestion | MISSING |
| Pull-based ingestion | MISSING |

---

## 2. Background Ingestion — Complete Gap Analysis

### 2.1 The IngestJob Model Exists But Is Never Processed

**Evidence**: `app/models.py` — `IngestJob` model has fields:
- `project_id`, `workspace_id`, `source_type`, `config`, `status`, `stage`, `progress`, `error_message`

**Evidence**: `app/api/ingest.py` — `legacy_start_ingest()` endpoint creates `IngestJob` records:
```python
job = IngestJob(
    project_id=data.project_id,
    workspace_id=tc.workspace_id,
    source_type=data.source_type,
    config=data.config,
)
db.add(job)
await db.commit()
```

**Gap**: No code anywhere reads `IngestJob` records from the database and processes them. The endpoint creates jobs that sit in the database forever.

**Evidence**: No Celery, RQ, Dramatiq, or any task queue configuration in `pyproject.toml`, `requirements.txt`, or `docker-compose.yml`. No `worker` service in deployment config.

**Impact**: Every ingestion blocks the HTTP request synchronously. For large conversation exports (10,000 messages, 10MB+), this creates long timeouts and poor UX. There is no retry mechanism, no progress tracking, no batch processing.

### 2.2 The "Upload" Endpoint Runs Pipeline Synchronously

**Evidence**: `app/api/ingest.py` — `upload_and_ingest()` calls `await run_pipeline()` directly in the request handler. M0→M1→M2→M3→M4 runs in the HTTP request thread.

**Gap**: A slow LLM call (M1 summary generation) or large file blocks the request. No timeout handling. No cancellation.

### 2.3 No Retry or Error Recovery

**Evidence**: `pipeline.py` — on exception:
```python
except Exception as exc:
    source.status = "failed"
    source.error_message = str(exc)
    await db.flush()
    raise
```

The source is marked failed but there is no retry mechanism. A transient database error or LLM timeout permanently fails the ingestion.

### 2.4 No Progress Tracking for Background Jobs

**Evidence**: `IngestJob` has `stage` and `progress` fields but they are never updated by any consumer. They are set at creation time and remain static.

### 2.5 No Ingestion Queue or Priority System

**Evidence**: No queue implementation. No priority ordering. No deduplication beyond content hash.

---

## 3. Connector Inventory (M0)

### 3.1 Implemented Connectors

| Connector | File | Detection | Validation | Parse |
|-----------|------|-----------|------------|-------|
| ChatGPT | `connectors.py` | JSON `mapping` field + filename | JSON validation, size check | Iterates `mapping` values |
| Claude | `connectors.py` | `chat_messages` or `conversations` field | JSON validation, size check | Handles single + multi-conversation |
| Claude Code | `connectors.py` | JSONL with `type` field | String-only, size check | JSONL events: user/assistant/system/summary |
| Generic JSON | `connectors.py` | Array with `role`+`content` or `messages` key | JSON validation, size check | Flat message array |
| JSONL | `connectors.py` | `.jsonl` extension + valid JSON first line | String-only, size check | One JSON object per line |
| Markdown | `connectors.py` | `.md` extension or `#` prefix | None visible | Falls through to text |

### 3.2 Markdown Connector Is Incomplete

**Evidence**: `MarkdownConnector.parse()` is truncated at the end of the file (truncation marker visible). The parse method is not fully visible in source.

**Gap**: Cannot verify markdown parsing is complete or functional.

### 3.3 Connector Security Limits

| Limit | Value | Evidence |
|-------|-------|----------|
| Max content size | 10 MB (`_MAX_CONTENT_LENGTH`) | `connectors.py` |
| Max message size | 100 KB (`_MAX_MESSAGE_LENGTH`) | `connectors.py` |
| Max messages per conversation | 10,000 | `connectors.py:_MAX_MESSAGES` |

These limits are hardcoded constants, not configurable via environment variables or settings.

---

## 4. LLM Provider Integration

### 4.1 Provider Abstraction Exists

**Evidence**: `app/services/llm.py` — defines `LLMProvider` abstract base class and `get_llm_provider()` factory.

### 4.2 Anthropic Provider Implemented

**Evidence**: Anthropic provider exists and is used in `chat_orchestrator.py`. Model: `claude-sonnet-4-5-20250929` (hardcoded default).

### 4.3 OpenAI Provider: Unknown

**Evidence**: No OpenAI provider implementation found. No OpenAI API key configuration in `app/core/config.py`. The provider factory may fail if Anthropic is not configured.

### 4.4 No Provider Fallback

**Evidence**: `chat_orchestrator.py` — if `get_llm_provider()` returns a provider that fails, the error propagates to the caller. No fallback to alternative providers.

---

## 5. External Agent Integration

### 5.1 Claude Code Integration

**Status**: PARTIAL

**What exists**:
- M0 connector for Claude Code JSONL format (`ClaudeCodeConnector`)
- Import path for Claude Code sessions via ingestion API

**What is missing**:
- No bidirectional integration (Claude Code cannot call SwarmVault APIs directly from sessions)
- No tool-use bridge (Claude Code tool calls are flattened to `[tool:name]` text in M0)
- No real-time memory injection into Claude Code sessions

### 5.2 Codex Integration

**Status**: DOCUMENTED ONLY

**Evidence**: No Codex-specific connector, no Codex API client, no Codex import format handler found in source code. Documentation may reference it but no implementation exists.

### 5.3 MCP (Model Context Protocol)

**Status**: DOCUMENTED ONLY

**Evidence**: No MCP server implementation, no MCP tool definitions, no MCP transport layer found in source.

### 5.4 Universal Adapter

**Status**: DOCUMENTED ONLY

**Evidence**: No Universal Adapter implementation found. The connector registry in `connectors.py` is the closest equivalent but is limited to 6 formats.

---

## 6. SSE Streaming Architecture

### 6.1 What Exists

**Evidence**: `app/api/chat.py` — `/chat/stream` endpoint:
- Creates SSE stream with `text/event-stream` media type
- Events: `sources`, `token`, `done`, `error`
- Uses `StreamingResponse` from Starlette
- Headers: `Cache-Control: no-cache`, `X-Accel-Buffering: no`

### 6.2 SSE Gaps

| Gap | Evidence |
|-----|----------|
| No connection timeout handling | `chat.py` — generator runs until completion or error |
| No reconnection support | Client must re-request on disconnect |
| No message persistence during stream | Messages written only at stream end |
| No backpressure | Unbounded token generation |
| No cancellation token | Cannot cancel from client side |
| No heartbeat / keepalive | Long quiet periods may trigger proxy timeouts |
| SSE only — no WebSocket | No bidirectional channel |

---

## 7. Background Processing Infrastructure

### 7.1 Current State: None

| Component | Status | Evidence |
|-----------|--------|----------|
| Task queue (Celery/RQ/Dramatiq) | MISSING | No dependency in requirements |
| Worker process | MISSING | No worker config in docker-compose |
| Redis / broker | MISSING | No Redis service in deployment config |
| Beat scheduler | MISSING | No periodic task config |
| Result backend | MISSING | No result store config |

### 7.2 Impact

- All ingestion is synchronous HTTP
- No retry on transient failure
- No batch processing
- No priority queue
- No SLA on processing time
- No dead-letter queue for failed jobs

---

## 8. Integration Gap Matrix

| Integration | Status | Blocks Persistent Memory | Blocks Memory Intelligence | Evidence |
|-------------|--------|--------------------------|----------------------------|----------|
| Background ingestion worker | MISSING | YES | YES | No task queue found |
| IngestJob processing | MISSING | YES | YES | `app/api/ingest.py` |
| Async pipeline execution | MISSING | YES | YES | `app/services/pipeline.py` |
| OpenAI LLM provider | MISSING | NO | PARTIAL | No implementation found |
| Provider fallback | MISSING | NO | PARTIAL | `app/services/llm.py` |
| Codex integration | DOCUMENTED ONLY | NO | NO | No source code |
| MCP integration | DOCUMENTED ONLY | NO | NO | No source code |
| Universal Adapter | DOCUMENTED ONLY | NO | NO | No source code |
| Webhook ingestion | MISSING | NO | NO | No endpoint found |
| Pull-based ingestion | MISSING | NO | NO | No scheduler found |
| WebSocket chat | MISSING | NO | NO | SSE only |
| SSE reconnection | MISSING | NO | NO | `app/api/chat.py` |

---

## 9. What a Future Memory Intelligence Layer Must Not Assume

1. **Do not assume ingestion is asynchronous**: All ingestion is synchronous HTTP. Background ingestion infrastructure does not exist.
2. **Do not assume IngestJob records are processed**: The model and endpoint exist but nothing consumes them.
3. **Do not assume multi-provider LLM**: Only Anthropic is implemented. No fallback.
4. **Do not assume external agent write access**: Claude Code, Codex, MCP, and Universal Adapter are documented but not implemented.
5. **Do not assume bidirectional streaming**: SSE is one-way (server → client). No WebSocket.
6. **Do not assume markdown ingestion works**: The connector is incomplete.

---

## 10. Required Conditions Before Memory Intelligence

1. **Background ingestion worker** — async pipeline execution with retry, progress tracking, and dead-letter queue
2. **IngestJob consumer** — actual processing of queued jobs
3. **Multi-provider LLM with fallback** — at minimum, graceful degradation if primary provider is unavailable
4. **At least one external agent write API** — a documented, tested, secured API that external agents can call to write memory
5. **Ingestion webhook or pull endpoint** — for real-time or scheduled ingestion from external sources
6. **Markdown connector completion** — verify and complete the truncated implementation
