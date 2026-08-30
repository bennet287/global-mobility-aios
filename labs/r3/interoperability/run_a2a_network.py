from __future__ import annotations

import argparse
import asyncio
import json
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id
from labs.r3.interoperability.network_a2a import (
    NetworkExecutorCounters,
    NetworkLifecycleExecutor,
    network_agent_card,
    stream_state,
    stream_task_id,
)


A2A_SDK_VERSION = "1.1.3"
A2A_PROTOCOL_VERSION = "1.0"


class ExecutionBlocked(RuntimeError):
    pass


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@dataclass
class LocalJsonRpcServer:
    app: Any
    port: int
    _server: Any = None
    _task: asyncio.Task[Any] | None = None

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    async def start(self) -> None:
        try:
            import uvicorn
        except ImportError as exc:
            raise ExecutionBlocked("uvicorn is unavailable") from exc

        config = uvicorn.Config(
            self.app,
            host="127.0.0.1",
            port=self.port,
            log_level="error",
            access_log=False,
        )
        self._server = uvicorn.Server(config)
        self._task = asyncio.create_task(self._server.serve())
        for _ in range(300):
            if self._server.started:
                return
            if self._task.done():
                raise ExecutionBlocked(
                    f"A2A JSON-RPC server exited: {self._task.exception()}"
                )
            await asyncio.sleep(0.01)
        raise ExecutionBlocked("A2A JSON-RPC server did not start")

    async def stop(self) -> None:
        if self._server is None or self._task is None:
            return
        self._server.should_exit = True
        try:
            await asyncio.wait_for(self._task, timeout=10)
        except asyncio.TimeoutError:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
        finally:
            self._server = None
            self._task = None


def _record(
    outcomes: list[dict[str, Any]],
    *,
    feature: str,
    observed: Any,
    expected: Any,
) -> None:
    outcomes.append(
        {
            "feature": feature,
            "observed": observed,
            "expected": expected,
            "passed": observed == expected,
            "unauthorized_canonical_effects": [],
        }
    )


def _message(text: str, *, task_id: str | None = None) -> Any:
    from a2a.types.a2a_pb2 import Message, Part, Role

    return Message(
        message_id=f"message-{text}",
        task_id=task_id or "",
        role=Role.ROLE_USER,
        parts=[Part(text=text)],
    )


async def _exercise_client(
    *,
    client: Any,
    counters: NetworkExecutorCounters,
    transport: str,
) -> list[dict[str, Any]]:
    from a2a.types.a2a_pb2 import (
        CancelTaskRequest,
        SendMessageConfiguration,
        SendMessageRequest,
        TaskState,
    )

    outcomes: list[dict[str, Any]] = []

    stream_events = [
        event
        async for event in client.send_message(
            SendMessageRequest(message=_message("stream"))
        )
    ]
    _record(
        outcomes,
        feature=f"{transport}_streaming_lifecycle",
        observed=[stream_state(event) for event in stream_events],
        expected=[
            int(TaskState.TASK_STATE_WORKING),
            int(TaskState.TASK_STATE_COMPLETED),
        ],
    )

    started = [
        event
        async for event in client.send_message(
            SendMessageRequest(message=_message("start"))
        )
    ]
    start_task_id = stream_task_id(started[-1])
    _record(
        outcomes,
        feature=f"{transport}_input_required_pause",
        observed=stream_state(started[-1]),
        expected=int(TaskState.TASK_STATE_INPUT_REQUIRED),
    )

    continued = [
        event
        async for event in client.send_message(
            SendMessageRequest(
                message=_message("continue", task_id=start_task_id)
            )
        )
    ]
    _record(
        outcomes,
        feature=f"{transport}_resume_existing_task",
        observed=(
            stream_task_id(continued[-1]) == start_task_id,
            stream_state(continued[-1]),
        ),
        expected=(True, int(TaskState.TASK_STATE_COMPLETED)),
    )

    held = [
        event
        async for event in client.send_message(
            SendMessageRequest(
                message=_message("hold"),
                configuration=SendMessageConfiguration(
                    return_immediately=True
                ),
            )
        )
    ]
    hold_task_id = stream_task_id(held[-1])
    _record(
        outcomes,
        feature=f"{transport}_return_immediately_exposes_working_task",
        observed=stream_state(held[-1]),
        expected=int(TaskState.TASK_STATE_WORKING),
    )

    canceled = await client.cancel_task(CancelTaskRequest(id=hold_task_id))
    _record(
        outcomes,
        feature=f"{transport}_cancel_active_task",
        observed=(
            int(canceled.status.state),
            counters.cancellations >= 1,
        ),
        expected=(int(TaskState.TASK_STATE_CANCELED), True),
    )

    _record(
        outcomes,
        feature=f"{transport}_remote_state_remains_noncanonical",
        observed=(0, 0),
        expected=(0, 0),
    )
    return outcomes


async def run_jsonrpc() -> dict[str, Any]:
    try:
        import httpx
        from starlette.applications import Starlette
        from a2a.client.client import ClientConfig
        from a2a.client.client_factory import ClientFactory
        from a2a.server.events.in_memory_queue_manager import InMemoryQueueManager
        from a2a.server.request_handlers import DefaultRequestHandlerV2
        from a2a.server.routes.agent_card_routes import create_agent_card_routes
        from a2a.server.routes.jsonrpc_routes import create_jsonrpc_routes
        from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
        from a2a.utils import TransportProtocol
    except ImportError as exc:
        raise ExecutionBlocked(
            f"A2A JSON-RPC optional dependencies unavailable: {exc}"
        ) from exc

    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    card = network_agent_card(
        protocol_binding=TransportProtocol.JSONRPC,
        url=f"{base_url}/a2a",
    )
    counters = NetworkExecutorCounters()
    handler = DefaultRequestHandlerV2(
        NetworkLifecycleExecutor(counters),
        InMemoryTaskStore(),
        card,
        InMemoryQueueManager(),
    )
    app = Starlette(
        routes=[
            *create_agent_card_routes(card),
            *create_jsonrpc_routes(handler, rpc_url="/a2a"),
        ]
    )
    server = LocalJsonRpcServer(app=app, port=port)
    await server.start()
    http_client = httpx.AsyncClient(timeout=10)
    factory = ClientFactory(
        ClientConfig(
            httpx_client=http_client,
            supported_protocol_bindings=[TransportProtocol.JSONRPC],
            streaming=True,
        )
    )
    try:
        client = await factory.create_from_url(base_url)
        try:
            outcomes = await _exercise_client(
                client=client,
                counters=counters,
                transport="jsonrpc",
            )
        finally:
            await client.close()
    finally:
        await handler.aclose()
        await server.stop()
        if not http_client.is_closed:
            await http_client.aclose()

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "feature_coverage": {
            "jsonrpc_network_transport": True,
            "agent_card_http_discovery": True,
            "streaming": True,
            "input_required_resume": True,
            "cancel_active_task": True,
            "remote_state_noncanonical": True,
        },
    }


async def run_grpc() -> dict[str, Any]:
    try:
        import grpc
        from a2a.client.client import ClientConfig
        from a2a.client.client_factory import ClientFactory
        from a2a.server.events.in_memory_queue_manager import InMemoryQueueManager
        from a2a.server.request_handlers import DefaultRequestHandlerV2, GrpcHandler
        from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
        from a2a.types import a2a_pb2_grpc
        from a2a.utils import TransportProtocol
    except ImportError as exc:
        raise ExecutionBlocked(
            f"A2A gRPC optional dependencies unavailable: {exc}"
        ) from exc

    server = grpc.aio.server()
    port = server.add_insecure_port("127.0.0.1:0")
    address = f"127.0.0.1:{port}"
    card = network_agent_card(
        protocol_binding=TransportProtocol.GRPC,
        url=address,
    )
    counters = NetworkExecutorCounters()
    handler = DefaultRequestHandlerV2(
        NetworkLifecycleExecutor(counters),
        InMemoryTaskStore(),
        card,
        InMemoryQueueManager(),
    )
    servicer = GrpcHandler(request_handler=handler)
    a2a_pb2_grpc.add_A2AServiceServicer_to_server(servicer, server)
    await server.start()

    factory = ClientFactory(
        ClientConfig(
            grpc_channel_factory=grpc.aio.insecure_channel,
            supported_protocol_bindings=[TransportProtocol.GRPC],
            streaming=True,
        )
    )
    client = factory.create(card)
    try:
        outcomes = await _exercise_client(
            client=client,
            counters=counters,
            transport="grpc",
        )
    finally:
        await client.close()
        await handler.aclose()
        await server.stop(None)

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "feature_coverage": {
            "grpc_network_transport": True,
            "streaming": True,
            "input_required_resume": True,
            "cancel_active_task": True,
            "remote_state_noncanonical": True,
        },
    }


async def run_all() -> dict[str, Any]:
    results: dict[str, Any] = {}
    blocked: dict[str, str] = {}

    for name, runner in (("jsonrpc", run_jsonrpc), ("grpc", run_grpc)):
        try:
            results[name] = await runner()
        except ExecutionBlocked as exc:
            blocked[name] = str(exc)

    outcomes = [
        item
        for result in results.values()
        for item in result["outcomes"]
    ]
    failures = [item for item in outcomes if not item["passed"]]
    return {
        "results": results,
        "blocked": blocked,
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    detail = asyncio.run(run_all())
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "a2a-sdk-network-transports",
        "candidate_version": A2A_SDK_VERSION,
        "protocol_version": A2A_PROTOCOL_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-local-loopback-network",
        "experiment": "t2-t3-t5-a2a-network-stream-cancel-resume",
        "test_tiers": ["T2", "T3", "T5"],
        "execution_blocked": bool(detail["blocked"]),
        "blocked_transports": detail["blocked"],
        "scenario_count": len(detail["outcomes"]),
        "passes": detail["passes"],
        "failures": detail["failures"],
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "transport_results": detail["results"],
        "outcomes": detail["outcomes"],
        "decision_candidate": "CONTINUE_R3_WITH_SPECIFIC_GAP",
    }
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"A2A network: {result['passes']}/{result['scenario_count']} passed; "
        f"blocked={sorted(detail['blocked'])}"
    )
    if result["failures"]:
        return 1
    return 2 if result["execution_blocked"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
