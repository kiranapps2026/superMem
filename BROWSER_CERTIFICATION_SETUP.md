# Browser Certification Setup

## Environment

| Component       | Value                                     |
|-----------------|-------------------------------------------|
| Frontend dir    | `C:\Users\Administrator\Documents\SwarmVaultwebapp\frontend` |
| Backend dir     | `C:\Users\Administrator\Documents\SwarmVaultwebapp` |
| Frontend URL    | `http://localhost:3000` (Next.js dev)     |
| Backend URL     | `http://localhost:8000` (FastAPI + Uvicorn) |
| Frontend env    | `.env.local` → `NEXT_PUBLIC_API_URL=http://localhost:8000` |
| Browser         | Playwright Chromium (Chrome for Testing 153) |
| Node version    | via `npx` (system Node.js)                |
| Playwright      | v1.62.1                                   |

## Startup Commands

```bash
# Backend (from C:\Users\Administrator\Documents\SwarmVaultwebapp)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (from C:\Users\Administrator\Documents\SwarmVaultwebapp\frontend)
npm run dev
```

## Playwright Config

- File: `frontend/playwright.config.ts`
- Base URL: `http://localhost:3000`
- Reporter: `list`
- Test dir: `frontend/e2e/`
- Browser: `chromium`

## Authentication

- JWT access/refresh tokens stored in `localStorage` key `sv_tokens`
- AuthRedirect component wraps protected routes → redirects to `/auth/login`
- Golden-journey tests use `page.request` (Playwright API context with cookies) for auth flow

## Capabilities

| Capability           | Tool                    |
|----------------------|-------------------------|
| Navigation           | `page.goto()`           |
| Clicking             | `page.locator().click()`|
| Typing               | `page.locator().fill()` |
| Screenshot           | `page.screenshot()`     |
| Network inspection   | `page.route()` / `page.request` |
| Console inspection   | `page.on('console')`    |
| Viewport changes     | `page.setViewportSize()`|

## Known Constraints

- Playwright must run against live servers (not static exports)
- Backend must be running on port 8000
- Frontend must be running on port 3000
- Database must be initialized (Alembic migrations applied)
- No seed data in current DB (golden-journey tests create their own via API)
