"""Read-only file inspection; call only inside the service's bounded worker.

The decoded PDF budget is checked after decompression. It is not a memory sandbox:
resource/time limits must surround this module, including native image decoders.
"""
from __future__ import annotations

import math
import re
import warnings
from pathlib import Path

from defusedxml import ElementTree
from PIL import Image
from pypdf import PdfReader, __version__ as PDF_EXTRACTOR_VERSION
from pypdf.generic import ArrayObject, StreamObject

INSPECTOR_REVISION = "inspect-v1"
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_TEXT_BYTES = 1024 * 1024
MAX_TEXT_CHARS = 20_000
MAX_IMAGE_PIXELS = 10_000_000
MAX_IMAGE_SIDE = 10_000
MAX_PDF_PAGES = 10
MAX_PAGE_DECODED = 5 * 1024 * 1024
MAX_PDF_DECODED = 20 * 1024 * 1024
EXTENSIONS = {".png": "png", ".jpg": "jpeg", ".jpeg": "jpeg", ".svg": "svg", ".pdf": "pdf", ".txt": "text", ".md": "markdown"}


class InspectionBlocked(ValueError):
    pass


def _normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _inspect_image(path: Path, actual: str) -> tuple[dict, str]:
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(path) as image:
            if image.format not in {"PNG", "JPEG"}:
                raise InspectionBlocked("The image decoder did not identify PNG or JPEG bytes.")
            if image.format.lower() != actual:
                raise InspectionBlocked("The image signature and decoded format disagree.")
            width, height = image.size
            if width <= 0 or height <= 0 or width > MAX_IMAGE_SIDE or height > MAX_IMAGE_SIDE or width * height > MAX_IMAGE_PIXELS:
                raise InspectionBlocked("Image exceeds 10 megapixels or 10,000 pixels per side.")
            if getattr(image, "n_frames", 1) != 1:
                raise InspectionBlocked("Animated or multiple-frame images are unsupported.")
            image.verify()
        with Image.open(path) as image:
            image.load()  # Metadata alone cannot certify valid decoded image bytes.
            metadata = {"width_px": width, "height_px": height, "format": actual, "frames": 1}
            if actual == "png":
                alpha = image.convert("RGBA").getchannel("A")
                minimum, maximum = alpha.getextrema()
                metadata.update({"nonopaque_pixels": minimum < 255, "alpha_min": minimum, "alpha_max": maximum})
            return metadata, ""


def _pixel_length(value: str | None) -> float | None:
    if value is None:
        return None
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?|\.\d+)\s*(?:px)?\s*", value)
    if not match:
        return None
    number = float(match.group(1))
    return number if math.isfinite(number) and number > 0 else None


def _inspect_svg(data: bytes) -> tuple[dict, str]:
    decoded = data.decode("utf-8", errors="strict")
    if re.search(r"<\?xml-stylesheet\b", decoded, flags=re.I):
        raise InspectionBlocked("SVG stylesheet processing instructions are unsupported.")
    root = ElementTree.fromstring(data, forbid_dtd=True, forbid_entities=True, forbid_external=True)
    if root.tag not in {"svg", "{http://www.w3.org/2000/svg}svg"}:
        raise InspectionBlocked("XML root is not an SVG element.")
    count = 0
    for element in root.iter():
        count += 1
        if count > 20_000:
            raise InspectionBlocked("SVG exceeds the 20,000-element metadata inspection budget.")
        tag = element.tag.rsplit("}", 1)[-1].lower()
        if tag in {"script", "foreignobject", "iframe", "object", "embed"}:
            raise InspectionBlocked("SVG contains active or embedded content; metadata inspection was blocked.")
        for name, value in element.attrib.items():
            attribute = name.rsplit("}", 1)[-1].lower()
            if attribute.startswith("on"):
                raise InspectionBlocked("SVG contains an event handler.")
            if attribute in {"href", "src", "base"} and value and not value.startswith("#"):
                raise InspectionBlocked("SVG references an external or embedded resource.")
            if re.search(r"url\s*\(|@import", value, flags=re.I):
                raise InspectionBlocked("SVG CSS resource references are unsupported.")
        if tag == "style" and re.search(r"url\s*\(|@import", element.text or "", flags=re.I):
            raise InspectionBlocked("SVG CSS resource references are unsupported.")
    metadata = {"width_px": _pixel_length(root.get("width")), "height_px": _pixel_length(root.get("height")), "metadata_only": True}
    if root.get("viewBox"):
        values = [float(value) for value in re.split(r"[\s,]+", root.get("viewBox").strip())]
        if len(values) != 4 or not all(math.isfinite(value) for value in values) or values[2] <= 0 or values[3] <= 0:
            raise InspectionBlocked("SVG viewBox is invalid.")
        metadata["view_box"] = values
    return metadata, ""


def _pdf_stream_bytes(page) -> int:
    """Count decoded page/Form streams before text extraction, including nested Forms."""
    seen: set[int] = set()
    nodes = 0
    total = 0

    def visit(value, depth: int = 0) -> None:
        nonlocal nodes, total
        if value is None:
            return
        nodes += 1
        if nodes > 1000 or depth > 20:
            raise InspectionBlocked("PDF content resource graph exceeds inspection limits.")
        value = value.get_object() if hasattr(value, "get_object") else value
        if id(value) in seen:
            return
        seen.add(id(value))
        if isinstance(value, ArrayObject):
            for item in value:
                visit(item, depth + 1)
        elif isinstance(value, StreamObject):
            total += len(value.get_data())
            if total > MAX_PAGE_DECODED:
                raise InspectionBlocked("PDF decoded content exceeds 5 MiB on a page.")
            resources(value.get("/Resources"), depth + 1)

    def resources(value, depth: int) -> None:
        if value is None:
            return
        value = value.get_object()
        objects = value.get("/XObject")
        if objects:
            for reference in objects.get_object().values():
                obj = reference.get_object()
                if obj.get("/Subtype") == "/Form":
                    visit(obj, depth + 1)

    visit(page.get("/Contents"))
    resources(page.get("/Resources"), 0)
    return total


def _inspect_pdf(path: Path) -> tuple[dict, str]:
    reader = PdfReader(path, strict=True)
    if reader.is_encrypted:
        raise InspectionBlocked("Encrypted PDFs are unsupported, including empty-password PDFs.")
    pages = len(reader.pages)
    if not 1 <= pages <= MAX_PDF_PAGES:
        raise InspectionBlocked("PDF must have between 1 and 10 pages.")
    decoded = 0
    parts: list[str] = []
    sources: list[dict] = []
    chars = 0
    for number, page in enumerate(reader.pages, start=1):
        decoded += _pdf_stream_bytes(page)
        if decoded > MAX_PDF_DECODED:
            raise InspectionBlocked("PDF decoded content exceeds 20 MiB in total.")
        text = _normalize_text(page.extract_text() or "")
        separator = "\n\n" if parts else ""
        start = chars + len(separator)
        chars = start + len(text)
        if chars > MAX_TEXT_CHARS:
            raise InspectionBlocked("Extracted PDF text exceeds 20,000 characters; no partial text was retained.")
        parts.append(text)
        sources.append({"page": number, "start": start, "end": chars})
    text = "\n\n".join(parts)
    if not text.strip():
        raise InspectionBlocked("PDF has no extractable native text. Scanned PDFs and OCR are unsupported.")
    return {"pages": pages, "source_units": sources, "decoded_content_bytes": decoded, "extractor": "pypdf-native-text", "extractor_version": PDF_EXTRACTOR_VERSION}, text


def inspect_file(path: Path, name: str) -> dict:
    """Inspect a regular file without writing, executing or resolving network content.

    Blocked output never contains partial text or technical properties that could be
    mistaken for a successful inspection. `type` remains the detected actual type.
    """
    path = Path(path)
    actual = "unsupported"
    try:
        if path.is_symlink() or not path.is_file():
            raise InspectionBlocked("Inspection requires a regular, non-symlink file.")
        size = path.stat().st_size
        if size == 0 or size > MAX_FILE_BYTES:
            raise InspectionBlocked("File is empty or exceeds the 10 MiB file limit.")
        extension = Path(name).suffix.lower()
        declared = EXTENSIONS.get(extension)
        with path.open("rb") as handle:
            header = handle.read(32)
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            actual = "png"
        elif header.startswith(b"\xff\xd8\xff"):
            actual = "jpeg"
        elif header.startswith(b"%PDF-"):
            actual = "pdf"
        elif declared in {"svg", "text", "markdown"}:
            actual = declared
        else:
            raise InspectionBlocked("Unsupported file signature or extension.")
        if actual != declared:
            raise InspectionBlocked(f"File extension mismatch: decoded bytes identify {actual}, not {declared or 'a supported declared type'}.")
        if actual in {"png", "jpeg"}:
            metadata, text = _inspect_image(path, actual)
        elif actual == "pdf":
            metadata, text = _inspect_pdf(path)
        else:
            if size > MAX_TEXT_BYTES:
                raise InspectionBlocked("TXT, Markdown and SVG files must not exceed 1 MiB.")
            data = path.read_bytes()
            if actual == "svg":
                metadata, text = _inspect_svg(data)
            else:
                text = _normalize_text(data.decode("utf-8", errors="strict"))
                if "\x00" in text:
                    raise InspectionBlocked("Text contains null bytes and is not supported plain text.")
                if len(text) > MAX_TEXT_CHARS:
                    raise InspectionBlocked("Text exceeds 20,000 characters; no partial text was retained.")
                if not text.strip():
                    raise InspectionBlocked("Text file is empty after decoding.")
                metadata = {"encoding": "utf-8", "characters": len(text)}
        return {"type": actual, "inspection": "inspected", "metadata": metadata, "text": text, "error": None}
    except InspectionBlocked as error:
        reason = str(error)
    except Exception as error:
        # Do not expose uploaded content, local paths or parser tracebacks in UI.
        reason = f"File could not be safely inspected ({type(error).__name__})."
    return {"type": actual, "inspection": "blocked", "metadata": {}, "text": "", "error": reason}
