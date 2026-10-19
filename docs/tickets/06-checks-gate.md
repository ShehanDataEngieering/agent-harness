# 06 Checks gate the Submission

**Status:** todo · **Seam:** Session · **Depends on:** 01 · **Stories:** 10, 11

## What

The Pack's Checks run after each agent step. A failing Check sends the failures back to the agent instead of submitting. The step limit stops endless repair.

## Acceptance tests

- [ ] work that fails a Check is never submitted
- [ ] the Check failures are given to the agent on its next step
- [ ] a Session that reaches the step limit ends as given up
