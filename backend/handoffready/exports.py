"""Versioned client records rendered from one privacy-preserving projection."""
import html
import json
from .checks import evaluate
from .policy import LIMITS
from .store import now, uid, StoreError
from .summary import build_summary

SCHEMA_VERSION = 2
SCOPE_NOTICE = "Delivery evidence and human review only. This is not a certification, client acceptance, website execution test or aesthetic judgment."
ORIGINALS_NOTICE = "Send the original files alongside this record. This document identifies supporting files; it does not contain their original bytes."
STATUS_LABELS = {"draft_with_gaps": "Draft with outstanding items", "reviewed_with_exceptions": "Reviewed with scope exceptions", "reviewed": "Reviewed delivery record"}
STATUS_MEANINGS = {
    "draft_with_gaps": "Outstanding review, assessment, technical findings or exception explanations remain. Read the actions below before sending.",
    "reviewed_with_exceptions": "Applicable items have current review; the reviewer has explicitly excluded items listed below. Excluded technical findings remain visible.",
    "reviewed": "Current human review is recorded and no applicable narrow technical check is failed or unavailable. This does not establish client acceptance.",
}


def projection(project, acknowledge):
    if project["baseline"]["state"] != "approved" or not project["baseline"]["requirements"]:
        raise StoreError("baseline_not_approved", "Review and approve the baseline before exporting.")
    checks = evaluate(project)
    summary = build_summary(project, checks)
    decisions = {decision["requirement_id"]: decision for decision in project["decisions"]}
    files = {file["id"]: file for file in project["files"]}
    states = {row["requirement_id"]: row for row in summary["rows"]}
    requirements, gaps, selected_ids = [], [], set()
    for requirement in project["baseline"]["requirements"]:
        state = states[requirement["id"]]
        decision = decisions.get(requirement["id"])
        current = state["review_currency"] == "current"
        row_files = []
        for file_id in decision["file_ids"] if current else []:
            if file_id in files:
                selected_ids.add(file_id)
                row_files.append({key: files[file_id][key] for key in ("id", "name", "type", "size", "sha256", "inspection")})
        # A literal expectation may quote a private brief. Preserve numeric facts,
        # but exclude source quotes, raw file text, model reasons and private notes.
        safe_checks = [{key: value for key, value in check.items() if key != "expected" or check["kind"] != "literal_text"}
                       for check in checks if check["requirement_id"] == requirement["id"]]
        row_gaps = list(state["messages"])
        gaps.extend({"requirement_id": requirement["id"], "message": message} for message in row_gaps)
        requirements.append({
            **state, "id": requirement["id"], "title": requirement["title"], "origin": requirement["origin"],
            "review_state": "confirmed" if current else "stale" if state["review_currency"] == "stale" else decision.get("review_state", "unreviewed") if decision else "unreviewed",
            "client_usage_note": decision.get("client_usage_note", "") if current else "",
            "client_exception_note": decision.get("client_exception_note", "") if state["is_exception"] else "",
            "checks": safe_checks, "files": row_files, "gaps": row_gaps,
        })
    if gaps and not acknowledge:
        raise StoreError("unresolved_export", "This handoff has unresolved items. Acknowledge the gaps or resolve them first.")
    inventory = [{key: file[key] for key in ("id", "name", "type", "size", "sha256", "inspection")}
                 for file in project["files"] if file["id"] in selected_ids]
    return {"schema_version": SCHEMA_VERSION, "id": uid(), "project_name": project["name"], "created_at": now(),
            "source_revision": project.get("revision", 0), "input_hash": summary["input_hash"],
            "baseline_hash": project["baseline"]["hash"], "status": summary["status"], "attention_summary": summary,
            "requirements": requirements, "gaps": gaps, "files": inventory, "scope_notice": SCOPE_NOTICE, "originals_notice": ORIGINALS_NOTICE}


def _escape_md(text):
    text = str(text).replace("\\", "\\\\")
    for character in "<>[]*_#`|":
        text = text.replace(character, "\\" + character)
    return text.replace("\r", " ").replace("\n", " ")


def _size(size):
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MiB"
    if size >= 1024:
        return f"{size / 1024:.1f} KiB"
    return f"{size} bytes"


def _check_lines(check):
    labels = {"manual": "Human judgment", "presence": "Required file format", "count": "Selected file quantity",
              "image_dimensions": "Image pixel dimensions", "png_nonopaque_pixels": "PNG contains nonopaque pixels",
              "pdf_pages": "PDF page count", "literal_text": "Exact text presence"}
    label = labels.get(check["kind"], check["kind"].replace("_", " "))
    status = "requires human assessment" if check["kind"] == "manual" else check["status"]
    lines = [label + ": " + status + ". " + check["reason"]]
    for fact in ("expected", "actual"):
        if fact in check:
            lines.append(label + " " + ("expected" if fact == "expected" else "observed") + ": " + json.dumps(check[fact], ensure_ascii=False))
    return lines


_CSS = """
:root{color-scheme:light;--ink:#203c34;--muted:#52645d;--rule:#d6dfd9;--paper:#fff;--warm:#f7f6f0;--sage:#edf3ec;--amber:#73541d}
*{box-sizing:border-box}body{margin:0;background:var(--warm);color:var(--ink);font:15px/1.6 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
main{max-width:980px;margin:40px auto;padding:48px;background:var(--paper);border:1px solid var(--rule)}
h1,h2,h3,p{margin:0 0 12px}h1{font:500 clamp(28px,5vw,44px)/1.15 Georgia,serif;letter-spacing:-.025em;overflow-wrap:anywhere}h2{font:500 25px/1.25 Georgia,serif}h3{font-size:16px;line-height:1.4;overflow-wrap:anywhere}
.eyebrow{font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}.hero{padding-bottom:28px;border-bottom:2px solid var(--ink)}.identity{margin:16px 0;font-size:12px;color:var(--muted);overflow-wrap:anywhere}
.status{display:inline-block;font-size:13px;font-weight:700;padding:6px 12px;border:1px solid var(--rule);background:var(--sage);margin:8px 0 12px}.status.draft_with_gaps,.status.reviewed_with_exceptions{background:#fbf1df;color:var(--amber);border-color:#d9c8a4}
.meaning,.notice{max-width:76ch}.notice{font-size:13px;color:var(--muted)}.originals{padding:14px 18px;background:var(--sage);border-left:3px solid var(--ink);margin:20px 0}
.stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;padding:24px 0}.stat{border-bottom:1px solid var(--rule);padding-bottom:12px}.stat strong{display:block;font:500 27px/1.2 Georgia,serif}.stat span{font-size:12px;color:var(--muted)}.explanation{font-size:12px;color:var(--muted)}.group{margin-top:32px}.actions{border:1px solid #d9c8a4;padding:18px;background:#fffbf3}.actions li{margin:6px 0}.record-row{margin-top:22px;border-top:1px solid var(--rule);padding-top:18px}.row-heading{display:flex;align-items:baseline;gap:14px}.number{color:var(--muted);font-size:12px}.assessment{font-size:13px;margin:10px 0;display:flex;gap:16px;flex-wrap:wrap}.assessment span{border-left:2px solid var(--rule);padding-left:10px}
.exception{background:#fbf5e9;padding:14px;border-left:3px solid #9d7941}.note{padding:12px;background:var(--sage);white-space:pre-wrap}.facts{margin:12px 0;padding-left:22px}.facts li{margin:5px 0;overflow-wrap:anywhere}ul{padding-left:22px}li{overflow-wrap:anywhere}.file-list{list-style:none;padding:0;margin:10px 0}.file-list li{padding:7px 0;border-bottom:1px solid var(--rule);font-size:13px}.file-list strong{display:block;overflow-wrap:anywhere}.metadata{font-size:12px;color:var(--muted)}code{font-size:11px;overflow-wrap:anywhere;white-space:normal}details{margin:6px 0}summary{cursor:pointer;font-size:12px;color:var(--muted)}summary:focus-visible{outline:2px solid var(--ink);outline-offset:3px}.footer{margin-top:32px;padding-top:18px;border-top:2px solid var(--ink);font-size:11px;color:var(--muted);overflow-wrap:anywhere}
@media(max-width:600px){main{margin:0;padding:24px 18px;border:0}.stats{gap:10px;grid-template-columns:repeat(2,minmax(0,1fr))}.row-heading{gap:8px}.assessment{gap:10px}}
@page{size:auto;margin:16mm 15mm}@media print{body{background:#fff;color:#182d27;font-size:10pt;line-height:1.45}main{max-width:none;margin:0;padding:0;border:0}h1{font-size:26pt}h2{font-size:18pt}h3{font-size:12pt}.hero{padding-bottom:14pt}.stats{padding:14pt 0;gap:12pt}.stat strong{font-size:19pt}.status,.notice,.metadata,.explanation,.assessment{font-size:9pt}.group{margin-top:20pt}.record-row{margin-top:14pt;padding-top:12pt}.row-heading,h2,h3{break-after:avoid}p,li{orphans:3;widows:3}.file-list li,.exception,.originals,.stat{break-inside:avoid}.footer{font-size:8pt}details{display:block}details>summary{display:none}details>code{display:block!important}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""


def render(value):
    """Render a new or historical projection; persisted historic bytes aren't rewritten."""
    def esc(text):
        return html.escape(str(text), quote=True)
    status = value["status"]
    label = STATUS_LABELS.get(status, status)
    meaning = STATUS_MEANINGS.get(status, "Read the review and technical findings below.")
    summary = value.get("attention_summary", {})
    inventory = value.get("files")
    if inventory is None:
        inventory = list({file["id"]: file for row in value["requirements"] for file in row["files"]}.values())
    md = ["# " + _escape_md(value["project_name"]) + " — client delivery record", "",
          "Status: " + _escape_md(label) + " (" + _escape_md(status) + ")", "", meaning, "",
          "Snapshot: " + _escape_md(value["id"]), "Created: " + _escape_md(value["created_at"]),
          "Source revision: " + str(value.get("source_revision", "legacy")), "",
          value.get("originals_notice", ORIGINALS_NOTICE), "", value["scope_notice"], ""]
    stats = []
    for field, caption in (("requirement_count", "Scope items"), ("current_review_count", "Current human reviews"), ("failed_check_count", "Failed technical checks"),
                           ("unknown_check_count", "Unavailable technical checks"), ("exception_count", "Scope exceptions"),
                           ("manual_requirement_count", "Items with human-only checks")):
        if field in summary:
            stats.append('<div class="stat"><strong>' + str(summary[field]) + '</strong><span>' + caption + '</span></div>')
            md.append(caption + ": " + str(summary[field]))
    stats.append('<div class="stat"><strong>' + str(len(inventory)) + '</strong><span>Supporting originals</span></div>')
    md.extend(["Supporting originals: " + str(len(inventory)), "", "Counts overlap: check counts and requirement counts measure different things.", ""])
    actions = []
    titles = {row["id"]: row["title"] for row in value["requirements"]}
    if value["gaps"]:
        md.extend(["## Outstanding actions", ""])
        for gap in value["gaps"]:
            text = titles.get(gap["requirement_id"], gap["requirement_id"]) + ": " + gap["message"]
            actions.append("<li>" + esc(text) + "</li>")
            md.append("- " + _escape_md(text))
        md.append("")
    sections = []
    for index, row in enumerate(value["requirements"], 1):
        disposition = row["human_disposition"].replace("_", " ")
        currency = row.get("review_currency", row["review_state"]).replace("_", " ")
        md.extend(["## " + str(index) + ". " + _escape_md(row["title"]), "",
                   "Human disposition: " + _escape_md(disposition), "Review currency: " + _escape_md(currency), ""])
        body = '<div class="assessment"><span>Human assessment: <strong>' + esc(disposition) + '</strong></span><span>Review: ' + esc(currency) + '</span></div>'
        if row.get("is_exception", row["human_disposition"] == "not_applicable"):
            text = "Reviewer scope exception: " + (row.get("client_exception_note") or "Client-facing explanation not supplied.")
            body += '<p class="exception">' + esc(text) + '</p><p class="explanation">Technical findings remain reported; this is a reviewer exclusion, not verified client approval.</p>'
            md.extend([_escape_md(text), "", "Technical findings remain reported; this is a reviewer exclusion, not verified client approval.", ""])
        lines = [line for check in row["checks"] for line in _check_lines(check)]
        lines.extend("Outstanding: " + gap for gap in row["gaps"])
        if lines:
            body += '<ul class="facts">' + "".join("<li>" + esc(line) + "</li>" for line in lines) + '</ul>'
            md.extend("- " + _escape_md(line) for line in lines)
            md.append("")
        if row["files"]:
            body += '<p class="eyebrow">Supporting files</p><ul class="file-list">'
            for file in row["files"]:
                text = file["name"] + " · " + file["type"] + " · " + _size(file["size"]) + " · SHA-256 " + file["sha256"][:12]
                body += '<li>' + esc(text) + '</li>'
                md.append("- " + _escape_md(text))
            body += '</ul>'
            md.append("")
        if row["client_usage_note"]:
            body += '<p class="note"><strong>Usage note</strong><br>' + esc(row["client_usage_note"]) + '</p>'
            md.extend(["Usage note: " + _escape_md(row["client_usage_note"]), ""])
        sections.append('<section class="record-row"><div class="row-heading"><span class="number">' + f"{index:02}" + '</span><h3>' + esc(row["title"]) + '</h3></div>' + body + '</section>')
    md.extend(["## Supporting file inventory", ""])
    file_html = []
    for file in inventory:
        md.extend(["- " + _escape_md(file["name"] + " · " + file["type"] + " · " + _size(file["size"]) + " · " + file["inspection"]),
                   "  SHA-256: " + _escape_md(file["sha256"])])
        file_html.append('<li><strong>' + esc(file["name"]) + '</strong><span class="metadata">' + esc(file["type"] + " · " + _size(file["size"]) + " · " + file["inspection"]) + ' · SHA-256 ' + esc(file["sha256"][:12]) + '</span><details open><summary>Full file checksum</summary><code>' + esc(file["sha256"]) + '</code></details></li>')
    identity = "Input SHA-256: " + value["input_hash"] + " · Baseline SHA-256: " + value["baseline_hash"]
    md.extend(["", "## Record identity", "", "Schema version: " + str(value.get("schema_version", "legacy")),
               "Input SHA-256: " + value["input_hash"], "Baseline SHA-256: " + value["baseline_hash"], "",
               "Checksums identify content; they are not signatures, proof of client approval or trusted timestamps.", ""])
    page = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + esc(value["project_name"] + " — client delivery record") + '</title><style>' + _CSS + '</style></head><body><main><header class="hero"><p class="eyebrow">HandoffReady · client delivery record</p><h1>' + esc(value["project_name"]) + '</h1><p class="identity">' + esc(value["created_at"] + " · Snapshot " + value["id"] + " · Source revision " + str(value.get("source_revision", "legacy"))) + '</p><span class="status ' + esc(status) + '">' + esc(label) + '</span><p class="meaning">' + esc(meaning) + '</p><p class="notice">' + esc(value["scope_notice"]) + '</p></header><div class="stats">' + "".join(stats) + '</div><p class="explanation">Counts overlap: check counts and requirement counts measure different things. Excluded failures remain counted.</p><p class="originals">' + esc(value.get("originals_notice", ORIGINALS_NOTICE)) + '</p>'
    if actions:
        page += '<section class="group actions"><h2>Outstanding actions</h2><ul>' + "".join(actions) + '</ul></section>'
    page += '<section class="group"><h2>Scope &amp; review</h2>' + "".join(sections) + '</section><section class="group"><h2>Supporting file inventory</h2><ul class="file-list">' + "".join(file_html) + '</ul></section><footer class="footer"><p>Schema ' + esc(value.get("schema_version", "legacy")) + ' · ' + esc(identity) + '</p><p>Checksums identify content; they are not signatures, proof of client approval or trusted timestamps.</p></footer></main></body></html>'
    rendered = {"json": json.dumps(value, ensure_ascii=False, indent=2), "md": "\n".join(md), "html": page}
    if any(len(content.encode()) > LIMITS["export_bytes"] for content in rendered.values()):
        raise StoreError("export_limit", "Export exceeds the text size limit.", 413)
    return rendered
