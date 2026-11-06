"""HTTP safety regressions using synthetic local context, never a room trial."""

import base64

import pytest
from fastapi.testclient import TestClient

from handoffready.api import create_app
from handoffready.delivery import DeliveryBinding
from handoffready.store import StoreError
from test_api import baseline, create, decision, fresh, mutate, upload
from test_delivery_api import CONFIG, bound_job, scoped


def local_client(app):
    client = TestClient(app, base_url="http://127.0.0.1:8877")
    client.headers.update({"X-Handoff-Token": app.state.token, "Origin": "http://127.0.0.1:8877"})
    return client


@pytest.fixture
def desk(tmp_path):
    with local_client(create_app(tmp_path, delivery_config=CONFIG)) as client:
        yield client


def packet(desk, *, reviewed=False):
    project = upload(desk, baseline(desk, create(desk), [{"kind": "literal_text", "needle": "delivery"}]))
    if reviewed:
        project = decision(desk, project)
    return project, bound_job(desk, project)


def context(desk, project):
    result = desk.get(f'/api/v1/projects/{project["id"]}/delivery-context')
    assert result.status_code == 200, result.text
    return result.json()["data"]["job"]


def question(desk, project, job, *, key="question", text="PRIVATE QUESTION campaign identity?", source="PRIVATE QUESTION SOURCE"):
    state = context(desk, project)
    body = {"operation_key": key, "expected_revision": project["revision"], "input_hash": project["input_hash"],
            "expected_context_epoch": state["context_epoch"], "requirement_id": "r1",
            "file_ids": [project["files"][0]["id"]], "question": text, "source_ref": source}
    result = desk.post(f"/api/v1/delivery/jobs/{job}/questions", json=body)
    assert result.status_code in {200, 201}, result.text
    return result.json()["data"]["result"]["question_id"], body


def reply(desk, job, question_id, original_hash, *, key="reply", source="PRIVATE REPLY SOURCE", text="PRIVATE REPLY confirms campaign identity"):
    body = {"operation_key": key, "question_input_hash": original_hash, "source_ref": source,
            "reported_speaker": "PRIVATE REPORTED SPEAKER", "text": text}
    result = desk.post(f"/api/v1/delivery/jobs/{job}/questions/{question_id}/replies", json=body)
    assert result.status_code in {200, 201}, result.text
    return result.json()["data"]["result"]["reply_id"], body


def resolution_body(desk, project, *, covered=(), used=(), action="dismiss", key="resolve"):
    project = fresh(desk, project)
    return {"operation_key": key, "expected_revision": project["revision"], "input_hash": project["input_hash"],
            "expected_context_epoch": context(desk, project)["context_epoch"], "action": action,
            "covered_reply_ids": list(covered), "used_reply_ids": list(used),
            "reason": "PRIVATE LOCAL REASON checked the conversation source", "confirmed_reviewed": True}


def resolve(desk, job, question_id, body):
    return desk.post(f"/api/v1/delivery/jobs/{job}/questions/{question_id}/resolve", json=body)


def export_request(desk, project):
    project = fresh(desk, project)
    return desk.post(f'/api/v1/projects/{project["id"]}/exports',
                     headers={"If-Match": str(project["revision"])},
                     json={"input_hash": project["input_hash"], "preview_revision": project["revision"],
                           "acknowledge_unresolved": True})


def assert_record_hold(desk, project):
    project = fresh(desk, project)
    assert project["attention_summary"]["status"] == "draft_with_gaps"
    preview = desk.get(f'/api/v1/projects/{project["id"]}/handoff-preview')
    assert preview.status_code == 200, preview.text
    assert preview.json()["data"]["status"] == "draft_with_gaps"
    assert preview.json()["data"]["gaps"]
    assert export_request(desk, project).status_code == 409
    for secret in ("PRIVATE QUESTION", "PRIVATE REPLY", "PRIVATE LOCAL REASON", "PRIVATE REPORTED SPEAKER"):
        assert secret not in preview.text


def test_agent_can_propose_and_reply_but_cannot_resolve_or_save_review(desk):
    project, job = packet(desk)
    epoch = context(desk, project)["context_epoch"]
    scoped(desk)
    body = {"operation_key": "agent_question", "expected_revision": project["revision"],
            "input_hash": project["input_hash"], "expected_context_epoch": epoch, "requirement_id": "r1",
            "file_ids": [project["files"][0]["id"]], "question": "Which campaign was agreed?", "source_ref": "synthetic:q"}
    result = desk.post(f"/api/v1/delivery/jobs/{job}/questions", json=body)
    assert result.status_code in {200, 201}, result.text
    question_id = result.json()["data"]["result"]["question_id"]
    reply(desk, job, question_id, project["input_hash"])
    for method, path in [
        ("POST", f"/api/v1/delivery/jobs/{job}/questions/{question_id}/resolve"),
        ("POST", f'/api/v1/projects/{project["id"]}/exports'),
        ("PUT", f'/api/v1/projects/{project["id"]}/baseline'),
        ("POST", f'/api/v1/projects/{project["id"]}/baseline/approve'),
        ("PUT", f'/api/v1/projects/{project["id"]}/decisions/r1'),
    ]:
        assert desk.request(method, path, json={}).status_code == 403
    assert desk.get(f'/api/v1/projects/{project["id"]}/delivery-context').status_code == 403
    assert desk.post(f"/api/v1/delivery/jobs/{job}/questions", json=dict(body, operation_key="foreign"),
                     headers={"X-Delivery-Binding": "wrong"}).status_code == 403
    assert desk.app.state.store.get(project["id"])["decisions"] == []


@pytest.mark.parametrize("confirmation", [None, False, 1, "true"])
def test_local_resolution_requires_strict_source_review_confirmation(desk, confirmation):
    project, job = packet(desk, reviewed=True)
    question_id, _ = question(desk, project, job)
    before = context(desk, project)
    body = resolution_body(desk, project)
    if confirmation is None:
        del body["confirmed_reviewed"]
    else:
        body["confirmed_reviewed"] = confirmation
    assert resolve(desk, job, question_id, body).status_code == 422
    assert context(desk, project) == before
    assert_record_hold(desk, project)


def test_reply_race_requires_refresh_and_complete_covered_set(desk):
    project, job = packet(desk, reviewed=True)
    question_id, _ = question(desk, project, job)
    first, _ = reply(desk, job, question_id, project["input_hash"])
    stale_body = resolution_body(desk, project, covered=[first])
    second, _ = reply(desk, job, question_id, project["input_hash"], key="reply2", source="synthetic:reply2")
    assert resolve(desk, job, question_id, stale_body).status_code == 409
    incomplete = resolution_body(desk, project, covered=[first], key="incomplete")
    assert resolve(desk, job, question_id, incomplete).status_code == 409
    assert_record_hold(desk, project)
    complete = resolution_body(desk, project, covered=[first, second], key="complete")
    assert resolve(desk, job, question_id, complete).status_code in {200, 201}
    assert context(desk, project)["questions"][0]["state"] == "resolved"
    assert fresh(desk, project)["decisions"][0]["review_state"] == "confirmed"
    assert export_request(desk, project).status_code == 201


def test_acceptance_stales_review_and_preserves_historical_export_bytes(desk):
    project, job = packet(desk, reviewed=True)
    old_export = export_request(desk, project)
    assert old_export.status_code == 201, old_export.text
    export_id = old_export.json()["data"]["export"]["id"]
    downloads = {fmt: desk.get(f'/api/v1/projects/{project["id"]}/exports/{export_id}/{fmt}').content
                 for fmt in ("json", "md", "html")}
    project = fresh(desk, project)
    question_id, _ = question(desk, project, job)
    reply_id, _ = reply(desk, job, question_id, project["input_hash"])
    body = resolution_body(desk, project, covered=[reply_id], used=[reply_id], action="accept")
    result = resolve(desk, job, question_id, body)
    assert result.status_code in {200, 201}, result.text
    committed = result.json()["data"]
    current = fresh(desk, project)
    assert current["input_hash"] != project["input_hash"]
    assert committed["input_hash"] == current["input_hash"]
    assert committed["source_revision"] == current["revision"]
    assert current["decisions"][0]["review_state"] == "stale"
    assert current["attention_summary"]["stale_review_count"] == 1
    assert resolve(desk, job, question_id, body).json()["data"] == committed
    assert fresh(desk, project)["revision"] == current["revision"]
    changed = resolve(desk, job, question_id, dict(body, reason="Different content under same key"))
    assert changed.status_code == 409
    for fmt, content in downloads.items():
        assert desk.get(f'/api/v1/projects/{project["id"]}/exports/{export_id}/{fmt}').content == content
    current = decision(desk, current)
    new_export = export_request(desk, current)
    assert new_export.status_code == 201, new_export.text
    new_id = new_export.json()["data"]["export"]["id"]
    for fmt in ("json", "md", "html"):
        text = desk.get(f'/api/v1/projects/{project["id"]}/exports/{new_id}/{fmt}').text
        for secret in ("PRIVATE QUESTION", "PRIVATE REPLY", "PRIVATE LOCAL REASON", "PRIVATE REPORTED SPEAKER"):
            assert secret not in text


def test_accepting_one_question_does_not_hide_another_pending_question(desk):
    project, job = packet(desk, reviewed=True)
    first, _ = question(desk, project, job)
    second, _ = question(desk, project, job, key="question2", text="Second contextual ambiguity?", source="synthetic:q2")
    reply_id, _ = reply(desk, job, first, project["input_hash"])
    body = resolution_body(desk, project, covered=[reply_id], used=[reply_id], action="accept")
    assert resolve(desk, job, first, body).status_code in {200, 201}
    states = {row["question_id"]: row["state"] for row in context(desk, project)["questions"]}
    assert states == {first: "resolved", second: "pending"}
    assert_record_hold(desk, project)


def test_agent_status_holds_ready_review_without_revealing_context_prose(desk):
    project, job = packet(desk, reviewed=True)
    question_id, _ = question(desk, project, job)
    reply(desk, job, question_id, project["input_hash"])
    scoped(desk)
    result = desk.get(f"/api/v1/delivery/jobs/{job}/status")
    assert result.status_code == 200, result.text
    assert result.json()["data"]["pending_context_count"] == 1
    assert result.json()["data"]["state"] != "ready_to_prepare_record"
    for secret in ("PRIVATE QUESTION", "PRIVATE REPLY", "PRIVATE REPORTED SPEAKER"):
        assert secret not in result.text


@pytest.mark.parametrize("pending", ["question", "receipt"])
def test_context_and_record_hold_survive_delivery_disabled_restart(tmp_path, pending):
    with local_client(create_app(tmp_path, delivery_config=CONFIG)) as desk:
        project, job = packet(desk, reviewed=True)
        question_id = None
        if pending == "question":
            question_id, _ = question(desk, project, job)
        else:
            result = desk.post(f"/api/v1/delivery/jobs/{job}/receipts", json={
                "operation_key": "pending_attachment", "source_id": "synthetic:pending",
                "filename": "replacement-guide.txt", "content_base64": base64.b64encode(b"Pending replacement delivery guide.").decode(),
            })
            assert result.status_code == 201, result.text
        assert_record_hold(desk, project)
    with local_client(create_app(tmp_path)) as desk:
        result = desk.get(f'/api/v1/projects/{project["id"]}/delivery-context')
        assert result.status_code == 200, result.text
        assert result.json()["data"]["enabled"] is False
        if question_id:
            assert result.json()["data"]["job"]["questions"][0]["question_id"] == question_id
        assert_record_hold(desk, project)


def test_new_reply_reopens_dismissed_question_but_source_edit_keeps_it_historical(desk):
    project, job = packet(desk, reviewed=True)
    question_id, _ = question(desk, project, job)
    body = resolution_body(desk, project)
    assert resolve(desk, job, question_id, body).status_code in {200, 201}
    assert export_request(desk, project).status_code == 201
    reply(desk, job, question_id, project["input_hash"])
    assert_record_hold(desk, project)
    project = fresh(desk, project)
    project = mutate(desk, project, "patch", f'/files/{project["files"][0]["id"]}', {"display_name": "corrected-guide.txt"})
    assert context(desk, project)["questions"][0]["state"] == "superseded"
    reply(desk, job, question_id, body["input_hash"], key="late", source="synthetic:late")
    assert context(desk, project)["questions"][0]["state"] == "superseded"
    project = decision(desk, project)
    assert export_request(desk, project).status_code == 201


def test_second_binding_for_same_project_is_refused_without_extra_job(desk):
    project, _ = packet(desk)
    service = desk.app.state.delivery_service
    with pytest.raises(StoreError):
        service.create_job(DeliveryBinding(CONFIG["server"], "second_synthetic_room"), project["id"], "second_binding")
    with service.store.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM delivery_jobs WHERE project_id=?", (project["id"],)).fetchone()[0] == 1


def test_newer_persisted_schema_refused_even_when_delivery_disabled(tmp_path):
    app = create_app(tmp_path, delivery_config=CONFIG)
    with local_client(app) as desk:
        project, _ = packet(desk)
    # Startup would normally interrupt this synthetic job and write the project.
    # Unsupported integration state must be refused before that recovery write.
    app.state.store.mutate(project["id"], None, lambda value, db: value["jobs"].append({
        "id": "synthetic_running_job", "state": "running", "stage": "synthetic", "error": None,
    }))
    with app.state.store.connection() as db:
        before_projects = db.execute("SELECT * FROM projects").fetchall()
        db.execute("UPDATE delivery_schema SET version=999")
    with pytest.raises(StoreError):
        create_app(tmp_path)
    with app.state.store.connection() as db:
        assert db.execute("SELECT version FROM delivery_schema").fetchone()[0] == 999
        assert db.execute("SELECT * FROM projects").fetchall() == before_projects


def test_bound_project_delete_guard_is_in_store_transaction_and_survives_disabled_config(desk):
    project, _ = packet(desk, reviewed=True)
    record = export_request(desk, project)
    assert record.status_code == 201
    project = fresh(desk, project)
    store = desk.app.state.store
    with store.connection() as db:
        before = db.execute('SELECT * FROM exports').fetchall()
    # Direct Store use must enforce retention too, rather than trusting an API
    # preflight that could race with room binding.
    with pytest.raises(StoreError) as error:
        store.delete(project['id'], project['revision'])
    assert error.value.code == 'delivery_project_bound'
    with local_client(create_app(store.directory)) as disabled:
        result = disabled.delete(f'/api/v1/projects/{project["id"]}',headers={'If-Match':str(project['revision'])})
        assert result.status_code == 409
        assert result.json()['error']['code'] == 'delivery_project_bound'
    with store.connection() as db:
        assert db.execute('SELECT * FROM exports').fetchall() == before
    assert [{k:v for k,v in f.items() if k != '_path'} for f in store.get(project['id'])['files']] == project['files']
