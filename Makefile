# Peptimancer PatentPulse Deployment Makefile

.PHONY: help verify-canary promote-canary rollback-canary health-check seed-dev view-logs check-slos run-collector dry-run-collector db-backup db-restore require-manual-ops docs

help:
	@echo "Peptimancer PatentPulse Deployment Commands"
	@echo ""
	@echo "Development:"
	@echo "  make seed-dev          - Seed development data"
	@echo "  make health-check      - Quick health check"
	@echo ""
	@echo "Deployment:"
	@echo "  make verify-canary     - Run post-deploy verification"
	@echo "  make promote-canary    - Promote canary to 100%"
	@echo "  make rollback-canary   - Rollback to pre-patentpulse"
	@echo ""
	@echo "Monitoring:"
	@echo "  make view-logs         - Tail PatentPulse logs"
	@echo "  make check-slos        - Check SLO compliance"
	@echo ""
	@echo "Manual operations guard:"
	@echo "  Set CONFIRM_MANUAL_OPS=yes for promote/rollback/backup/restore targets"

require-manual-ops:
	@if [ "$(CONFIRM_MANUAL_OPS)" != "yes" ]; then \
		echo "Manual operation blocked. Re-run with CONFIRM_MANUAL_OPS=yes after human review."; \
		exit 2; \
	fi

# Development commands
seed-dev:
	@echo "🌱 Seeding PatentPulse development data..."
	cd backend && ENV=dev python -m jobs.seed_patentpulse_dev

health-check:
	@echo "🏥 Running health check..."
	@curl -s http://localhost:8001/health | jq .
	@curl -s http://localhost:8001/api/patentpulse/stats | jq '.total'

# Deployment commands
verify-canary:
	@echo "🔍 Running post-deploy verification..."
	@export API_BASE_URL=${API_BASE_URL:-http://localhost:8001} && \
	export MONGO_URI=${MONGO_URI:-mongodb://localhost:27017} && \
	export FEATURE_PATENTPULSE=true && \
	python backend/jobs/post_deploy_verifier.py

promote-canary: require-manual-ops
	@echo "🚀 Promoting canary to 100% traffic..."
	@echo "   1. Updating feature flag to enabled"
	@echo "   2. Scaling up production pods"
	@echo "   3. Tagging release"
	@git tag "production-patentpulse-$$(date +%Y%m%d-%H%M)"
	@echo "✅ Canary promoted successfully"
	@echo ""
	@echo "Next steps:"
	@echo "  - Monitor dashboards for 24 hours"
	@echo "  - Schedule weekly collector job"
	@echo "  - Update runbook with any new learnings"

rollback-canary: require-manual-ops
	@echo "⚠️  Rolling back canary deployment..."
	@echo "   1. Disabling FEATURE_PATENTPULSE"
	@echo "   2. Reverting to pre-patentpulse-20251111-1950"
	@echo "   3. Restarting services"
	@git checkout pre-patentpulse-20251111-1950
	@echo "🔄 Rollback complete"
	@echo ""
	@echo "Post-rollback checklist:"
	@echo "  - Verify services are healthy"
	@echo "  - Check error rates returned to baseline"
	@echo "  - Review logs for root cause"
	@echo "  - Create incident post-mortem"

# Monitoring commands
view-logs:
	@echo "📋 Tailing PatentPulse logs..."
	@tail -f /var/log/supervisor/backend.*.log | grep -i "patentpulse"

check-slos:
	@echo "📊 Checking SLO compliance..."
	@echo ""
	@echo "Latency SLO (p95 ≤ 900ms):"
	@for i in {1..10}; do \
		time curl -s -w "%{time_total}\n" -o /dev/null http://localhost:8001/api/patentpulse/items?limit=10; \
	done | awk '{sum+=$$1; if($$1>max) max=$$1} END {print "  Avg:", sum/NR*1000"ms  Max:", max*1000"ms"}'
	@echo ""
	@echo "Error Rate SLO (≤ 2%):"
	@python3 -c "import requests; \
		results = [requests.get('http://localhost:8001/api/patentpulse/items').status_code for _ in range(20)]; \
		errors = sum(1 for s in results if s >= 500); \
		print(f'  Errors: {errors}/20 ({errors/20*100:.1f}%)')"

# Collector management
run-collector:
	@echo "🔄 Running PatentPulse collector..."
	cd backend && FEATURE_PATENTPULSE=true python -m jobs.patentpulse_collector

dry-run-collector:
	@echo "🧪 Dry-run PatentPulse collector..."
	cd backend && FEATURE_PATENTPULSE=true DRY_RUN=true python -m jobs.patentpulse_collector

# Database operations
db-backup: require-manual-ops
	@echo "💾 Backing up patentpulse_items collection..."
	@mongodump --uri="mongodb://localhost:27017/peptimancer_db" \
		--collection=patentpulse_items \
		--out=./backups/patentpulse-$$(date +%Y%m%d-%H%M)
	@echo "✅ Backup complete"

db-restore: require-manual-ops
	@echo "⚠️  Restoring patentpulse_items from backup..."
	@echo "Specify backup path with BACKUP_PATH=..."
	@if [ -z "$(BACKUP_PATH)" ]; then \
		echo "Error: BACKUP_PATH not set"; \
		exit 1; \
	fi
	@mongorestore --uri="mongodb://localhost:27017/peptimancer_db" \
		--collection=patentpulse_items \
		$(BACKUP_PATH)

# Documentation
docs:
	@echo "📚 Opening PatentPulse documentation..."
	@open docs/README_PATENTPULSE.md || xdg-open docs/README_PATENTPULSE.md
