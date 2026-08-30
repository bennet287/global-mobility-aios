from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from a2a.helpers.proto_helpers import get_message_text, new_task_from_user_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types.a2a_pb2 import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    Part,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import TransportProtocol


@dataclass
class NetworkExecutorCounters:
    executions: int = 0
    cancellations: int = 0


class NetworkLifecycleExecutor(AgentExecutor):
    """Synthetic A2A lifecycle with stream, resume and cancellable hold."""

    def __init__(self, counters: NetworkExecutorCounters) -> None:
        self.counters = counters

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        self.counters.executions += 1
        text = get_message_text(context.message) if context.message else ""

        if text == "start":
            if context.message is None:
                raise ValueError("start requires a message")
            task = new_task_from_user_message(context.message)
            task.status.state = TaskState.TASK_STATE_INPUT_REQUIRED
            await event_queue.enqueue_event(task)
            return

        if text == "continue":
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=context.task_id,
                    context_id=context.context_id,
                    status=TaskStatus(state=TaskState.TASK_STATE_COMPLETED),
                )
            )
            return

        if text == "hold":
            if context.message is None:
                raise ValueError("hold requires a message")
            task = new_task_from_user_message(context.message)
            task.status.state = TaskState.TASK_STATE_WORKING
            await event_queue.enqueue_event(task)
            await asyncio.Event().wait()
            return

        if context.message is None:
            raise ValueError("stream requires a message")
        task = new_task_from_user_message(context.message)
        task.status.state = TaskState.TASK_STATE_WORKING
        await event_queue.enqueue_event(task)
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_COMPLETED),
            )
        )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        self.counters.cancellations += 1
        if context.current_task is None:
            raise ValueError("cancel requires current task")
        updater = TaskUpdater(
            event_queue=event_queue,
            task_id=context.current_task.id,
            context_id=context.current_task.context_id,
        )
        await updater.update_status(
            state=TaskState.TASK_STATE_CANCELED,
        )


def network_agent_card(
    *,
    protocol_binding: str,
    url: str,
) -> AgentCard:
    return AgentCard(
        name="gmai-r3-network-agent",
        description="Synthetic non-authoritative network A2A agent.",
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        supported_interfaces=[
            AgentInterface(
                protocol_binding=protocol_binding,
                url=url,
                protocol_version="1.0",
            )
        ],
    )


def stream_state(event: Any) -> int:
    if event.HasField("task"):
        return int(event.task.status.state)
    if event.HasField("status_update"):
        return int(event.status_update.status.state)
    raise AssertionError("stream event has neither task nor status_update")


def stream_task_id(event: Any) -> str:
    if event.HasField("task"):
        return str(event.task.id)
    if event.HasField("status_update"):
        return str(event.status_update.task_id)
    raise AssertionError("stream event has no task id")
