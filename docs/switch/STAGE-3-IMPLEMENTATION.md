# Context clarification and fresh review — Stage 3

5 November 2026. Implemented local clarification handling; a real contextual room exchange and human review remain a separate evidence gate. This is not a finished business workflow or a contest submission.

## What changed

Questions are tied to an approved checklist item, exact packet revision/hash and a context epoch. The backend records provisional checks of the selected files. A reply retains its original question identity, source reference and reported speaker; provenance is explicitly unverified. The agent cannot decide whether a reply changes the agreed scope or constitutes a satisfactory delivery.

The local review card shows the question, provisional checks, replies, source references and earlier accepted context together. The reviewer must check the source and account for every current reply before accepting selected context, dismissing the question, or withdrawing an earlier acceptance. Accepting context invalidates prior assessments. Dismissing a later follow-up preserves an earlier accepted basis visibly. The checklist action only navigates to the editor; it makes no scope decision or resolution.

Source identity is separate from accepted context identity. A real brief/checklist/file/inspector change permanently supersedes older questions and retires their accepted basis. Returning to the old hash cannot revive them. Accepting question A does not hide pending question B. A new reply to a current resolved question reopens its hold; a reply to historical context stays historical. Same source with different text conflicts rather than overwriting a receipt.

A project-wide hold covers pending questions and unconfirmed attachments, even after integration is disabled. The workspace summary and client preview show a draft; creating a new delivery record is refused while held, including when draft gaps are acknowledged. Existing historical record downloads remain unchanged. Bound-project deletion is refused inside the same database write transaction, preventing a race with room binding.

## Data preservation and bounded tools

Schema 2→3 adds immutable questions, reply receipts, resolutions and per-job epochs. Legacy blocker text/revision/hash are preserved and labelled unknown-source, unverified and dismiss-only. Ambiguous duplicate project bindings and unsupported newer schemas fail closed. Migration never rewrites historical exports.

Private tool configuration version 3 explicitly adds `delivery_propose_question` and `delivery_record_reply`; version 1 keeps two read tools and version 2 keeps its three-tool intake inventory. Both new tools retain the fixed local origin/binding, strict arguments, bounded text/IDs, exact currency and caller-owned operation keys. There is no agent tool for context resolution, human assessment, checklist approval or sharing. This remains a narrow product interface, not isolation from unrestricted same-user shell access.

Local resolution persists a stable key/body through interrupted replies and browser remounts. Success is announced only after both the actual project and context refresh. Ordinary source changes invalidate review through every project writer: Store mutation, startup original recovery and complete-packet confirmation. Turning off integration preserves the visible hold; re-enable it to use the local resolution controls.

## Verification and limitations

**483 backend tests and105 interface tests passed**, along with production build, formatting and whitespace checks. One existing Starlette/httpx deprecation warning remains; no dependencies were added. See [Stage3 verification](verification-20261105.json) for exact scope and source fingerprints. Backend checks use synthetic SQLite/files, HTTP and command subprocesses. Interface tests use API doubles. They are not evidence of a colleague trial, production security, delivery quality or a guaranteed contest outcome.

The pre-activation migration rehearsal used an owner-private backup of the actual synthetic Stage 2 project. Project/export/receipt/packet rows remained byte-identical, revision remained 2, the committed probe remained exactly 109 bytes, and zero assessments were present. The external evidence is `execution/stage3-migration-rehearsal.json`; neither private runtime data nor credentials enter this repository.

Remaining evidence gates: a real question and substantive human reply/correction through the Switch room, local source review and fresh delivery assessment, a second packet composition, supervised immutable sharing/send reconciliation, second-person access and a genuine freelancer trial. Do not infer these from automated tests or the earlier owner packet smoke test.

## Activated local checkpoint

After the backup rehearsal, the supported launcher restarted the actual desk on8896 with schema3. The original project remained revision2 with the sole109-byte probe and zero assessments immediately after upgrade. The parent then prepared a clearly labelled synthetic brief/checklist draft; Yash explicitly confirmed that checklist, independently observed at revision5. No delivery assessment or share authorization was saved.

An isolated live HTTP/CLI rehearsal created a question, held export with409, recorded/replayed an explicitly automated reply and resolved it locally without a human assessment. A separate actual browser interaction on that isolated copy selected an automated reply, checked sources and observed the authoritative success after refresh. These are automated fixtures, not real participants. External receipts: `execution/stage3-cli-http-rehearsal.json` and `execution/stage3-browser-rehearsal.json`.

The dedicated agent's private client profile explicitly enables version3 while preserving its credential/attachment root; prior profile and instructions were backed up. Approval settings remain unchanged. The real room question is still pending: native app control could expose a draft in accessibility text but did not visibly send it; the browser fallback requires a fresh sign-in. The owner was asked to post a short addressed request in the existing trial channel. No actual agent context-tool invocation or substantive human reply has been claimed.

## Real owner reply received

The actual posted room request reached the dedicated Antigravity session. Its real bounded status and question operations completed after a one-time approval. Question `05ec631ffd794941b0d0a9555c4f022c` is bound to original revision5, the correct requirement and the committed probe. The owner then posted the assistant-drafted internal-purpose answer; after the reply command's one-time approval, the actual reply receipt was independently read from the local service with the correct original question, Discord source reference, exact text/hash and reported speaker. It remains explicitly unverified provenance. The question is pending, the project hold is active, and no assessment/resolution/sharing was saved. Evidence: `execution/stage3-owner-reply-receipt.json`. This is an AI-assisted owner smoke test, not independent customer feedback or a colleague trial.

A final integration review also caught possible loss of an unsaved editor draft during context refresh/acceptance. The card now blocks those actions while the parent has unsaved edits, preserves the existing guarded checklist navigation and displays the required save/discard action. A meaningful interface regression preserves an unsaved assessment and refuses context actions. The fresh105-test UI suite, build and formatting pass.

The owner subsequently reviewed and accepted the exact reply locally. Independent verification observed revision6/context epoch3, the expected used/covered reply, a changed review identity, no remaining context hold and zero delivery assessments. Source receipt: `execution/stage3-owner-context-reviewed.json`. This closes the real question/reply/local-context portion of the owner smoke. The corrected-packet/stale-review/fresh-assessment gate remains open; acceptance of context is not a delivery assessment.

## First actual selected review and observed usability friction

The owner's first save was a valid draft: revision7, no selected file and Unresolved assessment. That failure to complete the intended mapping is retained in `execution/stage3-owner-initial-review.json`; it is not relabelled successful. After explicit guidance, independent inspection observed revision10 with the exact probe selected, Satisfied disposition, current input hash, passing marker check, no workflow hold and reviewed summary. Receipt: `execution/stage3-owner-selected-review.json`. The wording for the reason was assistant-drafted. This remains an assisted owner smoke test, not independent or unassisted user validation.

The interface now describes an empty selection/unresolved assessment before saving and reports those facts in the saved status. It continues to allow legitimate draft judgments. The existing boundary test verifies the draft save still occurs and its incomplete state is visible. Fresh105-interface tests, production build and formatting pass. No backend behavior or actual review was changed by this copy fix.

A clearly labelled assistant-prepared explanatory receipt, based on the actual owner reply and verified original probe identity, is ready outside Git at `execution/spike-fixtures/integration-receipt.md`. It has not been uploaded, staged or imported; the actual corrected-packet/stale-review check remains pending.

## Stage3 assisted owner gate passed

The actual Discord-uploaded1140-byte correction matched its prepared bytes, was downloaded and staged by the dedicated agent after one-time permissions, then explicitly confirmed by the owner alongside the unchanged109-byte probe (1249bytes total). Independent verification at revision11 found the old assessment stale and the earlier question permanently superseded/accepted basis retired. The owner selected both files and saved a fresh Satisfied assessment at revision12; the current summary is reviewed and no workflow hold remains. External receipts: `execution/stage3-discord-correction-receipt.json`, `execution/stage3-owner-correction-confirmed.json`, `execution/stage3-owner-fresh-review.json`. This passes the Stage3 owner-loop gate only. The prepared fixtures, drafted reason and parent guidance make this an assisted synthetic owner rehearsal, not a genuine colleague trial or evidence of time saved. Stage4 begins under its [frozen contract](STAGE-4-CONTRACT.md).
