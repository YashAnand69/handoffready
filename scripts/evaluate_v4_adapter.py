"""Capture one existing model call, then canonicalize its before/after guard output.

No inference occurs at import. The evaluator invokes this only after candidate freeze.
The transient wrappers only copy returned data and always restore originals.
"""
from __future__ import annotations

import copy
import time

from handoffready import model
from handoffready.evidence import source_catalog, validate_source_evidence

SAFE_MODEL_FIELDS = {"model_id", "model", "engine", "prompt_version", "temperature", "seed", "input_tokens", "output_tokens", "elapsed_seconds", "input_sha256", "output_sha256", "vision_used", "source_catalog_version", "required_suggestion_count", "excluded_suggestion_count", "unrelated_association_count", "typed_rejection_count", "association_guard_version", "supporting_association_count"}


def source_record(record, text, source_id):
    result = copy.deepcopy(record)
    occurrence = result.get("evidence_unit_id")
    if occurrence is not None:
        units = {unit["evidence_unit_id"]: unit for unit in source_catalog(text, source_id)}
        unit = units.get(occurrence)
        if unit:
            result["quote"] = unit["quote"]
            result["source_span"] = unit
    try:
        validate_source_evidence(text, source_id, result.get("quote"), result.get("source_span"))
        result["quote_valid"] = True
    except (ValueError, TypeError):
        result["quote_valid"] = False
    return result


def requirements_for_score(records, brief, source_id, default=None):
    converted = []
    for record in records:
        normalized = source_record(record, brief, source_id)
        if default is not None:
            normalized.setdefault("obligation", default)
        converted.append(normalized)
    return converted


def proposals_for_score(records, files, *, guarded=False):
    inventory = {file["id"]: file for file in files}
    converted = []
    for proposal in records:
        candidates = []
        for candidate in proposal["candidates"]:
            file = inventory.get(candidate["file_id"])
            if file and file.get("text"):
                normalized = source_record(candidate, file["text"], file["id"])
            else:
                normalized = copy.deepcopy(candidate)
                normalized["quote_valid"] = None  # Non-text metadata candidate has no text-quote denominator.
            candidates.append(normalized)
        # Post-guard records have had their relation removed after acceptance.
        # Raw unrelated candidates remain available for diagnostics and quotes,
        # but do not express a positive association.
        supporting = [candidate for candidate in candidates if candidate.get("relation") == "supports" or (guarded and "relation" not in candidate)]
        converted.append({"requirement_id": proposal["requirement_id"], "file_ids": [candidate["file_id"] for candidate in supporting], "candidates": candidates, "unrelated_candidate_count": sum(candidate.get("relation") == "unrelated" for candidate in candidates), "candidate_count": len(candidates), "coverage": proposal.get("coverage", "")})
    return converted


def captured_call(stage, brief, source_id, files, requirements):
    original_generate = model._generate
    original_request = model._request
    captured = {"stage": stage, "structured_call_count": 0, "completion_response_count": 0, "request_started_monotonic": time.monotonic(), "synthetic_data_only": True}
    structured = None

    def generate_copy(*args, **kwargs):
        nonlocal structured
        captured["structured_call_count"] += 1
        returned = original_generate(*args, **kwargs)
        structured = copy.deepcopy(returned)
        return returned

    def request_copy(*args, **kwargs):
        returned = original_request(*args, **kwargs)
        if isinstance(returned, dict) and isinstance(returned.get("choices"), list):
            captured["completion_response_count"] += 1
            # Capture only generation output and accounting, never URLs, headers,
            # prompts, request configuration, local model paths or credentials.
            captured["completion"] = {"choices": [{"index": choice.get("index"), "finish_reason": choice.get("finish_reason"), "content": choice.get("message", {}).get("content")} for choice in returned["choices"]], "usage": copy.deepcopy(returned.get("usage"))}
        return returned

    model._generate = generate_copy
    model._request = request_copy
    outcome = None
    failure = None
    try:
        source = {"id": source_id, "text": brief}
        deadline = time.monotonic() + 180
        if stage == "extract":
            outcome = model.extract(source, deadline=deadline, capture_predictions=True)
        else:
            outcome = model.match(source, requirements, files, deadline=deadline, capture_predictions=True)
        if captured["structured_call_count"] != 1:
            raise ValueError("Expected exactly one structured model generation")
        if "pre_guard_predictions" not in outcome.get("model", {}):
            raise ValueError("Current model did not return captured pre-guard predictions")
    except Exception as error:
        failure = {"code": getattr(error, "code", type(error).__name__), "message": getattr(error, "message", "Captured call failed; see error code."), "stage": stage}
    finally:
        model._generate = original_generate
        model._request = original_request
        captured["elapsed_seconds"] = time.monotonic() - captured.pop("request_started_monotonic")
    raw = outcome.get("model", {}).get("pre_guard_predictions") if outcome else None
    if raw is None and structured:
        raw = {key: value for key, value in structured.items() if key != "model"}
    captured["structured_pre_guard"] = copy.deepcopy(raw)
    metadata = (outcome or structured or {}).get("model", {})
    captured["model_metadata"] = {key: copy.deepcopy(value) for key, value in metadata.items() if key in SAFE_MODEL_FIELDS and isinstance(value, (str, int, float, bool, type(None)))}
    if stage == "extract":
        raw_predictions = requirements_for_score((raw or {}).get("requirements", []), brief, source_id)
        guarded_predictions = requirements_for_score((outcome or {}).get("requirements", []), brief, source_id, "required")
        # Optional/excluded suggestions are classified outputs, not approved work.
        guarded_predictions += requirements_for_score((outcome or {}).get("model", {}).get("excluded_suggestions", []), brief, source_id)
    else:
        raw_predictions = proposals_for_score((raw or {}).get("proposals", []), files)
        guarded_predictions = proposals_for_score((outcome or {}).get("proposals", []), files, guarded=True)
    return {"raw_predictions": raw_predictions, "guarded_predictions": guarded_predictions, "capture": captured, "failure": failure}


def extract(*, brief, source_id, files, requirements, capture_predictions=True):
    if capture_predictions is not True:
        raise ValueError("Evaluation requires captured predictions")
    return captured_call("extract", brief, source_id, files, requirements)


def associate(*, brief, source_id, files, requirements, capture_predictions=True):
    if capture_predictions is not True:
        raise ValueError("Evaluation requires captured predictions")
    return captured_call("associate", brief, source_id, files, requirements)
