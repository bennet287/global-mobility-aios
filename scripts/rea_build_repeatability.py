#!/usr/bin/env python3
"""Bounded CI byte evidence for REA source compilation; never execute REA outputs.

GitHub's job/run identity is supplied by the owning workflow, not authenticated by
this manifest. Acceptance requires inspecting that exact workflow's two builds
and comparison job. This is not publisher provenance or runtime admission.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import gzip
import io
import tarfile
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess

SOURCE_COMMIT = "4c8dc39f439b5283b077c6aa47f262714d7c4bbd"
SOURCE_TREE = "08978a8a18b4fd1a4a9b540c17f79feecbb94fcb"
MATERIALS_SHA256 = "a2215de5912f6f7a52573a3d450e75982afaa4c6a48a037894c8a94211bd1552"
REPOSITORY = "bennet287/global-mobility-aios"
MAX_FILES = 10000
MAX_ENTRIES = 20000
MAX_DEPTH = 32
MAX_BYTES = 128 * 1024 * 1024
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_JSON_BYTES = 4 * 1024 * 1024
MIN_OUTPUTS = {"main.js", "cli.js", "mcpDoctor.js", "cliOutput.js"}
MANIFEST_KEYS = {"format", "context", "job", "captured_at", "source", "toolchain", "recipe", "files"}


class EvidenceError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()


def parse_json(data: bytes) -> object:
    require(len(data) <= MAX_JSON_BYTES, "JSON bound exceeded")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    def constant(value):
        raise EvidenceError("nonfinite JSON")
    try:
        result = json.loads(data.decode("utf-8", errors="strict"), object_pairs_hook=pairs, parse_constant=constant)
        nodes = 0
        def visit(value, depth=0):
            nonlocal nodes
            nodes += 1
            require(nodes <= 100000 and depth <= 32, "JSON structural bound exceeded")
            if type(value) is float:
                require(math.isfinite(value), "nonfinite JSON number")
            elif isinstance(value, str):
                value.encode("utf-8", errors="strict")
            elif isinstance(value, dict):
                for k, v in value.items():
                    visit(k, depth + 1)
                    visit(v, depth + 1)
            elif isinstance(value, list):
                for v in value:
                    visit(v, depth + 1)
        visit(result)
        return result
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise EvidenceError("invalid JSON") from exc


def safe_path(value: str) -> str:
    require(type(value) is str and len(value.encode("utf-8")) <= 512, "invalid path")
    path = PurePosixPath(value)
    require(value and not path.is_absolute() and str(path) == value, "noncanonical path")
    require(all(part not in (".", "..", "") and not part.startswith(".") for part in path.parts), "unsafe path")
    require("\\" not in value and all(ord(c) >= 32 and ord(c) != 127 for c in value), "unsafe path")
    return value


def identity(info) -> tuple:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def read_regular(path: Path, limit: int = MAX_FILE_BYTES, *, dir_fd=None) -> bytes:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dir_fd)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= limit, "unsafe regular file")
        data = bytearray()
        while len(data) <= limit:
            chunk = os.read(fd, min(65536, limit + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        after = os.fstat(fd)
        require(len(data) == before.st_size and len(data) <= limit and identity(before) == identity(after), "file changed or oversized")
        return bytes(data)
    finally:
        os.close(fd)


def inventory(root: Path, *, source: bool = False) -> tuple[list[dict], dict[str, bytes]]:
    """Walk using directory FDs: no followed links, special files or empty dirs."""
    records, contents, seen = [], {}, set()
    total = 0
    entries = 0
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    def walk(fd, prefix, depth=0):
        nonlocal total, entries
        require(depth <= MAX_DEPTH, "directory depth bound exceeded")
        directory_before = os.fstat(fd)
        names = sorted(os.listdir(fd))
        require(names, "empty directory")
        for name in names:
            entries += 1
            require(entries <= MAX_ENTRIES, "directory entry bound exceeded")
            relative = f"{prefix}/{name}" if prefix else name
            if not source:
                safe_path(relative)
            before = os.stat(name, dir_fd=fd, follow_symlinks=False)
            if stat.S_ISDIR(before.st_mode):
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                try:
                    require((before.st_dev, before.st_ino) == (os.fstat(child).st_dev, os.fstat(child).st_ino), "directory changed")
                    walk(child, relative, depth + 1)
                finally:
                    os.close(child)
            else:
                require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, "nonregular or hardlinked output")
                require(source or not before.st_mode & 0o111, "executable output")
                require(before.st_size <= MAX_FILE_BYTES, "file bound exceeded")
                file_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
                try:
                    opened = os.fstat(file_fd)
                    require(identity(opened) == identity(before), "file changed")
                    content = bytearray()
                    while len(content) <= MAX_FILE_BYTES:
                        chunk = os.read(file_fd, min(65536, MAX_FILE_BYTES + 1 - len(content)))
                        if not chunk:
                            break
                        content.extend(chunk)
                    require(identity(os.fstat(file_fd)) == identity(before) and len(content) == before.st_size, "file changed or oversized")
                finally:
                    os.close(file_fd)
                require((before.st_dev, before.st_ino) not in seen, "duplicate inode")
                seen.add((before.st_dev, before.st_ino))
                total += len(content)
                require(total <= MAX_BYTES and len(records) < MAX_FILES, "tree bound exceeded")
                data = bytes(content)
                records.append({"path": relative, "size": len(data), "sha256": sha(data)})
                contents[relative] = data
        require(identity(os.fstat(fd)) == identity(directory_before) and sorted(os.listdir(fd)) == names, "directory changed")
    try:
        walk(root_fd, "")
    finally:
        os.close(root_fd)
    return sorted(records, key=lambda r: r["path"]), contents


def command(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, check=True, capture_output=True, timeout=30)
    require(len(result.stdout) <= MAX_JSON_BYTES, "command output bound")
    return result.stdout.decode("utf-8", errors="strict").strip()


def materials(path: Path) -> dict:
    raw = read_regular(path, MAX_JSON_BYTES)
    require(sha(raw) == MATERIALS_SHA256, "materials pin mismatch")
    value = parse_json(raw)
    require(type(value) is dict and value["source_commit"] == SOURCE_COMMIT and value["source_tree"] == SOURCE_TREE, "source pin mismatch")
    return value


def verify_source(root: Path, materials_path: Path) -> dict:
    value = materials(materials_path)
    git = lambda *args: command(["git", "-C", str(root), *args])
    require(git("rev-parse", "HEAD") == SOURCE_COMMIT and git("rev-parse", "HEAD^{tree}") == SOURCE_TREE, "git source mismatch")
    require(git("status", "--porcelain=v1", "--untracked-files=all") == "", "source checkout not clean")
    raw_tree = git("ls-tree", "-r", "--full-tree", "HEAD")
    expected = {r["path"]: r for r in value["files"]}
    tracked = {}
    for line in raw_tree.splitlines():
        metadata, path = line.split("\t", 1)
        mode, kind, _ = metadata.split(" ")
        require(kind == "blob" and mode in ("100644", "100755"), "unsafe source tree")
        tracked[path] = mode
    require(set(tracked) == set(expected) and len(tracked) == value["file_count"], "source tree completeness")
    total = 0
    for path, item in expected.items():
        # Pinned source paths include dotfiles; reject traversal, then open each
        # parent separately with O_NOFOLLOW so a swapped directory cannot redirect.
        require(not PurePosixPath(path).is_absolute() and ".." not in PurePosixPath(path).parts, "unsafe source path")
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            parts = PurePosixPath(path).parts
            for part in parts[:-1]:
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = next_fd
            file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
            try:
                before = os.fstat(file_fd)
                require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size == item["size"], "source file shape")
                require(tracked[path] == item["mode"] and bool(before.st_mode & 0o111) == (item["mode"] == "100755"), "source file mode")
                data = os.read(file_fd, item["size"] + 1)
                require(len(data) == item["size"] and sha(data) == item["sha256"] and identity(os.fstat(file_fd)) == identity(before), "source bytes mismatch")
                total += len(data)
            finally:
                os.close(file_fd)
        finally:
            os.close(fd)
    require(total == value["total_bytes"], "source aggregate mismatch")
    require(git("status", "--porcelain=v1", "--untracked-files=all") == "", "source changed")
    return {"commit": SOURCE_COMMIT, "tree": SOURCE_TREE, "materials_sha256": MATERIALS_SHA256,
            "dependency_lock_sha256": value["dependency_lock_sha256"], "reviewed_recipe_sha256": value["recipe_sha256"],
            "tracked_files": value["file_count"], "tracked_bytes": total}


def context(candidate: str, repository: str, run_id: str, run_attempt: str) -> dict:
    require(type(candidate) is str and re.fullmatch(r"[0-9a-f]{40}", candidate), "candidate SHA")
    require(repository == REPOSITORY, "repository mismatch")
    require(type(run_id) is str and re.fullmatch(r"[1-9][0-9]{0,19}", run_id), "run id")
    require(type(run_attempt) is str and re.fullmatch(r"[1-9][0-9]{0,5}", run_attempt), "run attempt")
    return {"candidate": candidate, "repository": repository, "run_id": run_id, "run_attempt": run_attempt, "runner": "ubuntu-24.04"}


def recipe(helper: Path, workflow: Path) -> dict:
    return {"helper_sha256": sha(read_regular(helper)), "workflow_sha256": sha(read_regular(workflow)),
            "command": "node node_modules/typescript/bin/tsc -p tsconfig.build.json", "lifecycle_scripts": False, "fresh_npm_cache": True}


def toolchain(root: Path, node: Path, npm_cli: Path) -> dict:
    node = node.resolve(strict=True)
    npm_cli = npm_cli.resolve(strict=True)
    ts_root = root / "node_modules/typescript"
    versions = {"node": command([str(node), "--version"]), "npm": command([str(node), str(npm_cli), "--version"]),
                "typescript": parse_json(read_regular(ts_root / "package.json"))["version"]}
    require(versions == {"node": "v24.18.0", "npm": "11.16.0", "typescript": "5.9.3"}, "toolchain version mismatch")
    # These identify observed compiler/tool entry bytes, not the entire installed
    # dependency closure or a publisher signature on these downloads.
    inputs = {"node": node, "npm_cli": npm_cli, "npm_package": npm_cli.parent.parent / "package.json",
              "typescript_package": ts_root / "package.json", "typescript_entry": ts_root / "bin/tsc",
              "typescript_tsc": ts_root / "lib/tsc.js", "typescript_compiler": ts_root / "lib/_tsc.js"}
    hashes = {key: sha(read_regular(path, MAX_BYTES)) for key, path in inputs.items()}
    return {"versions": versions, "input_sha256": hashes}


def capture(root: Path, output: Path, materials_path: Path, ctx: dict, job: str, tools: dict, recipe_value: dict) -> dict:
    require(job in ("a", "b") and not output.exists(), "output/job invalid")
    source = verify_source(root, materials_path)
    files, contents = inventory(root / "dist")
    require(MIN_OUTPUTS <= set(contents), "required outputs absent")
    manifest = {"format": "aios-rea-build-job.v1", "context": ctx, "job": job,
                "captured_at": datetime.now(timezone.utc).isoformat(), "source": source,
                "toolchain": tools, "recipe": recipe_value, "files": files}
    require(len(canonical(manifest)) <= MAX_JSON_BYTES, "manifest bound")
    output.mkdir(parents=True)
    for path, data in contents.items():
        target = output / "dist" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (output / "manifest.json").write_bytes(canonical(manifest))
    return manifest


def validate_toolchain(value: object) -> None:
    require(type(value) is dict and set(value) == {"versions", "input_sha256"}, "toolchain shape")
    require(canonical(value["versions"]) == canonical({"node": "v24.18.0", "npm": "11.16.0", "typescript": "5.9.3"}), "toolchain versions")
    hashes = value["input_sha256"]
    require(type(hashes) is dict and set(hashes) == {"node", "npm_cli", "npm_package", "typescript_package", "typescript_entry", "typescript_tsc", "typescript_compiler"}, "tool inputs")
    require(all(type(v) is str and re.fullmatch(r"[0-9a-f]{64}", v) for v in hashes.values()), "tool input hash")


def load_build(path: Path, ctx: dict, job: str, expected_source: dict, expected_recipe: dict) -> tuple[dict, dict]:
    files, contents = inventory(path)
    require("manifest.json" in contents, "manifest absent")
    value = parse_json(contents["manifest.json"])
    require(type(value) is dict and set(value) == MANIFEST_KEYS and value["format"] == "aios-rea-build-job.v1", "manifest shape")
    require(canonical(value["context"]) == canonical(ctx) and value["job"] == job, "stale or wrong job context")
    require(canonical(value["source"]) == canonical(expected_source), "source evidence mismatch")
    require(canonical(value["recipe"]) == canonical(expected_recipe), "recipe mismatch")
    validate_toolchain(value["toolchain"])
    try:
        require(type(value["captured_at"]) is str, "capture time type")
        captured = datetime.fromisoformat(value["captured_at"])
        require(captured.utcoffset() == timedelta(0), "capture time timezone")
        require(timedelta(0) <= datetime.now(timezone.utc) - captured <= timedelta(hours=2), "capture time stale/future")
    except (TypeError, ValueError) as exc:
        raise EvidenceError("capture time invalid") from exc
    actual = [{"path": r["path"][5:], "size": r["size"], "sha256": r["sha256"]} for r in files if r["path"].startswith("dist/")]
    require(all(r["path"] == "manifest.json" or r["path"].startswith("dist/") for r in files), "extra artifact file")
    require(canonical(value["files"]) == canonical(actual), "manifest/actual output mismatch")
    actual_contents = {p[5:]: data for p, data in contents.items() if p.startswith("dist/")}
    require(MIN_OUTPUTS <= set(actual_contents), "required outputs absent")
    return value, actual_contents


def compare(a: Path, b: Path, materials_path: Path, ctx: dict, recipe_value: dict) -> dict:
    value = materials(materials_path)
    source = {"commit": SOURCE_COMMIT, "tree": SOURCE_TREE, "materials_sha256": MATERIALS_SHA256,
              "dependency_lock_sha256": value["dependency_lock_sha256"], "reviewed_recipe_sha256": value["recipe_sha256"],
              "tracked_files": value["file_count"], "tracked_bytes": value["total_bytes"]}
    left, left_bytes = load_build(a, ctx, "a", source, recipe_value)
    right, right_bytes = load_build(b, ctx, "b", source, recipe_value)
    require(canonical(left["toolchain"]) == canonical(right["toolchain"]), "compiler/tool input drift")
    require(left_bytes == right_bytes and canonical(left["files"]) == canonical(right["files"]), "build outputs differ")
    return {"format": "aios-rea-build-repeatability.v1", "context": ctx, "source": source,
            "recipe": recipe_value, "toolchain": left["toolchain"], "files": left["files"],
            "received_manifest_sha256": {"a": sha(read_regular(a / "manifest.json")), "b": sha(read_regular(b / "manifest.json"))},
            "repeatability_observed": True, "source_compiler_recipe_context_observed": True,
            "publisher_provenance_verified": False, "runtime_dependency_closure_verified": False,
            "installed_runtime_bytes_verified": False, "isolation_verified": False,
            "provider_ready": False, "live_transport_owned": False, "execution_authorized": False}


def read_source_asset(root: Path, path: str) -> bytes:
    safe_path(path)
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        parts = PurePosixPath(path).parts
        for part in parts[:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return read_regular(Path(parts[-1]), dir_fd=fd)
    finally:
        os.close(fd)


def package(a: Path, b: Path, source: Path, materials_path: Path, ctx: dict, recipe_value: dict, output: Path) -> dict:
    """Assemble diagnostic bytes only, without npm pack or builder authority."""
    require(not output.exists(), "package output exists")
    report = compare(a, b, materials_path, ctx, recipe_value)
    verify_source(source, materials_path)
    snapshot = materials(materials_path)
    source_files = {v["path"]: v for v in snapshot["files"]}
    metadata = parse_json(read_source_asset(source, "package.json"))
    prefixes = metadata["files"]
    require(type(prefixes) is list and all(type(v) is str for v in prefixes), "package declarations invalid")
    required = {"package.json", "LICENSE", "README.md"}
    required.update(path for path in source_files if any(path == p or path.startswith(p + "/") for p in prefixes if p != "dist"))
    _, dist = load_build(a, ctx, "a", report["source"], recipe_value)
    contents = {"dist/" + path: data for path, data in dist.items()}
    for path in sorted(required):
        safe_path(path)
        # Complete source verification before and after these inert reads binds
        # the assets to the pinned tracked bytes; no build/generator runs here.
        data = read_source_asset(source, path)
        pin = source_files[path]
        require(len(data) == pin["size"] and sha(data) == pin["sha256"], "source asset drift")
        contents[path] = data
    require(len(contents) <= MAX_FILES and sum(map(len, contents.values())) <= MAX_BYTES, "package bounds")
    require(len({p.casefold() for p in contents}) == len(contents), "package path collision")
    raw_tar = io.BytesIO()
    with tarfile.open(fileobj=raw_tar, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for path, data in sorted(contents.items()):
            member = tarfile.TarInfo("package/" + path)
            member.size = len(data)
            member.mode = 0o644
            member.mtime = member.uid = member.gid = 0
            archive.addfile(member, io.BytesIO(data))
    raw = gzip.compress(raw_tar.getvalue(), mtime=0)
    verify_source(source, materials_path)
    manifest = [{"path": p, "size": len(v), "sha256": sha(v)} for p, v in sorted(contents.items())]
    result = {"format": "aios-rea-package-correlation.v1", "repeatability": report,
              "package": {"archive_sha256": sha(raw), "archive_bytes": len(raw), "files": manifest},
              "diagnostic_only": True}
    require(len(canonical(result)) <= MAX_JSON_BYTES, "package report bound")
    output.mkdir(parents=True)
    (output / "rea-package.tar.gz").write_bytes(raw)
    (output / "correlation.json").write_bytes(canonical(result))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("verify-source", "capture", "compare", "package"))
    parser.add_argument("--source", type=Path)
    parser.add_argument("--materials", type=Path, required=True)
    parser.add_argument("--candidate")
    parser.add_argument("--repository", default=REPOSITORY)
    parser.add_argument("--run-id")
    parser.add_argument("--run-attempt")
    parser.add_argument("--job", choices=("a", "b"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--a", type=Path)
    parser.add_argument("--b", type=Path)
    parser.add_argument("--node", type=Path)
    parser.add_argument("--npm-cli", type=Path)
    parser.add_argument("--workflow", type=Path)
    args = parser.parse_args()
    try:
        needed = {"verify-source": ("source",), "capture": ("source", "candidate", "run_id", "run_attempt", "job", "output", "node", "npm_cli", "workflow"), "compare": ("candidate", "run_id", "run_attempt", "a", "b", "output", "workflow"), "package": ("source", "candidate", "run_id", "run_attempt", "a", "b", "output", "workflow")}[args.operation]
        require(all(getattr(args, field) is not None for field in needed), "required operation argument missing")
        if args.operation == "verify-source":
            result = verify_source(args.source, args.materials)
        else:
            ctx = context(args.candidate, args.repository, args.run_id, args.run_attempt)
            require(command(["git", "-C", str(Path(__file__).resolve().parent.parent), "rev-parse", "HEAD"]) == ctx["candidate"], "AIOS checkout candidate mismatch")
            recipe_value = recipe(Path(__file__), args.workflow)
            if args.operation == "capture":
                result = capture(args.source, args.output, args.materials, ctx, args.job,
                                 toolchain(args.source, args.node, args.npm_cli), recipe_value)
            elif args.operation == "package":
                result = package(args.a, args.b, args.source, args.materials, ctx, recipe_value, args.output)
            else:
                result = compare(args.a, args.b, args.materials, ctx, recipe_value)
                require(not args.output.exists(), "comparison output exists")
                args.output.write_bytes(canonical(result))
        print(json.dumps({"operation": args.operation, "success": True, "files": len(result.get("files", []))}))
    except (EvidenceError, OSError, subprocess.SubprocessError, KeyError, TypeError) as exc:
        parser.exit(1, f"REA build evidence rejected: {exc}\n")


if __name__ == "__main__":
    main()
