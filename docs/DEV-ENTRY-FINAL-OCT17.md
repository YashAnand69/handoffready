# Final entry preparation — 17 October 2026

Parent integration owns publication. The user has now explicitly requested submission tonight; this supersedes the earlier publication hold. This document does not itself certify release readiness. Update the existing DEV draft **6228689**, rather than creating a second Week 2 entry.

Copy only between ARTICLE START and ARTICLE END. Before publishing, the parent must verify that the public walkthrough below shows the current candidate, replace/add its actual video embed, add one current readable screenshot if available, and link the final source revision and evidence from the release page. Do not publish internal preparation notes. The body deliberately does not claim a customer trial or fresh-machine/accessibility/print validation. Its demo description is gated on the actual final recording/explorer matching that sequence.

<!-- ARTICLE START -->
---
title: "HandoffReady: the folder looks finished. Does it fulfill the brief?"
published: false
tags: devchallenge, hf26challenge, ai, opensource
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12).*

## What I Built

A client asks for a transparent logo, three launch images and instructions for updating their website's contact email. The delivery folder has all the right-looking filenames. The freelancer is ready to send it.

Except the logo is opaque, two launch images are identical, and the guide contains a welcome message instead of instructions.

That is HandoffReady's synthetic demonstration: an exported-file review desk for web/design freelancers and small agencies. It connects the agreed brief, outgoing originals and a client delivery record. Local Gemma proposes requirements and supporting files. The reviewer confirms scope, examines findings and records what is ready or still outstanding.

The potential paid service is a repeatable check before each delivery, with a record that helps explain unresolved work to the client. It does not require moving the client into another project-management platform. That is a business hypothesis, not established demand: no freelancer trial, payment or measured saving has been recorded yet.

## Demo

[Watch the current 90-second walkthrough](https://yashanand69.github.io/handoffready/) · [Inspect the recorded findings](https://yashanand69.github.io/handoffready/explore/) · [Read the exported client record](https://yashanand69.github.io/handoffready/records/after.html)

[![Actual current HandoffReady interface: an agent-operated synthetic review](https://yashanand69.github.io/handoffready/walkthrough.poster.png)](https://yashanand69.github.io/handoffready/)

The silent video is an edited sequence of actual interface captures from the 17 October local workflow, rather than continuous footage of inference or its waiting time. Actual local extraction and matching succeeded in that session. The separate explorer preserves an explicitly dated earlier recording of the same review contracts. Neither public page runs Gemma in your browser. Materials and decisions are agent-operated synthetic examples.

Here is the consequential part of the journey:

1. Confirm the checklist against the brief. An exact quotation helps locate a requirement; the reviewer still checks formats, quantities and omitted details.
2. Inspect the packet. Two launch files share identical bytes. The logo contains no nonopaque pixels. The welcome-only guide lacks the requested contact-email instructions.
3. Replace the logo with a corrected original. The packet changed, so previous reviews become stale and need checking again.
4. Export a fresh client record. The earlier snapshot remains unchanged; the new one retains the duplicate-image and guide gaps.

The ending is deliberately a partial correction. Three filenames cannot establish three distinct designs. Transparent pixels cannot establish a correctly prepared logo. An impressive-looking file cannot establish that it fulfills the brief.

The useful output is a delivery record carrying the review, outstanding work and identities of supporting originals. Send the actual files alongside it. The record explains the review; it is not the delivery itself or client acceptance.

## Code

[HandoffReady on GitHub](https://github.com/YashAnand69/handoffready)

The project began on 13 October, during Week 2. Application code is MIT-licensed and the original synthetic fixtures are CC0. Gemma and the runtime retain their own licenses. The repository includes installation instructions, evaluation methods, saved results and known failures.

## How I Built It

React and TypeScript provide the review desk. FastAPI, SQLite and bounded file inspectors handle projects and originals locally. Gemma runs through llama.cpp; no remote model API account is needed for supported inference after the explicit installation.

The key design decision is to keep three judgments separate: **Gemma's suggestion, an inspected file fact and the reviewer's assessment**. Marking a requirement satisfied cannot erase a failed technical check. Changing the brief, approved scope or packet invalidates earlier reviews. A failed file replacement preserves the previous original.

The [17 October verification](https://github.com/YashAnand69/handoffready/blob/d0b603fa9fc41fcac2da035b3d64c19b68b6b263/docs/release-oct17-checks.json) passed 250 backend and 74 interface tests, the production build and static checks. The [remote verification workflow](https://github.com/YashAnand69/handoffready/actions/runs/39025893074) also passed. Separate actual-model smoke calls succeeded; those calls do not measure accuracy.

The interface follows that repeat-review loop: saved projects summarize outstanding attention, evidence can be searched, and “Save and next” advances after the decision is saved. Client records separate private review notes from wording deliberately shared with the client.

### Why use a model for this?

Ordinary checks can establish properties such as dimensions, format and identical bytes. They do not readily connect a paraphrased brief to a relevant guide with an unexpected filename. Gemma proposes that connection and extracts a draft checklist from prose.

An evaluation compared association approaches on ten authored synthetic packets containing 27 files. With approved requirements supplied separately, a locked filename-plus-inspected-text baseline found **13 of 19 keyed supporting file pairs**. Gemma found all 19, plus two incorrect format substitutions. The inspected-format guard removed those two substitutions from the same captured outputs.

One concrete gain: Gemma connected `distribution.txt`, which says to place an announcement near a stall entrance and on the community board, to the flyer-placement guide requirement. The filename-plus-text baseline missed that pair.

That narrow gain is six additional support pairs on this set. It is not general accuracy or proof that the automatically extracted workflow is complete.

Extraction was weaker: **15 of 21 mandatory obligations met the predefined coverage rules**; six proposals missed required format details. The actual app also suggested that the welcome-only guide supported contact-email instructions. A real quotation did not make that association useful. The demonstration preserves that mistake, which is why scope confirmation and review are central to the product.

[Methods, raw-result identity and limitations](https://github.com/YashAnand69/handoffready/blob/d0b603fa9fc41fcac2da035b3d64c19b68b6b263/docs/MODEL-EVIDENCE-UPGRADE.md) distinguish model calls, synthetic workflow checks and automated tests. None is presented as customer evidence.

### The human role

My contribution was product direction: choosing the web/design freelancer context, insisting on a free/local approach and asking for a full delivery workflow with careful repeat review. AI coding agents assisted with implementation, testing, interface work, evaluation and this write-up. The next responsibility is getting the tool into a freelancer's hands; scripted sample approvals are not customer judgments.

## Why Does Open Innovation Matter?

A freelance packet may contain material its owner has not authorized uploading to an external AI service. Running an open-weight model locally gives that owner another option. There is no per-request model API bill, although hardware, installation and electricity still have costs.

Open source also makes the boundaries inspectable: which properties are checked, which suggestion came from the model, how source evidence is bound, and when decisions become stale. The model, inspectors and workflow can be adapted independently. Open execution makes that possible; it does not make predictions correct.

The validated environment is a single local user on Apple Silicon macOS. The app does not execute websites or certify visual design quality. Local storage is not encrypted by the application. The next product test is straightforward: can a freelancer complete a real handoff with little assistance, find the exported record useful and want to use it again?

## Prize Categories

**Best Use of Gemma.** Local requirement extraction and file association are meaningful, recorded model tasks at the center of the workflow. I am also entering the overall challenge.
<!-- ARTICLE END -->
