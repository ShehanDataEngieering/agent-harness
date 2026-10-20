# 06 Checks gate the Submission

**Status:** done · **Seam:** Session · **Depends on:** 01 · **Stories:** 10, 11

## What

The Pack's Checks run after each agent step. A failing Check sends the failures back to the agent instead of submitting. The step limit stops endless repair.

## Acceptance tests

- [x] work that fails a Check is never submitted
- [x] the Check failures are given to the agent on its next step
- [x] a Session that reaches the step limit ends as given up

## Notes

Step accounting and the fixed limit of 30 agent steps per Session are defined in the [spec's implementation decisions](../spec.md#implementation-decisions).

## Mutation notes

Historical, before integrating main. Current results are under Integration validation.

mutmut 3.8: 35 mutants, 34 killed; `out_of_steps` (`>=` → `>`) is killed. The survivor is the `SessionWorkflow.__init__` `self._phase = None` mutant, equivalent as explained in ticket 02.

`SessionWorkflow.run` is decorated, so mutmut skips it and its new lines were mutated by hand (10 mutants, 9 killed). The survivor needs no test:

- The Check request's key `idempotency_key(session_id, self._step)` → `self._step + 1`: unobservable. Checks are deterministic and change nothing, so `Pack.check` does not take the key. The key is carried only to follow the activity-input rule, and later for the Trace.

## Integration validation

Current results, measured before the step limit was fixed at 30. Integrated main at `e4a62ffd`, preserving Cancel, typed steering Signals, Review refusals, and all existing acceptance tests. Resolved conflicts in the ADR, models, workflow, test support, Payload examples, and Session tests.

- Reproduced three Cancel-during-Checks regressions before the fix: passing work created a Submission, failing work started another agent step, and failure at the step limit returned `gave_up`. Checking Cancel after the Check activity now ends the Session as cancelled before repair or Submission; all three regression cases pass.
- Added Session-seam coverage for ordered, once-only steering during repeated Check repairs; Review refusal while Checks run; and Approval after passing Checks on the final allowed step.
- `make check`: lint, formatting, strict typing and 48 tests passed.
- `uv run mutmut run --max-children 2`: 72 mutants, 68 killed, 4 inherited equivalents. These are the Review wrapper's `and` to `or` (the only ApplicationError from our Update is ReviewRefused), initial `_phase = None` (overwritten by `run`), initial `_review = ""` (reset before awaiting Review), and initial `_cancelled = None` (read only for truthiness).
- Six manual workflow mutations were all killed: ignoring Cancel after Checks, submitting failed Checks, dropping failure feedback, allowing an extra agent step, dropping steering, and repeating steering. These targeted checks supplement mutmut's decorated-method gap; they do not close ticket 17's full mutation-gate requirement.
- Matt Pocock's independent Standards and Spec reviews in separate Herdr agents: zero findings on each axis.
