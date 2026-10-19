# 01 Approved Submission commits the work

**Status:** in review · **Seam:** Session, Payload · **Depends on:** — · **Stories:** 1, 2, 3

## What

The tracer bullet. A Session starts, the FakeAgent produces work, the Session waits for Review (Checks arrive in ticket 06), the owner approves, and the work is committed. Sets up the workflow, the review Update, the status Query, a test Pack, the worker factory and the Temporal test environment.

## Acceptance tests

- [x] an approved Submission completes the Session as approved, with the work committed
- [x] status shows the Session working on step 1 with nothing submitted yet
- [x] status shows the Session waiting for Review on Submission 1 after step 1
- [x] an agent step carries the Session ID and step as its idempotency key
- [x] the commit reaches the Pack with the Session ID and step as its idempotency key
- [x] a Session for an unknown Pack fails before any work
- [x] every workflow and activity model round-trips through the data converter unchanged (Payload seam)

## Evidence

- `make check`: ruff, pyright strict (0 errors), 16 tests passed.
- Mutation testing on `src/harness/core/` is partial. mutmut 3.8 does not generate mutants for decorated methods, so `SessionWorkflow.run`/`review`/`status` and the activity methods were not mutation-tested. The 25/25 killed result covered only undecorated core code (constructors, `SessionHandle`, `start_session`, `idempotency_key`) and was measured before the unknown-Pack fix. Closing this gap is tracked in [ticket 17](17-ci-and-mutation.md).
