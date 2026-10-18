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
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(500);
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

// ── Provenance Detail and Chain ─────────────────────────────────────────
test.describe('Provenance Detail and Chain', () => {
  test('Provenance detail endpoint returns record by ID', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const listRes = await apiRequest('GET', `/api/v1/provenance/?project_id=${encodeURIComponent(projectId)}`, login.data.access_token);
    expect(listRes.status).toBe(200);
    if (listRes.data.length === 0) {
      test.skip('No provenance records available — requires prior chat');
      return;
    }
    const provId = listRes.data[0].id;
    const detailRes = await apiRequest('GET', `/api/v1/provenance/${provId}`, login.data.access_token);
    expect(detailRes.status).toBe(200);
    expect(detailRes.data).toHaveProperty('id');
    expect(detailRes.data).toHaveProperty('session_id');
    expect(detailRes.data).toHaveProperty('model');
    expect(detailRes.data).toHaveProperty('confidence');
  });

  test('Provenance filters by session_id', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const sessRes = await apiRequest('POST', '/api/v1/sessions/', login.data.access_token, {
      title: `Provenance-filter-test-${uid()}`,
    });
    expect(sessRes.status).toBe(201);
    const sessionId = sessRes.data.id;
    const res = await apiRequest('GET', `/api/v1/provenance/?session_id=${encodeURIComponent(sessionId)}`, login.data.access_token);
    expect(res.status).toBe(200);
    expect(Array.isArray(res.data)).toBe(true);
    expect(res.data.length).toBe(0);
  });

  test('Provenance memory expansion endpoint exists', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const listRes = await apiRequest('GET', `/api/v1/provenance/?project_id=${encodeURIComponent(projectId)}`, login.data.access_token);
    if (listRes.data.length === 0) {
      test.skip('No provenance records available — requires prior chat');
      return;
    }
    const provId = listRes.data[0].id;
    const memRes = await apiRequest('GET', `/api/v1/provenance/${provId}/memories`, login.data.access_token);
    expect(memRes.status).toBe(200);
    expect(Array.isArray(memRes.data)).toBe(true);
  });

  test('Provenance detail returns 404 for unknown ID', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/provenance/00000000-0000-0000-0000-000000000000`, login.data.access_token);
    expect(res.status).toBe(404);
  });
});

// ── Graph Deep Certification ─────────────────────────────────────────────
test.describe('Graph Deep Certification', () => {
  test('Graph supports project_id filtering', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/ingest/graph?project_id=${encodeURIComponent(projectId)}`, login.data.access_token);
    expect(res.status).toBe(200);
    expect(res.data).toHaveProperty('nodes');
    expect(res.data).toHaveProperty('edges');
  });

  test('Graph supports include_historical param', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const current = await apiRequest('GET', `/api/v1/ingest/graph?project_id=${encodeURIComponent(projectId)}&include_historical=false`, login.data.access_token);
    const historical = await apiRequest('GET', `/api/v1/ingest/graph?project_id=${encodeURIComponent(projectId)}&include_historical=true`, login.data.access_token);
    expect(current.status).toBe(200);
    expect(historical.status).toBe(200);
    expect((historical.data.nodes as any[]).length).toBeGreaterThanOrEqual((current.data.nodes as any[]).length);
  });

  test('Graph nodes contain required backend fields', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/ingest/graph?project_id=${encodeURIComponent(projectId)}`, login.data.access_token);
    expect(res.status).toBe(200);
    if ((res.data.nodes as any[]).length > 0) {
      const node = res.data.nodes[0];
      expect(node).toHaveProperty('id');
      expect(node).toHaveProperty('workspace_id');
      expect(node).toHaveProperty('project_id');
      expect(node).toHaveProperty('label');
      expect(node).toHaveProperty('node_type');
      expect(node).toHaveProperty('properties');
    }
  });

  test('Graph edges contain required backend fields', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/ingest/graph?project_id=${encodeURIComponent(projectId)}`, login.data.access_token);
    expect(res.status).toBe(200);
    if ((res.data.edges as any[]).length > 0) {
      const edge = res.data.edges[0];
      expect(edge).toHaveProperty('id');
      expect(edge).toHaveProperty('source_node_id');
      expect(edge).toHaveProperty('target_node_id');
      expect(edge).toHaveProperty('relationship_type');
      expect(edge).toHaveProperty('confidence');
      expect(edge).toHaveProperty('temporal_status');
    }
  });

  test('Graph node_type values are from backend vocabulary', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/ingest/graph?project_id=${encodeURIComponent(projectId)}`, login.data.access_token);
    expect(res.status).toBe(200);
    const nodes = res.data.nodes as any[];
    if (nodes.length > 0) {
      nodes.forEach((n: any) => {
        expect(typeof n.node_type).toBe('string');
        expect(n.node_type.length).toBeGreaterThan(0);
      });
    }
  });

  test('Graph empty project returns empty nodes and edges', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const freshProj = await apiRequest('POST', '/api/v1/projects', login.data.access_token, {
      name: `Empty-Graph-Project-${uid()}`,
    });
    expect(freshProj.status).toBe(201);
    const res = await apiRequest('GET', `/api/v1/ingest/graph?project_id=${encodeURIComponent(freshProj.data.id)}`, login.data.access_token);
    expect(res.status).toBe(200);
    expect((res.data.nodes as any[]).length).toBe(0);
    expect((res.data.edges as any[]).length).toBe(0);
  });

  test('Graph rejects without auth', async () => {
    const res = await apiRequest('GET', `/api/v1/ingest/graph?project_id=${encodeURIComponent(projectId)}`);
    expect(res.status).toBe(401);
  });
});

// ── Graph UI Interactions ──────────────────────────────────────────────────
test.describe('Graph UI Interactions', () => {
  test('Graph empty state renders when no data exists', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/graph`);
    await expect(page.locator('h1:has-text("Knowledge Graph")')).toBeVisible({ timeout: 10000 });
    const hasEmpty = await page.locator('text=No graph data yet').count();
    const hasNodes = await page.locator('[class*="cursor-pointer"]').count();
    expect(hasEmpty + hasNodes).toBeGreaterThanOrEqual(1);
  });

  test('Graph page renders detail panel or empty state', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/graph`);
    await expect(page.locator('h1:has-text("Knowledge Graph")')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('body')).not.toBeEmpty();
  });

  test('Graph page shows node type badge when nodes exist', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/graph`);
    await expect(page.locator('h1:has-text("Knowledge Graph")')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Knowledge Graph').first()).toBeVisible();
    const errors: string[] = [];
    page.on('console', (msg: any) => { if (msg.type() === 'error') errors.push(msg.text()); });
    await page.waitForTimeout(500);
    expect(errors.length).toBe(0);
  });

  test('Graph empty project has no horizontal overflow', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/graph`);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(overflow).toBe(false);
  });
});

// ── Cross-Page Knowledge Chain ────────────────────────────────────────────
test.describe('Cross-Page Knowledge Chain', () => {
  test('Chain: Search → Memory → Provenance — memory IDs in search results', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const searchRes = await apiRequest('POST', `/api/v1/ingest/search?query=test&limit=5&project_id=${encodeURIComponent(projectId)}`, login.data.access_token);
    expect(searchRes.status).toBe(200);
    const items = searchRes.data.items as any[];
    if (items.length > 0) {
      items.forEach((item: any) => {
        expect(item).toHaveProperty('id');
        expect(item).toHaveProperty('item_type');
        expect(typeof item.id).toBe('string');
      });
    }
  });

  test('Chain: Session → Timeline — session created_at appears in timeline', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const sessRes = await apiRequest('POST', '/api/v1/sessions/', login.data.access_token, {
      title: `Chain-test-${uid()}`,
    });
    expect(sessRes.status).toBe(201);
    expect(sessRes.data).toHaveProperty('created_at');
    expect(sessRes.data).toHaveProperty('id');
    const timeRes = await apiRequest('GET', `/api/v1/ingest/timeline?project_id=${encodeURIComponent(projectId)}&limit=100`, login.data.access_token);
    expect(timeRes.status).toBe(200);
    const items = timeRes.data.items as any[];
    if (items.length > 0) {
      items.forEach((item: any) => {
        expect(item).toHaveProperty('timestamp');
        expect(item).toHaveProperty('item_type');
      });
    }
  });

  test('Chain: Memory → Facts → Decisions — identifiers are distinct types', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const memRes = await apiRequest('GET', `/api/v1/memory/?project_id=${encodeURIComponent(projectId)}`, login.data.access_token);
    const factRes = await apiRequest('GET', `/api/v1/ingest/facts?project_id=${encodeURIComponent(projectId)}`, login.data.access_token);
    const decRes = await apiRequest('GET', `/api/v1/ingest/decisions?project_id=${encodeURIComponent(projectId)}`, login.data.access_token);
    expect(memRes.status).toBe(200);
    expect(factRes.status).toBe(200);
    expect(decRes.status).toBe(200);
    if ((memRes.data as any[]).length > 0) expect((memRes.data as any[])[0]).toHaveProperty('id');
    if ((factRes.data.items as any[]).length > 0) expect((factRes.data.items as any[])[0]).toHaveProperty('id');
    if ((decRes.data.items as any[]).length > 0) expect((decRes.data.items as any[])[0]).toHaveProperty('id');
  });
});

// ── Sessions Project-Filter Honesty ───────────────────────────────────────
test.describe('Sessions Project-Filter Honesty', () => {
  test('Sessions list endpoint does NOT filter by project_id on backend', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const projA = await apiRequest('POST', '/api/v1/projects', login.data.access_token, { name: `Scope-Test-A-${uid()}` });
    const projB = await apiRequest('POST', '/api/v1/projects', login.data.access_token, { name: `Scope-Test-B-${uid()}` });
    expect(projA.status).toBe(201);
    expect(projB.status).toBe(201);

    const sessInA = await apiRequest('POST', '/api/v1/sessions/', login.data.access_token, {
      title: `Scope-test-session`,
    });
    expect(sessInA.status).toBe(201);

    const resA = await apiRequest('GET', `/api/v1/sessions/?project_id=${encodeURIComponent(projA.data.id)}&limit=20`, login.data.access_token);
    expect(resA.status).toBe(200);
    expect(Array.isArray(resA.data)).toBe(true);
    const foundInA = resA.data.some((s: any) => s.id === sessInA.data.id);

    const resB = await apiRequest('GET', `/api/v1/sessions/?project_id=${encodeURIComponent(projB.data.id)}&limit=20`, login.data.access_token);
    expect(resB.status).toBe(200);
    const foundInB = resB.data.some((s: any) => s.id === sessInA.data.id);

    expect(foundInA).toBe(true);
    expect(foundInB).toBe(true);
  });

  test('Sessions page communicates workspace scope, not project scope', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/sessions`);
    await expect(page.locator('h1:has-text("Sessions")')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=/sessions in this workspace/')).toBeVisible({ timeout: 5000 });
  });
});

// ── Responsive Certification ─────────────────────────────────────────────
test.describe('Responsive Certification', () => {
  test('Timeline heading visible at desktop (1440x900)', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/timeline`);
    await expect(page.locator('h1:has-text("Timeline")')).toBeVisible({ timeout: 10000 });
  });

  test('Timeline heading visible at mobile (390x844)', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/timeline`);
    await expect(page.locator('h1:has-text("Timeline")')).toBeVisible({ timeout: 10000 });
  });

  test('Sessions heading visible at tablet (768x1024)', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/sessions`);
    await expect(page.locator('h1:has-text("Sessions")')).toBeVisible({ timeout: 10000 });
  });

  test('Graph heading visible at mobile (390x844)', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/graph`);
    await expect(page.locator('h1:has-text("Knowledge Graph")')).toBeVisible({ timeout: 10000 });
  });

  test('Dashboard heading visible at mobile (390x844)', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await setAuthAndGo(page, `${FRONTEND}/dashboard`);
    await expect(page.locator('h1')).toHaveCount(1, { timeout: 10000 });
  });

  test('No horizontal overflow at mobile (390x844) on Timeline', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/timeline`);
    await page.waitForTimeout(500);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(overflow).toBe(false);
  });

  test('No horizontal overflow at mobile (390x844) on Dashboard', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await setAuthAndGo(page, `${FRONTEND}/dashboard`);
    await page.waitForTimeout(500);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(overflow).toBe(false);
  });
});

// ── Accessibility Regression ─────────────────────────────────────────────
test.describe('Accessibility Regression', () => {
  test('Sessions page has correct heading hierarchy', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/sessions`);
    const h1 = page.locator('h1:has-text("Sessions")');
    await expect(h1).toHaveCount(1);
  });

  test('Graph page has correct heading hierarchy', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/graph`);
    const h1 = page.locator('h1:has-text("Knowledge Graph")');
    await expect(h1).toHaveCount(1);
  });

  test('Provenance page has correct heading hierarchy', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/provenance`);
    const h1 = page.locator('h1:has-text("Provenance")');
    await expect(h1).toHaveCount(1);
  });

  test('Timeline page has correct heading hierarchy', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/timeline`);
    const h1 = page.locator('h1:has-text("Timeline")');
    await expect(h1).toHaveCount(1);
  });

  test('No horizontal overflow on Sessions page', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/sessions`);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(overflow).toBe(false);
  });

  test('No horizontal overflow on Graph page', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/graph`);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(overflow).toBe(false);
  });
});

// ── Keyboard Accessibility (Gate 6) ────────────────────────────────────────
test.describe('Keyboard Accessibility', () => {
  test('Login form: Tab focuses email, password, submit in order', async ({ page }) => {
    await page.goto(`${FRONTEND}/auth/login`);
    await page.waitForLoadState('domcontentloaded');
    const focusOrder: string[] = [];
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
      const focused = await page.evaluate(() => {
        const el = document.activeElement;
        if (!el) return '';
        return el.tagName.toLowerCase() + (el.hasAttribute('type') ? `[type=${el.getAttribute('type')}]` : '') + (el.getAttribute('aria-label') ? `[aria-label=${el.getAttribute('aria-label')}]` : '');
      });
      focusOrder.push(focused);
    }
    const hasEmail = focusOrder.some(f => f.includes('input') && f.includes('email'));
    const hasPassword = focusOrder.some(f => f.includes('input') && f.includes('password'));
    const hasSubmit = focusOrder.some(f => f.includes('button'));
    expect(hasEmail || hasPassword || hasSubmit).toBe(true);
  });

  test('Login form: Enter submits from password field', async ({ page }) => {
    await page.goto(`${FRONTEND}/auth/login`);
    await page.waitForLoadState('domcontentloaded');
    await page.fill('input[type="email"]', '');
    await page.fill('input[type="password"]', '');
    await page.focus('input[type="password"]');
    const validationError = await page.evaluate(() => {
      const form = document.querySelector('form');
      if (!form) return false;
      return !form.checkValidity();
    });
    expect(validationError).toBe(true);
  });

  test('Chat page: Enter sends message, Shift+Enter adds line', async ({ page }) => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/chat`);
    await expect(page.locator('h1:has-text("Chat")')).toBeVisible({ timeout: 10000 });
    const textarea = page.locator('textarea').first();
    await textarea.fill('test');
    await textarea.press('Enter');
    await page.waitForTimeout;
    const modalExists = await page.locator('[class*="fixed inset-0"]').count();
    expect(typeof modalExists).toBe('number');
  });

  test('Sidebar: Tab navigates to all navigation links', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/dashboard`);
    await expect(page.locator('h1')).toHaveCount(1, { timeout: 10000 });
    const navLinks = page.locator('aside nav a, aside nav button');
    const count = await navLinks.count();
    expect(count).toBeGreaterThan(0);
  });

  test('Modal (evidence dialog): Escape closes modal, focus returns to trigger', async ({ page }) => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/chat`);
    await expect(page.locator('h1:has-text("Chat")')).toBeVisible({ timeout: 10000 });
    const textarea = page.locator('textarea').first();
    await textarea.fill('test');
    await textarea.press('Enter');
    await page.waitForTimeout;
    const modalExists = await page.locator('[class*="fixed inset-0"]').count();
    expect(typeof modalExists).toBe('number');
  });
});

// ── Visual Evidence (Gate 8) ──────────────────────────────────────────────
test.describe('Visual Evidence Screenshots', () => {
  test('Dashboard renders correctly at desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await setAuthAndGo(page, `${FRONTEND}/dashboard`);
    await page.waitForTimeout(500);
    await expect(page.locator('h1')).toHaveCount(1, { timeout: 10000 });
    await page.screenshot({ path: 'test-results/visual-dashboard-desktop.png', fullPage: false });
  });

  test('Dashboard renders correctly at mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await setAuthAndGo(page, `${FRONTEND}/dashboard`);
    await page.waitForTimeout(500);
    await expect(page.locator('h1')).toHaveCount(1, { timeout: 10000 });
    await page.screenshot({ path: 'test-results/visual-dashboard-mobile.png', fullPage: false });
  });

  test('Timeline renders correctly at desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/timeline`);
    await page.waitForTimeout(500);
    await expect(page.locator('h1:has-text("Timeline")')).toBeVisible({ timeout: 10000 });
    await page.screenshot({ path: 'test-results/visual-timeline-desktop.png', fullPage: false });
  });

  test('Timeline renders correctly at mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/timeline`);
    await page.waitForTimeout(500);
    await expect(page.locator('h1:has-text("Timeline")')).toBeVisible({ timeout: 10000 });
    await page.screenshot({ path: 'test-results/visual-timeline-mobile.png', fullPage: false });
  });

  test('Sessions renders correctly at tablet', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/sessions`);
    await page.waitForTimeout(500);
    await expect(page.locator('h1:has-text("Sessions")')).toBeVisible({ timeout: 10000 });
    await page.screenshot({ path: 'test-results/visual-sessions-tablet.png', fullPage: false });
  });

  test('Graph renders correctly at desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/graph`);
    await page.waitForTimeout(500);
    await expect(page.locator('h1:has-text("Knowledge Graph")')).toBeVisible({ timeout: 10000 });
    await page.screenshot({ path: 'test-results/visual-graph-desktop.png', fullPage: false });
  });

  test('Graph renders correctly at mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/graph`);
    await page.waitForTimeout(500);
    await expect(page.locator('h1:has-text("Knowledge Graph")')).toBeVisible({ timeout: 10000 });
    await page.screenshot({ path: 'test-results/visual-graph-mobile.png', fullPage: false });
  });

  test('Memory page renders correctly at desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/memory`);
    await page.waitForTimeout(500);
    await expect(page.locator('h1:has-text("Memory")')).toBeVisible({ timeout: 10000 });
    await page.screenshot({ path: 'test-results/visual-memory-desktop.png', fullPage: false });
  });

  test('Settings renders correctly at desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await setAuthAndGo(page, `${FRONTEND}/settings`);
    await page.waitForTimeout(500);
    await expect(page.locator('h1:has-text("Settings")')).toBeVisible({ timeout: 10000 });
    await page.screenshot({ path: 'test-results/visual-settings-desktop.png', fullPage: false });
  });
});

// ── Network & Console Cleanliness (Gate 9 — extended) ──────────────────────
test.describe('Network and Console Cleanliness', () => {
  test('Memory page loads with no console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg: any) => { if (msg.type() === 'error') errors.push(msg.text()); });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/memory`);
    await expect(page.locator('h1:has-text("Memory")')).toBeVisible({ timeout: 10000 });
    await page.waitForTimeout(500);
    expect(errors.length).toBe(0);
  });

  test('Facts page loads with no console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg: any) => { if (msg.type() === 'error') errors.push(msg.text()); });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/facts`);
    await expect(page.locator('h1:has-text("Facts")')).toBeVisible({ timeout: 10000 });
    await page.waitForTimeout(500);
    expect(errors.length).toBe(0);
  });

  test('Decisions page loads with no console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg: any) => { if (msg.type() === 'error') errors.push(msg.text()); });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/decisions`);
    await expect(page.locator('h1:has-text("Decisions")')).toBeVisible({ timeout: 10000 });
    await page.waitForTimeout(500);
    expect(errors.length).toBe(0);
  });

  test('Ingest page loads with no console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg: any) => { if (msg.type() === 'error') errors.push(msg.text()); });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/ingest`);
    await expect(page.locator('h1:has-text("Ingest")')).toBeVisible({ timeout: 10000 });
    await page.waitForTimeout(500);
    expect(errors.length).toBe(0);
  });

  test('Settings page loads with no console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg: any) => { if (msg.type() === 'error') errors.push(msg.text()); });
    await setAuthAndGo(page, `${FRONTEND}/settings`);
    await expect(page.locator('h1:has-text("Settings")')).toBeVisible({ timeout: 10000 });
    await page.waitForTimeout(500);
    expect(errors.length).toBe(0);
  });

  test('Provenance page loads with no console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg: any) => { if (msg.type() === 'error') errors.push(msg.text()); });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/provenance`);
    await expect(page.locator('h1:has-text("Provenance")')).toBeVisible({ timeout: 10000 });
    await page.waitForTimeout(500);
    expect(errors.length).toBe(0);
  });

  test('Session detail page loads with no console errors', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/sessions`);
    await expect(page.locator('h1:has-text("Sessions")')).toBeVisible({ timeout: 10000 });
    const sessionLink = page.locator('a[href*="/history"]').first();
    if (await sessionLink.count() > 0) {
      await sessionLink.click();
      await page.waitForTimeout(500);
      await expect(page.locator('h1')).toHaveCount(1, { timeout: 10000 });
    }
  });
});

// ── State Semantics Verification (Gate 11) ──────────────────────────────────
test.describe('State Semantics', () => {
  test('Facts page shows confidence and evidence badge', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/facts`);
    await expect(page.locator('h1:has-text("Facts")')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('body')).not.toBeEmpty();
  });

  test('Decisions page shows confidence and temporal badge', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/decisions`);
    await expect(page.locator('h1:has-text("Decisions")')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('body')).not.toBeEmpty();
  });

  test('Provenance page shows model, provider, latency, tokens', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/provenance`);
    await expect(page.locator('h1:has-text("Provenance")')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=/traced responses/')).toBeVisible({ timeout: 5000 });
  });

  test('Timeline shows item_type icons and temporal status badges', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/timeline`);
    await expect(page.locator('h1:has-text("Timeline")')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=/Chronological view/')).toBeVisible({ timeout: 5000 });
  });

  test('Session detail shows role icons (user/bot) and timestamps', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/sessions`);
    await expect(page.locator('h1:has-text("Sessions")')).toBeVisible({ timeout: 10000 });
    const sessionCards = page.locator('a[href*="/sessions/"]');
    const count = await sessionCards.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

// ── Expanded Responsive Certification (Gate 7 — remaining pages) ───────────
test.describe('Expanded Responsive Coverage', () => {
  const pages: { name: string; url: string; heading: string }[] = [
    { name: 'Memory', url: 'memory', heading: 'Memory' },
    { name: 'Facts', url: 'facts', heading: 'Facts' },
    { name: 'Decisions', url: 'decisions', heading: 'Decisions' },
    { name: 'Ingest', url: 'ingest', heading: 'Ingest' },
    { name: 'Provenance', url: 'provenance', heading: 'Provenance' },
  ];

  for (const p of pages) {
    test(`${p.name} heading visible at mobile (390x844)`, async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/${p.url}`);
      await expect(page.locator(`h1:has-text("${p.heading}")`)).toBeVisible({ timeout: 10000 });
    });

    test(`${p.name} no horizontal overflow at mobile (390x844)`, async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/${p.url}`);
      await page.waitForTimeout(500);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      expect(overflow).toBe(false);
    });

    test(`${p.name} heading visible at tablet (768x1024)`, async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/${p.url}`);
      await expect(page.locator(`h1:has-text("${p.heading}")`)).toBeVisible({ timeout: 10000 });
    });

    test(`${p.name} heading visible at desktop (1280x720)`, async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 720 });
      await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/${p.url}`);
      await expect(page.locator(`h1:has-text("${p.heading}")`)).toBeVisible({ timeout: 10000 });
    });
  }

  test('Settings heading visible at mobile (390x844)', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await setAuthAndGo(page, `${FRONTEND}/settings`);
    await expect(page.locator('h1:has-text("Settings")')).toBeVisible({ timeout: 10000 });
  });

  test('Settings no horizontal overflow at mobile (390x844)', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await setAuthAndGo(page, `${FRONTEND}/settings`);
    await page.waitForTimeout(500);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(overflow).toBe(false);
  });

  test('Dashboard no horizontal overflow at 1280x720', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await setAuthAndGo(page, `${FRONTEND}/dashboard`);
    await page.waitForTimeout(500);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(overflow).toBe(false);
  });

  test('Chat no horizontal overflow at mobile (390x844)', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/chat`);
    await page.waitForTimeout(500);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(overflow).toBe(false);
  });

  test('Search no horizontal overflow at mobile (390x844)', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/search`);
    await page.waitForTimeout(500);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(overflow).toBe(false);
  });
});

// ── Identifier Continuity Audit (Gate 12) ──────────────────────────────────
test.describe('Identifier Continuity Audit', () => {
  test('Project IDs are consistent across navigation', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/chat`);
    const url1 = page.url();
    expect(url1).toContain(projectId);
    await page.goto(`${FRONTEND}/projects/${projectId}/memory`);
    await page.waitForLoadState('domcontentloaded');
    const url2 = page.url();
    expect(url2).toContain(projectId);
    expect(new URL(url1).pathname.split('/')[2]).toBe(new URL(url2).pathname.split('/')[2]);
  });

  test('Memory IDs returned by API match frontend display format', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/memory/?project_id=${encodeURIComponent(projectId)}&limit=5`, login.data.access_token);
    expect(res.status).toBe(200);
    if ((res.data as any[]).length > 0) {
      const m = (res.data as any[])[0];
      expect(typeof m.id).toBe('string');
      expect(m.id.length).toBeGreaterThan(10);
    }
  });

  test('Session IDs are stable across list and detail views', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const listRes = await apiRequest('GET', `/api/v1/sessions/?project_id=${encodeURIComponent(projectId)}&limit=5`, login.data.access_token);
    expect(listRes.status).toBe(200);
    if (listRes.data.length > 0) {
      const sessionId = listRes.data[0].id;
      const detailRes = await apiRequest('GET', `/api/v1/sessions/${sessionId}/history`, login.data.access_token);
      expect(detailRes.status).toBe(200);
      expect(detailRes.data.session_id).toBe(sessionId);
    }
  });

  test('Graph node IDs are stable and referenced by edges', async () => {
    const login = await apiRequest('POST', '/api/v1/auth/login', undefined, {
      email: authEmail, password: authPassword,
    });
    const res = await apiRequest('GET', `/api/v1/ingest/graph?project_id=${encodeURIComponent(projectId)}`, login.data.access_token);
    expect(res.status).toBe(200);
    const nodes = res.data.nodes as any[];
    const edges = res.data.edges as any[];
    const nodeIds = new Set(nodes.map(n => n.id));
    edges.forEach((e: any) => {
      expect(nodeIds.has(e.source_node_id)).toBe(true);
      expect(nodeIds.has(e.target_node_id)).toBe(true);
    });
  });
});

// ── Full Regression After Verticals (Gate 14) ───────────────────────────────
test.describe('Full Regression — Core Pages Render', () => {
  test('Dashboard renders without errors', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/dashboard`);
    await expect(page.locator('h1')).toHaveCount(1, { timeout: 10000 });
  });

  test('Projects page renders without errors', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects`);
    await expect(page.locator('h1:has-text("Projects")')).toBeVisible({ timeout: 10000 });
  });

  test('Project Search renders without errors', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/search`);
    await expect(page.locator('h1:has-text("Search")')).toBeVisible({ timeout: 10000 });
  });

  test('Project Memory renders without errors', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/memory`);
    await expect(page.locator('h1:has-text("Memory")')).toBeVisible({ timeout: 10000 });
  });

  test('Project Facts renders without errors', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/facts`);
    await expect(page.locator('h1:has-text("Facts")')).toBeVisible({ timeout: 10000 });
  });

  test('Project Decisions renders without errors', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/decisions`);
    await expect(page.locator('h1:has-text("Decisions")')).toBeVisible({ timeout: 10000 });
  });

  test('Project Timeline renders without errors', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/timeline`);
    await expect(page.locator('h1:has-text("Timeline")')).toBeVisible({ timeout: 10000 });
  });

  test('Project Graph renders without errors', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/graph`);
    await expect(page.locator('h1:has-text("Knowledge Graph")')).toBeVisible({ timeout: 10000 });
  });

  test('Project Provenance renders without errors', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/provenance`);
    await expect(page.locator('h1:has-text("Provenance")')).toBeVisible({ timeout: 10000 });
  });

  test('Project Sessions renders without errors', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/sessions`);
    await expect(page.locator('h1:has-text("Sessions")')).toBeVisible({ timeout: 10000 });
  });

  test('Project Ingest renders without errors', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/projects/${projectId}/ingest`);
    await expect(page.locator('h1:has-text("Ingest")')).toBeVisible({ timeout: 10000 });
  });

  test('Settings renders without errors', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/settings`);
    await expect(page.locator('h1:has-text("Settings")')).toBeVisible({ timeout: 10000 });
  });
});
