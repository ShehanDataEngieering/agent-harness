# 10 Native Capability calling

**Status:** todo · **Seam:** Session · **Depends on:** 09 · **Stories:** 18

## What

The agent loop turns Capabilities into tool definitions from their Pydantic argument models, executes returned tool calls as activities, and returns invalid-argument errors to the agent.

## Acceptance tests

- [ ] a Capability called with invalid arguments returns the error to the agent and the Session continues
- [ ] a retried draft-write with the same idempotency key is applied once
