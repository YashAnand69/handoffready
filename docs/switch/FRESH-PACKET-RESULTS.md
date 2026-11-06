# First fresh synthetic packet run

6 November 2026 (Asia/Kolkata). The first execution passed **69 of 69 declared assertions across all six families**. This is an assistant-authored synthetic workflow evaluation against a frozen backend copy. It is not independently held-out validation, model-accuracy evidence, observed human review, a live Switch/provider run, or a genuine trial.

Inputs, authored expected facts, operation keys and exact source fingerprints were frozen at **2026-11-05 21:24:52 UTC**, before the first execution at **21:24:56–21:24:58 UTC**. These timestamps establish ordering; they are not usability or productivity measurements. No prior workflow run of these fixtures was used to adjust expectations. The first-run directory is preserved; there were no unexpected assertion failures or execution errors in this run.

| Family | Actual first-run observations | Declared assertions |
|---|---|---:|
| Complete assets | Real bounded workers decoded a 4×4 PNG and UTF-8 guide. Four narrow checks passed. Scripted synthetic local review produced a reviewed record. | 10/10 |
| Duplicate/wrong size | Two filenames had one unique PNG checksum; both decoded to 8×4. Distinct-byte count and required 4×4 dimensions failed. A scripted “satisfied” disposition retained both technical failures. Unacknowledged export was refused; acknowledged record remained draft. | 15/15 |
| Irrelevant same-name guide | The file called `guide.txt` parsed as text, but lacked the explicit release marker. Presence passed; exact literal check failed. The failed fact remained visible after scripted “satisfied” disposition; only an acknowledged draft was created. | 11/11 |
| Ambiguous/manual | The manual check remained `unknown` and synthetic disposition `unresolved`. A contextual question and unverified reply containing “approved” left the project held. Neither question nor reply prose appeared in agent status. New export was refused. | 9/9 |
| Malformed/unsupported | Both parser probes were blocked with empty metadata/text. Complete-packet commit returned `delivery_inspection_failed`, committed zero files and preserved pending intake. Export returned `delivery_hold`. | 9/9 |
| Corrected packet | Initial guide produced a reviewed synthetic record. Same-name corrected bytes changed input identity and staled the old review. Every original JSON/Markdown/HTML download remained byte-identical. Fresh scripted review produced a second reviewed record. | 15/15 |

Expected failures in the table are successful safety observations, not missed test cases. No unexpected false flags or missed declared technical facts were observed among these assertions. That statement applies only to the authored fixture expectations; there was no independent answer set or measurement of semantic/model false positives or false negatives. The manual `unknown` is a deliberate abstention. Malformed-input refusal is not a completed intake workflow. No model schema/time errors were evaluated because no model request was made.

The run exercised the actual local API, Store/SQLite, attachment staging, packet preview/confirmation, idempotent receipt replay, bounded parser subprocesses, deterministic checks, synthetic local dispositions and record downloads. Candidate mappings and checklist requirements were authored directly. They are not model extraction/association results. Application fields named `human_added` and `human_disposition` identify the local API behavior being exercised; the fixture notes explicitly disclose assistant authorship.

## Frozen identity and artifacts

The exact fingerprints and per-input checksums are in [FRESH-PACKET-PROVENANCE.json](FRESH-PACKET-PROVENANCE.json). The full input/answer manifest, copied backend/runner, isolated data stores, per-family first results, API path/status traces without credentials, downloaded records and aggregate result remain outside the repository:

```text
/Users/yashanand/Documents/Codex/2026-11-06/evaluation-artifacts/handoffready-fresh-packets-20261106/
  frozen/manifest.json
  frozen/manifest.sha256
  frozen/candidate/
  frozen/inputs/
  runs/run-01/results.json
  runs/run-01/command-observation.json
  runs/run-01/<family>-result.json
  runs/run-01/<family>/data/
```

- Frozen manifest SHA-256: `80af92141e04bc2d1bd0911faa01d6d3289fe2af18806a5167aca2a8d913640a`.
- Exact source-map fingerprint: `aebf0cdf613ee5dd24f9c3123ad1056d5816aa6b637b174914bbd5b6eea5d453` (17 backend files plus runner).
- First aggregate result SHA-256: `c07250d2993efb7f9806653046f99aa048bac38aa8fdd4482738abdf36d76fd3`.
- Base HEAD at freeze: `a0406304cafa5842fd9c9c991fe79fd7f29dcf4a`. This is a base reference; the tested working candidate is identified by the frozen source map, not claimed as this commit.
- Final corrected-packet JSON record SHA-256: `21e158612cd69b2229d1f2f19bf4d500383cf632a60648828c54e8bee9210b06`.

The copied backend includes the share-context-epoch repair present at freeze. This suite does not dispatch or verify a share, and does not replace share-specific regression evidence.

## Commands and environment

All three commands completed with exit code 0:

```text
.venv/bin/python -m py_compile scripts/evaluate_switch_workflow.py
.venv/bin/python scripts/evaluate_switch_workflow.py freeze /Users/yashanand/Documents/Codex/2026-11-06/evaluation-artifacts/handoffready-fresh-packets-20261106
.venv/bin/python scripts/evaluate_switch_workflow.py run /Users/yashanand/Documents/Codex/2026-11-06/evaluation-artifacts/handoffready-fresh-packets-20261106
```

Python 3.12.13; FastAPI 0.143.0; Starlette 1.8.0; HTTPX 0.28.1; Pydantic 2.14.1; Pillow 12.3.0; pypdf 6.20.1; psutil 7.2.2. TestClient emitted a deprecation warning recommending HTTPX2; it did not fail this execution. No dependency was changed for the evaluation.

## What remains unverified

Model extraction, model evidence association, real provider/Switch transport, contextual human correction and fresh local human review, external delivery, independent human judgments, genuine participant usability and timing remain outside this run. The tiny fixtures do not establish parser robustness for arbitrary files, document quality, aesthetic compliance or business usefulness. Inputs and expected facts were authored together and visible to the assistant. All execution data was isolated; live data, credentials and synced project sources were not accessed. This result does not declare a full stage or release complete.
