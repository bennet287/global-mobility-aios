#!/usr/bin/env python3
"""Commit to reviewed REA source bytes without importing or executing donor code."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

SOURCE_COMMIT = "4c8dc39f439b5283b077c6aa47f262714d7c4bbd"
DESTINATION = Path(__file__).resolve().parents[1] / "apps/api/app/services/rea_catalog/build_materials.json"
RECIPE_FILES = ("package.json", "package-lock.json", ".nvmrc", "tsconfig.json", "tsconfig.build.json", "turbo.json",
                "scripts/prepack.mjs", "scripts/prepare.mjs", "scripts/check-dependency-install.mjs",
                "scripts/clean-build-output.mjs", "scripts/generate-package-metadata.mjs",
                "scripts/lib/generated-file.mjs", ".github/workflows/release.yml")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def git(source: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null", "-C", str(source), *args], timeout=10)


def generate(source: Path) -> bytes:
    started = time.monotonic()
    if git(source, "rev-parse", "HEAD").decode().strip() != SOURCE_COMMIT:
        raise ValueError("REA checkout is not the reviewed source commit")
    if git(source, "status", "--porcelain", "--untracked-files=no"):
        raise ValueError("REA tracked source is dirty")
    entries = git(source, "ls-tree", "-rz", SOURCE_COMMIT).split(b"\0")
    if len(entries) > 5001:
        raise ValueError("source file count exceeds bounds")
    files, total = [], 0
    for entry in entries:
        if time.monotonic() - started > 120:
            raise ValueError("source inspection deadline exceeded")
        if not entry:
            continue
        header, raw_path = entry.split(b"\t", 1)
        mode, kind, blob = header.decode().split()
        path = raw_path.decode("utf-8")
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError("reviewed source includes non-regular material")
        data = git(source, "cat-file", "blob", blob)
        total += len(data)
        if len(data) > 16 * 1024 * 1024 or total > 64 * 1024 * 1024:
            raise ValueError("source bytes exceed bounds")
        files.append({"path": path, "mode": mode, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    files.sort(key=lambda item: item["path"])
    by_path = {item["path"]: item for item in files}
    recipe = [by_path[path] for path in sorted(RECIPE_FILES)]
    package = json.loads(git(source, "show", f"{SOURCE_COMMIT}:package.json"))
    if (package["name"], package["version"]) != ("rea-agents", "3.2.1"):
        raise ValueError("reviewed package identity differs")
    result = {"format": "aios-rea-build-materials.v1", "repository": "https://github.com/morluto/rea.git",
              "source_commit": SOURCE_COMMIT, "source_tree": git(source, "rev-parse", f"{SOURCE_COMMIT}^{{tree}}").decode().strip(),
              "package_name": package["name"], "package_version": package["version"], "files": files,
              "file_count": len(files), "total_bytes": total, "recipe_sha256": hashlib.sha256(canonical(recipe)).hexdigest(),
              "dependency_lock_sha256": by_path["package-lock.json"]["sha256"]}
    return canonical(result) + b"\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = generate(args.source)
    if args.check:
        if DESTINATION.read_bytes() != data:
            raise ValueError("checked-in source materials differ from reviewed commit")
    else:
        DESTINATION.write_bytes(data)
    print("REA reviewed source-material commitment SHA-256:", hashlib.sha256(data).hexdigest())


if __name__ == "__main__":
    main()
