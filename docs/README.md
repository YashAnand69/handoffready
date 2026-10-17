# Documentation index

This index separates the **current local upgrade** from the **historical v0.1.0 release** and the **original plans**. A proposed feature in an older plan is not an implemented capability. Old test counts, screenshots and model results describe their recorded checkpoint, not the current source.

## Start here

- [Current submission status](SUBMISSION-STATUS-CURRENT.md): authoritative preparation status and remaining gates.
- [Integrated upgrade checkpoint](FINAL-UPGRADE-CHECKPOINT.md) and [15 October checks](final-upgrade-verification.json): 250 Python / 74 frontend tests.
- [Week 1 postmortem and Week 2 response](WEEK1-POSTMORTEM-AND-WEEK2-RESPONSE.md), with [winner breadth research](WEEK1-WINNERS-BREADTH.md).
- [Earlier upgrade status](UPGRADE-STATUS.md): historical upgrade checkpoint and measured checks.
- [Project README](../README.md): workflow, local setup, privacy and supported scope.
- [Contribution guide](../CONTRIBUTING.md): contracts and test expectations.
- [V4 fresh evaluation protocol](EVALUATION-PROTOCOL-V4.md): frozen synthetic fixtures, raw/guarded comparisons and failure accounting.
- [Frozen candidate metadata](model-evaluation-v4-candidate.json): source-digest-bound evaluation identity, not a published release identifier.
- [Fresh first-run model analysis](MODEL-EVIDENCE-UPGRADE.md), [immutable report](model-evaluation-v4-first.json), [actual browser workflow](upgrade-browser-workflow.json) and [scripted loopback workflow](workflow-verification-upgrade.json): separate evidence classes and retained limitations.
- [Upgrade video verification](video-upgrade-verification.json): 64-second edited actual-capture walkthrough; separate from the historical public video.
- [Recorded upgrade explorer](replay/index.html): actual captured before/after records, visible findings and unchanged historical snapshot; not live browser inference.
- [Historical earlier local checks](upgrade-release-checks.json): 239 Python tests, 54 interface tests and production build/format/correctness/audit evidence.
- [Final clean manual-workflow receipt](workflow-verification-clean-manual-final.json): latest copied-source/fresh-dependency synthetic workflow with no inference attempted. The [earlier clean receipt](workflow-verification-clean-manual.json) remains historical.
- [Browser reflow receipt](upgrade-layout-checks.json): observed 320/390/768/1440 px layouts, not physical-device certification.
- [First-user trial guide](USER-TRIAL.md): how to collect genuine authorized feedback; no completed trial is implied.

## Product and architecture references

[PRD](PRD.md), [TRD](TRD.md), [build contract](BUILD-CONTRACT.md), [implementation plan](IMPLEMENTATION-PLAN.md) and [backend notes](BACKEND-IMPLEMENTATION-NOTES.md) describe the foundation. Read the current upgrade status alongside them for later changes and present limits. The app remains React/TypeScript → FastAPI → SQLite/local originals → bounded inspectors → local llama.cpp/Gemma → human review → immutable client records.

## Historical release evidence

These records preserve the original release and its limitations:

- [Full-stack release guide](FULL-STACK-RELEASE.md) and [stage reviews](STAGE-REVIEWS.md).
- [Model evidence](MODEL-EVIDENCE.md), including developmental iterations and recorded mistakes.
- [Rules review](FINAL-RULES-REVIEW.md), [correctness review](FINAL-CORRECTNESS-REVIEW.md) and [usability review](FINAL-USABILITY-REVIEW.md).
- [Local check receipt](final-release-checks.json), [reviewed workflow receipt](workflow-verification-release-reviewed.json), [public release receipt](public-release-verification.json).
- [Recorded walkthrough documentation](VIDEO-DEMO.md), [capture manifest](video-demo-manifest.json), [verification receipt](video-demo-verification.json).

The public [v0.1.0 release](https://github.com/YashAnand69/handoffready/releases/tag/v0.1.0) and [recorded walkthrough](https://yashanand69.github.io/handoffready/) remain historical. They are not a live hosted application or proof of the new upgrade revision.

## Submission materials

[Submission checklist](SUBMISSION-CHECKLIST.md), [publication review](PUBLICATION-REVIEW.md), [DEV draft](DEV-SUBMISSION-DRAFT.md) and [entry text](DEV-ENTRY.md) are preparation materials. **Read-only DEV dashboard verification on 17 October confirmed HandoffReady article 6228689 remains a draft. Earlier publication claims were incorrect. The user has instructed publication to stay on hold.** Their historical text must be reconciled with fresh upgrade evidence before any later publication. Synthetic evaluation and agent-operated demos must not be described as customer use.

## Original research and planning

The [13 October original planning package](planning/README.md) is retained as a historical proposal, including its illustrative UI and deferred options. Its “implementation pending” language was true when written and does not describe the current app. [Foundations](HF-WEEK2-FOUNDATIONS.md), [ideas](HF-WEEK2-IDEAS.md), [recommendation](HF-WEEK2-RECOMMENDATION.md) and [rules research](HF-WEEK2-RULES.md) preserve the original decision process. Recheck official rules before publication; no document promises an awarded score or contest win.
