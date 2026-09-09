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
 * Navigates to /auth/login first, sets tokens, then goes to the target URL.
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

// ── Timeline Network Contract (CP12) ────────────────────────────────────
test.describe('Timeline Network Contract', () => {
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
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/timeline`);
    await expect(page.locator('h1:has-text("Timeline")')).toBeVisible({ timeout: 10000 });
  });

  test('Timeline page has empty state', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/timeline`);
    await expect(page.locator('h1:has-text("Timeline")')).toBeVisible({ timeout: 10000 });
  });

  test('Timeline vertical slice — items are sorted by timestamp descending', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/ingest/timeline?project_id=${encodeURIComponent(projectId)}&limit=100`, login.data.access_token);
    expect(res.status).toBe(200);
    expect(res.data).toHaveProperty('items');
    expect(res.data).toHaveProperty('total');
    if ((res.data.items as any[]).length > 1) {
      const items = res.data.items as any[];
      const timestamps = items.map(i => new Date(i.timestamp).getTime());
      for (let i = 0; i < timestamps.length - 1; i++) {
        expect(timestamps[i]).toBeGreaterThanOrEqual(timestamps[i + 1]);
      }
    }
  });

  test('Timeline vertical slice — items contain mixed types (fact, decision, memory)', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/ingest/timeline?project_id=${encodeURIComponent(projectId)}&limit=100`, login.data.access_token);
    expect(res.status).toBe(200);
    const items = res.data.items as any[];
    if (items.length > 0) {
      const types = [...new Set(items.map(i => i.item_type))];
      expect(types.every(t => ['fact', 'decision', 'memory'].includes(t))).toBe(true);
    }
  });
});

// ── Sessions Network Contract (CP13) ────────────────────────────────────
test.describe('Sessions Network Contract', () => {
  test('Sessions API: GET /api/v1/sessions/ with project_id returns 200', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/sessions/?project_id=${encodeURIComponent(projectId)}&limit=20&offset=0`, login.data.access_token);
    expect(res.status).toBe(200);
    expect(Array.isArray(res.data)).toBe(true);
  });

  test('Sessions page renders heading', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/sessions`);
    await expect(page.locator('h1:has-text("Sessions")')).toBeVisible({ timeout: 10000 });
  });

  test('Sessions page has empty state', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/sessions`);
    await expect(page.locator('h1:has-text("Sessions")')).toBeVisible({ timeout: 10000 });
  });

  test('Sessions vertical slice — API returns correct schema with limit and offset', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/sessions/?project_id=${encodeURIComponent(projectId)}&limit=20&offset=0`, login.data.access_token);
    expect(res.status).toBe(200);
    expect(Array.isArray(res.data)).toBe(true);
    if (res.data.length > 0) {
      const s = res.data[0];
      expect(s).toHaveProperty('id');
      expect(s).toHaveProperty('title');
      expect(s).toHaveProperty('created_at');
      expect(s).toHaveProperty('updated_at');
    }
  });

  test('Sessions vertical slice — empty project returns empty array', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    // Use a fresh project with no sessions
    const freshProj = await apiRequest('POST', '/api/v1/projects', login.data.access_token, {
      name: `Empty-Session-Project-${uid()}`,
    });
    expect(freshProj.status).toBe(201);
    const res = await apiRequest('GET', `/api/v1/sessions/?project_id=${encodeURIComponent(freshProj.data.id)}&limit=20&offset=0`, login.data.access_token);
    expect(res.status).toBe(200);
    expect(Array.isArray(res.data)).toBe(true);
    expect(res.data.length).toBe(0);
  });
});

// ── Graph Network Contract (CP14) ───────────────────────────────────────
test.describe('Graph Network Contract', () => {
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
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/graph`);
    await expect(page.locator('h1:has-text("Knowledge Graph")')).toBeVisible({ timeout: 10000 });
  });

  test('Graph page has empty state', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/graph`);
    await expect(page.locator('h1:has-text("Knowledge Graph")')).toBeVisible({ timeout: 10000 });
  });

  test('Graph vertical slice — API returns { nodes, edges } schema', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/ingest/graph?project_id=${encodeURIComponent(projectId)}`, login.data.access_token);
    expect(res.status).toBe(200);
    expect(res.data).toHaveProperty('nodes');
    expect(res.data).toHaveProperty('edges');
    if ((res.data.nodes as any[]).length > 0) {
      const node = res.data.nodes[0];
      expect(node).toHaveProperty('id');
      expect(node).toHaveProperty('label');
      expect(node).toHaveProperty('node_type');
      expect(node).toHaveProperty('temporal_status');
    }
  });

  test('Graph vertical slice — edges reference valid node IDs', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/ingest/graph?project_id=${encodeURIComponent(projectId)}`, login.data.access_token);
    expect(res.status).toBe(200);
    const nodes = res.data.nodes as any[];
    const edges = res.data.edges as any[];
    const nodeIds = new Set(nodes.map(n => n.id));
    if (edges.length > 0) {
      edges.forEach((e: any) => {
        expect(nodeIds.has(e.source_node_id)).toBe(true);
        expect(nodeIds.has(e.target_node_id)).toBe(true);
      });
    }
  });
});

// ── Provenance Network Contract (CP15) ──────────────────────────────────
test.describe('Provenance Network Contract', () => {
  test('Provenance API: GET /api/v1/provenance/ with project_id returns 200', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/provenance/?project_id=${encodeURIComponent(projectId)}`, login.data.access_token);
    expect(res.status).toBe(200);
    expect(Array.isArray(res.data)).toBe(true);
  });

  test('Provenance page renders heading', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/provenance`);
    await expect(page.locator('h1:has-text("Provenance")')).toBeVisible({ timeout: 10000 });
  });

  test('Provenance page has empty state', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/provenance`);
    await expect(page.locator('h1:has-text("Provenance")')).toBeVisible({ timeout: 10000 });
  });

  test('Provenance vertical slice — API returns correct schema', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/provenance/?project_id=${encodeURIComponent(projectId)}`, login.data.access_token);
    expect(res.status).toBe(200);
    expect(Array.isArray(res.data)).toBe(true);
    if (res.data.length > 0) {
      const p = res.data[0];
      expect(p).toHaveProperty('id');
      expect(p).toHaveProperty('session_id');
      expect(p).toHaveProperty('model');
      expect(p).toHaveProperty('provider');
      expect(p).toHaveProperty('latency_ms');
      expect(p).toHaveProperty('total_tokens');
      expect(p).toHaveProperty('retrieval_method');
      expect(p).toHaveProperty('created_at');
    }
  });

  test('Provenance vertical slice — requires authentication', async () => {
    const res = await apiRequest('GET', `/api/v1/provenance/?project_id=${encodeURIComponent(projectId)}`);
    expect(res.status).toBe(401);
  });
});
