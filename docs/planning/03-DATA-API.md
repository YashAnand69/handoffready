# HandoffReady — Data model, state transitions and API contract

Version 0.1 · 13 October 2026 · Planned contract, not implemented endpoints. Canonical numeric limits and parser/model budgets are in `02-TRD.md`. API schemas must be frozen in Stage 0 and generated into TypeScript/OpenAPI; agents must not invent divergent fields. UTC timestamps are RFC 3339 strings; UI displays the user's timezone. IDs are server-generated UUIDs, sizes are bytes, pixel/page/count values are integers, digests are lowercase SHA-256 hex. No percentage confidence field exists.

## 1. Database entities

SQLite migrations are explicit numbered scripts, with foreign keys, schema-version metadata and a tested transaction for each migration. Prepared parameters only. All entities have `id`, creation timestamp and `project_id` where applicable.

| Entity | Important fields and relationships |
|---|---|
| Project | `name`, `revision`, `active_baseline_id`, `packet_revision`, `current_packet_hash`, `created_at`, `updated_at`, `deleted_at`; deletion is a purge operation, not a reusable soft-delete product feature |
| SourceUnit | immutable `origin` (`brief_paste` / `delivery_text` / `pdf_page`), `original_file_version_id?`, `page_number?`, canonical `text`, `text_sha256`, `extraction_revision`, `parser_version`; brief paste preserves owner-supplied source label |
| Baseline | immutable approved version: `requirements_json`, `baseline_hash`, `source_unit_ids`, `state`, `supersedes_id?`, `approved_at?`; draft changes produce new revision; source/baseline changes mark prior approvals stale |
| Requirement | stable logical `requirement_id` within baseline, `title`, `origin` (`model_suggested` / `human_added`), source span(s), `check_specs`, `count_semantics`, `human_note`; each approved version stores complete copied rows |
| FileVersion | logical `file_id`, version UUID, display name, original byte hash/size, immutable private storage key, declared extension, identified type, active flag, inspection state/reason, metadata/extraction policy and source-unit IDs; no client-visible filesystem path |
| CheckResult | requirement/baseline/file-version references, `kind`, typed `expected`/`actual`, `status`, reason, `evidence`, `input_snapshot`, validator version, created timestamp; never mutate fail to pass because of a human note |
| MatchProposal | requirement reference, candidate file-version IDs, source evidence, explanation, model provenance, `input_snapshot`, validation status, coverage note; not an approval |
| ReviewDecision | requirement, selected file-version IDs, proposal ID if used, `review_state`, `human_disposition`, `internal_decision_note`, `client_usage_note` (default empty), `input_snapshot`, timestamp; immutable history, separate active pointer; rejected proposals need no matched file |
| Job | kind, state, immutable kind-specific inputs, stages/coverage, attempt, cancellation flag, safe error, timestamps; one app worker; no automatic retry on restart |
| Export | immutable snapshot JSON + rendered Markdown/JSON/HTML bytes, snapshot hash, export version, safe client projection version, unresolved acknowledgment, created timestamp; no delivery original bytes |
| AuditEvent | action enum, object IDs, revision, timestamp and safe structured deltas; private local review trail; avoid duplicating complete prompts/client content in log messages |

Metadata/check specifications should be versioned JSON stored alongside their discriminators, validated on every read/write. This avoids a five-day over-normalization project while maintaining typed domain boundaries. Core foreign keys and uniqueness constraints are real SQL constraints, not frontend conventions.

## 2. Immutable identity and revisions

- `project.revision` increments on every committed user mutation and publication of new inspection/model results. It supports optimistic UI concurrency; it is not the only stale-job guard.
- Every newly created project has an empty immutable draft baseline version, so pre-approval jobs have real baseline IDs/hashes rather than invented approvals. Approval requires at least one requirement. `baseline_hash` is SHA-256 of a deterministic canonical serialization of source hashes, ordered requirement IDs, approved titles, source spans, typed check specifications and count semantics. Approval time and unrelated UI state are excluded.
- `packet_hash` is SHA-256 of a deterministic serialization of **active** file logical/version IDs, display names, original byte hashes and identified types, sorted by stable file ID. Excludes upload order/timestamps; a changed display name still changes the packet identity.
- `source_set_hash` covers all relevant immutable source IDs/text hashes/extraction revisions and inspection policy version. Failed/unknown extraction facts are represented explicitly, not omitted to imply completeness.
- `InputSnapshot` for matching/decisions/export is `{baseline_id, baseline_hash, packet_hash, source_set_hash, validator_revision}`. Model provenance is attached to a proposal; a changed model must not retroactively change its origin.
- Job output commits if its relevant input fields still match and it is neither cancelled nor superseded. Extraction jobs compare current source ID/text hash and draft-baseline hash; inspection jobs compare active file version/packet hash and parser-policy revision; matching jobs compare the complete baseline/packet/source/validator tuple. Export compares the full tuple and current project revision. Unused snapshot fields are recorded for audit but do not invalidate an otherwise current parser/extraction job. An unrelated user note or earlier job completion may change project revision without invalidating the inputs; a mutation to the fields relevant to that job kind invalidates it.
- Any active packet mutation conservatively marks current mappings and human dispositions `stale`; the approved brief baseline remains approved. Changing the brief or requirement specifications creates a new draft baseline and stale prior dependent evidence. UI must re-review decisions. Preserve history without marking a changed baseline approved.
- Every foreign ID must belong to the same project and exact baseline/file version. A SHA-256 supplied by the browser is never trusted as the original-byte digest; the backend computes it.

### Kind-specific job inputs and publication guards

Do not require future inspection output to exist when scheduling work. `Job.inputs` is a discriminated union, not the review snapshot reused indiscriminately:

```text
ExtractionInputs {
  kind: extract,
  source_unit_id, source_text_sha256, draft_baseline_hash,
  extraction_revision, prompt_revision, model_artifact_sha256
}
InspectionInputs {
  kind: inspect,
  packet_hash,
  files: [{file_version_id, original_sha256}],
  parser_policy_revision
}
MatchingInputs {
  kind: match,
  input_snapshot: InputSnapshot,
  requirement_ids, prompt_revision, model_artifact_sha256
}
```

Extraction validates its selected current source and draft baseline. Inspection validates current active file versions, bytes/packet and parser policy; **it does not depend on a future `source_set_hash`**. Matching validates the complete review input tuple. Model identity/prompt revision always bind the run's provenance; an explicit configuration change cancels/supersedes in-flight requests instead of relabeling their outputs. Before publishing, compare captured relevant inputs inside the transaction, then insert results and update derived hashes atomically. The worker's own new source units/identified types naturally change derived hashes after that successful comparison; do not compare the newly produced source hash to its pre-job value and falsely self-supersede. An unrelated project note/revision change does not invalidate the job. A selected-source edit, active-file change or deletion does. Record the initial project/baseline revision additionally for audit, without pretending an empty draft is an approved baseline.

Canonical serialization must be explicitly specified in tests: UTF-8; sorted object keys; no extra whitespace; arrays sorted only where the schema states they are sets; integers serialized as integers; no NaN/Infinity; Unicode code-point text unchanged beyond newline conversion. Python and browser need not independently compute approval hashes: backend returns the authoritative digest.

## 3. Source span contract

```json
{
  "source_unit_id": "uuid",
  "source_text_sha256": "64-character hex",
  "start_cp": 37,
  "end_cp": 92,
  "quote": "Three 1080 × 1080 launch images in PNG format.",
  "page_number": null,
  "extraction_revision": "native-v1"
}
```

Numbers above are illustrative, not a validated index for that quote. The invariant is `Array.from(source.text).slice(start_cp,end_cp).join('') === quote` in JS and `text[start_cp:end_cp] == quote` in Python. Require `0 ≤ start_cp < end_cp ≤ len_cp`, matching source hash and ≤500-code-point quote. Recompute server-side; reject mismatches. The model returns source ID plus exact quote; the server resolves a unique occurrence. Ambiguous occurrences are unapproved and require a human-selected span, never first-match guessing. A source link names an immutable extraction/page; UI cannot reflow/re-normalize the text and reuse old offsets.

No source span is invented for manually added requirements. `origin=human_added` with no span displays that fact and requires a human note. The backend retains original canonical source text privately so source navigation remains reproducible after refresh.

## 4. Typed deterministic checks

```text
CheckSpec =
  presence { allowed_types: [png|jpeg|svg|pdf|text|markdown] }
  count { comparison: exact|at_least, value: integer 1..30, distinct_bytes: boolean, allowed_types: [...] }
  image_dimensions { width_px: integer 1..10000, height_px: integer 1..10000 }
  png_nonopaque_pixels { required: true }
  pdf_pages { comparison: exact|at_least, value: integer 1..10 }
  literal_text { source_file_id: uuid?, needle: string 1..500 code points }
  manual { instruction: string 1..2000 code points }
```

Check specs cannot contain executable patterns, arbitrary code, remote URLs or SQL. No unbounded regex. Empty type lists and contradictory parameters reject with field errors. `literal_text` is case-sensitive exact text against the displayed canonical extraction; a hit does not prove the requested instructions are good. Semantic instructional adequacy uses `manual` and human disposition, with model-proposed supporting paragraphs. Requirements about visual distinction, functioning features or quality are manual regardless of hashes/metadata.

`CheckResult` contains `status=pass|fail|unknown|not_applicable`, `reason_code`, explanatory message, expected/actual, input snapshot and evidence. Examples: `encoded_dimensions_match`, `opaque_png`, `exact_duplicate_excluded`, `encrypted_pdf`, `no_extractable_text`, `unsupported_svg_units`, `parse_timeout`, `file_missing`, `manual_required`. `unknown` and `fail` are different; a parser failure cannot prove absence or satisfaction. Manual check result stays `unknown/manual_required` even when the human disposition is `satisfied`; the report shows both.

## 5. State transitions

### Baseline

`draft → approved` only through explicit whole-baseline confirmation after row review. Approved baseline editing creates a new draft version and marks dependent decisions stale; it never edits an approved snapshot in place. Approval requires valid source spans for model-origin clauses, confirmed typed parameters and no unresolved contradictory interpretation. Human additions remain visibly human-origin. Rejecting model suggestions is permitted and retained in history.

### File/packet

`queued → running → inspected | blocked`. Byte receipt is separate from inspection. Type/size/page/pixel limits and unsupported inputs give visible per-file results. Inspection results publish only to the matching current file version. Inspection may run before baseline approval; approving a baseline recomputes its checks from saved current metadata/extracted text without reparsing files. File mutation and subsequent inspection publication recompute affected checks and preserve unknown/blocked states. Removing/replacing/renaming a file changes packet identity and invalidates confirmations. Selecting a file with the same display name is not an implicit replacement; the UI must identify the target logical file ID explicitly.

### Job

`queued → running → succeeded | failed | cancelled | superseded`; restart converts prior `running → interrupted`. User retry creates a new job with a new current snapshot, never resets history. Cancellation on `queued` is immediate; running cancellation prevents result publication regardless of whether the model server finishes its internal work. Terminal states do not revert. Only one active inspection/model job per project and one model request globally; conflicting starts return `409 job_active`.

### Review

Model proposal starts `unreviewed`; user `confirmed` selects exact file versions and a human disposition/note, or `rejected` declines the proposal. User may select files without a model proposal; origin records `human_selected`. A packet/baseline mutation produces `stale`. No checkbox begins confirmed by default. Current deterministic fail remains visible when a person chooses `satisfied` or `not_applicable`; unresolved technical discrepancies are called out in export rather than hidden.

## 6. HTTP conventions and security

Base `/api/v1`, same origin. JSON uses `Content-Type: application/json`; uploads use bounded multipart. All sensitive reads and writes require `X-Handoff-Session`; every mutation also requires `X-CSRF-Token` and exact approved `Origin`. Tokens are bootstrapped same-origin and held in browser memory. Production origin is `http://127.0.0.1:8877`; model URL is trusted fixed loopback configuration, never a request parameter. API returns `Cache-Control: no-store`; Host checks apply to bootstrap too. GET never mutates state. Missing/null/unapproved Origin on mutation rejects. No arbitrary CORS or remote URL ingestion.

All project mutations use `If-Match: "project-r42"` from the current project response/ETag. Missing precondition returns `428`; stale precondition returns `409 revision_conflict` and safe current revision. User must reload/review, never auto-overwrite. Jobs capture input hashes before running. Destructive delete also requires the latest revision and explicit UI confirmation.

Successful JSON:

```json
{"data":{"id":"uuid","revision":42},"meta":{"request_id":"uuid","schema_version":"v1"}}
```

Error JSON:

```json
{"error":{"code":"revision_conflict","message":"The packet changed. Refresh before saving this decision.","fields":[],"retryable":false,"current_revision":43},"meta":{"request_id":"uuid"}}
```

Use `400` malformed request, `403` session/CSRF/Host/Origin rejection, `404` missing object, `409` conflict/gate failure, `413` byte limit, `415` unsupported upload input, `422` validated field errors, `428` missing revision, `503` model unavailable. Do not put stack traces, paths, raw document text or secrets in errors. File inspection can report `blocked` inside a successful job; this is a domain result rather than an HTTP parser traceback. `202` means job accepted, not completed or approved.

`Idempotency-Key` (UUID) is required for create project/start job/create export operations; persist operation+project+payload hash+response for 24 hours. Same key/same payload returns same result; changed payload returns `409 idempotency_conflict`. Ordinary PATCH/PUT decisions rely on revision control rather than bespoke idempotency. Session/CSRF validation still occurs on replay.

## 7. Endpoint inventory

| Method/path | Input | Output and gate |
|---|---|---|
| `GET /bootstrap` | Same-origin request, exact Host | In-memory session + CSRF token, app/schema version; no private project data; no cookie/URL secret |
| `GET /capabilities` | Session | Canonical limits, supported types, model readiness/provenance, runtime mode (`local`); never returns assumed readiness |
| `GET /projects` | Session | Project IDs/names/current revisions, bounded list ≤10 |
| `POST /projects` | `{name}` + idempotency | `201` project with an empty immutable draft baseline ID/hash and empty packet hash; name 1..120 code points; quota enforced |
| `GET /projects/{id}` | Session | Current project, baseline summary, file results, proposals/decisions, active jobs, readiness gaps; ETag |
| `PUT /projects/{id}/brief` | `{text,source_label}` + If-Match | Immutable canonical source; new draft state and revision; invalidates current baseline-dependent approvals; max20k code points |
| `GET /projects/{id}/sources/{source_id}` | Session | Exact canonical text/hash/parser revision/page and UTF code-point convention; only same-project sources |
| `POST /projects/{id}/jobs/extract` | `{source_unit_id}` + If-Match + idempotency | `202` job; source current, model ready, no conflicting job; suggestions only |
| `PUT /projects/{id}/baseline` | `{requirements:[...]}` + If-Match | Validated draft rows and new revision; 0..20 in draft (approval requires1..20), explicit origins/typed specs/source spans |
| `POST /projects/{id}/baseline/approve` | `{baseline_id,baseline_hash,reviewed_requirement_ids:[...]}` + If-Match | Approved immutable baseline; reviewed IDs must exactly equal included current rows, valid evidence/parameters |
| `POST /projects/{id}/files` | multipart `files[]` + If-Match | `201` file versions/receipts; aggregate active30/50MiB and per-file10MiB; transaction registers all accepted bytes atomically; no implicit same-name replacement |
| `POST /projects/{id}/files/{file_id}/replacement` | multipart one `file` + If-Match | New active version, prior version retained as inactive local history; quota enforcement and approval invalidation |
| `PATCH /projects/{id}/files/{file_id}` | `{display_name}` + If-Match | Sanitized name/revision; invalidates hash-bound current matches |
| `DELETE /projects/{id}/files/{file_id}` | If-Match | Remove active pointer, invalidate decisions, retain historical metadata; pending jobs cannot resurrect it |
| `POST /projects/{id}/jobs/inspect` | `{file_version_ids:[...]}` + If-Match + idempotency | `202` bounded job on active pending versions; blocked outcomes remain visible; computes check results after approved baseline where applicable |
| `POST /projects/{id}/jobs/match` | `{baseline_id,requirement_ids:[...]}` + If-Match + idempotency | `202`; approved current baseline and completed or explicitly blocked inspection; eligible evidence only; track not_proposed coverage |
| `GET /projects/{id}/jobs/{job_id}` | Session | Saved state/stage/coverage/error; polling, no inferred percentage |
| `POST /projects/{id}/jobs/{job_id}/cancel` | If-Match | Cancellation acknowledged; eventual terminal state; no silent automatic retry |
| `PUT /projects/{id}/decisions/{requirement_id}` | See decision schema below + If-Match | Saved current hash-bound human decision, review and disposition; validation does not rewrite checks |
| `POST /projects/{id}/exports` | See export schema + If-Match + idempotency | `201` immutable three-format snapshot/URLs; reject if inputs changed or acknowledgment missing |
| `GET /projects/{id}/exports/{export_id}/{format}` | Session, format `json|md|html` | Immutable download bytes; `Content-Disposition: attachment`; escaped script-free HTML, no external resources |
| `DELETE /projects/{id}` | If-Match | Purge project/originals/exports, cancel jobs; current state cannot be republished by late result; forensic limitations disclosed |

Bootstrap URL is `/api/v1/bootstrap`, not a cross-origin publicly exposed credential service. Implement all read checks before returning private data. Project/file upload has no server-path or URL field. Optional future PDF-brief import belongs to a separately reviewed endpoint, not hidden inside text intake.

Uploads use an ASGI stream-byte fence before multipart parsing: multipart request ≤52 MiB including overhead, ≤30 file parts, bounded names/form fields, no duplicate control fields. Per-file/application/packet caps remain independently checked during streaming. Stage temporary bytes and all receipt records; if any hard byte/count/quota constraint fails, discard the whole request and report the offending constraint, preserving previous packet. Unsupported type is a visible blocked receipt only if safely accepted within caps, with no parser execution; do not silently drop it. Rate-limit one upload batch per session while it is in progress. Initial bytes must not count as inspected just because an upload returned `201`.

## 8. Main payload examples

### Model proposal (validated server output)

```json
{
  "proposal_id":"uuid",
  "requirement_id":"uuid",
  "file_version_ids":["uuid"],
  "evidence":[{"source_unit_id":"uuid","source_text_sha256":"hex","start_cp":0,"end_cp":17,"quote":"illustrative text","page_number":2,"extraction_revision":"native-v1"}],
  "reason":"This supplied paragraph describes changing contact details.",
  "validation_status":"valid",
  "review_state":"unreviewed",
  "input_snapshot":{"baseline_id":"uuid","baseline_hash":"hex","packet_hash":"hex","source_set_hash":"hex","validator_revision":"v1"},
  "model_provenance":{"model_revision":"pinned-at-stage-0","artifact_sha256":"hex","runtime_commit":"pinned-at-stage-0","prompt_version":"match-v1","schema_version":"v1"}
}
```

Examples use placeholders and illustrative offsets. Files with no text can have metadata evidence `{file_version_id, original_sha256, metadata_key, value, inspection_revision}`. The model may propose an image file by name/metadata but must explain that visual content was not inspected. No bogus source quote is necessary for such a mapping; resulting visual/semantic adequacy stays manual.

### Human decision

```json
{
  "proposal_id":null,
  "selected_file_version_ids":["uuid"],
  "review_state":"confirmed",
  "human_disposition":"needs_work",
  "internal_decision_note":"Guide contains the contact steps, but the screenshots still show the old screen.",
  "client_usage_note":"",
  "input_snapshot":{"baseline_id":"uuid","baseline_hash":"hex","packet_hash":"hex","source_set_hash":"hex","validator_revision":"v1"}
}
```

Reject unknown/stale input tuples; selected versions must be active/same-project. `internal_decision_note` is private evidence-review commentary and never exported; `client_usage_note` is a distinct optional 0..2,000-code-point field, default empty, shown in the exact client preview before sharing. `confirmed` means the user confirmed a mapping, not that the deliverable passed. `rejected` requires a proposal ID and declines that proposal; separate human file selection remains possible. `not_applicable` requires a note and stays visible. `satisfied` with a deterministic failure raises an explicit discrepancy in current readiness/export; it does not turn the check green. A reviewer may acknowledge the discrepancy for draft handoff, but the record remains honest.

### Export creation

```json
{
  "baseline_id":"uuid",
  "input_snapshot":{"baseline_id":"uuid","baseline_hash":"hex","packet_hash":"hex","source_set_hash":"hex","validator_revision":"v1"},
  "acknowledge_unresolved":true
}
```

Return export ID, snapshot hash, timestamp, gaps, three immutable download endpoints and format sizes. All three P0 formats derive from the same safe client projection of the same snapshot. They exclude raw source quotes and full source text; the source-linked evidence remains available inside the private local app. A private evidence archive or explicit source-sharing mode is P1 with a separate privacy review. Include project name, confirmed requirement text, final file display names/type/hash, exact technical check scope, human dispositions, explicitly entered client usage notes, unresolved/stale/manual issues, generated timestamp and scope notice. Do not include originals, full brief, source quotes, internal decision notes, private paths, raw model prompts or credentials. Never automatically summarize private review commentary into client text. HTML is escaped, contains no scripts/external fonts/resources and prints through the browser; server response downloads HTML rather than rendering untrusted original content inline.

A new export after changes creates a new ID; previous exports never morph. HTML/Markdown/client summaries must not omit gaps to create a misleading all-clear. Client JSON includes narrow reproducibility identifiers/hashes and check-version information, not private model inputs or full source excerpts. Even this safe projection contains client/project information; the user controls sharing.

## 9. Failure and UI obligations

| Code/outcome | User action | Data promise |
|---|---|---|
| `model_unavailable` / timeout | Start/configure supported local model or explicitly continue manually | No fake model output or silently swapped category |
| `invalid_model_evidence` | Inspect rejected quote/proposal, correct manually or retry explicitly | Unsupported claims cannot become confirmed sources |
| `context_limit` / partial coverage | Narrow selected requirements/files or review remaining rows manually | Coverage remains explicit; never implies complete scan |
| `parse_timeout` / `parser_memory_limit` | Use smaller/native text file or manual review | Originals/earlier decisions retained; file blocked |
| `revision_conflict` | Refresh then review/save against current snapshot | Older tab never overwrites changed packet |
| `superseded` | Start a new run on current inputs if necessary | Late old output cannot attach to new packet |
| `interrupted` | Explicit retry after restart | Saved reviewed work survives |
| `storage_limit` | Delete/export a project or remove extra data | No partial accepted packet or silent deletion |
| Export has unresolved items | Resolve or explicitly export a draft with visible gaps | Never becomes certified completion |

## 10. Contract acceptance checklist

Before feature implementation, approve one canonical OpenAPI schema and domain module; test source span round-trips across Python/TS, canonical digest stability, same-name upload handling, all cap boundaries and the race between export and mutation. Verify no read/write path bypasses session/Host/Origin policy. Validate schema against each proposed model and parser. See the QA document for the full threat/evidence matrix. These contracts must be reviewed against working code and revised if a measured constraint changes; a detailed plan is not proof that edge cases have been solved.
