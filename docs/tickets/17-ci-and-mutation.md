# 17 CI and mutation gate

**Status:** todo · **Seam:** — · **Depends on:** 01 · **Stories:** —

## What

GitHub Actions runs make check; mutation testing on core/ with a minimum score; no-mistakes gates pushes.

Note: the GitHub Actions workflow running make check on every PR and on main exists since PR #2 (ticket 01), so only the mutation gate remains.

## Acceptance tests

- [ ] CI fails on a lint, type or test error
- [ ] mutation score on core/ meets the agreed minimum
