# Release Gate Stabilization

This branch is being stabilized through a canonical Release Gate workflow.

## Current intent

- Keep `main` as the target branch.
- Run the gate on pull requests into `main`.
- Also run the gate on pushes to `refactor/monorepo-structure` so stabilization commits produce fresh CI signals.

## Canonical gate

The canonical workflow is:

```text
.github/workflows/release-gate.yml
```

It verifies:

- Backend dependency installation
- Backend dependency consistency via `pip check`
- External Emergent package absence
- Backend app import
- Backend pytest suite
- Frontend dependency installation under Node 20
- Frontend production build
- Frontend test command

## Notes

Legacy workflows are quarantined to manual dispatch during stabilization so their older assumptions do not pollute the PR signal.

The frontend gate uses Node 20 because the current dependency graph includes packages that require Node >=20.
