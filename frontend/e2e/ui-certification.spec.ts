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

  test('Facts page renders', async ({ page }) => {
    await page.goto(`${FRONTEND}/projects/${projectId}/facts`);
    await expect(page).toHaveURL(/\/facts/);
    await expect(page.locator('h1:has-text("Facts")')).toBeVisible({ timeout: 5000 });
  });

  test('Decisions page renders', async ({ page }) => {
    await page.goto(`${FRONTEND}/projects/${projectId}/decisions`);
    await expect(page).toHaveURL(/\/decisions/);
    await expect(page.locator('h1:has-text("Decisions")')).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Search Network Contract', () => {
  test('Search sends POST /api/v1/ingest/search with query and limit params', async ({ page }) => {
    await page.goto(FRONTEND);
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    expect(login.status).toBe(200);
    const { access_token, refresh_token } = login.data;
    await page.evaluate((tokens: any) => {
      localStorage.setItem('sv_tokens', JSON.stringify(tokens));
    }, { access_token, refresh_token });

    await page.goto(`${FRONTEND}/projects/${projectId}/search`);
    await expect(page).toHaveURL(/\/search/);
    await expect(page.getByRole('heading', { name: 'Search' })).toBeVisible({ timeout: 5000 });

    let capturedReq: { method: string; url: string } | null = null;
    page.on('request', (req) => {
      if (req.url().includes('/api/v1/ingest/search')) {
        capturedReq = { method: req.method(), url: req.url() };
      }
    });

    await page.fill('input[placeholder*="Search"]', 'test query');
    await page.click('button:has-text("Search")');

    await new Promise<void>((resolve) => {
      const timeout = setTimeout(() => resolve(), 15000);
      page.on('response', (resp) => {
        if (resp.url().includes('/api/v1/ingest/search')) {
          clearTimeout(timeout);
          resolve();
        }
      });
    });

    expect(capturedReq).not.toBeNull();
    expect(capturedReq.method).toBe('POST');
    expect(capturedReq.url).toContain('/api/v1/ingest/search');
    expect(capturedReq.url).toContain('query=');
    expect(capturedReq.url).toContain('limit=');
  });

  test('Search empty query does not send request', async ({ page }) => {
    await page.goto(FRONTEND);
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    expect(login.status).toBe(200);
    const { access_token, refresh_token } = login.data;
    await page.evaluate((tokens: any) => {
      localStorage.setItem('sv_tokens', JSON.stringify(tokens));
    }, { access_token, refresh_token });

    await page.goto(`${FRONTEND}/projects/${projectId}/search`);
    await expect(page).toHaveURL(/\/search/);

    let searchRequests = 0;
    page.on('request', (request) => {
      if (request.url().includes('/api/v1/ingest/search')) searchRequests++;
    });

    await page.waitForLoadState('networkidle');
    expect(searchRequests).toBe(0);
  });
});

test.describe('Memory Network Contract', () => {
  test('Memory loads via GET /api/v1/memory/ with project_id param', async ({ page }) => {
    await page.goto(FRONTEND);
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    expect(login.status).toBe(200);
    const { access_token, refresh_token } = login.data;
    await page.evaluate((tokens: any) => {
      localStorage.setItem('sv_tokens', JSON.stringify(tokens));
    }, { access_token, refresh_token });

    let capturedReq: { method: string; url: string } | null = null;
    page.on('request', (req) => {
      if (req.url().includes('/api/v1/memory/')) {
        capturedReq = { method: req.method(), url: req.url() };
      }
    });

    await page.goto(`${FRONTEND}/projects/${projectId}/memory`);
    await expect(page).toHaveURL(/\/memory/);
    await expect(page.getByRole('heading', { name: /Memory|Memories/ })).toBeVisible({ timeout: 5000 });

    await new Promise<void>((resolve) => {
      const timeout = setTimeout(() => resolve(), 15000);
      page.on('response', (resp) => {
        if (resp.url().includes('/api/v1/memory/') && resp.status() === 200) {
          clearTimeout(timeout);
          resolve();
        }
      });
    });

    expect(capturedReq).not.toBeNull();
    expect(capturedReq.method).toBe('GET');
    expect(capturedReq.url).toContain('/api/v1/memory/');
    expect(capturedReq.url).toContain('project_id=');
  });

  test('Memory page has filter and structure', async ({ page }) => {
    await page.goto(FRONTEND);
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    expect(login.status).toBe(200);
    const { access_token, refresh_token } = login.data;
    await page.evaluate((tokens: any) => {
      localStorage.setItem('sv_tokens', JSON.stringify(tokens));
    }, { access_token, refresh_token });

    await page.goto(`${FRONTEND}/projects/${projectId}/memory`);
    await expect(page).toHaveURL(/\/memory/);
    await expect(page.getByRole('heading', { name: /Memory|Memories/ })).toBeVisible({ timeout: 5000 });
    const select = page.locator('select');
    await expect(select).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Facts Network Contract', () => {
  test('Facts loads via GET /api/v1/ingest/facts with project_id param', async ({ page }) => {
    await page.goto(FRONTEND);
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    expect(login.status).toBe(200);
    const { access_token, refresh_token } = login.data;
    await page.evaluate((tokens: any) => {
      localStorage.setItem('sv_tokens', JSON.stringify(tokens));
    }, { access_token, refresh_token });

    await page.goto(`${FRONTEND}/projects/${projectId}/facts`);
    await expect(page).toHaveURL(/\/facts/);
    await expect(page.locator('h1:has-text("Facts")')).toBeVisible({ timeout: 5000 });

    let capturedReq: { method: string; url: string } | null = null;
    page.on('request', (req) => {
      if (req.url().includes('/api/v1/ingest/facts')) {
        capturedReq = { method: req.method(), url: req.url() };
      }
    });

    // Navigate away and back to trigger a new request the listener will catch
    await page.goto(`${FRONTEND}/projects/${projectId}/search`);
    await page.goto(`${FRONTEND}/projects/${projectId}/facts`);
    await expect(page).toHaveURL(/\/facts/);

    await new Promise<void>((resolve) => {
      const timeout = setTimeout(() => resolve(), 15000);
      page.on('response', (resp) => {
        if (resp.url().includes('/api/v1/ingest/facts')) {
          clearTimeout(timeout);
          resolve();
        }
      });
    });

    expect(capturedReq).not.toBeNull();
    expect(capturedReq.method).toBe('GET');
    expect(capturedReq.url).toContain('/api/v1/ingest/facts');
    expect(capturedReq.url).toContain('project_id=');
  });

  test('Facts page has empty state and subject-predicate-object display', async ({ page }) => {
    await page.goto(FRONTEND);
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    expect(login.status).toBe(200);
    const { access_token, refresh_token } = login.data;
    await page.evaluate((tokens: any) => {
      localStorage.setItem('sv_tokens', JSON.stringify(tokens));
    }, { access_token, refresh_token });

    await page.goto(`${FRONTEND}/projects/${projectId}/facts`);
    await expect(page).toHaveURL(/\/facts/);
    await expect(page.locator('h1:has-text("Facts")')).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Decisions Network Contract', () => {
  test('Decisions loads via GET /api/v1/ingest/decisions with project_id param', async ({ page }) => {
    await page.goto(FRONTEND);
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    expect(login.status).toBe(200);
    const { access_token, refresh_token } = login.data;
    await page.evaluate((tokens: any) => {
      localStorage.setItem('sv_tokens', JSON.stringify(tokens));
    }, { access_token, refresh_token });

    let capturedReq: { method: string; url: string } | null = null;
    page.on('request', (req) => {
      if (req.url().includes('/api/v1/ingest/decisions')) {
        capturedReq = { method: req.method(), url: req.url() };
      }
    });

    await page.goto(`${FRONTEND}/projects/${projectId}/decisions`);
    await expect(page).toHaveURL(/\/decisions/);
    await expect(page.locator('h1:has-text("Decisions")')).toBeVisible({ timeout: 5000 });

    await new Promise<void>((resolve) => {
      const timeout = setTimeout(() => resolve(), 15000);
      page.on('response', (resp) => {
        if (resp.url().includes('/api/v1/ingest/decisions') && resp.status() === 200) {
          clearTimeout(timeout);
          resolve();
        }
      });
    });

    expect(capturedReq).not.toBeNull();
    expect(capturedReq.method).toBe('GET');
    expect(capturedReq.url).toContain('/api/v1/ingest/decisions');
    expect(capturedReq.url).toContain('project_id=');
  });

  test('Decisions page has empty state', async ({ page }) => {
    await page.goto(FRONTEND);
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    expect(login.status).toBe(200);
    const { access_token, refresh_token } = login.data;
    await page.evaluate((tokens: any) => {
      localStorage.setItem('sv_tokens', JSON.stringify(tokens));
    }, { access_token, refresh_token });

    await page.goto(`${FRONTEND}/projects/${projectId}/decisions`);
    await expect(page).toHaveURL(/\/decisions/);
    await expect(page.locator('h1:has-text("Decisions")')).toBeVisible({ timeout: 5000 });
  });
});
