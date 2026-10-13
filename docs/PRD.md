# HandoffReady — Product requirements document

> Historical planning specification, preserved from 13 October 2026. Current implementation, verified departures and release limits are recorded in [STAGE-REVIEWS.md](STAGE-REVIEWS.md), [BUILD-CONTRACT.md](BUILD-CONTRACT.md) and [FULL-STACK-RELEASE.md](FULL-STACK-RELEASE.md). A proposed benchmark or trial below is not evidence that it occurred.

Version: planning v1 · 13 October 2026 · owner: Yash Anand

**Stage 0: proposed product.** This document specifies behavior to build and validate. It is not evidence of implemented features, model performance, customer demand, a completed user trial, revenue, or contest eligibility certification. The working name is provisional.

## 1. Product decision and purpose

HandoffReady helps a freelance web developer or designer prepare a final delivery package against an agreed brief. The user confirms the requirements, inspects file-backed evidence, resolves discrepancies and exports a clear handoff manifest. A local open model proposes semantic matches; bounded deterministic inspections check supported technical properties; the freelancer owns the final decisions.

The proposed promise is: **“Check the files you are about to deliver, explain what each one satisfies, and carry unresolved items into the handoff.”** The product does not promise to certify a finished website, contract fulfillment, design quality, legal rights, or client acceptance.

This is a new Week 2 product, with original workflow/data logic built on credited licensed dependencies. It is not a renamed Soundwalk Atlas, a fork of a finished handoff service, or a general project manager. The full technical and UI contracts are in this pack's TRD and UI specification.

## 2. Customer, problem and evidence status

### Primary user

A solo web/design freelancer, or a small agency's delivery owner, who sends exports, guides and related files after a project. The user has access to a potential tester doing web development and design. No packet, recurring pain, actual usage or willingness to pay has yet been observed.

### Customer job

“Before I send the final folder, help me find missing/wrong exports and explain the contents so the client can use them without another round of avoidable questions.”

### Proposed buyer

The freelancer/studio owner who bears rework and support costs. The client is the recipient of the resulting manifest, not necessarily a logged-in user. Initial adoption must work without client migration, a team account, or third-party integrations.

### Hypotheses to test

| Hypothesis | Evidence needed | Current status |
|---|---|---|
| Packet omissions or ambiguity recur | Recent concrete delivery example and actual artifact requirements | Unverified |
| The checklist/manifest helps on real work | Observed use, corrections, useful output and next-project intention | Unverified |
| Semantic AI adds value over filename/rules | Same bounded cases evaluated against a simple baseline, including hard negatives | Unverified |
| Privacy/local operation matters | User's own tradeoff between local setup and cloud convenience | Unverified |
| Someone would pay | Tested price response or actual purchase; interest alone is insufficient | Unverified |

The contact need not respond before independent prototyping starts. Synthetic fixtures and parser/model tests are useful immediately. Genuine user validation gates claims of customer usefulness, time savings and demand, not all implementation work.

## 3. Success definition

### Release success

A fresh user can complete one supported task: add a brief, confirm a checklist, inspect selected files, review suggestions with evidence, resolve or retain open issues, and export/reopen a truthful manifest. The normal and failure paths are exercised on a supported machine with the actual selected model.

### Customer success

A consenting tester understands the output and can identify whether it improves their existing process. Record preparation/review time, corrections, missed seeded defects, false flags, useful catches and setup burden. Report findings descriptively; a small convenience sample cannot establish industry-wide savings.

### Open-model success

The model is actually invoked in extraction/matching, adds useful semantic proposals on at least some nontrivial cases, and never bypasses quote validation or human confirmation. If it adds no useful advantage, narrow or revise the product and its contest story before claiming open AI is central. Model/category selection follows the TRD's benchmark gate; Gemma is a candidate, not an already integrated feature.

### Contest delivery target

Freeze a tested release and finish the truthful entry by **18 October evening IST**, ahead of the official **19 October 2026, 12:29 p.m. IST** deadline. Writing and practical paid utility matter; no winning odds or numeric judging weights are assumed. [Week 2 brief](https://dev.to/challenges/hacktoberfest-week2-2026-10-12), [specific rules](https://dev.to/page/hacktoberfest-week2-2026-10-12-contest-rules).

## 4. Scope and sequencing

### P0 — required for a coherent release

- Local workspace with one project, a pasted agreed brief, source provenance and a user-confirmed requirement baseline.
- Actual local open-model extraction and semantic matching behind a replaceable, pinned adapter.
- Bounded individual-file intake for PNG/JPEG/SVG, plain text/Markdown and text-extractable PDF, subject to parser validation. A failing/unsupported PDF is explicitly unchecked, not “missing” or “satisfied.”
- Inventory with detected type, hashes and supported inspections; no execution of imported content.
- Exact quoted source evidence, proposed versus confirmed matches, multiple files per requirement and manual requirements.
- Review states that distinguish a technical check from human acceptance, visible unresolved items and reasoned exceptions.
- Hash/revision-bound approvals, safe persistence/recovery and complete export of decisions and outstanding work.
- A complete synthetic fixture and real-model demonstration, with accessible task-focused UI.
- A public sample if hosted: clearly labeled sample/replay, distinct from live local inference and private client work.

### P1 — only after P0 passes

- Native-text PDF as a brief input, with page/quote navigation, if the text parser has proven reliable. Pasted text remains the dependable P0 baseline.
- Reusable studio checklist templates and a second packet revision using the same approved brief.
- Readable side-by-side packet change summary and optional polished printable output.
- Additional supported properties or small improvements motivated by the actual tester.

P1 must not delay the complete task, model evidence, testing or submission. If a candidate dependency misses its safety/quality gate, remove that format from supported scope visibly rather than imply support.

### Non-goals for this week

Cloud client storage, subscriptions/payments, Figma OAuth, email/WhatsApp ingestion, messages to clients, scanned-brief OCR, voice, PSD/AI source interpretation, ZIP extraction, arbitrary HTML rendering, website crawling, repository audits, website execution, medical/legal guidance, visual/a11y compliance certification, and a team collaboration dashboard.

Links may be included as user-entered references with “not checked” status; the app will not fetch them or infer a website works. Archive import is excluded: the user selects supported individual files instead.

### Canonical initial limits

These caps align with the TRD; changes must be made consistently in config, UI, tests and documentation: 30 delivery files; 50 MiB per packet; 10 MiB per file; native-text delivery PDFs at most 10 pages; raster images at most 10 megapixels and 10,000 pixels per side; text/SVG at most 1 MiB; brief at most 20,000 Unicode code points; 20 confirmed requirements; extracted delivery text at most 20,000 code points per file and 100,000 in aggregate. P1 brief-PDF intake is limited to 5 MiB and the validated native-text parsing path. Specific decoder/resource limits remain in TRD.

Caps are operational bounds, not evidence that every within-cap file is parseable or semantically reviewed. The UI tells users which intake or extraction was blocked and why; over-budget text is rejected rather than silently clipped. Do not silently reduce the scope and then claim full review.

## 5. Core workflow and review model

1. **Brief:** paste the agreed text, label its source, and preserve an immutable snapshot.
2. **Checklist:** AI proposes atomic requirements with literal quotes. User corrects, splits/combines where appropriate, identifies manual checks and confirms a versioned baseline.
3. **Packet:** select bounded files; see inventory, supported properties and extraction limitations.
4. **Evidence:** AI proposes semantic associations. Technical inspections and exact source spans remain inspectable. No proposal pre-approves itself.
5. **Review:** the user confirms useful associations, rejects wrong ones, notes manual verification or records a reasoned exception.
6. **Handoff:** export a client-readable file map with decisions, usage notes, evidence and unresolved/unchecked items. No automatic sends.
7. **Revisit:** restore a workspace or replace files; changed content/baselines invalidate dependent review decisions.

### State principles

The canonical baseline states are **draft / approved / stale**; match-decision states are **unreviewed / confirmed / rejected / stale**; file-inspection states are **queued / running / inspected / blocked**; check outcomes are **pass / fail / unknown / not_applicable**; human-disposition states are **unresolved / satisfied / needs_work / not_applicable**. UI language may say “needs attention” or “manually verified” where appropriate, but must preserve the distinction between a check and a human decision. A human exception is recorded separately and never converts a failed technical inspection into a pass. Job states and exact transition rules are authoritative in the TRD.

There is no “100% contract complete” score. Summary counts describe review progress and unresolved items only. A manual-only requirement remains visibly manual even after the user records verification.

## 6. Functional requirements and acceptance cases

| ID | Requirement | Acceptance example / release evidence |
|---|---|---|
| **FR-01** | Preserve brief source and snapshot. | Pasted text with source label survives reopening unchanged; editing creates a new baseline candidate rather than replacing the approved source silently. |
| **FR-02** | Produce evidence-backed candidates through the actual selected model. | Every AI-derived candidate contains a valid source ID and exact quote present in that source. A fabricated quote, malformed response, refusal or timeout is rejected/marked failed; it creates no confirmed requirement. Manual checklist entry remains available. |
| **FR-03** | Require explicit baseline confirmation. | User may edit titles/checks, mark manual or reject candidates. A human-added requirement without a brief quote is labeled user-added. Packet review cannot represent an unconfirmed candidate as agreed scope. |
| **FR-04** | Support atomic checks without discarding compound scope. | “Two logo variants as SVG and transparent PNG” can be represented as related checks for variants/formats/transparency. Parent quote remains available; the user confirms whether two variants or four files are required. AI cannot choose that ambiguity silently. |
| **FR-05** | Bound and identify intake. | Too-large/too-many/unsupported files are rejected with a specific explanation and do not erase accepted inventory. A renamed JPEG does not pass a PNG-format requirement. Corrupt, encrypted or textless PDF yields explicit unknown/unchecked reasons. Over-budget extraction is explicitly blocked, with no silent clipping or partial-success content review. Blocked, incomplete or unavailable extraction cannot establish that a requested passage is absent. Limits are set once in TRD/config, surfaced in UI and tested at boundaries. |
| **FR-06** | Inspect supported technical properties. | Actual image dimensions and decoded transparency are checked against approved constraints. A PNG with an alpha channel whose pixels are all opaque fails “transparent background”; at least one nonopaque pixel is necessary but not proof of a correctly removed background. A JPEG cannot satisfy transparency. SVG is parsed safely, never embedded as uploaded markup. |
| **FR-07** | Treat count and duplication according to intent. | Three renamed copies of identical bytes do not silently satisfy “three distinct launch images.” The user sees duplicate hashes. Exact duplicates may be legitimate deliverables in a repeated-location requirement; accepting this needs an explicit reason. Hash identity detects exact duplicates only, not visually similar images or distinct creative variants. |
| **FR-08** | Propose inspectable semantic associations. | A requirement about editing contact details can match a quoted passage in `maintenance-notes.pdf`. A plausible `final-guide.pdf` filename alone is insufficient. Proposed links display file identity, excerpt and limitation; invalid/out-of-source quotes cannot be promoted to evidence. |
| **FR-09** | Support uncertainty and multiple artifacts. | User can select several files, reject all candidates, select another inspected file or leave unresolved. No automatic best-match acceptance; unsupported/missing text is not treated as proof of missing content. Scores, if retained internally, are not presented as certainty percentages. |
| **FR-10** | Keep manual checks and exceptions honest. | “Contact form works” is marked manual/unchecked. User can record “tested on staging” with a note, or accept an opaque logo by agreement. Export retains manual provenance, technical mismatch and exception reason. The app does not certify the claim or hide its limitation. |
| **FR-11** | Invalidate stale decisions. | Any active packet or approved-baseline mutation makes all current P0 match confirmations and human dispositions stale and requires review. Changed files receive new inspections; prior evidence and decisions stay in history. Even an unchanged-byte rename counts as a packet mutation because filenames affect mappings. Ambiguous duplicate names require disambiguation. |
| **FR-12** | Recover state without silent corruption. | Restart/reopen preserves confirmed scope, packet identities and decisions. Partial/corrupt state shows a recoverable error; it never invents empty-success state. Recovery is explicit and does not overwrite another workspace silently. |
| **FR-13** | Export usable and complete results. | JSON preserves revisions, hashes, provenance and all unresolved/manual/exception states; Markdown/printable handoff provides filenames, user-confirmed usage notes and outstanding actions. Original brief text, model prompts and private source conversations are excluded from client-facing output by default; the preview makes included evidence explicit. Export with unresolved items requires an explicit acknowledgement and includes them prominently. Unreviewed proposals are not exported as established facts. |
| **FR-14** | Provide truthful execution/privacy status. | User sees model readiness, progress, cancellation/error and the selected model/revision. Ordinary operation uses local inference and local files, with no hosted model fallback or analytics upload. Initial dependency/model download is disclosed. Public sample never invites private-file upload to a nonexistent model service. |
| **FR-15** | Make review accessible and actionable. | Keyboard users can complete intake through export with visible focus and labeled controls. Evidence has readable source context; color is not the sole status cue. Long filenames, empty states, model failure and parser rejection remain usable at narrow viewport widths. Reduced motion disables decorative motion; critical controls/status do not depend on animation. |

## 7. Illustrative end-to-end release fixture

Use a synthetic, redistributable packet, clearly labeled fictional:

- Brief: transparent PNG + SVG logo, three distinct 1080 × 1080 launch images, and a contact-editing guide.
- Faulty packet: opaque PNG; one wrong-size image; a renamed exact duplicate; a misleadingly named empty guide; useful editing instructions in a differently named text document.
- Review: confirm correct semantic guide match, see real dimension/transparency/duplicate findings, reject the misleading filename, leave unsupported requirements open.
- Corrected packet: replace only the defective files. Current review decisions become stale under the conservative P0 packet-mutation rule; historical unchanged-file evidence stays attributable. The user reviews the current packet and exports a new truthful manifest.

Include a clean packet too: the app must not manufacture findings merely to make the demo dramatic. Synthetic evidence is not a real customer case.

## 8. Commercial hypothesis and free-budget boundary

Potential offering: a paid local tool, studio-template setup or support package that reduces avoidable delivery preparation/rework. Pricing is deliberately unset until the customer task and installation burden are understood. Ask about current cost and willingness to use first; test a clearly hypothetical price afterward without reporting it as revenue.

This week's spending allowance is **zero new charges**. Use permissively licensed local dependencies/weights and existing hardware; any account-specific credit requires verified terms, quota and no-overage behavior before reliance. No checkout, card, paid GPU, paid narration or payment collection. Local inference still has hardware, storage, electricity and support costs. Earlier model generations and each artifact have their own licenses; pin and record the chosen revision/license in the technical/license records.

## 9. Release gates, risks and decision rights

- **Problem gate:** proceed with synthetic engineering immediately; narrow/pivot after real feedback if packet omissions are not the tester's pain. Do not turn interest into an adoption claim.
- **Model gate:** actual benchmark selects the model; invalid evidence can never escape validation. Drop the Gemma category if Gemma is not meaningfully used.
- **Parser gate:** unsupported formats fail closed, with clear unchecked reasons; importing content never executes it.
- **Workflow gate:** full fixture, stale-decision and recovery paths pass; unresolved exports stay truthful.
- **User-evidence gate:** no testimonial, private artifact, client detail or measured savings is published without appropriate permission and actual evidence.
- **Submission gate:** one original Week 2 entry, truthful provenance, linked reproducible release, verified rules and publication before deadline. Personal eligibility/terms confirmation is handled separately by the owner when required.

The owner approves product direction, any actual budget change and publication/legal declarations. Engineering agents can develop/test reversible implementation within the authorized plan. They cannot fabricate customer evidence or guarantee mergeability, acceptance or a contest win.

## 10. Sources and linked planning material

- [Week 2 challenge](https://dev.to/challenges/hacktoberfest-week2-2026-10-12) — theme, writing priority and template.
- [Week 2 specific rules](https://dev.to/page/hacktoberfest-week2-2026-10-12-contest-rules) — entry window and requirements.
- [General rules](https://dev.to/page/official-hackathon-rules) — eligibility and permissions.
- [Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4), [license](https://ai.google.dev/gemma/apache_2) — candidate model family, not an implementation claim.
- `../HF-WEEK2-RECOMMENDATION.md` and `../HF-WEEK2-RULES.md` — source research dated 13 October 2026.
- [original 06-USER-VALIDATION.md](planning/06-USER-VALIDATION.md) — evidence protocol and claims boundaries.
