# CODEX.md — Repo Operator Instructions

## Mission

Move this repository toward a production-ready Peptimancer MVP through small, reviewable, test-driven changes.

## Operating Rules

- Work in branches and pull requests.
- Do not commit secrets, tokens, private keys, `.env` files, or credentials.
- Do not weaken, skip, or delete failing tests just to make CI green.
- Do not bypass security, authentication, billing, or RBAC checks.
- Prefer small fixes with clear verification over broad rewrites.
- Treat executable tests and source code as higher authority than readiness claims in markdown.
- If product scope is contradictory, preserve current behavior and document the decision point.

## Release Gate

A change is not ready until the release gate passes or the failure has been diagnosed and documented.

Backend verification:

```bash
cd backend
pip install -r requirements.txt
pytest -q
```

Frontend verification:

```bash
cd frontend
yarn install --frozen-lockfile
yarn build
yarn test --watchAll=false
```

## Completion Standard

A task is complete only when:

1. Code is implemented.
2. Tests are added or updated when appropriate.
3. Existing tests pass or failures are documented with root cause.
4. Relevant docs are updated.
5. PR summary explains what changed, why, risks, and verification.
