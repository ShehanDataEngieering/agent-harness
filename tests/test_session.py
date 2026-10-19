"""WHAT IT DOES: the Session's behaviour, proven from the outside.

Read the test names first: each one is a line of the spec. Every test has three parts:
  ARRANGE - set up fakes (a scripted agent, an in-memory ledger)
  ACT     - drive the Session through its SessionHandle, like a real caller would
  ASSERT  - check one observable result
Tests never reach inside the workflow; that is what lets the code be refactored freely.
"""

import asyncio

import pytest
from temporalio.client import Client, WorkflowFailureError

from harness.core.client import ReviewRefusedError
from harness.core.models import PackName, Phase, Receipt, Review, SessionOutcome, SessionStatus
from harness.core.worker import Dependencies, session_worker
from tests.fakes import FakeAgent, Ledger, NotesPack, PausingAgent, PausingPack
from tests.support import (
    APPROVAL,
    NOTE,
    REJECTION,
    SANDBOX,
    SECOND_NOTE,
    start,
    until_awaiting_review,
)


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


async def test_status_shows_the_session_committing_while_the_approved_work_is_being_committed(
    client: Client,
) -> None:
    pack = PausingPack()
    deps = Dependencies(agent=FakeAgent(script=[NOTE]), packs=[pack])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-committing")
        await until_awaiting_review(session)
        await session.review(APPROVAL)
        await pack.started.wait()
        status = await session.status()
        pack.finish.set()
        await session.outcome()

    assert status == SessionStatus(phase=Phase.COMMITTING, step=2, submission=1)


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


async def test_a_session_for_an_unknown_pack_fails_before_any_work(client: Client) -> None:
    agent = FakeAgent(script=[NOTE])
    deps = Dependencies(agent=agent, packs=[NotesPack(Ledger(), name=PackName("other"))])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-unknown-pack")
        with pytest.raises(WorkflowFailureError):
            await session.outcome()

    assert agent.requests == []


async def test_a_rejected_submission_returns_to_the_agent_with_the_reason(
    client: Client,
) -> None:
    agent = FakeAgent(script=[NOTE])
    deps = Dependencies(agent=agent, packs=[NotesPack(Ledger())])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-rejected")
        await until_awaiting_review(session)
        await session.review(REJECTION)
        await until_awaiting_review(session, submission=2)
        await session.review(Review(submission=2, verdict="approval", reviewer="owner"))
        await session.outcome()

    assert [request.rejection_reason for request in agent.requests] == [None, "Too vague."]


async def test_the_resubmitted_work_is_submission_2(client: Client) -> None:
    ledger = Ledger()
    deps = Dependencies(agent=FakeAgent(script=[NOTE, SECOND_NOTE]), packs=[NotesPack(ledger)])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-resubmitted")
        await until_awaiting_review(session)
        await session.review(REJECTION)
        await until_awaiting_review(session, submission=2)
        status = await session.status()
        await session.review(Review(submission=2, verdict="approval", reviewer="owner"))
        await session.outcome()

    # the Submission it waits on is 2, and approving it commits the second try, not the first
    assert (status, ledger.entries) == (
        SessionStatus(phase=Phase.AWAITING_REVIEW, step=2, submission=2),
        [SECOND_NOTE],
    )


async def test_the_third_rejection_ends_the_session_as_given_up_with_nothing_committed(
    client: Client,
) -> None:
    agent = FakeAgent(script=[NOTE])
    ledger = Ledger()
    deps = Dependencies(agent=agent, packs=[NotesPack(ledger)])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-given-up")
        for submission in (1, 2, 3):
            await until_awaiting_review(session, submission=submission)
            await session.review(
                Review(submission=submission, verdict="rejection", reviewer="owner", reason="No.")
            )
        async with asyncio.timeout(10):  # a Session that never gives up fails here, not hangs
            outcome = await session.outcome()

    # it stopped after three tries: no fourth agent step and nothing in the ledger
    assert (outcome, len(agent.requests), ledger.entries) == (
        SessionOutcome(phase=Phase.GAVE_UP, receipt=None),
        3,
        [],
    )


async def test_a_second_review_of_the_same_submission_is_refused(client: Client) -> None:
    agent = FakeAgent(script=[NOTE])
    deps = Dependencies(agent=agent, packs=[NotesPack(Ledger())])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-extra-review")
        await until_awaiting_review(session)
        # two Rejections of Submission 1 at once: whichever lands second is refused
        results = await asyncio.gather(
            session.review(REJECTION),
            session.review(
                Review(submission=1, verdict="rejection", reviewer="owner", reason="Too short.")
            ),
            return_exceptions=True,
        )
        await until_awaiting_review(session, submission=2)
        await session.review(Review(submission=2, verdict="approval", reviewer="owner"))
        async with asyncio.timeout(10):
            await session.outcome()

    # one accepted, one refused; one repair, so the extra Review did not reject Submission 2
    assert (sorted(type(result).__name__ for result in results), len(agent.requests)) == (
        ["NoneType", "ReviewRefusedError"],
        2,
    )


async def test_a_review_naming_an_old_submission_is_refused(client: Client) -> None:
    deps = Dependencies(agent=FakeAgent(script=[NOTE]), packs=[NotesPack(Ledger())])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-old-submission")
        await until_awaiting_review(session)
        await session.review(REJECTION)
        await until_awaiting_review(session, submission=2)
        with pytest.raises(ReviewRefusedError, match="Submission 2"):
            await session.review(APPROVAL)  # names Submission 1, but Submission 2 is waiting
        await session.review(Review(submission=2, verdict="approval", reviewer="owner"))


async def test_a_review_while_the_agent_is_working_is_refused_and_the_work_is_not_committed(
    client: Client,
) -> None:
    gate = asyncio.Event()
    gate.set()  # step 1 runs straight through
    agent = FakeAgent(script=[NOTE, SECOND_NOTE], gate=gate)
    ledger = Ledger()
    deps = Dependencies(agent=agent, packs=[NotesPack(ledger)])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-review-while-working")
        await until_awaiting_review(session)
        gate.clear()  # hold the repair step in progress
        await session.review(REJECTION)
        try:
            async with asyncio.timeout(10):
                while len(agent.requests) < 2:  # the agent is repairing Submission 1
                    await asyncio.sleep(0.05)
            with pytest.raises(ReviewRefusedError, match="not waiting"):
                await session.review(APPROVAL)  # names Submission 1, which the agent is repairing
        finally:
            gate.set()  # let the agent finish, even if the Review was wrongly accepted
        await until_awaiting_review(session, submission=2)
        committed_when_the_agent_finished = list(ledger.entries)
        await session.review(Review(submission=2, verdict="approval", reviewer="owner"))
        await session.outcome()

    # nothing was committed when the agent finished; the real Approval then committed once
    assert (committed_when_the_agent_finished, ledger.entries) == ([], [SECOND_NOTE])


async def test_a_rejection_without_a_reason_is_refused(client: Client) -> None:
    deps = Dependencies(agent=FakeAgent(script=[NOTE]), packs=[NotesPack(Ledger())])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-rejection-without-reason")
        await until_awaiting_review(session)
        with pytest.raises(
            ReviewRefusedError, match=r"^a Rejection needs a reason to send back to the agent$"
        ):
            await session.review(Review(submission=1, verdict="rejection", reviewer="owner"))
        await session.review(APPROVAL)


async def test_a_rejection_with_a_blank_reason_is_refused(client: Client) -> None:
    deps = Dependencies(agent=FakeAgent(script=[NOTE]), packs=[NotesPack(Ledger())])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-rejection-blank-reason")
        await until_awaiting_review(session)
        with pytest.raises(ReviewRefusedError, match="reason"):
            await session.review(
                Review(submission=1, verdict="rejection", reviewer="owner", reason=" ")
            )
        status = await session.status()
        await session.review(APPROVAL)

    assert status == SessionStatus(phase=Phase.AWAITING_REVIEW, step=1, submission=1)


async def test_a_refused_review_leaves_the_session_unchanged(client: Client) -> None:
    ledger = Ledger()
    deps = Dependencies(agent=FakeAgent(script=[NOTE]), packs=[NotesPack(ledger)])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-refused-unchanged")
        await until_awaiting_review(session)
        with pytest.raises(ReviewRefusedError):
            await session.review(Review(submission=1, verdict="rejection", reviewer="owner"))
        status = await session.status()
        # still waiting on Submission 1, and its real Review is accepted and commits the work
        await session.review(APPROVAL)
        outcome = await session.outcome()

    assert (status, outcome.phase, ledger.entries) == (
        SessionStatus(phase=Phase.AWAITING_REVIEW, step=1, submission=1),
        Phase.APPROVED,
        [NOTE],
    )


async def test_status_shows_the_session_working_on_step_2_while_the_agent_repairs(
    client: Client,
) -> None:
    agent = FakeAgent(script=[NOTE], hold_at_step=2)
    deps = Dependencies(agent=agent, packs=[NotesPack(Ledger())])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-repairing")
        await until_awaiting_review(session)
        await session.review(REJECTION)
        async with asyncio.timeout(10):
            while len(agent.requests) < 2:  # the agent has started its repair step
                await asyncio.sleep(0.05)
        status = await session.status()
        agent.release.set()
        await until_awaiting_review(session, submission=2)
        await session.review(Review(submission=2, verdict="approval", reviewer="owner"))
        await session.outcome()

    assert status == SessionStatus(phase=Phase.WORKING, step=2, submission=1)


async def test_a_cancel_while_waiting_for_review_ends_the_session_as_cancelled_with_nothing_committed(  # noqa: E501 - named after the ticket line
    client: Client,
) -> None:
    ledger = Ledger()
    deps = Dependencies(agent=FakeAgent(script=[NOTE]), packs=[NotesPack(ledger)])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-cancel-review")
        await until_awaiting_review(session)
        await session.cancel()
        outcome = await session.outcome()

    assert (outcome, ledger.entries) == (SessionOutcome(phase=Phase.CANCELLED, receipt=None), [])


async def test_a_cancel_while_the_agent_is_working_ends_the_session_as_cancelled_after_the_current_step(  # noqa: E501 - named after the ticket line
    client: Client,
) -> None:
    agent = PausingAgent(result=NOTE)
    ledger = Ledger()
    deps = Dependencies(agent=agent, packs=[NotesPack(ledger)])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-cancel-working")
        await agent.started.wait()
        await session.cancel()
        agent.finish.set()
        outcome = await session.outcome()
        status = await session.status()

    # The step in progress finished (step 1), but nothing was submitted or committed.
    assert (outcome, status, ledger.entries) == (
        SessionOutcome(phase=Phase.CANCELLED, receipt=None),
        SessionStatus(phase=Phase.CANCELLED, step=1, submission=0),
        [],
    )


async def test_a_cancel_after_an_approval_is_too_late_and_the_commit_goes_ahead(
    client: Client,
) -> None:
    pack = PausingPack()
    deps = Dependencies(agent=FakeAgent(script=[NOTE]), packs=[pack])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-cancel-committing")
        await until_awaiting_review(session)
        await session.review(APPROVAL)
        await pack.started.wait()
        await session.cancel()
        pack.finish.set()
        outcome = await session.outcome()

    assert outcome == SessionOutcome(phase=Phase.APPROVED, receipt=Receipt(reference="paused#1"))
