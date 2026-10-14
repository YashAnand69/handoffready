"""Encode an explicitly edited walkthrough from actual captured app screenshots.

Offline only. Never records a screen, alters original captures, or invents UI.
Pillow is in the backend environment; imageio-ffmpeg lives in .runtime/demo-tools.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".runtime" / "demo-tools"))
DISCLOSURE = "Actual app captures · edited walkthrough · agent-operated synthetic demo"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def font(size: int):
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default(size=size)


def bounded_int(value, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer from {low} to {high}.")
    return value


def load_manifest(path: Path):
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("recording_type") != "captured_screens_walkthrough":
        raise ValueError("Manifest must declare recording_type: captured_screens_walkthrough.")
    width = bounded_int(value.get("width", 1920), "width", 640, 3840)
    height = bounded_int(value.get("height", 1200), "height", 480, 2160)
    fps = bounded_int(value.get("fps", 24), "fps", 1, 60)
    if width % 2 or height % 2:
        raise ValueError("Video width and height must be even for H.264/yuv420p.")
    title = value.get("title", "HandoffReady")
    if not isinstance(title, str) or not title.strip() or len(title) > 120:
        raise ValueError("title must be nonempty text of at most 120 characters.")
    slides = value.get("slides")
    if not isinstance(slides, list) or not 1 <= len(slides) <= 40:
        raise ValueError("Provide 1–40 actual captured screens.")
    captures, frame_count = [], 0
    for index, slide in enumerate(slides, 1):
        if not isinstance(slide, dict):
            raise ValueError(f"Slide {index} must be an object.")
        filename = slide.get("image")
        caption = slide.get("caption")
        duration = slide.get("duration_seconds")
        if not isinstance(filename, str) or not filename:
            raise ValueError(f"Slide {index} needs a captured image path.")
        image_path = (path.parent / filename).resolve()
        if not image_path.is_relative_to(path.parent.resolve()):
            raise ValueError(f"Slide {index} image must remain within the manifest directory.")
        if image_path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            raise ValueError(f"Slide {index} must reference PNG/JPEG bytes.")
        if not isinstance(caption, str) or not caption.strip() or len(caption) > 180:
            raise ValueError(f"Slide {index} needs a concise caption of 1–180 characters.")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or not 1 <= duration <= 90:
            raise ValueError(f"Slide {index} duration must be 1–90 seconds.")
        frames = round(duration * fps)
        frame_count += frames
        data = image_path.read_bytes()
        if len(data) > 50 * 1024 * 1024:
            raise ValueError(f"Slide {index} capture exceeds 50 MiB.")
        with Image.open(BytesIO(data)) as source:
            if source.format not in {"PNG", "JPEG"} or getattr(source, "n_frames", 1) != 1:
                raise ValueError(f"Slide {index} is not a static PNG/JPEG capture.")
            if source.width * source.height > 20_000_000:
                raise ValueError(f"Slide {index} capture exceeds 20 million pixels.")
            image = ImageOps.exif_transpose(source).convert("RGB")
        captures.append({"path": image_path, "sha256": sha256(data), "image": image,
                         "caption": caption.strip(), "frames": frames,
                         "requested_duration_seconds": duration})
    if frame_count / fps > 600:
        raise ValueError("Walkthrough exceeds ten minutes; shorten the holds.")
    return value, captures, width, height, fps, frame_count, sha256(raw)


def wrapped(draw, text: str, selected_font, max_width: int):
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=selected_font) <= max_width:
            current = candidate
        else:
            if not current or draw.textlength(word, font=selected_font) > max_width:
                raise ValueError("Caption contains an overlong word; shorten it.")
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) > 2:
        raise ValueError("Caption exceeds two readable lines at this geometry; shorten it.")
    return lines


def compose(capture, width: int, height: int):
    canvas = Image.new("RGB", (width, height), "#14271e")
    draw = ImageDraw.Draw(canvas)
    header_height = max(42, round(height * 0.045))
    caption_height = max(94, round(height * 0.10))
    margin = max(12, round(width * 0.008))
    disclosure_font = font(max(12, round(width / 96)))
    while draw.textlength(DISCLOSURE, font=disclosure_font) > width - 2 * margin:
        disclosure_font = font(disclosure_font.size - 1)
    draw.text((margin, header_height / 2), DISCLOSURE, font=disclosure_font,
              fill="#e9eee8", anchor="lm")
    image_area_height = height - header_height - caption_height - 2 * margin
    resized = ImageOps.contain(capture["image"], (width - 2 * margin, image_area_height),
                               method=Image.Resampling.LANCZOS)
    x = (width - resized.width) // 2
    y = header_height + margin + (image_area_height - resized.height) // 2
    canvas.paste(resized, (x, y))
    caption_font = font(max(20, round(width / 64)))
    lines = wrapped(draw, capture["caption"], caption_font, width - 2 * margin)
    line_height = round(caption_font.size * 1.4)
    first_y = height - caption_height + (caption_height - len(lines) * line_height) // 2
    for index, line in enumerate(lines):
        draw.text((margin, first_y + index * line_height), line, font=caption_font,
                  fill="#fffefa")
    return canvas


def ffmpeg_module():
    try:
        import imageio_ffmpeg
    except ImportError as error:
        raise RuntimeError("Install imageio-ffmpeg==0.6.0 into .runtime/demo-tools; see docs/VIDEO-DEMO.md.") from error
    return imageio_ffmpeg


def verify_video(ffmpeg, path: Path, width: int, height: int, fps: int, expected_frames: int):
    reader = ffmpeg.read_frames(str(path))
    try:
        metadata = next(reader)
        first = next(reader)
        if len(first) != width * height * 3:
            raise RuntimeError("Decoded first frame has unexpected geometry.")
    finally:
        reader.close()
    frames, duration = ffmpeg.count_frames_and_secs(str(path))
    expected_duration = expected_frames / fps
    if tuple(metadata["source_size"]) != (width, height):
        raise RuntimeError("Encoded video geometry does not match the manifest.")
    if abs(metadata["fps"] - fps) > 0.01 or "h264" not in metadata["codec"]:
        raise RuntimeError("Expected H.264 video at the declared frame rate.")
    if frames != expected_frames or abs(duration - expected_duration) > max(0.1, 1 / fps):
        raise RuntimeError("Decoded frame count or duration differs from the declared holds.")
    return {"metadata": metadata, "decoded_frames": frames, "duration_seconds": duration,
            "expected_duration_seconds": expected_duration, "expected_frames": expected_frames}


def assemble(manifest_path: Path, output: Path, overwrite: bool):
    manifest, captures, width, height, fps, frames, manifest_hash = load_manifest(manifest_path)
    ffmpeg = ffmpeg_module()
    if output.suffix.lower() != ".mp4":
        raise ValueError("Output must use the .mp4 extension.")
    receipt_path = output.with_suffix(".verification.json")
    poster_path = output.with_suffix(".poster.png")
    if not overwrite and any(p.exists() for p in (output, receipt_path, poster_path)):
        raise FileExistsError("Output, poster or receipt already exists; choose a new name or pass --overwrite.")
    source_paths = {c["path"] for c in captures}
    if any(p.resolve() in source_paths or p.resolve() == manifest_path.resolve() for p in (output, receipt_path, poster_path)):
        raise ValueError("Outputs must never overwrite source captures or the manifest.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".mp4", dir=output.parent, delete=False) as pending:
        temporary_path = Path(pending.name)
    writer = None
    try:
        writer = ffmpeg.write_frames(str(temporary_path), (width, height), fps=fps,
                                     codec="libx264", macro_block_size=2,
                                     output_params=["-preset", "veryfast", "-tune", "stillimage",
                                                    "-crf", "18", "-movflags", "+faststart"],
                                     ffmpeg_log_level="error")
        writer.send(None)
        first_image = None
        for index, capture in enumerate(captures, 1):
            composed = compose(capture, width, height)
            if first_image is None:
                first_image = composed.copy()
            pixels = composed.tobytes()
            for _ in range(capture["frames"]):
                writer.send(pixels)
            print(f"Encoded capture {index}/{len(captures)} ({capture['frames'] / fps:.2f}s)", flush=True)
        writer.close()
        writer = None
        verification = verify_video(ffmpeg, temporary_path, width, height, fps, frames)
        for capture in captures:
            if sha256(capture["path"].read_bytes()) != capture["sha256"]:
                raise RuntimeError("A source capture changed during assembly; video was not finalized.")
        temporary_path.replace(output)
        first_image.save(poster_path)
        receipt = {"verified_at": datetime.now(timezone.utc).isoformat(), "title": manifest.get("title", "HandoffReady"),
                   "recording_type": "captured_screens_walkthrough", "disclosure": DISCLOSURE,
                   "silent": True, "manifest_sha256": manifest_hash, "video": output.name,
                   "video_sha256": sha256(output.read_bytes()), "bytes": output.stat().st_size,
                   "poster": poster_path.name, "source_capture_bytes_preserved": True,
                   "captures": [{"image": str(c["path"].relative_to(manifest_path.parent.resolve())),
                                  "sha256": c["sha256"], "caption": c["caption"],
                                  "frames": c["frames"], "duration_seconds": c["frames"] / fps}
                                 for c in captures], **verification}
        receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Verified {frames} frames · {frames / fps:.2f}s · {width}×{height} · H.264")
        print(output)
        print(receipt_path)
    finally:
        if writer is not None:
            writer.close()
        temporary_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, help="Default: walkthrough.mp4 beside manifest")
    parser.add_argument("--overwrite", action="store_true", help="Replace only the named generated outputs")
    args = parser.parse_args()
    manifest = args.manifest.resolve()
    output = (args.output or manifest.parent / "walkthrough.mp4").resolve()
    try:
        assemble(manifest, output, args.overwrite)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Demo assembly failed: {error}\n")


if __name__ == "__main__":
    main()
