"""Narrow deterministic facts; never infer aesthetic or contractual acceptance."""


def evaluate(project):
    from .store import input_hash
    current_hash = input_hash(project)
    files = {f["id"]: f for f in project["files"]}
    decisions = {d["requirement_id"]: d for d in project["decisions"]}
    results = []
    for requirement in project["baseline"]["requirements"]:
        decision = decisions.get(requirement["id"])
        selected = [files[i] for i in decision["file_ids"] if i in files] if decision else []
        for check in requirement["checks"]:
            result = {"requirement_id": requirement["id"], "kind": check["kind"], "status": "unknown", "reason": "Choose current files and review this mapping."}
            kind = check["kind"]
            if kind == "manual":
                result["reason"] = check["instruction"]
            elif not decision or decision["review_state"] != "confirmed" or decision["input_hash"] != current_hash or not selected:
                pass
            elif any(f["inspection"] != "inspected" for f in selected):
                result["reason"] = "A selected file could not be inspected. Review it manually."
            elif kind in {"presence", "count"}:
                supported = [f for f in selected if f["type"] in check["types"]]
                actual = len({f["sha256"] for f in supported}) if check.get("distinct_bytes") else len(supported)
                target = 1 if kind == "presence" else check["value"]
                good = actual >= target if kind == "presence" or check["comparison"] == "at_least" else actual == target
                result.update(status="pass" if good else "fail", reason="Selected inspected files counted; distinct bytes do not prove distinct designs.", expected=target, actual=actual)
            elif kind == "literal_text":
                text_files = [f for f in selected if f["text"]]
                if text_files:
                    found = any(check["needle"] in f["text"] for f in text_files)
                    result.update(status="pass" if found else "fail", reason="Case-sensitive literal text checked; this does not prove instructional quality.", expected=check["needle"], actual=found)
                else:
                    result["reason"] = "Selected files have no extractable text."
            elif kind == "image_dimensions":
                dimensions = [(f["metadata"].get("width_px"), f["metadata"].get("height_px")) for f in selected if f["type"] in {"png", "jpeg", "svg"}]
                if not dimensions or any(width is None or height is None for width, height in dimensions):
                    result["reason"] = "Dimensions are unavailable for at least one selected file."
                else:
                    expected = (check["width_px"], check["height_px"])
                    result.update(status="pass" if all(d == expected for d in dimensions) else "fail", reason="Encoded pixel dimensions checked for every selected file.", expected=list(expected), actual=[list(d) for d in dimensions])
            elif kind == "png_nonopaque_pixels":
                alpha = [f["metadata"].get("nonopaque_pixels") for f in selected if f["type"] == "png"]
                if not alpha or any(value is None for value in alpha):
                    result["reason"] = "This check requires inspected PNG files."
                else:
                    result.update(status="pass" if all(alpha) else "fail", reason="At least one nonopaque pixel per PNG; correct background removal still needs visual review.", actual=alpha)
            elif kind == "pdf_pages":
                pages = [f["metadata"].get("pages") for f in selected if f["type"] == "pdf"]
                if not pages or any(value is None for value in pages):
                    result["reason"] = "This check requires inspected PDFs."
                else:
                    good = all(value == check["value"] if check["comparison"] == "exact" else value >= check["value"] for value in pages)
                    result.update(status="pass" if good else "fail", reason="Native PDF page count checked for every selected PDF.", expected=check["value"], actual=pages)
            results.append(result)
    return results
