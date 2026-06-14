# Unbuildr PR Gate Note

This note records the working rule for future Unbuildr-assisted BiohackStuff changes.

## Rule

Future changes should be proposed through pull requests and should wait for repository checks before merge.

## Current first focus

The current first focus is documentation and operations clarity only. Application logic, provider configuration, payment settings, production release behavior, and database procedures remain out of scope for this lane.

## Expected PR shape

Each PR should be small and easy to review:

- one narrow purpose
- limited files
- clear summary
- no committed secrets
- no production-only configuration
- no broad refactor

## Validation

Use the smallest relevant checks for the touched area. For docs-only changes, repository checks should still be allowed to run before merge.
