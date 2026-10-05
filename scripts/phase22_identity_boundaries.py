#!/usr/bin/env python3
"""Target-host identity evidence. Every observation is real; no fixture mode exists.

Finite surfaces v1: seven running production containers plus the exited migration
container's configuration, all configured secret files (64 files/64 KiB each),
web /app/.next/static and /app/public (10,000 files/128 MiB), rendered cockpit
HTML (2 MiB), and timestamp-bounded logs (8 MiB per running container). Exact
values are compared only in private memory. Transformed values and other logs
remain outside this finite scan; no universal absence or rotation is claimed.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import selectors
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit
from uuid import UUID
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apps' / 'api'))
from sqlmodel import Session
from app.core.db import engine, register_models
from app.models.domain import OrganizationActorType
from app.core.startup_safety import DEFAULT_INSECURE_PASSWORDS, DEFAULT_INSECURE_SECRETS
from app.services.organization_command import OrganizationCommandContext
from app.services.production_deployment_acceptance import IDENTITY_REQUIRED_PROOFS, TARGET_HOST_IDENTITY_EXECUTOR_ACTOR, record_target_host_identity_receipt, validated_deployment_networking_contract
from scripts import phase22_target_host_acceptance as host
SCOPES = frozenset({'database', 'auth', 'automation', 'documents', 'storage', 'llm', 'bootstrap'})
SHARED = SCOPES - {'bootstrap'}
CONTAINERS = {'gmai-postgres-prod': {'database'}, 'gmai-api-migrate-prod': {'database'}, 'gmai-api-prod': SCOPES, 'gmai-worker-prod': SHARED, 'gmai-beat-prod': set(), 'gmai-web-prod': set(), 'gmai-ingress-prod': set(), 'gmai-redis-prod': set()}
SECRET_FIELDS = frozenset({'DATABASE_PASSWORD', 'JWT_SECRET', 'AUTH_ADMIN_PASSWORD', 'AUTOMATION_ENCRYPTION_KEY', 'AUTOMATION_ENCRYPTION_PREVIOUS_KEY', 'AUTOMATION_WEBHOOK_SECRET', 'DOCUMENT_ACCESS_TOKEN_SECRET', 'MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY', 'DEEPSEEK_API_KEY', 'MOONSHOT_API_KEY', 'GEMINI_API_KEY'})
MANDATORY = {'DATABASE_PASSWORD_REF', 'JWT_SECRET_REF', 'AUTH_ADMIN_PASSWORD_REF', 'AUTOMATION_ENCRYPTION_KEY_REF', 'AUTOMATION_WEBHOOK_SECRET_REF', 'DOCUMENT_ACCESS_TOKEN_SECRET_REF'}

class ProbeError(RuntimeError):
    """Only fixed identifiers may leave the private executor boundary."""

def require(condition: bool, code: str) -> None:
    if not condition:
        raise ProbeError(code)

def private_run(command: list[str], *, input_value: str | None=None, limit: int=8388608, timeout: int=60, merge_stderr: bool=False) -> str:
    """Drain bounded pipes, including stderr, without exposing command output on failure."""
    process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.PIPE if input_value is not None else subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    selector = selectors.DefaultSelector()
    output = bytearray()
    total = 0
    started = time.monotonic()
    try:
        remaining = memoryview(b'')
        if input_value is not None:
            encoded = input_value.encode()
            require(len(encoded) <= 4194304, 'input_limit')
            remaining = memoryview(encoded)
            os.set_blocking(process.stdin.fileno(), False)
            selector.register(process.stdin, selectors.EVENT_WRITE)
        for stream in (process.stdout, process.stderr):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ)
        while selector.get_map():
            require(time.monotonic() - started <= timeout, 'command_timeout')
            for key, _ in selector.select(timeout=0.5):
                if key.fileobj is process.stdin:
                    written = os.write(process.stdin.fileno(), remaining[:65536])
                    remaining = remaining[written:]
                    if not remaining:
                        selector.unregister(process.stdin)
                        process.stdin.close()
                    continue
                chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                total += len(chunk)
                require(total <= limit, 'surface_limit')
                if key.fileobj is process.stdout or merge_stderr:
                    output.extend(chunk)
        require(process.wait(timeout=1) == 0, 'command_failed')
        return output.decode('utf-8')
    except (ProbeError, KeyboardInterrupt):
        raise
    except Exception:
        raise ProbeError('command_failed') from None
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        if process.poll() is None:
            process.wait()
        selector.close()
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None and (not stream.closed):
                stream.close()

def inspect_container(name: str) -> dict:
    try:
        data = json.loads(private_run(['docker', 'inspect', name], limit=1048576))
        require(isinstance(data, list) and len(data) == 1, 'container_invalid')
        return data[0]
    except (ValueError, KeyError, TypeError):
        raise ProbeError('container_invalid') from None

def runtime_configuration(containers: dict[str, dict]) -> dict:
    return {name: {'id': value['Id'], 'image': value['Image'], 'env': sorted(value['Config']['Env']), 'labels': value['Config']['Labels'], 'mounts': sorted(((mount['Type'], mount['Source'], mount['Destination'], mount['RW']) for mount in value['Mounts']))} for name, value in containers.items()}

def bounded_secret(path: Path) -> str:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        with os.fdopen(descriptor, 'rb') as stream:
            data = stream.read(65537)
        require(len(data) <= 65536, 'secret_limit')
        value = data.decode('utf-8').rstrip('\r\n')
        require(4 <= len(value) <= 65536, 'secret_value_limit')
        return value
    except Exception:
        raise ProbeError('secret_read') from None

def secret_material(container_data: dict[str, dict], root: Path) -> tuple[dict[str, str], list[str]]:
    root = root.resolve(strict=True)
    envs = {}
    for name, container in container_data.items():
        env = dict((item.split('=', 1) for item in container['Config']['Env']))
        envs[name] = env
        actual = {}
        for mount in container['Mounts']:
            source = Path(mount['Source']).resolve()
            destination = mount['Destination']
            if source == root or root in source.parents or source in root.parents or destination.startswith('/run/secrets/aios'):
                require(mount['Type'] == 'bind' and mount['RW'] is False, 'mount_scope')
                scope = source.name
                require(source.parent == root and scope in SCOPES and (destination == f'/run/secrets/aios/{scope}'), 'mount_scope')
                require(scope not in actual, 'mount_scope')
                actual[scope] = mount
        require(set(actual) == set(CONTAINERS[name]), 'mount_scope')
        for key, value in env.items():
            require(key not in SECRET_FIELDS and (not re.search('(?:PASSWORD|SECRET|TOKEN|API_KEY)$', key)) or not value, 'plaintext_environment')
            if '://' in value and (not key.endswith('_REF')):
                parsed = urlsplit(value)
                require(parsed.password is None, 'embedded_url_credential')
            if key.endswith('_REF') and value:
                require(value.startswith('file:///run/secrets/aios/'), 'secret_reference')
                relative = Path(value[len('file:///run/secrets/aios/'):])
                require(len(relative.parts) == 2 and relative.parts[0] in actual and ('..' not in relative.parts), 'secret_reference')
                require((root / relative).is_file() and (not (root / relative).is_symlink()), 'secret_reference')
    for name, container in container_data.items():
        require(name == 'gmai-api-migrate-prod' or container['State']['Running'] is True, 'dependency_unavailable')
    require(envs['gmai-postgres-prod'].get('POSTGRES_PASSWORD_FILE') == '/run/secrets/aios/database/postgres_password', 'postgres_reference')
    api = envs['gmai-api-prod']
    require(MANDATORY <= {k for k, v in api.items() if v}, 'mandatory_reference')
    require(api.get('APP_ENV', '').strip().lower() in {'prod', 'production'} and api.get('AUTH_ENABLED', '').lower() == 'true' and (api.get('AUTH_ALLOW_HEADER_ROLE', '').lower() == 'false'), 'runtime_auth_policy')
    values = []
    for scope in sorted(SCOPES):
        directory = root / scope
        require(directory.is_dir() and (not directory.is_symlink()), 'secret_scope')
        for file in sorted(directory.iterdir()):
            require(file.is_file() and (not file.is_symlink()), 'secret_file')
            require(len(values) < 64 and file.stat().st_size <= 65536, 'secret_limit')
            value = bounded_secret(file)
            values.append(value)
    require(not (root / 'auth' / 'admin_password').exists(), 'legacy_bootstrap_copy')

    def resolve(key):
        relative = api[key][len('file:///run/secrets/aios/'):]
        return bounded_secret(root / relative)
    private = {'username': api.get('AUTH_ADMIN_USERNAME', 'admin'), 'password': resolve('AUTH_ADMIN_PASSWORD_REF'), 'jwt': resolve('JWT_SECRET_REF'), 'cookieName': api.get('AUTH_SESSION_COOKIE', 'gmai_session'), 'ttl': int(api.get('AUTH_SESSION_TTL_SECONDS') or 28800)}
    require(bool(private['username']) and bool(private['cookieName']), 'runtime_auth_policy')
    for scope in sorted(SHARED):
        require(not any((private['password'] in bounded_secret(file) for file in (root / scope).iterdir())), 'bootstrap_shared_copy')
    require(private['password'] not in DEFAULT_INSECURE_PASSWORDS and private['jwt'] not in DEFAULT_INSECURE_SECRETS, 'default_credentials')
    for env in envs.values():
        require(not any((secret in value for value in env.values() for secret in values)), 'environment_exposure')
    return (private, values)
_RUNTIME_RESOLVE_PY = r"""
import json
from app.core.config import settings, Settings
from app.core.secrets import SecretResolutionError
from app.services.llm_client import _provider_api_key
values={}
for key in ("database_password", "jwt_secret", "auth_admin_password", "automation_encryption_key",
            "automation_encryption_previous_key", "automation_webhook_secret", "document_access_token_secret",
            "minio_access_key", "minio_secret_key"):
    if getattr(settings,key+"_ref",""): values[key]=getattr(settings,key)
for key in ('deepseek_api_key','moonshot_api_key','gemini_api_key'):
    reference=getattr(settings,key+'_ref','')
    if reference: values[key]=_provider_api_key(value_setting=key,reference_setting=key+'_ref')
s=Settings(auth_admin_password='fallback',auth_admin_password_ref='file:///run/secrets/aios/bootstrap/phase22_definitely_missing')
try: s.auth_admin_password
except SecretResolutionError: pass
else: raise SystemExit(1)
print(json.dumps({"values":values,"policy":{"username":settings.auth_admin_username,"cookieName":settings.auth_session_cookie,"ttl":settings.auth_session_ttl_seconds}}))
"""
_DENIAL_PY = r"""
import json
from pathlib import Path
import sys
allowed=set(json.loads(sys.argv[1]))
for scope in ('database','auth','automation','documents','storage','llm','bootstrap'):
    if scope in allowed: continue
    try:
        list(Path('/run/secrets/aios',scope).iterdir())
    except (FileNotFoundError,PermissionError): pass
    else: raise SystemExit(1)
print('denied')
"""

def read_denials(container_data: dict[str, dict], private: dict, root: Path) -> None:
    database_value = private_run(['docker', 'exec', 'gmai-postgres-prod', 'cat', '/run/secrets/aios/database/postgres_password'], limit=65536).rstrip('\r\n')
    require(database_value == bounded_secret(root / 'database' / 'postgres_password'), 'postgres_resolution')
    for name in ('gmai-api-prod', 'gmai-worker-prod', 'gmai-api-migrate-prod'):
        prefix = ['docker', 'exec', name, 'python', '-c']
        if name == 'gmai-api-migrate-prod':
            prefix = ['docker', 'run', '--rm', '--pull', 'never', '--network', 'none', '--volumes-from', name, '--env-file', '/dev/stdin', container_data[name]['Image'], 'python', '-c']
            environment = '\n'.join((item for item in container_data[name]['Config']['Env'] if item.startswith('DATABASE_PASSWORD_REF='))) + '\n'
            resolved = json.loads(private_run(prefix + [_RUNTIME_RESOLVE_PY], input_value=environment, limit=262144))
        else:
            resolved = json.loads(private_run(prefix + [_RUNTIME_RESOLVE_PY], limit=262144))
        observed_policy = resolved['policy']
        actual_values = resolved['values']
        environment_values = dict((item.split('=', 1) for item in container_data[name]['Config']['Env']))
        expected = {}
        for key in SECRET_FIELDS:
            reference = environment_values.get(key + '_REF', '')
            if reference:
                relative = reference[len('file:///run/secrets/aios/'):]
                expected[key.lower()] = bounded_secret(root / relative)
        require(actual_values == expected and actual_values, 'runtime_resolution')
        resolved = actual_values
        if name == 'gmai-api-prod':
            require(observed_policy == {key: private[key] for key in ('username', 'cookieName', 'ttl')}, 'runtime_auth_policy')
            require(resolved.get('auth_admin_password') == private['password'] and resolved.get('jwt_secret') == private['jwt'], 'runtime_resolution')
        else:
            require('auth_admin_password' not in resolved, 'bootstrap_resolution')
        if name != 'gmai-api-prod':
            private_run(prefix + [_DENIAL_PY, json.dumps(sorted(CONTAINERS[name]))], input_value=environment if name == 'gmai-api-migrate-prod' else None, limit=8192)
    for name in CONTAINERS:
        if name in {'gmai-api-prod', 'gmai-worker-prod', 'gmai-api-migrate-prod'}:
            continue
        tests = ' && '.join(('test ! -e /run/secrets/aios/' + scope for scope in sorted(SCOPES - CONTAINERS[name])))
        private_run(['docker', 'exec', name, 'sh', '-c', tests], limit=8192)
_ASSET_SCAN = r"""
const fs=require('fs'),path=require('path');let s='';process.stdin.on('data',x=>{s+=x;if(s.length>4194304)process.exit(2)});
process.stdin.on('end',()=>{try{const secrets=JSON.parse(s);let files=0,bytes=0,exposed=false;
function walk(root){if(!fs.existsSync(root))throw Error();for(const name of fs.readdirSync(root)){const p=path.join(root,name),st=fs.lstatSync(p);if(st.isSymbolicLink())throw Error();if(st.isDirectory())walk(p);else if(st.isFile()){if(++files>10000||(bytes+=st.size)>134217728)throw Error();const fd=fs.openSync(p,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);let b;try{const size=fs.fstatSync(fd).size;if(size!==st.size)throw Error();b=Buffer.alloc(size+1);const got=fs.readSync(fd,b,0,b.length,0);if(got!==size)throw Error();b=b.subarray(0,got);}finally{fs.closeSync(fd)}if(secrets.some(v=>b.includes(Buffer.from(v))))exposed=true;}}}
walk('/app/.next/static');walk('/app/public');console.log(JSON.stringify({files,bytes,exposed}));}catch{process.exit(2)}});
"""

def scan_assets(values: list[str]) -> int:
    data = json.loads(private_run(['docker', 'exec', '-i', 'gmai-web-prod', 'node', '-e', _ASSET_SCAN], input_value=json.dumps(values), limit=8192))
    require(data.get('exposed') is False and 0 < data.get('files', 0) <= 10000, 'asset_exposure')
    return data['files']

def scan_logs(values: list[str], started: str, completed: str) -> int:
    count = 0
    for name in CONTAINERS:
        if name == 'gmai-api-migrate-prod':
            continue
        data = private_run(['docker', 'logs', '--since', started, '--until', completed, name], limit=8388608, merge_stderr=True)
        require(not any((value in data for value in values)), 'log_exposure')
        count += len(data.encode())
    require(count > 0, 'logs_incomplete')
    return count

def executor_context(tenant: str) -> OrganizationCommandContext:
    return OrganizationCommandContext(tenant_key=tenant, actor_id=TARGET_HOST_IDENTITY_EXECUTOR_ACTOR, actor_type=OrganizationActorType.system, authenticated_user_id='system', role='operator', department='Technology', position_key=None, authority_level=None)

def run_identity(session: Session, *, tenant_key: str, run_id: UUID, candidate_root: Path, secrets_root: Path, max_wait_seconds: int) -> dict:
    require(310 <= max_wait_seconds <= 86520, 'wait_budget')
    context = executor_context(tenant_key)
    run, network = validated_deployment_networking_contract(session, context, deployment_run_id=run_id, require_fresh_identity_boundaries=True)
    executor_sha = host.trusted_executor_commit_sha(ROOT)

    def identity():
        require(host.resolve_target_environment_fingerprint() == run.target_environment_fingerprint, 'host_identity')
        host.verify_release_checkout(candidate_root, expected_commit_sha=run.release_commit_sha, expected_configuration_fingerprint=run.release_configuration_fingerprint)
        return host.verify_running_release_identity(expected_commit_sha=run.release_commit_sha, expected_configuration_fingerprint=run.release_configuration_fingerprint)
    before = identity()
    started = datetime.now(timezone.utc).isoformat()
    details = {key: False for key in IDENTITY_REQUIRED_PROOFS}
    details.update(executor_commit_sha=executor_sha, observed_started_at=started, observed_completed_at=started, session_ttl_seconds=0, waited_seconds=0, asset_files_scanned=0, log_bytes_scanned=0, secret_values_recorded=False, failure_stage=None, failure_code=None, surface_contract='phase22.identity.finite-surfaces.v1')
    details['host_release_verified_before'] = True
    status = 'failed'
    stage = 'runtime'
    try:
        containers = {name: inspect_container(name) for name in CONTAINERS}
        pinned_runtime = runtime_configuration(containers)
        private, values = secret_material(containers, secrets_root)
        require(max_wait_seconds >= private['ttl'] + 10, 'wait_budget')
        details['session_ttl_seconds'] = private['ttl']
        details['runtime_configuration_verified'] = True
        details['runtime_secret_mounts_verified'] = True
        details['runtime_secret_references_verified'] = True
        details['runtime_environment_scan_verified'] = True
        read_denials(containers, private, secrets_root)
        details['runtime_secret_read_denial_verified'] = True
        details['asset_files_scanned'] = scan_assets(values)
        details['client_asset_scan_verified'] = True
        stage = 'browser'
        payload = {**private, 'api': 'https://' + network['api_hostname'], 'web': 'https://' + network['web_hostname'], 'maxWait': max_wait_seconds, 'secrets': values}
        pinned = (run.release_commit_sha, run.release_configuration_fingerprint, run.record_fingerprint)
        session.rollback()
        observed = json.loads(private_run(['node', str(ROOT / 'scripts/phase22_identity_browser.mjs')], input_value=json.dumps(payload), limit=16384, timeout=max_wait_seconds + 180))
        proof = observed.get('proof', {})
        browser_keys = set(IDENTITY_REQUIRED_PROOFS) - {'host_release_verified_before', 'host_release_verified_after', 'runtime_configuration_verified', 'runtime_secret_mounts_verified', 'runtime_secret_read_denial_verified', 'runtime_secret_references_verified', 'runtime_environment_scan_verified', 'client_asset_scan_verified', 'interval_log_scan_verified'}
        require(set(proof) == browser_keys | {'waited_seconds'}, 'browser_evidence')
        require(all((proof[key] is True for key in browser_keys)), 'browser_evidence')
        details.update(proof)
        stage = 'postflight'
        run, network_after = validated_deployment_networking_contract(session, context, deployment_run_id=run_id, require_fresh_identity_boundaries=True)
        require((run.release_commit_sha, run.release_configuration_fingerprint, run.record_fingerprint) == pinned, 'prepared_identity')
        require(identity() == before and network_after == network, 'release_changed')
        after_containers = {name: inspect_container(name) for name in CONTAINERS}
        require(runtime_configuration(after_containers) == pinned_runtime, 'runtime_changed')
        after_private, after_values = secret_material(after_containers, secrets_root)
        require(private == after_private and values == after_values, 'credential_changed')
        details['host_release_verified_after'] = True
        completed = datetime.now(timezone.utc).isoformat()
        details['log_bytes_scanned'] = scan_logs(values, started, completed)
        details['interval_log_scan_verified'] = True
        require(identity() == before, 'release_changed')
        final_containers = {name: inspect_container(name) for name in CONTAINERS}
        require(runtime_configuration(final_containers) == pinned_runtime, 'runtime_changed')
        final_private, final_values = secret_material(final_containers, secrets_root)
        require(private == final_private and values == final_values, 'credential_changed')
        details['observed_completed_at'] = datetime.now(timezone.utc).isoformat()
        status = 'satisfied'
    except Exception:
        details['failure_stage'] = stage
        details['failure_code'] = 'identity_probe_failed'
        details['observed_completed_at'] = datetime.now(timezone.utc).isoformat()
        run, _ = validated_deployment_networking_contract(session, context, deployment_run_id=run_id, require_fresh_identity_boundaries=True)
        identity()
    receipt = record_target_host_identity_receipt(session, context, deployment_run_id=run_id, status=status, observed_target_environment_fingerprint=run.target_environment_fingerprint, observed_release_commit_sha=run.release_commit_sha, observed_release_configuration_fingerprint=run.release_configuration_fingerprint, executor_commit_sha=executor_sha, redacted_details=details)
    return {'receipt_id': str(receipt.id), 'deployment_run_id': str(run_id), 'status': status}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', type=UUID, required=True)
    parser.add_argument('--tenant-key', default='default')
    parser.add_argument('--candidate-root', type=Path, required=True)
    parser.add_argument('--secrets-root', type=Path, required=True)
    parser.add_argument('--max-wait-seconds', type=int, required=True)
    args = parser.parse_args()
    try:
        register_models()
        with Session(engine) as session:
            payload = run_identity(session, tenant_key=args.tenant_key, run_id=args.run_id, candidate_root=args.candidate_root.resolve(), secrets_root=args.secrets_root.resolve(), max_wait_seconds=args.max_wait_seconds)
        print(json.dumps(payload, sort_keys=True))
        return 0 if payload['status'] == 'satisfied' else 1
    except Exception:
        print('Phase 22 identity executor failed; no satisfaction asserted.', file=sys.stderr)
        return 1
if __name__ == '__main__':
    raise SystemExit(main())
