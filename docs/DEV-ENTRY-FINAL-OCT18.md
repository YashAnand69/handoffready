# Published entry revision — 18 October 2026

Editorial source for the existing published Week 2 entry. This supersedes the 17 October article text, not the dated demonstration or its evidence. Preserve the existing title, URL, cover, challenge association, tags and truthful AI disclosure. No second entry. Publication verification is recorded separately.

<!-- ARTICLE START -->
---
title: "HandoffReady: the folder looks finished. Does it fulfill the brief?"
published: true
tags: devchallenge, hf26challenge, ai, opensource
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12).*

## What I Built

A client asks for a transparent logo, three launch images and instructions for updating their website's contact email. The delivery folder has all the right-looking filenames. The freelancer is ready to send it.

Except the logo is opaque, two launch images are identical, and the guide contains a welcome message instead of instructions.

That is HandoffReady's synthetic demonstration. It is a local review desk for freelancers and small agencies delivering exported brand/web assets and written guides: connect the agreed brief to outgoing files, examine what each file actually supports, and export a client record of what is ready and what still needs work.

Gemma proposes a checklist and relevant files. **The person doing the handoff confirms the scope, judges the work and decides what to share.** The useful result is a record they can explain to a client, with unresolved work still visible.

### Where it would fit into a working day

These are intended workflows within the supported exported-file scope; they have been exercised with synthetic materials, not validated with paying clients.

| Delivery | What HandoffReady helps check | What the person still decides |
| --- | --- | --- |
| Logo or brand exports | Whether the selected originals include the requested formats, and whether a PNG actually has nonopaque pixels | Whether the artwork is correct and usable; transparency alone cannot establish that |
| A campaign image pack | Dimensions and byte-identical duplicates, alongside the approved quantity | Whether the images are the distinct designs promised in the brief |
| A client update guide | Readable text in a native PDF, TXT or Markdown file, with proposed supporting passages | Whether the instructions really explain the requested task |
| A corrected delivery | Changed inputs make old reviews stale; a fresh export preserves the new review while the previous snapshot stays unchanged | Whether the revision resolves the problem, and how to describe remaining work |

This fits just before sending exported assets and documentation. It does not execute a website, inspect a running app or certify visual design quality. The client can read the exported HTML or Markdown record without joining another project-management system. The actual files must be sent alongside it; the record identifies supporting originals and does not contain their bytes.

### The human work behind the project

My role was product direction. I chose the web development/design freelancer context, required a free/local approach and asked for a complete workflow rather than an interface-only demo. Across iterations I pushed for clearer usability, more careful audits and an explanation of what a real freelancer would gain from it.

AI coding agents carried out implementation, interface work, testing, evaluation and documentation, including assistance with this post. The agents also operated the synthetic demonstration.

The human role inside the product is equally concrete: check the extracted scope against the agreement, correct omissions, read the proposed evidence, record a judgment and choose client-facing wording. A model suggestion never becomes approval on its own. That is especially important when the suggestion is plausible and wrong, as the demo shows.

## Demo

[Watch the 90-second walkthrough](https://yashanand69.github.io/handoffready/) · [Inspect the recorded findings](https://yashanand69.github.io/handoffready/explore/) · [Read the exported client record](https://yashanand69.github.io/handoffready/records/after.html)

[![HandoffReady's actual interface in the 17 October agent-operated synthetic review](https://yashanand69.github.io/handoffready/walkthrough.poster.png)](https://yashanand69.github.io/handoffready/)

The silent video is an edited sequence of actual interface captures from the 17 October local workflow. It is not continuous footage of inference or its waiting time. Actual local extraction and matching succeeded in that session. The separate explorer preserves an explicitly dated earlier recording. Neither public page runs Gemma in your browser. Materials and decisions are agent-operated synthetic examples.

The important sequence is a partial correction:

1. **Confirm the brief.** Check the proposed requirements, including formats, quantities and omitted details.
2. **Review the packet.** The logo has no nonopaque pixels. Two launch files have identical bytes. The welcome-only guide does not explain changing the contact email.
3. **Replace the logo.** The packet changes, so earlier reviews become stale and need checking again.
4. **Export a fresh record.** The old snapshot stays unchanged. The new record retains the duplicate-image and guide gaps.

A corrected file should not silently make the whole delivery look complete. The saved record explains the review and outstanding work; it is not client acceptance.

### Who might pay, and what remains unproven?

The first buyer I would test is a designer or small-agency lead who repeatedly checks delivery packets. The possible service is a local pre-delivery review with a repeatable client record. Its value would be catching an omission before sending and making the remaining work easier to discuss. The current project is free, open-source software; this is a service hypothesis, not a launched paid offering.

No completed freelancer trial, payment, measured time saving or willingness-to-pay result has been recorded. The next test is whether a freelancer can review one real packet with little help, finds the record useful and wants to repeat the process. That result should determine the next feature, and whether the service deserves to exist.

## Code

[HandoffReady on GitHub](https://github.com/YashAnand69/handoffready) · [Download v0.2.1 with the built interface](https://github.com/YashAnand69/handoffready/releases/tag/v0.2.1)

The project began on 13 October, during Week 2. Application code is MIT-licensed; original synthetic fixtures are CC0. Gemma, llama.cpp and dependencies retain their respective licenses and are credited in the repository. The release still needs Python dependencies and explicit optional model installation. It is not a hosted inference service or a one-click standalone executable.

## How I Built It

React and TypeScript provide the review desk. FastAPI, SQLite and bounded file inspectors handle projects and originals locally. Gemma 4 E2B runs through llama.cpp. No remote model API account is needed for supported inference after installation.

Three judgments remain separate: **Gemma's suggestion, an inspected file fact and the reviewer's assessment**. Marking a requirement satisfied cannot erase a failed technical check. Changing the brief, confirmed scope or packet invalidates earlier reviews. If a file replacement fails, the previous original is preserved.

The interface follows that repeat-review loop: saved projects summarize outstanding attention, evidence can be searched, and “Save and next” advances through unreviewed or stale items, then opens the draft record. Private review notes are separated from deliberate client notes. Titles and check descriptions also appear in client records, so their wording needs review before sharing.

### What Gemma contributes, and where it fails

Dimensions, format and identical bytes are ordinary file checks. The model's job is different: extract a draft checklist from prose and connect a requirement to a relevant file even when its filename does not give it away.

On ten authored synthetic packets containing 27 files, an association experiment supplied **approved requirements separately**. A locked filename-plus-inspected-text baseline found **13 of 19 keyed supporting file pairs**. Captured Gemma output found all 19, plus two incorrect format substitutions. The inspected-format guard removed those two substitutions from the same outputs.

For example, Gemma connected `distribution.txt`—instructions to place an announcement near a stall entrance and on the community board—to a flyer-placement guide requirement. The baseline missed it. That is a narrow gain of six supporting pairs on this set, not general accuracy or evidence that the complete automatic workflow is reliable.

Extraction was weaker: **15 of 21 mandatory obligations met the predefined coverage rules**; six proposals missed required format details. In the actual app, Gemma also proposed the welcome-only guide as support for contact-email instructions. An authentic quotation did not make that association useful. The demonstration retains the mistake and records the guide as needing work.

[Methods, captured-result identity and limitations](https://github.com/YashAnand69/handoffready/blob/d0b603fa9fc41fcac2da035b3d64c19b68b6b263/docs/MODEL-EVIDENCE-UPGRADE.md) separate the model experiments, workflow checks and customer outcomes. They are different kinds of evidence.

### Final audit: two actual fixes

The 18 October [v0.2.1 audit](https://github.com/YashAnand69/handoffready/blob/97592fd5dffbb904cc785eaddfb1645a6a6fe3af/docs/FINAL-CRITICAL-AUDIT-OCT18.md) found that a second launcher could interfere with another process's data folder. The supported launcher now acquires an exclusive folder lock before recovery or cleanup. A process-level regression checks that refusal and recovery after the owner stops.

It also found that “Save and next” could revisit reviewed items before an unreviewed one. Navigation now finishes pending reviews before opening the record, while preserving the saved gaps.

[Remote verification](https://github.com/YashAnand69/handoffready/actions/runs/39142499845) passes **254 backend and 75 interface tests**, static checks and the production build. Separate real-model smoke calls succeeded. Test counts do not measure model accuracy or customer usefulness. The video remains the dated 17 October recording, before these two audit fixes.

## Why Does Open Innovation Matter?

A freelance packet may contain material its owner has not authorized uploading to an external AI service. Local inference offers another route. The supported app and model services bind to loopback, and no remote model API is required after setup. There is no per-request model API bill, although hardware, installation and electricity still cost something.

Open code makes the review rules inspectable: what was measured, what the model suggested, which originals support a decision and when that decision became stale. Open weights let the model run locally; the model, inspectors and workflow can be adapted independently. That control is useful even when the model is imperfect.

The validated environment is a single local user on Apple Silicon macOS. Setup has a real cost: Python dependencies and, for inference, roughly 8 GB of free disk for model/build artifacts. Local storage is not encrypted by the application. Live website execution, PSD/Office/ZIP review and scanned-PDF OCR are outside this release. These boundaries keep the promise specific enough to examine.

## Prize Categories

**Best Use of Gemma.** Local requirement extraction and file association are recorded model tasks at the center of the workflow, with measured gains and retained failures. I am also entering the overall challenge.
<!-- ARTICLE END -->
