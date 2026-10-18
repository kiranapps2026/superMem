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

test('debug: capture console errors and check auth state', async ({ page }) => {
  const email = `debug6-${uid()}@test.com`;
  const password = 'DebugPass123!';
  const reg = await apiRequest('POST', '/api/v1/auth/register', undefined, {
    email, password, name: 'Debug User', workspace_name: `Debug-WS-${uid()}`,
    password_confirm: password,
  });
  expect(reg.status).toBe(201);

  await page.goto(`${FRONTEND}/auth/login`);
  await page.waitForLoadState('networkidle');
  await page.evaluate((tokens: any) => {
    localStorage.setItem('sv_tokens', JSON.stringify(tokens));
  }, reg.data);

  // Capture ALL console messages
  const consoleMessages: string[] = [];
  page.on('console', (msg) => {
    consoleMessages.push(`[${msg.type()}] ${msg.text()}`);
  });

  // Navigate and wait longer
  await page.goto(`${FRONTEND}/dashboard`);
  await page.waitForTimeout;

  // Check auth state from within the page
  const authState = await page.evaluate(() => {
    const tokensRaw = localStorage.getItem('sv_tokens');
    const tokens = tokensRaw ? JSON.parse(tokensRaw) : null;
    return {
      hasTokens: !!tokens,
      hasAccessToken: !!tokens?.access_token,
      tokenPrefix: tokens?.access_token?.substring(0, 20),
    };
  });

  // Check if there are console errors
  const errors = consoleMessages.filter(m => m.includes('error') || m.includes('Error') || m.includes('ERR_'));
  const allMessages = consoleMessages;

  console.log('=== Auth State ===');
  console.log(JSON.stringify(authState));
  console.log('=== Console Errors ===');
  for (const e of errors) console.log(e);
  console.log('=== All Console Messages ===');
  for (const m of allMessages) console.log(m);
  console.log('=== Final URL ===');
  console.log(page.url());
  console.log('=== Body text ===');
  console.log((await page.locator('body').textContent())?.substring(0, 500));
});
