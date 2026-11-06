"""Frozen public records and one-use supervised return, never transport proof."""
import base64
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone

from .delivery_context import context_hold
from .exports import projection, render
from .store import StoreError, canonical, digest, input_hash, now, uid

SHARE_BYTES = 5 * 1024 * 1024
SHARES_PER_JOB = 20


def install_share_schema(db):
    db.execute('CREATE TABLE IF NOT EXISTS delivery_shares (id TEXT PRIMARY KEY,job_id TEXT NOT NULL,body TEXT NOT NULL,created_at TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS delivery_share_events (id TEXT PRIMARY KEY,intent_id TEXT NOT NULL,body TEXT NOT NULL,created_at TEXT NOT NULL)')


def validate_destination(value):
    if (not isinstance(value, dict) or set(value) != {'platform','url','label'} or value['platform'] != 'discord'
            or not isinstance(value['url'], str) or re.fullmatch(r'https://discord\.com/channels/[0-9]{1,30}/[0-9]{1,30}', value['url']) is None
            or not isinstance(value['label'], str) or not 1 <= len(value['label']) <= 160
            or not value['label'].strip() or any(not c.isprintable() for c in value['label'])):
        raise StoreError('delivery_destination_invalid', 'Configure the exact Discord main channel and its label before sharing.', 422)
    return dict(value)


def authority(project):
    # A new export increments revision but must not invalidate an unchanged
    # review. Private judgment affects authority only through this digest.
    return digest({'input_hash': input_hash(project), 'name': project['name'], 'decisions': project['decisions']})


def _text(value, maximum, label):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(not c.isprintable() and c not in '\n\t' for c in value):
        raise StoreError('delivery_invalid_input', f'Invalid {label}.', 422)


def _hash(value):
    if not isinstance(value,str) or re.fullmatch(r'[a-f0-9]{64}',value) is None:
        raise StoreError('delivery_invalid_input','An exact artifact hash is required.',422)


class DeliveryShare:
    def __init__(self, delivery):
        self.delivery, self.store = delivery, delivery.store

    def _row(self, db, job_id, intent_id):
        row=db.execute('SELECT body FROM delivery_shares WHERE id=? AND job_id=?',(intent_id,job_id)).fetchone()
        if row is None:raise StoreError('delivery_share_missing','This record is not part of this delivery.',404)
        return json.loads(row[0])

    def _events(self, db, intent_id):
        return [json.loads(r[0]) for r in db.execute('SELECT body FROM delivery_share_events WHERE intent_id=? ORDER BY rowid',(intent_id,))]

    def _event(self, db, intent_id, state, **data):
        if db.execute('SELECT COUNT(*) FROM delivery_share_events WHERE intent_id=?',(intent_id,)).fetchone()[0] >= 16:
            raise StoreError('delivery_share_event_limit','This record has reached its event limit.',413)
        body={'state':state,'created_at':now(),**data}
        db.execute('INSERT INTO delivery_share_events (id,intent_id,body,created_at) VALUES (?,?,?,?)',(uid(),intent_id,canonical(body),body['created_at']))
        return body

    def _view(self, db, body, project):
        events=self._events(db,body['intent_id'])
        state=events[-1]['state'] if events else 'authorized'
        # Conversation decisions can preserve the review hash (for example,
        # dismissing a new question). They still require fresh share consent.
        # Earlier bodies without this binding remain readable but cannot issue.
        current=(body['authority_digest']==authority(project)
                 and body.get('context_epochs')==context_hold(db,project['id'])['context_epochs'])
        if state=='authorized':
            if not current:state='superseded'
            elif datetime.fromisoformat(body['expires_at'])<=datetime.now(timezone.utc):state='expired'
        return {k:v for k,v in body.items() if k!='authority_digest'} | {'state':state,'is_current':current,'current_revision':project['revision'],'events':events}

    def _destination(self, binding, destination):
        if binding.thread is not None:raise StoreError('delivery_destination_invalid','This release supports the configured main channel only.',422)
        return {**validate_destination(destination),'server':binding.server,'room_id':binding.room,'thread_id':None}

    def _preview(self, db, job, project, destination):
        hold=context_hold(db,project['id'])
        if hold['blocked']:raise StoreError('delivery_hold','Resolve room context and confirm the complete packet before sharing.')
        value=projection(project,True)
        # Record ID/time will be assigned when the export is frozen.
        value['id']=value['created_at']=None
        signature=authority(project)
        issued=False
        active_intent_id=None
        for (raw,) in db.execute('SELECT body FROM delivery_shares WHERE job_id=?',(job['id'],)):
            old=json.loads(raw)
            if old['authority_digest']==signature:
                if any(e['state']=='issued_unverified' for e in self._events(db,old['intent_id'])):issued=True
                if self._view(db,old,project)['state']=='authorized':active_intent_id=old['intent_id']
        return {'job_id':job['id'],'source_revision':project['revision'],'input_hash':input_hash(project),'destination':destination,
                'projection':value,'context_epochs':hold['context_epochs'],'preview_hash':digest({'projection':value,'destination':destination,'authority':signature,'context_epochs':hold['context_epochs']}),
                'preview_markdown':render({**value,'id':'Assigned when frozen','created_at':'Assigned when frozen','snapshot_hash':'Assigned when frozen'})['md'],'active_intent_id':active_intent_id,'duplicate_risk':issued,'draft':value['status']=='draft_with_gaps','expiry_minutes':15}

    def preview(self, project_id, binding, destination):
        destination=self._destination(binding,destination)
        with self.store.lock:
            self.store.reconcile_originals(project_id)
            with self.store.connection() as db:
                row=db.execute('SELECT id FROM delivery_jobs WHERE project_id=? AND binding=?',(project_id,binding.key())).fetchone()
                if row is None:raise StoreError('delivery_binding_refused','This project has no configured delivery room.',403)
                job=self.delivery._job(db,row[0],binding)
                return self._preview(db,job,self.store.get(project_id,db),destination)

    def _mutate(self, job_id, binding, key, kind, payload, apply, project_id=None):
        with self.store.lock,self.store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            if binding is not None:job=self.delivery._job(db,job_id,binding)
            else:
                row=db.execute('SELECT project_id FROM delivery_jobs WHERE id=?',(job_id,)).fetchone()
                if row is None or row[0]!=project_id:raise StoreError('delivery_share_missing','This record is not part of this project.',404)
                job={'id':job_id,'project_id':project_id}
            replay=self.delivery._replay(db,job,kind,key,payload)
            if replay is not None:
                if kind=='issue_share':
                    # Reconcile an issued permission; never grant another send.
                    replay={**replay,'retry_advice':'reconcile','result':{**replay['result'],'send_permitted':False,'switch_send_arguments':None}}
                return replay
            if db.execute('SELECT COUNT(*) FROM delivery_operations WHERE job_id=?',(job_id,)).fetchone()[0]>=self.delivery.limits['operations_per_job']:
                raise StoreError('delivery_operation_limit','This delivery has reached its operation limit.',413)
            project=self.store.get(job['project_id'],db);before=canonical(project)
            reconciled=self.store._reconcile_originals(project)
            synced=self.store._sync_delivery_context(project,db)
            if reconciled or synced:
                project['revision']+=1;project['updated_at']=now()
            result=apply(db,job,project)
            if canonical(project)!=before:
                if not (reconciled or synced):project['revision']+=1;project['updated_at']=now()
                db.execute('UPDATE projects SET body=? WHERE id=?',(canonical(project),project['id']))
            outcome={'operation_id':uid(),'state':'succeeded','source_revision':project['revision'],'input_hash':input_hash(project),'result':result,'retry_advice':'none'}
            encoded=canonical(outcome)
            if len(encoded.encode())>self.delivery.limits['result_bytes']:raise StoreError('delivery_result_limit','This share result exceeds its storage limit.',413)
            db.execute('INSERT INTO delivery_operations (id,job_id,kind,operation_key,payload_digest,result) VALUES (?,?,?,?,?,?)',(outcome['operation_id'],job_id,kind,key,digest(payload),encoded))
            return outcome

    def create(self, project_id, binding, destination, key, *, expected_revision, expected_hash, preview_hash, confirmed_reviewed, acknowledge_draft=False, acknowledge_duplicate_risk=False):
        destination=self._destination(binding,destination)
        if type(expected_revision)is not int or expected_revision<1 or confirmed_reviewed is not True or type(acknowledge_draft)is not bool or type(acknowledge_duplicate_risk)is not bool:
            raise StoreError('delivery_invalid_input','Review the public projection and destination explicitly.',422)
        _hash(expected_hash);_hash(preview_hash)
        with self.store.lock,self.store.connection() as db:
            row=db.execute('SELECT id FROM delivery_jobs WHERE project_id=? AND binding=?',(project_id,binding.key())).fetchone()
            if row is None:raise StoreError('delivery_binding_refused','This project has no configured delivery room.',403)
            job_id=row[0]
        payload=dict(expected_revision=expected_revision,expected_hash=expected_hash,preview_hash=preview_hash,confirmed_reviewed=True,acknowledge_draft=acknowledge_draft,acknowledge_duplicate_risk=acknowledge_duplicate_risk,destination=destination)
        def apply(db,job,project):
            if project['revision']!=expected_revision or input_hash(project)!=expected_hash:raise StoreError('revision_conflict','Refresh the current share preview before authorizing.')
            preview=self._preview(db,job,project,destination)
            if preview['preview_hash']!=preview_hash:raise StoreError('delivery_share_preview_conflict','The public record or destination changed. Review the new preview.')
            if preview['active_intent_id']:raise StoreError('delivery_share_pending','This review already has an authorized return. Use or cancel it before creating another.')
            if preview['draft'] and not acknowledge_draft:raise StoreError('delivery_share_draft','Explicitly acknowledge the draft and its outstanding items.')
            if preview['duplicate_risk'] and not acknowledge_duplicate_risk:raise StoreError('delivery_share_duplicate_risk','This revision was already issued. Acknowledge possible duplicate delivery before authorizing another return.')
            if db.execute('SELECT COUNT(*) FROM delivery_shares WHERE job_id=?',(job_id,)).fetchone()[0]>=SHARES_PER_JOB:raise StoreError('delivery_share_limit','This delivery has reached its retained-record limit.',413)
            if len(project['exports'])>=100:raise StoreError('export_history_limit','This project has reached its retained-export limit.')
            value=projection(project,True);value['snapshot_hash']=digest(value);formats=render(value);raw=formats['md'].encode()
            if not 1<=len(raw)<=SHARE_BYTES:raise StoreError('delivery_share_size','The Markdown record exceeds the return budget.',413)
            intent_id=uid();created=now()
            body={'intent_id':intent_id,'job_id':job_id,'export_id':value['id'],'snapshot_hash':value['snapshot_hash'],'artifact_sha256':hashlib.sha256(raw).hexdigest(),'artifact_size':len(raw),'filename':f'handoff-{value["id"]}.md','format':'md','duplicate_risk_acknowledged':acknowledge_duplicate_risk,'source_revision':project['revision'],'input_hash':input_hash(project),'authority_digest':authority(project),'destination':destination,'status':value['status'],'created_at':created,'expires_at':(datetime.fromisoformat(created)+timedelta(minutes=15)).isoformat()}
            body['context_epochs']=preview['context_epochs']
            db.execute('INSERT INTO exports (id,project_id,json,md,html) VALUES (?,?,?,?,?)',(value['id'],project_id,formats['json'],formats['md'],formats['html']))
            project['exports'].append({'id':value['id'],'created_at':created,'snapshot_hash':value['snapshot_hash'],'status':value['status'],'gaps':value['gaps'],'preview':value})
            db.execute('INSERT INTO delivery_shares (id,job_id,body,created_at) VALUES (?,?,?,?)',(intent_id,job_id,canonical(body),created))
            return {'intent_id':intent_id,'export_id':value['id'],'artifact_sha256':body['artifact_sha256'],'state':'authorized','send_permitted':False}
        return self._mutate(job_id,binding,key,'authorize_share',payload,apply)

    def read_project(self, project_id):
        with self.store.lock,self.store.connection() as db:
            project=self.store.get(project_id,db)
            return [self._view(db,json.loads(r[0]),project) for r in db.execute('SELECT s.body FROM delivery_shares s JOIN delivery_jobs j ON j.id=s.job_id WHERE j.project_id=? ORDER BY s.rowid DESC',(project_id,))]

    def _eligible(self, db, job, project, intent_id, destination):
        body=self._row(db,job['id'],intent_id);view=self._view(db,body,project)
        if body['destination']!=destination:raise StoreError('delivery_share_destination_changed','The configured destination changed. Authorize a new return.')
        if view['state']!='authorized':raise StoreError('delivery_share_not_authorized','This return is expired, superseded, cancelled or already issued. Reconcile it instead of sending again.')
        if context_hold(db,project['id'])['blocked']:raise StoreError('delivery_hold','Unresolved room work blocks this return.')
        if not body.get('duplicate_risk_acknowledged',False):
            for (raw,) in db.execute('SELECT body FROM delivery_shares WHERE job_id=? AND id<>?',(job['id'],intent_id)):
                other=json.loads(raw)
                if other['authority_digest']==body['authority_digest'] and any(e['state']=='issued_unverified' for e in self._events(db,other['intent_id'])):
                    raise StoreError('delivery_share_duplicate_risk','Another return of this review was issued. Inspect it before authorizing a possible duplicate.')
        return body

    def material(self, job_id, binding, destination, intent_id):
        destination=self._destination(binding,destination)
        with self.store.lock:
            job=self.delivery.get_job(job_id,binding);self.store.reconcile_originals(job['project_id'])
            with self.store.connection() as db:
                body=self._eligible(db,job,self.store.get(job['project_id'],db),intent_id,destination)
                row=db.execute('SELECT md FROM exports WHERE id=? AND project_id=?',(body['export_id'],job['project_id'])).fetchone()
                if row is None:raise StoreError('delivery_share_artifact_missing','The frozen artifact is unavailable.')
                raw=row[0].encode()
                if len(raw)!=body['artifact_size'] or hashlib.sha256(raw).hexdigest()!=body['artifact_sha256']:raise StoreError('delivery_share_artifact_changed','The frozen artifact identity does not match.')
                return {k:body[k] for k in ('intent_id','filename','artifact_sha256','artifact_size')} | {'content_base64':base64.b64encode(raw).decode()}

    def issue(self, job_id, binding, destination, intent_id, key, artifact_sha256):
        destination=self._destination(binding,destination);_hash(artifact_sha256)
        payload={'intent_id':intent_id,'artifact_sha256':artifact_sha256,'destination':destination}
        def apply(db,job,project):
            body=self._eligible(db,job,project,intent_id,destination)
            if artifact_sha256!=body['artifact_sha256']:raise StoreError('delivery_share_artifact_changed','Issue only the exact frozen artifact.')
            attempt=uid();self._event(db,intent_id,'issued_unverified',attempt_id=attempt,verification='none')
            label='DRAFT with outstanding items' if body['status']=='draft_with_gaps' else 'Reviewed record with scope exceptions' if body['status']=='reviewed_with_exceptions' else 'Reviewed delivery record'
            caption=f'HandoffReady: {label}. Source revision {body["source_revision"]}. SHA-256 {artifact_sha256}. Return requires local verification; this is not client acceptance.'
            return {'intent_id':intent_id,'attempt_id':attempt,'artifact_sha256':artifact_sha256,'state':'issued_unverified','send_permitted':True,'switch_send_arguments':{'room_id':destination['room_id'],'caption':caption}}
        return self._mutate(job_id,binding,key,'issue_share',payload,apply)

    def _local_job(self, project_id, intent_id):
        with self.store.connection() as db:
            row=db.execute('SELECT s.job_id FROM delivery_shares s JOIN delivery_jobs j ON j.id=s.job_id WHERE s.id=? AND j.project_id=?',(intent_id,project_id)).fetchone()
            if row is None:raise StoreError('delivery_share_missing','This record is not part of this project.',404)
            return row[0]

    def cancel(self, project_id, intent_id, key, *, reason, acknowledge_may_have_sent=False):
        _text(reason,1000,'cancellation reason')
        job_id=self._local_job(project_id,intent_id)
        def apply(db,job,project):
            self._row(db,job_id,intent_id);events=self._events(db,intent_id);state=events[-1]['state'] if events else 'authorized'
            if state not in {'authorized','issued_unverified'}:raise StoreError('delivery_share_outcome_conflict','This return already has a final local outcome.')
            if state=='issued_unverified' and acknowledge_may_have_sent is not True:raise StoreError('delivery_share_unknown','The record may already have been sent. Inspect the room and acknowledge that uncertainty.')
            state='cancelled_unverified' if state=='issued_unverified' else 'cancelled';self._event(db,intent_id,state,reason=reason,verification='none')
            return {'intent_id':intent_id,'state':state}
        return self._mutate(job_id,None,key,'cancel_share',{'intent_id':intent_id,'reason':reason,'acknowledge_may_have_sent':acknowledge_may_have_sent},apply,project_id)

    def verify(self, project_id, intent_id, key, *, attempt_id, message_url, content, confirmed_destination):
        _text(attempt_id,100,'attempt');_text(message_url,512,'message link')
        if confirmed_destination is not True or not isinstance(content,bytes) or not 1<=len(content)<=SHARE_BYTES:raise StoreError('delivery_invalid_input','Supply the returned file and explicitly check its destination.',422)
        sha=hashlib.sha256(content).hexdigest();job_id=self._local_job(project_id,intent_id)
        payload={'intent_id':intent_id,'attempt_id':attempt_id,'message_url':message_url,'artifact_sha256':sha,'artifact_size':len(content),'confirmed_destination':True}
        def apply(db,job,project):
            body=self._row(db,job_id,intent_id);events=self._events(db,intent_id)
            issued=next((e for e in events if e['state']=='issued_unverified'),None)
            if issued is None or issued['attempt_id']!=attempt_id:raise StoreError('delivery_share_attempt_missing','This return has no matching issued attempt.')
            if events[-1]['state'] not in {'issued_unverified','operator_confirmed'}:raise StoreError('delivery_share_outcome_conflict','This return was cancelled without verification.')
            if re.fullmatch(re.escape(body['destination']['url'])+r'/[0-9]{1,30}',message_url) is None:raise StoreError('delivery_share_destination_mismatch','Use the message link from the exact configured main channel.',422)
            if sha!=body['artifact_sha256'] or len(content)!=body['artifact_size']:raise StoreError('delivery_share_artifact_changed','The returned file does not match the frozen record.',422)
            if events[-1]['state']=='operator_confirmed':
                if events[-1]['message_url']!=message_url:raise StoreError('delivery_share_outcome_conflict','This record was already verified against another message.')
            else:self._event(db,intent_id,'operator_confirmed',attempt_id=attempt_id,message_url=message_url,artifact_sha256=sha,artifact_size=len(content),verification='operator_checked_destination_and_exact_bytes')
            return {'intent_id':intent_id,'state':'operator_confirmed','verification':'operator_checked_destination_and_exact_bytes','is_current':self._view(db,body,project)['is_current']}
        return self._mutate(job_id,None,key,'verify_share',payload,apply,project_id)
