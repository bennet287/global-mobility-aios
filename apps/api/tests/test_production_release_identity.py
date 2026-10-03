from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import production_release_identity as release_identity


def _write(root: Path, relative: str, value: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def test_release_configuration_fingerprint_is_deterministic_and_sensitive(tmp_path: Path) -> None:
    paths = ("docker-compose.prod.yml", "apps/api/Dockerfile")
    _write(tmp_path, paths[0], "services:\n  api: {}\n")
    _write(tmp_path, paths[1], "FROM python:3.12-slim\n")

    first = release_identity.compute_release_configuration_fingerprint(tmp_path, paths=paths)
    second = release_identity.compute_release_configuration_fingerprint(
        tmp_path,
        paths=reversed(paths),
    )
    assert first == second
    assert len(first) == 64

    _write(tmp_path, paths[1], "FROM python:3.12-slim\nLABEL changed=true\n")
    changed = release_identity.compute_release_configuration_fingerprint(tmp_path, paths=paths)
    assert changed != first


def test_release_identity_requires_clean_exact_git_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for relative in release_identity.RELEASE_CONFIGURATION_PATHS:
        _write(tmp_path, relative, f"{relative}\n")

    def clean_git(args: tuple[str, ...], *, root: Path) -> str:
        assert root == tmp_path
        if args[0] == "status":
            return ""
        if args == ("rev-parse", "HEAD"):
            return "a" * 40
        raise AssertionError(args)

    monkeypatch.setattr(release_identity, "_git_output", clean_git)
    identity = release_identity.resolve_production_release_identity(tmp_path)
    assert identity.commit_sha == "a" * 40
    assert len(identity.configuration_fingerprint) == 64

    monkeypatch.setattr(
        release_identity,
        "_git_output",
        lambda args, *, root: " M docker-compose.prod.yml" if args[0] == "status" else "a" * 40,
    )
    with pytest.raises(RuntimeError, match="clean Git working tree"):
        release_identity.resolve_production_release_identity(tmp_path)


def test_production_build_injects_derived_identity_and_scopes_app_images(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file = tmp_path / ".env.production"
    env_file.write_text("APP_ENV=production\n", encoding="utf-8")
    identity = release_identity.ProductionReleaseIdentity(
        commit_sha="b" * 40,
        configuration_fingerprint="c" * 64,
    )
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        release_identity,
        "resolve_production_release_identity",
        lambda root: identity,
    )

    def fake_run(command, **kwargs):
        captured["command"] = tuple(command)
        captured["cwd"] = kwargs.get("cwd")
        captured["env"] = kwargs.get("env")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(release_identity.subprocess, "run", fake_run)

    result = release_identity.build_production_release_images(
        root=tmp_path,
        env_file=env_file,
        pull=True,
    )

    assert result == identity
    command = captured["command"]
    assert command[:2] == ("docker", "compose")
    assert "--pull" in command
    assert command[-len(release_identity.PRODUCTION_BUILD_SERVICES):] == release_identity.PRODUCTION_BUILD_SERVICES
    env = captured["env"]
    assert env["AIOS_RELEASE_COMMIT_SHA"] == "b" * 40
    assert env["AIOS_RELEASE_CONFIGURATION_FINGERPRINT"] == "c" * 64
