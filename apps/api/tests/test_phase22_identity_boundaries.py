from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path
import pytest
from scripts import phase22_identity_boundaries as executor

def test_private_runner_caps_both_streams_and_sanitizes_failure() -> None:
    for code in ("import sys;print('private-token');sys.exit(2)", "import sys;sys.stderr.write('private-token'*10000)"):
        with pytest.raises(executor.ProbeError) as raised:
            executor.private_run([sys.executable, '-c', code], limit=512)
        assert 'private-token' not in str(raised.value)
    assert executor.private_run([sys.executable, '-c', "import sys;sys.stderr.write('bounded')"], merge_stderr=True) == 'bounded'

def test_private_runner_transmits_private_input_without_command_arguments() -> None:
    value = 'transient-value' * 10000
    output = executor.private_run([sys.executable, '-c', 'import sys; print(len(sys.stdin.read()))'], input_value=value, limit=512)
    assert int(output) == len(value)

def test_private_runner_timeout_is_fixed() -> None:
    with pytest.raises(executor.ProbeError, match='command_timeout'):
        executor.private_run([sys.executable, '-c', 'import time; time.sleep(3)'], timeout=0)

def _containers(root: Path) -> dict:
    data = {}
    refs = {'DATABASE_PASSWORD_REF': 'database/postgres_password', 'JWT_SECRET_REF': 'auth/jwt_secret', 'AUTH_ADMIN_PASSWORD_REF': 'bootstrap/admin_password', 'AUTOMATION_ENCRYPTION_KEY_REF': 'automation/key', 'AUTOMATION_WEBHOOK_SECRET_REF': 'automation/webhook', 'DOCUMENT_ACCESS_TOKEN_SECRET_REF': 'documents/token'}
    for scope in executor.SCOPES:
        (root / scope).mkdir()
    for relative in refs.values():
        (root / relative).write_text('distinct-private-' + relative)
    for name, scopes in executor.CONTAINERS.items():
        env = ['APP_ENV=production', 'AUTH_ENABLED=true', 'AUTH_ALLOW_HEADER_ROLE=false'] if name == 'gmai-api-prod' else []
        if name == 'gmai-postgres-prod':
            env.append('POSTGRES_PASSWORD_FILE=/run/secrets/aios/database/postgres_password')
        env += [f'{key}=file:///run/secrets/aios/{relative}' for key, relative in refs.items() if relative.split('/')[0] in scopes]
        data[name] = {'Config': {'Env': env}, 'State': {'Running': True}, 'Mounts': [{'Type': 'bind', 'RW': False, 'Source': str(root / scope), 'Destination': '/run/secrets/aios/' + scope} for scope in scopes]}
    return data

def test_runtime_mount_environment_and_copy_boundaries(tmp_path: Path) -> None:
    root = tmp_path / 'secrets'
    root.mkdir()
    data = _containers(root)
    private, values = executor.secret_material(data, root)
    assert private['ttl'] == 28800 and private['password'] in values
    data['gmai-worker-prod']['Config']['Env'].append('REDIS_URL=redis://user:private-embedded@redis:6379/0')
    with pytest.raises(executor.ProbeError, match='embedded_url_credential'):
        executor.secret_material(data, root)
    data['gmai-worker-prod']['Config']['Env'].pop()
    (root / 'auth' / 'backup').write_text(private['password'])
    with pytest.raises(executor.ProbeError, match='bootstrap_shared_copy'):
        executor.secret_material(data, root)

def test_extra_broad_alias_mount_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / 'secrets'
    root.mkdir()
    data = _containers(root)
    data['gmai-worker-prod']['Mounts'].append({'Type': 'bind', 'RW': False, 'Source': str(root.parent), 'Destination': '/host-backup'})
    with pytest.raises(executor.ProbeError, match='mount_scope'):
        executor.secret_material(data, root)

def test_actual_node_signature_verifier_rejects_tampering_and_matches_python_contract() -> None:
    root = Path(__file__).resolve().parents[3]
    helper = (root / 'scripts/phase22_identity_browser.mjs').as_uri()
    source = f"\nimport assert from 'node:assert/strict';\nimport {{createHmac}} from 'node:crypto';\nimport {{verifiedClaims}} from {json.dumps(helper)};\nconst key='private-test-signing-key'; const iat=Math.floor(Date.now()/1000);\nfunction token(claims) {{const payload=Buffer.from(JSON.stringify(claims)).toString('base64url');return payload+'.'+createHmac('sha256',key).update(payload).digest('hex');}}\nconst claims={{v:1,iat,exp:iat+300,username:'operator',role:'admin'}};\nassert.equal(verifiedClaims(token(claims),key,300).exp,claims.exp);\nfor(const replacement of [{{...claims,v:2}},{{...claims,exp:iat+301}},{{...claims,iat:'bad'}},{{...claims,iat:iat-100,exp:iat+200}}]) {{assert.throws(()=>verifiedClaims(token(replacement),key,300));}}\nassert.throws(()=>verifiedClaims(token(claims),'wrong-key',300));\nassert.throws(()=>verifiedClaims(token(claims)+'extra',key,300));\n"
    result = subprocess.run(['node', '--input-type=module', '-e', source], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

def test_identity_gate_freshness_blocks_before_host_or_secret_probe(monkeypatch, tmp_path):
    from uuid import uuid4
    calls = []

    def reject(*args, **kwargs):
        assert kwargs['require_fresh_identity_boundaries'] is True
        raise executor.ProbeError('existing_receipt')
    monkeypatch.setattr(executor, 'validated_deployment_networking_contract', reject)
    monkeypatch.setattr(executor.host, 'trusted_executor_commit_sha', lambda *a: calls.append('host'))
    with pytest.raises(executor.ProbeError, match='existing_receipt'):
        executor.run_identity(object(), tenant_key='default', run_id=uuid4(), candidate_root=tmp_path, secrets_root=tmp_path, max_wait_seconds=310)
    assert calls == []

def test_actual_runtime_reference_values_must_match_their_own_fields(monkeypatch, tmp_path):
    root = tmp_path / 'secrets'
    root.mkdir()
    data = _containers(root)
    private, values = executor.secret_material(data, root)
    refs = dict((item.split('=', 1) for item in data['gmai-api-prod']['Config']['Env'] if '_REF=' in item))
    actual = {key.removesuffix('_REF').lower(): (root / value.split('/run/secrets/aios/')[1]).read_text() for key, value in refs.items()}
    actual['database_password'] = actual['jwt_secret']

    def fake_run(command, **kwargs):
        if command[2] == 'gmai-postgres-prod':
            return (root / 'database' / 'postgres_password').read_text()
        return json.dumps({'values': actual, 'policy': {}})
    monkeypatch.setattr(executor, 'private_run', fake_run)
    with pytest.raises(executor.ProbeError, match='runtime_resolution'):
        executor.read_denials(data, private, root)

def test_private_runtime_snapshot_detects_same_image_recreation_and_cors_change():
    value = {'Id': 'first', 'Image': 'same-image', 'Config': {'Env': ['CORS_ALLOWED_ORIGINS=https://web.example.eu'], 'Labels': {}}, 'Mounts': []}
    before = executor.runtime_configuration({'api': value})
    value['Id'] = 'second'
    assert executor.runtime_configuration({'api': value}) != before
    value['Id'] = 'first'
    value['Config']['Env'] = ['CORS_ALLOWED_ORIGINS=https://other.example.eu']
    assert executor.runtime_configuration({'api': value}) != before

def test_log_scan_includes_stderr_and_denies_exposure(monkeypatch):

    def fake_run(command, **kwargs):
        assert kwargs['merge_stderr'] is True
        return 'stderr-only-private-credential'
    monkeypatch.setattr(executor, 'private_run', fake_run)
    with pytest.raises(executor.ProbeError, match='log_exposure'):
        executor.scan_logs(['private-credential'], '2026-10-04T00:00:00+00:00', '2026-10-04T01:00:00+00:00')

def test_input_backpressure_remains_deadline_bounded():
    with pytest.raises(executor.ProbeError, match='command_timeout'):
        executor.private_run([sys.executable, '-c', 'import time;time.sleep(3)'], input_value='x' * 1000000, timeout=1)

@pytest.mark.parametrize('drift', ['container', 'credential', 'browser'])
def test_orchestration_drift_or_failed_browser_never_satisfies(monkeypatch, tmp_path, drift):
    from types import SimpleNamespace
    from uuid import uuid4
    from app.services.production_deployment_acceptance import IDENTITY_REQUIRED_PROOFS
    run = SimpleNamespace(id=uuid4(), target_environment_fingerprint='e' * 64, release_commit_sha='a' * 40, release_configuration_fingerprint='b' * 64, record_fingerprint='c' * 64)
    network = {'api_hostname': 'api.example.eu', 'web_hostname': 'web.example.eu'}
    monkeypatch.setattr(executor, 'validated_deployment_networking_contract', lambda *a, **kw: (run, network))
    monkeypatch.setattr(executor.host, 'trusted_executor_commit_sha', lambda *a: 'd' * 40)
    monkeypatch.setattr(executor.host, 'resolve_target_environment_fingerprint', lambda: run.target_environment_fingerprint)
    monkeypatch.setattr(executor.host, 'verify_release_checkout', lambda *a, **kw: None)
    monkeypatch.setattr(executor.host, 'verify_running_release_identity', lambda **kw: ())
    snapshots = 0

    def snapshot(containers):
        nonlocal snapshots
        snapshots += 1
        return 'changed' if drift == 'container' and snapshots > 1 else 'same'
    monkeypatch.setattr(executor, 'runtime_configuration', snapshot)
    monkeypatch.setattr(executor, 'inspect_container', lambda name: {})
    material_count = 0

    def material(*args):
        nonlocal material_count
        material_count += 1
        password = 'changed' if drift == 'credential' and material_count > 1 else 'private'
        return ({'ttl': 300, 'password': password}, ['private'])
    monkeypatch.setattr(executor, 'secret_material', material)
    monkeypatch.setattr(executor, 'read_denials', lambda *a: None)
    monkeypatch.setattr(executor, 'scan_assets', lambda *a: 1)
    monkeypatch.setattr(executor, 'scan_logs', lambda *a: 100)

    def browser(*args, **kwargs):
        if drift == 'browser':
            raise executor.ProbeError('private-upstream-secret')
        browser_keys = set(IDENTITY_REQUIRED_PROOFS) - {'host_release_verified_before', 'host_release_verified_after', 'runtime_configuration_verified', 'runtime_secret_mounts_verified', 'runtime_secret_read_denial_verified', 'runtime_secret_references_verified', 'runtime_environment_scan_verified', 'client_asset_scan_verified', 'interval_log_scan_verified'}
        return json.dumps({'proof': {**{key: True for key in browser_keys}, 'waited_seconds': 301}})
    monkeypatch.setattr(executor, 'private_run', browser)
    persisted = []

    def writer(*args, **kwargs):
        persisted.append(kwargs)
        return SimpleNamespace(id=uuid4())
    monkeypatch.setattr(executor, 'record_target_host_identity_receipt', writer)
    result = executor.run_identity(SimpleNamespace(rollback=lambda: None), tenant_key='default', run_id=run.id, candidate_root=tmp_path, secrets_root=tmp_path, max_wait_seconds=310)
    assert result['status'] == 'failed' and persisted[0]['status'] == 'failed'
    assert persisted[0]['redacted_details']['failure_code'] == 'identity_probe_failed'
    assert 'private-upstream-secret' not in json.dumps(persisted[0], default=str)
