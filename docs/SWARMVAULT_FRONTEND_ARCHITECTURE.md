# SwarmVault Frontend Architecture

> Forensic reconciliation document. Read-only analysis. No code changes.
> Generated from static source inspection of `C:\Users\Administrator\Documents\SwarmVaultwebapp\frontend\`

---

## 1. NEXT.JS ARCHITECTURE

### Framework & Version

- **Next.js 15** (^15.0.0) with **React 18.3.0**
- **TypeScript 5** with strict mode
- `reactStrictMode: true` in `next.config.js:3`
- Module resolution: `bundler` (ESM), JSX: `preserve`

### App Router — Route Structure

All pages are under `frontend/src/app/` using the Next.js App Router. Every page component is a client component (`'use client'`).

**Route map (21 pages):**

| Route | File | Component |
|---|---|---|
| `/` | `src/app/page.tsx` | `HomePage` — redirect to `/dashboard` or `/auth/login` |
| `/auth/login` | `src/app/auth/login/page.tsx` | `LoginPage` |
| `/auth/register` | `src/app/auth/register/page.tsx` | `RegisterPage` |
| `/dashboard` | `src/app/dashboard/page.tsx` | `DashboardPage` |
| `/projects` | `src/app/projects/page.tsx` | `ProjectsPage` |
| `/settings` | `src/app/settings/page.tsx` | `SettingsPage` (tabs: workspace, members, invitations) |
| `/settings/profile` | `src/app/settings/profile/page.tsx` | `ProfilePage` |
| `/settings/api-keys` | `src/app/settings/api-keys/page.tsx` | `ApiKeysPage` (uses `@/features/apiKeys/useApiKeys`) |
| `/settings/storage` | `src/app/settings/storage/page.tsx` | `StoragePage` (uses `@/features/ingest/useIngest`) |
| `/projects/[id]` | `src/app/projects/[id]/layout.tsx` | `ProjectLayout` — sub-navigation + project editing |
| `/projects/[id]/chat` | `src/app/projects/[id]/chat/page.tsx` | `ChatPage` |
| `/projects/[id]/ingest` | `src/app/projects/[id]/ingest/page.tsx` | `IngestPage` |
| `/projects/[id]/sessions` | `src/app/projects/[id]/sessions/page.tsx` | `SessionsPage` |
| `/projects/[id]/sessions/[sessionId]` | `src/app/projects/[id]/sessions/[sessionId]/page.tsx` | `SessionDetailPage` |
| `/projects/[id]/memory` | `src/app/projects/[id]/memory/page.tsx` | `MemoryPage` |
| `/projects/[id]/facts` | `src/app/projects/[id]/facts/page.tsx` | `FactsPage` |
| `/projects/[id]/decisions` | `src/app/projects/[id]/decisions/page.tsx` | `DecisionsPage` |
| `/projects/[id]/timeline` | `src/app/projects/[id]/timeline/page.tsx` | `TimelinePage` |
| `/projects/[id]/graph` | `src/app/projects/[id]/graph/page.tsx` | `GraphPage` |
| `/projects/[id]/search` | `src/app/projects/[id]/search/page.tsx` | `SearchPage` |
| `/projects/[id]/provenance` | `src/app/projects/[id]/provenance/page.tsx` | `ProvenancePage` |

### Layout Hierarchy

```
RootLayout (src/app/layout.tsx:12)
├── ThemeProvider (src/hooks/useTheme.tsx:26)
│   └── AuthProvider (src/hooks/useAuth.tsx:20)
│       └── AppShell (src/hooks/AppShell.tsx:7)
│           ├── Sidebar (src/components/Sidebar.tsx:105)  [when authenticated]
│           │   ├── NavGroup — Workspace
│           │   ├── NavGroup — Knowledge
│           │   ├── NavGroup — Ingestion
│           │   ├── ProjectNav (contextual, when inside /projects/[id])
│           │   └── NavGroup — Account + Logout
│           └── <main> (content area)
└── children (page route)
```

The `ProjectLayout` (`src/app/projects/[id]/layout.tsx:12`) wraps project sub-pages with its own left sidebar (192px) for project navigation and editing.

### SSR/SSG Patterns

**There are no server components.** Every page is `'use client'`. The application is entirely client-rendered (CSR). The `layout.tsx` at root is a server component but contains only provider wiring. There are no `generateStaticParams`, `generateMetadata`, or server-side data fetching patterns. All data fetching happens via `useEffect` in client components after mount.

The root `layout.tsx:7` exports a static `metadata` object with title and description. It also injects an inline script (`layout.tsx:16-20`) that runs before React hydration to read `sv_theme` from localStorage and set `data-theme` on `<html>`, preventing a flash of unstyled content on theme change.

---

## 2. STYLING

### Tailwind Configuration

`tailwind.config.js`:
```js
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  darkMode: 'class',
  theme: { extend: {} },
  plugins: [],
};
```

Minimal config — all design tokens live in CSS custom properties. Tailwind is used purely for utility classes (spacing, layout, typography, responsive). No custom theme extensions.

### CSS Variables — Design Token System

Defined in `src/app/globals.css:10-95`. Token categories:

**Surfaces** (6 levels): `--sv-bg-base`, `--sv-bg-raised`, `--sv-bg-overlay`, `--sv-bg-sunken`, `--sv-bg-input`

**Borders** (4 levels): `--sv-border-default`, `--sv-border-subtle`, `--sv-border-strong`, `--sv-border-focus`

**Text** (5 levels): `--sv-text-primary`, `--sv-text-secondary`, `--sv-text-tertiary`, `--sv-text-disabled`, `--sv-text-inverse`

**Accent**: `--sv-accent` (#6366f1 indigo), `--sv-accent-hover`, `--sv-accent-muted` (40% opacity), `--sv-accent-subtle` (10% opacity)

**Semantic**: `--sv-success` (#22c55e), `--sv-warning` (#f59e0b), `--sv-error` (#ef4444), `--sv-info` (#3b82f6)

**Authority** (6 levels matching Badge component): `--sv-auth-unverified` through `--sv-auth-certified`

**Evidence class** (4 levels): `--sv-evidence-ingested` through `--sv-evidence-proven`

**Temporal status** (3 levels): `--sv-temporal-active`, `--sv-temporal-superseded`, `--sv-temporal-archived`

**Motion**: `--sv-duration-fast` (100ms), `--sv-duration-base` (200ms), `--sv-duration-slow` (350ms), four easing curves (base, enter, exit, spring)

**Typography**: `--sv-font-sans` (Inter → system-ui fallback chain), `--sv-font-mono` (JetBrains Mono → Fira Code → SF Mono)

**Spacing**: `--sv-sidebar-width` (14rem / 224px), `--sv-sidebar-collapsed` (3.5rem), `--sv-header-height` (3rem)

**Radius**: `--sv-radius-sm` (6px), `--sv-radius-md` (8px), `--sv-radius-lg` (12px)

**Shadows**: `--sv-shadow-sm/md/lg` with black alpha

**Z-index**: `--sv-z-dropdown` (100), `--sv-z-sticky` (200), `--sv-z-modal` (300), `--sv-z-toast` (400)

### Light Theme Override

`globals.css:98-119` — `[data-theme="light"]` overrides surfaces, borders, text, and shadows. Does NOT override accent, semantic, authority, evidence, temporal, motion, or typography tokens (those remain theme-agnostic).

**GAP**: `globals.css:14` defines `--sv-bg-base: #0a0a0f`. The login page (`auth/login/page.tsx:24`) uses `bg-[var(--sv-bg-primary)]` — but `--sv-bg-primary` is **never defined**. This falls back to `inherit` (effectively black/transparent). Same issue on register page `auth/register/page.tsx:30` and home page `page.tsx:14`. This is a CSS variable gap — the intent was clearly `--sv-bg-base`.

### Built-in Animations

`globals.css:161-191` defines three named animations:
- `sv-pulse-dot` (1.5s loop, opacity pulse)
- `sv-shimmer` (loading skeleton effect using gradient)
- `sv-fade-in` / `sv-slide-up` (entry transitions using duration/easing tokens)

`globals.css:194-200` — `prefers-reduced-motion: reduce` kills all animation durations.

---

## 3. COMPONENT ARCHITECTURE

### UI Primitive Library (`src/components/ui/`)

17 exported components in `src/components/ui/index.ts`:

| Component | File | Purpose |
|---|---|---|
| `Card` | `Card.tsx` | Surface with optional header (title/subtitle/actions) |
| `Badge` | `Badge.tsx` | Multi-category badge: status (legacy variant), authority, evidence, temporal |
| `EmptyState` | `EmptyState.tsx` | Centered icon + title + description + optional action |
| `ErrorAlert` | `ErrorAlert.tsx` | Role="alert" error banner with optional retry and dismiss |
| `LoadingSpinner` | `LoadingSpinner.tsx` | Spinner (used in settings, project pages) |
| `Skeleton` | `Skeleton.tsx` | Placeholder shimmer |
| `ConfirmDialog` | `ConfirmDialog.tsx` | Modal confirmation (used for delete/revoke actions) |
| `Pagination` | `Pagination.tsx` | Page navigation with ellipsis, aria-label, aria-current |
| `FileInput` | `FileInput.tsx` | File upload input |
| `Toast` / `ToastProvider` / `useToast` | `Toast.tsx` | Toast notification system (imported in settings but not widely used) |
| `Tabs` / `TabPanel` | `Tabs.tsx` | Tab container (used in settings page) |
| `Tooltip` | `Tooltip.tsx` | Hover tooltip (used in sidebar) |
| `Collapsible` | `Collapsible.tsx` | Expand/collapse with aria-expanded |
| `Progress` | `Progress.tsx` | Progress bar (used in ingest upload) |
| `StatCard` | `StatCard.tsx` | Dashboard stat tile (icon + label + value) |
| `useClipboard` | `useClipboard.ts` | Copy-to-clipboard hook with timeout |

### Component Patterns

- All UI components are client components (`'use client'`)
- Consistent CSS variable usage throughout: `bg-[var(--sv-bg-raised)]`, `text-[var(--sv-text-primary)]`, etc.
- Form inputs follow a consistent pattern: `bg-[var(--sv-bg-input)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm focus:outline-none focus:border-[var(--sv-accent)]`
- The `Badge` component has two APIs: legacy `variant="success|warning|danger|info|muted|default"` and new `category="authority|evidence|temporal"` with `value`. Pages mix both.

### Feature Hooks (`src/features/`)

Domain-specific custom hooks (state + API logic bundled):

| Hook | File | Endpoints Used |
|---|---|---|
| `useMemoryList` | `features/memory/useMemory.ts` | `GET /api/v1/memory/` |
| `useMemorySearch` | `features/memory/useMemory.ts` | `POST /api/v1/memory/search` |
| `useCreateMemory` | `features/memory/useMemory.ts` | `POST /api/v1/memory/` |
| `useDeleteMemory` | `features/memory/useMemory.ts` | `DELETE /api/v1/memory/{id}` |
| `useChat` | `features/chat/useChat.ts` | `POST /api/v1/chat/stream` (SSE) |
| `useSources` | `features/ingest/useIngest.ts` | `GET /api/v1/ingest/sources` |
| `useFacts` | `features/ingest/useIngest.ts` | `GET /api/v1/ingest/facts` |
| `useDecisions` | `features/ingest/useIngest.ts` | `GET /api/v1/ingest/decisions` |
| `useUploadFile` | `features/ingest/useIngest.ts` | `POST /api/v1/ingest/upload` (multipart) |
| `useIngestJobs` | `features/ingest/useIngest.ts` | `GET /api/v1/ingest/jobs` |
| `useGraph` | `features/graph/useGraph.ts` | `GET /api/v1/ingest/graph` |
| `useSearch` | `features/search/useSearch.ts` | `POST /api/v1/ingest/search` |
| `useProjects` | `features/projects/useProjects.ts` | CRUD on `/api/v1/projects` |
| `useApiKeys` | `features/apiKeys/useApiKeys.ts` | CRUD on `/api/v1/api-keys` |

### Shared Hooks (`src/hooks/`)

| Hook | File | Purpose |
|---|---|---|
| `useAuth` | `useAuth.tsx` | Auth context: user state, login, register, logout |
| `ThemeProvider` / `useTheme` | `useTheme.tsx` | Dark/light/system theme with localStorage persistence |
| `AppShell` | `AppShell.tsx` | Auth guard + sidebar + main layout wrapper |
| `AuthRedirect` | `AuthRedirect.tsx` | Auth guard (available but AppShell supersedes it) |
| `useSSE` | `useSSE.tsx` | SSE stream reader with AbortController cancellation |

---

## 4. STATE MANAGEMENT

**No global state management library.** The application uses React's built-in state primitives exclusively.

### Local Component State

Every page uses `useState` for local state. Standard pattern:
```tsx
const [items, setItems] = useState<Type[]>([]);
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
```

### URL-Based State

- `useParams()` — used by all project pages for `projectId` (e.g., `src/app/projects/[id]/memory/page.tsx:17`)
- `usePathname()` — used in Sidebar for active link detection (`src/components/Sidebar.tsx:67`) and AppShell for auth page detection (`src/hooks/AppShell.tsx:9`)
- `useRouter()` — programmatic navigation after login/logout/creation

### Context-Based State

Two React contexts:
1. **AuthContext** (`useAuth.tsx:18`) — holds `user`, `loading`, `error` + `login`, `register`, `logout`, `clearError`
2. **ThemeContext** (`useTheme.tsx:13`) — holds `mode` (dark/light/system), `resolved`, `setMode`

### Server State

Data fetching is manual `useEffect` + `apiGet/apiPost` calls. There are no React Query, SWR, or similar libraries. The feature hooks in `src/features/` partially abstract this pattern but are inconsistently adopted — many pages still do inline data fetching.

### Derived State

Some pages derive data client-side:
- `GraphPage` builds a `nodeMap` from edges (`graph/page.tsx:67`)
- `Badge` auto-detects status from children strings (`Badge.tsx:66-68`)

---

## 5. AUTHENTICATION

### Token Storage

Tokens are stored in `localStorage` under key `sv_tokens` as a JSON object:
```json
{ "access_token": "...", "refresh_token": "...", "token_type": "bearer", "expires_in": 1800 }
```

Relevant code: `src/lib/api.ts:31-33` (`storeTokens`), `src/lib/api.ts:3-9` (`getToken`), `src/lib/api.ts:30` (`clearTokens`).

### Token Refresh Flow

`src/lib/api.ts:11-28` — `refreshAccessToken()` reads the refresh token, calls the refresh endpoint, updates localStorage with new access + refresh tokens. The main `request()` function (`api.ts:35-70`) intercepts 401 responses, attempts one automatic refresh, and clears tokens if the refresh also fails or returns 401.

### Login/Register Flow

- **Login**: `POST /api/v1/auth/login` → store tokens → `GET /api/v1/auth/me` → set user state (`useAuth.tsx:37-49`)
- **Register**: `POST /api/v1/auth/register` → store tokens → `GET /api/v1/auth/me` → set user state (`useAuth.tsx:51-63`)
- **Logout**: `POST /api/v1/auth/logout` with refresh_token → clear tokens → reset state (`useAuth.tsx:65-78`)

### Protected Routes

Auth guard is implemented in `AppShell` (`src/hooks/AppShell.tsx:15-22`):
- While loading: render nothing (spinner)
- If no user and not on auth page → redirect to `/auth/login`
- If user on auth page → redirect to `/dashboard`
- Auth pages (`/auth/login`, `/auth/register`, `/`) render without sidebar

Initial auth check on mount: `useAuth.tsx:23-34` calls `GET /api/v1/auth/me` with an 8-second timeout fallback.

### API Call Authentication

Every API request in `request()` (`api.ts:39-45`) attaches `Authorization: Bearer {access_token}`. SSE streams (`api.ts:87-136`, `useSSE.tsx:37-44`) and file uploads (`api.ts:165-167`) also attach the bearer token.

---

## 6. ROUTE → COMPONENT → API MATRIX

### Public Routes

| Route | Page Component | API Calls | Backend Endpoints |
|---|---|---|---|
| `/` | `HomePage` | None (redirects) | — |
| `/auth/login` | `LoginPage` | `POST /api/v1/auth/login`, `GET /api/v1/auth/me` | `/api/v1/auth/login`, `/api/v1/auth/me` |
| `/auth/register` | `RegisterPage` | `POST /api/v1/auth/register`, `GET /api/v1/auth/me` | `/api/v1/auth/register`, `/api/v1/auth/me` |

### Dashboard Route

| Route | Page Component | API Calls | Backend Endpoints |
|---|---|---|---|
| `/dashboard` | `DashboardPage` | `GET /api/v1/workspace`, `GET /api/v1/dashboard/`, `GET /api/v1/projects` | `/api/v1/workspace`, `/api/v1/dashboard/`, `/api/v1/projects` |

### Projects Routes

| Route | Page Component | API Calls | Backend Endpoints |
|---|---|---|---|
| `/projects` | `ProjectsPage` | `GET /api/v1/projects` | `/api/v1/projects` |
| `/projects/[id]` | `ProjectLayout` | `GET /api/v1/projects/{id}`, `PATCH /api/v1/projects/{id}`, `DELETE /api/v1/projects/{id}` | `/api/v1/projects/{id}` |

### Project Sub-Routes

| Route | Page Component | API Calls | Backend Endpoints |
|---|---|---|---|
| `/projects/[id]/chat` | `ChatPage` | `POST /api/v1/sessions/`, `POST /api/v1/chat/stream` (SSE) | `/api/v1/sessions/`, `/api/v1/chat/stream` |
| `/projects/[id]/ingest` | `IngestPage` | `GET /api/v1/ingest/sources`, `POST /api/v1/ingest/upload` (JSON + multipart) | `/api/v1/ingest/sources`, `/api/v1/ingest/upload` |
| `/projects/[id]/sessions` | `SessionsPage` | `GET /api/v1/sessions/` | `/api/v1/sessions/` |
| `/projects/[id]/sessions/[sessionId]` | `SessionDetailPage` | `GET /api/v1/sessions/{id}/history` | `/api/v1/sessions/{id}/history` |
| `/projects/[id]/memory` | `MemoryPage` | `GET /api/v1/memory/` | `/api/v1/memory/` |
| `/projects/[id]/facts` | `FactsPage` | `GET /api/v1/ingest/facts` | `/api/v1/ingest/facts` |
| `/projects/[id]/decisions` | `DecisionsPage` | `GET /api/v1/ingest/decisions` | `/api/v1/ingest/decisions` |
| `/projects/[id]/timeline` | `TimelinePage` | `GET /api/v1/ingest/timeline` | `/api/v1/ingest/timeline` |
| `/projects/[id]/graph` | `GraphPage` | `GET /api/v1/ingest/graph` | `/api/v1/ingest/graph` |
| `/projects/[id]/search` | `SearchPage` | `POST /api/v1/ingest/search` | `/api/v1/ingest/search` |
| `/projects/[id]/provenance` | `ProvenancePage` | `GET /api/v1/provenance/` | `/api/v1/provenance/` |
| `/projects/[id]/settings` | `ProjectSettingsPage` | `useProject`, `useUpdateProject`, `useDeleteProject` (via features hooks) | `/api/v1/projects/{id}` |

### Settings Routes

| Route | Page Component | API Calls | Backend Endpoints |
|---|---|---|---|
| `/settings` | `SettingsPage` | `GET /api/v1/workspace`, `GET /api/v1/workspace/members`, `PATCH /api/v1/workspace`, `POST /api/v1/workspace/members`, `PATCH /api/v1/workspace/members/{id}`, `DELETE /api/v1/workspace/members/{id}`, `GET /api/v1/workspace/members/invitations`, `DELETE /api/v1/workspace/members/invitation/{id}` | `/api/v1/workspace`, `/api/v1/workspace/members` |
| `/settings/profile` | `ProfilePage` | `PATCH /api/v1/auth/me`, `POST /api/v1/auth/change-password` | `/api/v1/auth/me`, `/api/v1/auth/change-password` |
| `/settings/api-keys` | `ApiKeysPage` | `GET /api/v1/api-keys`, `POST /api/v1/api-keys`, `DELETE /api/v1/api-keys/{id}`, `POST /api/v1/api-keys/{id}/rotate` | `/api/v1/api-keys` |
| `/settings/storage` | `StoragePage` | `POST /api/v1/ingest/upload` (via uploadFile) | `/api/v1/ingest/upload` |

---

## 7. KNOWLEDGE VIEWS

### Memory (`/projects/[id]/memory`)

- **Data**: `MemoryItemOut[]` from `GET /api/v1/memory/?project_id=&limit=&offset=&memory_type=`
- **Pagination**: client-side offset (PAGE_SIZE=20), but `total` is set to `data.length` (not from a `total` field) — see GAPS
- **Filter**: memory_type dropdown (semantic, episodic, procedural, working)
- **Display**: Cards showing type badge, authority %, temporal badge, confidence %, tags from `extra_metadata.tags`, content with line-clamp-3
- **Temporal status mapping**: backend stores lowercase (`current`, `superseded`, `archived`), frontend maps to ACTIVE/SUPERSEDED/ARCHIVED (`memory/page.tsx:44`)

### Facts (`/projects/[id]/facts`)

- **Data**: `{ items: FactItem[] }` from `GET /api/v1/ingest/facts?project_id=&limit=&offset=`
- **Display**: Cards showing content, confidence %, authority %, evidence badge (PROVEN vs INGESTED based on `source_id` presence), temporal badge, SPO triple (`subject → predicate → object`) in monospace

### Decisions (`/projects/[id]/decisions`)

- **Data**: `{ items: DecisionItem[] }` from `GET /api/v1/ingest/decisions?project_id=&limit=&offset=`
- **Display**: Cards showing content, confidence % as accent badge, context (italic), temporal badge, authority %, superseded indicator, timestamp

### Timeline (`/projects/[id]/timeline`)

- **Data**: `{ items: TimelineItem[] }` from `GET /api/v1/ingest/timeline?project_id=&limit=100`
- **Display**: Vertical timeline with left border, dot indicators, type icons (decision/fact/memory), temporal badges, chronological ordering. Fixed limit of 100, no pagination.

### Graph (`/projects/[id]/graph`)

- **Data**: `{ nodes: GraphNode[], edges: GraphEdge[] }` from `GET /api/v1/ingest/graph?project_id=`
- **Display**: Two-column layout (2/3 + 1/3). Left: node list with click-to-expand neighbors. Right: detail panel with node properties (collapsible JSON). Node type mapped to Badge category variants. Edges show relationship type, confidence, target node.

### Search (`/projects/[id]/search`)

- **Data**: `POST /api/v1/ingest/search?query=&limit=&memory_type=` returning `{ items: SearchResultItem[], total }`
- **Display**: Search bar with type filter dropdown, results with type badge, temporal badge, score %, content snippet, proper pagination using `total`

### Provenance (`/projects/[id]/provenance`)

- **Data**: `ProvenanceOut[]` from `GET /api/v1/provenance/?project_id=`
- **Display**: Cards showing model, provider badge, latency, tokens, retrieval method, confidence %, first 5 memory_ids as monospace chips

### Chat (`/projects/[id]/chat`)

- **Data**: SSE stream from `POST /api/v1/chat/stream` with `{ message, session_id, project_id }`
- **Display**: Full chat UI with message bubbles, user/assistant avatars, streaming cursor, evidence sources panel ("Why this answer?" modal), abort support. Creates a session first via `POST /api/v1/sessions/`.
- **Two implementations**: `chat/page.tsx` has inline SSE handling (130 lines), while `features/chat/useChat.ts` provides a `useChat` hook with the same logic. The page does NOT use the hook — it duplicates the streaming logic.

---

## 8. RESPONSIVE

### Breakpoints (Tailwind defaults)

- **sm**: 640px — `sm:grid-cols-2`, `sm:grid-cols-3`
- **md**: 768px — sidebar auto-collapse trigger (`Sidebar.tsx:116`: `window.innerWidth < 768`)
- **lg**: 1024px — `lg:grid-cols-3`, `lg:grid-cols-6`
- **xl**: 1280px — not explicitly used

### Responsive Patterns

- **Dashboard stats**: `grid-cols-2 sm:grid-cols-3 lg:grid-cols-6` (`dashboard/page.tsx:115`)
- **Project cards**: `sm:grid-cols-2 lg:grid-cols-3` (`projects/page.tsx:70`)
- **Graph layout**: `grid-cols-1 lg:grid-cols-3` (`graph/page.tsx:105`)
- **Content max-width**: `max-w-4xl` or `max-w-5xl` / `max-w-6xl` with `mx-auto` and `p-6`
- **Sidebar**: collapses to icon-only at `< 768px` width (`Sidebar.tsx:114-123`)
- **Project sidebar**: fixed 192px (`layout.tsx:70`) — no collapse behavior
- **Chat textarea**: `max-h-48` with auto-resize (`chat/page.tsx:310`)

---

## 9. ACCESSIBILITY

### ARIA Usage

| Pattern | Location | Notes |
|---|---|---|
| `role="alert"` | `ErrorAlert.tsx:13` | Error banners |
| `aria-label` | Sidebar nav links, collapse buttons, logout button | Descriptive labels on icon-only buttons |
| `aria-expanded` | `NavGroup.tsx:93`, `Collapsible.tsx:20` | Collapsible sections |
| `aria-current="page"` | `Pagination.tsx:48` | Current pagination page |
| `aria-label="Pagination"` | `Pagination.tsx:25` | Pagination navigation landmark |
| `aria-hidden` | `Collapsible.tsx:30`, `Sidebar.tsx:95` | Decorative elements |
| `aria-label` on password toggle | `profile/page.tsx:130` | Show/hide password button |

### Focus Management

- `:focus-visible` ring: `globals.css:153-158` — 2px solid accent with 2px offset, applied globally
- `*:focus:not(:focus-visible)` removes outline for mouse users
- Input focus: `focus:border-[var(--sv-accent)]` on all form fields

### Skip Navigation

`globals.css:202-230` — `.sr-only` class with focus-reveal behavior. Creates a skip-to-content link that becomes visible on keyboard focus, positioned fixed at top-left with z-index `--sv-z-modal`.

### Reduced Motion

`globals.css:194-200` — `prefers-reduced-motion: reduce` sets all animation durations to 0.01ms and iteration counts to 1.

### Gaps

- No skip-link element in the actual HTML (the `.sr-only` class is defined but no element uses it as a skip link)
- No `lang` attribute changes for internationalization (hardcoded `lang="en"` in `layout.tsx:14`)
- No ARIA live regions for streaming chat updates
- No form validation error associations (`aria-describedby` / `aria-invalid`)

---

## 10. SECURITY

### Token Storage

- **Tokens in localStorage** (`sv_tokens` key) — vulnerable to XSS. No `httpOnly` cookie option.
- **Theme preference in localStorage** (`sv_theme` key) — low risk
- Inline script in `layout.tsx:17-19` reads `sv_theme` to prevent flash — this is a minor XSS vector though the value is constrained to `'light'` or anything else.

### XSS Prevention

- React's default JSX escaping protects against injection in component rendering
- No `dangerouslySetInnerHTML` usage except the theme script in layout
- User-generated content displayed as text nodes (not HTML) throughout
- Monospace blocks render JSON via `JSON.stringify` in `<pre>` tags (`graph/page.tsx:157`) — safe

### Sensitive Data Handling

- **API keys**: displayed once on creation with a "copy now, won't be shown again" warning (`settings/api-keys/page.tsx:59-68`). Masked in list view (`settings/api-keys/page.tsx:114`: `maskKey` adds bullet padding).
- **Passwords**: `type="password"` with show/hide toggle on profile page
- **Session IDs**: displayed as truncated (`slice(0, 8)`) in evidence modal (`chat/page.tsx:357`)
- **Memory IDs**: displayed as truncated in provenance and chat sources

### CSRF

- `credentials: 'include'` is set on all `fetch` calls in `api.ts:45` — cookies are sent cross-origin
- No CSRF token implementation visible
- **GAP**: If the backend uses cookies for session auth in addition to JWT, CSRF protection is missing

### Content Security Policy

- No CSP headers configured in `next.config.js`
- Inline script in layout.tsx would violate a strict CSP without a nonce/hash

---

## 11. FRONTEND/BACKEND GAPS

### Critical Gaps

1. **`bg-[var(--sv-bg-primary)]` undefined variable**: Used on login (`auth/login/page.tsx:24`), register (`auth/register/page.tsx:30`), and home (`page.tsx:14`) pages. The CSS variable `--sv-bg-primary` is never defined in `globals.css`. The intent was clearly `--sv-bg-base`. This results in `inherit` (black/transparent) — visually works in dark mode but is semantically wrong.

2. **Pagination total mismatch**: `MemoryPage` sets `total = data.length` (`memory/page.tsx:33`) rather than using a server-provided total. This makes the pagination component (`Pagination.tsx`) calculate `totalPages` incorrectly — it shows `page + 2` as a heuristic rather than a real total. The `FactsPage` and `DecisionsPage` have the same issue (`facts/page.tsx:30`, `decisions/page.tsx:29`).

3. **Duplicate SSE streaming logic**: The chat page (`chat/page.tsx:79-179`) implements SSE parsing inline (130 lines), while `lib/api.ts:87-136` has a `streamChat()` generator and `features/chat/useChat.ts` has a `useChat` hook. The page uses none of these — it duplicates the full streaming implementation. This creates a maintenance burden and the three implementations could diverge.

4. **Token in URL query params for search**: `SearchPage` passes `project_id` in the URL search params but the endpoint is `/api/v1/ingest/search?query=&limit=&memory_type=` — `project_id` is not sent in the URL (`search/page.tsx:38`). The backend may expect it from the authenticated user's context, or this is a gap.

### Moderate Gaps

5. **Storage page uses workspace_id as project_id**: `settings/storage/page.tsx:34-39` fetches `/api/v1/auth/me` and uses `workspace_id` as `project_id` for uploads. The ingest endpoint expects a project_id, not workspace_id. This is a temporary workaround with a comment acknowledging the issue (`storage/page.tsx:31-32`).

6. **No error boundary**: No React Error Boundary implementation. Unhandled errors in client components will unmount the tree.

7. **Inconsistent pagination patterns**: Some pages use offset-based pagination (memory, facts, decisions, sessions), SearchPage uses client-side slice of a single result set (`search/page.tsx:48`), and TimelinePage has no pagination at all (fixed limit=100).

8. **`useAuth` hook reads tokens but `useSSE` and chat page also read tokens directly**: Token access is centralized in `lib/api.ts` exports (`getToken`, `storeTokens`, etc.), but `useSSE.tsx:6` imports `getToken` directly, and `chat/page.tsx:59` reads it inline. This works but means `useSSE` and the chat page are coupled to the localStorage key format.

9. **No loading skeleton for most pages**: Most pages show a text "Loading…" rather than the `Skeleton` component. The `Skeleton` component exists in `components/ui/` but is only used in `settings/api-keys/page.tsx:104` and `features/apiKeys/useApiKeys.ts`.

10. **`confirm()` and `alert()` usage**: Project deletion uses `window.confirm` (`projects/[id]/layout.tsx:49`) and `alert()` (`layout.tsx:50`). This blocks the thread with native dialogs. Other pages use the `ConfirmDialog` component correctly.

### Minor Gaps

11. **`AuthRedirect` hook unused**: `src/hooks/AuthRedirect.tsx` exists and exports an `AuthRedirect` component, but `AppShell.tsx` supersedes it. The redirect logic is duplicated.

12. **Memory page pagination heuristic**: `Pagination page={page} totalPages={page + 2}` (`memory/page.tsx:118`) is a rough heuristic that may show incorrect total page counts.

13. **`sv_bg-primary` vs `sv-bg-base` inconsistency**: The CSS uses kebab-case (`--sv-bg-base`) while some components reference camelCase-style names. Only `--sv-bg-primary` is problematic (undefined).

14. **Graph page node type color mapping not aligned with Badge**: `graph/page.tsx:76-83` maps node types to Badge variants (info, accent, warning, success, default) but the `Badge` component's variant system doesn't have an `accent` variant — it has `default, success, warning, danger, info, muted`. The `accent` variant falls through to `default`.

15. **Type definition duplication**: `ApiKeyOut` is defined in both `src/types/api.ts:156-163` and `src/features/apiKeys/useApiKeys.ts:6-14` with slightly different shapes (the feature version adds `raw_key?`). The `src/types/api.ts` version is the canonical one used elsewhere.

---

## Summary of File Paths

| Purpose | Path |
|---|---|
| Root layout | `frontend/src/app/layout.tsx` |
| Design tokens | `frontend/src/app/globals.css` |
| Tailwind config | `frontend/tailwind.config.js` |
| Next.js config | `frontend/next.config.js` |
| TypeScript config | `frontend/tsconfig.json` |
| API client | `frontend/src/lib/api.ts` |
| Error formatting | `frontend/src/lib/errors.ts` |
| Type definitions | `frontend/src/types/api.ts` |
| Auth context | `frontend/src/hooks/useAuth.tsx` |
| Theme context | `frontend/src/hooks/useTheme.tsx` |
| App shell | `frontend/src/hooks/AppShell.tsx` |
| SSE hook | `frontend/src/hooks/useSSE.tsx` |
| Auth redirect (unused) | `frontend/src/hooks/AuthRedirect.tsx` |
| Sidebar | `frontend/src/components/Sidebar.tsx` |
| UI primitives | `frontend/src/components/ui/` (17 components) |
| Feature hooks | `frontend/src/features/` (7 domain hooksets) |
| Package manifest | `frontend/package.json` |
