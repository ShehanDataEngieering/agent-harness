"""Pretend versions of the outside world, used only in tests.

We fake only what we don't own: the AI model and the system of record a Pack writes to.
Our own code (workflow, activities) always runs for real in tests.
"""

import asyncio
from dataclasses import dataclass, field
from typing import override

from harness.core.models import AgentRequest, IdempotencyKey, PackName, Receipt, Work
from tests.support import NOTES


@dataclass
class FakeAgent:
    """Stands in for the Agent model: returns scripted work, one item per step.

    With `hold_at_step`, that step waits for `release` to be set, so a test can look at
    the Session while the agent is still working.
    """

    script: list[Work]
    requests: list[AgentRequest] = field(default_factory=list[AgentRequest])
    hold_at_step: int | None = None  # this step stays working until release is set
    release: asyncio.Event = field(default_factory=asyncio.Event)
    gate: asyncio.Event | None = None  # if set, each step stays working until the gate opens

    async def work(self, request: AgentRequest) -> Work:
        self.requests.append(request)
        if request.step == self.hold_at_step:
            await self.release.wait()
        if self.gate is not None:
            await self.gate.wait()
        return self.script[min(len(self.requests), len(self.script)) - 1]


@dataclass
class PausingAgent:
    """An Agent model that stays mid-step until the test lets it finish."""

    result: Work
    started: asyncio.Event = field(default_factory=asyncio.Event)
    finish: asyncio.Event = field(default_factory=asyncio.Event)

    async def work(self, request: AgentRequest) -> Work:
        self.started.set()
        await self.finish.wait()
        return self.result


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

    async def check(self, work: Work) -> tuple[str, ...]:
        return ()

    async def commit(self, work: Work, key: IdempotencyKey) -> Receipt:
        self.ledger.entries.append(work)
        self.ledger.keys.append(key)
        return Receipt(reference=f"ledger#{len(self.ledger.entries)}")


@dataclass
class CheckedNotesPack(NotesPack):
    """A NotesPack whose Checks fail notes with the listed content: same note, same failures."""

    failures: dict[str, tuple[str, ...]] = field(default_factory=dict[str, tuple[str, ...]])

    @override
    async def check(self, work: Work) -> tuple[str, ...]:
        return self.failures.get(work.content, ())


@dataclass
class PausingPack:
    """A Pack whose commit stays in progress until the test lets it finish."""

    name: PackName = NOTES
    started: asyncio.Event = field(default_factory=asyncio.Event)
    finish: asyncio.Event = field(default_factory=asyncio.Event)

    async def check(self, work: Work) -> tuple[str, ...]:
        return ()

    async def commit(self, work: Work, key: IdempotencyKey) -> Receipt:
        self.started.set()
        await self.finish.wait()
        return Receipt(reference="paused#1")
