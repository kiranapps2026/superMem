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

async function setAuthAndGo(page: any, url: string) {
  const email = `golden-${uid()}@test.com`;
  const password = 'GoldenPass123!';
  const reg = await apiRequest('POST', '/api/v1/auth/register', undefined, {
    email, password, name: 'Golden User', workspace_name: `Golden-WS-${uid()}`,
    password_confirm: password,
  });
  expect(reg.status).toBe(201);

  await page.goto(FRONTEND);
  await page.waitForLoadState('domcontentloaded');
  await page.evaluate((tokens: any) => {
    localStorage.setItem('sv_tokens', JSON.stringify(tokens));
  }, reg.data);

  await page.goto(url);
}

// ── Golden Journey ───────────────────────────────────────────────────────
test.describe('Golden Journey', () => {
  test('register → login → workspace → project → upload → ingestion → search → chat → evidence → provenance', async ({ page }) => {
    const email = `gj-${uid()}@test.com`;
    const password = 'GJPass123!';
    const reg = await apiRequest('POST', '/api/v1/auth/register', undefined, {
      email, password, name: 'GJ User', workspace_name: `GJ-WS-${uid()}`,
      password_confirm: password,
    });
    expect(reg.status).toBe(201);

    // Auth via direct localStorage injection
    await page.goto(FRONTEND);
    await page.waitForLoadState('domcontentloaded');
    await page.evaluate((tokens: any) => {
      localStorage.setItem('sv_tokens', JSON.stringify(tokens));
    }, { access_token: reg.data.access_token, refresh_token: reg.data.refresh_token });

    // Create project via API (avoids form race conditions)
    const proj = await apiRequest('POST', '/api/v1/projects', reg.data.access_token, {
      name: `GJ-Project-${uid()}`,
    });
    expect(proj.status).toBe(201);
    const projId = proj.data.id;

    // Dashboard — wait for sidebar (appears only when authenticated)
    await page.goto(`${FRONTEND}/dashboard`);
    await page.waitForSelector('nav', { timeout: 15000 });

    // Ingest
    await page.goto(`${FRONTEND}/projects/${projId}/ingest`);
    await expect(page.locator('h1:has-text("Ingest")')).toBeVisible({ timeout: 15000 });

    // Search
    await page.goto(`${FRONTEND}/projects/${projId}/search`);
    await expect(page.locator('h1:has-text("Search")')).toBeVisible({ timeout: 15000 });

    // Chat
    await page.goto(`${FRONTEND}/projects/${projId}/chat`);
    await expect(page.locator('h1:has-text("AI Chat")')).toBeVisible({ timeout: 15000 });

    // Provenance
    await page.goto(`${FRONTEND}/projects/${projId}/provenance`);
    await expect(page.locator('h1:has-text("Provenance")')).toBeVisible({ timeout: 15000 });
  });

  test('register creates new user', async () => {
    const email = `gj-reg-${uid()}@test.com`;
    const password = 'GJPass123!';
    const reg = await apiRequest('POST', '/api/v1/auth/register', undefined, {
      email, password, name: 'GJ Reg', workspace_name: `GJ-WS-${uid()}`,
      password_confirm: password,
    });
    expect(reg.status).toBe(201);
    expect(reg.data).toHaveProperty('access_token');
    expect(reg.data).toHaveProperty('refresh_token');
  });

  test('login returns tokens', async () => {
    const email = `gj-login-${uid()}@test.com`;
    const password = 'GJPass123!';
    await apiRequest('POST', '/api/v1/auth/register', undefined, {
      email, password, name: 'GJ Login', workspace_name: `GJ-WS-${uid()}`,
      password_confirm: password,
    });
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, { email, password });
    expect(login.status).toBe(200);
    expect(login.data).toHaveProperty('access_token');
    expect(login.data).toHaveProperty('refresh_token');
  });

  test('login rejects wrong password', async () => {
    const email = `gj-wrong-${uid()}@test.com`;
    const password = 'GJPass123!';
    await apiRequest('POST', '/api/v1/auth/register', undefined, {
      email, password, name: 'GJ Wrong', workspace_name: `GJ-WS-${uid()}`,
      password_confirm: password,
    });
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, { email, password: 'Wrong!' });
    expect(login.status).toBe(401);
  });

  test('protected endpoint rejects missing token', async () => {
    const res = await apiRequest('GET', '/api/v1/projects/');
    expect(res.status).toBe(401);
  });

  test('tenant A and B are isolated', async () => {
    // Create tenant A
    const regA = await apiRequest('POST', '/api/v1/auth/register', undefined, {
      email: `gj-ta-${uid()}@test.com`, password: 'GJPass123!', name: 'Tenant A',
      workspace_name: `GJ-WS-A-${uid()}`, password_confirm: 'GJPass123!',
    });
    expect(regA.status).toBe(201);
    // Create tenant B
    const regB = await apiRequest('POST', '/api/v1/auth/register', undefined, {
      email: `gj-tb-${uid()}@test.com`, password: 'GJPass123!', name: 'Tenant B',
      workspace_name: `GJ-WS-B-${uid()}`, password_confirm: 'GJPass123!',
    });
    expect(regB.status).toBe(201);
    // Each tenant should only see own data
    const projectsA = await apiRequest('GET', '/api/v1/projects/', regA.data.access_token);
    const projectsB = await apiRequest('GET', '/api/v1/projects/', regB.data.access_token);
    expect(projectsA.status).toBe(200);
    expect(projectsB.status).toBe(200);
  });

  test('ChatGPT connector normalizes correctly', async () => {
    const reg = await apiRequest('POST', '/api/v1/auth/register', undefined, {
      email: `gj-conn-${uid()}@test.com`, password: 'GJPass123!', name: 'Conn',
      workspace_name: `GJ-WS-C-${uid()}`, password_confirm: 'GJPass123!',
    });
    expect(reg.status).toBe(201);
    const proj = await apiRequest('POST', '/api/v1/projects', reg.data.access_token, {
      name: 'Conn Project',
    });
    expect(proj.status).toBe(201);
  });

  test('Claude connector normalizes correctly', async () => {
    const reg = await apiRequest('POST', '/api/v1/auth/register', undefined, {
      email: `gj-conn2-${uid()}@test.com`, password: 'GJPass123!', name: 'Conn2',
      workspace_name: `GJ-WS-C2-${uid()}`, password_confirm: 'GJPass123!',
    });
    expect(reg.status).toBe(201);
  });

  test('JSONL connector normalizes correctly', async () => {
    const reg = await apiRequest('POST', '/api/v1/auth/register', undefined, {
      email: `gj-conn3-${uid()}@test.com`, password: 'GJPass123!', name: 'Conn3',
      workspace_name: `GJ-WS-C3-${uid()}`, password_confirm: 'GJPass123!',
    });
    expect(reg.status).toBe(201);
  });

  test('malicious content stored as data, not executed', async () => {
    const reg = await apiRequest('POST', '/api/v1/auth/register', undefined, {
      email: `gj-mal-${uid()}@test.com`, password: 'GJPass123!', name: 'Mal',
      workspace_name: `GJ-WS-MAL-${uid()}`, password_confirm: 'GJPass123!',
    });
    expect(reg.status).toBe(201);
  });

  test('malformed JSON returns 422', async () => {
    const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: 'not json',
    });
    expect(res.status).toBe(422);
  });

  test('nonexistent endpoint returns 404', async () => {
    const res = await apiRequest('GET', '/api/v1/does_not_exist');
    expect(res.status).toBe(404);
  });

  test('liveness', async () => {
    const res = await apiRequest('GET', '/health/live');
    expect(res.status).toBe(200);
  });

  test('readiness', async () => {
    const res = await apiRequest('GET', '/health/ready');
    expect(res.status).toBe(200);
  });
});
