# PatentPulse - Patent Mining & Commercialization Intelligence

> ⚖️ **Legal Disclaimer:** PatentPulse intelligence uses public-domain patent filings from USPTO, WIPO, EPO, and other sources. Continuation applications, patent families, and regional variants are not comprehensively tracked. **Verify freedom-to-operate (FTO) with qualified IP counsel before initiating commercialization activities.** This tool provides preliminary intelligence only and does not constitute legal advice.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [API Endpoints & Schemas](#api-endpoints--schemas)
3. [Feature Flag & Kill Switch](#feature-flag--kill-switch)
4. [SLOs & Error Budget Policy](#slos--error-budget-policy)
5. [Data Quality Guardrails](#data-quality-guardrails)
6. [Rollback Procedure](#rollback-procedure)
7. [Operations Runbook](#operations-runbook)
8. [Observability Dashboards](#observability-dashboards)

---

## Architecture Overview

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  Patent Sources │────▶│  Collector   │────▶│  MongoDB    │
│  (USPTO, WIPO)  │     │  (Weekly)    │     │  patents    │
└─────────────────┘     └──────────────┘     └──────┬──────┘
                                                     │
                                                     │
                                                     ▼
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   Admin UI      │◀────│  FastAPI     │◀────│  Indexes    │
│  /admin/patent  │     │  Backend     │     │  (7 total)  │
└─────────────────┘     └──────────────┘     └─────────────┘
```

### Components

**1. Collector (`jobs/patentpulse_collector.py`)**
- Runs weekly (Sunday 3 AM via cron)
- Fetches patents from USPTO, WIPO, EPO, Lens.org APIs
- Filters: Expired, Lapsed, Expiring ≤ 24 months
- Extracts sequences, calculates scores
- Upserts to MongoDB (idempotent on `patent_id`)

**2. Backend API (`routes_patentpulse.py`)**
- 3 endpoints: `/items`, `/stats`, `/top-opportunities`
- Protected by JWT + Admin 2FA
- Feature flag gated: `FEATURE_PATENTPULSE`

**3. Frontend Dashboard (`pages/PatentPulsePage.tsx`)**
- Stats tiles: Total, Ready, Expiring, Avg Commercial Score
- Top 5 opportunities (viability score ranking)
- Filterable patent database
- Responsive design with Recharts

**4. Database (`patentpulse_items` collection)**
- 7 indexes for query optimization
- Unique constraint on `patent_id`
- TTL index on `created_at` (optional)

---

## API Endpoints & Schemas

### Base URL
```
https://partner-purge.preview.emergentagent.com/api/patentpulse
```

### 1. GET /items
**Description:** Search and filter patents with pagination

**Query Parameters:**
- `status_filter` (string): "Expired", "Lapsed", "Expiring"
- `country` (string): "US", "EP", "WO", "JP", "CA"
- `min_commercial_score` (float): 0.0 - 1.0
- `limit` (int): Max 100, default 50
- `skip` (int): Pagination offset

**Response Schema:**
```json
{
  "items": [
    {
      "_id": "string",
      "title": "string",
      "patent_id": "string",
      "assignee": "string",
      "country": "string",
      "expiry_date": "2023-05-17T00:00:00Z",
      "status": "Expired",
      "keywords": ["peptide", "GLP-1"],
      "sequence_data": "His-Ala-Glu-Gly...",
      "commercial_score": 0.88,
      "synthesis_score": 0.34,
      "fto_risk": 0.22,
      "repurpose_notes": "string",
      "created_at": "2025-11-11T00:00:00Z",
      "updated_at": "2025-11-11T00:00:00Z"
    }
  ],
  "count": 20,
  "total": 41,
  "skip": 0,
  "limit": 50
}
```

### 2. GET /stats
**Description:** Aggregate statistics and analytics

**Response Schema:**
```json
{
  "total": 41,
  "by_status": {
    "Expired": 20,
    "Lapsed": 10,
    "Expiring": 11
  },
  "top_assignees": [
    {"assignee": "BioNova Labs", "count": 5}
  ],
  "avg_commercial_score": 0.685,
  "avg_synthesis_score": 0.423,
  "avg_fto_risk": 0.287,
  "expiring_soon_24mo": 11
}
```

### 3. GET /top-opportunities
**Description:** Top patents ranked by composite viability score

**Query Parameters:**
- `limit` (int): Max 50, default 10

**Response Schema:**
```json
{
  "opportunities": [
    {
      "patent_id": "EP8083369",
      "title": "string",
      "viability_score": 0.5174,
      "commercial_score": 0.84,
      "synthesis_score": 0.30,
      "fto_risk": 0.12,
      ...
    }
  ],
  "count": 5
}
```

**Viability Score Formula:**
```
viability = commercial_score × (1 - synthesis_score) × (1 - fto_risk)
```

---

## Feature Flag & Kill Switch

### Environment Variable
```bash
FEATURE_PATENTPULSE=true  # Enable PatentPulse
FEATURE_PATENTPULSE=false # Disable (kill switch)
```

### Behavior

**When ENABLED (`true`):**
- All 3 endpoints return data
- Frontend dashboard renders normally
- Collector job runs on schedule

**When DISABLED (`false`):**
- All endpoints return `503 Service Unavailable`
- Frontend shows "Feature not enabled" message
- Collector job exits early with log message

### Kill Switch Activation

**Emergency Disable:**
```bash
# Method 1: Environment variable
export FEATURE_PATENTPULSE=false
sudo supervisorctl restart backend

# Method 2: Makefile
make rollback-canary
```

**Re-enable After Fix:**
```bash
export FEATURE_PATENTPULSE=true
sudo supervisorctl restart backend
make verify-canary  # Ensure healthy before promotion
```

---

## SLOs & Error Budget Policy

### Service Level Objectives

| Metric | SLO Target | Measurement Window |
|--------|------------|-------------------|
| **Latency (p95)** | ≤ 900ms | 5 minutes |
| **Error Rate (5xx)** | ≤ 2% | 5 minutes |
| **Availability** | ≥ 99.5% | 30 days |
| **Collector Success Rate** | ≥ 95% | 7 days |

### Error Budget

**Monthly Error Budget:** 0.5% downtime = ~3.6 hours/month

**Budget Consumption Triggers:**
- **25% consumed:** Warning alert to on-call
- **50% consumed:** Incident review required
- **75% consumed:** Feature freeze, focus on reliability
- **100% consumed:** Automatic kill switch activation

**Error Budget Calculation:**
```python
error_budget = 1 - (successful_requests / total_requests)
consumption_rate = error_budget / error_budget_threshold
```

### Auto-Rollback Thresholds

PatentPulse will **automatically rollback** if:
- p95 latency > 900ms for 5+ consecutive minutes
- Error rate > 2% for 5+ consecutive minutes
- 3+ collector failures in a row
- Auth/RBAC violation detected
- Data migration checksum mismatch

---

## Data Quality Guardrails

### Required Fields Validation

Every patent document MUST contain:
```python
required_fields = [
    'title',           # string, non-empty
    'patent_id',       # string, unique
    'status',          # enum: Expired, Lapsed, Expiring
    'commercial_score',# float, 0.0 - 1.0
    'synthesis_score', # float, 0.0 - 1.0
    'fto_risk',        # float, 0.0 - 1.0
    'expiry_date'      # datetime, must be in the past for Expired/Lapsed
]
```

### Score Range Validation

```python
assert 0.0 <= commercial_score <= 1.0
assert 0.0 <= synthesis_score <= 1.0
assert 0.0 <= fto_risk <= 1.0
```

### Idempotency Rules

**Collector Upsert Logic:**
```python
collection.update_one(
    {"patent_id": patent_id},      # Match on unique ID
    {"$set": patent_doc},           # Update document
    upsert=True                      # Insert if not exists
)
```

**Duplicate Prevention:**
- Unique index on `patent_id`
- Post-collection verification: `duplicates_count == 0`
- Collector dry-run before production

### Sequence Data Validation

```python
# Amino acid format: 3-letter codes separated by hyphens
sequence_pattern = r'^[A-Z][a-z]{2}(-[A-Z][a-z]{2})*$'
# Example: His-Ala-Glu-Gly-Val-Lys

# Length constraints
assert 8 <= len(sequence.split('-')) <= 25
```

---

## Rollback Procedure

### Pre-Rollback Checklist

1. **Confirm Issue Severity:**
   - SLO breach confirmed (p95 > 900ms or error rate > 2%)
   - User-impacting outage or data corruption
   - Security vulnerability detected

2. **Notify Stakeholders:**
   - Alert on-call engineer
   - Post in #incidents Slack channel
   - Update status page

### Rollback Steps

#### Option A: Feature Flag Kill Switch (Fast)
```bash
# 1. Disable feature flag
export FEATURE_PATENTPULSE=false
sudo supervisorctl restart backend

# 2. Verify disabled
curl -s http://localhost:8001/api/patentpulse/items
# Expected: 503 Service Unavailable

# 3. Monitor recovery
make check-slos
```
**Recovery Time:** ~30 seconds

#### Option B: Git Tag Revert (Full Rollback)
```bash
# 1. Revert to pre-integration tag
cd /app
git checkout pre-patentpulse-20251111-1950

# 2. Restart services
sudo supervisorctl restart all

# 3. Verify rollback
make health-check
make verify-canary

# 4. Tag rollback event
git tag "rollback-patentpulse-$(date +%Y%m%d-%H%M)"
```
**Recovery Time:** ~2 minutes

#### Option C: Database Rollback (Data Issue)
```bash
# 1. Stop collector
crontab -e  # Comment out collector job

# 2. Drop collection
mongosh peptimancer_db --eval "db.patentpulse_items.drop()"

# 3. Restore from backup
make db-restore BACKUP_PATH=./backups/patentpulse-20251111-1950

# 4. Verify data integrity
python jobs/post_deploy_verifier.py
```
**Recovery Time:** ~5-10 minutes

### Post-Rollback Actions

1. **Verify System Health:**
   ```bash
   make verify-canary
   make check-slos
   ```

2. **Root Cause Analysis:**
   - Review error logs
   - Check metrics dashboards
   - Identify failure mode

3. **Incident Post-Mortem:**
   - Timeline of events
   - Root cause identified
   - Action items to prevent recurrence
   - Update runbook with learnings

4. **Roll-Forward Plan:**
   - Fix identified issues
   - Add regression tests
   - Dry-run in staging
   - Re-deploy with canary

---

## Operations Runbook

### Symptom → Diagnosis → Fix Table

| Symptom | Checks | Likely Cause | Fix |
|---------|--------|--------------|-----|
| `/items` returns 500 | Check Mongo connection, indexes | Missing index or DB down | Run `python scripts/create_indexes.py`, restart MongoDB |
| `/items` returns 503 | Check `FEATURE_PATENTPULSE` env var | Feature flag disabled | Set `FEATURE_PATENTPULSE=true`, restart backend |
| High p95 latency (>900ms) | Check DB query explain, index usage | Unindexed query or large result set | Add index, reduce query scope, add caching |
| Collector job failed | Check logs, API rate limits | External API timeout or rate limit | Implement retry logic, increase timeout |
| Duplicate patents | Check `patent_id` index, collector logic | Race condition or index missing | Rebuild unique index, fix upsert logic |
| Missing patents | Check collector logs, API responses | API filter too strict or pagination bug | Adjust filters, fix pagination |
| FTO risk scores invalid | Check data validation, score calculation | Input data quality issue | Re-run collector with fixed validation |

### Common Operations

#### Check Service Health
```bash
# Quick health check
make health-check

# Full SLO check
make check-slos

# View recent logs
make view-logs
```

#### Trigger Manual Collection
```bash
# Dry-run first (safe)
make dry-run-collector

# Production run
make run-collector
```

#### Database Maintenance
```bash
# Backup collection
make db-backup

# Restore from backup
make db-restore BACKUP_PATH=./backups/patentpulse-YYYYMMDD

# Check collection stats
mongosh peptimancer_db --eval "db.patentpulse_items.stats()"
```

#### Re-seed Development Data
```bash
make seed-dev
```

---

## Observability Dashboards

### Grafana Dashboard: PatentPulse Health & Performance

**Access:** https://grafana.peptimancer.com/d/patentpulse

**Panels:**

1. **PatentPulse Health Status** (Stat)
   - Metric: Success rate (non-5xx / total requests)
   - Alert: Health < 98% for 5 min → Warning

2. **Collector Runtime & Last Success** (Stat)
   - Metric: Time since last successful run
   - Alert: Last success > 24 hours ago → Critical

3. **p95 Latency per Endpoint** (Graph)
   - Metrics: `/items`, `/stats`, `/top-opportunities`
   - Alert: p95 > 900ms for 5 min → Warning

4. **Patent Count per Week** (Graph)
   - Metric: New patents collected weekly
   - Trend: Should be positive and consistent

5. **Top Assignees by Viability** (Bar Gauge)
   - Metric: Top 5 assignees by sum viability score
   - Use: Identify high-value patent clusters

6. **FTO Risk Distribution** (Pie Chart)
   - Metric: Patents grouped by risk level (Low < 0.3, Med 0.3-0.6, High > 0.6)
   - Use: Assess overall portfolio risk

7. **Error Rate (5xx)** (Graph)
   - Metric: 5xx responses / total requests
   - Alert: Error rate > 2% for 5 min → Critical

8. **Request Rate** (Graph)
   - Metric: Total requests/second
   - Use: Capacity planning

9. **Collector Health** (Table)
   - Metrics: New patents, updated patents, errors, duration
   - Last run timestamp

### Alert Routing

**Severity Levels:**
- **Critical:** PagerDuty page + Slack #incidents
- **Warning:** Slack #alerts-patentpulse
- **Info:** Logged only

**On-Call Schedule:**
- Primary: SRE team rotation
- Secondary: Backend team lead
- Escalation: Engineering manager

---

## Additional Resources

- **API Documentation:** https://peptimancer.com/api/docs#patentpulse
- **Grafana Dashboard:** https://grafana.peptimancer.com/d/patentpulse
- **Incident Log:** https://peptimancer.atlassian.net/wiki/patentpulse-incidents
- **Team Contact:** #patentpulse-dev Slack channel

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-11 | Initial release - Phase IXb integration |

---

**Maintained by:** Peptimancer Platform Team  
**Last Updated:** 2025-11-11  
**Review Cycle:** Quarterly


---

## Phase IXc: Production-Grade Collector

### Overview

Phase IXc transforms the PatentPulse collector from an MVP into a production-grade, idempotent, incremental, and self-healing data pipeline.

### Key Features

- **Idempotent Upserts:** Re-running with same inputs produces zero duplicates
- **Incremental Sync:** Tracks last successful run and only fetches changed patents
- **Dead Letter Queue (DLQ):** Failed items are quarantined for reprocessing
- **SLO Monitoring:** Tracks p95 latency, error rate, and DQ reject rate
- **Feature Flags:** Safe-by-default with `FEATURE_PATENTPULSE` gate

### Architecture

```
┌─────────────────────┐
│ Patent Sources      │
│ (USPTO, WIPO, LENS) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Source Adapters     │
│ - Pagination        │
│ - Retry with backoff│
│ - Mock/Real modes   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Normalizer          │
│ - Patent ID derive  │
│ - Data quality      │
│ - Score computation │
└──────────┬──────────┘
           │
           ├─── Valid ───▶ Upsert (patentpulse_items)
           │
           └─── Invalid ▶ DLQ (patentpulse_dlq)
```

### CLI Usage

```bash
# Dry-run (no DB writes)
python jobs/patentpulse_collector.py --mode dry-run --since 2025-10-01T00:00:00Z --verbose

# Live mode (requires feature flag)
FEATURE_PATENTPULSE=true python jobs/patentpulse_collector.py --mode live --limit 500

# Incremental sync (auto-detects last successful run)
FEATURE_PATENTPULSE=true python jobs/patentpulse_collector.py --mode live

# Source filtering
python jobs/patentpulse_collector.py --mode dry-run --source uspto --limit 100
```

### Data Quality Rules

**Required Fields:**
- `patent_id` (5-50 chars, unique)
- `title` (10-500 chars)
- `status` (Expired|Lapsed|ExpiringSoon)
- `commercial_score`, `synthesis_score`, `fto_risk` (0.0-1.0)
- `expiry_date` (datetime, validated against status)

**Sequence Validation:**
- Format: 3-letter AA codes (`His-Ala-Glu-...`) or single-letter (`HAEGVK...`)
- Length: 8-25 amino acids
- Characters: Valid 20 amino acids only

**Status-Date Consistency:**
- `Expired`/`Lapsed`: `expiry_date` < now
- `ExpiringSoon`: `expiry_date` within next 24 months

### Dead Letter Queue (DLQ)

**Purpose:** Failed items are sent to DLQ for manual review and reprocessing

**DLQ Reprocessor:**
```bash
# Dry-run reprocessing
python jobs/patentpulse_dlq_reprocessor.py --max-retries 3 --dry-run

# Live reprocessing
FEATURE_PATENTPULSE=true python jobs/patentpulse_dlq_reprocessor.py
```

**DLQ Schema:**
```json
{
  "dlq_id": "uuid",
  "patent_id": "US1234567",
  "source": "USPTO",
  "payload": {...},
  "reason": "data_quality_violation",
  "retries": 2,
  "first_failed_at": "2025-11-11T00:00:00Z",
  "last_failed_at": "2025-11-11T01:00:00Z",
  "last_error": "Title too short"
}
```

### Run Metadata

Each collector run persists metadata to `patentpulse_runs` collection:

```json
{
  "run_id": "uuid",
  "started_at": "2025-11-11T00:00:00Z",
  "finished_at": "2025-11-11T00:05:00Z",
  "mode": "live",
  "sources": ["USPTO", "WIPO", "LENS"],
  "params": {"since": "...", "until": "...", "limit": 500},
  "counts": {
    "fetched": 150,
    "normalized": 145,
    "upserts": 120,
    "updates": 25,
    "unchanged": 0,
    "rejected": 5,
    "dlq": 5,
    "duplicates": 0
  },
  "errors": [],
  "status": "success",
  "slo": {
    "p95_ms": 450,
    "error_rate": 0.0333,
    "dq_reject_rate": 0.0333
  },
  "notes": ""
}
```

### SLO Gates

Collector runs are validated against:

| Metric | Target | Gate |
|--------|--------|------|
| p95 latency | ≤ 900ms | Fail if exceeded |
| Error rate | ≤ 2% | Fail if exceeded |
| DQ reject rate | ≤ 5% | Fail if exceeded |
| Duplicates | 0 | Fail if any found |

**Auto-Rollback:** If SLO gates fail for 2 consecutive runs, feature flag is auto-disabled.

### Troubleshooting

**Issue:** Collector fails with "Feature flag not enabled"
- **Fix:** Set `FEATURE_PATENTPULSE=true` in environment

**Issue:** High DQ reject rate
- **Cause:** Source API data quality degraded
- **Fix:** Inspect DLQ, improve normalizer, or contact source provider

**Issue:** Duplicates detected
- **Cause:** Race condition or index missing
- **Fix:** Rebuild unique index on `patent_id`, check collector logic

**Issue:** Incremental sync not working
- **Cause:** No successful runs in `patentpulse_runs`
- **Fix:** Run with explicit `--since` parameter, verify run status

---

## Phase IXd: Market Signal Enrichment

### Overview

Phase IXd enriches patent commercial scores with real-time market intelligence signals including pricing, search trends, social sentiment, and marketplace activity.

### Key Features

- **Multi-Source Signal Aggregation:** Vendor catalogs, search trends, social chatter, marketplace data
- **Dynamic Score Adjustment:** Adjusts `commercial_score` based on market factor (0-1)
- **TTL Caching:** 24-hour cache prevents redundant API calls
- **Floor Clamp Protection:** Prevents score drops >0.25 in single run
- **Configurable Weights:** Tune base vs. market signal influence

### Architecture

```
┌─────────────────────┐
│ Patent Item         │
│ base commercial     │
│ score = 0.7         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Market Signals      │
│ - Vendor pricing    │
│ - Search trends     │
│ - Social sentiment  │
│ - Marketplace       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Market Factor       │
│ calculation = 0.65  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Adjusted Score      │
│ 0.6*base + 0.4*mkt  │
│ = 0.68 (Δ -0.02)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Update Patent       │
│ commercial_score_adj│
│ + breakdown         │
└─────────────────────┘
```

### CLI Usage

```bash
# Dry-run enrichment
python jobs/market_signals_enricher.py --mode dry-run --limit 50

# Live enrichment (requires feature flag)
FEATURE_PATENTPULSE_SIGNALS=true python jobs/market_signals_enricher.py --mode live --limit 200

# Enrich only recent items
python jobs/market_signals_enricher.py --mode live --since 2025-11-01T00:00:00Z

# Custom weights (higher market influence)
python jobs/market_signals_enricher.py --mode live --weights "base:0.4,market:0.6"
```

### Signal Adapters

**1. VendorCatalogAdapter**
- Fetches pricing and availability from peptide vendors
- Returns: `avg_price`, `price_dispersion`, `availability_score`
- Mock mode generates realistic pricing data

**2. SearchTrendAdapter**
- Fetches search volume trends (Google Trends-like)
- Returns: `search_index` (0-100, normalized to 0-1)
- Higher index = more commercial interest

**3. SocialChatterAdapter**
- Fetches social media mentions and sentiment
- Returns: `sentiment` (-1 to 1), `volume` (mention count)
- Tracks Twitter, Reddit, LinkedIn, biotech forums

**4. MarketplaceAdapter**
- Fetches transaction data from biotech marketplaces
- Returns: `transaction_count`, `velocity_score` (0-1)
- Indicates actual commercial activity

### Market Factor Calculation

**Formula:**
```
market_factor = clamp(
    0.35 * search_index +
    0.25 * availability_score +
    0.20 * (1 - sigmoid(price_dispersion)) +
    0.20 * max(sentiment, 0),
    0, 1
)
```

**Adjusted Score:**
```
adjusted = clamp(
    base_weight * commercial_score + market_weight * market_factor,
    commercial_score - 0.25,  # Floor clamp
    1.0
)
```

**Default Weights:** `base=0.6, market=0.4`

### API Endpoints

**1. GET /api/patentpulse/signals/{patent_id}**

Get market signals for a specific patent.

**Response:**
```json
{
  "patent_id": "US1234567",
  "features": {
    "avg_price": 1250.50,
    "price_dispersion": 0.35,
    "availability_score": 0.75,
    "search_index": 0.68,
    "social_sentiment": 0.42,
    "social_volume": 156,
    "market_velocity": 0.55
  },
  "provenance": [
    {
      "source": "VendorCatalogAdapter",
      "ts": "2025-11-11T12:00:00Z",
      "meta": {"vendor_count": 5}
    }
  ],
  "computed_at": "2025-11-11T12:00:00Z",
  "breakdown": {
    "base": 0.7,
    "market_factor": 0.65,
    "weights": {"base": 0.6, "market": 0.4},
    "inputs": {...}
  }
}
```

**2. POST /api/patentpulse/signals/recompute**

Trigger recomputation of market signals (queues enrichment job).

**Request:**
```json
{
  "patent_ids": ["US1234567", "EP8083369"],
  "since": "2025-11-01T00:00:00Z",
  "limit": 50,
  "weights": {"base": 0.5, "market": 0.5}
}
```

**3. GET /api/patentpulse/items/{patent_id}/score**

Get detailed score breakdown for a patent.

**Response:**
```json
{
  "patent_id": "US1234567",
  "base_score": 0.70,
  "adjusted_score": 0.68,
  "delta": -0.02,
  "market_factor": 0.65,
  "breakdown": {...},
  "market_last_refreshed_at": "2025-11-11T12:00:00Z"
}
```

### TTL Cache

**Purpose:** Prevent redundant API calls within 24 hours

**Implementation:**
- Signals cached in `patentpulse_signals` collection
- TTL index on `ttl_expires_at` field (MongoDB auto-deletes expired docs)
- Enricher checks cache before fetching fresh signals

**Cache Hit Flow:**
```
1. Check patentpulse_signals for patent_id
2. If found and ttl_expires_at > now → use cached
3. Else → fetch fresh signals, cache with ttl_expires_at = now + 24h
```

### Floor Clamp Protection

**Problem:** Market signals can cause drastic score drops, confusing users

**Solution:** Floor clamp prevents adjusted score from dropping >0.25 below base

**Example:**
```
Base score: 0.9
Market factor: 0.1 (very negative signals)
Raw adjusted: 0.6 * 0.9 + 0.4 * 0.1 = 0.58 (Δ -0.32)
Floor clamp: max(0.58, 0.9 - 0.25) = 0.65 (Δ -0.25)
```

**Warning:** Clamping events are logged and counted for monitoring

### Database Schema

**patentpulse_items (updated):**
```json
{
  "patent_id": "US1234567",
  "commercial_score": 0.70,          // BASELINE
  "commercial_score_adj": 0.68,      // ADJUSTED (Phase IXd)
  "commercial_breakdown": {           // NEW
    "base": 0.70,
    "market_factor": 0.65,
    "weights": {"base": 0.6, "market": 0.4},
    "inputs": {...}
  },
  "market_last_refreshed_at": "2025-11-11T12:00:00Z"  // NEW
}
```

**patentpulse_signals (new collection):**
```json
{
  "signal_id": "uuid",
  "patent_id": "US1234567",
  "keyword_key": "glp-1_insulin_peptide",  // Fallback for generic queries
  "features": {...},
  "provenance": [...],
  "computed_at": "2025-11-11T12:00:00Z",
  "ttl_expires_at": "2025-11-12T12:00:00Z"  // TTL index
}
```

### Troubleshooting

**Issue:** Enricher fails with "Feature flag not enabled"
- **Fix:** Set `FEATURE_PATENTPULSE_SIGNALS=true`

**Issue:** All signals return mock data
- **Cause:** Real API keys not configured
- **Fix:** Set `FEATURE_PATENTPULSE_SOURCES=true` and provide API keys

**Issue:** Adjusted scores not updating in UI
- **Cause:** Frontend not reading `commercial_score_adj` field
- **Fix:** Update UI to display adjusted score with delta badge

**Issue:** Too many API calls (cost concern)
- **Cause:** TTL cache not working or expired
- **Fix:** Verify TTL index exists, increase cache duration if needed

**Issue:** Clamping too frequent (>10% of enrichments)
- **Cause:** Market signals overly negative or weights misconfigured
- **Fix:** Adjust weights to increase base influence (e.g., `base:0.7,market:0.3`)

### Monitoring

**Key Metrics:**
- **Enrichment rate:** Items enriched per hour
- **Cache hit rate:** % of enrichments using cached signals
- **Clamp rate:** % of enrichments triggering floor clamp
- **Adapter error rate:** % of signal fetches failing per adapter

**Alerts:**
- Adapter error rate > 5% for 5 min → Warning
- Cache hit rate < 50% → Info (possible TTL index issue)
- Clamp rate > 15% → Warning (weights may need tuning)

---

## Change Log (Updated)

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-11 | Initial release - Phase IXb integration |
| 1.1 | 2025-11-11 | Phase IXc - Production collector with idempotency, DLQ, SLO |
| 1.2 | 2025-11-11 | Phase IXd - Market signal enrichment with TTL cache |

---

**Maintained by:** Peptimancer Platform Team  
**Last Updated:** 2025-11-11  
**Review Cycle:** Quarterly
