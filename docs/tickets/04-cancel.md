# 04 Cancel ends a Session

**Status:** in review · **Seam:** Session · **Depends on:** 01 · **Stories:** 7

## What

A Cancel Signal ends the Session whether it is working or waiting for Review.

## Acceptance tests

- [x] a Cancel while waiting for Review ends the Session as cancelled, with nothing committed
- [x] a Cancel while the agent is working ends the Session as cancelled after the current step

## Known gaps

- A Cancel during COMMITTING is accepted but ignored: the commit already underway finishes and the Session ends approved. Not covered by this ticket's acceptance lines.
- A Review that arrives after a Cancel, before the Session closes, is accepted and ignored. Refusing it belongs to [ticket 03](03-invalid-review-refused.md).
- `SessionHandle.cancel()` on a finished Session raises Temporal's "workflow already completed" error unwrapped.

## Evidence

- `make check`: ruff, pyright strict (0 errors), 19 tests passed.
- Mutation testing on `src/harness/core/`: 37 of 38 mutants killed, including every mutant in `SessionHandle.cancel` and `SessionWorkflow._cancelled_outcome`. The survivor sets `_cancelled = None` instead of `False`. It is equivalent, because the flag is only read for truthiness. mutmut 3.8 skips decorated methods, so the `cancel` Signal handler and the Cancel checks in `run()` were not mutation-tested ([ticket 17](17-ci-and-mutation.md)).
