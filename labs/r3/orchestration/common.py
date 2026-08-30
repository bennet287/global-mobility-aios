from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CanonicalMobilityRecord:
    status: str = "OPEN"
    authority_state: str = "RETAINED"
    human_approval: bool = False
    external_actions: int = 0
    events: list[str] = field(default_factory=list)
    processed_commands: set[str] = field(default_factory=set)


class NativeDurableReference:
    """AIOS-owned semantic reference for R3 differential experiments only."""

    def __init__(self) -> None:
        self.record = CanonicalMobilityRecord()

    def apply(self, command_id: str, event: str) -> bool:
        if command_id in self.record.processed_commands:
            return False
        if event == "COMPLETE" and not self.record.human_approval:
            raise ValueError("human approval required")

        self.record.processed_commands.add(command_id)
        self.record.events.append(event)
        if event == "DOCUMENTS_REQUESTED":
            self.record.status = "WAITING_DOCUMENTS"
        elif event == "SOURCE_UPDATED":
            self.record.status = "HUMAN_REVIEW_REQUIRED"
        elif event == "HUMAN_APPROVED":
            self.record.human_approval = True
            self.record.status = "READY_FOR_GUARDED_COMPLETION"
        elif event == "COMPLETE":
            self.record.status = "COMPLETED"
        return True

    def snapshot(self) -> dict[str, Any]:
        return {
            "status": self.record.status,
            "authority_state": self.record.authority_state,
            "human_approval": self.record.human_approval,
            "external_actions": self.record.external_actions,
            "events": list(self.record.events),
            "processed_commands": sorted(self.record.processed_commands),
        }


def framework_result(
    *,
    candidate: str,
    final_status: str,
    framework_events: list[str],
    resumed_after_pause: bool,
    duplicate_suppressed: bool,
    human_gate_observed: bool,
) -> dict[str, Any]:
    return {
        "candidate": candidate,
        "final_status": final_status,
        "framework_events": framework_events,
        "resumed_after_pause": resumed_after_pause,
        "duplicate_suppressed": duplicate_suppressed,
        "human_gate_observed": human_gate_observed,
        "framework_state_is_canonical": False,
        "canonical_authority_effects": 0,
        "canonical_external_actions": 0,
    }
