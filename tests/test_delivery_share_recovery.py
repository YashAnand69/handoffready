"""Hard-process fault checks on disposable data; no real send or human review.

Terminate before/after the SQLite commit, without Python cleanup, then inspect
durable exports, permissions and verification receipts from a new process/store.
These tests establish process-interruption behavior, not power-loss durability.
"""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import secrets
import socket
import time

import httpx
import pytest

from handoffready.api import create_app
from handoffready.delivery import DeliveryService
from handoffready.store import Store
from test_api import baseline, create, decision, upload
from test_delivery_api import bound_job
from test_delivery_context_api import local_client
from test_delivery_share import share as share, SHARE_CONFIG
from test_delivery_share import BINDING, DEST, authorize, issued, preview


ROOT = Path(__file__).resolve().parents[1]
CRASH_CODE = 86
CRASH_PROGRAM = r'''
import base64,json,os,sys
from contextlib import contextmanager
from handoffready.delivery import DeliveryBinding,DeliveryService
from handoffready.store import Store,exclusive_directory

args=json.loads(sys.stdin.read())
with exclusive_directory(args['directory']):
    store=Store(args['directory'])
    shares=DeliveryService(store).shares
    binding=DeliveryBinding(**args['binding'])
    original=store.connection
    @contextmanager
    def interrupted_connection():
        transaction=False
        with original() as db:
            yield db
            transaction=db.in_transaction
            if transaction and args['boundary']=='before_commit':
                os._exit(86)
        if transaction and args['boundary']=='after_commit':
            os._exit(86)
    store.connection=interrupted_connection
    if args['action']=='authorize':
        shares.create(args['project'],binding,args['destination'],'crash-authorize',
            **args['payload'])
    elif args['action']=='issue':
        shares.issue(args['job'],binding,args['destination'],args['intent'],
            'crash-issue',args['sha'])
    elif args['action']=='verify':
        shares.verify(args['project'],args['intent'],'crash-verify',
            attempt_id=args['attempt'],message_url=args['message_url'],
            content=base64.b64decode(args['content']),confirmed_destination=True)
raise AssertionError('The declared transaction boundary was never reached')
'''


def crash(c, p, job, action, boundary, **arguments):
    body = {
        'directory': str(c.app.state.store.directory), 'project': p['id'],
        'job': job, 'action': action, 'boundary': boundary,
        'binding': {'server': BINDING.server, 'room': BINDING.room},
        'destination': DEST, **arguments,
    }
    result = subprocess.run(
        [sys.executable, '-c', CRASH_PROGRAM], input=json.dumps(body),
        text=True, capture_output=True, timeout=15,
        env={**os.environ, 'PYTHONPATH': str(ROOT / 'backend')},
    )
    assert result.returncode == CRASH_CODE, result.stderr
    store = Store(c.app.state.store.directory)
    return store, DeliveryService(store).shares


def original_bytes(store):
    return {p.name: p.read_bytes() for p in store.files.iterdir()}


@pytest.mark.parametrize('boundary', ['before_commit', 'after_commit'])
def test_hard_stop_authorization_has_all_or_none_and_replay_creates_one_export(share, boundary):
    c, p, job = share
    store = c.app.state.store
    before = store.get(p['id'])
    files = original_bytes(store)
    view = preview(c, p)
    payload = {
        'expected_revision': view['source_revision'],
        'expected_hash': view['input_hash'], 'preview_hash': view['preview_hash'],
        'confirmed_reviewed': True,
    }
    recovered, shares = crash(c, p, job, 'authorize', boundary, payload=payload)
    committed = boundary == 'after_commit'
    with recovered.connection() as db:
        assert db.execute('SELECT count(*) FROM exports').fetchone()[0] == int(committed)
        assert db.execute('SELECT count(*) FROM delivery_shares').fetchone()[0] == int(committed)
        assert db.execute("SELECT count(*) FROM delivery_operations WHERE operation_key='crash-authorize'").fetchone()[0] == int(committed)
    if not committed:
        assert recovered.get(p['id']) == before
    result = shares.create(p['id'], BINDING, DEST, 'crash-authorize', **payload)
    again = shares.create(p['id'], BINDING, DEST, 'crash-authorize', **payload)
    assert result == again
    assert len(recovered.get(p['id'])['exports']) == len(shares.read_project(p['id'])) == 1
    assert recovered.get(p['id'])['decisions'] == before['decisions']
    assert original_bytes(recovered) == files


@pytest.mark.parametrize('boundary', ['before_commit', 'after_commit'])
def test_hard_stop_issue_reconciles_permission_without_regrant_after_commit(share, boundary):
    c, p, job = share
    created, _ = authorize(c, p)
    intent, sha = created['result']['intent_id'], created['result']['artifact_sha256']
    before = c.app.state.store.get(p['id'])
    recovered, shares = crash(c, p, job, 'issue', boundary, intent=intent, sha=sha)
    committed = boundary == 'after_commit'
    view = shares.read_project(p['id'])[0]
    assert view['state'] == ('issued_unverified' if committed else 'authorized')
    assert len(view['events']) == int(committed)
    with recovered.connection() as db:
        assert db.execute("SELECT count(*) FROM delivery_operations WHERE operation_key='crash-issue'").fetchone()[0] == int(committed)
    result = shares.issue(job, BINDING, DEST, intent, 'crash-issue', sha)['result']
    assert result['send_permitted'] is (not committed)
    if committed:
        assert result['switch_send_arguments'] is None
        assert result['attempt_id'] == view['events'][0]['attempt_id']
    replay = shares.issue(job, BINDING, DEST, intent, 'crash-issue', sha)['result']
    assert replay['send_permitted'] is False and replay['switch_send_arguments'] is None
    assert len(shares.read_project(p['id'])[0]['events']) == 1
    assert recovered.get(p['id']) == before


@pytest.mark.parametrize('boundary', ['before_commit', 'after_commit'])
def test_hard_stop_verification_reconciles_one_receipt_without_changing_record(share, boundary):
    c, p, job = share
    intent, material, issue = issued(c, p, job)
    attempt = issue['result']['attempt_id']
    before = c.app.state.store.get(p['id'])
    url = DEST['url'] + '/333'
    recovered, shares = crash(c, p, job, 'verify', boundary, intent=intent,
        attempt=attempt, message_url=url, content=material['content_base64'])
    committed = boundary == 'after_commit'
    view = shares.read_project(p['id'])[0]
    assert view['state'] == ('operator_confirmed' if committed else 'issued_unverified')
    assert len(view['events']) == (2 if committed else 1)
    result = shares.verify(p['id'], intent, 'crash-verify', attempt_id=attempt,
        message_url=url, content=base64.b64decode(material['content_base64']),
        confirmed_destination=True)
    replay = shares.verify(p['id'], intent, 'crash-verify', attempt_id=attempt,
        message_url=url, content=base64.b64decode(material['content_base64']),
        confirmed_destination=True)
    assert replay == result
    assert result['result']['verification'] == 'operator_checked_destination_and_exact_bytes'
    assert len(shares.read_project(p['id'])[0]['events']) == 2
    assert recovered.get(p['id']) == before
    with recovered.connection() as db:
        assert db.execute('SELECT md FROM exports WHERE id=?', (view['export_id'],)).fetchone()[0].encode() == base64.b64decode(material['content_base64'])


@pytest.fixture
def server_packet(tmp_path):
    """Close the seed app before any real server owns its disposable directory."""
    directory = tmp_path / 'data'
    config = {**SHARE_CONFIG, 'token': secrets.token_urlsafe(32)}
    with local_client(create_app(directory, delivery_config=config)) as c:
        p = decision(c, upload(c, baseline(c, create(c))))
        job = bound_job(c, p)
        created, _ = authorize(c, p)
        intent = created['result']['intent_id']
        expected = c.app.state.store.get(p['id'])
        with c.app.state.store.connection() as db:
            markdown = db.execute('SELECT md FROM exports').fetchone()[0]
    config_file = tmp_path / 'server-config.json'
    config_file.write_text(json.dumps(config))
    config_file.chmod(0o600)
    with socket.socket() as available:
        available.bind(('127.0.0.1', 0))
        port = available.getsockname()[1]
    origin = f'http://127.0.0.1:{port}'
    env = {**os.environ, 'HANDOFFREADY_DATA': str(directory),
        'HANDOFFREADY_PORT': str(port), 'HANDOFFREADY_DELIVERY_CONFIG': str(config_file)}
    yield directory, config, env, origin, p, job, intent, created['result']['artifact_sha256'], expected, markdown


def start_server(env):
    return subprocess.Popen([sys.executable, str(ROOT / 'scripts/run.py')],
        cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def ready(client, process):
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        try:
            r = client.get('/api/v1/bootstrap')
            if r.status_code == 200:
                return r.json()['data']['token']
        except httpx.TransportError:
            pass
        assert process.poll() is None, 'Disposable recovery server exited before readiness'
        time.sleep(.05)
    raise AssertionError('Disposable recovery server did not become ready')


def stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    if process.stderr:
        process.stderr.close()


def test_real_server_disconnect_restart_keeps_unknown_send_and_refuses_regrant(server_packet):
    directory, config, env, origin, p, job, intent, sha, expected, markdown = server_packet
    process = start_server(env)
    second = None
    scoped = {'Origin': origin, 'X-Delivery-Token': config['token'],
        'X-Delivery-Binding': config['binding_id']}
    payload = {'operation_key': 'http-issue', 'artifact_sha256': sha}
    issue_path = f'/api/v1/delivery/jobs/{job}/shares/{intent}/issue'
    try:
        with httpx.Client(base_url=origin, trust_env=False, timeout=2) as client:
            old_token = ready(client, process)
            first = client.post(issue_path, headers=scoped, json=payload)
            assert first.status_code == 200, first.text
            first = first.json()['data']['result']
            assert first['send_permitted'] is True
            # Permission was consumed; deliberately make no external send.
            process.kill()
            assert process.wait(timeout=5) < 0
        with httpx.Client(base_url=origin, trust_env=False, timeout=.5) as offline:
            with pytest.raises(httpx.TransportError):
                offline.post(issue_path, headers=scoped, json=payload)
        second = start_server(env)
        with httpx.Client(base_url=origin, trust_env=False, timeout=2) as client:
            new_token = ready(client, second)
            local = {'Origin': origin, 'X-Handoff-Token': new_token}
            assert client.get('/api/v1/projects', headers={**local, 'X-Handoff-Token': old_token}).status_code == 403
            replay = client.post(issue_path, headers=scoped, json=payload)
            assert replay.status_code == 200, replay.text
            replay = replay.json()['data']['result']
            assert replay['attempt_id'] == first['attempt_id']
            assert replay['send_permitted'] is False and replay['switch_send_arguments'] is None
            history = client.get(f'/api/v1/projects/{p["id"]}/delivery-shares', headers=local).json()['data']['items']
            assert len(history) == 1 and history[0]['state'] == 'issued_unverified'
            assert len(history[0]['events']) == 1
            material = client.get(f'/api/v1/delivery/jobs/{job}/shares/{intent}/material', headers=scoped)
            assert material.status_code == 409
            # No local approval, duplicate export or human verification appeared.
        stop(second)
        recovered = Store(directory)
        assert recovered.get(p['id']) == expected
        with recovered.connection() as db:
            assert db.execute('SELECT md FROM exports').fetchall() == [(markdown,)]
    finally:
        stop(process)
        if second is not None:
            stop(second)


def test_second_server_refuses_owned_data_without_recovering_or_altering_it(server_packet):
    directory, config, env, origin, p, job, intent, sha, expected, markdown = server_packet
    process = start_server(env)
    try:
        with httpx.Client(base_url=origin, trust_env=False, timeout=2) as client:
            token = ready(client, process)
            other = subprocess.run([sys.executable, str(ROOT / 'scripts/run.py')],
                cwd=ROOT, env=env, capture_output=True, timeout=10)
            assert other.returncode != 0
            assert b'already open in another HandoffReady process' in other.stderr
            assert config['token'].encode() not in other.stdout + other.stderr
            assert process.poll() is None
            headers = {'Origin': origin, 'X-Handoff-Token': token}
            history = client.get(f'/api/v1/projects/{p["id"]}/delivery-shares', headers=headers).json()['data']['items']
            assert len(history) == 1 and history[0]['state'] == 'authorized'
            assert history[0]['events'] == []
    finally:
        stop(process)
    assert Store(directory).get(p['id']) == expected
