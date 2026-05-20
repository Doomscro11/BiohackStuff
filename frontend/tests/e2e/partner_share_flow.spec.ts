/**
 * E2E Test: Partner Share Flow (Phase IXf+)
 * 
 * Tests the complete partner share lifecycle:
 * 1. Admin creates share
 * 2. Partner accesses share link
 * 3. Partner downloads file
 * 4. Analytics counters increment
 * 5. Admin revokes share
 * 6. Partner sees revoked error
 */

import { test, expect } from '@playwright/test';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const ADMIN_EMAIL = 'founder@peptologic.ai';

test.describe('Partner Share Flow', () => {
  let shareToken: string;
  let shareUrl: string;

  test('Admin can create a partner share', async ({ page }) => {
    // Navigate to admin page
    await page.goto('/admin');

    // Login with magic code
    await page.fill('input[type="email"]', ADMIN_EMAIL);
    await page.click('button:has-text("Send Magic Code")');

    // Wait for demo code to appear (in demo mode)
    await page.waitForSelector('text=/\\d{6}/');
    const demoCode = await page.textContent('[data-testid="demo-code"]') || '';
    const code = demoCode.match(/\d{6}/)?.[0] || '';

    // Enter code
    await page.fill('input[placeholder*="code"]', code);
    await page.click('button:has-text("Verify")');

    // Wait for admin panel to load
    await expect(page.locator('text="Admin Panel"')).toBeVisible();

    // Navigate to Partner Shares
    await page.click('a:has-text("Partner Shares")');

    // Click Create Share button
    await page.click('[data-testid="pp-partner-create"]');

    // Fill out form
    await page.selectOption('select[name="file_id"]', { index: 1 }); // Select first export
    await page.fill('input[name="recipient_email"]', 'partner@test.com');
    await page.fill('input[name="recipient_first_name"]', 'Test');
    await page.fill('input[name="company_or_project"]', 'Test Company');
    await page.fill('input[name="expires_in_days"]', '14');
    await page.fill('input[name="max_downloads"]', '5');

    // Submit form
    await page.click('button:has-text("Create Share")');

    // Wait for success message
    await expect(page.locator('text=/Share created/')).toBeVisible({ timeout: 10000 });

    // Extract share URL from alert or success message
    const alertText = await page.evaluate(() => {
      return (window as any).lastAlert || '';
    });

    const urlMatch = alertText.match(/https?:\/\/[^\s]+/);
    if (urlMatch) {
      shareUrl = urlMatch[0];
      shareToken = shareUrl.split('/share/')[1];
    }

    expect(shareUrl).toBeTruthy();
  });

  test('Partner can view share metadata', async ({ page }) => {
    test.skip(!shareUrl, 'Requires shareUrl from previous test');

    await page.goto(shareUrl);

    // Check for welcome message
    await expect(page.locator('h2:has-text("Welcome")')).toBeVisible();

    // Check for file info
    await expect(page.locator('text="Downloads Remaining"')).toBeVisible();
    await expect(page.locator('text="Expires"')).toBeVisible();

    // Check for download button
    await expect(page.locator('[data-testid="pp-partner-download"]')).toBeVisible();
  });

  test('Partner can download file', async ({ page }) => {
    test.skip(!shareUrl, 'Requires shareUrl from previous test');

    await page.goto(shareUrl);

    // Set up download listener
    const downloadPromise = page.waitForEvent('download');

    // Click download button
    await page.click('[data-testid="pp-partner-download"]');

    // Wait for download
    const download = await downloadPromise;
    expect(download).toBeTruthy();
    expect(download.suggestedFilename()).toMatch(/\.pdf$/);

    // Verify downloads counter updated
    await page.reload();
    await expect(page.locator('text=/1.*of.*5/')).toBeVisible();
  });

  test('Admin can view analytics', async ({ page }) => {
    test.skip(!shareToken, 'Requires shareToken from create test');

    // Login as admin
    await page.goto('/admin');
    // ... (login flow as in first test)

    // Navigate to Partner Shares
    await page.click('a:has-text("Partner Shares")');

    // Find the share row and click analytics
    const shareRow = page.locator(`tr:has-text("partner@test.com")`);
    await shareRow.locator('button[title="View Analytics"]').click();

    // Verify analytics modal
    await expect(page.locator('text="Share Analytics"')).toBeVisible();
    await expect(page.locator('text="Opens"')).toBeVisible();
    await expect(page.locator('text="Downloads"')).toBeVisible();

    // Verify counters are > 0
    const downloadsValue = await page.locator('.metric-value:has-text("1")').count();
    expect(downloadsValue).toBeGreaterThan(0);
  });

  test('Admin can revoke share', async ({ page }) => {
    test.skip(!shareToken, 'Requires shareToken from create test');

    // Login as admin
    await page.goto('/admin');
    // ... (login flow)

    // Navigate to Partner Shares
    await page.click('a:has-text("Partner Shares")');

    // Find the share row and click revoke
    const shareRow = page.locator(`tr:has-text("partner@test.com")`);
    await shareRow.locator('[data-testid="pp-partner-revoke"]').click();

    // Confirm revocation
    await page.fill('input[placeholder*="reason"]', 'Test revocation');
    await page.click('button:has-text("Confirm")');

    // Verify share is revoked
    await expect(shareRow.locator('text="revoked"')).toBeVisible();
  });

  test('Partner sees revoked error after revocation', async ({ page }) => {
    test.skip(!shareUrl, 'Requires shareUrl from previous test');

    await page.goto(shareUrl);

    // Should see revoked error
    await expect(page.locator('text=/revoked/i')).toBeVisible();
    await expect(page.locator('text=/This share link has been revoked/')).toBeVisible();

    // Download button should not be clickable
    const downloadButton = page.locator('[data-testid="pp-partner-download"]');
    if (await downloadButton.isVisible()) {
      await expect(downloadButton).toBeDisabled();
    }
  });

  test('Policy enforcement: max downloads', async ({ page }) => {
    // This would require creating a new share with max_downloads=1
    // and downloading twice to test enforcement
    test.skip('TODO: Implement max downloads test');
  });

  test('Policy enforcement: expiry', async ({ page }) => {
    // This would require creating a share with expires_in_days=0
    // or manipulating the database
    test.skip('TODO: Implement expiry test');
  });

  test('Policy enforcement: IP allowlist', async ({ page }) => {
    // This would require creating a share with IP allowlist
    // and accessing from different IP
    test.skip('TODO: Implement IP allowlist test');
  });

  test('Rate limiting prevents excessive requests', async ({ page }) => {
    test.skip('TODO: Implement rate limiting test');
  });
});
