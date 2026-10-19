"""HANDS: the real work a Session asks for, run as Temporal activities.

Everything non-deterministic (model calls, saving to a system of record) happens here,
never in session.py. Temporal stores each activity's result, so after a crash a finished
activity is not run again.

The core does not know which agent or which domain it is talking to: it only sees the
Agent and Pack contracts from ports.py. Tests plug in fakes; production plugs in real ones.
"""

from collections.abc import Sequence

from temporalio import activity
from temporalio.exceptions import ApplicationError

from harness.core.models import (
    AgentRequest,
    CheckReport,
    CheckRequest,
    CommitRequest,
    PackName,
    Receipt,
    Work,
)
from harness.core.ports import Agent, Pack


class SessionActivities:
    def __init__(self, agent: Agent, packs: Sequence[Pack]) -> None:
        self._agent = agent
        self._packs = {pack.name: pack for pack in packs}  # look up a Pack by its name

    # One agent step: hand the request to the Agent and return the work it produced.
    @activity.defn(name="agent_work")
    async def agent_work(self, request: AgentRequest) -> Work:
        self._pack(request.pack)
        return await self._agent.work(request)

    # Run the Pack's Checks on the agent's work; only work with no failures is submitted.
    @activity.defn(name="check_work")
    async def check_work(self, request: CheckRequest) -> CheckReport:
        return CheckReport(failures=await self._pack(request.pack).check(request.work))

    # Commit approved work through the Session's Pack (the only place real state changes).
    @activity.defn(name="commit_work")
    async def commit_work(self, request: CommitRequest) -> Receipt:
        return await self._pack(request.pack).commit(request.work, request.idempotency_key)

    # An unknown Pack can never succeed, so fail the Session instead of retrying.
    def _pack(self, name: PackName) -> Pack:
        if name not in self._packs:
            raise ApplicationError(f"unknown Pack: {name}", non_retryable=True)
        return self._packs[name]
