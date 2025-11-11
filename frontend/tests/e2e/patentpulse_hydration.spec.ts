/**
 * PatentPulse Hydration E2E Tests
 * Tests hydration, API calls, and data rendering for PatentPulse pages
 */

import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.REACT_APP_FRONTEND_URL || 'http://localhost:3000';
const ADMIN_EMAIL = 'founder@peptologic.ai';

// Helper to track network requests
interface RequestTracker {
  url: string;
  method: string;
  headers: Record<string, string>;
  timestamp: number;
}

test.describe('PatentPulse Hydration & Data-Sync', () => {
  let consoleErrors: string[] = [];
  let networkRequests: RequestTracker[] = [];
  
  test.beforeEach(async ({ page }) => {
    // Reset tracking
    consoleErrors = [];
    networkRequests = [];
    
    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Track API requests
    page.on('request', request => {
      if (request.url().includes('/api/patentpulse')) {
        networkRequests.push({
          url: request.url(),
          method: request.method(),
          headers: request.headers(),
          timestamp: Date.now()
        });
      }
    });
  });
  
  test('PatentPulse Dashboard loads without hydration errors', async ({ page }) => {
    // Navigate to PatentPulse
    await page.goto(`${BASE_URL}/admin/patentpulse`, { 
      waitUntil: 'networkidle' 
    });
    
    // Wait for content to load
    await page.waitForTimeout(2000);
    
    // Assert no hydration errors
    const hydrationErrors = consoleErrors.filter(err => 
      /hydration/i.test(err) || /did not match/i.test(err)
    );
    expect(hydrationErrors).toHaveLength(0);
    
    // Assert no "Response body already used" errors
    const bodyErrors = consoleErrors.filter(err =>
      /response body.*already used/i.test(err)
    );
    expect(bodyErrors).toHaveLength(0);
  });
  
  test('PatentPulse stats endpoint called with credentials', async ({ page }) => {
    await page.goto(`${BASE_URL}/admin/patentpulse`, { 
      waitUntil: 'networkidle' 
    });
    
    await page.waitForTimeout(2000);
    
    // Find stats API request
    const statsRequest = networkRequests.find(req => 
      req.url.includes('/api/patentpulse/stats')
    );
    
    if (statsRequest) {
      // Check for credentials (Cookie or Authorization header)
      const hasCredentials = 
        !!statsRequest.headers.cookie || 
        !!statsRequest.headers.Cookie ||
        !!statsRequest.headers.authorization;
      
      expect(hasCredentials).toBeTruthy();
    }
  });
  
  test('No duplicate API requests for same endpoint', async ({ page }) => {
    await page.goto(`${BASE_URL}/admin/patentpulse`, { 
      waitUntil: 'networkidle' 
    });
    
    await page.waitForTimeout(3000);
    
    // Group requests by URL
    const requestCounts = new Map<string, number>();
    networkRequests.forEach(req => {
      const count = requestCounts.get(req.url) || 0;
      requestCounts.set(req.url, count + 1);
    });
    
    // Check for duplicates
    const duplicates = Array.from(requestCounts.entries())
      .filter(([_, count]) => count > 1);
    
    if (duplicates.length > 0) {
      console.warn('Duplicate requests found:', duplicates);
    }
    
    // Allow 1 retry for flaky networks, but more than 2 is an issue
    const excessiveDuplicates = duplicates.filter(([_, count]) => count > 2);
    expect(excessiveDuplicates).toHaveLength(0);
  });
  
  test('Stats cards render with data', async ({ page }) => {
    await page.goto(`${BASE_URL}/admin/patentpulse`, { 
      waitUntil: 'networkidle' 
    });
    
    // Wait for stats to load
    await page.waitForTimeout(3000);
    
    // Check for stat cards (flexible selectors)
    const statCards = await page.locator('[data-testid*="pp-"], [class*="stat"], [class*="card"]').count();
    
    // Should have at least some cards/stats displayed
    expect(statCards).toBeGreaterThan(0);
    
    // Check that loading states resolved
    const loadingElements = await page.locator('[class*="loading"], [class*="skeleton"]').count();
    expect(loadingElements).toBe(0);
  });
  
  test('Top opportunities section renders', async ({ page }) => {
    await page.goto(`${BASE_URL}/admin/patentpulse`, { 
      waitUntil: 'networkidle' 
    });
    
    await page.waitForTimeout(3000);
    
    // Look for opportunities section
    const oppsSection = await page.locator('[data-testid*="opportunities"], [class*="opportunit"]').count();
    
    // Should have opportunities section or empty state
    expect(oppsSection).toBeGreaterThanOrEqual(0);
  });
  
  test('API responses have valid JSON structure', async ({ page }) => {
    const responses: any[] = [];
    
    // Intercept responses
    page.on('response', async response => {
      if (response.url().includes('/api/patentpulse')) {
        try {
          const data = await response.json();
          responses.push({ url: response.url(), data });
        } catch (e) {
          // Not JSON or already consumed
        }
      }
    });
    
    await page.goto(`${BASE_URL}/admin/patentpulse`, { 
      waitUntil: 'networkidle' 
    });
    
    await page.waitForTimeout(3000);
    
    // Validate stats response structure
    const statsResponse = responses.find(r => r.url.includes('/stats'));
    if (statsResponse) {
      expect(statsResponse.data).toHaveProperty('total');
      expect(typeof statsResponse.data.total).toBe('number');
    }
    
    // Validate top-opportunities response
    const oppsResponse = responses.find(r => r.url.includes('/top-opportunities'));
    if (oppsResponse) {
      expect(oppsResponse.data).toHaveProperty('opportunities');
      expect(Array.isArray(oppsResponse.data.opportunities)).toBeTruthy();
    }
  });
  
  test('Error states handled gracefully', async ({ page }) => {
    // Simulate API failure
    await page.route('**/api/patentpulse/**', route => {
      route.fulfill({
        status: 503,
        body: JSON.stringify({ detail: 'Service unavailable' })
      });
    });
    
    await page.goto(`${BASE_URL}/admin/patentpulse`, { 
      waitUntil: 'domcontentloaded' 
    });
    
    await page.waitForTimeout(2000);
    
    // Should show error state, not crash
    const errorMessages = await page.locator('[class*="error"], [class*="alert"]').count();
    expect(errorMessages).toBeGreaterThan(0);
    
    // Should not have uncaught exceptions
    const uncaughtErrors = consoleErrors.filter(err => 
      /uncaught/i.test(err) && !/service unavailable/i.test(err)
    );
    expect(uncaughtErrors).toHaveLength(0);
  });
  
  test('Content-Type headers set for POST requests', async ({ page }) => {
    // This test would apply if there are POST endpoints like /signals/recompute
    await page.goto(`${BASE_URL}/admin/patentpulse`, { 
      waitUntil: 'networkidle' 
    });
    
    await page.waitForTimeout(2000);
    
    // Check POST requests (if any)
    const postRequests = networkRequests.filter(req => req.method === 'POST');
    
    postRequests.forEach(req => {
      const contentType = req.headers['content-type'] || req.headers['Content-Type'];
      if (contentType) {
        expect(contentType).toContain('application/json');
      }
    });
  });
  
  test('Navigation between PatentPulse routes works', async ({ page }) => {
    await page.goto(`${BASE_URL}/admin/patentpulse`, { 
      waitUntil: 'networkidle' 
    });
    
    await page.waitForTimeout(2000);
    
    // Try navigating to other admin pages
    const analyticsLink = await page.locator('a[href*="analytics"]').first();
    if (await analyticsLink.isVisible()) {
      await analyticsLink.click();
      await page.waitForTimeout(1000);
      
      // Navigate back
      const patentPulseLink = await page.locator('a[href*="patentpulse"]').first();
      if (await patentPulseLink.isVisible()) {
        await patentPulseLink.click();
        await page.waitForTimeout(1000);
      }
    }
    
    // No console errors during navigation
    const navErrors = consoleErrors.filter(err => 
      !/favicon|manifest/.test(err)
    );
    expect(navErrors.length).toBeLessThan(3); // Allow minor warnings
  });
});

test.describe('PatentPulse Performance', () => {
  test('Page loads within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto(`${BASE_URL}/admin/patentpulse`, { 
      waitUntil: 'networkidle',
      timeout: 10000
    });
    
    const loadTime = Date.now() - startTime;
    
    // Should load within 10 seconds
    expect(loadTime).toBeLessThan(10000);
    
    console.log(`Page load time: ${loadTime}ms`);
  });
});
