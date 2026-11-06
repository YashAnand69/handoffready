# Stage 4 — frozen record and supervised return

5 November 2026. Stage3's real owner-operated loop passed at revision12: actual Discord receipt/correction, bounded agent question/reply, explicit local context decision, current initial review, changed two-file packet with stale prior review, then fresh owner review. This is an assisted synthetic owner rehearsal with assistant-prepared data/reasons, not a colleague trial or independent product validation.

## Bounded implementation decision

Use the existing immutable export projection and one Markdown return. A local reviewer previews public content, fixed main-channel destination, draft status and repeat-send risk, then freezes the export and authorizes one return atomically. An agent may prepare that exact artifact and consume a one-use send permission. Sending uses Switch's real `send_attachment` under supervision. HandoffReady never equates a model's assertion, an issued file or an outbox row with transport delivery.

The final outcome is **operator-confirmed**, after the lead downloads the returned attachment, supplies its exact bytes and the Discord message link, and confirms the destination. The backend compares bytes against the frozen artifact and validates the link belongs to the configured Discord channel. This verifies bytes plus a disclosed human destination check, not independent transport authentication. No automatic sender, retries, custom Discord bot/token, remote auth or exactly-once transport claim.

## Pinned transport and research

Read the installed-version source at `switch-console-v0.40.1` (`6ab2ff463ad9518920ba2a15b182b1d2e760fd9f`), not the newer checkout HEAD. `console/packages/switch-agent-runtime/src/hosted.ts` defines `send_attachment(path|paths,caption?,thread_id?,room_id?)`. It reads all named files first, sends to explicit room or current room, and includes a thread only when supplied. Current Stage4 supports the bound main Discord channel only (`binding.thread is None`); no guessed thread mapping. Caption is generated from fixed status/revision/IDs/hash, never untrusted titles/mentions. Agent must use the exact returned Switch arguments once.

Community inputs inspected (including empty comment threads): [An outbox preserves notification intent; delivery deduplication is a separate boundary](https://dev.to/hirodeath/an-outbox-preserves-notification-intent-delivery-deduplication-is-a-separate-boundary-510h) reports a synthetic fake-provider experiment; it does not prove real delivery. [A Pet Photo Is Not Posted Until It Has a Receipt](https://dev.to/susiewang/a-pet-photo-is-not-posted-until-it-has-a-receipt-build-a-durable-community-outbox-16j8) is a sponsored tutorial with a memory repository/unconfigured adapter; its catch-all failed-state example is insufficient for ambiguous sends. Adopt explicit unknown state, not those examples as production guarantees.

## Stored authority and lifecycle

Schema3→4 adds `delivery_shares(id,job_id,body,created_at)` and immutable `delivery_share_events(id,intent_id,body,created_at)`. Frozen body contains export/snapshot/artifact identities, exact destination, source revision/hash, authority digest, status, expiry and byte count. Old project/export layouts and historical bytes remain unchanged. Maximum20 intents/job and5MiB Markdown/intent; existing100-export and1000-operation limits apply.

Authority digest covers current input identity, project name and actual saved decisions (including a digest of private judgment, never its prose in an artifact). Ignore unrelated export history/revision increments; changed review/name/source invalidates unissued authority. Project-wide context/receipt holds block both authorization and first issue. Recheck originals, currency, destination and expiry immediately before issuing permission.

States: `authorized`, `issued_unverified`, `operator_confirmed`, `cancelled`, `cancelled_unverified`; derive `expired`/`superseded` for unissued authority and `is_current` separately. Issued records remain historical when the project changes. No background process or restart can turn issued into sent. Cancelled unverified retains uncertainty. A new authorization for an authority already issued requires an explicit duplicate-risk acknowledgement, including after operator confirmation. No automatic reissue/retry.

## Local actions

Local project read shows history even if integration is disabled. With explicit trusted destination config `{platform:'discord',url:'https://discord.com/channels/<guild>/<channel>',label:...}`, local preview shows public projection, destination and deterministic preview digest. Creation requires exact revision/hash/preview digest, strict confirmation that public content/destination were reviewed, explicit draft acknowledgement if needed, and explicit repeat-risk acknowledgement if previously issued.

Export row, project export history, frozen intent and operation receipt commit together. Stable create-key replay precedes currency checks. Failure rolls back all rows/history. Old exports remain accessible.

Local cancellation requires a reason; cancelling an issued permission additionally acknowledges that the record may already have been sent. Local return verification requires one bounded actual file, issued attempt ID, bound Discord message URL and strict destination confirmation. Exact file SHA/size must match frozen bytes. Wrong job/intent/destination/file refuses without changing outcome. Confirmation after source change labels the return historical, never ready for the newer packet. Verification is local-only and works against retained state when integration is disabled.

## Restricted command bridge

Private client schema4 explicitly adds an owner-private `outgoing_root` and `delivery_take_share`; versions1/2/3 keep2/3/5 tools. No local authorization, cancellation, assessment or verification tool is exposed.

The command first obtains the already-authorized artifact, validates its identities/bounds/hash and writes a stable600 file inside the configured outgoing root, rejecting links/collisions. It then requests one-use issue with the caller-owned operation key and expected artifact SHA. Only the first committed issue can return `send_permitted:true`. A replay returns the committed attempt identity with `send_permitted:false`, no new bytes/send instruction, and reconciliation advice. This intentional consumption flag differs from ordinary mutation-result replay: it must never grant a second external effect. A lost first response remains unverified; it does not authorize blind resend.

The product cannot isolate a same-user unrestricted shell agent from other files or destinations. That limitation remains explicit. Do not read account credentials, call arbitrary messaging APIs or weaken permission settings.

## Required checks and activation gate

Atomic export/intent rollback/replay; old schema/export preservation/newer refusal; binding/local-only actions; exact preview/authority/destination; pending holds including disabled restart; changed source/name/review; expiry; draft/repeat acknowledgements; one-use issue including concurrent claims/replay/lost reply; artifact budgets and output-root confinement; cancellation/unknown retained; exact downloaded-byte verification/bound link; historical verification; privacy projection and mention-free caption. Follow passing checks with backup upgrade and an actual supervised return/download/byte comparison. Code tests are not the live return gate.

## 6 November correction: conversation epoch binding

A scoped independent review reproduced an old authorization becoming usable after a new question was dismissed without changing the review hash. New previews and intents now bind durable project-wide context epochs as well as review authority. Later questions/replies require fresh authorization even after holds clear. Legacy unissued intents lacking epochs fail closed; issued/confirmed history and exact export bytes remain available, conservatively historical. No database/export rewrite. See INDEPENDENT-RETURN-REVIEW-20261106.md for reproduction and scoped checks.
