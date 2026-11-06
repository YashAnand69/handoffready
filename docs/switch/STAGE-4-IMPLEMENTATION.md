# Frozen record and supervised return — Stage4 checkpoint

5 November 2026. Code is installed on the actual local desk at8896. The actual record has appeared in the main Discord channel and its downloaded bytes match. The owner completed the explicit local destination confirmation at15:39:49UTC (21:09:49IST). Stage4 passed as an assisted owner-operated synthetic return, labelled operator-confirmed.

## Implemented behavior

The local reviewer reads the exact public projection and configured main Discord destination, then authorizes one frozen Markdown return. Drafts require an explicit draft acknowledgement. Repeated issuance of the same review requires a separate duplicate-risk acknowledgement. One review cannot accumulate several active authorizations.

Export bytes, export history, the immutable authorization and the idempotency receipt commit in one SQLite transaction. Authority binds the actual source/review/name, not incidental export-history revision increments. Pending room context or files block both authorization and issuance. Changed source/name/review, changed destination or expiry refuse an unissued return.

Private client schema4 adds only `delivery_take_share` and a separate owner-private outgoing folder. The tool verifies the frozen bytes/identity, prepares a600 Markdown file without following links or overwriting a conflicting artifact, then consumes one send permission. Only the first issue returns true permission and exact Switch arguments. Replays, lost responses and refusals do not authorize another send. It does not send anything itself, authorize a record or confirm delivery.

The agent's actual return uses the pinned Switch0.40.1 `send_attachment` once, with the explicit bound room and fixed caption. No guessed APIs, new Discord credentials or settings bypasses are used. A send error or missing reply remains unknown externally. HandoffReady keeps `issued_unverified` through restart rather than treating an outbox row, provider response or model claim as delivery proof.

The lead verifies by downloading the actual returned Markdown and supplying its bytes and exact Discord message link in the local desk. The server checks hash/length against the frozen record and validates the configured channel; the human explicitly checks the destination. The outcome is labelled **operator-confirmed**, not authenticated transport proof or client acceptance. Historical returns stay historical when the current packet changes. Cancellation preserves any earlier unknown send and never silently retries it.

The interface keeps one operation key/body through a lost reply and remount. Verification can reselect the same returned file even if the previous write succeeded but refresh failed. The actual project and returned-record history must refresh and contain the expected record before a success message appears. Existing immutable exports and downloads remain available.

## Checked evidence

Fresh full runs: **523 backend tests,116 interface tests**, production build, formatting and whitespace checks passed. The existing Starlette/httpx deprecation remains. No dependencies were added. [Machine-readable scope and fingerprints](verification-stage4-20261105.json).

Synthetic checks cover transactional rollback/replay, strict confirmations, binding/local-only actions, public projection, concurrent permission consumption, changed authority/destination, pending holds, expiry, draft/repeat risk, cancellation uncertainty, exact downloaded-byte/channel verification, disabled restart, historical returns, private-path confinement and lost issue replies. These are tests, not a security certification.

A consistent database/evidence backup preceded upgrade. On a separate copy, schema3→4 preserved original project/export/packet/receipt/context rows byte-for-byte. An actual local HTTP/CLI rehearsal prepared the exact2033-byte Markdown, issued once, refused retry, and exercised byte verification using an explicitly automated file/link fixture. No Switch send, Discord post or human destination check occurred in that rehearsal. External receipt: `execution/stage4-cli-http-rehearsal.json`.

An actual browser rehearsal on that separate copy exercised public-content/repeat-risk acknowledgement and observed an authorized record after authoritative refresh; no send occurred. Screenshot: `execution/stage4-browser-authorization.jpg`. The isolated8897 service was subsequently stopped so it is not confused with the live desk.

Actual8896 activation preserved the prior data rows and the owner's reviewed revision12 with both files. Zero live share intents existed at activation. Existing credential, binding and permission settings were retained; previous profiles/instructions were backed up. The real destination preview was opened for the owner with its checkbox unchecked. Receipt: `execution/stage4-activation.json`; screenshot: `execution/stage4-owner-share-preview.jpg`.

Stage4 parent code was reviewed through explicit invariants, fault tests and browser/HTTP rehearsals; there is no fresh independent full-code sign-off. Earlier scoped reviewers reached their account quota during Stage3. No genuine colleague trial, full recovery/release pass, contest submission or outcome claim is made.

## Live gate and supported limits

The owner authorized intent `3b7f827b10e64f9fbddf018ade6cc16b` at15:32:22UTC and approved the scoped return tool. One Switch send-attachment activity completed at15:36:12UTC. Discord visibly contains the Markdown in its configured main channel, message `1567925513228656710`. The independently downloaded2033bytes match SHA-256 `1ea3d1b45cddd7a1d73547c94e24df03a9bb536aef1b01ede11957926d8094f8`. At the initial observation, local state remained `issued_unverified`; the downloaded file/link were prepared with the human checkbox unchecked. The subsequent owner confirmation is recorded below. Receipt: `execution/stage4-actual-return-observed.json`. This is an assisted synthetic owner rehearsal, not a colleague trial or authenticated transport receipt. The normalized Switch activity journal exposes completion but does not independently expose the send arguments.

The owner finished the explicit local destination/byte check at15:39:49UTC; retained state is `operator_confirmed`, with verification `operator_checked_destination_and_exact_bytes`. Receipt: `execution/stage4-owner-verified-return.json`. This passes Stage4's real-return gate within its disclosed limits. Stage5 still needs ordinary failure/restart checks and an independent quality pass; Stage6 needs a disclosed actual colleague trial if available. Do not infer any of these from the automated fixture's operator-confirmed label.

Current return supports only the explicitly configured main Discord channel and one Markdown projection. It excludes original delivery bytes. Maximum20 retained intents/job and5MiB/artifact; no silent retention cleanup. Expired or unverified work is never automatically resent. This remains a local lead-operated service with supervised sending, not remote multiuser auth or isolation from an unrestricted same-user shell agent. [Frozen implementation decisions and sources](STAGE-4-CONTRACT.md).

## 6 November independent correction

The scoped final return review found and repaired context-hold clearance resurrecting old send authority. New authorizations bind conversation epochs; legacy receipts remain retained and verifiable but historical. The earlier live owner return is still valid historical evidence. This repair was installed after a consistent private backup, 536 passing backend tests, and a passing production build/format check. Read-back preserved revision13/two files/one export/operator-confirmed history; legacy history is conservatively historical. See INDEPENDENT-RETURN-REVIEW-20261106.md.
