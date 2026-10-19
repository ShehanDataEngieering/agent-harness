"""BRAIN: the step-by-step story of one Session.

Read `run()` as three steps: ask the agent -> wait for the human -> commit the work.
A Rejection loops back to step 1 with the human's reason; the third one gives up.

This is a Temporal workflow, so it only *decides* what happens next. It never does I/O
itself (no model calls, no saving): it asks activities to do that (see activities.py).
Temporal records every decision, so after a crash it can replay this code and carry on
from exactly where it was (ADR 0001).
"""

from datetime import timedelta
from typing import assert_never

from temporalio import workflow

# Temporal runs workflow code in a sandbox that blocks anything non-deterministic.
# Our own models are safe, so we let them through unchanged.
with workflow.unsafe.imports_passed_through():
    from harness.core.activities import SessionActivities
    from harness.core.models import (
        AgentRequest,
        CheckRequest,
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


# Before the commit, the step count is the number of agent steps taken.
def out_of_steps(steps: int, max_steps: int) -> bool:
    return steps >= max_steps


@workflow.defn
class SessionWorkflow:
    def __init__(self) -> None:
        # The Session's state. It lives only in Temporal's history (no database of our own).
        self._phase = Phase.WORKING
        # Each agent step, and the commit, is one step; Checks share their agent's step.
        self._step = 0
        self._submission = 0  # how many times the work has been handed to a human
        self._rejections = 0  # how many of those Submissions were sent back
        self._reviews: list[Review] = []  # filled by the review Update below

    @workflow.run
    async def run(self, session: SessionInput) -> SessionOutcome:
        # The workflow ID doubles as the Session ID.
        session_id = SessionId(workflow.info().workflow_id)

        rejection_reason: str | None = None
        check_failures: tuple[str, ...] = ()
        while True:
            # The step limit stops endless repair: give up instead of taking another step.
            if out_of_steps(self._step, session.max_steps):
                self._phase = Phase.GAVE_UP
                return SessionOutcome(phase=self._phase, receipt=None)

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
                    check_failures=check_failures,
                    idempotency_key=idempotency_key(session_id, self._step),
                ),
                start_to_close_timeout=ACTIVITY_TIMEOUT,
            )

            # Checks gate the Submission: work that fails one goes back to the agent.
            report = await workflow.execute_activity_method(
                SessionActivities.check_work,
                CheckRequest(
                    pack=session.pack,
                    work=work,
                    idempotency_key=idempotency_key(session_id, self._step),
                ),
                start_to_close_timeout=ACTIVITY_TIMEOUT,
            )
            check_failures = report.failures
            if check_failures:
                continue

            # Step 2: submit the work and wait for a human Review.
            # The wait costs nothing and survives worker restarts; it can last for days.
            # Reviews that arrived while the agent worked were not about this Submission: drop them.
            self._submission += 1
            self._phase = Phase.AWAITING_REVIEW
            self._reviews.clear()
            # Only a Review naming this Submission counts; Reviews of older ones are ignored.
            await workflow.wait_condition(lambda: bool(self._reviews_of_this_submission()))
            review = self._reviews_of_this_submission()[-1]  # the newest one answers it

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

    def _reviews_of_this_submission(self) -> list[Review]:
        return [review for review in self._reviews if review.submission == self._submission]

    # Update = a message from outside that gets an answer back (the caller learns if it worked).
    @workflow.update
    async def review(self, review: Review) -> None:
        self._reviews.append(review)  # wakes up the wait_condition in Step 2

    # Query = read-only peek at the Session's state; it never changes anything.
    @workflow.query
    def status(self) -> SessionStatus:
        return SessionStatus(phase=self._phase, step=self._step, submission=self._submission)
