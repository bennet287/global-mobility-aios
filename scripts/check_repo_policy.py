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
}

IGNORE_DIRS = {".git", "__pycache__", ".venv", "node_modules", "dist", "build"}

ALLOWLIST_FILES = {
    "REPOSITORY_POLICY.md",
    "0001-approved-repository-strategy.md",
    "check_repo_policy.py",
    "apply_mvp1_stabilization.py",
}

def should_scan(path: Path) -> bool:
    if any(part in IGNORE_DIRS for part in path.parts):
        return False
    return path.is_file() and path.suffix in SCAN_EXTENSIONS

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Project root to scan")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    violations: list[str] = []

    for path in root.rglob("*"):
        if not should_scan(path):
            continue

        if path.name in ALLOWLIST_FILES:
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")

        for pattern in BANNED_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append(
                    f"{path.relative_to(root)} contains banned repo/category pattern: {pattern}"
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
