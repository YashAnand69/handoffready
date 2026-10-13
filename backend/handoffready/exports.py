import html
import json
from .checks import evaluate
from .store import input_hash, now, uid, StoreError
from .policy import LIMITS


def projection(project, acknowledge):
    if project["baseline"]["state"] != "approved":
        raise StoreError("baseline_not_approved", "Review and approve the baseline before exporting.")
    decisions = {d["requirement_id"]: d for d in project["decisions"]}
    files = {f["id"]: f for f in project["files"]}
    checks = evaluate(project)
    requirements, gaps = [], []
    current_hash = input_hash(project)
    for requirement in project["baseline"]["requirements"]:
        decision = decisions.get(requirement["id"])
        row_checks = [c for c in checks if c["requirement_id"] == requirement["id"]]
        current = decision and decision["input_hash"] == current_hash and decision["review_state"] == "confirmed"
        disposition = decision["human_disposition"] if current else "unresolved"
        review_state = decision["review_state"] if decision else "unreviewed"
        row_gaps = []
        if not current:
            row_gaps.append("Mapping needs current human review.")
        if disposition in {"unresolved", "needs_work"}:
            row_gaps.append("Human disposition: " + disposition)
        if disposition != "not_applicable":
            for check in row_checks:
                if check["status"] in {"fail", "unknown"} and check["kind"] != "manual":
                    row_gaps.append(check["kind"] + ": " + check["status"])
        gaps.extend({"requirement_id": requirement["id"], "message": message} for message in row_gaps)
        # Deliberately omit raw brief, quotations, private review notes and model reasoning.
        safe_checks = [{key: value for key, value in check.items() if key != "expected" or check["kind"] != "literal_text"} for check in row_checks]
        requirements.append({"id": requirement["id"], "title": requirement["title"], "origin": requirement["origin"],
                             "review_state": review_state, "human_disposition": disposition,
                             "client_usage_note": decision["client_usage_note"] if current else "", "checks": safe_checks,
                             "files": [{key: files[file_id][key] for key in ("id", "name", "type", "size", "sha256", "inspection")} for file_id in decision["file_ids"] if file_id in files] if current else [],
                             "gaps": row_gaps})
    if gaps and not acknowledge:
        raise StoreError("unresolved_export", "This handoff has unresolved items. Acknowledge the gaps or resolve them first.")
    return {"id": uid(), "project_name": project["name"], "created_at": now(), "input_hash": current_hash,
            "baseline_hash": project["baseline"]["hash"], "status": "draft_with_gaps" if gaps else "reviewed",
            "requirements": requirements, "gaps": gaps,
            "scope_notice": "Delivery evidence and human review only. This is not a certification, client acceptance, website execution test or aesthetic judgment."}


def render(value):
    def escape_md(text):
        return str(text).replace("\\", "\\\\").replace("<", "\\<").replace(">", "\\>").replace("[", "\\[").replace("]", "\\]").replace("*", "\\*").replace("_", "\\_").replace("#", "\\#")
    md = ["# " + escape_md(value["project_name"]) + " — handoff", "", "Status: " + value["status"], "", value["scope_notice"], ""]
    sections = []
    for row in value["requirements"]:
        md.extend(["## " + escape_md(row["title"]), "", "Human disposition: " + row["human_disposition"], ""])
        lines = []
        for file in row["files"]:
            lines.append("File: " + file["name"] + " (" + file["type"] + ")")
        for check in row["checks"]:
            lines.append(check["kind"] + ": " + check["status"] + ". " + check["reason"])
            for fact in ("expected", "actual"):
                if fact in check:
                    lines.append(check["kind"] + " " + fact + ": " + json.dumps(check[fact], ensure_ascii=False))
        for gap in row["gaps"]:
            lines.append("Unresolved: " + gap)
        if row["client_usage_note"]:
            lines.append("Usage note: " + row["client_usage_note"])
        md.extend("- " + escape_md(line) for line in lines)
        md.append("")
        sections.append("<section><h2>" + html.escape(row["title"]) + "</h2><p>Human disposition: " + html.escape(row["human_disposition"]) + "</p><ul>" + "".join("<li>" + html.escape(line) + "</li>" for line in lines) + "</ul></section>")
    rendered = {"json": json.dumps(value, ensure_ascii=False, indent=2), "md": "\n".join(md),
                "html": '<!doctype html><html lang="en"><meta charset="utf-8"><title>Handoff</title><style>body{font:16px system-ui;max-width:850px;margin:3rem auto;padding:1rem;line-height:1.6}section{break-inside:avoid}li{overflow-wrap:anywhere}</style><body><h1>' + html.escape(value["project_name"]) + '</h1><p>Status: ' + value["status"] + '</p><p>' + html.escape(value["scope_notice"]) + '</p>' + "".join(sections) + '</body></html>'}
    if any(len(content.encode()) > LIMITS["export_bytes"] for content in rendered.values()):
        raise StoreError("export_limit", "Export exceeds the text size limit.", 413)
    return rendered
