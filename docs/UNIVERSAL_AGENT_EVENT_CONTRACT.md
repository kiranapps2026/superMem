# Universal Agent Event Contract
**Phase**: M-ARCH — Memory Architecture Freeze Gate
**Status**: PROPOSED — requires review and approval before implementation
**Created**: 2026-09-10

---

## 1. Purpose

This contract defines a **canonical event format** that all external agents
(Claude Code, Codex, future agents) MUST emit when interacting with SwarmVault.

Without this contract, each agent integration invents its own ingestion semantics,
leading to inconsistent memory quality, unpredictable provenance, and fragile
retrieval.

---

## 2. Canonical Event Schema

```typescript
interface UniversalAgentEvent {
  // ── Identity ──────────────────────────────────────────────
  event_id: string;          // UUID v4 — unique per event
  event_type: EventType;     // Enum — what kind of event this is
  timestamp: string;         // ISO 8601 UTC

  // ── Provider ─────────────────────────────────────────────
  provider: {
    name: string;            // "claude_code" | "codex" | "custom"
    version: string;         // Provider version string
  };

  // ── Agent Context ─────────────────────────────────────────
  agent: {
    agent_id: string;        // Unique agent instance ID
    agent_type: string;      // "cli" | "ide" | "api" | "agent"
    session_id: string;      // Agent session (maps to SwarmVault session)
    run_id: string;          // Agent run/turn (maps to SwarmVault run)
  };

  // ── User Context ─────────────────────────────────────────
  user: {
    user_id: string;         // SwarmVault user ID
    workspace_id: string;    // SwarmVault workspace
    project_id: string | null; // Optional project scope
  };

  // ── Message ──────────────────────────────────────────────
  message: {
    role: MessageRole;       // "user" | "assistant" | "system" | "tool" | "tool_result"
    content: string;         // Message content
    parent_message_id: string | null; // For threading
    turn_index: number;      // Sequential turn number in session
  };

  // ── Tool Use (optional) ──────────────────────────────────
  tool_use: {
    tool_calls: Array<{
      tool_name: string;
      tool_input: Record<string, any>;
      tool_call_id: string;
    }>;
    tool_results: Array<{
      tool_call_id: string;
      result: string | Record<string, any>;
      is_error: boolean;
    }>;
  } | null;

  // ── Source Reference ──────────────────────────────────────
  source: {
    source_type: string;     // "conversation" | "document" | "api" | "agent_session"
    source_id: string | null; // Original source identifier
    external_id: string | null; // Agent's internal ID for this conversation
    content_hash: string | null; // SHA-256 of full conversation content
    url: string | null;      // If applicable
  };

  // ── Metadata ──────────────────────────────────────────────
  metadata: Record<string, any>; // Agent-specific data (preserved, not interpreted)
}

type EventType =
  | "message"           // Standard message exchange
  | "session_start"     // Agent session began
  | "session_end"       // Agent session ended
  | "tool_use"          // Agent invoked a tool
  | "memory_write"      // Agent explicitly wrote memory
  | "memory_read"       // Agent explicitly read memory
  | "summary"           // Agent produced a summary
  | "error"             // Agent error event
  | "heartbeat";        // Keepalive for long sessions

type MessageRole =
  | "user"
  | "assistant"
  | "system"
  | "tool"
  | "tool_result";
```

---

## 3. Event Flow by Integration

### 3.1 Claude Code Integration

```
Claude Code Session
       │
       ▼
Claude Code JSONL file
       │
       ▼
ClaudeCodeConnector (M0 — app/services/connectors.py)
       │
       ▼
UniversalAgentEvent (canonical format)
       │
       ▼
run_pipeline() (M0–M4)
       │
       ▼
PostgreSQL (memories, facts, decisions, graph)
```

**Current**: `ClaudeCodeConnector` in `app/services/connectors.py` parses JSONL
and produces a `NormalizedConversation`. The connector does NOT produce
`UniversalAgentEvent` format.

**Required**: Add a `to_universal_event()` method on each connector that
produces the canonical format.

### 3.2 Codex Integration (Planned)

```
Codex Session
       │
       ▼
CodexConnector (does not exist)
       │
       ▼
UniversalAgentEvent (canonical format)
       │
       ▼
[Same as Claude Code]
```

### 3.3 Direct API Integration

```
External Agent
       │
       ▼
POST /api/v1/agent/events
       │
       ▼
UniversalAgentEvent validation
       │
       ▼
run_pipeline() or direct MemoryService.write()
```

**Current**: No such endpoint exists. The closest equivalent is `/ingest/upload`.

---

## 4. M0 Mapping: UniversalAgentEvent → NormalizedConversation

Every connector MUST implement:

```python
class BaseConnector:
    def to_universal_event(self, raw: Any) -> UniversalAgentEvent:
        """Convert raw agent output to canonical event format."""
        raise NotImplementedError

    def to_normalized_conversation(self, raw: Any) -> NormalizedConversation:
        """Convert raw agent output to SwarmVault internal format."""
        # Calls to_universal_event() internally
        event = self.to_universal_event(raw)
        return self._event_to_conversation(event)
```

This ensures:
1. Every connector produces the canonical format
2. The canonical format is the single source of truth for external data
3. The internal `NormalizedConversation` is derived from the canonical format
4. Future connectors only need to implement `to_universal_event()`

---

## 5. Source Identity Contract

Every `UniversalAgentEvent` MUST carry enough information to uniquely identify
its source. The `content_hash` field MUST be the SHA-256 of the **full raw
content** (entire conversation, not per-message).

For streaming/long-running agents:
- `content_hash` is computed incrementally (rolling SHA-256)
- Final hash is attached to the `session_end` event
- Deduplication uses the final hash

---

## 6. Session/Run Mapping

| Agent Concept | SwarmVault Concept | Mapping |
|---------------|-------------------|---------|
| Agent session | `Session` | `agent.session_id` → `sessions.id` |
| Agent turn/run | `Run` (future) or `Message` | `agent.run_id` → `messages.id` (current) |
| Agent instance | `agent_id` in Memory | `agent.agent_id` → `memories.agent_id` |
| Conversation | `Source` | `source.external_id` → `sources.external_id` |

---

## 7. Current Connector Compliance

| Connector | File | Produces UniversalAgentEvent? | Produces NormalizedConversation? |
|-----------|------|------------------------------|--------------------------------|
| ChatGPT | `connectors.py` | NO | YES |
| Claude | `connectors.py` | NO | YES |
| Claude Code | `connectors.py` | NO | YES |
| Generic JSON | `connectors.py` | NO | YES |
| JSONL | `connectors.py` | NO | YES |
| Markdown | `connectors.py` | PARTIAL (truncated) | PARTIAL |

---

## 8. Event Validation Rules

Inbound `UniversalAgentEvent` MUST pass:

1. Schema validation (Pydantic model)
2. `user.workspace_id` exists and is accessible to the authenticated caller
3. `event_id` is unique (idempotency check)
4. `timestamp` is within acceptable skew (±5 minutes)
5. `content` is non-empty and within size limits
6. `source.content_hash` matches SHA-256 of `content` (when provided)
7. `agent.agent_id` is registered (for write operations)

---

## 9. Implementation Requirements

| Requirement | Priority | Effort |
|-------------|----------|--------|
| Define UniversalAgentEvent Pydantic model | P0 | LOW |
| Add `to_universal_event()` to all connectors | P0 | MEDIUM |
| Add `/api/v1/agent/events` endpoint | P0 | MEDIUM |
| Implement event validation middleware | P0 | MEDIUM |
| Add content hash verification | P1 | LOW |
| Add idempotency check (event_id) | P1 | LOW |
| Implement session/run mapping | P1 | MEDIUM |
| Add Codex connector | P1 | MEDIUM |
| Add streaming event support | P2 | HIGH |
