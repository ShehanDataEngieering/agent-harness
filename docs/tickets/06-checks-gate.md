# 06 Checks gate the Submission

**Status:** done · **Seam:** Session · **Depends on:** 01 · **Stories:** 10, 11

## What

The Pack's Checks run after each agent step. A failing Check sends the failures back to the agent instead of submitting. The step limit stops endless repair.

## Acceptance tests

- [x] work that fails a Check is never submitted
- [x] the Check failures are given to the agent on its next step
- [x] a Session that reaches the step limit ends as given up

## Notes

- The Check activity shares the step number (and idempotency key) of the agent step whose work it checks, so a step is still "one agent step" and the commit stays at step N+1.
- The step limit is `SessionInput.max_steps` (default `MAX_STEPS = 30`, spec: Limits). Before the commit, the step count equals the agent steps taken, so the limit compares against it directly.

## Mutation notes

mutmut 3.8: 35 mutants, 34 killed; `out_of_steps` (`>=` → `>`) is killed. The survivor is the `SessionWorkflow.__init__` `self._phase = None` mutant, equivalent as explained in ticket 02.

`SessionWorkflow.run` is decorated, so mutmut skips it and its new lines were mutated by hand (10 mutants, 9 killed). The survivor needs no test:

- The Check request's key `idempotency_key(session_id, self._step)` → `self._step + 1`: unobservable. Checks are deterministic and change nothing, so `Pack.check` does not take the key. The key is carried only to follow the activity-input rule, and later for the Trace.
