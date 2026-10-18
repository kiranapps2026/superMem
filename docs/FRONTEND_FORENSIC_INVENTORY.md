# SwarmVault Frontend — Complete Forensic Inventory

**Date:** 2026-09-10  
**Repository:** `C:\Users\Administrator\Documents\SwarmVaultwebapp`  
**Frontend root:** `C:\Users\Administrator\Documents\SwarmVaultwebapp\frontend\`  
**Status:** Read-only inventory. No code was modified.

---

## Section 1: Application Structure

### 1.1 Complete File Tree of `src/`

```
src/
  app/
    globals.css                          # Global styles + design tokens
    layout.tsx                           # Root layout (providers + html shell)
    page.tsx                             # Root redirect page ("/")
    auth/
      login/
        page.tsx                         # Login page
      register/
        page.tsx                         # Registration page
    dashboard/
      page.tsx                           # Dashboard
    projects/
      page.tsx                           # Projects list
      [id]/
        layout.tsx                       # Project layout (sidebar + children)
        chat/
          page.tsx                       # AI Chat
        ingest/
          page.tsx                       # Upload & Ingest
        sessions/
          page.tsx                       # Sessions list
          [sessionId]/
            page.tsx                     # Session detail/history
        memory/
          page.tsx                       # Memory items
        facts/
          page.tsx                       # Extracted facts
        decisions/
          page.tsx                       # Extracted decisions
        timeline/
          page.tsx                       # Chronological timeline
        graph/
          page.tsx                       # Knowledge graph
        provenance/
          page.tsx                       # Provenance/audit trail
        search/
          page.tsx                       # Semantic search
        settings/
          page.tsx                       # Project settings
    settings/
      page.tsx                           # Workspace settings
      profile/
        page.tsx                         # User profile
      api-keys/
        page.tsx                         # API key management
      storage/
        page.tsx                         # File storage management
  components/
    Sidebar.tsx                           # Application sidebar navigation
    ui/
      Badge.tsx                           # Badge component (status/authority/evidence/temporal)
      Card.tsx                            # Card container component
      Collapsible.tsx                     # Collapsible section
      ConfirmDialog.tsx                   # Modal confirmation dialog
      EmptyState.tsx                      # Empty state placeholder
      ErrorAlert.tsx                      # Error display with dismiss/retry
      FileInput.tsx                       # Drag-and-drop file input
      LoadingSpinner.tsx                  # Spinner (sm/md/lg)
      Pagination.tsx                      # Pagination control
      Progress.tsx                        # Progress bar
      Skeleton.tsx                        # Skeleton loading placeholder
      StatCard.tsx                        # Dashboard stat card
      Tabs.tsx                            # Tabs + TabPanel
      Toast.tsx                           # Toast notification system
      Tooltip.tsx                         # Tooltip on hover/focus
      useClipboard.ts                     # Clipboard hook
      index.ts                            # Barrel exports
  features/
    apiKeys/
      useApiKeys.ts                       # API keys hooks (list/create/revoke/rotate)
    chat/
      useChat.ts                          # Chat hook (SSE streaming)
    graph/
      useGraph.ts                         # Graph data hook
    ingest/
      useIngest.ts                        # Ingestion hooks (sources/facts/decisions/jobs/upload)
    memory/
      useMemory.ts                        # Memory hooks (list/search/create/delete)
    projects/
      useProjects.ts                      # Project hooks (list/get/create/update/delete)
    search/
      useSearch.ts                        # Search hook
  hooks/
    AppShell.tsx                          # App shell (sidebar + auth guard)
    AuthRedirect.tsx                      # Auth redirect wrapper (unused in current code)
    useAuth.tsx                           # Auth context + hooks
    useSSE.tsx                            # SSE streaming hook
    useTheme.tsx                          # Theme context + hooks
  lib/
    api.ts                                # API client (fetch, SSE, upload, token management)
    errors.ts                             # Error formatting utilities
  types/
    api.ts                                # TypeScript type definitions for all API responses
```

### 1.2 Next.js Configuration

**File:** `next.config.js` and `next.config.mjs` (both identical, both present)

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};
module.exports = nextConfig;
```

- **Strict mode:** Enabled (`reactStrictMode: true`)
- **No custom rewrites, redirects, or headers** — default Next.js behavior
- **No image optimization config** — no `images` key
- **No experimental features** configured

### 1.3 Tailwind Configuration

**File:** `tailwind.config.js`

```js
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  darkMode: 'class',
  theme: { extend: {} },
  plugins: [],
};
```

- **Scan paths:** `./src/**/*.{js,ts,jsx,tsx,mdx}`
- **Dark mode strategy:** `class` (toggled via `data-theme` attribute on `<html>`)
- **No custom theme extensions** — all design tokens are CSS custom properties in `globals.css`
- **No plugins** configured

### 1.4 Route Structure (all page.tsx files)

| Route | File | Description |
|---|---|---|
| `/` | `src/app/page.tsx` | Root redirect — sends authenticated users to `/dashboard`, unauthenticated to `/auth/login` |
| `/auth/login` | `src/app/auth/login/page.tsx` | Login form |
| `/auth/register` | `src/app/auth/register/page.tsx` | Registration form |
| `/dashboard` | `src/app/dashboard/page.tsx` | Workspace dashboard |
| `/projects` | `src/app/projects/page.tsx` | Project list |
| `/projects/[id]/*` | `src/app/projects/[id]/layout.tsx` | Project layout (inner sidebar + children) |
| `/projects/[id]/chat` | `src/app/projects/[id]/chat/page.tsx` | AI chat |
| `/projects/[id]/ingest` | `src/app/projects/[id]/ingest/page.tsx` | Upload & ingest |
| `/projects/[id]/sessions` | `src/app/projects/[id]/sessions/page.tsx` | Session list |
| `/projects/[id]/sessions/[sessionId]` | `src/app/projects/[id]/sessions/[sessionId]/page.tsx` | Session detail |
| `/projects/[id]/memory` | `src/app/projects/[id]/memory/page.tsx` | Memory items |
| `/projects/[id]/facts` | `src/app/projects/[id]/facts/page.tsx` | Extracted facts |
| `/projects/[id]/decisions` | `src/app/projects/[id]/decisions/page.tsx` | Extracted decisions |
| `/projects/[id]/timeline` | `src/app/projects/[id]/timeline/page.tsx` | Chronological timeline |
| `/projects/[id]/graph` | `src/app/projects/[id]/graph/page.tsx` | Knowledge graph |
| `/projects/[id]/provenance` | `src/app/projects/[id]/provenance/page.tsx` | Provenance trail |
| `/projects/[id]/search` | `src/app/projects/[id]/search/page.tsx` | Semantic search |
| `/projects/[id]/settings` | `src/app/projects/[id]/settings/page.tsx` | Project settings |
| `/settings` | `src/app/settings/page.tsx` | Workspace settings |
| `/settings/profile` | `src/app/settings/profile/page.tsx` | User profile |
| `/settings/api-keys` | `src/app/settings/api-keys/page.tsx` | API key management |
| `/settings/storage` | `src/app/settings/storage/page.tsx` | File storage |

### 1.5 Layout Files

1. **`src/app/layout.tsx`** — Root layout. Wraps all pages with:
   - `<ThemeProvider>` — theme context
   - `<AuthProvider>` — authentication context
   - `<AppShell>` — sidebar + auth guard
   - Inline `<script>` to read `sv_theme` from `localStorage` before React hydration (prevents theme flash)
   - Metadata: title "SwarmVault", description "AI-powered conversation memory and retrieval"

2. **`src/app/projects/[id]/layout.tsx`** — Project layout. Provides:
   - Left sidebar with project info, navigation links, Edit/Delete buttons
   - Edit mode for project name/description
   - Delete confirmation
   - Uses `useProject`, `useUpdateProject`, `useDeleteProject` feature hooks

### 1.6 Component Files

**Shared (global):**
- `Sidebar.tsx` — Collapsible sidebar with workspace/project navigation

**UI Design System (`components/ui/`):**
- `Badge.tsx`, `Card.tsx`, `Collapsible.tsx`, `ConfirmDialog.tsx`, `EmptyState.tsx`, `ErrorAlert.tsx`, `FileInput.tsx`, `LoadingSpinner.tsx`, `Pagination.tsx`, `Progress.tsx`, `Skeleton.tsx`, `StatCard.tsx`, `Tabs.tsx`, `Toast.tsx`, `Tooltip.tsx`
- `useClipboard.ts` — Clipboard copy hook
- `index.ts` — Barrel exports

**Feature hooks (`features/`):**
- `useProjects.ts` — `useProjects`, `useProject`, `useCreateProject`, `useUpdateProject`, `useDeleteProject`
- `useChat.ts` — `useChat` (SSE streaming chat)
- `useGraph.ts` — `useGraph`
- `useIngest.ts` — `useSources`, `useFacts`, `useDecisions`, `useUploadFile`, `useIngestJobs`
- `useMemory.ts` — `useMemoryList`, `useMemorySearch`, `useCreateMemory`, `useDeleteMemory`
- `useSearch.ts` — `useSearch`
- `useApiKeys.ts` — `useApiKeys`, `useCreateKey`, `useRevokeKey`, `useRotateKey`

---

## Section 2: Pages Inventory

### 2.1 Root Page (`src/app/page.tsx`)

- **Purpose:** Root redirect. Sends authenticated users to `/dashboard`, unauthenticated to `/auth/login`.
- **Data fetching:** None. Reads `user` and `loading` from `useAuth()`.
- **State:** None (just `useEffect` for redirect).
- **Loading state:** Shows "Loading..." spinner with Brain icon while auth state resolves.
- **Error handling:** None.

### 2.2 Login Page (`src/app/auth/login/page.tsx`)

- **Purpose:** User login form.
- **Data fetching:** Calls `useAuth().login(email, password)` which POSTs to `/api/v1/auth/login`, stores tokens, then GETs `/api/v1/auth/me`.
- **State:** `email`, `password` (useState), `loading`, `error` (from `useAuth`).
- **Error handling:** Displays `ErrorAlert` component with the error message. Dismissable via `clearError()`.
- **Loading state:** Button shows "Signing in..." when loading. Form inputs disabled during submission.
- **Navigation:** Links to `/auth/register`.

### 2.3 Register Page (`src/app/auth/register/page.tsx`)

- **Purpose:** New user registration form.
- **Data fetching:** Calls `useAuth().register({ email, password, name, workspace_name })` which POSTs to `/api/v1/auth/register`, stores tokens, then GETs `/api/v1/auth/me`.
- **State:** `email`, `password`, `confirm`, `name`, `workspaceName` (useState). `passwordMismatch` computed.
- **Error handling:** Displays `ErrorAlert` for server errors. Shows inline "Passwords do not match" error for client-side mismatch.
- **Loading state:** Button shows "Creating account..." when loading. Disabled if passwords mismatch.
- **Navigation:** Links to `/auth/login`.

### 2.4 Dashboard Page (`src/app/dashboard/page.tsx`)

- **Purpose:** Workspace overview with stats, project creation, project grid, recent activity.
- **Data fetching:**
  - `apiGet('/api/v1/workspace')` — workspace details
  - `apiGet('/api/v1/dashboard/')` — dashboard summary (stats)
  - `apiGet('/api/v1/projects')` — project list
  - All three run in parallel via `Promise.all` after auth resolves.
- **State:** `workspace`, `projects`, `overview` (stats), `loading`, `showNew`, `newName`, `newDesc`, `creating`, `view` ('overview' | 'recent'), `wsCollapsed`.
- **Project creation:** POST to `/api/v1/projects` with `{ name, description }`.
- **Error handling:** `alert()` on project creation failure. No ErrorAlert component used here.
- **Loading state:** "Loading..." text during auth and data fetch.
- **Views:**
  - **Overview:** Stats grid (6 stat cards) + project cards grid (responsive: 1/2/3 columns).
  - **Recent:** Last 7 days activity summary with memory distribution badges.
- **Used by:** Authenticated users only (guarded by AppShell).

### 2.5 Projects Page (`src/app/projects/page.tsx`)

- **Purpose:** List all projects with search filter.
- **Data fetching:** `apiGet('/api/v1/projects')` — project list.
- **State:** `projects`, `loading`, `search`.
- **Search:** Client-side filter on project name/description (shown only if >5 projects).
- **Error handling:** None explicit (just catches and sets loading=false).
- **Loading state:** "Loading..." text.
- **Empty states:** "No projects yet" and "No projects match" with FolderOpen icon.

### 2.6 Project Layout (`src/app/projects/[id]/layout.tsx`)

- **Purpose:** Shared layout for all project pages. Shows project nav sidebar.
- **Data fetching:** `apiGet('/api/v1/projects/${projectId}')` on mount / projectId change.
- **State:** `project`, `loading`, `editing`, `editName`, `editDesc`, `saving`, `error`.
- **Edit:** PATCH to `/api/v1/projects/${projectId}` with changed fields.
- **Delete:** `apiDelete('/api/v1/projects/${projectId}')` with `confirm()` dialog, then `window.location.href = '/projects'`.
- **Error handling:** `ErrorAlert` in edit mode. `alert()` on delete failure.
- **Loading state:** "Loading..." / "Project not found."

### 2.7 Chat Page (`src/app/projects/[id]/chat/page.tsx`)

- **Purpose:** AI chat interface with SSE streaming, evidence sources, and "Why this answer?" modal.
- **Data fetching:**
  - Creates session via POST `/api/v1/sessions/` with `{ project_id }` before each message.
  - Streams response via POST `/api/v1/chat/stream` with `{ message, session_id, project_id }`.
  - Uses raw `fetch()` directly (not `apiPost`), with inline token handling.
- **State:** `messages`, `input`, `loading`, `showSources`, `evidenceModal`, `error`, `retrying`, refs for scroll, textarea, abort controller.
- **SSE Handling:** Manual SSE parsing in-page (separate from `useSSE` hook). Parses `data:` lines for `token`, `sources`, `done`, `error` event types.
- **Error handling:** Error messages rendered inline in chat. ErrorAlert for general errors.
- **Loading state:** "Thinking..." spinner in chat bubble. Send button shows spinner.
- **Evidence Modal:** Shows answer + evidence trail with memory types and scores.
- **Keyboard:** Enter to send, Shift+Enter for new line.
- **Note:** This page has its own SSE implementation rather than using the `useSSE` hook. The `useChat` feature hook exists but is NOT used by this page.

### 2.8 Ingest Page (`src/app/projects/[id]/ingest/page.tsx`)

- **Purpose:** Upload files or paste text for ingestion. Shows source list.
- **Data fetching:**
  - `apiGet('/api/v1/ingest/sources?project_id=...&limit=50')` — source list.
  - `uploadFile(projectId, file, onProgress)` — multipart file upload via XHR.
  - `apiPost('/api/v1/ingest/upload', { project_id, source_type, content, title })` — text upload.
- **State:** `sources`, `loading`, `uploading`, `uploadProgress`, `rawContent`, `sourceType`, `title`, `error`.
- **Source types:** text, chatgpt, claude, jsonl, markdown.
- **Error handling:** `ErrorAlert` component.
- **Loading state:** "Loading..." text. Upload progress bar during file upload.
- **Source list:** Shows status icons (Queued/Processing/Completed/Failed), message count, date.

### 2.9 Memory Page (`src/app/projects/[id]/memory/page.tsx`)

- **Purpose:** Display memory items for a project with type filtering and pagination.
- **Data fetching:** `apiGet('/api/v1/memory/?limit=20&offset=...&project_id=...&memory_type=...')`.
- **State:** `items`, `loading`, `memoryType`, `page`, `total`, `error`.
- **Filtering:** Memory type filter (semantic, episodic, procedural, working). Resets to page 0 on filter change.
- **Pagination:** PAGE_SIZE=20, uses `Pagination` UI component. Pagination only shown if `items.length >= PAGE_SIZE`.
- **Temporal status mapping:** Maps lowercase backend values to uppercase Badge values.
- **Error handling:** `ErrorAlert` component.
- **Empty state:** `EmptyState` with Brain icon.

### 2.10 Facts Page (`src/app/projects/[id]/facts/page.tsx`)

- **Purpose:** Display extracted facts with subject-predicate-object display.
- **Data fetching:** `apiGet('/api/v1/ingest/facts?project_id=...&limit=20&offset=...')`.
- **State:** `facts`, `loading`, `page`, `error`.
- **Pagination:** PAGE_SIZE=20.
- **Display:** Shows content, confidence/authority scores, temporal status badge, evidence badge, subject-predicate-object triple in monospace.
- **Error handling:** `ErrorAlert` component.
- **Empty state:** `EmptyState` with GitBranch icon.

### 2.11 Decisions Page (`src/app/projects/[id]/decisions/page.tsx`)

- **Purpose:** Display extracted decisions.
- **Data fetching:** `apiGet('/api/v1/ingest/decisions?project_id=...&limit=20&offset=...')`.
- **State:** `decisions`, `loading`, `page`, `error`.
- **Pagination:** PAGE_SIZE=20.
- **Display:** Content, confidence badge, context (if any), temporal status, authority, superseded indicator.
- **Error handling:** `ErrorAlert` component.
- **Empty state:** `EmptyState` with CheckSquare icon.

### 2.12 Timeline Page (`src/app/projects/[id]/timeline/page.tsx`)

- **Purpose:** Chronological view of all knowledge items (memories, facts, decisions).
- **Data fetching:** `apiGet('/api/v1/ingest/timeline?project_id=...&limit=100')`.
- **State:** `events`, `loading`, `error`.
- **Display:** Vertical timeline with dot indicators, type icons, temporal badges, timestamps.
- **No pagination** — fetches up to 100 items at once.
- **Error handling:** `ErrorAlert` component.
- **Empty state:** `EmptyState` with GitBranch icon.

### 2.13 Graph Page (`src/app/projects/[id]/graph/page.tsx`)

- **Purpose:** Knowledge graph visualization (node list + detail panel, not visual graph rendering).
- **Data fetching:** `apiGet('/api/v1/ingest/graph?project_id=...')`.
- **State:** `data` (GraphResponse), `loading`, `selectedNode`, `error`.
- **Display:** Two-column layout. Left: node list with expandable neighbor edges. Right: detail panel for selected node (type, temporal status, properties in collapsible JSON).
- **Node type colors:** concept→info, entity→accent, decision→warning, fact→success.
- **Error handling:** `ErrorAlert` component.
- **Empty state:** `EmptyState` with Network icon.

### 2.14 Search Page (`src/app/projects/[id]/search/page.tsx`)

- **Purpose:** Semantic search across project knowledge.
- **Data fetching:** `apiPost('/api/v1/ingest/search?query=...&limit=...&memory_type=...')`.
  - **Note:** Uses POST despite being a read/search operation. The API requires it.
  - Memory type filter: semantic_memory, episodic_memory, procedural_memory, working_memory, fact, decision.
- **State:** `query`, `results`, `searching`, `total`, `searched`, `error`, `page`, `memoryType`.
- **Pagination:** PAGE_SIZE=10. Client-side slicing of results.
- **Keyboard:** Enter to search.
- **Error handling:** `ErrorAlert` component.
- **Empty state:** `EmptyState` with Search icon.

### 2.15 Sessions Page (`src/app/projects/[id]/sessions/page.tsx`)

- **Purpose:** List sessions for a project.
- **Data fetching:** `apiGet('/api/v1/sessions/?project_id=...&limit=20&offset=...')`.
- **State:** `sessions`, `loading`, `page`, `error`.
- **Pagination:** PAGE_SIZE=20.
- **Display:** Session cards with title, source badge, message count, date. Links to session detail.
- **Note:** Page subtitle says "in this workspace" — the sessions endpoint returns all workspace sessions, not filtered by project_id.
- **Error handling:** `ErrorAlert` component.
- **Empty state:** `EmptyState` with MessageSquare icon.

### 2.16 Session Detail Page (`src/app/projects/[id]/sessions/[sessionId]/page.tsx`)

- **Purpose:** Display full conversation history for a session.
- **Data fetching:** `apiGet('/api/v1/sessions/${sessionId}/history')`.
- **State:** `history`, `loading`, `error`.
- **Display:** Back link → session title + source badge → message count → message list with user/assistant avatars, timestamps.
- **Error handling:** `ErrorAlert` component.

### 2.17 Provenance Page (`src/app/projects/[id]/provenance/page.tsx`)

- **Purpose:** Audit trail of AI responses (model, provider, retrieval method, latency, tokens).
- **Data fetching:** `apiGet('/api/v1/provenance/?project_id=...')`.
- **State:** `records`, `loading`, `error`.
- **Display:** Record cards with model, provider badge, latency, tokens, retrieval method, confidence, memory IDs used.
- **Error handling:** `ErrorAlert` component.
- **Empty state:** `EmptyState` with GitBranch icon.

### 2.18 Project Settings Page (`src/app/projects/[id]/settings/page.tsx`)

- **Purpose:** Project-level settings with three tabs: General, Members, Danger Zone.
- **Data fetching:**
  - Uses `useProject(projectId)` hook for project data.
  - `apiGet('/api/v1/workspace/members')` for members list.
- **State:** `activeTab`, `name`, `description`, `message`, `showDelete`, `members`, `membersLoading`, clipboard state.
- **Tabs:**
  - **General:** Edit project name/description via `useUpdateProject`.
  - **Members:** List workspace members with role badges. (Note: lists ALL workspace members, not project-specific.)
  - **Danger Zone:** Delete project with `ConfirmDialog`.
- **Error handling:** `ErrorAlert` with success/error message states.
- **Uses feature hooks:** `useProject`, `useUpdateProject`, `useDeleteProject`.

### 2.19 Settings Page (`src/app/settings/page.tsx`)

- **Purpose:** Workspace-level settings with three tabs: Workspace, Members, Invitations.
- **Data fetching:**
  - `apiGet('/api/v1/workspace')` — workspace details.
  - `apiGet('/api/v1/workspace/members')` — member list.
  - `apiGet('/api/v1/workspace/members/invitations')` — invitations (lazy-loaded when tab active).
- **State:** `activeTab`, `workspace`, `members`, `invitations`, `loading`, `currentUserRole`, `message`, `saving`, `inviting`, `removingId`.
- **Workspace tab:** Edit workspace name/description. Change password form (`apiPost('/api/v1/auth/change-password')`). Profile info display.
- **Members tab:** Invite by email + role select (owner/admin/member/viewer). Role change dropdown. Remove member. Role-based permission checks (canManage, isOwner).
- **Invitations tab:** List pending/past invitations. Revoke invitation.
- **Error handling:** Inline success/error message banner.

### 2.20 Profile Page (`src/app/settings/profile/page.tsx`)

- **Purpose:** User profile management and password change.
- **Data fetching:** Reads `user` from `useAuth()`.
- **State:** `saving`, `changingPassword`, `showPassword`, `message`, `name`, `currentPassword`, `newPassword`.
- **Actions:**
  - PATCH `/api/v1/auth/me` with `{ name }` — update profile.
  - POST `/api/v1/auth/change-password` with `{ current_password, new_password }`.
- **Error handling:** Success/error message banner.
- **Security:** Password visibility toggle.

### 2.21 API Keys Page (`src/app/settings/api-keys/page.tsx`)

- **Purpose:** Manage workspace API keys (create, revoke, rotate).
- **Data fetching:** Uses `useApiKeys()` hook (GET `/api/v1/api-keys`).
- **State:** `name`, `showRevoke`, `showRotate`, `localError`, clipboard state.
- **Actions:**
  - Create: POST `/api/v1/api-keys` with `{ name }`.
  - Revoke: DELETE `/api/v1/api-keys/${id}`.
  - Rotate: POST `/api/v1/api-keys/${id}/rotate`.
- **Raw key display:** Shows newly created/rotated raw key once with copy button and warning.
- **Error handling:** Error banner.
- **Uses feature hooks:** `useApiKeys`, `useCreateKey`, `useRevokeKey`, `useRotateKey`.

### 2.22 Storage Page (`src/app/settings/storage/page.tsx`)

- **Purpose:** File upload and management UI.
- **Data fetching:**
  - GET `/api/v1/auth/me` to get workspace_id on mount.
  - Uses `useUploadFile` hook (which calls `uploadFile` from `lib/api`).
- **State:** `files`, `projectId`, `deleting`, `deleteConfirm`.
- **Upload:** File input with drag-and-drop (via `FileInput` component). Calls `uploadFile()` with progress tracking.
- **Delete:** Removes from local tracked list only (no backend delete endpoint for raw uploads).
- **Note:** Uses workspace_id as projectId for upload endpoint — this is likely incorrect since the ingest endpoint expects a project_id, not workspace_id.
- **No error handling component** — uses inline text styling with `text-red-500` etc.

---

## Section 3: Components Inventory

### 3.1 Sidebar (`src/components/Sidebar.tsx`)

- **Props:** None (uses `useAuth()` internally).
- **API calls:** None directly (reads `user` from auth context).
- **State:** `sidebarCollapsed` (local). Auto-collapses on viewport < 768px.
- **Navigation groups:**
  - **Workspace:** Dashboard, Projects
  - **Knowledge:** Knowledge Search, Chat, Memory, Facts, Decisions, Timeline, Graph, Provenance
  - **Ingestion:** Upload & Ingest
  - **Project:** Dynamically shown when on a project route (Chat, Ingest, Sessions, Memory, Facts, Decisions, Timeline, Search, Graph, Provenance)
  - **Account:** Settings, Logout
- **Active link detection:** `pathname === item.href || pathname.startsWith(item.href + '/')`.
- **Used by:** `AppShell` — wraps all authenticated page content.
- **Icons:** Uses `lucide-react` icons.

### 3.2 Badge (`src/components/ui/Badge.tsx`)

- **Props:** `children?`, `category?` ('status'|'authority'|'evidence'|'temporal'), `value?`, `variant?`, `size?` ('sm'|'md'), `className?`.
- **API calls:** None.
- **State:** None.
- **Variant maps:**
  - `STATUS_VARIANTS`: default, success, warning, danger, info, muted
  - `AUTHORITY_VARIANTS`: UNVERIFIED, INFERRED, OBSERVED, DECISION, VERIFIED, CERTIFIED
  - `EVIDENCE_VARIANTS`: INGESTED, PROCESSED, INTEGRATED, PROVEN
  - `TEMPORAL_VARIANTS`: ACTIVE, SUPERSEDED, ARCHIVED
- **Used by:** MemoryPage, FactsPage, DecisionsPage, TimelinePage, GraphPage, SearchPage, SessionsPage, ProvenancePage, ProjectSettingsPage, SettingsPage, StoragePage, ChatPage.

### 3.3 Card (`src/components/ui/Card.tsx`)

- **Props:** `title?`, `subtitle?`, `children`, `className?`, `actions?`.
- **Used by:** DashboardPage, StoragePage, ApiKeysPage, SettingsPage (profile card).

### 3.4 Collapsible (`src/components/ui/Collapsible.tsx`)

- **Props:** `label`, `children`, `defaultOpen?`, `badge?`.
- **Used by:** GraphPage (node properties panel).

### 3.5 ConfirmDialog (`src/components/ui/ConfirmDialog.tsx`)

- **Props:** `open`, `title`, `description`, `confirmLabel?`, `danger?`, `onConfirm`, `onCancel`.
- **Features:** Escape key to cancel, auto-focus confirm button, backdrop blur.
- **Used by:** ProjectSettingsPage (delete), ApiKeysPage (revoke/rotate), StoragePage (delete file).

### 3.6 EmptyState (`src/components/ui/EmptyState.tsx`)

- **Props:** `icon`, `title`, `description?`, `action?`.
- **Used by:** ChatPage, IngestPage, MemoryPage, FactsPage, DecisionsPage, TimelinePage, GraphPage, SearchPage, SessionsPage, ProvenancePage, ApiKeysPage, StoragePage, ProjectSettingsPage.

### 3.7 ErrorAlert (`src/components/ui/ErrorAlert.tsx`)

- **Props:** `title?` (default "Error"), `message`, `onRetry?`, `onDismiss?`.
- **Used by:** LoginPage, RegisterPage, IngestPage, MemoryPage, FactsPage, DecisionsPage, TimelinePage, GraphPage, SearchPage, SessionsPage, ProvenancePage, SessionDetailPage, ProjectSettingsPage, SettingsPage.

### 3.8 FileInput (`src/components/ui/FileInput.tsx`)

- **Props:** `onFile`, `accept?`, `disabled?`, `children?`.
- **Features:** Drag-and-drop support, click to browse, keyboard accessible.
- **Used by:** StoragePage.

### 3.9 LoadingSpinner (`src/components/ui/LoadingSpinner.tsx`)

- **Props:** `size?` ('sm'|'md'|'lg').
- **Used by:** ProjectSettingsPage, ProfilePage, ApiKeysPage.

### 3.10 Pagination (`src/components/ui/Pagination.tsx`)

- **Props:** `page`, `totalPages`, `onPageChange`, `className?`.
- **Features:** Ellipsis for large page counts, prev/next buttons, aria labels.
- **Used by:** MemoryPage, FactsPage, DecisionsPage, SearchPage, SessionsPage.

### 3.11 Progress (`src/components/ui/Progress.tsx`)

- **Props:** Implicit from usage — `value`, `label?` (via className), `variant` via size.
- **Features:** Animated width transition, percentage display.
- **Used by:** IngestPage (upload progress).

### 3.12 Skeleton (`src/components/ui/Skeleton.tsx`)

- **Props:** `className?`, `lines?` (default 3).
- **Used by:** DashboardPage (via StatCard's `loading` prop).

### 3.13 StatCard (`src/components/ui/StatCard.tsx`)

- **Props:** `label`, `value`, `icon?`, `trend?`, `loading?`, `className?`.
- **Loading state:** Shimmer animation placeholder.
- **Used by:** DashboardPage.

### 3.14 Tabs (`src/components/ui/Tabs.tsx`)

- **Props:** `items` (array of `{id, label}`), `active`, `onSelect`, `children`.
- **Children:** `TabPanel` components that show/hide based on `active` value via context.
- **Used by:** None currently (defined but not used in any page — the pages use inline tab buttons instead).

### 3.15 Toast (`src/components/ui/Toast.tsx`)

- **Props/Context:** `ToastProvider` wraps app, `useToast()` returns `{ toast(message, variant) }`.
- **Variants:** info, success, warning, error.
- **Auto-dismiss:** 4 seconds.
- **Note:** `ToastProvider` is exported but NOT currently used in the app wrapper (not in `layout.tsx` or `AppShell`). The toast system exists but is not wired up.

### 3.16 Tooltip (`src/components/ui/Tooltip.tsx`)

- **Props:** `text`, `children`.
- **Features:** Hover and focus triggers, fixed positioning based on trigger rect.
- **Used by:** Sidebar, DashboardPage, ProjectsPage.

### 3.17 useClipboard (`src/components/ui/useClipboard.ts`)

- **Returns:** `{ copied, copy }`.
- **Features:** Clipboard API with `document.execCommand('copy')` fallback, auto-reset after timeout.
- **Used by:** ApiKeysPage, ProjectSettingsPage.

---

## Section 4: API Client

### 4.1 HTTP Client

**File:** `src/lib/api.ts`

- **Library:** Native `fetch()` (no axios, no wrapper library).
- **Base URL:** `process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'` (from `.env.example`: `http://localhost:8000`).
- **Content-Type:** Auto-set to `application/json` unless body is `FormData`.
- **Credentials:** `credentials: 'include'` on all requests (for CSRF cookies).

### 4.2 REST Methods

| Function | Method | Signature |
|---|---|---|
| `apiGet` | GET | `apiGet<T>(path: string): Promise<T>` |
| `apiPost` | POST | `apiPost<T>(path: string, body?: unknown): Promise<T>` |
| `apiPatch` | PATCH | `apiPatch<T>(path: string, body: unknown): Promise<T>` |
| `apiDelete` | DELETE | `apiDelete<T>(path: string): Promise<T>` |

### 4.3 Authentication Token Handling

- **Storage:** `localStorage` key `sv_tokens` — JSON with `{ access_token, refresh_token }`.
- **Token retrieval:** `getToken()` reads `sv_tokens` from `localStorage`, parses JSON, returns `access_token`.
- **Token refresh:** Automatic 401 retry flow:
  1. Initial request with current token.
  2. If 401, call `refreshAccessToken()` → POST `/api/v1/auth/refresh` with `refresh_token`.
  3. Retry original request with new token.
  4. If retry also 401, clear tokens.
- **Token cleanup:** `clearTokens()` removes `sv_tokens` from `localStorage`.
- **Token storage:** `storeTokens(tokens)` saves `{ access_token, refresh_token }` to `localStorage`.

### 4.4 Error Handling

- **Non-OK responses:** Throws `Error` with message extracted from response:
  1. Try parsing JSON → use `detail` or `message` field.
  2. Fall back to raw text.
  3. Attach `status` property to error.
- **204 responses:** Returns `undefined` (no JSON parsing).
- **Network errors:** Caught by caller, formatted via `formatApiError()` from `errors.ts`.

### 4.5 Error Formatting (`src/lib/errors.ts`)

- **`formatApiError(err)`:** Maps errors to `{ title, message }`:
  - HTTP status code mapping (400, 401, 403, 404, 409, 422, 429, 500, 502, 503).
  - Detail code mapping (not_found, already_exists, invalid_credentials, token_expired, rate_limit_exceeded, validation_error, permission_denied, internal_error, upload_failed, ingest_error, project_not_found).
- **`isNetworkError(err)`:** Checks for "Failed to fetch", "NetworkError", "Network request failed".
- **`isAuthError(err)`:** Checks for 401 status or "token"/"unauthorized"/"authentication" in message.

### 4.6 SSE Streaming

**Two implementations exist:**

1. **`streamChat()` in `lib/api.ts`** — Async generator function:
   - POST `/api/v1/chat/stream` with `{ message }`.
   - Yields `event.content` for `token` events.
   - Returns on `done` event.
   - Throws on `error` event.
   - **Not used by any page** (the Chat page has its own inline implementation).

2. **`useSSE()` hook in `hooks/useSSE.tsx`** — React hook with callback-based API:
   - Same endpoint: POST `/api/v1/chat/stream`.
   - Callbacks: `onMessage`, `onDone`, `onError`.
   - Handles `token`, `sources`, `done`, `error` event types.
   - AbortController support via `stop()`.
   - **Used by `useChat` feature hook** (but `useChat` itself is NOT used by the Chat page).

### 4.7 File Upload

**`uploadFile()` in `lib/api.ts`:**
- Uses `XMLHttpRequest` (XHR) for progress tracking.
- POST to `/api/v1/ingest/upload`.
- `FormData` with `project_id`, `source_type` (auto-detected from file extension), `file`.
- Progress callback via `xhr.upload.addEventListener('progress')`.
- Bearer token in `Authorization` header.

### 4.8 Raw fetch() Usage in Pages

The following pages use raw `fetch()` directly instead of the API client:
- **ChatPage:** Creates session and streams chat directly.
- **Settings/Profile:** Some pages use raw `fetch('/api/v1/auth/me')` for workspace_id (StoragePage).
- **E2E tests:** All use raw `fetch()` with `X-E2E` header.

---

## Section 5: State Management

### 5.1 State Library

- **No external state management library detected.** The project uses:
  - **React Context** for global state (Auth, Theme).
  - **`useState` / `useCallback` / `useEffect`** for component-level state.
  - **No Redux, Zustand, Jotai, Recoil, or similar.**

### 5.2 Server State (Data Fetching)

- **No data fetching library** (no React Query, SWR, RTK Query).
- **Pattern:** Each page/feature hook manages its own server state via `useState` + `useEffect` + `useCallback`.
- **No caching layer** — every mount triggers a fresh API call.
- **No stale-while-revalidate** pattern.
- **No request deduplication** — each hook independently fetches.

### 5.3 Client State

| Context | Provider | State | Consumers |
|---|---|---|---|
| `AuthContext` | `useAuth.tsx` | `user`, `loading`, `error`, `login`, `register`, `logout`, `clearError` | All pages via `useAuth()` |
| `ThemeContext` | `useTheme.tsx` | `mode`, `resolved`, `setMode` | Used in globals.css via `data-theme` attribute |

### 5.4 Feature Hook State Pattern

All feature hooks follow the same pattern:
```ts
const [items, setItems] = useState<T[]>([]);
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
const load = useCallback(async () => { ... }, [deps]);
useEffect(() => { load(); }, [load]);
return { items, loading, error, reload: load };
```

Hooks: `useProjects`, `useProject`, `useGraph`, `useSources`, `useFacts`, `useDecisions`, `useIngestJobs`, `useApiKeys`, `useSearch`, `useMemoryList`, `useMemorySearch`.

Mutation hooks (`useCreateProject`, `useUpdateProject`, `useDeleteProject`, `useCreateMemory`, `useDeleteMemory`, `useUploadFile`, `useCreateKey`, `useRevokeKey`, `useRotateKey`) follow a similar pattern with `loading`/`error` state and a callback action.

---

## Section 6: Styling

### 6.1 Tailwind Classes Usage

- **Framework:** Tailwind CSS v3.4 with `@tailwind` directives in `globals.css`.
- **Custom CSS approach:** All design tokens are CSS custom properties (variables) defined in `globals.css`, referenced in Tailwind classes via `var(--sv-*)` syntax.
- **Example:** `bg-[var(--sv-bg-primary)]`, `text-[var(--sv-text-primary)]`, `border-[var(--sv-border-default)]`.
- **No `@apply` directives** used extensively — classes are written inline in JSX.

### 6.2 Custom CSS (`globals.css`)

**Design Token Categories:**
- **Surfaces:** `--sv-bg-base`, `--sv-bg-raised`, `--sv-bg-overlay`, `--sv-bg-sunken`, `--sv-bg-input`
- **Borders:** `--sv-border-default`, `--sv-border-subtle`, `--sv-border-strong`, `--sv-border-focus`
- **Text:** `--sv-text-primary`, `--sv-text-secondary`, `--sv-text-tertiary`, `--sv-text-disabled`, `--sv-text-inverse`
- **Accent:** `--sv-accent` (indigo-500: #6366f1), `--sv-accent-hover`, `--sv-accent-muted`, `--sv-accent-subtle`
- **Semantic:** `--sv-success`, `--sv-warning`, `--sv-error`, `--sv-info`
- **Authority (6 levels):** unverified, inferred, observed, decision, verified, certified
- **Evidence (4 levels):** ingested, processed, integrated, proven
- **Temporal (3 levels):** active, superseded, archived
- **Motion:** duration (fast/base/slow), easing curves
- **Typography:** font families (Inter, JetBrains Mono), sidebar width, header height
- **Radius:** sm (6px), md (8px), lg (12px)
- **Shadows:** sm, md, lg
- **Z-index:** dropdown (100), sticky (200), modal (300), toast (400)

**Light theme** overrides via `[data-theme="light"]` selector — swaps all surface, text, border, and shadow values.

**Animations:**
- `sv-pulse-dot` — opacity pulse (used for "Thinking..." indicator)
- `sv-shimmer` — gradient shimmer (used in Skeleton/StatCard loading)
- `sv-fade-in` — fade in
- `sv-slide-up` — slide up with opacity

**Accessibility:**
- `sr-only` with `:focus` variant for skip navigation.
- `:focus-visible` styling with accent border.
- `prefers-reduced-motion` media query kills all animations.
- Custom scrollbar styling (dark/light aware).

**Base reset:**
- `box-sizing: border-box`
- Full-height html/body
- Selection color = accent
- `color-scheme: dark/light` for form controls

### 6.3 Theme Handling

- **Strategy:** `data-theme` attribute on `<html>` element. Values: `"dark"` (default), `"light"`.
- **Provider:** `ThemeProvider` in `useTheme.tsx`:
  - Reads `sv_theme` from `localStorage` on init (values: 'dark', 'light', 'system').
  - Default: 'dark'.
  - Applies theme via `document.documentElement.setAttribute('data-theme', theme)`.
  - Listens for `prefers-color-scheme` changes when mode is 'system'.
- **SSR guard:** Inline `<script>` in `layout.tsx` sets `data-theme="light"` before React hydrates if `sv_theme` is 'light' in localStorage.
- **Tailwind config:** `darkMode: 'class'` (but the app doesn't actually use `dark:` prefix classes — it uses CSS variables with `data-theme`).

### 6.4 Responsive Design

- **Approach:** Tailwind responsive prefixes (`sm:`, `lg:`).
- **Breakpoints used:**
  - `sm:` (640px) — Dashboard stat grid columns, project card grid
  - `md:` — Not directly used in Tailwind breakpoints
  - `lg:` (1024px) — Graph page two-column layout, project card grid
  - `xl:` — Not used
- **Custom responsive behavior:**
  - Sidebar auto-collapses at viewport < 768px (via `useEffect` + `resize` listener).
  - Dashboard grid: 2 columns (sm), 3 columns (sm+ for stats), 6 columns (lg).
  - Project cards: 2 columns (sm), 3 columns (lg).
- **E2E tests verify:** Mobile (390x844), Tablet (768x1024), Desktop (1440x900, 1280x720) — checking for horizontal overflow.

---

## Section 7: Authentication Flow

### 7.1 Login Page

- **File:** `src/app/auth/login/page.tsx`
- **Form:** Email + Password fields.
- **Action:** Calls `useAuth().login(email, password)`.
- **Flow:**
  1. POST `/api/v1/auth/login` with `{ email, password }`.
  2. On success: stores tokens via `storeTokens()`, GETs `/api/v1/auth/me` for user info.
  3. Redirects to `/dashboard` via `router.push()`.
- **Error display:** `ErrorAlert` with server error message.

### 7.2 Registration Page

- **File:** `src/app/auth/register/page.tsx`
- **Form:** Full name, Email, Workspace name, Password, Confirm password.
- **Client validation:** Password mismatch check.
- **Action:** Calls `useAuth().register({ email, password, name, workspace_name })`.
- **Flow:**
  1. POST `/api/v1/auth/register` with `{ email, password, name, workspace_name }`.
  2. On success: stores tokens, GETs `/api/v1/auth/me`.
  3. Redirects to `/dashboard`.
- **Note:** `password_confirm` is NOT sent to the backend — it's only checked client-side.

### 7.3 Token Storage

- **Location:** `localStorage` key `sv_tokens`.
- **Format:** JSON `{ access_token: string, refresh_token: string }`.
- **No HttpOnly cookies** for tokens — purely client-side storage.
- **No sessionStorage** — uses localStorage for persistence across tabs.

### 7.4 Token Refresh

- **Automatic:** In `lib/api.ts` `request()` function:
  1. On 401 response, calls `refreshAccessToken()`.
  2. POST `/api/v1/auth/refresh` with `{ refresh_token }`.
  3. Stores new tokens.
  4. Retries original request.
  5. If retry 401 or refresh fails, clears tokens.
- **Timeout guard:** AuthProvider has an 8-second timeout for the initial `/api/v1/auth/me` call — if it doesn't resolve, clears loading state.

### 7.5 Logout

- **Implementation:** `useAuth().logout()`:
  1. POST `/api/v1/auth/logout` with `{ refresh_token }` (best effort — doesn't throw if it fails).
  2. Calls `clearTokens()` to remove from localStorage.
  3. Resets auth state to `{ user: null, loading: false, error: null }`.
- **Sidebar:** Has a Logout button that calls `logout()` then `router.push('/auth/login')`.
- **No server-side session invalidation** if the logout POST fails.

### 7.6 Protected Routes

- **Guard:** `AppShell` component (`src/hooks/AppShell.tsx`):
  - While loading: shows "Loading..." spinner.
  - Auth pages (`/auth/login`, `/auth/register`, `/`): rendered without sidebar.
  - If authenticated: renders `<Sidebar />` + `<main>` content area.
  - If not authenticated and not auth page: returns `null` (redirect via `router.replace`).
- **Redirect logic:**
  - `!user && !isAuthPage` → `router.replace('/auth/login')`
  - `user && isAuthPage` → `router.replace('/dashboard')`
- **Public paths:** `/auth/login`, `/auth/register`, `/`.
- **Auth check:** `/api/v1/auth/me` on app load to validate stored tokens.

### 7.7 Auth Context

- **File:** `src/hooks/useAuth.tsx`
- **State:** `{ user: UserInfo | null, loading: boolean, error: string | null }`
- **Methods:** `login()`, `register()`, `logout()`, `clearError()`
- **Type:** `UserInfo` = `{ id, email, name, workspace_id, tenant_id }`

---

## Section 8: E2E Tests

### 8.1 Test Framework

- **Framework:** Playwright v1.62.1
- **Config:** `playwright.config.ts`
- **Base URL:** `http://localhost:3000` (frontend) via `PLAYWRIGHT_BASE_URL`
- **API Base:** `http://localhost:8000` via `PLAYWRIGHT_API_URL`
- **Browser:** Chromium only (Desktop Chrome)
- **Workers:** 1 (sequential)
- **Retries:** 0 locally, 2 in CI
- **Reporter:** `list`
- **Web server:** `npm run dev`, port 3000, 30s timeout, reuses existing.
- **Trace:** `on-first-retry`
- **Video:** `retain-on-failure`

### 8.2 Test Helper

**File:** `e2e/test-helpers.ts`

- **`clearAuth(page)`:** Clears `sv_tokens` from localStorage.
- **`installAuthIsolation()`:** Installs global beforeEach/afterEach that clears auth.
- **`apiRequest()`:** HTTP helper with `X-E2E: true` header (bypasses rate limiter).
- **`uid()`:** Random string generator for test isolation.
- **`loginViaUI()`:** Navigates to login, fills form, waits for dashboard URL.
- **`registerAndLoginUI()`:** Registers via API, logs in via UI.
- **`captureConsoleErrors()`:** Captures console/page errors for assertion.
- **`filterConsoleNoise()`:** Filters UV_HANDLE_CLOSING and DevTools noise.
- **`mainContent()` / `sidebar()`:** Selector helpers for landmarks.

### 8.3 Global Setup

**File:** `e2e/global-setup.ts`

- No-op — web server lifecycle handled by Playwright config.

### 8.4 Test Files

#### `e2e/auth.spec.ts` (7 tests)

| Test | Description |
|---|---|
| Login page renders with form elements | Checks h1, email input, password input, Sign in button |
| Register page link is accessible | "Create one" link on login page |
| Login with invalid credentials shows error | Fills bad credentials, expects error message |
| Login with empty fields validates | Submits empty form, expects to stay on login |
| Register page renders | Checks h1, email input, password inputs |
| Register with mismatched passwords shows error | Fills mismatched passwords, expects error |
| Login link on register page works | Navigates between login and register |

#### `e2e/dashboard.spec.ts` (3 tests)

| Test | Description |
|---|---|
| Unauthenticated dashboard redirects to login | Navigates to /dashboard, expects redirect |
| Unauthenticated projects redirects to login | Navigates to /projects, expects redirect |
| Unauthenticated settings redirects to login | Navigates to /settings, expects redirect |

#### `e2e/api-e2e.spec.ts` (13 tests across 5 describe blocks)

| Suite | Tests | Description |
|---|---|---|
| Golden Journey | 1 | Full workflow: register→login→project→upload→ingest→search→chat→provenance |
| Authentication | 3 | Register creates user, login returns tokens, login rejects wrong password |
| Tenant Isolation | 1 | Tenant A cannot see Tenant B data |
| Connectors | 3 | ChatGPT, Claude, JSONL uploads succeed |
| Security - Prompt Injection | 1 | Malicious content stored as data only |
| Error Handling | 2 | Malformed body → 422, nonexistent endpoint → 404 |
| Health | 2 | Liveness and readiness endpoints |

#### `e2e/frontend-journey.spec.ts` (5 tests)

| Test | Description |
|---|---|
| Full journey: dashboard → create project → navigate | Registers, creates project, visits dashboard/projects/settings |
| Sidebar navigation is present and links work | Checks sidebar nav links |
| Logout redirects to login | Clears tokens, verifies redirect |
| Unauthenticated access redirects to login | Navigates to dashboard without auth |

#### `e2e/golden-journey.spec.ts` (12 tests)

| Test | Description |
|---|---|
| Register → login → workspace → project → upload → ingestion → search → chat → evidence → provenance | Full UI journey |
| Register creates new user | API-level registration check |
| Login returns tokens | Token pair verification |
| Login rejects wrong password | Auth rejection |
| Protected endpoint rejects missing token | 401 check |
| Tenant A and B are isolated | Cross-tenant data isolation |
| ChatGPT/Claude/JSONL connector normalizes | Connector registration |
| Malicious content stored as data | Security check |
| Malformed JSON returns 422 | Error handling |
| Nonexistent endpoint returns 404 | Error handling |
| Liveness/Readiness | Health checks |

#### `e2e/search-chat-certification.spec.ts` (14 tests across 3 describe blocks)

| Suite | Tests | Description |
|---|---|---|
| Search Browser Certification | 8 | Page renders, input, filter, button, API contract, empty results, console clean, responsive |
| Chat Browser Certification | 8 | Page renders, empty state, SSE contract, auth rejection, send message, console clean, responsive, evidence button |
| Network Contracts | 2 | Search POST contract, memory GET contract |

#### `e2e/ui-certification.spec.ts` (136+ tests across 15 describe blocks)

| Suite | Tests | Description |
|---|---|---|
| UI Browser Certification - Authenticated | 11 | Dashboard, project creation, projects, chat, search, memory, settings, ingest, facts, decisions render + interactions |
| Search Network Contract | 2 | POST contract, memory_type filter |
| Memory Network Contract | 6 | API contract, page structure, schema verification, filter by type, filter by temporal, empty state |
| Facts Network Contract | 2 | API contract, page rendering |
| Decisions Network Contract | 2 | API contract, page rendering |
| Timeline Network Contract | 4 | API contract, heading, empty state, sorting |
| Sessions Network Contract | 4 | API contract, heading, empty state, schema |
| Graph Network Contract | 4 | API contract, heading, empty state, schema |
| Provenance Network Contract | 5 | API contract, heading, empty state, schema, auth required |
| Provenance Detail and Chain | 4 | Detail by ID, session filter, memory expansion, 404 |
| Graph Deep Certification | 6 | project_id filter, include_historical, node fields, edge fields, node_type values, empty project |
| Graph UI Interactions | 3 | Empty state, detail panel, node type badges, no overflow |
| Cross-Page Knowledge Chain | 3 | Search→Memory→Provenance, Session→Timeline, Memory→Facts→Decisions |
| Sessions Project-Filter Honesty | 2 | Backend doesn't filter by project_id, page communicates workspace scope |
| Responsive Certification | 6 | Mobile/tablet/desktop for Timeline, Sessions, Graph, Dashboard |
| Accessibility Regression | 6 | Heading hierarchy, no horizontal overflow |
| Keyboard Accessibility | 4 | Tab order, Enter submit, Chat Enter/Shift+Enter, Modal Escape |
| Visual Evidence Screenshots | 9 | Desktop/mobile screenshots for Dashboard, Timeline, Sessions, Graph, Memory, Settings |
| Network & Console Cleanliness | 7 | No console errors on Memory, Facts, Decisions, Ingest, Settings, Provenance, Session detail |
| State Semantics | 4 | Facts confidence, Decisions temporal, Provenance fields, Timeline icons |
| Expanded Responsive Coverage | 16+ | Mobile/tablet/desktop for all project pages, no overflow checks |
| Identifier Continuity Audit | 4 | Project ID consistency, memory IDs, session ID stability, graph node IDs |
| Full Regression | 12 | All core pages render without errors |

### 8.5 Archived Tests

- `e2e/_archive/debug-auth.spec.ts` — Debug auth test (archived)
- `e2e/_archive/test-diag.spec.ts` — Diagnostic test (archived)

---

## Section 9: Additional Findings

### 9.1 Unused/Dead Code

1. **`AuthRedirect` component** (`src/hooks/AuthRedirect.tsx`): Defined and exported but never imported/used anywhere. The `AppShell` component handles all auth redirect logic.

2. **`streamChat()` function** (`src/lib/api.ts`): Async generator SSE implementation. Not used by any page — the Chat page has its own inline SSE implementation, and the `useSSE` hook has a separate implementation.

3. **`useChat` feature hook** (`src/features/chat/useChat.ts`): Defined with full SSE streaming logic. Not used by the Chat page, which has its own inline implementation.

4. **`Tabs` / `TabPanel` components** (`src/components/ui/Tabs.tsx`): Fully implemented with context-based active panel switching. Not used in any page.

5. **`ToastProvider` / `useToast`** (`src/components/ui/Toast.tsx`): Fully implemented toast notification system. Not wired into the app (not in `layout.tsx` or `AppShell`).

6. **`Skeleton` component** (`src/components/ui/Skeleton.tsx`): Defined but only used indirectly via `StatCard`'s `loading` prop. Never used standalone.

7. **`useSSE` hook** (`src/hooks/useSSE.tsx`): Implemented but only consumed by `useChat` feature hook, which is itself unused.

8. **`useMemorySearch`** in `useMemory.ts`: Defined but not used by any page.

9. **`useIngestJobs`** in `useIngest.ts`: Defined but not used by any page.

### 9.2 Duplicate/Inconsistent Implementations

1. **SSE streaming:** Three separate implementations of the same SSE logic:
   - `streamChat()` in `lib/api.ts` (async generator)
   - `useSSE()` hook (callback-based)
   - Inline SSE parsing in `ChatPage` (manual ReadableStream parsing)
   All three target `/api/v1/chat/stream` with slightly different event handling.

2. **Token refresh:** Both `lib/api.ts` `request()` and `useSSE` hook have their own token retrieval logic, but only `request()` handles refresh retry. `useSSE` and `ChatPage` get tokens fresh but don't handle refresh.

3. **Error messages:** Pages use a mix of `ErrorAlert` component, inline styled divs, and `alert()`:
   - `ErrorAlert`: Login, Register, Ingest, Memory, Facts, Decisions, Timeline, Graph, Search, Sessions, Provenance, SessionDetail, ProjectSettings.
   - Inline div: SettingsPage (custom styled success/error banners).
   - `alert()`: DashboardPage (project creation), ProjectSettings (delete).
   - Plain text: StoragePage.

4. **Auth token injection in E2E tests:** Multiple test files each define their own `apiRequest()`, `setAuthAndGo()`, and `uid()` functions with slight variations (some use `password_confirm`, some don't).

### 9.3 Type Inconsistencies

1. **`ApiKeyOut`** is defined in both `src/types/api.ts` and `src/features/apiKeys/useApiKeys.ts` with slightly different shapes (the feature hook version includes `raw_key?`).

2. **`ChatMessage`** is defined in both `src/app/projects/[id]/chat/page.tsx` (local interface) and `src/features/chat/useChat.ts` (exported interface) with different fields.

3. **`Pagination` component:** Used in some pages with `totalPages={page + 2}` (approximation) and in SearchPage with actual calculated `totalPages`. The `totalPages` prop is required but pages calculate it inconsistently.

4. **Memory endpoint response type:** `types/api.ts` types `MemoryItemOut` as a single item, but the Memory page and `useMemoryList` treat the response as an array `MemoryItemOut[]`. The backend actually returns an array directly (not `PaginatedResponse`).

### 9.4 Potential Bugs

1. **StoragePage uses `workspace_id` as `projectId`:** The `uploadFile()` call in `StoragePage` passes `projectId` which was set from `workspace_id` from `/api/v1/auth/me`. The ingest endpoint expects a project_id, not workspace_id.

2. **Pagination logic in MemoryPage:** `total` is set to `data.length` (not a server-provided total), and `totalPages` is calculated as `page + 2` — this means pagination appears prematurely and the "last page" is always wrong.

3. **SearchPage pagination:** Uses client-side slicing (`results.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)`) on all results, but the API only returns `limit=10` results. So page 2+ will always be empty unless the API returns more than 10 results.

4. **ChatPage SSE doesn't handle token refresh:** If the access token expires during a stream, the stream will fail with 401 and there's no retry/refresh logic.

5. **`useChat` hook's `stream()` callback captures `projectId` from opts but the `lib/api.ts` `streamChat()` function doesn't accept projectId at all** — they're separate implementations with different capabilities.

6. **Session scope mismatch:** The Sessions page subtitle says "in this workspace" but the sessions endpoint accepts `project_id` as a query param (the backend may or may not filter by it). The `remaining-contracts.spec.ts` explicitly tests and documents that the backend does NOT filter sessions by project_id.

7. **Settings page `loadData` dependency:** `useCallback` depends on `user?.id`, but `user` is from `useAuth()` which is a stable reference. The effect runs on mount and whenever `user?.id` changes.

8. **`useMemoryList` re-fetches on every `memoryType` change** without preserving the current page offset, which can lead to unexpected pagination resets.

### 9.5 Package Dependencies

**Runtime (2):**
- `lucide-react` ^0.468.0 — Icon library
- `next` ^15.0.0 — Framework
- `react` ^18.3.0 / `react-dom` ^18.3.0 — UI library

**Dev (7):**
- `@playwright/test` ^1.62.1 — E2E testing
- `@types/node` ^20.0.0, `@types/react` ^18.3.0, `@types/react-dom` ^18.3.0 — TypeScript types
- `autoprefixer` ^10.4.0 — CSS autoprefixer
- `eslint` ^8.57.0 / `eslint-config-next` ^15.0.0 — Linting
- `postcss` ^8.4.0 / `tailwindcss` ^3.4.0 — Styling
- `typescript` ^5.0.0 — Type checking

**Notable absences:**
- No state management library (Redux, Zustand, etc.)
- No data fetching library (React Query, SWR)
- No form library (React Hook Form, Formik)
- No validation library (Zod, Yup)
- No component library (MUI, Chakra, etc.)
- No animation library (Framer Motion)

### 9.6 TypeScript Configuration

- **Target:** ES5
- **Module:** ESNext with bundler resolution
- **Strict mode:** Enabled
- **Path alias:** `@/*` → `./src/*`
- **JSX:** preserve (Next.js handles transformation)
- **Excluded:** `node_modules`, `e2e`

---

*End of forensic inventory.*
