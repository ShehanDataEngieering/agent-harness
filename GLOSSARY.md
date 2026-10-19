# Agent Harness

A personal learning rebuild of the ideas behind Sefira's Sophia Harness: an AI agent that works a task through governed tools, checks its own work and waits for a human. Domain-specific behaviour lives in Packs so the same core serves process design and compliance review.

## Language

**Session**:
One agent working one Task from start to finish; durable, and it can be paused, steered and resumed.
_Avoid_: Run, Job

**Pack**:
A pluggable domain that supplies everything domain-specific: tools, documents, prompt, output shape and scoring.
_Avoid_: Plugin, domain module

**Process pack**:
The first Pack, mirroring Sophia: the agent designs or edits a process draft.

**Advisense pack**:
The second Pack: the agent reviews a customer case for compliance risk.

**Agent model**:
The model that does the work inside a Session.
_Avoid_: Worker model, main model

**Judge model**:
A different model from the Agent model, used only to produce Judgements.

**Capability**:
A typed, governed operation a Session may perform, which declares its Effect.
_Avoid_: Tool, function, action

**Effect**:
What a Capability is allowed to change: `read` (nothing), `draft-write` (the agent's own working state) or `commit` (real state, only after an Approval and never by the agent).
_Avoid_: Permission, scope

**Clause**:
One retrievable passage of a Pack's documents, with a stable ID such as `handbook#4.2`.
_Avoid_: Chunk, passage, section

**Citation**:
A reference from the agent's work to a Clause ID; it is only valid if that Clause exists.
_Avoid_: Source, reference

**Check**:
A deterministic rule the agent's work must pass inside a Session; same input, same result, every time.
_Avoid_: Validation, test

**Judgement**:
A separate model's advisory assessment of the agent's work inside a Session, carrying reasons and confidence (or "Unknown"); it can prompt one repair but never blocks a Submission.
_Avoid_: Review (that is the human's), score

**Rubric**:
The versioned set of Checks, judged dimensions and weights that defines what "good" means for a Pack; once an EvaluationRun starts, its Rubric cannot change.

**Fixture**:
A labelled test Task with its known-good expectations, used to score the agent offline.
_Avoid_: Test case, example

**EvaluationRun**:
An offline scoring of many Fixtures against one pinned Rubric version and one model, giving per-dimension results and a weighted composite score; separate from any Session.
_Avoid_: Eval, benchmark

**Submission**:
The point where a Session hands its work to a human for Review; the Session then waits.

**Review**:
A human's verdict on a Submission: either an Approval or a Rejection.

**Approval**:
The Review verdict that commits a Session's work (in the Process pack, publishes the Draft). The agent can never approve its own work.

**Rejection**:
The Review verdict that sends the work back to the agent with a reason; a Session allows at most three Rejections before it gives up.

**Cancel**:
A human ending a Session at any time, without committing anything.
_Avoid_: Abort, stop

## Process pack

**Draft**:
The editable, unpublished copy of a process; both a human and the agent may change it, and it can be checked but never run.
_Avoid_: Working copy

**Revision**:
The number of a Draft's current state; every edit names the Revision it was based on and is rejected if the Draft has moved on.

**Published version**:
A frozen, approved copy of a process; it never changes, and real runs use it.
_Avoid_: Release
