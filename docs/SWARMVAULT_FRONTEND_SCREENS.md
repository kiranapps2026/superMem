# SwarmVault Frontend Screen Manifest

**Version:** 1.0.0
**Date:** 2026-09-24
**Branch:** recovery/restore-2026-09-24
**Authority:** Source code is the single source of truth. This document is authoritative only when it matches source.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Application Shell](#2-application-shell)
3. [Screen Catalog](#3-screen-catalog)
4. [Component Inventory](#4-component-inventory)
5. [State Management](#5-state-management)
6. [Data Fetching](#6-data-fetching)
7. [Routing Map](#7-routing-map)
8. [Theming](#8-theming)
9. [Build & Deploy](#9-build--deploy)
10. [E2E Test Coverage](#10-e2e-test-coverage)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Next.js 15 App Router                                │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                          Layout Hierarchy                             │  │
│  │                                                                       │  │
│  │  RootLayout                                                           │  │
│  │    └── ThemeProvider                                                   │  │
│  │      └── AuthProvider                                                  │  │
│  │        └── AppShell                                                    │  │
│  │          └── {children}                                                │  │
│  │            ├── AuthLayout (login, register)                             │  │
│  │            └── ProjectLayout (all /projects/{id}/* pages)              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │    Pages     │  │  Components  │  │   Hooks      │  │  Features      │  │
│  │  (21 files)  │  │  (13 files)  │  │  (5 files)   │  │  (6 files)     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └───────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Data Layer                                    │  │
│  │  lib/api.ts     (fetch wrapper with auth + refresh)                   │  │
│  │  lib/errors.ts  (API error typing)                                    │  │
│  │  types/api.ts   (TypeScript interfaces)                               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
    ┌───────────────────────┐    ┌──────────────────────┐    ┌─────────────┐
    │  Backend API          │    │  Theme (CSS vars)     │    │  Icons       │
    │  localhost:8000       │    │  data-theme attribute │    │  lucide-react│
    │  /api/v1/*            │    │  light / dark         │    │  (32 icons)  │
    └───────────────────────┘    └──────────────────────┘    └─────────────┘
```

### 1.1 Tech Stack

| Layer | Technology | Purpose | Source File |
|---|---|---|---|
| Framework | Next.js 15 (App Router) | React meta-framework | frontend/package.json |
| Runtime | Node.js | JS runtime | — |
| Language | TypeScript 5.x | Type safety | tsconfig.json |
| Styling | CSS Modules + CSS Variables | Scoped styles, theming | globals.css |
| Icons | lucide-react | Icon set | 8 screen files |
| State | React Context + useState | Client state | hooks/ |
| Data | fetch + Context | API communication | lib/api.ts |
| Routing | App Router | File-system routing | app/ |
| Auth | JWT in localStorage | Token storage | lib/api.ts |
| Testing | Playwright | E2E tests | e2e/ |
| Build | Turbopack | Dev server | next.config.js |

### 1.2 Directory Structure

```
frontend/src/
  app/
    auth/
      login/page.tsx          ← Public auth
      register/page.tsx       ← Public auth
    dashboard/page.tsx        ← Protected home
    layout.tsx                ← Root layout (providers)
    page.tsx                  ← Landing page (public)
    projects/
      [id]/
        chat/page.tsx         ← Protected project
        decisions/page.tsx    ← Protected project
        facts/page.tsx        ← Protected project
        graph/page.tsx        ← Protected project
        ingest/page.tsx       ← Protected project
        layout.tsx            ← Project layout (sidebar)
        memory/page.tsx       ← Protected project
        provenance/page.tsx   ← Protected project
        search/page.tsx       ← Protected project
        section/...           ← (not present)
        session/...           ← (not present)
        settings/page.tsx     ← Protected project
        timeline/page.tsx     ← Protected project
      page.tsx                ← Protected project list
    section/...               ← (not present)
    session/...               ← (not present)
    settings/
      api-keys/page.tsx       ← Protected settings
      page.tsx                ← Protected settings
      profile/page.tsx        ← Protected settings
      storage/page.tsx        ← Protected settings
  components/
    Sidebar.tsx               ← Global navigation
    ui/                       ← 14 UI components + 1 hook (useClipboard)
  features/
    apiKeys/useApiKeys.ts     ← Custom hook
    chat/useChat.ts           ← Custom hook
    graph/useGraph.ts         ← Custom hook
    ingest/useIngest.ts       ← Custom hook
    memory/useMemory.ts       ← Custom hook
    projects/useProjects.ts   ← Custom hook
    search/useSearch.ts       ← Custom hook
  hooks/
    AppShell.tsx              ← Shell wrapper
    AuthRedirect.tsx          ← Route guard
    useAuth.tsx               ← Auth context
    useSSE.tsx                ← Server-sent events
    useTheme.tsx              ← Theme context
  lib/
    api.ts                    ← Fetch wrapper
    errors.ts                 ← Error types
  types/
    api.ts                    ← TypeScript interfaces
```

---

## 2. Application Shell

### 2.1 Provider Tree

| Provider | Context | Purpose | Source File |
|---|---|---|---|
| `ThemeProvider` | `data-theme` attribute | Light/dark mode | hooks/useTheme.tsx |
| `AuthProvider` | `user`, `login`, `logout`, `loading` | Authentication state | hooks/useAuth.tsx |
| `AppShell` | Layout wrapper | Sidebar + content area | hooks/AppShell.tsx |

### 2.2 Theme System

| Aspect | Detail | Source File |
|---|---|---|
| Storage | `localStorage.sv_theme` | hooks/useTheme.tsx |
| Attribute | `data-theme="light"` or `data-theme="dark"` | hooks/useTheme.tsx |
| Init | Inline script in `<head>` (SSR-safe) | app/layout.tsx:17-20 |
| CSS vars | `--bg-primary`, `--text-primary`, etc. | globals.css |

### 2.3 Authentication State

| State | Value | Meaning | Source File |
|---|---|---|---|
| `loading` | `true` | Checking stored tokens | hooks/useAuth.tsx |
| `loading` | `false` | Auth check complete | hooks/useAuth.tsx |
| `user` | `User \| null` | Logged-in user or null | hooks/useAuth.tsx |
| `login(email, password)` | Function | Performs login, stores tokens | hooks/useAuth.tsx |
| `logout()` | Function | Clears tokens, resets state | hooks/useAuth.tsx |
| `register(...)` | Function | Creates account via API | hooks/useAuth.tsx |

### 2.4 Token Management

| Operation | Storage Key | Source File |
|---|---|---|
| Store tokens | `localStorage.sv_tokens` | lib/api.ts:31-33 |
| Retrieve access token | `localStorage.sv_tokens.access_token` | lib/api.ts:3-8 |
| Auto-refresh | `POST /api/v1/auth/refresh` | lib/api.ts:11-28 |
| Clear tokens | `localStorage.removeItem('sv_tokens')` | lib/api.ts:30 |

### 2.5 API Client

| Feature | Implementation | Source File |
|---|---|---|
| Base URL | `NEXT_PUBLIC_API_URL` or `http://localhost:8000` | lib/api.ts:1 |
| Auth header | `Authorization: Bearer {token}` | lib/api.ts:44 |
| Auto-refresh | On 401, call refresh endpoint, retry once | lib/api.ts:50-58 |
| Token clear | On refresh failure, redirect to login | lib/api.ts:54-57 |
| Content-Type | JSON (auto, unless FormData) | lib/api.ts:40-43 |
| Error handling | Parse error JSON, throw Error | lib/api.ts:60+ |

---

## 3. Screen Catalog

### 3.1 Public Screens (3)

| # | Route | Component | Purpose | Data Fetch | Source File |
|---|---|---|---|---|---|
| 1 | `/` | `LandingPage` | Public landing | Static | app/page.tsx |
| 2 | `/auth/login` | `LoginPage` | Sign in | `login()` AuthProvider | app/auth/login/page.tsx |
| 3 | `/auth/register` | `RegisterPage` | Sign up | `register()` AuthProvider | app/auth/register/page.tsx |

### 3.2 Protected Static Screens (6)

| # | Route | Component | Purpose | Data Fetch | Source File |
|---|---|---|---|---|---|
| 4 | `/dashboard` | `DashboardPage` | Home + project creation | `GET /workspace`, `GET /dashboard/`, `GET /projects` | app/dashboard/page.tsx |
| 5 | `/projects` | `ProjectsListPage` | Project list | `GET /projects` | app/projects/page.tsx |
| 6 | `/settings` | `SettingsLayoutPage` | Settings hub | Static + redirect | app/settings/page.tsx |
| 7 | `/settings/api-keys` | `APIKeysPage` | API key management | `GET/POST/DELETE /api-keys/` | app/settings/api-keys/page.tsx |
| 8 | `/settings/profile` | `ProfilePage` | Profile edit | `GET /auth/me`, `PATCH /auth/me` | app/settings/profile/page.tsx |
| 9 | `/settings/storage` | `StoragePage` | Storage config | Static | app/settings/storage/page.tsx |

### 3.3 Protected Dynamic Screens (11 project pages)

| # | Route | Component | Purpose | Data Fetch | Source File |
|---|---|---|---|---|---|
| 10 | `/projects/{id}/chat` | `ChatPage` | AI chat interface | `POST /chat/` | app/projects/[id]/chat/page.tsx |
| 11 | `/projects/{id}/decisions` | `DecisionsPage` | Extracted decisions | `GET /ingest/decisions` | app/projects/[id]/decisions/page.tsx |
| 12 | `/projects/{id}/facts` | `FactsPage` | Extracted facts | `GET /ingest/facts` | app/projects/[id]/facts/page.tsx |
| 13 | `/projects/{id}/graph` | `GraphPage` | Knowledge graph | `GET /ingest/graph` | app/projects/[id]/graph/page.tsx |
| 14 | `/projects/{id}/ingest` | `IngestPage` | Upload + ingest | `POST /ingest/` | app/projects/[id]/ingest/page.tsx |
| 15 | `/projects/{id}/memory` | `MemoryPage` | Semantic search | `GET /memory/search` | app/projects/[id]/memory/page.tsx |
| 16 | `/projects/{id}/provenance` | `ProvenancePage` | Trace history | `GET /provenance/` | app/projects/[id]/provenance/page.tsx |
| 17 | `/projects/{id}/search` | `SearchPage` | Hybrid search | `POST /ingest/search` | app/projects/[id]/search/page.tsx |
| 18 | `/projects/{id}/sessions` | `SessionsPage` | Conversation list | `GET /sessions/` | app/projects/[id]/sessions/page.tsx |
| 19 | `/projects/{id}/sessions/{sid}` | `SessionDetailPage` | Conversation detail | `GET /sessions/{sid}` | app/projects/[id]/sessions/[sid]/page.tsx |
| 20 | `/projects/{id}/settings` | `ProjectSettingsPage` | Project config | `GET /projects/{id}` | app/projects/[id]/settings/page.tsx |
| 21 | `/projects/{id}/timeline` | `TimelinePage` | Chronological view | `GET /ingest/graph?include_historical` | app/projects/[id]/timeline/page.tsx |

**Total: 21 screens (3 public + 18 protected).**

---

## 4. Component Inventory

### 4.1 Layout Components

| Component | File | Purpose | Props |
|---|---|---|---|
| `RootLayout` | app/layout.tsx | Provider tree, SSR theme init | `{ children }` |
| `AppShell` | hooks/AppShell.tsx | Sidebar + content wrapper | `{ children }` |
| `ProjectLayout` | app/projects/[id]/layout.tsx | Project sidebar + content | `{ children }` |
| `Sidebar` | components/Sidebar.tsx | Responsive nav | `{ open, onClose }` (mobile) |
| `NavLink` | components/Sidebar.tsx | Active nav item | — (uses usePathname) |
| `ProjectNav` | components/Sidebar.tsx | Project-level nav | `{ projectId }` |
| `AuthRedirect` | hooks/AuthRedirect.tsx | Route guard | — |

### 4.2 UI Components (shadcn/ui)

| Component | File | Purpose | Props |
|---|---|---|---|
| `Badge` | components/ui/Badge.tsx | Status/color indicator | `{ children, variant }` |
| `Card` | components/ui/Card.tsx | Content card | `{ children, className }` |
| `Collapsible` | components/ui/Collapsible.tsx | Expandable section | `{ trigger, children }` |
| `ConfirmDialog` | components/ui/ConfirmDialog.tsx | Confirmation modal | `{ open, onConfirm, onCancel, title, message }` |
| `EmptyState` | components/ui/EmptyState.tsx | No-data placeholder | `{ icon, title, description }` |
| `ErrorAlert` | components/ui/ErrorAlert.tsx | Error display | `{ message, onRetry }` |
| `FileInput` | components/ui/FileInput.tsx | File upload | `{ accept, multiple, onChange, disabled }` |
| `LoadingSpinner` | components/ui/LoadingSpinner.tsx | Loading indicator | `{ size, className }` |
| `Pagination` | components/ui/Pagination.tsx | Page navigation | `{ page, totalPages, onPageChange }` |
| `Progress` | components/ui/Progress.tsx | Progress bar | `{ value, max, label }` |
| `Skeleton` | components/ui/Skeleton.tsx | Loading placeholder | `{ className, variant }` |
| `StatCard` | components/ui/StatCard.tsx | KPI metric card | `{ label, value, icon, trend }` |
| `Tabs` | components/ui/Tabs.tsx | Tab navigation | `{ tabs, active, onChange }` |
| `Toast` | components/ui/Toast.tsx | Notification | `{ message, type, onClose }` |
| `Tooltip` | components/ui/Tooltip.tsx | Hover tooltip | `{ content, children }` |

### 4.3 Feature Hooks

| Hook | File | Purpose | Returns |
|---|---|---|---|
| `useAuth` | hooks/useAuth.tsx | Auth context | `{ user, login, logout, register, loading }` |
| `useTheme` | hooks/useTheme.tsx | Theme context | `{ theme, setTheme, toggleTheme }` |
| `useProjects` | features/projects/useProjects.ts | Project CRUD | `{ projects, loading, error, create, delete, refetch }` |
| `useChat` | features/chat/useChat.ts | Chat state | `{ messages, sendMessage, loading, error }` |
| `useGraph` | features/graph/useGraph.ts | Knowledge graph | `{ data, loading, error, refetch }` |
| `useIngest` | features/ingest/useIngest.ts | Ingestion state | `{ jobs, ingest, loading, progress }` |
| `useMemory` | features/memory/useMemory.ts | Memory search | `{ results, search, loading, error }` |
| `useSearch` | features/search/useSearch.ts | Hybrid search | `{ results, query, loading, error }` |
| `useApiKeys` | features/apiKeys/useApiKeys.ts | API key management | `{ keys, create, revoke, loading, error }` |

### 4.4 Custom Hooks

| Hook | File | Purpose |
|---|---|---|
| `useSSE` | hooks/useSSE.tsx | Server-sent events connection |
| `useClipboard` | components/ui/useClipboard.ts | Clipboard copy/paste |

---

## 5. State Management

### 5.1 State Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      Frontend State Layers                         │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐   │
│  │ Server State   │  │ Client State   │  │  URL State       │   │
│  │ (from API)     │  │ (React)        │  │  (Next.js)       │   │
│  │                │  │                │  │                  │   │
│  │ - fetched data │  │ - UI state     │  │ - route params   │   │
│  │ - loading      │  │ - modal open   │  │ - search params  │   │
│  │ - error        │  │ - form input   │  │ - pathname       │   │
│  │ - refetch      │  │ - sidebar open │  │ - query string   │   │
│  │                │  │ - theme        │  │                  │   │
│  │ useState/      │  │ - user auth    │  │ usePathname      │   │
│  │ useCallback    │  │                │  │ useSearchParams  │   │
│  │ (per-screen)   │  │ React Context  │  │ useRouter        │   │
│  └────────────────┘  └────────────────┘  └──────────────────┘   │
│                                                                  │
│  Persistent State (localStorage):                                │
│  - sv_tokens (access + refresh tokens)                            │
│  - sv_theme (light / dark)                                       │
│  - sv_color (accent color)                                       │
└──────────────────────────────────────────────────────────────────┘
```

### 5.2 Context Providers

| Provider | State | Subscribers | Source File |
|---|---|---|---|
| `AuthProvider` | `user`, `login`, `logout`, `register`, `loading` | All protected pages | hooks/useAuth.tsx |
| `ThemeProvider` | `theme`, `setTheme`, `toggleTheme` | All pages (for CSS vars) | hooks/useTheme.tsx |
| `AppShell` | `sidebarOpen` (mobile), `currentView` | Sidebar, children | hooks/AppShell.tsx |

### 5.3 State Persistence

| State | Storage | Key | Source File |
|---|---|---|---|
| JWT tokens | `localStorage` | `sv_tokens` | lib/api.ts:31-33 |
| Theme | `localStorage` | `sv_theme` | hooks/useTheme.tsx |
| SSR theme init | `<script>` in `<head>` | `sv_theme` | app/layout.tsx:17-20 |

---

## 6. Data Fetching

### 6.1 API Client (`lib/api.ts`, ~80 lines)

| Function | Purpose | Auth | Returns |
|---|---|---|---|
| `apiGet<T>(path)` | GET request | Auto | `Promise<T>` |
| `apiPost<T>(path, body)` | POST JSON | Auto | `Promise<T>` |
| `apiPut<T>(path, body)` | PUT JSON | Auto | `Promise<T>` |
| `apiDelete<T>(path)` | DELETE | Auto | `Promise<T>` |
| `apiUpload(path, formData)` | POST multipart | Auto | `Promise<T>` |

All functions auto-attach Bearer token, auto-refresh on 401, and throw typed errors.

### 6.2 Error Types (`lib/errors.ts`)

| Type | Purpose |
|---|---|
| `APIError` | Non-2xx response with code/message/requestId |
| `AuthError` | 401/403 responses |
| `NetworkError` | fetch failures |

### 6.3 Custom Hooks Pattern

```
Custom Hook (e.g., useChat)
  │
  ├── useState (data)
  ├── useState (loading)
  ├── useState (error)
  ├── useCallback (action)
  └── api[Get|Post|...] (inside useEffect or callback)
```

All feature hooks follow this pattern for consistency.

---

## 7. Routing Map

### 7.1 Full Route Tree

| Route | Layout | Auth | Component | Source File |
|---|---|---|---|---|
| `/` | RootLayout | Public | `LandingPage` | app/page.tsx |
| `/auth/login` | AuthLayout | Public | `LoginPage` | app/auth/login/page.tsx |
| `/auth/register` | AuthLayout | Public | `RegisterPage` | app/auth/register/page.tsx |
| `/dashboard` | AppShell | Protected | `DashboardPage` | app/dashboard/page.tsx |
| `/projects` | AppShell | Protected | `ProjectsListPage` | app/projects/page.tsx |
| `/projects/{id}` | AppShell | Protected | `ProjectLayout` | app/projects/[id]/layout.tsx |
| `/projects/{id}/chat` | ProjectLayout | Protected | `ChatPage` | app/projects/[id]/chat/page.tsx |
| `/projects/{id}/decisions` | ProjectLayout | Protected | `DecisionsPage` | app/projects/[id]/decisions/page.tsx |
| `/projects/{id}/facts` | ProjectLayout | Protected | `FactsPage` | app/projects/[id]/facts/page.tsx |
| `/projects/{id}/graph` | ProjectLayout | Protected | `GraphPage` | app/projects/[id]/graph/page.tsx |
| `/projects/{id}/ingest` | ProjectLayout | Protected | `IngestPage` | app/projects/[id]/ingest/page.tsx |
| `/projects/{id}/memory` | ProjectLayout | Protected | `MemoryPage` | app/projects/[id]/memory/page.tsx |
| `/projects/{id}/provenance` | ProjectLayout | Protected | `ProvenancePage` | app/projects/[id]/provenance/page.tsx |
| `/projects/{id}/search` | ProjectLayout | Protected | `SearchPage` | app/projects/[id]/search/page.tsx |
| `/projects/{id}/sessions` | ProjectLayout | Protected | `SessionsPage` | app/projects/[id]/sessions/page.tsx |
| `/projects/{id}/sessions/{sid}` | ProjectLayout | Protected | `SessionDetailPage` | app/projects/[id]/sessions/[sid]/page.tsx |
| `/projects/{id}/settings` | ProjectLayout | Protected | `ProjectSettingsPage` | app/projects/[id]/settings/page.tsx |
| `/projects/{id}/timeline` | ProjectLayout | Protected | `TimelinePage` | app/projects/[id]/timeline/page.tsx |
| `/settings` | AppShell | Protected | `SettingsLayoutPage` | app/settings/page.tsx |
| `/settings/api-keys` | AppShell | Protected | `APIKeysPage` | app/settings/api-keys/page.tsx |
| `/settings/profile` | AppShell | Protected | `ProfilePage` | app/settings/profile/page.tsx |
| `/settings/storage` | AppShell | Protected | `StoragePage` | app/settings/storage/page.tsx |

**21 pages (3 public + 18 protected).**

### 7.2 Navigation Structure

| Section | Items | Source File |
|---|---|---|
| **Workspace** (top-level) | Dashboard, Projects | Sidebar.tsx:19-22 |
| **Knowledge** (top-level) | Search, Chat, Memory, Facts, Decisions, Timeline, Graph, Provenance | Sidebar.tsx:24-33 |
| **Ingestion** (top-level) | Upload & Ingest | Sidebar.tsx:35-37 |
| **Account** (top-level) | Settings, Logout | Sidebar.tsx:39-41 |
| **Project** (inside /projects/{id}) | Chat, Ingest, Sessions, Memory, Facts, Decisions, Timeline, Search, Graph, Provenance | Sidebar.tsx:44-55 |

**22 icons used from lucide-react:** LayoutDashboard, FolderOpen, LogOut, MessageSquare, Upload, Brain, GitBranch, ShieldCheck (×2), Clock (×2), Search, Share2, Settings, Activity, Database, Plus, Eye, Code, Link, ChevronRight, ChevronDown, Menu, X, Trash2, Copy, Check, RefreshCw, Play, Pause, SkipForward, Circle, CheckCircle, XCircle, AlertTriangle, Loader2, ExternalLink, Info, HelpCircle.

---

## 8. Theming

### 8.1 Theme System

| Aspect | Detail | Source File |
|---|---|---|
| Provider | `ThemeProvider` | hooks/useTheme.tsx |
| Storage | `localStorage.sv_theme` | hooks/useTheme.tsx |
| Values | `light`, `dark` | hooks/useTheme.tsx |
| SSR init | Inline script in `<head>` | app/layout.tsx:17-20 |
| Attribute | `data-theme` on `<html>` | hooks/useTheme.tsx |

### 8.2 CSS Variable System

| Variable | Purpose | Example (light) | Example (dark) |
|---|---|---|---|
| `--bg-primary` | Main background | `#ffffff` | `#0f172a` |
| `--bg-secondary` | Elevated surface | `#f8fafc` | `#1e293b` |
| `--bg-tertiary` | Higher elevation | `#f1f5f9` | `#334155` |
| `--text-primary` | Main text | `#0f172a` | `#f8fafc` |
| `--text-secondary` | Muted text | `#64748b` | `#94a3b8` |
| `--text-muted` | Helper text | `#94a3b8` | `#64748b` |
| `--border-primary` | Default border | `#e2e8f0` | `#334155` |
| `--border-secondary` | Subtle border | `#f1f5f9` | `#1e293b` |
| `--accent-primary` | Primary accent | `#3b82f6` | `#60a5fa` |
| `--accent-hover` | Hover state | `#2563eb` | `#3b82f6` |
| `--accent-light` | Subtle accent bg | `#dbeafe` | `#1e3a5f` |
| `--error-primary` | Error color | `#ef4444` | `#f87171` |
| `--error-light` | Error bg | `#fef2f2` | `#7f1d1d` |
| `--success-primary` | Success color | `#22c55e` | `#4ade80` |
| `--success-light` | Success bg | `#f0fdf4` | `#14532d` |
| `--warning-primary` | Warning color | `#f59e0b` | `#fbbf24` |
| `--warning-light` | Warning bg | `#fffbeb` | `#78350f` |

---

## 9. Build & Deploy

### 9.1 Build Configuration

| Aspect | Detail | Source |
|---|---|---|
| Framework | Next.js 15 (package.json: ^15.0.0) | package.json |
| Build command | `npm run build` | package.json |
| Output | `.next/` directory | — |
| Build tool | Webpack (default) | next.config.js |
| Lint | `npm run lint` | ESLint |
| Type check | `npx tsc --noEmit` | TypeScript |
| Environment | `.env` (root), `.env.local`, `.env.development` | — |

### 9.2 Build Stats (verified 2026-09-24)

| Metric | Value |
|---|---|
| Build time | ~5s |
| First Load JS (shared) | 103 kB |
| Routes | 22 (17 dynamic, 5 static) |
| Static pages | 12 prerendered |
| tsc errors | 0 |
| Lint errors | 0 |
| Lint warnings | 3 (react-hooks/exhaustive-deps) |

### 9.3 Environment Variables

| Variable | Default | Purpose | Source File |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API base | lib/api.ts:1 |
| `NEXT_PUBLIC_APP_URL` | — | Frontend URL (for callbacks) | — |

---

## 10. E2E Test Coverage

### 10.1 Test Suite Inventory

| Spec | Tests | Purpose | Source File |
|---|---|---|---|
| `remaining-contracts.spec.ts` | 120 | Network contracts, responsive, a11y, cross-page | e2e/remaining-contracts.spec.ts |
| `ui-certification.spec.ts` | 22 | UI rendering, network contracts | e2e/ui-certification.spec.ts |
| `search-chat-certification.spec.ts` | 19 | Search + chat flows | e2e/search-chat-certification.spec.ts |
| `frontend-journey.spec.ts` | 4 | Full user journeys | e2e/frontend-journey.spec.ts |
| `golden-journey.spec.ts` | 14 | Golden path scenarios | e2e/golden-journey.spec.ts |
| `api-e2e.spec.ts` | 14 | Direct API tests | e2e/api-e2e.spec.ts |
| `auth.spec.ts` | 7 | Authentication flows | e2e/auth.spec.ts |
| `dashboard.spec.ts` | 3 | Dashboard rendering | e2e/dashboard.spec.ts |
| **Total** | **203** | | |

### 10.2 Test Execution

| Config | Workers | Passed | Failed | Skipped | Source |
|---|---|---|---|---|---|
| Full suite | 1 | 197 | 3 | 2 | Playwright output |
| Full suite | 1 | 101 | 0 | 2 | Playwright output (alternate) |
| Baseline (e6f4b1c) | 1 | 199 | 4 | 2 | Playwright output |

**3 failures are PRE-EXISTING** at baseline e6f4b1c (which has 4). Our tree fixed 1. Failures are React hydration warnings in shared `LinkComponent` (div inside a tag).

### 10.3 Test Helpers

| Helper | File | Purpose |
|---|---|---|
| `test-helpers.ts` | e2e/test-helpers.ts | Shared fixtures, API key setup |
| `global-setup.ts` | e2e/global-setup.ts | Browser launch config |
| `createApiKey` | test-helpers.ts | Automated API key creation for E2E |
| `seedTestData` | test-helpers.ts | Test data fixture |

---

## Appendix A: Known Issues

| Issue | Severity | Status | Source File |
|---|---|---|---|
| React hydration mismatch (div inside a tag) | Low | PRE-EXISTING (3 failures) | components/Sidebar.tsx |
| Next.js workspace root warning | Low | Dev only | frontend/package.json |
| In-memory rate limiter (not Redis) | Medium | Documented, not blocking | middleware/rate_limit.py |
| Anthropic/OpenAI API keys empty | Low | Uses MockProvider in tests | .env |
| No error boundary in project pages | Low | Not blocking | app/projects/[id]/chat/page.tsx |

---

## Appendix B: Source Authority Map

| Manifest Section | Source File | Authority |
|---|---|---|
| Architecture overview | app/layout.tsx, package.json | Single source of truth |
| Provider tree | app/layout.tsx | Single source of truth |
| Sidebar nav | components/Sidebar.tsx | Single source of truth |
| Screen components | app/*/page.tsx | Single source of truth |
| Feature hooks | features/*/use*.ts | Single source of truth |
| API client | lib/api.ts | Single source of truth |
| Theme system | hooks/useTheme.tsx, globals.css | Single source of truth |
| Auth context | hooks/useAuth.tsx | Single source of truth |
| UI components | components/ui/*.tsx | Single source of truth |
| E2E tests | e2e/*.spec.ts | Single source of truth |
| Build config | next.config.js, package.json | Single source of truth |
| CSS variables | globals.css | Single source of truth |

---

*This document is maintained by source-of-truth reconciliation. When source diverges from document, source wins and document is corrected.*
