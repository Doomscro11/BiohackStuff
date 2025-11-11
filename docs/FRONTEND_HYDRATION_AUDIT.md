# Frontend Hydration & Data-Sync Audit

## Overview

This document describes the hydration and data-sync audit system for the Peptimancer frontend, specifically for the PatentPulse module. The audit ensures:

1. **No Hydration Errors**: React hydration completes without mismatches
2. **Correct API Usage**: All API calls include proper credentials and headers
3. **Single Response Read**: Response bodies are never read twice
4. **No Duplicate Requests**: Each endpoint called once per render cycle
5. **Valid Data Schemas**: API responses match expected TypeScript types

## Quick Start

### Prerequisites

```bash
# Install dependencies
cd frontend
yarn install

# Install Playwright browsers
npx playwright install --with-deps chromium
```

### Running Audits Locally

```bash
# Full audit suite
yarn audit:hydration

# Unit tests only
yarn test:unit

# E2E tests only
yarn test:e2e

# All tests
yarn test
```

## Audit Components

### 1. Hydration Audit Script (`scripts/hydration_audit.ts`)

**Purpose**: Automated headless browser audit that checks for hydration errors, API usage, and rendering issues.

**What it checks**:
- Console errors matching hydration patterns
- "Response body already used" errors
- Duplicate network requests
- Missing credentials in API calls
- Visible content rendering

**Usage**:
```bash
npm run audit:hydration

# With custom URL
REACT_APP_FRONTEND_URL=http://localhost:3000 npm run audit:hydration
```

**Exit codes**:
- `0`: All checks passed
- `1`: Failures detected

### 2. Playwright E2E Tests (`tests/e2e/patentpulse_hydration.spec.ts`)

**Purpose**: End-to-end tests for PatentPulse pages with focus on hydration and data loading.

**Test coverage**:
- Dashboard loads without hydration errors
- API calls include credentials
- No duplicate requests
- Stats cards render with data
- Error states handled gracefully
- Navigation works without errors

**Usage**:
```bash
# Run all e2e tests
npx playwright test

# Run with UI
npx playwright test --ui

# Run specific test
npx playwright test -g "hydration errors"

# Debug mode
npx playwright test --debug
```

**Viewing reports**:
```bash
# Open HTML report
npx playwright show-report playwright-report

# View traces (on failure)
npx playwright show-trace test-results/[test-name]/trace.zip
```

### 3. Unit Tests (`tests/unit/patentpulse_api.spec.ts`)

**Purpose**: Unit tests for API module functions to ensure correct request configuration.

**Test coverage**:
- `credentials: 'include'` present
- Content-Type headers set correctly
- Response body read exactly once
- Error handling without double-reads
- Query parameters built correctly

**Usage**:
```bash
# Run unit tests
npm run test:unit

# With coverage
npm run test:unit -- --coverage

# Watch mode
npm run test:unit -- --watch
```

## Common Issues & Remediation

### Issue 1: "Response body is already used"

**Symptoms**:
- Console error: `Failed to execute 'clone' on 'Response': Response body is already used`
- Happens when loading PatentPulse pages

**Root cause**:
- Response object's body (stream) can only be read once
- Attempting to call both `.json()` and `.text()` on same response
- Or calling `.json()` twice

**Fix**:
```typescript
// ❌ WRONG - reads body twice
const response = await fetch(url);
const data = await response.json();
const text = await response.text(); // Error!

// ✅ CORRECT - read once, store result
const response = await fetch(url);
if (response.ok) {
  const data = await response.json(); // Read once
  return { ok: true, data };
} else {
  const text = await response.text(); // Read once
  return { ok: false, text, status: response.status };
}
```

**Verify fix**:
```bash
# Should show 0 body-related errors
npm run audit:hydration
```

### Issue 2: Hydration Mismatch

**Symptoms**:
- Warning: `Text content did not match. Server: "X" Client: "Y"`
- UI flickers on load
- Content appears then disappears

**Root cause**:
- Server-rendered HTML differs from client-rendered HTML
- Often caused by:
  - Date/time formatting differences
  - Random values
  - Browser-only APIs (localStorage, window)

**Fix**:
```typescript
// ❌ WRONG - uses Date.now() which differs server/client
const timestamp = Date.now();

// ✅ CORRECT - suppress hydration warning or use useEffect
const [timestamp, setTimestamp] = useState(null);
useEffect(() => {
  setTimestamp(Date.now());
}, []);
```

**Verify fix**:
```bash
# Check for hydration errors in console
npx playwright test -g "hydration"
```

### Issue 3: Missing Credentials

**Symptoms**:
- API returns 401 Unauthorized
- User appears logged out on PatentPulse pages

**Root cause**:
- `credentials: 'include'` not set in fetch options
- Cookies not sent with cross-origin requests

**Fix**:
```typescript
// ❌ WRONG - no credentials
fetch(url, { method: 'GET' })

// ✅ CORRECT - include credentials
fetch(url, { 
  method: 'GET',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' }
})
```

**Verify fix**:
```bash
# Unit tests check for credentials
npm run test:unit
```

### Issue 4: Duplicate Requests

**Symptoms**:
- Same API endpoint called multiple times
- Network tab shows 2+ identical requests
- Slower page loads

**Root cause**:
- React StrictMode (double-renders in dev)
- Multiple useEffect hooks
- Parent and child both fetching

**Fix**:
```typescript
// ✅ Use proper dependency array
useEffect(() => {
  let cancelled = false;
  
  const load = async () => {
    const result = await getPatentStats();
    if (!cancelled && result.ok) {
      setStats(result.data);
    }
  };
  
  load();
  
  return () => { cancelled = true; };
}, []); // Empty deps = run once
```

**Verify fix**:
```bash
# Check for duplicate request warnings
npm run audit:hydration
```

### Issue 5: Schema Validation Failures

**Symptoms**:
- TypeScript errors: `Property 'X' does not exist on type 'Y'`
- Runtime errors: `Cannot read property of undefined`

**Root cause**:
- API response shape changed
- Backend/frontend types out of sync

**Fix**:
1. Check backend response:
```bash
curl -s http://localhost:8001/api/patentpulse/stats | jq
```

2. Update TypeScript types:
```typescript
// In src/lib/types.ts
export interface PatentStats {
  total: number;
  by_status: Record<string, number>;
  // Add new fields here
}
```

3. Update API expectations in tests

**Verify fix**:
```bash
# Type check
npm run typecheck

# E2E schema validation
npx playwright test -g "valid JSON"
```

## CI/CD Integration

### GitHub Actions Workflow

File: `.github/workflows/frontend-hydration-ci.yml`

**Triggers**:
- Push to main/develop
- Pull requests to main/develop
- Only when frontend files change

**Steps**:
1. TypeScript type check
2. Build frontend
3. Run unit tests
4. Run E2E tests with Playwright
5. Run hydration audit
6. Upload artifacts on failure

**Artifacts**:
- `playwright-report/`: HTML test report
- `test-results/`: Traces and screenshots
- `coverage/`: Unit test coverage

**Viewing CI results**:
1. Go to GitHub Actions tab
2. Select the workflow run
3. Download artifacts if tests failed
4. Open `playwright-report/index.html` locally

### Local Pre-commit Checks

Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
cd frontend
npm run typecheck || exit 1
npm run test:unit || exit 1
echo "✅ Pre-commit checks passed"
```

## Monitoring in Production

### Browser Console Monitoring

Add to your frontend:
```javascript
if (process.env.NODE_ENV === 'production') {
  window.addEventListener('error', (event) => {
    if (event.message.includes('hydration')) {
      // Log to monitoring service
      console.error('Hydration error in production:', event);
    }
  });
}
```

### Performance Monitoring

Track key metrics:
- Time to first paint
- Time to interactive
- API response times
- Error rates

## Checklist for New Features

Before merging PatentPulse changes:

- [ ] No console errors in browser DevTools
- [ ] `npm run typecheck` passes
- [ ] `npm run test:unit` passes
- [ ] `npm run test:e2e` passes
- [ ] `npm run audit:hydration` passes
- [ ] Manual test: Navigate to `/admin/patentpulse` and verify data loads
- [ ] Manual test: Hard refresh (Ctrl+Shift+R) - no hydration warnings
- [ ] CI workflow green

## Troubleshooting

### Tests timing out

**Problem**: E2E tests timeout waiting for page load

**Solution**:
```bash
# Increase timeout in playwright.config.ts
use: {
  actionTimeout: 15000, // Increase from 10000
  navigationTimeout: 45000, // Increase from 30000
}
```

### Mock server issues

**Problem**: Tests fail with 404 errors

**Solution**: Ensure mock server is running and returns expected responses
```bash
# Start mock manually
node tests/mocks/server.js &
```

### Playwright installation fails

**Problem**: `npx playwright install` fails

**Solution**:
```bash
# Install system dependencies
npx playwright install-deps

# Or install specific browser
npx playwright install chromium
```

## Best Practices

1. **Always use `fetchJSON` from `lib/http.ts`** - ensures consistent credentials/headers
2. **Read response body exactly once** - use conditional logic, not multiple reads
3. **Add data-testid attributes** for easier E2E testing
4. **Mock API responses in tests** - don't rely on live backend
5. **Run audit before committing** - catch issues early

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Jest Documentation](https://jestjs.io)
- [React Hydration Guide](https://react.dev/reference/react-dom/client/hydrateRoot)
- [Fetch API MDN](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)

## Maintainers

- Peptimancer Platform Team
- Last Updated: 2025-11-11
