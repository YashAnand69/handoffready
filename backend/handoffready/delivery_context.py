"""Immutable, unverified delivery context and local review identity.

Transport receipts are provenance claims, not authenticated source evidence. Only
an explicit local resolution may contribute to the project's review identity.
"""
import hashlib
import json
import re

from . import store as store_module
from .checks import evaluate_selection
from .policy import LIMITS
from .store import StoreError, canonical, digest, input_hash, invalidate, now, uid


def _source_hash(project):
    return store_module.source_hash(project)


def _has(db, table):
    return db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def _text(value, field, maximum, multiline=False, optional=False):
    if (not isinstance(value, str) or len(value) > maximum or (not optional and not value.strip())
            or any(not c.isprintable() and not (multiline and c in '\n\t') for c in value)):
        raise StoreError('delivery_invalid_input', f'Invalid {field}.', 422)
    return value


def _ids(value, field, maximum):
    if (not isinstance(value, list) or len(value) > maximum
            or any(not isinstance(i, str) or re.fullmatch(r'[A-Za-z0-9_-]{1,100}', i) is None for i in value)
            or len(set(value)) != len(value)):
        raise StoreError('delivery_invalid_input', f'Choose bounded unique {field}.', 422)
    return sorted(value)


def _currency(revision, hash_value, epoch):
    if (type(revision) is not int or not 1 <= revision <= 2**53-1 or type(epoch) is not int or not 0 <= epoch <= 2**53-1
            or not isinstance(hash_value, str) or re.fullmatch(r'[a-f0-9]{64}', hash_value) is None):
        raise StoreError('delivery_invalid_input', 'Current revision, input hash and context epoch are required.', 422)


def _bump(db, job_id):
    db.execute('INSERT OR IGNORE INTO delivery_context_jobs (job_id,epoch) VALUES (?,?)', (job_id, 0))
    db.execute('UPDATE delivery_context_jobs SET epoch=epoch+1 WHERE job_id=?', (job_id,))
    return _epoch(db, job_id)


def _epoch(db, job_id):
    row = db.execute('SELECT epoch FROM delivery_context_jobs WHERE job_id=?', (job_id,)).fetchone()
    return row[0] if row else 0


def _questions(db, job_id):
    return [(row[0], json.loads(row[1])) for row in db.execute('SELECT id,body FROM delivery_questions WHERE job_id=? ORDER BY rowid', (job_id,))]


def _replies(db, question_id):
    return [dict(json.loads(row[1]), reply_id=row[0]) for row in db.execute('SELECT id,body FROM delivery_replies WHERE question_id=? ORDER BY rowid', (question_id,))]


def _resolutions(db, question_id):
    return [dict(json.loads(row[1]), resolution_id=row[0]) for row in db.execute('SELECT id,body FROM delivery_resolutions WHERE question_id=? ORDER BY rowid', (question_id,))]


def _state(replies, resolutions):
    if any(row['action'] == 'source_superseded' for row in resolutions):
        return 'superseded'
    if resolutions and set(resolutions[-1]['covered_reply_ids']) == {row['reply_id'] for row in replies}:
        return 'resolved'
    return 'pending'


def _active(resolutions):
    active = None
    for row in resolutions:
        if row['action'] == 'accept':
            active = row['active_context']
        elif row['action'] in {'withdraw', 'source_superseded'}:
            active = None
    return active


def _resolution(db, job_id, question_id, body):
    if db.execute('SELECT COUNT(*) FROM delivery_resolutions WHERE job_id=?', (job_id,)).fetchone()[0] >= 1100:
        raise StoreError('delivery_resolution_limit', 'This delivery has reached its resolution limit.', 413)
    resolution_id = uid()
    body = {**body, 'created_at': now(), 'provenance': 'unverified'}
    db.execute('INSERT INTO delivery_resolutions (id,job_id,question_id,body,created_at) VALUES (?,?,?,?,?)',
               (resolution_id, job_id, question_id, canonical(body), body['created_at']))
    return dict(body, resolution_id=resolution_id)


def install_context_schema(db):
    """Add schema3 inside the owner's transaction, preserving all old rows."""
    # Refuse ambiguity before making even additive migration changes.
    if db.execute('SELECT project_id FROM delivery_jobs GROUP BY project_id HAVING COUNT(*)>1 LIMIT 1').fetchone():
        raise StoreError('delivery_project_binding_conflict', 'A project has multiple delivery bindings. Resolve this before upgrading.')
    db.execute('CREATE UNIQUE INDEX IF NOT EXISTS delivery_jobs_project_unique ON delivery_jobs(project_id)')
    for statement in (
        'CREATE TABLE IF NOT EXISTS delivery_context_jobs (job_id TEXT PRIMARY KEY, epoch INTEGER NOT NULL)',
        'CREATE TABLE IF NOT EXISTS delivery_questions (id TEXT PRIMARY KEY, job_id TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL)',
        'CREATE TABLE IF NOT EXISTS delivery_replies (id TEXT PRIMARY KEY, job_id TEXT NOT NULL, question_id TEXT NOT NULL, source_ref TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(question_id,source_ref))',
        'CREATE TABLE IF NOT EXISTS delivery_resolutions (id TEXT PRIMARY KEY, job_id TEXT NOT NULL, question_id TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL)',
    ):
        db.execute(statement)
    db.execute('INSERT OR IGNORE INTO delivery_context_jobs (job_id,epoch) SELECT id,0 FROM delivery_jobs')
    if _has(db, 'delivery_blockers'):
        for row in db.execute('SELECT id,job_id,requirement_id,message,source_revision,input_hash,created_at FROM delivery_blockers ORDER BY rowid').fetchall():
            if db.execute('SELECT 1 FROM delivery_questions WHERE id=?', (row[0],)).fetchone():
                continue
            project_row = db.execute('SELECT body FROM projects WHERE id=(SELECT project_id FROM delivery_jobs WHERE id=?)', (row[1],)).fetchone()
            if project_row is None:
                raise StoreError('delivery_project_missing', 'A legacy delivery project is missing.')
            _legacy(db, {'id': row[1]}, json.loads(project_row[0]), row[0], row[2], row[3], row[4], row[5], row[6])


def _legacy(db, job, project, blocker_id, requirement_id, message, original_revision, original_hash, created_at=None):
    if db.execute('SELECT 1 FROM delivery_questions WHERE id=?', (blocker_id,)).fetchone():
        return blocker_id
    created_at = created_at or now()
    body = {'requirement_id': requirement_id, 'question': message, 'source_ref': None,
            'source_revision': original_revision, 'input_hash': original_hash, 'source_hash': None,
            'observed_source_hash': _source_hash(project), 'file_ids': [], 'evidence': [], 'legacy': True,
            'provenance': 'unverified', 'source_anchor': 'unknown', 'created_at': created_at}
    db.execute('INSERT INTO delivery_questions (id,job_id,body,created_at) VALUES (?,?,?,?)', (blocker_id, job['id'], canonical(body), created_at))
    _bump(db, job['id'])
    return blocker_id


def sync_source_context(project, db):
    """Latch genuine source edits; caller owns serialization and transaction."""
    if not _has(db, 'delivery_questions'):
        return False
    current = _source_hash(project)
    retired = set()
    for (job_id,) in db.execute('SELECT id FROM delivery_jobs WHERE project_id=?', (project['id'],)).fetchall():
        affected = False
        for question_id, question in _questions(db, job_id):
            resolutions = _resolutions(db, question_id)
            if any(row['action'] == 'source_superseded' for row in resolutions):
                continue
            anchor = question.get('source_hash') or question.get('observed_source_hash')
            if anchor == current:
                continue
            _resolution(db, job_id, question_id, {'action': 'source_superseded', 'covered_reply_ids': [r['reply_id'] for r in _replies(db, question_id)],
                        'used_reply_ids': [], 'reason': 'Source inputs changed; this context is historical.', 'source_hash': current})
            retired.add(question_id)
            affected = True
        if affected:
            _bump(db, job_id)
    basis = project.get('delivery_context_basis', [])
    kept = [row for row in basis if row['question_id'] not in retired and row['source_hash'] == current]
    if kept == basis:
        return False
    project['delivery_context_basis'] = kept
    invalidate(project)
    return True


def context_hold(db, project_id):
    """One project-wide data query, independent of the configured binding.

    Table discovery supports disabled integrations and older stores. The union
    snapshots all jobs together, rather than trusting the active room's job.
    """
    result = {'pending_context_count': 0, 'pending_receipt_count': 0, 'blocked': False, 'messages': [], 'context_epochs': {}}
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if 'delivery_jobs' not in tables:
        return result
    epoch_join = 'LEFT JOIN delivery_context_jobs e ON e.job_id=j.id' if 'delivery_context_jobs' in tables else ''
    epoch_value = 'COALESCE(e.epoch,0)' if epoch_join else 'NULL'
    selects = [f"SELECT 'job' AS kind,j.id AS job_id,NULL AS question_id,NULL AS record_id,{epoch_value} AS body,0 AS position FROM delivery_jobs j {epoch_join} WHERE j.project_id=?"]
    if 'delivery_questions' in tables:
        selects.extend([
            "SELECT 'question',q.job_id,q.id,q.id,q.body,q.rowid FROM delivery_questions q JOIN delivery_jobs j ON j.id=q.job_id WHERE j.project_id=?",
            "SELECT 'reply',r.job_id,r.question_id,r.id,r.body,r.rowid FROM delivery_replies r JOIN delivery_jobs j ON j.id=r.job_id WHERE j.project_id=?",
            "SELECT 'resolution',r.job_id,r.question_id,r.id,r.body,r.rowid FROM delivery_resolutions r JOIN delivery_jobs j ON j.id=r.job_id WHERE j.project_id=?",
        ])
    elif 'delivery_blockers' in tables:
        selects.append("SELECT 'legacy',b.job_id,b.id,b.id,NULL,b.rowid FROM delivery_blockers b JOIN delivery_jobs j ON j.id=b.job_id WHERE j.project_id=?")
    if 'delivery_receipts' in tables:
        selects.append("SELECT 'receipt',r.job_id,NULL,r.id,NULL,r.rowid FROM delivery_receipts r JOIN delivery_jobs j ON j.id=r.job_id WHERE j.project_id=?")
    if 'delivery_packets' in tables:
        selects.append("SELECT 'packet',p.job_id,NULL,p.id,p.body,p.rowid FROM delivery_packets p JOIN delivery_jobs j ON j.id=p.job_id WHERE j.project_id=? AND p.rowid=(SELECT MAX(last.rowid) FROM delivery_packets last WHERE last.job_id=p.job_id)")
    rows = db.execute(' UNION ALL '.join(selects) + ' ORDER BY kind,position', (project_id,) * len(selects)).fetchall()
    questions, replies, resolutions, receipts, considered = set(), {}, {}, {}, {}
    for kind, job_id, question_id, record_id, body, _ in rows:
        if kind == 'job' and body is not None:
            result['context_epochs'][job_id] = body
        elif kind == 'question':
            questions.add(question_id)
        elif kind == 'legacy':
            result['pending_context_count'] += 1
        elif kind == 'reply':
            replies.setdefault(question_id, []).append(dict(json.loads(body), reply_id=record_id))
        elif kind == 'resolution':
            resolutions.setdefault(question_id, []).append(json.loads(body))
        elif kind == 'receipt':
            receipts.setdefault(job_id, set()).add(record_id)
        elif kind == 'packet':
            considered[job_id] = set(json.loads(body)['considered_receipt_ids'])
    result['pending_context_count'] += sum(_state(replies.get(qid, []), resolutions.get(qid, [])) == 'pending' for qid in questions)
    result['pending_receipt_count'] = sum(len(ids - considered.get(job_id, set())) for job_id, ids in receipts.items())
    if result['pending_context_count']:
        result['messages'].append('Delivery context requires local review.')
    if result['pending_receipt_count']:
        result['messages'].append('New delivery attachments await complete packet confirmation.')
    result['blocked'] = bool(result['messages'])
    return result


class DeliveryContext:
    def __init__(self, delivery):
        self.delivery = delivery
        self.store = delivery.store

    def read_project(self, project_id):
        with self.store.lock:
            self.store.reconcile_originals(project_id)
            with self.store.connection() as db:
                project = self.store.get(project_id, db)
                row = db.execute('SELECT id FROM delivery_jobs WHERE project_id=? ORDER BY rowid LIMIT 1', (project_id,)).fetchone()
                if row is None:
                    return None
                job_id = row[0]
                questions = []
                for question_id, question in _questions(db, job_id):
                    replies, resolutions = _replies(db, question_id), _resolutions(db, question_id)
                    questions.append({**{k: v for k, v in question.items() if k != 'observed_source_hash'}, 'question_id': question_id,
                                      'state': _state(replies, resolutions), 'active_context': self._public_active(_active(resolutions)), 'replies': replies,
                                      'latest_resolution': resolutions[-1] if resolutions else None})
                return {'job_id': job_id, 'source_revision': project['revision'], 'input_hash': input_hash(project),
                        'context_epoch': _epoch(db, job_id), 'questions': questions}

    @staticmethod
    def _public_active(active):
        return dict(active, used_reply_ids=[r['reply_id'] for r in active['used_replies']]) if active else None

    def _mutate(self, job_id, binding, operation_key, kind, payload, apply, expected=None):
        with self.store.lock, self.store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            job = self.delivery._job(db, job_id, binding)
            replay = self.delivery._replay(db, job, kind, operation_key, payload)
            if replay is not None:
                return replay
            if db.execute('SELECT COUNT(*) FROM delivery_operations WHERE job_id=?', (job_id,)).fetchone()[0] >= self.delivery.limits['operations_per_job']:
                raise StoreError('delivery_operation_limit', 'This delivery has reached its operation limit.', 413)
            project = self.store.get(job['project_id'], db)
            before = canonical(project)
            reconciled = self.store._reconcile_originals(project)
            synced = sync_source_context(project, db)
            if reconciled or synced:
                project['revision'] += 1
                project['updated_at'] = now()
            if expected:
                revision, hash_value, epoch = expected
                if project['revision'] != revision:
                    raise StoreError('revision_conflict', 'The project changed. Refresh before continuing.')
                if input_hash(project) != hash_value:
                    raise StoreError('delivery_input_conflict', 'The packet changed. Refresh before continuing.')
                if _epoch(db, job_id) != epoch:
                    raise StoreError('delivery_context_conflict', 'Delivery context changed. Refresh before continuing.')
            revision_before = project['revision']
            body_before = canonical(project)
            outcome = apply(db, job, project)
            if canonical(project) != body_before and project['revision'] == revision_before:
                project['revision'] += 1
                project['updated_at'] = now()
            if canonical(project) != before:
                db.execute('UPDATE projects SET body=? WHERE id=?', (canonical(project), project['id']))
            result = {'operation_id': uid(), 'state': 'succeeded', 'source_revision': project['revision'], 'input_hash': input_hash(project),
                      'result': outcome, 'retry_advice': 'none'}
            encoded = canonical(result)
            if len(encoded.encode()) > self.delivery.limits['result_bytes']:
                raise StoreError('delivery_result_limit', 'The operation result exceeds its storage limit.', 413)
            db.execute('INSERT INTO delivery_operations (id,job_id,kind,operation_key,payload_digest,result) VALUES (?,?,?,?,?,?)',
                       (result['operation_id'], job_id, kind, operation_key, digest(payload), encoded))
            return result

    def propose_question(self, job_id, binding, operation_key, *, expected_revision, expected_hash, expected_epoch, requirement_id, file_ids, question, source_ref):
        _currency(expected_revision, expected_hash, expected_epoch)
        _text(requirement_id, 'requirement', 100)
        _text(question, 'question', 1000)
        _text(source_ref, 'source reference', 256)
        file_ids = _ids(file_ids, 'candidate files', LIMITS['files'])
        payload = dict(expected_revision=expected_revision, expected_hash=expected_hash, expected_epoch=expected_epoch,
                       requirement_id=requirement_id, file_ids=file_ids, question=question, source_ref=source_ref)
        def apply(db, job, project):
            if project['baseline']['state'] != 'approved' or not project['baseline']['requirements']:
                raise StoreError('baseline_not_approved', 'The local reviewer must confirm the checklist first.')
            requirement = next((r for r in project['baseline']['requirements'] if r['id'] == requirement_id), None)
            if requirement is None:
                raise StoreError('delivery_requirement_missing', 'The requirement is not in the current checklist.', 422)
            files = {f['id']: f for f in project['files']}
            if not set(file_ids) <= files.keys():
                raise StoreError('invalid_files', 'Choose registered files from this packet.', 422)
            if db.execute('SELECT COUNT(*) FROM delivery_questions WHERE job_id=?', (job_id,)).fetchone()[0] >= self.delivery.limits['blockers_per_job']:
                raise StoreError('delivery_blocker_limit', 'This delivery has reached its question limit.', 413)
            evidence = [{k: ('Human assessment is required in the local desk.' if k == 'reason' and c['kind'] == 'manual' else v)
                         for k, v in c.items() if k != 'expected' or c['kind'] != 'literal_text'}
                        for c in evaluate_selection(requirement, [files[i] for i in file_ids])]
            body = {'requirement_id': requirement_id, 'question': question, 'source_ref': source_ref, 'source_revision': project['revision'],
                    'input_hash': input_hash(project), 'source_hash': _source_hash(project), 'file_ids': file_ids,
                    'evidence': evidence, 'legacy': False, 'provenance': 'unverified', 'created_at': now()}
            question_id = uid()
            db.execute('INSERT INTO delivery_questions (id,job_id,body,created_at) VALUES (?,?,?,?)', (question_id, job_id, canonical(body), body['created_at']))
            return {'question_id': question_id, 'context_epoch': _bump(db, job_id), 'assessment_saved': False}
        return self._mutate(job_id, binding, operation_key, 'propose_question', payload, apply, (expected_revision, expected_hash, expected_epoch))

    def record_reply(self, job_id, binding, operation_key, *, question_id, question_input_hash, source_ref, reported_speaker, text):
        _text(question_id, 'question identity', 100)
        _text(source_ref, 'source reference', 256)
        _text(reported_speaker, 'reported speaker', 120)
        _text(text, 'reply', 2000, multiline=True)
        if not isinstance(question_input_hash, str) or re.fullmatch(r'[a-f0-9]{64}', question_input_hash) is None:
            raise StoreError('delivery_invalid_input', 'The original question input hash is required.', 422)
        payload = dict(question_id=question_id, question_input_hash=question_input_hash, source_ref=source_ref, reported_speaker=reported_speaker, text=text)
        def apply(db, job, project):
            question = self._question(db, job_id, question_id)
            if question['input_hash'] != question_input_hash:
                raise StoreError('delivery_question_hash_conflict', 'Reply must reference the original question input hash.')
            row = db.execute('SELECT id,body FROM delivery_replies WHERE question_id=? AND source_ref=?', (question_id, source_ref)).fetchone()
            if row:
                previous = json.loads(row[1])
                if previous['reported_speaker'] != reported_speaker or previous['text'] != text:
                    raise StoreError('delivery_source_conflict', 'This source reference already names a different reply.')
                reply_id, epoch = row[0], _epoch(db, job_id)
            else:
                if db.execute('SELECT COUNT(*) FROM delivery_replies WHERE job_id=?', (job_id,)).fetchone()[0] >= 200:
                    raise StoreError('delivery_reply_limit', 'This delivery has reached its reply limit.', 413)
                reply_id = uid()
                body = {'source_ref': source_ref, 'reported_speaker': reported_speaker, 'text': text,
                        'text_hash': hashlib.sha256(text.encode()).hexdigest(), 'created_at': now(), 'provenance': 'unverified'}
                db.execute('INSERT INTO delivery_replies (id,job_id,question_id,source_ref,body,created_at) VALUES (?,?,?,?,?,?)',
                           (reply_id, job_id, question_id, source_ref, canonical(body), body['created_at']))
                epoch = _bump(db, job_id)
            return {'reply_id': reply_id, 'question_id': question_id, 'context_epoch': epoch,
                    'state': _state(_replies(db, question_id), _resolutions(db, question_id)), 'provenance': 'unverified'}
        return self._mutate(job_id, binding, operation_key, 'record_reply', payload, apply)

    def _question(self, db, job_id, question_id):
        row = db.execute('SELECT body FROM delivery_questions WHERE id=? AND job_id=?', (question_id, job_id)).fetchone()
        if row is None:
            raise StoreError('delivery_question_missing', 'This question is not part of this delivery.', 404)
        return json.loads(row[0])

    def resolve(self, job_id, binding, operation_key, *, question_id, expected_revision, expected_hash, expected_epoch, action, covered_reply_ids, used_reply_ids, reason):
        _currency(expected_revision, expected_hash, expected_epoch)
        _text(question_id, 'question identity', 100)
        _text(reason, 'resolution reason', 1000, multiline=True, optional=action == 'accept')
        if action not in {'accept', 'dismiss', 'withdraw'}:
            raise StoreError('delivery_invalid_input', 'Choose a supported local resolution.', 422)
        covered_reply_ids = _ids(covered_reply_ids, 'covered replies', 200)
        used_reply_ids = _ids(used_reply_ids, 'used replies', 200)
        if (action == 'accept' and not used_reply_ids) or (action != 'accept' and used_reply_ids) or not set(used_reply_ids) <= set(covered_reply_ids):
            raise StoreError('delivery_invalid_input', 'Choose used replies only when accepting context.', 422)
        payload = dict(question_id=question_id, expected_revision=expected_revision, expected_hash=expected_hash, expected_epoch=expected_epoch,
                       action=action, covered_reply_ids=covered_reply_ids, used_reply_ids=used_reply_ids, reason=reason)
        def apply(db, job, project):
            question = self._question(db, job_id, question_id)
            replies, resolutions = _replies(db, question_id), _resolutions(db, question_id)
            if _state(replies, resolutions) == 'superseded':
                raise StoreError('delivery_question_historical', 'Historical context cannot be adopted. Create a current question instead.')
            if question['legacy'] and action != 'dismiss':
                raise StoreError('delivery_legacy_dismiss_only', 'Legacy unverified questions can only be dismissed.')
            if set(covered_reply_ids) != {r['reply_id'] for r in replies}:
                raise StoreError('delivery_reply_set_conflict', 'New replies arrived. Review every current reply before resolving.')
            active = _active(resolutions)
            if action == 'accept':
                active = {'question_id': question_id, 'source_hash': question['source_hash'],
                          'used_replies': [{k: r[k] for k in ('reply_id', 'text_hash', 'source_ref')} for r in sorted(replies, key=lambda r: r['reply_id']) if r['reply_id'] in used_reply_ids]}
            elif action == 'withdraw':
                active = None
            basis = project.get('delivery_context_basis', [])
            updated = [b for b in basis if b['question_id'] != question_id]
            if active:
                updated.append(active)
            updated.sort(key=lambda b: b['question_id'])
            if updated != basis:
                project['delivery_context_basis'] = updated
                invalidate(project)
                project['revision'] += 1
                project['updated_at'] = now()
            resolution = _resolution(db, job_id, question_id, {'action': action, 'covered_reply_ids': covered_reply_ids, 'used_reply_ids': used_reply_ids,
                                     'reason': reason, 'active_context': active, 'source_hash': _source_hash(project),
                                     'source_revision': project['revision'], 'input_hash': input_hash(project), 'context_epoch': _epoch(db, job_id) + 1})
            return {'resolution_id': resolution['resolution_id'], 'question_id': question_id, 'context_epoch': _bump(db, job_id),
                    'state': 'resolved', 'assessment_saved': False, 'active_context': active}
        return self._mutate(job_id, binding, operation_key, 'resolve_context', payload, apply, (expected_revision, expected_hash, expected_epoch))

    def record_legacy(self, db, job, project, blocker_id, requirement_id, message, original_revision, original_hash):
        return _legacy(db, job, project, blocker_id, requirement_id, message, original_revision, original_hash)
