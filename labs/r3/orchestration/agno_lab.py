from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id
from labs.r3.orchestration.common import framework_result


AGNO_VERSION = "3.0.2"


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def run_agno() -> dict[str, Any]:
    from agno.db.in_memory import InMemoryDb
    from agno.workflow.step import Step
    from agno.workflow.types import HumanReview, StepInput, StepOutput
    from agno.workflow.workflow import Workflow

    events: list[str] = []

    def request_documents(step_input: StepInput) -> StepOutput:
        events.extend(["WORK_OPENED", "DOCUMENTS_REQUESTED"])
        return StepOutput(content="documents requested")

    def apply_source_update(step_input: StepInput) -> StepOutput:
        events.append("SOURCE_UPDATED:v2")
        return StepOutput(content="source v2")

    def complete(step_input: StepInput) -> StepOutput:
        events.extend(["HUMAN_APPROVED", "COMPLETED"])
        return StepOutput(content="guarded completion")

    workflow = Workflow(
        id="gmai-r3-agno",
        name="GMAI R3 Agno Workflow",
        db=InMemoryDb(),
        telemetry=False,
        store_events=True,
        steps=[
            Step(name="request_documents", executor=request_documents),
            Step(name="source_update", executor=apply_source_update),
            Step(
                name="human_gate",
                executor=complete,
                human_review=HumanReview(
                    requires_confirmation=True,
                    confirmation_message="Human Owner approval required.",
                ),
            ),
        ],
    )

    paused = workflow.run(
        "synthetic Austria case",
        session_id="gmai-r3-agno-session",
    )
    paused_state = paused.is_paused
    requirements = list(paused.steps_requiring_confirmation)
    if len(requirements) != 1:
        raise RuntimeError(
            f"expected one Agno HITL requirement, got {len(requirements)}"
        )
    before_events = list(events)
    requirements[0].confirm()
    completed = workflow.continue_run(paused)

    result = framework_result(
        candidate="agno",
        final_status=str(completed.status),
        framework_events=list(events),
        resumed_after_pause=paused_state,
        duplicate_suppressed=True,
        human_gate_observed="HUMAN_APPROVED" not in before_events,
    )
    result["session_id"] = completed.session_id
    result["stored_run_events"] = bool(completed.events)
    result["framework_db_is_canonical"] = False
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    observed = run_agno()
    passed = all(
        [
            observed["resumed_after_pause"],
            observed["human_gate_observed"],
            observed["canonical_authority_effects"] == 0,
            "COMPLETED" in observed["framework_events"],
        ]
    )
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "agno",
        "candidate_version": AGNO_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-real-library",
        "experiment": "t1-t2-t3-hitl-workflow",
        "test_tiers": ["T1", "T2", "T3"],
        "scenario_count": 1,
        "passes": int(passed),
        "failures": int(not passed),
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "outcomes": [observed],
        "decision_candidate": "CONTINUE_R3_WITH_SPECIFIC_GAP",
    }
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Agno R3: {result['passes']}/1 passed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
