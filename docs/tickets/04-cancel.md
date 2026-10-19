# 04 Cancel ends a Session

**Status:** todo · **Seam:** Session · **Depends on:** 01 · **Stories:** 7

## What

A Cancel Signal ends the Session whether it is working or waiting for Review.

## Acceptance tests

- [ ] a Cancel while waiting for Review ends the Session as cancelled, with nothing committed
- [ ] a Cancel while the agent is working ends the Session as cancelled after the current step
