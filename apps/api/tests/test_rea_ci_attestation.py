"""Synthetic policy/IO fixtures, never a claim of real signature verification."""
from copy import deepcopy
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import time

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    SPEC = importlib.util.spec_from_file_location("rea_ci_attestation", ROOT / "scripts/rea_ci_attestation.py")
    proof = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(proof)
finally:
    sys.path.pop(0)


def expected():
    return proof.expected_identity(candidate="a" * 40, run_id="123", run_attempt="2", source_sha="b" * 40,
                                   workflow_sha="c" * 40, source_ref="refs/pull/318/merge", trigger="pull_request")


def verified(subject=b"report"):
    cert = {k: v for k, v in expected().items() if k != "context"}
    return [{"verificationResult": {"signature": {"certificate": cert},
            "verifiedTimestamps": [{"type": "Tlog", "uri": "https://rekor.sigstore.dev", "timestamp": "2026-01-01T00:00:00Z"}],
            "statement": {"_type": "https://in-toto.io/Statement/v1", "predicateType": "https://slsa.dev/provenance/v1",
                          "subject": [{"name": "correlation.json", "digest": {"sha256": proof.sha(subject)}}],
                          "predicate": {"run_id": "attacker-controlled", "metadata": {"invocationId": "made up"}}}}}]


def test_verified_certificate_not_predicate_owns_identity():
    value = verified()
    result = proof.validate_result(proof.canonical(value), b"report", expected())
    assert result["certificate"]["runInvocationURI"].endswith("/runs/123/attempts/2")
    assert result["certificate"]["sourceRepositoryDigest"] != expected()["context"]["candidate"]
    assert result["certificate"]["subjectAlternativeName"] == expected()["buildSignerURI"]


@pytest.mark.parametrize("field", [k for k in expected() if k != "context"])
@pytest.mark.parametrize("change", ["missing", "wrong"])
def test_every_authenticated_identity_field_required(field, change):
    value = verified()
    cert = value[0]["verificationResult"]["signature"]["certificate"]
    if change == "missing":
        del cert[field]
    else:
        cert[field] = "forged"
    # Matching predicate fields cannot replace a missing/wrong certificate field.
    value[0]["verificationResult"]["statement"]["predicate"] = expected()
    with pytest.raises(proof.EvidenceError, match="certificate"):
        proof.validate_result(proof.canonical(value), b"report", expected())


@pytest.mark.parametrize("mutate", [
    lambda v: v.append(deepcopy(v[0])),
    lambda v: v[0]["verificationResult"].update(verifiedTimestamps=[]),
    lambda v: v[0]["verificationResult"].update(verifiedTimestamps=[{"type": "CurrentTime", "timestamp": "2026-01-01T00:00:00Z"}]),
    lambda v: v[0]["verificationResult"].update(verifiedTimestamps=[{"type": "Tlog", "timestamp": "2999-01-01T00:00:00Z"}]),
    lambda v: v[0]["verificationResult"].update(verifiedTimestamps=[{"type": "Tlog", "timestamp": "2026-01-01"}]),
    lambda v: v[0]["verificationResult"]["statement"].update(predicateType="custom"),
    lambda v: v[0]["verificationResult"]["statement"].update(subject=[{"name": "correlation.json", "digest": {"sha256": "0" * 64}}]),
    lambda v: v[0]["verificationResult"]["statement"].update(subject=[{"name": "other.json", "digest": {"sha256": proof.sha(b"report")}}]),
])
def test_statement_witness_and_subject_negatives(mutate):
    value = verified()
    mutate(value)
    with pytest.raises(proof.EvidenceError):
        proof.validate_result(proof.canonical(value), b"report", expected())


def test_strict_fresh_json():
    with pytest.raises(proof.EvidenceError):
        proof.validate_result(b'{"same":1,"same":2}', b"report", expected())


@pytest.mark.parametrize("change", [
    {"source_sha": "bad"}, {"workflow_sha": "bad"}, {"trigger": "pull_request_target"},
    {"source_ref": "refs/heads/main"}, {"source_ref": "refs/pull/0/merge"}, {"run_attempt": "0"},
])
def test_context_never_falls_back(change):
    args = {"candidate": "a" * 40, "run_id": "123", "run_attempt": "2", "source_sha": "b" * 40,
            "workflow_sha": "c" * 40, "source_ref": "refs/pull/318/merge", "trigger": "pull_request"}
    args.update(change)
    with pytest.raises(proof.EvidenceError):
        proof.expected_identity(**args)


def test_dispatch_explicit_source_identity():
    value = proof.expected_identity(candidate="a" * 40, run_id="123", run_attempt="2", source_sha="a" * 40,
                                    workflow_sha="a" * 40, source_ref="refs/heads/main", trigger="workflow_dispatch")
    assert value["buildTrigger"] == "workflow_dispatch"


@pytest.mark.parametrize("kind", ["symlink", "parent_symlink", "hardlink", "oversized"])
def test_snapshot_denies_unsafe_input(tmp_path, kind):
    original = tmp_path / "original"
    original.write_bytes(b"raw")
    target = original
    if kind == "symlink":
        target = tmp_path / "link"
        target.symlink_to(original)
    elif kind == "parent_symlink":
        target = tmp_path / "dirlink" / "original"
        target.parent.symlink_to(tmp_path, target_is_directory=True)
    elif kind == "hardlink":
        os.link(original, tmp_path / "hardlink")
    with pytest.raises((OSError, proof.EvidenceError)):
        proof.snapshot(target, 1 if kind == "oversized" else 100)


def test_minimal_environment_ignores_credentials_and_overrides(tmp_path, monkeypatch):
    for key in ("GH_TOKEN", "GITHUB_TOKEN", "GH_HOST", "HTTP_PROXY", "HTTPS_PROXY", "SSL_CERT_FILE", "GH_DEBUG", "GIT_CONFIG_COUNT"):
        monkeypatch.setenv(key, "untrusted")
    value = proof.minimal_environment(tmp_path)
    assert value["GH_HOST"] == "github.com"
    assert not set(value).intersection({"GH_TOKEN", "GITHUB_TOKEN", "HTTP_PROXY", "HTTPS_PROXY", "SSL_CERT_FILE", "GH_DEBUG", "GIT_CONFIG_COUNT"})
    assert value["GH_CONFIG_DIR"] == str(tmp_path / "config")
    assert value["GIT_NO_REPLACE_OBJECTS"] == "1"
    assert value["GIT_CONFIG_NOSYSTEM"] == "1"


def cli_archive(member=proof.CLI_MEMBER, kind=None):
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:gz") as archive:
        record = tarfile.TarInfo(member)
        content = b"synthetic first party binary"
        record.size = len(content)
        if kind == "link":
            record.type, record.linkname, record.size = tarfile.SYMTYPE, "elsewhere", 0
        archive.addfile(record, io.BytesIO(content) if record.isreg() else None)
    return data.getvalue()


def test_cli_archive_requires_pin_before_extract(tmp_path):
    with pytest.raises(proof.EvidenceError, match="pin mismatch"):
        proof.extract_cli(cli_archive(), tmp_path)
    assert not (tmp_path / "gh").exists()


@pytest.mark.parametrize("kind", ["link", "missing", "good"])
def test_only_exact_regular_cli_member_extracted(tmp_path, monkeypatch, kind):
    raw = cli_archive("unrelated" if kind == "missing" else proof.CLI_MEMBER, kind)
    monkeypatch.setattr(proof, "CLI_ARCHIVE_SHA256", proof.sha(raw))
    if kind == "good":
        assert proof.extract_cli(raw, tmp_path).read_bytes() == b"synthetic first party binary"
        assert not (tmp_path / "unrelated").exists()
    else:
        with pytest.raises(proof.EvidenceError):
            proof.extract_cli(raw, tmp_path)


@pytest.mark.parametrize("operation", ["failure", "stderr_bound", "stdout_bound", "timeout"])
def test_bounded_process_rejects_failures_without_echoing(tmp_path, monkeypatch, operation):
    monkeypatch.setattr(proof, "MAX_PROCESS", 100)
    code = {"failure": "import sys;sys.stderr.write('credential-like-secret');sys.exit(3)",
            "stderr_bound": "import sys;sys.stderr.write('x'*101)",
            "stdout_bound": "print('x'*101)", "timeout": "import time;time.sleep(10)"}[operation]
    with pytest.raises(proof.EvidenceError) as exc:
        proof.bounded_process([sys.executable, "-c", code], cwd=tmp_path, env={"PATH": "/usr/bin:/bin"}, timeout=0.2)
    assert "credential-like-secret" not in str(exc.value)


@pytest.fixture
def verification_inputs(tmp_path, monkeypatch):
    candidate, workflow = tmp_path / "candidate", tmp_path / "workflow"
    for root in (candidate, workflow):
        (root / ".github/workflows").mkdir(parents=True)
        (root / proof.WORKFLOW).write_bytes(b"synthetic workflow")
    (candidate / "scripts").mkdir()
    (candidate / "scripts/rea_build_repeatability.py").write_bytes(b"synthetic build helper")
    (candidate / "scripts/rea_ci_attestation.py").write_bytes(b"synthetic verifier helper")
    report = {"format": "aios-rea-package-correlation.v1", "diagnostic_only": True,
              "repeatability": {"context": expected()["context"], "recipe": {
                  "workflow_sha256": proof.sha(b"synthetic workflow"), "helper_sha256": proof.sha(b"synthetic build helper")}}}
    subject, bundle, archive = tmp_path / "correlation.json", tmp_path / "bundle.json", tmp_path / "cli.tar.gz"
    subject.write_bytes(proof.canonical(report))
    bundle.write_bytes(b'{"synthetic":"not real signature proof"}')
    archive.write_bytes(cli_archive())
    monkeypatch.setattr(proof, "CLI_ARCHIVE_SHA256", proof.sha(archive.read_bytes()))
    calls = []
    def process(argv, **kw):
        calls.append(argv)
        if argv[0] == "/usr/bin/git":
            root = Path(argv[2])
            if argv[3] == "rev-parse":
                return (("a" if root == candidate else "c") * 40 + "\n").encode()
            return (root / argv[4].split(":", 1)[1]).read_bytes()
        if argv[1] == "--version":
            return b"gh version 2.102.0 (synthetic)\n"
        return proof.canonical(verified(subject.read_bytes()))
    monkeypatch.setattr(proof, "bounded_process", process)
    args = dict(subject_path=subject, bundle_path=bundle, cli_archive=archive, candidate_root=candidate,
                workflow_root=workflow, expected=expected(), output=tmp_path / "result")
    return args, calls


def test_verify_invokes_fresh_pinned_cli_and_keeps_authority_false(verification_inputs):
    args, calls = verification_inputs
    result = proof.verify(**args)
    verify_call = next(c for c in calls if "attestation" in c)
    assert "--bundle" in verify_call and "--hostname" in verify_call and "--deny-self-hosted-runners" in verify_call
    assert not any("--custom-trusted-root" in c for c in calls)
    assert result["attesting_execution_identity_verified"] is True
    assert result["ci_source_sha"] != result["context"]["candidate"]
    for key in ("owning_github_execution_authenticated", "independent_compiler_causality_verified", "candidate_to_ci_source_relation_verified",
                "publisher_provenance_verified", "runtime_dependency_closure_verified", "installed_runtime_bytes_verified",
                "isolation_verified", "provider_ready", "live_transport_owned", "execution_authorized"):
        assert result[key] is False
    assert (args["output"] / "bundle.json").read_bytes() == args["bundle_path"].read_bytes()


@pytest.mark.parametrize("change", ["workflow", "helper", "context", "original_subject", "verifier_failure"])
def test_verify_rejects_recipe_context_and_freshness_failures(verification_inputs, monkeypatch, change):
    args, calls = verification_inputs
    process = proof.bounded_process
    if change == "workflow":
        (args["workflow_root"] / proof.WORKFLOW).write_bytes(b"different actual workflow")
    elif change in ("helper", "context"):
        report = json.loads(args["subject_path"].read_bytes())
        if change == "helper":
            report["repeatability"]["recipe"]["helper_sha256"] = "0" * 64
        else:
            report["repeatability"]["context"]["run_attempt"] = "1"
        args["subject_path"].write_bytes(proof.canonical(report))
    else:
        def altered(argv, **kw):
            value = process(argv, **kw)
            if "attestation" in argv:
                if change == "verifier_failure":
                    raise proof.EvidenceError("fresh CLI failed")
                args["subject_path"].write_bytes(b"mutated")
            return value
        monkeypatch.setattr(proof, "bounded_process", altered)
    with pytest.raises(proof.EvidenceError):
        proof.verify(**args)
    assert not args["output"].exists()


def test_workflow_privileges_and_independent_raw_verification():
    import yaml
    workflow = yaml.safe_load((ROOT / proof.WORKFLOW).read_text())
    assert workflow["permissions"] == {"contents": "read"}
    jobs = workflow["jobs"]
    assert "permissions" not in jobs["source-build"]
    assert jobs["compare"]["permissions"] == {"contents": "read", "id-token": "write", "attestations": "write"}
    assert "head.repo.full_name == github.repository" in jobs["compare"]["if"]
    assert jobs["verify-attestation"]["permissions"] == {"contents": "read"}
    attest = next(s for s in jobs["compare"]["steps"] if str(s.get("uses", "")).startswith("actions/attest@"))
    assert attest["uses"] == "actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6"
    assert attest["with"] == {"subject-path": "rea-package-correlation/correlation.json"}
    fresh = next(s["run"] for s in jobs["verify-attestation"]["steps"] if "rea_ci_attestation.py" in s.get("run", ""))
    assert "--bundle received-attestation/bundle.json" in fresh
    raw_upload = next(i for i, step in enumerate(jobs["compare"]["steps"])
                      if step.get("with", {}).get("name") == "rea-ci-attestation-raw")
    producer_verify = next(i for i, step in enumerate(jobs["compare"]["steps"])
                           if "--subject rea-package-correlation/correlation.json" in step.get("run", ""))
    assert raw_upload < producer_verify
    assert any(step.get("with", {}).get("name") == "rea-ci-attestation-raw"
               for step in jobs["verify-attestation"]["steps"])
    assert "verification.json" not in fresh and "GH_TOKEN" not in str(jobs)
    assert "pull_request_target" not in (ROOT / proof.WORKFLOW).read_text()


def test_timeout_kills_descendant_after_group_leader_exits(tmp_path):
    pid_file = tmp_path / "child-pid"
    code = ("import subprocess,sys,pathlib;"
            "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);"
            "pathlib.Path(sys.argv[1]).write_text(str(p.pid))")
    with pytest.raises(proof.EvidenceError, match="timeout"):
        proof.bounded_process([sys.executable, "-c", code, str(pid_file)], cwd=tmp_path,
                              env={"PATH": "/usr/bin:/bin"}, timeout=0.3)
    pid = int(pid_file.read_text())
    proc = Path(f"/proc/{pid}/stat")
    # A killed orphan can briefly remain a zombie until PID 1 reaps it.
    deadline = time.monotonic() + 1
    while proc.exists() and proc.read_text().split()[2] not in ("Z", "X") and time.monotonic() < deadline:
        time.sleep(0.01)
    assert not proc.exists() or proc.read_text().split()[2] in ("Z", "X")


def test_git_replace_cannot_redirect_authenticated_bytes(tmp_path):
    import subprocess
    repo = tmp_path / "repo"
    repo.mkdir()
    env = proof.minimal_environment(tmp_path)
    def git(*args):
        return subprocess.check_output(["/usr/bin/git", "-C", str(repo), *args], env=env)
    git("init", "-q")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "user.name", "Synthetic Fixture")
    (repo / "recipe").write_bytes(b"original")
    git("add", "recipe")
    git("commit", "-qm", "original")
    original = git("rev-parse", "HEAD").decode().strip()
    (repo / "recipe").write_bytes(b"replacement")
    git("commit", "-qam", "replacement")
    replacement = git("rev-parse", "HEAD").decode().strip()
    git("replace", original, replacement)
    assert proof.git_bytes(repo, original, "recipe", env) == b"original"
