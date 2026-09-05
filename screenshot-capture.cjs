const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const FRONTEND = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';
const API = 'http://localhost:8000';
const OUTPUT_DIR = path.resolve(__dirname, 'screenshots');

if (!fs.existsSync(OUTPUT_DIR)) fs.mkdirSync(OUTPUT_DIR, { recursive: true });

async function apiRequest(method, endpoint, token, body) {
  const headers = { 'Content-Type': 'application/json', 'X-E2E': 'true' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API}${endpoint}`, {
    method, headers, body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let data = text;
  try { data = JSON.parse(text); } catch {}
  return { status: res.status, data };
}

async function main() {
  // First, register and login via API to get a token
  const unique = Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  const email = `ss-${unique}@test.com`;
  const password = 'Screenshot123!';

  console.log('Registering test user...');
  const reg = await apiRequest('POST', '/api/v1/auth/register', null, {
    email, password, name: 'Screenshot User', workspace_name: `SS-WS-${unique}`,
  });
  if (reg.status !== 201) { console.error('Register failed:', reg.status, reg.data); process.exit(1); }

  const login = await apiRequest('POST', '/api/v1/auth/login', null, { email, password });
  if (login.status !== 200) { console.error('Login failed:', login.status, login.data); process.exit(1); }
  const token = login.data.access_token;

  // Create project
  const proj = await apiRequest('POST', '/api/v1/projects/', token, { name: 'Screenshot Project', description: 'For screenshots' });
  if (proj.status !== 201) { console.error('Project creation failed:', proj.status, proj.data); process.exit(1); }
  const projectId = proj.data.id;
  console.log('Project ID:', projectId);

  // Use two browser contexts: one unauthenticated, one authenticated
  const browser = await chromium.launch({ headless: true });

  // Authenticated context with pre-seeded localStorage
  const authContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await authContext.addInitScript((tok) => {
    localStorage.setItem('sv_tokens', JSON.stringify({ access_token: tok, refresh_token: '' }));
  }, token);
  const authPage = await authContext.newPage();

  // Unauthenticated context (no init script)
  const unauthContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const unauthPage = await unauthContext.newPage();

  async function captureAuth(url, filename, label, waitMs = 2500) {
    await authPage.goto(`${FRONTEND}${url}`);
    await authPage.waitForTimeout(waitMs);
    await authPage.screenshot({ path: path.join(OUTPUT_DIR, filename), fullPage: false });
    console.log(`  [OK] ${label} → ${filename}`);
  }

  async function captureUnauth(url, filename, label, waitMs = 2500) {
    await unauthPage.goto(`${FRONTEND}${url}`);
    await unauthPage.waitForTimeout(waitMs);
    await unauthPage.screenshot({ path: path.join(OUTPUT_DIR, filename), fullPage: false });
    console.log(`  [OK] ${label} → ${filename}`);
  }

  // ── 01: Landing Page (unauthenticated) ──
  await captureUnauth('/auth/login', '01-landing.png', 'Landing / Login page');

  // ── 02: Registration Page ──
  await captureUnauth('/auth/register', '02-register.png', 'Registration page');

  // ── 03: Dashboard (Empty) ──
  await captureAuth('/dashboard', '03-dashboard-empty.png', 'Dashboard empty', 3000);

  // ── 04: Dashboard (With Project) ──
  await captureAuth('/dashboard', '04-dashboard-with-projects.png', 'Dashboard with projects', 3000);

  // ── 05: Projects Page ──
  await captureAuth('/projects', '05-projects-page.png', 'Projects page', 3000);

  // ── 06: Sidebar Expanded ──
  await captureAuth(`/projects/${projectId}/chat`, '06-sidebar-expanded.png', 'Sidebar expanded', 3000);

  // ── 07: Sidebar Collapsed ──
  await authPage.goto(`${FRONTEND}/projects/${projectId}/chat`);
  await authPage.waitForTimeout;
  const menuBtn = await authPage.locator('aside button').first();
  if (await menuBtn.count() > 0) {
    await menuBtn.click();
    await authPage.waitForTimeout;
  }
  await authPage.screenshot({ path: path.join(OUTPUT_DIR, '07-sidebar-collapsed.png'), fullPage: false });
  console.log('  [OK] 07-sidebar-collapsed.png');

  // ── 08: Chat Empty ──
  await captureAuth(`/projects/${projectId}/chat`, '08-chat-empty.png', 'Chat empty', 3000);

  // ── 09: Chat With Messages ──
  await authPage.goto(`${FRONTEND}/projects/${projectId}/chat`);
  await authPage.waitForTimeout;
  const textarea = await authPage.locator('textarea').first();
  if (await textarea.count() > 0) {
    await textarea.fill('What is SwarmVault?');
    await authPage.waitForTimeout;
    const sendBtn = await authPage.getByRole('button', { name: /send/i }).first();
    if (await sendBtn.count() > 0) {
      await sendBtn.click();
      await authPage.waitForTimeout;
    }
  }
  await authPage.screenshot({ path: path.join(OUTPUT_DIR, '09-chat-with-messages.png'), fullPage: false });
  console.log('  [OK] 09-chat-with-messages.png');

  // ── 10: Ingest Empty ──
  await captureAuth(`/projects/${projectId}/ingest`, '10-ingest-empty.png', 'Ingest empty', 3000);

  // ── 11: Ingest With Sources ──
  await apiRequest('POST', '/api/v1/ingest/upload', token, {
    project_id: projectId,
    content: JSON.stringify({ mapping: { n1: { message: { author: { role: 'user' }, content: { parts: ['Test content'] }, create_time: 1700000000 } } } }),
    source_type: 'chatgpt',
    title: 'Sample ChatGPT Conversation',
  });
  await captureAuth(`/projects/${projectId}/ingest`, '11-ingest-with-sources.png', 'Ingest with sources', 3000);

  // ── 12: Memory Page ──
  await captureAuth(`/projects/${projectId}/memory`, '12-memory-page.png', 'Memory page', 3000);

  // ── 13: Search Page ──
  await captureAuth(`/projects/${projectId}/search`, '13-search-page.png', 'Search page', 3000);

  // ── 14: Graph Page ──
  await captureAuth(`/projects/${projectId}/graph`, '14-graph-page.png', 'Knowledge Graph', 3000);

  // ── 15: Timeline Page ──
  await captureAuth(`/projects/${projectId}/timeline`, '15-timeline-page.png', 'Timeline page', 3000);

  // ── 16: Facts Page ──
  await captureAuth(`/projects/${projectId}/facts`, '16-facts-page.png', 'Facts page', 3000);

  // ── 17: Decisions Page ──
  await captureAuth(`/projects/${projectId}/decisions`, '17-decisions-page.png', 'Decisions page', 3000);

  // ── 18: Sessions Page ──
  await captureAuth(`/projects/${projectId}/sessions`, '18-sessions-page.png', 'Sessions page', 3000);

  // ── 19: Session Detail ──
  const sessions = await apiRequest('GET', `/api/v1/sessions/?project_id=${projectId}`, token);
  let sessionId = null;
  if (sessions.status === 200 && sessions.data?.items?.length > 0) {
    sessionId = sessions.data.items[0].id;
  }
  const sessUrl = sessionId ? `/projects/${projectId}/sessions/${sessionId}` : `/projects/${projectId}/sessions`;
  await captureAuth(sessUrl, '19-session-detail.png', 'Session detail', 3000);

  // ── 20: Provenance Page ──
  await captureAuth(`/projects/${projectId}/provenance`, '20-provenance-page.png', 'Provenance page', 3000);

  // ── 21: API Keys Page ──
  await captureAuth('/settings/api-keys', '21-api-keys.png', 'API Keys', 3000);

  // ── 22: Storage Page ──
  await captureAuth('/settings/storage', '22-storage.png', 'Storage', 3000);

  // ── 23: Settings Profile (default tab) ──
  await captureAuth('/settings', '23-settings-profile.png', 'Settings Profile', 3000);

  // ── 24: Settings Members ──
  await authPage.goto(`${FRONTEND}/settings`);
  await authPage.waitForTimeout;
  const membersTab = await authPage.getByRole('tab', { name: /members/i }).first();
  if (await membersTab.count() > 0) {
    await membersTab.click();
    await authPage.waitForTimeout;
  }
  await authPage.screenshot({ path: path.join(OUTPUT_DIR, '24-settings-members.png'), fullPage: false });
  console.log('  [OK] 24-settings-members.png');

  // ── 25: Settings Invitations ──
  await authPage.goto(`${FRONTEND}/settings`);
  await authPage.waitForTimeout;
  const inviteTab = await authPage.getByRole('tab', { name: /invitation/i }).first();
  if (await inviteTab.count() > 0) {
    await inviteTab.click();
    await authPage.waitForTimeout;
  }
  await authPage.screenshot({ path: path.join(OUTPUT_DIR, '25-settings-invitations.png'), fullPage: false });
  console.log('  [OK] 25-settings-invitations.png');

  // ── 26: Project Settings ──
  await captureAuth(`/projects/${projectId}/settings`, '26-project-settings.png', 'Project Settings', 3000);

  // ── 27: Evidence Modal ──
  await authPage.goto(`${FRONTEND}/projects/${projectId}/chat`);
  await authPage.waitForTimeout;
  const whyBtn = await authPage.getByRole('button', { name: /why this answer|evidence/i }).first();
  if (await whyBtn.count() > 0) {
    await whyBtn.click();
    await authPage.waitForTimeout;
  }
  await authPage.screenshot({ path: path.join(OUTPUT_DIR, '27-evidence-modal.png'), fullPage: false });
  console.log('  [OK] 27-evidence-modal.png');

  // ── 28: Error States ──
  await captureAuth('/dashboard', '28-error-states.png', 'Dashboard (reference)', 2000);

  // ── Summary ──
  console.log('\nAll screenshots captured to:', OUTPUT_DIR);
  const files = fs.readdirSync(OUTPUT_DIR).filter(f => f.endsWith('.png')).sort();
  console.log(`Total: ${files.length} screenshots`);
  files.forEach(f => {
    const stat = fs.statSync(path.join(OUTPUT_DIR, f));
    console.log(`  - ${f} (${(stat.size / 1024).toFixed(1)} KB)`);
  });

  await browser.close();
}

main().catch(err => { console.error(err); process.exit(1); });
