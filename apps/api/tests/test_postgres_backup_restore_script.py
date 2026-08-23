from __future__ import annotations

import importlib.util
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "scripts" / "postgres_backup_restore.py"
SPEC = importlib.util.spec_from_file_location("postgres_backup_restore", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
backup_restore = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backup_restore)

MIGRATION_HEAD = "0081_capability_autonomy_evidence_evaluation_policy"
PUBLIC_TABLE_COUNT = 124


def _write_manifest(
    backup_path: Path,
    *,
    alembic_version: str = MIGRATION_HEAD,
    public_table_count: int = PUBLIC_TABLE_COUNT,
) -> Path:
    manifest_path = backup_path.with_suffix(".manifest.json")
    payload = {
        "schema_version": backup_restore.BACKUP_SCHEMA_VERSION,
        "created_at": "2026-08-23T20:00:00+00:00",
        "backup_file": backup_path.name,
        "format": "postgres-custom",
        "sha256": backup_restore._sha256(backup_path),
        "size_bytes": backup_path.stat().st_size,
        "source": {
            "compose_service": "postgres",
            "database": "gmai",
            "postgres_user": "gmai",
            "alembic_version": alembic_version,
            "public_table_count": public_table_count,
        },
    }
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    return manifest_path


def _prepare_backup_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    *,
    metadata_sequence: list[tuple[str, int]] | None = None,
) -> None:
    monkeypatch.setattr(
        backup_restore,
        "_container_env_value",
        lambda _base, key: {"POSTGRES_USER": "gmai", "POSTGRES_DB": "gmai"}[key],
    )
    metadata = iter(
        metadata_sequence
        or [
            (MIGRATION_HEAD, PUBLIC_TABLE_COUNT),
            (MIGRATION_HEAD, PUBLIC_TABLE_COUNT),
        ]
    )
    monkeypatch.setattr(
        backup_restore,
        "_source_schema_metadata",
        lambda *_args, **_kwargs: next(metadata),
    )
    monkeypatch.setattr(
        backup_restore,
        "_utc_now",
        lambda: datetime(2026, 8, 23, 20, 0, tzinfo=timezone.utc),
    )
    monkeypatch.setattr(backup_restore.uuid, "uuid4", lambda: SimpleNamespace(hex="12345678abcdef"))


def test_create_backup_writes_dump_and_integrity_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    compose_file = tmp_path / "docker-compose.prod.yml"
    env_file = tmp_path / ".env.production"
    output_dir = tmp_path / "backups"
    compose_file.write_text("services: {}\n", encoding="utf-8")
    env_file.write_text("POSTGRES_USER=gmai\nPOSTGRES_DB=gmai\n", encoding="utf-8")
    _prepare_backup_dependencies(monkeypatch)

    def fake_run(args, *, stdout=None, stderr=None, **_kwargs):
        assert "pg_dump" in args
        assert stdout is not None
        stdout.write(b"postgres-custom-backup")
        return subprocess.CompletedProcess(args, 0, stdout=None, stderr=b"")

    monkeypatch.setattr(backup_restore.subprocess, "run", fake_run)

    backup_path, manifest_path = backup_restore.create_backup(
        compose_file=compose_file,
        env_file=env_file,
        output_dir=output_dir,
    )

    assert backup_path.name == "gmai-postgres-20260823T200000Z-12345678.dump"
    assert backup_path.read_bytes() == b"postgres-custom-backup"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == backup_restore.BACKUP_SCHEMA_VERSION
    assert manifest["backup_file"] == backup_path.name
    assert manifest["format"] == "postgres-custom"
    assert manifest["sha256"] == backup_restore._sha256(backup_path)
    assert manifest["size_bytes"] == backup_path.stat().st_size
    assert manifest["source"] == {
        "compose_service": "postgres",
        "database": "gmai",
        "postgres_user": "gmai",
        "alembic_version": MIGRATION_HEAD,
        "public_table_count": PUBLIC_TABLE_COUNT,
    }


def test_create_backup_removes_partial_dump_on_pg_dump_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    compose_file = tmp_path / "docker-compose.prod.yml"
    env_file = tmp_path / ".env.production"
    output_dir = tmp_path / "backups"
    compose_file.write_text("services: {}\n", encoding="utf-8")
    env_file.write_text("POSTGRES_USER=gmai\nPOSTGRES_DB=gmai\n", encoding="utf-8")
    _prepare_backup_dependencies(monkeypatch)

    def fake_run(args, *, stdout=None, stderr=None, **_kwargs):
        assert stdout is not None
        stdout.write(b"partial")
        return subprocess.CompletedProcess(args, 1, stdout=None, stderr=b"pg_dump exploded")

    monkeypatch.setattr(backup_restore.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="pg_dump exploded"):
        backup_restore.create_backup(
            compose_file=compose_file,
            env_file=env_file,
            output_dir=output_dir,
        )

    assert list(output_dir.glob("*.dump")) == []
    assert list(output_dir.glob("*.manifest.json")) == []


def test_create_backup_fails_if_source_schema_changes_during_dump(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    compose_file = tmp_path / "docker-compose.prod.yml"
    env_file = tmp_path / ".env.production"
    output_dir = tmp_path / "backups"
    compose_file.write_text("services: {}\n", encoding="utf-8")
    env_file.write_text("POSTGRES_USER=gmai\nPOSTGRES_DB=gmai\n", encoding="utf-8")
    _prepare_backup_dependencies(
        monkeypatch,
        metadata_sequence=[
            (MIGRATION_HEAD, PUBLIC_TABLE_COUNT),
            ("0082_future_schema", PUBLIC_TABLE_COUNT + 1),
        ],
    )

    def fake_run(args, *, stdout=None, stderr=None, **_kwargs):
        assert stdout is not None
        stdout.write(b"postgres-custom-backup")
        return subprocess.CompletedProcess(args, 0, stdout=None, stderr=b"")

    monkeypatch.setattr(backup_restore.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="Source schema metadata changed"):
        backup_restore.create_backup(
            compose_file=compose_file,
            env_file=env_file,
            output_dir=output_dir,
        )

    assert list(output_dir.glob("*.dump")) == []
    assert list(output_dir.glob("*.manifest.json")) == []


def test_create_backup_removes_dump_if_post_dump_metadata_check_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    compose_file = tmp_path / "docker-compose.prod.yml"
    env_file = tmp_path / ".env.production"
    output_dir = tmp_path / "backups"
    compose_file.write_text("services: {}\n", encoding="utf-8")
    env_file.write_text("POSTGRES_USER=gmai\nPOSTGRES_DB=gmai\n", encoding="utf-8")

    monkeypatch.setattr(
        backup_restore,
        "_container_env_value",
        lambda _base, key: {"POSTGRES_USER": "gmai", "POSTGRES_DB": "gmai"}[key],
    )
    calls = 0

    def fake_metadata(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return MIGRATION_HEAD, PUBLIC_TABLE_COUNT
        raise RuntimeError("source metadata unavailable")

    monkeypatch.setattr(backup_restore, "_source_schema_metadata", fake_metadata)
    monkeypatch.setattr(
        backup_restore,
        "_utc_now",
        lambda: datetime(2026, 8, 23, 20, 0, tzinfo=timezone.utc),
    )
    monkeypatch.setattr(backup_restore.uuid, "uuid4", lambda: SimpleNamespace(hex="12345678abcdef"))

    def fake_run(args, *, stdout=None, stderr=None, **_kwargs):
        assert stdout is not None
        stdout.write(b"postgres-custom-backup")
        return subprocess.CompletedProcess(args, 0, stdout=None, stderr=b"")

    monkeypatch.setattr(backup_restore.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="source metadata unavailable"):
        backup_restore.create_backup(
            compose_file=compose_file,
            env_file=env_file,
            output_dir=output_dir,
        )

    assert list(output_dir.glob("*.dump")) == []
    assert list(output_dir.glob("*.manifest.json")) == []


def test_manifest_verification_requires_companion_manifest(tmp_path: Path) -> None:
    backup_path = tmp_path / "backup.dump"
    backup_path.write_bytes(b"original")

    with pytest.raises(RuntimeError, match="manifest not found"):
        backup_restore._load_and_verify_manifest(backup_path)


def test_manifest_verification_fails_closed_on_tampered_dump(tmp_path: Path) -> None:
    backup_path = tmp_path / "backup.dump"
    backup_path.write_bytes(b"original")
    _write_manifest(backup_path)
    backup_path.write_bytes(b"tampered")

    with pytest.raises(RuntimeError, match="SHA-256"):
        backup_restore._load_and_verify_manifest(backup_path)


def test_manifest_verification_rejects_missing_source_schema_metadata(tmp_path: Path) -> None:
    backup_path = tmp_path / "backup.dump"
    backup_path.write_bytes(b"original")
    manifest_path = _write_manifest(backup_path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["source"].pop("alembic_version")
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RuntimeError, match="source alembic_version"):
        backup_restore._load_and_verify_manifest(backup_path)


def test_verify_restore_uses_network_isolation_matches_source_schema_and_writes_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backup_path = tmp_path / "backup.dump"
    backup_path.write_bytes(b"valid-dump")
    _write_manifest(backup_path)

    monkeypatch.setattr(backup_restore.uuid, "uuid4", lambda: SimpleNamespace(hex="abcdef1234567890"))
    monkeypatch.setattr(backup_restore.secrets, "token_urlsafe", lambda _n: "ephemeral-password")
    monkeypatch.setattr(backup_restore, "_wait_for_postgres", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        backup_restore,
        "_utc_now",
        lambda: datetime(2026, 8, 23, 20, 30, tzinfo=timezone.utc),
    )

    calls: list[list[str]] = []

    def fake_run_text(args: list[str], *, check: bool = True):
        calls.append(args)
        joined = " ".join(args)
        if "SELECT count(*) FROM pg_catalog.pg_tables" in joined:
            stdout = f"{PUBLIC_TABLE_COUNT}\n"
        elif "SELECT version_num FROM alembic_version" in joined:
            stdout = f"{MIGRATION_HEAD}\n"
        else:
            stdout = "ok\n"
        return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(backup_restore, "_run_text", fake_run_text)

    verification_path = backup_restore.verify_restore(backup_path=backup_path)
    verification = json.loads(verification_path.read_text(encoding="utf-8"))

    assert verification["schema_version"] == backup_restore.RESTORE_SCHEMA_VERSION
    assert verification["restore_verified"] is True
    assert verification["manifest_verified"] is True
    assert verification["verification_id"] == "abcdef123456"
    assert verification["restore_image_id"] == "ok"
    assert verification["network_mode"] == "none"
    assert verification["isolated_container"] is True
    assert verification["source_public_table_count"] == PUBLIC_TABLE_COUNT
    assert verification["restored_public_table_count"] == PUBLIC_TABLE_COUNT
    assert verification["source_alembic_version"] == MIGRATION_HEAD
    assert verification["restored_alembic_version"] == MIGRATION_HEAD

    docker_run = next(call for call in calls if call[:2] == ["docker", "run"])
    network_index = docker_run.index("--network")
    assert docker_run[network_index + 1] == "none"
    assert "--rm" not in docker_run
    assert any("pg_restore" in call for call in calls)
    assert calls[-1][:3] == ["docker", "rm", "-f"]


def test_verify_restore_fails_closed_on_source_schema_mismatch_and_cleans_container(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backup_path = tmp_path / "backup.dump"
    backup_path.write_bytes(b"valid-dump")
    _write_manifest(backup_path)

    monkeypatch.setattr(backup_restore.uuid, "uuid4", lambda: SimpleNamespace(hex="abcdef1234567890"))
    monkeypatch.setattr(backup_restore.secrets, "token_urlsafe", lambda _n: "ephemeral-password")
    monkeypatch.setattr(backup_restore, "_wait_for_postgres", lambda *_args, **_kwargs: None)

    calls: list[list[str]] = []

    def fake_run_text(args: list[str], *, check: bool = True):
        calls.append(args)
        joined = " ".join(args)
        if "SELECT count(*) FROM pg_catalog.pg_tables" in joined:
            stdout = f"{PUBLIC_TABLE_COUNT}\n"
        elif "SELECT version_num FROM alembic_version" in joined:
            stdout = "0080_old_schema\n"
        else:
            stdout = "ok\n"
        return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(backup_restore, "_run_text", fake_run_text)

    with pytest.raises(RuntimeError, match="alembic_version does not match"):
        backup_restore.verify_restore(backup_path=backup_path)

    assert calls[-1][:3] == ["docker", "rm", "-f"]
    assert list(tmp_path.glob("backup.restore-verification-*.json")) == []


def test_verify_restore_does_not_write_success_receipt_if_cleanup_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backup_path = tmp_path / "backup.dump"
    backup_path.write_bytes(b"valid-dump")
    _write_manifest(backup_path)

    monkeypatch.setattr(backup_restore.uuid, "uuid4", lambda: SimpleNamespace(hex="abcdef1234567890"))
    monkeypatch.setattr(backup_restore.secrets, "token_urlsafe", lambda _n: "ephemeral-password")
    monkeypatch.setattr(backup_restore, "_wait_for_postgres", lambda *_args, **_kwargs: None)

    def fake_run_text(args: list[str], *, check: bool = True):
        joined = " ".join(args)
        if args[:3] == ["docker", "rm", "-f"]:
            return subprocess.CompletedProcess(args, 1, stdout="", stderr="cleanup failed")
        if "SELECT count(*) FROM pg_catalog.pg_tables" in joined:
            stdout = f"{PUBLIC_TABLE_COUNT}\n"
        elif "SELECT version_num FROM alembic_version" in joined:
            stdout = f"{MIGRATION_HEAD}\n"
        else:
            stdout = "ok\n"
        return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(backup_restore, "_run_text", fake_run_text)

    with pytest.raises(RuntimeError, match="cleanup failed"):
        backup_restore.verify_restore(backup_path=backup_path)

    assert list(tmp_path.glob("backup.restore-verification-*.json")) == []
