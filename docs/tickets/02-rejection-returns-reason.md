# 02 Rejection returns the reason to the agent

**Status:** todo · **Seam:** Session · **Depends on:** 01 · **Stories:** 4, 5

## What

A Rejection with a reason sends the work back; the agent sees the reason on its next step and submits again as Submission 2. The third Rejection makes the Session give up.

## Acceptance tests

- [ ] a rejected Submission returns to the agent with the reason
- [ ] the resubmitted work is Submission 2
- [ ] the third Rejection ends the Session as given up, with nothing committed
