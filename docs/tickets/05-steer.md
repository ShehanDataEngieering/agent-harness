# 05 Steering reaches the agent

**Status:** done · **Seam:** Session · **Depends on:** 01 · **Stories:** 6

## What

A steer Signal adds guidance that the agent receives on its next step.

## Acceptance tests

- [x] guidance sent while the agent works is given to the agent on its next step
- [x] guidance is given once, not repeated on later steps

## Mutation notes

mutmut 3.8: 41 mutants, 40 killed (both `_take_guidance` mutants and all four `SessionHandle.steer` mutants among them). It skips decorated methods, so the `steer` Signal and the new line in `SessionWorkflow.run` were mutated by hand (3 mutants, 3 killed):

- `guidance=self._take_guidance()` → `guidance=()`: killed.
- `steer` body `self._guidance.append(guidance)` → `pass`: killed.
- `guidance=self._take_guidance()` → `guidance=tuple(self._guidance)` (never cleared): killed by the "given once" test.

Surviving mutant and why it needs no test:

- mutmut's `SessionWorkflow.__init__` `self._phase = None`: equivalent, already noted in ticket 02; `run()` sets the phase before any Query can see it.
