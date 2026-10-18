# SwarmVault WebApp — SSE / Chat Contract
**Release:** `0534efe426e42f9c03f1622dd792f052647038cc`
**Endpoint:** `POST /api/v1/chat/stream`
**Content-Type:** `text/event-stream`
**Status:** FROZEN

---

## Connection

```
POST /api/v1/chat/stream
Headers:
  Authorization: Bearer <access_token>
  Content-Type: application/json
  Accept: text/event-stream

Body:
{
  "message": "string (required, min 1 char)",
  "session_id": "string | null (optional — creates new if omitted)",
  "project_id": "string | null (optional)"
}

Response: 200 OK with text/event-stream body
```

## Event Format

Events are sent as Server-Sent Events. Each event has a `type` field that determines the payload structure.

### Event: `sources`

Retrieved memory sources sent at the beginning of the stream, before any tokens.

```json
{
  "type": "sources",
  "sources": [
    {
      "memory_id": "uuid",
      "content": "source content preview",
      "memory_type": "episodic_memory",
      "confidence": 0.85,
      "authority": 0.9,
      "temporal_status": "current",
      "project_id": "uuid"
    }
  ]
}
```

**Frontend behavior:** Render source cards before streaming text begins. If `sources` is empty array `[]`, display "No sources found."

### Event: `token`

Incremental text chunk. May arrive as full words, partial words, or single characters depending on the LLM provider.

```json
{
  "type": "token",
  "content": "partial or complete text chunk"
}
```

**Frontend behavior:** Append `content` to the displayed response. Do NOT wait for the full response before showing anything — render incrementally.

### Event: `done`

Stream completion. Sent exactly once per successful stream.

```json
{
  "type": "done",
  "message_id": "uuid",
  "session_id": "uuid",
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 200
  },
  "latency_ms": 1500,
  "memory_grounded": true
}
```

**Frontend behavior:** Finalize the displayed message. Store `message_id` for feedback. Hide loading state.

### Event: `error`

Fatal error. Sent instead of `done` when the stream cannot complete.

```json
{
  "type": "error",
  "detail": "An internal error occurred"
}
```

**Frontend behavior:** Display error to user. Allow retry. The `detail` field is sanitized — no stack traces, no internal paths, no secrets.

---

## State Machine

```
Client connects
  → sources (may be empty)
  → token (zero or more)
  → done | error
  → connection closes
```

## Frontend Implementation Guide

### Using EventSource (NOT compatible — POST required)

`EventSource` only supports GET. This endpoint requires POST with a body. Use `fetch()` with a `ReadableStream` reader instead.

```typescript
const response = await fetch('/api/v1/chat/stream', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ message, session_id, project_id }),
});

const reader = response.body.getReader();
const decoder = new TextDecoder();
let buffer = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split('\n');
  buffer = lines.pop() || '';

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6));
      handleEvent(event);
    }
  }
}
```

### Event Handling

```typescript
function handleEvent(event: ChatEvent) {
  switch (event.type) {
    case 'sources':
      renderSources(event.sources);  // Show source cards
      break;
    case 'token':
      appendToken(event.content);    // Append to response text
      break;
    case 'done':
      finalizeMessage(event);        // Save message_id, hide loading
      break;
    case 'error':
      showError(event.detail);       // Display sanitized error
      break;
  }
}
```

### Cancellation

The frontend can cancel by aborting the fetch:

```typescript
const controller = new AbortController();
const response = await fetch(url, { signal: controller.signal });
// To cancel:
controller.abort();
```

Server-side: disconnect triggers cleanup. No partial message is persisted unless the stream completed.

### Retry

On error or network failure:
1. Do NOT automatically retry (prevents duplicate messages)
2. Show retry button to user
3. Re-submit with same `session_id` if user wants to retry

### SSE Browser Compatibility

| Browser | Support |
|---------|---------|
| Chrome | Full |
| Firefox | Full |
| Safari | Full |
| Edge | Full |

No polyfills required for modern browsers.

## CONTRACT GAPS

| Gap | Severity | Detail |
|------|----------|--------|
| No RBAC on `/chat/stream` | P1 | Any authenticated workspace member can stream, while `/chat/` requires viewer role |
| No cancel token in stream | P3 | Client must use AbortController; no server-side cancel endpoint |
| No message deduplication on retry | P3 | If frontend retries without user action, duplicate messages may be created |
| No stream timeout documentation | P2 | Frontend cannot determine appropriate timeout — recommend 120s for normal, 300s for long |
