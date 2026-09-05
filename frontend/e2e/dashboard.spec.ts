import { test, expect } from '@playwright/test';

const FRONTEND = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';

test.describe('Dashboard Page', () => {
  test('unauthenticated access redirects to login', async ({ page }) => {
    await page.goto(`${FRONTEND}/dashboard`);
    await page.waitForTimeout(2000);
    const onLogin = page.url().includes('/auth/login') ||
      await page.locator('input[type="email"]').count() > 0;
    expect(onLogin).toBeTruthy();
  });
});

test.describe('Projects Page', () => {
  test('unauthenticated access redirects to login', async ({ page }) => {
    await page.goto(`${FRONTEND}/projects`);
    await page.waitForTimeout(2000);
    const onLogin = page.url().includes('/auth/login') ||
      await page.locator('input[type="email"]').count() > 0;
    expect(onLogin).toBeTruthy();
  });
});

test.describe('Settings Page', () => {
  test('unauthenticated access redirects to login', async ({ page }) => {
    await page.goto(`${FRONTEND}/settings`);
    await page.waitForTimeout(2000);
    const onLogin = page.url().includes('/auth/login') ||
      await page.locator('input[type="email"]').count() > 0;
    expect(onLogin).toBeTruthy();
  });
});
