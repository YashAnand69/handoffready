# V4: fresh, agent-authored synthetic evaluation

This is a small synthetic evaluation authored by a Codex agent. It is not a customer study, independently authored human test set, production accuracy estimate, or evidence that handoffs are complete. All briefs and original PNG, JPEG, TXT, Markdown, native-text PDF, and SVG files were created for this evaluation and dedicated under CC0. No private client material was used.

## Before predictions

`scripts/evaluate_model_v4.py --prepare-only` creates ten briefs, 27 bounded original files, extraction answer keys, fixed approved association requirements, and a fixture manifest. It invokes the repository parser worker on actual bytes; it does not import the model, read existing model prompts or old evaluation cases, or run inference. The preparation has passed inspection for all 27 files and Pydantic validation for all 21 fixed approved requirements. See `docs/model-evaluation-v4-preflight.json` for this preparation evidence.

The manifest is `fixtures/evaluation-v4/fixture-freeze.json`. The dataset SHA-256 is `2718aab4fe4a75398bd499c64e53ea568a04d8f71d848ddad0e95b3229e2d910`; the scoring definition SHA-256 is `152a208cac161c7501ac0cc99791212dfd16f747f531e91903e79160799ab062`. These hashes were recorded before model predictions. The manifest binds the original file bytes, briefs, keys and license; source evidence binds exact Unicode code-point ranges in each original brief.

The author did not read earlier model prompts or old evaluation cases when creating the fixture and keys. During the later adapter work, after the fixture freeze but before candidate freeze, a broad symbol search accidentally displayed current prompt lines. This disclosure is retained; no fixture or key changed and no inference occurred. Parent review and candidate freeze must precede any real inference. Final evaluator and adapter hashes are recorded separately when the candidate is frozen. A changed dataset, scoring definition, evaluator, inspector or adapter blocks a run.

Before inference, the scorer was revised for source occurrence validation and fair classification/attribute accounting. The original fixture freeze and original preflight remain immutable. `fixtures/evaluation-v4/scoring-freeze-v4.1.json` binds the revised definition to the unchanged dataset and original preflight. Candidate freeze binds this effective scoring hash as well as the original scoring hash. This is a disclosed pre-inference revision, not a modification based on predictions.

A subsequent pre-inference review found that the adapter incorrectly counted raw candidates explicitly labeled `unrelated` as positive pairs. Version 4.2 corrects this: only raw `supports` candidates enter positive-pair scoring. All original raw candidates remain captured and unrelated-candidate counts have a separate candidate denominator. Post-guard accepted candidates, whose relation was removed by the model guard, remain positive. `scoring-freeze-v4.2.json` binds the correction and the preserved v4.1 freeze; original records are retained. The current candidate freeze must bind the v4.2 effective scoring hash. The regression script `scripts/test_evaluate_v4_adapter.py` uses synthetic output only and tests mixed relations, explicit no-support, missed true support, and post-guard accepted candidates.

## Coverage and keys

| Packet | Included challenge |
| --- | --- |
| Cedar Cart | Required PNG dimensions and transparency, SVG, optional Markdown, JPEG decoy |
| Lantern market | JPEG versus PNG decoy, paraphrased text placement guide |
| Pebble studio | SVG, two-page native PDF guide, draft text decoy |
| Reed workshop | PNG dimensions, live audio behavior without file proof |
| Rowan newsletter | Multiple distinct caption files, exact copy, optional portrait absent |
| Vale sponsorship | Missing PDF delivery, plausible TXT with matching filename, PNG badge |
| Juniper bakery | Repeated scheduling boilerplate, SVG, paraphrased Markdown notes |
| Moss tutoring | Inspected text injection, genuine guide content, JPEG versus PNG |
| Fern ceramics | Two distinct JPEG supports, missing PDF guide, Markdown outline decoy |
| Willow event | JPEG, paraphrased native PDF accessibility guide, live keyboard behavior |

There are 23 extraction key items: 21 mandatory and two optional. Association uses only the 21 fixed approved mandatory requirements, with 19 keyed supporting file pairs and four requirements with no file support. Requirements consisting only of a live manual test have no supporting file. A guide can be associated by semantic relevance while its manual quality check still requires human review. Neither association nor inspection certifies semantic quality or live behavior.

## Separate tasks and comparisons

Extraction is assessed against brief source occurrences independently of file association. Coverage requires validated exact source evidence overlapping at least 80% of one keyed atomic obligation, correct required/optional classification, and the requested format union. A manual-only live obligation also requires a manual check. Matching is one-to-one; duplicate predictions cannot increase coverage. Repeated text is valid with its exact occurrence span and does not require globally unique wording. Optional work classified as required is a classification error; mandatory work classified as optional receives no mandatory coverage. Omitted mandatory work is counted as missed, never a correct abstention.

Attribute scoring removes null fields, sorts type arrays and ignores manual instruction wording while retaining the manual check kind. It reports correct, missing and extra normalized checks against all keyed checks, plus exact check-set matches with a separate requirement denominator. Thus a useful paraphrase of manual review does not fail for wording alone. Literal-text checks remain in the original key: the current generated-check schema does not emit these human-added-only checks, so literal needle misses should be read as a documented schema limitation, separately from format coverage or semantic quality. Mandatory and optional coverage, unmatched proposals, classification errors and valid source quotations have explicit denominators. Optional/excluded classified outputs are retained for extraction scoring through diagnostics and never enter fixed approved association inputs.

Association always receives the keyed approved requirements, even if extraction misses or invents requirements. It compares:

1. A locked filename token-overlap baseline with type eligibility and no content text.
2. The same locked baseline with filename plus inspected text.
3. One captured structured Gemma prediction before guards.
4. That same captured prediction after repository guards.

The baseline lowercases alphanumeric tokens, removes the frozen stop words, divides overlapping query tokens by all title/quote query tokens, and keeps every typed eligible file scoring at least 0.20. Manual-only live checks abstain. This is a deliberately simple filename ablation with a type filter, not an assertion that filenames establish proof. The threshold and stop words were fixed before predictions; there is no fitting to model outcomes.

For each case and in aggregate, association reports correct, wrong and missed support pairs, predicted and keyed pair denominators, completely correct supported requirements, and correct/wrong/failed no-support decisions with their denominator. Captured predictions allow before/after guards to be compared without a second inference. Guard changes should be read as changes to the same initial output, not a second model's performance.

## Frozen candidate contract and run

The candidate metadata must include `candidate_revision`, `model_id`, `model_weights_sha256`, `prompt_sha256`, `generation_parameters`, `adapter`, `adapter_sha256`, and a `candidate_source_sha256` mapping including `backend/handoffready/model.py`. Metadata is supplied by the parent after freezing its candidate. `--prepare-only --candidate-metadata PATH` writes an immutable candidate freeze recording that metadata and the dataset, scoring, evaluator and inspector hashes. It verifies the candidate source bytes both at freeze and at run, and never silently overwrites an existing freeze.

The adapter supplies `extract` and `associate` callables with keyword arguments `brief`, `source_id`, `files`, `requirements`, `capture_predictions=True`. Each stage must issue exactly one captured structured call and return `raw_predictions`, `guarded_predictions`, `capture`, and `failure`. Guarded predictions are produced from the captured output without another model call. The adapter must classify model timeout, token/truncation, parsing, structured-schema and runtime errors as failures. Valid structured empty predictions are the only possible successful abstention. This contract intentionally blocks running until a reviewed adapter and candidate metadata are available.

Run explicitly with `scripts/evaluate_model_v4.py --run --report docs/model-evaluation-v4-first.json`. The first report is written with exclusive creation and cannot be overwritten. Later runs require a different explicit path and must retain the original first report and captured calls. No prompt, key, model, threshold or fixtures should be tuned using first-run outcomes and presented as the unchanged first result.

The adapter is `scripts/evaluate_v4_adapter.py`. It calls existing `model.extract`/`model.match` with `capture_predictions=True`. Pre-guard occurrence IDs are converted to exact quotes/spans through the repository source catalog; post-guard source bindings are validated through the same evidence validator. Capturing transient wrappers copy the one structured result and completion output before guards can throw, restore the original functions in `finally`, and do not alter prompts, source or model decisions. Captures omit prompts, headers, endpoints, credential configuration and local weight paths.

Association before guards scores candidates marked `supports`; after guards scores retained accepted candidates. Raw candidates marked `unrelated` are explicit negative judgments, retained in the capture and counted separately, and never positive pairs. This makes guard filtering visible without treating a correct negative judgment as a false positive. A valid source quote establishes a literal occurrence, not semantic support. Textual candidate quote validity covers all retained diagnostic candidates and has its own numerator/denominator; raster/vector metadata candidates have no text-quote denominator.

Reports retain actual inspector results, raw and guarded predictions, captures, errors, case scores, aggregate numerator/denominator totals and elapsed call latency. Exceptions and model failures score zero correct abstentions and all expected supports as missed. Latency denominators include failed attempts. A parser failure is an evaluation preparation failure, not proof that a requirement has no file support. Exclusive per-run start and per-stage capture records under `fixtures/evaluation-v4/runs/` prevent silently restarting an interrupted first run under the same report name. The final first report still uses exclusive creation and cannot be overwritten.

## Limits

Ten agent-authored synthetic packets do not estimate population accuracy. The same agent authors the data and scorer, and exact source/check scoring can penalize alternate requirement granularities. This evaluation covers bounded supported formats and native PDF text only; it tests neither OCR nor image meaning, live browser functionality, subjective quality, privacy guarantees or customer outcomes. It does not promise 100% accuracy. Any headline must include the synthetic label, numerator and denominator, failure counts and before/after guard distinction.
