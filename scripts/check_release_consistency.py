#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any


REVISION_RE = re.compile(r"\*\*Code migration head:\*\*\s*`([^`]+)`")
MARKER_RE = re.compile(r"<!--\s*CURRENT_MIGRATION_HEAD:\s*([^\s]+)\s*-->")
README_NEXT_RE = re.compile(r"^- Next\.js\s+([^\s]+)\s*$", re.MULTILINE)


def _literal_assignment(tree: ast.Module, name: str) -> Any:
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        return ast.literal_eval(node.value)
    raise ValueError(f"Migration is missing {name!r}")


def migration_graph(versions_dir: Path) -> tuple[set[str], set[str]]:
    revisions: set[str] = set()
    parents: set[str] = set()
    for path in sorted(versions_dir.glob("*.py")):
        if path.name.startswith("__"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        revision = _literal_assignment(tree, "revision")
        down_revision = _literal_assignment(tree, "down_revision")
        if not isinstance(revision, str) or not revision:
            raise ValueError(f"{path}: revision must be a non-empty string")
        if revision in revisions:
            raise ValueError(f"Duplicate Alembic revision: {revision}")
        revisions.add(revision)
        if isinstance(down_revision, str):
            parents.add(down_revision)
        elif isinstance(down_revision, (tuple, list)):
            parents.update(item for item in down_revision if isinstance(item, str))
        elif down_revision is not None:
            raise ValueError(f"{path}: unsupported down_revision value {down_revision!r}")
    return revisions, parents


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    versions_dir = root / "apps" / "api" / "alembic" / "versions"
    roadmap = root / "docs" / "ROADMAP.md"
    readme = root / "README.md"
    web_package = root / "apps" / "web" / "package.json"

    revisions, parents = migration_graph(versions_dir)
    unknown_parents = sorted(parents - revisions)
    if unknown_parents:
        print("Release consistency check failed: unknown Alembic parent revisions:")
        for revision in unknown_parents:
            print(f"- {revision}")
        return 1

    heads = sorted(revisions - parents)
    if len(heads) != 1:
        print(f"Release consistency check failed: expected one Alembic head, found {heads}")
        return 1
    head = heads[0]

    text = roadmap.read_text(encoding="utf-8")
    visible = REVISION_RE.search(text)
    marker = MARKER_RE.search(text)
    failures: list[str] = []
    if visible is None:
        failures.append("ROADMAP.md is missing the '**Code migration head:**' field")
    elif visible.group(1) != head:
        failures.append(f"ROADMAP visible migration head is {visible.group(1)!r}, expected {head!r}")
    if marker is None:
        failures.append("ROADMAP.md is missing <!-- CURRENT_MIGRATION_HEAD: ... -->")
    elif marker.group(1) != head:
        failures.append(f"ROADMAP machine migration marker is {marker.group(1)!r}, expected {head!r}")

    package = json.loads(web_package.read_text(encoding="utf-8"))
    next_version = str(package.get("dependencies", {}).get("next", "")).strip()
    readme_text = readme.read_text(encoding="utf-8")
    readme_next = README_NEXT_RE.search(readme_text)
    if not next_version:
        failures.append("apps/web/package.json is missing dependencies.next")
    if readme_next is None:
        failures.append("README.md is missing the Web stack Next.js version line")
    elif next_version and readme_next.group(1) != next_version:
        failures.append(
            f"README Next.js version is {readme_next.group(1)!r}, expected package.json {next_version!r}"
        )

    if failures:
        print("Release consistency check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Release consistency check passed. Alembic head: {head}; Next.js: {next_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
