# HandoffReady — QA, model evaluation and acceptance plan

Planning baseline: 13 October 2026, Asia/Kolkata. This document defines work to perform, not tests already passed or customer results already obtained. Read with the PRD, TRD and risk/release plan. The limits and state names below are aligned with the technical planning agent's contract; any later TRD change must update the corresponding tests.

## 1. What quality means

The product helps a freelancer prepare a delivery packet. It does not certify contractual completion, visual quality, accessibility, copyright clearance or a working website. A valid release keeps evidence and human decisions attached to the exact brief and delivery files that were reviewed. It also makes unchecked work visible.

The most damaging failures are a misleading completion claim, lost client work, leakage of private material, or stale evidence appearing current. Protect these before optimizing model speed or interface polish.

Use three separate acceptance layers:

1. **Software correctness:** deterministic inspectors, bounded parsing, state transitions, persistence, deletion and export behave as specified.
2. **Model usefulness:** a real pinned open model produces useful extraction/matching suggestions on unseen cases, with measurable correction burden.
3. **Customer usefulness:** a real freelancer can prepare and understand the handoff, and identifies a concrete improvement over their existing practice.

Passing one layer does not establish the others. Valid JSON is not a correct interpretation, and a user liking the idea is not a sale.

## 2. Test fixtures and privacy

Keep public fixtures synthetic and label them as such. Use an explicitly permissioned, redacted historical delivery for private evaluation only. Record what may be processed locally, what may be shown in a demo and what may be quoted in the submission separately. Permission to test does not imply permission to publish.

Every fixture packet needs an immutable brief, file hashes, expected explicit requirements, intended artifact associations, supported technical checks, and manual/unknown requirements. Include the reason for each expected outcome. Do not derive expected results from model outputs or implementation behavior.

For a small benchmark, plan **six development packets and twelve held-out synthetic packets**, aiming for at least forty explicit requirement instances across the held-out set. These are collection targets, not existing samples. Include a separate real-user packet if consented; report its results independently. Keep prompt tuning confined to the development set. If a held-out case is used to fix the prompt, retire it from held-out reporting and record that change.

An independent reviewer checks the fixture answers before evaluation. Ambiguous requirements are marked ambiguous rather than forced into a convenient expected match. Synthetic packets cannot establish prevalence of real delivery problems.

## 3. Meaningful regression and boundary coverage

| Area | Required cases | Expected safety/behavior |
|---|---|---|
| Brief extraction | Negation, optional versus mandatory, revised quantities, alternatives, exclusions, duplicate sentences, conflicting instructions | Preserve literal evidence and ambiguity; do not silently invent or reconcile obligations |
| Source evidence | ASCII, composed/decomposed Unicode, emoji, curly quotes, CRLF, repeated quotations, PDF page breaks | Quote and codepoint offsets resolve into the immutable extracted text. Never normalize into a false match; navigate the correct occurrence |
| Evidence validation | Missing source IDs, fabricated quotations, out-of-range offsets, stale parser revision, changed source hash | Reject invalid evidence and retain user-visible reason; it cannot become a confirmed baseline |
| File identity | Same content under two names; same name with different content; reordered inventory; deleted/replaced artifact | Detect exact duplicate hashes and do not count duplicates as separate unique deliverables by default; explain the count policy |
| PNG/JPEG | Correct and wrong dimensions, corrupt/truncated image, huge pixel dimensions, grayscale, palette PNG with transparency, fully opaque alpha channel | Inspect decoded format and actual alpha behavior. An alpha channel alone does not prove transparent pixels; JPEG cannot satisfy transparent PNG. At least one non-opaque pixel proves only that narrow property, not proper background removal |
| SVG | Correct dimensions/viewBox, missing dimensions, conflicting dimensions, script/event attributes, external references, XML entities, malformed XML | Metadata only through bounded safe parsing; no DOM embedding, external fetch or script execution. Unknown raster-export size stays unchecked |
| PDF | Native text, blank page, image-only PDF, malformed/encrypted PDF, excessive pages, huge extracted text, pathological objects | Bounded subprocess/time/memory handling; image-only extraction is unsupported in MVP, not an empty brief or evidence of missing content |
| Actual file type | `.png` name containing PDF/text, wrong extension, double extension, non-UTF-8 text, executable/HTML/ZIP input | Detect supported content conservatively and explain mismatch; reject unsupported formats; do not execute or unpack them |
| Quantity/type checks | Three images with a renamed duplicate, alternatives such as SVG **or** PNG, mixed dimensions, multiple variants | Match the confirmed human interpretation and count policy. Avoid counting one file twice to satisfy distinct variants automatically |
| Model outputs | Invalid schema, partial stream, unknown artifact ID, unsupported inspection key, fabricated paragraph, excessive result length | Validate and cap before storing proposals; abstain/retry only within bounded policy; do not quietly convert failure into success |
| Prompt injection | Brief or artifact text says “ignore instructions”, requests file access, or demands all checks pass | Treat content as data. Model has no tools/network/file access; source and artifact validation remain enforced |
| State invalidation | Edit baseline after model run; replace file after confirmation; packet changes during inspector/model request | Increment packet/baseline revision and invalidate affected decisions. Old results may be retained as history but cannot enter current export |
| Cancel/retry | Cancel during parsing/inference, double click, request timeout, restart mid-job, response arrives after cancel | No stale success, duplicate artifacts or partial write. Job identity/revision checked before committing; retry remains deliberate |
| Recovery | Reload with draft, interrupted atomic write, corrupted stored state, disk full/read-only directory, migration failure | Do not overwrite recoverable work. Explain recovery limits and provide safe export/backup path; failed save never claims “saved” |
| Export | No files, unresolved requirement, changed evidence, user notes with HTML/Markdown, unicode filenames, duplicate basenames | Preserve unresolved/manual work and current revisions. Escape rendered text; references identify actual artifacts; no private local paths or model chain-of-thought |
| Local security | Non-loopback Host/Origin, cross-origin mutation, traversal names, dangerous symlink if path import supported | Reject unauthorized mutations and traversal; imported bytes remain inside app-managed storage; loopback is not itself CSRF protection |
| Deletion | Cancel deletion, confirmed project deletion, active job during deletion | Cancel preserves work; confirmed deletion removes defined copies/history, stops writes and states what downloaded exports remain outside app control |

Boundary tests use **limit − 1, limit, limit + 1** where meaningful: file bytes, packet total, file count, PDF pages/text length, decoded pixels, parser wall time, model input/output and retry count. Test both preflight rejection and data that expands only during parsing. Wall-clock timeout alone does not impose a memory limit.

Exact duplicate detection does not find perceptually similar but recompressed images. Distinct hashes do not prove distinct visual variants. Treat both as explicit limitations; do not claim the MVP catches every duplicate or verifies design variants.

### Aligned limits and states

P0 brief intake is pasted text. Native PDF brief import is P1, behind its own extraction gate; the reserved limit is 5 MiB and ten pages. Native-text delivery PDFs remain P0 after the parser gate. Use pypdf, Pillow and defusedxml in bounded workers; SVG is inspected as metadata only.

| Contract | Boundary cases to generate |
|---|---|
| 30 delivery files; 50 MiB active original bytes; 10 MiB per delivery file | 29/30/31 files; total and per-file bytes just under/at/over each cap; no omitted extra file silently disappears |
| PDF ten pages; text/SVG 1 MiB | Nine/ten/eleven pages; file byte boundaries; native text versus scan/encryption/corruption |
| PDF decoded content 5 MiB/page and 20 MiB/file | Content streams that expand beyond either limit, including tiny compressed originals; decoding remains in the time/RSS-bounded worker |
| Images 10,000,000 decoded pixels; 10,000 pixels per side | Area cap below/at/over, including extreme aspect ratios and compressed small files with excessive decoded size |
| Brief 20,000 Unicode codepoints; delivery text 20,000/file and 100,000 aggregate | ASCII and emoji boundaries, aggregate expansion; return explicit blocked/unsupported reason instead of silent truncation |
| Twenty confirmed requirements | Nineteen/twenty/twenty-one; user must deliberately narrow the checklist rather than losing extracted obligations |
| One parsing worker; PDF 20 s, image 5 s, text/SVG 3 s, packet 120 s; worker RSS 512 MiB | Worker time/memory termination, continued safe app operation, canceled queued work and missing/partial outputs |
| Model context 8,192 tokens; ≤6,000 input and ≤1,500 output tokens | Tokenizer-counted system/schema/data totals at boundaries; deterministic batching and explicit unprocessed coverage instead of silent truncation |
| Model request 60 s; extraction/matching job 120 s; at most one structural repair call inside budget | Timeout across initial/repair requests; no time-budget reset or hidden repeated retries; malformed output never passes silently |
| Ten active projects; 1 GiB app-original-byte quota | Project count and stored-byte boundaries including retained file versions; failed admission preserves old work. Monitor DB/text/export overhead separately |
| Generated export ≤2 MiB per format | JSON/Markdown/HTML size boundaries, escaped expansion, excessive notes; safe failure retains the prior export and current project |

Inspection states are `queued/running/inspected/blocked`; check outcomes are `pass/fail/unknown/not_applicable`; baseline states are `draft/approved/stale`; proposal-review decisions are `unreviewed/confirmed/rejected/stale`; human dispositions are `unresolved/satisfied/needs_work/not_applicable`; jobs are `queued/running/succeeded/failed/cancelled/interrupted/superseded`. Test the allowed transitions and reject impossible current-state writes. Check `pass` is a narrow inspector result, never automatic whole-requirement confirmation. A human `satisfied` decision with a technical failure preserves that discrepancy; a manual check remains technically `unknown/manual_required` even when human-confirmed.

Exports are Markdown, JSON and printable HTML from one immutable database snapshot and the same client-safe privacy projection. The format and current revision must agree across all three; unresolved work requires explicit labeling/acknowledgment, not an automatic complete verdict. Verify that P0 exports omit source quotations/full briefs, private conversation text, prompts, credentials and local paths. Explicit source sharing is P1 behind a separate privacy review; P0 cannot silently add excerpts. Private database audit history is not the client projection.

## 4. Complete workflow checks

Run these against the actual app in a browser, not only mocks:

1. Start a new project, paste the sample brief, inspect extraction evidence, correct an ambiguous requirement and confirm the baseline.
2. Import a defective synthetic packet; verify wrong dimensions, opaque PNG and duplicate count with visible file evidence.
3. Run real model matching; inspect the paragraph behind a semantically useful suggestion, change another match and leave unsupported website functionality manual.
4. Correct a file and reimport; verify the old decision is invalidated, then recheck and export the current handoff.
5. Reopen the project and compare stored revisions; verify a canceled/stale job cannot overwrite the current state.
6. Export with unresolved/manual work and verify that the recipient sees the limits. No green “all complete” indicator may erase those limits.
7. Repeat with keyboard navigation, screen-reader landmark/label inspection and reduced motion. Exercise error recovery and narrow-screen reading/export; a desktop file-inspection app need not promise mobile local inference.

Record app commit, browser/version, operating system, model/runtime identifiers, exact fixture, expected result and observed result. Screenshots are useful evidence of UI but do not prove persistence or model execution.

## 5. Real model and baseline protocol

Compare a pinned Gemma candidate and a licensed Qwen fallback using the same packet split, task schema, bounded context and artifact text. Record actual model revision, GGUF hash, quantization, runtime build, prompt/schema version and decoding settings. A recorded example must identify whether it is a live run, stored result or replay.

Use two inexpensive baselines:

- **Rule baseline:** file extension/content checks, filenames, literal token matching and deterministic metadata. Its mapping rules are documented and frozen before held-out evaluation.
- **Manual workflow baseline:** freelancer’s normal checklist/file review on a comparable packet. Match task scope and do not report repeated inspection of the same familiar packet as unbiased time savings.

Measure separately:

| Metric | Definition and denominator |
|---|---|
| Explicit requirement recall | Correct explicit requirements extracted ÷ manually labeled explicit requirements. Human-review ambiguity is reported separately |
| Unsupported extraction | Proposed requirements absent from the brief ÷ all proposed requirements, with raw counts |
| Evidence validity | Proposals with resolving source ID/hash/offset/quote ÷ all proposals. This establishes traceability, not semantic correctness |
| Match precision | Correct proposed artifact associations ÷ proposed associations; a one-to-many requirement is scored against labeled permissible associations |
| Match coverage | Explicit requirements with at least one correct proposal ÷ explicit requirements requiring artifact matching |
| False completion | Requirements incorrectly represented as satisfied in a current export ÷ exported requirements, plus raw incident count and cause |
| Correction burden | Confirmed/rejected/edited proposals and active review minutes per packet. Report untouched manual/unknown items separately |
| Technical defect coverage | Supported planted defects caught ÷ supported planted defects. Report unsupported defects in a separate denominator |
| Latency | Cold startup/download separately from first/warm model runs; include input size, sample count, median and observed maximum |
| Resource use | Observed peak process memory, disk footprint and hardware; distinguish measured peak from estimates |

Do not describe model scores as probabilities/confidence unless calibrated. On a small test set, publish raw counts and case failures instead of implying population accuracy. Schema-validity and evidence-validity rates must never be presented as model accuracy.

**Selection gate:** retain the model only when it adds useful semantic matches missed by rules and the freelancer can inspect those matches at acceptable correction cost. Before selecting Gemma, seek at least three clear held-out semantic wins, no safety-gate failures, and no materially greater false-match burden than the documented alternative. These are practical acceptance targets for a tiny evaluation, not statistical proof. If no candidate provides useful advantage, narrow the task or stop the AI-centered entry rather than conceal the result.

Set the performance target after the first real hardware run. A suggested usability target is warm proposal generation within thirty seconds for the defined small packet on the owner’s Mac; if unmet, reduce context/scope and explain the measured limit. Never select a category solely because the model has the preferred sponsor name.

## 6. First-user study

Recruit the reachable web/design freelancer for one consented historical packet and a short prototype session. Ask about the last actual delivery, omissions and their current checklist before demonstrating the app. This reduces leading feedback.

Observe setup/import difficulty, time spent verifying suggestions, defects noticed/missed, misleading flags, evidence comprehension and export usefulness. Ask which next project they would use it for and only then ask about a concrete hypothetical price. “Would pay” is an interview statement, not revenue; a synthetic planted defect is not a real defect found for a client.

Do not ask the participant to send live client work publicly. Use separate publication consent for quotations, screenshots and names. If the user cannot participate, report “no first-user trial completed” and provide synthetic evaluation honestly; this does not automatically disqualify an entry under the researched rules.

## 7. Stage reviews and release gates

| Gate | Implementer responsibility | Independent review responsibility | Blocking evidence |
|---|---|---|---|
| Feasibility | Create labeled packets and run real models | Challenge labels, privacy assumptions and baseline fairness | No actual useful open-model contribution or unbounded runtime |
| Ingestion/evidence | Test inspectors and quote binding | Attack malformed inputs and stale-source examples | Unbounded parsing, invalid evidence accepted, privacy exposure |
| Review/persistence | Verify state transitions and recovery | Run change/cancel/reload/export cases against browser and stored state | Lost work, stale approval, false save or falsely satisfied export |
| Usability | Run keyboard/error/narrow-screen flow | Observe a first-time task without coaching | Core task inaccessible or unresolved work visually hidden |
| Release | Freeze commit, run relevant suite and actual-run demo | Reconcile claims, source/licenses, release artifact and submission | Open P0/P1 defect, unverified claim, rights mismatch or absent required artifact |

After each stage, the parent/integration owner reconciles findings and runs the combined workflow. Reviewers own evidence and findings; they do not approve their own change as independent review. One person may cover roles sequentially when necessary, but document that limitation.

**P0:** data loss, client-data leak, arbitrary execution, stale/rejected evidence exported as current satisfaction. **P1:** wrong supported inspection, broken source navigation/confirmation, failed recovery, misleading status. Both block release. A P2 cosmetic or non-core defect may be deferred only with a written impact and user-visible limitation where relevant.

All required relevant tests must pass on the release commit. New failures reopen the affected gate; unchanged checks need not be rerun endlessly. A zero-failure test suite does not establish zero risk or guarantee a contest result.

## 8. Evidence bundle to produce

- Fixture manifest and privately held consent record; no private client files in Git.
- Automated test summary and actual browser workflow checklist tied to the release SHA.
- Model/baseline evaluation table with raw denominators, hardware and failures.
- Reviewer findings and resolution links, including consciously deferred issues.
- Real-model demonstration, clearly labeled public sample and reproducible setup instructions.
- Optional first-user record with exact publication permissions and acknowledged study limitations.

Rules and foundation context: [Week 2 brief](https://dev.to/challenges/hacktoberfest-week2-2026-10-12), [specific rules](https://dev.to/page/hacktoberfest-week2-2026-10-12-contest-rules), [llama.cpp server documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md). Further implementation-specific limits belong in the TRD and must be reflected here before coding.
