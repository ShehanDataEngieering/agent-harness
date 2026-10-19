"""CONTRACTS: what the core needs from the outside world (like TypeScript interfaces).

Anything that matches these shapes can be plugged in; nothing has to inherit from them.
"""

from typing import Protocol

from harness.core.models import AgentRequest, IdempotencyKey, PackName, Receipt, Work


class Agent(Protocol):
    """Whatever does the work: a fake in tests, the Agent model in production."""

    async def work(self, request: AgentRequest) -> Work: ...


class Pack(Protocol):
    """A pluggable domain. The core never knows which one it is talking to."""

    @property
    def name(self) -> PackName: ...

    # Run the Pack's Checks on the work and return what failed, empty if all passed.
    # Checks are deterministic: the same work always gets the same failures.
    async def check(self, work: Work) -> tuple[str, ...]: ...

    # Make approved work real in the Pack's system of record. The key is the same on a
    # retry, so the Pack can make sure the commit lands only once.
    async def commit(self, work: Work, key: IdempotencyKey) -> Receipt: ...
