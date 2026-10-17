"""Pure, shared delivery state: review, assessment, facts and exclusions stay separate."""

from .checks import evaluate
from .store import input_hash


SUMMARY_VERSION = 1


def build_summary(project, checks=None):
    """Describe saved evidence without altering project data or copying private prose."""
    checks = evaluate(project) if checks is None else checks
    current_hash = input_hash(project)
    decisions = {decision["requirement_id"]: decision for decision in project["decisions"]}
    by_requirement = {}
    for check in checks:
        by_requirement.setdefault(check["requirement_id"], []).append(check)
    rows = []
    for requirement in project["baseline"]["requirements"]:
        decision = decisions.get(requirement["id"])
        current = bool(decision and decision.get("input_hash") == current_hash
                       and decision.get("review_state") == "confirmed")
        stale = bool(decision and (decision.get("review_state") == "stale"
                                  or decision.get("input_hash") != current_hash))
        disposition = decision["human_disposition"] if current else "unresolved"
        findings = by_requirement.get(requirement["id"], [])
        failed = sum(check["kind"] != "manual" and check["status"] == "fail" for check in findings)
        unknown = sum(check["kind"] != "manual" and check["status"] == "unknown" for check in findings)
        exception = current and disposition == "not_applicable"
        reasons, messages = [], []

        def add(code, message):
            reasons.append(code)
            messages.append(message)

        if not current:
            add("stale_review" if stale else "needs_review", "Mapping needs current human review.")
        if not exception:
            if failed:
                add("technical_failure", f"{failed} technical check(s) failed.")
            if unknown:
                add("technical_unknown", f"{unknown} technical check(s) unavailable.")
        if current and disposition in {"needs_work", "unresolved"}:
            add("human_" + disposition, "Human disposition: " + disposition)
        if exception and not decision.get("client_exception_note", "").strip():
            add("exception_note_missing", "Scope exception needs a deliberate client-facing explanation.")
        rows.append({
            "requirement_id": requirement["id"],
            "review_currency": "current" if current else "stale" if stale else "unreviewed",
            "human_disposition": disposition, "applicable_attention": bool(reasons),
            "is_exception": bool(exception), "reason_codes": reasons, "messages": messages,
            "failed_check_count": failed, "unknown_check_count": unknown,
            "has_manual_checks": any(check["kind"] == "manual" for check in findings),
        })
    approved = project["baseline"].get("state") == "approved" and bool(rows)
    attention = [row["requirement_id"] for row in rows if row["applicable_attention"]]
    exceptions = [row["requirement_id"] for row in rows if row["is_exception"]]
    return {
        "contract_version": SUMMARY_VERSION, "source_revision": project.get("revision", 0),
        "input_hash": current_hash, "baseline_approved": approved,
        "status": "draft_with_gaps" if not approved or attention else "reviewed_with_exceptions" if exceptions else "reviewed",
        "requirement_count": len(rows),
        "current_review_count": sum(row["review_currency"] == "current" for row in rows),
        "stale_review_count": sum(row["review_currency"] == "stale" for row in rows),
        "unreviewed_count": sum(row["review_currency"] == "unreviewed" for row in rows),
        "needs_work_count": sum(row["review_currency"] == "current" and row["human_disposition"] == "needs_work" for row in rows),
        "unresolved_count": sum(row["review_currency"] == "current" and row["human_disposition"] == "unresolved" for row in rows),
        "exception_count": len(exceptions),
        "failed_check_count": sum(row["failed_check_count"] for row in rows),
        "unknown_check_count": sum(row["unknown_check_count"] for row in rows),
        "manual_requirement_count": sum(row["has_manual_checks"] for row in rows),
        "failed_requirement_ids": [row["requirement_id"] for row in rows if row["failed_check_count"]],
        "unknown_requirement_ids": [row["requirement_id"] for row in rows if row["unknown_check_count"]],
        "attention_requirement_ids": attention, "exception_requirement_ids": exceptions, "rows": rows,
    }
