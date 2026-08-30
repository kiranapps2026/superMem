# Consolidated Features Reference

> Mem0 memory platform · SwarmVault workspace management
> Last updated: 2026-08-30

---

## 1. Mem0 — Memory Platform

### 1.1 Memory Types

| Type | Enum Value | Status | Availability |
|---|---|---|---|
| Procedural memory | `procedural_memory` | Implemented | Python OSS only (`Memory`/`AsyncMemory`); requires `agent_id` |
| Semantic memory | `semantic_memory` | Not implemented | Defined in enum, rejected by validation |
| Episodic memory | `episodic_memory` | Not implemented | Defined in enum, rejected by validation |

> **Only `procedural_memory` is a real, working value.** Omitting `memory_type` stores messages as ordinary memory — there is no semantic/episodic pathway.

### 1.2 Memory Scoping Identifiers

| Identifier | Scope | Notes |
|---|---|---|
| `user_id` | Person or account | Required on `add()` |
| `agent_id` | Agent or assistant persona | Required for procedural memory |
| `run_id` | Session, task, or conversation thread | Optional; narrows scope further |
| `app_id` | Application or tenant | Platform only |

At least one identifier is required on `add()`. Passing more narrows scope further (e.g., `user_id` + `run_id`).

### 1.3 Core Operations

| Operation | Method | Description |
|---|---|---|
| Add Memory | `add(messages, user_id, ...)` | Extract + store facts from conversations |
| Search Memory | `search(query, filters)` | Semantic vector search with filters |
| Get All | `get_all(filters, page)` | Paginated retrieval with filters |
| Get One | `get(memory_id)` | Fetch a single memory by ID |
| Update | `update(memory_id, text, ...)` | Update text, metadata, or expiration |
| Delete | `delete(memory_id)` | Remove a single memory |
| Batch Delete | `batch_delete([ids])` | Remove up to 1,000 memories |
| Delete All | `delete_all(filters)` | Filter-based bulk deletion |
| History | `history(memory_id)` | Get history of a specific memory |
| Users | `users()` | List all users, agents, and runs with memories |
| Reset | `reset()` | Delete all users and memories |
| Feedback | `feedback(memory_id, feedback, reason)` | Positive/negative feedback on a memory |
| Create Export | `create_memory_export()` | Structured export with Pydantic schemas |
| Get Export | `get_memory_export()` | Retrieve export results by ID or filters |
| Project Update | `project.update()` | Update custom categories and instructions |
| Project Get | `project.get()` | Retrieve project details |

### 1.4 Add Memory Details

**Platform (`MemoryClient`):**
- Async by default — returns `{"event_id": "...", "status": "PENDING"}`
- Poll `GET /v1/event/{event_id}/` to confirm completion
- Automatic conversation context: pulls prior messages by scope automatically

**OSS (`Memory` / `AsyncMemory`):**
- Synchronous or async
- `infer=True` (default) — LLM extraction pipeline
- `infer=False` — raw message storage without extraction
- `expiration_date` — format `YYYY-MM-DD`, UTC evaluated, inclusive of date itself
- `metadata` — optional dict for filtering (e.g., `{"category": "movie_recommendations"}`)

**Extraction Pipeline** (when `infer=True`):
1. Context gathering — pulls recent messages already stored for the same scope
2. Existing memory retrieval — vector search for candidates that might need changes
3. Extraction — single LLM call decides ADD, UPDATE, DELETE, or leave alone per fact
4. Entity extraction — named entities (people, places, orgs) linked across memories

**Storage model:** ADD-only. New memories accumulate; nothing overwrites or is deleted by the pipeline (explicit `delete`/`update` calls are the exception).

### 1.5 Search & Retrieval

| Feature | Notes |
|---|---|
| Vector search | Cosine similarity across scoped dataset |
| Multi-signal retrieval | Semantic + BM25 + entity boost + temporal reasoning (fused into combined `score`) |
| Reranking | `rerank=True`; deep semantic reordering; ~150-200ms latency; improves top-N precision |
| Filter logic | `AND`/`OR`/`NOT` with comparison operators |
| Metadata filters | Combine entity IDs + metadata in same dict |
| Date filtering | `gt`, `gte`, `lt`, `lte` on `created_at`, `updated_at`, `timestamp`, `expiration_date` |
| Category filtering | `in`, `contains` on `categories` |
| Keyword filtering | `contains`, `icontains` on `keywords` (OSS only; not inside `search()`) |
| Wildcard filtering | `"*"` for non-null matches |
| Score explanation | `explain=True` — returns `score_details` with semantic + BM25 + entity breakdown |
| `top_k` | 1-1000, default 10 |
| `threshold` | Default 0.1; pass 0.0 to disable |
| Temporal Reasoning | Time-aware queries; default on in Platform v3 |
| `memory_ids` filter | Fetch specific memory IDs |
| `show_expired` | Include expired memories in search/get_all |

### 1.6 Memory Filters

| Field Category | Fields | Operators |
|---|---|---|
| Entity | `user_id`, `agent_id`, `app_id`, `run_id` | `eq`, `ne`, `in`, `*` |
| Time | `created_at`, `updated_at`, `timestamp`, `expiration_date` | `gt`, `gte`, `lt`, `lte`, `ne`, `in` |
| Content | `categories`, `metadata`, `keywords` | `in`, `contains`, `eq`, `ne`, `icontains` |
| Special | `memory_ids` | `in` |
| Logical | — | `AND`, `OR`, `NOT` (nestable) |

> Flat filter syntax (sibling keys implicitly ANDed). No `nin` operator on Platform (OSS only).

### 1.7 Memory Expiration

- `expiration_date` on `add()` and `update()` — hides from `search()`/`get_all()` after date
- `get(memory_id)` still returns expired memories
- `show_expired`/`showExpired` parameter to include expired
- Clear with `expiration_date=None` (Python) / `expirationDate: null` (JS)
- Inclusive of the date itself (expires the next day)
- Malformed dates fail open (never silently vanish)

### 1.8 Memory Decay (Platform Only)

- Re-ranks results by how recently a memory was used (older = lower score)
- Does **not** filter results — only reorders
- Per-project, opt-in, reversible

### 1.9 Custom Categories

- Default catalog: 15 categories (`personal_details`, `family`, `professional_details`, `sports`, `travel`, `food`, `music`, `health`, `technology`, `hobbies`, `fashion`, `entertainment`, `milestones`, `user_preferences`, `misc`)
- Project-level override via `project.update(custom_categories=[...])`
- Per-call override via `custom_categories` parameter on `add()`
- Priority: per-call > project > built-in defaults
- Applied at ingestion time only (no re-tagging of existing memories)

### 1.10 Feedback Mechanism (Platform)

| Feedback Type | Meaning |
|---|---|
| `POSITIVE` | Memory is useful |
| `NEGATIVE` | Memory is not useful |
| `VERY_NEGATIVE` | Memory is not useful at all |

- `feedback_reason` — optional explanation
- Remove feedback by passing `None`/`null`
- Bulk: loop over list of `{memory_id, feedback, feedback_reason}` dicts
- Error: malformed `memory_id` → `400`; non-existent/unauthorized → `500` (known bug MEM-5745)
- Only call `feedback` with `memory_id` from a recent `get_all` or `search` response

### 1.11 Memory Evaluation

| Benchmark | Description |
|---|---|
| **LoCoMo** | Long-conversation memory benchmark |
| **LongMemEval** | Long-term memory evaluation |
| **BEAM** | 1M and 10M token scales |

- Token efficiency: mean ~7K tokens/query vs 25K+ for full-context
- Open-source framework (`memory-benchmarks` repo)
- `--predict-only`, `--evaluate-only`, `--resume` modes
- Web UI for per-question results
- Multi-cutoff evaluation (`top_k-cutoffs`: 10, 20, 50, 200)

### 1.12 Async Client

- `AsyncMemoryClient` — non-blocking operations (Python `await`, JS `async/await`)
- Methods: `add`, `search`, `get_all`, `get`, `delete`, `delete_all`, `history`, `users`, `reset`, `feedback`
- `delete_all` requires at least one filter

### 1.13 Memory Export

- Structured export using Pydantic-compatible JSON schemas
- `create_memory_export(schema, filters, export_instructions)` — submit export job
- `get_memory_export(memory_export_id)` — retrieve results
- `export_instructions` — LLM guidance for schema population
- Schema supports `$defs`, enums, `anyOf`, `minLength`/`maxLength`, nullable fields
- Filters: `user_id`, `agent_id`, `run_id`, `created_at`
- Returns structured JSON matching the schema

### 1.14 Entity-Scoped Memory

- Four-dimensional scoping: User, Agent, Application, Run
- `app_id` for tenant/white-label separation (Platform)
- Extraction attribution: `user_id` or `agent_id` (not both) on default path
- Direct Import (`infer=False`) writes both fields on one record
- Consistent identifier formats for group operations

### 1.15 Group Chat

- Multi-participant conversations scoped per speaker
- **`name` field does NOT change scope** — extraction context only
- Call `add()` once per participant with their own `user_id` for separate memory profiles
- Shared `run_id` ties all participants to one session
- Filter by `run_id` + wildcard `user_id` to get all participants
- Works with both Platform and OSS
- Message roles: `user` (human), `assistant` (AI), `agent`
- Use cases: team meetings, customer support, multi-agent systems, collaborative projects

### 1.16 Platform vs OSS

| Capability | Platform | OSS |
|---|---|---|
| Add behavior | ADD-only, async with `event_id` | ADD-only, you control storage |
| Rate limits | Managed quotas | Limited by hardware/provider APIs |
| Dashboard | Yes | CLI/logs/custom UI |
| Entity graph | Queryable | Ranking-only |
| Reranking | Managed catalog | Requires local/third-party config |
| Filter syntax | Full logical operators | Basic + Python hooks |
| `nin` operator | Not available | Available |
| `app_id` | Supported | Not available |
| Temporal Reasoning | On by default | Available |
| Custom categories | Project + per-call | Per-call only |
| Memory decay | Supported | Not available |
| Memory export | Supported | Not available |
| Feedback | Supported | Not available |
| Graph memory | Built-in, automatic | Ranking-only |
| MCP Server | `mem0-mcp` | Not available |

### 1.17 V2 → V3 Migration Changes

| What Changed | Before | After |
|---|---|---|
| Extraction | Two LLM passes (extract + merge) | Single-pass ADD-only |
| Memory mutations | ADD, UPDATE, DELETE | ADD only |
| Agent-generated facts | Often ignored | First-class |
| Graph memory | External graph store (Neo4j) | Built-in, automatic |
| Retrieval | Semantic only | Hybrid (semantic + BM25 + entity + temporal) |

| Metric | Before | After |
|---|---|---|
| LoCoMo Overall | 71.4 | 91.6 (+20.2) |
| LongMemEval Overall | 67.8 | 93.4 (+25.6) |
| Extraction latency (p50) | ~2.0s | ~1.0s |
| Mean tokens per query | N/A | 6.8-7.0K |

**SDK Breaking Changes:** Removed `org_id`, `project_id`, `api_version`, `output_format`, `async_mode`, `enable_graph`, `immutable`, `filter_memories`, `batch_size`, `force_add_only`, `includes`, `excludes`, `keyword_search`, `org_name`, `project_name` (Python); all parameters now camelCase with equivalents removed (TypeScript).

---

## 2. SwarmVault — Workspace Management

Base URL: `https://api.fast.io/current/`
Auth: Bearer JWT token
IDs: 19-digit numeric strings

### 2.1 Workspace CRUD

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/org/{org_id}/create/workspace/` | JWT + Org Member+ | Create workspace (becomes owner) |
| `GET` | `/workspace/{id}/details/` | JWT + Member+ | Get full workspace details |
| `POST` | `/workspace/{id}/update/` | JWT + Admin+ | Update settings |
| `DELETE` | `/workspace/{id}/delete/?confirm={name_or_id}` | JWT + Owner + 2FA | Soft-delete workspace |
| `POST` | `/workspace/{id}/archive/` | JWT + Admin+ + 2FA | Archive workspace |
| `POST` | `/workspace/{id}/unarchive/` | JWT + Admin+ + 2FA | Unarchive workspace |

**Create request fields:** `folder_name` (required, regex `^[\p{L}\p{N}-]+$`, globally unique), `name` (required, 2-100 chars), `description` (optional, 10-1000 chars), `perm_join` (required), `perm_member_manage` (required), `intelligence` (optional, defaults "true"), `accent_color` (JSON), `background_color1` (JSON), `background_color2` (JSON).

**Create response:** `{"result": true, "workspace": {"id": "...", "folder_name": "..."}}`

**Update request fields (all optional):** `folder_name`, `name`, `description`, `perm_join`, `perm_member_manage`, `intelligence`, `accent_color`, `background_color1`, `background_color2`, `owner_defined` (JSON). Send `"null"` or `""` to clear text fields.

### 2.2 Workspace Discovery

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/workspaces/all/` | List all accessible workspaces |
| `GET` | `/workspaces/available/` | List joinable workspaces |
| `GET` | `/workspaces/check/name/{name}/` | Check folder name availability |
| `GET` | `/org/{org_id}/list/workspaces/` | List workspaces in an org |

**Compact response levels** (`?output=` query param):
| Level | Fields |
|---|---|
| `terse` | id, name, folder_name, org_domain, user_status |
| `standard` | terse + description, lifecycle flags, storage, branding, intelligence, capabilities |
| `full` | standard + cloud_import, comments, chat, search, assets, perm_* blocks, platform, suspended |
| `markdown` | Add `,markdown` modifier for GitHub-flavored Markdown response |

### 2.3 Workspace Assets

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/workspace/assets/` | JWT | List available asset types |
| `GET` | `/workspace/{id}/assets/` | JWT + Owner + 2FA | List workspace assets |
| `POST` | `/workspace/{id}/assets/{name}/` | JWT + Admin+ | Upload/set asset (multipart/form-data) |
| `DELETE` | `/workspace/{id}/assets/{name}/` | JWT + Admin+ | Delete asset |
| `GET` | `/workspace/{id}/assets/{name}/read/` | JWT + Member + 2FA | Download binary |
| `HEAD` | `/workspace/{id}/assets/{name}/read/` | JWT + Member + 2FA | Get metadata headers |

**Upload body:** `file` (required, multipart), `metadata` (optional JSON array string)

### 2.4 Workspace Members

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/workspace/{id}/members/{email_or_user_id}/` | JWT + perm_member_manage | Add member or send invitation |
| `DELETE` | `/workspace/{id}/members/{user_id}/` | JWT + perm_member_manage | Remove member (cannot remove owner) |
| `GET` | `/workspace/{id}/members/list/` | JWT + Member | List all members |
| `DELETE` | `/workspace/{id}/member/` | JWT | Leave workspace (self; owners must transfer first) |
| `GET` | `/workspace/{id}/member/{member_id}/details/` | JWT + Member | Get member details |
| `POST` | `/workspace/{id}/member/{member_id}/update/` | JWT + perm_member_manage | Update role, notifications, expiration |
| `POST` | `/workspace/{id}/member/{member_id}/transfer_ownership/` | JWT + Owner | Transfer ownership (current→admin) |
| `POST` | `/workspace/{id}/members/join/` | JWT | Self-join by org membership |
| `POST` | `/workspace/{id}/members/join/{key}/{action}/` | JWT | Join via invitation (accept/decline) |

**Add member params (by user ID):** `permissions` (admin/member/guest), `notifications`, `expires` (YYYY-MM-DD HH:MM:SS UTC), `force_notification`
**Add member params (by email/invite):** `permissions`, `message`, `invitation_expires`
**Update member params:** `permissions`, `notifications`, `expires`

### 2.5 Workspace Invitations

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/workspace/{id}/members/invitations/list/` | JWT + Member | List all invitations |
| `GET` | `/workspace/{id}/members/invitations/list/{state}/` | JWT + Member | List by state (pending/accepted/declined/expired/revoked) |
| `POST` | `/workspace/{id}/members/invitation/{invitation_id}/` | JWT + perm_member_manage | Update invitation (by ID or email) |
| `DELETE` | `/workspace/{id}/members/invitation/{invitation_id}/` | JWT + perm_member_manage | Delete/revoke invitation (by ID or email) |

**Update invitation params:** `state`, `permissions`, `expires`

### 2.6 Workspace Shares

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/workspace/{id}/create/share/` | JWT + Admin+ | Create a share |
| `GET` | `/workspace/{id}/list/shares/` | JWT + View+ | List shares (query `archived=true/false`) |
| `POST` | `/workspace/{id}/import/share/{share_id}/` | JWT + Member + Share Owner | Import user-owned share to workspace |

**Create share params:** `intelligence` (required), `share_type` (send/receive/exchange), `access_options`, `invite` (owners/guests), `storage_mode` (independent/workspace_folder), `folder_node_id`, `create_folder`, `folder_name`, `title`, `description`, `custom_name`, `password`, `expires`, `notify`, `comments_enabled`, `download_security`, `guest_chat_enabled`, `accent_color`, `background_color1`, `background_color2`, `owner_defined`

**Access options:** "Only members of the Share or Workspace" (default), "Members of the Share, Workspace or Org", "Anyone with a registered account", "Anyone with the link" (Send only)

### 2.7 File Shares (Durable Single-File Links)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/workspace/{id}/create/fileshare/` | JWT + Member | Create bound to a file node |
| `GET` | `/workspace/{id}/list/fileshares/` | JWT + Member | List workspace file shares |
| `POST`/`PATCH` | `/fileshare/{id}/update/` | JWT + Member | Update title, access tier, password |
| `DELETE` | `/fileshare/{id}/delete/` | JWT + Member | Delete file share |
| `GET`/`POST`/`DELETE` | `/fileshare/{id}/grants/` | JWT + Member | List, grant, revoke per-user capabilities |

**Create body:** `node` (required, OpaqueId of file), `title`, `access_option` (anyone_with_link/any_registered/named_people), `password` (1-255 chars, body-only), `expires` (relative seconds) or `expires_at` (absolute datetime, mutually exclusive)

### 2.8 Cloud Sync

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/workspace/{id}/cloud-import/enable/` | Enable cloud sync |
| `POST` | `/workspace/{id}/cloud-import/disable/` | Disable cloud sync |
| `GET` | `/cloudsync/workspace/{id}/providers/` | List available providers for plan |
| `GET` | `/cloudsync/workspace/{id}/identities/` | List provider identities |
| `POST` | `/cloudsync/workspace/{id}/identities/provision/` | Provision a provider identity |
| `POST` | `/cloudsync/oauth/{provider}/complete/` | Finish browser OAuth (all four providers) |
| `GET` | `/cloudsync/workspace/{id}/identities/{id}/` | Get identity details |
| `POST` | `/cloudsync/workspace/{id}/identities/{id}/revoke/` | Revoke a provider identity |
| `GET` | `/cloudsync/workspace/{id}/identities/{id}/drives/` | List reachable drives |
| `POST` | `/cloudsync/workspace/{id}/identities/{id}/drives/refresh/` | Refresh the drive catalog |
| `GET` | `/cloudsync/workspace/{id}/sources/` | List the workspace's sync sources |
| `POST` | `/cloudsync/workspace/{id}/sources/create/` | Create a sync source from an identity you own |
| `POST` | `/cloudsync/workspace/{id}/sources/discover/` | Browse an identity's cloud folders to pick what to sync |
| `GET` | `/cloudsync/details/{source_id}/` | Get source details |
| `POST` | `/cloudsync/details/{source_id}/update/` | Update a source's settings |
| `POST` | `/cloudsync/details/{source_id}/refresh/` | Trigger an immediate incremental sync |
| `POST` | `/cloudsync/details/{source_id}/disconnect/` | Disconnect a source, leaving its imported files in place |
| `POST` | `/cloudsync/details/{source_id}/delete/` | Delete a source and the files it imported |
| `GET` | `/cloudsync/details/{source_id}/jobs/` | List a source's sync jobs |
| `GET` | `/cloudsync/details/{source_id}/jobs/{job_id}/` | Get one sync job's details and progress |
| `POST` | `/cloudsync/details/{source_id}/jobs/{job_id}/cancel/` | Cancel a pending or running sync job |
| `GET` | `/cloudsync/details/{source_id}/writebacks/` | List write-back jobs |
| `POST` | `/cloudsync/details/{source_id}/writebacks/push/{node_id}/` | Push one imported file back to the provider |
| `GET` | `/cloudsync/details/{source_id}/writebacks/{id}/` | Get write-back job details |
| `POST` | `/cloudsync/details/{source_id}/writebacks/{id}/retry/` | Retry a failed write-back |
| `POST` | `/cloudsync/details/{source_id}/writebacks/{id}/resolve/` | Resolve a write-back conflict |
| `POST` | `/cloudsync/details/{source_id}/writebacks/{id}/cancel/` | Cancel a pending or conflicting write-back |

### 2.9 Permission System

#### Permission Values

| Setting | Values |
|---|---|
| `perm_join` | "Member or above" (default), "Admin or above", "Only Org Owners" |
| `perm_member_manage` | "Member or above" (default), "Admin or above" |

#### Permission Levels (Numeric Hierarchy)

| Level | Numeric | Description |
|---|---|---|
| **Owner** | 1000 | Full control; one per workspace |
| **Admin** | 500 | Administrative access |
| **Member** | 100 | Standard member |
| **Guest** | 50 | Limited guest access |
| **View** | 20 | Read-only access |

#### Access Levels by Endpoint

| Endpoint Category | Required Level |
|---|---|
| Create workspace | Org Owner/Admin/Member |
| Get details | View or above |
| Update workspace | Admin or Owner |
| Delete workspace | Owner only + 2FA |
| Archive/Unarchive | Admin or Owner + 2FA |
| List/Upload assets | Owner only + 2FA |
| Download assets | Any member + 2FA |
| Add/Remove members | perm_member_manage level |
| Update member role | perm_member_manage level |
| Transfer ownership | Owner only |
| Create share | Admin or Owner |
| List shares | View or above |
| Import share | Member + Share Owner |

### 2.10 Intelligence (AI Indexing)

- **Enable** (`intelligence=true`) — auto-index files for RAG; requires `content_ai` + `ai_agent` plan features
- **Disable** (`intelligence=false`) — no RAG indexing; files still stored/shared
- **Rate-limited** — ~2x per minute, ~5x per hour (error 1685)
- **On by default** at creation (unless plan lacks AI features)
- **Disabling flushes embeddings** — re-enabling triggers re-indexing (costs AI credits)
- Required for `chat_with_files` AI chat type

### 2.11 Member States & Pending Members

| Status | Meaning | Invite Field |
|---|---|---|
| `active` | Registered user, invitation accepted | `"accepted"` |
| `pending` | Invited by email, no account yet | `{id, created, expires}` object |

- Pending member: `first_name` = email address, `last_name` = empty
- Account claim transitions pending → active
- Remove pending member by deleting their invitation
- Pending members receive no notifications until they claim their account

### 2.12 Field Constraints

| Field | Constraint |
|---|---|
| `folder_name` | Regex `^[\p{L}\p{N}-]+$` (letters, numbers, hyphens), globally unique |
| `name` | 2–100 characters, non-blank |
| `description` | 10–1000 characters, optional |
| Share `title` | 2–80 characters |
| Share `custom_name` | 4–80 characters, URL-friendly |

### 2.13 Error Codes Reference

| Code | HTTP | Meaning |
|---|---|---|
| 1605 | 406 | Invalid Input |
| 1609 | 404 | Not Found |
| 1650 | 401 | Authentication Invalid |
| 1654 | 500 | Internal Error |
| 1656 | 413 | Limit Exceeded |
| 1658 | 406 | Not Acceptable (duplicate/conflict) |
| 1660 | 409 | Conflict (concurrent operation) |
| 1663 | 500 | Update Failed (internal) |
| 1666 | 500 | Delete Failed (internal) |
| 1679 | 500 | Update Failed (invitation) |
| 1680 | 401 | Access Denied |
| 1685 | 412 | Feature Limit (plan or rate limit) |
| 1691 | 412 | File Missing (asset upload) |
| 1692 | 500 | Cannot Add As Owner |
| 9661-9669 | Various | Additional error.code family |

> Four-digit 16xx/17xx values are HTTP-status classes, not `error.code`. Use HTTP status as the gate and documented error.code only as refinement.

### 2.14 Response Format

- Standard envelope: `{"result": true, ...}` with data nested
- List endpoints: `{"result": true, "items": [...]}`
- `output=` query param for compact shapes
- IDs are 19-digit numeric strings
- Auth: Bearer JWT token in `Authorization` header

---

## 3. Cross-System Notes

### 3.1 Identifiers

| System | ID Format |
|---|---|
| Mem0 | Varies (UUID-style strings) |
| SwarmVault | 19-digit numeric strings |

### 3.2 Auth Models

| System | Method |
|---|---|
| Mem0 | API key (`api_key=`) |
| SwarmVault | Bearer JWT token |

### 3.3 Scoping Patterns

| System | Scoping Mechanism |
|---|---|
| Mem0 | `user_id`, `agent_id`, `run_id`, `app_id` on every operation |
| SwarmVault | Workspace membership (JWT-scoped) + `user_id`/`agent_id` in operations |

---

# Cognee v1.0 — `remember()` Features

## Core Operation

| Feature | Description |
|---|---|
| `remember()` | Main ingestion entry point (v1.0) |
| **Permanent memory** | Full pipeline — ingest, build graph, enrich |
| **Session memory** | Fast cache write + optional background bridge to permanent graph |
| `run_in_background=True` | Async pipeline execution, returns `RememberResult` immediately |

## Input Types

| Type | Notes |
|---|---|
| Raw text strings | `"Einstein was born in Ulm."` |
| Local file paths | Absolute, relative, `file://` URLs |
| HTTP/HTTPS URLs | Fetched and ingested (permanent mode only) |
| S3 paths | `s3://bucket/key` (requires `s3fs`) |
| `DataItem` objects | Wrapper with `data`, `label`, `external_metadata`, `data_id` |
| HTTP upload objects | `.file` + `.filename` (e.g., FastAPI `UploadFile`) |

> Not accepted: plain `open("doc.pdf", "rb")` file handles (raises `IngestionError`)

## Parameters

| Parameter | Purpose |
|---|---|
| `data` | Content to store (text, path, URL, DataItem, upload, or list) |
| `dataset_name` | Target dataset (default: `main_dataset`) |
| `dataset_id` | Target existing dataset by UUID (takes precedence over `dataset_name`) |
| `session_id` | Switches to session-memory mode |
| `self_improvement` | Auto-start Improve pass after storage (default: `True`) |
| `run_in_background` | Async pipeline execution |
| `chunk_size` / `chunker` | Customize chunking |
| `custom_prompt` | Override graph-extraction prompt |
| `session_ids` | Sync graph knowledge back into specific sessions |
| `graph_model` | Override graph schema (default: `KnowledgeGraph`); pass a `DataPoint` subclass |
| `node_set` | Attach node-set tags during ingestion |
| `preferred_loaders` | Control which loaders are preferred |
| `incremental_loading` | Only process new/changed data on dataset reuse |
| `data_per_batch` | Tune ingestion batching |
| `chunks_per_batch` | Tune chunk-processing batching |
| `user` | Run under a specific user context |
| `vector_db_config` | Override vector store config |
| `graph_db_config` | Override graph store config |
| `primary_key` | dlt upsert/dedup column name |
| `write_disposition` | dlt: `replace` (default), `merge`, `append` |
| `query` | dlt SQL `WHERE`-style filter |
| `max_rows_per_table` | Cap rows per table per call |

## RememberResult Fields

| Field | Meaning |
|---|---|
| `status` | `running`, `completed`, `errored`, `session_stored` |
| `dataset_name` | Target dataset name |
| `dataset_id` | Dataset UUID |
| `session_ids` | Session IDs (when bridging involved) |
| `pipeline_run_id` | Pipeline run UUID |
| `elapsed_seconds` | Wall-clock time |
| `items_processed` | Number of processed items |
| `content_hash` | Content hash of first item |
| `items` | Per-item metadata (IDs, names, token counts, MIME type, hashes) |
| `raw_result` | Raw pipeline result payload |
| `error` | Error text on failure |

## What Permanent Remember Produces

- Dataset records in the relational store
- Normalized source content
- Chunks
- Graph nodes and edges
- Embeddings and summaries
- Improvement artifacts (if `self_improvement=True`)

## Pipeline Stages

| Stage | Description |
|---|---|
| **Add** | Normalize data, attach to dataset |
| **Cognify** | Chunk, extract entities/relationships, embed |
| **Improve** | Add derived retrieval structures (default enabled) |

## Supported File Formats

| Loader | Extensions | Extra |
|---|---|---|
| CodeLoader | `.py`, `.js`, `.ts`, `.go`, `.rs`, `.java` + 25 more | built-in |
| TextLoader | `.txt`, `.md`, `.json`, `.xml`, `.yaml`, `.yml`, `.log` | built-in |
| DltCsvLoader | `.csv` (takes precedence over CsvLoader) | `pip install cognee[dlt]` |
| CsvLoader | `.csv` | built-in |
| PyPdfLoader | `.pdf` | built-in |
| ImageLoader | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.tif`, `.tiff`, `.heic`, `.avif`, `.ico`, `.psd`, `.apng`, `.cr2`, `.dwg`, `.xcf`, `.jxr`, `.jpx` | built-in |
| AudioLoader | `.mp3`, `.wav`, `.aac`, `.flac`, `.ogg`, `.m4a`, `.mid`, `.amr`, `.aiff` | built-in |
| UnstructuredLoader | `.docx`, `.doc`, `.odt`, `.xlsx`, `.xls`, `.ods`, `.pptx`, `.ppt`, `.odp`, `.rtf`, `.html`, `.htm`, `.eml`, `.msg`, `.epub` | `pip install cognee[docs]` |
| AdvancedPdfLoader | `.pdf` (layout-aware) | `pip install cognee[docs]` |
| BeautifulSoupLoader | `.html` | `pip install cognee[scraping]` |
| DoclingDocument | Pre-converted `DoclingDocument` objects | `pip install cognee[docling]` |

## HTTP API Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/datasets/status` | Check indexing status for a dataset |
| `GET /api/v1/activity/pipeline-runs` | Recent pipeline runs and operation records |

## Dataset Status Values

| Status | Meaning |
|---|---|
| `DATASET_PROCESSING_INITIATED` | Pipeline queued |
| `DATASET_PROCESSING_STARTED` | Actively processing |
| `DATASET_PROCESSING_COMPLETED` | Finished successfully |
| `DATASET_PROCESSING_ERRORED` | Encountered an error |

## Configuration

| Setting | Values | Purpose |
|---|---|---|
| `CACHING` | `true` / `false` | Enable/disable session caching |
| `CACHE_BACKEND` | `filesystem` (default), `redis` | Session cache backend |

## Unique Design Behaviors

- Non-text inputs in session mode become text representations, not parsed source content
- Concurrent `recall()` during background indexing is supported (no global lock)
- Single-process only — embedded file-based defaults (Kuzu, SQLite, LanceDB) cannot be shared across processes
- Session cache is keyed by user + session — same `session_id` under different users ≠ shared memory
- URL strings in session mode are stored as text, not fetched — permanent mode required for URL ingestion
- An absolute-looking string that does not point to an existing file is stored as text, not resolved as a path
- With `run_in_background=True`, file-like inputs are read up-front and copied into owned in-memory buffers before scheduling
