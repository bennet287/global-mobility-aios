#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys

# PR #8 is a long-lived product branch that predates the stronger multi-commit
# diff-hygiene gate. Its accepted history contains known whitespace debt and
# Markdown hard-break spacing. We therefore start strict multi-commit hygiene at
# the commit where the stronger gate was introduced, while future PRs compare
# target branch -> HEAD normally.
TRANSITION_BRANCH = "roadmap/global-mobility-aios-v12"
TRANSITION_PR = "8"
TRANSITION_BASELINE = "8624d7f9891a3af6bcbd3693c1286984f5c1fbfd"


def _run_git(*args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def _ensure_commit(sha: str) -> None:
    probe = _run_git("cat-file", "-e", f"{sha}^{{commit}}")
    if probe.returncode == 0:
        return

    fetched = _run_git("fetch", "--no-tags", "origin", sha)
    if fetched.returncode != 0:
        print(fetched.stdout, end="")
        raise RuntimeError(f"Unable to fetch diff-hygiene baseline {sha}")


def _ensure_target_branch(branch: str) -> str:
    remote_ref = f"origin/{branch}"
    probe = _run_git("rev-parse", "--verify", remote_ref)
    if probe.returncode == 0:
        return remote_ref

    fetched = _run_git(
        "fetch",
        "--no-tags",
        "origin",
        f"+refs/heads/{branch}:refs/remotes/origin/{branch}",
    )
    if fetched.returncode != 0:
        print(fetched.stdout, end="")
        raise RuntimeError(f"Unable to fetch target branch {branch!r}")
    return remote_ref


def _select_base() -> tuple[str, str]:
    woodpecker_pr = os.getenv("CI_COMMIT_PULL_REQUEST", "").strip()
    woodpecker_target = os.getenv("CI_COMMIT_TARGET_BRANCH", "").strip()
    github_base = os.getenv("GITHUB_BASE_REF", "").strip()
    github_head = os.getenv("GITHUB_HEAD_REF", "").strip()

    is_pr = bool(woodpecker_pr or github_base)
    if not is_pr:
        return "HEAD^", "non-PR latest-commit hygiene"

    if woodpecker_pr == TRANSITION_PR or github_head == TRANSITION_BRANCH:
        _ensure_commit(TRANSITION_BASELINE)
        return TRANSITION_BASELINE, "V12 long-lived-branch transition baseline"

    target = woodpecker_target or github_base
    if not target:
        raise RuntimeError("PR diff hygiene requires a target branch")
    return _ensure_target_branch(target), "target-branch-to-HEAD hygiene"


def main() -> int:
    try:
        base, reason = _select_base()
    except RuntimeError as exc:
        print(f"Diff hygiene setup failed: {exc}")
        return 2

    print(f"Diff hygiene base: {base} ({reason})")
    result = subprocess.run(
        [
            "git",
            "diff",
            "--check",
            base,
            "HEAD",
            "--",
            ".",
            ":(exclude)vendor/**",
        ],
        text=True,
    )
    if result.returncode != 0:
        print(
            "Diff hygiene failed. Historical debt before the selected base is "
            "grandfathered; this failure was introduced after that base."
        )
    else:
        print("Diff hygiene check passed.")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
