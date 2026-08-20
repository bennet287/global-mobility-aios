#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

REQUIREMENTS = Path("apps/api/requirements.txt")
CONSTRAINTS = Path("apps/api/constraints.txt")
NAME = re.compile(r"^([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?")
EXACT_CONSTRAINT = re.compile(
    r"^[A-Za-z0-9_.-]+(?:\[[^\]]+\])?==[^\s;<>!=~@]+$"
)


def normalized_name(line: str) -> str:
    match = NAME.match(line.strip())
    if match is None:
        raise ValueError(f"Unsupported dependency declaration: {line!r}")
    return re.sub(r"[-_.]+", "-", match.group(1)).lower()


def dependency_lines(path: Path) -> list[str]:
    result: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        value = raw.split("#", 1)[0].strip()
        if value:
            result.append(value)
    return result


def main() -> int:
    requirements = dependency_lines(REQUIREMENTS)
    constraints = dependency_lines(CONSTRAINTS)
    constraint_by_name = {normalized_name(line): line for line in constraints}
    violations: list[str] = []

    if len(constraint_by_name) != len(constraints):
        violations.append("constraints.txt contains duplicate dependency names")

    requirement_names = [normalized_name(line) for line in requirements]
    if len(set(requirement_names)) != len(requirement_names):
        violations.append("requirements.txt contains duplicate dependency names")

    for requirement in requirements:
        name = normalized_name(requirement)
        constraint = constraint_by_name.get(name)
        if constraint is None:
            violations.append(f"missing exact constraint for {name}")
        elif EXACT_CONSTRAINT.fullmatch(constraint) is None:
            violations.append(
                f"constraint for {name} must be one unconditional exact == pin: {constraint!r}"
            )

    for name in sorted(set(constraint_by_name) - set(requirement_names)):
        violations.append(f"orphaned direct constraint: {name}")

    if violations:
        print("Python dependency constraint violations detected:")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print(f"Python dependency constraints passed for {len(requirements)} direct dependencies.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
