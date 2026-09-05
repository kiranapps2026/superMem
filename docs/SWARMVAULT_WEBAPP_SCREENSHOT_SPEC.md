# SWARMVAULT WEBAPP SCREENSHOT SPECIFICATION

**Version:** 1.0.0
**Date:** 2026-09-05
**Application Version:** 0.1.0
**Repository SHA:** d970d6b (master)
**Documentation Status:** COMPLETE — All 28 screenshots captured in `docs/screenshots/`
**Author:** SwarmVault Documentation Authority

---

## Overview

This document specifies exactly which screenshots to capture for the SwarmVault WebApp documentation. Each entry describes:
- **Route** — The page URL
- **State** — The specific state to capture (default, empty, filled, loading, error)
- **Key Elements** — Visual elements to verify
- **Caption** — Suggested figure caption

**Viewport:** Desktop (1440x900 minimum)
**Theme:** Dark mode (default)
**Browser:** Chrome 120+

---

## Screen 1: Landing Page (Unauthenticated)

| Property | Value |
|----------|-------|
| **Route** | `/` (or `/auth/login` after redirect) |
| **State** | Default — no user session |
| **Key Elements** | SwarmVault logo/title, "Sign in to SwarmVault" heading, email/password fields, "Sign in" button, "Create one" link, testimonial/quotes, footer with "Built with Claude Code" |
| **Caption** | Figure 1: SwarmVault landing page — sign in screen |

### What to verify
- Brand name "SwarmVault" visible
- Sign in heading matches "Sign in to SwarmVault"
- Email field labeled "Email"
- Password field labeled "Password"
- "Sign in" button styled with primary accent color
- "Create one" link at bottom
- Testimonial quotes section with quotes from users
- Footer badge "Built with Claude Code"
- Background gradient (dark theme)

---

## Screen 2: Registration Page

| Property | Value |
|----------|-------|
| **Route** | `/auth/register` |
| **State** | Default form — empty fields |
| **Key Elements** | "Sign in to SwarmVault" heading, Full name, Email, Workspace name, Password, Confirm password fields, "Create account" button, "Already have an account?" link |
| **Caption** | Figure 2: Registration page — new account creation |

### What to verify
- Full name field (optional, helper text: "Optional")
- Email field (required)
- Workspace name field (required)
- Password field (required, min 8 characters)
- Confirm password field (required, must match)
- "Create account" button
- Link back to login

---

## Screen 3: Dashboard (Empty State)

| Property | Value |
|----------|-------|
| **Route** | `/dashboard` |
| **State** | Authenticated, no projects created |
| **Key Elements** | Sidebar (collapsed/expanded), workspace name, "0 projects", "New Project" button, empty state with FolderOpen icon and "No projects yet." text |
| **Caption** | Figure 3: Dashboard — empty state before any projects |

### What to verify
- Sidebar visible with SwarmVault brand
- Dashboard active in sidebar navigation
- Workspace name displayed
- "New Project" button (primary action)
- Empty state illustration (FolderOpen icon)
- "No projects yet." message

---

## Screen 4: Dashboard (With Projects)

| Property | Value |
|----------|-------|
| **Route** | `/dashboard` |
| **State** | Authenticated, 2-3 projects exist |
| **Key Elements** | Project cards in grid, each with name, description, creation date |
| **Caption** | Figure 4: Dashboard — populated with projects |

### What to verify
- Project cards in responsive grid
- Card shows project name (bold)
- Card shows description (2-line truncation)
- Card shows "Click to open" link

---

## Screen 5: Projects Page

| Property | Value |
|----------|-------|
| **Route** | `/projects` |
| **State** | Authenticated, projects exist |
| **Key Elements** | "Projects" heading, "No projects yet. Create one from the Dashboard." or project card grid |
| **Caption** | Figure 5: Projects list page |

### What to verify
- "Projects" heading with count
- Consistent card styling with Dashboard
- Empty state message guides to Dashboard

---

## Screen 6: Sidebar (Expanded)

| Property | Value |
|----------|-------|
| **Route** | Any authenticated page |
| **State** | Sidebar expanded (224px) |
| **Key Elements** | SwarmVault brand, collapse button (hamburger), top nav items (Dashboard, Projects, Settings), project nav items (when on project), bottom section (Settings, Logout) |
| **Caption** | Figure 6: Sidebar — expanded navigation |

### What to verify
- Brand name "SwarmVault" with sparkle icon
- Hamburger menu button (collapse)
- Top section: Dashboard, Projects, Settings & Members
- Project section (when context is active): Chat, Ingest, Sessions, Memory, Facts, Decisions, Timeline, Search, Graph
- Bottom: Settings, Logout
- Active page highlighted in navigation

---

## Screen 7: Sidebar (Collapsed)

| Property | Value |
|----------|-------|
| **Route** | Any authenticated page |
| **State** | Sidebar collapsed (56px) |
| **Key Elements** | Icons only, brand icon, nav icons, expand button |
| **Caption** | Figure 7: Sidebar — collapsed (icon-only mode) |

### What to verify
- Sidebar shrinks to ~56px
- Icons only (no text labels)
- Hover shows tooltips
- Expand button to restore

---

## Screen 8: Chat Page (Empty Session)

| Property | Value |
|----------|-------|
| **Route** | `/projects/{id}/chat` |
| **State** | Authenticated, no messages in session |
| **Key Elements** | "AI Chat" header, "Grounded in project memory" subtitle, back button, empty message area, "Start a conversation" prompt, composer textarea + Send button |
| **Caption** | Figure 8: Chat page — empty session |

### What to verify
- Header: "AI Chat" title
- Subtitle: "Grounded in project memory"
- Back button (arrow-left icon)
- Empty state in message area
- Composer: textarea + Send button
- Evidence button ("Why this answer?") present

---

## Screen 9: Chat Page (With Conversation)

| Property | Value |
|----------|-------|
| **Route** | `/projects/{id}/chat` |
| **State** | Authenticated, conversation with user and assistant messages |
| **Key Elements** | User message (right, accent color), Assistant message (left, secondary), Sources panel (if applicable), Evidence button, Composer |
| **Caption** | Figure 9: Chat page — active conversation with memory-grounded response |

### What to verify
- User messages: right-aligned, accent background
- Assistant messages: left-aligned, secondary background
- Sources panel shows retrieved memories
- "Why this answer?" button visible
- Streaming response animation (if actively generating)

---

## Screen 10: Ingest Page (Empty State)

| Property | Value |
|----------|-------|
| **Route** | `/projects/{id}/ingest` |
| **State** | Authenticated, no sources uploaded |
| **Key Elements** | "Ingest" header, source type selector, title input, textarea, file picker, "Upload & Process" button |
| **Caption** | Figure 10: Ingest page — empty state with upload form |

### What to verify
- Source type dropdown (7 options)
- Title input field
- Content textarea
- File picker button
- "Upload & Process" button

---

## Screen 11: Ingest Page (With Sources)

| Property | Value |
|----------|-------|
| **Route** | `/projects/{id}/ingest` |
| **State** | Authenticated, 1+ sources with different statuses |
| **Key Elements** | Source cards/table showing title, source type, status, creation date, file size; processing spinner, completed badges, error badges |
| **Caption** | Figure 11: Ingest page — sources with mixed processing states |

### What to verify
- Source cards/table rows
- Status badges: Queued (FileText), Processing (Loader animation), Completed (CheckCircle), Failed (XCircle)
- Source type label
- File size and creation date
- Progress indicators for processing items

---

## Screen 12: Memory Page

| Property | Value |
|----------|-------|
| **Route** | `/projects/{id}/memory` |
| **State** | Authenticated, memory items exist |
| **Key Elements** | "Memory" header, item count, filter input, memory cards with type, content, temporal status badge, confidence score, tags |
| **Caption** | Figure 12: Memory page — extracted knowledge items |

### What to verify
- "Memory" header with item count ("{N} memory items")
- Filter input (placeholder: "Filter by type...")
- Memory type badges (semantic_memory, episodic_memory, etc.)
- Content text (truncated)
- Temporal status badges (current: green, superseded: yellow)
- Confidence score (percentage)
- Tag badges
- Empty state: "No memory items yet. Ingest sessions to populate memory."

---

## Screen 13: Search Page

| Property | Value |
|----------|-------|
| **Route** | `/projects/{id}/search` |
| **State** | Authenticated, search results displayed |
| **Key Elements** | "Search" header, search input, results cards with type badge, content snippet, relevance score, temporal status, creation date |
| **Caption** | Figure 13: Search page — semantic search results |

### What to verify
- Search input (Enter-to-search)
- Results display as cards
- Type badges (memory, fact, decision)
- Content snippet (3-line truncation)
- Relevance score (0-100%)
- Temporal status
- Creation date
- Empty state: "No results found"

---

## Screen 14: Knowledge Graph Page

| Property | Value |
|----------|-------|
| **Route** | `/projects/{id}/graph` |
| **State** | Authenticated, graph with nodes and edges |
| **Key Elements** | Graph canvas with nodes (circles) and edges (lines), node type labels, detail panel (when node selected), "Include historical" toggle |
| **Caption** | Figure 14: Knowledge Graph — entity relationship visualization |

### What to verify
- Graph canvas rendering
- Nodes as circles with labels
- Edges connecting related nodes
- Click interaction on nodes
- Detail panel showing node properties
- "Include historical" toggle switch

---

## Screen 15: Timeline Page

| Property | Value |
|----------|-------|
| **Route** | `/projects/{id}/timeline` |
| **State** | Authenticated, timeline events exist |
| **Key Elements** | "Timeline" header, vertical timeline with border, dot markers, event type badges, timestamps, content previews |
| **Caption** | Figure 15: Timeline — chronological event view |

### What to verify
- Vertical timeline with left border
- Dot markers at each event
- Event type badges (memory/fact/decision)
- Temporal status (current/superseded)
- Timestamps
- Content preview text
- Empty state: "No events yet."

---

## Screen 16: Facts Page

| Property | Value |
|----------|-------|
| **Route** | `/projects/{id}/facts` |
| **State** | Authenticated, facts exist |
| **Key Elements** | "Facts" header, "current facts" / "superseded facts" tabs, fact cards with statement, subject, predicate, confidence score (color-coded), status badge |
| **Caption** | Figure 16: Facts page — extracted factual statements |

### What to verify
- Tabs: "current facts" and "superseded facts"
- Fact cards showing:
  - Statement text
  - Subject/predicate if available
  - Confidence score (color-coded: green ≥80%, yellow ≥50%, red <50%)
  - Status and authority badges
- Empty state: "No facts yet."

---

## Screen 17: Decisions Page

| Property | Value |
|----------|-------|
| **Route** | `/projects/{id}/decisions` |
| **State** | Authenticated, decisions exist |
| **Key Elements** | "Decisions" header, tabs for current/superseded, decision cards with content, confidence score (color-coded), temporal status, tags |
| **Caption** | Figure 17: Decisions page — extracted decision records |

### What to verify
- Tabs: "current decisions" and "superseded decisions"
- Decision cards:
  - Decision text
  - Confidence score (color-coded)
  - Temporal status badge
  - Tags if available
- Empty state: "No decisions yet."

---

## Screen 18: Sessions Page

| Property | Value |
|----------|-------|
| **Route** | `/projects/{id}/sessions` |
| **State** | Authenticated, sessions exist |
| **Key Elements** | "Sessions" header, session list cards with title, source type, creation date, chevron navigation |
| **Caption** | Figure 18: Sessions page — conversation history |

### What to verify
- Session cards with:
  - Title (or "Untitled session")
  - Source type badge
  - Creation date
  - Chevron to navigate
- Empty state: "No sessions yet."

---

## Screen 19: Session Detail Page

| Property | Value |
|----------|-------|
| **Route** | `/projects/{id}/sessions/{sessionId}` |
| **State** | Authenticated, session with messages |
| **Key Elements** | Session title, message count, back link, message bubbles (user/assistant alternating), timestamps |
| **Caption** | Figure 19: Session detail — individual conversation |

### What to verify
- Session title displayed
- Message count indicator
- Back button/link to sessions list
- Message bubbles (user: right/accent, assistant: left/secondary)
- Message ordering (chronological)
- Empty state: "No messages in this session."

---

## Screen 20: Provenance Page

| Property | Value |
|----------|-------|
| **Route** | `/projects/{id}/provenance` |
| **State** | Authenticated, provenance records exist |
| **Key Elements** | "Provenance" header, provenance cards/table with model, provider, timestamp, latency, token usage, retrieval method, confidence score, memory source IDs |
| **Caption** | Figure 20: Provenance page — AI answer audit trail |

### What to verify
- Provenance records displayed as table or cards
- Fields: model, provider, timestamp, latency (ms), token usage, retrieval method, confidence score, memory source IDs

---

## Screen 21: API Keys Page

| Property | Value |
|----------|-------|
| **Route** | `/settings/api-keys` |
| **State** | Authenticated, admin role |
| **Key Elements** | "API Keys" heading, Create button, key list with prefix (masked), createdAt date, Revoke button, "Last 4" display (masked) |
| **Caption** | Figure 21: API Keys — programmatic access management |

### What to verify
- "API Keys" header
- "Create API key" button
- Key list showing:
  - Key prefix (first 8 chars) + "......" (masked)
  - "Last 4" characters shown
  - Created date
  - Revoke button
- Empty state: "No API keys yet."

---

## Screen 22: Storage Page

| Property | Value |
|----------|-------|
| **Route** | `/settings/storage` |
| **State** | Authenticated, files uploaded |
| **Key Elements** | "Storage" header, file list with name, size, upload date, status badge (uploading/ingested/failed), progress bar |
| **Caption** | Figure 22: Storage — uploaded files management |

### What to verify
- "Storage" header
- File table/list with:
  - File name
  - File size (formatted)
  - Upload date
  - Status badge
- Empty state

---

## Screen 23: Settings — Profile

| Property | Value |
|----------|-------|
| **Route** | `/settings` (Profile tab) |
| **State** | Authenticated, viewing own profile |
| **Key Elements** | Profile section (email, name, role — read-only), Password change form (current password, new password, confirm, submit) |
| **Caption** | Figure 23: Settings — Profile tab |

### What to verify
- Email (read-only)
- Name (read-only)
- Role (read-only)
- Password change form with:
  - Current password
  - New password (min 8 chars)
  - Confirm new password
  - "Change password" button

---

## Screen 24: Settings — Workspace Members

| Property | Value |
|----------|-------|
| **Route** | `/settings` (Members tab) |
| **State** | Authenticated, 2+ members |
| **Key Elements** | Invite form (email + role + "Invite" button), member list with avatars, names, emails, role badges, role editor (admin+), remove button |
| **Caption** | Figure 24: Settings — Workspace Members |

### What to verify
- Invite section: email input, role dropdown, "Invite" button
- Member cards with:
  - Avatar circle (initial letter)
  - Name and email
  - Role badge
  - Role dropdown (admin+)
  - Remove button (admin+, not owner)

---

## Screen 25: Settings — Invitations

| Property | Value |
|----------|-------|
| **Route** | `/settings` (Invitations tab) |
| **State** | Authenticated, pending invitations exist |
| **Key Elements** | Pending invitations table with email, role, state badge, creation date, expiration date, Revoke button |
| **Caption** | Figure 25: Settings — Invitations management |

### What to verify
- Invitation list with:
  - Email address
  - Role
  - State (pending/accepted/declined)
  - Created date
  - Expiration date
  - Revoke button (pending only)

---

## Screen 26: Project Settings

| Property | Value |
|----------|-------|
| **Route** | `/projects/{id}/settings` |
| **State** | Authenticated, viewing project |
| **Key Elements** | Tab navigation (General, Members, Danger Zone), project name/description (editable), "Save changes" button, member list, "Delete this project" with confirmation dialog |
| **Caption** | Figure 26: Project Settings — general, members, danger zone |

### What to verify
- Three tabs: General, Members, Danger Zone
- General: name/description form
- Members: workspace member list (read-only)
- Danger Zone: delete button, confirmation dialog

---

## Screen 27: Evidence Modal

| Property | Value |
|----------|-------|
| **Route** | `/projects/{id}/chat` |
| **State** | Chat with messages, evidence modal open |
| **Key Elements** | Modal overlay, answer text, evidence trail list with source memory IDs, scores, content snippets, close button |
| **Caption** | Figure 27: Evidence modal — "Why this answer?" provenance details |

### What to verify
- Modal overlay (dark backdrop)
- Answer text displayed
- Evidence sources listed with:
  - Memory ID
  - Relevance score
  - Content snippet
- Close/dismiss button

---

## Screen 28: Error States

| Property | Value |
|----------|-------|
| **Route** | Various |
| **State** | Error conditions |
| **Key Elements** | Error messages from API, inline error displays, loading spinners, empty states |
| **Caption** | Figure 28: Error states — API error display |

### What to verify
- Error messages styled with red/orange accent
- Inline error banners
- Loading spinner component
- ErrorAlert component in various states

---

## Screenshot Checklist

| # | Screen | Status | Captured | File |
|---|--------|--------|----------|------|
| 1 | Landing Page | Done | ✅ | `01-landing.png` |
| 2 | Registration | Done | ✅ | `02-register.png` |
| 3 | Dashboard Empty | Done | ✅ | `03-dashboard-empty.png` |
| 4 | Dashboard Populated | Done | ✅ | `04-dashboard-with-projects.png` |
| 5 | Projects List | Done | ✅ | `05-projects-page.png` |
| 6 | Sidebar Expanded | Done | ✅ | `06-sidebar-expanded.png` |
| 7 | Sidebar Collapsed | Done | ✅ | `07-sidebar-collapsed.png` |
| 8 | Chat Empty | Done | ✅ | `08-chat-empty.png` |
| 9 | Chat Active | Done | ✅ | `09-chat-with-messages.png` |
| 10 | Ingest Empty | Done | ✅ | `10-ingest-empty.png` |
| 11 | Ingest Populated | Done | ✅ | `11-ingest-with-sources.png` |
| 12 | Memory | Done | ✅ | `12-memory-page.png` |
| 13 | Search | Done | ✅ | `13-search-page.png` |
| 14 | Graph | Done | ✅ | `14-graph-page.png` |
| 15 | Timeline | Done | ✅ | `15-timeline-page.png` |
| 16 | Facts | Done | ✅ | `16-facts-page.png` |
| 17 | Decisions | Done | ✅ | `17-decisions-page.png` |
| 18 | Sessions | Done | ✅ | `18-sessions-page.png` |
| 19 | Session Detail | Done | ✅ | `19-session-detail.png` |
| 20 | Provenance | Done | ✅ | `20-provenance-page.png` |
| 21 | API Keys | Done | ✅ | `21-api-keys.png` |
| 22 | Storage | Done | ✅ | `22-storage.png` |
| 23 | Settings Profile | Done | ✅ | `23-settings-profile.png` |
| 24 | Settings Members | Done | ✅ | `24-settings-members.png` |
| 25 | Settings Invitations | Done | ✅ | `25-settings-invitations.png` |
| 26 | Project Settings | Done | ✅ | `26-project-settings.png` |
| 27 | Evidence Modal | Done | ✅ | `27-evidence-modal.png` |
| 28 | Error States | Done | ✅ | `28-error-states.png` |

**Total: 28/28 screenshots captured.**

All screenshots captured on 2026-09-05 using Playwright (Chromium headless) at 1440x900 viewport.
