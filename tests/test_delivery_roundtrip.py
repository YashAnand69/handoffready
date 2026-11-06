"""Actual stdio → HTTP → SQLite rehearsal, entirely synthetic and provider-free.

This is not a Switch room test or evidence of a real human assessment.
"""
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time

import httpx


ROOT = Path(__file__).resolve().parents[1]


def test_live_tool_rehearsal_correction_and_current_human_review(tmp_path):
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    origin = f"http://127.0.0.1:{port}"
    token = secrets.token_urlsafe(32)
    config = {"binding_id": "synthetic_roundtrip", "server": "https://synthetic.switch.invalid", "room": "test_only", "token": token}
    config_file = tmp_path / "private-config.json"
    config_file.write_text(json.dumps(config))
    config_file.chmod(0o600)
    environment = {**os.environ, "HANDOFFREADY_DATA": str(tmp_path / "data"), "HANDOFFREADY_PORT": str(port), "HANDOFFREADY_DELIVERY_CONFIG": str(config_file)}
    process = subprocess.Popen([sys.executable, str(ROOT / "scripts/run.py")], cwd=ROOT, env=environment, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        with httpx.Client(base_url=origin, trust_env=False, timeout=10) as client:
            deadline = time.monotonic() + 10
            while True:
                try:
                    bootstrap = client.get("/api/v1/bootstrap")
                    if bootstrap.status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                assert process.poll() is None, "Synthetic local server exited before readiness"
                assert time.monotonic() < deadline, "Synthetic local server did not become ready"
                time.sleep(.05)
            client.headers.update({"X-Handoff-Token": bootstrap.json()["data"]["token"], "Origin": origin})

            def request(method, path, body=None, **kwargs):
                result = client.request(method, "/api/v1" + path, json=body, **kwargs)
                assert result.status_code in {200, 201}, (result.status_code, result.text)
                return result.json()["data"]

            def mutate(project, method, suffix, body):
                return request(method, f'/projects/{project["id"]}' + suffix, body, headers={"If-Match": str(project["revision"])})

            def add_file(project, name, content):
                result = client.post(f'/api/v1/projects/{project["id"]}/files', files=[("files[]", (name, content))], headers={"If-Match": str(project["revision"])})
                assert result.status_code == 201, result.text
                return result.json()["data"]

            project = request("POST", "/projects", {"name": "Synthetic tool roundtrip"})
            project = mutate(project, "PUT", "/brief", {"text": "Supply two text guides.", "source_label": "Synthetic brief"})
            requirement = {"id": "guides", "title": "Two guides", "origin": "human_added", "human_note": "Synthetic test fixture, not human trial", "checks": [{"kind": "count", "types": ["text"], "comparison": "exact", "value": 2, "distinct_bytes": False}]}
            project = mutate(project, "PUT", "/baseline", {"requirements": [requirement]})
            project = mutate(project, "POST", "/baseline/approve", {"baseline_hash": project["baseline"]["hash"], "reviewed_requirement_ids": ["guides"]})
            project = add_file(project, "first.txt", b"Synthetic first guide")
            created = request("POST", "/delivery/jobs", {"project_id": project["id"], "operation_key": "start"})
            job_id = created["result"]["job_id"]

            def tool(name, arguments):
                messages = [
                    {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "synthetic-rehearsal", "version": "1"}}},
                    {"jsonrpc": "2.0", "method": "notifications/initialized"},
                    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                    {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": name, "arguments": arguments}},
                ]
                run = subprocess.run([sys.executable, str(ROOT / "scripts/delivery_tools.py")], input="".join(json.dumps(message) + "\n" for message in messages), text=True, capture_output=True, timeout=20, env={**os.environ, "HANDOFFREADY_DELIVERY_ORIGIN": origin, "HANDOFFREADY_DELIVERY_BINDING": config["binding_id"], "HANDOFFREADY_DELIVERY_TOKEN": token})
                assert run.returncode == 0
                assert not run.stderr
                assert token not in run.stdout
                replies = [json.loads(line) for line in run.stdout.splitlines()]
                assert {entry["name"] for entry in replies[1]["result"]["tools"]} == {"delivery_status", "delivery_check_preview"}
                return json.loads(replies[2]["result"]["content"][0]["text"])

            status = tool("delivery_status", {"job_id": job_id})
            assert status["source_revision"] == project["revision"]
            arguments = {"job_id": job_id, "requirement_id": "guides", "file_ids": [row["id"] for row in project["files"]], "expected_revision": project["revision"], "input_hash": project["input_hash"]}
            before = request("GET", f'/projects/{project["id"]}')
            first = tool("delivery_check_preview", arguments)
            assert first["checks"][0]["status"] == "fail"
            assert first["checks"][0]["actual"] == 1
            assert request("GET", f'/projects/{project["id"]}') == before
            project = add_file(project, "second.txt", b"Synthetic corrected guide")
            stale = tool("delivery_check_preview", arguments)
            assert stale["error"]["code"] == "revision_conflict"
            assert stale["retry_advice"] == "refresh"
            arguments.update(file_ids=[row["id"] for row in project["files"]], expected_revision=project["revision"], input_hash=project["input_hash"])
            corrected = tool("delivery_check_preview", arguments)
            assert corrected["checks"][0]["status"] == "pass"
            assert not corrected["assessment_saved"]
            assert request("GET", f'/projects/{project["id"]}')["decisions"] == []
            # A passing preliminary check cannot produce a reviewed record.
            refused = client.post(f'/api/v1/projects/{project["id"]}/exports', json={"acknowledge_unresolved": False, "input_hash": project["input_hash"]}, headers={"If-Match": str(project["revision"])})
            assert refused.status_code == 409
            project = mutate(project, "PUT", "/decisions/guides", {"file_ids": arguments["file_ids"], "review_state": "confirmed", "human_disposition": "satisfied", "input_hash": project["input_hash"], "internal_decision_note": "SYNTHETIC PRIVATE TEST NOTE"})
            assert tool("delivery_status", {"job_id": job_id})["state"] == "ready_to_prepare_record"
            exported = mutate(project, "POST", "/exports", {"acknowledge_unresolved": False, "input_hash": project["input_hash"]})
            assert exported["export"]["status"] == "reviewed"
            assert request("POST", "/delivery/jobs", {"project_id": project["id"], "operation_key": "start"}) == created
            artifact = client.get(f'/api/v1/projects/{project["id"]}/exports/{exported["export"]["id"]}/md')
            assert artifact.status_code == 200
            assert "SYNTHETIC PRIVATE TEST NOTE" not in artifact.text
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
