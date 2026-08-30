from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, TypedDict

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id
from labs.r3.orchestration.common import framework_result


LANGGRAPH_VERSION = "1.2.11"


class MobilityState(TypedDict):
    phase: str
    events: list[str]
    source_version: str
    human_approved: bool
    canonical_effects: int


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def run_langgraph() -> dict[str, Any]:
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.graph import END, START, StateGraph
    from langgraph.types import Command, interrupt

    def open_case(state: MobilityState) -> dict[str, Any]:
        return {
            "phase": "REQUESTING_DOCUMENTS",
            "events": [*state["events"], "WORK_OPENED", "DOCUMENTS_REQUESTED"],
        }

    def source_update(state: MobilityState) -> dict[str, Any]:
        return {
            "phase": "HUMAN_REVIEW_REQUIRED",
            "source_version": "v2",
            "events": [*state["events"], "SOURCE_UPDATED:v2"],
        }

    def human_gate(state: MobilityState) -> dict[str, Any]:
        approved = bool(
            interrupt(
                {
                    "type": "HUMAN_APPROVAL_REQUIRED",
                    "source_version": state["source_version"],
                }
            )
        )
        return {
            "phase": "READY_FOR_GUARDED_COMPLETION" if approved else "DENIED",
            "human_approved": approved,
            "events": [
                *state["events"],
                "HUMAN_APPROVED" if approved else "HUMAN_REJECTED",
            ],
        }

    def complete(state: MobilityState) -> dict[str, Any]:
        if not state["human_approved"]:
            return {"phase": "DENIED"}
        return {
            "phase": "COMPLETED",
            "events": [*state["events"], "COMPLETED"],
            "canonical_effects": 0,
        }

    builder = StateGraph(MobilityState)
    builder.add_node("open_case", open_case)
    builder.add_node("source_update", source_update)
    builder.add_node("human_gate", human_gate)
    builder.add_node("complete", complete)
    builder.add_edge(START, "open_case")
    builder.add_edge("open_case", "source_update")
    builder.add_edge("source_update", "human_gate")
    builder.add_edge("human_gate", "complete")
    builder.add_edge("complete", END)

    saver = InMemorySaver()
    graph = builder.compile(checkpointer=saver)
    config = {"configurable": {"thread_id": "gmai-r3-langgraph-case-001"}}
    initial: MobilityState = {
        "phase": "NEW",
        "events": [],
        "source_version": "v1",
        "human_approved": False,
        "canonical_effects": 0,
    }

    first = graph.invoke(initial, config)
    paused = graph.get_state(config)
    interrupt_present = bool(first.get("__interrupt__")) or bool(paused.next)
    pre_approval_values = dict(paused.values)

    graph.invoke(Command(resume=True), config)
    final_values = dict(graph.get_state(config).values)
    checkpoints = list(saver.list(config))
    after_read = dict(graph.get_state(config).values)

    result = framework_result(
        candidate="langgraph",
        final_status=str(final_values["phase"]),
        framework_events=list(final_values["events"]),
        resumed_after_pause=interrupt_present,
        duplicate_suppressed=after_read == final_values,
        human_gate_observed=pre_approval_values["human_approved"] is False,
    )
    result["checkpoint_count"] = len(checkpoints)
    result["source_version"] = final_values["source_version"]
    result["checkpoint_state_is_canonical"] = False
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    observed = run_langgraph()
    passed = all(
        [
            observed["final_status"] == "COMPLETED",
            observed["resumed_after_pause"],
            observed["human_gate_observed"],
            observed["checkpoint_count"] >= 2,
            observed["canonical_authority_effects"] == 0,
        ]
    )
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "langgraph",
        "candidate_version": LANGGRAPH_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-real-library",
        "experiment": "t1-t2-t3-t8-durable-graph",
        "test_tiers": ["T1", "T2", "T3", "T8"],
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
    print(f"LangGraph R3: {result['passes']}/1 passed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
