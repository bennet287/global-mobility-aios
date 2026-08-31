from __future__ import annotations

import json
from pathlib import Path

from labs.r3.common.harness import fingerprint
from labs.r3.run_programme import (
    _step_selected,
    expected_head,
    parse_worktree_porcelain,
    verify_artifact,
)


def test_parse_worktree_porcelain_maps_branch() -> None:
    text = """worktree D:/global-mobility-aios
HEAD aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
branch refs/heads/radar/r3-runtime

worktree D:/gmai-r3-authority
HEAD bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
branch refs/heads/radar/r3-authority

"""
    worktrees = parse_worktree_porcelain(text)
    assert [item.branch for item in worktrees] == [
        "radar/r3-runtime",
        "radar/r3-authority",
    ]
    assert worktrees[1].path == Path("D:/gmai-r3-authority")


def test_runtime_expected_head_is_dynamic() -> None:
    inventory = {
        "branch_heads": {
            "radar/r3-runtime": "old",
            "radar/r3-authority": "authority-head",
        }
    }
    assert (
        expected_head(
            branch="radar/r3-runtime",
            inventory=inventory,
            runtime_head="current-runtime",
        )
        == "current-runtime"
    )
    assert (
        expected_head(
            branch="radar/r3-authority",
            inventory=inventory,
            runtime_head="current-runtime",
        )
        == "authority-head"
    )


def test_verify_artifact_recomputes_fingerprint_and_head(tmp_path: Path) -> None:
    result = {
        "git_sha": "a" * 40,
        "scenario_count": 1,
        "passes": 1,
        "failures": 0,
    }
    result["result_sha256"] = fingerprint(result)
    path = tmp_path / "result.json"
    path.write_text(json.dumps(result), encoding="utf-8")

    valid, defects, _ = verify_artifact(
        path,
        expected_git_sha="a" * 40,
    )
    assert valid is True
    assert defects == []

    result["passes"] = 2
    path.write_text(json.dumps(result), encoding="utf-8")
    valid, defects, _ = verify_artifact(
        path,
        expected_git_sha="a" * 40,
    )
    assert valid is False
    assert "invalid_fingerprint" in defects


def test_comparative_steps_are_opt_in() -> None:
    core = {
        "lane": "memory",
        "required_for_r4": True,
    }
    comparison = {
        "lane": "memory",
        "required_for_r4": False,
    }
    assert _step_selected(
        core,
        lanes={"memory"},
        include_comparative=False,
    )
    assert not _step_selected(
        comparison,
        lanes={"memory"},
        include_comparative=False,
    )
    assert _step_selected(
        comparison,
        lanes={"memory"},
        include_comparative=True,
    )
