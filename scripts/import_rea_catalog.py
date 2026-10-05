#!/usr/bin/env python3
"""Import reviewed REA generated data without importing or executing donor code."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

SOURCE_COMMIT = "4c8dc39f439b5283b077c6aa47f262714d7c4bbd"
SOURCE_FILES = ("src/generatedMcpToolCatalog.ts", "docs/product-catalog.json", "package.json", "server.json", "LICENSE", "scripts/generate-mcp-tool-catalog.mjs", "src/server/toolRegistrationOptions.ts", "src/contracts/toolSchemaMetadata.ts", "src/catalogIdentity.ts", "src/contracts/toolEffects.ts")
DESTINATION = Path(__file__).resolve().parents[1] / "apps/api/app/services/rea_catalog"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def git(source: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(source), *args])


def generate(source: Path) -> tuple[bytes, bytes]:
    if git(source, "rev-parse", "HEAD").decode().strip() != SOURCE_COMMIT:
        raise ValueError("REA source is not the reviewed commit")
    # Check tracked state only; never traverse dependencies or execute donor scripts.
    if git(source, "status", "--porcelain", "--untracked-files=no"):
        raise ValueError("REA tracked source is dirty")
    files = {name: git(source, "show", f"{SOURCE_COMMIT}:{name}") for name in SOURCE_FILES}
    for name, expected in files.items():
        path = source / name
        if path.is_symlink() or path.read_bytes() != expected:
            raise ValueError(f"REA source bytes differ: {name}")
    match = re.search(r"const GENERATED_PAYLOAD_JSON =\s*('(?:[^'\\]|\\.)*');", files[SOURCE_FILES[0]].decode())
    if match is None:
        raise ValueError("generated catalog literal is missing")
    catalog = json.loads(ast.literal_eval(match.group(1)))["catalog"]
    if len(catalog) != 122 or len({tool["name"] for tool in catalog}) != 122:
        raise ValueError("reviewed 122-tool catalog is incomplete")
    catalog.sort(key=lambda tool: tool["name"])
    nodes: list[object] = []
    indices: dict[bytes, int] = {}

    def pack(value: object) -> list:
        if isinstance(value, dict):
            node = ["object", [[key, pack(item)] for key, item in sorted(value.items())]]
        elif isinstance(value, list):
            node = ["array", [pack(item) for item in value]]
        else:
            return ["value", value]
        key = canonical(node)
        if key not in indices:
            indices[key] = len(nodes)
            nodes.append(node)
        return ["ref", indices[key]]

    roots = [pack(tool) for tool in catalog]
    manifest = {
        "format": "aios-rea-catalog.v1",
        "source": {
            "repository": "https://github.com/morluto/rea.git",
            "commit": SOURCE_COMMIT,
            "files_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()},
            "package": json.loads(files["package.json"])["name"],
            "version": json.loads(files["package.json"])["version"],
            "upstream_declared_runtime_digests": json.loads(files["docs/product-catalog.json"])["runtime_catalog"]["digests"],
            "schema_projection": "generatedMcpToolCatalog SDK advertisement; not direct Zod runtime identity",
        },
        "tool_count": 122,
        "local_catalog_sha256": hashlib.sha256(canonical(catalog)).hexdigest(),
        "roots": roots,
        "nodes": nodes,
    }
    return canonical(manifest) + b"\n", files["LICENSE"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--check", action="store_true", help="compare bytes with checked-in snapshot")
    args = parser.parse_args()
    snapshot, license_text = generate(args.source.resolve())
    for name, data in (("catalog.json", snapshot), ("REA_LICENSE.txt", license_text)):
        destination = DESTINATION / name
        if args.check:
            if destination.read_bytes() != data:
                raise ValueError(f"checked-in {name} differs from reviewed import")
        else:
            destination.write_bytes(data)
    print(f"REA 122-tool snapshot SHA-256: {hashlib.sha256(snapshot).hexdigest()}")


if __name__ == "__main__":
    main()
