"""Render a captioned current-UI walkthrough from preserved actual screenshots.

This is an edited, silent sequence, not a continuous session or inference video.
Uses the bounded manifest validation and decoder checks in assemble_demo.py.
No capture, model inference, network request, or publication occurs here.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import tempfile

from PIL import Image, ImageDraw, ImageOps

from assemble_demo import (
    DISCLOSURE,
    ffmpeg_module,
    font,
    load_manifest,
    sha256,
    verify_video,
    wrapped,
)


def timestamp(seconds: float, *, vtt: bool = False) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, remainder = divmod(remainder, 1000)
    if vtt:
        return f"{hours:02}:{minutes:02}:{seconds:02}.{remainder:03}"
    return f"{hours * 60 + minutes}:{seconds:02}"


def compose(capture, slide, width, height, index, total):
    """Frame the untouched capture; all editorial text remains outside its box."""
    canvas = Image.new("RGB", (width, height), "#f5f2e9")
    draw = ImageDraw.Draw(canvas)
    margin = round(width * .027)
    heading_size = round(width * .023)
    caption_font = font(round(width * .019))
    small = font(round(width * .0105))
    header_height = round(height * .095)
    footer_height = round(height * .15)
    phase = str(slide.get("phase", "Delivery review"))[:60]
    label = f"{index:02} / {total:02}   {phase}"
    draw.text((margin, round(height * .025)), "HANDOFFREADY", font=font(heading_size), fill="#183c2d")
    draw.text((width - margin, round(height * .035)), label, font=small,
              fill="#4b6053", anchor="ra")
    top = header_height
    area_height = height - top - footer_height - margin
    image = ImageOps.contain(capture["image"], (width - 2 * margin, area_height),
                            method=Image.Resampling.LANCZOS)
    x = (width - image.width) // 2
    y = top + (area_height - image.height) // 2
    draw.rounded_rectangle((x - 2, y - 2, x + image.width + 2, y + image.height + 2),
                           radius=4, fill="#cbd3c7")
    canvas.paste(image, (x, y))
    caption_y = height - footer_height + round(height * .012)
    lines = wrapped(draw, capture["caption"], caption_font, width - 2 * margin)
    for line in lines:
        draw.text((margin, caption_y), line, font=caption_font, fill="#173b2b")
        caption_y += round(caption_font.size * 1.35)
    draw.text((margin, height - round(height * .025)), DISCLOSURE,
              font=small, fill="#59685c", anchor="ld")
    progress_y = height - 5
    draw.rectangle((0, progress_y, round(width * index / total), height), fill="#a5ba73")
    return canvas


def write_player(directory, output, manifest, captures, fps):
    """Prepare a portable self-hosted player and equivalent text transcript."""
    chapters, transcript, elapsed = [], [], 0.0
    for index, (capture, slide) in enumerate(zip(captures, manifest["slides"], strict=True), 1):
        label = html.escape(str(slide.get("phase", f"Step {index}")))
        caption = html.escape(capture["caption"])
        chapters.append(f'<button type="button" data-time="{elapsed}"><span>{timestamp(elapsed)}</span>{label}</button>')
        transcript.append(f'<li><time>{timestamp(elapsed)}</time><p>{caption}</p></li>')
        elapsed += capture["frames"] / fps
    name = html.escape(output.name, quote=True)
    stem = html.escape(output.stem, quote=True)
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; img-src 'self'; media-src 'self'; style-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'">
<meta name="description" content="A current-interface walkthrough of HandoffReady's local delivery review, with actual synthetic app captures and explicit limitations.">
<title>HandoffReady — current-interface walkthrough</title><link rel="stylesheet" href="current-demo.css"><script src="current-demo.js" defer></script></head>
<body><a class="skip" href="#player">Skip to walkthrough</a><header><a class="brand" href="https://github.com/YashAnand69/handoffready">HandoffReady <span>DELIVERY DESK</span></a><a href="../">Project overview</a></header>
<main><section class="intro"><p class="eyebrow">A COMPLETE DELIVERY REVIEW</p><h1>The files you promised.<br>The handoff you can explain.</h1><p class="lead">Follow the current local interface from an agreed brief to a client record that keeps remaining work visible.</p><p class="notice"><strong>Edited actual app captures.</strong> This silent {timestamp(elapsed)} walkthrough uses a synthetic packet and agent-operated review decisions. It is not a continuous session or a recording of a new model run. No freelancer trial is claimed.</p></section>
<div class="layout"><section id="player" aria-label="Current-interface video"><video controls playsinline preload="metadata" poster="{stem}.poster.png" aria-label="HandoffReady edited current-interface walkthrough"><source src="{name}" type="video/mp4"><track kind="captions" src="{stem}.vtt" srclang="en" label="Workflow captions"><a href="{name}">Download the MP4</a></video><p id="playback-status" role="status">Silent edited walkthrough · {timestamp(elapsed)} · actual app captures</p><p><a href="{name}" download>Download MP4</a> · <a href="{stem}.transcript.md">Text transcript</a> · <a href="{stem}.verification.json">Encoding evidence</a></p></section>
<aside><p class="eyebrow">JUMP TO A STEP</p><nav aria-label="Video chapters">{''.join(chapters)}</nav></aside></div>
<section class="boundary"><h2>Keep the evidence in context.</h2><p>Gemma proposes requirements and file associations. Supported file checks establish narrow facts. An operator confirms the meaning, chooses the disposition and decides what to share. Changed inputs invalidate earlier reviews.</p><p>The full app runs locally. This public page plays recorded material and does not receive delivery files or run a model. A separate read-only explorer retains the actual saved records and earlier model findings.</p><p><a href="../explore/">Explore the recorded findings</a> · <a href="https://github.com/YashAnand69/handoffready#run-locally">Run the local app</a></p></section>
<details><summary>Read the full workflow transcript</summary><ol>{''.join(transcript)}</ol></details></main><footer>Synthetic demonstration · AI coding assistance disclosed · Source captures preserved and hashed</footer></body></html>'''
    (directory / "index.html").write_text(page, encoding="utf-8")
    (directory / "current-demo.css").write_text('''
:root{color-scheme:light;--paper:#f6f3eb;--ink:#173d2c;--muted:#596a60;--line:#cbd4c8}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.65 system-ui,sans-serif}a{color:inherit;text-underline-offset:4px}a:hover{color:#456a38}button,a,summary{touch-action:manipulation}a:focus-visible,button:focus-visible,summary:focus-visible,video:focus-visible{outline:3px solid #568b39;outline-offset:4px}.skip{position:absolute;top:-100px;left:20px;padding:10px;background:white}.skip:focus{top:10px;z-index:5}header,main,footer{max-width:1320px;margin:auto;padding:24px 40px}header{display:flex;justify-content:space-between;gap:20px;align-items:center;border-bottom:1px solid var(--line)}.brand{font-size:23px;text-decoration:none;font-weight:650}.brand span{font-size:10px;letter-spacing:.16em;display:block}.intro{max-width:920px;padding:30px 0}.eyebrow{font-size:11px;font-weight:700;letter-spacing:.18em}h1{font:clamp(36px,4.8vw,66px)/1.08 Georgia,serif;letter-spacing:-.035em;margin:20px 0}.lead{font-size:20px;max-width:740px}.notice{border-left:3px solid #97af6a;padding:14px 20px;background:#ebeede;color:#354f3d}.layout{display:grid;grid-template-columns:minmax(0,1fr) 250px;gap:28px;align-items:start}video{width:100%;display:block;background:#173d2c;border-radius:10px;border:1px solid var(--line)}#playback-status{font-size:13px;color:var(--muted)}aside nav{display:grid;gap:8px}button{font:inherit;display:flex;gap:12px;text-align:left;padding:12px;border:1px solid var(--line);border-radius:7px;background:#fffdf7;color:var(--ink);cursor:pointer}button:hover{background:#e8eddf}button span{font-variant-numeric:tabular-nums;font-size:12px;color:var(--muted)}.boundary{max-width:900px;padding:24px 0}h2{font:32px/1.2 Georgia,serif}details{border-top:1px solid var(--line);padding:20px 0}summary{cursor:pointer;font-weight:650}ol{padding:0;list-style:none;max-width:850px}li{display:flex;gap:20px;border-bottom:1px solid var(--line);padding:12px 0}li p{margin:0}time{color:var(--muted);font-variant-numeric:tabular-nums}footer{border-top:1px solid var(--line);font-size:12px;color:var(--muted)}@media(max-width:900px){.layout{grid-template-columns:1fr}aside nav{grid-template-columns:repeat(2,minmax(0,1fr))}header,main,footer{padding:20px}.intro{padding-top:10px}}@media(max-width:520px){aside nav{grid-template-columns:1fr}.lead{font-size:18px}header>a:last-child{font-size:12px}h1{font-size:39px}.notice{padding:12px 14px}}''', encoding="utf-8")
    (directory / "current-demo.js").write_text('''
"use strict";
const video = document.querySelector("video");
const status = document.querySelector("#playback-status");
document.querySelectorAll("[data-time]").forEach((button) => {
  button.addEventListener("click", () => {
    const position = Number(button.dataset.time);
    if (!Number.isFinite(position) || position < 0) return;
    video.currentTime = position;
    video.focus();
    status.textContent = `Selected ${button.textContent.trim()}. Press play to continue.`;
  });
});
video.addEventListener("error", () => {
  status.textContent = "The video could not be loaded. Read the complete transcript below or download the MP4.";
});
''', encoding="utf-8")


def assemble(manifest_path: Path, output: Path, overwrite: bool = False):
    manifest, captures, width, height, fps, frames, manifest_hash = load_manifest(manifest_path)
    if output.suffix.lower() != ".mp4":
        raise ValueError("Output must be an MP4 file.")
    targets = {
        "video": output,
        "poster": output.with_suffix(".poster.png"),
        "receipt": output.with_suffix(".verification.json"),
        "captions": output.with_suffix(".vtt"),
        "transcript": output.with_suffix(".transcript.md"),
    }
    if not overwrite and any(path.exists() for path in targets.values()):
        raise FileExistsError("An output already exists; choose a new output or pass --overwrite.")
    sources = {capture["path"] for capture in captures} | {manifest_path.resolve()}
    if any(path.resolve() in sources for path in targets.values()):
        raise ValueError("Outputs must never overwrite captures or the manifest.")
    ffmpeg = ffmpeg_module()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".mp4", dir=output.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
    writer = None
    try:
        writer = ffmpeg.write_frames(
            str(temporary_path), (width, height), fps=fps, codec="libx264", macro_block_size=2,
            output_params=["-preset", "veryfast", "-tune", "stillimage", "-crf", "18", "-movflags", "+faststart"],
            ffmpeg_log_level="error",
        )
        writer.send(None)
        poster, cues, transcript, elapsed = None, ["WEBVTT\n"], [], 0.0
        previous = None
        for index, (capture, slide) in enumerate(zip(captures, manifest["slides"], strict=True), 1):
            composed = compose(capture, slide, width, height, index, len(captures))
            if poster is None:
                poster = composed.copy()
            # The short crossfade is editorial; no fabricated intermediate app state.
            fade_frames = min(round(fps * .25), capture["frames"] // 4) if previous is not None else 0
            for frame in range(fade_frames):
                writer.send(Image.blend(previous, composed, (frame + 1) / fade_frames).tobytes())
            pixels = composed.tobytes()
            for _ in range(capture["frames"] - fade_frames):
                writer.send(pixels)
            previous = composed
            duration = capture["frames"] / fps
            cues.append(f"{index}\n{timestamp(elapsed, vtt=True)} --> {timestamp(elapsed + duration, vtt=True)}\n{capture['caption']}\n")
            transcript.append(f"- **{timestamp(elapsed)}** — {capture['caption']}")
            elapsed += duration
            print(f"Encoded actual capture {index}/{len(captures)} ({duration:g}s)", flush=True)
        writer.close()
        writer = None
        verification = verify_video(ffmpeg, temporary_path, width, height, fps, frames)
        for capture in captures:
            if sha256(capture["path"].read_bytes()) != capture["sha256"]:
                raise RuntimeError("A screenshot changed during encoding; output was not finalized.")
        temporary_path.replace(output)
        poster.save(targets["poster"])
        targets["captions"].write_text("\n".join(cues), encoding="utf-8")
        targets["transcript"].write_text(
            "# HandoffReady — current-interface walkthrough\n\n"
            f"{DISCLOSURE}. Silent edited screenshot sequence; not continuous footage or an inference recording.\n\n"
            + "\n".join(transcript) + "\n", encoding="utf-8",
        )
        receipt = {
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "title": manifest["title"], "recording_type": "captured_screens_walkthrough",
            "disclosure": DISCLOSURE, "silent": True, "continuous_recording": False,
            "model_inference_recording": False, "manifest_sha256": manifest_hash,
            "video": output.name, "video_sha256": sha256(output.read_bytes()),
            "bytes": output.stat().st_size, "poster": targets["poster"].name,
            "source_capture_bytes_preserved": True,
            "captures": [{"image": str(c["path"].relative_to(manifest_path.parent.resolve())),
                          "sha256": c["sha256"], "caption": c["caption"],
                          "frames": c["frames"], "duration_seconds": c["frames"] / fps}
                         for c in captures], **verification,
        }
        targets["receipt"].write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        write_player(output.parent, output, manifest, captures, fps)
        print(json.dumps({"video": str(output), "duration_seconds": elapsed,
                          "video_sha256": receipt["video_sha256"]}, indent=2))
    finally:
        if writer is not None:
            writer.close()
        temporary_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    manifest = args.manifest.resolve()
    try:
        assemble(manifest, (args.output or manifest.parent / "walkthrough.mp4").resolve(), args.overwrite)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Current demo assembly failed: {error}\n")


if __name__ == "__main__":
    main()
