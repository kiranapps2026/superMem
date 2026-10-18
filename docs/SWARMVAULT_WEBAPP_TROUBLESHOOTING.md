# SWARMVAULT WEBAPP TROUBLESHOOTING

**Version:** 1.0.0
**Date:** 2026-09-05
**Application Version:** 0.1.0
**Repository SHA:** d970d6b (master)
**Documentation Status:** DRAFT — Based on verified codebase behavior

---

## Table of Contents

1. [Quick Diagnosis](#1-quick-diagnosis)
2. [Connection Issues](#2-connection-issues)
3. [Authentication Problems](#3-authentication-problems)
4. [Chat & Streaming Issues](#4-chat--streaming-issues)
5. [Ingestion Problems](#5-ingestion-problems)
6. [Search & Retrieval Issues](#6-search--retrieval-issues)
7. [Permission & Access Issues](#7-permission--access-issues)
8. [Performance Issues](#8-performance-issues)
9. [Data Issues](#9-data-issues)
10. [Frontend-Specific Issues](#10-frontend-specific-issues)
11. [Backend-Specific Issues](#11-backend-specific-issues)
12. [Integration Issues](#12-integration-issues)
13. [Escalation & Debug Steps](#13-escalation--debug-steps)
14. [Health Check Reference](#14-health-check-reference)

---

## 1. Quick Diagnosis

### 1.1 Is the Backend Running?

```bash
curl -s http://localhost:8000/health/ready
# Expected: {"status": "ok"} or {"detail": "..."}
```

If this fails:
- Start the backend: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Check that PostgreSQL is running and accessible
- Verify environment variables are set

### 1.2 Is the Frontend Running?

```
Open http://localhost:3000 in browser
```

If this fails:
- Start the frontend: `cd frontend && npm run dev`
- Check for port conflicts
- Verify Node.js version (requires Node 18+)

### 1.3 Is the Database Accessible?

```bash
# Check PostgreSQL connection
psql -U sv_user -d sv_db -c "SELECT 1;"
```

### 1.4 Is the LLM Provider Configured?

Check backend logs for LLM initialization messages. If the LLM provider is not configured:
- Chat responses will fail or return errors
- Ingestion pipeline may fail at M5 (retrieval)
- Set `LLM_PROVIDER`, `LLM_API_KEY`, and `LLM_MODEL` environment variables

---

## 2. Connection Issues

### 2.1 "Cannot connect to server"

**Symptoms:** Browser shows "ERR_CONNECTION_REFUSED" or blank page

**Cause:**
- Frontend not running
- Wrong port (frontend on 3000, backend on 8000)
- Firewall blocking ports

**Resolution:**
```bash
# Verify frontend
curl -s http://localhost:3000 | head -5

# Verify backend
curl -s http://localhost:8000/health | head -5

# Check listening ports
netstat -ano | findstr ":3000\|:8000"
```

### 2.2 "CORS error" in browser console

**Symptoms:** Console shows CORS policy violation

**Cause:**
- Frontend origin not in backend CORS allowlist
- Backend `CORS_ORIGINS` environment variable mismatch

**Resolution:**
- Verify backend `CORS_ORIGINS` includes `http://localhost:3000`
- Check that requests include proper `Content-Type` header
- Ensure no proxy stripping CORS headers

### 2.3 "Network Error" on API requests

**Symptoms:** API calls fail silently or show network errors

**Cause:**
- Backend server down
- Wrong API base URL in frontend
- Network/firewall issue

**Resolution:**
```javascript
// Check frontend config
console.log(process.env.NEXT_PUBLIC_API_URL);
// Should be http://localhost:8000
```

---

## 3. Authentication Problems

### 3.1 "Cannot log in" — 500 error

**Symptoms:** Login returns HTTP 500

**Possible causes (verified from codebase):**

| Cause | Indicator | Resolution |
|-------|-----------|------------|
| Password hash mismatch | Backend log shows bcrypt error | Verify password is correct |
| User disabled | `is_active = false` in DB | Admin must reactivate |
| Database error | DB connection failed | Check PostgreSQL status |
| Registration conflict | Duplicate email | Use different email |

**Debug steps:**
```bash
# Check backend logs for details
tail -f /var/log/swarmvault/backend.log

# Verify user exists
psql -U sv_user -d sv_db -c "SELECT id, email, is_active FROM users WHERE email = 'user@example.com';"
```

### 3.2 "Session expired" — frequent re-login

**Symptoms:** User keeps getting redirected to login

**Causes:**
| Cause | Resolution |
|-------|------------|
| Access token expired (60 min) | Client auto-refreshes; check refresh token validity |
| Refresh token expired (30 days) | Re-login required |
| localStorage cleared | Check browser privacy settings |
| Clock skew | Ensure server and client clocks are synchronized |

### 3.3 "401 Unauthorized" on API calls

**Symptoms:** API calls return 401

**Resolution:**
1. Check if token exists in localStorage:
   ```javascript
   const tokens = localStorage.getItem('sv_tokens');
   console.log(tokens ? JSON.parse(tokens) : 'No tokens found');
   ```
2. Verify token format: `Bearer eyJ...`
3. Check if token is expired (decode JWT, check `exp` claim)

### 3.4 "403 Forbidden" — Insufficient permissions

**Symptoms:** API returns 403

**Causes:**
| Cause | Resolution |
|-------|------------|
| Wrong role | Check user role in workspace |
| Cross-workspace access | Verify workspace membership |
| Policy engine rejection | Check policy rules in DB |

**Debug:**
```bash
# Check user role
psql -U sv_user -d sv_db -c "
  SELECT u.email, wm.role, w.name
  FROM users u
  JOIN workspace_members wm ON wm.user_id = u.id
  JOIN workspaces w ON w.id = wm.workspace_id
  WHERE u.email = 'user@example.com';
"
```

---

## 4. Chat & Streaming Issues

### 4.1 "Chat not responding"

**Symptoms:** Send button has no effect, no response

**Causes:**
| Cause | Check | Resolution |
|-------|-------|------------|
| Backend down | `/health/ready` | Start backend |
| LLM provider unreachable | Backend logs | Check LLM_API_KEY and provider URL |
| No memories ingested | Memory page empty | Ingest sources first |
| SSE connection failure | Network tab | Check CORS, Content-Type headers |

### 4.2 "Streaming response is broken"

**Symptoms:** Partial response, garbled text, or no streaming

**Causes:**
| Cause | Resolution |
|-------|------------|
| SSE format error | Ensure backend sends `data: {json}\n\n` |
| Client parsing error | Check browser console for parse errors |
| Proxy buffering SSE | Configure proxy to pass through SSE |
| Content-Type mismatch | Server must return `text/event-stream` |

### 4.3 "Sources not showing in chat"

**Symptoms:** Chat responds but no sources panel

**Causes:**
| Cause | Resolution |
|-------|------------|
| No relevant memories | Ingest more content |
| Low relevance scores | Adjust search threshold |
| M5 retrieval not configured | Check retrieval settings |

### 4.4 SSE Event Reference

| Event | When | Data |
|-------|------|------|
| `sources` | Before text generation | Memory references with scores |
| `token` | During text generation | Text chunk |
| `done` | After completion | Message ID, session ID, usage, latency |
| `error` | On error | Error detail string |

---

## 5. Ingestion Problems

### 5.1 "Ingestion fails with 400"

**Symptoms:** Upload returns 400 Bad Request

**Causes:**
| Cause | Resolution |
|-------|------------|
| Wrong `source_type` | Match format to type (see table) |
| Missing `project_id` | Include valid project ID |
| Empty content | Provide non-empty content string |
| Invalid JSONL | Check JSONL line format |

### 5.2 "Ingestion stuck on 'Processing'"

**Symptoms:** Source shows "Processing" indefinitely

**Causes:**
| Cause | Resolution |
|-------|------------|
| Large file | Wait longer; check processing logs |
| Backend worker crashed | Check backend logs for crash |
| Database deadlock | Restart backend, check DB locks |

**Debug:**
```bash
# Check source status
psql -U sv_user -d sv_db -c "
  SELECT id, source_type, status, message_count
  FROM ingest_sources
  WHERE project_id = '<project-uuid>'
  ORDER BY created_at DESC;
"
```

### 5.3 "No knowledge extracted after ingestion"

**Symptoms:** Source shows "completed" but memory/facts empty

**Causes:**
| Cause | Resolution |
|-------|------------|
| Insufficient conversation data | Need meaningful conversation content |
| Connector didn't match | Verify `source_type` matches format |
| Pipeline error (M1-M5) | Check backend logs for pipeline errors |

### 5.4 Supported Format Reference

| Format | `source_type` | Expected Structure |
|--------|---------------|-------------------|
| ChatGPT | `chatgpt` | JSON with `mapping` |
| Claude | `claude` | JSON with `chat_messages` |
| Claude Code | `claude-code` | JSONL with events |
| Generic | `json` | Array of `{role, content}` |
| JSONL | `jsonl` | Line-delimited JSON |
| Markdown | `markdown` | `.md` text |
| Plain text | `text` | Raw text |

---

## 6. Search & Retrieval Issues

### 6.1 "Search returns no results"

**Symptoms:** Empty results despite having content

**Causes:**
| Cause | Resolution |
|-------|------------|
| No ingested content | Ingest sources first |
| No memory items | Wait for M0-M5 pipeline to complete |
| Query too specific | Try broader terms |
| Project mismatch | Verify correct project selected |

### 6.2 "Search returns irrelevant results"

**Symptoms:** Results don't match query

**Causes:**
| Cause | Resolution |
|-------|------------|
| Limited ingested data | Ingest more content |
| Poor quality source data | Verify source content quality |
| Low confidence threshold | Review confidence scores |

---

## 7. Permission & Access Issues

### 7.1 "Cannot access project"

**Symptoms:** 403 or 404 when accessing project

| Error | Meaning | Resolution |
|-------|---------|------------|
| 403 | Not a member of the workspace | Request invitation |
| 404 | Project doesn't exist or deleted | Verify project ID |
| 403 | Insufficient role | Request admin upgrade |

### 7.2 "Cannot delete memory"

**Symptoms:** Delete fails with 403

**Cause:** Memory deletion requires Owner role only

**Resolution:**
- Ask workspace Owner to delete
- Or have Owner transfer ownership

### 7.3 "Cannot invite members"

**Symptoms:** Invite button disabled or returns 403

**Cause:** Only Owner and Admin roles can invite members

**Resolution:**
- Ask Owner/Admin to send invitation

---

## 8. Performance Issues

### 8.1 "Slow API responses"

**Symptoms:** API calls take >5 seconds

**Possible causes:**
| Cause | Investigation | Resolution |
|-------|---------------|------------|
| Database query slow | Check query plans, indexes | Add indexes, optimize queries |
| LLM latency | Check provider dashboard | Switch to faster model |
| Large payloads | Check request/response sizes | Paginate, limit results |
| No connection pooling | Check DB connection count | Increase pool size |

### 8.2 "Frontend is slow"

**Symptoms:** UI lag, slow navigation

**Causes:**
| Cause | Resolution |
|-------|------------|
| Large project (1000+ items) | Implement pagination |
| Many SSE connections | Close unused connections |
| No React memoization | Profile and optimize re-renders |
| Large bundle | Check Next.js bundle analysis |

### 8.3 "Search is slow"

**Symptoms:** Search takes >3 seconds

**Causes:**
| Cause | Resolution |
|-------|------------|
| No vector index | Ensure pgvector extension and indexes exist |
| Large corpus | Implement result limits |
| Complex semantic search | Cache frequent queries |

---

## 9. Data Issues

### 9.1 "Data disappeared after restart"

**Symptoms:** Projects/memories missing after server restart

**Causes:**
| Cause | Resolution |
|-------|------------|
| Using SQLite without persistence | Ensure volume mapping in Docker |
| Database not initialized | Run migrations: `alembic upgrade head` |
| Wrong database URL | Check `DATABASE_URL` environment variable |

### 9.2 "Duplicate items after re-ingestion"

**Symptoms:** Same content appears multiple times

**Resolution:**
- This is expected behavior if content hash differs (e.g., different titles)
- System deduplicates by content hash; different metadata = new source

### 9.3 "Old knowledge persisting"

**Symptoms:** Superseded knowledge still showing in results

**Cause:** M3 temporal truth processing marks items as superseded but doesn't delete them

**Resolution:**
- Toggle temporal filters in UI
- Or purge superseded items (requires direct DB access)

---

## 10. Frontend-Specific Issues

### 10.1 "Blank page after login"

**Symptoms:** Login succeeds but page is blank

**Causes:**
| Cause | Resolution |
|-------|------------|
| JavaScript error | Check browser console |
| Route mismatch | Verify routing configuration |
| AuthProvider not wrapping | Check layout.tsx structure |

### 10.2 "Sidebar not collapsing"

**Symptoms:** Hamburger button doesn't work

**Causes:**
| Cause | Resolution |
|-------|------------|
| CSS issue | Check for conflicting styles |
| State not updating | Check sidebar state management |
| Mobile detection | Verify window width > 768px |

### 10.3 "Form submissions not working"

**Symptoms:** Clicking submit has no effect

**Causes:**
| Cause | Resolution |
|-------|------------|
| API call failing silently | Check browser Network tab |
| Missing event handler | Verify `onSubmit` handler exists |
| CORS preflight failure | Check OPTIONS request |

### 10.4 "TypeScript errors in development"

**Symptoms:** Build warnings or runtime type errors

**Resolution:**
- Run `npm run typecheck` in frontend directory
- Verify `types/api.ts` matches backend response schemas
- Check for missing type imports

---

## 11. Backend-Specific Issues

### 11.1 "Database connection pool exhausted"

**Symptoms:** 503 errors, "Connection pool is full"

**Resolution:**
- Check `DATABASE_POOL_SIZE` (default: 20)
- Check for connection leaks (unclosed sessions)
- Monitor with: `SELECT count(*) FROM pg_stat_activity;`

### 11.2 "Migration fails"

**Symptoms:** `alembic upgrade head` fails

**Resolution:**
```bash
# Check current migration state
alembic current

# If DB is empty, stamp it
alembic stamp head

# If partial, check for conflicts
alembic history --verbose
```

### 11.3 "Rate limit errors"

**Symptoms:** 429 responses on valid requests

**Resolution:**
- Wait for rate limit window (60 seconds)
- Check `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW` config
- In development, pass `X-E2E: true` header to bypass

### 11.4 "Policy engine blocking requests"

**Symptoms:** 403 from policy engine

**Causes:**
| Cause | Resolution |
|-------|------------|
| Policy table empty | Run policy seed migration |
| Policy rule misconfigured | Check `policies` table |
| Database error during policy check | Fail-closed: check DB health |

---

## 12. Integration Issues

### 12.1 "MCP server not connecting"

**Symptoms:** Cannot connect to SwarmVault from MCP client

**Causes:**
| Cause | Resolution |
|-------|------------|
| API key invalid | Verify key exists and is not revoked |
| CORS blocking | Add MCP client origin to CORS_ORIGINS |
| Network unreachable | Check firewall and proxy settings |
| Wrong endpoint | Verify `SWARMVAULT_URL` in MCP config |

### 12.2 "File upload failing"

**Symptoms:** Upload returns error or stalls

**Causes:**
| Cause | Resolution |
|-------|------------|
| File too large | Check 50MB limit |
| Wrong content type | Verify multipart/form-data |
| Disk full | Check server disk space |
| Permission denied | Check file system permissions |

### 12.3 "Chat streaming disconnects"

**Symptoms:** SSE connection drops mid-response

**Causes:**
| Cause | Resolution |
|-------|------------|
| Proxy timeout | Increase proxy timeout for SSE |
| LLM timeout | Check provider timeout settings |
| Network interruption | Implement reconnection logic |
| Backend crash | Check backend logs |

---

## 13. Escalation & Debug Steps

### 13.1 Frontend Debug

```bash
# 1. Check browser console for JavaScript errors
# Open DevTools → Console tab

# 2. Check Network tab for failed requests
# Look for non-2xx status codes

# 3. Check localStorage for tokens
localStorage.getItem('sv_tokens')

# 4. Verify API base URL
console.log(process.env.NEXT_PUBLIC_API_URL)

# 5. Check React DevTools for component state
```

### 13.2 Backend Debug

```bash
# 1. Check backend logs
tail -f /var/log/swarmvault/backend.log

# 2. Verify database connection
psql -U sv_user -d sv_db -c "SELECT 1;"

# 3. Check migration status
alembic current

# 4. Verify environment variables
env | grep -E "DATABASE|LLM|REDIS|CORS"

# 5. Test API directly
curl -s http://localhost:8000/health/ready
curl -s http://localhost:8000/health/live

# 6. Check active connections
psql -U sv_user -d sv_db -c "SELECT * FROM pg_stat_activity;"
```

### 13.3 Database Debug

```sql
-- Check user accounts
SELECT id, email, is_active, created_at FROM users;

-- Check workspace membership
SELECT u.email, w.name, wm.role
FROM workspace_members wm
JOIN users u ON u.id = wm.user_id
JOIN workspaces w ON w.id = wm.workspace_id;

-- Check source processing status
SELECT id, source_type, status, message_count, created_at
FROM ingest_sources
ORDER BY created_at DESC
LIMIT 20;

-- Check memory items
SELECT id, memory_type, temporal_status, confidence_score, created_at
FROM memories
WHERE project_id = '<uuid>'
LIMIT 20;

-- Check for pending migrations
SELECT * FROM alembic_version;
```

---

## 14. Health Check Reference

### 14.1 Health Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `GET /health/live` | Liveness probe | `{"status": "alive"}` |
| `GET /health/ready` | Readiness probe | `{"status": "ok"}` or `{"detail": "..."}` |
| `GET /health/health` | General health | Status details |

### 14.2 Full Health Check Script

```bash
#!/bin/bash
# swarmvault-healthcheck.sh

echo "=== SwarmVault Health Check ==="

echo "1. Backend liveness..."
curl -sf http://localhost:8000/health/live && echo " OK" || echo " FAIL"

echo "2. Backend readiness..."
curl -sf http://localhost:8000/health/ready && echo " OK" || echo " FAIL"

echo "3. Database connectivity..."
psql -U sv_user -d sv_db -c "SELECT 1;" && echo " OK" || echo " FAIL"

echo "4. Frontend..."
curl -sf http://localhost:3000 > /dev/null && echo " OK" || echo " FAIL"

echo "5. API authentication..."
TOKEN=$(curl -sf -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
if [ -n "$TOKEN" ]; then
  echo " OK"
  echo "6. API projects endpoint..."
  curl -sf http://localhost:8000/api/v1/projects \
    -H "Authorization: Bearer $TOKEN" && echo " OK" || echo " FAIL"
else
  echo " FAIL"
fi

echo "=== Health Check Complete ==="
```

### 14.3 Common Port Reference

| Service | Port | Check Command |
|---------|------|---------------|
| Frontend | 3000 | `curl -s http://localhost:3000` |
| Backend | 8000 | `curl -s http://localhost:8000/health/live` |
| PostgreSQL | 5432 | `nc -zv localhost 5432` |
| Redis (optional) | 6379 | `nc -zv localhost 6379` |

### 14.4 Log Locations

| Component | Log Location | Check Command |
|-----------|-------------|---------------|
| Backend | Console / stdout | `docker logs swarmvault-backend` |
| Frontend | Console / stdout | `docker logs swarmvault-frontend` |
| PostgreSQL | `/var/log/postgresql/` | `tail -f /var/log/postgresql/*.log` |
| Nginx (if used) | `/var/log/nginx/` | `tail -f /var/log/nginx/error.log` |
