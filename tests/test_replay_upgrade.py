"""Static replay integrity tests use only the allowlisted synthetic capture.

These verify staging boundaries and literal artifacts, not model quality or
customer evidence. Copies live in temporary test directories.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("prepare_upgrade_replay", ROOT / "scripts/prepare_upgrade_replay.py")
replay = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(replay)


def digest(value):
    return hashlib.sha256(value).hexdigest()


@pytest.fixture
def captured(tmp_path):
    original = ROOT / "docs/replay"
    if not (original / "data.json").exists():
        pytest.fail("The approved synthetic replay capture is required for integrity tests")
    copied = tmp_path / "recorded"
    shutil.copytree(original, copied)
    return copied / "data.json"


def edit(data_path, update):
    data = json.loads(data_path.read_text())
    update(data)
    data_path.write_text(json.dumps(data, ensure_ascii=False))
    return data


def rehash(data_path, name):
    edit(data_path, lambda data: data["assets"].update({name: digest((data_path.parent / name).read_bytes())}))


def test_actual_allowlisted_recording_stages_with_exact_asset_bytes(captured, tmp_path):
    destination = tmp_path / "public-stage"
    result = replay.build(captured, destination)
    assert result["checkpoint_count"] == 5
    assert result["old_snapshot_unchanged"] is True
    data = json.loads(captured.read_text())
    assert (destination / "data.json").read_bytes() == captured.read_bytes()
    receipt = json.loads((destination / "replay-verification.json").read_text())
    for name in data["assets"]:
        assert (destination / name).read_bytes() == (captured.parent / name).read_bytes()
        assert receipt["file_sha256"][name] == data["assets"][name]
    assert "no browser inference" in receipt["disclosure"]


@pytest.mark.parametrize("where", ["top", "checkpoint", "snapshot", "source", "comparison"])
def test_unknown_manifest_fields_are_rejected(captured, where):
    def inject(data):
        container = {"top": data, "checkpoint": data["checkpoints"][0], "snapshot": data["snapshots"]["before"], "source": data["source"], "comparison": data["comparison"]}[where]
        container["extra_private_field"] = "not allowlisted"
    edit(captured, inject)
    with pytest.raises(ValueError, match="non-allowlisted"):
        replay.validate(captured)


def test_asset_path_traversal_is_rejected(captured):
    edit(captured, lambda data: data["assets"].update({"../private.json": "0" * 64}))
    with pytest.raises(ValueError, match="path/type"):
        replay.validate(captured)


def test_linked_record_asset_is_rejected_even_with_correct_hash(captured, tmp_path):
    path = captured.parent / "records/before.json"
    elsewhere = tmp_path / "outside-record.json"
    elsewhere.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(elsewhere)
    with pytest.raises(ValueError, match="linked or out-of-scope"):
        replay.validate(captured)


def test_linked_manifest_is_not_resolved_into_allowed_source(captured, tmp_path):
    linked = tmp_path / "manifest.json"
    linked.symlink_to(captured)
    with pytest.raises(ValueError, match="symbolic link"):
        replay.build(linked, tmp_path / "stage")


def test_asset_tampering_is_rejected(captured):
    with (captured.parent / "records/before.md").open("a") as output:
        output.write("\nChanged after capture.")
    with pytest.raises(ValueError, match="changed"):
        replay.validate(captured)


def test_descriptor_cannot_misrepresent_recorded_snapshot(captured):
    edit(captured, lambda data: data["snapshots"]["before"].update({"status": "reviewed"}))
    with pytest.raises(ValueError, match="descriptor differs"):
        replay.validate(captured)


def test_snapshot_digest_is_verified_independently_of_asset_hash(captured):
    path = captured.parent / "records/before.json"
    record = json.loads(path.read_text())
    record["project_name"] += " changed"
    path.write_text(json.dumps(record))
    rehash(captured, "records/before.json")
    with pytest.raises(ValueError, match="canonical projection"):
        replay.validate(captured)


def test_private_nested_fields_rejected_even_if_asset_digest_updated(captured):
    path = captured.parent / "records/before.json"
    record = json.loads(path.read_text())
    record["requirements"][0]["internal_decision_note"] = "private operator material"
    path.write_text(json.dumps(record))
    rehash(captured, "records/before.json")
    with pytest.raises(ValueError, match="Private/non-client"):
        replay.validate(captured)


def test_immutable_history_requires_exact_later_download(captured):
    path = captured.parent / "records/before-verified-again.json"
    path.write_bytes(path.read_bytes() + b"\n")
    rehash(captured, "records/before-verified-again.json")
    with pytest.raises(ValueError, match="Earlier snapshot bytes changed"):
        replay.validate(captured)


def test_immutable_history_claim_requires_evidence_file(captured):
    edit(captured, lambda data: data["comparison"].pop("unchanged_artifact"))
    with pytest.raises(ValueError, match="exact later-downloaded"):
        replay.validate(captured)


def test_source_candidate_hash_cannot_be_misreported(captured):
    def replace_hash(data):
        name = next(iter(data["source"]["module_sha256"]))
        data["source"]["module_sha256"][name] = "0" * 64
    edit(captured, replace_hash)
    with pytest.raises(ValueError, match="Source changed since"):
        replay.validate(captured)


def test_nonexistent_base_commit_is_rejected(captured):
    edit(captured, lambda data: data["source"].update({"base_commit": "0" * 40}))
    with pytest.raises(subprocess.CalledProcessError):
        replay.validate(captured)


@pytest.mark.parametrize("field,value", [("actor", "genuine customer trial"), ("sample_id", "actual private customer"), ("version", "future")])
def test_recording_disclosure_contract_is_enforced(captured, field, value):
    edit(captured, lambda data: data.update({field: value}))
    with pytest.raises(ValueError):
        replay.validate(captured)


def test_build_cannot_overwrite_recorded_source(captured):
    before = captured.read_bytes()
    with pytest.raises(ValueError, match="separate staging"):
        replay.build(captured, captured.parent)
    assert captured.read_bytes() == before


def test_build_refuses_stale_staging_assets(captured, tmp_path):
    stage = tmp_path / "stage"
    stage.mkdir()
    sentinel = stage / "old.json"
    sentinel.write_text("private or stale")
    with pytest.raises(ValueError, match="must be empty"):
        replay.build(captured, stage)
    assert sentinel.read_text() == "private or stale"


def test_recorded_finding_details_do_not_change_source(captured, tmp_path):
    data = json.loads(captured.read_text())
    before = copy.deepcopy(data)
    replay.build(captured, tmp_path / "stage")
    assert json.loads(captured.read_text()) == before
    assert any(finding["status"] == "fail" for checkpoint in before["checkpoints"] for finding in checkpoint["findings"])
    assert any(finding["status"] == "note" for checkpoint in before["checkpoints"] for finding in checkpoint["findings"])


def test_arbitrary_html_cannot_pass_by_copying_snapshot_identity(captured):
    path = captured.parent / "records/before.html"
    path.write_text(path.read_text() + "<script>fetch('/private')</script>")
    rehash(captured, "records/before.html")
    with pytest.raises(ValueError, match="Active/network HTML"):
        replay.validate(captured)


def test_build_cannot_stage_inside_its_capture_source(captured):
    with pytest.raises(ValueError, match="separate staging"):
        replay.build(captured, captured.parent / "public")


def test_historical_capture_provenance_is_preserved_without_replacing_changed_api_hash():
    recorded = ROOT / "docs/replay"
    historical_bytes = (recorded / "capture-provenance.json").read_bytes()
    assert digest(historical_bytes) == "fa796d2a0d8b8050f6c9f933c469cdbb4980dd43d23f3758b5f7f8013e630ef4"
    historical = json.loads(historical_bytes)
    current = json.loads((recorded / "data.json").read_text())
    api = "backend/handoffready/api.py"
    assert api in historical["source"]["module_sha256"]
    assert api not in current["source"]["module_sha256"]
    assert current["source"]["module_sha256"] == {
        name: value for name, value in historical["source"]["module_sha256"].items() if name != api
    }
    assert current["assets"] == historical["assets"]
    assert current["snapshots"] == historical["snapshots"]
    assert "compatibility fix" in current["checkpoints"][-1]["facts"][-1]
