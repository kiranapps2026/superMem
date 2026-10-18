# SwarmVault Webapp vs Consolidated Features — Priority Analysis

> Generated 2026-08-30 from source code review of `C:\Users\Administrator\Documents\SwarmVaultwebapp`
> compared against `CONSOLIDATED-FEATURES.md`

---

## Summary

The webapp currently implements ~**40%** of workspace management and ~**15%** of memory features
from the consolidated specs. Below is a priority-ranked list of what to build next, based on
what 80%+ of business users and applications need.

---

## Current Webapp State

### Already Implemented
| Area | What Exists |
|---|---|
| Auth | JWT (access + refresh), register, login, logout, change password |
| Tenants | CRUD, plan tracking, slug |
| Workspaces | CRUD, soft-delete, member roles |
| Members | Add/remove/list, role-based (owner/admin/member/viewer) |
| Invitations | Create/update/list by state/respond |
| Sessions | CRUD, soft-delete, title, metadata |
| Messages | Create/list by session, roles, metadata |
| Projects | CRUD |
| Memories | Store with user_id/agent_id/run_id, procedural_memory type, embedding, metadata |
| Ingest | Job tracking (queued/running/completed/error), stage/progress |

### Missing — Categorized by Priority

---

## P0 — Critical (build now)

These are table-stakes. Without them, the app is not usable.

| Feature | Source Section | Why Critical |
|---|---|---|
| **Memory search (vector)** | §1.5 | Users need to find stored memories. The entire point of the memory layer is retrieval. Implement basic cosine similarity search with `user_id`/`run_id` filters. |
| **Memory get_all / pagination** | §1.3, §1.5 | List memories with filters and pagination. Without this, the admin can't see what's stored. |
| **Workspace archive/unarchive** | §2.1 | Part of the workspace lifecycle. Already in the API design, missing from the webapp. |
| **Soft-delete confirmation** | §2.1 | Delete endpoint needs `?confirm={name_or_id}` pattern per spec. Currently missing. |
| **Frontend routing / SPA feel** | — | The app currently serves a single HTML page. Needs routing for auth vs workspace views. |

**Estimated effort: 2–3 weeks**

---

## P1 — High (build soon)

These are features that 80%+ of business users expect. Missing them means the app feels incomplete.

| Feature | Source Section | Why High |
|---|---|---|
| **Memory update & delete** | §1.3 | Users correct mistakes and clean up stale data. Basic CRUD parity. |
| **Workspace assets (logo upload)** | §2.3 | Every SaaS workspace needs branding. Logo/icon upload is expected. |
| **Workspace shares (basic)** | §2.6 | Sharing is core to collaboration. At minimum: create + list shares. |
| **Memory custom categories** | §1.9 | Default 15 categories + override. Tags memories for organization. Critical for a knowledge vault. |
| **Memory expiration** | §1.7 | TTL on memories. GDPR/privacy and data hygiene. |
| **Reranking on search** | §1.5 | `rerank=True` flag. Improves top-N precision significantly. Small code change for big quality gain. |
| **Score explanation** | §1.5 | `explain=True` — transparency for why a memory matched. Builds trust. |
| **Workspace member update** | §2.4 | Change roles, set expiration dates, toggle notifications per member. |

**Estimated effort: 3–4 weeks**

---

## P2 — Medium (build next quarter)

Useful but not blocking. 60–80% of users will want these.

| Feature | Source Section | Why Medium |
|---|---|---|
| **Workspace discovery** | §2.2 | `GET /workspaces/all/`, `available/`, `check/name/`. Browse and join workspaces. |
| **File shares (durable single-file links)** | §2.7 | Share individual files with access control, passwords, expiry. Complements workspace shares. |
| **Memory batch operations** | §1.3 | `batch_delete` (up to 1000), `delete_all` with filters. Bulk management. |
| **Memory feedback** | §1.10 | POSITIVE/NEGATIVE/VERY_NEGATIVE ratings. Drives quality improvement. |
| **Memory history** | §1.3 | Track changes to a memory over time. Audit trail. |
| **Group chat (multi-user sessions)** | §1.15 | Multiple participants, shared `run_id`, per-speaker memory. Team use case. |
| **Cloud sync** | §2.8 | Google Drive/Dropbox integration. Power-user feature. |
| **Projects → workspace linking** | — | Currently projects exist but have no rich operations. Add comments, assets. |

**Estimated effort: 4–6 weeks**

---

## P3 — Nice-to-have (later)

<20% of users will use these initially. Build after core is solid.

| Feature | Source Section | Why Low Priority |
|---|---|---|
| **Memory entity graph** | §1.16 | Automatic entity linking across memories. Cool but requires graph infra. |
| **Memory decay** | §1.8 | Re-rank by recency. UX improvement, not blocking. |
| **Memory export** | §1.13 | Structured export with Pydantic schemas. Admin/portability use case. |
| **MCP Server (`mem0-mcp`)** | §1.16 | Expose memories to AI agents. Future integration point. |
| **Workspace assets (full)** | §2.3 | Multiple asset types, metadata, HEAD requests. Extend after logo upload works. |
| **Temporal reasoning** | §1.5 | Time-aware queries. Auto-enabled in Platform v3. |
| **Workspace comments** | §2.2 | Comment threads on workspaces. |
| **Graph memory (built-in)** | §1.16 | Entity graph as first-class citizen. Requires graph database. |

---

## Recommendation: Build Order

```
Week 1-2:   P0 — Memory search + get_all + workspace archive
Week 3-4:   P1 — Memory update/delete + logo upload + custom categories
Week 5-6:   P1 — Workspace shares (basic) + reranking + score explanation
Week 7-8:   P1 — Workspace member update + memory expiration
Week 9-10:  P2 — Workspace discovery + file shares + batch memory ops
Week 11-14: P2 — Feedback, history, group chat
Q2:         P3 — Cloud sync, memory export, MCP server, entity graph
```

---

## Key Insight

The biggest gap is **memory search**. The webapp stores memories but has no way to retrieve them
meaningfully. That's the single highest-value feature to implement next — it's the difference
between a data store and a knowledge vault.

The second biggest gap is **frontend UX**. The single-page HTML needs routing, workspace switching,
and a proper memory management UI. A backend without a usable frontend delivers zero business value.
