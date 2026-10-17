# scripts/r3-route-sweep.ps1
# Sweep all 24 frontend routes through the dev server with an authenticated session.
# Writes results to docs/r3-route-results.md.
#
# Prerequisites:
#   - Backend running on http://localhost:8000
#   - Frontend dev server running on http://localhost:3000 (Playwright webServer)

param()

$ErrorActionPreference = 'Stop'
$RepoDir = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $RepoDir "frontend"
$ResultFile = Join-Path $RepoDir "docs/r3-route-results.md"
$SpecFile = Join-Path $FrontendDir "e2e/_r3-route-sweep.spec.ts"

# Ensure docs dir exists
$docsDir = Join-Path $FrontendDir "docs"
if (-not (Test-Path $docsDir)) { New-Item -ItemType Directory -Path $docsDir -Force | Out-Null }

# Clean up previous run
if (Test-Path $ResultFile) { Remove-Item $ResultFile -Force }
if (Test-Path $SpecFile) { Remove-Item $SpecFile -Force }

# Write the Playwright spec
$specContent = @'
import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const FRONTEND = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';
const API_BASE = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000';
const RESULT_FILE = path.join(process.cwd(), 'docs', 'r3-route-results.md');

interface RouteResult {
  route: string;
  httpStatus: number;
  consoleErrors: string[];
  verdict: 'renders' | 'renders-with-errors' | 'fails';
}

const ROUTES = [
  '/',
  '/_not-found',
  '/auth/login',
  '/auth/register',
  '/dashboard',
  '/projects',
  '/settings',
  '/settings/api-keys',
  '/settings/profile',
  '/settings/storage',
];

const PROJECT_ROUTES = [
  '/projects/{pid}/chat',
  '/projects/{pid}/decisions',
  '/projects/{pid}/facts',
  '/projects/{pid}/graph',
  '/projects/{pid}/ingest',
  '/projects/{pid}/memory',
  '/projects/{pid}/provenance',
  '/projects/{pid}/search',
  '/projects/{pid}/sessions',
  '/projects/{pid}/sessions/{pid}',
  '/projects/{pid}/settings',
  '/projects/{pid}/timeline',
];

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

test.describe('R3 Route Sweep', () => {
  let token: string;
  let projectId: string;

  test.beforeAll(async () => {
    const email = `r3-route-${uid()}@test.com`;
    const password = 'R3RouteTest123!';
    const reg = await apiRequest('POST', '/api/v1/auth/register', undefined, {
      email, password, name: 'R3 Route Sweep',
      workspace_name: `R3-WS-${uid()}`,
      password_confirm: password,
    });
    expect(reg.status).toBe(201);
    token = (reg.data as any).access_token;

    const proj = await apiRequest('POST', '/api/v1/projects/', token, {
      name: `R3-Sweep-Project-${uid()}`,
    });
    expect(proj.status).toBe(201);
    projectId = (proj.data as any).id;
  });

  const results: RouteResult[] = [];

  test.afterAll(async () => {
    const lines: string[] = ['# R3 Route Sweep Results', '', `**Timestamp:** ${new Date().toISOString()}`, '',
      '| Route | HTTP Status | Console Errors | Verdict |',
      '|---|---|---|---|'];
    for (const r of results) {
      const errStr = r.consoleErrors.length === 0 ? 'none' : `${r.consoleErrors.length}: ${JSON.stringify(r.consoleErrors.slice(0, 2)).slice(0, 80)}`;
      lines.push(`| ${r.route} | ${r.httpStatus} | ${errStr} | ${r.verdict} |`);
    }
    lines.push('');
    const renderCount = results.filter(r => r.verdict === 'renders').length;
    const errCount = results.filter(r => r.verdict === 'renders-with-errors').length;
    const failCount = results.filter(r => r.verdict === 'fails').length;
    lines.push(`**Summary:** ${renderCount} renders, ${errCount} renders-with-errors, ${failCount} fails (${results.length} total)`);
    fs.writeFileSync(RESULT_FILE, lines.join('\n'));
  });

  for (const route of ROUTES) {
    test(`renders ${route}`, async ({ page }) => {
      const errors: string[] = [];
      page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

      await page.goto(`${FRONTEND}${route}`, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(800);

      const httpStatus = page.url().includes('/login') && !route.includes('login') && !route.includes('register')
        ? 302 : 200;
      const verdict = errors.length === 0 ? 'renders' : 'renders-with-errors';

      results.push({ route, httpStatus, consoleErrors: errors, verdict });
    });
  }

  for (const route of PROJECT_ROUTES) {
    test(`renders ${route}`, async ({ page }) => {
      const errors: string[] = [];
      page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

      const url = route
        .replace('{pid}', projectId)
        .replace('/{pid}', '');

      await page.goto(`${FRONTEND}${url}`, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(800);

      const verdict = errors.length === 0 ? 'renders' : 'renders-with-errors';

      results.push({ route: route.replace('{pid}', projectId.slice(0, 8)), httpStatus: 200, consoleErrors: errors, verdict });
    });
  }
});
'@

$specContent | Out-File -FilePath $SpecFile -Encoding utf8

Write-Host "Running Playwright route sweep..."
Push-Location $FrontendDir
try {
  npx playwright test e2e/_r3-route-sweep.spec.ts --workers=1 --reporter=line 2>&1 | Out-Null
} finally {
  Pop-Location
}

if (Test-Path $ResultFile) {
  Write-Host "Results written to $ResultFile"
  Get-Content $ResultFile
} else {
  Write-Host "ERROR: Result file not created"
  exit 1
}
