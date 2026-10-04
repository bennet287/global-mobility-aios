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


def test_database_compatibility_probe_requires_model_schema_and_one_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        executor,
        "_run_process",
        lambda *args, **kwargs: json.dumps(
            {
                "missing_tables": [],
                "missing_columns": {},
                "schema_revisions": ["0100_phase22_release_networking_contract"],
                "leads_count": 7,
            }
        ),
    )
    observed = executor.database_compatibility_probe()
    assert observed.schema_revision == "0100_phase22_release_networking_contract"
    assert observed.stable_leads_count == 7

    monkeypatch.setattr(
        executor,
        "_run_process",
        lambda *args, **kwargs: json.dumps(
            {
                "missing_tables": ["organization_activities"],
                "missing_columns": {},
                "schema_revisions": ["0100_phase22_release_networking_contract"],
                "leads_count": 7,
            }
        ),
    )
    with pytest.raises(RuntimeError, match="model_schema_mismatch"):
        executor.database_compatibility_probe()


def test_switch_release_retains_schema_and_never_runs_migrations_or_pulls(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    release_root = tmp_path / "release"
    release_root.mkdir()
    (release_root / "docker-compose.prod.yml").write_text("services: {}", encoding="utf-8")
    env_file = tmp_path / ".env.production"
    env_file.write_text("X=1\\n", encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(command: list[str], **kwargs):
        calls.append(command)
        return ""

    monkeypatch.setattr(executor, "_run_process", fake_run)
    monkeypatch.setattr(executor, "wait_release_ready", lambda **kwargs: ())
    monkeypatch.setattr(executor, "verify_local_https", lambda contract: None)

    executor.switch_release(
        release_root,
        env_file=env_file,
        project_name="global-mobility-aios",
        commit_sha="a" * 40,
        configuration_fingerprint="b" * 64,
        networking_contract={"web_hostname": "web.example.eu", "api_hostname": "api.example.eu"},
        timeout_seconds=60,
    )

    assert "config" in calls[0]
    assert not any("api-migrate" in call or "alembic" in call for call in calls)
    assert "up" in calls[1]
    assert calls[1].index("up") < calls[1].index("api")
    assert "--no-build" in calls[1]
    assert "--no-deps" in calls[1]
    assert calls[1][calls[1].index("--pull") + 1] == "never"


def test_release_networking_v2_success_requires_real_rollback_and_restoration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run = SimpleNamespace(
        id=__import__("uuid").UUID("11111111-1111-4111-8111-111111111111"),
        target_environment_fingerprint="e" * 64,
        release_commit_sha="a" * 40,
        release_configuration_fingerprint="b" * 64,
        rollback_release_commit_sha="c" * 40,
        rollback_configuration_fingerprint="d" * 64,
    )
    external = SimpleNamespace(
        manifest_sha256="1" * 64,
        verifier_public_key_fingerprint="2" * 64,
        verifier_ref="refs/heads/main",
        verifier_commit_sha="3" * 40,
        network_contract_satisfied=True,
        blockers=(),
    )
    networking = {
        "web_hostname": "web.example.eu",
        "api_hostname": "api.example.eu",
    }
    env_file = tmp_path / ".env.production"
    env_file.write_text("X=1\\n", encoding="utf-8")
    candidate_root = tmp_path / "candidate"
    rollback_root = tmp_path / "rollback"
    candidate_root.mkdir()
    rollback_root.mkdir()
    envelope = tmp_path / "envelope.json"
    envelope.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(
        executor,
        "validated_deployment_networking_contract",
        lambda *args, **kwargs: (run, networking),
    )
    monkeypatch.setattr(executor, "trusted_executor_commit_sha", lambda root=executor.ROOT: "4" * 40)
    monkeypatch.setattr(executor, "verify_release_checkout", lambda *args, **kwargs: None)
    monkeypatch.setattr(executor, "_load_external_envelope", lambda path: object())
    monkeypatch.setattr(
        executor,
        "verify_external_network_manifest",
        lambda *args, **kwargs: external,
    )
    monkeypatch.setattr(executor, "wait_post_restore_external_observation", lambda *args, **kwargs: external)
    monkeypatch.setattr(executor, "resolve_target_environment_fingerprint", lambda: "e" * 64)
    monkeypatch.setattr(executor, "verify_release_images", lambda **kwargs: None)
    monkeypatch.setattr(executor, "verify_running_release_identity", lambda **kwargs: ())
    monkeypatch.setattr(executor, "resolve_compose_project_name", lambda: "global-mobility-aios")
    monkeypatch.setattr(executor, "restart_candidate_release", lambda *args, **kwargs: None)

    probes = iter(
        [
            executor.DatabaseCompatibilityObservation("0100_phase22_release_networking_contract", 7),
            executor.DatabaseCompatibilityObservation("0100_phase22_release_networking_contract", 7),
            executor.DatabaseCompatibilityObservation("0100_phase22_release_networking_contract", 7),
        ]
    )
    monkeypatch.setattr(executor, "database_compatibility_probe", lambda: next(probes))
    switched: list[Path] = []
    monkeypatch.setattr(
        executor,
        "switch_release",
        lambda root, **kwargs: switched.append(root),
    )
    captured = {}

    def fake_record(*args, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(id=__import__("uuid").uuid4(), status=kwargs["status"])

    monkeypatch.setattr(executor, "record_target_host_release_networking_receipt", fake_record)

    result = executor.record_release_networking_v2(
        object(),
        tenant_key="default",
        run_id=run.id,
        external_network_envelope=envelope,
        env_file=env_file,
        candidate_root=candidate_root,
        rollback_root=rollback_root,
        timeout_seconds=60,
    )

    assert result["status"] == "satisfied"
    assert result["candidate_restored"] is True
    assert switched == [rollback_root, candidate_root]
    details = captured["redacted_details"]
    assert details["rollback_retained_schema_verified"] is True
    assert details["rollback_release_identity_verified"] is True
    assert details["rollback_schema_compatibility_verified"] is True
    assert details["rollback_stable_data_verified"] is True
    assert details["candidate_restore_retained_schema_verified"] is True
    assert details["candidate_restore_identity_verified"] is True
    assert details["candidate_restore_schema_compatibility_verified"] is True
    assert details["candidate_restore_stable_data_verified"] is True
    assert details["failure_stage"] is None


@pytest.mark.parametrize("restore_failed", [False, True])
def test_release_networking_v2_failed_rollback_still_attempts_candidate_restore(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    restore_failed: bool,
) -> None:
    run = SimpleNamespace(
        id=__import__("uuid").UUID("22222222-2222-4222-8222-222222222222"),
        target_environment_fingerprint="e" * 64,
        release_commit_sha="a" * 40,
        release_configuration_fingerprint="b" * 64,
        rollback_release_commit_sha="c" * 40,
        rollback_configuration_fingerprint="d" * 64,
    )
    external = SimpleNamespace(
        manifest_sha256="1" * 64,
        verifier_public_key_fingerprint="2" * 64,
        verifier_ref="refs/heads/main",
        verifier_commit_sha="3" * 40,
        network_contract_satisfied=True,
        blockers=(),
    )
    env_file = tmp_path / ".env.production"
    env_file.write_text("X=1\\n", encoding="utf-8")
    candidate_root = tmp_path / "candidate"
    rollback_root = tmp_path / "rollback"
    candidate_root.mkdir()
    rollback_root.mkdir()
    envelope = tmp_path / "envelope.json"
    envelope.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(
        executor,
        "validated_deployment_networking_contract",
        lambda *args, **kwargs: (run, {"web_hostname": "web.example.eu", "api_hostname": "api.example.eu"}),
    )
    monkeypatch.setattr(executor, "trusted_executor_commit_sha", lambda root=executor.ROOT: "4" * 40)
    monkeypatch.setattr(executor, "verify_release_checkout", lambda *args, **kwargs: None)
    monkeypatch.setattr(executor, "_load_external_envelope", lambda path: object())
    monkeypatch.setattr(executor, "verify_external_network_manifest", lambda *args, **kwargs: external)
    monkeypatch.setattr(executor, "wait_post_restore_external_observation", lambda *args, **kwargs: external)
    monkeypatch.setattr(executor, "resolve_target_environment_fingerprint", lambda: "e" * 64)
    monkeypatch.setattr(executor, "verify_release_images", lambda **kwargs: None)
    monkeypatch.setattr(executor, "verify_running_release_identity", lambda **kwargs: ())
    monkeypatch.setattr(executor, "resolve_compose_project_name", lambda: "global-mobility-aios")
    monkeypatch.setattr(executor, "restart_candidate_release", lambda *args, **kwargs: None)
    probes = iter(
        [
            executor.DatabaseCompatibilityObservation("0100_phase22_release_networking_contract", 7),
            executor.DatabaseCompatibilityObservation("0100_phase22_release_networking_contract", 7),
        ]
    )
    monkeypatch.setattr(executor, "database_compatibility_probe", lambda: next(probes))
    switched: list[Path] = []

    def fake_switch(root: Path, **kwargs):
        switched.append(root)
        if root == rollback_root:
            raise RuntimeError("rollback:health_failed")
        if restore_failed:
            raise RuntimeError("candidate_restore:health_failed")

    monkeypatch.setattr(executor, "switch_release", fake_switch)
    captured = {}

    def fake_record(*args, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(id=__import__("uuid").uuid4(), status=kwargs["status"])

    monkeypatch.setattr(executor, "record_target_host_release_networking_receipt", fake_record)

    def invoke():
        return executor.record_release_networking_v2(
        object(),
        tenant_key="default",
        run_id=run.id,
        external_network_envelope=envelope,
        env_file=env_file,
        candidate_root=candidate_root,
        rollback_root=rollback_root,
        timeout_seconds=60,
    )


    if restore_failed:
        with pytest.raises(RuntimeError, match="unverified_operator_intervention"):
            invoke()
        assert switched == [rollback_root, candidate_root]
        assert captured == {}
        return
    result = invoke()

    assert result["status"] == "failed"
    assert switched == [rollback_root, candidate_root]
    assert captured["redacted_details"]["failure_stage"] == "rollback"
    assert captured["redacted_details"]["candidate_restored"] is True


def test_post_restore_external_evidence_rejects_pre_drill_and_waits_for_new_signature(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    from datetime import datetime, timedelta, timezone
    restored = datetime.now(timezone.utc)
    stale = SimpleNamespace(manifest_sha256="a" * 64, observed_started_at=restored - timedelta(seconds=1), verifier_ref="refs/heads/main")
    replay = SimpleNamespace(manifest_sha256="a" * 64, observed_started_at=restored, verifier_ref="refs/heads/main")
    new = SimpleNamespace(manifest_sha256="b" * 64, observed_started_at=restored + timedelta(seconds=1), verifier_ref="refs/heads/main")
    observations = iter([stale, replay, new])
    monkeypatch.setattr(executor, "_load_external_envelope", lambda path: object())
    monkeypatch.setattr(executor, "verify_external_network_manifest", lambda *args, **kwargs: next(observations))
    monkeypatch.setattr(executor.time, "sleep", lambda seconds: None)
    result = executor.wait_post_restore_external_observation(
        object(), object(), run_id=__import__("uuid").uuid4(), path=tmp_path / "envelope",
        candidate_restored_at=restored, previous_manifest_sha256="a" * 64, timeout_seconds=30,
    )
    assert result is new


def test_post_restore_missing_evidence_times_out(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from datetime import datetime, timezone
    ticks = iter([0, 0, 31])
    monkeypatch.setattr(executor.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(executor.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(executor, "_load_external_envelope", lambda path: (_ for _ in ()).throw(RuntimeError("missing")))
    with pytest.raises(RuntimeError, match="post_restore_evidence_timeout"):
        executor.wait_post_restore_external_observation(
            object(), object(), run_id=__import__("uuid").uuid4(), path=tmp_path / "missing",
            candidate_restored_at=datetime.now(timezone.utc), previous_manifest_sha256="a" * 64,
            timeout_seconds=30,
        )


def test_failed_networking_drill_returns_nonzero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(executor.sys, "argv", ["executor", "record-release-networking", "--run-id", "11111111-1111-4111-8111-111111111111", "--external-network-envelope", "/unused/envelope", "--env-file", "/unused/env", "--candidate-root", "/unused/candidate", "--rollback-root", "/unused/rollback", "--json"])
    monkeypatch.setattr(executor, "register_models", lambda: None)
    monkeypatch.setattr(executor, "record_release_networking_v2", lambda *args, **kwargs: {"status": "failed", "candidate_restored": True})
    assert executor.main() == 1


def test_database_probe_rejects_extra_required_columns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(executor, "_run_process", lambda *args, **kwargs: json.dumps({
        "missing_tables": [], "missing_columns": {}, "unsafe_extra_columns": {"leads": ["required_new_field"]},
        "schema_revisions": ["0100_phase22_release_networking_contract"], "leads_count": 7,
    }))
    with pytest.raises(RuntimeError, match="model_schema_mismatch"):
        executor.database_compatibility_probe()
