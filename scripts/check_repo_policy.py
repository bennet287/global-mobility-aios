#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

BANNED_PATTERNS = [
    r"Claude-code_leak",
    r"Claude-code-leaks",
    r"claudecode",
    r"claurst",
    r"claw-code",
    r"system-prompts-and-models-of-ai-tools",
    r"RoguePlanet",
    r"C2TeamServer",
    r"masscan",
    r"routersploit",
    r"SpotX",
    r"iptv",
]

SCAN_EXTENSIONS = {
    ".md",
    ".py",
    ".txt",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".ini",
    ".env",
    ".ps1",
    ".sh",
    ".js",
    ".ts",
    ".tsx",
}

IGNORE_DIRS = {
    ".git",
    ".gmai-patch-backups",
    "__pycache__",
    ".venv",
    "node_modules",
    "dist",
    "build",
}

ALLOWLIST_FILES = {
    "REPOSITORY_POLICY.md",
    "0001-approved-repository-strategy.md",
    "check_repo_policy.py",
    "apply_mvp1_stabilization.py",
}

# PowerShell/shell redirection mistakes such as ``pip install celery>=5.4`` can
# create a tracked file named ``=5.4``. These names are not valid repository
# artifacts regardless of extension, so inspect every file before content filtering.
SUSPICIOUS_ARTIFACT_NAME_PATTERNS = (
    re.compile(r"^=.+"),
    re.compile(r"^[<>].+"),
)


def is_ignored(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def suspicious_artifact_name(path: Path) -> bool:
    return any(pattern.match(path.name) for pattern in SUSPICIOUS_ARTIFACT_NAME_PATTERNS)


def should_scan(path: Path) -> bool:
    if is_ignored(path):
        return False
    return path.is_file() and path.suffix in SCAN_EXTENSIONS


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Project root to scan")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    violations: list[str] = []

    for path in root.rglob("*"):
        if is_ignored(path) or not path.is_file():
            continue

        relative = path.relative_to(root)
        if suspicious_artifact_name(path):
            violations.append(
                f"{relative} has a suspicious shell-redirection artifact filename"
            )

        if not should_scan(path) or path.name in ALLOWLIST_FILES:
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in BANNED_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append(
                    f"{relative} contains banned repo/category pattern: {pattern}"
                )

    if violations:
        print("Repository policy violations detected:")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print("Repository policy check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
