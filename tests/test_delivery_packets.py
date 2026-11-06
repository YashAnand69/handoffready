"""Whole-packet confirmation: actual SQLite/files, synthetic bytes and bounded parser."""
import sqlite3
import os
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest

from handoffready.api import inspect_bounded
from handoffready.delivery import DeliveryBinding, DeliveryService
from handoffready.store import Store, StoreError, input_hash

BINDING = DeliveryBinding("http://127.0.0.1:63054", "synthetic-room")

@pytest.fixture
def packet(tmp_path):
    store = Store(tmp_path)
    project = store.create("Synthetic complete packet", 10)
    service = DeliveryService(store)
    job = service.create_job(BINDING, project["id"], "create")["result"]["job_id"]
    return store, service, job, project


def stage(service, job, name="guide.txt", content=b"Read this synthetic guide.", source="source1"):
    return service.stage_receipt(job, BINDING, source, source_id=source, filename=name, content=content)["result"]["receipt_id"]


def preview(service, job, project, receipts):
    return service.preview_packet(job, BINDING, receipt_ids=receipts, expected_revision=project["revision"], expected_hash=input_hash(project))


def confirm(service, job, project, receipts, key="confirm", inspector=inspect_bounded, manifest=None):
    manifest = manifest or preview(service, job, project, receipts)["manifest_hash"]
    return service.confirm_packet(job, BINDING, key, receipt_ids=receipts, expected_revision=project["revision"], expected_hash=input_hash(project), manifest_hash=manifest, inspect_file=inspector)


def test_whole_packet_commit_retry_and_restart(packet):
    store, service, job, project = packet
    receipt = stage(service, job)
    assert service.list_receipts(job, BINDING)["pending_count"] == 1
    before = preview(service, job, project, [receipt])
    assert before["changes"] == {"added": ["guide.txt"], "replaced": [], "removed": [], "unchanged": []}
    result = confirm(service, job, project, [receipt], manifest=before["manifest_hash"])
    current = store.get(project["id"])
    assert current["revision"] == project["revision"] + 1 == result["source_revision"]
    assert result["input_hash"] == input_hash(current)
    assert len(current["files"]) == 1
    assert (store.files / current["files"][0]["_path"]).read_bytes() == b"Read this synthetic guide."
    restarted = DeliveryService(Store(store.directory))
    assert confirm(restarted, job, project, [receipt], manifest=before["manifest_hash"]) == result
    assert restarted.list_receipts(job, BINDING)["pending_count"] == 0
    assert restarted.context_for_project(project["id"], BINDING)["last_packet"]["packet_id"] == result["result"]["packet_id"]


def test_unchanged_packet_retains_review_ids_and_revision(packet):
    store, service, job, project = packet
    receipt = stage(service, job)
    confirm(service, job, project, [receipt])
    current = store.get(project["id"])
    def assessed(value, db):
        value["decisions"] = [{"review_state": "confirmed", "requirement_id": "r", "human_disposition": "satisfied", "input_hash": input_hash(value)}]
    current = store.mutate(current["id"], current["revision"], assessed)
    another = stage(service, job, source="source2")
    result = confirm(service, job, current, [another], key="unchanged")
    assert result["result"]["changed"] is False
    assert store.get(current["id"]) == current
    assert service.list_receipts(job, BINDING)["pending_count"] == 0


def test_correction_replaces_whole_packet_stales_review_and_keeps_exports(packet):
    store, service, job, project = packet
    first = stage(service, job)
    extra = stage(service, job, "other.txt", b"Extra file", "source-extra")
    confirm(service, job, project, [first, extra])
    current = store.get(project["id"])
    def assessed(value, db):
        value["decisions"] = [{"review_state": "confirmed", "requirement_id": "r", "human_disposition": "satisfied", "input_hash": input_hash(value)}]
        db.execute("INSERT INTO exports VALUES (?,?,?,?,?)", ("historic",value["id"],"frozen-json","frozen-md","frozen-html"))
    current = store.mutate(current["id"], current["revision"], assessed)
    corrected = stage(service, job, content=b"Corrected guide.", source="source2")
    view = preview(service, job, current, [corrected])
    assert view["changes"]["replaced"] == ["guide.txt"] and view["changes"]["removed"] == ["other.txt"]
    result = confirm(service, job, current, [corrected], key="revision2")
    updated = store.get(current["id"])
    assert updated["decisions"][0]["review_state"] == "stale"
    assert len(updated["decision_history"]) == 1
    assert len(updated["files"]) == 1
    assert result["input_hash"] != input_hash(current)
    with store.connection() as db:
        assert db.execute("SELECT json,md,html FROM exports").fetchone() == ("frozen-json","frozen-md","frozen-html")


def test_later_receipt_and_revision_invalidate_preview(packet):
    store, service, job, project = packet
    first = stage(service, job)
    before = preview(service, job, project, [first])
    stage(service, job, "ignored.txt", b"Unselected", "second")
    with pytest.raises(StoreError) as error:
        confirm(service, job, project, [first], manifest=before["manifest_hash"])
    assert error.value.code == "delivery_manifest_changed"
    assert store.get(project["id"]) == project
    refreshed = preview(service, job, project, [first])
    assert len(refreshed["excluded_receipts"]) == 1
    assert refreshed["excluded_receipts"][0]["filename"] == "ignored.txt"
    assert refreshed["excluded_receipts"][0]["source_id"] == "second"
    assert refreshed["excluded_receipt_ids"] == [refreshed["excluded_receipts"][0]["receipt_id"]]
    current = store.mutate(project["id"],project["revision"],lambda value,db:value.update(name="Changed name"))
    with pytest.raises(StoreError) as error:
        confirm(service, job, project, [first], manifest=before["manifest_hash"])
    assert error.value.code == "revision_conflict"
    assert store.get(project["id"]) == current


@pytest.mark.parametrize("names", [("Guide.txt","guide.TXT"),("caf\u00e9.txt","cafe\u0301.txt")])
def test_normalized_filename_collision_refused(packet,names):
    store, service, job, project = packet
    ids=[stage(service,job,name,b"Synthetic","source"+str(i)) for i,name in enumerate(names)]
    with pytest.raises(StoreError) as error: preview(service,job,project,ids)
    assert error.value.code == "delivery_filename_collision"
    assert not store.get(project["id"])["files"]


@pytest.mark.parametrize("selected", [[],["missing"],["duplicate","duplicate"]])
def test_partial_or_invalid_manifest_cannot_commit(packet,selected):
    store, service, job, project = packet
    with pytest.raises(StoreError): confirm(service,job,project,selected)
    assert store.get(project["id"]) == project


def test_selected_tampering_between_preview_and_copy_keeps_packet(packet,monkeypatch):
    store, service, job, project = packet
    receipt=stage(service,job)
    actual=service._copy_receipt
    def tamper(job_id,row,destination):
        (service.staging/job_id/row["receipt_id"]).write_bytes(b"Tampered")
        return actual(job_id,row,destination)
    monkeypatch.setattr(service,"_copy_receipt",tamper)
    with pytest.raises(StoreError): confirm(service,job,project,[receipt])
    assert store.get(project["id"]) == project and not list(store.files.iterdir())


def test_one_parser_failure_rolls_back_entire_packet(packet):
    store,service,job,project=packet
    ids=[stage(service,job),stage(service,job,"bad.zip",b"unsupported", "bad")]
    with pytest.raises(StoreError) as error: confirm(service,job,project,ids)
    assert error.value.code == "delivery_inspection_failed"
    assert store.get(project["id"]) == project and not list(store.files.iterdir())
    with store.connection() as db: assert not db.execute("SELECT * FROM delivery_packets").fetchall()


def test_same_operation_key_conflicting_payload_and_concurrent_retry(packet):
    store,service,job,project=packet
    receipt=stage(service,job)
    view=preview(service,job,project,[receipt])
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:confirm(service,job,project,[receipt],manifest=view["manifest_hash"]),range(2)))
    assert results[0] == results[1]
    with pytest.raises(StoreError) as error:
        confirm(service,job,project,[receipt],manifest="0"*64)
    assert error.value.code == "delivery_operation_conflict"
    with store.connection() as db: assert db.execute("SELECT count(*) FROM delivery_packets").fetchone()[0] == 1


def test_foreign_receipt_cannot_be_used(packet):
    store,service,job,project=packet
    other=store.create("Other",10)
    binding=DeliveryBinding(BINDING.server,"other")
    other_job=service.create_job(binding,other["id"],"create")["result"]["job_id"]
    receipt=service.stage_receipt(other_job,binding,"source",source_id="source",filename="guide.txt",content=b"Private other packet")["result"]["receipt_id"]
    with pytest.raises(StoreError) as error: preview(service,job,project,[receipt])
    assert error.value.code == "delivery_receipt_missing"


def test_v1_migration_preserves_old_records(packet):
    store,_,_,project=packet
    with store.connection() as db:
        db.execute("DROP TABLE delivery_packets");db.execute("UPDATE delivery_schema SET version=1")
        before=db.execute("SELECT * FROM projects").fetchall()
    DeliveryService(store)
    with store.connection() as db:
        assert db.execute("SELECT * FROM projects").fetchall() == before
        assert db.execute("SELECT version FROM delivery_schema").fetchone()[0] == 4
        assert len(db.execute("PRAGMA table_info(projects)").fetchall()) == 2


def test_damaged_original_is_not_retained_as_unchanged(packet):
    store,service,job,project=packet
    receipt=stage(service,job)
    confirm(service,job,project,[receipt])
    current=store.get(project["id"])
    (store.files/current["files"][0]["_path"]).write_bytes(b"Wrong original")
    with pytest.raises(StoreError) as error: preview(service,job,current,[receipt])
    assert error.value.code == "revision_conflict"
    reconciled=store.get(project["id"])
    assert reconciled["files"][0]["inspection"] == "blocked"
    view=preview(service,job,reconciled,[receipt])
    assert view["changes"]["replaced"] == ["guide.txt"]
    confirm(service,job,reconciled,[receipt],key="repair")
    assert store.get(project["id"])["files"][0]["inspection"] == "inspected"


def test_historical_staging_damage_does_not_damage_committed_packet(packet):
    store,service,job,project=packet
    def checklist(value,db): value["baseline"].update(state="approved",requirements=[{"id":"r","title":"Guide","checks":[{"kind":"manual","instruction":"Review"}]}])
    project=store.mutate(project["id"],project["revision"],checklist)
    receipt=stage(service,job)
    confirm(service,job,project,[receipt])
    (service.staging/job/receipt).unlink()
    status=service.status(job,BINDING)
    assert status["unavailable_receipts"] == 0 and status["pending_receipts"] == 0
    assert status["files"][0]["inspection"] == "inspected"
    stage(service,job,"correction.txt",b"Pending correction","later")
    assert service.status(job,BINDING)["state"] == "awaiting_packet_confirmation"


def test_known_disk_failure_keeps_old_packet_and_no_receipt(packet,monkeypatch):
    from pathlib import Path
    store,service,job,project=packet
    first=stage(service,job);confirm(service,job,project,[first])
    current=store.get(project["id"])
    new=stage(service,job,content=b"Correction",source="later")
    original=Path.open
    def fail(path,*args,**kwargs):
        if path.parent == store.files and args and args[0] == "xb": raise OSError("Synthetic disk full")
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,"open",fail)
    with pytest.raises(OSError):confirm(service,job,current,[new],key="fail")
    assert store.get(project["id"]) == current
    assert (store.files/current["files"][0]["_path"]).exists()
    with store.connection() as db:assert db.execute("SELECT count(*) FROM delivery_packets").fetchone()[0] == 1


def test_commit_acknowledgement_loss_reconciles_without_deleting_registered_bytes(packet,monkeypatch):
    from contextlib import contextmanager
    store,service,job,project=packet
    receipt=stage(service,job)
    original=store.connection
    lost=False
    @contextmanager
    def connection():
        nonlocal lost
        should_fail=False
        with original() as db:
            before=db.execute("SELECT count(*) FROM delivery_packets").fetchone()[0]
            yield db
            should_fail=db.execute("SELECT count(*) FROM delivery_packets").fetchone()[0] > before and not lost
        if should_fail:
            lost=True
            raise sqlite3.OperationalError("Synthetic lost acknowledgement after commit")
    monkeypatch.setattr(store,"connection",connection)
    result=confirm(service,job,project,[receipt])
    assert lost and result["state"] == "succeeded"
    current=store.get(project["id"])
    assert (store.files/current["files"][0]["_path"]).exists()
    assert len(current["files"]) == 1


def test_unconfirmed_packet_budget_and_newer_schema_refused_without_modification(packet,monkeypatch):
    from handoffready.policy import LIMITS
    store,service,job,project=packet
    receipt=stage(service,job)
    monkeypatch.setitem(LIMITS,"packet_bytes",2)
    with pytest.raises(StoreError) as error:preview(service,job,project,[receipt])
    assert error.value.code == "delivery_packet_limit"
    assert store.get(project["id"]) == project
    with store.connection() as db:db.execute("UPDATE delivery_schema SET version=5")
    with pytest.raises(StoreError):DeliveryService(store)
    with store.connection() as db:assert db.execute("SELECT version FROM delivery_schema").fetchone()[0] == 5


def test_legacy_duplicate_filename_is_removed_as_changed_not_false_noop(packet):
    store,service,job,project=packet
    receipt=stage(service,job);confirm(service,job,project,[receipt])
    current=store.get(project["id"])
    def legacy_duplicate(value,db):
        duplicate=dict(value["files"][0]);duplicate["id"]="legacy-duplicate"
        value["files"].append(duplicate)
    current=store.mutate(current["id"],current["revision"],legacy_duplicate)
    view=preview(service,job,current,[receipt])
    assert view["review_will_be_stale"] and view["changes"]["removed"] == ["guide.txt"]
    result=confirm(service,job,current,[receipt],key="deduplicate")
    assert result["result"]["changed"] and len(store.get(project["id"])["files"]) == 1


def test_unknown_commit_keeps_old_and_new_bytes_until_reconciliation(packet,monkeypatch):
    from contextlib import contextmanager
    store,service,job,project=packet
    first=stage(service,job);confirm(service,job,project,[first])
    current=store.get(project["id"]);old_path=store.files/current["files"][0]["_path"]
    corrected=stage(service,job,content=b"New correction",source="second")
    manifest=preview(service,job,current,[corrected])["manifest_hash"]
    original=store.connection
    failed=False
    @contextmanager
    def connection():
        nonlocal failed
        if failed:raise sqlite3.OperationalError("Synthetic reconciliation unavailable")
        should_fail=False
        with original() as db:
            before=db.execute("SELECT count(*) FROM delivery_packets").fetchone()[0]
            yield db
            should_fail=db.execute("SELECT count(*) FROM delivery_packets").fetchone()[0] > before
        if should_fail:
            failed=True
            raise sqlite3.OperationalError("Synthetic acknowledgement loss")
    monkeypatch.setattr(store,"connection",connection)
    with pytest.raises(StoreError) as error:confirm(service,job,current,[corrected],key="unknown",manifest=manifest)
    assert error.value.code == "delivery_commit_unknown"
    assert old_path.exists() and len(list(store.files.iterdir())) == 2
    monkeypatch.setattr(store,"connection",original)
    replay=confirm(service,job,current,[corrected],key="unknown",manifest=manifest)
    latest=store.get(project["id"])
    assert replay["source_revision"] == latest["revision"]
    assert (store.files/latest["files"][0]["_path"]).exists()


def test_staging_commit_error_never_deletes_registered_receipt(packet,monkeypatch):
    from contextlib import contextmanager
    store,service,job,project=packet
    original=store.connection
    lost=False
    @contextmanager
    def connection():
        nonlocal lost
        should_fail=False
        with original() as db:
            before=db.execute("SELECT count(*) FROM delivery_receipts").fetchone()[0]
            yield db
            should_fail=db.execute("SELECT count(*) FROM delivery_receipts").fetchone()[0] > before and not lost
        if should_fail:
            lost=True
            raise sqlite3.OperationalError("Synthetic receipt acknowledgement loss")
    monkeypatch.setattr(store,"connection",connection)
    with pytest.raises(sqlite3.OperationalError):stage(service,job)
    retry=stage(service,job)
    assert (service.staging/job/retry).read_bytes() == b"Read this synthetic guide."
    assert service.list_receipts(job,BINDING)["pending_count"] == 1


def test_process_crash_during_preparation_recovers_only_scratch(packet):
    store,service,job,project=packet
    first=stage(service,job)
    confirm(service,job,project,[first])
    current=store.get(project["id"])
    original=store.files/current["files"][0]["_path"]
    with store.connection() as db:
        db.execute("INSERT INTO exports VALUES (?,?,?,?,?)",("kept",project["id"],"json","markdown","html"))
    correction=stage(service,job,content=b"Synthetic corrected guide",source="crash-correction")
    program='''
import os,sys
from handoffready.store import Store,input_hash
from handoffready.delivery import DeliveryBinding,DeliveryService
store=Store(sys.argv[1]);service=DeliveryService(store)
binding=DeliveryBinding("http://127.0.0.1:63054","synthetic-room")
project=store.get(sys.argv[3])
view=service.preview_packet(sys.argv[2],binding,receipt_ids=[sys.argv[4]],expected_revision=project["revision"],expected_hash=input_hash(project))
def crash(path,name,deadline):
    assert path.read_bytes() == b"Synthetic corrected guide"
    os._exit(87)
service.confirm_packet(sys.argv[2],binding,"crashed",receipt_ids=[sys.argv[4]],expected_revision=project["revision"],expected_hash=input_hash(project),manifest_hash=view["manifest_hash"],inspect_file=crash)
'''
    environment={**os.environ,"PYTHONPATH":str(Path(__file__).resolve().parents[1]/"backend")}
    child=subprocess.run([sys.executable,"-c",program,str(store.directory),job,project["id"],correction],env=environment,capture_output=True,timeout=15)
    assert child.returncode == 87,child.stderr.decode()
    assert len(list(service.root.glob("packet-*"))) == 1
    restarted_store=Store(store.directory)
    restarted=DeliveryService(restarted_store)
    assert not list(restarted.root.glob("packet-*"))
    assert restarted_store.get(project["id"]) == current
    assert original.read_bytes() == b"Read this synthetic guide."
    assert (restarted.staging/job/correction).read_bytes() == b"Synthetic corrected guide"
    with restarted_store.connection() as db:
        assert db.execute("SELECT json,md,html FROM exports WHERE id='kept'").fetchone() == ("json","markdown","html")
        assert db.execute("SELECT count(*) FROM delivery_operations WHERE operation_key='crashed'").fetchone()[0] == 0


def test_scratch_recovery_refuses_unknown_or_linked_contents(packet,tmp_path):
    store,service,job,project=packet
    unrelated=tmp_path/"operator-notes.txt"
    unrelated.write_text("Keep operator files")
    scratch=service.root/"packet-12345678"
    scratch.mkdir(mode=0o700)
    (scratch/("a"*32)).symlink_to(unrelated)
    with pytest.raises(StoreError) as error:DeliveryService(store)
    assert error.value.code == "delivery_storage_failure"
    assert unrelated.read_text() == "Keep operator files"
    assert (scratch/("a"*32)).is_symlink()
    assert store.get(project["id"]) == project
