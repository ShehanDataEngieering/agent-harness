# 02 Rejection returns the reason to the agent

**Status:** done · **Seam:** Session · **Depends on:** 01 · **Stories:** 4, 5

## What

A Rejection with a reason sends the work back; the agent sees the reason on its next step and submits again as Submission 2. The third Rejection makes the Session give up.

## Acceptance tests

- [x] a rejected Submission returns to the agent with the reason
- [x] the resubmitted work is Submission 2
- [x] the third Rejection ends the Session as given up, with nothing committed

## Mutation notes

mutmut 3.8 does not mutate decorated methods, so `SessionWorkflow.run` was mutated by hand (11 mutants, 9 killed). Surviving mutants and why they need no test:

- `self._rejections == MAX_REJECTIONS` → `>=`: equivalent; the count only rises by 1 from 0 and the Session returns when it reaches the limit.
- `self._reviews.pop()` → `pop(0)`: only differs when two Reviews arrive in one activation while waiting; which wins is unspecified, and ticket 03 refuses the second one.
- mutmut's `SessionWorkflow.__init__` `self._phase = None`: equivalent; `run()` sets the phase before any Query can see it.
