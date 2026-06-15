# CI Review Plan

This document defines the first conservative CI review boundary for BiohackStuff.

## Purpose

The goal is to understand the current release-gate posture before modifying application code, workflow configuration, dependencies, or lockfiles.

This PR does not change CI behavior. It documents what should be reviewed next.

## Current Release Gate Surface

The current release gate workflow is located at:

```text
.github/workflows/release-gate.yml
```

The workflow currently includes:

1. Backend tests
2. Frontend build
3. Frontend tests
4. Release gate summary

## Backend Review Checklist

Review the backend gate for:

- Python setup version.
- `backend/requirements.txt` install behavior.
- `pip check` dependency consistency.
- Import viability for `server`.
- Backend test execution through `pytest -q`.
- MongoDB service availability and test database configuration.
- Demo OTP and demo mode boundaries.

No backend code change is authorized by this document.

## Frontend Build Review Checklist

Review the frontend build gate for:

- Node version.
- Yarn availability and lockfile behavior.
- Install behavior under `yarn install --non-interactive --ignore-scripts`.
- Build behavior under `yarn build`.
- Whether diagnostics are being captured when the build fails.

No frontend code change is authorized by this document.

## Frontend Test Review Checklist

Review the frontend test gate for:

- Presence of `frontend/jest.config.js`.
- Install behavior under the test job.
- Unit test execution through `yarn test:unit --runInBand`.
- Whether diagnostics are uploaded on failure.

No frontend code change is authorized by this document.

## Workflow Review Boundary

The workflow may be inspected, but it should not be modified in this first documentation-only PR.

Workflow edits require a later explicit approval packet that identifies:

- The failing job or step.
- The proposed workflow line-level change.
- Why the change is not hiding a product defect.
- Why the change does not introduce deployment, secret, or auto-merge authority.

## Next Evidence Needed

Before any repair PR, collect or confirm:

- Which release-gate job fails, if any.
- The first failing step in that job.
- The relevant diagnostics artifact or log section.
- Whether the issue is documentation, test expectation, dependency consistency, application code, or workflow configuration.

## Guardrails

- Do not introduce dependencies.
- Do not modify lockfiles.
- Do not modify secrets or environment files.
- Do not add deployment automation.
- Do not auto-merge.
- Do not treat this document as authorization for code or workflow mutation.
