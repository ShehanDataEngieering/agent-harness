"""BUTTONS: how anything outside Temporal (tests, later the CLI) starts and drives a Session.

start_session() starts one; the SessionHandle it returns has a method per thing you can do.
"""

from temporalio.client import Client, WorkflowHandle, WorkflowUpdateFailedError
from temporalio.exceptions import ApplicationError

from harness.core.models import (
    Review,
    SessionId,
    SessionInput,
    SessionOutcome,
    SessionStatus,
    SteerRequest,
)
from harness.core.session import REVIEW_REFUSED, SessionWorkflow


class ReviewRefusedError(Exception):
    """The Session refused a Review; nothing about the Session changed."""


class SessionHandle:
    """A remote control for one running Session."""

    def __init__(self, handle: WorkflowHandle[SessionWorkflow, SessionOutcome]) -> None:
        self._handle = handle

    @property
    def session_id(self) -> SessionId:
        return SessionId(self._handle.id)

    async def status(self) -> SessionStatus:
        """Peek at where the Session is (a Query: changes nothing)."""
        return await self._handle.query(SessionWorkflow.status)

    async def review(self, review: Review) -> None:
        """Send a human Review (an Update: waits until the Session has accepted it).

        Raises ReviewRefusedError, with the Session's reason, if the Session refuses it.
        """
        try:
            # temporalio's execute_update overloads include an untyped `args` variant, which
            # pyright strict reports as partially unknown. The single-arg overload used is typed.
            await self._handle.execute_update(SessionWorkflow.review, review)  # pyright: ignore[reportUnknownMemberType]
        except WorkflowUpdateFailedError as error:
            cause = error.cause
            if isinstance(cause, ApplicationError) and cause.type == REVIEW_REFUSED:
                raise ReviewRefusedError(cause.message) from error
            raise

    async def cancel(self) -> None:
        """Send a Cancel Signal; see GLOSSARY.md's Cancel contract."""
        await self._handle.signal(SessionWorkflow.cancel)

    async def steer(self, guidance: str) -> None:
        """Send extra guidance for the agent's next step (a Signal: no answer comes back)."""
        await self._handle.signal(SessionWorkflow.steer, SteerRequest(guidance=guidance))

    async def outcome(self) -> SessionOutcome:
        """Wait for the Session to finish and return how it ended."""
        return await self._handle.result()


async def start_session(
    client: Client, session: SessionInput, *, session_id: SessionId, task_queue: str
) -> SessionHandle:
    """Start a new Session on the given task queue and return its remote control."""
    handle = await client.start_workflow(
        SessionWorkflow.run, session, id=session_id, task_queue=task_queue
    )
    return SessionHandle(handle)
