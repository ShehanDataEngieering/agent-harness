"""Shared test setup, so each test file reads as just its story."""

import asyncio

from temporalio.client import Client
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner, SandboxRestrictions

from harness.core.client import SessionHandle, start_session
from harness.core.models import MAX_STEPS, PackName, Phase, Review, SessionId, SessionInput, Work

# Mutation testing injects `mutmut` trampolines into workflow code; they read os.environ.
# Passing the module through keeps the determinism sandbox on for everything else.
SANDBOX = SandboxedWorkflowRunner(
    restrictions=SandboxRestrictions.default.with_passthrough_modules("mutmut")
)

NOTES = PackName("notes")
NOTE = Work(summary="first note", content="Remember the milk.")
SECOND_NOTE = Work(summary="second note", content="Remember the milk, 2 litres.")
BLANK_NOTE = Work(summary="blank note", content="")
APPROVAL = Review(submission=1, verdict="approval", reviewer="owner")
REJECTION = Review(submission=1, verdict="rejection", reviewer="owner", reason="Too vague.")


async def start(
    client: Client, task_queue: str, session_id: str, max_steps: int = MAX_STEPS
) -> SessionHandle:
    return await start_session(
        client,
        SessionInput(pack=NOTES, task="Write a note", max_steps=max_steps),
        session_id=SessionId(session_id),
        task_queue=task_queue,
    )


async def until_awaiting_review(session: SessionHandle, submission: int = 1) -> None:
    """Poll status until the Session waits for a human on this Submission (gives up after 10 s)."""
    async with asyncio.timeout(10):
        while True:
            status = await session.status()
            if (status.phase, status.submission) == (Phase.AWAITING_REVIEW, submission):
                return
            await asyncio.sleep(0.05)
