"""Workspace summaries distinguish persisted review state from live file integrity."""
from test_api import client as client
from test_api import create, baseline, upload, decision, fresh
from handoffready.store import Store


def overview(client):
    result = client.get('/api/v1/projects')
    assert result.status_code == 200
    return result.json()['data'][0]


def test_overview_exposes_counts_without_private_content(client):
    decision(client, upload(client, baseline(client, create(client))))
    row = overview(client)
    assert row['saved_review'] == {
        'status': 'reviewed', 'baseline_approved': True, 'requirement_count': 1,
        'attention_count': 0, 'stale_review_count': 0, 'file_count': 1,
        'originals_verified': False,
    }
    assert row['updated_at']
    assert not any(key in row for key in ('brief', 'files', 'decisions', 'proposals'))
    assert 'SECRET PRIVATE NOTE' not in str(row)


def test_overview_never_claims_live_integrity_and_open_reconciles_damage(client, monkeypatch):
    project = decision(client, upload(client, baseline(client, create(client))))
    store = client.app.state.store
    stored = store.get(project['id'])['files'][0]
    (store.files / stored['_path']).write_bytes(b'tampered')
    original = store._original_error
    with monkeypatch.context() as patch:
        patch.setattr(store, '_original_error', lambda file: (_ for _ in ()).throw(AssertionError('list hashed original')))
        row = overview(client)
        assert row['saved_review']['status'] == 'reviewed'
        assert row['saved_review']['originals_verified'] is False
    assert store._original_error == original
    opened = fresh(client, project)
    assert opened['files'][0]['inspection'] == 'blocked'
    row = overview(client)
    assert row['saved_review']['stale_review_count'] == 1
    assert row['saved_review']['attention_count'] == 1
    assert row['saved_review']['status'] == 'draft_with_gaps'


def test_only_real_mutation_sets_activity_timestamp(client):
    project = create(client)
    store = client.app.state.store
    assert overview(client)['updated_at'] is None
    store.mutate(project['id'], None, lambda project, db: None)
    assert overview(client)['updated_at'] is None
    store.mutate(project['id'], None, lambda project, db: project.update(name='Renamed'))
    timestamp = overview(client)['updated_at']
    assert timestamp
    store.mutate(project['id'], None, lambda project, db: None)
    assert overview(client)['updated_at'] == timestamp


def test_restart_recovery_updates_activity_only_when_state_changes(tmp_path, monkeypatch):
    store = Store(tmp_path)
    untouched = store.create('Untouched legacy project', 10)
    active = store.create('Interrupted work', 10)
    monkeypatch.setattr('handoffready.store.now', lambda: '2026-10-14T12:00:00+00:00')
    store.mutate(active['id'], None, lambda project, db: project['jobs'].append({
        'id': 'pending-job', 'state': 'running', 'stage': 'matching',
    }))
    before = store.get(active['id'])
    monkeypatch.setattr('handoffready.store.now', lambda: '2026-10-15T12:00:00+00:00')
    restarted = Store(tmp_path)
    recovered = restarted.get(active['id'])
    assert recovered['jobs'][0]['state'] == 'interrupted'
    assert recovered['revision'] == before['revision'] + 1
    assert recovered['updated_at'] == '2026-10-15T12:00:00+00:00'
    assert restarted.get(untouched['id']) == untouched
    monkeypatch.setattr('handoffready.store.now', lambda: '2026-10-16T12:00:00+00:00')
    unchanged = Store(tmp_path)
    assert unchanged.get(active['id']) == recovered
    assert unchanged.get(untouched['id']) == untouched


def test_restart_original_reconciliation_updates_activity(client, monkeypatch):
    project = decision(client, upload(client, baseline(client, create(client))))
    store = client.app.state.store
    original = store.get(project['id'])['files'][0]
    (store.files / original['_path']).write_bytes(b'tampered')
    monkeypatch.setattr('handoffready.store.now', lambda: '2026-10-15T12:00:00+00:00')
    recovered = Store(store.directory).get(project['id'])
    assert recovered['updated_at'] == '2026-10-15T12:00:00+00:00'
    assert recovered['revision'] == project['revision'] + 1
    assert recovered['files'][0]['inspection'] == 'blocked'
    assert recovered['decisions'][0]['review_state'] == 'stale'
