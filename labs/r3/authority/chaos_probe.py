from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from labs.r3.authority.adapters import OpenFgaAdapter, OpaAdapter
from labs.r3.common.generate_fixtures import build_authority_corpus
from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id


VERSIONS = {"openfga": "v1.18.1", "opa": "v1.19.1"}


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=["openfga", "opa"], required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--opa-url", default="http://127.0.0.1:18181")
    parser.add_argument("--openfga-url", default="http://127.0.0.1:18080")
    args = parser.parse_args()
    validate_run_id(args.run_id)
    if args.candidate == "opa":
        adapter = OpaAdapter(base_url=args.opa_url)
    else:
        adapter = OpenFgaAdapter(
            base_url=args.openfga_url,
            store_id="unavailable-store",
            authorization_model_id="unavailable-model",
        )

    request = build_authority_corpus()["scenarios"][0]["request"]
    observed = adapter.decide(request)
    passed = (
        observed.decision == "DENY"
        and observed.reason_class == "ENGINE_UNAVAILABLE"
        and observed.provider_called
    )
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": args.candidate,
        "candidate_version": VERSIONS[args.candidate],
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated",
        "experiment": "engine-unavailable",
        "expected_decision": "DENY",
        "observed_decision": observed.decision,
        "observed_reason_class": observed.reason_class,
        "provider_called": observed.provider_called,
        "passed": passed,
        "unauthorized_canonical_effects": 0,
    }
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"{args.candidate} unavailable probe: decision={observed.decision}; "
        f"reason={observed.reason_class}; passed={passed}"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
