# 03 Invalid Reviews are refused

**Status:** todo · **Seam:** Session · **Depends on:** 02 · **Stories:** 8

## What

The review Update validates before it is accepted, and the caller gets the refusal.

## Acceptance tests

- [ ] a Review naming an old Submission is refused
- [ ] a Review while the agent is still working is refused
- [ ] a Rejection without a reason is refused
- [ ] a refused Review leaves the Session unchanged
