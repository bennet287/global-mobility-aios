from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Any


MANIFEST = Path(__file__).resolve().parent / "execution_manifest.v2.json"


def _git_head(path: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _tcp(host: str, port: int, timeout: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def preflight(manifest: dict[str, Any], worktrees: dict[str, Path]) -> dict[str, Any]:
    branch_checks: dict[str, Any] = {}
    for name, config in manifest["physical_branches"].items():
        path = worktrees.get(name)
        actual = None
        error = None
        if path is not None:
            try:
                actual = _git_head(path)
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
        branch_checks[name] = {
            "path": str(path) if path else None,
            "expected_head": config["head"],
            "actual_head": actual,
            "match": actual == config["head"],
            "error": error,
        }

    executables = {
        name: shutil.which(name)
        for name in (
            "git",
            "docker",
            "cedar",
            "opa",
            "promptfoo",
            "garak",
            "ollama",
        )
    }
    python_modules = {
        name: _module(name)
        for name in (
            "pytest",
            "httpx",
            "inspect_ai",
            "mcp",
            "a2a",
            "opentelemetry",
            "mem0",
            "openviking_sdk",
            "microsandbox",
            "temporalio",
            "langgraph",
            "agno",
        )
    }
    services = {
        "ollama_11434": _tcp("127.0.0.1", 11434),
        "openviking_1933": _tcp("127.0.0.1", 1933),
        "openfga_18080": _tcp("127.0.0.1", 18080),
        "opa_18181": _tcp("127.0.0.1", 18181),
        "openbao_18200": _tcp("127.0.0.1", 18200),
        "postgres_15432": _tcp("127.0.0.1", 15432),
        "otel_collector_14317": _tcp("127.0.0.1", 14317),
    }

    snapshot_ready = all(item["match"] for item in branch_checks.values())
    hard_requirements = {
        "git": bool(executables["git"]),
        "docker": bool(executables["docker"]),
        "pytest": python_modules["pytest"],
        "httpx": python_modules["httpx"],
    }
    optional_candidate_dependencies = {
        "cedar_cli": bool(executables["cedar"]),
        "opa_cli": bool(executables["opa"]),
        "promptfoo_cli": bool(executables["promptfoo"]),
        "garak_cli": bool(executables["garak"]),
        "ollama_cli": bool(executables["ollama"]),
        **python_modules,
    }

    return {
        "contract_version": "gmai.r3.preflight.v1",
        "snapshot_ready": snapshot_ready,
        "hard_requirements_ready": all(hard_requirements.values()),
        "campaign_can_start": snapshot_ready and all(hard_requirements.values()),
        "branch_checks": branch_checks,
        "hard_requirements": hard_requirements,
        "candidate_dependencies": optional_candidate_dependencies,
        "currently_listening_services": services,
        "notes": [
            "Candidate dependency absence is not a PASS and does not mutate evidence state.",
            "Docker-backed services may be started later by their lane runbooks.",
            "Mem0/OpenViking remain local-only; missing local providers must become execution_blocked.",
            "This preflight performs no repository writes, service starts, credential reads, or model calls.",
        ],
    }


def _worktree(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("expected physical_branch=path")
    name, raw = value.split("=", 1)
    return name, Path(raw).resolve()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--worktree", action="append", type=_worktree, default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = preflight(manifest, dict(args.worktree))
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["campaign_can_start"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
