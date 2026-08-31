from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from labs.r3.integration.grand_trial import (
    REQUIRED_LANES,
    _classify_lane,
    _load,
    evaluate_evidence,
)


def build_scorecard(paths: list[Path]) -> dict[str, Any]:
    evidence = evaluate_evidence(paths)
    lanes: dict[str, dict[str, Any]] = {
        lane: {
            "status": "EVIDENCE_MISSING",
            "artifacts": [],
            "passes": 0,
            "failures": 0,
            "blocked": 0,
            "unauthorized_canonical_effects": 0,
            "accepted_artifacts": evidence["accepted_artifacts"].get(lane, 0),
            "accepted_tiers": evidence["accepted_tiers"].get(lane, []),
            "minimum_tiers": evidence["minimum_tiers"].get(lane, []),
            "defects": [],
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

    for defect in evidence["defects"]:
        parts = defect.split(":")
        if len(parts) >= 2 and parts[1] in lanes:
            lanes[parts[1]]["defects"].append(defect)
        elif defect.startswith("missing_lane:"):
            lane = defect.split(":", 1)[1]
            if lane in lanes:
                lanes[lane]["defects"].append(defect)

    for lane, entry in lanes.items():
        if not entry["artifacts"]:
            entry["status"] = "EVIDENCE_MISSING"
        elif entry["defects"]:
            if entry["blocked"]:
                entry["status"] = "EXECUTION_BLOCKED"
            elif entry["unauthorized_canonical_effects"]:
                entry["status"] = "R3_SOVEREIGNTY_FAILURE"
            else:
                entry["status"] = "R3_EVIDENCE_INCOMPLETE_OR_FAILED"
        else:
            entry["status"] = "R3_EVIDENCE_PASS"

    eligible = bool(evidence["evidence_ready"])
    return {
        "schema": "gmai-technology-radar-v1.3.6-r3-scorecard.v2",
        "lanes": lanes,
        "evidence_ready": evidence["evidence_ready"],
        "evidence_defects": evidence["defects"],
        "r4_decision_eligible": eligible,
        "production_adoption_authorized": False,
        "professional_austria_review_satisfied": False,
        "notes": [
            "R3 evidence does not authorize production adoption.",
            "Technology selection never changes Human Owner authority.",
            "Austria professional review is a separate unresolved gate unless independently satisfied.",
            "A lane passes only when Grand Trial evidence acceptance rules also pass.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("results", nargs="+", type=Path)
    args = parser.parse_args()

    scorecard = build_scorecard(args.results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(scorecard, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "R4 decision eligible"
        if scorecard["r4_decision_eligible"]
        else "R4 decision not yet eligible"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
