# SwarmVault WebApp — Frontend Architecture Reference
**Version:** 1.0.0
**Date:** 2026-09-01
**Evidence base:** Repository inspection (commit 902d85e), frontend/src/ tree

---

## 1. Technology Stack

| Component | Technology |
|-----------|-----------|
| Framework | Next.js 15 (App Router) |
| Language | TypeScript (strict mode implied by @/ path aliases) |
| Styling | Tailwind CSS |
| State Management | Zustand |
| API Client | Axios |
| Authentication | JWT Bearer (access + refresh token) |
| Data Fetching | Axios + React Query pattern (NOT verified — direct fetches observed) |

---

## 2. Directory Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # Root layout, auth state provider
│   │   ├── page.tsx                # Landing/home page
│   │   ├── globals.css             # Tailwind directives
│   │   ├── api/                    # API utility layer
│   │   ├── auth/                   # Auth pages
│   │   │   ├── login/              # Login page
│   │   │   │   └── page.tsx
│   │   │   └── register/           # Register page
│   │   │       └── page.tsx
│   │   ├── dashboard/              # Dashboard page
│   │   │   └── page.tsx
│   │   ├── projects/               # Project management
│   │   │   ├── page.tsx            # Project list
│   │   │   ├── [id]/               # Project detail
│   │   │   │   └── page.tsx
│   │   │   └── [id]/               # (potential sub-routes)
│   │   └── settings/               # Settings page
│   │       └── page.tsx
│   └── (stores, lib, components if present — NOT VERIFIED IN REPO)
├── package.json
├── tailwind.config.ts (or .js)
├── next.config.ts (or .js)
├── tsconfig.json
└── .env.local (NOT READ — see never-read rules)
```

---

## 3. Page Routes

| Route | Purpose | Auth Required |
|-------|---------|---------------|
| `/` | Landing/home page | No |
| `/auth/login` | Login form | No |
| `/auth/register` | Registration form | No |
| `/dashboard` | Workspace overview | Yes |
| `/projects` | Project list | Yes |
| `/projects/[id]` | Project detail | Yes |
| `/settings` | User/workspace settings | Yes |

---

## 4. Authentication Flow (Frontend)

```
Landing Page (/)
 │  • "Get Started" → /auth/register
 │  • "Sign In" → /auth/login
 │
 ▼
Register (/auth/register)
 │  • Form: email, name, password, workspace name
 │  • POST /auth/register
 │  • Store access_token + refresh_token
 │  • Redirect → /dashboard
 │
 Login (/auth/login)
 │  • Form: email, password
 │  • POST /auth/login
 │  • Store access_token + refresh_token
 │  • Redirect → /dashboard
 │
 Authenticated
 │  • access_token in Authorization header
 │  • refresh_token in memory/store (NOT confirmed)
 │  • Redirect → /dashboard if unauthenticated
```

**Evidence:** `auth/register/page.tsx`, `auth/login/page.tsx`

---

## 5. Known Features (Frontend)

Based on available pages:
1. **Authentication** — Registration and login with email/password
2. **Dashboard** — Overview statistics (total memories, sources, sessions, etc.)
3. **Projects** — List and view project details
4. **Settings** — User/workspace configuration

**Features NOT ESTABLISHED IN AVAILABLE SOURCE:**
- Chat UI (chat endpoint exists in backend but no chat page found in frontend/src/app/)
- Memory creation/editing UI (memory API exists but no dedicated page found)
- Ingestion upload UI (ingest API exists but no upload page found)
- Knowledge graph visualization (graph API exists but no visualization page found)
- Provenance explorer (provenance API exists but no explorer page found)
