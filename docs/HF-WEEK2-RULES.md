# Hacktoberfest Week 2: verified rules and technology constraints

Research date: 13 October 2026, Asia/Kolkata. Read-only research; no terms accepted, credits claimed, account changes, project implementation, or submissions performed.

## Decision-critical requirements

The Week 2 theme is **Side Hustle**: open AI must be central to a useful product with a plausible paying customer. Actual first-user feedback is optional but explicitly rewarded. Writing receives the greatest weight; other criteria cover theme fit, originality, execution, and relevant partner use. **No numeric judging percentages are published.** Prior OSS can be adapted with substantial original changes and attribution. The FAQ requires a fresh repository, credits nontrivial reuse, disallows old-project entries, and asks that post-deadline commits be identified in README. English is required for prize consideration. AI-assisted construction is allowed. Teams can contain up to four people. [Challenge and FAQ](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)

The legally specified window starts **12 October at noon PDT = 13 October 2026, 00:30 IST** and ends **18 October at 23:59 PDT = 19 October 2026, 12:29 p.m. IST**. Submit one entry; only the first counts if multiple are submitted. Required: published DEV template post, new AI-centered project built during the window, plausible paid utility, deployed link or video, repository link, and explanation of openness. Partner entries need meaningful technology use and named categories. There is one overall prize ($250), six featured prizes ($200), eleven partner prizes ($100), and a valid-entry badge; each participant can win at most once. A tied score is resolved using positive DEV reactions. [Specific rules](https://dev.to/page/hacktoberfest-week2-2026-10-12-contest-rules)

Entrants must satisfy age/legal-majority, active DEV account, geographic/export-control, and other eligibility conditions. India is not among the listed excluded jurisdictions; personal eligibility is not certified by this research. The general rules require original work begun within the window and sufficient IP/privacy permissions. The entrant retains ownership but grants perpetual, irrevocable, worldwide, sublicensable contest/promotional use of entry materials. Sponsor's clock controls receipt. Winners may need eligibility/release/tax documentation. [General rules](https://dev.to/page/official-hackathon-rules)

The template sections are What I Built, Demo, Code, How I Built It, Why Does Open Innovation Matter?, optional My Agent Session, optional My First User, and applicable Prize Categories. It pre-fills `devchallenge` and `hf26challenge`. Remove optional sections that would otherwise contain invented evidence. [Official template link on challenge page](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)

## GitHub reuse versus from-scratch decision

**Recommended: a new repository and original product workflow, built on a small number of licensed open-source components.** Writing a model runtime, OCR engine, document parser, or agent framework ourselves adds risk without helping the customer's problem. Conversely, cloning a complete app and changing branding is not a credible substantial contribution. Soundwalk Atlas cannot simply become the Week 2 submission.

Interpretation: a fresh product using established dependencies is the clearest way to satisfy both the new-project rule and the explicit encouragement of significant OSS adaptation. A fresh fork of a large old application is more ambiguous because its repository history predates the window. If choosing that route, seek organizer clarification before investing implementation time; prefer creating an original repository with credited vendored components instead.

Before adopting code or weights, record exact upstream URL, commit/model revision, license, copied/modified files, notices, and role in the product. Public GitHub visibility alone grants no reuse license. Dependencies, model weights, datasets, screenshots, fonts, and generated assets can have separate terms. Pin relevant versions. Preserve attribution, license text, and required NOTICE files; identify modifications. Prefer MIT/Apache-2.0/BSD components for this short build. These are engineering selection recommendations, not extra contest rules.

The meaningful new value should be visible in the demo: domain-specific constraints, evidence links, correction flow, usable output, and measured behavior on realistic examples. An original business workflow built around a reusable model is stronger than original boilerplate around a generic chatbot.

## Available categories and what constitutes use

The hub lists the following categories; the Week 2 page has the same set. [Official category descriptions](https://dev.to/challenges/hf26)

| Category | Required substance |
|---|---|
| Render | AI runtime or agent frontend hosting |
| TabPFN | Tabular predictions; latest version and wider prediction agent favored |
| Tinker | Task-specific fine-tuning with measured baseline improvement |
| Arduino | UNO Q hardware/model/physical agent |
| DigitalOcean | Hosting, open-model compute, or Gradient AI |
| Gemma | Actual Gemma inference, tuning, or serving |
| Backboard | R-CLI, model comparison, or assistant memory/RAG |
| ElevenLabs | Agent voice, transcription, or narration |
| Entire | Shared agent sessions or past-work search |
| GitHub Copilot | Copilot development/review or GitHub Actions automation |
| Mastra | Agent orchestration, tools, memory, or workflow |
| MongoDB Atlas | Database, retrieval, or agent memory |
| Sentry Agent Tracing | Execution/performance/debugging traces in write-up |
| SerpApi | Live search or fresh retrieval |
| .tech | Claimed domain, deployed project, linked write-up |
| Temporal | Durable workflow, recovery, retries |
| Tiger Data | Embeddings, hybrid retrieval, or database agent |

Do not accumulate categories merely by installing SDKs. Choose one primary partner aligned with the core product, with additional categories only when useful, demonstrated, and free-budget compatible. Overall entry needs no partner.

## Free-tier and commercial-use constraints

### Gemma: strongest default partner candidate

Current official documentation is for **Gemma 4**, whose model card explicitly specifies **Apache-2.0**. Earlier Gemma generations retain different terms; do not generalize the new license backwards. [Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4), [official license](https://ai.google.dev/gemma/apache_2)

Google's approximate memory table lists E2B Q4 at 2.9 GB, E4B Q4 at 4.5 GB, and 12B Q4 at 6.7 GB; runtime/context adds memory. Local execution can avoid a metered inference bill, but needs an actual hardware and latency trial. Text, images, and selected audio support vary by model/runtime. [Official overview and memory planning](https://ai.google.dev/gemma/docs/core)

Recommendation: test a pinned small Gemma 4 instruction model early on the user's hardware; retain a validated alternative if its factual extraction/structured-output behavior is insufficient. A hosted provider's terms/costs are separate from the model license. No arbitrary cloud GPU provisioning.

### TabPFN: contest category exists, paid-product rights are a blocker

TabPFN-3.5's published license permits noncommercial/nonproduction use and restricts even outputs used in business processes, client deliverables, or revenue-generating work without a separate commercial license. [Actual model license](https://huggingface.co/Prior-Labs/tabpfn_3_5/blob/main/LICENSE)

Prior Labs docs also distinguish exploratory experiments from workflows affecting business decisions and require a commercial license/API agreement for production. Derivatives inherit the restriction. Older versions have their own licenses; a code license does not automatically license newer weights. [Official licensing guidance](https://docs.priorlabs.ai/models)

Interpretation: a noncommercial challenge prototype may be feasible, but a first paying customer or operational business pilot is not safely compatible with the default free model license. The organizer recommending free noncommercial access does not override Prior Labs' rights. Avoid selecting TabPFN for our core side-hustle product unless suitable commercial rights are confirmed without payment. Otherwise frame it strictly as a research prototype with an explicit commercialization blocker, weakening the first-user story.

### Tinker: useful only if verified credits and sufficient data

Tinker bills training/sampling by tokens; checkpoint storage is $0.10/GB/month. Its model roster changes, and some old model IDs are retired. Serverless inference is marked beta and not recommended for intensive production. [Current pricing](https://tinker-docs.thinkingmachines.ai/tinker/models/models_and_pricing/)

The organization can be created free but training/sampling need a balance or enterprise agreement. [Account/billing prerequisites](https://tinker-docs.thinkingmachines.ai/tinker/data-model/)

Challenge promo credits are advertised, but **the user's actual balance, amount, expiry, payment requirements, and overage behavior have not been verified**. Do not infer a universal $150/$250 allocation from anecdotes. Use Tinker only after inspecting the authenticated promo and billing state, with a hard allowed budget, no automatic top-up, and confirmation of model license/data rights. Without a genuine training dataset and held-out evaluation, fine-tuning is unnecessary scope.

### ElevenLabs: avoid repeating the Week 1 licensing problem

Official help says Free generation lacks a commercial license; shared noncommercial output needs provider attribution in its title. Paid-plan output has different rights, and Beta services are excluded from commercial/production use. Upgrading later does not retroactively convert previously free output. [Official publication guidance](https://help.elevenlabs.io/hc/en-us/articles/13313564601361-Can-I-publish-the-content-I-generate-on-the-platform)

Inference: because this challenge concerns paid utility and grants promotional reuse rights, Free generated narration/voices carry a rights mismatch. Do not assume contest credits solve it: their exact plan and output license must be verified. Prefer the user's own recorded narration or a properly licensed local speech model if voice is necessary; omit the partner category otherwise. Whether specific free transcriptions fall under identical output restrictions remains unverified, so do not build a commercial dependency around that assumption.

### Render: free demo possible, not a free production guarantee

Free web services sleep after 15 minutes, can take roughly a minute to wake, lose local filesystem changes on restart, and free databases expire after 30 days. Static sites are free. Bandwidth/build limits can create billing with payment methods; without payment methods, services/builds can instead be suspended. Render itself discourages Free for production applications. [Official Free documentation](https://render.com/docs/free)

Recommendation: a static frontend or honest demo is feasible, but do not claim reliable zero-cost hosted model inference. Keep durable user data client-side or in explicitly validated storage, and avoid surprise overages.

### Other partners

Entire's current docs describe an MIT-licensed CLI with Codex support and session capture. It can help substantiate the build story, but review/redact session material before publishing. [Official Entire introduction](https://docs.entire.io/)

Mastra is a TypeScript agent framework with tools/workflows/traces; model inference and hosting costs are separate. Use only if orchestration improves the actual workflow. [Official Mastra documentation](https://mastra.ai/docs)

Account-specific quotas/licenses for Backboard, DigitalOcean, MongoDB Atlas, Sentry, SerpApi, Temporal cloud, Tiger Data, and the free .tech promotion were not authenticated in this research. Treat them as pending, not confirmed free infrastructure. A domain's first-year promotion is not permanent free hosting, and renewal settings require inspection.

## Best strategy under our constraints

1. Pick a narrow customer task with an accessible real tester before architecture work.
2. Build original UX/business logic in a fresh repository during the valid window.
3. Use local, commercially permissive open weights as the actual core, with citations and evaluation.
4. Consider Gemma as the main category if it passes hardware/task tests. Add genuine GitHub Actions or session documentation only when helpful.
5. Deliver a deployed sample experience plus reproducible real-model demo; label sample/replay output clearly.
6. Measure time/error improvements against the customer's current workflow, collect consented firsthand feedback, and write the story around those facts.
7. Freeze/tag a tested commit before the deadline; record later changes honestly. Aim to publish by 18 October evening IST to leave margin.

No numeric winning probability can be justified before seeing eligible entries and judge decisions. Narrow usefulness, verified first-user evidence, clear open-model advantage, and excellent writing are the defensible levers.
