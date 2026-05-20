# Manual Release Gate Verification

Use this when the GitHub connector does not expose the latest branch-push workflow run.

## GitHub Actions UI path

1. Open the repository in GitHub.
2. Go to **Actions**.
3. Select **Release Gate**.
4. Confirm the latest run is for branch `refactor/monorepo-structure`.
5. Open failed jobs and inspect the first failed step.

## Expected workflow shape

The canonical Release Gate has four jobs:

- `Backend tests`
- `Frontend build`
- `Frontend tests`
- `Release gate summary`

## Expected commands

Backend:

```bash
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
pip check
PYTHONPATH=backend python -c "import server; print('backend import ok')"
pytest -q
```

Frontend build:

```bash
cd frontend
yarn install --frozen-lockfile
yarn build
```

Frontend unit tests:

```bash
cd frontend
yarn install --frozen-lockfile
yarn test:unit
```

## Environment assumptions

Backend CI supplies:

```text
MONGO_URL=mongodb://localhost:27017
DB_NAME=peptimancer_test_db
JWT_SECRET=release-gate-test-secret-change-in-prod
ADMIN_EMAILS=admin@peptimancer.com
ENABLE_DEMO_OTP=true
DEMO_MODE=true
ENV=development
PARTNER_SIGNING_SECRET=release-gate-partner-secret
STRIPE_SECRET_KEY=sk_test_placeholder
STRIPE_WEBHOOK_SECRET=whsec_placeholder
REACT_APP_BACKEND_URL=http://localhost:8001
PYTHONPATH=${{ github.workspace }}/backend
```

Frontend CI uses Node 20 because the dependency graph requires Node >=20.

## Patch rule

Patch the first real failing layer only. Do not bypass or weaken release-critical checks to make the gate green.
