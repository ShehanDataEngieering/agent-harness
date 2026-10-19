# Spec: Agent Harness v1

Vocabulary follows [GLOSSARY.md](../GLOSSARY.md). Decisions with trade-offs are in [docs/adr](adr/).

## Problem

Sefira's Sophia Harness lets an AI agent design processes safely: it edits a Draft through governed operations, checks its own work, and only a human can publish. I want to understand that design by building it myself, without Logos code. I also want the same engine to run a second domain, compliance case review, for the Advisense forward-deployed engineering case. If both domains run on one core, the core is generic.

## Goals

- A durable Session: it survives a worker crash or a long wait for Review without losing state or acting twice.
- Code decides, models advise, humans approve: Checks gate, a Judgement advises, only Approval commits.
- A new domain is a Pack, not a change to the core.
- Quality is measured: EvaluationRuns score Fixtures against a pinned Rubric.

## Non-goals (v1)

- No UI; the CLI is the only interface.
- No real Sefira API, no multi-tenancy, no authentication.
- No production deployment; local Docker only.
- No agent framework (ADR 0002).

## User stories

Roles: **owner** (the human who starts a Session and does Review), **operator** (runs the harness), **evaluator** (measures quality).

### Session lifecycle

1. As an owner, I start a Session with a Task and a Pack, and the agent works it without further input.
2. As an owner, I see a Session's status at any time: its phase, step, Submission number and latest Checks and Judgement.
3. As an owner, I approve a Submission, and only then is the work committed.
4. As an owner, I reject a Submission with a reason, and the agent repairs and submits again.
5. As an owner, after my third Rejection the Session gives up without committing anything.
6. As an owner, I steer a working Session with extra guidance, and the agent receives it once, on its next agent step.
7. As an owner, I Cancel a Session at any time, and nothing is committed.
8. As an owner, my Review is refused if it does not match the current Submission, if the Session is not waiting for Review, or if a Rejection has no reason.
9. As an operator, a Session continues correctly after its worker is killed, including while it waits for Review.
10. As an operator, a Session that exceeds its step limit gives up instead of looping forever.

### Checking

11. As an owner, I never receive a Submission that fails a Check; failures go back to the agent.
12. As an owner, a Judgement that raises a concern gives the agent one repair attempt, and the Judgement is attached to the Submission I review.
13. As an owner, a Judgement never blocks a Submission.

### Process pack

14. As an owner, the agent builds a Draft through Capabilities: add step, connect steps, set owner.
15. As an owner, an agent edit based on a stale Revision is rejected and the agent must re-read the Draft.
16. As an owner, the agent can never publish; Approval publishes the Draft as a Published version.
17. As an owner, the agent searches the handbook and cites Clauses; a Citation to a Clause that does not exist fails a Check.
18. As an owner, a Capability called with invalid arguments returns the error to the agent instead of failing the Session.

### Models

19. As an operator, the Agent model is DeepSeek via OpenRouter, and the Judge model is a separate, configurable OpenRouter model.
20. As an operator, API keys come from the environment and never appear in logs or Traces.

### Evaluation

21. As an evaluator, I run an EvaluationRun over a Pack's Fixtures and get a composite score (0.75 Checks with partial credit, 0.25 Judgement), a per-dimension breakdown and pass^3.
22. As an evaluator, an EvaluationRun pins the Rubric version and both models, so runs are comparable.

### Advisense pack

23. As a compliance owner, the agent reviews a customer case using read-only Capabilities and proposes risk flags, each citing a Clause of a fictional AML policy.
24. As a compliance owner, my Approval commits the Decision; the agent never does.

### Trace

25. As an operator, I export a readable Trace of a Session, derived from its Temporal history, with every model call, Capability call, Check, Judgement and Review.

## Implementation decisions

- Temporal is the only record of Session state (ADR 0001). Model calls, Capabilities, Checks and Judgements run as activities.
- Review is a Temporal **Update** (it returns success or a refusal); steer and Cancel are **Signals**; status is a **Query**.
- Steering queues guidance in arrival order for the next agent activity, without repeating it on later steps. Currently another agent activity only follows a Rejection; guidance still queued at Approval is never delivered, and the Signal gives the owner no delivery confirmation.
- Each activity input carries an idempotency key derived from the Session ID and step.
- Own agent loop and hybrid retrieval, no framework (ADR 0002). Retrieval: BM25 (`tsvector`) plus pgvector, merged by Reciprocal Rank Fusion, embeddings via OpenRouter, cached per Clause.
- Capabilities use native tool calling; schemas come from Pydantic models.
- Limits: 30 agent steps per Session, 3 Rejections, 1 Judgement repair per Submission.
- Storage: Postgres with pgvector and the Temporal dev server, in one `docker-compose.yml`.
- The core never names a domain concept; domain words live only in Packs.

## Code standards

- Python 3.13, `uv`.
- Pydantic v2 for every boundary model: `strict=True, frozen=True, extra="forbid"`. Temporal uses `pydantic_data_converter`.
- pyright `strict`, zero errors. No `Any`; `Protocol` for interfaces; `NewType` IDs; `Literal`/`StrEnum` with `assert_never`.
- `pydantic-settings` for config; secrets are `SecretStr`.
- ruff lint and format.
- `make check` runs lint, types and tests.

## Testing decisions

- TDD in vertical slices: one failing test, minimal code, repeat.
- Seams:
  1. **Session seam** (most tests): drive a Session through the Temporal client (start, review, steer, cancel, status) in Temporal's time-skipping test environment.
  2. **Payload seam**: every workflow and activity model round-trips through the Pydantic data converter unchanged.
  3. **Replay seam**: recorded Session histories replay without nondeterminism errors.
- Fakes only at the model boundary (FakeAgent, FakeJudge) and for external systems of record. Never mock our own classes.
- Expected values are literals from the spec, never recomputed.
- Mutation testing on `core/` after each ticket is green; surviving mutants get a test or a written reason.
- Review with the `code-review` skill; `no-mistakes` gates every push.

## Tickets

See [docs/tickets](tickets/), in build order.
