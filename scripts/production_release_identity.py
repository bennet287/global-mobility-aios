#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
RELEASE_IDENTITY_CONTRACT = "phase22.release-identity.v1"
RELEASE_CONFIGURATION_PATHS: tuple[str, ...] = (
    "docker-compose.prod.yml",
    "apps/api/Dockerfile",
    "apps/api/.dockerignore",
    "apps/api/requirements.txt",
    "apps/api/constraints.txt",
    "apps/web/Dockerfile",
    "apps/web/.dockerignore",
    "apps/web/package.json",
    "apps/web/package-lock.json",
    "infrastructure/deployment/Caddyfile",
    "infrastructure/deployment/check-ingress-env.sh",
)
PRODUCTION_BUILD_SERVICES: tuple[str, ...] = (
    "api",
    "web",
)
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ProductionReleaseIdentity:
    commit_sha: str
    configuration_fingerprint: str
    contract: str = RELEASE_IDENTITY_CONTRACT


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def release_configuration_manifest(
    root: Path = ROOT,
    *,
    paths: Iterable[str] = RELEASE_CONFIGURATION_PATHS,
) -> tuple[dict[str, str], ...]:
    entries: list[dict[str, str]] = []
    for relative in sorted(set(paths)):
        path = root / relative
        if not path.is_file():
            raise RuntimeError(f"Release configuration input is missing: {relative}")
        entries.append(
            {
                "path": relative,
                "sha256": _sha256_bytes(path.read_bytes()),
            }
        )
    if not entries:
        raise RuntimeError("Release configuration input set is empty")
    return tuple(entries)


def compute_release_configuration_fingerprint(
    root: Path = ROOT,
    *,
    paths: Iterable[str] = RELEASE_CONFIGURATION_PATHS,
) -> str:
    payload = {
        "contract": RELEASE_IDENTITY_CONTRACT,
        "files": list(release_configuration_manifest(root, paths=paths)),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return _sha256_bytes(encoded)


def _git_output(args: tuple[str, ...], *, root: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise RuntimeError(detail[:2000])
    return completed.stdout.strip()


def resolve_production_release_identity(
    root: Path = ROOT,
) -> ProductionReleaseIdentity:
    dirty = _git_output(("status", "--porcelain", "--untracked-files=all"), root=root)
    if dirty:
        raise RuntimeError("Production release identity requires a clean Git working tree")

    commit_sha = _git_output(("rev-parse", "HEAD"), root=root).lower()
    if _HEX40.fullmatch(commit_sha) is None:
        raise RuntimeError("Git HEAD did not resolve to an exact lowercase 40-character commit SHA")

    configuration_fingerprint = compute_release_configuration_fingerprint(root)
    if _HEX64.fullmatch(configuration_fingerprint) is None:
        raise RuntimeError("Release configuration fingerprint is invalid")

    return ProductionReleaseIdentity(
        commit_sha=commit_sha,
        configuration_fingerprint=configuration_fingerprint,
    )


def production_build_command(
    *,
    root: Path = ROOT,
    env_file: Path,
    pull: bool = False,
) -> tuple[str, ...]:
    command: list[str] = [
        "docker",
        "compose",
        "--env-file",
        str(env_file),
        "-f",
        str(root / "docker-compose.prod.yml"),
        "build",
    ]
    if pull:
        command.append("--pull")
    command.extend(PRODUCTION_BUILD_SERVICES)
    return tuple(command)


def production_build_environment(
    identity: ProductionReleaseIdentity,
    *,
    base_environment: Mapping[str, str] | None = None,
) -> dict[str, str]:
    env = dict(base_environment if base_environment is not None else os.environ)
    env["AIOS_RELEASE_COMMIT_SHA"] = identity.commit_sha
    env["AIOS_RELEASE_CONFIGURATION_FINGERPRINT"] = identity.configuration_fingerprint
    return env


def build_production_release_images(
    *,
    root: Path = ROOT,
    env_file: Path,
    pull: bool = False,
) -> ProductionReleaseIdentity:
    if not env_file.is_file():
        raise RuntimeError(f"Production environment file was not found: {env_file}")

    identity = resolve_production_release_identity(root)
    completed = subprocess.run(
        production_build_command(root=root, env_file=env_file, pull=pull),
        cwd=root,
        env=production_build_environment(identity),
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Production release image build failed with exit code {completed.returncode}")
    return identity


def _identity_payload(identity: ProductionReleaseIdentity) -> dict[str, object]:
    return {
        "contract": identity.contract,
        "commit_sha": identity.commit_sha,
        "configuration_fingerprint": identity.configuration_fingerprint,
        "tracked_configuration_inputs": list(RELEASE_CONFIGURATION_PATHS),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Derive exact Phase 22 release identity from a clean checkout and optionally build "
            "the production application images with immutable OCI release labels."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    show_parser = subparsers.add_parser("show", help="Print the exact release identity for this checkout")
    show_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    build_parser = subparsers.add_parser(
        "build",
        help="Build production application images with exact release identity labels",
    )
    build_parser.add_argument(
        "--env-file",
        type=Path,
        default=ROOT / ".env.production",
        help="Production Compose environment file",
    )
    build_parser.add_argument(
        "--pull",
        action="store_true",
        help="Ask Docker Compose to pull newer base images before building",
    )

    args = parser.parse_args()
    try:
        if args.command == "show":
            identity = resolve_production_release_identity(ROOT)
        else:
            identity = build_production_release_images(
                root=ROOT,
                env_file=args.env_file.resolve(),
                pull=bool(args.pull),
            )
        payload = _identity_payload(identity)
        if getattr(args, "json", False):
            print(json.dumps(payload, sort_keys=True))
        else:
            print(f"contract={payload['contract']}")
            print(f"commit_sha={payload['commit_sha']}")
            print(f"configuration_fingerprint={payload['configuration_fingerprint']}")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Production release identity failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
