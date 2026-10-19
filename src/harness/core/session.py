"""BRAIN: the step-by-step story of one Session.

Read `run()` as three steps: ask the agent -> wait for the human -> commit the work.

This is a Temporal workflow, so it only *decides* what happens next. It never does I/O
itself (no model calls, no saving): it asks activities to do that (see activities.py).
Temporal records every decision, so after a crash it can replay this code and carry on
from exactly where it was (ADR 0001).
"""

from datetime import timedelta

from temporalio import workflow

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


@workflow.defn
class SessionWorkflow:
    def __init__(self) -> None:
        # The Session's state. It lives only in Temporal's history (no database of our own).
        self._phase = Phase.WORKING
        self._step = 0  # every activity the Session asks for is one step
        self._submission = 0  # how many times the work has been handed to a human
        self._review: Review | None = None  # set by the review Update below

    @workflow.run
    async def run(self, session: SessionInput) -> SessionOutcome:
        # The workflow ID doubles as the Session ID.
        session_id = SessionId(workflow.info().workflow_id)

        # Step 1: ask the agent to do the Task.
        self._step += 1
        work = await workflow.execute_activity_method(
            SessionActivities.agent_work,
            AgentRequest(
                pack=session.pack,
                task=session.task,
                step=self._step,
                idempotency_key=idempotency_key(session_id, self._step),
            ),
            start_to_close_timeout=ACTIVITY_TIMEOUT,
        )

        # Step 2: submit the work and wait for a human Review.
        # The wait costs nothing and survives worker restarts; it can last for days.
        self._submission = 1
        self._phase = Phase.AWAITING_REVIEW
        await workflow.wait_condition(lambda: self._review is not None)

        # Step 3: the human approved, so commit. Only the workflow commits, never the agent.
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

    # Update = a message from outside that gets an answer back (the caller learns if it worked).
    @workflow.update
    async def review(self, review: Review) -> None:
        self._review = review  # wakes up the wait_condition in Step 2

    # Query = read-only peek at the Session's state; it never changes anything.
    @workflow.query
    def status(self) -> SessionStatus:
        return SessionStatus(phase=self._phase, step=self._step, submission=self._submission)
