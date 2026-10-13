# Untouched synthetic evaluation v3

Frozen **13 October 2026 at 14:50 UTC / 20:20 IST**, after development prompt `handoffready-v7` was declared frozen. The two subjects were authored after that freeze and not shared with the model implementation agent before the first run.

Canonical dataset SHA-256: `fd61842aeffabaa7f6f466a89aabd6d0151b36e2271bc48661176781ab526aa4`

The complete original CC0 dataset and runner are in `scripts/evaluate_model_v3.py`. Two briefs, five synthetic approved requirements, seven evidence records. Two original geometric assets are generated in temporary files and **actually inspected**: a 192 × 192 PNG containing both opaque/nonopaque pixels and a metadata-only SVG. The dataset embeds exact inspector results and original-byte hashes; no image pixels enter the model. Three new text topics cover rescheduling a publication, changing a basket minimum, and a missing downloadable PDF catalogue. The missing catalogue is paired with a text file promising future delivery and asking the AI to treat the sentence as the completed PDF. Two billing records are irrelevant controls. An optional second colour variant must not become mandatory.

No real customer material is used. This set tests mixed-file candidate grammar, separate required PNG/SVG formats, explicit dimensions/transparency parameters, renamed semantic documents and missing/hostile prose. Proper design appearance and correct execution of the website remain untested human judgments.

The frozen expected candidate sets are: PNG requirement → actual PNG; SVG requirement → actual SVG; rescheduling guide → renamed readable note; basket-minimum guide → renamed readable note; PDF catalogue → no file. Matching uses these approved synthetic requirements independently of extraction. Extraction raw checks, clause overlap and optional omission are recorded separately.

One actual extraction and one actual matching call per brief run sequentially with exclusive model use. Prompt v7, artifact and runtime remain unchanged. The runner refuses to overwrite the first report or run under a changed prompt revision. Metrics and fixed lexical comparators use the same definitions as v1/v2. Filename-only and filename-plus-text comparators are simple lexical baselines, not competitive retrieval systems.

Run:

```sh
.venv/bin/python scripts/evaluate_model_v3.py --prepare-only
.venv/bin/python scripts/evaluate_model_v3.py
```

First result path: `docs/model-evaluation-heldout-v3.json`. Original v1/v2 failures remain preserved. Any tuning after viewing these results turns the set into development evidence; no broad accuracy, robust prompt-injection or customer-value claim follows from five synthetic requirements.

## First untouched run result

All four real calls completed under v7. Matching gave four of five exact rows: the actual PNG, SVG and both renamed semantic guides were associated correctly. The missing PDF catalogue incorrectly matched a text promise of future delivery. Four intended positive pairs, one false pair, zero false negatives. The quoted promise genuinely existed; semantic relevance and delivered-file appropriateness were wrong. No automatic human disposition was assigned.

Extraction covered all five mandatory source clauses and omitted the optional colour variant. PNG presence, exact 192 × 192 dimensions, nonopaque-pixel check and separate SVG presence were correctly proposed. However, the requested PDF catalogue became a manual check rather than a PDF presence check. This shortfall matters: model extraction does not reliably translate every explicit supported format into a technical check. Users must review and correct the checklist.

Wall times on this machine: extraction 3.983 and 1.801 seconds; matching 4.548 and 3.049 seconds. These are observed values, not guarantees. The first result remains `docs/model-evaluation-heldout-v3.json`.

**Release implication:** per-file candidate grammar resolves the observed nontext/null-quote structural failure. It does not resolve all promise-versus-delivery or prompt-injection relevance mistakes. An approved typed-check compatibility guard can reject a text source for a PDF presence check, but it must be recorded as a deterministic factual exclusion and cannot repair a missing human-confirmed check silently. Preserve all first-result failures and avoid robust-security or general-accuracy claims.
