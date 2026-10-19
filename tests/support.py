"""Shared test setup, so each test file reads as just its story."""

import asyncio

from temporalio.client import Client
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner, SandboxRestrictions

from harness.core.client import SessionHandle, start_session
from harness.core.models import PackName, Phase, Review, SessionId, SessionInput, Work

# Mutation testing injects `mutmut` trampolines into workflow code; they read os.environ.
# Passing the module through keeps the determinism sandbox on for everything else.
SANDBOX = SandboxedWorkflowRunner(
    restrictions=SandboxRestrictions.default.with_passthrough_modules("mutmut")
)

NOTES = PackName("notes")
NOTE = Work(summary="first note", content="Remember the milk.")
APPROVAL = Review(submission=1, verdict="approval", reviewer="owner")


async def start(client: Client, task_queue: str, session_id: str) -> SessionHandle:
    return await start_session(
        client,
        SessionInput(pack=NOTES, task="Write a note"),
        session_id=SessionId(session_id),
        task_queue=task_queue,
    )


async def until_awaiting_review(session: SessionHandle) -> None:
    """Poll status until the Session is waiting for a human (gives up after 10 s)."""
    async with asyncio.timeout(10):
        while (await session.status()).phase is not Phase.AWAITING_REVIEW:
            await asyncio.sleep(0.05)
