# Cron Job Setup for Background Tasks

This document describes how to set up scheduled background jobs for Peptimancer.

---

## Jobs to Schedule

### 1. Share Link Cleaner (`share_link_cleaner.py`)

**Purpose:** Expire old share links and cleanup analytics events

**Frequency:** Daily at 2:00 AM UTC

**Command:**
```bash
/usr/bin/python3 /app/backend/jobs/share_link_cleaner.py
```

**Cron Entry:**
```cron
0 2 * * * cd /app/backend && /usr/bin/python3 jobs/share_link_cleaner.py >> /var/log/share_cleaner.log 2>&1
```

**What it does:**
- Marks expired shares as `expired`
- Sends reminder emails for shares expiring soon (if configured)
- Cleans up old analytics events (>90 days)

---

## Setup Instructions

### Option 1: System Crontab (Recommended for Production)

1. **Open crontab editor:**
   ```bash
   crontab -e
   ```

2. **Add job entries:**
   ```cron
   # Peptimancer Background Jobs
   0 2 * * * cd /app/backend && /usr/bin/python3 jobs/share_link_cleaner.py >> /var/log/share_cleaner.log 2>&1
   ```

3. **Save and exit**

4. **Verify cron jobs:**
   ```bash
   crontab -l
   ```

### Option 2: Kubernetes CronJob (Recommended for K8s)

Create a CronJob manifest:

```yaml
# k8s/cronjobs/share-cleaner.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: share-link-cleaner
  namespace: peptimancer
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM UTC
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: share-cleaner
            image: peptimancer-backend:latest
            command:
            - /usr/bin/python3
            - /app/backend/jobs/share_link_cleaner.py
            env:
            - name: MONGO_URL
              valueFrom:
                secretKeyRef:
                  name: peptimancer-secrets
                  key: mongo-url
            - name: DB_NAME
              value: "peptimancer_db"
            resources:
              requests:
                memory: "256Mi"
                cpu: "100m"
              limits:
                memory: "512Mi"
                cpu: "200m"
          restartPolicy: OnFailure
```

Deploy:
```bash
kubectl apply -f k8s/cronjobs/share-cleaner.yaml
```

### Option 3: Supervisor (Development Only)

For development, you can run as a periodic task in supervisor:

```ini
# /etc/supervisor/conf.d/share_cleaner.conf
[program:share_cleaner]
command=/bin/bash -c "while true; do sleep 86400; /usr/bin/python3 /app/backend/jobs/share_link_cleaner.py; done"
directory=/app/backend
autostart=true
autorestart=true
stdout_logfile=/var/log/share_cleaner.out.log
stderr_logfile=/var/log/share_cleaner.err.log
```

Reload supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start share_cleaner
```

---

## Monitoring

### Check Job Execution

**System Cron:**
```bash
# View logs
tail -f /var/log/share_cleaner.log

# Check cron execution history
grep CRON /var/log/syslog | grep share_cleaner
```

**Kubernetes:**
```bash
# List jobs
kubectl get jobs -n peptimancer

# View job logs
kubectl logs -n peptimancer -l job-name=share-link-cleaner-<timestamp>

# Check CronJob status
kubectl get cronjobs -n peptimancer
```

### Job Success Metrics

The job logs should show:
```
INFO - Starting share link cleanup...
INFO - Marked 5 shares as expired
INFO - Sent 3 reminder emails
INFO - Cleaned up 120 old analytics events
INFO - Cleanup complete
```

### Alerts

Set up monitoring alerts for:
- Job failures (exit code != 0)
- Job not running for >25 hours
- High number of expired shares (may indicate issue)

---

## Environment Variables

Required for all job execution methods:

```bash
MONGO_URL=mongodb://localhost:27017
DB_NAME=peptimancer_db

# Optional for email reminders
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@peptimancer.com
SMTP_PASSWORD=...
SUPPORT_EMAIL=support@peptimancer.com
```

---

## Manual Execution

To run the job manually for testing:

```bash
cd /app/backend
python3 jobs/share_link_cleaner.py
```

**Expected Output:**
```
2025-01-19 02:00:00 - share_cleaner - INFO - Starting share link cleanup...
2025-01-19 02:00:01 - share_cleaner - INFO - Marked 5 shares as expired
2025-01-19 02:00:02 - share_cleaner - INFO - Sent 3 reminder emails
2025-01-19 02:00:03 - share_cleaner - INFO - Cleaned up 120 old analytics events
2025-01-19 02:00:03 - share_cleaner - INFO - Cleanup complete
```

---

## Troubleshooting

### Job Not Running

**Check cron service:**
```bash
sudo systemctl status cron
```

**Check cron logs:**
```bash
grep CRON /var/log/syslog
```

**Verify Python path:**
```bash
which python3
# Should output: /usr/bin/python3
```

### Job Fails

**Check MongoDB connection:**
```bash
python3 -c "from motor.motor_asyncio import AsyncIOMotorClient; import asyncio; asyncio.run(AsyncIOMotorClient('mongodb://localhost:27017').admin.command('ping'))"
```

**Check permissions:**
```bash
ls -la /app/backend/jobs/share_link_cleaner.py
# Should be readable by cron user
```

**Run with debug logging:**
```bash
LOG_LEVEL=DEBUG python3 jobs/share_link_cleaner.py
```

### Database Issues

**Check expired shares:**
```javascript
// In MongoDB shell
use peptimancer_db
db.partner_shares.find({
  status: "active",
  expires_at: { $lt: new Date() }
}).count()
```

**Manual cleanup:**
```javascript
db.partner_shares.updateMany(
  {
    status: "active",
    expires_at: { $lt: new Date() }
  },
  {
    $set: { status: "expired" }
  }
)
```

---

## Best Practices

1. **Logging:** Always redirect output to log files
2. **Monitoring:** Set up alerts for job failures
3. **Testing:** Run manually after any code changes
4. **Backup:** Take DB backup before first production run
5. **Timezone:** Use UTC for all cron schedules
6. **Resource Limits:** Set appropriate memory/CPU limits in K8s
7. **Error Handling:** Job should handle errors gracefully
8. **Idempotency:** Job should be safe to run multiple times

---

## Future Jobs

Additional jobs that may be scheduled:

- **Export Cleaner:** Delete old reclaim pack exports
- **Analytics Aggregator:** Pre-compute daily analytics
- **User Notifications:** Send usage reports
- **Database Maintenance:** Compact collections, rebuild indexes
- **Backup Job:** Automated MongoDB backups

---

## References

- [Cron Syntax Guide](https://crontab.guru/)
- [Kubernetes CronJobs](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
- [MongoDB Scheduled Operations](https://docs.mongodb.com/manual/tutorial/manage-mongodb-processes/)
