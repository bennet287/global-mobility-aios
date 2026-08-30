from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from labs.r3.common.harness import fingerprint


GIT_SHA = re.compile(r"^[a-f0-9]{40}$")


def verify_result(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8"))
    expected_fingerprint = result.pop("result_sha256", None)
    if not isinstance(expected_fingerprint, str):
        raise ValueError(f"{path}: missing result_sha256")
    observed_fingerprint = fingerprint(result)
    if observed_fingerprint != expected_fingerprint:
        raise ValueError(
            f"{path}: fingerprint mismatch; expected {expected_fingerprint}, "
            f"observed {observed_fingerprint}"
        )
    if result.get("unauthorized_canonical_effects") != 0:
        raise ValueError(f"{path}: unauthorized canonical effects are non-zero")
    if result.get("critical_failures", 0) != 0:
        raise ValueError(f"{path}: critical failures are non-zero")
    git_sha = result.get("git_sha")
    if git_sha is not None and not GIT_SHA.fullmatch(git_sha):
        raise ValueError(f"{path}: invalid git_sha {git_sha!r}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = args.paths or sorted(Path("labs/r3").glob("**/results/*.json"))
    if not paths:
        raise SystemExit("no R3 result artifacts found")
    for path in paths:
        verify_result(path)
        print(f"verified {path}")
    print(f"Verified {len(paths)} R3 result artifact(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
