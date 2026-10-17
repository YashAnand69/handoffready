"""API tests use explicitly fake inference; these are not model-performance evidence."""
import json
import threading
import time
import pytest
from fastapi.testclient import TestClient
from handoffready.api import create_app
from handoffready.store import Store


class FakeModel:
    def ready(self):
        return {"available": True, "test_double": True}

    def extract(self, brief, *, deadline=None):
        return {"requirements": [{"title": "Delivery guide", "quote": brief["text"], "checks": [{"kind": "manual", "instruction": "Review guide quality."}]}], "model": {"test_double": True}}

    def match(self, brief, requirements, files, *, deadline=None):
        return {"proposals": [{"requirement_id": r["id"], "candidates": [{"file_id": f["id"], "reason": "Explicit test mapping"} for f in files if f["inspection"] == "inspected"], "coverage": "Test double"} for r in requirements], "model": {"test_double": True}}


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path, FakeModel())
    with TestClient(app, base_url="http://127.0.0.1:8877") as result:
        token = result.get("/api/v1/bootstrap").json()["data"]["token"]
        result.headers.update({"X-Handoff-Token": token, "Origin": "http://127.0.0.1:8877"})
        yield result


def create(client):
    result = client.post("/api/v1/projects", json={"name": "Fixture project"})
    assert result.status_code == 201, result.text
    return result.json()["data"]


def mutate(client, project, method, suffix, payload=None, **kwargs):
    result = client.request(method.upper(), f'/api/v1/projects/{project["id"]}' + suffix, json=payload, headers={"If-Match": str(project["revision"])}, **kwargs)
    assert result.status_code in {200, 201, 202}, result.text
    return result.json()["data"]


def fresh(client, project):
    return client.get(f'/api/v1/projects/{project["id"]}').json()["data"]


def baseline(client, project, checks=None):
    project = mutate(client, project, "put", "/brief", {"text": "Supply final delivery guide.", "source_label": "Private brief"})
    requirements = [{"id": "r1", "title": "Delivery guide", "origin": "human_added", "quote": None, "source_id": None, "checks": checks or [{"kind": "manual", "instruction": "Review guide quality."}], "human_note": "Explicit human requirement"}]
    project = mutate(client, project, "put", "/baseline", {"requirements": requirements})
    return mutate(client, project, "post", "/baseline/approve", {"baseline_hash": project["baseline"]["hash"], "reviewed_requirement_ids": ["r1"]})


def upload(client, project, data=b"A delivery guide.", name="guide.txt"):
    result = client.post(f'/api/v1/projects/{project["id"]}/files', files=[("files[]", (name, data))], headers={"If-Match": str(project["revision"])})
    assert result.status_code == 201, result.text
    return result.json()["data"]


def decision(client, project, disposition="satisfied", note="SECRET PRIVATE NOTE", client_note="Use this guide."):
    return mutate(client, project, "put", "/decisions/r1", {"file_ids": [f["id"] for f in project["files"]], "review_state": "confirmed", "human_disposition": disposition, "internal_decision_note": note, "client_usage_note": client_note, "input_hash": project["input_hash"]})


def wait_job(client, project, job_id):
    for _ in range(100):
        job = client.get(f'/api/v1/projects/{project["id"]}/jobs/{job_id}').json()["data"]
        if job["state"] not in {"queued", "running"}:
            return job
        time.sleep(.01)
    raise AssertionError("Job did not finish")


def test_security_reads_writes_hosts_origins(client):
    assert client.get("/api/v1/projects", headers={"X-Handoff-Token": "wrong"}).status_code == 403
    assert client.post("/api/v1/projects", json={"name": "Leak"}, headers={"Origin": "https://evil.test"}).status_code == 403
    assert client.get("/api/v1/bootstrap", headers={"Host": "evil.test"}).status_code == 403
    assert client.post("/api/v1/projects", json={"name": "Leak"}, headers={"Origin": "null"}).status_code == 403
    assert client.get("/api/v1/projects").headers["cache-control"] == "no-store"


def test_optimistic_revision_prevents_overwrite(client):
    project = create(client)
    assert client.put(f'/api/v1/projects/{project["id"]}/brief', json={"text": "Brief"}).status_code == 428
    new = mutate(client, project, "put", "/brief", {"text": "Current"})
    result = client.put(f'/api/v1/projects/{project["id"]}/brief', headers={"If-Match": str(project["revision"])}, json={"text": "Stale"})
    assert result.status_code == 409
    assert fresh(client, new)["brief"]["text"] == "Current"


def test_quote_integrity_and_approval_review(client):
    project = create(client)
    project = mutate(client, project, "put", "/brief", {"text": "Same. Same. Unique 🐦."})
    row = {"id": "r1", "title": "Clause", "origin": "model_suggested", "source_id": project["brief"]["id"], "quote": "Same.", "checks": [{"kind": "manual", "instruction": "Review"}], "human_note": ""}
    url = f'/api/v1/projects/{project["id"]}/baseline'
    assert client.put(url, headers={"If-Match": str(project["revision"])}, json={"requirements": [row]}).status_code == 422
    row["quote"] = "Unique 🐦."
    project = mutate(client, project, "put", "/baseline", {"requirements": [row]})
    result = client.post(url + "/approve", headers={"If-Match": str(project["revision"])}, json={"baseline_hash": project["baseline"]["hash"], "reviewed_requirement_ids": []})
    assert result.status_code == 409


@pytest.mark.parametrize("check", [
    {"kind": "count", "types": ["png"], "comparison": "exact", "value": True, "distinct_bytes": True},
    {"kind": "count", "types": ["png"], "comparison": "exact", "value": 3},
    {"kind": "count", "types": [], "comparison": "exact", "value": 3, "distinct_bytes": False},
    {"kind": "manual", "instruction": "Review", "value": 5},
    {"kind": "image_dimensions", "width_px": 1080, "height_px": 10001},
])
def test_strict_check_parameters(client, check):
    project = create(client)
    row = {"id": "r1", "title": "Clause", "origin": "human_added", "human_note": "Human", "checks": [check]}
    result = client.put(f'/api/v1/projects/{project["id"]}/baseline', headers={"If-Match": str(project["revision"])}, json={"requirements": [row]})
    assert result.status_code == 422
    assert "input" not in result.text


def test_private_persistence_stale_guard_and_exports(client):
    project = baseline(client, create(client), [{"kind": "literal_text", "needle": "delivery"}])
    project = upload(client, project)
    assert project["files"][0]["inspection"] == "inspected"
    assert "_path" not in project["files"][0]
    project = decision(client, project)
    assert project["checks"][0]["status"] == "pass"
    exported = mutate(client, project, "post", "/exports", {"acknowledge_unresolved": False, "input_hash": project["input_hash"]})
    export_id = exported["export"]["id"]
    original = {}
    for format in ("json", "md", "html"):
        result = client.get(f'/api/v1/projects/{project["id"]}/exports/{export_id}/{format}')
        assert result.status_code == 200
        assert "SECRET PRIVATE NOTE" not in result.text
        assert "Supply final delivery guide." not in result.text
        assert "Use this guide." in result.text
        original[format] = result.text
    project = fresh(client, project)
    old_hash = project["input_hash"]
    project = mutate(client, project, "patch", f'/files/{project["files"][0]["id"]}', {"display_name": "renamed.txt"})
    assert project["input_hash"] != old_hash
    assert project["decisions"][0]["review_state"] == "stale"
    assert project["checks"][0]["status"] == "unknown"
    for format in original:
        assert client.get(f'/api/v1/projects/{project["id"]}/exports/{export_id}/{format}').text == original[format]


def test_unresolved_exports_require_explicit_ack(client):
    project = baseline(client, create(client))
    result = client.post(f'/api/v1/projects/{project["id"]}/exports', headers={"If-Match": str(project["revision"])}, json={"acknowledge_unresolved": False, "input_hash": project["input_hash"]})
    assert result.status_code == 409
    result = mutate(client, project, "post", "/exports", {"acknowledge_unresolved": True, "input_hash": project["input_hash"]})
    assert result["export"]["status"] == "draft_with_gaps"


def test_duplicates_and_exact_count_are_narrow_facts(client):
    project = baseline(client, create(client), [{"kind": "count", "types": ["text"], "comparison": "exact", "value": 2, "distinct_bytes": True}])
    project = upload(client, project)
    project = upload(client, project, name="copy.txt")
    project = decision(client, project)
    assert project["checks"][0]["status"] == "fail"
    assert project["checks"][0]["actual"] == 1
    result = client.post(f'/api/v1/projects/{project["id"]}/exports', headers={"If-Match": str(project["revision"])}, json={"acknowledge_unresolved": False, "input_hash": project["input_hash"]})
    assert result.status_code == 409  # Human satisfaction cannot erase failed count.


def test_upload_rejected_atomically_and_blocked_visible(client):
    project = create(client)
    project = upload(client, project, b"<html>not a png</html>", "logo.png")
    assert project["files"][0]["inspection"] == "blocked"
    result = client.post(f'/api/v1/projects/{project["id"]}/files', files=[("files[]", ("small.txt", b"ok")), ("files[]", ("large.txt", b"x" * (10 * 1024 * 1024 + 1)))], headers={"If-Match": str(project["revision"])})
    assert result.status_code == 413
    assert len(fresh(client, project)["files"]) == 1
    assert len(list(client.app.state.store.files.iterdir())) == 1


def test_jobs_use_actual_adapter_calls_and_preserve_decisions(client):
    project = create(client)
    project = mutate(client, project, "put", "/brief", {"text": "Supply final delivery guide."})
    result = mutate(client, project, "post", "/jobs/extract", {})
    assert wait_job(client, project, result["job"]["id"])["state"] == "succeeded"
    project = fresh(client, project)
    assert project["baseline"]["requirements"][0]["quote"] == project["brief"]["text"]
    ids = [r["id"] for r in project["baseline"]["requirements"]]
    project = mutate(client, project, "post", "/baseline/approve", {"baseline_hash": project["baseline"]["hash"], "reviewed_requirement_ids": ids})
    result = mutate(client, project, "post", "/jobs/match", {})
    assert wait_job(client, project, result["job"]["id"])["state"] == "succeeded"
    assert fresh(client, project)["proposals"][0]["candidates"] == []


def test_late_job_cannot_resurrect_deleted_project(tmp_path):
    gate = threading.Event()
    class SlowModel(FakeModel):
        def extract(self, brief, *, deadline=None):
            gate.wait(2)
            return super().extract(brief)
    app = create_app(tmp_path, SlowModel())
    with TestClient(app, base_url="http://127.0.0.1:8877") as client:
        client.headers.update({"X-Handoff-Token": client.get("/api/v1/bootstrap").json()["data"]["token"], "Origin": "http://127.0.0.1:8877"})
        project = mutate(client, create(client), "put", "/brief", {"text": "Supply guide."})
        mutate(client, project, "post", "/jobs/extract", {})
        for _ in range(100):
            project = fresh(client, project)
            if project["jobs"][0]["state"] == "running": break
            time.sleep(.01)
        assert client.delete(f'/api/v1/projects/{project["id"]}', headers={"If-Match": str(project["revision"])}).status_code == 200
        gate.set()
        time.sleep(.1)
        assert client.get("/api/v1/projects").json()["data"] == []


def test_restart_marks_jobs_interrupted_and_keeps_saved_state(tmp_path):
    store = Store(tmp_path)
    project = store.create("Preserved", 10)
    def update(current, db):
        current["jobs"].append({"id": "job", "state": "running", "stage": "generating"})
    store.mutate(project["id"], project["revision"], update)
    restored = Store(tmp_path).get(project["id"])
    assert restored["name"] == "Preserved"
    assert restored["jobs"][0]["state"] == "interrupted"


def test_export_html_escapes_user_text(client):
    project = baseline(client, create(client))
    project = decision(client, project, client_note='<script>alert("x")</script>')
    result = mutate(client, project, "post", "/exports", {"acknowledge_unresolved": False, "input_hash": project["input_hash"]})
    html = client.get(f'/api/v1/projects/{project["id"]}/exports/{result["export"]["id"]}/html').text
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


@pytest.mark.parametrize("operation,terminal", [("cancel", "cancelled"), ("edit_baseline", "superseded"), ("edit_brief", "superseded")])
def test_cancel_or_input_changes_discard_late_output(tmp_path, operation, terminal):
    gate, started = threading.Event(), threading.Event()
    class SlowModel(FakeModel):
        def extract(self, brief, *, deadline=None):
            started.set()
            gate.wait(2)
            return super().extract(brief, deadline=deadline)
    app = create_app(tmp_path, SlowModel())
    with TestClient(app, base_url="http://127.0.0.1:8877") as client:
        client.headers.update({"X-Handoff-Token": client.get("/api/v1/bootstrap").json()["data"]["token"], "Origin": "http://127.0.0.1:8877"})
        project = mutate(client, create(client), "put", "/brief", {"text": "Original clause."})
        result = mutate(client, project, "post", "/jobs/extract", {})
        assert started.wait(1)
        project = fresh(client, project)
        if operation == "cancel":
            project = mutate(client, project, "post", f'/jobs/{result["job"]["id"]}/cancel', {})
        elif operation == "edit_brief":
            project = mutate(client, project, "put", "/brief", {"text": "New clause."})
        else:
            project = mutate(client, project, "put", "/baseline", {"requirements": [{"id": "human", "title": "Keep human edit", "origin": "human_added", "human_note": "Human addition", "checks": [{"kind": "manual", "instruction": "Review"}]}]})
        gate.set()
        assert wait_job(client, project, result["job"]["id"])["state"] == terminal
        current = fresh(client, project)
        if operation == "edit_baseline":
            assert current["baseline"]["requirements"][0]["title"] == "Keep human edit"
        else:
            assert current["baseline"]["requirements"] == []


def test_json_budget_rejects_large_private_input_before_parse(client):
    result = client.post("/api/v1/projects", content=json.dumps({"name": "SECRET" * 50000}), headers={"Content-Type": "application/json"})
    assert result.status_code == 413
    assert "SECRET" not in result.text


def test_replacement_changes_hash_without_growing_packet(client):
    project = baseline(client, create(client))
    project = upload(client, project)
    project = decision(client, project)
    original_hash, original_id = project["input_hash"], project["files"][0]["id"]
    result = client.post(f'/api/v1/projects/{project["id"]}/files/{original_id}/replacement', files={"file": ("guide.txt", b"Revised guide.")}, headers={"If-Match": str(project["revision"])})
    assert result.status_code == 201, result.text
    updated = result.json()["data"]
    assert len(updated["files"]) == 1
    assert updated["files"][0]["id"] != original_id
    assert updated["input_hash"] != original_hash
    assert updated["decisions"][0]["review_state"] == "stale"
    assert len(list(client.app.state.store.files.iterdir())) == 1


def test_failed_model_evidence_never_enters_project(tmp_path):
    class InvalidModel(FakeModel):
        def extract(self, brief, *, deadline=None):
            result = super().extract(brief)
            result["requirements"][0]["quote"] = "Fabricated quote"
            return result
    app = create_app(tmp_path, InvalidModel())
    with TestClient(app, base_url="http://127.0.0.1:8877") as client:
        client.headers.update({"X-Handoff-Token": client.get("/api/v1/bootstrap").json()["data"]["token"], "Origin": "http://127.0.0.1:8877"})
        project = mutate(client, create(client), "put", "/brief", {"text": "Actual clause."})
        result = mutate(client, project, "post", "/jobs/extract", {})
        job = wait_job(client, project, result["job"]["id"])
        assert job["state"] == "failed"
        assert job["error_code"] == "invalid_source_quote"
        assert fresh(client, project)["baseline"]["requirements"] == []


def test_typed_image_checks_only_consider_applicable_selected_assets(client):
    from io import BytesIO
    from PIL import Image
    buffer = BytesIO()
    Image.new("RGBA", (8, 8), (50, 60, 70, 0)).save(buffer, format="PNG")
    project = baseline(client, create(client), [{"kind": "presence", "types": ["png"]}, {"kind": "presence", "types": ["text"]}, {"kind": "png_nonopaque_pixels"}, {"kind": "image_dimensions", "width_px": 8, "height_px": 8}])
    project = upload(client, project, buffer.getvalue(), "logo.png")
    project = upload(client, project)
    project = decision(client, project)
    assert [check["status"] for check in project["checks"]] == ["pass"] * 4


def test_stale_input_hash_rejected_after_file_change(client):
    project = baseline(client, create(client))
    old_hash = project["input_hash"]
    project = upload(client, project)
    result = client.put(f'/api/v1/projects/{project["id"]}/decisions/r1', headers={"If-Match": str(project["revision"])}, json={"file_ids": [project["files"][0]["id"]], "review_state": "confirmed", "human_disposition": "satisfied", "input_hash": old_hash})
    assert result.status_code == 409


def test_all_export_formats_retain_safe_numeric_evidence(client):
    project = baseline(client, create(client), [{"kind": "count", "types": ["text"], "comparison": "exact", "value": 2, "distinct_bytes": False}])
    project = upload(client, project)
    project = decision(client, project, "needs_work")
    result = mutate(client, project, "post", "/exports", {"acknowledge_unresolved": True, "input_hash": project["input_hash"]})
    for format in ("md", "html"):
        exported = client.get(f'/api/v1/projects/{project["id"]}/exports/{result["export"]["id"]}/{format}').text
        assert "expected: 2" in exported
        assert "observed: 1" in exported


def test_visual_preview_requires_token_current_inspected_image(client):
    from io import BytesIO
    from PIL import Image
    data = BytesIO()
    Image.new("RGB", (8, 8), (45, 60, 70)).save(data, format="PNG")
    project = upload(client, create(client), data.getvalue(), "logo.png")
    file = project["files"][0]
    path = f'/api/v1/projects/{project["id"]}/files/{file["id"]}/preview'
    assert client.get(path, headers={"X-Handoff-Token": "invalid"}).status_code == 403
    preview = client.get(path)
    assert preview.status_code == 200
    assert preview.content == data.getvalue()
    assert preview.headers["content-type"] == "image/png"
    assert preview.headers["cache-control"] == "no-store"
    assert preview.headers["x-content-type-options"] == "nosniff"
    project = upload(client, project, b"<script>not executable</script>", "notes.txt")
    text_id = project["files"][-1]["id"]
    assert client.get(f'/api/v1/projects/{project["id"]}/files/{text_id}/preview').status_code == 415
    project = upload(client, project, b"fake png", "broken.png")
    blocked_id = project["files"][-1]["id"]
    assert client.get(f'/api/v1/projects/{project["id"]}/files/{blocked_id}/preview').status_code == 415
    stored = client.app.state.store.get(project["id"])["files"][0]
    (client.app.state.store.files / stored["_path"]).write_bytes(b"tampered")
    assert client.get(path).status_code == 415
    assert fresh(client, project)["files"][0]["inspection"] == "blocked"


def test_handoff_preview_has_no_private_fields_or_mutation(client):
    project = baseline(client, create(client))
    project = decision(client, project)
    preview = client.get(f'/api/v1/projects/{project["id"]}/handoff-preview')
    assert preview.status_code == 200
    assert "SECRET PRIVATE NOTE" not in preview.text
    assert "Supply final delivery guide." not in preview.text
    assert preview.json()["data"]["id"] is None
    current = fresh(client, project)
    assert current["revision"] == project["revision"]
    assert current["exports"] == []


def test_forged_unicode_spans_rejected_and_valid_history_private(client):
    project = create(client)
    text = "🐦 café intro. Provide a logo ✨."
    project = mutate(client, project, "put", "/brief", {"text": text})
    quote = "Provide a logo ✨."
    row = {"id": "quoted", "title": "Logo", "origin": "model_suggested", "quote": quote, "source_id": project["brief"]["id"],
           "source_span": {"source_unit_id": "forged", "source_text_sha256": "0" * 64, "start_cp": 0, "end_cp": 1, "quote": "x"},
           "checks": [{"kind": "manual", "instruction": "Review logo."}]}
    rejected = client.put(f'/api/v1/projects/{project["id"]}/baseline', headers={"If-Match": str(project["revision"])}, json={"requirements": [row]})
    assert rejected.status_code == 422
    row.pop("source_span")  # A unique legacy quote can be resolved on the server.
    project = mutate(client, project, "put", "/baseline", {"requirements": [row]})
    span = project["baseline"]["requirements"][0]["source_span"]
    assert span["start_cp"] == text.index(quote)
    assert text[span["start_cp"]:span["end_cp"]] == quote
    assert span["source_unit_id"] == project["brief"]["id"]
    assert span["source_text_sha256"] == project["brief"]["sha256"]
    project = mutate(client, project, "put", "/brief", {"text": "Changed brief."})
    stored = client.app.state.store.get(project["id"])
    assert stored["baseline_history"][-1]["source"]["text"] == text
    assert stored["baseline_history"][-1]["baseline"]["requirements"][0]["source_span"] == span
    assert "baseline_history" not in project


def test_audit_history_is_bounded_and_cancelled_late_result_no_revision_bump(client):
    project = create(client)
    for index in range(23):
        project = mutate(client, project, "put", "/brief", {"text": f"Brief {index}"})
    stored = client.app.state.store.get(project["id"])
    assert len(stored["baseline_history"]) == 20
    revision = stored["revision"]
    updated = client.app.state.store.mutate(project["id"], revision, lambda project, db: None)
    assert updated["revision"] == revision


def test_streamed_json_budget_returns_413_without_echo(client):
    result = client.post("/api/v1/projects", content=iter([b'{"name":"', b'PRIVATE' * 50000, b'"}']), headers={"Content-Type": "application/json"})
    assert result.status_code == 413
    assert "PRIVATE" not in result.text


@pytest.mark.parametrize("quote", [None, "Invented passage"])
def test_api_rejects_model_text_mapping_without_exact_evidence(tmp_path, quote):
    class BadMatchModel(FakeModel):
        def match(self, brief, requirements, files, *, deadline=None):
            candidate = {"file_id": files[0]["id"], "reason": "Semantic mapping"}
            if quote is not None:
                candidate["quote"] = quote
            return {"proposals": [{"requirement_id": "r1", "candidates": [candidate], "coverage": "test"}], "model": {"test_double": True}}
    app = create_app(tmp_path, BadMatchModel())
    with TestClient(app, base_url="http://127.0.0.1:8877") as client:
        client.headers.update({"X-Handoff-Token": client.get("/api/v1/bootstrap").json()["data"]["token"], "Origin": "http://127.0.0.1:8877"})
        project = upload(client, baseline(client, create(client)))
        started = mutate(client, project, "post", "/jobs/match", {})
        job = wait_job(client, project, started["job"]["id"])
        assert job["state"] == "failed"
        assert job["error_code"] == "invalid_model_evidence"
        assert fresh(client, project)["proposals"] == []


def test_private_audit_history_requires_token_and_preserves_source(client):
    project = baseline(client, create(client))
    project = mutate(client, project, "put", "/brief", {"text": "New source."})
    path = f'/api/v1/projects/{project["id"]}/audit-history'
    assert client.get(path, headers={"X-Handoff-Token": "invalid"}).status_code == 403
    result = client.get(path)
    assert result.status_code == 200
    data = result.json()["data"]
    assert data["private"] is True
    assert data["baseline_history"][-1]["source"]["text"] == "Supply final delivery guide."
    assert "baseline_history" not in fresh(client, project)


def test_parser_queue_wait_obeys_absolute_batch_deadline(tmp_path):
    from handoffready.api import PARSER_LOCK, inspect_bounded
    started = time.monotonic()
    PARSER_LOCK.acquire()
    try:
        result = inspect_bounded(tmp_path / "not-read.txt", "not-read.txt", started + .02)
    finally:
        PARSER_LOCK.release()
    assert result["inspection"] == "blocked"
    assert "queue" in result["error"].lower()
    assert time.monotonic() - started < .2


def test_filename_display_drops_paths_and_directional_controls():
    from handoffready.api import clean_name
    assert clean_name("../../logo\u202egnp.txt") == "logognp.txt"
    assert clean_name("folder\\guide.txt") == "guide.txt"
    assert clean_name("\x00\r\n") == "Unnamed file"


def test_large_unicode_worker_output_does_not_deadlock_or_clip(client):
    text = "🐦" * 19000
    project = upload(client, create(client), text.encode(), "unicode.txt")
    assert project["files"][0]["inspection"] == "inspected"
    assert project["files"][0]["text"] == text


def test_actual_parser_worker_respects_expired_execution_budget(tmp_path):
    from handoffready.api import inspect_bounded
    path = tmp_path / "guide.txt"
    path.write_text("Delivery guide")
    started = time.monotonic()
    result = inspect_bounded(path, "guide.txt", started + .001)
    assert result["inspection"] == "blocked"
    assert "time limit" in result["error"]
    assert time.monotonic() - started < 1


@pytest.mark.parametrize("operation", ["upload", "replacement", "rename", "remove"])
def test_packet_changes_archive_private_proposals_before_invalidation(client, monkeypatch, operation):
    def good_test_match(self, brief, requirements, files, *, deadline=None):
        return {"proposals": [{"requirement_id": "r1", "candidates": [{"file_id": files[0]["id"], "reason": "SECRET_PRIVATE_ASSOCIATION", "quote": files[0]["text"]}], "coverage": "Explicit test double"}], "model": {"test_double": True}}
    monkeypatch.setattr(FakeModel, "match", good_test_match)
    project = upload(client, baseline(client, create(client)))
    started = mutate(client, project, "post", "/jobs/match", {})
    assert wait_job(client, project, started["job"]["id"])["state"] == "succeeded"
    project = fresh(client, project)
    old_proposals, old_hash = project["proposals"], project["input_hash"]
    file_id = project["files"][0]["id"]
    if operation == "upload":
        project = upload(client, project, b"New data", "extra.txt")
    elif operation == "replacement":
        result = client.post(f'/api/v1/projects/{project["id"]}/files/{file_id}/replacement', files={"file": ("new.txt", b"Replacement")}, headers={"If-Match": str(project["revision"])})
        assert result.status_code == 201
        project = result.json()["data"]
    elif operation == "rename":
        project = mutate(client, project, "patch", f"/files/{file_id}", {"display_name": "changed.txt"})
    else:
        project = mutate(client, project, "delete", f"/files/{file_id}")
    assert project["proposals"] == []
    assert "proposal_history" not in project
    stored = client.app.state.store.get(project["id"])
    assert stored["proposal_history"][-1]["proposals"] == old_proposals
    assert stored["proposal_history"][-1]["input_hash"] == old_hash
    exported = mutate(client, project, "post", "/exports", {"acknowledge_unresolved": True, "input_hash": project["input_hash"]})
    result = client.get(f'/api/v1/projects/{project["id"]}/exports/{exported["export"]["id"]}/json')
    assert "SECRET_PRIVATE_ASSOCIATION" not in result.text
    assert "A delivery guide." not in result.text


def test_unchanged_source_and_checklist_preserve_confirmed_reviews(client):
    project = decision(client, upload(client, baseline(client, create(client))))
    original_revision = project["revision"]
    original_hash = project["input_hash"]
    project = mutate(client, project, "put", "/brief", {"text": project["brief"]["text"], "source_label": project["brief"]["label"]})
    project = mutate(client, project, "put", "/baseline", {"requirements": project["baseline"]["requirements"]})
    assert project["revision"] == original_revision
    assert project["input_hash"] == original_hash
    assert project["baseline"]["state"] == "approved"
    assert project["decisions"][0]["review_state"] == "confirmed"
    changed = mutate(client, project, "put", "/brief", {"text": "A genuinely new obligation."})
    assert changed["baseline"]["state"] == "draft"
    assert changed["decisions"][0]["review_state"] == "stale"


@pytest.mark.parametrize("revision_value", ["²", "9" * 5000, "-1"])
def test_invalid_revision_headers_fail_as_validation(client, revision_value):
    project = create(client)
    result = client.put(f'/api/v1/projects/{project["id"]}/brief', headers={"If-Match": revision_value.encode("latin-1")}, json={"text": "A brief"})
    assert result.status_code == 422
    assert result.json()["error"]["code"] == "invalid_revision"


def test_runtime_original_damage_cannot_generate_a_current_pass_export(client):
    project = decision(client, upload(client, baseline(client, create(client), [{"kind": "presence", "types": ["text"]}])))
    assert project["checks"][0]["status"] == "pass"
    file = client.app.state.store.get(project["id"])["files"][0]
    (client.app.state.store.files / file["_path"]).unlink()
    stale = client.post(f'/api/v1/projects/{project["id"]}/exports', headers={"If-Match": str(project["revision"])}, json={"input_hash": project["input_hash"], "acknowledge_unresolved": True})
    assert stale.status_code == 409
    current = fresh(client, project)
    assert current["files"][0]["inspection"] == "blocked"
    assert current["decisions"][0]["review_state"] == "stale"
    assert current["checks"][0]["status"] == "unknown"
    preview = client.get(f'/api/v1/projects/{project["id"]}/handoff-preview').json()["data"]
    assert preview["status"] == "draft_with_gaps"
    assert not preview["requirements"][0]["files"]
