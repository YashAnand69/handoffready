"""Coordination contracts using synthetic data; no model/provider is invoked."""

import json
import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest

from handoffready.delivery import DeliveryBinding, DeliveryService
from handoffready.store import Store, StoreError, canonical, input_hash


BINDING = DeliveryBinding("https://switch.example.com", "room-1", "thread-1")


@pytest.fixture
def setup(tmp_path):
    store = Store(tmp_path)
    project = store.create("Synthetic packet", 10)
    def baseline(value, db):
        value["brief"] = {"sha256": "a" * 64, "text": "PRIVATE BRIEF", "source_label": "PRIVATE SOURCE"}
        value["baseline"]["requirements"] = [{"id": "r1", "title": "Guide", "checks": [{"kind": "manual", "instruction": "Review guide"}], "human_note": "PRIVATE NOTE"}]
    project = store.mutate(project["id"], project["revision"], baseline)
    service = DeliveryService(store)
    job = service.create_job(BINDING, project["id"], "create")["result"]["job_id"]
    return store, project, service, job


def error(code):
    return pytest.raises(StoreError, match=".")


def proposal(service, job, project, key="blocker", **kwargs):
    return service.propose_blocker(job, BINDING, key, expected_revision=project["revision"], expected_hash=input_hash(project), requirement_id="r1", message="Please clarify this requirement.", **kwargs)


def test_additive_migration_preserves_legacy_bytes_and_reopens(setup):
    store, project, service, job = setup
    with store.connection() as db:
        db.execute("INSERT INTO exports VALUES (?,?,?,?,?)", ("e1", project["id"], '{"historic":true}', "historic md", "historic html"))
        before = db.execute("SELECT * FROM projects").fetchall(), db.execute("SELECT * FROM exports").fetchall()
    again = DeliveryService(store)
    with store.connection() as db:
        assert before == (db.execute("SELECT * FROM projects").fetchall(), db.execute("SELECT * FROM exports").fetchall())
        assert len(db.execute("SELECT * FROM delivery_schema").fetchall()) == 1
        assert len(db.execute("PRAGMA table_info(projects)").fetchall()) == 2
        assert len(db.execute("PRAGMA table_info(exports)").fetchall()) == 5
    assert again.get_job(job, BINDING)["project_id"] == project["id"]


def test_newer_schema_refused_without_modifying_version(setup):
    store, _, _, _ = setup
    with store.connection() as db:
        db.execute("UPDATE delivery_schema SET version=99")
    with error("delivery_schema_unsupported") as caught:
        DeliveryService(store)
    assert caught.value.code == "delivery_schema_unsupported"
    with store.connection() as db:
        assert db.execute("SELECT version FROM delivery_schema").fetchone()[0] == 99


def test_migration_failure_rolls_back_new_tables(tmp_path):
    store = Store(tmp_path)
    with store.connection() as db:
        db.execute("CREATE TABLE delivery_jobs (foreign_shape TEXT)")
    with pytest.raises(sqlite3.OperationalError):
        DeliveryService(store)
    with store.connection() as db:
        assert db.execute("SELECT 1 FROM sqlite_master WHERE name='delivery_schema'").fetchone() is None
        assert db.execute("PRAGMA table_info(delivery_jobs)").fetchone()[1] == "foreign_shape"


def test_binding_checked_before_operation_lookup_and_status(setup):
    _, project, service, job = setup
    proposal(service, job, project)
    for binding in (replace(BINDING, room="other"), replace(BINDING, server="https://other.example.com"), replace(BINDING, thread="other")):
        with error("delivery_binding_refused") as caught:
            service.propose_blocker(job, binding, "blocker", expected_revision=project["revision"], expected_hash=input_hash(project), requirement_id="r1", message="Please clarify this requirement.")
        assert caught.value.code == "delivery_binding_refused"
        with error("delivery_binding_refused"):
            service.status(job, binding)


def test_binding_cannot_be_reassigned_to_another_project(setup):
    store, _, service, _ = setup
    other = store.create("Other", 10)
    with error("delivery_binding_conflict") as caught:
        service.create_job(BINDING, other["id"], "different")
    assert caught.value.code == "delivery_binding_conflict"


def test_committed_retry_precedes_revision_check_and_preserves_review(setup):
    store, project, service, job = setup
    before = canonical(store.get(project["id"]))
    result = proposal(service, job, project)
    assert canonical(store.get(project["id"])) == before
    updated = store.mutate(project["id"], project["revision"], lambda value, db: value.update(name="Renamed"))
    assert proposal(service, job, project) == result
    with error("revision_conflict") as caught:
        proposal(service, job, project, "new")
    assert caught.value.code == "revision_conflict"
    with error("delivery_operation_conflict") as caught:
        service.propose_blocker(job, BINDING, "blocker", expected_revision=updated["revision"], expected_hash=input_hash(updated), requirement_id="r1", message="Different")
    assert caught.value.code == "delivery_operation_conflict"


def test_missing_requirement_or_current_hash_cannot_create_proposal(setup):
    _, project, service, job = setup
    with error("delivery_input_conflict") as caught:
        service.propose_blocker(job, BINDING, "bad", expected_revision=project["revision"], expected_hash="0" * 64, requirement_id="r1", message="Proposed")
    assert caught.value.code == "delivery_input_conflict"
    with error("delivery_requirement_missing") as caught:
        service.propose_blocker(job, BINDING, "absent", expected_revision=project["revision"], expected_hash=input_hash(project), requirement_id="absent", message="Proposed")
    assert caught.value.code == "delivery_requirement_missing"


def test_status_omits_private_content_and_marks_changed_proposal(setup):
    store, project, service, job = setup
    proposal(service, job, project)
    status = service.status(job, BINDING)
    assert "PRIVATE" not in json.dumps(status)
    assert "Please clarify" not in json.dumps(status)
    assert status["approval"] == "local_human_review_required"
    assert status["blockers"][0]["state"] == "proposed"
    store.mutate(project["id"], project["revision"], lambda value, db: value["baseline"].update(hash="changed"))
    assert service.status(job, BINDING)["blockers"][0]["state"] == "superseded"


def test_staged_bytes_survive_old_store_restart_and_retry(setup):
    store, project, service, job = setup
    args = dict(source_id="attachment-1", filename="guide.txt", content=b"Synthetic guide")
    result = service.stage_receipt(job, BINDING, "stage", **args)
    assert service.stage_receipt(job, BINDING, "stage", **args) == result
    second = service.stage_receipt(job, BINDING, "stage-again", **args)
    assert second["result"]["receipt_id"] == result["result"]["receipt_id"]
    assert list(store.files.iterdir()) == []
    restarted = DeliveryService(Store(store.directory))
    path = restarted.staging / job / result["result"]["receipt_id"]
    assert path.read_bytes() == args["content"]
    assert restarted.status(job, BINDING)["staged_receipts"] == 1
    with error("delivery_source_conflict") as caught:
        restarted.stage_receipt(job, BINDING, "changed", **{**args, "content": b"Changed bytes"})
    assert caught.value.code == "delivery_source_conflict"
    assert store.get(project["id"])["files"] == []


@pytest.mark.parametrize("filename", ["../guide.txt", "a/b.txt", "a\\b.txt", ".."])
def test_staging_rejects_paths(setup, filename):
    _, _, service, job = setup
    with error("delivery_invalid_input"):
        service.stage_receipt(job, BINDING, "bad", source_id="source", filename=filename, content=b"x")


def test_resource_bounds_and_failed_write_leave_no_extra_rows(setup):
    store, project, _, job = setup
    service = DeliveryService(store, limits={"jobs": 1, "receipts_per_job": 1, "staging_bytes": 3, "file_bytes": 3, "operations_per_job": 3, "blockers_per_job": 1})
    other = store.create("Other", 10)
    with error("delivery_job_limit"):
        service.create_job(replace(BINDING, room="second"), other["id"], "second")
    service.stage_receipt(job, BINDING, "one", source_id="one", filename="a.txt", content=b"abc")
    with error("delivery_staging_limit"):
        service.stage_receipt(job, BINDING, "two", source_id="two", filename="b.txt", content=b"b")
    with error("delivery_file_limit"):
        service.stage_receipt(job, BINDING, "big", source_id="big", filename="c.txt", content=b"abcd")
    proposal(service, job, project)
    with error("delivery_operation_limit") as caught:
        proposal(service, job, project, "too-many")
    assert caught.value.code == "delivery_operation_limit"
    with store.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM delivery_operations").fetchone()[0] == 3
        assert db.execute("SELECT COUNT(*) FROM delivery_receipts").fetchone()[0] == 1


def test_oversized_result_rolls_back_bytes_and_receipt(setup):
    store, _, _, job = setup
    service = DeliveryService(store, limits={"result_bytes": 10})
    with error("delivery_result_limit") as caught:
        service.stage_receipt(job, BINDING, "too-large", source_id="source", filename="a.txt", content=b"abc")
    assert caught.value.code == "delivery_result_limit"
    assert list((service.staging / job).iterdir()) == []
    with store.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM delivery_receipts").fetchone()[0] == 0


@pytest.mark.parametrize("change", ["remove", "tamper", "symlink"])
def test_committed_receipt_retry_reports_current_availability(setup, tmp_path, change):
    _, _, service, job = setup
    args = dict(source_id="one", filename="guide.txt", content=b"abc")
    first = service.stage_receipt(job, BINDING, "stage", **args)
    path = service.staging / job / first["result"]["receipt_id"]
    assert first["availability"] == "available"
    if change == "tamper":
        path.write_bytes(b"xyz")
    else:
        path.unlink()
        if change == "symlink":
            other = tmp_path / "outside"
            other.write_bytes(b"abc")
            path.symlink_to(other)
    replay = service.stage_receipt(job, BINDING, "stage", **args)
    assert replay["result"] == first["result"]
    assert replay["operation_id"] == first["operation_id"]
    assert replay["availability"] != "available"
    assert replay["retry_advice"] == "operator_action"
    assert service.status(job, BINDING)["unavailable_receipts"] == 1


def test_original_tampering_is_reconciled_before_new_proposal(setup):
    store, project, service, job = setup
    original = store.files / "original"
    original.write_bytes(b"abc")
    row = {"id": "file-1", "name": "guide.txt", "_path": "original", "size": 3, "sha256": hashlib.sha256(b"abc").hexdigest(), "type": "text", "inspection": "inspected", "metadata": {"characters": 3}, "text": "abc", "error": None}
    project = store.mutate(project["id"], project["revision"], lambda value, db: value["files"].append(row))
    first = proposal(service, job, project)
    original.write_bytes(b"xyz")
    assert proposal(service, job, project) == first
    with error("revision_conflict") as caught:
        proposal(service, job, project, "new-after-tampering")
    assert caught.value.code == "revision_conflict"
    current = store.get(project["id"])
    assert current["files"][0]["inspection"] == "blocked"
    assert current["revision"] > project["revision"]
    assert service.status(job, BINDING)["blockers"][0]["state"] == "superseded"


def test_concurrent_duplicate_staging_has_one_receipt(setup):
    store, _, service, job = setup
    def stage(_):
        return service.stage_receipt(job, BINDING, "same", source_id="one", filename="guide.txt", content=b"abc")
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(stage, range(8)))
    assert all(result == results[0] for result in results)
    with store.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM delivery_receipts").fetchone()[0] == 1
    assert len(list((service.staging / job).iterdir())) == 1


def test_disk_failure_does_not_commit_receipt_or_operation(setup, monkeypatch):
    store, _, service, job = setup
    def fail(_):
        raise OSError("synthetic disk failure")
    monkeypatch.setattr("handoffready.delivery.os.fsync", fail)
    with pytest.raises(OSError, match="synthetic disk failure"):
        service.stage_receipt(job, BINDING, "disk", source_id="one", filename="guide.txt", content=b"abc")
    with store.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM delivery_receipts").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM delivery_operations WHERE operation_key='disk'").fetchone()[0] == 0
    assert list((service.staging / job).iterdir()) == []
