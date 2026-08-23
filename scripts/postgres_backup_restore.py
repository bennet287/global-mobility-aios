from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMPOSE_FILE = ROOT / "docker-compose.prod.yml"
DEFAULT_ENV_FILE = ROOT / ".env.production"
DEFAULT_OUTPUT_DIR = ROOT / "backups" / "postgres"
DEFAULT_POSTGRES_IMAGE = "postgres:16-alpine"
BACKUP_SCHEMA_VERSION = "gmai-postgres-backup-v1"
RESTORE_SCHEMA_VERSION = "gmai-postgres-restore-verification-v1"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_text(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, capture_output=True, text=True)
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "command failed").strip()
        raise RuntimeError(detail[:2000])
    return result


def _compose_base(compose_file: Path, env_file: Path) -> list[str]:
    if not compose_file.is_file():
        raise FileNotFoundError(f"Compose file not found: {compose_file}")
    if not env_file.is_file():
        raise FileNotFoundError(f"Production env file not found: {env_file}")
    return [
        "docker",
        "compose",
        "--env-file",
        str(env_file),
        "-f",
        str(compose_file),
    ]


def _container_env_value(base: list[str], key: str) -> str:
    result = _run_text(base + ["exec", "-T", "postgres", "printenv", key])
    value = result.stdout.strip()
    if not value:
        raise RuntimeError(f"Postgres container did not expose {key}")
    return value


def _source_schema_metadata(base: list[str], postgres_user: str, postgres_db: str) -> tuple[str, int]:
    alembic_result = _run_text(
        base
        + [
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            postgres_user,
            "-d",
            postgres_db,
            "-Atc",
            "SELECT version_num FROM alembic_version LIMIT 1;",
        ]
    )
    alembic_version = alembic_result.stdout.strip()
    if not alembic_version:
        raise RuntimeError("Source database alembic_version is missing")

    table_count_result = _run_text(
        base
        + [
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            postgres_user,
            "-d",
            postgres_db,
            "-Atc",
            "SELECT count(*) FROM pg_catalog.pg_tables WHERE schemaname = 'public';",
        ]
    )
    try:
        table_count = int(table_count_result.stdout.strip())
    except ValueError as exc:
        raise RuntimeError("Source database public-table count is invalid") from exc
    if table_count <= 0:
        raise RuntimeError("Source database has no public tables")
    return alembic_version, table_count


def _write_json(path: Path, payload: dict[str, object]) -> None:
    temporary_path = path.with_name(f"{path.name}.tmp")
    try:
        temporary_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def create_backup(
    *,
    compose_file: Path = DEFAULT_COMPOSE_FILE,
    env_file: Path = DEFAULT_ENV_FILE,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> tuple[Path, Path]:
    base = _compose_base(compose_file, env_file)
    postgres_user = _container_env_value(base, "POSTGRES_USER")
    postgres_db = _container_env_value(base, "POSTGRES_DB")

    source_alembic_before, source_table_count_before = _source_schema_metadata(
        base,
        postgres_user,
        postgres_db,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = _utc_now()
    suffix = uuid.uuid4().hex[:8]
    backup_path = output_dir / f"gmai-postgres-{created_at:%Y%m%dT%H%M%SZ}-{suffix}.dump"
    manifest_path = backup_path.with_suffix(".manifest.json")

    dump_command = base + [
        "exec",
        "-T",
        "postgres",
        "pg_dump",
        "--format=custom",
        "--no-owner",
        "--no-privileges",
        "-U",
        postgres_user,
        "-d",
        postgres_db,
    ]

    with backup_path.open("wb") as handle:
        result = subprocess.run(dump_command, stdout=handle, stderr=subprocess.PIPE)

    if result.returncode != 0:
        backup_path.unlink(missing_ok=True)
        detail = (result.stderr or b"pg_dump failed").decode("utf-8", errors="replace").strip()
        raise RuntimeError(detail[:2000])

    size_bytes = backup_path.stat().st_size
    if size_bytes <= 0:
        backup_path.unlink(missing_ok=True)
        raise RuntimeError("pg_dump produced an empty backup")

    try:
        source_alembic_after, source_table_count_after = _source_schema_metadata(
            base,
            postgres_user,
            postgres_db,
        )
        if (
            source_alembic_before != source_alembic_after
            or source_table_count_before != source_table_count_after
        ):
            raise RuntimeError("Source schema metadata changed while the backup was being created")

        digest = _sha256(backup_path)
        manifest = {
            "schema_version": BACKUP_SCHEMA_VERSION,
            "created_at": created_at.isoformat(),
            "backup_file": backup_path.name,
            "format": "postgres-custom",
            "sha256": digest,
            "size_bytes": size_bytes,
            "source": {
                "compose_service": "postgres",
                "database": postgres_db,
                "postgres_user": postgres_user,
                "alembic_version": source_alembic_after,
                "public_table_count": source_table_count_after,
            },
        }
        _write_json(manifest_path, manifest)
    except Exception:
        backup_path.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        raise
    return backup_path, manifest_path


def _load_and_verify_manifest(backup_path: Path) -> tuple[dict[str, Any], str]:
    manifest_path = backup_path.with_suffix(".manifest.json")
    if not manifest_path.is_file():
        raise RuntimeError("Backup manifest not found; restore verification requires an integrity manifest")

    digest = _sha256(backup_path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("Backup manifest must contain a JSON object")
    if payload.get("schema_version") != BACKUP_SCHEMA_VERSION:
        raise RuntimeError("Backup manifest schema is not supported")
    if payload.get("backup_file") != backup_path.name:
        raise RuntimeError("Backup manifest filename does not match the dump")
    if payload.get("format") != "postgres-custom":
        raise RuntimeError("Backup manifest format is not supported")
    if payload.get("sha256") != digest:
        raise RuntimeError("Backup SHA-256 does not match its manifest")
    if payload.get("size_bytes") != backup_path.stat().st_size:
        raise RuntimeError("Backup size does not match its manifest")

    source = payload.get("source")
    if not isinstance(source, dict):
        raise RuntimeError("Backup manifest source metadata is missing")
    source_alembic_version = source.get("alembic_version")
    source_public_table_count = source.get("public_table_count")
    if not isinstance(source_alembic_version, str) or not source_alembic_version.strip():
        raise RuntimeError("Backup manifest source alembic_version is missing")
    if not isinstance(source_public_table_count, int) or source_public_table_count <= 0:
        raise RuntimeError("Backup manifest source public_table_count is invalid")

    return payload, digest


def _wait_for_postgres(container_name: str, postgres_user: str, postgres_db: str, timeout_seconds: int) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        result = _run_text(
            ["docker", "exec", container_name, "pg_isready", "-U", postgres_user, "-d", postgres_db],
            check=False,
        )
        if result.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError(f"Disposable restore container was not ready within {timeout_seconds}s")


def verify_restore(
    *,
    backup_path: Path,
    image: str = DEFAULT_POSTGRES_IMAGE,
    timeout_seconds: int = 60,
) -> Path:
    if not backup_path.is_file():
        raise FileNotFoundError(f"Backup not found: {backup_path}")
    if backup_path.stat().st_size <= 0:
        raise RuntimeError("Backup is empty")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")

    manifest, digest = _load_and_verify_manifest(backup_path)
    source = manifest["source"]
    assert isinstance(source, dict)
    source_alembic_version = str(source["alembic_version"])
    source_public_table_count = int(source["public_table_count"])

    container_name = f"gmai-restore-verify-{uuid.uuid4().hex[:10]}"
    postgres_user = "gmai_restore"
    postgres_db = "gmai_restore_verify"
    postgres_password = secrets.token_urlsafe(24)
    started = False
    verified_payload: dict[str, object] | None = None

    try:
        _run_text(
            [
                "docker",
                "run",
                "--detach",
                "--name",
                container_name,
                "--network",
                "none",
                "--label",
                "com.global-mobility-aios.purpose=restore-verification",
                "--env",
                f"POSTGRES_USER={postgres_user}",
                "--env",
                f"POSTGRES_PASSWORD={postgres_password}",
                "--env",
                f"POSTGRES_DB={postgres_db}",
                image,
            ]
        )
        started = True
        _wait_for_postgres(container_name, postgres_user, postgres_db, timeout_seconds)
        _run_text(["docker", "cp", str(backup_path), f"{container_name}:/tmp/backup.dump"])
        _run_text(
            [
                "docker",
                "exec",
                container_name,
                "pg_restore",
                "--exit-on-error",
                "--no-owner",
                "--no-privileges",
                "-U",
                postgres_user,
                "-d",
                postgres_db,
                "/tmp/backup.dump",
            ]
        )

        table_count_result = _run_text(
            [
                "docker",
                "exec",
                container_name,
                "psql",
                "-U",
                postgres_user,
                "-d",
                postgres_db,
                "-Atc",
                "SELECT count(*) FROM pg_catalog.pg_tables WHERE schemaname = 'public';",
            ]
        )
        try:
            table_count = int(table_count_result.stdout.strip())
        except ValueError as exc:
            raise RuntimeError("Restored public-table count is invalid") from exc
        if table_count != source_public_table_count:
            raise RuntimeError(
                "Restored public-table count does not match the source backup metadata "
                f"({table_count} != {source_public_table_count})"
            )

        alembic_result = _run_text(
            [
                "docker",
                "exec",
                container_name,
                "psql",
                "-U",
                postgres_user,
                "-d",
                postgres_db,
                "-Atc",
                "SELECT version_num FROM alembic_version LIMIT 1;",
            ]
        )
        alembic_version = alembic_result.stdout.strip()
        if not alembic_version:
            raise RuntimeError("Restore completed but alembic_version is missing")
        if alembic_version != source_alembic_version:
            raise RuntimeError(
                "Restored alembic_version does not match the source backup metadata "
                f"({alembic_version!r} != {source_alembic_version!r})"
            )

        image_id_result = _run_text(
            ["docker", "inspect", "--format", "{{.Image}}", container_name]
        )
        restore_image_id = image_id_result.stdout.strip()
        if not restore_image_id:
            raise RuntimeError("Disposable restore container image ID is missing")

        verified_at = _utc_now()
        verification_id = uuid.uuid4().hex[:12]
        verified_payload = {
            "schema_version": RESTORE_SCHEMA_VERSION,
            "verification_id": verification_id,
            "verified_at": verified_at.isoformat(),
            "backup_file": backup_path.name,
            "backup_created_at": manifest.get("created_at"),
            "sha256": digest,
            "manifest_verified": True,
            "restore_image": image,
            "restore_image_id": restore_image_id,
            "network_mode": "none",
            "isolated_container": True,
            "source_public_table_count": source_public_table_count,
            "restored_public_table_count": table_count,
            "source_alembic_version": source_alembic_version,
            "restored_alembic_version": alembic_version,
            "restore_verified": True,
        }
    finally:
        if started:
            cleanup_result = _run_text(["docker", "rm", "-f", container_name], check=False)
            if verified_payload is not None and cleanup_result.returncode != 0:
                detail = (cleanup_result.stderr or cleanup_result.stdout or "docker rm failed").strip()
                raise RuntimeError(f"Restore verified but disposable-container cleanup failed: {detail[:1000]}")

    assert verified_payload is not None
    verification_id = str(verified_payload["verification_id"])
    verification_path = backup_path.with_name(
        f"{backup_path.stem}.restore-verification-{verification_id}.json"
    )
    _write_json(verification_path, verified_payload)
    return verification_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a PostgreSQL production backup and verify it in a disposable isolated Postgres container."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup_parser = subparsers.add_parser("backup", help="Create a custom-format pg_dump plus integrity manifest")
    backup_parser.add_argument("--compose-file", type=Path, default=DEFAULT_COMPOSE_FILE)
    backup_parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    backup_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)

    verify_parser = subparsers.add_parser(
        "verify-restore",
        help="Restore a manifested dump into a network-isolated disposable Postgres container and verify schema parity",
    )
    verify_parser.add_argument("--backup", type=Path, required=True)
    verify_parser.add_argument("--image", default=DEFAULT_POSTGRES_IMAGE)
    verify_parser.add_argument("--timeout-seconds", type=int, default=60)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        if args.command == "backup":
            backup_path, manifest_path = create_backup(
                compose_file=args.compose_file.resolve(),
                env_file=args.env_file.resolve(),
                output_dir=args.output_dir.resolve(),
            )
            print(f"PostgreSQL backup created: {backup_path}")
            print(f"Integrity manifest: {manifest_path}")
            return 0

        verification_path = verify_restore(
            backup_path=args.backup.resolve(),
            image=args.image,
            timeout_seconds=args.timeout_seconds,
        )
        print(f"Isolated restore verification passed: {verification_path}")
        return 0
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"PostgreSQL backup/restore operation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
