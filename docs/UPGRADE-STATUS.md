# Local upgrade status

**Recorded 15 October 2026, Asia/Kolkata.** This document describes the local working upgrade. It is not a new public release announcement. The historical public release remains v0.1.0; publication of the upgraded DEV entry remains on hold by the user's instruction. The earlier entry is already published and was not changed during this upgrade.

## Implemented

| Area | Current behavior |
| --- | --- |
| Exact source grounding | Repeated source text retains distinct server-owned occurrence IDs. Evidence binds source identity, full-text hash, Unicode code-point range and exact literal. Valid legacy spans keep their shape; ambiguous quote-only evidence is rejected. |
| Review and attention | Shared server summary separates current/stale/unreviewed mappings, human assessment, narrow findings and exclusions. Counts overlap deliberately and do not form a completion score. |
| Scope exceptions | A current reviewer exclusion needs a separate deliberate client-facing explanation for a reviewed-with-exceptions record. Failed/unknown facts remain displayed and counted. Private reasons are never copied into client prose. |
| Client delivery record | Versioned JSON/Markdown/HTML share one projection. Overview, outstanding actions, scope details and selected-original inventory include source revision, timestamp and full file checksums. Print layout uses the reader's A4/Letter settings. Originals must be sent separately. |
| Unsaved selections | Revision-bound server check previews respond to draft selections without saving decisions or claiming approval. Saving remains a separate action. |
| No-op handling | An unchanged normalized filename avoids parsing, revision churn and review invalidation. Actual packet changes still invalidate decisions. |
| Local jobs | Compact job-status polling avoids repeated original-byte hashing while authoritative actions and model-result publication still verify originals. Damaged originals are committed as blocked and prior decisions become stale before late results are discarded. |
| Interface | Attention filters, explicit assessment/fact labels, public exception editing, evidence near decisions, current-state client preview and restrained reduced-motion-compatible interactions. |
| Recorded explorer | The local static explorer displays actual captured synthetic review states and before/after records. It retains unresolved findings and the byte-identical earlier snapshot. It does not run AI, accept new uploads or substitute for the live app. |
| Launcher | Explicit alternative app/model ports retain loopback-only service URLs, port ownership checks and model-origin binding. Default app/model ports remain 8877/18081. |

These features do not establish semantic accuracy, visual quality, full website behavior or client approval. The local controls are not a hardened OS sandbox. Storage remains unencrypted by the app; one user/backend process per data directory is the supported shape.

## Validation checkpoint

The [final local integration receipt](upgrade-release-checks.json) records **239 passing Python tests**, including 26 recorded-explorer tests and four evaluation-adapter regressions; **54 interface tests passed**. Strict TypeScript/production build, frontend formatting, focused Ruff `F,E9` and `npm audit` passed with zero reported vulnerabilities. The Python suite retains one Starlette/httpx TestClient deprecation warning. These are actual local checks, not new remote CI results.

Independent final review found a persisted-null legacy baseline no-op regression beyond the earlier generated legacy-span cases. The compatibility repair and its added regressions are included in the 239-test rerun. The restarted app at loopback port 8879 retained three reviews and two snapshots in the synthetic sample. This verifies those saved records, not all possible legacy data.

[Actual browser workflow](upgrade-browser-workflow.json) records real V11 extraction/matching, a technical correction, three stale reviews after replacement and the byte-identical old record. A separate [scripted loopback API receipt](workflow-verification-upgrade.json) verifies seven synthetic model/manual/correction/export/restart stages. The final suite includes 26 passing recorded-explorer tests. [Reflow measurements](upgrade-layout-checks.json) found no horizontal overflow at 320/390/768/1440 px for the explorer, home, review and handoff screens. These are agent-operated synthetic checks; no customer or physical-device validation is claimed.

The new [64-second walkthrough verification](video-upgrade-verification.json) records a silent H.264 video assembled from actual captures at 1440×1080, 24 fps and 1,536 decoded frames. Source capture bytes are preserved. It is an edited agent-operated synthetic walkthrough, not continuous screen recording or customer evidence. The current public video remains historical.

Actual upgraded [review](screenshots/upgrade-review.jpg) and [client record](screenshots/upgrade-manifest.jpg) captures are retained. Screen inspection confirms the visible manifest header and summary are readable. Native A4/Letter pagination is **not yet verified**: no HTML-to-PDF engine is installed in the checked environment, and regenerating the page with ReportLab would not test the app’s HTML/CSS. This is a declared print-validation limitation of the local candidate, not a claim that the demonstrated local workflow is blocked.

The [final clean manual-workflow receipt](workflow-verification-clean-manual-final.json) records a latest copied-source/fresh-venv run with cached locked dependencies and rebuilt UI: all seven synthetic file/review/correction/export/restart stages passed without attempting inference. Its optional readiness probe received HTTP 401 from the occupied model endpoint; this was not an inference attempt or a failed manual workflow. Clean optional-model setup is not implied by that result.

The source/grounding stage also received a non-author read-only review: occurrence forgery, legacy no-op preservation, alternate-adapter rejection, exception privacy and original-tampering result publication were checked. A declared adversarial adapter with a real quote and forged digest was rejected without publishing proposals. Test doubles establish guards and workflow behavior, not Gemma performance.

## Fresh model evaluation

The [V4 protocol](EVALUATION-PROTOCOL-V4.md) freezes ten agent-authored synthetic packets, inspected original bytes, separate extraction/association keys, simple lexical baselines and raw-versus-guarded model scoring. [Candidate metadata](model-evaluation-v4-candidate.json) binds the local source/model/runtime used for the run.

The [immutable first report](model-evaluation-v4-first.json) and [independently recounted analysis](MODEL-EVIDENCE-UPGRADE.md) are now retained. There were 20/20 successful actual calls. Raw associations had 19 correct/21 positive pairs and two wrong format substitutions; after guards the same captured calls retained 19/19 correct pairs. Extraction covered 15/21 mandatory obligations under the frozen source/classification/format definition; all 21 proposals had valid source spans, but six omitted requested format coverage. Association uses fixed keyed requirements separately from extraction, so its result cannot establish automatic end-to-end completeness.

The actual app’s welcome-guide relevance error remains documented separately. Historical failures, first predictions, scorer revisions and model limits are preserved. A later renderer-label change means the final whole-source mapping differs from the evaluated freeze; model/evidence/guard sources remain unchanged. No tuning against these first results or replacement of the first report is claimed.

## Candidate package and remaining limitations

The integrated checks, actual screen captures, reflow, client-output privacy, correction/review invalidation and model/manual export/restart workflows are complete within their recorded scope. The candidate package combines tested source, built frontend, licensed synthetic fixtures, documentation and evidence. It excludes client data, databases, keys, installed dependencies, model weights and runtimes. It is a local candidate archive, not a new GitHub release; installation still follows the README. The earlier public v0.1.0 release remains unchanged.

The corrected full command, `PYTHONPATH=backend .venv/bin/python -m pytest tests scripts/test_evaluate_v4_adapter.py -q`, passed all 239 tests. An initial invocation without `PYTHONPATH=backend` produced import-collection setup errors; that setup failure was not claimed to have passed.

Remaining limitations and owner actions are:

1. Native A4/Letter pagination is unverified. Screen and reflow checks do not substitute for browser print-preview or physical-device certification.
2. A genuine authorized freelancer trial has **not happened**. Participant, payment and time-saving results remain unestablished.
3. Known model extraction omissions and semantic guide-relevance mistakes remain visible in the evidence; human review is required.
4. Reconcile and review the upgraded article, then lift the publication hold explicitly before any updated public article or deployment. The current public video remains historical. Keep the evaluated model/source identity distinct from the later presentation and legacy compatibility changes.

## Submission boundary

The earlier DEV article is already published; the upgraded draft and its publication remain on hold. Its writing must clearly distinguish human product direction and review from AI-assisted code/prose, synthetic fixtures from customers, model predictions from deterministic guards, and local operation from the public recorded demonstration. A useful completed workflow is the objective; a “10/10” score or contest win cannot be certified by internal testing.
