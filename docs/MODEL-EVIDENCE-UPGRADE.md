# Local model upgrade evidence: first synthetic V4 run

The frozen first run found 19 correct and two wrong positive file associations before guards. Reusing those same captured outputs after guards retained the 19 correct associations and removed the two wrong-format associations. Extraction covered 15 of 21 mandatory obligations under the frozen coverage definition; six proposals omitted required format checks. These are results from ten small, agent-authored synthetic packets, not customer validation or a general accuracy estimate.

This note audits the saved first report without additional inference, model tuning, fixture edits or replacement of raw outputs. Positive association pairs were independently recounted from candidate relations and file keys, rather than trusting aggregate totals. Exact extraction source spans, obligation/format classification and conditional check matches were independently recounted from saved predictions and original briefs. The recounted values agree with the report. The original reports and pre-inference corrections remain available.

## Frozen first-run identity

The authoritative report is [model-evaluation-v4-first.json](model-evaluation-v4-first.json), SHA-256 `141849f2659698e17eb820824464fe9332259342e2e4047a0ebe473da91de8e8`. The source revision is `f1ee8226934244ef81a117444098e59743110a0f` plus the source-digest-bound local upgrade recorded in the report. The report binds these identities:

| Artifact | SHA-256 |
| --- | --- |
| Original synthetic dataset | `2718aab4fe4a75398bd499c64e53ea568a04d8f71d848ddad0e95b3229e2d910` |
| Effective scoring V4.2 | `aaaff0ef921a7cffa919054c0ed44112a73ff86a9e4bc1df410afb9e5714b439` |
| Evaluator | `833c07b6cf85d8965ac04f9bf62322b00e03ff9b50602abb23dd74a2210c44cb` |
| Capture adapter | `c14b6197d40b9aa5a59ad8a8eaae8522714a7feadc570c8733bb9c7ceada9566` |
| Model integration source, `backend/handoffready/model.py` | `f0ea34b95590209df6e130872b60226c2794ce6a87d736ade1a25d32aba5239f` |
| Inspector source | `643be1430e7a28eb49ed308131115d10140444bb60bce07ad095a4f2a01d7191` |
| Model weights | `8e30dff3ac4c8434c49a7036fa15564bdbb6044e42bf04550bf1a096ad7e6a52` |
| Combined run freeze | `187bddb4e84aa332295b787906b78240e9805abecc905199d6d8bd9acccffb6c` |

The model is `handoffready-gemma4-e2b`, prompt version `handoffready-v11`, using runtime tag `b11583`, temperature 0 and seed 20261013. The isolated server used loopback port 18082 and the pinned original weight bytes. The recorded `prompt_sha256` is the entire production model adapter module hash, including prompts and generation configuration, not a prompts-only digest. The report's `prompt_hash_scope` says “entire adapter module”; this means `backend/handoffready/model.py`, whose exact source digest matches that entry, not the evaluation capture adapter. The capture adapter has its separate hash above.

After the evaluation freeze, the parent changed a delivery-record renderer label in `exports.py`. The final application's complete source mapping therefore differs from the first-report snapshot; the frozen first report remains the authoritative evaluated revision. The model module, evidence binding, association guards and weight identity remain unchanged. A presentation-label change must not be presented as an identical whole-source freeze or as a new model evaluation.

The [protocol](EVALUATION-PROTOCOL-V4.md) explains original fixture authorship, format bounds and the two disclosed pre-inference scorer revisions. V4.1 repaired extraction occurrence/classification accounting. V4.2 repaired counting `unrelated` raw candidates as positive associations. Both previous freezes and preflights were preserved; V4.2 and the corrected capture adapter were frozen before this first prediction. During adapter development, a symbol search displayed current prompt lines after the dataset/key freeze; that exposure is disclosed in the protocol. No first-run outcomes were used to tune this candidate or replace the original keys.

## Association against fixed approved requirements

Association receives 21 fixed, keyed approved requirements independently of extracted proposals. Seventeen have file support, comprising 19 required file pairs, and four have no file support. The files include missing deliveries, format decoys, an inspected injection-bearing document, paraphrased guides, multiple supports and live manual checks. All 27 original file bytes inspected successfully.

| Method | Correct positive pairs / predicted positives | Wrong pairs | Missed pairs / 19 keyed pairs | Pair precision | Pair recall | Completely correct supported requirements / 17 | Correct no-support / 4 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Locked filename-only baseline with type filter | 9/9 | 0 | 10/19 | 9/9 (100%) | 9/19 (47.4%) | 9/17 | 4/4 |
| Locked filename + inspected text baseline with type filter | 13/13 | 0 | 6/19 | 13/13 (100%) | 13/19 (68.4%) | 13/17 | 4/4 |
| Gemma captured output before guards | 19/21 | 2 | 0/19 | 19/21 (90.5%) | 19/19 (100%) | 15/17 | 4/4 |
| Same captured output after guards | 19/19 | 0 | 0/19 | 19/19 (100%) | 19/19 (100%) | 17/17 | 4/4 |

These fractions describe only this authored set. High precision from the lexical baselines accompanies lower recall; none of these percentages is an overall product accuracy rate. There were zero wrong no-support decisions and zero failed no-support calls in this run. Raw output contained 25 candidates: 21 explicit `supports` judgments and four explicit `unrelated` judgments. The four unrelated candidates were retained diagnostically and never counted as positive pairs. After guard filtering, 19 candidates remained. Valid exact source quotes were 12/12 text-bearing raw candidates and 8/8 retained text-bearing candidates; nontext metadata candidates have no quote denominator.

The two raw wrong pairs were PNG substitutes for explicit JPEG requirements in `02-market` and `08-tutor`. The deterministic inspected-format guard removed these substitutions. It did not generate replacement evidence, improve the model's semantic judgment, certify image appearance, or prove immunity to instructions embedded in documents. The selected file sets were corrected, but the original coverage text in those rows still mentions both image files; readers should rely on the actual retained candidates and recorded guard diagnostics rather than treat prose coverage as a certification. The inspected injection case had correct keyed associations on this packet, which is a narrow result and not a prompt-injection security guarantee.

## Extraction is a separate, weaker result

| Metric | First-run numerator / denominator |
| --- | --- |
| Valid exact source spans and quotes | 21/21 predicted requirements |
| Mandatory obligations meeting frozen source, classification and requested-format coverage | 15/21 keyed mandatory obligations (71.4%) |
| Mandatory obligations not meeting that coverage definition | 6/21 |
| Wrong required/optional classification | 0/21 predicted requirements |
| Explicit format or allowed-format-union failures | 6/21 predicted requirements |
| Optional items proposed/classified | 0/2 keyed optional items |
| Normalized keyed attribute checks credited | 18/37 keyed checks |
| Missing normalized attribute checks | 19/37 keyed checks |
| Extra normalized checks credited on covered proposals | 2 extras; 15 covered proposals evaluated |
| Exact normalized check sets | 11/23 keyed items, including two optional items |
| Unmatched predicted source obligations | 0/21 predictions |

All 21 mandatory source obligations had a grounded proposal; six did not receive coverage credit because their explicit requested formats were omitted or narrowed. They were the market TXT guide, studio PDF guide, newsletter TXT/Markdown caption count, newsletter TXT welcome copy, sponsor PDF report and bakery Markdown guide. Two PDF proposals supplied page checks but omitted explicit PDF presence. The caption proposal omitted the Markdown alternative and the requested count/distinctness attributes. This distinction matters: exact quotation does not establish a complete typed requirement.

The two optional items were not proposed. Their absence is reported separately and is not counted as a mandatory miss or an association failure. Guards did not improve extraction scores in this run. Human review must still correct missing formats and attributes before approving an extracted checklist; association's fixed keyed inputs bypassed those extraction errors deliberately, so perfect guarded association here does not describe an end-to-end automatically extracted workflow.

Attribute counts are conditional under the frozen scorer: a proposal failing obligation/format coverage receives no attribute credit, including otherwise correct page-count checks. The 18/37 count therefore is not an independent per-attribute correctness estimate. Scoring ignores manual instruction wording, removes null fields and sorts type lists, but retains check kinds and values. The original key contains human-added literal-text checks that the generated-check schema cannot emit; those limitations remain reported instead of changing keys after observing predictions. The one-to-one 80% source-span overlap and atomic keyed granularity can penalize a useful alternative split/merge. The strict results should be read with those limitations, not relabeled as semantic quality scores.

## Calls, latency and deadline mismatch

There were 20/20 successful actual calls: ten extraction and ten association. Each saved capture records exactly one structured generation and one completion response. Before/after results are from that same call, not two runs. No parse, schema, truncation, token-budget or timeout failures occurred in this first run; the failure policy remains zero abstention credit for failed calls.

| Stage | Successful calls / attempts | Total elapsed seconds | Mean / ten attempts | Maximum elapsed seconds |
| --- | --- | --- | --- | --- |
| Extraction | 10/10 | 25.202 | 2.520 | 3.254 |
| Association | 10/10 | 34.145 | 3.415 | 3.970 |

The evaluator adapter gives a call a 180-second deadline, while the application gives a queued job 120 seconds including queue time. This is a protocol difference, not an equivalence claim. Every measured call finished in less than four seconds, so no recorded success depended on the extra 60 seconds. This does not establish behavior under application queuing, heavy load, cold startup or slower hardware. Maximum recorded input/output tokens were 1,702/397, below configured 6,000/1,500 bounds. The elapsed measurements are local warm-runtime call observations, not service latency guarantees or a benchmark against another model.

## Preserved failures and separate workflow evidence

The original [model evidence](MODEL-EVIDENCE.md) and earlier reports remain unchanged. V1 had safe schema/source failures; fresh V2 wrongly associated instruction-bearing TXT with a missing CSV export; fresh V3 wrongly associated a future-promise TXT with a missing PDF catalogue. Later repairs on those same cases are development regressions, not fresh held-out evidence. V8/V9 requirement merging and missing-transparency observations also remain recorded. No Qwen comparison or customer study was performed.

[browser-demo-verification.json](browser-demo-verification.json) retains an actual V10 semantic error: a welcome-only guide was associated with contact-email update instructions. It also retains an assertion that duplicate launch candidates were distinct, while deterministic distinct-byte counting failed. A correct file type or a real quoted heading cannot catch every semantically irrelevant guide. The later actual V11 [upgrade-browser-workflow.json](upgrade-browser-workflow.json) preserves the same unresolved welcome-guide mistake in `recorded_semantic_errors`: the candidate quotes `# Client guide`, and its reason treats that heading and “Welcome to your new website.” as relevant to contact-email instructions. The receipt is allowlisted from the agent-operated public synthetic sample's actual saved candidates. It is separate from the ten V4 packets and must not be hidden by their guarded association results.

The parent separately performed a V11 repeated-text smoke check with distinct occurrence IDs. Its detailed raw receipt is not retained in the V4 first report, so this note does not count it among the 20 scored calls or claim retained independent repeated-obligation validation. The fresh V4 set contains repeated non-obligation scheduling boilerplate, which is a different challenge from two identical required sentences. Synthetic offline occurrence tests and the parent-observed smoke are separate evidence classes.

The [upgrade browser workflow](upgrade-browser-workflow.json) records agent-operated synthetic extraction and matching jobs, correction of one failed technical check, three stale reviews after file replacement, and preservation of the prior record. [workflow-verification-upgrade.json](workflow-verification-upgrade.json) records a separate scripted loopback API workflow. These demonstrate particular workflow behavior; they are not customer review, additional V4 cases, or proof of model completeness. Narrow technical checks, file associations, review currency and human acceptance remain separate.

The first V4 report supports a narrow improvement statement: on these ten authored packets, the model found six more keyed support pairs than the locked filename-plus-text baseline, and the existing format guard removed two wrong substitutions. It also exposes incomplete extraction and leaves the known guide-relevance failure unresolved. It does not justify overall “100% accuracy,” automatic satisfaction, visual quality assurance or general security claims.
