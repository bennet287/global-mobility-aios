from __future__ import annotations

import json
import zipfile
from pathlib import Path

from scripts.check_github_release_ready import (
    REQUIRED_ARCHIVE_ENTRIES,
    REQUIRED_TAGS,
    GitState,
    build_github_release_report,
    build_push_commands,
    inspect_release_archive,
)


def _ready_git_state() -> GitState:
    return GitState(
        branch="feature/github-release-prep-v6.3",
        head="abc1234",
        working_tree_clean=True,
        tags=REQUIRED_TAGS,
        remote_urls=("origin\thttps://github.com/example/global-mobility-aios.git (fetch)",),
    )


def _write_docs(root: Path) -> None:
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    for name in (
        "CHANGELOG.md",
        "RELEASE_NOTES_MVP_V6_2.md",
        "GITHUB_RELEASE_PREP_V6_3.md",
        "MVP_RELEASE_ARCHIVE_V6_2.md",
    ):
        (docs / name).write_text(f"# {name}\n", encoding="utf-8")


def _write_ready_archive(path: Path) -> None:
    manifest = {
        "status": "ready",
        "archive_version": "v6.2",
        "safety": {
            "auto_send": "disabled",
            "automatic_submission": "disabled",
            "automatic_lead_conversion": "disabled",
            "human_review_required": True,
        },
        "included_files": list(REQUIRED_ARCHIVE_ENTRIES),
    }
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("release/mvp-release-bundle-v6.1.md", "# Bundle\n")
        archive.writestr("release/mvp-release-bundle-v6.1.json", "{}")
        archive.writestr("metadata/manifest.json", json.dumps(manifest))


def test_github_release_report_ready_with_clean_git_docs_tags_and_archive(tmp_path: Path) -> None:
    _write_docs(tmp_path)
    archive_path = tmp_path / "mvp-release-archive-v6.2.zip"
    _write_ready_archive(archive_path)

    report = build_github_release_report(
        root=tmp_path,
        archive_path=archive_path,
        git_state=_ready_git_state(),
    )

    assert report["status"] == "ready"
    assert report["checks"]["working_tree_clean"] is True
    assert report["checks"]["required_tags_present"] is True
    assert report["checks"]["release_archive_ready"] is True
    assert report["archive"]["safety"]["auto_send"] == "disabled"


def test_github_release_report_blocks_dirty_tree_and_missing_tag(tmp_path: Path) -> None:
    _write_docs(tmp_path)
    archive_path = tmp_path / "mvp-release-archive-v6.2.zip"
    _write_ready_archive(archive_path)
    dirty_git = GitState(
        branch="feature/github-release-prep-v6.3",
        head="abc1234",
        working_tree_clean=False,
        tags=tuple(tag for tag in REQUIRED_TAGS if tag != "mvp-release-v6.2"),
    )

    report = build_github_release_report(
        root=tmp_path,
        archive_path=archive_path,
        git_state=dirty_git,
    )

    assert report["status"] == "not_ready"
    assert report["checks"]["working_tree_clean"] is False
    assert report["checks"]["required_tags_present"] is False
    assert report["git"]["missing_tags"] == ["mvp-release-v6.2"]


def test_release_archive_inspection_rejects_missing_manifest(tmp_path: Path) -> None:
    archive_path = tmp_path / "broken.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("release/mvp-release-bundle-v6.1.md", "# Bundle\n")

    result = inspect_release_archive(archive_path)

    assert result["status"] == "not_ready"
    assert "metadata/manifest.json" in result["missing_entries"]


def test_push_commands_reference_branch_tags_release_notes_and_archive() -> None:
    commands = "\n".join(build_push_commands("feature/github-release-prep-v6.3"))

    assert "git push -u origin feature/github-release-prep-v6.3" in commands
    assert "mvp-release-v6.2" in commands
    assert "docs/RELEASE_NOTES_MVP_V6_2.md" in commands
    assert "release_exports/mvp-release-archive-v6.2.zip" in commands
