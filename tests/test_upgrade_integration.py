"""Upgrade contracts exercised through the actual API with declared model doubles."""
import copy
import hashlib
import threading
import time

import pytest
from fastapi.testclient import TestClient
from handoffready.api import create_app
from handoffready.evidence import source_catalog
from handoffready.schemas import CheckSpec
from handoffready.store import canonical, digest
from test_api import FakeModel, create, mutate, fresh, baseline, upload, decision, wait_job


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path, FakeModel())
    with TestClient(app, base_url="http://127.0.0.1:8877") as connection:
        token = connection.get("/api/v1/bootstrap").json()["data"]["token"]
        connection.headers.update({"X-Handoff-Token": token, "Origin": "http://127.0.0.1:8877"})
        yield connection


def requirement(project, span):
    return {"id": "repeat", "title": "SVG logo", "origin": "model_suggested", "source_id": project["brief"]["id"], "quote": span["quote"], "source_span": span, "checks": [{"kind": "presence", "types": ["svg"]}], "human_note": ""}


def test_repeated_occurrence_approval_and_noop_save(client):
    project = mutate(client, create(client), "PUT", "/brief", {"text": "🐦 intro.\r\nDeliver an SVG logo.\r\nDeliver an SVG logo."})
    units = source_catalog(project["brief"]["text"], project["brief"]["id"])
    row = requirement(project, units[-1])
    project = mutate(client, project, "PUT", "/baseline", {"requirements": [row]})
    project = mutate(client, project, "POST", "/baseline/approve", {"baseline_hash": project["baseline"]["hash"], "reviewed_requirement_ids": ["repeat"]})
    after = mutate(client, project, "PUT", "/baseline", {"requirements": project["baseline"]["requirements"]})
    assert after["revision"] == project["revision"]
    assert after["baseline"] == project["baseline"]
    assert after["baseline"]["requirements"][0]["source_span"]["start_cp"] == units[-1]["start_cp"]
    forged = copy.deepcopy(row)
    forged["source_span"]["start_cp"] = units[1]["start_cp"]
    result = client.put(f'/api/v1/projects/{project["id"]}/baseline', headers={"If-Match": str(project["revision"])}, json={"requirements": [forged]})
    assert result.status_code == 422
    assert fresh(client, project)["baseline"] == project["baseline"]


def test_valid_legacy_repeated_span_remains_unchanged(client):
    project = mutate(client, create(client), "PUT", "/brief", {"text": "Deliver an SVG logo.\nDeliver an SVG logo."})
    span = source_catalog(project["brief"]["text"], project["brief"]["id"])[1]
    span.pop("evidence_unit_id")
    span.pop("catalog_version")
    project = mutate(client, project, "PUT", "/baseline", {"requirements": [requirement(project, span)]})
    project = mutate(client, project, "POST", "/baseline/approve", {"baseline_hash": project["baseline"]["hash"], "reviewed_requirement_ids": ["repeat"]})
    after = mutate(client, project, "PUT", "/baseline", {"requirements": project["baseline"]["requirements"]})
    assert after["baseline"]["requirements"][0]["source_span"] == span
    assert after["revision"] == project["revision"]


def test_identical_normalized_filename_does_not_parse_or_invalidate(client, monkeypatch):
    project = decision(client, upload(client, baseline(client, create(client))))
    def unexpected(*args):
        raise AssertionError("No-op rename must not invoke the parser")
    monkeypatch.setattr("handoffready.api.inspect_bounded", unexpected)
    after = mutate(client, project, "PATCH", f'/files/{project["files"][0]["id"]}', {"display_name": "folder/guide.txt"})
    assert after["revision"] == project["revision"]
    assert after["decisions"] == project["decisions"]
    assert after["input_hash"] == project["input_hash"]


def test_exception_explained_separately_and_old_export_immutable(client):
    project = baseline(client, create(client), [{"kind": "presence", "types": ["pdf"]}])
    project = decision(client, project, "not_applicable", note="PRIVATE_SCOPE_REASON")
    preview = client.get(f'/api/v1/projects/{project["id"]}/handoff-preview').json()["data"]
    assert preview["status"] == "draft_with_gaps"
    saved = mutate(client, project, "POST", "/exports", {"acknowledge_unresolved": True, "input_hash": project["input_hash"], "preview_revision": project["revision"]})
    export_id = saved["export"]["id"]
    paths = [f'/api/v1/projects/{project["id"]}/exports/{export_id}/{format}' for format in ("json", "md", "html")]
    old = [client.get(path).content for path in paths]
    assert all(b"PRIVATE_SCOPE_REASON" not in body for body in old)
    project = fresh(client, project)
    project = mutate(client, project, "PUT", "/decisions/r1", {"file_ids": [], "review_state": "confirmed", "human_disposition": "not_applicable", "internal_decision_note": "PRIVATE_SCOPE_REASON", "client_exception_note": "Excluded from this packet by reviewer.", "input_hash": project["input_hash"]})
    preview = client.get(f'/api/v1/projects/{project["id"]}/handoff-preview').json()["data"]
    assert preview["status"] == "reviewed_with_exceptions"
    assert preview["attention_summary"]["unknown_check_count"] == 1
    assert preview["requirements"][0]["checks"][0]["status"] == "unknown"
    assert preview["source_revision"] == project["revision"]
    assert [client.get(path).content for path in paths] == old


def test_same_inputs_new_decisions_reject_stale_preview(client):
    project = decision(client, upload(client, baseline(client, create(client))))
    before = project["revision"]
    project = decision(client, project, "needs_work")
    result = client.post(f'/api/v1/projects/{project["id"]}/exports', headers={"If-Match": str(project["revision"])}, json={"acknowledge_unresolved": True, "input_hash": project["input_hash"], "preview_revision": before})
    assert result.status_code == 409
    assert result.json()["error"]["code"] == "stale_preview"
    assert fresh(client, project)["exports"] == []


def test_new_model_occurrence_passes_publication_boundary(tmp_path):
    class OccurrenceModel:
        def extract(self, brief, **kwargs):
            span = source_catalog(brief["text"], brief["id"])[1]
            return {"requirements": [{"title": "Repeated logo", "quote": span["quote"], "source_span": span, "checks": [{"kind": "presence", "types": ["svg"]}]}], "model": {"test_double": True}}
    app = create_app(tmp_path, OccurrenceModel())
    with TestClient(app, base_url="http://127.0.0.1:8877") as connection:
        connection.headers.update({"X-Handoff-Token": app.state.token, "Origin": "http://127.0.0.1:8877"})
        project = mutate(connection, create(connection), "PUT", "/brief", {"text": "Deliver an SVG logo.\nDeliver an SVG logo."})
        started = mutate(connection, project, "POST", "/jobs/extract", {})
        assert wait_job(connection, project, started["job"]["id"])["state"] == "succeeded"
        assert fresh(connection, project)["baseline"]["requirements"][0]["source_span"]["start_cp"] > 0


def test_tampering_during_model_job_commits_invalidation_without_polling(tmp_path):
    entered, release = threading.Event(), threading.Event()
    class BlockingModel:
        def match(self, brief, requirements, files, **kwargs):
            entered.set()
            assert release.wait(5)
            span = source_catalog(files[0]["text"], files[0]["id"])[0]
            return {"proposals": [{"requirement_id": "r1", "candidates": [{"file_id": files[0]["id"], "reason": "Declared double", "quote": span["quote"], "source_span": span}]}], "model": {"test_double": True}}
    app = create_app(tmp_path, BlockingModel())
    with TestClient(app, base_url="http://127.0.0.1:8877") as connection:
        connection.headers.update({"X-Handoff-Token": app.state.token, "Origin": "http://127.0.0.1:8877"})
        project = decision(connection, upload(connection, baseline(connection, create(connection))))
        started = mutate(connection, project, "POST", "/jobs/match", {})
        assert entered.wait(5)
        stored = app.state.store.get(project["id"])
        file = stored["files"][0]
        path = app.state.store.files / file["_path"]
        path.write_bytes(b"x" * file["size"])
        assert hashlib.sha256(path.read_bytes()).hexdigest() != file["sha256"]
        release.set()
        # Read Store only: no API middleware poll can perform the repair for us.
        until = time.monotonic() + 5
        while time.monotonic() < until:
            stored = app.state.store.get(project["id"])
            job = next(j for j in stored["jobs"] if j["id"] == started["job"]["id"])
            if job["state"] != "running":
                break
            time.sleep(.01)
        assert job["state"] == "superseded"
        assert stored["files"][0]["inspection"] == "blocked"
        assert stored["decisions"][0]["review_state"] == "stale"
        assert stored["proposals"] == []
        assert stored["files"][0]["sha256"] == file["sha256"]


def test_selection_preview_does_not_save_or_approve(client):
    project = upload(client, baseline(client, create(client), [{"kind": "presence", "types": ["text"]}, {"kind": "manual", "instruction": "Judge instructional usefulness."}]))
    before = client.app.state.store.get(project["id"])
    file_ids = [project["files"][0]["id"]]
    result = client.post(f'/api/v1/projects/{project["id"]}/requirements/r1/check-preview', headers={"If-Match": str(project["revision"])}, json={"file_ids": file_ids, "input_hash": project["input_hash"]})
    assert result.status_code == 200, result.text
    preview = result.json()["data"]
    assert preview["preview"] is True and preview["file_ids"] == file_ids
    assert preview["source_revision"] == project["revision"]
    assert [c["status"] for c in preview["checks"]] == ["pass", "unknown"]
    assert client.app.state.store.get(project["id"]) == before
    assert fresh(client, project)["attention_summary"]["current_review_count"] == 0


def test_preview_rejects_stale_unknown_duplicate_and_foreign_ids(client):
    project = upload(client, baseline(client, create(client)))
    url = f'/api/v1/projects/{project["id"]}/requirements/r1/check-preview'
    body = {"file_ids": [project["files"][0]["id"]], "input_hash": project["input_hash"]}
    assert client.post(url, headers={"If-Match": str(project["revision"] - 1)}, json=body).status_code == 409
    assert client.post(url, headers={"If-Match": str(project["revision"])}, json={**body, "file_ids": ["unknown"]}).status_code == 422
    assert client.post(url, headers={"If-Match": str(project["revision"])}, json={**body, "file_ids": body["file_ids"] * 2}).status_code == 422
    assert client.post(url, headers={"If-Match": str(project["revision"]), "Origin": "https://evil.test"}, json=body).status_code == 403


def test_preview_commits_detected_integrity_damage_before_conflict(client):
    project = decision(client, upload(client, baseline(client, create(client))))
    file = client.app.state.store.get(project["id"])["files"][0]
    (client.app.state.store.files / file["_path"]).write_bytes(b"x" * file["size"])
    result = client.post(f'/api/v1/projects/{project["id"]}/requirements/r1/check-preview', headers={"If-Match": str(project["revision"])}, json={"file_ids": [file["id"]], "input_hash": project["input_hash"]})
    assert result.status_code == 409
    stored = client.app.state.store.get(project["id"])
    assert stored["revision"] > project["revision"]
    assert stored["files"][0]["inspection"] == "blocked"
    assert stored["decisions"][0]["review_state"] == "stale"


def test_status_poll_does_not_read_originals_or_expose_private_evidence(client, monkeypatch):
    project = upload(client, baseline(client, create(client)))
    store = client.app.state.store
    def register_job(current, db):
        current["jobs"] = [{"id": "j", "kind": "match", "state": "running", "stage": "working", "error": None, "model": {"private": "DO_NOT_EXPOSE"}, "_input": {"brief": "DO_NOT_EXPOSE"}}]
    store.mutate(project["id"], project["revision"], register_job)
    checked = []
    verify = store._original_error
    def count(file):
        checked.append(file["id"])
        return verify(file)
    monkeypatch.setattr(store, "_original_error", count)
    response = client.get(f'/api/v1/projects/{project["id"]}/job-status')
    assert response.status_code == 200 and checked == []
    assert set(response.json()["data"]) == {"jobs", "revision"}
    assert set(response.json()["data"]["jobs"][0]) == {"id", "kind", "state", "stage", "error"}
    assert "DO_NOT_EXPOSE" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert client.get(f'/api/v1/projects/{project["id"]}/job-status', headers={"X-Handoff-Token": "wrong"}).status_code == 403
    assert checked == []
    assert client.get(f'/api/v1/projects/{project["id"]}').status_code == 200
    assert checked == [project["files"][0]["id"]]


@pytest.mark.parametrize("model_source", [False, True])
def test_persisted_v01_null_shape_noop_preserves_approved_scope_and_history(client, model_source):
    project = baseline(client, create(client))
    if model_source:
        span = source_catalog(project["brief"]["text"], project["brief"]["id"])[0]
        span.pop("evidence_unit_id")
        span.pop("catalog_version")
        row = {"id": "r1", "title": "Delivery guide", "origin": "model_suggested",
               "source_id": project["brief"]["id"], "quote": span["quote"], "source_span": span,
               "checks": [{"kind": "manual", "instruction": "Review guide quality."}], "human_note": ""}
        project = mutate(client, project, "PUT", "/baseline", {"requirements": [row]})
        project = mutate(client, project, "POST", "/baseline/approve", {"baseline_hash": project["baseline"]["hash"], "reviewed_requirement_ids": ["r1"]})
    store = client.app.state.store
    def restore_v01_shape(current, db):
        for row in current["baseline"]["requirements"]:
            # The v0.1 CheckSpec model_dump included all unused null parameters.
            row["checks"] = [CheckSpec.model_validate(check).model_dump() for check in row["checks"]]
        current["baseline"]["hash"] = digest(current["baseline"]["requirements"])
    store.mutate(project["id"], project["revision"], restore_v01_shape)
    project = fresh(client, project)
    project = decision(client, upload(client, project))
    before = store.get(project["id"])
    submitted = copy.deepcopy(project["baseline"]["requirements"])
    if model_source:
        # New optional span fields may be serialized by a client as explicit null.
        submitted[0]["source_span"].update(evidence_unit_id=None, catalog_version=None)
    saved = mutate(client, project, "PUT", "/baseline", {"requirements": submitted})
    assert saved["revision"] == project["revision"]
    assert saved["baseline"]["state"] == "approved"
    assert canonical(store.get(project["id"])) == canonical(before)
    assert any(value is None for value in saved["baseline"]["requirements"][0]["checks"][0].values())
    if model_source:
        assert "evidence_unit_id" not in saved["baseline"]["requirements"][0]["source_span"]

    changed = copy.deepcopy(submitted)
    changed[0]["checks"][0]["instruction"] = "Review guide quality and confirm contact details."
    edited = mutate(client, saved, "PUT", "/baseline", {"requirements": changed})
    assert edited["revision"] > saved["revision"]
    assert edited["baseline"]["state"] == "draft"
    assert edited["baseline"]["hash"] != saved["baseline"]["hash"]
    assert edited["decisions"][0]["review_state"] == "stale"
    assert store.get(project["id"])["baseline_history"][-1]["baseline"] == before["baseline"]


def test_invalid_submitted_occurrence_is_rejected_before_legacy_noop_comparison(client):
    project = mutate(client, create(client), "PUT", "/brief", {"text": "Deliver an SVG logo.\nDeliver an SVG logo."})
    span = source_catalog(project["brief"]["text"], project["brief"]["id"])[1]
    row = requirement(project, span)
    project = mutate(client, project, "PUT", "/baseline", {"requirements": [row]})
    project = mutate(client, project, "POST", "/baseline/approve", {"baseline_hash": project["baseline"]["hash"], "reviewed_requirement_ids": ["repeat"]})
    before = canonical(client.app.state.store.get(project["id"]))
    submitted = copy.deepcopy(project["baseline"]["requirements"])
    submitted[0]["source_span"]["catalog_version"] = "unsupported"
    response = client.put(f'/api/v1/projects/{project["id"]}/baseline', headers={"If-Match": str(project["revision"])}, json={"requirements": submitted})
    assert response.status_code == 422
    assert canonical(client.app.state.store.get(project["id"])) == before
