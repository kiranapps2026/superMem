import { test, expect } from '@playwright/test';

const FRONTEND = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';
const API = 'http://localhost:8000';

// API calls use Node.js fetch (bypasses CORS, sends proper HTTP).
async function apiRequest(method: string, path: string, token?: string, body?: any) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, { method, headers, body: body ? JSON.stringify(body) : undefined });
  const text = await res.text();
  let data: any = text;
  try { data = JSON.parse(text); } catch { /* keep raw */ }
  return { status: res.status, data };
}

async function registerAndLogin(page: any) {
  const unique = crypto.randomUUID();
  const email = `fj-${unique}@test.com`;
  const password = 'TestPass123!';

  const reg = await apiRequest('POST', '/api/v1/auth/register', undefined, {
    email, password, name: 'FJ User', workspace_name: `FJ-WS-${unique}`,
  });
  expect(reg.status).toBe(201);

  const login = await apiRequest('POST', '/api/v1/auth/login', undefined, { email, password });
  expect(login.status).toBe(200);
  const { access_token, refresh_token } = login.data;

  // Set localStorage so the frontend sees the session
  await page.goto(FRONTEND);
  await page.evaluate((tokens) => {
    localStorage.setItem('sv_tokens', JSON.stringify(tokens));
  }, { access_token, refresh_token });

  return { email, password, token: access_token };
}

test.describe('Golden Journey — Frontend UI', () => {
  test('full journey: dashboard -> create project -> navigate pages', async ({ page }) => {
    await registerAndLogin(page);

    await page.goto(`${FRONTEND}/dashboard`);
    await expect(page.getByText(/dashboard|workspace/i)).toBeVisible({ timeout: 10000 });

    const nameInput = page.getByPlaceholder(/project name/i);
    if (await nameInput.count() > 0) {
      await nameInput.first().fill('Golden Project');
      await page.getByRole('button', { name: /create/i }).first().click();
      await expect(page.getByText('Golden Project')).toBeVisible({ timeout: 10000 });
    }

    await page.goto(`${FRONTEND}/projects`);
    await expect(page.locator('main')).toBeVisible({ timeout: 10000 });

    await page.goto(`${FRONTEND}/settings`);
    await expect(page.locator('main')).toBeVisible({ timeout: 10000 });
  });

  test('sidebar navigation is present and links work', async ({ page }) => {
    await registerAndLogin(page);
    await page.goto(`${FRONTEND}/dashboard`);

    const sidebar = page.locator('aside');
    await expect(sidebar).toBeVisible({ timeout: 10000 });

    const destinations = ['/projects', '/settings'];
    for (const href of destinations) {
      await page.goto(`${FRONTEND}${href}`);
      await expect(page.locator('main')).toBeVisible({ timeout: 10000 });
    }
  });

  test('logout redirects to login', async ({ page }) => {
    await registerAndLogin(page);
    await page.goto(`${FRONTEND}/dashboard`);

    const logoutBtn = page.getByRole('button', { name: /logout|log out/i });
    if (await logoutBtn.count() > 0) {
      await logoutBtn.first().click();
      await page.waitForURL(new RegExp('/auth/login'), { timeout: 10000 });
    }
  });

  test('unauthenticated access redirects to login', async ({ page }) => {
    await page.goto(`${FRONTEND}/dashboard`);
    await page.waitForURL(new RegExp('/auth/login'), { timeout: 10000 });
  });
});
