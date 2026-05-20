# Smoke Test Guide - Global Login & RBAC

## Overview

This document provides step-by-step smoke tests to verify the authentication and authorization system is working correctly after deployment.

## Prerequisites

- Access to the application URL
- Two test accounts:
  - **Non-admin**: `test@example.com` (or any non-admin email)
  - **Admin**: `founder@peptologic.ai` or `cto@peptologic.ai`
- Demo mode enabled (`ENABLE_DEMO_OTP=true`) for testing

---

## Test 1: Non-Admin User Flow

### Objective
Verify that non-admin users can:
- Log in successfully
- Access protected routes
- Cannot access admin routes

### Steps

1. **Navigate to login page**
   - URL: `https://your-app.com/login`
   - ✅ **Expected**: Login page displays with email input

2. **Request magic code**
   - Enter email: `test@example.com`
   - Click "Send Magic Code"
   - ✅ **Expected**: "Enter 6-Digit Code" screen appears
   - ✅ **Expected** (Demo Mode): Yellow banner shows "Your code: XXXXXX"

3. **Verify magic code**
   - Enter the 6-digit code from banner
   - Click "Verify & Sign In"
   - ✅ **Expected**: Redirected to home page (`/`)

4. **Check navigation links**
   - ✅ **Expected Links Visible**:
     - Billing & Credits
     - Analytics
     - PatentPulse
     - Logout
   - ❌ **Expected Link NOT Visible**:
     - Admin (should be hidden for non-admin)

5. **Access protected routes**
   - Navigate to `/billing`
   - ✅ **Expected**: Billing page loads successfully
   
   - Navigate to `/admin/analytics`
   - ✅ **Expected**: Analytics page loads successfully

6. **Try to access admin route**
   - Navigate to `/admin`
   - ✅ **Expected**: "Access Denied" page with message:
     - "You don't have permission to access this page. Admin access is required."
     - "Go to Home" button present

7. **Test logout**
   - Click "Logout" button
   - ✅ **Expected**: Redirected to `/login`
   
   - Try accessing `/billing` directly
   - ✅ **Expected**: Redirected to `/login?returnTo=%2Fbilling`

### Result Summary

| Check | Status | Notes |
|-------|--------|-------|
| Login flow | ⬜ | |
| Protected routes accessible | ⬜ | |
| Admin route blocked | ⬜ | |
| Navigation links correct | ⬜ | |
| Logout working | ⬜ | |

---

## Test 2: Admin User Flow

### Objective
Verify that admin users can:
- Log in successfully
- Access all protected routes
- Access admin-only routes
- See admin navigation link

### Steps

1. **Navigate to login page**
   - URL: `https://your-app.com/login`
   - ✅ **Expected**: Login page displays

2. **Request magic code**
   - Enter email: `founder@peptologic.ai`
   - Click "Send Magic Code"
   - ✅ **Expected**: Code entry screen appears
   - ✅ **Expected** (Demo Mode): Demo code displayed

3. **Verify magic code**
   - Enter the 6-digit code
   - Click "Verify & Sign In"
   - ✅ **Expected**: Redirected to `/admin` (admin default landing)

4. **Check navigation links**
   - ✅ **Expected Links Visible**:
     - Billing & Credits
     - Analytics
     - PatentPulse
     - **Admin** (should be visible for admin)
     - Logout

5. **Access admin routes**
   - Navigate to `/admin`
   - ✅ **Expected**: Admin page loads with feature flags panel
   
   - Navigate to `/admin/analytics`
   - ✅ **Expected**: Analytics page loads
   
   - Navigate to `/admin/patentpulse`
   - ✅ **Expected**: PatentPulse page loads

6. **Access regular protected routes**
   - Navigate to `/`
   - ✅ **Expected**: Home page loads
   
   - Navigate to `/billing`
   - ✅ **Expected**: Billing page loads

7. **Test logout**
   - Click "Logout"
   - ✅ **Expected**: Redirected to `/login`
   
   - Try accessing `/admin`
   - ✅ **Expected**: Redirected to `/login?returnTo=%2Fadmin`

### Result Summary

| Check | Status | Notes |
|-------|--------|-------|
| Admin login flow | ⬜ | |
| Admin routes accessible | ⬜ | |
| Regular routes accessible | ⬜ | |
| Admin link visible | ⬜ | |
| Logout working | ⬜ | |

---

## Test 3: Public Routes

### Objective
Verify that public routes are accessible without authentication

### Steps

1. **Access login page (not logged in)**
   - Navigate to `/login`
   - ✅ **Expected**: Login page displays (no redirect)

2. **Access partner share link (not logged in)**
   - Navigate to `/share/test-token-123`
   - ✅ **Expected**: Share page displays (even if token is invalid)
   - ❌ **Should NOT**: Redirect to login

3. **Access protected route (not logged in)**
   - Navigate to `/` directly
   - ✅ **Expected**: Redirected to `/login?returnTo=%2F`

4. **Access admin route (not logged in)**
   - Navigate to `/admin` directly
   - ✅ **Expected**: Redirected to `/login?returnTo=%2Fadmin`

### Result Summary

| Check | Status | Notes |
|-------|--------|-------|
| Login page public | ⬜ | |
| Share links public | ⬜ | |
| Protected routes blocked | ⬜ | |
| Admin routes blocked | ⬜ | |

---

## Test 4: Session Persistence

### Objective
Verify that authentication state persists across page navigation and refreshes

### Steps

1. **Log in as non-admin user**
   - Complete login flow with `test@example.com`
   - ✅ **Expected**: Logged in successfully

2. **Navigate between protected routes**
   - Go to `/billing`
   - Go to `/admin/analytics`
   - Go to `/` (home)
   - ✅ **Expected**: No login prompts, all pages load correctly

3. **Refresh page**
   - On any protected page, press F5 (refresh)
   - ✅ **Expected**: Page reloads, still authenticated (no redirect to login)

4. **Open new tab**
   - Open new tab in same browser
   - Navigate to `/billing`
   - ✅ **Expected**: Billing page loads (session shared across tabs)

5. **Logout from one tab**
   - In one tab, click "Logout"
   - ✅ **Expected**: Redirected to `/login`
   
   - In other tab, try to navigate
   - ✅ **Expected**: Redirected to `/login` (session cleared globally)

### Result Summary

| Check | Status | Notes |
|-------|--------|-------|
| Route navigation preserves session | ⬜ | |
| Page refresh preserves session | ⬜ | |
| Session shared across tabs | ⬜ | |
| Logout clears global session | ⬜ | |

---

## Test 5: Edge Cases

### Objective
Verify proper handling of error conditions

### Steps

1. **Invalid email format**
   - Navigate to `/login`
   - Enter: `not-an-email`
   - Click "Send Magic Code"
   - ✅ **Expected**: Email validation error OR 422 error from backend

2. **Invalid OTP code**
   - Request magic code for `test@example.com`
   - Enter wrong code: `000000`
   - Click "Verify & Sign In"
   - ✅ **Expected**: Error message: "Invalid or expired code"
   - ✅ **Expected**: Code input cleared, stays on verification screen

3. **Expired OTP (if possible)**
   - Request magic code
   - Wait 10+ minutes (OTP_EXPIRES_MINUTES)
   - Try to verify code
   - ✅ **Expected**: Error message: "Invalid or expired code"

4. **Access after logout**
   - Log in successfully
   - Navigate to `/billing`
   - Logout
   - Use browser back button
   - ✅ **Expected**: Redirected to `/login` (not cached page)

5. **Direct URL access**
   - When not logged in, paste URL: `/admin/analytics`
   - ✅ **Expected**: Redirected to `/login?returnTo=%2Fadmin%2Fanalytics`
   - After login, should redirect back to `/admin/analytics`

### Result Summary

| Check | Status | Notes |
|-------|--------|-------|
| Invalid email handled | ⬜ | |
| Invalid OTP handled | ⬜ | |
| Expired OTP handled | ⬜ | |
| Post-logout access blocked | ⬜ | |
| ReturnTo parameter working | ⬜ | |

---

## Test 6: CORS Configuration

### Objective
Verify that CORS is properly configured and credentials work

### Steps

1. **Check browser console (Dev Tools)**
   - Open browser DevTools (F12)
   - Navigate to login page
   - Check Console tab
   - ❌ **Should NOT see**: `blocked by CORS policy` errors

2. **Check Network tab**
   - Open Network tab in DevTools
   - Request magic code
   - Check request to `/api/auth/magic/request`
   - ✅ **Expected Response Headers**:
     - `Access-Control-Allow-Origin: <your-origin>`
     - `Access-Control-Allow-Credentials: true`

3. **Verify cookie storage**
   - Complete login flow
   - Check Application tab → Cookies
   - ✅ **Expected**: Cookie named `pmnc_jwt` present
   - ✅ **Expected Attributes**:
     - HttpOnly: ✓
     - Secure: ✓ (in production)
     - SameSite: Lax

### Result Summary

| Check | Status | Notes |
|-------|--------|-------|
| No CORS errors | ⬜ | |
| CORS headers correct | ⬜ | |
| JWT cookie set properly | ⬜ | |

---

## Automated Test Script (Optional)

For CI/CD environments, you can automate these tests:

```python
#!/usr/bin/env python3
"""
Smoke test script for Global Login & RBAC
Usage: python smoke_test.py <base_url>
Example: python smoke_test.py https://app.peptimancer.com
"""

import requests
import sys

def test_login_flow(base_url):
    """Test basic login flow"""
    print("Testing login flow...")
    
    # Request magic code
    response = requests.post(
        f"{base_url}/api/auth/magic/request",
        json={"email": "test@example.com"}
    )
    assert response.status_code == 200, "Magic code request failed"
    data = response.json()
    
    # In demo mode, code is in response
    if 'demo_code' in data:
        code = data['demo_code']
        print(f"  ✅ Magic code received: {code}")
        
        # Verify code
        verify_response = requests.post(
            f"{base_url}/api/auth/magic/verify",
            json={"email": "test@example.com", "code": code}
        )
        assert verify_response.status_code == 200, "Code verification failed"
        print("  ✅ Login successful")
        
        # Get JWT cookie
        jwt_cookie = verify_response.cookies.get('pmnc_jwt')
        assert jwt_cookie, "JWT cookie not set"
        print("  ✅ JWT cookie received")
        
        return jwt_cookie
    else:
        print("  ⚠️  Demo mode not enabled, cannot test login")
        return None

def test_protected_endpoint(base_url, jwt_cookie):
    """Test protected endpoint access"""
    print("Testing protected endpoint...")
    
    # Without auth - should fail
    response = requests.get(f"{base_url}/api/billing/state")
    assert response.status_code == 401, "Protected endpoint should return 401 without auth"
    print("  ✅ Returns 401 without auth")
    
    # With auth - should succeed
    cookies = {'pmnc_jwt': jwt_cookie}
    response = requests.get(f"{base_url}/api/billing/state", cookies=cookies)
    assert response.status_code == 200, "Protected endpoint should return 200 with auth"
    print("  ✅ Returns 200 with auth")

def test_admin_endpoint(base_url, jwt_cookie):
    """Test admin endpoint access"""
    print("Testing admin endpoint (expect 403 for non-admin)...")
    
    cookies = {'pmnc_jwt': jwt_cookie}
    response = requests.get(f"{base_url}/api/admin/features/flags", cookies=cookies)
    assert response.status_code in [403, 401], f"Expected 403 or 401, got {response.status_code}"
    print(f"  ✅ Returns {response.status_code} for non-admin user")

def main():
    if len(sys.argv) < 2:
        print("Usage: python smoke_test.py <base_url>")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    print(f"Running smoke tests against: {base_url}\n")
    
    try:
        jwt = test_login_flow(base_url)
        if jwt:
            test_protected_endpoint(base_url, jwt)
            test_admin_endpoint(base_url, jwt)
        
        print("\n✅ All smoke tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## Production Hardening Checklist

Before considering the system production-ready:

- [ ] Set `ENABLE_DEMO_OTP=false` in production `.env`
- [ ] Verify `JWT_SECRET` is strong (32+ bytes) and unique
- [ ] Confirm `ADMIN_EMAILS` contains only authorized admin emails
- [ ] Set `CORS_ORIGINS` to production frontend URL(s) only (no localhost)
- [ ] Verify all origins use HTTPS in production
- [ ] Test all smoke test scenarios above
- [ ] Confirm JWT cookies have `Secure` flag in production
- [ ] Document any additional admin emails for future reference

---

## Quick Smoke Test (Manual)

**Time: 5 minutes**

1. ✅ Login as non-admin → Can access home, billing, analytics
2. ✅ Non-admin cannot access `/admin`
3. ✅ Login as admin → Can access all routes including `/admin`
4. ✅ Logout → Session cleared, redirected to login
5. ✅ No CORS errors in browser console

If all 5 checks pass → System is ready ✅

---

## Troubleshooting

### Issue: OTP not working
- Check `ENABLE_DEMO_OTP=true` in `.env`
- Restart backend: `sudo supervisorctl restart backend`
- Check backend logs: `tail -f /var/log/supervisor/backend.out.log`

### Issue: CORS errors
- Check `CORS_ORIGINS` includes your frontend URL
- Restart backend after changing `.env`
- See [CORS_SETUP.md](./CORS_SETUP.md) for details

### Issue: Session not persisting
- Check browser cookies - `pmnc_jwt` should be present
- Verify cookie attributes (HttpOnly, SameSite=Lax)
- Check JWT_SECRET is set correctly

### Issue: Admin access not working
- Verify admin email is in `ADMIN_EMAILS` environment variable
- Check logs during login to confirm role assignment
- Admin routes may require 2FA (return 403) - this is by design

---

## Related Documentation

- [AUTH_FLOW.md](./AUTH_FLOW.md) - Complete authentication architecture
- [CORS_SETUP.md](./CORS_SETUP.md) - CORS configuration guide
- [test_result.md](../test_result.md) - Automated test results

---

**Last Updated**: 2025-11-22  
**Version**: 1.0  
**Tested Against**: refactor/monorepo-structure branch
