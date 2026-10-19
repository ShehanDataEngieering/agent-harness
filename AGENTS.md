# Agent Harness — instructions for coding agents

Read before changing code: [GLOSSARY.md](GLOSSARY.md) (use its words, avoid its _Avoid_ words), [docs/adr](docs/adr/) (don't undo an ADR without writing a new one), [docs/spec.md](docs/spec.md), [docs/tickets](docs/tickets/).

## Workflow

1. Work one ticket at a time, in order. Mark its status and acceptance boxes as they pass.
2. TDD in vertical slices: one failing test at an agreed seam, then the minimum code to pass it. Seams: Session, Payload, Replay (see spec). Never mock our own classes; fake only models and external systems.
3. After a ticket is green: refactor under the `code-review` skill, run mutation testing on `src/harness/core/`, then `no-mistakes` before any push.

## Code standards

- Python 3.13 via `uv`. `make check` (ruff + pyright strict + pytest) must pass.
- Pydantic v2 models at every boundary: `strict=True, frozen=True, extra="forbid"`. Temporal uses `pydantic_data_converter`.
- pyright strict, zero errors. No `Any`. `Protocol` for interfaces, `NewType` for IDs, `Literal`/`StrEnum` + `assert_never` for closed sets. `# type: ignore` only with a reason.
- Secrets are `SecretStr` from `pydantic-settings`; never log them.
- `src/harness/core/` never names a domain concept; domain words live in Packs.

## Temporal rules

- Workflow code is deterministic: no I/O, `datetime.now()`, `uuid4()` or `random` (use `workflow.now()` / `workflow.uuid4()`). Model calls, Capabilities, Checks and Judgements are activities.
- Import models into workflow modules inside `workflow.unsafe.imports_passed_through()`.
- Review is an Update; steer and Cancel are Signals; status is a Query.
- Activity inputs carry an idempotency key (Session ID + step).
