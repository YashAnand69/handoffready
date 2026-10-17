# Experience upgrade — 15 October 2026

This local checkpoint supersedes the earlier UI checkpoint, not its model evaluation. It has not been published or deployed.

## What changed

- Rebuilt the delivery desk with warm ivory and forest colors, editorial typography, a brief-to-record illustration, subtle transitions, responsive layouts and reduced-motion support.
- Saved projects resume at the next useful step. A suggested action guides the workflow.
- Review queues and selected files are searchable. Evidence and check findings precede the human assessment. Save and next advances only after a successful save and refresh.
- Search and filtering do not dirty the review. Clicking Continue on the current item preserves unsaved-edit protection; an independently reproduced regression is covered.
- File search, attention and duplicate filters make larger packets easier to inspect. Rename drafts survive filtering. Upload preflight explains count and size limits; backend inspection remains authoritative.
- A failed replacement preserves the original file, decisions, revision and exports. The rejected staged candidate is removed. Six regression cases cover recovery.
- Saved client records show the newest snapshot first with clearer download actions.

## Verified at this checkpoint

- 245 Python tests passed (including evaluation adapter tests).
- 71 frontend tests passed across seven files.
- TypeScript and production Vite build passed using Node 24.19.0. An earlier build passed under Node 20.18 but emitted Vite's unsupported-version warning; the final build uses the supported runtime.
- Frontend formatting, Ruff F/E9 and git whitespace checks passed.
- Live browser: saved sample resumed at its first attention item; duplicate filtering showed two of six files; client record retained gaps and immutable earlier records.
- Browser layout: home had no horizontal overflow at 390 and 1440 pixels; review at 390 and 320 pixels; files and handoff at 320 pixels. This is viewport testing, not physical-device validation.
- Screenshots: `screenshots/experience-home.png` and `screenshots/experience-mobile.png`.
- Installed local model was available. Model inference/evaluation was not rerun for these UI changes; earlier V4 evidence retains its original limitations.

## Remaining evidence and release boundaries

A genuine freelancer trial remains pending. Native print pagination and physical mobile operation remain unverified. Passing tests does not guarantee a defect-free product or contest outcome. The public demo, recorded walkthrough and published entry still describe their earlier checkpoint; DEV publication remains on hold. The earlier video and release receipt are historical and must not be described as captures of this redesigned UI.

Run this working copy with the installed dependencies using:

```sh
.venv/bin/python scripts/start.py --with-model --port 8879 --model-port 18082 --data-dir .runtime/upgrade-data
```

The packaged source excludes private project data, model weights, local runtime, credentials and installed dependencies. The built frontend is included; Python dependencies and optional model installation remain required.

## Motion refinement

Added after the packaged experience checkpoint: scroll-triggered entrance reveals for home sections, a short headline entrance and illustrated evidence-line draw, restrained button press/hover feedback, card lift and status arrival. No new dependency or continuous animation loop. Content remains visible without browser animation support. Reduced-motion preferences disable motion, including cancelling active scroll reveals when the preference changes; observers and animations are cleaned up on navigation. Focused sections are not animated.

Validation: all 71 frontend tests passed, TypeScript and production build passed using Node 24.19.0. Live browser verified the new headline/illustration animation styles, the delivery anchor scroll landing, visible sections and no horizontal overflow at the current viewport. Backend code was unchanged in this refinement. The earlier archive predates this motion pass; the local source and built frontend contain it.
