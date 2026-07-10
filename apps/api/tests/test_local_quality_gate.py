from __future__ import annotations

from pathlib import Path
import sys

from scripts.check_local_quality import build_quality_commands


def test_local_quality_gate_command_plan_includes_required_checks() -> None:
    labels = [command.label for command in build_quality_commands()]

    assert labels == [
        "compileall",
        "repo_policy",
        "database_migrations",
        "docker_profile",
        "local_db_schema",
        "pytest",
    ]


def test_local_quality_gate_sets_pythonpath_for_pytest() -> None:
    pytest_command = build_quality_commands()[-1]

    assert pytest_command.argv == (sys.executable, "-m", "pytest", "apps/api/tests", "-q")
    assert pytest_command.env is not None
    pythonpath = Path(pytest_command.env["PYTHONPATH"])
    assert pythonpath.name == "api"
    assert pythonpath.parent.name == "apps"


def test_local_quality_gate_can_list_static_checks_without_pytest() -> None:
    labels = [command.label for command in build_quality_commands(skip_pytest=True)]

    assert labels == [
        "compileall",
        "repo_policy",
        "database_migrations",
        "docker_profile",
        "local_db_schema",
    ]
