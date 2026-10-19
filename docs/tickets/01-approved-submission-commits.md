# 01 Approved Submission commits the work

**Status:** todo · **Seam:** Session, Payload · **Depends on:** — · **Stories:** 1, 2, 3

## What

The tracer bullet. A Session starts, the FakeAgent produces work, Checks pass, the Session waits for Review, the owner approves, and the work is committed. Sets up the workflow, the review Update, the status Query, a test Pack, the worker factory and the Temporal test environment.

## Acceptance tests

- [ ] an approved Submission completes the Session as approved, with the work committed
- [ ] status shows the Session waiting for Review on Submission 1
- [ ] every workflow and activity model round-trips through the data converter unchanged (Payload seam)
