"""Synthetic intake HTTP boundary; model cannot confirm packets or save reviews."""
import base64

import pytest
from fastapi.testclient import TestClient

from handoffready.api import create_app
from handoffready.delivery_api import STAGE_REQUEST_BYTES
from test_delivery_api import desk as desk, scoped, bound_job
from test_api import create


def stage_body(**changes):
    return {"operation_key":"source1","source_id":"discord-synthetic1","filename":"guide.txt","content_base64":base64.b64encode(b"Synthetic readable guide.").decode(),**changes}


def test_scoped_stage_does_not_commit_and_local_confirmation_required(desk):
    project=create(desk);job=bound_job(desk,project);token=desk.app.state.token
    scoped(desk)
    staged=desk.post(f"/api/v1/delivery/jobs/{job}/receipts",json=stage_body())
    assert staged.status_code == 201, staged.text
    receipt=staged.json()["data"]["result"]["receipt_id"]
    assert desk.app.state.store.get(project["id"])["files"] == []
    for method,suffix,payload in [("GET","receipts",None),("POST","packet-preview",{}),("POST","packet-confirm",{})]:
        assert desk.request(method,f"/api/v1/delivery/jobs/{job}/{suffix}",json=payload).status_code == 403
    desk.headers["X-Handoff-Token"]=token
    context=desk.get(f'/api/v1/projects/{project["id"]}/delivery').json()["data"]
    assert context["enabled"] and context["job"]["pending_count"] == 1
    body={"receipt_ids":[receipt],"expected_revision":project["revision"],"input_hash":project["input_hash"]}
    view=desk.post(f"/api/v1/delivery/jobs/{job}/packet-preview",json=body)
    assert view.status_code == 200, view.text
    payload={**body,"operation_key":"confirm","manifest_hash":view.json()["data"]["manifest_hash"]}
    for complete in [None,False,"true"]:
        invalid=payload if complete is None else {**payload,"confirmed_complete":complete}
        assert desk.post(f"/api/v1/delivery/jobs/{job}/packet-confirm",json=invalid).status_code == 422
    confirmed=desk.post(f"/api/v1/delivery/jobs/{job}/packet-confirm",json={**payload,"confirmed_complete":True})
    assert confirmed.status_code == 200,confirmed.text
    assert len(desk.app.state.store.get(project["id"])["files"]) == 1
    assert desk.app.state.store.get(project["id"])["decisions"] == []
    assert desk.post(f"/api/v1/delivery/jobs/{job}/packet-confirm",json={**payload,"confirmed_complete":True}).json() == confirmed.json()


@pytest.mark.parametrize("changes", [{"content_base64":"not base64 secret-marker"},{"content_base64":""},{"filename":"../secret.txt"},{"source_id":"\nprivate-marker"},{"room":"foreign"}])
def test_invalid_intake_redacted_and_no_receipt(desk,changes):
    project=create(desk);job=bound_job(desk,project);scoped(desk)
    response=desk.post(f"/api/v1/delivery/jobs/{job}/receipts",json=stage_body(**changes))
    assert response.status_code == 422
    assert "secret-marker" not in response.text and "private-marker" not in response.text
    assert desk.get(f"/api/v1/delivery/jobs/{job}/status").json()["data"]["staged_receipts"] == 0


def test_intake_specific_body_budget_and_wrong_binding(desk):
    project=create(desk);job=bound_job(desk,project);scoped(desk)
    large=stage_body(content_base64=base64.b64encode(b"x"*(300*1024)).decode())
    assert desk.post(f"/api/v1/delivery/jobs/{job}/receipts",json=large).status_code == 201
    assert desk.post(f"/api/v1/delivery/jobs/{job}/preview",json=large).status_code == 413
    assert desk.post(f"/api/v1/delivery/jobs/{job}/receipts",json=stage_body(),headers={"Content-Length":str(STAGE_REQUEST_BYTES+1)}).status_code == 413
    assert desk.post(f"/api/v1/delivery/jobs/{job}/receipts",json=stage_body(),headers={"X-Delivery-Binding":"foreign"}).status_code == 403
    assert desk.post(f"/api/v1/delivery/jobs/{job}/receipts",json=stage_body(),headers={"Origin":"https://foreign.example"}).status_code == 403


def test_disabled_delivery_context_and_capability(tmp_path):
    app=create_app(tmp_path)
    with TestClient(app,base_url="http://127.0.0.1:8877") as client:
        client.headers.update({"X-Handoff-Token":app.state.token,"Origin":"http://127.0.0.1:8877"})
        project=create(client)
        assert client.get(f'/api/v1/projects/{project["id"]}/delivery').json()["data"] == {"enabled":False,"job":None}
        assert client.get('/api/v1/capabilities').json()["data"]["delivery"] == {"enabled":False}


def test_bound_project_delete_cannot_orphan_room_or_receipts(desk):
    project=create(desk);job=bound_job(desk,project)
    response=desk.delete(f'/api/v1/projects/{project["id"]}',headers={"If-Match":str(project["revision"])})
    assert response.status_code == 409 and response.json()["error"]["code"] == "delivery_project_bound"
    assert desk.get(f'/api/v1/projects/{project["id"]}').status_code == 200
    assert desk.get(f'/api/v1/delivery/jobs/{job}/status').status_code == 200
