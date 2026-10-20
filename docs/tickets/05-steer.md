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

- Integrated main at `771bf764`, including its Cancel handling, Review refusals, and acceptance tests. Resolved conflicts in the client, workflow, Session tests, spec, and ADR without dropping either behavior.
- Added `SteerRequest(Payload)` to satisfy the strict Pydantic boundary rule. `session.steer("guidance")` wraps the string before sending the Signal; the Payload seam covers its serialization round-trip.
- `make check`: lint and formatting passed, pyright strict reported zero errors, 36 tests passed.
- Fresh mutation run: 71 mutants, 67 killed, 4 survived. All generated steering mutants were killed. The four survivors are inherited equivalents: the Review error guard's `and` to `or` (only ReviewRefused ApplicationErrors are raised), initial `_phase = None` (overwritten by `run`), initial `_review = ""` (reset before awaiting Review), and initial `_cancelled = None` (read only for truthiness).
- Repeated the three manual steering mutations listed above against the typed Signal handler and merged workflow; all three were killed. mutmut still skips decorated handlers, so this is targeted coverage rather than a complete mutation gate (ticket 17).
- Matt Pocock's Standards review found the missing boundary model, which was fixed; the Standards and Spec rereviews reported no further findings.
