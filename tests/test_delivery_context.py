"""Synthetic context safety checks; no model output or external evidence."""
import json
import sqlite3

import pytest

from handoffready.delivery import DeliveryBinding, DeliveryService
from handoffready.delivery_context import DeliveryContext, context_hold, install_context_schema, sync_source_context
from handoffready.store import Store, StoreError, canonical, digest, input_hash, source_hash

BINDING = DeliveryBinding('https://switch.example.com', 'context-room')


@pytest.fixture
def room(tmp_path):
    store = Store(tmp_path)
    project = store.create('Synthetic contextual packet', 10)
    def approve(value, db):
        value['baseline'].update(state='approved', hash=digest(['synthetic']))
        value['baseline']['requirements'] = [{'id': 'r1', 'title': 'Synthetic guide', 'checks': [
            {'kind': 'manual', 'instruction': 'PRIVATE manual instruction'},
            {'kind': 'literal_text', 'needle': 'PRIVATE literal expectation'}]}]
    project = store.mutate(project['id'], project['revision'], approve)
    delivery = DeliveryService(store)
    job_id = delivery.create_job(BINDING, project['id'], 'create')['result']['job_id']
    return store, project['id'], delivery, DeliveryContext(delivery), job_id


def current(room):
    store, project_id, _, context, _ = room
    project = store.get(project_id)
    return project, context.read_project(project_id)


def propose(room, key='question', **overrides):
    _, _, _, context, job_id = room
    project, state = current(room)
    payload = dict(expected_revision=project['revision'], expected_hash=input_hash(project), expected_epoch=state['context_epoch'],
                   requirement_id='r1', file_ids=[], question='Which correction should the guide use?', source_ref='synthetic:question')
    payload.update(overrides)
    return context.propose_question(job_id, BINDING, key, **payload)


def reply(room, question_id, key='reply', **overrides):
    _, project_id, _, context, job_id = room
    question = next(q for q in context.read_project(project_id)['questions'] if q['question_id'] == question_id)
    payload = dict(question_id=question_id, question_input_hash=question['input_hash'], source_ref='synthetic:' + key,
                   reported_speaker='Synthetic teammate', text='Use the corrected instruction.\nThis is synthetic text.')
    payload.update(overrides)
    return context.record_reply(job_id, BINDING, key, **payload)


def resolve(room, question_id, key='resolve', action='accept', **overrides):
    _, _, _, context, job_id = room
    project, state = current(room)
    question = next(q for q in state['questions'] if q['question_id'] == question_id)
    ids = [r['reply_id'] for r in question['replies']]
    payload = dict(question_id=question_id, expected_revision=project['revision'], expected_hash=input_hash(project), expected_epoch=state['context_epoch'],
                   action=action, covered_reply_ids=ids, used_reply_ids=ids if action == 'accept' else [], reason='Reviewed the synthetic source.')
    payload.update(overrides)
    return context.resolve(job_id, BINDING, key, **payload)


def assert_error(code, call):
    with pytest.raises(StoreError) as caught:
        call()
    assert caught.value.code == code


def test_questions_are_immutable_provisional_and_sanitized(room):
    store, project_id, _, context, job_id = room
    before = canonical(store.get(project_id))
    result = propose(room)
    assert result['result']['assessment_saved'] is False
    assert result['result']['context_epoch'] == 1
    assert canonical(store.get(project_id)) == before
    question = context.read_project(project_id)['questions'][0]
    assert question['source_hash'] == source_hash(store.get(project_id))
    assert question['state'] == 'pending' and question['provenance'] == 'unverified'
    assert 'PRIVATE' not in canonical(question['evidence'])
    with store.connection() as db:
        hold = context_hold(db, project_id)
    assert hold['pending_context_count'] == 1 and hold['context_epochs'][job_id] == 1
    assert 'Which correction' not in canonical(hold)


def test_accept_a_does_not_expire_b_and_result_has_committed_currency(room):
    store, project_id, _, context, _ = room
    a = propose(room, 'a')['result']['question_id']
    b = propose(room, 'b')['result']['question_id']
    reply(room, a)
    original = store.get(project_id)
    result = resolve(room, a)
    project, state = current(room)
    assert result['input_hash'] == input_hash(project) != input_hash(original)
    assert result['source_revision'] == project['revision'] == original['revision'] + 1
    assert source_hash(project) == source_hash(original)
    assert [(q['question_id'], q['state']) for q in state['questions']] == [(a, 'resolved'), (b, 'pending')]
    resolution = state['questions'][0]['latest_resolution']
    assert (resolution['source_revision'], resolution['input_hash'], resolution['context_epoch']) == (result['source_revision'], result['input_hash'], result['result']['context_epoch'])
    with store.connection() as db:
        assert context_hold(db, project_id)['pending_context_count'] == 1


def test_source_change_latches_history_and_late_replies_never_reopen(room):
    store, project_id, _, context, _ = room
    question_id = propose(room)['result']['question_id']
    reply(room, question_id)
    resolve(room, question_id)
    original = store.get(project_id)
    original_baseline = original['baseline']['hash']
    changed = store.mutate(project_id, original['revision'], lambda p, db: p['baseline'].update(hash='changed'))
    assert not changed['delivery_context_basis']
    assert context.read_project(project_id)['questions'][0]['state'] == 'superseded'
    late = reply(room, question_id, 'late')
    assert late['result']['state'] == 'superseded'
    restored = store.mutate(project_id, changed['revision'], lambda p, db: p['baseline'].update(hash=original_baseline))
    assert source_hash(restored) == source_hash(original)
    assert context.read_project(project_id)['questions'][0]['state'] == 'superseded'
    assert_error('delivery_question_historical', lambda: resolve(room, question_id, 'historical'))
    with store.connection() as db:
        assert not context_hold(db, project_id)['blocked']
        assert len(db.execute('SELECT id FROM delivery_resolutions').fetchall()) == 2


def test_reply_reopens_exact_set_and_duplicate_does_not_advance_epoch(room):
    _, project_id, _, context, _ = room
    question_id = propose(room)['result']['question_id']
    first = reply(room, question_id, 'one')
    resolve(room, question_id)
    second = reply(room, question_id, 'two')
    assert second['result']['state'] == 'pending'
    duplicate = reply(room, question_id, 'duplicate', source_ref='synthetic:two')
    assert duplicate['result']['reply_id'] == second['result']['reply_id']
    assert duplicate['result']['context_epoch'] == second['result']['context_epoch']
    assert_error('delivery_source_conflict', lambda: reply(room, question_id, 'conflict', source_ref='synthetic:one', text='Different'))
    assert_error('delivery_reply_set_conflict', lambda: resolve(room, question_id, 'incomplete', covered_reply_ids=[first['result']['reply_id']], used_reply_ids=[first['result']['reply_id']]))
    resolve(room, question_id, 'dismiss-followup', action='dismiss')
    question = context.read_project(project_id)['questions'][0]
    assert question['state'] == 'resolved'
    assert question['active_context']['used_reply_ids'] == [first['result']['reply_id']]


def test_reaccept_identical_basis_preserves_reviews_replace_withdraw_invalidate(room):
    store, project_id, _, context, _ = room
    question_id = propose(room)['result']['question_id']
    reply(room, question_id, 'one')['result']['reply_id']
    resolve(room, question_id)
    def assess(p, db):
        p['decisions'] = [{'requirement_id': 'r1', 'file_ids': [], 'review_state': 'confirmed', 'input_hash': input_hash(p)}]
    project = store.mutate(project_id, None, assess)
    before_hash = input_hash(project)
    same = resolve(room, question_id, 'same')
    assert same['input_hash'] == before_hash
    assert store.get(project_id)['decisions'][0]['review_state'] == 'confirmed'
    second = reply(room, question_id, 'two')['result']['reply_id']
    resolve(room, question_id, 'replace', used_reply_ids=[second])
    project = store.get(project_id)
    assert project['decisions'][0]['review_state'] == 'stale'
    assert context.read_project(project_id)['questions'][0]['active_context']['used_reply_ids'] == [second]
    store.mutate(project_id, None, assess)
    resolve(room, question_id, 'withdraw', action='withdraw')
    assert not store.get(project_id)['delivery_context_basis']
    assert input_hash(store.get(project_id)) == source_hash(store.get(project_id))
    assert store.get(project_id)['decisions'][0]['review_state'] == 'stale'


def test_rename_and_noop_preserve_current_questions(room):
    store, project_id, _, context, _ = room
    question_id = propose(room)['result']['question_id']
    reply(room, question_id)
    resolve(room, question_id)
    before, before_state = current(room)
    renamed = store.mutate(project_id, before['revision'], lambda p, db: p.update(name='Renamed'))
    store.mutate(project_id, renamed['revision'], lambda p, db: p['baseline'].update(state='approved'))
    after, state = current(room)
    assert input_hash(after) == input_hash(before)
    assert state['context_epoch'] == before_state['context_epoch']
    assert state['questions'][0]['state'] == 'resolved'


def test_binding_and_replay_precede_currency_checks(room):
    store, project_id, _, context, job_id = room
    project, state = current(room)
    payload = dict(expected_revision=project['revision'], expected_hash=input_hash(project), expected_epoch=state['context_epoch'], requirement_id='r1', file_ids=[], question='Question', source_ref='source')
    result = context.propose_question(job_id, BINDING, 'stable', **payload)
    store.mutate(project_id, project['revision'], lambda p, db: p.update(name='Later'))
    assert context.propose_question(job_id, BINDING, 'stable', **payload) == result
    assert_error('delivery_binding_refused', lambda: context.propose_question(job_id, DeliveryBinding('https://switch.example.com', 'other'), 'stable', **payload))
    assert_error('delivery_operation_conflict', lambda: context.propose_question(job_id, BINDING, 'stable', **dict(payload, question='Different')))
    assert_error('revision_conflict', lambda: context.propose_question(job_id, BINDING, 'new', **payload))


def test_resolution_replay_returns_original_committed_result(room):
    _, _, _, context, job_id = room
    question_id = propose(room)['result']['question_id']
    reply(room, question_id)
    project, state = current(room)
    ids = [r['reply_id'] for r in state['questions'][0]['replies']]
    payload = dict(question_id=question_id, expected_revision=project['revision'], expected_hash=input_hash(project), expected_epoch=state['context_epoch'], action='accept', covered_reply_ids=ids, used_reply_ids=ids, reason='Reviewed')
    result = context.resolve(job_id, BINDING, 'stable-resolution', **payload)
    reply(room, question_id, 'later')
    assert context.resolve(job_id, BINDING, 'stable-resolution', **payload) == result


def test_legacy_unknown_anchor_dismiss_only_and_real_edit_supersedes(room):
    store, project_id, _, context, job_id = room
    project = store.get(project_id)
    with store.connection() as db:
        context.record_legacy(db, {'id': job_id}, project, 'legacy', 'r1', 'Unverified old blocker', 1, '0' * 64)
    question = context.read_project(project_id)['questions'][0]
    assert question['legacy'] and question['source_hash'] is None and question['source_anchor'] == 'unknown'
    assert question['source_revision'] == 1 and question['input_hash'] == '0' * 64
    assert question['state'] == 'pending'
    reply(room, 'legacy')
    assert_error('delivery_legacy_dismiss_only', lambda: resolve(room, 'legacy'))
    resolve(room, 'legacy', action='dismiss')
    with store.connection() as db:
        context.record_legacy(db, {'id': job_id}, project, 'legacy2', 'r1', 'Another', 1, '1' * 64)
    renamed = store.mutate(project_id, None, lambda p, db: p.update(name='Rename'))
    assert context.read_project(project_id)['questions'][1]['state'] == 'pending'
    store.mutate(project_id, renamed['revision'], lambda p, db: p['baseline'].update(hash='new source'))
    assert all(q['state'] == 'superseded' for q in context.read_project(project_id)['questions'])


def test_duplicate_project_bindings_refused_before_any_schema_changes():
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE delivery_jobs (id TEXT, project_id TEXT)')
    db.executemany('INSERT INTO delivery_jobs (id,project_id) VALUES (?,?)', [('a', 'p'), ('b', 'p')])
    assert_error('delivery_project_binding_conflict', lambda: install_context_schema(db))
    assert db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == [('delivery_jobs',)]


def test_result_budget_rolls_back_everything(room):
    store, project_id, delivery, context, _ = room
    delivery.limits['result_bytes'] = 1
    assert_error('delivery_result_limit', lambda: propose(room))
    assert context.read_project(project_id)['questions'] == []
    with store.connection() as db:
        assert context_hold(db, project_id)['context_epochs'][room[-1]] == 0
        assert db.execute("SELECT COUNT(*) FROM delivery_operations WHERE kind='propose_question'").fetchone()[0] == 0


@pytest.mark.parametrize('field,value', [('question', 'a' * 1001), ('source_ref', 'a' * 257), ('question', 'a\nb'), ('file_ids', ['x', 'x']), ('expected_epoch', True)])
def test_proposal_inputs_are_bounded(room, field, value):
    assert_error('delivery_invalid_input', lambda: propose(room, **{field: value}))


def test_reply_hash_is_original_and_input_limits_are_bounded(room):
    question_id = propose(room)['result']['question_id']
    assert_error('delivery_question_hash_conflict', lambda: reply(room, question_id, question_input_hash='0' * 64))
    for values in ({'text': 'a' * 2001}, {'text': 'bad\x00'}, {'reported_speaker': 'a' * 121}, {'source_ref': 'a' * 257}):
        assert_error('delivery_invalid_input', lambda: reply(room, question_id, **values))


def test_receipt_hold_uses_latest_packet_considered_set_and_safe_messages(room):
    store, project_id, delivery, _, job_id = room
    staged = delivery.stage_receipt(job_id, BINDING, 'stage', source_id='PRIVATE source', filename='PRIVATE.txt', content=b'synthetic')
    with store.connection() as db:
        hold = context_hold(db, project_id)
        assert hold['pending_receipt_count'] == 1
        assert 'PRIVATE' not in canonical(hold)
        db.execute('INSERT INTO delivery_packets (id,job_id,manifest_hash,body,created_at) VALUES (?,?,?,?,?)', ('packet', job_id, 'm', canonical({'considered_receipt_ids': [staged['result']['receipt_id']]}), 'now'))
        assert not context_hold(db, project_id)['blocked']


def test_schema_helpers_do_nothing_without_delivery_tables(tmp_path):
    store = Store(tmp_path)
    project = store.create('No delivery', 10)
    with store.connection() as db:
        assert sync_source_context(project, db) is False
        assert not context_hold(db, project['id'])['blocked']


def test_schema2_migration_imports_blocker_without_rewriting_project_or_export(tmp_path):
    store = Store(tmp_path)
    project = store.create('Legacy synthetic project', 10)
    with store.connection() as db:
        db.execute('CREATE TABLE delivery_jobs (id TEXT PRIMARY KEY,project_id TEXT NOT NULL)')
        db.execute('CREATE TABLE delivery_blockers (id TEXT PRIMARY KEY,job_id TEXT,requirement_id TEXT,message TEXT,input_hash TEXT,source_revision INTEGER,created_at TEXT)')
        db.execute('INSERT INTO delivery_jobs (id,project_id) VALUES (?,?)', ('job', project['id']))
        db.execute('INSERT INTO delivery_blockers (id,job_id,requirement_id,message,input_hash,source_revision,created_at) VALUES (?,?,?,?,?,?,?)', ('blocker', 'job', 'r1', 'Old unverified message', '0' * 64, 1, 'original-time'))
        db.execute('INSERT INTO exports (id,project_id,json,md,html) VALUES (?,?,?,?,?)', ('historical', project['id'], '{"historical":true}', 'original md', 'original html'))
        original = (db.execute('SELECT * FROM projects').fetchall(), db.execute('SELECT * FROM exports').fetchall(), db.execute('SELECT * FROM delivery_blockers').fetchall())
        install_context_schema(db)
        install_context_schema(db)
        after = (db.execute('SELECT * FROM projects').fetchall(), db.execute('SELECT * FROM exports').fetchall(), db.execute('SELECT * FROM delivery_blockers').fetchall())
        assert after == original
        assert db.execute('SELECT epoch FROM delivery_context_jobs').fetchone()[0] == 1
        question = json.loads(db.execute('SELECT body FROM delivery_questions').fetchone()[0])
        assert question['input_hash'] == '0' * 64 and question['source_revision'] == 1
        assert question['created_at'] == 'original-time' and question['source_hash'] is None
        assert context_hold(db, project['id'])['pending_context_count'] == 1
        assert sync_source_context(project, db) is False
        assert not db.execute('SELECT id FROM delivery_resolutions').fetchall()


def test_inspector_upgrade_retires_context_on_disabled_store_restart(room, monkeypatch):
    from handoffready import store as store_module
    store, project_id, _, context, _ = room
    question_id = propose(room)['result']['question_id']
    reply(room, question_id)
    resolve(room, question_id)
    monkeypatch.setattr(store_module, 'INSPECTION_REVISION', 'synthetic-inspector-upgrade')
    restarted = Store(store.directory)
    project = restarted.get(project_id)
    assert not project['delivery_context_basis']
    with restarted.connection() as db:
        assert not context_hold(db, project_id)['blocked']
        assert json.loads(db.execute('SELECT body FROM delivery_resolutions ORDER BY rowid DESC LIMIT 1').fetchone()[0])['action'] == 'source_superseded'


def test_disabled_restart_preserves_pending_hold_without_service_construction(room):
    store, project_id, _, _, _ = room
    propose(room)
    restarted = Store(store.directory)
    with restarted.connection() as db:
        hold = context_hold(db, project_id)
    assert hold['blocked'] and hold['pending_context_count'] == 1


def test_reply_race_rejects_old_resolution_epoch_and_exact_set(room):
    _, _, _, context, job_id = room
    question_id = propose(room)['result']['question_id']
    first = reply(room, question_id, 'first')['result']['reply_id']
    project, state = current(room)
    payload = dict(question_id=question_id, expected_revision=project['revision'], expected_hash=input_hash(project), expected_epoch=state['context_epoch'],
                   action='accept', covered_reply_ids=[first], used_reply_ids=[first], reason='Reviewed old replies')
    reply(room, question_id, 'racing-reply')
    assert_error('delivery_context_conflict', lambda: context.resolve(job_id, BINDING, 'stale-resolution', **payload))
    payload['expected_epoch'] = current(room)[1]['context_epoch']
    assert_error('delivery_reply_set_conflict', lambda: context.resolve(job_id, BINDING, 'missing-racing-reply', **payload))


def test_accept_result_failure_rolls_back_review_identity_resolution_and_epoch(room):
    store, project_id, delivery, context, _ = room
    question_id = propose(room)['result']['question_id']
    reply(room, question_id)
    before, context_before = current(room)
    delivery.limits['result_bytes'] = 1
    assert_error('delivery_result_limit', lambda: resolve(room, question_id))
    after, context_after = current(room)
    assert canonical(before) == canonical(after)
    assert context_before == context_after
    with store.connection() as db:
        assert db.execute('SELECT COUNT(*) FROM delivery_resolutions').fetchone()[0] == 0


def test_question_and_operation_resource_failures_do_not_advance_epoch(room):
    _, project_id, delivery, context, _ = room
    delivery.limits['blockers_per_job'] = 1
    propose(room)
    assert_error('delivery_blocker_limit', lambda: propose(room, 'over-question-budget'))
    assert context.read_project(project_id)['context_epoch'] == 1
    delivery.limits['operations_per_job'] = 2  # create + question already committed
    assert_error('delivery_operation_limit', lambda: propose(room, 'over-operation-budget'))
    assert context.read_project(project_id)['context_epoch'] == 1


def test_unanswered_dismissal_and_used_set_validation(room):
    _, project_id, _, context, _ = room
    question_id = propose(room)['result']['question_id']
    resolve(room, question_id, action='dismiss')
    assert context.read_project(project_id)['questions'][0]['state'] == 'resolved'
    assert_error('delivery_invalid_input', lambda: resolve(room, question_id, 'empty-accept'))
    assert_error('delivery_invalid_input', lambda: resolve(room, question_id, 'bad-dismiss', action='dismiss', used_reply_ids=['invented']))
    assert_error('delivery_invalid_input', lambda: resolve(room, question_id, 'empty-reason', action='withdraw', reason=''))


def test_hold_defensively_aggregates_all_project_jobs_with_one_data_query(room):
    store, project_id, _, _, first_job = room
    propose(room)
    with store.connection() as db:
        # A corrupted/old store can predate the unique index; generic holds must
        # still aggregate it, even though migration/startup refuses the shape.
        db.execute('DROP INDEX delivery_jobs_project_unique')
        db.execute('INSERT INTO delivery_jobs (id,binding,server,room,thread,project_id,created_at) VALUES (?,?,?,?,?,?,?)',
                   ('other-job', 'other-binding', 'https://switch.example.com', 'other-room', None, project_id, 'now'))
        db.execute('INSERT INTO delivery_context_jobs (job_id,epoch) VALUES (?,?)', ('other-job', 4))
        db.execute('INSERT INTO delivery_questions (id,job_id,body,created_at) VALUES (?,?,?,?)', ('other-question', 'other-job', '{}', 'now'))
        queries = []
        db.set_trace_callback(queries.append)
        hold = context_hold(db, project_id)
        db.set_trace_callback(None)
    assert hold['pending_context_count'] == 2
    assert hold['context_epochs'] == {first_job: 1, 'other-job': 4}
    data_queries = [sql for sql in queries if 'delivery_jobs' in sql]
    assert len(data_queries) == 1


def test_context_history_bodies_never_rewritten_after_source_edit(room):
    store, project_id, _, _, _ = room
    question_id = propose(room)['result']['question_id']
    reply(room, question_id)
    resolve(room, question_id)
    with store.connection() as db:
        original = {table: db.execute(f'SELECT id,body FROM {table} ORDER BY rowid').fetchall() for table in ('delivery_questions', 'delivery_replies', 'delivery_resolutions')}
    store.mutate(project_id, None, lambda p, db: p['baseline'].update(hash='actual source edit'))
    with store.connection() as db:
        for table, rows in original.items():
            assert db.execute(f'SELECT id,body FROM {table} ORDER BY rowid LIMIT ?', (len(rows),)).fetchall() == rows
