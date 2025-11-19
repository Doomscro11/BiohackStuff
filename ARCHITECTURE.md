# Peptimancer Architecture Documentation

**Last Updated:** 2025-01-19  
**Refactor Branch:** `refactor/monorepo-structure`

---

## Overview

Peptimancer is a full-stack AI platform for peptide design and patent mining, featuring a domain-driven monorepo architecture with clean separation of concerns.

### Technology Stack

- **Backend:** FastAPI (Python 3.11+)
- **Frontend:** React 18
- **Database:** MongoDB
- **Authentication:** JWT with magic link (OTP)
- **Deployment:** Docker, Kubernetes

---

## Architecture Principles

### 1. Domain-Driven Design
The codebase is organized by business domains rather than technical layers:
- **Peptimancer:** Core peptide design functionality
- **PatentPulse:** Patent mining and opportunity analysis
- **Admin:** System administration and analytics
- **Account:** User billing and subscription management

### 2. Separation of Concerns

**Backend:**
```
backend/
├── api/           # Thin controllers (routing, validation, responses)
├── services/      # Business logic (reusable, testable)
├── models/        # Persistence layer (database entities)
├── schemas/       # DTOs (request/response models)
├── jobs/          # Background tasks
└── middleware/    # Cross-cutting concerns (auth, logging)
```

**Frontend:**
```
frontend/src/
├── apps/          # Domain-specific pages/components
├── components/    # Shared UI components
├── lib/           # API clients and utilities
└── hooks/         # React hooks
```

### 3. Clean Code Patterns

- **Thin Controllers, Thick Services:** API routes delegate to services
- **Single Responsibility:** Each module has one clear purpose
- **Dependency Injection:** Services receive dependencies explicitly
- **Immutable DTOs:** Request/response models are validated and type-safe

---

## Backend Architecture

### API Layer (`backend/api/`)

**Purpose:** Handle HTTP requests, validate input, return responses

**Structure:**
```
api/
├── auth.py                    # Authentication endpoints
├── billing.py                 # Billing and subscription
├── chemistry.py               # Chemistry options
├── admin/
│   ├── analytics.py           # Admin analytics
│   ├── health.py              # System health checks
│   ├── modes.py               # Feature flags
│   └── users.py               # User management
└── patentpulse/
    ├── items.py               # Patent queries
    ├── reclaim.py             # Export generation
    ├── signals.py             # Market signals
    └── partner_shares.py      # Partner portal
```

**Pattern:**
```python
@router.get("/endpoint")
async def endpoint_handler(params, user=Depends(auth)):
    """Thin controller - delegates to service"""
    result = await service.business_logic(params)
    return result
```

### Service Layer (`backend/services/`)

**Purpose:** Implement business logic, data operations, external API calls

**Modules:**
- `auth_service.py` - OTP generation, user management, JWT
- `partner_share_service.py` - Share token management, access control
- `chemistry_service.py` - Tier-based chemistry filtering
- `patentpulse_service.py` - Patent queries, statistics
- `reclaim_service.py` - Export generation, validation

**Pattern:**
```python
async def create_resource(params: dict) -> dict:
    """Pure business logic - no HTTP concerns"""
    # Validate
    # Transform
    # Persist
    # Return data
    return result
```

### Models (`backend/models/`)

**Purpose:** Database persistence layer

**Examples:**
- `PartnerShare` - Partner share entity
- `PatentItemDB` - Patent database record
- `ReclaimPackExport` - Export metadata

**Pattern:**
```python
class EntityModel(BaseModel):
    """Persistence model - matches DB schema"""
    id: str
    created_at: datetime
    # ... fields
```

### Schemas (`backend/schemas/`)

**Purpose:** API contracts (DTOs)

**Modules:**
- `admin.py` - Admin operation DTOs
- `billing.py` - Billing operation DTOs
- `partner_share.py` - Share operation DTOs

**Pattern:**
```python
class RequestSchema(BaseModel):
    """API request body"""
    field: str = Field(validation...)
```

---

## Frontend Architecture

### Domain Structure (`frontend/src/apps/`)

Each domain has its own folder with pages, components, and styles:

```
apps/
├── peptimancer/
│   ├── pages/HomePage.js
│   └── components/AnalogueForm.js
├── patentpulse/
│   ├── pages/PatentPulsePage.js
│   ├── pages/SharePage.js
│   └── styles/SharePage.css
├── admin/
│   └── pages/AdminPage.js
└── account/
    └── pages/BillingPage.js
```

### Shared Resources

**Components (`components/`):**
- Cross-domain UI components
- Shadcn UI library (`components/ui/`)
- Domain-specific widgets (`components/admin/`, `components/billing/`)

**Libraries (`lib/`):**
- API clients (HTTP wrapper, domain-specific APIs)
- Utilities (auth, session, analytics)

**Pattern:**
```javascript
// Domain page
import { fetchData } from '@/lib/domain-api';
import { Button } from '@/components/ui/button';

function DomainPage() {
  // Use shared utilities and components
}
```

---

## Key Features

### 1. Authentication

**Flow:**
1. User requests magic link (OTP sent to email)
2. User verifies OTP
3. Backend creates JWT token
4. Token stored in HTTP-only cookie

**Implementation:**
- Service: `auth_service.py`
- Routes: `api/auth.py`
- Frontend: `lib/auth.js`

### 2. Partner Portal

**Flow:**
1. Admin creates secure share link
2. Link contains HMAC-signed token
3. Partner accesses via unique URL
4. System validates token, enforces policies
5. Files are watermarked on download

**Implementation:**
- Service: `partner_share_service.py`
- Routes: `api/patentpulse/partner_shares.py`
- Frontend: `apps/patentpulse/pages/SharePage.js`

### 3. Billing

**Flow:**
1. User selects plan or credits
2. Checkout initiated via Stripe
3. Webhook updates user tier/credits
4. Credits consumed on API calls

**Implementation:**
- Service: `billing/service.py`
- Routes: `api/billing.py`, `api/webhooks.py`
- Frontend: `apps/account/pages/BillingPage.js`

---

## Database Schema

### Collections

**Users:**
```javascript
{
  id: "user_xyz",
  email: "user@example.com",
  role: "researcher",
  org_id: "default",
  created_at: ISODate,
  last_login: ISODate
}
```

**Partner Shares:**
```javascript
{
  share_id: "uuid",
  reclaim_pack_id: "pack_123",
  recipient_org: "Company Inc",
  recipient_email: "partner@example.com",
  token: "hmac_signed_token",
  created_by: "admin@peptimancer.com",
  created_at: ISOString,
  expires_at: ISOString,
  status: "active",
  access_count: 0,
  download_count: 0,
  policy: {
    ttl_days: 14,
    max_downloads: 10,
    allowed_ips: [],
    watermark: true
  }
}
```

**Patent Items:**
```javascript
{
  patent_id: "US1234567",
  title: "Peptide...",
  status: "Expired",
  country: "US",
  assignee: "BigPharma Inc",
  expiry_date: ISODate,
  commercial_score: 0.85,
  synthesis_score: 0.42,
  fto_risk: 0.15
}
```

---

## Environment Variables

### Backend

```bash
# Database
MONGO_URL=mongodb://localhost:27017
DB_NAME=peptimancer_db

# Authentication
ADMIN_EMAILS=admin@peptimancer.com
OTP_LENGTH=6
OTP_EXPIRES_MINUTES=10
JWT_EXPIRES_HOURS=72

# Partner Portal
PARTNER_SIGNING_SECRET=change_in_production
PARTNER_SHARE_TTL_DAYS=14
PARTNER_MAX_DOWNLOADS=10
WATERMARK_ENABLED=true

# Billing
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Feature Flags
PATENTPULSE_ENABLED=true
```

### Frontend

```bash
REACT_APP_BACKEND_URL=http://localhost:8001
```

---

## Development Workflow

### Running Locally

**Start Services:**
```bash
sudo supervisorctl restart all
```

**Check Status:**
```bash
sudo supervisorctl status
```

**View Logs:**
```bash
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/frontend.out.log
```

### Code Organization

**When adding a new feature:**

1. **Create service** in `backend/services/` with business logic
2. **Create schema** in `backend/schemas/` for request/response
3. **Create route** in `backend/api/` that delegates to service
4. **Create frontend page** in `frontend/src/apps/[domain]/pages/`
5. **Add route** to `MainApp.js`

**Example:**
```python
# 1. Service
async def create_widget(data: dict) -> dict:
    # Business logic
    return result

# 2. Schema
class WidgetRequest(BaseModel):
    name: str

# 3. Route
@router.post("/widgets")
async def create_widget_endpoint(body: WidgetRequest):
    return await service.create_widget(body.dict())
```

---

## Testing

### Backend Tests

Located in `backend/scripts/` and `backend/tests/`

**Run tests:**
```bash
pytest backend/tests/
python backend/scripts/verify_partner_portal.py
```

### Frontend Tests

Located in `frontend/src/__tests__/`

**Run tests:**
```bash
cd frontend
yarn test
```

---

## Deployment

### Docker

```bash
docker-compose up -d
```

### Kubernetes

Services run in pods with:
- Backend on port 8001
- Frontend on port 3000
- MongoDB as separate service

**Ingress rules:**
- `/api/*` → Backend service
- `/*` → Frontend service

---

## Security

### Authentication
- JWT tokens in HTTP-only cookies
- Short-lived OTP codes (10 min expiry)
- Rate limiting on login attempts

### Partner Portal
- HMAC-SHA256 signed tokens
- Time-based expiry
- Download count limits
- IP whitelisting support
- Watermarked PDFs

### API Security
- Role-based access control (admin, researcher)
- 2FA required for admin actions
- Input validation via Pydantic

---

## Performance

### Caching
- Client-side session caching
- MongoDB indexes on frequent queries

### Background Jobs
- Share link cleanup (expired shares)
- Export generation (async)

### Optimization
- Lazy loading for frontend routes
- Pagination on large datasets
- Compressed responses

---

## Monitoring

### Health Checks
- `GET /api/admin/health` - System status
- Supervisor process monitoring
- Database connection checks

### Analytics
- User activity tracking
- Share link analytics (opens, downloads)
- API usage metrics

---

## Contributing

### Code Style

**Python:**
- PEP 8 compliant
- Type hints preferred
- Docstrings for public functions

**JavaScript:**
- ESLint configured
- Functional components preferred
- Hooks for state management

### Git Workflow

1. Create feature branch from `main`
2. Make changes with clear commits
3. Test locally
4. Submit PR with description
5. Code review
6. Merge to `main`

---

## Maintenance

### Regular Tasks

1. **Database Cleanup:**
   - Run share link cleaner (see `jobs/share_link_cleaner.py`)
   - Archive old exports

2. **Dependency Updates:**
   - Update Python packages in `requirements.txt`
   - Update Node packages in `package.json`

3. **Monitoring:**
   - Check logs for errors
   - Review analytics for anomalies

---

## Troubleshooting

### Backend Won't Start

Check logs:
```bash
tail -n 100 /var/log/supervisor/backend.err.log
```

Common issues:
- MongoDB connection failed → Check `MONGO_URL`
- Import errors → Check Python environment
- Port already in use → Kill existing process

### Frontend Won't Build

Check logs:
```bash
tail -n 50 /var/log/supervisor/frontend.err.log
```

Common issues:
- Module not found → Check import paths
- Syntax errors → Check for TypeScript remnants
- Build timeout → Increase memory limit

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [Shadcn UI](https://ui.shadcn.com/)

---

## Contact

For questions or issues, contact the development team or file an issue in the repository.
