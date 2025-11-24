# CORS Configuration Guide

## Overview

Peptimancer uses FastAPI's CORSMiddleware to handle Cross-Origin Resource Sharing (CORS) for frontend-backend communication. This document explains the CORS setup and how to configure it for different environments.

## Current Configuration

### Backend CORS Settings (`backend/server.py`)

```python
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,  # Required for JWT cookies
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],     # Allow all HTTP methods
    allow_headers=["*"],     # Allow all headers
)
```

### Environment Variable

**`CORS_ORIGINS`** (required, comma-separated list)
- Controls which origins can make requests to the backend
- **MUST NOT** be `"*"` when `allow_credentials=True`
- Format: `"http://localhost:3000,https://app.example.com"`

## Why Credentials Require Specific Origins

When using `credentials: 'include'` in frontend fetch requests (required for HTTP-only JWT cookies):

❌ **WRONG**:
```
CORS_ORIGINS="*"
allow_credentials=True
```
**Result**: Browser blocks requests with error:
```
Access-Control-Allow-Origin header must not be '*' when credentials mode is 'include'
```

✅ **CORRECT**:
```
CORS_ORIGINS="http://localhost:3000,https://partner-purge.preview.emergentagent.com"
allow_credentials=True
```
**Result**: Browser allows requests with credentials

## Environment-Specific Configuration

### 1. Local Development

**Backend `.env`**:
```bash
CORS_ORIGINS="http://localhost:3000"
```

**Use Case**: 
- Frontend running on `localhost:3000`
- Backend running on `localhost:8001`
- Testing authentication with JWT cookies

### 2. Preview/Staging Environment

**Backend `.env`**:
```bash
CORS_ORIGINS="http://localhost:3000,https://partner-purge.preview.emergentagent.com"
```

**Use Case**:
- Allows both local development and preview URL testing
- Common in containerized environments (like Kubernetes)

### 3. Production Environment

**Backend `.env`**:
```bash
CORS_ORIGINS="https://app.peptimancer.com,https://www.peptimancer.com"
```

**Use Case**:
- Only production frontend URLs allowed
- No localhost or preview URLs
- Maximum security

## How to Add a New Allowed Origin

### Step 1: Identify the Origin
An origin consists of: `<scheme>://<hostname>:<port>`

Examples:
- `http://localhost:3000` (local dev)
- `https://app.example.com` (production, port 443 implied)
- `https://staging.example.com:8080` (staging with custom port)

### Step 2: Update Environment Variable

Edit `backend/.env`:
```bash
# Add new origin to comma-separated list
CORS_ORIGINS="existing-origin.com,new-origin.com"
```

### Step 3: Restart Backend
```bash
sudo supervisorctl restart backend
```

### Step 4: Verify
Check backend logs for startup confirmation:
```bash
tail -f /var/log/supervisor/backend.out.log
```

## Testing CORS Configuration

### Test 1: Preflight Request (OPTIONS)

```bash
curl -X OPTIONS https://backend.example.com/api/auth/session \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v
```

**Expected Response Headers**:
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: *
Access-Control-Allow-Headers: *
```

### Test 2: Actual Request with Credentials

```bash
curl https://backend.example.com/api/auth/session \
  -H "Origin: http://localhost:3000" \
  -H "Cookie: pmnc_jwt=<token>" \
  -v
```

**Expected Response Headers**:
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Credentials: true
```

### Test 3: Frontend JavaScript Test

Open browser console on `http://localhost:3000`:

```javascript
fetch('https://backend.example.com/api/auth/session', {
  credentials: 'include'
})
  .then(r => r.json())
  .then(data => console.log('✅ CORS working:', data))
  .catch(err => console.error('❌ CORS error:', err));
```

## Common CORS Issues and Solutions

### Issue 1: "Response header must not be '*' when credentials mode is 'include'"

**Cause**: `CORS_ORIGINS="*"` with `allow_credentials=True`

**Solution**: Set specific origins in `CORS_ORIGINS`
```bash
CORS_ORIGINS="http://localhost:3000,https://app.example.com"
```

### Issue 2: "Origin not allowed by Access-Control-Allow-Origin"

**Cause**: Frontend origin not in `CORS_ORIGINS` list

**Solution**: Add the origin to `CORS_ORIGINS`
```bash
# Before
CORS_ORIGINS="https://app.example.com"

# After
CORS_ORIGINS="https://app.example.com,https://new-frontend.example.com"
```

### Issue 3: Preflight request failing

**Cause**: Missing `OPTIONS` method handling or wrong headers

**Solution**: Verify middleware configuration
```python
allow_methods=["*"],  # Includes OPTIONS
allow_headers=["*"],  # Allows all request headers
```

### Issue 4: Cookies not being sent

**Cause**: Frontend not using `credentials: 'include'`

**Solution**: Update fetch calls
```javascript
// ❌ Wrong
fetch('/api/endpoint')

// ✅ Correct
fetch('/api/endpoint', {
  credentials: 'include'
})
```

## Security Best Practices

### 1. Never Use Wildcard in Production
❌ **Avoid**:
```bash
CORS_ORIGINS="*"
```

✅ **Use**:
```bash
CORS_ORIGINS="https://app.peptimancer.com"
```

### 2. Use HTTPS in Production
❌ **Avoid**:
```bash
CORS_ORIGINS="http://app.peptimancer.com"
```

✅ **Use**:
```bash
CORS_ORIGINS="https://app.peptimancer.com"
```

### 3. Minimize Allowed Origins
Only add origins that genuinely need access.

❌ **Too permissive**:
```bash
CORS_ORIGINS="http://localhost:3000,https://staging.example.com,https://dev.example.com,https://test.example.com"
```

✅ **Appropriate for production**:
```bash
CORS_ORIGINS="https://app.peptimancer.com"
```

### 4. Separate Environments
Use different `.env` files for different environments:

**Local (`backend/.env.local`)**:
```bash
CORS_ORIGINS="http://localhost:3000"
```

**Production (`backend/.env.production`)**:
```bash
CORS_ORIGINS="https://app.peptimancer.com"
```

## Integration with Authentication

### Why CORS Matters for Auth

Peptimancer uses HTTP-only JWT cookies for authentication:

1. **Login**: Backend sets `pmnc_jwt` cookie
2. **Authenticated Requests**: Frontend sends cookie automatically with `credentials: 'include'`
3. **CORS**: Browser enforces same-origin policy, requires proper CORS headers

### Auth Flow with CORS

```
1. Frontend (localhost:3000) → POST /api/auth/magic/verify
   Headers: Content-Type: application/json
   
2. Backend checks CORS_ORIGINS
   ✅ "localhost:3000" found → Allow request
   
3. Backend validates OTP, creates JWT
   
4. Backend response:
   Headers:
     Access-Control-Allow-Origin: http://localhost:3000
     Access-Control-Allow-Credentials: true
     Set-Cookie: pmnc_jwt=<token>; HttpOnly; Secure
   
5. Browser stores cookie, future requests include it automatically
```

### CORS Preflight for Auth Endpoints

**POST /api/auth/magic/verify** triggers preflight because:
- Uses `Content-Type: application/json`
- Uses `credentials: 'include'`

**Preflight Request**:
```
OPTIONS /api/auth/magic/verify
Origin: http://localhost:3000
Access-Control-Request-Method: POST
Access-Control-Request-Headers: Content-Type
```

**Preflight Response**:
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: *
Access-Control-Allow-Headers: *
```

## Debugging CORS Issues

### 1. Check Browser Console

Look for errors like:
```
Access to fetch at '...' from origin '...' has been blocked by CORS policy
```

### 2. Check Network Tab

**Preflight Request (OPTIONS)**:
- Status should be `200` or `204`
- Response headers should include `Access-Control-Allow-*`

**Actual Request (GET/POST)**:
- Response headers should include `Access-Control-Allow-Origin`
- Should match the request `Origin` header

### 3. Check Backend Logs

```bash
tail -f /var/log/supervisor/backend.out.log | grep -i cors
```

### 4. Verify Environment Variable

```bash
# In backend container/environment
echo $CORS_ORIGINS
```

### 5. Test with curl

```bash
# Check if origin is allowed
curl -X GET https://backend.example.com/api/auth/session \
  -H "Origin: http://localhost:3000" \
  -v 2>&1 | grep -i "access-control"
```

## Deployment Checklist

Before deploying to production:

- [ ] Set `CORS_ORIGINS` to production frontend URL(s)
- [ ] Remove any `localhost` origins from production config
- [ ] Verify all origins use HTTPS (not HTTP)
- [ ] Test authentication flow works with new CORS settings
- [ ] Document any additional origins in deployment docs
- [ ] Set `ENABLE_DEMO_OTP=false` in production
- [ ] Restart backend service after env changes

## Quick Reference

### Current Environments

| Environment | Frontend Origin | CORS_ORIGINS Value |
|-------------|----------------|-------------------|
| Local Dev | `http://localhost:3000` | `"http://localhost:3000"` |
| Preview | `https://partner-purge.preview.emergentagent.com` | `"http://localhost:3000,https://partner-purge.preview.emergentagent.com"` |
| Production | TBD | `"https://app.peptimancer.com"` |

### Required Headers for Credentials

**Request**:
- `Origin: http://localhost:3000`
- `Cookie: pmnc_jwt=<token>` (sent automatically by browser)

**Response**:
- `Access-Control-Allow-Origin: http://localhost:3000` (must match request origin)
- `Access-Control-Allow-Credentials: true`

### FastAPI Middleware Order

**IMPORTANT**: AuthMiddleware must be added BEFORE CORSMiddleware:

```python
# ✅ Correct order
app.add_middleware(AuthMiddleware)
app.add_middleware(CORSMiddleware, ...)

# ❌ Wrong order (CORS will process OPTIONS before auth)
app.add_middleware(CORSMiddleware, ...)
app.add_middleware(AuthMiddleware)
```

## Related Documentation

- [AUTH_FLOW.md](./AUTH_FLOW.md) - Complete authentication flow
- [Backend README](../backend/README.md) - Backend setup guide
- [Frontend README](../frontend/README.md) - Frontend setup guide

## Support

For CORS-related issues:
1. Check this document first
2. Verify environment variables are set correctly
3. Test with curl to isolate frontend vs backend issues
4. Check browser console and network tab for detailed errors

## Changelog

- **2025-11-22**: Initial CORS documentation created
  - Added environment-specific configurations
  - Documented credentials + CORS interaction
  - Added troubleshooting guide
  - Included security best practices
