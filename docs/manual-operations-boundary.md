# Manual Operations Boundary

This document records the current manual-only operations boundary for BiohackStuff.

## Purpose

BiohackStuff should keep high-impact operational changes reviewable and explicit. This document is informational and does not add automation.

## Manual-only areas

The following areas should remain manual unless changed through a dedicated reviewed PR:

- production release decisions
- database backup procedures
- database restore procedures
- payment-provider configuration
- LLM-provider credential configuration
- production admin-user changes

## Local validation before PR review

Before proposing changes in these areas, validate the smallest relevant surface only:

```bash
cd backend
pytest
```

```bash
cd frontend
yarn test:unit
```

For frontend-wide validation:

```bash
cd frontend
yarn test:all
```

## Current stance

BiohackStuff can continue to improve through small, bounded, reviewed PRs. Broad operational changes should be split into separate reviewable steps.
