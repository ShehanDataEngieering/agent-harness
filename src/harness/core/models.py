"""DATA: the shapes of everything that crosses the workflow/activity boundary.

Think Zod schemas: each class is both a type and a runtime validator. Temporal stores
these as JSON in its history and checks them again when it reads them back.
"""

from enum import StrEnum
from typing import Literal, NewType

from pydantic import BaseModel, ConfigDict

# Typed IDs: all plain strings underneath, but the type checker won't let one stand in for another.
SessionId = NewType("SessionId", str)
PackName = NewType("PackName", str)
IdempotencyKey = NewType("IdempotencyKey", str)

# How many agent steps a Session may take before it gives up (spec: Limits).
MAX_STEPS = 30


def idempotency_key(session_id: SessionId, step: int) -> IdempotencyKey:
    """The one rule for keys: Session ID + step. Same key = same step, never done twice."""
    return IdempotencyKey(f"{session_id}:{step}")


class Payload(BaseModel):
    # strict: no silent conversions ("1" is not an int); frozen: read-only after creation;
    # forbid: unknown fields are an error, not ignored.
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")


class Phase(StrEnum):
    """Where a Session is in its life."""

    WORKING = "working"
    AWAITING_REVIEW = "awaiting_review"
    COMMITTING = "committing"
    APPROVED = "approved"
    GAVE_UP = "gave_up"  # too many Rejections or out of steps; nothing was committed


class SessionInput(Payload):
    """What you give a Session when you start it."""

    pack: PackName  # which Pack handles this Session
    task: str  # what the human asked for, in words
    max_steps: int = MAX_STEPS  # the step limit; tests set a small one


class Work(Payload):
    """What the agent produced. Its content's meaning belongs to the Pack."""

    summary: str
    content: str


class AgentRequest(Payload):
    """One step asked of the agent."""

    pack: PackName
    task: str
    step: int
    rejection_reason: str | None  # why the last Submission was rejected; None on the first try
    check_failures: tuple[str, ...]  # what the Checks found in the last step's work; () if none
    idempotency_key: IdempotencyKey  # a retry of this step reuses the key


class Receipt(Payload):
    """Proof that a commit happened, pointing at what was written."""

    reference: str


class CommitRequest(Payload):
    """Approved work to make real, through the Session's Pack."""

    pack: PackName
    work: Work
    idempotency_key: IdempotencyKey  # passed to the Pack so a retried commit lands once


class CheckRequest(Payload):
    """The agent's latest work, to run through the Pack's Checks."""

    pack: PackName
    work: Work
    idempotency_key: IdempotencyKey  # the key of the agent step that produced the work


class CheckReport(Payload):
    """What the Checks found. Empty failures means the work may be submitted."""

    failures: tuple[str, ...]


class Review(Payload):
    """A human's verdict on one Submission."""

    submission: int  # which Submission this Review is about
    verdict: Literal["approval", "rejection"]
    reviewer: str
    reason: str | None = None  # why a Rejection sends the work back


class SessionStatus(Payload):
    """What the status Query shows."""

    phase: Phase
    step: int  # how many steps the Session has taken
    submission: int


class SessionOutcome(Payload):
    """How a Session ended."""

    phase: Phase
    receipt: Receipt | None  # None when nothing was committed
