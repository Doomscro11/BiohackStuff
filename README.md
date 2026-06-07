# BiohackStuff / Peptimancer

BiohackStuff is the repository for **Peptimancer**, a full-stack peptide-design application with a FastAPI backend, React/CRACO frontend, MongoDB/Motor persistence, authentication/admin surfaces, export workflows, and test/release-gate automation.

This README replaces the initial placeholder instructions with a developer and operator guide. It is intentionally conservative: it documents how to run and validate the project without adding deployment automation, secrets, auto-merge, or production access.

## Current Project State

The current Unbuildr evidence-gated audit baseline is stored at:

```text
docs/generated/unbuildr/target_project_state.md
docs/generated/unbuildr/target_project_state.json
```

Audit baseline:

| Metric | Value |
|---|---:|
| Files scanned | 226 |
| Files collected | 91 |
| Files skipped | 30 |
| Completion score | 82/100 |
| Confidence | High |

Known next blockers:

1. Replace the Emergent LLM integration with a reviewed provider adapter.
2. Harden demo OTP behavior so it fails closed in production.
3. Clearly mark deployment, backup, restore, and rollback actions as manual-only.

## Repository Layout

```text
backend/        FastAPI application, routes, middleware, services, tests
frontend/       React/CRACO application, unit/e2e tests, hydration checks
.github/        CI and release gate workflows
docs/           Generated audit artifacts and future operator documentation
```

## Backend

The backend is a FastAPI application using MongoDB through Motor.

Primary entrypoint:

```text
backend/server.py
```

Common backend dependencies include:

```text
fastapi
uvicorn
motor
pymongo
pydantic
pytest
stripe
python-jose
passlib
fpdf2
emergentintegrations
```

### Backend Environment

The backend expects environment variables to be provided locally through `backend/.env` or by the runtime environment.

At minimum, development requires MongoDB configuration such as:

```bash
MONGO_URL="mongodb://localhost:27017"
DB_NAME="biohackstuff"
```

LLM and payment integrations should be treated as external provider configuration and should not be committed to the repository.

## Frontend

The frontend is a React application built with CRACO.

Primary package file:

```text
frontend/package.json
```

Key scripts:

```bash
yarn start
yarn build
yarn test:unit
yarn test:e2e
yarn audit:hydration
yarn test:all
```

The project currently uses Node 20 in the release gate workflow.

## Local Development

### Backend

From the repository root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

In a separate terminal:

```bash
cd frontend
yarn install --frozen-lockfile
yarn start
```

## Testing

### Backend tests

```bash
cd backend
pytest
```

### Frontend tests

```bash
cd frontend
yarn test:unit
yarn test:e2e
yarn audit:hydration
```

### Full frontend validation

```bash
cd frontend
yarn test:all
```

## CI / Release Gate

The repository includes GitHub Actions release-gate automation under:

```text
.github/workflows/release-gate.yml
```

The release gate is intended to validate the repo before merge or release decisions. It should not be treated as production deployment authority.

## Safety and Operations Boundary

This repository should remain fail-closed around sensitive operations.

The following actions must remain manual unless reviewed in a dedicated PR:

- production deployment
- rollback
- database backup
- database restore
- payment-provider changes
- LLM-provider credential changes
- production admin-user changes
- auto-merge enablement

Do not commit secrets, tokens, private keys, payment-provider keys, LLM-provider keys, or production `.env` files.

## LLM Provider Boundary

The current backend imports an Emergent LLM integration from `backend/server.py`. The next guarded modernization step is to replace direct Emergent usage with a provider adapter boundary so the app can support explicit provider selection, testing, and production guardrails.

Until that replacement is complete:

- treat LLM calls as external side effects
- do not expose provider keys in logs
- do not auto-run production LLM calls from tests
- keep mock/sandbox modes explicit

## Unbuildr Completion Workflow

Unbuildr is being used to complete BiohackStuff one guarded PR at a time.

The current safe sequence is:

1. Preserve project state artifacts.
2. Replace placeholder project documentation.
3. Add/normalize provider adapter boundaries.
4. Harden production/demo safety checks.
5. Clarify manual operations procedures.
6. Re-run audit and update completion score.

Each PR should be bounded, reviewable, reversible, and avoid broad mutation.

## Current Status

BiohackStuff is not treated as complete yet. The repo has a functioning stack and meaningful test infrastructure, but the next completion work should focus on reducing operational ambiguity and replacing fragile integration boundaries before broad feature work.
