import json
import logging
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace
from uuid import UUID, uuid4
from unittest.mock import Mock

from celery import Celery
from celery.beat import ScheduleEntry, Scheduler, SchedulingError
from celery.signals import after_task_publish
import pytest
from sqlmodel import select

from app.core.organization_task_transport import (
    OrganizationTaskTransport, SCAN_TASK_NAME, observe_scan_publication, uuid_text,
)
from app.models.domain import AuditLog, OrganizationExecutionAttempt, OrganizationalWorkItem
from app.services import organization_governance as owner
from app.tasks.organization_tasks import execute_organization_work_item_task, scan_organization_work_task


def _work(client, suffix):
    client.headers.update({'X-GMAI-Role': 'admin', 'X-GMAI-User': 'human-owner'})
    response = client.post('/api/v1/organization/work-items', json={
        'idempotency_key': f'transport-{suffix}-{uuid4()}', 'title': 'Synthetic transport work',
        'objective': 'Observe bounded internal task transport without external actions.',
        'action': 'internal.analysis',
    })
    assert response.status_code == 201, response.text
    return UUID(response.json()['id'])


def _started(session, work_id):
    return session.exec(select(AuditLog).where(AuditLog.entity_id == str(work_id),
        AuditLog.action == 'organization_work_execution_started')).one()


def test_worker_request_is_linked_to_atomic_claim_attempt_and_token(raw_client, db_session):
    work_id = _work(raw_client, 'worker')
    task_id, scan_id = str(uuid4()), str(uuid4())
    task = execute_organization_work_item_task
    task.push_request(id=task_id, parent_id=scan_id, root_id=scan_id, called_directly=False, is_eager=False)
    try:
        task.run(str(work_id))
    finally:
        task.pop_request()
    attempt = db_session.exec(select(OrganizationExecutionAttempt).where(OrganizationExecutionAttempt.work_item_id == work_id)).one()
    state = json.loads(_started(db_session, work_id).after_state_json)
    assert state['execution_token'] == attempt.execution_token
    assert state['attempt'] == attempt.attempt_number
    assert state['transport'] == {'task_id': task_id, 'parent_id': scan_id, 'root_id': scan_id,
                                  'origin_independently_verified': False}


@pytest.mark.parametrize('mode', ['direct', 'eager', 'malformed'])
def test_direct_eager_and_malformed_requests_remain_unknown(raw_client, db_session, mode):
    work_id = _work(raw_client, mode)
    task = execute_organization_work_item_task
    if mode == 'direct':
        task(str(work_id))
    elif mode == 'eager':
        task.apply(args=[str(work_id)], task_id=str(uuid4()), throw=True)
    else:
        task.push_request(id='secret-malformed-id', parent_id=str(uuid4()), root_id=str(uuid4()), called_directly=False, is_eager=False)
        try:
            task.run(str(work_id))
        finally:
            task.pop_request()
    assert json.loads(_started(db_session, work_id).after_state_json)['transport'] == OrganizationTaskTransport().audit_state()


def test_claim_commit_failure_persists_neither_attempt_nor_transport_audit(raw_client, db_session, monkeypatch):
    work_id = _work(raw_client, 'atomic')
    monkeypatch.setattr(db_session, 'commit', Mock(side_effect=RuntimeError('synthetic commit failure')))
    with pytest.raises(RuntimeError, match='synthetic commit failure'):
        owner._claim_work_execution(db_session, work_id, actor='test-worker',
            transport=OrganizationTaskTransport(str(uuid4()), str(uuid4()), str(uuid4())))
    db_session.rollback()
    assert db_session.get(OrganizationalWorkItem, work_id).status == 'queued'
    assert db_session.exec(select(OrganizationExecutionAttempt).where(OrganizationExecutionAttempt.work_item_id == work_id)).all() == []
    assert db_session.exec(select(AuditLog).where(AuditLog.entity_id == str(work_id), AuditLog.action == 'organization_work_execution_started')).all() == []


def test_scan_returns_actual_child_ids_and_redacted_partial_failure_log(raw_client, db_session, monkeypatch, caplog):
    ids = [_work(raw_client, str(index)) for index in range(3)]
    children = [str(uuid4()) for _ in ids]
    scan_id = str(uuid4())
    task = scan_organization_work_task
    publish = Mock(side_effect=[SimpleNamespace(id=children[0]), RuntimeError('broker://secret@private'), SimpleNamespace(id=children[2])])
    monkeypatch.setattr(execute_organization_work_item_task, 'delay', publish)
    task.push_request(id=scan_id, root_id=scan_id, parent_id=None, called_directly=False, is_eager=False)
    try:
        with caplog.at_level(logging.INFO, logger='app.core.organization_task_transport'):
            with pytest.raises(RuntimeError, match='organization_work_publication_failed') as failure:
                task.run(limit=3)
        assert failure.value.__cause__ is None
        assert 'broker://secret' not in caplog.text + str(failure.value)
        assert publish.call_count == 2
        log = json.loads(caplog.records[-1].getMessage().split(' ', 1)[1])
        assert log['scan_transport']['task_id'] == scan_id
        assert log['children'] == [{'work_item_id': str(ids[0]), 'child_task_id': children[0], 'publication_call_returned': True}]
        assert log['publication_unknown_work_item_id'] == str(ids[1])
        assert log['unattempted_work_item_ids'] == [str(ids[2])]
        assert not log['delivery_verified'] and not log['execution_verified']
        monkeypatch.setattr(execute_organization_work_item_task, 'delay', Mock(side_effect=[SimpleNamespace(id=item) for item in children]))
        result = task.run(limit=3)
        assert result['queued'] == 3
        assert [child['child_task_id'] for child in result['transport_observation']['children']] == children
    finally:
        task.pop_request()
    assert all(db_session.get(OrganizationalWorkItem, item).status == 'queued' for item in ids)


def test_uuid_and_signal_redaction_never_serialize_arbitrary_input(caplog):
    class Hostile:
        def __str__(self):
            raise AssertionError('arbitrary object serialized')
    assert uuid_text(Hostile()) is None
    with caplog.at_level(logging.INFO, logger='app.core.organization_task_transport'):
        observe_scan_publication(sender='other-task', headers={'id': str(uuid4())})
        observe_scan_publication(sender=SCAN_TASK_NAME, headers={'id': 'malformed-secret'})
        assert caplog.records == []
        observe_scan_publication(sender=SCAN_TASK_NAME, headers={'id': str(uuid4()), 'root_id': str(uuid4()),
            'parent_id': Hostile(), 'secret': 'header-secret'}, body='body-secret', routing_key='route-secret', exchange='exchange-secret')
    text = caplog.text
    assert not any(secret in text for secret in ('header-secret', 'body-secret', 'route-secret', 'exchange-secret', 'malformed-secret'))
    payload = json.loads(caplog.records[0].getMessage().split(' ', 1)[1])
    assert payload['parent_id'] is None
    assert payload['origin_independently_verified'] is False
    assert payload['delivery_verified'] is False


def test_real_scheduler_publish_signal_follows_producer_return_only(caplog):
    app = Celery('transport-test', broker='memory://', backend='cache+memory://')
    app.conf.task_publish_retry = False
    scheduler = Scheduler(app=app, lazy=True)
    entry = ScheduleEntry(name='scan-test', task=SCAN_TASK_NAME, args=(25,), schedule=30, app=app)
    after_task_publish.connect(observe_scan_publication, sender=SCAN_TASK_NAME, weak=False, dispatch_uid='transport-test')
    try:
        with app.connection_for_write() as connection:
            producer = app.amqp.Producer(connection)
            with caplog.at_level(logging.INFO, logger='app.core.organization_task_transport'):
                result = scheduler.apply_async(entry, producer=producer, advance=False)
                payload = json.loads(caplog.records[-1].getMessage().split(' ', 1)[1])
                assert payload['task_id'] == result.id
                caplog.clear()
                producer.publish = Mock(side_effect=RuntimeError('producer-failure-secret'))
                with pytest.raises(SchedulingError):
                    scheduler.apply_async(entry, producer=producer, advance=False)
                assert caplog.records == []
    finally:
        after_task_publish.disconnect(sender=SCAN_TASK_NAME, dispatch_uid='transport-test')
        app.close()


def test_scheduler_only_import_does_not_access_runtime_secrets_or_task_db_imports():
    code = '''import sys
import app.core.secrets as secrets
def denied(*args, **kwargs): raise AssertionError("secret resolver called")
secrets.resolve_runtime_secret = denied
from app.core.celery_app import celery_app
from celery.signals import after_task_publish
assert celery_app.conf.include == []
assert "app.core.db" not in sys.modules
assert not any(name.startswith("app.tasks.") for name in sys.modules)
assert not any(name.startswith("app.services.") for name in sys.modules)
assert any("organization-scan-publication-v1" in str(receiver[0]) for receiver in after_task_publish.receivers)
'''
    repository_root = Path(__file__).resolve().parents[3]
    import_paths = [str(repository_root / 'apps/api'), str(repository_root)]
    if os.environ.get('PYTHONPATH'):
        import_paths.append(os.environ['PYTHONPATH'])
    env = {**os.environ, 'PYTHONPATH': os.pathsep.join(import_paths),
           'CELERY_BEAT_SCHEDULER_ONLY': 'true',
           'JWT_SECRET_REF': '/nonexistent/synthetic-jwt-secret', 'DATABASE_URL': 'postgresql://unused',
           'REDIS_URL': 'redis://localhost:6379/0'}
    completed = subprocess.run([os.sys.executable, '-c', code], cwd=repository_root,
                               env=env, capture_output=True, timeout=15)
    assert completed.returncode == 0, completed.stderr.decode()


def test_direct_service_and_incomplete_request_have_unknown_transport(raw_client, db_session):
    work_id = _work(raw_client, 'service')
    owner.execute_work_item(db_session, db_session.get(OrganizationalWorkItem, work_id))
    assert json.loads(_started(db_session, work_id).after_state_json)['transport'] == OrganizationTaskTransport().audit_state()
    assert OrganizationTaskTransport.from_request(SimpleNamespace(id=str(uuid4()))).audit_state() == OrganizationTaskTransport().audit_state()


def test_held_missing_and_rejected_work_do_not_invent_transport_attempts(raw_client, db_session):
    work_id = _work(raw_client, 'held')
    work = db_session.get(OrganizationalWorkItem, work_id)
    work.department = 'Executive'
    db_session.add(work)
    db_session.commit()
    task = execute_organization_work_item_task
    task.push_request(id=str(uuid4()), root_id=str(uuid4()), parent_id=str(uuid4()), called_directly=False, is_eager=False)
    try:
        assert task.run(str(work_id))['status'] == 'held'
        assert task.run(str(uuid4()))['status'] == 'not_found'
        work.department = 'Operations'
        work.status = 'running'
        db_session.add(work)
        db_session.commit()
        assert task.run(str(work_id))['status'] == 'skipped'
    finally:
        task.pop_request()
    assert db_session.exec(select(OrganizationExecutionAttempt).where(OrganizationExecutionAttempt.work_item_id == work_id)).all() == []
    assert db_session.exec(select(AuditLog).where(AuditLog.entity_id == str(work_id), AuditLog.action == 'organization_work_execution_started')).all() == []
