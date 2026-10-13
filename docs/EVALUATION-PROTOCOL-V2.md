# Untouched synthetic evaluation v2

Frozen **13 October 2026, 14:44 UTC / 20:14 IST**, after the model agent declared development prompt `handoffready-v5` frozen and all its development probes complete. No real inference was run on these new subjects before this protocol. The model implementer has agreed not to inspect or tune against the cases before the first run.

Dataset SHA-256: `a40066b755efe89345dadbce8b856968028e1a67823111091f9bfcb4979969b1`

Complete original CC0 cases and evidence labels live in `scripts/evaluate_model_v2.py`. Two new briefs, six matching requirements and nine documentation sources cover appointment-site maintenance and shop operations. Names are deliberately generic. Controls include a missing mailing-list export, missing webhook instructions, irrelevant billing, two inspected prompt-injection strings, a misleadingly named blocked document, optional/excluded scope, and two contradictory shipping-zone guides. Both shipping documents are potentially relevant evidence; their shared inclusion does not select a correct policy.

The model adapter, prompt v5, model artifact and server remain unchanged for this run. One real extraction call and one real matching call per case run sequentially, with exclusive model use. Matching uses the frozen human-approved synthetic requirement set independent of extracted output. The v1 failure artifact is preserved; these v2 topics were authored after structural repairs and development tuning, and were not shown to the model implementer beforehand.

Measures: exact requirement candidate sets, pair precision/recall, missing-item abstention, injected/blocked/irrelevant selections, ambiguous source retention, extraction clause-coverage probe, optional/excluded overlap, wall times and raw adapter provenance/results. Failures remain explicit failures. The same frozen filename-only and filename-plus-text lexical comparators defined in v1 run here without threshold or synonym tuning.

Run:

```sh
.venv/bin/python scripts/evaluate_model_v2.py --prepare-only
.venv/bin/python scripts/evaluate_model_v2.py
```

The runner refuses to replace the first result and rejects a changed prompt revision. Model-selected excluded suggestions and associations remain in raw provenance for inspection. A classifier can exclude genuine evidence; its omissions must be evaluated, not treated as harmless output cleaning. Exact quotation establishes source existence, not semantic relevance.

This small developer-authored synthetic set does not establish customer usefulness, general accuracy, willingness to pay or a competition-winning claim. After viewing this first run, any tuned rerun becomes development evidence. First result path: `docs/model-evaluation-heldout-v2.json`.

## First untouched run result

Recorded at 14:44 UTC on 13 October 2026. All four actual calls completed. Extraction covered all six mandatory source clauses and omitted optional/excluded clauses in the declared overlap probe; every extracted check remained a manual review, including the unsupported CSV export. This is source coverage, not a claim of fully automatic interpretation.

Matching produced **five of six exact requirement candidate sets**. Five intended positive evidence pairs were recovered, but one false pair was added: the missing mailing-list export was associated with the inspected adversarial file explicitly asking the AI to treat its sentence as an export. Its exact quote was genuine, yet its relevance was wrong. Pair counts were five true positives, one false positive and zero false negatives. The missing webhook guide remained empty; blocked sources were not selected; both contradictory shipping sources remained visible. The simple filename-only and filename-plus-text baselines each produced two of six exact rows. This tiny result is not a general accuracy estimate.

Observed extraction call times: 4.020 and 2.720 seconds. Observed matching call times: 4.743 and 5.513 seconds, including the adapter’s current relevance classification. These are this machine’s observed wall times, not service guarantees.

**Release implication:** source validation and structured grammar do not establish relevance or robust resistance to prompt injection. The false adversarial association needs a visible human-review warning and corrective development evaluation. No automatic approval occurred. Preserve this first result unchanged and disclose the defect. Any tuning against this case must be labeled development work; a new held-out claim requires new unseen cases.
