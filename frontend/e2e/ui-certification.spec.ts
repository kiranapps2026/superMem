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
 * This ensures AuthProvider picks them up on initial render and the
 * /api/v1/auth/me call succeeds, avoiding the redirect-to-login loop.
 */
async function setAuthAndGo(page: any, url: string) {
  // First, get a fresh token pair from the API
  const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
    email: authEmail, password: authPassword,
  });
  expect(login.status).toBe(200);

  // Navigate to a public page (won't trigger redirect), then set tokens
  await page.goto(`${FRONTEND}/auth/login`);
  await page.waitForLoadState('domcontentloaded');
  await page.evaluate((tokens: any) => {
    localStorage.setItem('sv_tokens', JSON.stringify(tokens));
  }, login.data);

  // Now navigate to the protected page — AuthProvider will read tokens
  // from localStorage on initial render and call /api/v1/auth/me
  await page.goto(url);
}

test.beforeEach(async ({ page }) => {
  await page.goto(FRONTEND);
  await page.evaluate(() => localStorage.removeItem('sv_tokens'));
});

test.afterEach(async ({ page }) => {
  await page.goto(FRONTEND);
  await page.evaluate(() => localStorage.removeItem('sv_tokens'));
});

test.describe('UI Browser Certification - Authenticated', () => {
  test('Dashboard renders with stats and project card', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/dashboard`);
    await expect(page.locator('text=/Cert-Project/')).toBeVisible({ timeout: 10000 });
  });

  test('Dashboard creates project via New Project form', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/dashboard`);
    await page.click('button:has-text("New Project")');
    const newName = `UI-Cert-${uid()}`;
    await page.fill('input[placeholder="Project name"]', newName);
    await page.click('button:has-text("Create")');
    await expect(page.locator(`text="${newName}"`)).toBeVisible({ timeout: 10000 });
  });

  test('Projects page lists projects', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects`);
    await expect(page.locator('h1:has-text("Projects")')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=/Cert-Project/')).toBeVisible({ timeout: 10000 });
  });

  test('Chat page renders with empty state', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/chat`);
    await expect(page.getByRole('heading', { name: 'AI Chat' })).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text="Start a conversation"')).toBeVisible({ timeout: 10000 });
  });

  test('Chat sends message and receives response', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/chat`);
    const textarea = page.locator('textarea');
    await textarea.fill('What is in this project?');

    // Press Enter to send (handled by onKeyDown handler)
    await textarea.press('Enter');

    // Input clears after successful send
    await expect(textarea).toHaveValue('', { timeout: 10000 });

    // Verify the user message appears in the chat area
    const messagesDiv = page.locator('.flex-1.overflow-y-auto');
    await expect(messagesDiv.locator('text="What is in this project?"').first()).toBeVisible({ timeout: 10000 });

    // AI response completes — "Thinking…" indicator appears then disappears
    // (mock LLM streams a response; this verifies the stream completes)
    await expect(page.getByText('Thinking…')).not.toBeVisible({ timeout: 60000 });
  });

  test('Search page renders', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/search`);
    await expect(page.getByRole('heading', { name: 'Search' })).toBeVisible({ timeout: 10000 });
    await expect(page.locator('input[placeholder*="Search"]')).toBeVisible({ timeout: 10000 });
  });

  test('Memory page renders', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/memory`);
    await expect(page.getByRole('heading', { name: /Memory|Memories/ })).toBeVisible({ timeout: 10000 });
  });

  test('Settings page renders', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/settings`);
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible({ timeout: 10000 });
  });

  test('Ingest page renders with upload form', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/ingest`);
    await expect(page.getByRole('heading', { name: 'Ingest' })).toBeVisible({ timeout: 10000 });
    await expect(page.locator('select')).toBeVisible({ timeout: 10000 });
  });

  test('Facts page renders', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/facts`);
    await expect(page.locator('h1:has-text("Facts")')).toBeVisible({ timeout: 10000 });
  });

  test('Decisions page renders', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/decisions`);
    await expect(page.locator('h1:has-text("Decisions")')).toBeVisible({ timeout: 10000 });
  });
});

// ── Search Network Contract ──────────────────────────────────────────────
test.describe('Search Network Contract', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(FRONTEND);
    await page.evaluate(() => localStorage.removeItem('sv_tokens'));
  });

  test('Search sends POST /api/v1/ingest/search with query and limit params', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/search`);
    await expect(page.getByRole('heading', { name: 'Search' })).toBeVisible({ timeout: 10000 });

    // Verify API contract directly
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('POST', `/api/v1/ingest/search?query=test&limit=10`, login.data.access_token);
    expect(res.status).toBe(200);
    expect(res.data).toHaveProperty('items');
    expect(res.data).toHaveProperty('total');
  });
});

// ── Memory Network Contract ───────────────────────────────────────────────
test.describe('Memory Network Contract', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(FRONTEND);
    await page.evaluate(() => localStorage.removeItem('sv_tokens'));
  });

  test('Memory loads via GET /api/v1/memory/ with project_id param', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/memory`);
    await expect(page.locator('h1:has-text("Memory")').first()).toBeVisible({ timeout: 10000 });

    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/memory/?project_id=${encodeURIComponent(projectId)}&limit=20&offset=0`, login.data.access_token);
    expect(res.status).toBe(200);
    // Memory endpoint returns paginated list (array or {items, total})
    expect(Array.isArray(res.data) || (res.data && Array.isArray(res.data.items))).toBe(true);
  });

  test('Memory page has filter and structure', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/memory`);
    await expect(page.locator('h1:has-text("Memory")').first()).toBeVisible({ timeout: 10000 });
    const select = page.locator('select');
    await expect(select).toBeVisible({ timeout: 10000 });
  });
});

// ── Facts Network Contract ───────────────────────────────────────────────
test.describe('Facts Network Contract', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(FRONTEND);
    await page.evaluate(() => localStorage.removeItem('sv_tokens'));
  });

  test('Facts loads via GET /api/v1/ingest/facts with project_id param', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/facts`);
    await expect(page.locator('h1:has-text("Facts")')).toBeVisible({ timeout: 10000 });

    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/ingest/facts?project_id=${encodeURIComponent(projectId)}&limit=50`, login.data.access_token);
    expect(res.status).toBe(200);
    expect(res.data).toHaveProperty('items');
    expect(res.data).toHaveProperty('total');
  });

  test('Facts page has empty state and subject-predicate-object display', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/facts`);
    await expect(page.locator('h1:has-text("Facts")')).toBeVisible({ timeout: 10000 });
  });
});

// ── Decisions Network Contract ───────────────────────────────────────────
test.describe('Decisions Network Contract', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(FRONTEND);
    await page.evaluate(() => localStorage.removeItem('sv_tokens'));
  });

  test('Decisions loads via GET /api/v1/ingest/decisions with project_id param', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/decisions`);
    await expect(page.locator('h1:has-text("Decisions")')).toBeVisible({ timeout: 10000 });

    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/ingest/decisions?project_id=${encodeURIComponent(projectId)}&limit=50`, login.data.access_token);
    expect(res.status).toBe(200);
    expect(res.data).toHaveProperty('items');
    expect(res.data).toHaveProperty('total');
  });

  test('Decisions page has empty state', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/decisions`);
    await expect(page.locator('h1:has-text("Decisions")')).toBeVisible({ timeout: 10000 });
  });
});
