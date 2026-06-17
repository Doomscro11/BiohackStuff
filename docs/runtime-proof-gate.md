# Runtime Proof Gate

This repository is not complete until its application behavior is runtime-proven.

## Required evidence

The repo completion record must include the applicable proof commands for:

1. dependency installation
2. test execution
3. primary entrypoint startup
4. service health checks when a service exists
5. background process startup when a long-running process exists
6. container image build when Dockerfiles exist
7. release or image mapping when release workflows exist

## Completion rule

Completion requires either a passing runtime proof or a recorded reason why a proof item is not applicable.

## Preservation rule

Runtime proof is additive validation only. It must not remove behavior, weaken existing checks, delete components, bypass branch protection, or replace application logic with stubs.

## Failure handling

A runtime proof failure becomes the next blocker. Patch the smallest observed cause and rerun the proof.
