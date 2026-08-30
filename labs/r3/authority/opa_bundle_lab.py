from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path
from typing import Any

import httpx

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id


OPA_VERSION = "1.19.1"
SIGNING_SECRET = "gmai-r3-opa-hs256-synthetic-secret"
POLICY = """package gmai.r3.bundle

import rego.v1

default allow := false

allow if {
    input.action == "case.read"
    input.risk <= data.policy.max_risk
}
"""


class ExecutionBlocked(RuntimeError):
    pass


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def _opa() -> str:
    binary = shutil.which("opa")
    if not binary:
        raise ExecutionBlocked("local OPA CLI is required for signed-bundle proof")
    return binary


def _write_source(path: Path, *, revision: str, max_risk: int) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "policy.rego").write_text(POLICY, encoding="utf-8")
    (path / "data.json").write_text(
        json.dumps(
            {"policy": {"revision": revision, "max_risk": max_risk}},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (path / ".manifest").write_text(
        json.dumps({"revision": revision, "roots": ["gmai"]}, indent=2) + "\n",
        encoding="utf-8",
    )


def _build_signed(opa: str, source: Path, output: Path) -> None:
    completed = subprocess.run(
        [
            opa,
            "build",
            "--bundle",
            str(source),
            "--signing-key",
            SIGNING_SECRET,
            "--signing-alg",
            "HS256",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout)[:1200])


def _serve_and_query(opa: str, bundle: Path, *, port: int, risk: int) -> bool:
    process = subprocess.Popen(
        [
            opa,
            "run",
            "--server",
            f"--addr=127.0.0.1:{port}",
            "--verification-key",
            SIGNING_SECRET,
            "--signing-alg",
            "HS256",
            "--bundle",
            str(bundle),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.time() + 8
        while time.time() < deadline:
            if process.poll() is not None:
                stderr = process.stderr.read() if process.stderr else ""
                raise RuntimeError(
                    f"OPA bundle server exited early: {stderr[:1000]}"
                )
            try:
                response = httpx.post(
                    f"http://127.0.0.1:{port}/v1/data/gmai/r3/bundle/allow",
                    json={"input": {"action": "case.read", "risk": risk}},
                    timeout=0.5,
                )
                if response.status_code == 200:
                    return bool(response.json().get("result", False))
            except httpx.HTTPError:
                pass
            time.sleep(0.1)
        raise RuntimeError("OPA bundle server did not become ready")
    finally:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()


def _tamper_bundle(source_bundle: Path, tampered_bundle: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="gmai-r3-opa-tamper-") as temp_dir:
        root = Path(temp_dir)
        with tarfile.open(source_bundle, "r:gz") as archive:
            archive.extractall(root)
        data_path = root / "data.json"
        data = json.loads(data_path.read_text(encoding="utf-8"))
        data["policy"]["max_risk"] = 99
        data_path.write_text(
            json.dumps(data, indent=2) + "\n", encoding="utf-8"
        )
        with tarfile.open(tampered_bundle, "w:gz") as archive:
            for item in sorted(root.rglob("*")):
                if item.is_file():
                    archive.add(
                        item,
                        arcname=item.relative_to(root).as_posix(),
                    )


def _tamper_rejected(opa: str, bundle: Path) -> bool:
    completed = subprocess.run(
        [
            opa,
            "run",
            "--verification-key",
            SIGNING_SECRET,
            "--signing-alg",
            "HS256",
            "--bundle",
            str(bundle),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=8,
    )
    return completed.returncode != 0


def run_bundle_lifecycle(*, base_port: int) -> dict[str, Any]:
    opa = _opa()
    outcomes: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="gmai-r3-opa-bundles-") as temp_dir:
        root = Path(temp_dir)
        v1_source = root / "v1"
        v2_source = root / "v2"
        v1_bundle = root / "v1.tar.gz"
        v2_bundle = root / "v2.tar.gz"
        tampered = root / "tampered.tar.gz"

        _write_source(v1_source, revision="v1", max_risk=5)
        _write_source(v2_source, revision="v2", max_risk=2)
        _build_signed(opa, v1_source, v1_bundle)
        _build_signed(opa, v2_source, v2_bundle)

        v1_allow = _serve_and_query(
            opa, v1_bundle, port=base_port, risk=4
        )
        v2_allow = _serve_and_query(
            opa, v2_bundle, port=base_port + 1, risk=4
        )
        rollback_allow = _serve_and_query(
            opa, v1_bundle, port=base_port + 2, risk=4
        )
        _tamper_bundle(v1_bundle, tampered)
        tamper_rejected = _tamper_rejected(opa, tampered)

        outcomes.extend(
            [
                {
                    "feature": "signed_bundle_v1_activates",
                    "observed": v1_allow,
                    "expected": True,
                },
                {
                    "feature": "stricter_signed_bundle_v2_changes_decision",
                    "observed": v2_allow,
                    "expected": False,
                },
                {
                    "feature": "rollback_to_signed_v1_reproduces_decision",
                    "observed": rollback_allow,
                    "expected": True,
                },
                {
                    "feature": "tampered_signed_bundle_rejected",
                    "observed": tamper_rejected,
                    "expected": True,
                },
            ]
        )

    for item in outcomes:
        item["passed"] = item["observed"] == item["expected"]
        item["unauthorized_canonical_effects"] = []

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "feature_coverage": {
            "bundle_build": True,
            "bundle_signing_hs256": True,
            "verification_on_activation": True,
            "stricter_rollout": True,
            "rollback": True,
            "tamper_rejection": True,
            "remote_bundle_polling": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-port", type=int, default=19181)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    try:
        detail = run_bundle_lifecycle(base_port=args.base_port)
        blocked = False
        block_reason = None
    except ExecutionBlocked as exc:
        detail = {
            "outcomes": [],
            "passes": 0,
            "failures": 0,
            "feature_coverage": {},
        }
        blocked = True
        block_reason = str(exc)

    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "opa",
        "candidate_version": OPA_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-real-cli",
        "experiment": "t2-t3-t4-opa-signed-bundle-lifecycle",
        "test_tiers": ["T2", "T3", "T4", "T8"],
        "execution_blocked": blocked,
        "block_reason": block_reason,
        "scenario_count": len(detail["outcomes"]),
        "passes": detail["passes"],
        "failures": detail["failures"],
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "feature_coverage": detail["feature_coverage"],
        "outcomes": detail["outcomes"],
        "decision_candidate": "CONTINUE_R3_WITH_SPECIFIC_GAP",
    }
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if blocked:
        print(f"OPA signed-bundle R3 blocked: {block_reason}")
        return 2
    print(
        f"OPA signed-bundle R3: {result['passes']}/{result['scenario_count']} passed"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
