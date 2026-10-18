import { test, expect } from '@playwright/test';

const FRONTEND = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';
const API_BASE = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000';

test('debug: check what nav looks like', async ({ page }) => {
  // Register
  const reg = await fetch(`${API_BASE}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-E2E': 'true' },
    body: JSON.stringify({ email: `diag-${Date.now()}@test.com`, password: 'DiagPass123!', name: 'Diag', workspace_name: `Diag-WS-${Date.now()}`, password_confirm: 'DiagPass123!' }),
  });
  const regData = await reg.json();
  console.log('REG:', JSON.stringify(regData).slice(0, 200));

  await page.goto(`${FRONTEND}/auth/login`);
  await page.waitForLoadState('domcontentloaded');
  console.log('After goto login, URL:', page.url());
  
  await page.evaluate((tokens: any) => {
    localStorage.setItem('sv_tokens', JSON.stringify(tokens));
  }, { access_token: regData.access_token, refresh_token: regData.refresh_token });
  
  console.log('Tokens injected, navigating to dashboard');
  await page.goto(`${FRONTEND}/dashboard`);
  
  // Wait for network idle to let auth/me resolve
  await page.waitForLoadState('networkidle', { timeout: 15000 });
  console.log('After goto dashboard, URL:', page.url());
  
  // Check what's in the DOM
  const html = await page.content();
  console.log('Has nav:', html.includes('<nav'));
  console.log('Has button New Project:', html.includes('New Project'));
  console.log('Has h1:', html.includes('<h1'));
  
  // Try to find nav by different selectors
  const navCount = await page.locator('nav').count();
  console.log('Nav count:', navCount);
  
  const bodyText = await page.locator('body').textContent();
  console.log('Body text:', bodyText?.slice(0, 500));
});
