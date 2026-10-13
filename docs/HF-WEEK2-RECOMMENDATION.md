# Week 2 decision: HandoffReady for freelance web and design delivery

Research completed 13 October 2026, Asia/Kolkata, by a rules researcher, foundation researcher, customer/idea researcher, and parent integration review. The owner confirms access to a freelancer or small agency doing web development and design. Research only: no new project built, models benchmarked, users tested, payments taken, or Week 2 submission published.

## Recommendation

Build a new, original application called **HandoffReady** (working name): an evidence-backed check of a freelancer's final delivery package against their approved brief. Use licensed open libraries and a locally run open-weight model. Do not fork and rebrand an existing business application or rebuild OCR/model infrastructure.

The recommendation is conditional on a short practical test: the contact actually delivers files/documentation and has experienced omissions, wrong exports, version ambiguity, or handoff confusion. If that is not their problem, use the alternative corresponding to their real workflow. Customer access is a major advantage, not proof of demand. No researched idea comes with defensible winning odds.

## Contest fit and timing

The official theme is Side Hustle: useful paid utility with open AI central to the new product. Writing matters most, and firsthand user feedback is valuable. Reuse is encouraged when the new work is significant and credited. The FAQ requires a new repository; an old project or contribution PR is unsuitable. [Brief and reuse FAQ](https://dev.to/challenges/hacktoberfest-week2-2026-10-12).

The specific entry window is 12 October noon PDT through 18 October 23:59 PDT: **13 October 00:30 IST to 19 October 12:29 p.m. IST**. The entry needs a published template post, code link, deployed project or video, plausible paying user, and explanation of openness. Only one entry counts. Schedule submission for 18 October evening IST. [Specific rules](https://dev.to/page/hacktoberfest-week2-2026-10-12-contest-rules).

These rules support an original product using existing dependencies. A dependency's older development history does not make the new application an old project. A full fork with inherited product/history is a less clear choice; no eligibility ruling for that route was obtained.

## The actual customer job

A freelancer agrees to deliver a website/design kit, then sends a folder containing exports, documentation, and links. The client subsequently asks which files are final, where an asset is, or why an export differs from the brief. The proposed tool makes that package understandable and checks the supported technical requirements before delivery.

Example approved brief:

- Two final logo variants, exported as SVG and transparent PNG.
- Three 1080 × 1080 launch images.
- A site handover guide with instructions for updating contact details.

Example packet contains one PNG with no transparency, two square images, a duplicate renamed as a third image, and a PDF without the requested editing instructions. AI proposes which files/paragraphs correspond to each brief requirement. The app verifies dimensions, actual type, transparency, duplicates and exact source quotations. It raises unresolved requirements and asks the freelancer to confirm the intended files. These are illustrative test cases, not measured findings or a real client's work.

Do not infer that a missing named document proves missing knowledge; relevant instructions may be in another artifact. Conversely a file named `final-guide.pdf` does not prove its contents satisfy the requirement. Both failures create a good demonstration of why model matching needs file evidence and human confirmation.

## Core workflow

1. Paste the agreed brief and mark its source. Support native text PDF only after extraction is validated.
2. Open AI extracts deliverable candidates with literal source quotes. User corrects and confirms the checklist before it becomes the comparison baseline.
3. Select delivery files. Inspect a bounded set of supported PNG/JPEG/SVG/PDF/text/Markdown artifacts without executing them.
4. Model proposes semantic requirement-to-artifact matches using names, inspected metadata and readable text. Proposed matches remain distinct from confirmed matches.
5. Deterministic checks inspect file type, dimensions, transparency, page/text presence, counts, duplicate hashes and package changes. Unsupported requirements remain explicitly unchecked.
6. Freelancer resolves missing/ambiguous items, approves matches, and exports a client-readable handoff manifest with filenames, usage notes, evidence and unresolved items.
7. If a file changes, invalidate its old approval/check result. A new packet can reuse a confirmed checklist without silently inheriting old evidence.

This is delivery preparation, not a certificate of contract completion. A website form, mobile behavior, business logic, deployment availability, visual quality, copyright clearance or accessibility compliance cannot be certified from a delivery folder. Put these in manual verification where required. No invoice, payment processing or client messaging is necessary for the MVP.

## Why this could compete

The demo can show a complete task and an inspectable result: one agreed brief, one actual packet, a missing or wrong artifact, correction, and a usable handoff. Its originality would lie in the connected workflow, source validation, technical inspections and artifact-bound review—not a claim that nobody has built a handoff tool.

A local model can interpret a natural-language requirement such as “instructions so the client can change their business contact details” and suggest the relevant paragraph in a document named `maintenance-notes.pdf`. A pure filename rule may miss this. This semantic advantage must be measured; if the model adds no useful matching beyond rules, the open-AI-core case is weak.

The potential customer receives a reusable operational output, not just advice in a chat window. Privacy and no metered inference charges may matter for client work. They are product hypotheses until the freelancer demonstrates value.

## Market reality and alternatives

| Concept | Potential buyer and output | Competitive concern | Decision |
|---|---|---|---|
| HandoffReady | Web/design freelancer; checked delivery packet and client manifest | Handoff, versioning and AI reviews already exist | First choice if packet errors are a real recurring problem |
| Revision Ledger | Designer; source-linked unresolved contradictions and version decisions | Framebase and revision reconciliation products overlap closely | Second choice only if a real multi-stakeholder conflict is the main pain |
| Copy Manifest | Web/design/marketing agency; approved facts versus HTML/PDF/caption drift | Existing proofing and brand checking products; meaning equivalence is hard | Good backup for stale prices, qualifiers, offer dates and required copy |
| Scope Evidence | Fixed-price freelancer; request beside exact approved scope passage | Multiple nearly identical scope products and a related Week 2 entry | Deprioritize; do not present generic scope detection as novel |
| Baker Board | Home baker; confirmed order amendments into a packing sheet | Existing bakery admin category; no reachable tester confirmed | Reserve for another validated customer, not this week's default |

[ScopeGuard](https://www.scopeguard.ai/) already markets client-message/SOW comparison and change orders. [Another ScopeGuard product](https://thescopeguard.com/blog/how-to-handle-scope-creep-as-a-freelancer) advertises pasted-request verdicts with quoted clauses. [Framebase](https://useframebase.com/) advertises feedback organization. [Nexibeo's revision blueprint](https://nexibeo.com/solutions/creative-revision-reconciler/) describes version-linked contradictory feedback; it labels demand/pricing as assumptions, not verified traction. These invalidate a broad uniqueness claim, not the possibility of building a better narrow product.

Handoff is also an established category: [Zeplin](https://zeplin.io/pricing/) offers existing handoff/review features. [Figma's official export documentation](https://help.figma.com/hc/en-us/articles/13402894554519-Export-formats-and-settings-for-static-designs) confirms real format/scale/transparency constraints; [Webflow's checklist](https://university.webflow.com/resources/checklists/enterprise-site-checklist) shows broader handoff requirements. Our niche is checking an existing final packet without requiring clients to migrate into another workspace. This distinction needs user validation.

Public-entry sampling was limited to three author-written entries, not an exhaustive or independently tested field: [Scope Slip](https://dev.to/itsdanielsultan/scope-slip-turns-a-request-into-a-work-outline-35b), [Cashcast](https://dev.to/starknight/cashcast-which-invoices-will-be-paid-late-tabpfn-on-a-laptop-checked-month-by-month-2d21), and [sifter](https://dev.to/max_ilands/sifter-a-23-mb-model-that-sorts-your-expenses-locally-for-free-2fg8). The practical lesson is to show real baselines and failures, not merely a local-model badge.

## Reuse versus scratch

**Build ourselves:** data model, user-confirmed requirement baseline, match/review states, exact-quote validator, packet manifest/checksum logic, technical validators, export, recovery, tests, evaluation cases, UX, and real-user study.

**Reuse:** [llama.cpp](https://github.com/ggml-org/llama.cpp) for MIT-licensed local inference; a selected [Gemma 4 E2B instruction model](https://huggingface.co/google/gemma-4-E2B-it) or [Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B) for Apache-2.0 open weights; [PDF.js](https://github.com/mozilla/pdf.js) or [Docling](https://github.com/docling-project/docling) for supported text extraction after choosing one tested path. Parser code and every downloaded model have separate licenses. Pin versions/revisions and preserve licenses/notices.

The verified Mac is Apple M5 Pro with 24 GiB memory. Small quantized local inference is plausible, but no latency/memory/task-quality benchmark has been performed. Gemma E2B's effective parameter name does not describe total parameter/storage size. Test its official Q4 artifact against Qwen on identical bounded cases before deciding.

Avoid large agent frameworks unless tool orchestration is necessary. Text-first input avoids the extra correctness burden of OCR and voice notes. Do not start with Figma OAuth, live email/WhatsApp integrations, remote site crawling, scanned briefs, PSD interpretation, full repository audits or automated sends. These consume the week without proving the core benefit.

## Free-tier and category choice

Primary target: overall challenge and **Best Use of Gemma**, only if actual Gemma inference passes the task test and is used in the finished workflow. Current Gemma 4 official weights are Apache-2.0; earlier Gemma terms differ. A Qwen fallback could preserve product quality while dropping the Gemma category. [Official Gemma 4 license](https://ai.google.dev/gemma/apache_2).

Do not use a partner merely to increase the category count. TabPFN's current noncommercial restrictions are a poor match for an operational paid-product pilot. ElevenLabs Free output rights remain unsuitable for a straightforward commercial-output assumption. Tinker credits/quotas have not been verified and fine-tuning is premature without data. Full details and primary links are in the rules report.

A static hosted frontend is not hosted live model inference. Best free-budget plan: a complete real local app tested on the owner's machine, a real-model video, and an explicitly labeled public sample review. A hosted arbitrary-input model service is optional only after a genuinely free allocation and limits are verified. Local execution has hardware, storage, electricity and support costs; do not describe the business as costless.

## Failure modes and planned remedies

| Risk | Remedy and evidence |
|---|---|
| AI invents a brief requirement or quote | Validate literal substring/source ID; reject invalid evidence; require baseline confirmation |
| A plausible filename causes a false match | Inspect actual metadata/text; display evidence; human selects final artifacts |
| AI falsely reports full completion | No global certified-pass score; unsupported/manual requirements stay open |
| Changed files inherit old approvals | Bind decisions to hashes and invalidate upon change |
| Malicious document/archive/script | Bounded file parsing, never execute uploads, no raw SVG embedding or unbounded archive extraction |
| Slow setup ruins first-use experience | Early real hardware benchmark; one clear setup path; demonstrate cold and warm latency |
| UI turns into another project manager | One task: brief → files → exceptions → handoff; no dashboards or empty integration menus |
| User likes idea but would not use/pay | Compare on real work, count corrections/false flags, ask about next project and price after use |
| Overclaiming uniqueness or winning | Describe measured result and limits; do not invent odds, sales or untested advantages |

## Evidence and build stages

**13 October:** ask the freelancer about their last delivery problem; inspect one consented/redacted packet. Label requirements manually. Run bounded model extraction/matching baseline. Kill or narrow the idea if file defects are not their pain or AI adds no value.

**14 October:** implement import, source quotes, confirmed checklist, file inventory, deterministic inspections and model match proposals. Review architecture and failure handling.

**15 October:** build exception review, corrections, hash-bound decisions, exports and persistence/recovery. Test ambiguous names, misleading extensions, duplicate contents and changed files. Separate prompt-development examples from held-out cases.

**16 October:** conduct a real user trial. Compare manual preparation to the tool on similar tasks; avoid reporting repeated-task familiarity as measured time savings. Record setup time, review time, missed defects, false flags, corrections and whether the output is useful. No invented testimonial or payment. Publish only permissioned/redacted evidence.

**17 October:** act on feedback and verify keyboard/mobile reading, source navigation, privacy/error messages, print/export and repeat use. Polish the useful flow. Capture an actual model-run video.

**18 October:** freeze a tested release, finish the specific story, cite upstream work, describe model failures and measured economics, and publish before the official deadline. Research is not a commitment that every stage is already complete.

The strongest submission story would be: a real freelancer's delivery problem, a narrowly built tool, a concrete mistake caught, a correction, and an honest explanation of what the open model contributed. This is the recommendation; customer evidence and implementation performance remain to be earned.

## Supporting reports

- HF-WEEK2-RULES.md — official requirements, deadline, categories and license/free-tier constraints.
- HF-WEEK2-FOUNDATIONS.md — six examined libraries/models, maintenance/license/runtime details and benchmark gates.
- HF-WEEK2-IDEAS.md — deeper customer/competitor analysis, alternate ideas and bounded entry comparison.
