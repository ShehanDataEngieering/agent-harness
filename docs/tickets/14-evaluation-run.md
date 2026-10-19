# 14 EvaluationRun

**Status:** todo · **Seam:** Evaluation · **Depends on:** 12 · **Stories:** 21, 22

## What

Fixtures and a versioned Rubric per Pack. Composite = 0.75 Checks (partial credit) + 0.25 Judgement, per-dimension breakdown, pass^3. Pins Rubric version and both models.

## Acceptance tests

- [ ] an EvaluationRun over known Fixtures reports the expected composite and per-dimension scores
- [ ] pass^3 counts a Fixture only if all three trials pass
- [ ] an EvaluationRun records the Rubric version and both models
