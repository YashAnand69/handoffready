# Final correctness review

Reviewed on 2026-10-13 and independently rechecked after integration on 2026-10-14. This is a source and local regression review, not a claim of a perfect security audit, general model accuracy, customer validation or a contest result.

## Scope and method

Reviewed `AGENTS.md`, the README, all backend modules, launcher and installer, current backend tests, and the client projection/review interfaces. Focused on source identity, human review invalidation, race ordering, restart recovery, request and parser budgets, Host/Origin/token checks, mixed-format checks and immutable client exports.

All reproductions used temporary local directories. Installer tests substitute explicitly synthetic artifacts without executing them, downloading weights or claiming inference. No private live user data or model keys were inspected, and the existing app/model processes were not stopped.

## Concrete defects and fixes

### P1: documented fresh model setup could not launch

The default `prepare_model.py` path activated an installation receipt but created the model server credential only with `--start`. The documented setup instructs users to run the installer, then `start.py --with-model`; that launcher requires the credential and otherwise exits. Existing machines already holding a key hid the clean-install defect.

Fixed by creating the credential with mode `0600` before activating a successful installation receipt, regardless of whether the installer also starts a server. An isolated installation test exercises the default path, verifies permissions and confirms the launcher accepts the resulting synthetic installation. It never launches the synthetic server.

### P2: missing/corrupt originals remained passing delivery evidence after restart

The database retained inspected text/metadata and confirmed human decisions when registered original bytes disappeared or changed. Image preview already rejected changed bytes, but restored projects and exports still trusted stored inspection records. A presence check could remain `pass`, and a new snapshot could say `reviewed` despite the original being unavailable.

Fixed startup recovery by checking each registered original as a regular, non-symlink file, checking its recorded bounded size, and comparing a streaming SHA-256 digest. Missing or changed originals become blocked; extracted text and metadata are cleared; current reviews become stale. Existing proposals and original confirmed decisions are archived before invalidation. The expected original SHA remains provenance and is never overwritten with a digest of corrupt content. Restoring bytes manually does not silently approve an inspection again; explicit replacement is required.

The same reconciliation is exposed as `Store.reconcile_originals(project_id)` and is integrated into authenticated API middleware before project handlers. Token and write-Origin checks run first; permitted project requests then reconcile originals before project/evidence reads, decisions, model jobs and new exports. A detected change advances the revision, so a previously prepared write conflicts and requires a refresh. Immutable exports created earlier remain historical snapshots. The independent integrated test run covers runtime original deletion followed by a stale export request, refreshed blocked/stale evidence and a preview with gaps.

Regression tests cover missing originals, same-size tampering after restart, healthy no-op reconciliation, runtime damage, bounded history preservation, expected SHA preservation and repeated checks without repeated archival.

### Minor malformed revision robustness

The revision parser's former `isdigit()` check accepted some Unicode characters that `int()` rejects; exceptionally long decimal headers also exceed Python's integer conversion bound. Fixed by requiring 1–20 ASCII decimal digits before conversion. Regression cases cover a Unicode digit, a 5,000-digit header and a negative revision; all return validation errors. This was a request error handling defect, not evidence that revisions could be bypassed.

### Unchanged saves now preserve approvals

Saving an identical normalized brief with the same label or an identical validated checklist is now a no-op. Current approval, decisions, input hash and revision remain stable. An actual source/checklist change still invalidates review. This avoids making completed human review stale solely because the user saved an unchanged form; the integrated regression confirms both behaviors.

## Verified invariants

- Private API reads require the random session token; writes additionally require a permitted local Origin. Host checking is performed before API routing. Browser CORS does not expose bootstrap tokens to arbitrary web origins.
- Validation errors omit submitted private field values. Request streaming has a cumulative byte budget, not just a Content-Length check.
- Upload bytes stage before an atomic revision-checked registration. Failed batches remove staged originals; registration removal commits before original-byte deletion. Startup removes unregistered orphan files.
- A changed brief, baseline or packet invalidates current mapping reviews. Late inference is discarded when its captured input snapshot is no longer current. Cancelled/deleted projects cannot be resurrected by a late job result. Restart interrupts queued/running jobs and does not silently rerun them.
- Source quotations are exact, unique and bounded. Source offsets and source hashes are reconstructed from current text rather than accepted from clients. Quotes establish provenance, not semantic correctness.
- Format checks apply to their applicable inspected assets in mixed packets. PNG alpha checks do not incorrectly require SVG/text files to have PNG alpha metadata; PDF page checks do not require accompanying Markdown to be a PDF. Human satisfaction does not erase technical failures.
- Client projections omit raw brief fields, model quotations/reasons, private decision notes and audit histories. Approved titles, check instructions and deliberate client usage notes are intentionally shared. HTML output escapes user text and uses a restrictive download policy. Existing snapshots remain immutable.
- Parser concurrency, execution time, decoded-content sizes and output text are bounded. PDF decompression limits are checked after decompression and process memory is sampled; this is not a hardened OS sandbox or an instantaneous memory ceiling.

## Remaining boundaries

Model classification and matching can be wrong, including semantic prompt-injection mistakes. Current source/format guards and explicit human review limit their effect; the sampled model evidence does not prove universal robustness. Manual checks record a human assessment rather than certify delivery quality, website behavior or client acceptance.

The service is designed for one backend process and local browser use. A malicious process running with the same user's permissions can read that user's files or interfere with the service; loopback and session controls do not provide isolation against that actor. Storage is not encrypted by the application. Concurrent upload staging is bounded per request and packet, but the active registered-byte quota is not a global temporary-disk concurrency quota.

Each permitted project request rehashes its bounded registered packet, including job polling. This favors current evidence integrity and may add disk work for large packets. Reconciliation is not a filesystem lock against other programs changing bytes immediately afterward; the same-user interference boundary still applies.

The broad Ruff 0.17.0 scan reports 57 style/maintainability findings across the existing code and tests, including import order, broad exception handlers, and script executable flags. The focused correctness rule set passes. These lint findings are not a demonstrated authentication or evidence-integrity bypass; an unrestricted clean-lint claim would be inaccurate.

The reviewed state has no demonstrated remote data leak or bypass of the normal current-review workflow in these checks. That statement is limited to the inspected code and tests; it does not mean the software has no possible flaws.

## Validation receipts

- Before fixes: both initial isolated reproductions failed their intended correctness assertions (recorded as strict expected failures during diagnosis).
- After fixes: four independent final-review regression tests pass.
- Independent final integrated backend run: **137 passed**, with one Starlette/httpx test-client dependency deprecation warning.
- Cached local Ruff 0.17.0 correctness rules (`E9,F63,F7,F82`) over backend, scripts and tests: **passed**. The broad scan returned the findings described above; no package was downloaded for these checks.

No expensive model download, real inference benchmark, publication or customer trial was performed as part of this review.
