#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
RELEASE_VERSION = "v6.3"
TARGET_MVP_RELEASE = "v6.2"
DEFAULT_ARCHIVE_PATH = ROOT / "release_exports" / "mvp-release-archive-v6.2.zip"
REQUIRED_TAGS = (
    "demo-release-v5.6",
    "demo-release-v5.7",
    "demo-release-v5.8",
    "demo-release-v5.9",
    "mvp-release-v6.0",
    "mvp-release-v6.1",
    "mvp-release-v6.2",
)
REQUIRED_DOCS = (
    "docs/CHANGELOG.md",
    "docs/RELEASE_NOTES_MVP_V6_2.md",
    "docs/GITHUB_RELEASE_PREP_V6_3.md",
    "docs/MVP_RELEASE_ARCHIVE_V6_2.md",
)
REQUIRED_ARCHIVE_ENTRIES = (
    "release/mvp-release-bundle-v6.1.md",
    "release/mvp-release-bundle-v6.1.json",
    "metadata/manifest.json",
)


@dataclass(frozen=True)
class GitState:
    branch: str
    head: str
    working_tree_clean: bool
    tags: tuple[str, ...]
    remote_urls: tuple[str, ...] = ()
    available: bool = True


def _run_git(args: Iterable[str], *, root: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "git command failed")
    return completed.stdout.strip()


def get_git_state(*, root: Path = ROOT) -> GitState:
    try:
        branch = _run_git(("rev-parse", "--abbrev-ref", "HEAD"), root=root)
        head = _run_git(("rev-parse", "--short", "HEAD"), root=root)
        status = _run_git(("status", "--porcelain"), root=root)
        tags = tuple(tag for tag in _run_git(("tag", "--list"), root=root).splitlines() if tag)
        remotes = tuple(line for line in _run_git(("remote", "-v"), root=root).splitlines() if line)
    except Exception:
        return GitState(
            branch="unknown",
            head="unknown",
            working_tree_clean=False,
            tags=(),
            remote_urls=(),
            available=False,
        )
    return GitState(
        branch=branch,
        head=head,
        working_tree_clean=(status == ""),
        tags=tags,
        remote_urls=remotes,
        available=True,
    )


def check_required_docs(*, root: Path = ROOT, required_docs: tuple[str, ...] = REQUIRED_DOCS) -> dict[str, Any]:
    existing: list[str] = []
    missing: list[str] = []
    for relative_path in required_docs:
        path = root / relative_path
        if path.exists() and path.is_file():
            existing.append(relative_path)
        else:
            missing.append(relative_path)
    return {
        "status": "ready" if not missing else "not_ready",
        "existing": existing,
        "missing": missing,
    }


def inspect_release_archive(archive_path: Path = DEFAULT_ARCHIVE_PATH) -> dict[str, Any]:
    if not archive_path.exists() or not archive_path.is_file():
        return {
            "status": "missing",
            "path": str(archive_path),
            "missing_entries": list(REQUIRED_ARCHIVE_ENTRIES),
            "manifest_status": "missing",
        }

    try:
        with zipfile.ZipFile(archive_path) as archive:
            names = set(archive.namelist())
            missing_entries = [entry for entry in REQUIRED_ARCHIVE_ENTRIES if entry not in names]
            manifest: dict[str, Any] = {}
            if "metadata/manifest.json" in names:
                manifest = json.loads(archive.read("metadata/manifest.json").decode("utf-8"))
    except Exception as exc:
        return {
            "status": "invalid",
            "path": str(archive_path),
            "error": str(exc),
            "missing_entries": list(REQUIRED_ARCHIVE_ENTRIES),
            "manifest_status": "invalid",
        }

    manifest_status = manifest.get("status", "unknown")
    archive_version = manifest.get("archive_version", "unknown")
    expected_archive = archive_version == "v6.2"
    ready = not missing_entries and manifest_status == "ready" and expected_archive
    return {
        "status": "ready" if ready else "not_ready",
        "path": str(archive_path),
        "archive_version": archive_version,
        "manifest_status": manifest_status,
        "included_files": manifest.get("included_files", []),
        "missing_entries": missing_entries,
        "safety": manifest.get("safety", {}),
    }


def build_push_commands(branch: str) -> list[str]:
    release_tags = " ".join(REQUIRED_TAGS)
    return [
        f"git push -u origin {branch}",
        f"git push origin {release_tags}",
        "# Create a GitHub release from tag mvp-release-v6.2.",
        "# Use docs/RELEASE_NOTES_MVP_V6_2.md as the release body.",
        "# Attach release_exports/mvp-release-archive-v6.2.zip as the local release archive.",
    ]


def build_github_release_report(
    *,
    root: Path = ROOT,
    archive_path: Path = DEFAULT_ARCHIVE_PATH,
    git_state: GitState | None = None,
    required_tags: tuple[str, ...] = REQUIRED_TAGS,
    required_docs: tuple[str, ...] = REQUIRED_DOCS,
) -> dict[str, Any]:
    git_state = git_state or get_git_state(root=root)
    missing_tags = [tag for tag in required_tags if tag not in set(git_state.tags)]
    docs = check_required_docs(root=root, required_docs=required_docs)
    archive = inspect_release_archive(archive_path)

    checks = {
        "git_available": git_state.available,
        "working_tree_clean": git_state.working_tree_clean,
        "required_tags_present": not missing_tags,
        "release_docs_present": docs["status"] == "ready",
        "release_archive_ready": archive["status"] == "ready",
    }
    ready = all(checks.values())

    return {
        "status": "ready" if ready else "not_ready",
        "release_prep_version": RELEASE_VERSION,
        "target_mvp_release": TARGET_MVP_RELEASE,
        "git": {
            "branch": git_state.branch,
            "head": git_state.head,
            "working_tree_clean": git_state.working_tree_clean,
            "available": git_state.available,
            "required_tags": list(required_tags),
            "missing_tags": missing_tags,
            "remote_urls": list(git_state.remote_urls),
        },
        "docs": docs,
        "archive": archive,
        "checks": checks,
        "push_commands": build_push_commands(git_state.branch),
    }


def print_text_report(report: dict[str, Any]) -> None:
    print(f"GitHub release prep {report['release_prep_version']}: {report['status']}")
    print(f"target_mvp_release={report['target_mvp_release']}")
    print(f"branch={report['git']['branch']}")
    print(f"head={report['git']['head']}")
    print(f"working_tree_clean={report['git']['working_tree_clean']}")
    print(f"missing_tags={','.join(report['git']['missing_tags']) or 'none'}")
    print(f"missing_docs={','.join(report['docs']['missing']) or 'none'}")
    print(f"archive_status={report['archive']['status']}")
    print(f"archive_path={report['archive']['path']}")
    if report["status"] == "ready":
        print("\nSuggested publish commands:")
        for command in report["push_commands"]:
            print(command)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether the MVP release is ready for GitHub backup/publishing.")
    parser.add_argument(
        "--archive",
        default=str(DEFAULT_ARCHIVE_PATH),
        help="Path to the local v6.2 release archive zip.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a text summary.")
    args = parser.parse_args()

    report = build_github_release_report(archive_path=Path(args.archive))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
