"""Pretend versions of the outside world, used only in tests.

We fake only what we don't own: the AI model and the system of record a Pack writes to.
Our own code (workflow, activities) always runs for real in tests.
"""

from dataclasses import dataclass, field

from harness.core.models import AgentRequest, IdempotencyKey, PackName, Receipt, Work
from tests.support import NOTES


@dataclass
class FakeAgent:
    """Stands in for the Agent model: returns scripted work, one item per step."""

    script: list[Work]
    requests: list[AgentRequest] = field(default_factory=list[AgentRequest])

    async def work(self, request: AgentRequest) -> Work:
        self.requests.append(request)
        return self.script[min(len(self.requests), len(self.script)) - 1]


@dataclass
class Ledger:
    """Stands in for the system of record a Pack commits to."""

    entries: list[Work] = field(default_factory=list[Work])
    keys: list[IdempotencyKey] = field(default_factory=list[IdempotencyKey])


@dataclass
class NotesPack:
    """A minimal Pack for core tests: its work is a note, committing appends it to a Ledger."""

    ledger: Ledger
    name: PackName = NOTES

    async def commit(self, work: Work, key: IdempotencyKey) -> Receipt:
        self.ledger.entries.append(work)
        self.ledger.keys.append(key)
        return Receipt(reference=f"ledger#{len(self.ledger.entries)}")
