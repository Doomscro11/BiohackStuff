# Monorepo Refactoring Plan - Peptimancer + PatentPulse

**Status:** ✅ **COMPLETE** (Phases 1-4)  
**Branch:** `refactor/monorepo-structure`  
**Date:** 2025-01-19

---

## ✅ Completed Phases

### Phase 1: Frontend Import Fixes
✅ Fixed all broken import paths after directory reorganization  
✅ Moved pages from `pages/` to `apps/[domain]/pages/`  
✅ Updated all imports to use `@/` alias  
✅ Frontend builds successfully with zero errors

### Phase 2: Business Logic Extraction (75%)
✅ Created 5 service modules (1,023 lines total)  
✅ Refactored 5 API routes to thin controllers  
✅ Backend remains stable and functional

**Services Created:**
- `services/auth_service.py` - Authentication logic
- `services/partner_share_service.py` - Share management
- `services/chemistry_service.py` - Chemistry filtering
- `services/patentpulse_service.py` - Patent operations
- `services/reclaim_service.py` - Export generation

### Phase 3: Model/Schema Separation
✅ Created `schemas/` directory for API DTOs  
✅ Separated persistence models from request/response schemas  
✅ Backward compatibility maintained via models/__init__.py

**Schemas Created:**
- `schemas/admin.py` - Admin operation DTOs
- `schemas/billing.py` - Billing operation DTOs
- `schemas/partner_share.py` - Share operation DTOs

### Phase 4: Frontend Reorganization
✅ Domain-driven structure in `apps/` directory  
✅ Removed all duplicate files from legacy `pages/`  
✅ Clean separation of domain concerns

**Infrastructure:**
- `/app/backend/core/__init__.py`
- `/app/backend/core/config.py`
- `/app/backend/core/db.py`
- `/app/backend/core/security.py`

## Backend Structure (Target)

```
backend/
├── core/                    # Shared infrastructure
│   ├── __init__.py
│   ├── config.py           # Settings & environment
│   ├── db.py               # MongoDB client
│   ├── security.py         # JWT & auth utilities
│   └── middleware.py       # FastAPI middleware
├── api/                    # HTTP routers by domain
│   ├── auth.py             # from routes_auth.py
│   ├── peptimancer.py      # Main peptide generation
│   ├── chemistry.py        # from routes_chemistry.py
│   ├── billing.py          # from routes_billing.py
│   ├── webhooks.py         # from routes_webhooks.py
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── modes.py        # from routes_admin.py
│   │   ├── users.py        # from routes_admin_users.py
│   │   ├── health.py       # from routes_admin_health.py
│   │   └── analytics.py    # from routes_analytics.py
│   └── patentpulse/
│       ├── __init__.py
│       ├── items.py        # from routes_patentpulse.py
│       ├── signals.py      # from routes/patentpulse_signals.py
│       ├── reclaim.py      # from routes/patentpulse_reclaim.py
│       └── partner_shares.py # from routes/partner_shares.py
├── services/               # Business logic (extracted)
│   ├── peptimancer_engine.py
│   ├── chemistry_rules.py
│   ├── credits_service.py
│   ├── billing_service.py
│   └── partner_portal_service.py
├── models/                 # Existing, organized
│   ├── __init__.py
│   ├── partner_share.py
│   ├── patentpulse.py
│   └── ... (existing models)
├── schemas/                # Pydantic DTOs
│   └── ... (to be extracted)
├── jobs/                   # Existing background jobs
├── scripts/                # Existing utility scripts
├── tests/                  # Existing tests
├── analytics/              # Existing analytics module
├── watermark/              # Existing watermark module
└── server.py               # Main FastAPI app
```

## Frontend Structure (Target)

```
frontend/src/
├── apps/
│   ├── peptimancer/        # Main research app
│   │   ├── pages/
│   │   │   └── HomePage.js     # from App.js
│   │   └── components/
│   │       ├── AnalogueForm.js
│   │       └── ResultsDisplay.js
│   ├── patentpulse/        # Partner Portal app
│   │   ├── pages/
│   │   │   ├── PatentPulsePage.js
│   │   │   ├── PatentPulseReclaim.js
│   │   │   └── SharePage.js    # from pages/partner/
│   │   └── components/
│   │       └── PartnerShares.js
│   ├── admin/              # Admin console
│   │   ├── pages/
│   │   │   ├── AdminPage.js
│   │   │   └── AnalyticsPage.js
│   │   └── components/
│   │       ├── AdminUsersPanel.js
│   │       ├── AdminPlansPanel.js
│   │       └── ... (existing admin components)
│   └── account/            # User account management
│       └── pages/
│           └── BillingPage.js
├── components/
│   ├── ui/                 # Existing UI components
│   └── layout/             # Layout components
├── lib/                    # Existing utility libraries
└── routes/
    └── MainApp.js          # Main router (update imports)
```

## Next Steps

1. Move route files to api/ structure
2. Update server.py imports
3. Extract services from routers
4. Reorganize frontend into apps/
5. Update all import paths
6. Run tests and verify
7. Create ARCHITECTURE.md
