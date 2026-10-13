# Week 2 customer and idea examination

Research date: 13 October 2026, Asia/Kolkata. This is a proposal, not evidence of users, sales, measured savings, or a winning probability. Parent task reports a reachable freelancer/small agency; the person does web development and design; representative material and the actual recurring pain remain to be established. That access changes the shortlist materially.

## Finding

The strongest strategy is a narrow tool tested on that person's actual work, with traceable evidence and an honest comparison to their existing process. Generic scope detection and feedback reconciliation are already crowded. An attractive UI plus local AI is insufficient differentiation. None of the ideas below is proven novel or proven payable. Build a new application during this challenge; reuse properly licensed infrastructure, not another product's complete workflow with renamed branding.

## What the theme rewards

The official challenge asks for open AI that performs essential work for a plausible paying customer, favors small specific problems, and welcomes a first-user report. Writing receives the greatest weight. Treat this as a product experiment with a technical demonstration, not a feature-count race. [Official Week 2 page](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)

## Bounded current-entry check

I opened three recent entries visible on the public tag page, not the entire field; their results are author-reported and their applications were not independently tested here.

- [Scope Slip](https://dev.to/itsdanielsultan/scope-slip-turns-a-request-into-a-work-outline-35b) matches vague requests to seven sample services with browser MiniLM and produces editable outlines. It reports no customers or sales. Therefore an initial-brief generator would have direct challenge overlap.
- [Cashcast](https://dev.to/starknight/cashcast-which-invoices-will-be-paid-late-tabpfn-on-a-laptop-checked-month-by-month-2d21) presents invoice timing forecasts with chronological backtests and explicit limitations, including a baseline that matches its model. Its useful lesson is evaluation quality and commercial-license attention, not another invoice tool.
- [sifter](https://dev.to/max_ilands/sifter-a-23-mb-model-that-sorts-your-expenses-locally-for-free-2fg8) uses a small local embedding model to classify lines from taught examples and reports a held-out evaluation with named failures. A local text classifier alone is already represented.

## Shortlist for the reachable freelancer

Provisional five-idea ranking, conditional on the actual user's job:

| Rank | Working concept | Why this position | Main disqualifier |
| --- | --- | --- | --- |
| 1 | Handoff Proof / HandoffReady | Bounded, inspectable file defects; plausible freelancer trial | User does not deliver file kits, or AI adds no value beyond rules |
| 2 | Revision Ledger | Accessible freelancer workflow and meaningful version-authority edge cases | Direct competitors; no real contradictory-feedback problem |
| 3 | Copy Manifest | Concrete publication drift and cheaper bounded evaluation than visual grading | Need actual copy/variants and semantic model advantage |
| 4 | Scope Evidence | Established need and reachable user | Very crowded; ambiguous terms cannot become legal/billing verdicts |
| 5 | Baker Board | Specific repeat order-change problem with existing paid category | No confirmed baker first user |

Repair Receipt and Listing Truth remain secondary alternatives. This ordering is analytical judgment, not a numerical winning probability. HandoffReady is only a working name. An optional milestone completion view must show reviewed evidence and unresolved requirements, never claim a contract is fulfilled or a payment is due.

### 1. Handoff Proof — verify the actual delivery packet

**Buyer:** a freelance brand/social designer who repeatedly exports files for clients. Start with one job type, such as a small brand/social kit; do not attempt every creative discipline.

**Job:** turn an approved deliverable list and a local folder into a reviewable map of what is present, missing, ambiguous, or the wrong format. Example: brief asks for a transparent logo and three 1080×1080 social exports; folder contains a flattened logo JPEG, two square exports, and a stale draft. The product catches file-level defects and asks the designer to identify the intended final files.

**Core:** open-model semantic mapping connects natural-language deliverables to candidate filenames or extracted text. Deterministic code checks dimensions, type, duplicate hashes, expected counts, and manifest integrity. Every model mapping has source text and a human confirmation. No generated claim that artwork is correct, trademark-safe, licensed, or legally accepted.

**Differentiation to test:** checking an existing final packet against a confirmed requirement, without migrating the client into another platform. This is narrower than a generic handoff assistant. [Figma's export documentation](https://help.figma.com/hc/en-us/articles/360040028114-Export-static-designs-from-Figma) establishes that exported formats, scales, names, and dimensions are relevant working artifacts. [Zeplin](https://zeplin.io/pricing/) already sells handoff/versioning and offers a free tier with AI review, so do not claim handoff itself is new. [TaskMender](https://taskmender.com/) already offers AI intake-to-task packets; its advertised pilot data is not verified here. [ReleaseTraq](https://releasetraq.com/en/pricing) advertises paid client acceptance reports. These demonstrate product categories and offers, not our customer's willingness to pay.

**Five-day boundary:** plain-text brief plus PNG/JPEG/SVG/PDF filenames and metadata; user-selected final artifacts; local-only review; ZIP/JSON/Markdown manifest export. Avoid archive extraction, remote URL execution, Figma OAuth, font/legal certification, and full visual design grading. Untrusted SVG should be treated as data and never embedded directly. A file existing does not prove the deliverable is satisfactory.

**Demo/evaluation:** seed authorized sample packets with one missing file, incorrect dimensions, stale names, duplicate contents, and intentional ambiguity. Test deterministic defect detection separately from semantic mapping. Compare keyword matching to the open model on manually labeled filename↔requirement pairs; publish false positives and abstentions. Real user processes one historical delivery unaided and then with the tool; record time, defects found, unnecessary flags, and required corrections. The commercial hypothesis is a small one-time desktop purchase or paid setup for a studio's own delivery templates, not a subscription established by this research.

**Failure risk:** if the reachable freelancer does not deliver file kits or already has a checklist that catches everything, reject this direction immediately. If deterministic checks do all useful work and AI adds no measurable semantic value, it is a weak open-AI-core submission.

### 2. Revision Ledger — unresolved feedback decisions, with version authority

**Buyer:** a designer/agency producer receiving feedback across existing chats or emails. **Job:** isolate still-unresolved requests on the same artifact/version and prepare a human-approved clarification sheet. Two people disagreeing is not automatically an inconsistency; latest timestamp is not automatically authority.

**Core:** open-model extraction and candidate relation detection; structured artifact/version/author/authority supplied or corrected by the user; proposed duplicate, conflict, refinement, superseded, or unrelated links. Preserve exact snippets. An explicit approval event can supersede a request; the model cannot invent approval or resolve a disagreement. Export approved actions and unresolved questions; do not send messages or change client files.

**Crowding is substantial:** [Framebase](https://useframebase.com/) advertises multichannel feedback, AI deduplication/conflicts, and clarification; its page also has a waitlist, so pricing is positioning, not proven adoption. [RevCue](https://www.revcue.app/) advertises AI scope checks, change orders, and payments. [Nexibeo's Creative revision reconciler](https://nexibeo.com/solutions/creative-revision-reconciler/) describes the same broad problem with a sample demo and hypothetical pilot pricing. [Pastel](https://usepastel.com/features) already supports annotation, export, resolution and agents. [Filestage](https://filestage.io/pricing/) offers review/version/report workflows, including a free plan. Therefore call this an inspectable local implementation for a particular workflow, not the first feedback reconciler.

**Potential distinctive contribution:** the explicit distinction between chronological order, artifact version, and approved authority; show adversarial cases where ordinary summarization chooses the wrong request. This distinction matters only if the reachable user encounters it and benefits from it.

**Five-day boundary:** manually pasted text with source labels and selected artifact/version; no live WhatsApp, screenshot OCR, voice transcription, OAuth or annotations. One review screen, correction log, decisions, export. Evaluate relations on held-out labeled examples: obvious/soft contradictions, sarcasm, quotations, old versions, conditional suggestions, legitimate refinements, and different audiences. Measure how often the model invents a source, wrongly treats the last message as authoritative, or misses a real unresolved conflict. Compare against a manually read queue and a simple latest-message baseline.

**Commercial hypothesis:** per-project reconciliation/setup may be easier to test than recurring subscription. Ask whether they would use it on the next revision round, what they would replace, and what they would pay. A positive answer is interview evidence, not a purchase.

### 3. Scope Evidence — confirmed scope versus later request

**Buyer:** a freelancer with an approved brief and later extras. **Job:** display the exact relevant scope passage beside the new request and mark supported, possible extra, or clarification required. Human decides, and any hours/rate are user-entered. No legal verdict or assertion that the client owes money.

**Primary need signal:** [Freelancers Union's contract creator](https://freelancersunion.org/contract/) includes services and revision allowances; its [scope-creep guidance](https://blog.freelancersunion.org/2015/02/18/how-fight-scope-creep-politely/) recommends explicit written scope and courteous discussion. [HoneyBook](https://www.honeybook.com/company/contact-us) already offers proposals/contracts and advertises entry plans from $29/month. This is evidence of an established paid category, not proof for this application.

**Why fourth:** the parent research identified direct ScopeGuard competitors; initial briefs overlap Scope Slip, while RevCue covers comments-versus-scope. A generic implementation would be hard to distinguish. Choose only if the real user supplies a sharply bounded failure existing tools don't solve. One differentiator could be clearly separated explicit inclusions, exclusions, revision allowances, and missing terms with source-verified abstention. This still requires evidence, not novelty rhetoric.

**Validation:** baseline paraphrases and negation tests; unmentioned feature must be ambiguous rather than automatically extra; client quotations/instructions cannot override system extraction; revision count alone cannot establish a billable change. No automated invoice, message or contract generation.

## Other candidates, deprioritized with current user access

### Baker Board — changes to custom orders already received

Manually paste a customer conversation; reconcile cake size/flavour/date/pickup changes into an order draft, show conflicting dates and unresolved questions, and export a kitchen sheet after seller approval. AI extracts language; deterministic arithmetic computes quantities only from confirmed values. Never infer allergen safety, food suitability, payment received, or a confirmed order from a conversational guess.

[Bakesy](https://www.bakesy.app/pricing) lists $9.99/$17.99 monthly plans. Its [FAQ](https://www.bakesy.app/faqs) explicitly supports orders received outside its app and manual invoice creation. Thus bakery administration is an existing paid category, while a bridge from messy existing conversations is a hypothesis worth testing. Build only with a reachable baker and consented/redacted examples. No WhatsApp scraping or API subscription. Held-out tests require changed dates, cancellations, ambiguous quantities, relative dates, currency, and mistaken payment claims. This may be more specific than freelance tools but lacks a confirmed first user here.

### Repair Receipt — intake discrepancy report

Turn a technician's authorized notes and customer's complaint into a reviewed intake ticket: device identifier, visible damage, requested work, missing permission, and exact source quotes. No diagnostics, data-access authorization, estimated repair success or unsafe technical instructions. [RepairShopr](https://www.repairshopr.com/pricing) offers tickets/invoices and customer portals at $69.99/month for its monthly Starter plan; an inexpensive local intake bridge is an unproven market proposition. First user and domain validation are necessary; do not attempt to build a complete repair CRM in this window.

### Listing Truth — supported product facts before persuasive copy

Compare a proposed product listing against a seller-confirmed facts card and flag unsupported material, dimensions, compatibility or benefits. The model locates semantic assertions; confirmed facts and units remain deterministic/user-reviewed. [Shopify Magic](https://help.shopify.com/en/manual/products/details/product-descriptions/shopify-magic) already generates descriptions and explicitly warns that it may add unprovided benefits/facts; [its built-in app page](https://apps.shopify.com/built-in-features/magic-product-descriptions) says descriptions are included with Shopify. A generic writer is therefore a poor direction. Narrow QA has a credible failure to target, but merchant access and differentiation are unproven. Do not promise marketplace compliance or sales uplift.

### Bold alternative: Copy Manifest — client-approved copy to published variants

For an agency copywriter/social designer: compare an approved facts-and-copy sheet against a batch of exported captions, landing-page text, and ad variants. Identify omitted mandatory facts, stale offer dates, changed prices, altered qualifiers, and inconsistent CTA destinations. Human marks intentional variation; deterministic code handles exact dates/prices/URL/length checks; open model flags meaning-changing paraphrases with quoted evidence. It is less ambitious than creative judging and produces a concrete correction queue. However semantic equivalence evaluation is hard, and useful AI-core value must beat exact-string rules. Research here does not establish that this niche lacks direct competitors. Ask the actual freelancer whether publishing drift occurs before elevating it.

## Decision and validation gate

Ask the reachable person to show one recurring annoying task and the most recent example before building. Do not ask only whether they like the named idea. Questions: what went wrong last time, how often, what do they currently use, what costs time/rework, what inputs may they share, and would they try the next real project?

Choose Handoff Proof if file-delivery defects are real; Revision Ledger if conflicting multi-version feedback is real; Copy Manifest if approved text drifts across outputs. Scope Evidence is a fallback only with a very specific unmet need. Avoid choosing based solely on the best animation, hypothetical subscription price, or fashionable agent stack.

Obtain authorized/redacted material; agree a small task and success measure; label expected outputs independently before model tuning; retain a held-out subset; measure review effort including model mistakes; ask for an honest usable/not-usable verdict and next request. Publish unsuccessful cases. Do not fabricate a testimonial, payment, or avoided loss. A real first user with an admitted failure and corrected workflow is stronger evidence than a large synthetic dashboard.

All proposed prices/models above are hypotheses. Competitor websites show that vendors offer tools and charge listed amounts; they do not prove customer demand for this new product or validate vendor marketing claims. A five-day prototype scope is an engineering estimate, not a delivery guarantee. Brand names are working titles and need availability checks before launch.
