# Stage 2 contract — complete packet intake

4 November 2026. Implementation contract for the additive delivery layer; not a claim of a finished workflow. Existing owner-operated Discord file return, restored room membership, and an actual Switch-managed Antigravity scoped CLI status call justify moving to the bounded intake build. A dedicated-agent packet loop and a second-person trial remain release gates.

## Roles and limits

The scoped assistant may stage a received attachment and read safe status/selection previews. Only the authenticated local desk previews/confirms a complete packet. Neither staging nor packet confirmation is a human assessment, scope approval, or share authorization. Source identifiers supplied by an assistant are **unverified conversation provenance**; the lead explicitly checks selection against the room before committing.

A packet is an explicit nonempty selection of at most30 receipt IDs, at most50MiB total and10MiB/file, within inherited parser/text/storage limits. It replaces the whole current packet; never silently append or merge. Reject filename collisions after NFC/casefold normalization. Distinct filenames with identical bytes are allowed as evidence of a possible duplicate, never proof of distinct designs.

Staging remains bounded by the existing60 receipts/job and100MiB total retained staging budget. This stage does not silently expire or discard receipts to make space. Reaching that limit is an explicit operator action; controlled retention/cleanup remains a later recovery task. Do not describe this as unlimited production retention.

## Service interface (backend owner)

Keep one Store owner. Add a versioned migration1→2 transactionally; do not change the legacy projects/exports layouts or content. Add `delivery_packets(id, job_id, manifest_hash, body, created_at)` with explicit columns. `body` is bounded JSON containing selected receipt identities, considered receipt IDs, committed file IDs/revision/hash and changed flag. Existing operation/result budgets apply.

- `list_receipts(job_id, binding)` returns `{job_id, source_revision, input_hash, receipts, pending_count, last_packet}`. Each receipt: `{receipt_id, source_id, filename, sha256, size, availability, considered}`; availability is available/unavailable/changed. `last_packet` is null or `{packet_id, receipt_ids, considered_receipt_ids, source_revision, input_hash}`. No paths/file text/private notes.
- `preview_packet(job_id, binding, *, receipt_ids, expected_revision, expected_hash)` returns `{job_id, source_revision, input_hash, manifest_hash, receipts, considered_receipt_ids, excluded_receipt_ids, total_bytes, changes, review_will_be_stale, replaces_entire_packet:true}`. `excluded_receipts` names each excluded receipt (identity, source, filename, hash and size) from the same snapshot as the manifest; the UI must not rely only on an older intake list. `changes` has added/replaced/removed/unchanged arrays of filenames. Selected receipts must belong to this job and have current bytes available. The digest covers binding/job, selected identity/name/hash/size, **all receipt identities present at preview**, and expected revision/hash. A later receipt arriving changes the digest, requiring another preview.
- `confirm_packet(job_id, binding, operation_key, *, receipt_ids, expected_revision, expected_hash, manifest_hash, inspect_file)` returns the existing operation envelope with **committed** source_revision/input_hash and `result:{packet_id, changed, file_ids, manifest_hash}`. `inspect_file(path,name,deadline)` is the inherited bounded inspector, passed by the API to avoid circular imports.
- `context_for_project(project_id,binding)` returns null when no bound job, otherwise `{job_id, ...list_receipts result}`. The local route wraps it as `{enabled:true, job:object_or_null}`; when the feature is disabled it returns `{enabled:false,job:null}`.

Require exact integers/identifiers/digests, unique nonempty receipt IDs. Binding enforcement precedes replay lookup. The operation digest includes all input fields except operation_key. Same key/same input returns its historical result **before** current revision/receipt/parser checks; same key/different input conflicts. New operations check current revision/hash/manifest again before committing. A new key importing identical filenames+bytes may record a new considered-receipt manifest, but preserves existing file IDs/project revision/assessments when the actual packet is unchanged.

## Atomicity and recovery

Prepare bounded copies under integration storage and run inherited parser isolation outside the SQLite write transaction. Recheck receipt hashes while copying, not just their stored metadata. Reject unsupported/blocked candidates as a whole and retain the existing packet/review. Before applying, reacquire the Store lock and BEGIN IMMEDIATE, repeat replay first, recheck currency/manifest, then register all new originals, project body and packet+operation receipt together. Do not call Store.mutate inside an existing transaction or hold a write transaction during parsing.

Unchanged current files can retain IDs/inspection records only after originals are reconciled and source identity matches. Changed input preserves proposal/decision history and invokes inherited invalidation. Original exports remain byte-for-byte unchanged. No partial packet is registered. The supported launcher owns the data-directory lock before recovery. Under a Store-shared preparation lock, startup and each new confirmation recover only recognized owner-private `packet-*` scratch directories containing owned regular receipt copies. Unknown/link contents refuse recovery and are preserved for operator attention. Scratch has no database references; receipt, original and outgoing stores are untouched. At most one bounded packet is prepared after abandoned copies are recovered. Old original bytes are removed only after confirmed commit; interruptions may leave bounded unregistered files for startup cleanup. Do not delete possibly registered new bytes on an ambiguous commit exception: reconcile the operation row first, or retain evidence and report an explicit unknown outcome.

The latest committed packet records **all considered receipt IDs**, including excluded files shown to the lead. Only later unconsidered receipts count as pending. Historical staged-byte damage does not falsely damage independently verified committed originals. Pending input is visibly awaiting packet confirmation and cannot be reported as a fresh ready delivery. Staging itself does not alter saved decisions. A selection is not proven complete merely because every selected file arrived; completeness is the lead's explicit declaration.

## HTTP and CLI boundary (integration owner)

Keep scoped credentials limited to GET status, POST preview and new POST `/api/v1/delivery/jobs/{job_id}/receipts`. Receipt body: `{operation_key,source_id,filename,content_base64}`. Validate base64 strictly and enforce the actual decoded byte limit. Only this exact enabled route may receive its bounded base64 body budget; other JSON endpoints retain256KiB. No body/path/token echoes in validation errors.

Local-token-only endpoints:

- GET `/api/v1/projects/{project_id}/delivery` → context wrapper above (also works disabled).
- GET `/api/v1/delivery/jobs/{job_id}/receipts` → list_receipts.
- POST `/api/v1/delivery/jobs/{job_id}/packet-preview` body `{receipt_ids,expected_revision,input_hash}` → preview_packet.
- POST `/api/v1/delivery/jobs/{job_id}/packet-confirm` body `{operation_key,receipt_ids,expected_revision,input_hash,manifest_hash,confirmed_complete:true}` → confirm_packet. False/missing confirmation refused. Never expose confirmation on the model tool list.

Preserve existing two read tools. Add `delivery_stage_receipt` only when private client config version2 supplies an absolute `attachment_root` alongside the version1 origin/binding/token fields. Version1 remains valid and read-only. Stage tool arguments exactly `{job_id,operation_key,source_id,filename,file_path}`. No model-supplied root/origin/header/token/base64. Read a bounded owner-owned regular single-link file confined to configured root using O_NOFOLLOW for each component, reject traversal/symlinks/non-regular/oversized files, and return a redacted structured error. The root and its resolution are checked at configuration. This remains a product boundary, not OS isolation from a same-user assistant's other tools. MCP and CLI share the same client validation; default read-only compatibility is retained.

## Local desk

Show room intake only for a bound job. List received files, available/changed/unavailable state, and whether previously considered. Select pending files by default as a proposal. The lead may include earlier unchanged receipts to declare the full packet; no silent merge. Refuse a preview selection outside1–30 files. Show previewed added/replaced/removed names, exclusion count and each excluded filename/source, and warn that changed content invalidates earlier assessments. Require an explicit checkbox confirming comparison with the conversation and completeness. Store a stable operation key for the preview through retries; a network failure must not silently create a fresh key. Refresh current project/context after success, including historical replay. Old app projects and delivery-disabled mode continue to work.

## Evidence gate

Test migration1→2 preservation and newer-schema refusal; partial/foreign/tampered/colliding inputs; whole-packet rollback on parser/disk failure; concurrent duplicate confirmation; replay after revision advancement; unchanged packet no-op; real correction causing stale decisions while exports persist; restart before/after commit; exact scoped authorization; strict CLI confinement/redaction; and user-visible preview/confirmation/retry behavior. Use synthetic data only. Run appropriate full inherited suites after integration and an actual disposable-service browser rehearsal. No automated fixture is a human trial.
