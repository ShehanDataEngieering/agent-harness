# 06 Checks gate the Submission

**Status:** done · **Seam:** Session · **Depends on:** 01 · **Stories:** 10, 11

## What

The Pack's Checks run after each agent step. A failing Check sends the failures back to the agent instead of submitting. The step limit stops endless repair.

## Acceptance tests

- [x] work that fails a Check is never submitted
- [x] the Check failures are given to the agent on its next step
- [x] a Session that reaches the step limit ends as given up

## Notes

Step accounting and the configurable agent step limit are defined in the [spec's implementation decisions](../spec.md#implementation-decisions).

## Mutation notes

mutmut 3.8: 35 mutants, 34 killed; `out_of_steps` (`>=` → `>`) is killed. The survivor is the `SessionWorkflow.__init__` `self._phase = None` mutant, equivalent as explained in ticket 02.

`SessionWorkflow.run` is decorated, so mutmut skips it and its new lines were mutated by hand (10 mutants, 9 killed). The survivor needs no test:

- The Check request's key `idempotency_key(session_id, self._step)` → `self._step + 1`: unobservable. Checks are deterministic and change nothing, so `Pack.check` does not take the key. The key is carried only to follow the activity-input rule, and later for the Trace.

## Integration validation

Merged current main (`b9a9d68`), retaining its explicit refusal of invalid Reviews and the Checks gate. The obsolete test expecting a stale Review to be silently ignored is superseded by main's refusal tests.

- `make check`: lint, format, strict typing and 35 tests passed.
- `uv run mutmut run --max-children 2`: 57 mutants, 54 killed, 3 surviving equivalents already explained in ticket 03 (`review` error wrapper `and` → `or`, initial `_phase = None`, initial `_review = ""`). The Checks step-limit mutant remains killed. Decorated-method limitations and the earlier manual mutation evidence above still apply.
- Standards and Spec reviews of the integrated diff: no findings.
