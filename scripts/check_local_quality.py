#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "apps" / "api"


@dataclass(frozen=True)
class QualityCommand:
    label: str
    argv: tuple[str, ...]
    env: dict[str, str] | None = None


def build_quality_commands(*, skip_pytest: bool = False) -> list[QualityCommand]:
    commands = [
        QualityCommand(
            label="compileall",
            argv=(
                sys.executable,
                "-m",
                "compileall",
                "apps/api/app",
                "apps/api/tests",
                "scripts/check_local_db_schema.py",
                "scripts/check_demo_readiness.py",
                "scripts/seed_demo_data.py",
                "scripts/check_database_migrations.py",
                "scripts/check_docker_profile.py",
                "scripts/check_local_quality.py",
                "scripts/check_demo_release.py",
                "scripts/check_mvp_release.py",
                "scripts/export_mvp_release_bundle.py",
                "scripts/export_mvp_release_archive.py",
                "scripts/check_github_release_ready.py",
                "scripts/seed_global_jurisdiction_registry.py",
                "scripts/validate_global_coverage_evidence_pack.py",
            ),
        ),
        QualityCommand(
            label="coverage_evidence_packs",
            argv=(sys.executable, "scripts/validate_global_coverage_evidence_pack.py", "--all"),
        ),
        QualityCommand(
            label="repo_policy",
            argv=(sys.executable, "scripts/check_repo_policy.py", "--root", "."),
        ),
        QualityCommand(
            label="database_migrations",
            argv=(sys.executable, "scripts/check_database_migrations.py"),
        ),
        QualityCommand(
            label="docker_profile",
            argv=(sys.executable, "scripts/check_docker_profile.py"),
        ),
        QualityCommand(
            label="local_db_schema",
            argv=(sys.executable, "scripts/check_local_db_schema.py"),
        ),
    ]
    if not skip_pytest:
        commands.append(
            QualityCommand(
                label="pytest",
                argv=(sys.executable, "-m", "pytest", "apps/api/tests", "-q"),
                env={"PYTHONPATH": str(API_PATH)},
            )
        )
    return commands


def _command_env(command: QualityCommand) -> dict[str, str]:
    env = os.environ.copy()
    if command.env:
        env.update(command.env)
    return env


def run_command(command: QualityCommand) -> dict[str, Any]:
    started = perf_counter()
    completed = subprocess.run(
        command.argv,
        cwd=ROOT,
        env=_command_env(command),
        text=True,
    )
    elapsed = round(perf_counter() - started, 3)
    return {
        "label": command.label,
        "returncode": completed.returncode,
        "elapsed_seconds": elapsed,
        "argv": list(command.argv),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local Global Mobility AIOS quality gate.")
    parser.add_argument("--skip-pytest", action="store_true", help="Run static/local checks without pytest.")
    parser.add_argument("--list", action="store_true", help="Print the command plan without running it.")
    parser.add_argument("--json", action="store_true", help="Print a JSON summary after running or listing commands.")
    args = parser.parse_args()

    commands = build_quality_commands(skip_pytest=args.skip_pytest)

    if args.list:
        plan = {
            "status": "planned",
            "commands": [
                {
                    "label": command.label,
                    "argv": list(command.argv),
                    "env": command.env or {},
                }
                for command in commands
            ],
        }
        print(json.dumps(plan, indent=2) if args.json else "\n".join(item["label"] for item in plan["commands"]))
        return 0

    results = []
    for command in commands:
        print(f"\n==> {command.label}", flush=True)
        result = run_command(command)
        results.append(result)
        if result["returncode"] != 0:
            summary = {"status": "failed", "failed_step": command.label, "results": results}
            if args.json:
                print(json.dumps(summary, indent=2))
            return result["returncode"]

    summary = {"status": "passed", "results": results}
    print("\nLocal quality gate passed.")
    if args.json:
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
