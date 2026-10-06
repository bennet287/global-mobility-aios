"""Trusted runtime verification of raw REA CI evidence, never candidate Python.

The pinned CLI authenticates only the report's attesting execution. No supplied
verification JSON, predicate assertion, custom root or credential is trusted.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import io
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import tarfile
import tempfile
import time
from app.services.organization_command import InvalidTransition
from app.services.organization_rea_catalog import _bounded_json
from app.services import organization_rea_artifacts as artifact
from app.schemas_organization_rea_build import package_path

EvidenceError = InvalidTransition

def require(condition, message):
    if not condition:
        raise InvalidTransition(message)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def parse_json(raw):
    return _bounded_json(raw)

def context(candidate, repository, run_id, run_attempt):
    require(re.fullmatch(r"[0-9a-f]{40}", candidate) is not None and repository == REPOSITORY, "candidate/repository")
    require(re.fullmatch(r"[1-9][0-9]{0,19}", run_id) is not None and re.fullmatch(r"[1-9][0-9]{0,5}", run_attempt) is not None, "run identity")
    return dict(candidate=candidate, repository=repository, run_id=run_id, run_attempt=run_attempt, runner="ubuntu-24.04")

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
    timestamps = result.get("verifiedTimestamps")
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
    statement = result.get("statement")
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


@dataclass(frozen=True)
class ReaCiAttestationTrust:
    bundle_root: Path
    bundle_relative: str
    cli_archive_root: Path
    cli_archive_relative: str
    bundle_sha256: str
    ci_source_sha: str
    ci_workflow_sha: str
    source_ref: str
    trigger: str


def immutable_snapshot(root, relative, limit):
    """No-follow deployment locator, readonly custody and regular single-link file."""
    package_path(relative)
    parent = artifact._directory(root)
    try:
        for part in relative.split('/')[:-1]:
            require(not os.fstat(parent).st_mode & 0o222, "evidence directory writable")
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent)
            parent = child
        require(not os.fstat(parent).st_mode & 0o222, "evidence directory writable")
        parent_before = os.fstat(parent)
        fd = os.open(relative.split('/')[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        try:
            before = os.fstat(fd)
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and not before.st_mode & 0o222 and 0 < before.st_size <= limit, "evidence file unsafe")
            raw = bytearray()
            while len(raw) <= before.st_size:
                chunk = os.read(fd, min(65536, before.st_size + 1 - len(raw)))
                if not chunk:
                    break
                raw.extend(chunk)
            identity = lambda v: (v.st_dev, v.st_ino, v.st_mode, v.st_nlink, v.st_size, v.st_mtime_ns, v.st_ctime_ns)
            require(identity(os.fstat(fd)) == identity(before) and identity(os.fstat(parent)) == identity(parent_before) and len(raw) == before.st_size, "evidence changed while reading")
            return bytes(raw), identity(before), identity(parent_before)
        finally:
            os.close(fd)
    finally:
        os.close(parent)


def authenticate(compilation_trust, approved):
    trust = compilation_trust.ci_attestation
    require(type(trust) is ReaCiAttestationTrust and approved is not None, "governed raw attestation trust missing")
    pins = {key: getattr(trust, key) for key in type(approved).model_fields}
    require(all(type(value) is str for value in pins.values()), 'attestation deployment pin type differs')
    require(pins == approved.model_dump(mode='json'), "attestation deployment pins differ from governed review")
    expected = expected_identity(candidate=compilation_trust.candidate_sha, run_id=compilation_trust.run_id,
        run_attempt=compilation_trust.run_attempt, source_sha=trust.ci_source_sha, workflow_sha=trust.ci_workflow_sha,
        source_ref=trust.source_ref, trigger=trust.trigger)
    locators = [(compilation_trust.report_root, compilation_trust.report_relative, MAX_JSON),
                (trust.bundle_root, trust.bundle_relative, MAX_JSON),
                (trust.cli_archive_root, trust.cli_archive_relative, MAX_ARCHIVE)]
    snapshots = [immutable_snapshot(*locator) for locator in locators]
    subject, bundle, archive = [item[0] for item in snapshots]
    require(sha(subject) == compilation_trust.report_sha256 and sha(bundle) == trust.bundle_sha256, "raw attestation digest differs")
    parse_json(bundle)
    with tempfile.TemporaryDirectory(prefix='aios-rea-attestation-') as tmp:
        private = Path(tmp)
        env = minimal_environment(private)
        cli = extract_cli(archive, private)
        require(bounded_process([str(cli), '--version'], cwd=private, env=env).startswith(f'gh version {CLI_VERSION} '.encode()), "GitHub CLI version mismatch")
        sealed_subject, sealed_bundle = private / 'correlation.json', private / 'bundle.json'
        sealed_subject.write_bytes(subject); sealed_bundle.write_bytes(bundle)
        sealed_subject.chmod(0o400); sealed_bundle.chmod(0o400)
        cli_before = cli.read_bytes()
        raw = bounded_process([str(cli), 'attestation', 'verify', str(sealed_subject), '--bundle', str(sealed_bundle),
            '--repo', REPOSITORY, '--hostname', 'github.com', '--cert-identity', expected['buildSignerURI'],
            '--cert-oidc-issuer', ISSUER, '--source-digest', expected['sourceRepositoryDigest'],
            '--source-ref', expected['sourceRepositoryRef'], '--signer-digest', expected['buildSignerDigest'],
            '--deny-self-hosted-runners', '--format', 'json'], cwd=private, env=env)
        require(cli.read_bytes() == cli_before and sealed_subject.read_bytes() == subject and sealed_bundle.read_bytes() == bundle, "sealed verifier inputs changed")
        proof = validate_result(raw, subject, expected)
    def revalidate():
        require([immutable_snapshot(*locator) for locator in locators] == snapshots, "raw attestation evidence changed")
    revalidate()
    # Audit only fixed identity pins and bounded verified witness values; never
    # persist arbitrary certificate extension data or caller filesystem paths.
    summary = dict(bundle_sha256=sha(bundle), report_sha256=sha(subject), cli_archive_sha256=CLI_ARCHIVE_SHA256,
        cli_version=CLI_VERSION, certificate={key: proof['certificate'][key] for key in expected if key != 'context'},
        verified_timestamps=[{key: item[key] for key in ('type', 'timestamp')} for item in proof['verified_timestamps']], fresh_cli_output_sha256=proof['fresh_cli_output_sha256'],
        attesting_execution_identity_verified=True, candidate_to_ci_source_relation_verified=False,
        independent_compiler_causality_verified=False, owning_github_execution_authenticated=False)
    return summary, revalidate
