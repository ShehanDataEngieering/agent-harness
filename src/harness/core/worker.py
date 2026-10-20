"""WIRING: plugs the Session workflow and its activities into a running Temporal worker.

A worker is the process that actually executes Sessions. Temporal hands it work through a
task queue (a named inbox). Like `app.listen()`, but for workflows.
"""

import uuid
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass

from temporalio.client import Client
from temporalio.worker import Worker, WorkflowRunner
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner

from harness.core.activities import SessionActivities
from harness.core.ports import Agent, Pack
from harness.core.session import SessionWorkflow


@dataclass(frozen=True)
class Dependencies:
    """The outside-world pieces a worker needs (see ports.py)."""

    agent: Agent
    packs: Sequence[Pack]


@asynccontextmanager
async def session_worker(
    client: Client,
    deps: Dependencies,
    workflow_runner: WorkflowRunner | None = None,
) -> AsyncGenerator[str]:
    """Run a worker for the duration of an `async with` block and yield its task queue."""
    queue = f"harness-{uuid.uuid4()}"  # a fresh queue keeps tests isolated
    activities = SessionActivities(deps.agent, deps.packs)
    async with Worker(
        client,
        task_queue=queue,
        workflows=[SessionWorkflow],
        activities=[activities.agent_work, activities.check_work, activities.commit_work],
        # The sandbox catches non-deterministic workflow code; keep it on by default.
        workflow_runner=workflow_runner or SandboxedWorkflowRunner(),
    ):
        yield queue
