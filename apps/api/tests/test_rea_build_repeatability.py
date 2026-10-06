"""Synthetic byte fixtures, not a local REA build or provider invocation."""
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("rea_build_repeatability", ROOT / "scripts/rea_build_repeatability.py")
proof = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(proof)
MATERIALS = ROOT / "apps/api/app/services/rea_catalog/build_materials.json"


def source_record():
    value = proof.materials(MATERIALS)
    return {"commit": proof.SOURCE_COMMIT, "tree": proof.SOURCE_TREE,
            "materials_sha256": proof.MATERIALS_SHA256,
            "dependency_lock_sha256": value["dependency_lock_sha256"],
            "reviewed_recipe_sha256": value["recipe_sha256"],
            "tracked_files": value["file_count"], "tracked_bytes": value["total_bytes"]}


@pytest.fixture
def builds(tmp_path, monkeypatch):
    ctx = proof.context("a" * 40, proof.REPOSITORY, "123", "1")
    recipe = proof.recipe(ROOT / "scripts/rea_build_repeatability.py", ROOT / ".github/workflows/rea-build-repeatability.yml")
    keys = ["node", "npm_cli", "npm_package", "typescript_package", "typescript_entry", "typescript_tsc", "typescript_compiler"]
    tools = {"versions": {"node": "v24.18.0", "npm": "11.16.0", "typescript": "5.9.3"},
             "input_sha256": {key: "b" * 64 for key in keys}}
    monkeypatch.setattr(proof, "verify_source", lambda *args: source_record())
    source = tmp_path / "source"
    dist = source / "dist"
    dist.mkdir(parents=True)
    for name in proof.MIN_OUTPUTS:
        (dist / name).write_bytes(b"synthetic compiled bytes, never imported")
    (dist / "nested").mkdir()
    (dist / "nested/value.js").write_bytes(b"nested fixture")
    a, b = tmp_path / "a", tmp_path / "b"
    proof.capture(source, a, MATERIALS, ctx, "a", tools, recipe)
    proof.capture(source, b, MATERIALS, ctx, "b", tools, recipe)
    return a, b, ctx, recipe


def edit_manifest(path, change):
    manifest = json.loads((path / "manifest.json").read_bytes())
    change(manifest)
    (path / "manifest.json").write_bytes(proof.canonical(manifest))


def test_complete_actual_bytes_positive_and_authority_false(builds):
    a, b, ctx, recipe = builds
    result = proof.compare(a, b, MATERIALS, ctx, recipe)
    assert result["repeatability_observed"] is True
    assert len(result["files"]) == 5
    assert set(result["received_manifest_sha256"]) == {"a", "b"}
    for key in ("publisher_provenance_verified", "runtime_dependency_closure_verified", "installed_runtime_bytes_verified",
                "isolation_verified", "provider_ready", "live_transport_owned", "execution_authorized"):
        assert result[key] is False


@pytest.mark.parametrize("mutation", [
    lambda m: m["context"].update(candidate="c" * 40),
    lambda m: m["context"].update(run_id="999"),
    lambda m: m["context"].update(run_attempt="2"),
    lambda m: m["context"].update(repository="other/repository"),
    lambda m: m["context"].update(runner="self-hosted"),
    lambda m: m.update(job="a"),
    lambda m: m["source"].update(commit="d" * 40),
    lambda m: m["source"].update(tracked_files=True),
    lambda m: m["recipe"].update(lifecycle_scripts=True),
    lambda m: m["recipe"].update(fresh_npm_cache=1),
    lambda m: m["recipe"].update(helper_sha256="f" * 64),
    lambda m: m["toolchain"]["versions"].update(typescript="5.9.2"),
    lambda m: m["toolchain"]["input_sha256"].update(node="f" * 64),
    lambda m: m["toolchain"]["input_sha256"].update(node=True),
    lambda m: m["toolchain"].update(unexpected=True),
    lambda m: m.update(format="other"),
    lambda m: m.update(unexpected=True),
    lambda m: m.update(captured_at=(datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()),
    lambda m: m.update(captured_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()),
    lambda m: m.update(captured_at=datetime.now().isoformat()),
    lambda m: m.update(captured_at=True),
    lambda m: m["files"][0].update(size=True),
    lambda m: m["files"].pop(),
    lambda m: m["files"].append(dict(m["files"][0])),
    lambda m: m["files"][0].update(path="../escape"),
])
def test_manifest_schema_context_and_claim_drift_denied(builds, mutation):
    a, b, ctx, recipe = builds
    edit_manifest(b, mutation)
    with pytest.raises(proof.EvidenceError):
        proof.compare(a, b, MATERIALS, ctx, recipe)


@pytest.mark.parametrize("mutation", ["change", "missing", "extra", "empty-dir", "symlink-file", "symlink-dir", "hardlink", "fifo", "executable", "hidden"])
def test_actual_output_safety_and_completeness(builds, mutation):
    a, b, ctx, recipe = builds
    target = b / "dist/main.js"
    if mutation == "change":
        target.write_bytes(b"tampered")
    elif mutation == "missing":
        target.unlink()
    elif mutation == "extra":
        (b / "extra.txt").write_bytes(b"extra")
    elif mutation == "empty-dir":
        (b / "dist/empty").mkdir()
    elif mutation == "symlink-file":
        target.unlink()
        target.symlink_to(a / "dist/main.js")
    elif mutation == "symlink-dir":
        (b / "dist/link").symlink_to(a / "dist/nested", target_is_directory=True)
    elif mutation == "hardlink":
        target.unlink()
        os.link(a / "dist/main.js", target)
    elif mutation == "fifo":
        target.unlink()
        os.mkfifo(target)
    elif mutation == "executable":
        target.chmod(0o755)
    else:
        (b / "dist/.hidden").write_bytes(b"ignored by upload would be a defect")
    with pytest.raises((proof.EvidenceError, OSError)):
        proof.compare(a, b, MATERIALS, ctx, recipe)


def test_equal_manifest_claims_cannot_hide_changed_actual_bytes(builds):
    a, b, ctx, recipe = builds
    (a / "dist/main.js").write_bytes(b"different byte")
    (b / "dist/main.js").write_bytes(b"different byte")
    with pytest.raises(proof.EvidenceError, match="manifest/actual"):
        proof.compare(a, b, MATERIALS, ctx, recipe)


def test_both_updated_manifests_but_different_actual_outputs_denied(builds):
    a, b, ctx, recipe = builds
    (b / "dist/main.js").write_bytes(b"different byte")
    actual, _ = proof.inventory(b / "dist")
    edit_manifest(b, lambda m: m.update(files=actual))
    with pytest.raises(proof.EvidenceError, match="outputs differ"):
        proof.compare(a, b, MATERIALS, ctx, recipe)


@pytest.mark.parametrize("data", [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}', b'{"a":1e400}', b'"\\ud800"', b'\xff', b'{' ])
def test_raw_json_strict(data):
    with pytest.raises(proof.EvidenceError):
        proof.parse_json(data)


def test_json_bounds(monkeypatch):
    monkeypatch.setattr(proof, "MAX_JSON_BYTES", 20)
    with pytest.raises(proof.EvidenceError):
        proof.parse_json(b'"' + b'a' * 20 + b'"')
    monkeypatch.setattr(proof, "MAX_JSON_BYTES", 10000)
    with pytest.raises(proof.EvidenceError):
        proof.parse_json(b'[' * 40 + b'0' + b']' * 40)


@pytest.mark.parametrize("field,value", [("candidate", "abc"), ("candidate", "A" * 40), ("repository", "other/repo"),
                                         ("run_id", "0"), ("run_id", 1), ("run_attempt", "01")])
def test_context_strict(field, value):
    args = dict(candidate="a" * 40, repository=proof.REPOSITORY, run_id="123", run_attempt="1")
    args[field] = value
    with pytest.raises(proof.EvidenceError):
        proof.context(**args)


@pytest.mark.parametrize("limit", ["MAX_FILES", "MAX_BYTES", "MAX_FILE_BYTES"])
def test_actual_tree_bounds(builds, monkeypatch, limit):
    a, b, ctx, recipe = builds
    monkeypatch.setattr(proof, limit, 1)
    with pytest.raises(proof.EvidenceError):
        proof.compare(a, b, MATERIALS, ctx, recipe)


def test_required_outputs_even_when_manifests_match(builds):
    a, b, ctx, recipe = builds
    for path in (a, b):
        (path / "dist/main.js").unlink()
        records, _ = proof.inventory(path / "dist")
        edit_manifest(path, lambda m: m.update(files=records))
    with pytest.raises(proof.EvidenceError, match="required outputs"):
        proof.compare(a, b, MATERIALS, ctx, recipe)


@pytest.fixture
def git_source(tmp_path, monkeypatch):
    root = tmp_path / "donor"
    root.mkdir()
    (root / "src").mkdir()
    (root / "src/main.ts").write_bytes(b"synthetic source")
    (root / ".gitignore").write_bytes(b"dist/\nnode_modules/\n.cache/\n")
    (root / "build.sh").write_bytes(b"inert text")
    (root / "build.sh").chmod(0o755)
    subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.test", "commit", "-m", "fixture"], check=True, capture_output=True)
    commit = proof.command(["git", "-C", str(root), "rev-parse", "HEAD"])
    tree = proof.command(["git", "-C", str(root), "rev-parse", "HEAD^{tree}"])
    files = [{"path": name, "size": (root / name).stat().st_size, "sha256": proof.sha((root / name).read_bytes()),
              "mode": "100755" if name == "build.sh" else "100644"} for name in (".gitignore", "src/main.ts", "build.sh")]
    value = {"files": files, "file_count": 3, "total_bytes": sum(f["size"] for f in files),
             "dependency_lock_sha256": "a" * 64, "recipe_sha256": "b" * 64}
    monkeypatch.setattr(proof, "SOURCE_COMMIT", commit)
    monkeypatch.setattr(proof, "SOURCE_TREE", tree)
    monkeypatch.setattr(proof, "materials", lambda _: value)
    return root


def test_all_source_bytes_positive_before_and_after_ignored_output(git_source):
    first = proof.verify_source(git_source, MATERIALS)
    (git_source / "dist").mkdir()
    (git_source / "dist/main.js").write_bytes(b"synthetic compilation output")
    assert proof.verify_source(git_source, MATERIALS) == first


@pytest.mark.parametrize("mutation", ["tracked", "untracked", "mode", "symlink-parent", "hardlink"])
def test_source_byte_mode_and_parent_integrity(git_source, mutation):
    target = git_source / "src/main.ts"
    if mutation == "tracked":
        target.write_bytes(b"changed")
    elif mutation == "untracked":
        (git_source / "extra").write_bytes(b"extra")
    elif mutation == "mode":
        (git_source / "build.sh").chmod(0o644)
    elif mutation == "symlink-parent":
        moved = git_source / "elsewhere"
        (git_source / "src").rename(moved)
        (git_source / "src").symlink_to(moved, target_is_directory=True)
    else:
        os.link(target, git_source / "other-link")
    with pytest.raises((proof.EvidenceError, OSError)):
        proof.verify_source(git_source, MATERIALS)


def test_materials_digest_pin(tmp_path):
    altered = tmp_path / "materials.json"
    altered.write_bytes(MATERIALS.read_bytes() + b" ")
    with pytest.raises(proof.EvidenceError, match="materials pin"):
        proof.materials(altered)


def test_workflow_is_fresh_bounded_no_runtime_authority():
    import yaml
    workflow = (ROOT / ".github/workflows/rea-build-repeatability.yml").read_text()
    jobs = yaml.safe_load(workflow)["jobs"]
    assert jobs["compare"]["needs"] == ["source-build-a", "source-build-b"]
    runner_jobs = [jobs["compare"], jobs["verify-attestation"]]
    assert all(job["timeout-minutes"] == 10 for job in runner_jobs)
    for lane in ("a", "b"):
        caller = jobs[f"source-build-{lane}"]
        assert caller["uses"] == f"./.github/workflows/rea-source-build-{lane}.yml"
        assert "with" not in caller and "secrets" not in caller
        reusable = (ROOT / f".github/workflows/rea-source-build-{lane}.yml").read_text()
        compile_job = yaml.safe_load(reusable)["jobs"]["compile"]
        assert compile_job["timeout-minutes"] == 15
        runner_jobs.append(compile_job)
        assert "--ignore-scripts --no-audit --no-fund" in reusable
        assert "node node_modules/typescript/bin/tsc -p tsconfig.build.json" in reusable
        assert "npm run" not in reusable and "pull_request_target" not in reusable
        assert "cache: npm" not in reusable and "actions/cache" not in reusable
        assert "rea mcp" not in reusable and "node dist/" not in reusable
    assert all(job["runs-on"] == "ubuntu-24.04" for job in runner_jobs)
    checkouts = [step for job in runner_jobs for step in job["steps"]
                 if step.get("uses", "").startswith("actions/checkout@")]
    assert checkouts and all(step["with"]["persist-credentials"] is False for step in checkouts)


@pytest.mark.parametrize("limit", ["MAX_ENTRIES", "MAX_DEPTH"])
def test_directory_bounds_include_nonfiles(builds, monkeypatch, limit):
    a, b, ctx, recipe = builds
    monkeypatch.setattr(proof, limit, 0)
    with pytest.raises(proof.EvidenceError, match="bound"):
        proof.compare(a, b, MATERIALS, ctx, recipe)


def test_directory_changes_during_inventory_denied(tmp_path, monkeypatch):
    root = tmp_path / "tree"
    root.mkdir()
    (root / "one.js").write_bytes(b"one")
    original = proof.os.listdir
    calls = 0
    def changed(fd):
        nonlocal calls
        calls += 1
        if calls == 2:
            (root / "new.js").write_bytes(b"added during snapshot")
        return original(fd)
    monkeypatch.setattr(proof.os, "listdir", changed)
    with pytest.raises(proof.EvidenceError, match="directory changed"):
        proof.inventory(root)


@pytest.fixture
def package_assets(builds, tmp_path, monkeypatch):
    root=tmp_path/'assets';root.mkdir()
    bodies={'package.json':proof.canonical({'name':'rea-agents','version':'3.2.1','files':['dist','scripts'],'bin':{'rea':'scripts/rea.mjs','rea-agents':'scripts/rea.mjs'}}),
            'LICENSE':b'synthetic license','README.md':b'synthetic readme','scripts/rea.mjs':b'synthetic source asset never run'}
    for path,data in bodies.items():
        target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    actual_materials=proof.materials(MATERIALS)
    fixture_materials={**actual_materials,'files':[dict(path=p,size=len(v),sha256=proof.sha(v)) for p,v in sorted(bodies.items())]}
    monkeypatch.setattr(proof,'materials',lambda _:fixture_materials)
    return root


def test_package_contains_complete_actual_outputs_and_assets(builds,package_assets,tmp_path):
    import gzip
    import io
    import tarfile
    a,b,ctx,recipe=builds
    report=proof.package(a,b,package_assets,MATERIALS,ctx,recipe,tmp_path/'package-one')
    raw=(tmp_path/'package-one/rea-package.tar.gz').read_bytes()
    assert proof.sha(raw)==report['package']['archive_sha256']
    assert len(raw)==report['package']['archive_bytes']
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
        observed={v.name.removeprefix('package/'):archive.extractfile(v).read() for v in archive}
    assert len(observed)==9
    assert observed['dist/nested/value.js']==(a/'dist/nested/value.js').read_bytes()
    assert {'package.json','LICENSE','README.md','scripts/rea.mjs'} <= set(observed)
    assert report['package']['files']==[dict(path=p,size=len(v),sha256=proof.sha(v)) for p,v in sorted(observed.items())]
    assert report['diagnostic_only'] is True
    assert report['repeatability']['execution_authorized'] is False
    assert gzip.decompress(raw)[257:265]==b'ustar\x0000'
    from app.services import organization_rea_build as package_inspector
    parsed,metadata=package_inspector._archive_manifest(raw)
    assert parsed==report['package']['files']
    package_inspector._verify_source_assets(parsed,metadata,{v['path']:v for v in proof.materials(MATERIALS)['files']})
    second=proof.package(a,b,package_assets,MATERIALS,ctx,recipe,tmp_path/'package-two')
    assert (tmp_path/'package-two/rea-package.tar.gz').read_bytes()==raw
    assert second==report


@pytest.mark.parametrize('mutation',['tamper','missing','symlink-parent'])
def test_package_source_asset_changes_denied(builds,package_assets,tmp_path,mutation):
    a,b,ctx,recipe=builds
    if mutation=='tamper':(package_assets/'LICENSE').write_bytes(b'drift')
    elif mutation=='missing':(package_assets/'README.md').unlink()
    else:
        moved=tmp_path/'moved';(package_assets/'scripts').rename(moved)
        (package_assets/'scripts').symlink_to(moved,target_is_directory=True)
    with pytest.raises((proof.EvidenceError,OSError)):
        proof.package(a,b,package_assets,MATERIALS,ctx,recipe,tmp_path/'package')
    assert not (tmp_path/'package').exists()
