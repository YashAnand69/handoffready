"""Occurrence grounding tests verify literal identities, not semantic accuracy."""
import copy
import hashlib

import pytest

from handoffready.evidence import CATALOG_VERSION, source_catalog, validate_source_evidence


def test_catalog_retains_repeated_sentences_and_exact_offsets():
    text = "  Deliver PNG.\r\n  Deliver PNG.  "
    units = source_catalog(text, "brief")
    assert [unit["quote"] for unit in units] == ["Deliver PNG."] * 2
    assert units[0]["evidence_unit_id"] != units[1]["evidence_unit_id"]
    for unit in units:
        assert text[unit["start_cp"]:unit["end_cp"]] == unit["quote"]
        assert len(unit["evidence_unit_id"]) < 100
        assert unit["source_unit_id"] == "brief"
        assert unit["source_text_sha256"] == hashlib.sha256(text.encode()).hexdigest()
    assert source_catalog(text, "brief") == units


def test_same_literal_in_different_sources_has_different_identity():
    text = "Deliver PNG."
    assert source_catalog(text, "first")[0]["evidence_unit_id"] != source_catalog(text, "second")[0]["evidence_unit_id"]


def test_text_revision_invalidates_unit_even_when_quote_survives():
    original = "Deliver PNG."
    unit = source_catalog(original, "brief")[0]
    with pytest.raises(ValueError, match="changed/other"):
        validate_source_evidence(original + " Extra work.", "brief", unit["quote"], evidence_unit_id=unit["evidence_unit_id"], catalog_version=CATALOG_VERSION)


def test_non_bmp_and_crlf_use_original_code_point_positions():
    text = "🎨 Logo café.\r\n\r\n 🦉Second paragraph."
    units = source_catalog(text, "brief")
    assert units[1]["start_cp"] == text.index("🦉")
    assert units[1]["end_cp"] == len(text)
    for unit in units:
        assert validate_source_evidence(text, "brief", None, evidence_unit_id=unit["evidence_unit_id"], catalog_version=CATALOG_VERSION) == unit


@pytest.mark.parametrize("text", ["x" * 1001, "word " * 201, "x" * 499 + " z" * 300])
def test_long_units_are_bounded_without_losing_nonwhitespace(text):
    units = source_catalog(text, "brief")
    assert all(1 <= len(unit["quote"]) <= 500 for unit in units)
    addressed = set()
    for unit in units:
        addressed.update(range(unit["start_cp"], unit["end_cp"]))
    assert all(index in addressed for index, char in enumerate(text) if not char.isspace())


def test_exact_legacy_span_preserves_repeated_occurrence_without_migration():
    text = "same. same."
    unit = source_catalog(text, "brief")[1]
    legacy = {key: value for key, value in unit.items() if key not in {"evidence_unit_id", "catalog_version"}}
    before = copy.deepcopy(legacy)
    assert validate_source_evidence(text, "brief", "same.", legacy) == before
    assert legacy == before


def test_legacy_unique_quote_can_resolve_substring_not_catalog_unit():
    span = validate_source_evidence("Read the café guide.", "brief", "café")
    assert span["start_cp"] == 9
    assert span["end_cp"] == 13
    assert "evidence_unit_id" not in span


@pytest.mark.parametrize("text,quote", [("same. same.", "same."), ("aaaa", "aaa"), ("actual", "invented")])
def test_ambiguous_or_missing_legacy_quote_is_not_silently_located(text, quote):
    with pytest.raises(ValueError, match="missing or ambiguous"):
        validate_source_evidence(text, "brief", quote)


@pytest.mark.parametrize("key,value", [("source_unit_id", "other"), ("source_text_sha256", "0" * 64), ("start_cp", 1), ("end_cp", 999), ("quote", "invented"), ("start_cp", False)])
def test_new_unit_rejects_forged_span_field(key, value):
    text = "Exact source."
    unit = source_catalog(text, "brief")[0]
    forged = {**unit, key: value}
    with pytest.raises(ValueError):
        validate_source_evidence(text, "brief", unit["quote"], forged)


@pytest.mark.parametrize("key,value", [("source_unit_id", "other"), ("source_text_sha256", "0" * 64), ("start_cp", False), ("end_cp", 999), ("quote", "invented")])
def test_legacy_span_rejects_forged_fields(key, value):
    text = "Exact source."
    unit = source_catalog(text, "brief")[0]
    legacy = {k: v for k, v in unit.items() if k not in {"evidence_unit_id", "catalog_version"}}
    legacy[key] = value
    with pytest.raises(ValueError):
        validate_source_evidence(text, "brief", unit["quote"], legacy)


@pytest.mark.parametrize("unit_id,version", [("invented", CATALOG_VERSION), (None, CATALOG_VERSION), ("ev1_fake", None), ("ev1_fake", "future")])
def test_missing_unknown_and_unversioned_units_rejected(unit_id, version):
    with pytest.raises(ValueError):
        validate_source_evidence("Exact source.", "brief", "Exact source.", evidence_unit_id=unit_id, catalog_version=version)


def test_conflicting_top_level_and_span_occurrence_ids_rejected():
    text = "same. same."
    units = source_catalog(text, "brief")
    with pytest.raises(ValueError, match="disagree"):
        validate_source_evidence(text, "brief", units[0]["quote"], units[0], evidence_unit_id=units[1]["evidence_unit_id"], catalog_version=CATALOG_VERSION)


def test_invented_quote_cannot_override_real_unit():
    unit = source_catalog("Exact source.", "brief")[0]
    with pytest.raises(ValueError, match="Quote does not match"):
        validate_source_evidence("Exact source.", "brief", "invented", evidence_unit_id=unit["evidence_unit_id"], catalog_version=CATALOG_VERSION)


def test_no_unicode_normalization_of_source_or_digest():
    composed = "café"
    decomposed = "cafe\u0301"
    unit = source_catalog(composed, "brief")[0]
    with pytest.raises(ValueError):
        validate_source_evidence(decomposed, "brief", None, evidence_unit_id=unit["evidence_unit_id"], catalog_version=CATALOG_VERSION)


@pytest.mark.parametrize("source_id", ["", "x" * 101, None])
def test_invalid_source_identity_rejected(source_id):
    with pytest.raises(ValueError):
        source_catalog("Exact source.", source_id)


def test_source_character_bound_is_explicit():
    with pytest.raises(ValueError, match="character bound"):
        source_catalog("x" * 20001, "brief")


def test_alternate_model_port_remains_explicit_loopback_only(monkeypatch):
    from handoffready import model
    monkeypatch.setenv("HANDOFF_MODEL_PORT", "18082")
    monkeypatch.delenv("HANDOFF_MODEL_URL", raising=False)
    assert model._endpoint() == "http://127.0.0.1:18082"
    for value in ("80", "-1", "65536", "18a82", "１２３４５"):
        monkeypatch.setenv("HANDOFF_MODEL_PORT", value)
        with pytest.raises(model.ModelError):
            model._endpoint()
