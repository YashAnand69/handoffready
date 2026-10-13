"""Byte-level regression cases for the public inspector contract."""

import pytest
from PIL import Image
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

from handoffready.inspect import inspect_file


def write_image(path, mode="RGBA", alpha=255, size=(25, 30), format="PNG"):
    Image.new(mode, size, (40, 70, 50, alpha) if mode == "RGBA" else (40, 70, 50)).save(path, format=format)
    return path


def write_pdf(path, text="Change the contact email in Settings.", pages=1, encrypt=False, stream_bytes=None):
    writer = PdfWriter()
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
    font_ref = writer._add_object(font)
    for _ in range(pages):
        page = writer.add_blank_page(width=300, height=400)
        page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})})
        content = DecodedStreamObject()
        content.set_data(stream_bytes if stream_bytes is not None else f"BT /F1 12 Tf 10 300 Td ({text}) Tj ET".encode("ascii"))
        page[NameObject("/Contents")] = writer._add_object(content.flate_encode())
    if encrypt:
        writer.encrypt("")
    writer.write(path)
    return path


def assert_blocked(result, reason=None):
    assert result["inspection"] == "blocked"
    assert result["text"] == ""
    assert result["metadata"] == {}
    if reason:
        assert reason in result["error"]


def test_decodes_dimensions_and_detects_opaque_alpha(tmp_path):
    path = write_image(tmp_path / "logo.png")
    result = inspect_file(path, "logo.png")
    assert result["inspection"] == "inspected"
    assert result["metadata"]["width_px"] == 25
    assert result["metadata"]["height_px"] == 30
    assert result["metadata"]["nonopaque_pixels"] is False


def test_transparency_requires_decoded_pixels_and_handles_palette(tmp_path):
    image = Image.new("P", (8, 8), 1)
    image.putpalette([0, 0, 0, 70, 80, 90] + [0] * 762)
    image.putpixel((0, 0), 0)
    path = tmp_path / "palette.png"
    image.save(path, transparency=0)
    result = inspect_file(path, path.name)
    assert result["inspection"] == "inspected"
    assert result["metadata"]["nonopaque_pixels"] is True
    assert result["metadata"]["alpha_min"] == 0


def test_jpeg_renamed_as_png_cannot_pass_png_check(tmp_path):
    path = write_image(tmp_path / "logo.png", mode="RGB", format="JPEG")
    result = inspect_file(path, path.name)
    assert result["type"] == "jpeg"
    assert_blocked(result, "mismatch")


def test_truncated_png_is_not_inspected(tmp_path):
    path = write_image(tmp_path / "logo.png")
    path.write_bytes(path.read_bytes()[:40])
    assert_blocked(inspect_file(path, path.name))


@pytest.mark.parametrize("size", [(10_001, 1), (4000, 2501)])
def test_image_side_and_pixel_caps(tmp_path, size):
    path = write_image(tmp_path / "large.png", mode="RGB", size=size)
    assert_blocked(inspect_file(path, path.name), "10 megapixels")


def test_animated_png_blocked(tmp_path):
    path = tmp_path / "animated.png"
    first = Image.new("RGB", (10, 10), "red")
    first.save(path, save_all=True, append_images=[Image.new("RGB", (10, 10), "blue")], duration=100, loop=0)
    assert_blocked(inspect_file(path, path.name), "multiple-frame")


def test_text_canonicalization_preserves_unicode_and_markup(tmp_path):
    path = tmp_path / "guide.md"
    path.write_bytes("<script>not executed</script>\r\n😀 e\u0301\rEnd".encode("utf-8"))
    result = inspect_file(path, path.name)
    assert result["text"] == "<script>not executed</script>\n😀 e\u0301\nEnd"
    assert result["metadata"]["characters"] == len(result["text"])


@pytest.mark.parametrize("content", [b"\xff", b"hello\x00world", b" \r\n\t"])
def test_invalid_plain_text_is_blocked(tmp_path, content):
    path = tmp_path / "guide.txt"
    path.write_bytes(content)
    assert_blocked(inspect_file(path, path.name))


def test_text_limit_exact_boundary_and_no_partial_overflow(tmp_path):
    path = tmp_path / "guide.txt"
    path.write_text("😀" * 20_000, encoding="utf-8")
    assert inspect_file(path, path.name)["inspection"] == "inspected"
    path.write_text("😀" * 20_001, encoding="utf-8")
    assert_blocked(inspect_file(path, path.name), "20,000")


def test_text_raw_byte_cap(tmp_path):
    path = tmp_path / "guide.txt"
    path.write_bytes(b"a" * (1024 * 1024 + 1))
    assert_blocked(inspect_file(path, path.name), "1 MiB")


def test_svg_metadata_not_rendered_or_text_extracted(tmp_path):
    path = tmp_path / "logo.svg"
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1080px" height="100%" viewBox="0 0 1080 1080"><text>Private</text></svg>', encoding="utf-8")
    result = inspect_file(path, path.name)
    assert result["inspection"] == "inspected"
    assert result["metadata"]["width_px"] == 1080
    assert result["metadata"]["height_px"] is None
    assert result["metadata"]["metadata_only"] is True
    assert result["text"] == ""


@pytest.mark.parametrize("content", [
    '<!DOCTYPE svg [<!ENTITY read SYSTEM "file:///etc/passwd">]><svg>&read;</svg>',
    '<svg><script>alert(1)</script></svg>',
    '<?xml-stylesheet href="https://example.com/style.css"?><svg/>',
    '<svg><rect onclick="alert(1)"/></svg>',
    '<svg><image href="https://example.com/image.png"/></svg>',
    '<svg><image href="data:image/png;base64,AA"/></svg>',
    '<svg><style>@import "https://example.com/style.css";</style></svg>',
    '<svg><rect style="fill:url(https://example.com/a)"/></svg>',
    '<svg viewBox="0 0 NaN 10"/>',
    '<svg><foreignObject/></svg>',
    '<html/>',
])
def test_svg_untrusted_content_is_blocked(tmp_path, content):
    path = tmp_path / "logo.svg"
    path.write_text(content, encoding="utf-8")
    assert_blocked(inspect_file(path, path.name))


def test_native_pdf_page_sources_are_exact(tmp_path):
    path = write_pdf(tmp_path / "guide.pdf", pages=2)
    result = inspect_file(path, path.name)
    assert result["inspection"] == "inspected"
    assert result["metadata"]["pages"] == 2
    assert result["metadata"]["extractor_version"]
    for source in result["metadata"]["source_units"]:
        assert result["text"][source["start"]:source["end"]] == "Change the contact email in Settings."


@pytest.mark.parametrize("kwargs, reason", [
    ({"pages": 11}, "10 pages"),
    ({"encrypt": True}, "Encrypted"),
    ({"text": ""}, "no extractable"),
    ({"text": "a" * 20_001}, "20,000"),
    ({"stream_bytes": b" " * (5 * 1024 * 1024 + 1)}, "5 MiB"),
])
def test_pdf_limits_never_publish_partial_content(tmp_path, kwargs, reason):
    path = write_pdf(tmp_path / "guide.pdf", **kwargs)
    assert_blocked(inspect_file(path, path.name), reason)


def test_pdf_total_decoded_cap(tmp_path):
    path = write_pdf(tmp_path / "guide.pdf", pages=5, stream_bytes=b" " * (4 * 1024 * 1024 + 1))
    assert_blocked(inspect_file(path, path.name), "20 MiB")


def test_regular_file_and_supported_extension_required(tmp_path):
    path = tmp_path / "guide.txt"
    path.write_text("Guide", encoding="utf-8")
    link = tmp_path / "link.txt"
    link.symlink_to(path)
    assert_blocked(inspect_file(link, link.name), "non-symlink")
    assert_blocked(inspect_file(path, "guide.html"), "Unsupported")
    assert path.read_text() == "Guide"


@pytest.mark.parametrize("size", [(10_000, 1), (4000, 2500)])
def test_image_caps_allow_exact_boundary(tmp_path, size):
    path = write_image(tmp_path / "boundary.png", mode="RGB", size=size)
    assert inspect_file(path, path.name)["inspection"] == "inspected"


def test_partial_alpha_is_reported_as_nonopaque_not_proof_of_background_removal(tmp_path):
    path = write_image(tmp_path / "partial.png", alpha=128)
    result = inspect_file(path, path.name)
    assert result["metadata"]["nonopaque_pixels"] is True
    assert result["metadata"]["alpha_min"] == 128


def test_jpeg_does_not_claim_png_transparency(tmp_path):
    path = write_image(tmp_path / "photo.jpg", mode="RGB", format="JPEG")
    result = inspect_file(path, path.name)
    assert result["inspection"] == "inspected"
    assert result["type"] == "jpeg"
    assert "nonopaque_pixels" not in result["metadata"]


def test_svg_local_reference_does_not_fetch_any_resource(tmp_path):
    path = tmp_path / "logo.svg"
    path.write_text('<svg width="10" height="10"><defs><path id="shape" d="M0 0L10 10"/></defs><use href="#shape"/></svg>', encoding="utf-8")
    assert inspect_file(path, path.name)["inspection"] == "inspected"


def test_pdf_nested_form_content_is_budgeted_before_extraction(tmp_path):
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=400)
    form = DecodedStreamObject()
    form.set_data(b" " * (5 * 1024 * 1024 + 1))
    form[NameObject("/Subtype")] = NameObject("/Form")
    reference = writer._add_object(form.flate_encode())
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/XObject"): DictionaryObject({NameObject("/Fm"): reference})})
    content = DecodedStreamObject()
    content.set_data(b"/Fm Do")
    page[NameObject("/Contents")] = writer._add_object(content)
    path = tmp_path / "nested.pdf"
    writer.write(path)
    assert_blocked(inspect_file(path, path.name), "5 MiB")


def test_empty_and_overbudget_files_are_not_partially_read(tmp_path):
    path = tmp_path / "large.pdf"
    path.touch()
    assert_blocked(inspect_file(path, path.name), "empty")
    with path.open("wb") as handle:
        handle.write(b"%PDF-1.7\n")
        handle.truncate(10 * 1024 * 1024 + 1)
    assert_blocked(inspect_file(path, path.name), "10 MiB")
