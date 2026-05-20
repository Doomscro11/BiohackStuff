# Authentication Flow Documentation

## Overview

Peptimancer uses a comprehensive authentication system with JWT-based sessions, magic code (OTP) login, and role-based access control (RBAC). This document describes the complete authentication architecture and flow.

## Architecture

### Components

1. **Backend Authentication (`/api/auth`)**
   - Magic code generation and verification
   - JWT token creation and validation
   - Session management
   - Role-based access control

2. **Frontend Guards**
   - `ProtectedRoute`: Wraps authenticated pages
   - `AdminRoute`: Wraps admin-only pages
   - `LoginPage`: OTP-based login UI

3. **Middleware**
   - `AuthMiddleware`: Extracts and validates JWT from requests
   - Auth helpers: `require_auth`, `require_admin`, `require_role`

## Authentication Flow

### 1. Login Process

```
User → /login page
  ↓
Enter email
  ↓
POST /api/auth/magic/request {email}
  ↓
Backend generates 6-digit OTP
  ↓
User receives code (demo mode: shown in response)
  ↓
Enter OTP code
  ↓
POST /api/auth/magic/verify {email, code}
  ↓
Backend validates code
  ↓
JWT token generated with user claims
  ↓
JWT set as HTTP-only cookie (pmnc_jwt)
  ↓
User redirected based on role:
  - Admin → /admin (if returnTo is /)
  - Others → returnTo parameter or /
```

### 2. Session Validation

```
Frontend Route Access
  ↓
ProtectedRoute/AdminRoute component
  ↓
GET /api/auth/session
  ↓
Backend checks JWT cookie
  ↓
Returns {email, role, tier, credits, feature_level}
  ↓
Component checks authentication & role
  ↓
If authenticated & authorized → Render page
If not authenticated → Redirect to /login?returnTo=<path>
If authenticated but not admin → Show Access Denied
```

### 3. Logout Process

```
User clicks Logout
  ↓
POST /api/auth/logout
  ↓
Backend clears pmnc_jwt cookie
  ↓
Frontend redirects to /login
```

## Role-Based Access Control (RBAC)

### User Roles

1. **researcher** (default)
   - Access to core Peptimancer features
   - Can generate analogues
   - Access to billing and credits

2. **admin**
   - All researcher permissions
   - Access to admin dashboard
   - Feature flags management
   - PatentPulse access (with 2FA)
   - Partner share management
   - User analytics

3. **partner** (future)
   - Limited access for external partners
   - Access via share links

### Admin Email Configuration

Admin role is determined by email in `ADMIN_EMAILS` environment variable:
```
ADMIN_EMAILS=founder@peptologic.ai,cto@peptologic.ai
```

### Route Protection Matrix

| Route | Protection | Required Role | Public |
|-------|-----------|---------------|--------|
| `/login` | None | - | ✅ |
| `/share/:token` | None | - | ✅ |
| `/` (HomePage) | ProtectedRoute | Any authenticated | ❌ |
| `/billing` | ProtectedRoute | Any authenticated | ❌ |
| `/admin/analytics` | ProtectedRoute | Any authenticated | ❌ |
| `/admin/patentpulse` | ProtectedRoute | Any authenticated | ❌ |
| `/admin` | AdminRoute | admin | ❌ |

### API Endpoint Protection

| Endpoint | Protection | Required Role | Public |
|----------|-----------|---------------|--------|
| `POST /api/auth/magic/request` | None | - | ✅ |
| `POST /api/auth/magic/verify` | None | - | ✅ |
| `GET /api/auth/session` | JWT | Any authenticated | ❌ |
| `GET /api/billing/state` | JWT | Any authenticated | ❌ |
| `GET /api/chemistry/options` | None (tier-based) | - | ✅ |
| `GET /api/admin/features/flags` | JWT + Role | admin + 2FA | ❌ |
| `GET /api/patentpulse/*` | JWT + Role | admin + 2FA | ❌ |
| `GET /api/patentpulse/partner/share/:token` | Token-based | - | ✅ |

## JWT Structure

### Token Claims

```json
{
  "sub": "user_12345",
  "email": "user@example.com",
  "role": "researcher",
  "orgId": "default",
  "scope": "user",
  "iss": "peptimancer",
  "iat": 1700000000,
  "exp": 1700259200,
  "nbf": 1700000000
}
```

### Token Configuration

- **Issuer**: `JWT_ISSUER` (default: "peptimancer")
- **Secret**: `JWT_SECRET` (required, configured in .env)
- **Expiry**: `JWT_EXPIRES_HOURS` (default: 72 hours)
- **Storage**: HTTP-only cookie named `pmnc_jwt`
- **Cookie Settings**:
  - `httpOnly: true` (prevents XSS)
  - `secure: true` (HTTPS only in production)
  - `sameSite: Lax`
  - `path: /`

## Magic Code (OTP) System

### Code Generation

- 6-digit numeric code
- Random generation using secrets module
- Expires in `OTP_EXPIRES_MINUTES` (default: 10 minutes)
- Stored in `magic_codes` collection

### Rate Limiting

- Max attempts: `MAX_LOGIN_ATTEMPTS` (default: 5)
- Lockout duration: `LOCKOUT_DURATION_MINUTES` (default: 30)
- Tracked per email in `login_attempts` collection

### Demo Mode

When `ENABLE_DEMO_OTP=true`:
- OTP code returned in response for testing
- **MUST BE DISABLED IN PRODUCTION**

## Frontend Auth Integration

### ProtectedRoute Component

```javascript
<ProtectedRoute>
  <HomePage />
</ProtectedRoute>
```

**Behavior:**
1. Checks authentication via `/api/auth/session`
2. Shows loading spinner during check
3. Redirects to `/login?returnTo=<current-path>` if not authenticated
4. Renders children if authenticated

### AdminRoute Component

```javascript
<AdminRoute>
  <AdminPage />
</AdminRoute>
```

**Behavior:**
1. Checks authentication via `/api/auth/session`
2. Shows loading spinner during check
3. Redirects to `/login?returnTo=<current-path>` if not authenticated
4. Shows "Access Denied" page if authenticated but not admin
5. Renders children if authenticated and role === 'admin'

### Session Management

```javascript
// Fetch session on app bootstrap
useEffect(() => {
  fetchSession()
    .then(session => setUser(session))
    .catch(() => setUser(null));
}, []);
```

**Session Data:**
```json
{
  "email": "user@example.com",
  "role": "researcher",
  "tier": "basic",
  "credits": 100,
  "feature_level": 0
}
```

## Backend Auth Helpers

### require_auth

```python
from middleware.auth import require_auth

@router.get("/endpoint")
async def protected_endpoint(user = Depends(require_auth)):
    # user is guaranteed to be authenticated
    return {"user_id": user["id"]}
```

### require_admin

```python
from middleware.auth import require_admin

@router.get("/admin/endpoint")
async def admin_endpoint(user = Depends(require_admin)):
    # user is guaranteed to be authenticated and have admin role
    return {"admin": user["email"]}
```

### require_role

```python
from middleware.auth import require_role

@router.get("/endpoint", dependencies=[Depends(require_role(['admin']))])
async def role_endpoint():
    # Only admin users can access
    return {"data": "admin only"}
```

## Security Features

### 1. HTTP-Only Cookies
- JWT stored in HTTP-only cookie
- Not accessible via JavaScript
- Prevents XSS attacks

### 2. CSRF Protection
- SameSite=Lax cookie setting
- Requests must originate from same site

### 3. Rate Limiting
- Login attempts tracked per email
- Automatic lockout after max attempts
- Prevents brute force attacks

### 4. Token Expiry
- JWTs expire after configured duration
- Requires re-authentication
- Reduces risk of token theft

### 5. 2FA for Admin Actions
- Critical admin operations require 2FA
- TOTP-based verification
- Separate `pmnc_admin2fa` cookie
- 20-minute session for elevated access

## Error Handling

### Authentication Errors

| Error | Status | Description |
|-------|--------|-------------|
| Not Authenticated | 401 | Missing or invalid JWT token |
| Forbidden | 403 | Valid token but insufficient permissions |
| Rate Limited | 429 | Too many login attempts |
| Invalid OTP | 401 | Magic code is invalid or expired |
| Invalid Email | 422 | Email format validation failed |

### Frontend Error States

1. **Loading State**: Spinner while checking authentication
2. **Redirect State**: Automatic redirect to login
3. **Access Denied State**: Error page for insufficient permissions

## Testing

### Backend Tests

```bash
# Test authentication flow
curl -X POST $API_BASE/auth/magic/request \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

curl -X POST $API_BASE/auth/magic/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","code":"123456"}'

# Test session endpoint
curl -X GET $API_BASE/auth/session \
  -H "Cookie: pmnc_jwt=<token>"
```

### Frontend Tests

1. Access protected route without auth → redirects to login
2. Login with valid OTP → sets cookie and redirects
3. Access admin route as non-admin → shows access denied
4. Logout → clears cookie and redirects to login

## Migration Notes

### Adding New Protected Routes

1. **Frontend**: Wrap with `<ProtectedRoute>` or `<AdminRoute>`
```javascript
<Route path="/new-page" element={<ProtectedRoute><NewPage /></ProtectedRoute>} />
```

2. **Backend**: Add auth dependency
```python
@router.get("/api/new-endpoint")
async def new_endpoint(user = Depends(require_auth)):
    return {"data": "protected"}
```

### Adding New Roles

1. Update role assignment logic in `services/auth_service.py`
2. Add role to `require_role` checks
3. Update frontend navigation conditional rendering
4. Test with appropriate user accounts

## Troubleshooting

### Issue: Users can't log in
- Check `ENABLE_DEMO_OTP` is enabled for testing
- Verify `ADMIN_EMAILS` is correctly set
- Check `JWT_SECRET` is configured
- Review login attempt rate limits

### Issue: Session expires too quickly
- Increase `JWT_EXPIRES_HOURS` in .env
- Check system time synchronization

### Issue: Admin features not accessible
- Verify user email is in `ADMIN_EMAILS`
- Check JWT claims include correct role
- Test 2FA verification flow

### Issue: CORS errors
- Verify backend CORS settings
- Check `credentials: 'include'` in frontend requests
- Ensure cookies are set with correct domain

## Security Checklist

- [ ] `JWT_SECRET` is strong and unique
- [ ] `ENABLE_DEMO_OTP=false` in production
- [ ] `REQUIRE_HTTPS_COOKIES=true` in production
- [ ] Admin emails are correctly configured
- [ ] Rate limiting is enabled
- [ ] JWT expiry is appropriate for use case
- [ ] 2FA is required for sensitive admin operations
- [ ] Audit logs are enabled for admin actions

## Future Enhancements

1. **Remember Me**: Optional long-lived sessions
2. **Multi-Factor Options**: SMS, email, authenticator app
3. **Social Login**: OAuth integration (Google, GitHub)
4. **Session Management**: View and revoke active sessions
5. **Password Option**: Alternative to magic codes
6. **API Keys**: Programmatic access for integrations

## References

- JWT: https://jwt.io/
- OWASP Auth Cheatsheet: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
- React Router Guards: https://reactrouter.com/en/main
