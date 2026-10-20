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

After integration with main, mutmut 3.8 generated 71 mutants: 67 killed and 4 survived. All generated steering mutants were killed. The survivors are inherited equivalents documented in [ticket 03](03-invalid-review-refused.md#mutation-survivors) (the Review error guard, initial `_phase`, and initial `_review`) and [ticket 04](04-cancel.md#evidence) (initial `_cancelled`).

mutmut skips decorated methods, so the typed `steer` Signal and the new line in `SessionWorkflow.run` were mutated by hand (3 mutants, 3 killed):

- `guidance=self._take_guidance()` → `guidance=()`: killed.
- `steer` body `self._guidance.append(request.guidance)` → `pass`: killed.
- `guidance=self._take_guidance()` → `guidance=tuple(self._guidance)` (never cleared): killed by the "given once" test.

This is targeted coverage rather than a complete mutation gate ([ticket 17](17-ci-and-mutation.md)).

## Integration with main

- Integrated main at `771bf764`, including its Cancel handling, Review refusals, and acceptance tests. Resolved conflicts in the client, workflow, Session tests, spec, and ADR without dropping either behavior.
- Added `SteerRequest(Payload)` to satisfy the strict Pydantic boundary rule. `session.steer("guidance")` wraps the string before sending the Signal; the Payload seam covers its serialization round-trip.
- `make check`: lint and formatting passed, pyright strict reported zero errors, 36 tests passed.
- Matt Pocock's Standards review found the missing boundary model, which was fixed; the Standards and Spec rereviews reported no further findings.
