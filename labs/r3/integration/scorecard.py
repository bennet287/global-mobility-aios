from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from labs.r3.integration.grand_trial import REQUIRED_LANES, _classify_lane, _load


def build_scorecard(paths: list[Path]) -> dict[str, Any]:
    lanes: dict[str, dict[str, Any]] = {
        lane: {
            "status": "EVIDENCE_MISSING",
            "artifacts": [],
            "passes": 0,
            "failures": 0,
            "blocked": 0,
            "unauthorized_canonical_effects": 0,
        }
        for lane in sorted(REQUIRED_LANES)
    }

    for path in paths:
        result = _load(path)
        lane = _classify_lane(result)
        if lane is None:
            continue
        entry = lanes[lane]
        entry["artifacts"].append(str(path))
        entry["passes"] += int(result.get("passes", 0))
        entry["failures"] += int(result.get("failures", 0))
        entry["blocked"] += int(bool(result.get("execution_blocked")))
        entry["unauthorized_canonical_effects"] += int(
            result.get("unauthorized_canonical_effects", 0)
        )

    for entry in lanes.values():
        if not entry["artifacts"]:
            continue
        if entry["blocked"]:
            entry["status"] = "EXECUTION_BLOCKED"
        elif entry["failures"]:
            entry["status"] = "R3_EVIDENCE_FAILED"
        elif entry["unauthorized_canonical_effects"]:
            entry["status"] = "R3_SOVEREIGNTY_FAILURE"
        elif entry["passes"]:
            entry["status"] = "R3_EVIDENCE_PASS"
        else:
            entry["status"] = "IMPLEMENTED_EXECUTION_PENDING"

    eligible = all(entry["status"] == "R3_EVIDENCE_PASS" for entry in lanes.values())
    return {
        "schema": "gmai-technology-radar-v1.3.6-r3-scorecard.v1",
        "lanes": lanes,
        "r4_decision_eligible": eligible,
        "production_adoption_authorized": False,
        "professional_austria_review_satisfied": False,
        "notes": [
            "R3 evidence does not authorize production adoption.",
            "Technology selection never changes Human Owner authority.",
            "Austria professional review is a separate unresolved gate unless independently satisfied.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("results", nargs="+", type=Path)
    args = parser.parse_args()

    scorecard = build_scorecard(args.results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(scorecard, indent=2, sort_keys=True) + "\n")
    print(
        "R4 decision eligible"
        if scorecard["r4_decision_eligible"]
        else "R4 decision not yet eligible"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
