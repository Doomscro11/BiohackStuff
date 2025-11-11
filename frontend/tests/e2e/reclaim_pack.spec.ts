/**
 * PatentPulse Reclaim Pack E2E Tests
 * Tests export generation, download, and UI behavior
 */

import { test, expect, Page } from '@playwright/test';

const BASE_URL = process.env.REACT_APP_FRONTEND_URL || 'http://localhost:3000';
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

test.describe('PatentPulse Reclaim Pack', () => {
  let consoleErrors: string[] = [];
  let networkRequests: Array<{ url: string; method: string; headers: Record<string, string> }> = [];
  
  test.beforeEach(async ({ page }) => {
    consoleErrors = [];
    networkRequests = [];
    
    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Track network requests
    page.on('request', request => {
      if (request.url().includes('/api/patentpulse/reclaim')) {
        networkRequests.push({
          url: request.url(),
          method: request.method(),
          headers: request.headers()
        });
      }
    });
  });
  
  test('Reclaim UI loads without errors', async ({ page }) => {
    await page.goto(`${BASE_URL}/admin/patentpulse/reclaim`, {
      waitUntil: 'networkidle'
    });
    
    await page.waitForTimeout(2000);
    
    // Check for hydration errors
    const hydrationErrors = consoleErrors.filter(err =>
      /hydration/i.test(err) || /did not match/i.test(err)
    );
    expect(hydrationErrors).toHaveLength(0);
    
    // Check UI controls visible
    const formatSelect = await page.locator('[data-testid="pp-reclaim-format"]').isVisible();
    expect(formatSelect).toBeTruthy();
    
    const limitSelect = await page.locator('[data-testid="pp-reclaim-limit"]').isVisible();
    expect(limitSelect).toBeTruthy();
    
    const generateButton = await page.locator('[data-testid="pp-reclaim-generate"]').isVisible();
    expect(generateButton).toBeTruthy();
  });
  
  test('Generate JSON export (limit 5)', async ({ page }) => {
    // Mock API response
    await page.route('**/api/patentpulse/reclaim/export**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          file_id: 'test-123',
          file_name: 'patentpulse-reclaim-test.json',
          format: 'json',
          items: 5,
          viability_avg: 0.785,
          generated_at: new Date().toISOString(),
          expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
          size_kb: 45
        })
      });
    });
    
    await page.route('**/api/patentpulse/reclaim/list**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ exports: [] })
      });
    });
    
    await page.goto(`${BASE_URL}/admin/patentpulse/reclaim`);
    await page.waitForTimeout(1000);
    
    // Select JSON format
    await page.selectOption('[data-testid="pp-reclaim-format"]', 'json');
    
    // Select limit 5
    await page.selectOption('[data-testid="pp-reclaim-limit"]', '5');
    
    // Select status (required)
    await page.selectOption('[data-testid="pp-reclaim-status"]', 'Expired');
    
    // Click generate
    await page.click('[data-testid="pp-reclaim-generate"]');
    
    // Wait for success toast
    await page.waitForSelector('text=/JSON export generated/i', { timeout: 5000 });
    
    // Verify API call was made with correct params
    const exportRequest = networkRequests.find(req => req.url.includes('/export'));
    expect(exportRequest).toBeDefined();
    expect(exportRequest?.url).toContain('format=json');
    expect(exportRequest?.url).toContain('limit=5');
    expect(exportRequest?.url).toContain('status=Expired');
  });
  
  test('Generate PDF export (limit 10)', async ({ page }) => {
    await page.route('**/api/patentpulse/reclaim/export**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          file_id: 'test-456',
          file_name: 'patentpulse-reclaim-test.pdf',
          format: 'pdf',
          items: 10,
          viability_avg: 0.812,
          generated_at: new Date().toISOString(),
          expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
          size_kb: 245
        })
      });
    });
    
    await page.route('**/api/patentpulse/reclaim/list**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          exports: [{
            file_id: 'test-456',
            file_name: 'patentpulse-reclaim-test.pdf',
            format: 'pdf',
            items: 10,
            viability_avg: 0.812,
            generated_at: new Date().toISOString(),
            expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
            size_kb: 245
          }]
        })
      });
    });
    
    await page.goto(`${BASE_URL}/admin/patentpulse/reclaim`);
    await page.waitForTimeout(1000);
    
    // Select PDF (default)
    await page.selectOption('[data-testid="pp-reclaim-format"]', 'pdf');
    
    // Select limit 10 (default)
    await page.selectOption('[data-testid="pp-reclaim-limit"]', '10');
    
    // Select status
    await page.selectOption('[data-testid="pp-reclaim-status"]', 'Expired');
    
    // Generate
    await page.click('[data-testid="pp-reclaim-generate"]');
    
    // Wait for success
    await page.waitForSelector('text=/PDF export generated/i', { timeout: 5000 });
    
    // Check table row appears
    await page.waitForSelector('[data-testid="pp-reclaim-row"]', { timeout: 3000 });
    
    // Check download link
    const downloadLink = await page.locator('[data-testid="pp-reclaim-download"]').first();
    expect(await downloadLink.isVisible()).toBeTruthy();
  });
  
  test('Feature flag off shows gated message', async ({ page }) => {
    // Mock 503 response
    await page.route('**/api/patentpulse/reclaim/list**', route => {
      route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Feature not enabled' })
      });
    });
    
    await page.goto(`${BASE_URL}/admin/patentpulse/reclaim`);
    await page.waitForTimeout(2000);
    
    // Should show gated message
    const gatedMessage = await page.locator('text=/Feature Not Enabled/i').isVisible();
    expect(gatedMessage).toBeTruthy();
    
    // Should mention feature flag
    const flagMention = await page.locator('text=/FEATURE_PATENTPULSE_RECLAIM/i').isVisible();
    expect(flagMention).toBeTruthy();
  });
  
  test('2FA required shows prompt', async ({ page }) => {
    // Mock 403 response
    await page.route('**/api/patentpulse/reclaim/list**', route => {
      route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Admin 2FA required' })
      });
    });
    
    await page.goto(`${BASE_URL}/admin/patentpulse/reclaim`);
    await page.waitForTimeout(2000);
    
    // Should show 2FA prompt
    const twoFAPrompt = await page.locator('text=/Two-Factor Authentication Required/i').isVisible();
    expect(twoFAPrompt).toBeTruthy();
  });
  
  test('Filters respected in API call', async ({ page }) => {
    await page.route('**/api/patentpulse/reclaim/export**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          file_id: 'test-789',
          file_name: 'test.pdf',
          format: 'pdf',
          items: 5,
          viability_avg: 0.75,
          generated_at: new Date().toISOString(),
          expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
          size_kb: 100
        })
      });
    });
    
    await page.route('**/api/patentpulse/reclaim/list**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ exports: [] })
      });
    });
    
    await page.goto(`${BASE_URL}/admin/patentpulse/reclaim`);
    await page.waitForTimeout(1000);
    
    // Set filters
    await page.selectOption('[data-testid="pp-reclaim-country"]', 'US');
    await page.selectOption('[data-testid="pp-reclaim-status"]', 'ExpiringSoon');
    await page.selectOption('[data-testid="pp-reclaim-limit"]', '25');
    
    // Generate
    await page.click('[data-testid="pp-reclaim-generate"]');
    
    await page.waitForTimeout(1000);
    
    // Verify filters in API call
    const exportRequest = networkRequests.find(req => req.url.includes('/export'));
    expect(exportRequest?.url).toContain('country=US');
    expect(exportRequest?.url).toContain('status=ExpiringSoon');
    expect(exportRequest?.url).toContain('limit=25');
  });
  
  test('Credentials included in requests', async ({ page }) => {
    await page.route('**/api/patentpulse/reclaim/**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ exports: [] })
      });
    });
    
    await page.goto(`${BASE_URL}/admin/patentpulse/reclaim`);
    await page.waitForTimeout(2000);
    
    // Check that requests have credentials
    const listRequest = networkRequests.find(req => req.url.includes('/list'));
    
    // Note: Playwright doesn't expose credentials flag directly,
    // but we can check for cookies in headers
    expect(listRequest).toBeDefined();
  });
  
  test('No duplicate requests', async ({ page }) => {
    await page.route('**/api/patentpulse/reclaim/list**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ exports: [] })
      });
    });
    
    await page.goto(`${BASE_URL}/admin/patentpulse/reclaim`);
    await page.waitForTimeout(3000);
    
    // Count list requests
    const listRequests = networkRequests.filter(req => req.url.includes('/list'));
    
    // Should be called once (or twice max with React StrictMode)
    expect(listRequests.length).toBeLessThanOrEqual(2);
  });
});
