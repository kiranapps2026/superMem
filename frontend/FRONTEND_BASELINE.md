# SwarmVault WebApp — Frontend Baseline
**Date:** 2026-09-04
**Framework:** Next.js 15 (App Router) + React 18 + TypeScript 5
**Styling:** Tailwind CSS 3.4
**Icons:** lucide-react 0.468
**Dev server:** `npm run dev` → port 3000

---

## Current Architecture

```
frontend/
  src/
    app/
      layout.tsx          # Root layout: AuthProvider + Sidebar + main
      page.tsx            # Redirect to /dashboard or /auth/login
      globals.css         # Dark theme CSS variables
      auth/
        login/page.tsx    # Login form
        register/page.tsx # Registration form
      dashboard/
        page.tsx          # Workspace dashboard + project creation
      projects/
        page.tsx          # Project listing
        [id]/
          layout.tsx      # Project sidebar + settings/edit/delete
          chat/page.tsx   # SSE chat with sources + evidence modal
          ingest/page.tsx # File ingestion
          sessions/page.tsx # Session list
          sessions/[sessionId]/page.tsx # Session detail
          memory/page.tsx # Memory list with filter
          facts/page.tsx  # Facts list
          decisions/page.tsx # Decisions list
          timeline/page.tsx # Timeline view
          search/page.tsx # Unified search
          graph/page.tsx  # Knowledge graph
      settings/
        page.tsx          # Workspace settings
    components/
      Sidebar.tsx         # Collapsible sidebar with nav
    hooks/
      useAuth.tsx         # Auth context + JWT management
      useSSE.tsx          # SSE streaming hook
    lib/
      api.ts              # Centralized API client
    types/
      api.ts              # TypeScript interfaces matching backend schemas
```

## Existing Routes

| Route | Component | Status |
|-------|-----------|--------|
| `/` | Redirect | Complete |
| `/auth/login` | LoginPage | Complete |
| `/auth/register` | RegisterPage | Complete |
| `/dashboard` | DashboardPage | Complete |
| `/projects` | ProjectsPage | Complete |
| `/projects/[id]` | ProjectLayout | Complete |
| `/projects/[id]/chat` | ChatPage | Complete |
| `/projects/[id]/sessions` | SessionsPage | Complete |
| `/projects/[id]/sessions/[sessionId]` | SessionDetailPage | Complete |
| `/projects/[id]/memory` | MemoryPage | Complete |
| `/projects/[id]/facts` | FactsPage | Complete |
| `/projects/[id]/decisions` | DecisionsPage | Complete |
| `/projects/[id]/timeline` | TimelinePage | Complete |
| `/projects/[id]/search` | SearchPage | Complete |
| `/projects/[id]/graph` | GraphPage | Complete |
| `/projects/[id]/ingest` | IngestPage | Complete |
| `/projects/[id]/provenance` | ProvenancePage | Complete |
| `/settings` | SettingsPage | Complete |

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| next | ^15.0.0 | Framework |
| react | ^18.3.0 | UI library |
| react-dom | ^18.3.0 | DOM renderer |
| lucide-react | ^0.468.0 | Icons |
| typescript | ^5.0.0 | Type checking |
| tailwindcss | ^3.4.0 | Styling |
| @playwright/test | ^1.62.1 | E2E testing |

No additional runtime dependencies needed.

## API Client (lib/api.ts)

- Centralized HTTP client with JWT auth
- Token storage in localStorage
- Automatic token refresh on 401
- SSE streaming generator (`streamChat`)
- Multipart file upload with progress
- CRUD helpers: `apiGet`, `apiPost`, `apiPatch`, `apiDelete`
- Environment: `NEXT_PUBLIC_API_URL` or default `http://localhost:8000`

## Authentication (useAuth.tsx)

- Context-based auth state
- Auto-restore session on app load (`/auth/me`)
- Login, register, logout methods
- Token lifecycle managed by api.ts
- localStorage token storage

## Design System (globals.css)

Dark theme with CSS variables:
```css
--bg-primary: #0a0a0f      /* page background */
--bg-secondary: #111118    /* cards, panels */
--bg-tertiary: #1a1a24     /* elevated elements */
--border: #1f1f2e          /* subtle borders */
--accent: #6366f1          /* indigo primary */
--accent-hover: #818cf8    /* indigo lighter */
```

Tailwind classes used throughout with these variables. No component library.

## Type Coverage (types/api.ts)

Covers all backend schemas: auth, workspace, projects, sessions, chat, memory, facts, decisions, timeline, graph, search, sources, ingestion, provenance, feedback, API keys, invitations.

## Reusable Infrastructure

| Asset | Value |
|-------|-------|
| API client with auth + refresh | HIGH — keep as-is |
| Auth context | HIGH — keep as-is |
| Type definitions | HIGH — keep, extend |
| Sidebar component | HIGH — keep, extend |
| Dark theme CSS | HIGH — keep, extend |
| SSE streaming in chat | HIGH — keep |
| Chat UI (sources + evidence) | HIGH — keep |

## Known Gaps vs. Master Prompt

| Gap | Severity | Master Prompt Section |
|-----|----------|----------------------|
| No shared loading/error components | P2 | Phases 7, 24, 25 |
| No design system components (Card, Badge, Skeleton, etc.) | P2 | Phase 7 |
| Memory page uses `any[]` | P2 | Phase 3 |
| No feature hooks layer (UI → feature/domain hooks → API) | P2 | Phase 2 |
| No API client per-domain (all in api.ts) | P3 | Phase 2 |
| No accessibility attributes (aria, labels) | P2 | Phase 27 |
| No test infrastructure in frontend | P3 | Phase 32 |
| No golden journey E2E | P3 | Phase 33 |
| No .env.example for frontend | P3 | Phase 4 |
| Graph page needs implementation detail | P2 | Phase 18 |
| Provenance page needs depth | P2 | Phase 19 |
| Settings page needs completeness | P2 | Phase 23 |
| Storage page missing | P2 | Phase 21 |
| API Keys page missing | P2 | Phase 22 |
| No formal error handling component | P2 | Phase 24 |
| No responsive mobile nav | P3 | Phase 26 |
