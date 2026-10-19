# Tickets

Build in order. Each ticket is one vertical slice, done with TDD at the named seams.

| # | Ticket | Depends on |
|---|---|---|
| 01 | [Approved Submission commits the work](01-approved-submission-commits.md) | — |
| 02 | [Rejection returns the reason to the agent](02-rejection-returns-reason.md) | 01 |
| 03 | [Invalid Reviews are refused](03-invalid-review-refused.md) | 02 |
| 04 | [Cancel ends a Session](04-cancel.md) | 01 |
| 05 | [Steering reaches the agent](05-steer.md) | 01 |
| 06 | [Checks gate the Submission](06-checks-gate.md) | 01 |
| 07 | [Judgement advises, never blocks](07-judgement-advisory.md) | 06 |
| 08 | [Replay and worker crash](08-replay-and-crash.md) | 07 |
| 09 | [Process pack: Draft with Revisions](09-process-pack-draft.md) | 08 |
| 10 | [Native Capability calling](10-capability-calling.md) | 09 |
| 11 | [Hybrid retrieval and Citations](11-hybrid-retrieval.md) | 10 |
| 12 | [OpenRouter models](12-openrouter-models.md) | 10 |
| 13 | [CLI and local stack](13-cli-and-local-stack.md) | 12 |
| 14 | [EvaluationRun](14-evaluation-run.md) | 12 |
| 15 | [Trace export](15-trace-export.md) | 12 |
| 16 | [Advisense pack](16-advisense-pack.md) | 14 |
| 17 | [CI and mutation gate](17-ci-and-mutation.md) | 01 |
