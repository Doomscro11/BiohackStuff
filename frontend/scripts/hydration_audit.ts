#!/usr/bin/env tsx
/**
 * PatentPulse Hydration & Data-Sync Audit Script
 * Validates frontend hydration, API usage, and data consistency
 * 
 * Usage: npm run audit:hydration
 */

import { chromium, Browser, Page, ConsoleMessage } from 'playwright';

interface AuditResult {
  passed: boolean;
  errors: string[];
  warnings: string[];
  stats: {
    totalRequests: number;
    duplicateRequests: number;
    hydrationErrors: number;
    missingCredentials: number;
    schemaValidationErrors: number;
  };
}

// Patterns to detect in console
const HYDRATION_ERROR_PATTERNS = [
  /hydration failed/i,
  /did not match/i,
  /streaming error/i,
  /mismatched/i,
  /server.*client.*differ/i
];

const API_ERROR_PATTERNS = [
  /response body is already used/i,
  /cannot read properties of undefined/i,
  /unexpected token.*json/i,
  /failed to fetch/i
];

class HydrationAuditor {
  private browser: Browser | null = null;
  private page: Page | null = null;
  private consoleMessages: ConsoleMessage[] = [];
  private networkRequests: Map<string, number> = new Map();
  private apiCallHeaders: Map<string, any> = new Map();
  
  async init() {
    this.browser = await chromium.launch({ headless: true });
    const context = await this.browser.newContext({
      viewport: { width: 1920, height: 1080 }
    });
    
    this.page = await context.newPage();
    
    // Capture console messages
    this.page.on('console', (msg) => {
      this.consoleMessages.push(msg);
    });
    
    // Track network requests
    this.page.on('request', (request) => {
      const url = request.url();
      if (url.includes('/api/patentpulse')) {
        const count = this.networkRequests.get(url) || 0;
        this.networkRequests.set(url, count + 1);
        this.apiCallHeaders.set(url, request.headers());
      }
    });
  }
  
  async auditPage(url: string, pageName: string): Promise<AuditResult> {
    console.log(`\n🔍 Auditing: ${pageName} (${url})`);
    
    const result: AuditResult = {
      passed: true,
      errors: [],
      warnings: [],
      stats: {
        totalRequests: 0,
        duplicateRequests: 0,
        hydrationErrors: 0,
        missingCredentials: 0,
        schemaValidationErrors: 0
      }
    };
    
    // Reset tracking
    this.consoleMessages = [];
    this.networkRequests.clear();
    this.apiCallHeaders.clear();
    
    try {
      // Navigate and wait for network idle
      await this.page!.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
      
      // Wait a bit for React hydration
      await this.page!.waitForTimeout(2000);
      
      // Check console messages for errors
      this.checkConsoleMessages(result);
      
      // Check network requests
      this.checkNetworkRequests(result);
      
      // Check API headers
      this.checkAPIHeaders(result);
      
      // Check for visible content
      await this.checkVisibleContent(result, pageName);
      
      // Determine overall pass/fail
      result.passed = result.errors.length === 0;
      
      // Print results
      this.printResults(pageName, result);
      
    } catch (error: any) {
      result.passed = false;
      result.errors.push(`Navigation/render failed: ${error.message}`);
    }
    
    return result;
  }
  
  private checkConsoleMessages(result: AuditResult) {
    for (const msg of this.consoleMessages) {
      const text = msg.text();
      const type = msg.type();
      
      // Check for hydration errors
      if (HYDRATION_ERROR_PATTERNS.some(pattern => pattern.test(text))) {
        result.stats.hydrationErrors++;
        result.errors.push(`Hydration error: ${text}`);
      }
      
      // Check for API errors
      if (API_ERROR_PATTERNS.some(pattern => pattern.test(text))) {
        result.errors.push(`API error: ${text}`);
      }
      
      // Check for general errors
      if (type === 'error' && !text.includes('[HMR]')) {
        result.warnings.push(`Console error: ${text}`);
      }
    }
  }
  
  private checkNetworkRequests(result: AuditResult) {
    result.stats.totalRequests = this.networkRequests.size;
    
    for (const [url, count] of this.networkRequests.entries()) {
      if (count > 1) {
        result.stats.duplicateRequests++;
        result.warnings.push(`Duplicate request (${count}x): ${url}`);
      }
    }
  }
  
  private checkAPIHeaders(result: AuditResult) {
    for (const [url, headers] of this.apiCallHeaders.entries()) {
      // Check for credentials (Cookie header should be present)
      if (!headers.cookie && !headers.Cookie && !headers.authorization) {
        result.stats.missingCredentials++;
        result.warnings.push(`Missing credentials for: ${url}`);
      }
      
      // For POST/PUT, check Content-Type
      if (url.includes('recompute') || url.includes('POST')) {
        if (!headers['content-type']?.includes('application/json')) {
          result.warnings.push(`Missing Content-Type header for: ${url}`);
        }
      }
    }
  }
  
  private async checkVisibleContent(result: AuditResult, pageName: string) {
    if (!this.page) return;
    
    try {
      if (pageName.includes('patentpulse')) {
        // Check for stats cards
        const statsCards = await this.page.locator('[data-testid*="pp-"], [class*="stat"], [class*="card"]').count();
        if (statsCards === 0) {
          result.warnings.push('No stats cards found on page');
        }
        
        // Check for loading states that never resolve
        const loadingElements = await this.page.locator('[class*="loading"], [class*="skeleton"]').count();
        if (loadingElements > 0) {
          await this.page.waitForTimeout(3000);
          const stillLoading = await this.page.locator('[class*="loading"], [class*="skeleton"]').count();
          if (stillLoading > 0) {
            result.warnings.push(`${stillLoading} loading states never resolved`);
          }
        }
      }
    } catch (error: any) {
      result.warnings.push(`Content visibility check failed: ${error.message}`);
    }
  }
  
  private printResults(pageName: string, result: AuditResult) {
    console.log(`\n📊 Results for ${pageName}:`);
    console.log(`  Status: ${result.passed ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`  Errors: ${result.errors.length}`);
    console.log(`  Warnings: ${result.warnings.length}`);
    console.log(`  Total API requests: ${result.stats.totalRequests}`);
    console.log(`  Duplicate requests: ${result.stats.duplicateRequests}`);
    console.log(`  Hydration errors: ${result.stats.hydrationErrors}`);
    console.log(`  Missing credentials: ${result.stats.missingCredentials}`);
    
    if (result.errors.length > 0) {
      console.log('\n❌ Errors:');
      result.errors.forEach(err => console.log(`  - ${err}`));
    }
    
    if (result.warnings.length > 0) {
      console.log('\n⚠️  Warnings:');
      result.warnings.slice(0, 5).forEach(warn => console.log(`  - ${warn}`));
      if (result.warnings.length > 5) {
        console.log(`  ... and ${result.warnings.length - 5} more`);
      }
    }
  }
  
  async close() {
    if (this.browser) {
      await this.browser.close();
    }
  }
}

async function main() {
  console.log('🚀 PatentPulse Hydration & Data-Sync Audit');
  console.log('=' .repeat(60));
  
  const auditor = new HydrationAuditor();
  await auditor.init();
  
  const baseUrl = process.env.REACT_APP_FRONTEND_URL || 'http://localhost:3000';
  
  // Define pages to audit
  const pages = [
    { url: `${baseUrl}/admin/patentpulse`, name: 'PatentPulse Dashboard' },
    // Add more pages as they're implemented
  ];
  
  const results: AuditResult[] = [];
  
  for (const page of pages) {
    const result = await auditor.auditPage(page.url, page.name);
    results.push(result);
  }
  
  await auditor.close();
  
  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('📋 AUDIT SUMMARY');
  console.log('='.repeat(60));
  
  const totalErrors = results.reduce((sum, r) => sum + r.errors.length, 0);
  const totalWarnings = results.reduce((sum, r) => sum + r.warnings.length, 0);
  const allPassed = results.every(r => r.passed);
  
  console.log(`Total pages audited: ${results.length}`);
  console.log(`Total errors: ${totalErrors}`);
  console.log(`Total warnings: ${totalWarnings}`);
  console.log(`Overall status: ${allPassed ? '✅ PASS' : '❌ FAIL'}`);
  
  // Exit with appropriate code
  process.exit(allPassed && totalErrors === 0 ? 0 : 1);
}

// Run if executed directly
if (require.main === module) {
  main().catch(error => {
    console.error('❌ Audit failed:', error);
    process.exit(1);
  });
}

export { HydrationAuditor };
export type { AuditResult };
