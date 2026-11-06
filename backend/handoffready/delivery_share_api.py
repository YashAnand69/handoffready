"""Local authorization/verification and narrowly scoped artifact issue routes."""
import asyncio

from fastapi import Request
from pydantic import Field

from .delivery_share import SHARE_BYTES
from .schemas import Payload
from .store import StoreError


class ShareCreate(Payload):
    operation_key: str = Field(min_length=1,max_length=128)
    expected_revision: int = Field(ge=1,le=2**53-1)
    input_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    preview_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    confirmed_reviewed: bool
    acknowledge_draft: bool = False
    acknowledge_duplicate_risk: bool = False


class ShareIssue(Payload):
    operation_key: str = Field(min_length=1,max_length=128)
    artifact_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')


class ShareCancel(Payload):
    operation_key: str = Field(min_length=1,max_length=128)
    reason: str = Field(min_length=1,max_length=1000)
    acknowledge_may_have_sent: bool = False


class ShareVerify(Payload):
    operation_key: str = Field(min_length=1,max_length=128)
    attempt_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    message_url: str = Field(min_length=1,max_length=512)
    confirmed_destination: bool


def install_share_routes(app, service, config, response):
    store=app.state.store

    @app.get('/api/v1/projects/{project_id}/delivery-shares')
    def local_shares(project_id: str):
        store.get(project_id)
        bound=False
        if service is not None:
            with store.connection() as db:
                bound=db.execute('SELECT 1 FROM delivery_jobs WHERE project_id=?',(project_id,)).fetchone() is not None
        return response({'enabled':config is not None and config.destination is not None,'bound':bound,
                         'items':service.shares.read_project(project_id) if service else []})

    def configured():
        if service is None or config is None or config.destination is None:
            raise StoreError('delivery_share_disabled','Configure the reviewed destination to authorize a new return.',409)

    @app.get('/api/v1/projects/{project_id}/delivery-share-preview')
    def local_share_preview(project_id: str):
        configured()
        return response(service.shares.preview(project_id,config.binding,config.destination))

    @app.post('/api/v1/projects/{project_id}/delivery-shares')
    def local_authorize_share(project_id: str, payload: ShareCreate):
        configured()
        return response(service.shares.create(project_id,config.binding,config.destination,payload.operation_key,
            expected_revision=payload.expected_revision,expected_hash=payload.input_hash,preview_hash=payload.preview_hash,
            confirmed_reviewed=payload.confirmed_reviewed,acknowledge_draft=payload.acknowledge_draft,
            acknowledge_duplicate_risk=payload.acknowledge_duplicate_risk),201)

    @app.post('/api/v1/projects/{project_id}/delivery-shares/{intent_id}/cancel')
    def local_cancel_share(project_id: str,intent_id: str,payload: ShareCancel):
        if service is None:raise StoreError('delivery_share_missing','No retained share exists.',404)
        return response(service.shares.cancel(project_id,intent_id,payload.operation_key,reason=payload.reason,
                        acknowledge_may_have_sent=payload.acknowledge_may_have_sent))

    @app.post('/api/v1/projects/{project_id}/delivery-shares/{intent_id}/verify')
    async def local_verify_share(project_id: str,intent_id: str,request: Request):
        if service is None:raise StoreError('delivery_share_missing','No retained share exists.',404)
        async with request.form(max_files=1,max_fields=1,max_part_size=SHARE_BYTES) as form:
            if set(form)!= {'file','metadata'} or len(form.multi_items())!=2:
                raise StoreError('delivery_invalid_input','Choose exactly the returned file and its verification details.',422)
            file,metadata=form['file'],form['metadata']
            if not hasattr(file,'read') or not isinstance(metadata,str) or len(metadata)>8192:
                raise StoreError('delivery_invalid_input','Choose a bounded file and verification details.',422)
            try:payload=ShareVerify.model_validate_json(metadata)
            except ValueError:raise StoreError('delivery_invalid_input','Invalid verification details.',422) from None
            content=await file.read(SHARE_BYTES+1)
            return response(await asyncio.to_thread(service.shares.verify,project_id,intent_id,payload.operation_key,
                attempt_id=payload.attempt_id,message_url=payload.message_url,content=content,
                confirmed_destination=payload.confirmed_destination))

    if service is None or config is None or config.destination is None:return

    @app.get('/api/v1/delivery/jobs/{job_id}/shares/{intent_id}/material')
    def share_material(job_id: str,intent_id: str):
        return response(service.shares.material(job_id,config.binding,config.destination,intent_id))

    @app.post('/api/v1/delivery/jobs/{job_id}/shares/{intent_id}/issue')
    def issue_share(job_id: str,intent_id: str,payload: ShareIssue):
        return response(service.shares.issue(job_id,config.binding,config.destination,intent_id,payload.operation_key,payload.artifact_sha256))
