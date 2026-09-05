# SwarmVault WebApp — Frontend Redesign Document

**Version:** 1.2.0
**Date:** 2026-09-05
**Status:** PLANNING — Not for implementation
**Scope:** Complete frontend redesign plan aligned with SwarmVault Core architecture, with verified/proposed distinction
**Constraint:** This document is informational only. No code changes are to be made from this document.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Frontend Architecture Boundary](#2-frontend-architecture-boundary)
3. [Verification & Trust Model](#3-verification--trust-model)
4. [SwarmVault Core Capability Inventory](#4-swarmvault-core-capability-inventory)
5. [Architecture Fidelity Audit v2](#5-architecture-fidelity-audit-v2)
6. [Current State Analysis](#6-current-state-analysis)
7. [UI Coverage Gap Analysis](#7-ui-coverage-gap-analysis)
8. [Redesign Principles](#8-redesign-principles)
9. [Theme System](#9-theme-system)
10. [Typography & Motion System](#10-typography--motion-system)
11. [Layout Architecture](#11-layout-architecture)
12. [Sidebar Redesign](#12-sidebar-redesign)
13. [Navigation Restructure](#13-navigation-restructure)
14. [Page Redesign Plans](#14-page-redesign-plans)
15. [Trust & Evidence UX Model](#15-trust--evidence-ux-model)
16. [Provenance as a Pervasive UX Pattern](#16-provenance-as-a-pervasive-ux-pattern)
17. [Component Library Gaps](#17-component-library-gaps)
18. [Accessibility & Responsive Design](#18-accessibility--responsive-design)
19. [Implementation Roadmap](#19-implementation-roadmap)
20. [Appendices](#20-appendices)

---

## 1. Executive Summary

### 1.1 The Core Finding

> **The SwarmVault Core is substantially richer than the current WebApp communicates — but the WebApp is an adapter, not the system itself.**

SwarmVault Core is a local-first, single-operator knowledge vault. Its primary interfaces are the CLI (`python scripts/swarmvault.py`), MCP server, filesystem watcher, and Claude Code hook — not a web API. The M0–M5 modules are independent, optionally-loaded capabilities providing ingestion, structured memory, temporal truth, graph/provenance, and memory intelligence.

The current WebApp exposes approximately 30–40% of this capability through a functional but minimal interface. Many gaps are not visual — they are architecture-to-UI fidelity gaps.

### 1.2 Document Structure and Trust Levels

This document contains three distinct categories of content. They are labeled consistently throughout:

| Label | Meaning | Example |
|-------|---------|---------|
| **VERIFIED** | Confirmed against Core documentation, code, or existing backend endpoints | "M2 extracts structured facts with authority levels" |
| **PROPOSED** | UI/UX design recommendation not yet implemented or confirmed in backend | "Context Packs page with copy-to-clipboard" |
| **ILLUSTRATIVE** | Placeholder value, layout sketch, or example data — not real | "4,821 conversations", wireframe layouts |

Where a PROPOSED feature depends on a backend capability, the dependency is explicitly noted. Where an ILLUSTRATIVE value appears, it is marked as such.

### 1.3 What This Document Is

- A **design specification** for evolving the SwarmVault WebApp into a faithful presentation layer
- Does **not** propose changing any Core code
- Separates verified Core capabilities from proposed UI additions

### 1.4 What This Document Is Not

- Not a feature specification for new Core capabilities
- Not an implementation plan with file changes
- Not a rewrite of existing working pages
- Not a mandate to change anything immediately
- Not a suggestion that the WebApp should replace or subsume the CLI/MCP interfaces

---

## 2. Frontend Architecture Boundary

### 2.1 The WebApp Is a Presentation Adapter

> **Important:** The WebApp redesign must not imply Core capabilities that are not present, must not misrepresent the Core's architecture, and must not elevate the WebApp above the CLI/MCP interfaces in the user's mental model.

The authoritative SwarmVault architecture is **local-first and single-operator**, with the following primary interfaces:

| Interface | Role | Primary User |
|-----------|------|-------------|
| CLI (`python scripts/swarmvault.py`) | Direct command invocation | Developer, power user |
| MCP Server | Agent-accessible tools | Claude Code, other agents |
| Filesystem watcher | Automatic ingestion on file change | Passive background |
| Claude Code hook | Session-aware knowledge capture | During Claude Code sessions |
| **WebApp (this project)** | Visual exploration and management | Operator, reviewer |

The WebApp is one interface among several. The CLI and MCP are not "backends for the WebApp" — they are independent, equally-valid interfaces to the same Core. The WebApp backend (`app/`) is an **HTTP adapter** over the same data and logic.

### 2.2 What Is Out of Scope for the WebApp (per Architecture)

| Capability | Reason |
|------------|--------|
| Multi-user collaboration | Single-operator design |
| Workspace sharing / invitations | Single-operator design |
| Role-based access control (RBAC) | Single-operator design |
| Audit logging of user actions | Single-operator, no multi-user events |
| API key management for external consumers | Single-operator, local interface |
| Tenant isolation | Single-operator, single tenant |
| CORS for external origins | Local-first, same-origin or localhost |

> **Design implication:** Settings pages for Members, Roles, multi-tenant Audit Log should be removed or marked as adapter-level only. If retained for local API key configuration (MCP server access), scope them to that purpose.

### 2.3 WebApp Abstractions vs. Core Primitives

| WebApp Concept | Maps To | Notes |
|---------------|---------|-------|
| "Workspace" | WebApp tenancy grouping | Does NOT correspond to a Core memory scope |
| "Project" | Core `PROJECT` scope | Closest alignment — WebApp project ≈ Core project |
| `workspace_id` in DB | Adapter-level grouping | Not a Core concept; used for UI organization |
| Backend `/api/v1/*` | HTTP adapter over Core | CLI/MCP access same Core data directly |

### 2.4 Design Implications

1. **No SaaS language.** Avoid "multi-tenant," "team," "organization," "collaborate." Use "vault," "knowledge base," "operator," "session."
2. **Single-operator identity.** Design for one person managing their knowledge vault.
3. **CLI parity.** Where the CLI exposes a capability, the WebApp should surface it visually.
4. **MCP awareness.** Acknowledge Claude Code and other MCP clients operate on the same vault.
5. **Local-first honesty.** No cloud sync, multi-device, or remote access implications unless implemented.

---

## 3. Verification & Trust Model

### 3.1 The Three-Layer Trust Problem

SwarmVault has two distinct trust dimensions that the UI must represent independently:

```
EVIDENCE CHAIN (how we know something)
┌─────────────────────────────────────────┐
│  INGESTED                                 │  ← Raw input received
│    ↓                                      │
│  PROCESSED                                │  ← Parsed, redacted, deduplicated
│    ↓                                      │
│  INTEGRATED                                │  ← Added to knowledge store
│    ↓                                      │
│  PROVEN                                   │  ← Verified, linked to sources
└─────────────────────────────────────────┘

AUTHORITY (how confident we are)
UNVERIFIED → INFERRED → OBSERVED → DECISION → VERIFIED → CERTIFIED
```

**These are different axes.** A PROVEN item can be INFERRED authority. A CERTIFIED item might still be PROVING (in processing). The UI must never collapse these into a single "trust score."

### 3.2 UI Representation

| Dimension | Display | UI Element |
|-----------|---------|-----------|
| Evidence class | INGESTED / PROCESSED / INTEGRATED / PROVEN | Badge or icon |
| Authority | 6-level hierarchy | Badge with distinct color per level |
| Confidence | 0.0–1.0 float | Numeric or progress indicator |
| Temporal status | ACTIVE / SUPERSEDED / ARCHIVED | Badge |
| Scope | MESSAGE / SESSION / PROJECT / DOMAIN / GLOBAL | Label or tag |

### 3.3 Why This Matters for Implementation

Engineers implementing from this document must understand:
- `authority` is a discrete level, not a score
- `confidence` is independent of authority
- `temporal_status` is separate from both
- `evidence_class` is about the chain completeness, not quality
- None of these should be merged into a single "trust badge" in the UI

---

## 4. SwarmVault Core Capability Inventory

### 4.1 Core Modules (M0–M5)

M0–M5 are **independent, optionally-loaded modules**. M0 is always loaded (protected foundation). M1–M5 provide progressively richer capabilities and may be enabled or disabled independently.

| Module | UI-Friendly Label | Always Loaded | Description |
|--------|-------------------|---------------|-------------|
| **M0** | Foundation / Ingestion | ✅ Yes | Parse, redact, deduplicate, persist. The protected base. |
| **M1** | Memory Upgrade | Optional | Preserve, compress, resume. Session persistence and compaction. |
| **M2** | Structured Memory | Optional | Fact extraction, authority levels, confidence scoring, scoping. |
| **M3** | Temporal Truth | Optional | Supersession, temporal status, confidence decay, timeline reconstruction. |
| **M4** | Graph & Provenance | Optional | Entity/concept/decision nodes, relationship extraction, provenance chains, CAS hashes, case memory. |
| **M5** | Memory Intelligence | Optional | Multi-signal ranking, conflict detection, procedural memory, impact analysis, activation tracking, proactive recall. |

### 4.2 Module Dependency Chain

```
M0 (Foundation)
 ├─ M1 (Memory Upgrade)       ← session persistence depends on M0
 │   └─ M2 (Structured Memory) ← fact extraction needs preserved sessions
 │       └─ M3 (Temporal Truth) ← supersession needs structured facts
 │           └─ M4 (Graph & Provenance) ← graph nodes from facts+sessions
 │               └─ M5 (Memory Intelligence) ← ranking needs graph + temporal
```

Each module builds on the previous, but they are **independently loadable**. If M5 is disabled, M4 still works. If M2 is disabled, M1's session preservation still functions.

### 4.3 Core Systems

| System | Description | UI Relevance |
|--------|-------------|-------------|
| **Retrieval Engine** | BM25 + multi-signal scoring (authority, confidence, recency, activation, provenance, graph relevance) + diversity reranking. Semantic dedup uses Jaccard word-set similarity. | Search page, Chat retrieval controls |
| **Orchestration** | Tickets, claims, releases, board, inbox, supervisor, control signals, agent/platform/model/effort routing, scheduling, plan continuation, usage tracking | Operations Center |
| **Storage** | CAS (SHA-256 content identity), manifests, backups, restore, quarantine, verification, retention, garbage collection, lifecycle, WAL repair, compression, atomic writes | Storage & Recovery page |
| **Policy Engine** | Fail-closed policy evaluation for retrieval and ingestion | Settings → Policies |
| **Context/Resume** | `build_context_pack`, `build_resume_packet`, proactive context, session resumption | Context Packs page |
| **Procedures** | Detect repeatable patterns, register, store, find relevant procedures, extract from successful sessions | Procedures page |

### 4.4 Memory Model

| Attribute | Values | Description |
|-----------|--------|-------------|
| **Type** | fact, decision, task, preference, observation, procedure, entity | What kind of knowledge |
| **Authority** | UNVERIFIED → INFERRED → OBSERVED → DECISION → VERIFIED → CERTIFIED | Six-level trust hierarchy |
| **Confidence** | 0.0 – 1.0 float | Independent of authority |
| **Temporal Status** | ACTIVE, SUPERSEDED, ARCHIVED | Lifecycle state |
| **Evidence Class** | INGESTED, PROCESSED, INTEGRATED, PROVEN | Chain completeness |
| **Scope** | MESSAGE, SESSION, PROJECT, DOMAIN, GLOBAL | Visibility range |
| **Scope ID** | UUID of the scope entity | The specific message/session/project/domain |

### 4.5 Memory Scopes Explained

| Scope | Visibility | Example |
|-------|-----------|---------|
| **MESSAGE** | Only within the originating message | A fact from one specific message |
| **SESSION** | All messages in a conversation | Facts from a single chat session |
| **PROJECT** | All sessions in a project | Architecture decisions for a project |
| **DOMAIN** | Cross-project within a domain | Organizational preferences |
| **GLOBAL** | Entire vault | Universal facts, verified procedures |

> **Important:** The WebApp "project" maps to Core `PROJECT` scope. The WebApp "workspace" is a UI grouping and does NOT correspond to a Core scope.

### 4.6 Retrieval Signals (VERIFIED from Core docs)

The retrieval engine uses these signals for ranking:

| Signal | Type | Description |
|--------|------|-------------|
| Lexical relevance | BM25 | Term frequency matching |
| Authority | Discrete level | Six-level authority hierarchy |
| Confidence | Float 0.0–1.0 | Extraction confidence |
| Recency | Temporal | How recently the knowledge was confirmed |
| Activation | Float | Retrieval frequency (more recalled = more active) |
| Provenance | Chain depth | Number of verified source links |
| Graph relevance | Relationship | Connectedness in knowledge graph |
| Diversity | Reranking | Penalizes redundant results |

### 4.7 Storage Subsystem (VERIFIED)

| Component | Description |
|-----------|-------------|
| **CAS** | Content-addressed storage via SHA-256 |
| **Manifests** | Track stored objects and their metadata |
| **Backups** | Snapshot-based backup system |
| **Restore** | Point-in-time restore from backups |
| **Quarantine** | Isolated storage for suspicious/unverified content |
| **Verification** | Integrity checking of stored objects |
| **Retention** | TTL-based cleanup policies |
| **Garbage Collection** | Reclaim unreferenced storage |
| **Lifecycle** | HOT → WARM → COLD → PURGED tiers |
| **WAL Repair** | Write-ahead log recovery |
| **Compression** | Storage compression |
| **Atomic Writes** | Crash-safe write operations |
| **Locks** | Concurrent access protection |

---

## 5. Architecture Fidelity Audit v2

### 5.1 Correction Log

| # | Issue in v1.0 | Corrected in v1.1 | Corrected in v1.2 |
|---|--------------|-------------------|-------------------|
| 1 | Framed as SaaS/API product | WebApp is a local-first adapter | Kept |
| 2 | M0–M5 as linear pipeline | Independent modules | **Module names corrected** — M1=Memory Upgrade, M2=Structured Memory, M3=Temporal Truth, M4=Graph & Provenance, M5=Memory Intelligence |
| 3 | Dashboard M0–M5 progress bars | Capability grouping | Kept |
| 4 | M5 = retrieval/indexing | M5 = Memory Intelligence | Kept |
| 5 | 3 authority levels | 6 levels | Kept |
| 6 | 3 memory scopes | 5 scopes | Kept |
| 7 | "Semantic Search" | "Knowledge Search" | Kept |
| 8 | Combined health + pipeline + metrics | Separated sections | Kept |
| 9 | Wireframe numbers without disclaimer | Global disclaimer | Kept |
| 10 | Jobs as SaaS queue | Operations Center | **Split** — Operations (live) vs Recovery (checkpoint/restore) |
| 11 | Operations missing from nav | Added | Kept, refined with agent definitions |
| 12 | Procedures minor | Elevated to Executable Knowledge | Kept |
| 13 | Provenance standalone only | Made pervasive | Kept |
| 14 | No Trust & Proof page | Added | **Refactored** — Trust & Evidence model separated from Provenance |
| 15 | Mixed verified/proposed/illustrative without labeling | **NEW** — Three-layer trust system in §3 | Core improvement |
| 16 | M1-M5 naming inconsistent with Core docs | **NEW** — Corrected module names per implementation docs | Critical |
| 17 | Trust page conflates authority, confidence, evidence, proof | **NEW** — §15 separates Evidence Chain from Authority Hierarchy | Critical |
| 18 | No Conflicts page | **NEW** — §14.4 full Conflicts page design | Major gap |
| 19 | No "What Changed" page | **NEW** — §14.3 full design | Major gap |
| 20 | No Context Packs page | **NEW** — §14.5 full design | Major gap |
| 21 | Session detail under-specified | **NEW** — §14.6 full Session Detail design | Major gap |
| 22 | Storage underrepresented | **NEW** — §14.8 full Storage & Recovery design | Major gap |
| 23 | Recovery mixed with Operations | **NEW** — Split into separate sections | Major gap |
| 24 | Agents undefined | **NEW** — §13.9 Agent/MCP model clarified | Gap |
| 25 | No implementation sequencing correction | **NEW** — §19 corrected roadmap | Gap |

---

## 6. Current State Analysis

### 6.1 Current Navigation Map

```
Global
├── Dashboard
├── Projects
└── Settings & Members

Project (contextual)
├── Chat
├── Ingest
├── Sessions
├── Memory
├── Facts
├── Decisions
├── Timeline
├── Search
├── Graph
└── Settings
```

### 6.2 Current Theme State

| Aspect | Current State |
|--------|--------------|
| Theme mode | Dark only (hardcoded) |
| CSS variables | 5 (`--bg-primary`, `--bg-secondary`, `--bg-tertiary`, `--border`, `--accent`, `--accent-hover`) |
| Tailwind darkMode | `'class'` — configured but unused |
| Font family | System default (no custom font) |
| Font scale | Single size (text-sm throughout) |
| Animations | 1 (`animate-pulse-dot`) |
| Transitions | `transition-colors` on interactive elements only |

### 6.3 Current Component Library

| Component | Location | Status |
|-----------|----------|--------|
| Card | `components/ui/Card.tsx` | ✅ Basic |
| Badge | `components/ui/Badge.tsx` | ✅ Basic |
| Skeleton | `components/ui/Skeleton.tsx` | ✅ Basic |
| EmptyState | `components/ui/EmptyState.tsx` | ✅ Basic |
| ErrorAlert | `components/ui/ErrorAlert.tsx` | ✅ Basic |
| LoadingSpinner | `components/ui/LoadingSpinner.tsx` | ✅ Basic |
| ConfirmDialog | `components/ui/ConfirmDialog.tsx` | ✅ Basic |
| Pagination | `components/ui/Pagination.tsx` | ✅ Basic |
| FileInput | `components/ui/FileInput.tsx` | ✅ Basic |
| useClipboard | `components/ui/useClipboard.ts` | ✅ Hook |
| Collapsible | — | ❌ Missing |
| Tabs | — | ❌ Missing |
| Toast | — | ❌ Missing |
| Tooltip | — | ❌ Missing |
| Progress | — | ❌ Missing |
| Avatar | — | ❌ Missing |
| Dropdown | — | ❌ Missing |
| Breadcrumb | — | ❌ Missing |
| DataTable | — | ❌ Missing |
| StatCard | — | ❌ Missing |
| HealthIndicator | — | ❌ Missing |
| ContextPack | — | ❌ Missing |
| ConflictCard | — | ❌ Missing |
| EvidenceChain | — | ❌ Missing |
| ProcedureRunner | — | ❌ Missing |
| RecoveryPanel | — | ❌ Missing |

---

## 7. UI Coverage Gap Analysis

### 7.1 Page Coverage Matrix

| Page | Has Page? | Uses Backend? | Architecture Fidelity | Trust Level |
|------|-----------|---------------|----------------------|-------------|
| Landing / Login | ✅ | Partial | 60% | Verified existing |
| Registration | ✅ | ✅ | 80% | Verified existing |
| Dashboard | ✅ | ❌ | 15% — no stats, no health, no activity | Verified gap |
| Projects list | ✅ | ✅ | 50% | Verified existing |
| Project Chat | ✅ | ✅ | 70% — no retrieval controls, no provenance | Verified gap |
| Ingest | ✅ | ✅ | 60% — no source management | Verified gap |
| Sessions | ✅ | ✅ | 55% — basic list, no detail | Verified gap |
| Memory | ✅ | ✅ | 45% — wrong scope labels, no detail, wrong authority | Verified gap |
| Facts | ✅ | ✅ | 40% — basic list | Verified gap |
| Decisions | ✅ | ✅ | 40% — basic list | Verified gap |
| Timeline | ✅ | ✅ | 35% — empty state only | Verified gap |
| Knowledge Search | ✅ | ✅ | 50% — no signal controls | Verified gap |
| Graph | ✅ | ✅ | 30% — empty state only | Verified gap |
| Provenance | ❌ | ❌ | 0% | Proposed |
| Sources | ❌ | ❌ | 0% | Proposed |
| Operations Center | ❌ | ❌ | 0% — **major gap** | Proposed |
| Recovery Center | ❌ | ❌ | 0% — **major gap** | Proposed |
| Context Packs | ❌ | ❌ | 0% — **major gap** | Proposed |
| Conflicts | ❌ | ❌ | 0% — **major gap** | Proposed |
| What Changed | ❌ | ❌ | 0% — **major gap** | Proposed |
| Procedures | ⚠️ Basic list | ❌ | 10% — not first-class | Proposed upgrade |
| Trust & Proof | ❌ | ❌ | 0% | Proposed |
| System Health | ❌ | ❌ | 0% | Proposed |
| Storage & Recovery | ✅ (basic) | ✅ | 30% — only upload/listing | Proposed upgrade |
| Settings — General | ✅ | Partial | 50% | Verified existing |
| Settings — Members | ✅ | ✅ | ⚠️ Out of scope | Verified — should remove |
| Settings — API Keys | ✅ | Partial | ⚠️ Out of scope | Verified — should remove |
| Settings — Storage | ✅ | ✅ | 40% | Verified gap |
| Settings — Profile | ✅ | ✅ | 60% | Verified existing |
| Settings — Memory Config | ❌ | ❌ | 0% | Proposed |
| Settings — Retention | ❌ | ❌ | 0% | Proposed |
| Settings — Trust & Proof | ❌ | ❌ | 0% | Proposed |
| Settings — Appearance | ❌ | ❌ | 0% | Proposed |
| Settings — Developer | ❌ | ❌ | 0% | Proposed |
| Settings — Policies | ❌ | ❌ | 0% | Proposed |
| MCP Sessions | ❌ | ❌ | 0% — **major gap** | Proposed |

### 7.2 Coverage Score

```
Total pages: 33 possible
Implemented: 19 (58%)
Using backend: 14 (42%)
Architecture fidelity >70%: 3 pages (9%)
Architecture fidelity 40-70%: 8 pages (24%)
Architecture fidelity <40%: 8 pages (24%)
```

---

## 8. Redesign Principles

### 8.1 Design Philosophy

1. **Architecture fidelity first**: Every UI element must faithfully represent a Core capability. If the Core doesn't support it, the UI shouldn't imply it does.

2. **Verification-aware**: The UI must distinguish between verified evidence, inferred knowledge, and unverified ingestion. Never collapse evidence quality into a single badge.

3. **Adapter, not replacement**: The WebApp is a presentation layer. The CLI and MCP are equally valid interfaces. The UI should acknowledge this.

4. **Single-operator identity**: Design for one person managing their knowledge vault. Avoid team/collaboration language.

5. **Progressive disclosure**: Show overviews by default, drill into details on demand.

6. **Temporal awareness**: SwarmVault is not static. Knowledge evolves, gets superseded, decays, and strengthens. The UI should make change visible.

7. **Provenance everywhere**: Every knowledge item should expose its evidence chain. Provenance is not a page — it's a pattern.

8. **Consistent motion**: Shared animation vocabulary across the application.

9. **Theme parity**: Dark, light, and system modes equally refined.

10. **Accessibility by default**: Keyboard navigation, focus states, ARIA labels, color contrast built in.

### 8.2 Design Tokens

```css
:root {
  /* Surfaces */
  --sv-bg-base:        #0a0a0f;
  --sv-bg-raised:      #111118;
  --sv-bg-overlay:     #1a1a24;
  --sv-bg-sunken:      #060609;

  /* Borders */
  --sv-border-default: #1f1f2e;
  --sv-border-subtle:  #161622;
  --sv-border-strong:  #2a2a3e;

  /* Text */
  --sv-text-primary:   #e5e5e5;
  --sv-text-secondary: #9ca3af;
  --sv-text-tertiary:  #6b7280;
  --sv-text-disabled:  #4b5563;
  --sv-text-inverse:   #0a0a0f;

  /* Accent */
  --sv-accent:         #6366f1;
  --sv-accent-hover:   #818cf8;
  --sv-accent-muted:   #6366f120;
  --sv-accent-subtle:  #6366f108;

  /* Semantic */
  --sv-success:        #22c55e;
  --sv-warning:        #f59e0b;
  --sv-error:          #ef4444;
  --sv-info:           #3b82f6;

  /* Authority (6 levels — authority ≠ confidence) */
  --sv-auth-unverified: #6b7280;
  --sv-auth-inferred:   #f59e0b;
  --sv-auth-observed:   #3b82f6;
  --sv-auth-decision:   #a855f7;
  --sv-auth-verified:   #22c55e;
  --sv-auth-certified:  #6366f1;

  /* Evidence class */
  --sv-evidence-ingested:  #6b7280;
  --sv-evidence-processed: #3b82f6;
  --sv-evidence-integrated: #a855f7;
  --sv-evidence-proven:    #22c55e;

  /* Temporal status */
  --sv-temporal-active:    #22c55e;
  --sv-temporal-superseded:#f59e0b;
  --sv-temporal-archived:  #6b7280;

  /* Motion */
  --sv-duration-fast:   100ms;
  --sv-duration-base:   200ms;
  --sv-duration-slow:   350ms;
  --sv-easing:          cubic-bezier(0.4, 0, 0.2, 1);
  --sv-easing-enter:    cubic-bezier(0.0, 0, 0.2, 1);
  --sv-easing-exit:     cubic-bezier(0.4, 0, 1, 1);
  --sv-easing-spring:   cubic-bezier(0.34, 1.56, 0.64, 1);

  /* Typography */
  --sv-font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --sv-font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* Spacing */
  --sv-sidebar-width:      14rem;
  --sv-sidebar-collapsed:  3.5rem;
  --sv-header-height:      3rem;

  /* Radius */
  --sv-radius-sm: 6px;
  --sv-radius-md: 8px;
  --sv-radius-lg: 12px;

  /* Shadows */
  --sv-shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
  --sv-shadow-md: 0 4px 12px rgba(0,0,0,0.4);
  --sv-shadow-lg: 0 8px 24px rgba(0,0,0,0.5);

  /* Z-index */
  --sv-z-dropdown: 100;
  --sv-z-sticky:   200;
  --sv-z-modal:    300;
  --sv-z-toast:    400;
}

[data-theme="light"] {
  --sv-bg-base:        #f8fafc;
  --sv-bg-raised:      #ffffff;
  --sv-bg-overlay:     #f1f5f9;
  --sv-bg-sunken:      #e2e8f0;
  --sv-border-default: #e2e8f0;
  --sv-border-subtle:  #f1f5f9;
  --sv-border-strong:  #cbd5e1;
  --sv-text-primary:   #0f172a;
  --sv-text-secondary: #475569;
  --sv-text-tertiary:  #94a3b8;
  --sv-text-disabled:  #cbd5e1;
  --sv-shadow-sm:      0 1px 2px rgba(0,0,0,0.05);
  --sv-shadow-md:      0 4px 12px rgba(0,0,0,0.08);
  --sv-shadow-lg:      0 8px 24px rgba(0,0,0,0.12);
}
```

---

## 9. Theme System

### 9.1 Current State

- Dark mode only, hardcoded
- `darkMode: 'class'` configured in Tailwind but never used
- No theme switcher, no system preference detection

### 9.2 Theme Architecture

Three modes: Dark / Light / System (follows `prefers-color-scheme`).

### 9.3 Implementation

| Task | Files |
|------|-------|
| ThemeProvider context | `hooks/useTheme.tsx` |
| ThemeSwitcher component | `components/ThemeSwitcher.tsx` |
| Update globals.css | Full rewrite with authority/evidence/temporal color tokens |
| Update layout.tsx | Wrap in ThemeProvider, apply data-theme before render |
| Appearance settings tab | `app/settings/appearance/` |

### 9.4 Font Loading

Inter (UI) + JetBrains Mono (code/data). Loaded via Google Fonts with `display=swap`.

---

## 10. Typography & Motion System

### 10.1 Typography Scale

| Token | Size | Weight | Usage |
|-------|------|--------|-------|
| text-xs | 0.75rem | 400 | Captions, timestamps, metadata |
| text-sm | 0.875rem | 400 | Body, labels, inputs |
| text-base | 1rem | 400 | Primary content |
| text-md | 1.125rem | 500 | Subsection headings |
| text-lg | 1.25rem | 600 | Card titles, panel headings |
| text-xl | 1.5rem | 600 | Page titles |
| text-2xl | 2rem | 700 | Dashboard hero numbers |
| text-mono-xs | 0.6875rem | 400 | Inline code, IDs, hashes |
| text-mono-sm | 0.75rem | 400 | Code blocks, provenance chains |

### 10.2 Motion Tokens

| Token | Value | Usage |
|-------|-------|-------|
| --sv-duration-fast | 100ms | Hover, focus, micro-feedback |
| --sv-duration-base | 200ms | Expand, collapse, fade |
| --sv-duration-slow | 350ms | Modal enter, page transition |
| --sv-easing | `cubic-bezier(0.4, 0, 0.2, 1)` | Standard |
| --sv-easing-enter | `cubic-bezier(0.0, 0, 0.2, 1)` | Enter (fast out) |
| --sv-easing-exit | `cubic-bezier(0.4, 0, 1, 1)` | Exit (slow out) |
| --sv-easing-spring | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Springy |

### 10.3 Animation Library

| Animation | Duration | Easing | Usage |
|-----------|----------|--------|-------|
| sv-fade-in | 200ms | enter | Page content appear |
| sv-slide-up | 250ms | enter | Cards, modals, dropdowns |
| sv-scale-in | 200ms | spring | Modals, popovers |
| sv-collapse | 200ms | ease | Sidebar, accordions |
| sv-shimmer | 1.5s | linear | Skeleton loading |
| sv-ripple | 600ms | ease-out | Button click feedback |
| sv-pulse-soft | 2s | ease-in-out | Live indicators (sync, watcher) |
| sv-count-up | 400ms | ease-out | Dashboard stat numbers |

---

## 11. Layout Architecture

### 11.1 Structure

```
┌──────────────────────────────────────────────────────┐
│  AppShell                                             │
│  ┌───────────┬──────────────────────────────────────┐│
│  │ Sidebar   │  Header bar (breadcrumb + actions)   ││  48px
│  │ 224/56px  ├──────────────────────────────────────┤│
│  │ collaps.  │  Main content (scrollable)           ││
│  └───────────┴──────────────────────────────────────┘│
└──────────────────────────────────────────────────────┘
```

### 11.2 Responsive Breakpoints

| Breakpoint | Width | Sidebar | Content |
|------------|-------|---------|---------|
| Mobile | < 768px | Drawer | Full width |
| Tablet | 768–1024px | Collapsed | Full width |
| Desktop | 1024–1536px | Expanded | `max-w-5xl` |
| Wide | > 1536px | Expanded | `max-w-7xl` |

---

## 12. Sidebar Redesign

### 12.1 Structure

```
WORKSPACE
  Dashboard
  Projects
  Notifications

KNOWLEDGE
  Chat
  Knowledge Search
  Memory Explorer
  Facts
  Decisions
  Conflicts              ← NEW
  What Changed           ← NEW
  Procedures
  Timeline
  Provenance
  Graph

INGESTION
  Upload
  Sources
  Operations Center

OPERATIONS
  Board
  Agents
  Claims
  Tasks
  Supervisor
  Signals
  Usage
  Schedules

SYSTEM
  System Health
  Recovery Center        ← NEW (separate from Operations)
  Storage & Recovery     ← NEW (expanded from basic storage)
  Trust & Proof

VAULT SETTINGS
  General
  Memory Configuration   ← M1–M5 toggles, retrieval weights
  Retention
  Policies
  Security
  Appearance
  Developer

ACCOUNT
  Profile
```

### 12.2 Operation Indicators

Live state shown inline:
```
Sources     ● 3 connected
Watcher     ◉ Watching /path/to/vault
Sync        ✓ Up to date
Supervisor  ✓ Idle
```

### 12.3 Collapsed State

Icons only with tooltips on hover. Project section remains accessible via dropdown.

---

## 13. Navigation Restructure

### 13.1 Proposed Hierarchy

```
WORKSPACE
├── Dashboard
├── Projects
└── Notifications

KNOWLEDGE
├── Chat
├── Knowledge Search
├── Memory Explorer
├── Facts
├── Decisions
├── Conflicts
├── What Changed
├── Procedures
├── Context Packs        ← NEW
├── Timeline
├── Provenance
└── Graph

INGESTION
├── Upload
├── Sources
└── Operations Center

OPERATIONS
├── Board
├── Agents
├── Claims
├── Tasks
├── Supervisor
├── Signals
├── Usage
└── Schedules

SYSTEM
├── System Health
├── Recovery Center
├── Storage & Recovery
└── Trust & Proof

VAULT SETTINGS
├── General
├── Memory Configuration
├── Retention
├── Policies
├── Security
├── Appearance
├── Developer
└── Storage

ACCOUNT
└── Profile
```

---

## 14. Page Redesign Plans

> **All numerical values, content examples, and data shapes are ILLUSTRATIVE unless mapped to an existing backend/CLI/MCP data source.**

### 14.1 Dashboard → Command Center

**Backend:** `GET /api/v1/dashboard/stats`, `GET /api/v1/dashboard/health`, `GET /api/v1/projects`

**Three sections, three concerns:**

#### Services Health
```
SERVICES
  API            ● Healthy
  Database       ● Healthy
  Memory Service ● Healthy
  Ingestion      ● Healthy   1 job queued
  Storage        ● Healthy
  Watcher        ◉ Running   /path/to/vault
  CLI            ✓ Available
  MCP            ✓ Available
```

#### Knowledge State
```
KNOWLEDGE STATE
  Conversations    1,284    ← ILLUSTRATIVE
  Memory items     18,492   ← ILLUSTRATIVE
  Facts             7,832
  Decisions         1,204
  Procedures          82
  Conflicts            3    ⚠
  Graph nodes       9,821
  Graph edges      27,492
```

#### Activity Feed
```
RECENT ACTIVITY
  12 min ago  Conversation ingested       Claude export
  18 min ago  7 facts extracted           Session #82A
  22 min ago  Decision superseded         MongoDB → PostgreSQL
  1 hr ago    Graph rebuilt               9,821 nodes
```

### 14.2 Operations Center

**Route:** `/operations`

Surfaces the Core's orchestration layer — NOT a SaaS job queue.

```
RUNNING
  Watcher    ◉ Active   Watching /path/to/vault
  Sync       ✓ Up to date   Last: 15 min ago
  Supervisor ✓ Idle   No active tickets

RECOVERY
  Checkpoints
    Sep 5 14:32  Complete  48,221 rec  ✓
    Sep 5 09:15  Complete  47,980 rec  ✓
    Sep 4 23:00  Stale     47,500 rec  ⚠

HISTORY
  Completed syncs   12
  Imports           5
  Exports           2
```

### 14.3 What Changed (NEW)

**Route:** `/changed` or `/projects/{id}/changed`

> **PROPOSED** — depends on Core temporal/diff APIs not yet confirmed in WebApp backend.

This is one of the most valuable screens in the WebApp. SwarmVault tracks what changed in knowledge, not just what exists.

```
WHAT CHANGED — LAST 7 DAYS

+ 42 new facts           ← ILLUSTRATIVE
+ 8 decisions
↑ 17 facts strengthened
↓ 6 facts decayed
↻ 12 facts superseded
⚠ 3 contradictions detected
+ 2 procedures discovered

Sep 5
  PostgreSQL confidence    94 → 97
  MongoDB marked SUPERSEDED
  New procedure: "DB migration" discovered

Sep 4
  Redis architecture changed
  3 facts updated
  Decision: "Use PostgreSQL" created

Sep 3
  8 facts extracted from Session #82A
  Graph: 12 new edges
```

**This page requires backend APIs that return temporal diff data.** The Core tracks supersession and confidence changes, but the WebApp backend may not expose them yet. This should be marked as a **dependency** for implementation.

### 14.4 Conflicts (NEW)

**Route:** `/conflicts` or `/projects/{id}/conflicts`

> **PROPOSED** — depends on M5 conflict detection API.

M5 explicitly provides contradiction detection and conflict detection. The UI should surface this as a first-class experience.

```
CONFLICTS   3 unresolved

┌──────────────────────────────────────────────────────┐
│  ⚠  DATABASE CHOICE                         HIGH     │
│                                                      │
│  FACT A (ACTIVE)                                     │
│  "PostgreSQL is the production database"             │
│  Authority: VERIFIED  │  Confidence: 94%              │
│  Evidence: 4 sources  │  Scope: PROJECT              │
│                                                      │
│  FACT B (SUPERSEDED)                                 │
│  "MongoDB is the production database"                │
│  Authority: DECISION  │  Confidence: 81%              │
│  Evidence: 2 sources  │  Scope: PROJECT              │
│                                                      │
│  TIMELINE                                            │
│  Aug 12  MongoDB decision created                     │
│  Sep 4   PostgreSQL decision created → superseded     │
│                                                      │
│  IMPACT                                              │
│  7 dependent memories  │  3 graph edges  │  1 procedure │
│                                                      │
│  [Resolve] [View Evidence] [View Impact]              │
└──────────────────────────────────────────────────────┘
```

**Conflict resolution actions** (PROPOSED UI, depends on Core capability):
- Mark resolved (supersede older, confirm newer)
- View full evidence chain for both sides
- View impact (what else depends on each)
- Dismiss (acknowledge but don't resolve)

### 14.5 Context Packs (NEW)

**Route:** `/context-packs` or `/projects/{id}/context-packs`

> **PROPOSED** — depends on `build_context_pack` and `build_resume_packet` Core APIs.

Context packs exist partly to survive session compaction/context loss. The UI should make this explicit.

```
CONTEXT PACKS

┌──────────────────────────────────────────────────────┐
│  Resume: SwarmVault Architecture Work                 │
│  Generated: 4 min ago  │  ~18K tokens  │  PROJECT      │
│                                                      │
│  INCLUDED                                            │
│  ✓ 27 relevant facts                                 │
│  ✓ 8 decisions                                       │
│  ✓ 3 procedures                                      │
│  ✓ 12 graph relationships                            │
│  ✓ 4 unresolved questions                            │
│                                                      │
│  EVIDENCE                                            │
│  ✓ 38 source references  ✓ All provenance verified   │
│                                                      │
│  [Copy Pack] [Open as Session] [Regenerate]           │
└──────────────────────────────────────────────────────┘
```

**Context pack detail:**
```
RESUME PACK
Purpose: Resume SwarmVault architecture work

SCOPE
  Project: SwarmVault
  Sessions included: 14
  Time range: Aug 12 → Sep 5

KNOWLEDGE INCLUDED
  Facts             27    ← with authority badges
  Decisions          8    ← with evidence links
  Procedures         3    ← with step lists
  Graph edges       12    ← key relationships
  Open questions     4    ← unresolved items

EVIDENCE
  Source references  38
  All chains verified ✓
  Average authority  VERIFIED

FRESHNESS
  Generated: 4 min ago
  Staleness: Fresh (< 1 hour old)

USAGE
  [Copy to clipboard] — structured text for pasting into Claude
  [Open new session] — resume conversation with context
  [Regenerate] — rebuild with latest knowledge
```

### 14.6 Session Detail (Enhanced)

**Route:** `/projects/{id}/sessions/{sessionId}`

> **PROPOSED enhancement** — current session view is a basic list.

A session is the **origin of knowledge**. The detail page should show the causal chain from conversation to extracted knowledge.

```
SESSION #82A — "Architecture discussion"
Aug 20, 2026  │  Model: claude-sonnet-4-20250514  │  24 messages

OVERVIEW
  Messages: 24
  Duration: 47 min
  Model: claude-sonnet-4-20250514

EXTRACTED KNOWLEDGE
  8 facts    ← click to filter memory by this session
  2 decisions
  1 task
  1 procedure candidate
  4 graph relationships

MESSAGES
  [Full message list with expand/collapse]

EVIDENCE CHAIN
  Session → Messages → Extracted Facts → Graph Nodes

IMPACT
  7 downstream memories reference this session
  3 graph edges originate here
  1 procedure was extracted from this session

CHECKPOINT
  Last checkpoint: Sep 5, 14:32
  Compressed: Yes  │  Size: 4.2KB → 1.1KB

[Export] [Archive] [Delete from vault]
```

### 14.7 Chat Page (Enhanced)

```
┌──────────┬─────────────────────────┬───────────────┐
│          │                         │               │
│ Retrieval│    Messages             │ Context       │
│ Controls │                         │ Panel         │
│          │                         │               │
│ Mode     │  [User message]         │ Confidence    │
│ [Bal.]   │                         │ 92%           │
│          │  [AI response]          │               │
│ Scope    │  ████████ streaming      │ Authority     │
│ [Proj.]  │                         │ VERIFIED      │
│          │  [Evidence]              │               │
│ Include  │                         │ Sources       │
│ ☑ Facts  │                         │ 4             │
│ ☑ Decis. │                         │               │
│ ☑ Sess.  │                         │ [Provenance]  │
│ ☑ Proc.  │                         │ [Open Graph]  │
│ ☑ Graph  │                         │               │
│ ☐ Hist.  │                         │ Signals used: │
│          │                         │ BM25, Auth,   │
│ Min conf.│                         │ Conf, Recency │
│ [──●──]  │                         │               │
│ Max src. │                         │               │
│ [────●─] │                         │               │
├──────────┴─────────────────────────┴───────────────┤
│ [Type a message...                          ] [Send] │
└────────────────────────────────────────────────────┘
```

### 14.8 Storage & Recovery

**Route:** `/settings/storage` (enhanced from current basic upload page)

> **PROPOSED enhancement** — current storage page only handles upload/listing.

```
┌──────────────────────────────────────────────────────┐
│  Storage & Recovery                                  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  [Overview] [CAS] [Snapshots] [Integrity] [Lifecycle]│
├──────────────────────────────────────────────────────┤
│                                                      │
│  STORAGE HEALTH                                      │
│  CAS objects       18,421                             │
│  Chunks            42,883                             │
│  Snapshot count         8                             │
│  Orphaned chunks       12   ⚠                        │
│  Quarantined            2   ⚠                        │
│  Integrity check        ✓ Passed                     │
│                                                      │
│  Last backup            Sep 5, 14:32                 │
│  Last verification      Sep 5, 14:35                 │
│                                                      │
│  LIFECYCLE                                           │
│  HOT       42,100 objects    (recent, active)         │
│  WARM       8,200 objects    (infrequent access)      │
│  COLD       2,410 objects    (archive tier)           │
│  PURGED          0 objects   (reclaimed)              │
│                                                      │
│  BACKUPS                                             │
│  ┌──────────────────────────────────────────────┐    │
│  │  Sep 5 14:32  Full    18.4 GB  ✓ Valid       │    │
│  │  Sep 4 14:32  Full    18.3 GB  ✓ Valid       │    │
│  │  Sep 3 14:32  Full    18.2 GB  ✓ Valid       │    │
│  │  ...                                        │    │
│  │  [Create Backup] [Restore from...]            │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  QUARANTINE                                          │
│  ┌──────────────────────────────────────────────┐    │
│  │  2 objects quarantined                         │    │
│  │  [Review] [Restore] [Purge]                    │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 14.9 Recovery Center

**Route:** `/recovery`

> **PROPOSED** — separate from Operations. Recovery = what went wrong and how to resume.

```
┌──────────────────────────────────────────────────────┐
│  Recovery Center                                     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  CHECKPOINTS                                         │
│  ┌──────────────────────────────────────────────┐    │
│  │  Sep 5 14:32  Complete    48,221 records  ✓   │    │
│  │  Sep 5 09:15  Complete    47,980 records  ✓   │    │
│  │  Sep 4 23:00  Stale       47,500 records  ⚠    │    │
│  │  Sep 3 18:00  Failed      47,200 records  ✕    │    │
│  │                                               │    │
│  │  [Resume from stale] [Resume from failed]      │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  WAL REPAIR                                          │
│  Last WAL check: Sep 5, 14:35  ✓ Clean               │
│                                                      │
│  IMPORT / EXPORT                                     │
│  [Import vault] [Export vault] [Export as JSONL]      │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 14.10 Procedures (Enhanced)

**Route:** `/procedures`

> **PROPOSED upgrade** from current basic list to first-class Executable Knowledge.

**List:**
```
PROCEDURES   12 registered

┌──────────────────────────────────────────────────────┐
│  Database Migration Procedure                        │
│  Confidence: 94%  │  CERTIFIED  │  12 uses           │
│  Project: Screenshot Project  │  Last used: Sep 5    │
│  [View Steps] [Use] [Evidence]                        │
└──────────────────────────────────────────────────────┘
```

**Detail:**
```
DATABASE MIGRATION PROCEDURE
Migrate schema changes to production with rollback

┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐
│ Confid.  │ │ Authority│ │ Uses    │ │ Project│
│  94%    │ │ CERTIFIED│ │  12     │ │ Screen.│
└──────────┘ └──────────┘ └──────────┘ └────────┘

STEPS
1. Create migration file in migrations/
2. Run `alembic revision --autogenerate`
3. Review generated migration
4. Run `alembic upgrade head`
5. Verify with `alembic current`
6. If failure: `alembic downgrade -1`

INPUTS
  Project context, migration name

OUTPUTS
  Applied migration, verification result

EVIDENCE (12 sessions)
  Session #82A — Score: 96%
  Session #78C — Score: 91%

RELATED
  Facts: 4  │  Decisions: 2  │  Graph: 3 nodes

[Use Procedure] [View in Graph] [View Evidence]
```

> **Note:** "Use Procedure" produces a context packet (structured prompt + steps + evidence). It does not execute anything.

### 14.11 System Health

**Route:** `/settings/health`

```
SERVICES
  API            ● Healthy
  Database       ● Healthy
  Memory Service ● Healthy
  Ingestion      ● Healthy
  Storage        ● Healthy
  CLI            ✓ Available
  MCP            ✓ Available
  Watcher        ◉ Running

MODULES
  M0 Foundation     ✅ Loaded
  M1 Memory Upgrade  ✅ Loaded
  M2 Structured Mem  ✅ Loaded
  M3 Temporal Truth  ✅ Loaded
  M4 Graph           ✅ Loaded
  M5 Intelligence    ✅ Loaded

PERFORMANCE
  Avg retrieval:    180ms
  Avg ingestion:    4.2s
  Queue depth:      2
  Failed (24h):     0
  Storage:          18.4 GB
```

### 14.12 Memory Explorer (Enhanced)

**Route:** `/projects/{id}/memory`

Cards with correct authority levels (6), correct scope labels (5), and provenance links.

```
┌──────────────────────────────────────────────��
│ PostgreSQL is the production database        │
│                                               │
│ FACT  │  VERIFIED  │  94%  │  PROJECT scope  │
│ Updated Sep 4  │  4 sources  │  17 recalls    │
│ [Evidence] [History] [View in Graph]          │
└──────────────────────────────────────────────┘
```

**Authority badges (6 levels):**

| Level | Color | Meaning |
|-------|-------|---------|
| UNVERIFIED | Gray | Raw extraction, not validated |
| INFERRED | Amber | Deduced from evidence |
| OBSERVED | Blue | Seen in source material |
| DECISION | Purple | Explicitly decided |
| VERIFIED | Green | Cross-checked and confirmed |
| CERTIFIED | Indigo | Fully verified, high trust |

> Authority ≠ Confidence. Display both independently.

---

## 15. Trust & Evidence UX Model

### 15.1 The Two Axes

The UI must always represent evidence quality and authority as **separate, independent dimensions**.

```
MEMORY ITEM
├── Identity
│   ├── Type (fact/decision/task/preference/observation/procedure/entity)
│   ├── Content
│   └── Scope + Scope ID
│
├── Authority (discrete level)
│   UNVERIFIED → INFERRED → OBSERVED → DECISION → VERIFIED → CERTIFIED
│
├── Confidence (float 0.0–1.0)
│   Independent of authority level
│
├── Temporal Status
│   ACTIVE / SUPERSEDED / ARCHIVED
│
└── Evidence Chain
    └── INGESTED → PROCESSED → INTEGRATED → PROVEN
```

### 15.2 Evidence Chain Display (Pervasive)

Every knowledge item shows its evidence class at a glance:

| Evidence Class | Icon | Meaning |
|---------------|------|---------|
| INGESTED | `○` Gray dot | Raw input, not yet processed |
| PROCESSED | `◐` Half dot | Parsed and redacted, not yet linked |
| INTEGRATED | `◑` Mostly filled | Added to store, sources partial |
| PROVEN | `●` Full dot | Fully verified, complete chain |

### 15.3 Evidence Modal

Clicking `[Evidence]` on any item opens a consistent modal:

```
┌──────────────────────────────────────────────────────┐
│  Evidence Chain                            [Close]   │
├──────────────────────────────────────────────────────┤
│                                                      │
│  "PostgreSQL is the production database"              │
│                                                      │
│  AUTHORITY: VERIFIED   CONFIDENCE: 94%               │
│  SCOPE: PROJECT   STATUS: ACTIVE   EVIDENCE: PROVEN   │
│                                                      │
│  ┌─ 1. Original Source ──────────────────────────┐  │
│  │  Claude conversation export                    │  │
│  │  File: claude-conv-2026-09-04.json             │  │
│  │  CAS: a3f2...8c1d  ✓ Verified                  │  │
│  │  Redacted: ✓ No sensitive data                 │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌─ 2. Session ──────────────────────────────────┐  │
│  │  #82A — "Architecture discussion"              │  │
│  │  Messages: 24  │  Model: claude-sonnet-4       │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌─ 3. Message ──────────────────────────────────┐  │
│  │  "Let's use PostgreSQL for production..."       │  │
│  │  Role: assistant   Relevance: 96%               │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌─ 4. Extracted Memory ─────────────────────────┐  │
│  │  "PostgreSQL is the production database"        │  │
│  │  Authority: VERIFIED  │  Confidence: 94%        │  │
│  │  Recalls: 17  │  Created: Aug 12  │  Upd: Sep 4│  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  [View in Graph] [View Session] [View Timeline]       │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 15.4 Evidence in Context

**Memory card (abbreviated):**
```
● PROVEN  │  VERIFIED  │  94%  │  PROJECT
4 sources  [Evidence]
```

**Search result:**
```
VERIFIED · 94% · PROVEN
4 evidence sources  [View chain]
```

**Chat answer:**
```
Confidence: 94%
4 sources used  [Why this answer?]
```

---

## 16. Provenance as a Pervasive UX Pattern

### 16.1 Design Principle

Provenance (M4) is a Core value proposition. It should appear everywhere, not only in `/provenance`.

### 16.2 Provenance Entry Points

Every knowledge card, search result, and chat answer includes a lightweight provenance indicator:
- Evidence class dot (INGESTED/PROCESSED/INTEGRATED/PROVEN)
- Source count ("4 sources")
- `[Evidence]` link → opens evidence modal

### 16.3 Dedicated Provenance Page

**Route:** `/provenance`

Full provenance explorer — search, filter, and traverse chains across the entire vault.

### 16.4 Evidence Modal

As specified in §15.3 — consistent across all contexts.

---

## 17. Component Library Gaps

### 17.1 Missing Components

| Component | Purpose | Priority |
|-----------|---------|----------|
| Collapsible | Animated expand/collapse | P0 |
| Tabs | Tabbed navigation | P0 |
| Toast | Non-blocking notifications | P0 |
| Tooltip | Hover/focus tooltips | P1 |
| Progress | Progress bars | P1 |
| Avatar | User avatar | P1 |
| Dropdown | Context menus | P1 |
| Breadcrumb | Navigation breadcrumbs | P1 |
| DataTable | Sortable/filterable table | P1 |
| StatCard | Dashboard statistics | P0 |
| HealthIndicator | Service/health status | P1 |
| SearchInput | Debounced search | P1 |
| Badge variants | Authority (6), evidence class, temporal status | P1 |
| CodeBlock | Monospace with copy | P2 |
| EvidenceChain | Provenance chain visualization | P1 |
| ConflictCard | Conflict/contradiction display | P1 |
| ContextPack | Context/resume pack display | P1 |
| ProcedureRunner | Procedure execution context | P1 |
| RecoveryPanel | Checkpoint/recovery display | P1 |

### 17.2 Authority Badge Configuration

```tsx
const AUTHORITY_CONFIG = {
  UNVERIFIED: { color: 'gray',   label: 'Unverified' },
  INFERRED:   { color: 'amber',  label: 'Inferred' },
  OBSERVED:   { color: 'blue',   label: 'Observed' },
  DECISION:   { color: 'purple', label: 'Decision' },
  VERIFIED:   { color: 'green',  label: 'Verified' },
  CERTIFIED:  { color: 'indigo', label: 'Certified' },
};
```

### 17.3 Evidence Class Configuration

```tsx
const EVIDENCE_CONFIG = {
  INGESTED:    { color: 'gray',   label: 'Ingested',    icon: '○' },
  PROCESSED:   { color: 'blue',   label: 'Processed',   icon: '◐' },
  INTEGRATED:  { color: 'purple', label: 'Integrated',  icon: '◑' },
  PROVEN:      { color: 'green',  label: 'Proven',      icon: '●' },
};
```

### 17.4 Temporal Status Configuration

```tsx
const TEMPORAL_CONFIG = {
  ACTIVE:     { color: 'green',  label: 'Active' },
  SUPERSEDED: { color: 'amber',  label: 'Superseded' },
  ARCHIVED:   { color: 'gray',   label: 'Archived' },
};
```

---

## 18. Accessibility & Responsive Design

### 18.1 Focus Management

```css
:focus-visible {
  outline: 2px solid var(--sv-accent);
  outline-offset: 2px;
  border-radius: var(--sv-radius-sm);
}
*:focus:not(:focus-visible) { outline: none; }
```

### 18.2 Skip Navigation

```tsx
<a href="#main-content" className="sr-only focus:not-sr-only ...">
  Skip to main content
</a>
```

### 18.3 Touch Targets

All interactive elements ≥ 44×44px (WCAG 2.5.5).

### 18.4 Heading Hierarchy

Each page: exactly one `<h1>`, proper `<h2>` → `<h3>` cascade.

---

## 19. Implementation Roadmap

### 19.1 Phase 0: Foundation

| Task | Effort |
|------|--------|
| Font loading (Inter + JetBrains Mono) | 1h |
| CSS custom properties (full token set) | 2h |
| ThemeProvider + ThemeSwitcher | 3h |
| Collapsible component | 2h |
| Tabs component | 2h |
| Toast component + replace alert() | 3h |
| focus-visible styles | 1h |
| Tooltip component | 2h |
| Breadcrumb component | 1h |
| Touch target audit + fixes | 2h |
| Heading hierarchy audit | 2h |

**Total: ~22h | Risk: Low**

### 19.2 Phase 1: Core UX

| Task | Effort | Depends On |
|------|--------|-----------|
| Sidebar restructure (sections, icons, indicators) | 4h | Collapsible, Tooltip |
| Header bar + breadcrumbs | 3h | Breadcrumb |
| Dashboard → Command Center | 8h | StatCard, HealthIndicator |
| Chat: Retrieval controls + context panel | 7h | Collapsible, Toggle |
| Enhanced evidence modal | 4h | EvidenceChain |
| Memory: Category tabs, authority badges, detail page | 8h | Tabs, Badge variants |
| Knowledge Search: Signal controls | 3h | Slider, CheckboxGroup |

**Total: ~37h | Risk: Medium**

### 19.3 Phase 2: New Pages

| Task | Effort | Depends On |
|------|--------|-----------|
| Operations Center | 5h | HealthIndicator |
| Recovery Center | 4h | RecoveryPanel |
| Storage & Recovery (enhanced) | 5h | Tabs, Progress |
| Conflicts page | 5h | ConflictCard |
| What Changed page | 4h | Timeline, Diff |
| Context Packs page | 4h | ContextPack |
| Procedures (first-class) | 5h | ProcedureRunner |
| Trust & Proof page | 4h | EvidenceChain |
| Session detail (enhanced) | 5h | Collapsible, Tabs |
| Provenance page | 4h | EvidenceChain, Breadcrumb |
| Settings restructure | 8h | Tabs |
| Memory Configuration settings | 3h | Form, Slider |
| Retention settings | 3h | Form |
| MCP Sessions viewer | 4h | DataTable |

> **Note:** Phase 2 items marked "depends on backend APIs not yet confirmed" (What Changed, Context Packs, MCP Sessions) should be implemented behind feature flags or after backend API confirmation.

**Total: ~57h | Risk: Medium-High (new pages, new API integrations)**

### 19.4 Phase 3: Polish

| Task | Effort |
|------|--------|
| Animation system (shimmer, ripple, transitions) | 4h |
| Hover micro-interactions | 3h |
| Page transition animations | 3h |
| Loading choreography | 3h |
| Keyboard navigation audit | 4h |
| ARIA labels + screen reader testing | 4h |
| Responsive design refinement | 4h |
| Empty state illustrations | 3h |
| Color contrast audit | 2h |

**Total: ~30h | Risk: Low**

### 19.5 Summary

| Phase | Hours | Risk | Description |
|-------|-------|------|-------------|
| 0: Foundation | 22h | Low | Infrastructure |
| 1: Core UX | 37h | Medium | High-impact pages |
| 2: New Pages | 57h | Medium-High | Completes coverage (some depend on backend) |
| 3: Polish | 30h | Low | Refinement |
| **Total** | **146h** | | ~3.5 weeks @ 1 dev |

> **Sequencing note:** Phase 1 should complete before Phase 2 begins. Within Phase 2, Operations Center and Recovery Center should be built first (they don't depend on new backend APIs), followed by pages that depend on confirmed backend endpoints. What Changed, Context Packs, and MCP Sessions should be deferred until their backend APIs are confirmed.

---

## 20. Appendices

### 20.1 Backend Endpoint → UI Page Mapping

| Endpoint | Method | Current UI | Proposed UI | Backend Verified? |
|----------|--------|-----------|-------------|-------------------|
| `GET /api/v1/dashboard/stats` | GET | ❌ | Command Center stats | ✅ |
| `GET /api/v1/dashboard/health` | GET | ❌ | Command Center health | ✅ |
| `GET /api/v1/provenance/` | GET | ❌ | Provenance page | ✅ |
| `GET /api/v1/provenance/{id}` | GET | ❌ | Evidence modal | ✅ |
| `POST /api/v1/feedback/` | POST | ❌ | Chat feedback | ✅ |
| `GET /api/v1/memory/{id}` | GET | ❌ | Memory detail | ✅ |
| `PATCH /api/v1/memory/{id}` | PATCH | ❌ | Memory edit | ✅ |
| `GET /api/v1/ingest/sources` | GET | ⚠️ Partial | Sources management | ✅ |
| `GET /api/v1/ingest/graph` | GET | ⚠️ Basic | Graph Explorer | ✅ |
| `GET /api/v1/ingest/status/{id}` | GET | ❌ | Operations Center | ✅ |
| Temporal diff/changes | ? | ❌ | What Changed | ❌ **Needs API** |
| `build_context_pack` | ? | ❌ | Context Packs | ❌ **Needs API** |
| Conflict detection | ? | ❌ | Conflicts | ❌ **Needs API** |
| MCP session history | ? | ❌ | MCP Sessions | ❌ **Needs API** |
| `GET /api/v1/audit/` | GET | ❌ | ⚠️ Out of scope | ✅ (but out of scope) |
| `POST /api/v1/api-keys/` | POST | ❌ | ⚠️ Out of scope | ✅ (but out of scope) |

### 20.2 Navigation ↔ Backend API Mapping

| Nav Section | Pages | Backend APIs Used | APIs Not Covered |
|-------------|-------|-------------------|-----------------|
| Workspace | Dashboard, Projects, Notifications | dashboard/stats, dashboard/health, projects | dashboard/activity |
| Knowledge | Chat, Search, Memory, Facts, Decisions, Conflicts, What Changed, Procedures, Context Packs, Timeline, Provenance, Graph | chat/stream, memory/*, ingest/sources, ingest/graph, provenance/* | temporal diff, context packs, conflicts |
| Ingestion | Upload, Sources, Operations | ingest/* | — |
| Operations | Board, Agents, Claims, Tasks, Supervisor, Signals, Usage, Schedules | — | **No WebApp backend APIs confirmed** |
| System | Health, Recovery, Storage, Trust & Proof | dashboard/health, storage/* | recovery/*, trust/* |
| Vault Settings | General, Memory Config, Retention, Policies, Security, Appearance, Developer, Storage | config/*, policy/*, storage/* | retention/*, memory config |
| Account | Profile | auth/me | — |

### 20.3 M0–M5 Module → UI Feature Mapping

| Module | Core Capability | UI Pages | Backend Confirmed? |
|--------|----------------|----------|--------------------|
| M0 | Parse, redact, deduplicate, persist | Upload, Sources | ✅ |
| M1 | Preserve, compress, resume | Session detail, Operations | ✅ Partial |
| M2 | Structured facts, authority, confidence, scope | Memory Explorer, Facts, Decisions | ✅ |
| M3 | Temporal truth, supersession, decay, timeline | Timeline, What Changed | ✅ Partial |
| M4 | Graph, provenance, case memory, CAS | Graph, Provenance, Evidence modal | ✅ |
| M5 | Ranking, conflict detection, procedural memory, impact analysis, activation | Search, Chat, Conflicts, Procedures, What Changed | ⚠️ Partial (ranking ✅, conflicts ❌) |

### 20.4 Agent / MCP Model (VERIFIED)

The architecture defines:

| Concept | Description | UI Surface |
|---------|-------------|-----------|
| **Agent** | An external process (Claude Code, other MCP clients) that operates on the vault | Agents list — shows connected MCP clients |
| **Platform** | The runtime environment (Claude Code, CLI, WebApp) | Shown in agent detail |
| **Model** | The LLM model used by the agent (claude-sonnet-4, etc.) | Shown in session/agent detail |
| **Effort** | Computational effort spent per operation | Usage page |
| **Ticket** | A unit of work in the orchestration system | Board page |
| **Claim** | An agent's assertion about knowledge | Claims page |
| **Release** | A batch of completed work | Board page |
| **Supervisor** | Orchestrator that monitors and dispatches | Supervisor page |
| **Signal** | Control signal between components | Signals page |
| **Usage** | Tracking of agent/platform/model/effort | Usage page |
| **Schedule** | Planned operations | Schedules page |
| **Plan continuation** | Resuming interrupted work plans | Context Packs |

**UI implication:** The "Agents" page should show connected MCP clients, their recent activity, models used, and effort consumed. It's not about chatbot agents — it's about **which processes are operating on the vault**.

### 20.5 MCP Session Model

The architecture documents that MCP sessions should be visible in the WebApp:

```
MCP SESSIONS

┌──────────────────────────────────────────────────────┐
│  Claude Code                    Active  │  2h ago     │
│  Model: claude-sonnet-4-20250514                     │
│  Sessions: 14  │  Tokens: 284,500  │  Tools: 47     │
│  [View Sessions]                                     │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  Claude Code (previous)                Ended │ 5h ago │
│  Model: claude-opus-4-20250514                       │
│  Sessions: 8  │  Tokens: 412,000  │  Tools: 23      │
│  [View Sessions]                                     │
└──────────────────────────────────────────────────────┘
```

> **PROPOSED** — depends on MCP session history API. The architecture implies this data exists but the WebApp backend may not expose it.

---

*End of Frontend Redesign Document v1.2.0*
