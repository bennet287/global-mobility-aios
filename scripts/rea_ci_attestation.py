#!/usr/bin/env python3
"""Fresh, bounded CI signature diagnostics for a REA correlation report.

The pinned GitHub CLI authenticates the report's attesting execution. Predicate
claims do not prove independent compilation, product admission or execution.
No supplied verification JSON is accepted as an authentication input.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import io
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import tarfile
import tempfile
import time

from rea_build_repeatability import EvidenceError, canonical, context, identity, parse_json, read_regular, require, sha

REPOSITORY = "bennet287/global-mobility-aios"
REPOSITORY_ID = "1292651446"
OWNER_ID = "77139673"
WORKFLOW = ".github/workflows/rea-build-repeatability.yml"
ISSUER = "https://token.actions.githubusercontent.com"
CLI_VERSION = "2.102.0"
CLI_ARCHIVE_SHA256 = "bb766f710eef8ede859c18578c72c327597cd4c8a85b06001b1f3843c6019386"
CLI_ARCHIVE_URL = "https://github.com/cli/cli/releases/download/v2.102.0/gh_2.102.0_linux_amd64.tar.gz"
CLI_MEMBER = "gh_2.102.0_linux_amd64/bin/gh"
MAX_ARCHIVE = 64 * 1024 * 1024
MAX_JSON = 4 * 1024 * 1024
MAX_PROCESS = 4 * 1024 * 1024
PROCESS_TIMEOUT = 60


def snapshot(path: Path, limit: int) -> tuple[bytes, tuple]:
    """Traverse every parent with directory FDs; never follow a path symlink."""
    parts = Path(os.path.abspath(path)).parts
    fd = os.open(parts[0], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[1:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        before = os.stat(parts[-1], dir_fd=fd, follow_symlinks=False)
        data = read_regular(Path(parts[-1]), limit, dir_fd=fd)
        after = os.stat(parts[-1], dir_fd=fd, follow_symlinks=False)
        require(identity(before) == identity(after), "snapshot identity changed")
        return data, identity(after)
    finally:
        os.close(fd)


def bounded_process(argv: list[str], *, cwd: Path, env: dict[str, str], timeout: float = PROCESS_TIMEOUT) -> bytes:
    """Bound both pipes while running, rather than buffering before enforcing limits."""
    process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    chunks = {process.stdout: bytearray(), process.stderr: bytearray()}
    deadline = time.monotonic() + timeout
    try:
        with selectors.DefaultSelector() as selector:
            for pipe in chunks:
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ)
            while selector.get_map():
                require(time.monotonic() < deadline, "verifier process timeout")
                for key, _ in selector.select(min(0.1, max(0, deadline - time.monotonic()))):
                    data = os.read(key.fileobj.fileno(), 65536)
                    if not data:
                        selector.unregister(key.fileobj)
                        continue
                    chunks[key.fileobj].extend(data)
                    require(sum(map(len, chunks.values())) <= MAX_PROCESS, "verifier output bound exceeded")
            require(process.wait(timeout=max(0.001, deadline - time.monotonic())) == 0, "verifier process failed")
        return bytes(chunks[process.stdout])
    except BaseException:
        # Descendants can retain pipes after the group leader has exited.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        raise
    finally:
        process.stdout.close()
        process.stderr.close()


def minimal_environment(root: Path) -> dict[str, str]:
    config = root / "config"
    config.mkdir(mode=0o700)
    env = {"PATH": "/usr/bin:/bin", "HOME": str(root), "GH_CONFIG_DIR": str(config),
           "GH_HOST": "github.com", "GH_PROMPT_DISABLED": "1", "GH_NO_UPDATE_NOTIFIER": "1",
           "NO_COLOR": "1", "TERM": "dumb", "LANG": "C.UTF-8",
           "GIT_NO_REPLACE_OBJECTS": "1", "GIT_CONFIG_NOSYSTEM": "1"}
    # Bundle verification needs no token. No caller config, proxy, extensions,
    # alternate trust-root environment, debug settings or inherited git settings.
    return env


def extract_cli(raw: bytes, root: Path) -> Path:
    require(sha(raw) == CLI_ARCHIVE_SHA256, "GitHub CLI archive pin mismatch")
    binary = None
    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
            count = total = 0
            for member in archive:
                count += 1
                total += member.size
                require(count <= 2000 and 0 <= member.size <= MAX_ARCHIVE and total <= 256 * 1024 * 1024,
                        "GitHub CLI archive bound exceeded")
                if member.name == CLI_MEMBER:
                    require(binary is None and member.isreg(), "unsafe GitHub CLI binary member")
                    stream = archive.extractfile(member)
                    require(stream is not None, "missing GitHub CLI binary bytes")
                    binary = stream.read(MAX_ARCHIVE + 1)
                    require(len(binary) == member.size and len(binary) <= MAX_ARCHIVE, "GitHub CLI binary bound")
    except (tarfile.TarError, OSError) as exc:
        raise EvidenceError("invalid GitHub CLI archive") from exc
    require(binary is not None, "GitHub CLI binary missing")
    path = root / "gh"
    path.write_bytes(binary)
    path.chmod(0o500)
    return path


def expected_identity(*, candidate: str, run_id: str, run_attempt: str, source_sha: str,
                      workflow_sha: str, source_ref: str, trigger: str) -> dict:
    ctx = context(candidate, REPOSITORY, run_id, run_attempt)
    require(re.fullmatch(r"[0-9a-f]{40}", source_sha) is not None, "source digest")
    require(re.fullmatch(r"[0-9a-f]{40}", workflow_sha) is not None, "workflow digest")
    require(trigger in ("pull_request", "workflow_dispatch"), "unsupported trigger")
    if trigger == "pull_request":
        require(re.fullmatch(r"refs/pull/[1-9][0-9]*/merge", source_ref) is not None, "PR source ref")
    else:
        require(re.fullmatch(r"refs/heads/[A-Za-z0-9_.\-/]+", source_ref) is not None and ".." not in source_ref,
                "dispatch source ref")
    workflow_uri = f"https://github.com/{REPOSITORY}/{WORKFLOW}@{source_ref}"
    return {"context": ctx, "issuer": ISSUER, "subjectAlternativeName": workflow_uri,
            "buildSignerURI": workflow_uri, "buildSignerDigest": workflow_sha,
            "runnerEnvironment": "github-hosted", "sourceRepositoryURI": f"https://github.com/{REPOSITORY}",
            "sourceRepositoryDigest": source_sha, "sourceRepositoryRef": source_ref,
            "sourceRepositoryIdentifier": REPOSITORY_ID, "sourceRepositoryOwnerURI": "https://github.com/bennet287",
            "sourceRepositoryOwnerIdentifier": OWNER_ID, "buildConfigURI": workflow_uri,
            "buildConfigDigest": workflow_sha, "buildTrigger": trigger,
            "runInvocationURI": f"https://github.com/{REPOSITORY}/actions/runs/{run_id}/attempts/{run_attempt}"}


def validate_result(raw: bytes, subject: bytes, expected: dict) -> dict:
    """Called only with fresh successful pinned CLI stdout by verify()."""
    results = parse_json(raw)
    require(type(results) is list and len(results) == 1, "expected exactly one verified attestation")
    require(type(results[0]) is dict, "invalid verified result")
    result = results[0].get("verificationResult")
    require(type(result) is dict and type(result.get("signature")) is dict, "verified signature missing")
    certificate = result["signature"].get("certificate")
    require(type(certificate) is dict, "verified certificate missing")
    for key, value in expected.items():
        if key != "context":
            require(certificate.get(key) == value, f"certificate {key} mismatch")
    timestamps = result["verifiedTimestamps"]
    require(type(timestamps) is list and 1 <= len(timestamps) <= 16, "verified witness timestamp missing")
    for timestamp in timestamps:
        require(type(timestamp) is dict and timestamp.get("type") in ("Tlog", "TimestampAuthority"), "unknown witness type")
        value = timestamp.get("timestamp")
        require(type(value) is str and re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,9})?(?:Z|\+00:00)", value),
            "invalid witness timestamp")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise EvidenceError("invalid witness timestamp") from exc
        require(parsed.tzinfo is not None and parsed.utcoffset().total_seconds() == 0
                and parsed <= datetime.now(timezone.utc), "invalid witness time")
    statement = result["statement"]
    require(type(statement) is dict, "verified statement missing")
    require(statement.get("_type") == "https://in-toto.io/Statement/v1"
            and statement.get("predicateType") == "https://slsa.dev/provenance/v1", "unexpected signed statement type")
    subjects = statement.get("subject")
    require(type(subjects) is list and len(subjects) == 1 and type(subjects[0]) is dict
            and subjects[0].get("name") == "correlation.json"
            and subjects[0].get("digest") == {"sha256": sha(subject)}, "signed subject mismatch")
    # Do not inspect predicate metadata.invocationId to authorize a run: the
    # workflow controls the predicate, while runInvocationURI is in the cert.
    return {"certificate": certificate, "verified_timestamps": timestamps,
            "signed_subject": subjects[0], "fresh_cli_output_sha256": sha(raw)}


def git_bytes(root: Path, revision: str, path: str, env: dict) -> bytes:
    return bounded_process(["/usr/bin/git", "-C", str(root), "show", f"{revision}:{path}"], cwd=root, env=env)


def verify(*, subject_path: Path, bundle_path: Path, cli_archive: Path, candidate_root: Path,
           workflow_root: Path, expected: dict, output: Path) -> dict:
    candidate_root, workflow_root = candidate_root.absolute(), workflow_root.absolute()
    tracked = {subject_path: snapshot(subject_path, MAX_JSON), bundle_path: snapshot(bundle_path, MAX_JSON),
               cli_archive: snapshot(cli_archive, MAX_ARCHIVE),
               candidate_root / WORKFLOW: snapshot(candidate_root / WORKFLOW, MAX_JSON),
               candidate_root / "scripts/rea_build_repeatability.py": snapshot(candidate_root / "scripts/rea_build_repeatability.py", MAX_JSON),
               candidate_root / "scripts/rea_ci_attestation.py": snapshot(candidate_root / "scripts/rea_ci_attestation.py", MAX_JSON),
               workflow_root / WORKFLOW: snapshot(workflow_root / WORKFLOW, MAX_JSON)}
    subject, bundle, archive = (tracked[p][0] for p in (subject_path, bundle_path, cli_archive))
    parse_json(bundle)
    report = parse_json(subject)
    require(report.get("format") == "aios-rea-package-correlation.v1" and report.get("diagnostic_only") is True,
            "unexpected correlation report")
    repeatability = report["repeatability"]
    require(repeatability["context"] == expected["context"], "correlation context mismatch")
    workflow = tracked[candidate_root / WORKFLOW][0]
    helper = tracked[candidate_root / "scripts/rea_build_repeatability.py"][0]
    require(repeatability["recipe"]["workflow_sha256"] == sha(workflow)
            and repeatability["recipe"]["helper_sha256"] == sha(helper), "reviewed recipe byte mismatch")
    require(tracked[workflow_root / WORKFLOW][0] == workflow, "executed workflow differs from reviewed workflow")
    with tempfile.TemporaryDirectory(prefix="rea-ci-attestation-") as tmp:
        private = Path(tmp)
        env = minimal_environment(private)
        for root, revision in ((candidate_root, expected["context"]["candidate"]),
                               (workflow_root, expected["buildSignerDigest"])):
            head = bounded_process(["/usr/bin/git", "-C", str(root), "rev-parse", "HEAD"], cwd=private, env=env)
            require(head.decode().strip() == revision, "checkout identity mismatch")
            require(git_bytes(root, revision, WORKFLOW, env) == workflow, "workflow differs from authenticated git object")
        for path in ("scripts/rea_build_repeatability.py", "scripts/rea_ci_attestation.py"):
            require(git_bytes(candidate_root, expected["context"]["candidate"], path, env) == tracked[candidate_root / path][0],
                    "candidate helper differs from reviewed git object")
        cli = extract_cli(archive, private)
        version = bounded_process([str(cli), "--version"], cwd=private, env=env)
        require(version.startswith(f"gh version {CLI_VERSION} ".encode()), "GitHub CLI version mismatch")
        sealed_subject, sealed_bundle = private / "correlation.json", private / "bundle.json"
        sealed_subject.write_bytes(subject)
        sealed_bundle.write_bytes(bundle)
        cli_bytes = snapshot(cli, MAX_ARCHIVE)
        raw = bounded_process([str(cli), "attestation", "verify", str(sealed_subject), "--bundle", str(sealed_bundle),
                               "--repo", REPOSITORY, "--hostname", "github.com", "--cert-identity", expected["buildSignerURI"],
                               "--cert-oidc-issuer", ISSUER, "--source-digest", expected["sourceRepositoryDigest"],
                               "--source-ref", expected["sourceRepositoryRef"], "--signer-digest", expected["buildSignerDigest"],
                               "--deny-self-hosted-runners", "--format", "json"], cwd=private, env=env)
        require(snapshot(cli, MAX_ARCHIVE) == cli_bytes and read_regular(sealed_subject, MAX_JSON) == subject
                and read_regular(sealed_bundle, MAX_JSON) == bundle, "sealed verifier inputs changed")
        proof = validate_result(raw, subject, expected)
    for path, original in tracked.items():
        require(snapshot(path, MAX_ARCHIVE if path == cli_archive else MAX_JSON) == original, "original verifier input changed")
    summary = {"format": "aios-rea-ci-attestation-diagnostic.v1", "context": expected["context"],
               "ci_source_sha": expected["sourceRepositoryDigest"], "ci_workflow_sha": expected["buildSignerDigest"],
               "correlation_sha256": sha(subject), "raw_bundle_sha256": sha(bundle),
               "cli_version": CLI_VERSION, "cli_archive_sha256": CLI_ARCHIVE_SHA256,
               "reviewed_workflow_sha256": sha(workflow), "reviewed_build_helper_sha256": sha(helper),
               "reviewed_verifier_helper_sha256": sha(tracked[candidate_root / "scripts/rea_ci_attestation.py"][0]),
               "attesting_execution_identity_verified": True, "executed_workflow_bytes_match_reviewed": True,
               "owning_github_execution_authenticated": False, "independent_compiler_causality_verified": False,
               "candidate_to_ci_source_relation_verified": False,
               "publisher_provenance_verified": False, "runtime_dependency_closure_verified": False,
               "installed_runtime_bytes_verified": False, "isolation_verified": False, "provider_ready": False,
               "live_transport_owned": False, "execution_authorized": False, "diagnostic_only": True, **proof}
    output.mkdir(mode=0o700, parents=False)
    (output / "bundle.json").write_bytes(bundle)
    (output / "verification.json").write_bytes(raw)
    (output / "diagnostic.json").write_bytes(canonical(summary))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("subject", "bundle", "cli-archive", "candidate-root", "workflow-root", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    for name in ("candidate", "run-id", "run-attempt", "source-sha", "workflow-sha", "source-ref", "trigger"):
        parser.add_argument(f"--{name}", required=True)
    args = parser.parse_args()
    try:
        expected = expected_identity(candidate=args.candidate, run_id=args.run_id, run_attempt=args.run_attempt,
                                     source_sha=args.source_sha, workflow_sha=args.workflow_sha,
                                     source_ref=args.source_ref, trigger=args.trigger)
        result = verify(subject_path=args.subject, bundle_path=args.bundle, cli_archive=args.cli_archive,
                        candidate_root=args.candidate_root, workflow_root=args.workflow_root,
                        expected=expected, output=args.output)
        print(canonical({"correlation_sha256": result["correlation_sha256"], "attesting_execution_identity_verified": True,
                         "execution_authorized": False}).decode())
    except (EvidenceError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        # Never echo captured verifier output or token-bearing environment.
        raise SystemExit("REA CI attestation verification failed") from exc


if __name__ == "__main__":
    main()
