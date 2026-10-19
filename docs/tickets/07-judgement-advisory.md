# 07 Judgement advises, never blocks

**Status:** todo · **Seam:** Session · **Depends on:** 06 · **Stories:** 12, 13

## What

After Checks pass, the Judge model assesses the work. A concern (or Unknown) gives the agent one repair attempt per Submission; the Judgement is attached to the Submission.

## Acceptance tests

- [ ] a Judgement concern gives the agent one repair attempt
- [ ] a second concern on the same Submission does not block it
- [ ] the Submission shows the latest Judgement with reasons and confidence
