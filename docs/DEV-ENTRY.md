---
title: HandoffReady: check the handoff before sending it to the client
published: false
tags: devchallenge, hf26challenge, ai, opensource
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12).*

## What I Built

The brief asks for a transparent logo, three launch images and instructions for changing the website contact email. The delivery folder has all the right-looking names. But the PNG is fully opaque, two image files are identical, and “client guide” contains only a welcome message.

That is HandoffReady's original synthetic demo, not a customer result. It illustrates the problem I chose to build for: a web or design freelancer needs to check what they are handing over, then explain it clearly to the client.

HandoffReady connects the agreed brief, actual delivery files and a reviewed client manifest. It runs locally, including its open model.

The workflow has five steps:

1. Save the brief and ask a local open model to propose a checklist with exact source quotations.
2. Correct the interpretation and explicitly confirm the checklist, including required formats and quantities.
3. Bring the actual delivery packet. Inspect supported file properties and ask the model for evidence associations.
4. Choose files, review their contents and record an assessment. Technical facts remain separate from that assessment.
5. Preview and export a client manifest that keeps missing work visible and leaves private source/review fields out.

Changing the brief, checklist or packet invalidates affected review. A human assessment cannot overwrite a failed technical check. The manifest records evidence and review; client acceptance and live website testing still belong to people.

### Who might pay for it?

The intended customer is a solo web/design freelancer or small agency preparing repeated client handoffs. A private checklist and clear manifest might help them catch omissions and explain exactly what was delivered. That is the paid-utility hypothesis I would test.

I have not measured customer time savings, willingness to pay or recurring use. I deferred the genuine freelancer trial until the tested demo was complete. A real delivery is the next test, before choosing a price or adding team collaboration.

## Demo

[Watch the recorded local walkthrough](https://yashanand69.github.io/handoffready/) · [Download the MP4](https://yashanand69.github.io/handoffready/walkthrough.mp4)

The local sample uses original synthetic files and supports actual local inference. Its opaque logo, duplicate launch artwork and incomplete guide give the review something meaningful to catch. The recording labels its captured screens and shows actual local inference.

The two-minute-fifteen-second video follows a real local workflow: Gemma proposes a quoted checklist and file associations; the operator inspects the imperfect packet, preserves failed checks, marks the welcome-only guide as needing work, replaces the opaque logo, reviews again and downloads the manifest. The earlier export stays unchanged after correction.

It is an edited walkthrough assembled from actual app captures, not a continuous screen recording. The sample and agent-operated confirmations are synthetic; they are not customer or human-user trial evidence. Captions, a transcript and chapter navigation accompany the silent video.

The captured application revision is `b0d87f0730eb6a10b3ad3be4316e023152057e65`. The published repository also includes the subsequent demo tooling and evidence records. The watch page is a recording, not a hosted inference endpoint.

## Code

[Source code and verification evidence](https://github.com/YashAnand69/handoffready)

The project began on 13 October 2026 during the Week 2 window, in a fresh repository. The demonstrated app checkpoint is commit `b0d87f0`; the public repository preserves that revision and subsequent demo preparation. Application code and interface are original with AI assistance. The application uses licensed open-source foundations; model weights/runtime have their own notices and are not bundled into the source archive.

## How I Built It

The stack is React/TypeScript, a local FastAPI service, SQLite, bounded file inspectors and Gemma 4 E2B through llama.cpp. Pillow, pypdf and defusedxml inspect supported images, PDFs and SVG metadata. The app handles a delivery packet; it does not execute a client's website or send files to them.

Gemma has two jobs: propose requirements with quotations from the brief, then associate requirements with file evidence. In the recorded synthetic development packet, Gemma associated instructions for changing contact details with `01-guide.txt`, whose text describes editing the telephone number and email address through business settings. That generic filename cannot settle the association. In the same tuned packet, real inference associated three paraphrased guides that the frozen lexical baselines missed. That small example demonstrates a contribution, not general superiority.

Ordinary code checks supported facts: format, dimensions, native PDF page count, literal text, nonopaque PNG pixels and duplicate bytes. The reviewer checks whether the content is useful. Different hashes never prove different designs, and one nonopaque pixel never proves correct background removal.

### The human role

My role was to choose the audience, set the free/local constraint, prioritize the delivery workflow, insist on a complete application and require repeated independent reviews. Customer evaluation remains my next responsibility. The implementation preserves a clear decision boundary: the model proposes; the reviewer approves.

AI coding agents assisted with implementation, tests and documentation. Separate agents reviewed file handling, model behavior, the backend and interface, followed by integration and browser checks. The code is not exclusively hand-written, and those reviews did not eliminate every mistake.

### A failure that changed the design

The first real model calls failed strict schema or source-evidence validation. Later fresh synthetic evaluations exposed semantic mistakes: instruction-injection text was associated with a missing CSV, and a future promise inside a TXT file was treated as support for a missing PDF catalogue.

An exact quote proves that words exist, not that they meet the requirement. Repairs included tighter source/type grammar, model relevance classification and a deterministic guard against inspected formats conflicting with approved checks. The guard can suppress TXT-for-PDF when the required format is approved; it cannot decide whether a correctly typed document is useful. Suppressed suggestions retain diagnostics.

The recorded app demo exposed another wrong association: Gemma treated the welcome-only guide as supporting contact-email instructions. The operator marked it as needing work. The exact saved candidate and the two successful local model jobs are preserved in [`browser-demo-verification.json`](https://github.com/YashAnand69/handoffready/blob/main/docs/browser-demo-verification.json).

The original failures remain in the repository. Once a case informed a repair, its rerun became a development regression, not a fresh held-out success. Semantic associations and checklist completeness still need human review; prompt-injection robustness is unproved. The app labels model interpretation as unverified.

### What I actually verified

At the final local checkpoint, **137 Python tests and 31 interface tests passed**, along with strict TypeScript/production build, formatting and focused Python correctness checks (`F,E9`). npm audit reported zero known findings at that check. `docs/final-release-checks.json` records the actual outputs. Model unit tests use declared protocol stubs; actual inference is recorded separately.

The [first remote GitHub Actions run](https://github.com/YashAnand69/handoffready/actions/runs/38462789325) also passed the 137 backend tests, 31 interface tests, build, formatting and focused correctness checks. CI uses declared model doubles, not downloaded-model inference.

A separate real HTTP walkthrough recorded successful v10 extraction and matching, actual file inspection, exports, replacement, stale review and restart persistence. Browser checks exercised the sample workflow and downloaded output. Receipts and original failures are documented in `docs/MODEL-EVIDENCE.md` and the workflow records.

Final browser checks also confirmed that saving an unchanged source preserves the confirmed checklist and three current reviews. Narrow viewport checks found no horizontal document overflow at 320 pixels on Home/Files and 390 pixels on Review. These are browser observations, not physical-device or accessibility certification.

Exports omit raw source/private-note fields. Approved titles, check descriptions and client notes are deliberately shared and must be previewed for confidential content. Field separation cannot automatically remove private meaning copied into a title.

On the tested Apple M5 Pro with 24 GiB RAM, tuned v10 development calls took about five to six seconds. These are observations on small synthetic inputs, not service guarantees or an accuracy statistic. The RSS observations do not measure every GPU/system allocation.

## Why Does Open Innovation Matter?

Freelancer briefs and client files can contain private information. After explicit model setup, the supported workflow runs locally without a remote AI account or metered model API. That is the concrete benefit here: control over where inference happens, prompts, structured output, time budgets and evidence validation. Hardware, setup and electricity still have costs.

The source-built llama.cpp runtime and quantized Gemma model have pinned revisions and verified digests. Their provenance and the failing evaluations can be inspected alongside the adapter code. No closed-model comparator was run, so I am not claiming higher accuracy than a commercial API.

Open foundations made it practical to focus on the delivery problem. React and React DOM provide the interface; FastAPI/Starlette/Pydantic/Uvicorn provide the local service; SQLite stores projects; Pillow, pypdf and defusedxml inspect files; Gemma and llama.cpp provide inference. Locked versions, model revisions and licenses are recorded in `THIRD-PARTY-NOTICES.md` and the evidence documents. The application is MIT-licensed; the pinned Gemma model is Apache-2.0, and original synthetic fixtures are CC0. Their licenses remain separate.

## Prize Categories

**Best Use of Gemma.** Gemma runs locally and performs the central requirement extraction and evidence association tasks. The adapter verifies source evidence and keeps every suggestion subject to review. Real inference receipts record the model revision, quantization, digest, runtime and prompt version.

The project uses GitHub Actions for automated verification; it does not claim GitHub Copilot coding assistance. The named partner submission category here is Gemma.

## Current limits

The tested model installation is for Apple Silicon macOS and one local user/process. The release supports pasted English briefs and bounded PNG/JPEG, safe SVG metadata, readable native PDFs, text and Markdown. OCR, Office/PSD/ZIP import and automatic visual quality judgments are outside its scope. A parser result and correct file type are not proof of useful content. Local application storage is not encrypted by the app; privacy also depends on the device and what the reviewer chooses to share.

The next product test is a genuine freelancer trial: can they review a delivery without assistance, what do they correct, and would they use it again? Until that happens, HandoffReady is a tested local demonstration with a plausible customer, not a validated business.
