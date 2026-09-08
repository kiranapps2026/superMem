import { test, expect } from '@playwright/test';

const FRONTEND = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';

test.describe('Dashboard Page', () => {
  test('unauthenticated access redirects to login', async ({ page }) => {
    await page.goto(`${FRONTEND}/dashboard`);
    await page.waitForURL(/\/auth\/login/, { timeout: 10000 });
    await expect(page.locator('h1')).toContainText('SwarmVault');
  });

  test('Projects page unauthenticated access redirects', async ({ page }) => {
    await page.goto(`${FRONTEND}/projects`);
    await page.waitForURL(/\/auth\/login/, { timeout: 10000 });
    await expect(page.locator('h1')).toContainText('SwarmVault');
  });

  test('Settings page unauthenticated access redirects', async ({ page }) => {
    await page.goto(`${FRONTEND}/settings`);
    await page.waitForURL(/\/auth\/login/, { timeout: 10000 });
    await expect(page.locator('h1')).toContainText('SwarmVault');
  });
});
