# 08 Replay and worker crash

**Status:** todo · **Seam:** Replay, Session · **Depends on:** 07 · **Stories:** 9

## What

Record histories for the main paths and replay them in tests. Prove a Session survives a worker restart while waiting for Review.

## Acceptance tests

- [ ] recorded Session histories replay without nondeterminism errors (Replay seam)
- [ ] a Session waiting for Review completes after its worker is replaced
