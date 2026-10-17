"""Failed replacements preserve the usable packet; no real inference is used."""
import pytest
from fastapi.testclient import TestClient

from handoffready.api import create_app
from test_api import FakeModel, baseline, create, decision, fresh, mutate, upload, wait_job


class QuotedTestModel(FakeModel):
    def match(self, brief, requirements, files, *, deadline=None):
        return {"proposals": [{"requirement_id": "r1", "candidates": [{
            "file_id": files[0]["id"], "reason": "Declared test double",
            "quote": files[0]["text"],
        }], "coverage": "Declared test double"}], "model": {"test_double": True}}


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path, QuotedTestModel())
    with TestClient(app, base_url="http://127.0.0.1:8877") as connection:
        connection.headers.update({"X-Handoff-Token": app.state.token, "Origin": "http://127.0.0.1:8877"})
        yield connection


def reviewed_packet(client):
    project = decision(client, upload(client, baseline(client, create(client))))
    started = mutate(client, project, "POST", "/jobs/match", {})
    assert wait_job(client, project, started["job"]["id"])["state"] == "succeeded"
    return fresh(client, project)


def replace(client, project, name, data):
    return client.post(
        f'/api/v1/projects/{project["id"]}/files/{project["files"][0]["id"]}/replacement',
        files={"file": (name, data)}, headers={"If-Match": str(project["revision"])},
    )


@pytest.mark.parametrize("name,data", [
    ("guide.exe", b"UNTRUSTED_PRIVATE_CANDIDATE"),
    ("guide.png", b"\x89PNG\r\n\x1a\nUNTRUSTED_PRIVATE_CANDIDATE"),
    ("guide.txt", b"   \n"),
])
def test_blocked_replacement_keeps_original_and_complete_review_state(client, name, data):
    project = reviewed_packet(client)
    exported = mutate(client, project, "POST", "/exports", {"acknowledge_unresolved": True, "input_hash": project["input_hash"]})
    project = fresh(client, project)
    export_url = f'/api/v1/projects/{project["id"]}/exports/{exported["export"]["id"]}/json'
    snapshot = client.get(export_url).content
    store = client.app.state.store
    before = store.get(project["id"])
    assert before["proposals"] and before["decisions"][0]["review_state"] == "confirmed"
    originals = {path.name: path.read_bytes() for path in store.files.iterdir()}

    result = replace(client, project, name, data)

    assert result.status_code == 422, result.text
    assert result.json()["error"]["code"] == "replacement_not_inspected"
    assert "kept" in result.json()["error"]["message"]
    assert "UNTRUSTED_PRIVATE_CANDIDATE" not in result.text
    assert store.get(project["id"]) == before
    assert {path.name: path.read_bytes() for path in store.files.iterdir()} == originals
    assert client.get(export_url).content == snapshot


def test_inspection_timeout_replacement_is_recoverable_without_losing_original(client, monkeypatch):
    project = reviewed_packet(client)
    store = client.app.state.store
    before = store.get(project["id"])
    originals = {path.name: path.read_bytes() for path in store.files.iterdir()}
    monkeypatch.setattr("handoffready.api.inspect_bounded", lambda *args: {
        "type": "unknown", "inspection": "blocked", "metadata": {}, "text": "",
        "error": "File inspection exceeded its time limit.",
    })
    result = replace(client, project, "guide.txt", b"Revised guide.")
    assert result.status_code == 422
    assert "time limit" in result.json()["error"]["message"]
    assert store.get(project["id"]) == before
    assert {path.name: path.read_bytes() for path in store.files.iterdir()} == originals


def test_valid_replacement_still_invalidates_reviews_and_retires_old_original(client):
    project = reviewed_packet(client)
    store = client.app.state.store
    original = store.get(project["id"])["files"][0]
    result = replace(client, project, "guide.txt", b"Revised guide.")
    assert result.status_code == 201, result.text
    updated = result.json()["data"]
    assert updated["revision"] == project["revision"] + 1
    assert updated["input_hash"] != project["input_hash"]
    assert updated["decisions"][0]["review_state"] == "stale"
    assert updated["proposals"] == []
    assert not (store.files / original["_path"]).exists()
    assert len(list(store.files.iterdir())) == 1
    assert store.get(project["id"])["proposal_history"][-1]["proposals"] == project["proposals"]


def test_new_blocked_upload_remains_visible_for_correction(client):
    project = upload(client, create(client), b"unsupported", "guide.exe")
    assert project["files"][0]["inspection"] == "blocked"
    assert len(list(client.app.state.store.files.iterdir())) == 1
