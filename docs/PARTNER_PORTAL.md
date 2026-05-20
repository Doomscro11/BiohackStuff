# PatentPulse Partner Portal Documentation

## Overview

The Partner Portal (Phase IXf+) enables secure, audited sharing of PatentPulse Reclaim Pack reports with external partners. It provides a complete system for generating signed, expiring share links with watermarking, access analytics, and revocation capabilities.

## Features

### Core Capabilities

1. **Secure Share Links**
   - HMAC-signed tokens for authentication
   - Time-limited access with configurable expiry
   - Maximum download limits per share
   - IP allowlist support (CIDR notation)
   - Token rotation for security updates

2. **Watermarking**
   - PDF watermarking with recipient information
   - JSON metadata headers for tracking
   - Masked email display for privacy
   - Diagonal "CONFIDENTIAL" overlay
   - Footer with expiry date and recipient

3. **Access Control**
   - Per-IP rate limiting (default: 30/min)
   - State management (active, expired, revoked)
   - Instant revocation with audit trail
   - Download count tracking and enforcement
   - IP allowlist validation

4. **Analytics & Tracking**
   - Event logging (opens, downloads, blocked)
   - IP address tracking
   - Geographic distribution (optional)
   - User agent logging
   - Access analytics dashboard
   - Top IPs and countries breakdown

5. **Admin Management**
   - 2FA-protected admin endpoints
   - Create/rotate/revoke share links
   - View share analytics
   - Filter by state (active/expired/revoked)
   - Copy share URLs to clipboard
   - Internal notes for tracking

6. **Partner Experience**
   - Clean, mobile-friendly landing page
   - Downloads remaining counter
   - Expiry countdown
   - Clear error states
   - Watermarked PDF downloads
   - Support contact information

## Architecture

### Backend Components

#### 1. Models (`backend/models/partner_share.py`)

```python
class PartnerShare:
    share_id: str
    file_id: str  # Reference to patentpulse_exports
    recipient_email: EmailStr
    recipient_first_name: str
    company_or_project: str
    policy: SharePolicy
    share_token: str  # HMAC signed
    state: Literal["active", "expired", "revoked"]
    download_count: int
    created_by: str  # Admin email
    ...

class SharePolicy:
    expires_at: datetime
    max_downloads: int
    ip_allowlist: List[str]
    rate_limit_per_ip: str
    watermark_enabled: bool
```

#### 2. API Routes (`backend/routes/partner_shares.py`)

**Admin Endpoints (2FA Required):**

```
POST   /api/patentpulse/partner/shares           # Create share
GET    /api/patentpulse/partner/shares           # List shares (filters)
GET    /api/patentpulse/partner/shares/{id}      # Get share details
POST   /api/patentpulse/partner/shares/{id}/rotate    # Rotate token
POST   /api/patentpulse/partner/shares/{id}/revoke    # Revoke share
GET    /api/patentpulse/partner/shares/{id}/analytics # View analytics
GET    /api/patentpulse/partner/dashboard/metrics     # Dashboard metrics
```

**Public Endpoints (No Auth):**

```
GET    /share/{token}            # Share metadata for landing page
GET    /share/{token}/download   # Download with policy enforcement
```

#### 3. Analytics (`backend/analytics/partner_analytics.py`)

```python
# Event tracking
track_event(share_id, event, ip, user_agent, reason=None, ...)

# Share analytics
get_share_analytics(share_id) -> {opens, downloads, blocked, ...}

# Dashboard metrics
get_dashboard_metrics(start_date, end_date) -> {...}

# Cleanup
cleanup_old_events(days=180) -> deleted_count
```

#### 4. Watermarking (`backend/watermark/pdf_watermark.py`)

```python
# PDF watermarking
watermark_pdf(input_pdf, output_pdf, recipient_email, expires_at, company)

# JSON metadata headers
add_json_watermark_headers(data, recipient_email, expires_at, company)
```

#### 5. Cleanup Job (`backend/jobs/share_link_cleaner.py`)

Runs nightly to:
- Expire shares past their expiry date
- Send 3-day reminder emails (stub)
- Clean up old events (>180 days)
- Delete old watermarked files (>7 days)

### Frontend Components

#### 1. Partner Share Page (`frontend/src/pages/partner/SharePage.tsx`)

Public-facing page for partners to:
- View share metadata
- See downloads remaining and expiry
- Download watermarked files
- Read landing copy and legal disclaimers

Features:
- Mobile-responsive design
- Clear error states (expired, revoked, rate limited)
- Countdown timer for expiry
- Download button with loading state
- Support contact information

#### 2. Admin Management UI (`frontend/src/components/admin/PartnerShares.tsx`)

Admin interface to:
- Create new partner shares
- List and filter shares
- Copy share URLs
- Rotate tokens
- Revoke shares
- View analytics

Features:
- Create share form with validation
- Filter tabs (all/active/expired/revoked)
- Analytics modal with metrics
- Inline actions (copy, rotate, revoke)
- Internal notes tracking

## Configuration

### Environment Variables (`backend/.env`)

```bash
# Feature flag
FEATURE_PATENTPULSE_PARTNER=true

# Default policy
PARTNER_SHARE_TTL_DAYS=14
PARTNER_MAX_DOWNLOADS=10

# Security
PARTNER_SIGNING_SECRET=your_secret_key_64_bytes_minimum
RATE_LIMIT_PER_IP=30/min

# Watermarking
WATERMARK_ENABLED=true

# Storage
PARTNER_STORAGE=disk  # or s3
S3_BUCKET=patentpulse/exports  # if s3

# CORS
CORS_PARTNER_ORIGINS=https://partners.peptimancer.com

# Support
SUPPORT_EMAIL=support@peptimancer.com
```

### Database Collections

#### `partner_shares`

Stores share metadata and state.

**Indexes:**
- `share_id` (unique)
- `state`
- `recipient_email`
- `created_at` (descending)
- `policy.expires_at`

**TTL:** None (manual cleanup via state)

#### `partner_share_events`

Stores analytics events.

**Indexes:**
- `share_id`
- `ts` (descending)
- `event`
- `ip`

**TTL:** Cleaned by job (>180 days)

## Security

### Token Signing

Share tokens use HMAC-SHA256 signing:

```
token = share_id|file_id|expires_ts|signature
signature = HMAC-SHA256(share_id|file_id|expires_ts, PARTNER_SIGNING_SECRET)
```

Token verification:
1. Parse token components
2. Verify HMAC signature
3. Check expiry timestamp
4. Lookup share in database
5. Enforce policy (state, IP, downloads, rate limit)

### Access Control

1. **Admin Endpoints:** 2FA required via `require_role(['admin'])`
2. **Public Endpoints:** Token verification only
3. **Rate Limiting:** Per-IP limits (default: 30/min)
4. **IP Allowlist:** Optional CIDR notation support
5. **State Enforcement:** Active/Expired/Revoked checks
6. **Download Limits:** Max downloads per share

### Watermarking

1. **PDF:** Footer + diagonal overlay with masked email and expiry
2. **JSON:** Metadata headers (`X-PatentPulse-Recipient`, `X-PatentPulse-Expiry`)
3. **Email Masking:** `user@example.com` → `u***@example.com`
4. **Confidentiality:** "CONFIDENTIAL" overlay on PDFs

## Usage

### Creating a Partner Share (Admin)

1. Navigate to Admin > Partner Shares
2. Click "Create Share"
3. Select export file (Reclaim Pack)
4. Enter recipient details:
   - Email
   - First name
   - Company/project
5. Configure policy:
   - Expiry (days)
   - Max downloads
   - IP allowlist (optional)
   - Watermarking (enabled by default)
6. Add internal notes (optional)
7. Click "Create Share"
8. Copy generated share URL
9. Send URL to partner (via secure channel)

### Rotating a Token (Admin)

1. Find share in list
2. Click rotate button (🔄)
3. Confirm action
4. Copy new share URL
5. Send new URL to partner
6. Old token is immediately invalidated

### Revoking a Share (Admin)

1. Find share in list
2. Click revoke button (🚫)
3. Enter revocation reason
4. Confirm action
5. Share is immediately revoked
6. Partner will see "revoked" error on access

### Accessing a Share (Partner)

1. Open share link in browser
2. View share metadata and policy
3. Click "Download Reclaim Pack"
4. File is downloaded with watermark
5. Download count increments
6. Share expires when:
   - Expiry date reached
   - Max downloads reached
   - Admin revokes share

### Viewing Analytics (Admin)

1. Find share in list
2. Click analytics button (📊)
3. View metrics:
   - Opens, downloads, blocked events
   - Top IPs and events
   - Geographic distribution
   - Last access timestamp

## Testing

### Backend Tests (`backend/tests/test_partner_portal.py`)

```bash
pytest backend/tests/test_partner_portal.py -v
```

Tests:
- Share creation (admin 2FA required)
- Public download with policy enforcement
- Expiry and max download limits
- Revocation blocks access
- Token rotation invalidates old token
- IP allowlist enforcement
- Watermark application
- Analytics event tracking
- Email template compilation

### Frontend E2E Tests (`frontend/tests/e2e/partner_share_flow.spec.ts`)

```bash
cd frontend && npx playwright test partner_share_flow
```

Flow:
1. Admin creates share
2. Partner opens share link
3. Partner downloads file
4. Counters increment
5. Admin revokes share
6. Partner sees "revoked" error

### Manual Testing

1. **Create Share:**
   ```bash
   curl -X POST ${BACKEND_URL}/api/patentpulse/partner/shares \
     -H "Content-Type: application/json" \
     -H "Cookie: jwt=ADMIN_JWT" \
     -d '{
       "file_id": "export_123",
       "recipient_email": "partner@company.com",
       "recipient_first_name": "John",
       "company_or_project": "ACME Pharma",
       "expires_in_days": 14,
       "max_downloads": 10
     }'
   ```

2. **Get Share Metadata:**
   ```bash
   curl ${BACKEND_URL}/share/{token}
   ```

3. **Download File:**
   ```bash
   curl -O ${BACKEND_URL}/share/{token}/download
   ```

4. **Revoke Share:**
   ```bash
   curl -X POST ${BACKEND_URL}/api/patentpulse/partner/shares/{share_id}/revoke \
     -H "Cookie: jwt=ADMIN_JWT" \
     -d '{"reason": "Testing revocation"}'
   ```

## Monitoring

### Grafana Dashboard (`dashboards/grafana_patentpulse.json`)

Metrics:
- Active vs Expired vs Revoked shares (pie chart)
- Downloads per day by partner (time series)
- Blocked events (time series)
- Top geographies (bar chart)

Alerts:
- `spike_blocked_events`: >10 blocked events in 5min
- `single_ip_downloads_spike`: >20 downloads from single IP in 1h

### Logs

Key log events:
- Share creation: `"Created partner share: {share_id} for {email}"`
- Download: `"Partner download: share={share_id} file={file_id} ip={ip}"`
- Revocation: `"Revoked share: {share_id} by {admin_email}"`
- Blocked access: `"Blocked: {reason} for share={share_id} ip={ip}"`

## Troubleshooting

### Issue: "Invalid or expired share link"

**Causes:**
- Token signature mismatch (wrong `PARTNER_SIGNING_SECRET`)
- Token expired (past `expires_at`)
- Share revoked by admin
- Token format invalid

**Fix:**
1. Check `PARTNER_SIGNING_SECRET` in `.env`
2. Verify share state in database
3. Check expiry date
4. Regenerate token via rotate endpoint

### Issue: "Maximum download limit reached"

**Causes:**
- Share reached `max_downloads` limit
- Download counter incremented prematurely

**Fix:**
1. Check `download_count` in database
2. Increase `max_downloads` in share policy (requires DB update)
3. Create new share if needed

### Issue: "Your IP address is not authorized"

**Causes:**
- IP not in `ip_allowlist`
- Proxy/VPN changed partner's IP

**Fix:**
1. Check partner's current IP
2. Update `ip_allowlist` in database
3. Remove allowlist for open access (if acceptable)

### Issue: "Rate limit exceeded"

**Causes:**
- Partner exceeded per-IP rate limit
- Automated scraping detected

**Fix:**
1. Wait for rate limit window to reset
2. Adjust `RATE_LIMIT_PER_IP` in `.env`
3. Check for suspicious activity

### Issue: Watermark not applied

**Causes:**
- `PyPDF2` or `reportlab` not installed
- `WATERMARK_ENABLED=false` in config
- PDF generation failed

**Fix:**
1. Install: `pip install PyPDF2 reportlab`
2. Check `WATERMARK_ENABLED` setting
3. Check logs for watermarking errors
4. Verify input PDF is valid

## Cron Schedule

### Share Link Cleaner (`jobs/share_link_cleaner.py`)

**Frequency:** Nightly (2 AM UTC)

**Cron:**
```bash
0 2 * * * cd /app/backend && python jobs/share_link_cleaner.py >> /var/log/share_cleaner.log 2>&1
```

**Tasks:**
1. Expire shares past `policy.expires_at`
2. Send 3-day reminder emails
3. Clean up events older than 180 days
4. Delete watermarked files older than 7 days

## Email Templates

Located in `backend/emails/`:

1. **`partner_onboarding_invite.md`**: Initial invitation email
2. **`partner_access_granted.md`**: Share link delivery email
3. **`partner_access_reminder.md`**: 3-day expiry reminder
4. **`partner_access_revoked.md`**: Revocation notification

**Placeholders:**
- `{{recipient_first_name}}`
- `{{secure_share_url}}`
- `{{expiry_date}}`
- `{{max_downloads}}`
- `{{days_valid}}`
- `{{days_remaining}}`
- `{{support_email}}`
- `{{revoked_reason}}`

## Landing Copy

Located in `frontend/src/pages/partner/SharePage.tsx`.

Sections:
1. **Welcome & Context**
2. **What You'll Find** (features list)
3. **Important Notes** (policy, watermarking, limits)
4. **Legal Disclaimer** (not legal advice, not FTO clearance)
5. **Support Contact**

Key messaging:
- Preview is watermarked and time-limited
- Personal, non-transferable link
- For internal evaluation only
- No license grant or FTO clearance
- Always verify with qualified counsel

## API Reference

See inline documentation in `backend/routes/partner_shares.py`.

## Change Log

**v1.3 (Phase IXf+):**
- Added Partner Portal with secure share links
- Implemented HMAC-signed tokens
- Added PDF/JSON watermarking
- Created analytics tracking system
- Built admin management UI
- Added partner-facing landing page
- Implemented rate limiting
- Added IP allowlist support
- Created cleanup job
- Added email templates
- Updated documentation

## Future Enhancements

1. **Email Integration:** Connect email templates to real SMTP service
2. **Geo-IP Lookup:** Automatic country/city detection from IP
3. **Advanced Rate Limiting:** Redis-backed distributed rate limiter
4. **S3 Storage:** Support for S3-backed file storage
5. **CIDR Support:** Full CIDR notation parsing for IP allowlists
6. **Audit Exports:** CSV export of analytics events
7. **Custom Branding:** White-label share pages per partner
8. **Multi-file Shares:** Bundle multiple exports in one share
9. **Expiry Extension:** Admin can extend share expiry
10. **Partner Feedback:** Collect partner feedback on landing page
