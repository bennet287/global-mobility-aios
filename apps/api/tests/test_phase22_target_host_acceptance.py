from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import phase22_target_host_acceptance as executor


def test_target_environment_fingerprint_is_deterministic_and_sensitive() -> None:
    first = executor.target_environment_fingerprint(
        machine_id="machine-1",
        hostname="Canary-VPS",
        system_name="Linux",
        machine_architecture="x86_64",
    )
    second = executor.target_environment_fingerprint(
        machine_id="machine-1",
        hostname="Canary-VPS",
        system_name="Linux",
        machine_architecture="x86_64",
    )
    changed = executor.target_environment_fingerprint(
        machine_id="machine-2",
        hostname="Canary-VPS",
        system_name="Linux",
        machine_architecture="x86_64",
    )
    assert first == second
    assert len(first) == 64
    assert changed != first


def test_read_machine_id_uses_first_nonempty_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    empty = tmp_path / "empty"
    good = tmp_path / "machine-id"
    empty.write_text("\n", encoding="utf-8")
    good.write_text("machine-123\n", encoding="utf-8")
    assert executor.read_machine_id((missing, empty, good)) == "machine-123"


def test_running_release_identity_requires_all_running_exact_labels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commit = "a" * 40
    config = "b" * 64
    labels = {
        executor.RELEASE_REVISION_LABEL: commit,
        executor.RELEASE_CONFIGURATION_LABEL: config,
        executor.RELEASE_CONTRACT_LABEL: executor.RELEASE_IDENTITY_CONTRACT,
    }

    def fake_run(command: list[str]) -> str:
        container = command[-1]
        assert container in executor.PRODUCTION_APPLICATION_CONTAINERS
        template = command[command.index("--format") + 1]
        if template == "{{.State.Running}}":
            return "true"
        if template == "{{json .Config.Labels}}":
            return json.dumps(labels)
        if template == "{{.Image}}":
            return f"sha256:{container}"
        raise AssertionError(command)

    monkeypatch.setattr(executor, "_run_text", fake_run)
    observed = executor.verify_running_release_identity(
        expected_commit_sha=commit,
        expected_configuration_fingerprint=config,
    )
    assert [item.container_name for item in observed] == list(
        executor.PRODUCTION_APPLICATION_CONTAINERS
    )

    bad_labels = dict(labels)
    bad_labels[executor.RELEASE_REVISION_LABEL] = "c" * 40

    def bad_run(command: list[str]) -> str:
        template = command[command.index("--format") + 1]
        if template == "{{.State.Running}}":
            return "true"
        if template == "{{json .Config.Labels}}":
            return json.dumps(bad_labels)
        return "sha256:bad"

    monkeypatch.setattr(executor, "_run_text", bad_run)
    with pytest.raises(RuntimeError, match="release revision"):
        executor.verify_running_release_identity(
            expected_commit_sha=commit,
            expected_configuration_fingerprint=config,
        )


def test_executor_command_failure_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        executor.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="private transport detail",
        ),
    )
    with pytest.raises(RuntimeError, match="private transport detail"):
        executor._run_text(["docker", "inspect", "x"])
