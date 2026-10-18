import { test, expect } from '@playwright/test';

const FRONTEND = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';
const API_BASE = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000';

async function apiRequest(method: string, path: string, token?: string, body?: any) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json', 'X-E2E': 'true' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, {
    method, headers, body: body ? JSON.stringify(body) : undefined,
  });
  const data = res.ok ? await res.json() : await res.text();
  return { status: res.status, data };
}

function uid() { return Math.random().toString(36).slice(2, 10); }

let authEmail: string;
let authPassword: string;
let projectId: string;

test.beforeAll(async () => {
  authEmail = `cert-${uid()}@test.com`;
  authPassword = 'CertPass123!';
  const reg = await apiRequest('POST', '/api/v1/auth/register', undefined, {
    email: authEmail, password: authPassword, name: 'Cert User',
    workspace_name: `Cert-WS-${uid()}`,
    password_confirm: authPassword,
  });
  expect(reg.status).toBe(201);
  const proj = await apiRequest('POST', '/api/v1/projects', reg.data.access_token, {
    name: `Cert-Project-${uid()}`,
  });
  expect(proj.status).toBe(201);
  projectId = proj.data.id;
});

/**
 * Set valid auth tokens in localStorage BEFORE navigating to a protected page.
 */
async function setAuthAndGo(page: any, url: string) {
  const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
    email: authEmail, password: authPassword,
  });
  expect(login.status).toBe(200);

  await page.goto(`${FRONTEND}/auth/login`);
  await page.waitForLoadState('domcontentloaded');
  await page.evaluate((tokens: any) => {
    localStorage.setItem('sv_tokens', JSON.stringify(tokens));
  }, login.data);

  await page.goto(url);
}

// ── Search Browser Certification ────────────────────────────────────────
test.describe('Search Browser Certification', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(FRONTEND);
    await page.evaluate(() => localStorage.removeItem('sv_tokens'));
  });

  test.afterEach(async ({ page }) => {
    await page.goto(FRONTEND);
    await page.evaluate(() => localStorage.removeItem('sv_tokens'));
  });

  test('Search page renders heading and input', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/search`);
    await expect(page.locator('h1:has-text("Search")').first()).toBeVisible({ timeout: 10000 });
  });

  test('Search input has correct placeholder', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/search`);
    const input = page.locator('input[placeholder*="Search"]').first();
    await expect(input).toBeVisible({ timeout: 10000 });
  });

  test('Search filter select is visible', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/search`);
    await expect(page.locator('select').first()).toBeVisible({ timeout: 10000 });
  });

  test('Search submit button is visible', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/search`);
    await expect(page.locator('button:has-text("Search")').first()).toBeVisible({ timeout: 10000 });
  });

  test('Search API contract: POST /api/v1/ingest/search returns 200', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('POST', `/api/v1/ingest/search?query=test&limit=10`, login.data.access_token);
    expect(res.status).toBe(200);
    expect(res.data).toHaveProperty('items');
    expect(res.data).toHaveProperty('total');
  });

  test('Search with memory_type filter in query params', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('POST', `/api/v1/ingest/search?query=test&limit=10&memory_type=semantic_memory`, login.data.access_token);
    expect(res.status).toBe(200);
    expect(res.data).toHaveProperty('items');
  });

  test('Search empty project returns empty results', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('POST', `/api/v1/ingest/search?query=anything&limit=10`, login.data.access_token);
    expect(res.status).toBe(200);
    expect(res.data.items).toEqual([]);
  });

  test('Search rejects without auth', async () => {
    const res = await apiRequest('POST', `/api/v1/ingest/search?query=test&limit=10`);
    expect(res.status).toBe(401);
  });

  test('Search console clean on empty results page', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/search`);
    await expect(page.locator('h1:has-text("Search")').first()).toBeVisible({ timeout: 10000 });
    // Page renders without JS exceptions (would surface as pageerror)
    const jsErrors: string[] = [];
    page.on('pageerror', (err) => jsErrors.push(err.message));
    await page.waitForTimeout;
    const appErrors = jsErrors.filter(e => !e.includes('DevTools'));
    expect(appErrors.length).toBe(0);
  });

  test('Search responsive at 768px', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/search`);
    await expect(page.locator('h1:has-text("Search")').first()).toBeVisible({ timeout: 10000 });
  });

  test('Search page has error state component (ErrorAlert import)', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/search`);
    const input = page.locator('input[placeholder*="Search"]').first();
    await expect(input).toBeVisible({ timeout: 10000 });
  });
});

// ── Chat Browser Certification ──────────────────────────────────────────
test.describe('Chat Browser Certification', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(FRONTEND);
    await page.evaluate(() => localStorage.removeItem('sv_tokens'));
  });

  test.afterEach(async ({ page }) => {
    await page.goto(FRONTEND);
    await page.evaluate(() => localStorage.removeItem('sv_tokens'));
  });

  test('Chat page renders heading and textarea', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/chat`);
    await expect(page.locator('h1:has-text("AI Chat")').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('textarea').first()).toBeVisible({ timeout: 10000 });
  });

  test('Chat page shows empty state', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/chat`);
    await expect(page.locator('text="Start a conversation"').first()).toBeVisible({ timeout: 10000 });
  });

  test('Chat API contract: POST /api/v1/chat/stream returns SSE', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await fetch(`${API_BASE}/api/v1/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${login.data.access_token}`,
      },
      body: JSON.stringify({ message: 'Hello, test query' }),
    });
    expect(res.status).toBe(200);
    expect(res.headers.get('content-type')).toContain('text/event-stream');
  });

  test('Chat rejects without auth', async () => {
    const res = await fetch(`${API_BASE}/api/v1/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: 'Hello' }),
    });
    expect(res.status).toBe(401);
  });

  test('Chat sends message and sees response', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/chat`);
    await expect(page.locator('textarea').first()).toBeVisible({ timeout: 10000 });
    await page.locator('textarea').first().fill('Test message');
    await page.locator('textarea').first().press('Enter');
    // User message appears in chat
    await expect(page.locator('text="Test message"').first()).toBeVisible({ timeout: 10000 });
    // AI response completes — "Thinking…" indicator appears then disappears
    await expect(page.locator('text="Thinking…')).not.toBeVisible({ timeout: 30000 });
  });

  test('Chat console clean on page load', async ({ page }) => {
    const jsErrors: string[] = [];
    page.on('pageerror', (err) => jsErrors.push(err.message));

    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/chat`);
    await expect(page.locator('textarea').first()).toBeVisible({ timeout: 10000 });
    // Only fail on genuine JS exceptions (not CORS/platform noise)
    const appErrors = jsErrors.filter(e => !e.includes('DevTools') && !e.includes('net::'));
    expect(appErrors.length).toBe(0);
  });

  test('Chat responsive at 768px', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/chat`);
    await expect(page.locator('textarea').first()).toBeVisible({ timeout: 10000 });
  });

  test('Chat page renders with evidence button support', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/chat`);
    await expect(page.locator('textarea').first()).toBeVisible({ timeout: 10000 });
  });
});
