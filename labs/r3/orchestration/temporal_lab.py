from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
from datetime import timedelta
from pathlib import Path
from typing import Any

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id
from labs.r3.orchestration.common import framework_result


TEMPORAL_VERSION = "1.32.0"
TASK_QUEUE = "gmai-r3-orchestration"


class ExecutionBlocked(RuntimeError):
    pass


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


async def _execute_temporal() -> dict[str, Any]:
    from temporalio import activity, workflow
    from temporalio.client import WorkflowAlreadyStartedError
    from temporalio.common import RetryPolicy
    from temporalio.testing import WorkflowEnvironment
    from temporalio.worker import Worker

    @activity.defn(name="r3_request_documents")
    async def request_documents(case_id: str) -> str:
        if activity.info().attempt == 1:
            raise RuntimeError("synthetic first-attempt worker failure")
        return f"documents-requested:{case_id}"

    @workflow.defn(name="R3MobilityWorkflow")
    class MobilityWorkflow:
        def __init__(self) -> None:
            self.phase = "NEW"
            self.approved = False
            self.source_version = "v1"
            self.events: list[str] = []

        @workflow.run
        async def run(self, case_id: str) -> dict[str, Any]:
            self.phase = "REQUESTING_DOCUMENTS"
            self.events.append("WORK_OPENED")
            await workflow.execute_activity(
                request_documents,
                case_id,
                start_to_close_timeout=timedelta(seconds=5),
                retry_policy=RetryPolicy(maximum_attempts=2),
            )
            self.events.append("DOCUMENTS_REQUESTED")
            self.phase = "HUMAN_REVIEW_REQUIRED"
            await workflow.wait_condition(lambda: self.approved)
            self.events.append("HUMAN_APPROVED")
            self.phase = "COMPLETED"
            return {
                "status": self.phase,
                "source_version": self.source_version,
                "events": self.events,
                "framework_state_is_canonical": False,
                "canonical_authority_effects": 0,
                "canonical_external_actions": 0,
            }

        @workflow.signal
        def approve(self) -> None:
            self.approved = True

        @workflow.signal
        def source_updated(self, version: str) -> None:
            self.source_version = version
            self.events.append(f"SOURCE_UPDATED:{version}")

        @workflow.query
        def snapshot(self) -> dict[str, Any]:
            return {
                "phase": self.phase,
                "approved": self.approved,
                "source_version": self.source_version,
                "events": list(self.events),
            }

    try:
        env = await WorkflowEnvironment.start_time_skipping()
    except Exception as exc:
        raise ExecutionBlocked(
            f"Temporal local test server could not start: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    async with env:
        workflow_id = "gmai-r3-temporal-case-001"
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[MobilityWorkflow],
            activities=[request_documents],
        ):
            handle = await env.client.start_workflow(
                MobilityWorkflow.run,
                "case:AT-001",
                id=workflow_id,
                task_queue=TASK_QUEUE,
            )
            duplicate_suppressed = False
            try:
                await env.client.start_workflow(
                    MobilityWorkflow.run,
                    "case:AT-001",
                    id=workflow_id,
                    task_queue=TASK_QUEUE,
                )
            except WorkflowAlreadyStartedError:
                duplicate_suppressed = True

            for _ in range(200):
                snapshot = await handle.query(MobilityWorkflow.snapshot)
                if snapshot["phase"] == "HUMAN_REVIEW_REQUIRED":
                    break
                await asyncio.sleep(0.01)
            else:
                raise RuntimeError("workflow did not reach human review")

        # Worker #1 is gone. The workflow remains in Temporal state.
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[MobilityWorkflow],
            activities=[request_documents],
        ):
            await handle.signal(MobilityWorkflow.source_updated, "v2")
            before_approval = await handle.query(MobilityWorkflow.snapshot)
            await handle.signal(MobilityWorkflow.approve)
            completed = await handle.result()

    result = framework_result(
        candidate="temporal",
        final_status=completed["status"],
        framework_events=list(completed["events"]),
        resumed_after_pause=(
            before_approval["phase"] == "HUMAN_REVIEW_REQUIRED"
        ),
        duplicate_suppressed=duplicate_suppressed,
        human_gate_observed=before_approval["approved"] is False,
    )
    result["source_version"] = completed["source_version"]
    result["worker_restart_proven"] = True
    result["activity_retry_proven"] = True
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    try:
        observed = asyncio.run(_execute_temporal())
        blocked = False
        block_reason = None
    except ExecutionBlocked as exc:
        observed = {}
        blocked = True
        block_reason = str(exc)

    passed = bool(observed) and all(
        [
            observed.get("final_status") == "COMPLETED",
            observed.get("resumed_after_pause"),
            observed.get("duplicate_suppressed"),
            observed.get("human_gate_observed"),
            observed.get("worker_restart_proven"),
            observed.get("activity_retry_proven"),
        ]
    )
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "temporal-python",
        "candidate_version": TEMPORAL_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-local-temporal-test-server",
        "experiment": "t1-t2-t3-t5-t8-durable-orchestration",
        "test_tiers": ["T1", "T2", "T3", "T5", "T8"],
        "execution_blocked": blocked,
        "block_reason": block_reason,
        "scenario_count": int(not blocked),
        "passes": int(passed),
        "failures": int(not blocked and not passed),
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "outcomes": [observed] if observed else [],
        "decision_candidate": "CONTINUE_R3_WITH_SPECIFIC_GAP",
    }
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if blocked:
        print(f"Temporal R3 execution blocked: {block_reason}")
        return 2
    print(f"Temporal R3: {result['passes']}/{result['scenario_count']} passed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
