# Operator Change Boundary

This project should continue through small reviewed changes.

## Separate-review items

The following items should be handled in their own PRs:

- deployment procedure changes
- rollback procedure changes
- backup or restore procedure changes
- provider configuration changes
- production admin changes
- repository rule changes

## Routine items

The following items may be handled as ordinary bounded PRs:

- documentation updates
- local development notes
- tests
- non-secret examples
- CI validation that does not change production authority
- small fixes inside reviewed paths

## PR checklist

Each PR should state:

1. what changed
2. which files changed
3. how the change was validated
4. whether review remains required
5. whether any production authority changed

## Current focus

The next safe work should clarify validation, provider boundaries, demo behavior, and local operator instructions before broader feature work.
