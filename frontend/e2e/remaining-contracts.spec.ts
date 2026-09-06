import { test, expect } from '@playwright/test';

const FRONTEND = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';
const API_BASE = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000';

async function apiRequest(method: string, path: string, token?: string, body?: any) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json', 'X-E2E': 'true' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = res.ok ? await res.json() : await res.text();
  return { status: res.status, data };
}

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

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

async function loginAndSetToken(page: any) {
  await page.goto(FRONTEND);
  const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
    email: authEmail, password: authPassword,
  });
  expect(login.status).toBe(200);
  const { access_token, refresh_token } = login.data;
  await page.evaluate((tokens: any) => {
    localStorage.setItem('sv_tokens', JSON.stringify(tokens));
  }, { access_token, refresh_token });
}

// ── Timeline Network Contract (CP12) ────────────────────────────────────
test.describe('Timeline Network Contract', () => {
  test.beforeEach(async ({ page }) => { await loginAndSetToken(page); });

  test('Timeline API: GET /api/v1/ingest/timeline with project_id returns 200', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/ingest/timeline?project_id=${encodeURIComponent(projectId)}`, login.data.access_token);
    expect(res.status).toBe(200);
    expect(res.data).toHaveProperty('items');
    expect(res.data).toHaveProperty('total');
  });

  test('Timeline page renders heading', async ({ page }) => {
    await page.goto(`${FRONTEND}/projects/${projectId}/timeline`);
    await expect(page).toHaveURL(/\/timeline/);
    await expect(page.locator('h1:has-text("Timeline")')).toBeVisible({ timeout: 5000 });
  });

  test('Timeline page has empty state', async ({ page }) => {
    await page.goto(`${FRONTEND}/projects/${projectId}/timeline`);
    await expect(page).toHaveURL(/\/timeline/);
    await expect(page.locator('h1:has-text("Timeline")')).toBeVisible({ timeout: 5000 });
  });
});

// ── Sessions Network Contract (CP13) ────────────────────────────────────
test.describe('Sessions Network Contract', () => {
  test.beforeEach(async ({ page }) => { await loginAndSetToken(page); });

  test('Sessions API: GET /api/v1/sessions/ with project_id returns 200', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/sessions/?project_id=${encodeURIComponent(projectId)}&limit=20&offset=0`, login.data.access_token);
    expect(res.status).toBe(200);
    expect(Array.isArray(res.data)).toBe(true);
  });

  test('Sessions page renders heading', async ({ page }) => {
    await page.goto(`${FRONTEND}/projects/${projectId}/sessions`);
    await expect(page).toHaveURL(/\/sessions/);
    await expect(page.locator('h1:has-text("Sessions")')).toBeVisible({ timeout: 5000 });
  });

  test('Sessions page has empty state', async ({ page }) => {
    await page.goto(`${FRONTEND}/projects/${projectId}/sessions`);
    await expect(page).toHaveURL(/\/sessions/);
    await expect(page.locator('h1:has-text("Sessions")')).toBeVisible({ timeout: 5000 });
  });
});

// ── Graph Network Contract (CP14) ───────────────────────────────────────
test.describe('Graph Network Contract', () => {
  test.beforeEach(async ({ page }) => { await loginAndSetToken(page); });

  test('Graph API: GET /api/v1/ingest/graph returns 200', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/ingest/graph?project_id=${encodeURIComponent(projectId)}`, login.data.access_token);
    expect(res.status).toBe(200);
    expect(res.data).toHaveProperty('nodes');
    expect(res.data).toHaveProperty('edges');
  });

  test('Graph page renders heading', async ({ page }) => {
    await page.goto(`${FRONTEND}/projects/${projectId}/graph`);
    await expect(page).toHaveURL(/\/graph/);
    await expect(page.locator('h1:has-text("Knowledge Graph")')).toBeVisible({ timeout: 5000 });
  });

  test('Graph page has empty state', async ({ page }) => {
    await page.goto(`${FRONTEND}/projects/${projectId}/graph`);
    await expect(page).toHaveURL(/\/graph/);
    await expect(page.locator('h1:has-text("Knowledge Graph")')).toBeVisible({ timeout: 5000 });
  });
});

// ── Provenance Network Contract (CP15) ──────────────────────────────────
test.describe('Provenance Network Contract', () => {
  test.beforeEach(async ({ page }) => { await loginAndSetToken(page); });

  test('Provenance API: GET /api/v1/provenance/ with project_id returns 200', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/provenance/?project_id=${encodeURIComponent(projectId)}`, login.data.access_token);
    expect(res.status).toBe(200);
    expect(Array.isArray(res.data)).toBe(true);
  });

  test('Provenance page renders heading', async ({ page }) => {
    await page.goto(`${FRONTEND}/projects/${projectId}/provenance`);
    await expect(page).toHaveURL(/\/provenance/);
    await expect(page.locator('h1:has-text("Provenance")')).toBeVisible({ timeout: 5000 });
  });

  test('Provenance page has empty state', async ({ page }) => {
    await page.goto(`${FRONTEND}/projects/${projectId}/provenance`);
    await expect(page).toHaveURL(/\/provenance/);
    await expect(page.locator('h1:has-text("Provenance")')).toBeVisible({ timeout: 5000 });
  });
});
