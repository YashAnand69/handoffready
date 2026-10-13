# Essentials, skills and tooling

Planning only • 13 October 2026. Available skills are workflow aids, not automatic authorization for paid services or external messages.

## Required capability map

| Workstream | Essential skills | Owner during build | Concrete deliverable |
|---|---|---|---|
| Product | Customer interview, task scoping, acceptance design, clear writing | Parent + product agent + Yash's input | Confirmed task and PRD, factual first-user account |
| Interface | React, TypeScript, state/focus management, responsive CSS | UI agent | Five-step review workspace and honest states |
| API/storage | FastAPI, SQLite transactions, validation, revision control | Backend agent | Private project persistence and atomic decisions |
| File checks | Bounded parsing, metadata, hashing, MIME/signature distinction | File agent | Tested artifact inspectors and precise limitations |
| AI | Local llama.cpp/GGUF, structured output, source validation, evaluation | Model agent | Pinned model/runtime and recorded comparison |
| Quality | Adversarial tests, regression selection, browser flow, accessibility | Independent reviewer + parent | Test evidence, defects fixed and release gate |
| Delivery | Git, dependency licenses, reproducible setup, demo writing | Parent | Fresh repo, notices, tagged release and submission package |

At most three worker agents plus the parent run concurrently. Parallel work begins only after shared contracts are frozen. Agent expertise does not replace real-user feedback or measured model output. Assign files/modules explicitly; parent integrates and reviews each stage. No agent approves its own release alone.

## Stack essentials

- React + TypeScript + Vite: working UI, strong types and a small deployable sample surface.
- Python 3.12 + FastAPI + Pydantic: validation/API; SQLite for a single-user local installation.
- llama.cpp local server plus verified Gemma 4 E2B artifact; Qwen3-4B fallback only after identical evaluation. No closed API fallback.
- Pillow, pypdf, defusedxml: bounded image/PDF/SVG-metadata parsing, as finalized in TRD. Model code/weights/license notices remain separate.
- pytest, Vitest/Testing Library, TypeScript checks; meaningful parser/job/storage tests and browser verification. Installed versions and lock files must be recorded when implementation starts, not guessed in this plan.
- No required cloud database, authentication service, payment processor, OCR, voice model or agent framework.

## Relevant Codex skills during implementation

Use the skill available in that session and read its current instructions before first application:

- `superdesign:superdesign`: UI exploration if the canvas tooling is available and free-budget compatible. A written UI specification does not require a paid generation. Direct code-native wireframes are sufficient for this planning package.
- `vercel:react-best-practices`: review after multiple TSX component edits.
- `vercel:verification`: complete local browser → API → persistence → rendered response verification.
- `vercel:deployments-cicd`: public sample deployment when authorized; hosting does not provide local inference.
- `pdf:pdf`: visual inspection of generated PDF artifacts if PDF output is introduced. MVP uses print-ready HTML to avoid a separate PDF generator.
- `openai-docs`: only if actual OpenAI/Codex usage needs current documentation; it is not the project's inference provider.
- `plugin-management:plugin-management`: only if a necessary external capability is missing. No plugin installation is required for the planned MVP.

Do not introduce Supabase, payment/auth integrations, 3D asset tools or paid image generation without an actual product need and the user's free-only constraint being satisfied.

## Files to prepare at project start

Fresh repository during the current entry window; README with real capability/limitations; MIT application license if chosen by owner; THIRD-PARTY-NOTICES; dependency/model manifest; lock files; .gitignore excluding client data/models/secrets; AGENTS.md with ownership and review rules; docs/decisions; public synthetic fixtures with provenance; private evaluation path; tests; reproducible setup/readiness script; recorded evidence folder. No client assets or transcripts in public fixtures.

## Owner inputs

Yash supplies the reachable freelancer's specific workflow, requests their participation personally, and supplies only authorized/redacted material. Parent can proceed with clearly synthetic fixtures while waiting. A first-user account and any public testimonial require actual consented evidence. No agent contacts that person automatically. Submission authorization/rule acceptance is a separate final step if not already authorized for Week 2.

## Tooling and budget constraints

Verified available hardware from research: Apple M5 Pro, 24 GiB memory. Model latency and peak memory remain unmeasured. Reserve roughly 8–12GB temporary disk headroom as a planning allowance to verify, not a fixed requirement. Use free/local tooling; verify downloads, licenses and account quotas. No paid API keys, GPU rental, automatic top-up, subscriptions or paid plan upgrades. Open code does not remove hardware, electricity or support costs.
