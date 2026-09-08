import { test, expect } from '@playwright/test';

const FRONTEND = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';

test.beforeEach(async ({ page }) => {
  await page.goto(FRONTEND);
  await page.evaluate(() => localStorage.removeItem('sv_tokens'));
});

test.describe('Authentication Pages', () => {
  test('login page renders with form elements', async ({ page }) => {
    await page.goto(`${FRONTEND}/auth/login`);
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('h1')).toContainText('SwarmVault');
    await expect(page.locator('input[type="email"]')).toHaveCount(1);
    await expect(page.locator('input[type="password"]')).toHaveCount(1);
    await expect(page.getByRole('button', { name: /sign in/i })).toHaveCount(1);
  });

  test('register page link is accessible', async ({ page }) => {
    await page.goto(`${FRONTEND}/auth/login`);
    await page.waitForLoadState('domcontentloaded');
    await expect(page.getByRole('link', { name: /create one/i })).toHaveCount(1);
  });

  test('login with invalid credentials shows error', async ({ page }) => {
    await page.goto(`${FRONTEND}/auth/login`);
    await page.waitForLoadState('domcontentloaded');
    await page.fill('input[type="email"]', 'nonexistent@test.com');
    await page.fill('input[type="password"]', 'wrongpassword');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForLoadState('domcontentloaded');
    // Should remain on login page with error visible
    await expect(page).toHaveURL(new RegExp('/auth/login'));
    await expect(page.getByText('Invalid email or password')).toBeVisible({ timeout: 5000 });
  });

  test('login with empty fields validates', async ({ page }) => {
    await page.goto(`${FRONTEND}/auth/login`);
    await page.waitForLoadState('domcontentloaded');
    // Submit with empty fields — backend should reject with 422
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForLoadState('domcontentloaded');
    // After failed login, we should still be on the login page
    await expect(page).toHaveURL(new RegExp('/auth/login'));
  });

  test('register page renders', async ({ page }) => {
    await page.goto(`${FRONTEND}/auth/register`);
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('h1')).toContainText('Create your account');
    await expect(page.getByText(/create your account/i)).toBeVisible();
    await expect(page.locator('input[type="email"]')).toHaveCount(1);
    await expect(page.locator('input[type="password"]')).toHaveCount(2);
  });

  test('register with mismatched passwords shows error', async ({ page }) => {
    await page.goto(`${FRONTEND}/auth/register`);
    await page.waitForLoadState('domcontentloaded');
    await page.fill('input[placeholder="Jane Doe"]', 'Test User');
    await page.fill('input[type="email"]', `test-${Date.now()}@test.com`);
    await page.fill('input[placeholder="Acme Corp"]', 'Test WS');
    await page.fill('input[placeholder="Min 8 characters"]', 'SecurePass123!');
    await page.locator('input[placeholder="Repeat password"]').fill('DifferentPass123!');
    await expect(page.getByText('Passwords do not match')).toBeVisible();
  });

  test('login link on register page works', async ({ page }) => {
    await page.goto(`${FRONTEND}/auth/register`);
    await page.waitForLoadState('domcontentloaded');
    await page.getByRole('link', { name: /sign in/i }).click();
    await expect(page).toHaveURL(new RegExp('/auth/login'));
  });
});
