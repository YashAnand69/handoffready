"""Delivery records keep facts, exclusions, private evidence and history separate."""
import copy
import json

import pytest

from handoffready.exports import projection, render
from handoffready.store import StoreError, canonical, input_hash
from handoffready.summary import build_summary


def packet(count=1, disposition="satisfied", public_exception=""):
    project = {
        "name": "Studio delivery", "revision": 12,
        "brief": {"sha256": "PRIVATE_BRIEF_HASH", "text": "PRIVATE_RAW_BRIEF"},
        "baseline": {"state": "approved", "hash": "baseline", "requirements": []},
        "files": [{"id": "f1", "name": "guide.txt", "type": "text", "size": 15, "sha256": "a" * 64,
                   "inspection": "inspected", "metadata": {}, "text": "delivery guide", "_path": "PRIVATE_PATH"},
                  {"id": "f2", "name": "unselected-private.txt", "type": "text", "size": 12, "sha256": "b" * 64,
                   "inspection": "inspected", "metadata": {}, "text": "PRIVATE_FILE_TEXT", "_path": "PRIVATE_PATH"}],
        "decisions": [], "proposals": [{"reason": "PRIVATE_MODEL_REASON"}],
    }
    for index in range(count):
        project["baseline"]["requirements"].append({"id": f"r{index}", "title": f"Guide {index}", "origin": "human_added", "human_note": "PRIVATE_NOTE",
            "checks": [{"kind": "count", "types": ["text"], "comparison": "exact", "value": 2, "distinct_bytes": True}]})
    project["decisions"] = [{"requirement_id": row["id"], "file_ids": ["f1"], "review_state": "confirmed", "human_disposition": disposition,
                             "input_hash": input_hash(project), "internal_decision_note": "PRIVATE_INTERNAL", "client_usage_note": "Use the guide.",
                             "client_exception_note": public_exception} for row in project["baseline"]["requirements"]]
    return project


def confirm_hashes(project):
    for decision in project["decisions"]:
        decision["input_hash"] = input_hash(project)


def test_failure_remains_gap_even_when_human_satisfied():
    project = packet()
    summary = build_summary(project)
    assert summary["status"] == "draft_with_gaps"
    assert summary["current_review_count"] == 1
    assert summary["failed_check_count"] == 1
    assert summary["attention_requirement_ids"] == ["r0"]
    with pytest.raises(StoreError, match="unresolved"):
        projection(project, False)
    value = projection(project, True)
    assert value["requirements"][0]["checks"][0]["actual"] == 1
    for format, content in render(value).items():
        assert "PRIVATE_" not in content, format
        assert "unselected-private.txt" not in content
    assert value["source_revision"] == 12
    assert value["schema_version"] == 2
    assert len(value["files"]) == 1


def test_scope_exception_retains_failed_findings_without_applicable_blocker():
    project = packet(disposition="not_applicable", public_exception="Excluded by reviewer from this packet.")
    value = projection(project, False)
    assert value["status"] == "reviewed_with_exceptions"
    summary = value["attention_summary"]
    assert summary["failed_check_count"] == 1
    assert summary["attention_requirement_ids"] == []
    assert summary["exception_requirement_ids"] == ["r0"]
    assert value["requirements"][0]["checks"][0]["status"] == "fail"
    for content in render(value).values():
        assert "Excluded by reviewer" in content
        assert "client acceptance" in content


def test_legacy_exception_needs_deliberate_public_explanation():
    project = packet(disposition="not_applicable")
    del project["decisions"][0]["client_exception_note"]
    before = canonical(project)
    summary = build_summary(project)
    assert summary["rows"][0]["reason_codes"] == ["exception_note_missing"]
    assert summary["status"] == "draft_with_gaps"
    with pytest.raises(StoreError):
        projection(project, False)
    exported = render(projection(project, True))
    assert "Client-facing explanation not supplied." in exported["html"]
    assert "PRIVATE_INTERNAL" not in exported["json"]
    assert canonical(project) == before


def test_stale_exception_cannot_exclude_current_work():
    project = packet(disposition="not_applicable", public_exception="OLD_PUBLIC_EXCEPTION")
    project["files"][0]["name"] = "replacement.txt"
    value = projection(project, True)
    assert value["attention_summary"]["stale_review_count"] == 1
    assert value["attention_summary"]["exception_count"] == 0
    assert value["requirements"][0]["human_disposition"] == "unresolved"
    assert value["files"] == []
    assert "OLD_PUBLIC_EXCEPTION" not in json.dumps(value)


def test_manual_check_not_an_unavailable_technical_finding():
    project = packet()
    project["baseline"]["requirements"][0]["checks"] = [{"kind": "manual", "instruction": "Visually review the design."}]
    confirm_hashes(project)
    summary = build_summary(project)
    assert summary["unknown_check_count"] == 0
    assert summary["manual_requirement_count"] == 1
    assert summary["status"] == "reviewed"
    html = render(projection(project, False))["html"]
    assert "Human judgment: requires human assessment" in html
    assert "manual: pass" not in html


def test_twenty_rows_count_requirements_and_findings_separately():
    project = packet(count=20, disposition="not_applicable", public_exception="Excluded by reviewer.")
    project["baseline"]["requirements"][0]["checks"].append({"kind": "png_nonopaque_pixels"})
    confirm_hashes(project)
    summary = build_summary(project)
    assert summary["requirement_count"] == summary["current_review_count"] == summary["exception_count"] == 20
    assert summary["failed_check_count"] == 20
    assert summary["unknown_check_count"] == 1
    assert len(summary["failed_requirement_ids"]) == 20
    assert summary["unknown_requirement_ids"] == ["r0"]
    value = projection(project, False)
    assert len(value["files"]) == 1
    assert all(len(content.encode()) < 2 * 1024 * 1024 for content in render(value).values())


def test_unknown_and_unreviewed_statuses_remain_visible():
    project = packet()
    project["baseline"]["requirements"][0]["checks"] = [{"kind": "png_nonopaque_pixels"}]
    confirm_hashes(project)
    assert build_summary(project)["unknown_check_count"] == 1
    project["decisions"] = []
    summary = build_summary(project)
    assert summary["unreviewed_count"] == 1
    assert summary["current_review_count"] == 0
    assert summary["rows"][0]["reason_codes"] == ["needs_review", "technical_unknown"]


def test_safe_numeric_evidence_and_original_identity_in_all_formats():
    value = projection(packet(), True)
    output = render(value)
    for format in ("md", "html"):
        assert "expected: 2" in output[format]
        assert "observed: 1" in output[format]
        assert "a" * 64 in output[format]
        assert "Send the original files alongside this record." in output[format]
        assert "Source revision" in output[format]
    assert json.loads(output["json"])["files"][0]["size"] == 15


def test_hostile_strings_escape_and_cannot_create_markdown_blocks():
    project = packet(disposition="not_applicable", public_exception='<script>attack()</script>\n[link]: javascript:alert(1)')
    project["name"] = '<img onerror="attack()">'
    project["baseline"]["requirements"][0]["title"] = '<script>title()</script>'
    project["files"][0]["name"] = 'guide"><script>x()</script>.txt'
    confirm_hashes(project)
    output = render(projection(project, False))
    assert "<script>" not in output["html"]
    assert "&lt;script&gt;" in output["html"]
    assert "\n[link]:" not in output["md"]
    assert "\\[link\\]" in output["md"]
    assert "@page{size:auto" in output["html"]
    assert "<script src" not in output["html"]
    assert "@import" not in output["html"]


def test_private_literal_expectation_redacted():
    project = packet()
    project["baseline"]["requirements"][0]["checks"] = [{"kind": "literal_text", "needle": "PRIVATE_RAW_BRIEF"}]
    confirm_hashes(project)
    value = projection(project, True)
    assert "expected" not in value["requirements"][0]["checks"][0]
    assert value["requirements"][0]["checks"][0]["actual"] is False
    assert "PRIVATE_" not in json.dumps(value)


def test_rendered_snapshot_and_project_inputs_do_not_change():
    project = packet()
    before = copy.deepcopy(project)
    snapshot = projection(project, True)
    output = render(snapshot)
    project["files"][0]["name"] = "corrected.txt"
    project["decisions"][0]["human_disposition"] = "needs_work"
    build_summary(project)
    projection(project, True)
    assert render(snapshot) == output
    assert snapshot["files"][0]["name"] == before["files"][0]["name"]


def test_unapproved_or_empty_scope_never_appears_reviewed():
    project = packet()
    project["baseline"]["state"] = "draft"
    assert build_summary(project)["status"] == "draft_with_gaps"
    with pytest.raises(StoreError):
        projection(project, True)
    project["baseline"].update(state="approved", requirements=[])
    assert build_summary(project)["status"] == "draft_with_gaps"
    with pytest.raises(StoreError):
        projection(project, True)


def test_client_labels_describe_narrow_facts_not_internal_keys():
    from handoffready.exports import _check_lines
    lines = _check_lines({"kind": "png_nonopaque_pixels", "status": "fail", "reason": "Visual review still required.", "actual": [False]})
    assert lines[0].startswith("PNG contains nonopaque pixels: fail")
    assert all("png_nonopaque_pixels" not in line for line in lines)
    assert lines[1] == "PNG contains nonopaque pixels observed: [false]"
