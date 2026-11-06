# Fresh synthetic workflow protocol

6 November 2026. These cases are authored by the assistant implementing the runner. They are fresh synthetic regressions, not independently hidden validation, human judgments, model accuracy, customer evidence, or a live Switch trial. No model output is fabricated: model extraction and model evidence association are not run.

Before the first workflow execution, `scripts/evaluate_switch_workflow.py freeze` creates an external immutable input/answer manifest and copies the exact backend and runner source. The manifest records actual bytes, byte lengths, SHA-256 fingerprints, authored checklist/mapping/expected facts, operation keys, dependency versions and base Git HEAD. The working candidate is identified by source fingerprints, not represented as a clean candidate commit. The frozen runner imports the copied backend; bounded parser subprocesses also use that copy. Expected facts are authored and visible to the runner. Keeping their file outside the repository does not make these independently held-out cases.

Each run creates a new external data tree and keeps every earlier result. It does not overwrite a first failure. Per-family incremental results, API path/status traces without credentials, isolated databases, actual parser facts and downloaded record bytes remain in that tree. Frozen input/source fingerprints and dependency versions are checked before execution. Files under the project's synced `sources/` and live application data are never used.

| Family | Frozen inputs and authored expected facts |
|---|---|
| Complete assets | Decodable 4×4 PNG and a UTF-8 guide containing `RELEASE-NOTE-CEDAR`; presence, dimensions and exact text pass. A scripted synthetic local review can produce a reviewed local record. |
| Duplicate/wrong size | Two filenames contain the exact same 8×4 PNG bytes. Distinct-byte count of two and 4×4 dimensions fail. A synthetic “satisfied” action cannot erase technical failures; only an acknowledged draft record is expected. |
| Irrelevant same-name guide | The filename remains `guide.txt`, but its text is a tea recipe without the declared release marker. File presence passes; the explicit literal check fails. This tests the declared literal marker, not semantic relevance or model association accuracy. |
| Ambiguous manual scope | Text asks for “spacious” spacing without a measurable value. A manual check remains unknown and synthetic disposition unresolved. A question plus an unverified quoted “approved” reply cannot resolve the hold or authorize a record. |
| Malformed/unsupported | Truncated PNG-signature bytes and unsupported `.bin` bytes are blocked without partial metadata/text. Complete-packet confirmation fails atomically, commits no files, and pending intake blocks new exports. |
| Corrected packet | A valid guide is reviewed and exported, then same-name new bytes replace it. The input identity changes, old review becomes stale and old JSON/Markdown/HTML downloads remain byte-identical. Fresh scripted review produces a second record. |

All checklist additions, candidate mappings and local review decisions are scripted assistant-authored actions. The application's existing `human_added`/`human_disposition` field names describe the local API path being exercised; they do not establish a human authored or assessed these fixtures. No source extraction, independent correction judgment, transport delivery, share dispatch or genuine participant task is measured. There is no timing or productivity claim.

Commands (run from the repository using its existing local environment):

```text
.venv/bin/python -m py_compile scripts/evaluate_switch_workflow.py
.venv/bin/python scripts/evaluate_switch_workflow.py freeze /absolute/external/artifact-folder
.venv/bin/python scripts/evaluate_switch_workflow.py run /absolute/external/artifact-folder
```

Release limitations remain separate: passing this suite does not satisfy a real provider/Switch contextual review, genuine human trial, usability comparison, or Stage-wide completion gate.
