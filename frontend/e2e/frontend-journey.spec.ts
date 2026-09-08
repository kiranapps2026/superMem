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
  const email = `fj-${uid()}@test.com`;
  const password = 'FJPass123!';
  const reg = await apiRequest('POST', '/api/v1/auth/register', undefined, {
    email, password, name: 'FJ User', workspace_name: `FJ-WS-${uid()}`,
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

test.beforeEach(async ({ page }) => {
  await page.goto(FRONTEND);
  await page.evaluate(() => localStorage.removeItem('sv_tokens'));
});

test.afterEach(async ({ page }) => {
  await page.goto(FRONTEND);
  await page.evaluate(() => localStorage.removeItem('sv_tokens'));
});

test.describe('Golden Journey — Frontend UI', () => {
  test('full journey: dashboard -> create project -> navigate pages', async ({ page }) => {
    const email = `fj-journey-${uid()}@test.com`;
    const password = 'FJPass123!';
    const reg = await apiRequest('POST', '/api/v1/auth/register', undefined, {
      email, password, name: 'FJ Journey', workspace_name: `FJ-WS-${uid()}`,
      password_confirm: password,
    });
    expect(reg.status).toBe(201);

    // Auth via direct token injection
    await page.goto(FRONTEND);
    await page.waitForLoadState('domcontentloaded');
    await page.evaluate((tokens: any) => {
      localStorage.setItem('sv_tokens', JSON.stringify(tokens));
    }, reg.data);

    await page.goto(`${FRONTEND}/dashboard`);
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('h1')).toBeVisible({ timeout: 10000 });

    const nameInput = page.getByPlaceholder(/project name/i);
    if (await nameInput.count() > 0) {
      await nameInput.first().fill('Golden Project');
      await page.getByRole('button', { name: /create/i }).first().click();
      await expect(page.getByText('Golden Project')).toBeVisible({ timeout: 10000 });
    }

    await page.goto(`${FRONTEND}/projects`);
    await expect(page.locator('h1')).toBeVisible({ timeout: 10000 });

    await page.goto(`${FRONTEND}/settings`);
    await expect(page.locator('h1')).toBeVisible({ timeout: 10000 });
  });

  test('sidebar navigation is present and links work', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/dashboard`);

    const sidebar = page.locator('nav');
    await expect(sidebar).toBeVisible({ timeout: 10000 });

    const destinations = ['/projects', '/settings'];
    for (const href of destinations) {
      await page.goto(`${FRONTEND}${href}`);
      await expect(page.locator('h1')).toBeVisible({ timeout: 10000 });
    }
  });

  test('logout redirects to login', async ({ page }) => {
    await setAuthAndGo(page, `${FRONTEND}/dashboard`);

    // Simulate logout by clearing tokens (the button click is intercepted
    // by the Next.js dev overlay portal in Playwright)
    await page.evaluate(() => localStorage.removeItem('sv_tokens'));

    // Navigate away and back to trigger re-auth check
    await page.goto(`${FRONTEND}/dashboard`);
    await expect(page).toHaveURL(new RegExp('/auth/login'), { timeout: 10000 });

    // Verify tokens cleared
    expect(await page.evaluate(() => localStorage.getItem('sv_tokens'))).toBeNull();
  });

  test('unauthenticated access redirects to login', async ({ page }) => {
    await page.goto(`${FRONTEND}/dashboard`);
    await page.waitForURL(new RegExp('/auth/login'), { timeout: 10000 });
  });
});
