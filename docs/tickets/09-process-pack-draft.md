# 09 Process pack: Draft with Revisions

**Status:** todo · **Seam:** Session · **Depends on:** 08 · **Stories:** 14, 15, 16

## What

A mock draft store holds Drafts with Revisions. Capabilities with Effects: read_draft (read), add_step, connect_steps, set_owner (draft-write), publish (commit). The workflow, not the agent, calls commit Capabilities after Approval.

## Acceptance tests

- [ ] the agent builds a Draft through draft-write Capabilities
- [ ] an edit based on a stale Revision is rejected and the agent is told to re-read
- [ ] the agent is never offered a commit Capability
- [ ] Approval publishes the Draft as a Published version
