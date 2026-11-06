"""Synthetic five-file agency packet: technical facts never stand in for judgment."""
import io

from fastapi.testclient import TestClient
from PIL import Image
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from handoffready.api import create_app
from handoffready.delivery import DeliveryBinding
from test_api import create, mutate
from test_delivery_api import CONFIG, bound_job, scoped


def png(color, size=(1200, 1200)):
    output = io.BytesIO()
    Image.new("RGB", size, color).save(output, format="PNG")
    return output.getvalue()


def pdf():
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})})
    content = DecodedStreamObject()
    content.set_data(b"BT /F1 12 Tf 30 260 Td (Synthetic reference sheet) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(content)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def test_five_file_packet_duplicate_wrong_size_irrelevant_guide_and_correction(tmp_path):
    app = create_app(tmp_path, delivery_config=CONFIG)
    with TestClient(app, base_url="http://127.0.0.1:8877") as desk:
        desk.headers.update({"X-Handoff-Token": app.state.token, "Origin": "http://127.0.0.1:8877"})
        project = create(desk)
        project = mutate(desk, project, "put", "/brief", {"text": "Supply three distinct 1200-square PNG launch assets, a one-page sheet and a contact settings guide. Confirm whether the logo counts as a launch asset.", "source_label": "Synthetic agency brief"})
        requirements = [
            {"id": "images", "title": "Three launch assets", "origin": "human_added", "human_note": "Synthetic fixture; visual meaning and logo scope need a person", "checks": [
                {"kind": "count", "types": ["png"], "value": 3, "comparison": "exact", "distinct_bytes": False},
                {"kind": "count", "types": ["png"], "value": 3, "comparison": "exact", "distinct_bytes": True},
                {"kind": "image_dimensions", "width_px": 1200, "height_px": 1200},
                {"kind": "manual", "instruction": "Determine whether the designs fulfill the agreed purposes, including whether a logo belongs in this set."},
            ]},
            {"id": "sheet", "title": "One-page reference sheet", "origin": "human_added", "human_note": "Page count only; content not certified", "checks": [{"kind": "pdf_pages", "value": 1, "comparison": "exact"}]},
            {"id": "guide", "title": "Contact settings guide", "origin": "human_added", "human_note": "Presence of a literal is insufficient to prove useful instructions", "checks": [{"kind": "literal_text", "needle": "Contact settings"}, {"kind": "manual", "instruction": "Try the instructions and check that a colleague can follow them."}]},
        ]
        project = mutate(desk, project, "put", "/baseline", {"requirements": requirements})
        project = mutate(desk, project, "post", "/baseline/approve", {"baseline_hash": project["baseline"]["hash"], "reviewed_requirement_ids": ["images", "sheet", "guide"]})
        first = png("#274537")
        result = desk.post(f'/api/v1/projects/{project["id"]}/files', headers={"If-Match": str(project["revision"])}, files=[
            ("files[]", ("launch-01.png", first)),
            ("files[]", ("launch-02.png", first)),
            ("files[]", ("launch-03.png", png("#eed8bd", (600, 600)))),
            ("files[]", ("sheet.pdf", pdf())),
            ("files[]", ("guide.md", b"# Welcome\nThis is an unrelated welcome note.")),
        ])
        assert result.status_code == 201, result.text
        project = result.json()["data"]
        assert len(project["files"]) == 5
        job = bound_job(desk, project)
        operator_token = desk.headers["X-Handoff-Token"]
        scoped(desk)

        def preview(requirement, current, types):
            ids = [row["id"] for row in current["files"] if row["type"] in types]
            response = desk.post(f"/api/v1/delivery/jobs/{job}/preview", json={"requirement_id": requirement, "file_ids": ids, "expected_revision": current["revision"], "input_hash": current["input_hash"]})
            assert response.status_code == 200, response.text
            return response.json()["data"]

        initial_images = preview("images", project, {"png"})
        assert [check["status"] for check in initial_images["checks"]] == ["pass", "fail", "fail", "unknown"]
        assert initial_images["checks"][0]["actual"] == 3
        assert initial_images["checks"][1]["actual"] == 2
        assert preview("sheet", project, {"pdf"})["checks"][0]["status"] == "pass"
        assert preview("guide", project, {"markdown"})["checks"][0]["status"] == "fail"
        assert app.state.store.get(project["id"])["decisions"] == []

        desk.headers["X-Handoff-Token"] = operator_token
        for name, content in [
            ("launch-02.png", png("#d8e4da")),
            ("launch-03.png", png("#eed8bd")),
            ("guide.md", b"# Guide\nOpen Contact settings, change the email, publish, and send a test message."),
        ]:
            file_id = next(row["id"] for row in project["files"] if row["name"] == name)
            response = desk.post(f'/api/v1/projects/{project["id"]}/files/{file_id}/replacement', headers={"If-Match": str(project["revision"])}, files={"file": (name, content)})
            assert response.status_code == 201, response.text
            project = response.json()["data"]
        desk.headers.pop("X-Handoff-Token")
        corrected_images = preview("images", project, {"png"})
        assert [check["status"] for check in corrected_images["checks"]] == ["pass", "pass", "pass", "unknown"]
        corrected_guide = preview("guide", project, {"markdown"})
        assert [check["status"] for check in corrected_guide["checks"]] == ["pass", "unknown"]
        assert app.state.store.get(project["id"])["decisions"] == []
        assert app.state.delivery_service.status(job, DeliveryBinding(CONFIG["server"], CONFIG["room"]))["state"] == "human_review"
