# 03 Invalid Reviews are refused

**Status:** todo · **Seam:** Session · **Depends on:** 02 · **Stories:** 8

## What

The review Update validates before it is accepted, and the caller gets the refusal.

## Acceptance tests

- [ ] a Review naming an old Submission is refused (since ticket 02 a Review naming any Submission other than the current one is silently ignored, but the caller is still told it succeeded)
- [ ] a Review while the agent is still working is refused, and the work is not committed when the agent finishes (found in ticket 01 review; since ticket 02 an early Review is dropped when the next Submission starts, but the caller is still told it succeeded)
- [ ] a Rejection without a reason is refused
- [ ] a refused Review leaves the Session unchanged
- [ ] a Review sent after a Cancel is refused (found in ticket 04; it is accepted and then ignored, but the caller is still told it succeeded)
- [ ] `SessionHandle.cancel()` on a finished Session gives a clear error (found in ticket 04; it raises Temporal's "workflow already completed" error unwrapped)
