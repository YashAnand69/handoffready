"""Isolated review reproductions. No real model inference or installation downloads."""
import importlib.util
import hashlib
from pathlib import Path
import sys
import tarfile
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from handoffready.api import create_app
from handoffready.store import Store, input_hash


ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(f"final_review_{name}", ROOT / "scripts" / f"{name}.py")
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    return script


def test_default_setup_creates_key_needed_by_documented_launcher(tmp_path, monkeypatch):
    installer = load_script("prepare_model")
    runtime = tmp_path / ".runtime"
    runtime.mkdir()
    server = tmp_path / "llama-server"
    server.write_text("synthetic isolated installation artifact; never executed\n")
    archive = runtime / f"llama-{installer.RUNTIME_TAG}.tar.gz"
    with tarfile.open(archive, "w:gz") as bundle:
        bundle.add(server, arcname="bin/llama-server")
    monkeypatch.setattr(installer, "ROOT", tmp_path)
    monkeypatch.setattr(installer, "RUNTIME_SHA", installer.sha(archive))
    monkeypatch.setattr(installer.os, "uname", lambda: SimpleNamespace(machine="arm64", sysname="Darwin"))
    monkeypatch.setattr(installer, "download_ranges", lambda url, path, *args: path.write_bytes(b"synthetic weights; never loaded"))
    monkeypatch.setattr(installer, "MODEL_SHA", hashlib.sha256(b"synthetic weights; never loaded").hexdigest())
    monkeypatch.setattr(installer, "__name__", "final_review_install")
    monkeypatch.setattr(installer.__dict__["os"], "execv", lambda *args: pytest.fail("Unexpected process execution"))
    monkeypatch.setattr(sys, "argv", ["prepare_model.py"])
    installer.main()
    key = tmp_path / ".model/server.key"
    assert key.is_file(), "Successful default setup must leave the launcher credential ready"
    assert key.stat().st_mode & 0o777 == 0o600
    launcher = load_script("start")
    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    command = launcher.model_command()
    assert command[command.index("--api-key-file") + 1] == str(key)


def configured_client(app):
    client = TestClient(app, base_url="http://127.0.0.1:8877")
    client.headers.update({"X-Handoff-Token": client.get("/api/v1/bootstrap").json()["data"]["token"], "Origin": "http://127.0.0.1:8877"})
    return client


def request_change(client, project, method, suffix, payload):
    result = client.request(method, f'/api/v1/projects/{project["id"]}{suffix}', json=payload, headers={"If-Match": str(project["revision"])})
    assert result.status_code in {200, 201}, result.text
    return result.json()["data"]


@pytest.mark.parametrize("damage", ["missing", "same_size_tamper"])
def test_damaged_original_after_restart_invalidates_delivery_evidence(tmp_path, damage):
    app = create_app(tmp_path)
    with configured_client(app) as client:
        project = client.post("/api/v1/projects", json={"name": "Isolated integrity reproduction"}).json()["data"]
        project = request_change(client, project, "PUT", "/baseline", {"requirements": [{"id": "r", "title": "Text guide", "origin": "human_added", "human_note": "Explicit human requirement", "checks": [{"kind": "presence", "types": ["text"]}]}]})
        project = request_change(client, project, "POST", "/baseline/approve", {"baseline_hash": project["baseline"]["hash"], "reviewed_requirement_ids": ["r"]})
        result = client.post(f'/api/v1/projects/{project["id"]}/files', files={"file": ("guide.txt", b"Delivered guide")}, headers={"If-Match": str(project["revision"])})
        assert result.status_code == 201
        project = result.json()["data"]
        project = request_change(client, project, "PUT", "/decisions/r", {"file_ids": [project["files"][0]["id"]], "review_state": "confirmed", "human_disposition": "satisfied", "input_hash": project["input_hash"]})
        assert project["checks"][0]["status"] == "pass"
        registered = app.state.store.get(project["id"])["files"][0]
        original = app.state.store.files / registered["_path"]
        if damage == "missing":
            original.unlink()
        else:
            original.write_bytes(b"x" * registered["size"])
    restored = create_app(tmp_path)
    with configured_client(restored) as client:
        current = client.get(f'/api/v1/projects/{project["id"]}').json()["data"]
        assert current["files"][0]["sha256"] == registered["sha256"]
        assert current["files"][0]["metadata"] == {}
        assert current["files"][0]["text"] == ""
        assert current["decisions"][0]["review_state"] == "stale"
        assert current["checks"][0]["status"] != "pass", "Missing bytes must not continue passing presence"
        exported = client.post(f'/api/v1/projects/{project["id"]}/exports', json={"acknowledge_unresolved": False, "input_hash": current["input_hash"]}, headers={"If-Match": str(current["revision"])})
        assert exported.status_code == 409, "Missing originals must require visible export gaps"


def test_runtime_identity_reconciliation_archives_evidence_once(tmp_path):
    """Direct storage fixture exercises provenance preservation, without model output."""
    store = Store(tmp_path)
    project = store.create("Isolated runtime identity", 10)
    original = store.files / "original"
    original.write_bytes(b"abc")
    expected_sha = hashlib.sha256(b"abc").hexdigest()
    def register(current, db):
        current["files"] = [{"id": "f", "_path": "original", "name": "guide.txt", "size": 3, "sha256": expected_sha, "type": "text", "inspection": "inspected", "metadata": {"characters": 3}, "text": "abc", "error": None}]
        current["proposals"] = [{"id": "synthetic-storage-record", "requirement_id": "r", "candidates": [{"file_id": "f", "quote": "abc"}]}]
        current["decisions"] = [{"requirement_id": "r", "review_state": "confirmed", "input_hash": input_hash(current), "file_ids": ["f"], "human_disposition": "satisfied"}]
    project = store.mutate(project["id"], project["revision"], register)
    old_hash, old_proposals = input_hash(project), project["proposals"]
    assert store.reconcile_originals(project["id"])["revision"] == project["revision"]
    original.write_bytes(b"xyz")
    reconciled = store.reconcile_originals(project["id"])
    assert reconciled["revision"] == project["revision"] + 1
    assert reconciled["files"][0]["sha256"] == expected_sha
    assert reconciled["files"][0]["inspection"] == "blocked"
    assert reconciled["proposals"] == []
    assert reconciled["proposal_history"][-1]["input_hash"] == old_hash
    assert reconciled["proposal_history"][-1]["proposals"] == old_proposals
    assert reconciled["decision_history"][-1]["review_state"] == "confirmed"
    assert reconciled["decisions"][0]["review_state"] == "stale"
    again = store.reconcile_originals(project["id"])
    assert again["revision"] == reconciled["revision"]
    assert len(again["proposal_history"]) == 1
    original.write_bytes(b"abc")
    assert store.reconcile_originals(project["id"])["files"][0]["inspection"] == "blocked"
