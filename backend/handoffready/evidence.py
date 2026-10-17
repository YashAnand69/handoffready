"""Literal source occurrence identities and backward-compatible evidence validation.

Coordinates address Python Unicode code points in the original, unnormalised text.
A catalog identifies occurrences; it does not certify their semantic relevance.
"""
from __future__ import annotations

import hashlib
import json
import re

CATALOG_VERSION = "source-occurrence-v1"
MAX_QUOTE_LENGTH = 500
MAX_SOURCE_LENGTH = 20_000
_SEPARATOR = re.compile(r"(?<=[.!?;])\s+|\n+")


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _check_source(text: str, source_id: str) -> None:
    if not isinstance(text, str) or len(text) > MAX_SOURCE_LENGTH:
        raise ValueError("Source text exceeds the supported character bound.")
    if not isinstance(source_id, str) or not 1 <= len(source_id) <= 100:
        raise ValueError("Source identity is missing or invalid.")


def source_catalog(text: str, source_id: str) -> list[dict]:
    """Return every bounded literal unit, retaining repeated occurrences.

    IDs bind version, document identity, full text hash and exact range. The
    compact hash is collision checked within the catalog rather than trusted
    as a substitute for verifying source identity, digest, bounds and literal.
    """
    _check_source(text, source_id)
    digest = _text_hash(text)
    units: list[dict] = []
    seen: set[str] = set()
    boundaries = [match.span() for match in _SEPARATOR.finditer(text)]
    cursor = 0
    for separator_start, separator_end in boundaries + [(len(text), len(text))]:
        start, stop = cursor, separator_start
        while start < stop and text[start].isspace():
            start += 1
        while stop > start and text[stop - 1].isspace():
            stop -= 1
        while start < stop:
            end = min(start + MAX_QUOTE_LENGTH, stop)
            if end < stop:
                boundary = text.rfind(" ", start, end)
                if boundary > start:
                    end = boundary
            trimmed_end = end
            while trimmed_end > start and text[trimmed_end - 1].isspace():
                trimmed_end -= 1
            if trimmed_end > start:
                scope = json.dumps(
                    [CATALOG_VERSION, source_id, digest, start, trimmed_end],
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                unit_id = "ev1_" + hashlib.sha256(scope.encode("utf-8")).hexdigest()[:24]
                if unit_id in seen:
                    raise ValueError("Source occurrence identity collision; use manual review.")
                seen.add(unit_id)
                units.append({
                    "evidence_unit_id": unit_id,
                    "catalog_version": CATALOG_VERSION,
                    "source_unit_id": source_id,
                    "source_text_sha256": digest,
                    "start_cp": start,
                    "end_cp": trimmed_end,
                    "quote": text[start:trimmed_end],
                })
            start = end
            while start < stop and text[start].isspace():
                start += 1
        cursor = separator_end
    return units


def validate_source_evidence(
    text: str,
    source_id: str,
    quote: str | None,
    source_span: dict | None = None,
    *,
    evidence_unit_id: str | None = None,
    catalog_version: str | None = None,
) -> dict:
    """Resolve a new occurrence ID or validate an existing exact source span.

    Legacy spans remain structurally unchanged. Quote-only evidence resolves
    only if there is exactly one occurrence, including overlapping matches.
    Ambiguous legacy quotes need explicit source correction, never index(0).
    """
    _check_source(text, source_id)
    if source_span is not None and not isinstance(source_span, dict):
        raise ValueError("Source span must be an object.")
    span = dict(source_span) if source_span is not None else None
    span_id = span.get("evidence_unit_id") if span else None
    span_version = span.get("catalog_version") if span else None
    if evidence_unit_id is not None and span_id is not None and evidence_unit_id != span_id:
        raise ValueError("Source occurrence identities disagree.")
    if catalog_version is not None and span_version is not None and catalog_version != span_version:
        raise ValueError("Source catalog versions disagree.")
    unit_id = evidence_unit_id if evidence_unit_id is not None else span_id
    version = catalog_version if catalog_version is not None else span_version
    if unit_id is not None or version is not None:
        if not isinstance(unit_id, str) or version != CATALOG_VERSION:
            raise ValueError("Source occurrence identity/version is missing or unsupported.")
        unit = next((item for item in source_catalog(text, source_id) if item["evidence_unit_id"] == unit_id), None)
        if unit is None:
            raise ValueError("Source occurrence is unknown or belongs to changed/other source text.")
        if quote is not None and quote != unit["quote"]:
            raise ValueError("Quote does not match the selected source occurrence.")
        if span is not None:
            # A supplied span must contain the full established source binding.
            for key in ("source_unit_id", "source_text_sha256", "start_cp", "end_cp", "quote"):
                if key not in span or span[key] != unit[key]:
                    raise ValueError("Source span does not match the selected occurrence.")
            if type(span["start_cp"]) is not int or type(span["end_cp"]) is not int:
                raise ValueError("Source coordinates must be integer code-point positions.")
        return dict(unit)
    if not isinstance(quote, str) or not 1 <= len(quote) <= MAX_QUOTE_LENGTH:
        raise ValueError("A nonempty bounded exact source quote is required.")
    digest = _text_hash(text)
    if span is not None:
        start, end = span.get("start_cp"), span.get("end_cp")
        if (
            span.get("source_unit_id") != source_id
            or span.get("source_text_sha256") != digest
            or type(start) is not int
            or type(end) is not int
            or not 0 <= start < end <= len(text)
            or span.get("quote") != quote
            or text[start:end] != quote
        ):
            raise ValueError("Legacy source span has an invalid source identity, digest, range or literal.")
        return span
    start = text.find(quote)
    if start == -1 or text.find(quote, start + 1) != -1:
        raise ValueError("Source quote is missing or ambiguous; choose an exact occurrence.")
    return {
        "source_unit_id": source_id,
        "source_text_sha256": digest,
        "start_cp": start,
        "end_cp": start + len(quote),
        "quote": quote,
    }
