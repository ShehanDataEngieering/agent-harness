# 05 Steering reaches the agent

**Status:** done · **Seam:** Session · **Depends on:** 01 · **Stories:** 6

## What

Implement steering as defined in the [Session lifecycle and implementation decisions](../spec.md#session-lifecycle).

## Acceptance tests

- [x] guidance sent while the agent works is given to the agent on its next step
- [x] guidance is given once, not repeated on later steps

## Notes

- Revisit the [current steering delivery limitation](../spec.md#implementation-decisions) when the agent loop takes several steps per Submission (ticket 10).

## Mutation notes

mutmut 3.8: 41 mutants, 40 killed (both `_take_guidance` mutants and all four `SessionHandle.steer` mutants among them). It skips decorated methods, so the `steer` Signal and the new line in `SessionWorkflow.run` were mutated by hand (3 mutants, 3 killed):

- `guidance=self._take_guidance()` → `guidance=()`: killed.
- `steer` body `self._guidance.append(guidance)` → `pass`: killed.
- `guidance=self._take_guidance()` → `guidance=tuple(self._guidance)` (never cleared): killed by the "given once" test.

Surviving mutant and why it needs no test:

- mutmut's `SessionWorkflow.__init__` `self._phase = None`: equivalent, already noted in ticket 02; `run()` sets the phase before any Query can see it.

## Integration with main

- Resolved the Session test conflict by keeping main's Review refusal contract and the steering tests. The superseded test that expected a stale Review to be silently ignored was removed.
- `make check`: lint and formatting passed, pyright strict reported zero errors, 31 tests passed.
- Fresh mutation run: 63 mutants, 60 killed, 3 survived. Both `_take_guidance` mutants and all `SessionHandle.steer` mutants were killed. The three survivors are the existing ticket 03 equivalents: the Review error guard's `and` to `or` (only ReviewRefused ApplicationErrors are raised), initial `_phase = None` (overwritten by `run`), and initial `_review = ""` (reset before awaiting Review).
- Repeated the three manual steering mutations listed above against the merged code; all three were killed.
