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
https://peptide-designer-5.preview.emergentagent.com/api/patentpulse
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
