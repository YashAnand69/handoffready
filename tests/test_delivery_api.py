"""Real local API policy with synthetic packets; no provider or human-trial claims."""
import pytest
from fastapi.testclient import TestClient

from handoffready.api import create_app
from handoffready.delivery import DeliveryBinding
from handoffready.delivery_api import DeliveryConfig
from handoffready.store import StoreError
from test_api import baseline, create, decision, mutate, upload


CONFIG = {"binding_id": "room_demo", "server": "http://127.0.0.1:63056", "room": "room_synthetic", "token": "synthetic-delivery-token-for-tests"}


@pytest.fixture
def desk(tmp_path):
    app = create_app(tmp_path, delivery_config=CONFIG)
    with TestClient(app, base_url="http://127.0.0.1:8877") as client:
        client.headers.update({"X-Handoff-Token": app.state.token, "Origin": "http://127.0.0.1:8877"})
        yield client


def bound_job(desk, project):
    result = desk.post("/api/v1/delivery/jobs", json={"project_id": project["id"], "operation_key": "create_1"})
    assert result.status_code == 201, result.text
    return result.json()["data"]["result"]["job_id"]


def scoped(desk):
    desk.headers.pop("X-Handoff-Token")
    desk.headers.update({"X-Delivery-Token": CONFIG["token"], "X-Delivery-Binding": CONFIG["binding_id"]})


def test_scoped_credential_only_grants_two_read_tools(desk):
    project = create(desk)
    job = bound_job(desk, project)
    scoped(desk)
    assert desk.get(f"/api/v1/delivery/jobs/{job}/status").status_code == 200
    for method, path, body in [
        ("GET", "/api/v1/projects", None),
        ("GET", f'/api/v1/projects/{project["id"]}', None),
        ("POST", "/api/v1/delivery/jobs", {"project_id": project["id"], "operation_key": "other"}),
        ("PUT", f'/api/v1/projects/{project["id"]}/decisions/r1', {}),
        ("POST", f'/api/v1/projects/{project["id"]}/exports', {}),
        ("DELETE", f"/api/v1/delivery/jobs/{job}/status", None),
    ]:
        assert desk.request(method, path, json=body).status_code == 403
    assert desk.get(f"/api/v1/delivery/jobs/{job}/status", headers={"X-Delivery-Binding": "different_room"}).status_code == 403
    assert desk.get(f"/api/v1/delivery/jobs/{job}/status", headers={"X-Delivery-Token": "bad"}).status_code == 403


def test_safe_status_excludes_private_prose_and_foreign_binding(desk):
    project = baseline(desk, create(desk))
    project = upload(desk, project)
    project = decision(desk, project, note="PRIVATE HUMAN NOTE", client_note="CLIENT USAGE NOTE")
    job = bound_job(desk, project)
    service = desk.app.state.delivery_service
    foreign_project = create(desk)
    foreign = service.create_job(DeliveryBinding(CONFIG["server"], "other_room"), foreign_project["id"], "other")
    scoped(desk)
    result = desk.get(f"/api/v1/delivery/jobs/{job}/status")
    assert result.status_code == 200
    data = result.json()["data"]
    assert data["source_revision"] == project["revision"]
    assert data["input_hash"] == project["input_hash"]
    for private in ["PRIVATE HUMAN NOTE", "CLIENT USAGE NOTE", "Supply final delivery guide.", "A delivery guide.", "_path", "decision_history"]:
        assert private not in result.text
    assert desk.get(f'/api/v1/delivery/jobs/{foreign["result"]["job_id"]}/status').status_code == 403


def test_preview_is_provisional_current_and_does_not_save_review(desk):
    project = baseline(desk, create(desk), [{"kind": "literal_text", "needle": "delivery"}])
    project = upload(desk, project)
    job = bound_job(desk, project)
    before = desk.app.state.store.get(project["id"])
    scoped(desk)
    body = {"requirement_id": "r1", "file_ids": [project["files"][0]["id"]], "input_hash": project["input_hash"], "expected_revision": project["revision"]}
    result = desk.post(f"/api/v1/delivery/jobs/{job}/preview", json=body)
    assert result.status_code == 200, result.text
    preview = result.json()["data"]
    assert preview["preview"] and not preview["assessment_saved"]
    assert preview["approval"] == "local_human_review_required"
    assert preview["checks"][0]["status"] == "pass"
    assert desk.app.state.store.get(project["id"]) == before
    for invalid in [dict(body, expected_revision=project["revision"] - 1), dict(body, input_hash="f" * 64)]:
        assert desk.post(f"/api/v1/delivery/jobs/{job}/preview", json=invalid).status_code == 409
    for invalid in [dict(body, expected_revision=True), dict(body, room="other_room"), dict(body, file_ids=["missing"]), dict(body, file_ids=body["file_ids"] * 2)]:
        assert desk.post(f"/api/v1/delivery/jobs/{job}/preview", json=invalid).status_code == 422
    assert desk.post(f"/api/v1/delivery/jobs/{job}/preview", json=body, headers={"Origin": "https://untrusted.example"}).status_code == 403


def test_preview_reconciles_missing_original_before_currency_check(desk):
    project = baseline(desk, create(desk), [{"kind": "literal_text", "needle": "delivery"}])
    project = upload(desk, project)
    job = bound_job(desk, project)
    store = desk.app.state.store
    original = store.get(project["id"])["files"][0]
    (store.files / original["_path"]).unlink()
    scoped(desk)
    body = {"requirement_id": "r1", "file_ids": [original["id"]], "input_hash": project["input_hash"], "expected_revision": project["revision"]}
    assert desk.post(f"/api/v1/delivery/jobs/{job}/preview", json=body).status_code == 409
    data = desk.get(f"/api/v1/delivery/jobs/{job}/status").json()["data"]
    assert data["source_revision"] > project["revision"]
    assert data["input_hash"] != project["input_hash"]
    assert data["files"][0]["inspection"] == "blocked"


def test_no_delivery_schema_or_routes_without_opt_in(tmp_path):
    app = create_app(tmp_path)
    with app.state.store.connection() as db:
        assert db.execute("SELECT name FROM sqlite_master WHERE name='delivery_schema'").fetchone() is None
    with TestClient(app, base_url="http://127.0.0.1:8877") as client:
        result = client.get("/api/v1/delivery/jobs/example/status", headers={"X-Delivery-Token": CONFIG["token"], "X-Delivery-Binding": CONFIG["binding_id"]})
        assert result.status_code == 403


def test_status_distinguishes_packet_review_correction_and_stale(desk):
    project = create(desk)
    job = bound_job(desk, project)
    status = lambda: desk.get(f"/api/v1/delivery/jobs/{job}/status").json()["data"]
    assert status()["state"] == "scope_review"
    project = baseline(desk, project)
    assert status()["state"] == "awaiting_packet"
    project = upload(desk, project)
    assert status()["state"] == "human_review"
    project = decision(desk, project, disposition="needs_work")
    assert status()["state"] == "needs_correction"
    assert status()["next_actor"] == "teammate"
    project = decision(desk, project)
    assert status()["state"] == "ready_to_prepare_record"
    assert status()["approval"] == "local_human_review_required"
    mutate(desk, project, "patch", f'/files/{project["files"][0]["id"]}', {"display_name": "renamed.txt"})
    assert status()["state"] == "review_required"


def test_status_respects_explicit_scope_exception_without_hiding_facts(desk):
    project = baseline(desk, create(desk), [{"kind": "count", "types": ["text"], "comparison": "exact", "value": 2, "distinct_bytes": False}])
    project = upload(desk, project)
    project = mutate(desk, project, "put", "/decisions/r1", {"file_ids": [project["files"][0]["id"]], "review_state": "confirmed", "human_disposition": "not_applicable", "internal_decision_note": "Explicit synthetic scope exception", "client_exception_note": "Only one guide is required for this agreed example.", "input_hash": project["input_hash"]})
    job = bound_job(desk, project)
    scoped(desk)
    status = desk.get(f"/api/v1/delivery/jobs/{job}/status").json()["data"]
    assert status["state"] == "ready_to_prepare_record"
    assert status["review_summary"]["status"] == "reviewed_with_exceptions"
    assert status["review_summary"]["failed_check_count"] == 1


def test_literal_source_expectation_not_copied_to_scoped_tools(desk):
    project = baseline(desk, create(desk), [{"kind": "literal_text", "needle": "PRIVATE SOURCE EXPECTATION"}])
    project = upload(desk, project)
    job = bound_job(desk, project)
    scoped(desk)
    assert "PRIVATE SOURCE EXPECTATION" not in desk.get(f"/api/v1/delivery/jobs/{job}/status").text
    result = desk.post(f"/api/v1/delivery/jobs/{job}/preview", json={"requirement_id": "r1", "file_ids": [project["files"][0]["id"]], "input_hash": project["input_hash"], "expected_revision": project["revision"]})
    assert result.status_code == 200
    assert "PRIVATE SOURCE EXPECTATION" not in result.text
    assert result.json()["data"]["checks"][0]["status"] == "fail"


def test_private_manual_instruction_not_copied_to_scoped_tools(desk):
    project = baseline(desk, create(desk), [{"kind": "manual", "instruction": "PRIVATE MANUAL INSTRUCTION"}])
    project = upload(desk, project)
    job = bound_job(desk, project)
    scoped(desk)
    assert "PRIVATE MANUAL INSTRUCTION" not in desk.get(f"/api/v1/delivery/jobs/{job}/status").text
    result = desk.post(f"/api/v1/delivery/jobs/{job}/preview", json={"requirement_id": "r1", "file_ids": [project["files"][0]["id"]], "input_hash": project["input_hash"], "expected_revision": project["revision"]})
    assert result.status_code == 200
    assert "PRIVATE MANUAL INSTRUCTION" not in result.text
    assert result.json()["data"]["checks"][0]["status"] == "unknown"


@pytest.mark.parametrize("config", [dict(CONFIG, token="short"), dict(CONFIG, binding_id="../other"), dict(CONFIG, arbitrary="input"), dict(CONFIG, server="https://user:password@example.com")])
def test_bad_configuration_refused_without_logging_credentials(tmp_path, config):
    with pytest.raises((ValueError, StoreError)) as error:
        create_app(tmp_path, delivery_config=config)
    assert CONFIG["token"] not in str(error.value)


def test_explicit_private_config_file_only(tmp_path):
    import json
    path = tmp_path / "delivery.json"
    path.write_text(json.dumps(CONFIG))
    path.chmod(0o600)
    assert DeliveryConfig.load_file(str(path)) == CONFIG
    assert CONFIG["token"] not in repr(DeliveryConfig.parse(CONFIG))
    path.chmod(0o644)
    with pytest.raises(ValueError):
        DeliveryConfig.load_file(str(path))
    path.chmod(0o600)
    link = tmp_path / "link.json"
    link.symlink_to(path)
    with pytest.raises(ValueError):
        DeliveryConfig.load_file(str(link))
    with pytest.raises(ValueError):
        DeliveryConfig.load_file("relative.json")
    path.write_text('{"token":"FIRST SECRET","token":"SECOND SECRET"}')
    with pytest.raises(ValueError) as error:
        DeliveryConfig.load_file(str(path))
    assert "SECRET" not in str(error.value)
