from __future__ import annotations

import argparse
import json
from pathlib import Path

from labs.r3.common.harness import fingerprint


STARTER = Path(__file__).resolve().parent / "fixture" / "starter_candidate.py"


def build_packet() -> dict:
    packet = {
        "contract_version": "gmai.r3.dev-model-benchmark.v1",
        "task": (
            "Implement the five functions in starter_candidate.py. Preserve AIOS "
            "governance: capability is not authority, memory/model output is not "
            "VerifiedRule truth, replay is idempotent, secrets are redacted, and "
            "UI state cannot mutate canonical authority fields."
        ),
        "allowed_output": "one UTF-8 Python file replacing starter_candidate.py",
        "constraints": [
            "standard library only",
            "no network",
            "no file system dependency",
            "no subprocess",
            "no environment variable access",
            "do not change function signatures",
            "do not add product integrations",
        ],
        "starter_filename": "candidate.py",
        "starter_source": STARTER.read_text(encoding="utf-8"),
        "evaluation_boundary": {
            "microvm": "Microsandbox",
            "network": "NONE",
            "credentials": False,
            "host_volumes": False,
            "hidden_style_tests_disclosed": False,
        },
        "claim_boundary": (
            "The packet does not verify model/provider identity and a passing "
            "candidate does not authorize runtime use or production adoption."
        ),
    }
    packet["packet_sha256"] = fingerprint(packet)
    return packet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    packet = build_packet()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"development-model packet: {packet['packet_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
