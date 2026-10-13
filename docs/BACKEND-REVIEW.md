# Integrated backend review

Review covers the local API, private SQLite store, deterministic inspections, model adapter boundaries and safe exports. This is an engineering review, not a security certification or claim of flawless operation.

## Corrections from independent review

- **Parser lifetime:** stdout uses a temporary file, preventing large Unicode text from filling a pipe and deadlocking. Timeout/RSS failures kill and reap owned children. Parser-queue waiting also shares the absolute batch deadline.
- **Model lifetime:** queued/running requests retain immutable snapshots. Queue waiting plus adapter network calls share an absolute 120-second deadline; the adapter uses a whole-exchange asynchronous timeout so a slow drip response cannot repeatedly reset a read timeout. Late cancelled/superseded output cannot publish.
- **Stale decisions:** current technical checks require both confirmed review state and the current input hash. Edited filenames, source, baseline or original bytes invalidate prior decisions. A no-op late cancelled response no longer increments project revision.
- **Upload commits:** pre-commit failures remove staged bytes; response/cleanup failure after transactional registration cannot delete newly committed originals. Deletion commits record removal before purging original bytes, leaving recoverable orphan cleanup rather than broken database pointers after interruption.
- **Private access:** exact Host checks apply to bootstrap and every route. All sensitive reads require the current in-memory server token; mutations additionally require an exact allowed Origin. Malformed/non-ASCII tokens reject safely. JSON has a separate 256 KiB streaming fence; multipart file/count/byte budgets remain authoritative.
- **Evidence:** exact unique source quotations resolve to server-derived Unicode code-point spans; client-provided offsets are ignored. Text-file proposals require exact unique quotations. Metadata-only associations explicitly remain nonvisual. Model runs never automatically create human dispositions.
- **Exports:** preview and all three downloadable formats use the same server projection. Private brief/source text, evidence quotations, model reasoning and internal decision notes are omitted. Literal check needles are not emitted. Expected/actual safe numeric evidence remains visible. Stale selected mappings are excluded, and acknowledged gaps remain explicit.
- **Visual review:** authenticated previews permit only inspected PNG/JPEG bytes with size/hash revalidation. SVG/PDF/text/blocked files cannot render inline. The UI receives authenticated blobs, with only image blob URLs allowed by the page policy.
- **SVG:** external stylesheet processing instructions now block before XML parsing. Raw SVG has never been embedded/rendered, and the parser does not fetch resources.
- **Audit records:** private history retains the last 20 baseline/source snapshots, 20 proposal batches and 200 decisions. Authenticated history access is distinct from the ordinary envelope and from client exports. Inactive original-byte restore is not provided.

## Verification approach

`tests/test_api.py` uses explicitly injected test models for deterministic workflow/race tests. Parser tests use real decoders. Adapter tests use explicitly stubbed protocol responses to challenge schema, source, endpoint and deadline boundaries. These tests do not establish real model semantic quality.

`scripts/verify_workflow.py` starts a real isolated loopback service and uses actual HTTP requests plus the actual bounded subprocess parser. It checks an opaque PNG failure, reviewed draft export/private-sentinel exclusion, corrected replacement invalidation, reconfirmed narrow passes, immutable old snapshots and persistence after service restart. `--with-model` adds actual configured model jobs with no injection; failed/unavailable inference is reported separately. All approvals are scripted fixture actions, not evidence of a customer trial.

`scripts/start.py` provides repeatable local startup without automatic downloads or installation. It can optionally start an already installed verified model, never replaces an occupied unverified service, and stops only processes it owns.

The original V5 API receipt in `workflow-verification-model.json` preserves a successful extraction and a genuinely rejected PNG match. Its original top-level `state=passed` denoted the seven-step manual workflow; the model sub-record is partial and the failed run remains explicit. The verification script was corrected so new `--with-model` receipts and its command exit report partial/failed/unavailable inference as an overall non-pass. Subsequent prompt/version runs are saved separately and do not erase the initial failure.

The V7 isolated API run in `workflow-verification-model-v7.json` completed both actual extraction and actual PNG association jobs, alongside the seven manual/parser/persistence checks. Generation provenance records 1.334 seconds for extraction and 1.825 seconds for matching on this machine. These are single warm synthetic development measurements, not a latency guarantee, held-out quality score or customer result. PNG association remains explicitly nonvisual and unapproved by the model. The separate fresh model evaluation still exposes a semantic false association, so successful API publication does not establish model accuracy.

Final integrated Python verification at this review point: 119 tests passed (41 API/workflow cases, 40 file-inspection cases, 38 model-boundary cases). The current Starlette TestClient reports a deprecation warning about its httpx integration; no test failed. Parser queue/execution limits, full 76 KiB Unicode worker output, source-span recomputation and private proposal archival across upload/replacement/rename/removal are covered.

## Remaining release limitations

Synchronous inspection has no persisted progress/cancellation job. Original version backup and restoration are outside scope. Durable idempotency replay is not implemented. A single process is required. The application does not encrypt stored data or promise forensic erasure. Model semantic quality and abstention need their own measured evidence and human review. Actual freelancer usefulness remains untested until a permitted customer trial.
