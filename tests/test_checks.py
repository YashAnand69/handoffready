"""Format-specific checks apply to the intended format in a mixed deliverable."""
from handoffready.checks import evaluate
from handoffready.store import input_hash


def packet(kind, selected):
    project = {"brief": None, "baseline": {"hash": "test", "requirements": [{"id": "r", "checks": [{"kind": kind, "comparison": "exact", "value": 2}]}]}, "files": selected, "decisions": []}
    for index, file in enumerate(selected):
        file.update(id=str(index), name=f'{index}.{file["type"]}', inspection="inspected", text="", sha256=str(index))
    project["decisions"] = [{"requirement_id": "r", "file_ids": [f["id"] for f in selected], "review_state": "confirmed", "input_hash": input_hash(project)}]
    return project


def test_png_alpha_does_not_treat_required_svg_master_as_unknown():
    project = packet("png_nonopaque_pixels", [{"type": "png", "metadata": {"nonopaque_pixels": True}}, {"type": "svg", "metadata": {"metadata_only": True}}])
    assert evaluate(project)[0]["status"] == "pass"
    project["files"][0]["metadata"]["nonopaque_pixels"] = False
    project["decisions"][0]["input_hash"] = input_hash(project)
    assert evaluate(project)[0]["status"] == "fail"


def test_png_alpha_with_no_png_remains_unknown():
    assert evaluate(packet("png_nonopaque_pixels", [{"type": "svg", "metadata": {}}]))[0]["status"] == "unknown"


def test_pdf_pages_can_coexist_with_required_markdown_instructions():
    project = packet("pdf_pages", [{"type": "pdf", "metadata": {"pages": 2}}, {"type": "markdown", "metadata": {}}])
    assert evaluate(project)[0]["status"] == "pass"
    project["files"][0]["metadata"]["pages"] = 3
    project["decisions"][0]["input_hash"] = input_hash(project)
    assert evaluate(project)[0]["status"] == "fail"


def test_pdf_pages_with_no_pdf_remains_unknown():
    assert evaluate(packet("pdf_pages", [{"type": "markdown", "metadata": {}}]))[0]["status"] == "unknown"
