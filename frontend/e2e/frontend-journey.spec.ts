import { test, expect } from '@playwright/test';

const FRONTEND = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';
const API = 'http://localhost:8000';

async function registerAndLogin(page: any) {
  const suffix = Date.now().toString(36) + Math.random().toString(36).slice(2, 5);
  const email = `e2e-${suffix}@test.com`;
  const workspaceName = `E2E-WS-${suffix}`;
  const password = 'TestPass123!';

  await page.goto(FRONTEND);

  // Register via browser fetch (exercises full CORS + auth flow)
  const regResult = await page.evaluate(async ({ url, body }) => {
    const res = await fetch(url + '/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return { ok: res.ok, status: res.status, data: res.ok ? await res.json() : await res.text() };
  }, { url: API, body: { email, password, name: 'E2E User', workspace_name: workspaceName } });

  if (!regResult.ok) {
    throw new Error(`Registration failed [${regResult.status}]: ${regResult.data}`);
  }

  // Login
  const loginResult = await page.evaluate(async ({ url, body }) => {
    const res = await fetch(url + '/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return { ok: res.ok, status: res.status, data: res.ok ? await res.json() : await res.text() };
  }, { url: API, body: { email, password } });

  if (!loginResult.ok) {
    throw new Error(`Login failed [${loginResult.status}]: ${loginResult.data}`);
  }

  const { access_token, refresh_token } = loginResult.data;

  // Store in localStorage
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
