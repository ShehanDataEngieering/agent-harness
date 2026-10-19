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

from harness.core.models import PackName, Phase, Review, SessionOutcome, SessionStatus
from harness.core.worker import Dependencies, session_worker
from tests.fakes import CheckedNotesPack, FakeAgent, Ledger, NotesPack, PausingAgent, PausingPack
from tests.support import (
    APPROVAL,
    BLANK_NOTE,
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


async def test_an_extra_review_does_not_answer_the_next_submission(client: Client) -> None:
    agent = FakeAgent(script=[NOTE])
    deps = Dependencies(agent=agent, packs=[NotesPack(Ledger())])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-extra-review")
        await until_awaiting_review(session)
        # two Rejections of Submission 1 at once: the second lands while the agent repairs
        await asyncio.gather(
            session.review(REJECTION),
            session.review(
                Review(submission=1, verdict="rejection", reviewer="owner", reason="Too short.")
            ),
        )
        await until_awaiting_review(session, submission=2)
        await session.review(Review(submission=2, verdict="approval", reviewer="owner"))
        async with asyncio.timeout(10):
            await session.outcome()

    # one Rejection, one repair: the extra Review did not also reject Submission 2
    assert len(agent.requests) == 2


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


async def test_a_late_review_for_an_earlier_submission_does_not_decide_the_current_one(
    client: Client,
) -> None:
    agent = FakeAgent(script=[NOTE, SECOND_NOTE])
    ledger = Ledger()
    deps = Dependencies(agent=agent, packs=[NotesPack(ledger)])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-late-review")
        await until_awaiting_review(session)
        await session.review(REJECTION)
        await until_awaiting_review(session, submission=2)
        # a duplicate Rejection of Submission 1 arrives while Submission 2 waits
        await session.review(REJECTION)
        status = await session.status()
        runs = len(agent.requests)
        await session.review(Review(submission=2, verdict="approval", reviewer="owner"))
        async with asyncio.timeout(10):
            await session.outcome()

    # the late Review was ignored: still waiting on 2 after two agent runs, then 2 is committed
    assert (status, runs, ledger.entries) == (
        SessionStatus(phase=Phase.AWAITING_REVIEW, step=2, submission=2),
        2,
        [SECOND_NOTE],
    )


async def test_work_that_fails_a_check_is_never_submitted(client: Client) -> None:
    ledger = Ledger()
    pack = CheckedNotesPack(ledger, failures={"": ("The note is empty.",)})
    deps = Dependencies(agent=FakeAgent(script=[BLANK_NOTE, NOTE]), packs=[pack])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-check-failed")
        await until_awaiting_review(session)
        status = await session.status()
        await session.review(APPROVAL)
        await session.outcome()

    # Submission 1 is the second agent step: the empty note never reached the human
    assert (status, ledger.entries) == (
        SessionStatus(phase=Phase.AWAITING_REVIEW, step=2, submission=1),
        [NOTE],
    )


async def test_the_check_failures_are_given_to_the_agent_on_its_next_step(client: Client) -> None:
    agent = FakeAgent(script=[BLANK_NOTE, NOTE])
    pack = CheckedNotesPack(Ledger(), failures={"": ("The note is empty.",)})
    deps = Dependencies(agent=agent, packs=[pack])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-check-failures-returned")
        await until_awaiting_review(session)
        await session.review(APPROVAL)
        await session.outcome()

    assert [request.check_failures for request in agent.requests] == [
        (),
        ("The note is empty.",),
    ]


async def test_a_session_that_reaches_the_step_limit_ends_as_given_up(client: Client) -> None:
    agent = FakeAgent(script=[BLANK_NOTE])  # its note fails the Check on every step
    ledger = Ledger()
    pack = CheckedNotesPack(ledger, failures={"": ("The note is empty.",)})
    deps = Dependencies(agent=agent, packs=[pack])
    async with session_worker(client, deps, workflow_runner=SANDBOX) as task_queue:
        session = await start(client, task_queue, "session-step-limit", max_steps=3)
        async with asyncio.timeout(10):  # a Session that repairs forever fails here, not hangs
            outcome = await session.outcome()

    # three agent steps, then it gave up: nothing submitted, nothing committed
    assert (outcome, len(agent.requests), ledger.entries) == (
        SessionOutcome(phase=Phase.GAVE_UP, receipt=None),
        3,
        [],
    )
