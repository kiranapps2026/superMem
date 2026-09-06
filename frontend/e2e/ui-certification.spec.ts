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
    email: authEmail, password: authPassword, name: 'Cert User', workspace_name: `Cert-WS-${uid()}`,
  });
  expect(reg.status).toBe(201);
  const token = reg.data.access_token;
  const proj = await apiRequest('POST', '/api/v1/projects/', token, {
    name: 'Cert Project', description: 'UI certification project',
  });
  expect(proj.status).toBe(201);
  projectId = proj.data.id;
});

test.beforeEach(async ({ page }) => {
  // Navigate to frontend first to establish proper origin, then inject auth tokens
  await page.goto(FRONTEND);
  const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
    email: authEmail, password: authPassword,
  });
  expect(login.status).toBe(200);
  const { access_token, refresh_token } = login.data;
  await page.evaluate((tokens: any) => {
    localStorage.setItem('sv_tokens', JSON.stringify(tokens));
  }, { access_token, refresh_token });
});

test.describe('UI Browser Certification - Authenticated', () => {
  test('Dashboard renders with stats and project card', async ({ page }) => {
    await page.goto(`${FRONTEND}/dashboard`);
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator('text="Cert Project"')).toBeVisible({ timeout: 5000 });
  });

  test('Dashboard creates project via New Project form', async ({ page }) => {
    await page.goto(`${FRONTEND}/dashboard`);
    await expect(page).toHaveURL(/\/dashboard/);
    await page.click('button:has-text("New Project")');
    const newName = `UI-Cert-${uid()}`;
    await page.fill('input[placeholder="Project name"]', newName);
    await page.click('button:has-text("Create")');
    await expect(page.locator(`text="${newName}"`)).toBeVisible({ timeout: 5000 });
  });

  test('Projects page lists projects', async ({ page }) => {
    await page.goto(`${FRONTEND}/projects`);
    await expect(page).toHaveURL(/\/projects/);
    await expect(page.getByRole('heading', { name: 'Projects' })).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text="Cert Project"')).toBeVisible({ timeout: 5000 });
  });

  test('Chat page renders with empty state', async ({ page }) => {
    await page.goto(`${FRONTEND}/projects/${projectId}/chat`);
    await expect(page).toHaveURL(/\/chat/);
    await expect(page.getByRole('heading', { name: 'AI Chat' })).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text="Start a conversation"')).toBeVisible({ timeout: 5000 });
  });

  test('Chat sends message and receives response', async ({ page }) => {
    await page.goto(`${FRONTEND}/projects/${projectId}/chat`);
    await expect(page).toHaveURL(/\/chat/);
    const textarea = page.locator('textarea');
    await textarea.fill('What is in this project?');
    const sendBtn = page.locator('button:has(svg)').last();
    await sendBtn.click();
    await expect(page.locator('text="Thinking...')).not.toBeVisible({ timeout: 30000 });
  });

  test('Search page renders', async ({ page }) => {
    await page.goto(`${FRONTEND}/projects/${projectId}/search`);
    await expect(page).toHaveURL(/\/search/);
    await expect(page.getByRole('heading', { name: 'Search' })).toBeVisible({ timeout: 5000 });
    await expect(page.locator('input[placeholder*="Search"]')).toBeVisible({ timeout: 5000 });
  });

  test('Memory page renders', async ({ page }) => {
    await page.goto(`${FRONTEND}/projects/${projectId}/memory`);
    await expect(page).toHaveURL(/\/memory/);
    await expect(page.getByRole('heading', { name: /Memory|Memories/ })).toBeVisible({ timeout: 5000 });
  });

  test('Settings page renders', async ({ page }) => {
    await page.goto(`${FRONTEND}/settings`);
    await expect(page).toHaveURL(/\/settings/);
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible({ timeout: 5000 });
  });

  test('Ingest page renders with upload form', async ({ page }) => {
    await page.goto(`${FRONTEND}/projects/${projectId}/ingest`);
    await expect(page).toHaveURL(/\/ingest/);
    await expect(page.getByRole('heading', { name: 'Ingest' })).toBeVisible({ timeout: 5000 });
    await expect(page.locator('select')).toBeVisible({ timeout: 5000 });
  });
});
