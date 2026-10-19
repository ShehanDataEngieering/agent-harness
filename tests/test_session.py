"""WHAT IT DOES: the Session's behaviour, proven from the outside.

Read the test names first: each one is a line of the spec. Every test has three parts:
  ARRANGE - set up fakes (a scripted agent, an in-memory ledger)
  ACT     - drive the Session through its SessionHandle, like a real caller would
  ASSERT  - check one observable result
Tests never reach inside the workflow; that is what lets the code be refactored freely.
"""

from temporalio.client import Client

from harness.core.models import Phase, SessionStatus
from harness.core.worker import Dependencies, session_worker
from tests.fakes import FakeAgent, Ledger, NotesPack, PausingAgent
from tests.support import APPROVAL, NOTE, SANDBOX, start, until_awaiting_review


async def test_an_approved_submission_completes_the_session_as_approved_with_the_work_committed(
    client: Client,
) -> None:
    # ARRANGE: an agent that writes one note, and a ledger to commit it to
    ledger = Ledger()
    deps = Dependencies(agent=FakeAgent(script=[NOTE]), packs=[NotesPack(ledger)])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        # ACT: start, wait for the Submission, approve it, wait for the end
        session = await start(client, task_queue, "session-approved")
        await until_awaiting_review(session)
        await session.review(APPROVAL)
        outcome = await session.outcome()

    # ASSERT: the Session ended approved and the note reached the ledger
    assert (outcome.phase, ledger.entries) == (Phase.APPROVED, [NOTE])


async def test_status_shows_the_session_waiting_for_review_on_submission_1_after_step_1(
    client: Client,
) -> None:
    deps = Dependencies(agent=FakeAgent(script=[NOTE]), packs=[NotesPack(Ledger())])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-status")
        await until_awaiting_review(session)
        status = await session.status()
        await session.review(APPROVAL)

    assert status == SessionStatus(phase=Phase.AWAITING_REVIEW, step=1, submission=1)


async def test_status_shows_the_session_working_on_step_1_with_nothing_submitted_yet(
    client: Client,
) -> None:
    agent = PausingAgent(result=NOTE)
    deps = Dependencies(agent=agent, packs=[NotesPack(Ledger())])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-working")
        await agent.started.wait()
        status = await session.status()
        agent.finish.set()
        await until_awaiting_review(session)
        await session.review(APPROVAL)

    assert status == SessionStatus(phase=Phase.WORKING, step=1, submission=0)


async def test_an_agent_step_carries_the_session_id_and_step_as_its_idempotency_key(
    client: Client,
) -> None:
    agent = FakeAgent(script=[NOTE])
    deps = Dependencies(agent=agent, packs=[NotesPack(Ledger())])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-agent-key")
        await until_awaiting_review(session)
        await session.review(APPROVAL)
        await session.outcome()

    assert [request.idempotency_key for request in agent.requests] == ["session-agent-key:1"]


async def test_the_commit_reaches_the_pack_with_the_session_id_and_step_as_its_idempotency_key(
    client: Client,
) -> None:
    ledger = Ledger()
    deps = Dependencies(agent=FakeAgent(script=[NOTE]), packs=[NotesPack(ledger)])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-commit-key")
        await until_awaiting_review(session)
        await session.review(APPROVAL)
        await session.outcome()

    assert ledger.keys == ["session-commit-key:2"]
