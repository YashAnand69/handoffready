"""Frozen return safety with real SQLite/HTTP; no real messaging or people."""
import base64
import hashlib
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from handoffready.api import create_app
from handoffready.delivery import DeliveryBinding,DeliveryService
from handoffready.store import StoreError
from test_api import create,baseline,upload,decision,fresh,mutate
from test_delivery_api import CONFIG,bound_job
from test_delivery_context_api import local_client,question,reply,resolution_body,resolve

DEST={'platform':'discord','url':'https://discord.com/channels/111/222','label':'Synthetic trial / #delivery'}
SHARE_CONFIG={**CONFIG,'destination':DEST}
BINDING=DeliveryBinding(CONFIG['server'],CONFIG['room'])

@pytest.fixture
def share(tmp_path):
    with local_client(create_app(tmp_path,delivery_config=SHARE_CONFIG)) as c:
        p=decision(c,upload(c,baseline(c,create(c),[{'kind':'literal_text','needle':'delivery'}])),note='PRIVATE INTERNAL JUDGMENT',client_note='Use this public guide.')
        yield c,p,bound_job(c,p)


def preview(c,p):
    r=c.get(f'/api/v1/projects/{p["id"]}/delivery-share-preview');assert r.status_code==200,r.text
    return r.json()['data']


def authorize(c,p,key='authorize',**changes):
    v=preview(c,p)
    body={'operation_key':key,'expected_revision':v['source_revision'],'input_hash':v['input_hash'],'preview_hash':v['preview_hash'],'confirmed_reviewed':True,**changes}
    r=c.post(f'/api/v1/projects/{p["id"]}/delivery-shares',json=body)
    assert r.status_code==201,r.text
    return r.json()['data'],body


def service(c):return c.app.state.delivery_service.shares


def issued(c,p,job):
    created,_=authorize(c,p)
    intent=created['result']['intent_id']
    material=service(c).material(job,BINDING,DEST,intent)
    result=service(c).issue(job,BINDING,DEST,intent,'issue',material['artifact_sha256'])
    return intent,material,result


def test_atomic_authorization_freezes_projection_and_replays_after_rename(share):
    c,p,job=share
    result,body=authorize(c,p);intent=result['result']['intent_id']
    m=service(c).material(job,BINDING,DEST,intent);raw=base64.b64decode(m['content_base64'])
    assert hashlib.sha256(raw).hexdigest()==m['artifact_sha256']
    assert b'PRIVATE INTERNAL JUDGMENT' not in raw and b'Supply final delivery guide.' not in raw
    assert b'Use this public guide.' in raw
    before=c.app.state.store.get(p['id']);assert len(before['exports'])==1
    c.app.state.store.mutate(p['id'],None,lambda value,db:value.update(name='Changed project name'))
    replay=c.post(f'/api/v1/projects/{p["id"]}/delivery-shares',json=body)
    assert replay.json()['data']==result
    assert len(c.app.state.store.get(p['id'])['exports'])==1
    with pytest.raises(StoreError):service(c).material(job,BINDING,DEST,intent)
    with c.app.state.store.connection() as db:assert db.execute('SELECT md FROM exports').fetchone()[0].encode()==raw


def test_issue_is_one_use_even_with_concurrent_same_key_and_other_key(share):
    c,p,job=share;r,_=authorize(c,p);intent=r['result']['intent_id'];sha=r['result']['artifact_sha256']
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda _:service(c).issue(job,BINDING,DEST,intent,'same-issue',sha),range(4)))
    assert sum(r['result']['send_permitted'] for r in results)==1
    assert len({r['result']['attempt_id'] for r in results})==1
    assert all(r['result']['switch_send_arguments'] is None for r in results if not r['result']['send_permitted'])
    with pytest.raises(StoreError):service(c).issue(job,BINDING,DEST,intent,'different-key',sha)
    with pytest.raises(StoreError):service(c).material(job,BINDING,DEST,intent)
    history=service(c).read_project(p['id'])[0];assert history['state']=='issued_unverified' and len(history['events'])==1
    assert '@' not in next(r['result']['switch_send_arguments']['caption'] for r in results if r['result']['send_permitted'])


@pytest.mark.parametrize('change',['source','review','name','destination','hold'])
def test_rechecks_authority_destination_and_holds_before_issue(share,change):
    c,p,job=share;r,_=authorize(c,p);intent=r['result']['intent_id'];sha=r['result']['artifact_sha256'];dest=DEST
    if change=='source':mutate(c,fresh(c,p),'put','/brief',{'text':'Changed source'})
    elif change=='review':decision(c,fresh(c,p),note='Different private assessment')
    elif change=='name':c.app.state.store.mutate(p['id'],None,lambda value,db:value.update(name='Renamed'))
    elif change=='destination':dest={**DEST,'url':'https://discord.com/channels/111/333'}
    else:question(c,fresh(c,p),job)
    with pytest.raises(StoreError):service(c).issue(job,BINDING,dest,intent,'issue',sha)
    assert not service(c).read_project(p['id'])[0]['events']


def test_export_history_alone_does_not_invalidate_authority(share):
    c,p,job=share;r,_=authorize(c,p);intent=r['result']['intent_id'];current=fresh(c,p)
    response=c.post(f'/api/v1/projects/{p["id"]}/exports',headers={'If-Match':str(current['revision'])},json={'input_hash':current['input_hash'],'acknowledge_unresolved':False})
    assert response.status_code==201
    assert service(c).issue(job,BINDING,DEST,intent,'issue',r['result']['artifact_sha256'])['result']['send_permitted']


def test_draft_and_repeat_return_require_separate_explicit_acknowledgements(share):
    c,p,job=share
    p=decision(c,p,disposition='unresolved')
    v=preview(c,p);assert v['draft']
    with pytest.raises(StoreError):service(c).create(p['id'],BINDING,DEST,'draft-no',expected_revision=v['source_revision'],expected_hash=v['input_hash'],preview_hash=v['preview_hash'],confirmed_reviewed=True)
    r,_=authorize(c,p,acknowledge_draft=True);intent=r['result']['intent_id'];service(c).issue(job,BINDING,DEST,intent,'issue',r['result']['artifact_sha256'])
    assert preview(c,p)['duplicate_risk']
    with pytest.raises(StoreError):service(c).cancel(p['id'],intent,'cancel-no',reason='Cannot confirm return')
    service(c).cancel(p['id'],intent,'cancel',reason='Inspected room; outcome remains unverified',acknowledge_may_have_sent=True)
    v=preview(c,p)
    with pytest.raises(StoreError):service(c).create(p['id'],BINDING,DEST,'repeat-no',expected_revision=v['source_revision'],expected_hash=v['input_hash'],preview_hash=v['preview_hash'],confirmed_reviewed=True,acknowledge_draft=True)
    authorize(c,p,key='repeat',acknowledge_draft=True,acknowledge_duplicate_risk=True)
    assert service(c).read_project(p['id'])[1]['state']=='cancelled_unverified'


def test_local_download_verification_is_exact_and_historical_after_change_and_restart(share):
    c,p,job=share;intent,m,issue=issued(c,p,job);raw=base64.b64decode(m['content_base64']);attempt=issue['result']['attempt_id']
    for content,url in [(b'Wrong bytes',DEST['url']+'/999'),(raw,'https://discord.com/channels/111/333/999')]:
        with pytest.raises(StoreError):service(c).verify(p['id'],intent,'bad',attempt_id=attempt,message_url=url,content=content,confirmed_destination=True)
    mutate(c,fresh(c,p),'put','/brief',{'text':'Changed after issue'})
    # A restart with integration off retains unverified outcome and permits only
    # the local human's exact-byte/destination verification of the old record.
    with local_client(create_app(c.app.state.store.directory)) as disabled:
        history=disabled.get(f'/api/v1/projects/{p["id"]}/delivery-shares').json()['data']
        assert not history['enabled'] and history['items'][0]['state']=='issued_unverified' and not history['items'][0]['is_current']
        metadata={'operation_key':'verify','attempt_id':attempt,'message_url':DEST['url']+'/999','confirmed_destination':True}
        r=disabled.post(f'/api/v1/projects/{p["id"]}/delivery-shares/{intent}/verify',files={'file':('returned.md',raw),'metadata':(None,json.dumps(metadata))})
        assert r.status_code==200,r.text
        result=r.json()['data'];assert result['result']['state']=='operator_confirmed' and not result['result']['is_current']
        replay=disabled.post(f'/api/v1/projects/{p["id"]}/delivery-shares/{intent}/verify',files={'file':('returned.md',raw),'metadata':(None,json.dumps(metadata))})
        assert replay.json()['data']==result
        assert result['result']['verification']=='operator_checked_destination_and_exact_bytes'


def test_scoped_agent_cannot_authorize_verify_cancel_or_change_destination(share):
    c,p,job=share;r,_=authorize(c,p);intent=r['result']['intent_id']
    c.headers.pop('X-Handoff-Token');c.headers.update({'X-Delivery-Token':CONFIG['token'],'X-Delivery-Binding':CONFIG['binding_id']})
    assert c.get(f'/api/v1/delivery/jobs/{job}/shares/{intent}/material').status_code==200
    for method,path in [('GET',f'/api/v1/projects/{p["id"]}/delivery-shares'),('GET',f'/api/v1/projects/{p["id"]}/delivery-share-preview'),('POST',f'/api/v1/projects/{p["id"]}/delivery-shares'),('POST',f'/api/v1/projects/{p["id"]}/delivery-shares/{intent}/verify'),('POST',f'/api/v1/projects/{p["id"]}/delivery-shares/{intent}/cancel'),('POST',f'/api/v1/delivery/jobs/{job}/shares/{intent}/material'),('GET',f'/api/v1/delivery/jobs/{job}/shares/{intent}/issue')]:
        assert c.request(method,path,json={}).status_code==403
    assert c.get(f'/api/v1/delivery/jobs/foreign/shares/{intent}/material').status_code==403
    r=c.post(f'/api/v1/delivery/jobs/{job}/shares/{intent}/issue',json={'operation_key':'issue','artifact_sha256':'a'*64,'destination':DEST})
    assert r.status_code==422


def test_atomic_rollback_preserves_old_exports_and_no_partial_intent(share):
    c,p,job=share;store=c.app.state.store;before=store.get(p['id'])
    with store.connection() as db:db.execute("CREATE TRIGGER synthetic_fail BEFORE INSERT ON delivery_shares BEGIN SELECT RAISE(ABORT,'synthetic fault'); END")
    v=preview(c,p)
    with pytest.raises(sqlite3.IntegrityError):service(c).create(p['id'],BINDING,DEST,'fault',expected_revision=v['source_revision'],expected_hash=v['input_hash'],preview_hash=v['preview_hash'],confirmed_reviewed=True)
    assert store.get(p['id'])==before
    with store.connection() as db:
        assert db.execute('SELECT COUNT(*) FROM exports').fetchone()[0]==0
        assert db.execute('SELECT COUNT(*) FROM delivery_shares').fetchone()[0]==0


def test_schema3_upgrade_preserves_existing_record_bytes(share):
    c,p,job=share;intent,m,issue=issued(c,p,job);store=c.app.state.store
    with store.connection() as db:
        before=db.execute('SELECT * FROM exports').fetchall();db.execute('DROP TABLE delivery_share_events');db.execute('DROP TABLE delivery_shares');db.execute('UPDATE delivery_schema SET version=3')
    DeliveryService(store)
    with store.connection() as db:
        assert db.execute('SELECT * FROM exports').fetchall()==before
        assert db.execute('SELECT version FROM delivery_schema').fetchone()[0]==4


def test_expired_authorization_cannot_issue(share,monkeypatch):
    import handoffready.delivery_share as module
    c,p,job=share
    monkeypatch.setattr(module,'now',lambda:'2000-01-01T00:00:00+00:00')
    r,_=authorize(c,p)
    assert service(c).read_project(p['id'])[0]['state']=='expired'
    with pytest.raises(StoreError):service(c).issue(job,BINDING,DEST,r['result']['intent_id'],'issue',r['result']['artifact_sha256'])


def test_same_review_cannot_accumulate_active_authorizations(share):
    c,p,job=share;first,_=authorize(c,p)
    v=preview(c,p);assert v['active_intent_id']==first['result']['intent_id']
    with pytest.raises(StoreError) as error:
        service(c).create(p['id'],BINDING,DEST,'duplicate-authorization',expected_revision=v['source_revision'],expected_hash=v['input_hash'],preview_hash=v['preview_hash'],confirmed_reviewed=True)
    assert error.value.code=='delivery_share_pending'
    assert len(service(c).read_project(p['id']))==1 and len(c.app.state.store.get(p['id'])['exports'])==1


@pytest.mark.parametrize('flag',[False,1,'true',None])
def test_public_content_confirmation_is_strict_and_saves_nothing(share,flag):
    c,p,job=share;v=preview(c,p)
    r=c.post(f'/api/v1/projects/{p["id"]}/delivery-shares',json={'operation_key':'strict','expected_revision':v['source_revision'],'input_hash':v['input_hash'],'preview_hash':v['preview_hash'],'confirmed_reviewed':flag})
    assert r.status_code==422
    assert not service(c).read_project(p['id']) and not c.app.state.store.get(p['id'])['exports']


def test_artifact_budget_refusal_rolls_back_every_export_and_authorization(share,monkeypatch):
    import handoffready.delivery_share as module
    c,p,job=share;before=c.app.state.store.get(p['id']);monkeypatch.setattr(module,'SHARE_BYTES',1)
    v=preview(c,p)
    with pytest.raises(StoreError) as error:service(c).create(p['id'],BINDING,DEST,'too-large',expected_revision=v['source_revision'],expected_hash=v['input_hash'],preview_hash=v['preview_hash'],confirmed_reviewed=True)
    assert error.value.code=='delivery_share_size'
    assert c.app.state.store.get(p['id'])==before and not service(c).read_project(p['id'])


def test_agent_status_projects_unverified_return_without_private_reason(share):
    c,p,job=share;intent,m,issue=issued(c,p,job)
    result=c.app.state.delivery_service.status(job,BINDING)
    assert result['state']=='return_verification_required' and result['returns'][0]['state']=='issued_unverified'
    service(c).cancel(p['id'],intent,'cancel',reason='PRIVATE CANCELLATION REASON',acknowledge_may_have_sent=True)
    assert 'PRIVATE' not in json.dumps(c.app.state.delivery_service.status(job,BINDING))


@pytest.mark.parametrize('followup',['question','reply','historical_reply'])
def test_context_epoch_change_requires_fresh_share_even_after_hold_clears(share,followup):
    c,p,job=share
    question_id=None
    if followup!='question':
        question_id,_=question(c,fresh(c,p),job)
        body=resolution_body(c,p,key='initial-dismiss')
        assert resolve(c,job,question_id,body).status_code==200
        if followup=='historical_reply':
            current=fresh(c,p)
            current=mutate(c,current,'patch',f'/files/{current["files"][0]["id"]}',{'display_name':'current-guide.txt'})
            decision(c,current)
    created,original_request=authorize(c,p)
    intent=created['result']['intent_id'];sha=created['result']['artifact_sha256']
    previous_preview=preview(c,p)
    before=c.app.state.store.get(p['id'])
    if followup=='question':
        question_id,_=question(c,fresh(c,p),job)
        covered=[]
    else:
        reply_id,_=reply(c,job,question_id,p['input_hash'])
        covered=[reply_id]
    if followup!='historical_reply':
        body=resolution_body(c,p,covered=covered,key='dismiss-followup')
        assert resolve(c,job,question_id,body).status_code==200
    after=c.app.state.store.get(p['id'])
    assert after==before  # Epoch-only changes cannot rely on project currency.
    history=service(c).read_project(p['id'])[0]
    assert history['state']=='superseded' and not history['is_current']
    assert preview(c,p)['preview_hash']!=previous_preview['preview_hash']
    with pytest.raises(StoreError):service(c).material(job,BINDING,DEST,intent)
    with pytest.raises(StoreError):service(c).issue(job,BINDING,DEST,intent,'stale-issue',sha)
    # A stored authorization replay is evidence of that old operation, never
    # fresh consent; its old intent remains unusable after replay.
    replay=c.post(f'/api/v1/projects/{p["id"]}/delivery-shares',json=original_request)
    assert replay.json()['data']==created
    assert service(c).read_project(p['id'])[0]['state']=='superseded'
    stale={**original_request,'operation_key':'stale-preview','expected_revision':previous_preview['source_revision'],
           'input_hash':previous_preview['input_hash'],'preview_hash':previous_preview['preview_hash']}
    refused=c.post(f'/api/v1/projects/{p["id"]}/delivery-shares',json=stale)
    assert refused.status_code==409
    assert refused.json()['error']['code']=='delivery_share_preview_conflict'
    renewed,_=authorize(c,p,key='fresh-context-consent')
    assert service(c).issue(job,BINDING,DEST,renewed['result']['intent_id'],'new-issue',renewed['result']['artifact_sha256'])['result']['send_permitted']


@pytest.mark.parametrize('already_issued',[False,True])
def test_legacy_authorization_without_epoch_is_retained_but_cannot_issue(share,already_issued):
    c,p,job=share
    created,_=authorize(c,p);intent=created['result']['intent_id'];sha=created['result']['artifact_sha256']
    material=service(c).material(job,BINDING,DEST,intent)
    issue=service(c).issue(job,BINDING,DEST,intent,'legacy-issue',sha) if already_issued else None
    store=c.app.state.store
    with store.connection() as db:
        exports_before=db.execute('SELECT * FROM exports').fetchall()
        row=json.loads(db.execute('SELECT body FROM delivery_shares WHERE id=?',(intent,)).fetchone()[0])
        del row['context_epochs']
        db.execute('UPDATE delivery_shares SET body=? WHERE id=?',(json.dumps(row),intent))
    retained=service(c).read_project(p['id'])[0]
    assert retained['state']==('issued_unverified' if already_issued else 'superseded')
    assert not retained['is_current']
    with pytest.raises(StoreError):service(c).material(job,BINDING,DEST,intent)
    with pytest.raises(StoreError):service(c).issue(job,BINDING,DEST,intent,'another-issue',sha)
    if already_issued:
        verified=service(c).verify(p['id'],intent,'legacy-verify',attempt_id=issue['result']['attempt_id'],
            message_url=DEST['url']+'/999',content=base64.b64decode(material['content_base64']),confirmed_destination=True)
        assert verified['result']['state']=='operator_confirmed' and not verified['result']['is_current']
        replay=service(c).issue(job,BINDING,DEST,intent,'legacy-issue',sha)
        assert replay['result']['send_permitted'] is False and replay['result']['switch_send_arguments'] is None
    else:
        authorize(c,p,key='replace-legacy-authorization')
    with store.connection() as db:
        assert db.execute('SELECT * FROM exports WHERE id=?',(created['result']['export_id'],)).fetchall()==exports_before
