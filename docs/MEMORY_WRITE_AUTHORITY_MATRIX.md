# Memory Write Authority Matrix
**Phase**: M-ARCH — Memory Architecture Freeze Gate
**Status**: PROPOSED — requires review and approval before implementation
**Created**: 2026-09-10

---

## 1. Purpose

This matrix defines **who may perform which operations on memory objects**.
Leaving this implicit is the most dangerous architectural choice in the current
system — any component with database access can create, modify, or delete memories
without constraint.

---

## 2. Actor Definitions

| Actor | Description |
|-------|-------------|
| **User** | Authenticated human user |
| **Agent** | External agent (Claude Code, Codex) acting on behalf of a user |
| **Pipeline** | M0–M4 ingestion pipeline operating on ingested content |
| **Intelligence Layer** | Future Memory Intelligence Layer (not yet implemented) |
| **Admin** | Workspace/tenant administrator |
| **System** | Automated system processes (expiry, cleanup, consolidation) |

---

## 3. Operation Definitions

| Operation | Description | Side Effects |
|-----------|-------------|-------------|
| **CREATE** | Create a new memory object | Emits `memory.created` audit event, triggers notification |
| **READ** | Retrieve memory content | Emits `memory.read` audit event, no mutation |
| **UPDATE** | Modify content/metadata of existing memory | Emits `memory.updated` audit event, creates provenance entry |
| **SUPERSEDE** | Create new memory that replaces an existing one | Marks old as SUPERSEDED, links via FK, emits `memory.superseded` |
| **INVALIDATE** | Mark memory as known-false | Sets temporal_status=INVALIDATED, emits `memory.invalidated` |
| **DELETE** | Soft-delete memory | Sets status=DELETED, emits `memory.deleted` |
| **ARCHIVE** | Move to archive (excluded from retrieval) | Sets status=ARCHIVED, emits `memory.archived` |
| **RESTORE** | Recover from DELETED or ARCHIVED | Restores to ACTIVE, emits `memory.restored` |
| **CERTIFY** | Promote to CERTIFIED trust level | Sets trust_level=CERTIFIED, emits `memory.certified` |
| **PURGE** | Physically remove (tombstone) | Creates tombstone record, emits `memory.purged` |
| **EXPIRE** | Mark as expired based on time | Sets temporal_status=EXPIRED, emits `memory.expired` |
| **CONTRADICT** | Flag memory as contradicting another | Creates `contradicts` graph edge, emits `memory.contradicted` |

---

## 4. Authority Matrix

| Operation | User | Agent | Pipeline | Intelligence | Admin | System |
|-----------|:----:|:-----:|:--------:|:------------:|:-----:|:------:|
| CREATE | ✅ | ✅ (scoped) | ✅ | ✅ (scoped) | ✅ | ❌ |
| READ | ✅ (own scope) | ✅ (own scope) | ❌ | ✅ (scoped) | ✅ (all) | ❌ |
| UPDATE | ✅ (own) | ❌ | ❌ | ✅ (own lineage) | ✅ (all) | ❌ |
| SUPERSEDE | ✅ (own) | ❌ | ✅ | ✅ | ✅ | ❌ |
| INVALIDATE | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ (automated) |
| DELETE | ✅ (own) | ❌ | ❌ | ❌ | ✅ (all) | ✅ (automated expiry) |
| ARCHIVE | ✅ (own) | ❌ | ❌ | ❌ | ✅ (all) | ✅ (automated) |
| RESTORE | ✅ (own, recent) | ❌ | ❌ | ❌ | ✅ (all) | ❌ |
| CERTIFY | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| PURGE | ❌ | ❌ | ❌ | ❌ | ✅ (retention) | ✅ (retention) |
| EXPIRE | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| CONTRADICT | ❌ | ❌ | ✅ (pipeline) | ✅ | ✅ | ❌ |

**Legend**: ✅ = Allowed, ❌ = Not allowed, (scoped) = Within user/agent scope only

---

## 5. Enforcement Points

### 5.1 API Layer (FastAPI Dependencies)

```python
# app/api/dependencies.py

async def require_memory_write(
    tc: TenantContext,
    memory: Memory,
    db: AsyncSession,
) -> None:
    """Verify caller may modify this specific memory."""
    # 1. Memory must belong to same workspace
    if memory.workspace_id != tc.workspace_id:
        raise HTTPException(403, "Memory not in your workspace")
    # 2. User must be owner or admin
    if memory.user_id != tc.user_id and not tc.is_admin:
        raise HTTPException(403, "Not your memory")
    # 3. Memory must not be DELETED or ARCHIVED
    if memory.status != "active":
        raise HTTPException(409, f"Memory is {memory.status}")
    # 4. Policy engine check
    policy = PolicyEngine()
    result = policy.evaluate(AuthorizationRequest(
        principal=tc.user_id,
        resource=f"memory:{memory.id}",
        action="update",
    ))
    if result.effect != EFFECT_ALLOW:
        raise HTTPException(403, "Policy denied")
```

### 5.2 Service Layer (MemoryService)

```python
# app/services/memory.py

async def supersede(
    self,
    session: AsyncSession,
    memory_id: str,
    new_content: str,
    actor_id: str,
) -> MemoryRecord:
    """Supersede an existing memory with new content."""
    # 1. Load existing memory
    existing = await self._load_from_db(session, memory_id)
    if existing is None:
        raise MemoryNotFoundError(memory_id)
    # 2. Verify actor has permission
    if existing.user_id != actor_id and not self._is_admin(actor_id):
        raise PermissionError("Cannot supersede another user's memory")
    # 3. Create new memory with supersedes link
    new_record = MemoryRecord(
        memory_type=existing.memory_type,
        content=new_content,
        supersedes=memory_id,
        temporal_status="current",
        # ... copy scope fields
    )
    await self._persist_record(session, new_record)
    # 4. Update existing memory
    existing.temporal_status = "superseded"
    existing.superseded_by = new_record.memory_id
    await self._update_record(session, existing)
    # 5. Emit audit event
    self._audit.emit(MEMORY_SUPERSEDED, ...)
    # 6. Return new record
    return new_record
```

### 5.3 Policy Engine (AuthorizationRequest)

```python
# app/services/policy/engine.py

# Memory-specific policies (auto-generated from RBAC)
MEMORY_POLICIES = [
    {
        "actions": ["memory:create"],
        "roles": ["owner", "admin", "member"],
        "effect": "allow",
    },
    {
        "actions": ["memory:supersede"],
        "roles": ["owner", "admin"],
        "effect": "allow",
    },
    {
        "actions": ["memory:invalidate", "memory:certify", "memory:purge"],
        "roles": ["owner", "admin"],
        "effect": "allow",
    },
    {
        "actions": ["memory:delete"],
        "roles": ["owner", "admin"],
        "conditions": ["memory.age_hours < 24"],  # Soft-delete window
        "effect": "allow",
    },
]
```

---

## 6. Scope Rules

| Scope | Who Can Read | Who Can Write | Who Can Admin |
|-------|-------------|---------------|---------------|
| USER | Owner only | Owner only | Owner + Admin |
| TEAM | Team members | Team members | Team lead + Admin |
| PROJECT | Project members | Project members | Project admin + Admin |
| WORKSPACE | Workspace members | Workspace members | Workspace owner + Admin |
| TENANT | All tenant users | Restricted (admin) | Tenant owner only |

---

## 7. Special Rules

### 7.1 Agent Write Limits

External agents (Claude Code, Codex) may CREATE memories but:
- Cannot UPDATE or DELETE memories they didn't create
- Cannot CERTIFY or INVALIDATE
- Cannot supersede memories created by users (only pipeline-superseded)
- All agent-created memories start at UNVERIFIED trust level
- Agent writes are rate-limited (configurable per agent)

### 7.2 Pipeline Write Limits

The M0–M4 pipeline may:
- CREATE facts, decisions, and memory objects
- SUPERSEDE facts (subject+predicate match)
- Mark contradictions (via graph edges)
- Cannot INVALIDATE, CERTIFY, or PURGE

### 7.3 Intelligence Layer Write Limits

The future Intelligence Layer may:
- CREATE synthesized memories (with `derives_from` provenance)
- CERTIFY memories (trust level promotion)
- INVALIDATE memories (with evidence)
- Cannot PURGE or DELETE without admin approval

### 7.4 Memory Safety Gate

Before any CREATE/UPDATE/SUPERSEDE, the following MUST pass:

1. **Scope check**: Memory belongs to caller's accessible scope
2. **Content policy**: Content passes profanity/safety filter
3. **Rate limit**: Caller hasn't exceeded write rate limit
4. **Size limit**: Content ≤ max_size (configurable, default 1MB)
5. **Provenance check**: Source is accessible and verified
6. **Contradiction check**: New content doesn't contradict a CERTIFIED memory without flagging

---

## 8. Current Enforcement State

| Control | Currently Enforced? | Location | Gap |
|---------|---------------------|----------|-----|
| Scope isolation (workspace) | YES | `TenantContext` middleware | — |
| Scope isolation (project) | PARTIAL | Query filters on project_id | Missing on writes |
| RBAC (role-based) | YES | `require_min_role` middleware | — |
| Policy engine | YES | `app/services/policy/` | No memory-specific policies |
| Content size limit | YES | Schema `max_length` | Connector-level only |
| Memory ownership check | PARTIAL | `MemoryService` checks `user_id` | Missing on API routes |
| Agent write authorization | MISSING | — | No agent identity model |
| Intelligence layer authorization | MISSING | — | Layer not implemented |
| Rate limiting on memory writes | PARTIAL | In-memory rate limiter | Per-instance only |
| Content policy filter | MISSING | — | No profanity/safety check |

---

## 9. Implementation Requirements

| Requirement | Priority | Effort |
|-------------|----------|--------|
| Add memory ownership checks to API routes | P1 | MEDIUM |
| Add memory-specific RBAC policies | P1 | MEDIUM |
| Implement agent identity model | P1 | MEDIUM |
| Add content policy filter | P2 | MEDIUM |
| Add rate limiting on memory writes | P2 | LOW |
| Implement CERTIFY/INVALIDATE endpoints | P2 | MEDIUM |
| Add trust level enforcement in retrieval | P1 | MEDIUM |
| Implement Memory Safety Gate | P0 | HIGH |
