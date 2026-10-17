# Preparation notes — outside the article

Revised 17 October 2026. **Unpublished local preparation; publication remains on hold.** This document does not authorize publishing, submitting, deploying or contacting anyone. The previous draft is preserved byte-for-byte in `archive/DEV-ENTRY-UPGRADE-DRAFT-2026-10-15.md`.

Copy only the text between `ARTICLE START` and `ARTICLE END` when the entry is ready. The current public source/video are historical and must not be presented as the local upgrade. Before publication, attach the current actual walkthrough and approved screenshots, verify their public URLs and the final source revision, and reconcile the existing DEV entry rather than creating a duplicate. No new walkthrough or public release is claimed here.

Local preparation references, deliberately outside the article:

- Current checkpoint: [FINAL-UPGRADE-CHECKPOINT.md](FINAL-UPGRADE-CHECKPOINT.md); [15 October verification](final-upgrade-verification.json), 250 backend / 74 interface tests. This edit did not rerun tests.
- Actual model analysis: [MODEL-EVIDENCE-UPGRADE.md](MODEL-EVIDENCE-UPGRADE.md); frozen synthetic evaluation unchanged.
- Current media to prepare: [DEMO-STORYBOARD-FINAL.md](DEMO-STORYBOARD-FINAL.md). The 64-second local video and public 135-second video predate the final interface.
- Actual local captures available for review: [home](screenshots/experience-home.png), [mobile viewport](screenshots/experience-mobile.png), [motion refinement](screenshots/motion-refinement.png). Use only appropriately dated, approved captures and actual uploaded URLs.
- Genuine trial: [participant guide](trial/PARTICIPANT-GUIDE.md). No trial, endorsement, willingness to pay or measured saving has been established. Native print, physical-device and actual screen-reader checks remain outstanding.

<!-- ARTICLE START -->
---
title: HandoffReady: check the files before sending the handoff
published: false
tags: devchallenge, hf26challenge, ai, opensource
---

*Prepared for [Hacktoberfest Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12).*

## What I Built

A delivery folder has a logo, three launch images and a client guide. It looks ready. But the logo is opaque, two images contain identical bytes, and the guide says “Welcome to your new website” without explaining how to change the contact email.

That is HandoffReady’s synthetic example. The intended user is a web/design freelancer or small agency checking exported delivery files before sending them to a client.

HandoffReady connects an agreed brief, outgoing originals and a client delivery record. Local Gemma proposes requirements and supporting files; the reviewer confirms scope, inspects findings and decides what is ready. The application then produces a record of the reviewed delivery and its outstanding work.

The potential paid value is a repeatable final check and clearer communication without migrating clients into another platform. This remains a hypothesis: no genuine freelancer trial, willingness to pay, recurring use or time saving has been measured.

## Demo

The recorded synthetic workflow starts with the imperfect packet above. Gemma proposes a checklist from the brief, with quotations the reviewer can inspect and correct. The reviewer confirms required formats and quantities, then examines the actual files.

Ordinary file inspection finds no nonopaque pixels in the logo and two identical launch originals. Reading the guide reveals the missing instructions. Gemma’s actual suggestion incorrectly associated that welcome-only guide with the contact-email requirement; the reviewer records the gap. A valid quotation does not establish useful delivered content.

Replacing the opaque logo with a corrected original makes previous reviews stale. The reviewer checks the changed packet and exports a new record. One technical failure remains, and two requirements still need attention. The earlier record stays unchanged.

This is a partial correction, not an all-green ending. Different hashes do not prove different designs, and transparent pixels do not establish a correctly prepared logo. The record makes those boundaries and remaining work visible. Original delivery files must travel alongside it.

The walkthrough is agent-operated with synthetic materials. It is not customer feedback. The latest local upgrade still needs its current recording and synchronized public assets; the [existing public walkthrough](https://yashanand69.github.io/handoffready/) shows the historical version and runs no hosted inference.

## Code

[Public repository](https://github.com/YashAnand69/handoffready)

The repository preserves the original project. This draft describes an unpublished local upgrade; the public version does not yet represent every improvement below. The project began during Week 2, on 13 October. Application code is MIT-licensed, original synthetic fixtures are CC0, and model/runtime licenses remain separate.

## How I Built It

React and TypeScript provide the review desk; FastAPI, SQLite and bounded inspectors handle local projects and originals. Gemma runs through llama.cpp. The validated setup is one local user on Apple Silicon macOS. After explicit installation, supported inference needs no remote model API account.

The workflow keeps three things separate: a model’s suggestion, an inspected file fact and a reviewer’s assessment. Calling an item satisfied cannot erase a failed technical check. Changing the brief, scope or packet invalidates previous reviews. Correcting a file creates a new record instead of rewriting the old snapshot.

The interface supports that loop: saved projects reopen at the next useful step, evidence is searchable, and “Save and next” advances after saving. A failed replacement preserves the original. Client records separate private review notes from deliberate shared wording and identify the supporting originals.

### What Gemma adds—and misses

In a frozen synthetic evaluation of ten briefs and 27 files, a filename-plus-inspected-text baseline found 13 of 19 keyed support pairs without wrong positive pairs. Gemma proposed all 19 plus two wrong-format substitutions; the existing format guard removed those two. This was a separate association task with fixed approved requirements, not end-to-end workflow accuracy.

Extraction covered 15 of 21 mandatory obligations under the predefined scoring rules. Six omitted requested format checks. Exact source spans help inspect suggestions, but do not establish completeness. The welcome-guide mistake also remains recorded separately. These results justify assisted review, not automatic approval or general reliability claims.

### Checking the work

The integrated **15 October checkpoint** records 250 backend tests, 74 interface tests, TypeScript, production build, formatting and focused static checks passing. Those are recorded results, not new tests from this article revision. Actual model calls and synthetic browser workflows are documented separately from tests using doubles.

Fresh-machine setup, physical-device operation, an actual screen reader and native A4/Letter pagination remain unverified. Supported checks cover bounded image/document properties; the application does not execute websites, visually certify design quality or replace client acceptance.

### The human role

Human direction set the freelancer audience, free/local constraint, full delivery workflow and repeated-review requirement. AI coding agents assisted with implementation, testing, interface work, evaluation and drafting. Scripted sample decisions are not human customer approval. Real-user evaluation remains the next responsibility.

## Why Does Open Innovation Matter?

Local inference offers a practical choice for reviewing authorized delivery materials without uploading them to a remote AI service. Open source also makes the model’s contribution, deterministic checks and known failures inspectable and adaptable. Pinned dependencies and model provenance support reproducibility; openness does not make predictions correct.

Storage is local and unencrypted by the app. Records omit raw briefs and private notes, but shared titles and client wording still need review. The next test is whether a freelancer can complete a handoff with little assistance, find the record useful and want to return.

## Prize Categories

Overall and **Best Use of Gemma**: requirement extraction and file association are meaningful, recorded model tasks. Human review and technical checks retain their separate roles.
<!-- ARTICLE END -->
