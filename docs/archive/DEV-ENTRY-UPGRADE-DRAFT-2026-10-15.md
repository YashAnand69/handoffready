# Preparation notes — outside the article

Local unpublished draft, prepared 15 October 2026. Preserve `DEV-ENTRY.md` as the historical article. Do not publish, submit, contact anyone or change live DEV from this file.

The article lies between the `ARTICLE START` and `ARTICLE END` comments. Its screenshot and evidence links are local preparation references, not public asset URLs. Upload the approved screenshots/diagram and replace those references with their actual resulting URLs before publication; do not invent URLs. The existing public walkthrough is explicitly historical. The upgraded explorer and source are local working artifacts and are not represented as a new public release.

Current evidence: `EXPERIENCE-UPGRADE-STATUS.md` records 245 passing Python tests and 71 frontend tests for the experience checkpoint. The subsequent motion-only pass retained 71 passing frontend tests and a successful production build. These are recorded checkpoints, not a claim that every future edit has passed. The earlier `upgrade-release-checks.json` (239 Python / 54 frontend) and 64-second `outputs/upgrade-video/HandoffReady-upgrade.mp4` are historical. They must not be presented as receipts or captures of the current UI.

Use `screenshots/experience-home.png`, `screenshots/experience-mobile.png` and `screenshots/motion-refinement.png` for the relevant new UI checkpoints. The article's older review and manifest captures are explicitly labelled historical. Record a current walkthrough following `DEMO-STORYBOARD-FINAL.md` before representing the new interface in a video. Screenshot/Markdown links below are preparation references and require actual public asset URLs before publishing.

The first V4 model report and its limitations remain unchanged. UI changes were not used to retune or rerun that evaluation. Native print pagination, physical-device usability and a genuine customer trial remain unverified. Publication is on hold; the current local app is not a new public deployment. No customer endorsement, payment, measured time saving or business result has been established.

<!-- ARTICLE START -->
---
title: HandoffReady: a review desk for the files you actually deliver
published: false
tags: devchallenge, hf26challenge, ai, opensource
---

*This is a draft submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12).*

## What I Built

A freelancer's delivery folder can look finished before it is ready. In HandoffReady's synthetic sample, the logo is opaque, two launch images contain identical bytes, and the contact guide contains a welcome message instead of instructions.

HandoffReady connects the agreed brief, outgoing files and a reviewed client delivery record. The upgrade gives the reviewer a clearer next step while keeping unresolved work visible. Whether it makes a freelancer faster is still to be tested.

The desk moves from brief to confirmed scope, files, review and handoff. Gemma proposes grounded requirements and supporting files. The reviewer corrects scope, chooses evidence and records an assessment. File checks establish narrow facts; client acceptance stays with people.

The intended customer is a solo web/design freelancer or small agency preparing repeated handoffs. A clearer record and fewer avoidable omissions are the paid-utility hypothesis. No customer trial, time saving or willingness to pay has been measured.

![Current local delivery desk, with the motion refinement](screenshots/motion-refinement.png)

## A review that survives correction

Saved projects reopen at the next useful step. Review queues and file evidence are searchable; findings appear before the assessment controls. “Save and next” advances after a successful save. The file desk exposes duplicate and attention filters, while a failed replacement preserves the original and its reviews. Small entrance and button animations support orientation; reduced-motion preferences disable motion. These choices aim to make a repeatable work tool, not just a landing page.

The attention overview separates stale reviews, human assessments, technical findings and scope exceptions. These overlapping counts are not a completion score. Calling something “satisfied” cannot erase a failed check.

Selections can be checked before saving a decision. Source evidence has an exact location: document identity, text hash and Unicode character range. Repeated wording retains distinct occurrences instead of silently selecting the first match.

If the reviewer excludes an item, its failed or unknown findings remain visible. A reviewed record with scope exceptions needs a deliberate client-facing explanation, separate from private reasoning. Changing the brief, scope or packet invalidates affected reviews; saving an unchanged filename does not create unnecessary churn.

The exported record has an overview, outstanding actions, requirement details and a deduplicated inventory of supporting originals. JSON, Markdown and HTML share one projection, with snapshot identity and checksums. The original files must be sent separately. Corrections create a new record; they never rewrite the earlier snapshot.

![Earlier local client delivery record capture; one failed check remains visible. This predates the latest interface redesign](screenshots/upgrade-manifest.jpg)

## Demo and code

The [existing public walkthrough](https://yashanand69.github.io/handoffready/) shows the historical application checkpoint. It is an edited recording assembled from actual local captures and real Gemma jobs, using an agent-operated synthetic packet. It is not a hosted inference service, customer trial or continuous screen recording.

The local 64-second walkthrough uses actual captures from an earlier upgrade checkpoint, edited into 1,536 frames at 1440 × 1080. It is unpublished and does not show the latest interface or motion pass. The recorded explorer lets readers compare captured checkpoints and records; it accepts no uploads and runs no inference. The full application runs locally with React/TypeScript, FastAPI, SQLite, bounded inspectors and Gemma through llama.cpp.

The [public repository](https://github.com/YashAnand69/handoffready) preserves the original project. This draft describes an unpublished local upgrade; reviewed source, receipts and assets must accompany publication.

![Architecture explanation: local app and separate recorded explorer](screenshots/upgrade-architecture.svg)

## What Gemma contributed—and missed

Gemma handles requirement extraction and file association. Semantic association can help when a guide's wording differs from the brief. Ordinary code checks formats, dimensions, page counts, literal text, nonopaque PNG pixels and duplicate bytes.

For the upgrade, an agent authored ten new synthetic briefs and 27 original supported files, then froze the keys before predictions. Association received fixed approved requirements separately from extraction. One captured call per stage allowed before/after guard comparisons without rerunning the model.

| Association method | Correct / predicted positive pairs | Wrong pairs | Missed / 19 keyed pairs |
| --- | --- | --- | --- |
| Filename-only baseline, with type filtering | 9/9 | 0 | 10/19 |
| Filename plus inspected text baseline | 13/13 | 0 | 6/19 |
| Gemma before guards | 19/21 | 2 | 0/19 |
| Same predictions after guards | 19/19 | 0 | 0/19 |

The two wrong suggestions substituted PNG for explicitly requested JPEG. The inspected-format guard removed them. All four no-support requirements were correctly left without positive associations. This does not establish general relevance or injection security.

Extraction covered 15/21 mandatory obligations under the frozen source, classification and format definition. All 21 proposals had valid source spans, but six omitted requested format checks. Two optional items were absent and reported separately, not counted as mandatory misses. Exact check sets matched 11/23 keyed items. Strict granularity, conditional attribute scoring and human-added literal checks limit how those figures should be interpreted.

All twenty calls succeeded. Maximum extraction and association times were 3.254 and 3.970 seconds on the tested local runtime. The evaluator allowed 180 seconds while the app allows 120 including queuing; no measured call needed that extra allowance. These are small local observations, not service guarantees.

The upgraded browser workflow still exposed a bad match: Gemma treated a welcome-only guide as relevant to contact-email instructions. Its quoted heading and reasoning remain recorded, alongside earlier schema, TXT-for-CSV injection and TXT-for-PDF promise mistakes. A valid quotation does not prove delivery. See the local [first-run analysis](MODEL-EVIDENCE-UPGRADE.md).

## How I built and checked it

My role was product direction: choose the freelancer audience, set the free/local constraint, prioritize the full delivery workflow and require independent reviews. Genuine customer evaluation and final delivery decisions remain human responsibilities.

AI coding agents assisted with implementation, tests, interface work, evaluation and this draft. Separate agents reviewed parts of the system; their work was integrated and checked. I do not claim exclusively hand-written code or human customer approval for scripted sample decisions.

Actual browser jobs exercised extraction, matching, correction and export. Replacing the opaque logo made three reviews stale; re-review removed one technical failure, while duplicate artwork and the incomplete guide remained unresolved. The old record stayed byte-identical. A separate scripted API workflow checked persistence and exports.

The experience checkpoint passed 245 Python tests, 71 interface tests, TypeScript/build, formatting and focused Ruff. The subsequent motion-only refinement retained 71 passing interface tests and a successful production build. The legacy baseline compatibility fix passed old-format regressions. A clean manual installation completed seven scripted workflow stages without inference. Post-evaluation API/presentation fixes mean the final whole source differs from the frozen model candidate, whose core and first report remain unchanged.

The latest experience checkpoint found no horizontal overflow on home at 390 and 1440 pixels, review at 320 and 390 pixels, and files and handoff at 320 pixels. They do not certify physical devices or accessibility. Native A4/Letter print pagination remains unverified.

## Why open innovation matters

After explicit setup, supported inference runs locally without a remote AI account or metered model API. Pinned Gemma weights and llama.cpp sources have verified digests. The application is MIT-licensed, the pinned model is Apache-2.0, and the original synthetic fixtures are CC0; their licenses remain separate.

**Best Use of Gemma** is the relevant partner category: its extraction and association work is central and recorded, while deterministic guards and reviewer decisions remain distinct.

The validated setup is Apple Silicon macOS and one local user/process. OCR, Office/PSD/ZIP imports, live website execution and automatic visual judgment are outside scope. Storage is not encrypted by the app. Records omit raw briefs and private notes, but reviewers must inspect shared titles and client wording.

The next product test is a genuine authorized freelancer handoff: what do they correct, can they work without assistance, and would they return? Until then, this is a tested local demonstration with an unresolved model mistake and a plausible customer—not a validated business.
<!-- ARTICLE END -->
