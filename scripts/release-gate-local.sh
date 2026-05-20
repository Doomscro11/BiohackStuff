#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export MONGO_URL="${MONGO_URL:-mongodb://localhost:27017}"
export DB_NAME="${DB_NAME:-peptimancer_test_db}"
export JWT_SECRET="${JWT_SECRET:-release-gate-test-secret-change-in-prod}"
export ADMIN_EMAILS="${ADMIN_EMAILS:-admin@peptimancer.com}"
export ENABLE_DEMO_OTP="${ENABLE_DEMO_OTP:-true}"
export DEMO_MODE="${DEMO_MODE:-true}"
export ENV="${ENV:-development}"
export PARTNER_SIGNING_SECRET="${PARTNER_SIGNING_SECRET:-release-gate-partner-secret}"
export STRIPE_SECRET_KEY="${STRIPE_SECRET_KEY:-sk_test_placeholder}"
export STRIPE_WEBHOOK_SECRET="${STRIPE_WEBHOOK_SECRET:-whsec_placeholder}"
export REACT_APP_BACKEND_URL="${REACT_APP_BACKEND_URL:-http://localhost:8001}"
export PYTHONPATH="$ROOT_DIR/backend${PYTHONPATH:+:$PYTHONPATH}"

run_backend_gate() {
  echo "== Backend gate =="
  cd "$ROOT_DIR"
  python -m pip install --upgrade pip
  pip install -r backend/requirements.txt
  pip install pytest pytest-asyncio
  pip check
  python - <<'PY'
import importlib.metadata
import sys

try:
    importlib.metadata.version('emergentintegrations')
except importlib.metadata.PackageNotFoundError:
    print('external emergentintegrations package not installed')
    sys.exit(0)

print('external emergentintegrations package must not be installed')
sys.exit(1)
PY
  python -c "import server; print('backend import ok')"
  pytest -q
}

run_frontend_gate() {
  echo "== Frontend gate =="
  cd "$ROOT_DIR/frontend"
  yarn install --frozen-lockfile
  yarn build
  yarn test:unit
}

case "${1:-all}" in
  backend)
    run_backend_gate
    ;;
  frontend)
    run_frontend_gate
    ;;
  all)
    run_backend_gate
    run_frontend_gate
    ;;
  *)
    echo "Usage: $0 [backend|frontend|all]" >&2
    exit 2
    ;;
esac
