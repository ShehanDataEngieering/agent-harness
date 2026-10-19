# 01 Approved Submission commits the work

**Status:** in review · **Seam:** Session, Payload · **Depends on:** — · **Stories:** 1, 2, 3

## What

The tracer bullet. A Session starts, the FakeAgent produces work, Checks pass, the Session waits for Review, the owner approves, and the work is committed. Sets up the workflow, the review Update, the status Query, a test Pack, the worker factory and the Temporal test environment.

## Acceptance tests

- [x] an approved Submission completes the Session as approved, with the work committed
- [x] status shows the Session working on step 1 with nothing submitted yet
- [x] status shows the Session waiting for Review on Submission 1 after step 1
- [x] an agent step carries the Session ID and step as its idempotency key
- [x] the commit reaches the Pack with the Session ID and step as its idempotency key
- [x] every workflow and activity model round-trips through the data converter unchanged (Payload seam)

## Evidence

- `make check`: ruff, pyright strict (0 errors), 15 tests passed.
- Mutation testing on `src/harness/core/`: 25/25 mutants killed.
