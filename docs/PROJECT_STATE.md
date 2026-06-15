# BiohackStuff Project State

This document records the current conservative project state for the first Unbuildr-managed BiohackStuff target PR.

## Repository

- Target repo: `Doomscro11/BiohackStuff`
- Base branch: `main`
- Target branch: `biohackstuff-baseline-docs-ci-review-plan`
- Change type: documentation-only baseline readiness pass
- Auto-merge: not authorized
- Direct production or deployment action: not authorized

## Current Stack Snapshot

BiohackStuff currently presents as the Peptimancer application:

- Backend: FastAPI / Python
- Frontend: React / CRACO
- Persistence: MongoDB / Motor
- CI: GitHub Actions release gate
- Validation surface: backend tests, frontend build, frontend unit tests, release gate summary

## Current Known Readiness Signals

The README records an evidence-gated audit baseline with a completion score of `82/100` and high confidence. It also records three known next blockers:

1. Harden demo OTP behavior so it fails closed in production.
2. Clearly mark deployment, backup, restore, and rollback actions as manual-only.
3. Re-run the Unbuildr target audit after provider-boundary finalization lands.

## First Target PR Scope

This first target PR is intentionally limited to baseline documentation. It does not modify application code, workflow definitions, dependencies, secrets, lockfiles, generated local-only paths, or deployment behavior.

Allowed in this pass:

- Record current project state.
- Record CI review expectations.
- Preserve the current release-gate workflow without editing it.
- Establish the next safe review path before any code or workflow repair.

Not allowed in this pass:

- Workflow mutation.
- Dependency or lockfile changes.
- Secrets or environment changes.
- Production deployment, backup, restore, or rollback automation.
- Auto-merge.

## Next Safe Step

After this PR is opened, the next safe step is to inspect the release-gate result and document whether the current failures, if any, are backend, frontend build, frontend tests, dependency consistency, or workflow configuration issues. Any code or workflow fix should be proposed in a later narrow PR after that evidence is captured.
