# 03 Invalid Reviews are refused

**Status:** todo · **Seam:** Session · **Depends on:** 02 · **Stories:** 8

## What

The review Update validates before it is accepted, and the caller gets the refusal.

## Acceptance tests

- [ ] a Review naming an old Submission is refused
- [ ] a Review while the agent is still working is refused, and the work is not committed when the agent finishes (found in ticket 01 review: today an early Review is stored and commits as soon as the agent step returns)
- [ ] a Rejection without a reason is refused
- [ ] a refused Review leaves the Session unchanged
