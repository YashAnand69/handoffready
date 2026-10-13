# Predeclared model evaluation — synthetic holdout v1

Frozen **13 October 2026, 12:56 UTC / 18:26 IST**, before model readiness or inference on these cases. Author: independent evaluation agent. The model implementation agent has been asked not to inspect or tune against this set before the first results are recorded. The team can inspect source for software correctness; this is a small developer-authored holdout, not independent external validation.

Canonical dataset SHA-256:

`1ed7abc21723bc634558902b21da6b283ba653a8396277914a13ad516c1bc9f4`

The complete original CC0 dataset, approved synthetic matching requirements, source quotations, expected associations and controls are frozen in `scripts/evaluate_model.py`. Canonical serialization is UTF-8 JSON with sorted keys, no extra whitespace and Unicode preserved. `--prepare-only` validates exact unique quotes, IDs, expected membership and the eight-requirement count without contacting a model.

## Questions

1. Does actual open-model inference produce source-grounded checklist proposals for new briefs?
2. Can it associate differently named documentation through meaning rather than filenames alone?
3. Does it avoid unrelated, missing, blocked and instruction-injection evidence?
4. Does it retain both potentially relevant sources when instructions conflict, without establishing either as correct?
5. What time, schema/context failures and raw evidence are observed on this machine?

This evaluation does **not** test contractual satisfaction, aesthetic quality, live websites, broad customer accuracy, real customer usefulness or willingness to pay.

## Frozen cases

| Case | Mandatory deliverables | Expected evidence | Control |
|---|---|---|---|
| Site maintenance | Hero-image guide; footer-phone guide; transparent PNG logo | Renamed `section-01.txt` describes changing the first full-width picture; `section-02.md` describes the site-wide bottom bar’s calling number; logo has no source | Missing logo, irrelevant invoice, optional calendar and excluded brochures |
| Conflicting maintenance guides | Mailbox-routing guide; page-recovery guide; launch analytics report | Both `notes-a.txt` and `notes-b.md` describe MX routing with contradictory destinations; `notes-c.txt` describes Trash/Restore | Both routing sources remain potentially relevant; missing analytics; inspected prompt-injection text must not match |
| Storefront content | Checkout-message guide; accessible image-description guide | Renamed `record-01.md` describes post-payment text; `record-02.txt` describes alternative text and assistive speech | Inspected prompt injection; misleadingly named blocked guide |

Three briefs, eight matching requirements, eleven source records. Source text and labels are entirely synthetic. The matching phase uses predeclared human-approved requirements independently of extraction output, so extraction failure cannot silently erase a matching failure. One `extract` and one `match` call per case are planned, sequentially, after the model agent’s separate Stage 0 development probes finish. No inference contention is intended.

The two MX sources are deliberately contradictory. The expected candidate set includes both because both are relevant evidence. This probe measures whether both remain visible; it does not assert that matching alone can identify ambiguity or select the correct provider. Raw explanations must be inspected for unsupported certainty.

## Comparators

Two frozen, model-free comparators run over the exact same cases:

- Filename token overlap.
- Filename plus full extracted-text token overlap.

Each selects an inspected source when at least one nontrivial title token overlaps. Tokens are lowercase ASCII words of at least three characters after the fixed stop list in the script. No learned weights, synonym additions or thresholds will be adjusted after seeing results. These are simple reproducible comparators, not representative best-in-class retrieval systems.

## Metrics and evidence

Matching records candidate pairs, exact requirement-row sets, pair precision/recall, missing-requirement abstention, unrelated/injected/blocked files selected and ambiguous-source-set retention. A failed adapter call remains a failed case with its error, not a made-up empty successful result. Metric denominators include only completed matching outputs; reports must disclose failures alongside successful cases.

Extraction records raw requirements, exact unique source quotes, suggestion count, mandatory-clause overlap coverage and optional/excluded-clause overlap. Clause overlap is a lightweight coverage probe: it cannot establish that the inferred check parameters or interpretation are right. Human review must inspect raw output before drawing conclusions.

Every call records wall time and adapter provenance, including model/artifact/runtime receipts, prompt revision, input/output digests and text-only status. The first result file is `docs/model-evaluation-heldout-v1.json`; the runner refuses to overwrite it. Partial progress is saved after each case. Interrupted execution must be disclosed and later output assigned a distinct name.

## Execution and interpretation

Run:

```sh
.venv/bin/python scripts/evaluate_model.py --prepare-only
.venv/bin/python scripts/evaluate_model.py
```

The real authenticated local model must be available. There is no rule-based or canned success fallback. A tokenizer/context/output-schema failure is a measured failure. The fixed input/output/time limits are unchanged for this run.

After recording the untouched first run, fixes may use this dataset as development evidence, but subsequent tuned reruns must lose the held-out label. New held-out claims require new cases frozen before further tuning. Do not report a broad accuracy percentage from eight developer-authored requirements or portray synthetic examples as a freelancer trial.

**First real run:** recorded 13 October 2026 at 13:24 UTC in `docs/model-evaluation-heldout-v1.json`. All six calls failed safely: three extraction calls returned `model_schema`, and three matching calls returned `model_evidence` because exact source quotes were omitted. No association accuracy score can be inferred from failed calls. The original result is preserved unchanged. This dataset must be treated as development evidence after these failures were inspected; any improved held-out claim requires a newly frozen dataset. No customer outcome is claimed.
