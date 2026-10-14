# Local recorded walkthrough

The video is an **edited walkthrough assembled from actual captured HandoffReady app screens**, with readable holds and captions. It is not a continuous screen recording. The example packet and agent-operated review decisions are explicitly synthetic; its files, real parser findings, actual local model proposals and explicit review decisions can be shown without customer data. Captions must describe what the corresponding captured screen actually establishes. No invented UI, model response, customer feedback, generated voice, music or paid service is used.

## Inputs and output

Capture the actual browser stages into `outputs/HANDOFFREADY-DEMO/frames/`, then write `outputs/HANDOFFREADY-DEMO/manifest.json`. Captures may have different geometry. The assembler letterboxes them without cropping, with disclosure above and captions below. Source screenshots are read only; their SHA-256 hashes are verified again after encoding.

Every encoded frame displays:

> Actual app captures · edited walkthrough · agent-operated synthetic demo

Prefer approximately 6–10 seconds per screen and captions of one or two concise lines. For dense evidence, hold longer or capture a focused actual view. Captions should avoid interpreting a model suggestion as acceptance, or claiming that a technical property proves visual/guide quality. Let the final client preview show truthful gaps.

Suggested sequence, using only stages actually captured: local home/sample label; agreed brief; actual local extraction result; human checklist review; inspected packet; local matching suggestions; opaque PNG finding/visual review; duplicate-byte count; incomplete-guide human decision; current client preview and immutable export. A missing stage should be omitted, not synthesized.

## Manifest schema

```json
{
  "title": "HandoffReady local walkthrough",
  "recording_type": "captured_screens_walkthrough",
  "width": 1920,
  "height": 1200,
  "fps": 24,
  "slides": [
    {
      "image": "frames/01-home.png",
      "duration_seconds": 7,
      "caption": "A local delivery desk for web and design freelancers. Synthetic sample shown."
    },
    {
      "image": "frames/02-brief.png",
      "duration_seconds": 8,
      "caption": "Start from the saved brief. Review the agreed scope yourself."
    }
  ]
}
```

The example names are placeholders for actual capture paths, not supplied screens. `recording_type` is mandatory. Dimensions default to 1920×1200 and must be even: width 640–3840, height 480–2160. Frame rate defaults to 24 (allowed 1–60). Each slide requires a static PNG/JPEG path inside the manifest directory, 1–90 seconds of hold, and a 1–180-character caption that fits within two rendered lines. The assembler rounds each hold to the nearest frame. Limits: 1–40 slides, ten minutes total, 50 MiB and 20 million pixels per capture. `title` is receipt metadata; it is not overlaid on the app screen.

## Free offline tooling

Pillow is already pinned in the application's Python environment. The assembler uses the pinned `imageio-ffmpeg` 0.6.0 Python package to access its bundled FFmpeg executable. Install it into the ignored isolated tool directory:

```sh
uv pip install --python .venv/bin/python --target .runtime/demo-tools imageio-ffmpeg==0.6.0
```

If `uv` is unavailable, the equivalent isolated pip target is:

```sh
.venv/bin/python -m pip install --target .runtime/demo-tools imageio-ffmpeg==0.6.0
```

Installation requires a registry download; assembly is offline. The tested Apple Silicon wheel contains FFmpeg 7.1 with libx264. Its build reports `--enable-gpl`; the tooling has its own licenses. It stays in `.runtime/` and is not included in a source release. No runtime executable is embedded in the MP4. Other OS wheels may contain a different FFmpeg build and need separate verification. The package's local license is `.runtime/demo-tools/imageio_ffmpeg-0.6.0.dist-info/LICENSE`.

The assembler uses the local Helvetica font on the tested Mac, or DejaVu/Liberation/Arial when present on other systems. If none is present, Pillow's built-in font is used. No font download or font-file redistribution occurs.

## Assemble and verify

From the repository root:

```sh
.venv/bin/python scripts/assemble_demo.py outputs/HANDOFFREADY-DEMO/manifest.json
```

Default outputs beside the manifest:

- `walkthrough.mp4`: silent H.264/yuv420p video with constant frame rate and web-friendly fast-start metadata.
- `walkthrough.poster.png`: assembled first frame for a local preview; it is a derivative, not an original screenshot.
- `walkthrough.verification.json`: source hashes, manifest/video hash, encoded metadata, decoded frame count, duration and captions.

Choose a specific video name with `--output outputs/HANDOFFREADY-DEMO/HandoffReady-walkthrough.mp4`. Existing video/poster/receipt files are protected unless `--overwrite` is explicitly supplied. Source captures and the manifest can never be output targets. Encoding uses a temporary file; a failed verification does not replace the named video.

The assembler decodes the first frame, confirms frame geometry and H.264/frame rate, decodes/counts all frames, and verifies duration against the sum of frame-rounded holds. It also confirms that source bytes stayed unchanged. These checks establish file integrity and geometry, not narrative accuracy or full visual readability. Open the poster and play the final video to inspect caption size, screen readability and truthful sequencing before sharing.

Only a completed receipt with matching source/video hashes is assembly evidence. A tooling smoke check using a previous actual screenshot is separate from the final demo and must not be presented as a complete current workflow. The video remains local; assembly does not upload, publish or submit it.

## Assembler verification record

14 October 2026 IST: two local smoke encodes used a copy of the existing actual app capture `docs/screenshots/local-demo-home.png`, explicitly captioned as assembler verification rather than the final current workflow. Both decoded **48 frames / 2.00 seconds at 24 fps**, with H.264/yuv420p metadata, the declared geometry and unchanged capture hashes. Checked geometries: **1920×1200** and **1000×1200**. The portrait poster was visually inspected: a 153-character caption fit two readable lines below the complete uncropped screenshot. Receipts are separate under `outputs/HANDOFFREADY-DEMO/assembler-check/`.

For the current approximately 753×853 browser viewport captures, **1000×1200** is the selected final geometry: it fits the actual screen more closely than a landscape canvas. Do not enlarge or recapture the browser solely to create a different screenshot geometry. The manifest can select this portrait size directly. These smoke checks validate the assembler, not the final screenshot sequence; that sequence still needs its own encoding receipt and visual review.
