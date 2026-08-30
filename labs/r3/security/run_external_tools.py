from __future__ import annotations

import argparse
import importlib.metadata
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id
from labs.r3.security.external_target_server import SecurityTargetServer
from labs.r3.security.inspect_task import aios_security


CORPUS = Path(__file__).resolve().parent / "deep_attack_corpus.v2.json"


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _tool_result(
    *,
    tool: str,
    version: str | None,
    executed: bool,
    exit_code: int | None,
    blocked_reason: str | None,
    observations: list[dict[str, Any]],
    command: list[str] | None = None,
) -> dict[str, Any]:
    unauthorized = sum(
        sum(int(value) for value in item.get("effects", {}).values())
        for item in observations
    )
    return {
        "tool": tool,
        "version": version,
        "executed": executed,
        "exit_code": exit_code,
        "execution_blocked": not executed,
        "block_reason": blocked_reason,
        "command": command,
        "observations": observations,
        "observation_count": len(observations),
        "unauthorized_canonical_effects": unauthorized,
        "tool_execution_success": executed and exit_code == 0,
        "security_truth_source": "AIOS_STATE_DIFF",
    }


def run_inspect(log_dir: Path) -> dict[str, Any]:
    try:
        version = importlib.metadata.version("inspect-ai")
        from inspect_ai import eval as inspect_eval
    except (ImportError, importlib.metadata.PackageNotFoundError) as exc:
        return _tool_result(
            tool="inspect-ai",
            version=None,
            executed=False,
            exit_code=None,
            blocked_reason=f"inspect-ai unavailable: {exc}",
            observations=[],
        )

    logs = inspect_eval(
        aios_security(),
        model=None,
        display="none",
        log_dir=str(log_dir),
        log_format="json",
        fail_on_error=False,
        max_samples=1,
    )
    samples = sum(len(log.samples or []) for log in logs)
    statuses = [str(log.status) for log in logs]
    return {
        **_tool_result(
            tool="inspect-ai",
            version=version,
            executed=True,
            exit_code=0 if logs else 1,
            blocked_reason=None,
            observations=[],
        ),
        "framework_sample_count": samples,
        "framework_statuses": statuses,
        "owned_corpus_count": 36,
        "model_calls_required": False,
    }


def _promptfoo_config(base_url: str, corpus: dict[str, Any]) -> dict[str, Any]:
    tests = []
    for attack in corpus["attacks"]:
        tests.append(
            {
                "vars": {
                    "payload": attack["payload"],
                    "attack_json": json.dumps(attack, separators=(",", ":")),
                },
                "assert": [{"type": "equals", "value": "PASS"}],
            }
        )
    return {
        "description": "GMAI R3 owned 36-attack state-diff bridge",
        "prompts": ["{{payload}}"],
        "providers": [
            {
                "id": "http",
                "config": {
                    "url": f"{base_url}/attack",
                    "method": "POST",
                    "body": {"attack": "{{attack_json | dump}}"},
                    "transformResponse": "json.verdict",
                },
            }
        ],
        "tests": tests,
    }


def run_promptfoo(
    *,
    base_url: str,
    corpus: dict[str, Any],
    work_dir: Path,
) -> dict[str, Any]:
    exe = shutil.which("promptfoo")
    if not exe:
        return _tool_result(
            tool="promptfoo",
            version=None,
            executed=False,
            exit_code=None,
            blocked_reason="promptfoo executable unavailable",
            observations=[],
        )

    version_process = subprocess.run(
        [exe, "--version"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    version = (version_process.stdout or version_process.stderr).strip() or None
    config = work_dir / "promptfooconfig.json"
    output = work_dir / "promptfoo-output.json"
    config.write_text(
        json.dumps(_promptfoo_config(base_url, corpus), indent=2) + "\n",
        encoding="utf-8",
    )
    command = [
        exe,
        "eval",
        "-c",
        str(config),
        "--no-cache",
        "--output",
        str(output),
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=300,
    )
    return _tool_result(
        tool="promptfoo",
        version=version,
        executed=True,
        exit_code=completed.returncode,
        blocked_reason=None,
        observations=[],
        command=command,
    )


def _garak_options(base_url: str) -> dict[str, Any]:
    return {
        "rest": {
            "RestGenerator": {
                "name": "gmai-r3-state-diff-target",
                "uri": f"{base_url}/generate",
                "method": "post",
                "req_template_json_object": {"text": "$INPUT"},
                "response_json": True,
                "response_json_field": "text",
                "request_timeout": 10,
            }
        }
    }


def run_garak(*, base_url: str, work_dir: Path) -> dict[str, Any]:
    exe = shutil.which("garak")
    if not exe:
        return _tool_result(
            tool="garak",
            version=None,
            executed=False,
            exit_code=None,
            blocked_reason="garak executable unavailable",
            observations=[],
        )

    version_process = subprocess.run(
        [exe, "--version"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    version = (version_process.stdout or version_process.stderr).strip() or None
    options = work_dir / "garak-rest.json"
    options.write_text(
        json.dumps(_garak_options(base_url), indent=2) + "\n",
        encoding="utf-8",
    )
    command = [
        exe,
        "--target_type",
        "rest",
        "-G",
        str(options),
        "--probes",
        "promptinject,dan",
    ]
    completed = subprocess.run(
        command,
        cwd=work_dir,
        capture_output=True,
        text=True,
        timeout=600,
    )
    return _tool_result(
        tool="garak",
        version=version,
        executed=True,
        exit_code=completed.returncode,
        blocked_reason=None,
        observations=[],
        command=command,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--tools",
        default="inspect,promptfoo,garak",
        help="comma-separated subset of inspect,promptfoo,garak",
    )
    args = parser.parse_args()
    validate_run_id(args.run_id)

    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    requested = {item.strip() for item in args.tools.split(",") if item.strip()}
    results: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="gmai-r3-security-tools-") as temp:
        work_dir = Path(temp)
        if "inspect" in requested:
            results.append(run_inspect(work_dir / "inspect-logs"))

        with SecurityTargetServer() as server:
            before = len(server.journal)
            if "promptfoo" in requested:
                item = run_promptfoo(
                    base_url=server.base_url,
                    corpus=corpus,
                    work_dir=work_dir,
                )
                item["observations"] = list(server.journal[before:])
                item["observation_count"] = len(item["observations"])
                item["unauthorized_canonical_effects"] = sum(
                    sum(obs["effects"].values()) for obs in item["observations"]
                )
                results.append(item)
                before = len(server.journal)

            if "garak" in requested:
                item = run_garak(base_url=server.base_url, work_dir=work_dir)
                item["observations"] = list(server.journal[before:])
                item["observation_count"] = len(item["observations"])
                item["unauthorized_canonical_effects"] = sum(
                    sum(obs["effects"].values()) for obs in item["observations"]
                )
                results.append(item)

    unauthorized = sum(
        int(item["unauthorized_canonical_effects"]) for item in results
    )
    executed = [item for item in results if item["executed"]]
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "external-security-tool-shootout",
        "candidate_version": "v1",
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-local-tools",
        "experiment": "t4-external-security-frameworks",
        "test_tiers": ["T4"],
        "scenario_count": len(results),
        "passes": sum(
            1 for item in executed
            if item["tool_execution_success"]
            and item["unauthorized_canonical_effects"] == 0
        ),
        "failures": sum(
            1 for item in executed
            if not item["tool_execution_success"]
            or item["unauthorized_canonical_effects"] != 0
        ),
        "execution_blocked": len(executed) != len(results),
        "critical_failures": unauthorized,
        "unauthorized_canonical_effects": unauthorized,
        "tool_results": results,
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
        f"security tools executed={len(executed)}/{len(results)}; "
        f"unauthorized effects={unauthorized}"
    )
    return 1 if unauthorized else (2 if result["execution_blocked"] else 0)


if __name__ == "__main__":
    raise SystemExit(main())
