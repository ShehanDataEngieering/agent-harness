# 03 Invalid Reviews are refused

**Status:** done · **Seam:** Session · **Depends on:** 02 · **Stories:** 8

## What

The review Update validates before it is accepted, and the caller gets the refusal.

## Acceptance tests

- [x] a Review naming an old Submission is refused
- [x] a Review while the agent is still working is refused, and the work is not committed when the agent finishes (found in ticket 01 review; since ticket 02 an early Review is dropped when the next Submission starts, but the caller is still told it succeeded)
- [x] a Rejection without a reason is refused
- [x] a refused Review leaves the Session unchanged

## Mutation survivors

48 mutants on core/, 45 killed, 3 survive, all equivalent:

- `client.review`: `and` -> `or` in the refusal check. The review Update raises no other `ApplicationError`, so both forms behave the same today.
- `SessionWorkflow.__init__`: `_phase = None`. `run()` sets the phase to working before anything can observe it.
- `SessionWorkflow.__init__`: `_review = ""`. Each Submission resets it to None before the Session waits, and Reviews are refused until then.

## Follow-ups from ticket 04

Not implemented here; found while building Cancel.

- A Review sent after a Cancel is accepted and ignored; it should be refused.
- `cancel()` on a finished Session raises Temporal's raw error instead of a wrapped one.
- Decided: a Cancel after an Approval is too late, and the commit goes ahead.
