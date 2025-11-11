# PatentPulse Reclaim Pack Exporter

## Overview

The **Reclaim Pack Exporter** is a Phase IXe feature that generates investor-ready PDF and JSON reports of top expired and expiring peptide patent opportunities. These comprehensive exports combine PatentPulse collector data (Phase IXc) with market signal enrichment (Phase IXd) to produce actionable intelligence packages.

### Key Features

- 📄 **PDF Reports**: Professional, formatted reports with tables, charts, and legal disclaimers
- 📊 **JSON Exports**: Machine-readable data for programmatic integration
- 🎯 **Viability Scoring**: Automated ranking based on commercial potential, FTO risk, and synthesis feasibility
- 🔒 **Secure Access**: Admin 2FA required, feature-flag gated
- ⏰ **Auto-Cleanup**: TTL-based expiration (default: 7 days)
- 🌍 **Flexible Filters**: By status, country, and limit

---

## Prerequisites

### Environment Setup

```bash
# Required feature flag
export FEATURE_PATENTPULSE_RECLAIM=true

# Optional configuration
export RECLAIM_EXPORT_DIR=/app/exports    # Export directory
export EXPORT_TTL_DAYS=7                  # Days before auto-delete
export MAX_EXPORT_ITEMS=100               # Max items per export
```

### Access Requirements

1. **Admin Account**: Must have admin role
2. **2FA Enabled**: Admin two-factor authentication required
3. **Feature Flag**: `FEATURE_PATENTPULSE_RECLAIM=true` must be set

### Dependencies

- **Backend**: ReportLab (PDF generation), Motor (MongoDB async driver)
- **Frontend**: React, Tailwind CSS (styling)
- **Database**: MongoDB with `patentpulse_items` and `patentpulse_exports` collections

---

## Viability Score Formula

The **viability score** ranks patents by their commercialization potential:

```python
viability_score = (
    0.6 * commercial_score_adj +      # Market-adjusted commercial potential
    0.2 * (1 - fto_risk) +            # Freedom-to-operate likelihood
    0.2 * (1 - synthesis_score)       # Synthesis feasibility (lower = easier)
)
```

### Score Components

| Component | Weight | Description |
|-----------|--------|-------------|
| `commercial_score_adj` | 60% | Market-enriched commercial potential (Phase IXd) |
| `fto_risk` | 20% | Patent landscape risk (lower is better) |
| `synthesis_score` | 20% | Chemical synthesis complexity (lower is easier) |

**Result**: A score between 0.0 and 1.0, where higher values indicate better opportunities.

---

## Usage

### 1. CLI Generation

#### Generate PDF Export

```bash
cd /app/backend

# Top 10 expired patents (PDF)
FEATURE_PATENTPULSE_RECLAIM=true python jobs/reclaim_pack_generator.py \
  --format pdf \
  --limit 10 \
  --status Expired

# Output:
# ============================================================
# ✅ RECLAIM PACK GENERATED
# ============================================================
# File: patentpulse-reclaim-20251111-143022.pdf
# Format: PDF
# Items: 10
# Size: 245KB
# Avg Viability: 0.782
# Expires: 2025-11-18
# Path: /app/exports/patentpulse-reclaim-20251111-143022.pdf
# ============================================================
```

#### Generate JSON Export with Filters

```bash
# Top 25 US patents expiring soon (JSON)
FEATURE_PATENTPULSE_RECLAIM=true python jobs/reclaim_pack_generator.py \
  --format json \
  --limit 25 \
  --country US \
  --status ExpiringSoon \
  --out /app/exports
```

#### CLI Arguments

| Argument | Options | Default | Description |
|----------|---------|---------|-------------|
| `--format` | `pdf`, `json` | `pdf` | Export format |
| `--limit` | 1-100 | 10 | Number of top patents |
| `--country` | US, EP, JP, CA, WO | All | Country filter |
| `--status` | Expired, ExpiringSoon, Lapsed | All | Status filter |
| `--out` | Path | `/app/exports` | Output directory |

---

### 2. API Usage

#### Generate Export

```bash
# PDF export via API
curl -X GET "http://localhost:8001/api/patentpulse/reclaim/export?format=pdf&limit=10&status=Expired" \
  -H "Cookie: session=YOUR_SESSION_TOKEN" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "file_name": "patentpulse-reclaim-20251111-143022.pdf",
  "format": "pdf",
  "path": "/api/patentpulse/reclaim/a1b2c3d4-.../download",
  "size_kb": 245,
  "items": 10,
  "viability_avg": 0.782,
  "generated_at": "2025-11-11T14:30:22Z",
  "expires_at": "2025-11-18T14:30:22Z"
}
```

#### List Recent Exports

```bash
curl "http://localhost:8001/api/patentpulse/reclaim/list?limit=20" \
  -H "Cookie: session=YOUR_SESSION_TOKEN"
```

#### Download Export

```bash
curl "http://localhost:8001/api/patentpulse/reclaim/{file_id}/download" \
  -H "Cookie: session=YOUR_SESSION_TOKEN" \
  -o reclaim_pack.pdf
```

#### Delete Export

```bash
curl -X DELETE "http://localhost:8001/api/patentpulse/reclaim/{file_id}" \
  -H "Cookie: session=YOUR_SESSION_TOKEN"
```

---

### 3. Frontend UI

#### Accessing the UI

1. Navigate to: `/admin/patentpulse/reclaim`
2. Ensure Admin 2FA is completed
3. Select export options:
   - **Format**: PDF or JSON
   - **Limit**: 5, 10, 25, or 50 patents
   - **Country**: Optional filter
   - **Status**: Required (Expired, ExpiringSoon, Lapsed)

4. Click **"Generate Export"**
5. Wait for success toast
6. Download from **Recent Exports** table

#### UI Features

- **Real-time Generation**: Live progress with loading spinner
- **Recent Exports Table**: View all exports with metadata
- **Download Links**: Authenticated, time-limited URLs
- **Auto-Refresh**: Table updates after generation
- **Error Handling**: User-friendly messages for failures

---

## Export Formats

### PDF Structure

**Page 1: Cover & Summary**
- Report title and generation timestamp
- Summary metrics table:
  - Total opportunities
  - Average viability score
  - Average commercial score
  - Top assignee
  - Top country

**Page 2+: Patent Opportunities Table**
- Patent ID
- Title (truncated to 40 chars)
- Assignee
- Country
- Status
- Viability score

**Last Page: Legal Disclaimer**
- FTO notice
- Internal use only warning
- Compliance text

### JSON Structure

```json
{
  "metadata": {
    "generated_at": "2025-11-11T14:30:22Z",
    "generator": "PatentPulse Reclaim Pack v1.0",
    "criteria": {
      "limit": 10,
      "status_filter": ["Expired"],
      "country_filter": null
    }
  },
  "summary": {
    "total_items": 10,
    "avg_viability": 0.782,
    "avg_commercial": 0.754,
    "top_assignee": "Novo Nordisk",
    "top_country": "US"
  },
  "items": [
    {
      "patent_id": "US1234567",
      "title": "Novel peptide therapeutic composition...",
      "assignee": "Novo Nordisk",
      "country": "US",
      "status": "Expired",
      "expiry_date": "2023-05-15T00:00:00Z",
      "commercial_score": 0.70,
      "commercial_score_adj": 0.75,
      "fto_risk": 0.25,
      "synthesis_score": 0.40,
      "market_factor": 0.68,
      "viability_score": 0.821,
      "repurpose_notes": "Potential for commercial repurposing..."
    }
    // ... more items
  ],
  "totals": {
    "by_status": {
      "Expired": 8,
      "ExpiringSoon": 2
    },
    "by_country": {
      "US": 6,
      "EP": 3,
      "JP": 1
    }
  },
  "disclaimer": "IMPORTANT LEGAL NOTICE: ..."
}
```

---

## Database Schema

### Collection: `patentpulse_exports`

```javascript
{
  _id: ObjectId,
  file_id: "a1b2c3d4-...",              // UUID for download
  file_name: "patentpulse-reclaim-....pdf",
  format: "pdf",                        // "pdf" | "json"
  criteria: {
    limit: 10,
    status_filter: ["Expired"],
    country_filter: "US"
  },
  count: 10,                            // Number of items
  generated_at: ISODate("2025-11-11T14:30:22Z"),
  expires_at: ISODate("2025-11-18T14:30:22Z"),   // TTL
  viability_avg: 0.782,
  top_country: "US",
  created_by: "admin@example.com",      // Optional
  file_path: "/app/exports/patentpulse-reclaim-....pdf",
  size_kb: 245
}
```

### Indexes

```python
# TTL index for auto-cleanup
db.patentpulse_exports.create_index(
    "expires_at",
    name="patentpulse_exports_expires_at_ttl",
    expireAfterSeconds=0
)

# Query performance
db.patentpulse_exports.create_index(
    [("generated_at", -1)],
    name="generated_at_desc_idx"
)
```

---

## CI/CD Integration

### GitHub Actions Workflow

File: `.github/workflows/reclaim-pack-ci.yml`

**Triggers:**
- Push to `main`, `develop`, `feature/patentpulse`
- Pull requests to `main`, `develop`
- Changes to reclaim pack files

**Jobs:**
1. **backend-tests**: Run Python tests, generate sample PDF
2. **frontend-tests**: TypeScript typecheck, build, unit & E2E tests
3. **integration-test**: Full stack test with mock auth

**Artifacts:**
- `sample-reclaim-pack`: Generated PDF sample
- `playwright-reclaim-report`: Test reports on failure
- `playwright-reclaim-traces`: Debug traces on failure

### Running CI Locally

```bash
# Backend tests
cd backend
FEATURE_PATENTPULSE_RECLAIM=true pytest tests/test_reclaim_pack.py -v

# Frontend tests
cd frontend
npm run test:reclaim:unit
npm run test:reclaim:e2e

# Generate sample
cd backend
FEATURE_PATENTPULSE_RECLAIM=true python jobs/reclaim_pack_generator.py \
  --format pdf --limit 5 --out /tmp
```

---

## Compliance & Legal

### FTO Disclaimer (Included in All Exports)

```
IMPORTANT LEGAL NOTICE:

PatentPulse data represents publicly available patent filings and 
derived analytics. This report is for INTERNAL INTELLIGENCE PURPOSES 
ONLY and does not constitute:
- Legal advice
- Freedom-to-Operate (FTO) clearance
- Guarantee of commercial viability

ALWAYS verify freedom-to-operate with qualified patent counsel before 
commercialization. Patent statuses and rights may change. Conduct 
comprehensive due diligence.

Peptimancer™ disclaims all warranties. Use at your own risk.
```

### Data Privacy

- **No PII**: Exports contain only public patent data and analytics
- **Authenticated Access**: All downloads require valid session tokens
- **Time-Limited**: Exports auto-delete after `EXPORT_TTL_DAYS` (default: 7)
- **Audit Trail**: All generations logged in `patentpulse_exports`

---

## Troubleshooting

### Issue 1: "Feature Not Enabled"

**Symptoms:**
- UI shows "Feature Not Enabled" message
- API returns 503 error

**Solution:**
```bash
# Set feature flag
export FEATURE_PATENTPULSE_RECLAIM=true

# Restart backend
sudo supervisorctl restart backend
```

### Issue 2: "Admin 2FA Required"

**Symptoms:**
- UI shows "Two-Factor Authentication Required"
- API returns 403 error

**Solution:**
1. Navigate to Admin settings
2. Complete 2FA setup
3. Re-authenticate with 2FA code

### Issue 3: PDF Generation Fails

**Symptoms:**
- CLI error: `reportlab not installed`
- API 500 error during PDF generation

**Solution:**
```bash
# Install reportlab
pip install reportlab

# Verify installation
python -c "from reportlab.lib.pagesizes import letter; print('OK')"
```

### Issue 4: Font Issues in PDF

**Symptoms:**
- PDF contains garbled text
- Font warning in logs

**Solution:**
```bash
# Use fallback font
export PDF_FONT=Helvetica

# Or install specific fonts
# (OS-dependent, e.g., apt-get install fonts-liberation)
```

### Issue 5: Export Directory Permissions

**Symptoms:**
- CLI error: `Permission denied`
- Cannot write to export directory

**Solution:**
```bash
# Create directory with correct permissions
mkdir -p /app/exports
chmod 755 /app/exports

# Or use custom directory
export RECLAIM_EXPORT_DIR=/tmp/exports
mkdir -p /tmp/exports
```

### Issue 6: Old Exports Not Cleaning Up

**Symptoms:**
- Disk space filling up
- TTL not working

**Solution:**
```bash
# Check TTL index exists
cd backend
python -c "
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def check():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['peptimancer_db']
    indexes = await db.patentpulse_exports.list_indexes().to_list(None)
    for idx in indexes:
        if 'expires_at' in str(idx):
            print('✓ TTL index found:', idx)
            return
    print('✗ TTL index missing - run scripts/create_indexes.py')
    client.close()

asyncio.run(check())
"

# Recreate indexes
python scripts/create_indexes.py
```

---

## Best Practices

### For Developers

1. **Always Gate with Feature Flag**: Check `FEATURE_PATENTPULSE_RECLAIM` before enabling
2. **Validate Inputs**: Enforce limits, validate status/country filters
3. **Error Handling**: Graceful failures with user-friendly messages
4. **Test with Mock Data**: Seed test patents for CI/development
5. **Monitor Export Size**: Cap items to prevent massive files

### For Admins

1. **Regular Cleanup**: Monitor `/app/exports` disk usage
2. **Review Exports**: Audit `patentpulse_exports` collection monthly
3. **Update Disclaimers**: Keep FTO text current with legal guidance
4. **Backup Exports**: Copy critical exports before TTL expiry
5. **Access Control**: Limit 2FA-enabled admins

### For End Users

1. **Select Appropriate Filters**: Narrow by status/country for targeted results
2. **Download Promptly**: Exports expire after 7 days
3. **Verify Data**: Cross-reference with source patents before decisions
4. **Consult Legal**: Always get FTO clearance from patent counsel
5. **Keep Confidential**: Treat exports as internal intelligence only

---

## Screenshots

### UI Export Panel
![Export Panel](placeholder-export-panel.png)
*Export generation form with filters and recent exports table*

### Sample PDF Page
![PDF Sample](placeholder-pdf-sample.png)
*Cover page and opportunities table from generated PDF*

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-11 | Initial release (Phase IXe) |
| - | - | - CLI generator (PDF/JSON) |
| - | - | - API endpoints (export, list, download, delete) |
| - | - | - Frontend UI with filters |
| - | - | - Viability score calculation |
| - | - | - TTL-based auto-cleanup |
| - | - | - Legal disclaimers |

---

## Support & Resources

- **Documentation**: This file (`docs/RECLAIM_PACKS.md`)
- **API Reference**: See `routes/patentpulse_reclaim.py` docstrings
- **Code Examples**: Check `tests/` directory for usage patterns
- **CI Logs**: GitHub Actions → "Reclaim Pack CI" workflow

**Maintained by**: Peptimancer Platform Team  
**Last Updated**: 2025-11-11  
**Contact**: [support@peptimancer.com](mailto:support@peptimancer.com)
