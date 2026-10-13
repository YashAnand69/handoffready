# Backend stage review

Local API uses the frozen build contract in BUILD-CONTRACT.md. Private project text is stored only in the owner-restricted app data folder; exported client snapshots omit brief/source quotations, model reasoning, parser text and internal notes. Original bytes are not encrypted by the app.

## Deliberate implementation scope changes

- File ingestion runs bounded subprocess inspection during the upload request, not a durable asynchronous inspection job. Per-file deadlines and monitored 512 MiB worker RSS remain enforced; the whole inspection batch has a 120-second deadline. Aborted browser requests may still finish processing, so a refresh must check persisted packet state before retrying.
- Existing registered bytes are immutable until removed/replaced, but inactive original versions are not retained after replacement/removal. Decisions retain capped history (last 200); immutable client exports retain their original projection. Full backup/versioned original restoration is outside this release.
- Current project jobs and client exports are each capped at 100 to bound metadata growth. The 1 GiB quota counts registered original bytes, not SQLite overhead. Export sizes are separately capped at 2 MiB per format, and project/file/brief/text counts bound persistent metadata.
- Single process is required. SQLite writers serialize through one process lock and short BEGIN IMMEDIATE transactions. Multiple uvicorn workers are unsupported because their tokens and model scheduling would differ.
- A single server-session token lasts until app restart. Sensitive reads require it, mutations additionally require an exact allowed Origin. Bootstrap is not a private-data endpoint; no wildcard CORS is provided. Tokens are not sent in download URLs.
- API creation and job/export starts use revision/concurrency protection; durable idempotency-key replay is not implemented. The frontend must disable duplicate actions and refresh after an ambiguous request. The full planning API's source-unit endpoint is replaced by the private current brief/file text within the project envelope, while quotations still require a unique literal match.
- Saved source quotation spans are derived by the backend against canonical Unicode code-point text. Submitted offsets are never trusted. The private store keeps the last 20 baseline/source snapshots and last 20 replaced proposal batches; neither history nor source text enters client exports. Inactive original byte backup remains outside this release.
- The app's global inference lock imposes a 120-second queue/execution publication budget. Application cancellation prevents result publication; it does not claim to kill the separate model server generation. A finished late response is discarded, never marked completed.

## Review findings resolved

- Extraction captures brief hash plus draft baseline identity. An edit to the human checklist during generation discards the old response.
- Every selected-file check requires a confirmed decision bound to the current input hash; stale historical passes cannot appear as current checks.
- Parser stdout uses a temporary file rather than a pipe, avoiding deadlock when large Unicode extracted text fills a pipe. Worker cleanup kills/reaps children and closes output on failure.
- Registered uploaded bytes are preserved if post-commit response cleanup fails. Failed pre-commit batches are discarded atomically.
- Strict typed checks reject booleans as counts, absent count semantics, unexpected parameters and out-of-bounds units.
- JSON request bytes are capped independently at 256 KiB before parsing; multipart requests have a 52 MiB fence plus 10 MiB/file and 50 MiB/packet checks.
- Non-ASCII bogus tokens are rejected safely using constant-time byte comparison.
- Authenticated visual previews permit only inspected PNG/JPEG originals, verify immutable hashes, cap reads and deny blocked/text/SVG/PDF previews. These are for human visual review; the model does not inspect image appearance.

API tests explicitly use an injected fake model to test workflow/race invariants. They are not evidence of actual model quality; the model stage provides separate real inference evidence.
