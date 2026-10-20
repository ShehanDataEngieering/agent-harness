"""Payload seam: everything Temporal stores must come back exactly as it went in.

Temporal saves workflow and activity data as JSON in its history and validates it again
on the way back. Strict Pydantic could reject its own data there, so we round-trip one
example of every payload model.
"""

import pytest
from temporalio.contrib.pydantic import pydantic_data_converter

from harness.core import models
from harness.core.models import (
    AgentRequest,
    CommitRequest,
    IdempotencyKey,
    Payload,
    Phase,
    Receipt,
    SessionInput,
    SessionOutcome,
    SessionStatus,
    SteerRequest,
)
from tests.support import APPROVAL, NOTE, NOTES, REJECTION

KEY = IdempotencyKey("session-1:1")

# One example per payload model. A new model without an example fails the test below.
EXAMPLES: list[Payload] = [
    SessionInput(pack=NOTES, task="Write a note"),
    NOTE,
    AgentRequest(
        pack=NOTES,
        task="Write a note",
        step=1,
        rejection_reason=None,
        guidance=(),
        idempotency_key=KEY,
    ),
    AgentRequest(
        pack=NOTES,
        task="Write a note",
        step=2,
        rejection_reason="Too vague.",
        guidance=("Use metric units.",),
        idempotency_key=KEY,
    ),
    Receipt(reference="ledger#1"),
    CommitRequest(pack=NOTES, work=NOTE, idempotency_key=KEY),
    APPROVAL,
    REJECTION,
    SteerRequest(guidance="Use metric units."),
    SessionStatus(phase=Phase.AWAITING_REVIEW, step=1, submission=1),
    SessionOutcome(phase=Phase.APPROVED, receipt=Receipt(reference="ledger#1")),
    SessionOutcome(phase=Phase.GAVE_UP, receipt=None),
    SessionOutcome(phase=Phase.CANCELLED, receipt=None),
]


def test_every_payload_model_has_an_example() -> None:
    defined = {
        value
        for value in vars(models).values()
        if isinstance(value, type) and issubclass(value, Payload) and value is not Payload
    }
    assert {type(example) for example in EXAMPLES} == defined


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda example: type(example).__name__)
async def test_every_workflow_and_activity_model_round_trips_through_the_data_converter_unchanged(
    example: Payload,
) -> None:
    converter = pydantic_data_converter.payload_converter
    [stored] = converter.to_payloads([example])
    [restored] = converter.from_payloads([stored], [type(example)])

    assert restored == example
