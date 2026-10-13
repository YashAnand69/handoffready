# Independent final usability review

Initial review 13 October 2026; remediation recheck 14 October 2026 (IST). Scope: the local HandoffReady freelancer workflow, with static inspection and isolated React/jsdom regression checks. This is an engineering review, not observed customer feedback, a complete accessibility certification, or a fresh model evaluation. No live project data was edited. No service was published and no commit was created.

## Evidence and method

Reviewed `AGENTS.md`, README, PRD, actual stage/release records, model evidence, React application/components, styling, presentation/API/types, backend baseline/review/export behavior, and existing interface regressions. The parent separately exercised the live synthetic sample, real model jobs, review and export. Existing checkpoint counts (128 Python / 15 interface tests) are historical observations and must be updated after new repairs and regression tests.

`frontend/src/FinalAudit.test.tsx` contains 16 independent API-double regressions. The first four tests failed against the initial reviewed source: same-requirement navigation, unsaved filename/manual-review shortcut, duplicate raster preview, and unsaved filename/model-matching shortcut. A fifth test covers the ten-check limit. Additional tests verify connection retry/draft preservation, preview retry/fresh acknowledgment, individual-check removal, numeric validation, step/requirement focus, asynchronous image-error announcements and per-file draft ownership across unrelated operations. These doubles exercise interface state only; they do not establish semantic model performance.

## Remediation verification — 14 October

The final independent remediation run passed **31/31 interface tests** (15 earlier tests and 16 independent audit tests). The first remediation run passed 25 tests, then adaptive audit exposed U10 and preserved its failing regression. The parent repaired that shared dirty-state defect with per-file draft ownership; the final run includes upload recovery, two simultaneously edited filenames, hidden drafts, a completed save clearing only its own warning, requirement-heading focus and asynchronous image-error announcement.

Two actual isolated backend regressions also passed: `test_unchanged_source_and_checklist_preserve_confirmed_reviews` verifies unchanged revision/hash/approved baseline/current reviews and staleness after a real edit; `test_runtime_original_damage_cannot_generate_a_current_pass_export` verifies that damaged originals force blocked/stale/unknown evidence and cannot create a falsely current passing export. These isolated clients do not alter the live workspace. The existing Starlette TestClient deprecation warning remains. TypeScript and production build completed; this auditor's default Node 20.18 emitted a Vite minimum-version warning, so the parent must record its supported-runtime final build separately.

| Finding | Recheck result | Evidence |
|---|---|---|
| U01 | Fixed. Changed-source warning explains checklist reset/stale reviews. | Actual targeted backend test; no-op guards and consequence copy checked statically |
| U02 | Fixed for both Files shortcuts. | Both independent dirty-draft tests pass with discard declined |
| U03 | Fixed. | Current-requirement click leaves dirty guard intact; subsequent navigation prompts |
| U04 | Fixed. | Exactly one selected-raster visual control in regression |
| U05 | Fixed. | Ten-check cap, individual removal, minimum-one check and acknowledgment reset verified |
| U06 | Fixed for initial connection and client preview failures. | Successful explicit retries; entered project name preserved; export still needs acknowledgment |
| U07 | Clarity fix implemented. | Static review: creation time, saved status, same-source/packet caveat and earlier-source/packet label; snapshots explicitly do not update |
| U08 | Fixed. | Clear original-files delivery instruction present and tested |
| U09 | Implemented fixes verified within available methods. | Step and requirement heading focus tests pass; image error alert tested; preview/history alert roles checked. Real screen-reader assessment remains separate |
| U10 | Fixed. | Uploading unrelated files and saving one of two filename drafts preserves the other warning; hidden drafts retain beforeunload/leave protection; completed save clears its own marker |

Other implemented improvements checked in source: read-only full brief disclosure, check-level validation that disables invalid saves, filename-specific Rename/Remove accessible names, changed-selection finding notice, duplicate-byte warnings, local setup page/link, and a disabled explained model-suggestion action on an approved checklist. Numeric input now displays the actual invalid value instead of silently substituting one; invalid saves are blocked. No reproducible P1/P2 remains from this review's U01–U10 cases.

## Remaining verification and refinements

- **P3 wording:** The changed-source warning is also shown for label-only edits. State “source text or label” explicitly because either currently resets the checklist.
- **P3 context:** Repeated export-format buttons could use accessible names including snapshot date/hash. Large checklist field groups could provide requirement/check context beyond repeated labels.
- **Assessment limitation:** Keyboard focus and alert semantics are tested, but real screen-reader announcements and visual/mobile behavior require browser/user verification. No comprehensive accessibility certification is claimed.

These refinements do not weaken the tested approval/export boundary. A final browser pass, supported Node build and integrated backend suite remain the parent's release verification.

## What supports a coherent freelancer task

| Area | Observed behavior | Practical implication |
|---|---|---|
| Agreed source | Saved pasted brief, provenance label, exact literal quotes, explained manual additions | Freelancer has a reviewable source; no AI claim of client approval |
| Checklist | Editable title, technical/manual checks, explicit acknowledgment before confirmation | Scope requires a human decision; instructions explicitly warn about missed formats |
| Intake | Supported formats/limits, inspected metadata, blocked errors, immutable hashes, replace/rename/remove | Corrections can be made without claiming an extension changes format |
| Model associations | Separate suggestion panels, reasons/quotes, unverified interpretation, empty manual route | Candidate coverage never selects files or grants acceptance |
| Human judgment | Independent file selection, disposition, private note and deliberate client note | Technical facts and subjective sufficiency remain separate |
| Gaps | Saved findings, stale-review warning, unresolved/needs-work states, truthful client projection | Opaque PNG, duplicate bytes and incomplete guide can remain visible |
| Export | Server-generated preview, acknowledgment, approved-baseline/input guards, immutable snapshots | Failed technical checks survive satisfied human assessments; raw brief/private-note fields are omitted |
| Local operation | No account, cloud upload, paid API, telemetry or sending workflow in scope | Appropriate for a single local delivery owner; setup burden remains a product constraint |

The model's known omissions and wrong semantic associations are honestly preserved in `MODEL-EVIDENCE.md`. Typed guards address factual format conflicts, while human review still needs to catch same-format irrelevant content, future promises, instruction injection, omitted deliverables and insufficient explanations. A literal matching quote establishes provenance, not usefulness. A transparency pass establishes at least one nonopaque pixel, not a correctly removed background. Different file bytes establish byte difference, not three distinct designs.

## Findings requiring release review

Priorities reflect practical local-user impact. P1 means loss of work or a disruptive core-flow defect. P2 means a recoverability, correction, clarity or access problem. Findings below preserve the initial reviewed implementation and reproduction history; use the remediation table above for current status.

| ID | Priority | Reproduction / evidence | Required outcome |
|---|---|---|---|
| U01 | P1 | Reopen a reviewed project. It starts on Brief. Click **Save brief & continue** with unchanged source. `PUT /brief` unconditionally replaces source, clears all baseline requirements and invalidates decisions. No consequence warning is shown. Unchanged checklist resaving similarly invalidates reviews. | Unchanged saves/continuation preserve baseline and review state. Real scope changes clearly explain the invalidation before applying it. |
| U02 | P1 | On Files, Rename a file and type a new filename without saving. Click **Review manually** or **Suggest matches with local AI**. Both shortcuts bypass `allowLeave` and leave the editor; the draft disappears. | Both shortcuts honor the same dirty-state guard as step navigation. Declining discard keeps the draft and performs no model request. |
| U03 | P1 | On Review, type a private note, click the already-active requirement, accept the discard prompt, then switch workflow step. The editor was never remounted, but dirty became false; the later switch drops the still-visible draft without another warning. | Clicking the current requirement is a no-op; changing requirement preserves the leave guard. |
| U04 | P2 | Select one inspected PNG/JPEG, open Selected file evidence. Two identical **Inspect image visually** controls are rendered by duplicate `ImageEvidence` blocks. | Exactly one preview/control per selected raster file. |
| U05 | P2 | Add checks repeatedly to one requirement. UI does not cap ten checks and has no individual Remove check. Eleven checks fail strict server validation; deleting the whole source-derived requirement is the only built-in deletion route. | Remove individual checks while retaining at least one; stop additions at the server's ten-check cap; reset acknowledgment after edits. |
| U06 | P2 | Local bootstrap fails once (service starting/restarting). Error can be dismissed, but `connected` stays false, create/sample stay disabled, and there is no Retry. Client preview failure likewise has no explicit Retry. | Provide visible bounded retry with loading/error status and recover when service returns. |
| U07 | P2 | Create export, correct files/reviews, create another export. Saved exports display only opaque hash and format buttons, with no date or relation to current inputs. | Show creation time and current-input versus earlier-input label; immutable earlier exports remain downloadable with clear context. |
| U08 | P2 | Handoff speaks about a packet but only downloads manifest formats; there is no explicit instruction that original delivery files must be sent separately. | State that the manifest does not bundle original files and originals should accompany it. |
| U09 | P2 | Keyboard activation changes workflow content and scrolls to navigation, but does not focus/announce the new step heading. Review requirement selection does not move focus into the chosen decision. Async preview/image/history errors are plain paragraphs. | Supply predictable content focus or appropriate live announcement; async failures must be discoverable without scanning the entire page. |
| U10 | P1 | Edit a filename, upload an unrelated file, then navigate to Review. Successful generic tasks cleared dirty despite the filename draft remaining mounted. | Track per-file draft ownership; unrelated operations must preserve remaining drafts and leave/close warnings. |

## Smaller initial improvement opportunities — implementation history

The items below were recorded before remediation. Full brief context, setup link, validation, file-button names, changed-selection notice and duplicate-byte warnings are now implemented; only broader field-group context remains a refinement.

- Checklist displays selected exact quotes but not a full-source context control. Comparing a long source for omitted scope currently requires navigating away from unsaved edits. A read-only full brief disclosure in Checklist would make completeness review easier.
- Model-unavailable copy refers to a setup guide without an actual in-app link to that guide. Provide an accessible local setup route and keep manual work obvious.
- Numeric fields have HTML bounds but are not in a validating form; clearing a quantity stores zero while `value || 1` displays one. Prefer honest empty input and visible validation before confirmation. Empty exact text/format sets/manual instruction errors should identify the affected check.
- Repeated per-file Rename/Remove controls have identical accessible names. Associate each with its filename, particularly for screen-reader button lists. Requirement/check field groups should provide contextual legends for large checklists.
- Review can display saved findings while the visible file-selection draft has changed. The heading says **Saved check findings**, but a short “selection changed; save to recompute” notice would prevent casual interpretation as current checks.
- Packet inventory exposes hashes but no plain-language duplicate grouping before mapping. Distinct-count failure is useful later; showing duplicate-byte groups earlier would make correction faster.

## Accessibility and mobile assessment limits

Static inspection finds native buttons/inputs/selects, wrapped labels, workflow `aria-current`, selected requirement `aria-pressed`, global error/status regions, skip link, readable textual states beyond color, responsive layouts and reduced-motion overrides. These are useful foundations, not proof of complete accessibility.

The existing stage record reports one 390px viewport without document overflow. This independent review did not run a concurrent browser session, to avoid interfering with the parent. jsdom cannot establish visual contrast, zoom/reflow, browser focus behavior, actual mobile file-picker behavior, screen-reader announcements or touch ergonomics. Recheck keyboard-only use and 320px/390px/200%-zoom layouts after repairs, including long filenames, many checks, validation text and saved-export labels.

## Final verification checklist

1. Reopen a reviewed project and continue with no input changes; requirements/reviews must remain current.
2. Edit source/checks deliberately; observe explained invalidation and a fresh explicit confirmation.
3. Decline every dirty-discard route, including current requirement, manual review and model shortcut; all drafts remain.
4. Correct one bad check without recreating its requirement; limits and field errors match backend rules.
5. Use unsupported/blocked file, corrupt replacement and service outage; accepted inventory and drafts survive with actionable recovery.
6. Review actual files, not model prose; retain unresolved/failed checks in export. Never claim guide quality, visual quality or website execution from metadata.
7. Inspect client-safe preview, export old/current snapshots, and confirm private notes/raw source are absent while deliberate titles/check instructions/client notes remain reviewable.
8. Complete keyboard/mobile walkthrough and rerun independent regressions, all existing tests, type/build/format checks. Update documentation counts only from the final run.

Authentic first-user trial, willingness-to-pay evidence, broad model accuracy, general prompt-injection robustness and public contest submission remain separate from a tested local release. No user feedback, performance claim, remote result or contest eligibility is invented by this review.
