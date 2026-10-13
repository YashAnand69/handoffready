# Open-source, budget and submission plan

Planning only • 13 October 2026. No Week 2 entry has been published by this package, no agreement has been accepted, and no account credits are assumed.

## Original work and reuse

Create a fresh application repository during Week 2. Our original work is the approved requirement model, evidence validator, file-checking workflow, review/invalidation behavior, safe exports, UI and evaluation. Adopt dependencies rather than rebranding a complete business app. Credit nontrivial borrowed code and ideas in both repository and submission. Soundwalk Atlas remains a separate Week 1 entry; do not submit it again under new branding.

The challenge FAQ permits significant credited OSS reuse and requires a new project/repository within the window. [Official brief/FAQ](https://dev.to/challenges/hacktoberfest-week2-2026-10-12).

## Attribution manifest to complete at Stage 0

| Item | Upstream | License to verify/preserve | Build receipt |
|---|---|---|---|
| Local runtime | https://github.com/ggml-org/llama.cpp | MIT | Commit/release, build flags, binary hash |
| Preferred model | https://huggingface.co/google/gemma-4-E2B-it-qat-q4_0-gguf | Apache-2.0 for exact selected artifact | Revision, file, SHA256, size, model card |
| Alternative model | https://huggingface.co/Qwen/Qwen3-4B-GGUF | Apache-2.0 for exact selected artifact | Same receipt; state category change if used |
| PDF parser | https://github.com/py-pdf/pypdf | BSD-3-Clause, verify pinned release | Version, lock entry |
| Raster parser | https://github.com/python-pillow/Pillow | HPND, verify pinned release | Version, notices |
| XML parser | https://github.com/tiran/defusedxml | PSF, verify pinned release | Version, notices |
| UI/API dependencies | Official React/Vite/FastAPI/SQLite ecosystem sources | Preserve exact dependency notices | Versions and lock files |
| Public fixtures | Original synthetic brief/assets | MIT/CC0 as appropriate, explicit creator/provenance | Generator/seed/checksums |

These are selected candidates, not installed/pinned receipts. Do not leave placeholders in the final release or imply the application's MIT license relicenses weights/dependencies. Record copied/modified files separately from installed dependencies. Model licensing was researched, but exact artifact access/runtime compatibility still needs implementation verification.

## Category strategy

Overall entry plus Best Use of Gemma if the finished core actually uses Gemma inference successfully. If Qwen performs better and replaces it, prioritize execution quality and remove the Gemma claim. Extra categories require useful implemented technology and actual evidence; installing an SDK or naming a partner is insufficient. Do not build fine-tuning without data or add voice merely for another category.

Current Gemma 4 licensing is Apache-2.0; do not generalize to older generations. [Google license](https://ai.google.dev/gemma/apache_2). The existing research identifies TabPFN default commercial restrictions and ElevenLabs Free output limitations; retain those findings rather than assuming free contest credits resolve them. [Detailed rules/partner research](../HF-WEEK2-RULES.md).

## Deployment and free budget

Private real workflow runs on localhost with a prepared local model. Public hosting exposes only intentional example assets and recorded example suggestions. It must have no bridge to the user's local files/API/model service and must never silently receive private uploaded files. Clearly label the public sample, and include a video of actual inference plus setup instructions. Do not call a static sample live arbitrary-input AI.

Free hosting/account quotas must be checked before deployment. No paid plan, usage top-up, GPU rental or subscription. A code/license being free does not make hardware/storage/electricity/support free. Commercial pricing is a hypothesis to test, not a promise of a zero-cost SaaS business.

## Submission content and evidence map

| Article section | Evidence required |
|---|---|
| What I Built | Specific freelancer task; supported scope; plausible commercial value as hypothesis or actual evidence |
| Demo | Complete recorded real-model task, public sample distinction, visible limitations |
| Code | Fresh repository, tested release SHA/tag, licenses/attribution |
| How I Built It | Model/parser provenance, evidence architecture, review decisions, actual tests |
| Why Open Innovation Matters | Local client-data handling and measured model/runtime costs; no invented superiority over closed tools |
| My Agent Session | Truthful human direction and agent work; redact sensitive sessions before any publication |
| My First User | Actual consented trial only; no invented savings, purchase or quotation |
| Prize Categories | Only implemented and demonstrated partner use |

Use the official template and tags `devchallenge`, `hf26challenge`. One Week 2 entry; update that entry rather than publishing duplicates. Preserve required AI assistance disclosure. A model-generated claim still needs evidence even when it sounds confident.

## Timing and final authorization

Window: 13 October 00:30 IST through **19 October 12:29 p.m. IST**. Aim to freeze and publish on **18 October evening IST**. Specific rules require a new project, code and demo plus an explanation of openness. [Week 2 rules](https://dev.to/page/hacktoberfest-week2-2026-10-12-contest-rules).

Before any actual submission, present the concrete final post/demo and obtain any required Week 2 eligibility/rules acceptance. Week 1 consent should not be silently treated as acceptance of changed Week 2 terms. General rules retain entrant ownership while granting contest/promotional reuse rights; use only material we can lawfully share. [General rules](https://dev.to/page/official-hackathon-rules).

DEV–Hacktoberfest dashboard synchronization was unresolved in the prior account check. It is an account follow-up, not a reason to fabricate registration status or miss the DEV submission deadline. Verify the published entry directly, retain its URL/time and separately report sticker/account recognition. This package does not repair that account issue.

Post-deadline changes must be dated in README as required by the FAQ; preserve the submission tag. Do not rewrite release history or claim later features were in the submitted version.
