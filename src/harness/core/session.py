"""BRAIN: the step-by-step story of one Session.

Read `run()` as three steps: ask the agent -> wait for the human -> commit the work.
A Rejection loops back to step 1 with the human's reason; the third one gives up.

This is a Temporal workflow, so it only *decides* what happens next. It never does I/O
itself (no model calls, no saving): it asks activities to do that (see activities.py).
Temporal records every decision, so after a crash it can replay this code and carry on
from exactly where it was (ADR 0001).
"""

from datetime import timedelta
from typing import assert_never, cast

from temporalio import workflow
from temporalio.exceptions import ApplicationError

# Temporal runs workflow code in a sandbox that blocks anything non-deterministic.
# Our own models are safe, so we let them through unchanged.
with workflow.unsafe.imports_passed_through():
    from harness.core.activities import SessionActivities
    from harness.core.models import (
        AgentRequest,
        CommitRequest,
        Phase,
        Review,
        SessionId,
        SessionInput,
        SessionOutcome,
        SessionStatus,
        idempotency_key,
    )

# How long one activity (one agent step, one commit) may run before Temporal retries it.
ACTIVITY_TIMEOUT = timedelta(minutes=2)

# How many times a human may send the work back before the Session gives up (spec: Limits).
MAX_REJECTIONS = 3

# The error type a refused Review carries back to the caller (see client.ReviewRefusedError).
REVIEW_REFUSED = "ReviewRefused"


@workflow.defn
class SessionWorkflow:
    def __init__(self) -> None:
        # The Session's state. It lives only in Temporal's history (no database of our own).
        self._phase = Phase.WORKING
        self._step = 0  # every activity the Session asks for is one step
        self._submission = 0  # how many times the work has been handed to a human
        self._rejections = 0  # how many of those Submissions were sent back
        self._review: Review | None = None  # this Submission's Review, set by the Update below
        self._cancelled = False  # set by the cancel Signal below

    @workflow.run
    async def run(self, session: SessionInput) -> SessionOutcome:
        # The workflow ID doubles as the Session ID.
        session_id = SessionId(workflow.info().workflow_id)

        rejection_reason: str | None = None
        while True:
            # Step 1: ask the agent to do the Task (with the reason, if it was sent back).
            self._phase = Phase.WORKING
            self._step += 1
            work = await workflow.execute_activity_method(
                SessionActivities.agent_work,
                AgentRequest(
                    pack=session.pack,
                    task=session.task,
                    step=self._step,
                    rejection_reason=rejection_reason,
                    idempotency_key=idempotency_key(session_id, self._step),
                ),
                start_to_close_timeout=ACTIVITY_TIMEOUT,
            )
            if self._cancelled:  # a Cancel during the step lets the step finish, then ends
                return self._cancelled_outcome()

            # Step 2: submit the work and wait for a human Review.
            # The wait costs nothing and survives worker restarts; it can last for days.
            self._submission += 1
            self._review = None
            self._phase = Phase.AWAITING_REVIEW
            await workflow.wait_condition(lambda: self._review is not None or self._cancelled)
            if self._cancelled:  # checked first, so a Cancel beside an Approval commits nothing
                return self._cancelled_outcome()
            review = cast(Review, self._review)  # the wait above guarantees it is set

            match review.verdict:
                case "approval":
                    # Step 3: commit the latest work. Only the workflow commits, never the agent.
                    self._phase = Phase.COMMITTING
                    self._step += 1
                    receipt = await workflow.execute_activity_method(
                        SessionActivities.commit_work,
                        CommitRequest(
                            pack=session.pack,
                            work=work,
                            idempotency_key=idempotency_key(session_id, self._step),
                        ),
                        start_to_close_timeout=ACTIVITY_TIMEOUT,
                    )
                    self._phase = Phase.APPROVED
                    return SessionOutcome(phase=self._phase, receipt=receipt)
                case "rejection":
                    # Sent back: give up after the last allowed Rejection, else try again.
                    self._rejections += 1
                    if self._rejections == MAX_REJECTIONS:
                        self._phase = Phase.GAVE_UP
                        return SessionOutcome(phase=self._phase, receipt=None)
                    rejection_reason = review.reason
                case _:
                    assert_never(review.verdict)  # a new verdict must be handled above

    # Update = a message from outside that gets an answer back (the caller learns if it worked).
    @workflow.update
    async def review(self, review: Review) -> None:
        # Two Reviews in one batch both pass the validator before either is handled,
        # so check again here: the second one fails instead of overwriting the first.
        self._refuse_if_invalid(review)
        self._review = review  # wakes up the wait_condition in Step 2

    # Runs before the Update is accepted: a refused Review never reaches the handler or the
    # history, so the Session is unchanged and the caller gets the reason.
    @review.validator
    def validate_review(self, review: Review) -> None:
        self._refuse_if_invalid(review)

    # The rules live in plain methods so mutation testing reaches them (it skips decorated ones).
    def _refuse_if_invalid(self, review: Review) -> None:
        # An ApplicationError fails only the Update; any other error would fail the workflow task.
        if (refusal := self._refusal(review)) is not None:
            raise ApplicationError(refusal, type=REVIEW_REFUSED)

    def _refusal(self, review: Review) -> str | None:
        """Why this Review cannot be accepted now, or None if it can."""
        if self._phase != Phase.AWAITING_REVIEW:
            return f"the Session is not waiting for a Review (it is {self._phase})"
        if self._review is not None:
            return f"Submission {self._submission} already has a Review"
        if review.submission != self._submission:
            return (
                f"the Review names Submission {review.submission}, "
                f"but Submission {self._submission} is waiting"
            )
        if review.verdict == "rejection" and not (review.reason or "").strip():
            return "a Rejection needs a reason to send back to the agent"
        return None

    # Signal = a one-way message from outside; the caller gets no answer back.
    @workflow.signal
    def cancel(self) -> None:
        self._cancelled = True  # the Session ends at its next decision point

    # Query = read-only peek at the Session's state; it never changes anything.
    @workflow.query
    def status(self) -> SessionStatus:
        return SessionStatus(phase=self._phase, step=self._step, submission=self._submission)

    # A Cancel ends the Session as cancelled, with nothing committed.
    def _cancelled_outcome(self) -> SessionOutcome:
        self._phase = Phase.CANCELLED
        return SessionOutcome(phase=self._phase, receipt=None)
