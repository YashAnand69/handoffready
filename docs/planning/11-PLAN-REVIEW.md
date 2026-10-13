# Planning review and traceability

13 October 2026 • Review applies to documents and the illustrative UI prototype, not working product code. Parent integrated three independently drafted workstreams and a follow-up cross-document review. Detailed planning does not guarantee absence of flaws; implementation gates are designed to catch them.

## Issues found and resolved during planning

| Finding | Resolution |
|---|---|
| Same-byte rename could retain approval in one draft while packet identity changed elsewhere | Conservative P0 rule: any packet/baseline mutation makes current matches/dispositions stale; history remains |
| Check outcomes mislabeled as inspection states | Independent inspection, deterministic check, proposal-review and human-disposition axes |
| Visible truncation could be mistaken for complete PDF content | Over-budget extraction blocks explicitly; no partial absence claim |
| Minimum-only count could accept extra items when exact count was promised | Typed exact/at-least comparison; user confirms count interpretation |
| Jobs could exist before an approved baseline without snapshot identity | Empty draft baseline identity plus job-kind-specific current-input checks |
| Inspection output could be invalidated by its own new extracted text | Inspection publication compares file/packet/parser inputs, not the post-inspection source set |
| JSON could silently include private brief material | All P0 formats share one safe client projection; full evidence sharing P1 |
| Internal exception notes might leak into client output | Separate internal rationale and explicit client usage note; default client note empty; preview required |
| Stage numbering, filename and defect gate inconsistent | One canonical six-stage schedule in 10; valid 05 QA reference; blocking P0/P1 gate |

## Requirement-to-build/test map

| PRD requirement | Main stage | Verification family |
|---|---|---|
| FR-01 preserve source | 1 | Immutable source, Unicode, edit/reopen |
| FR-02 actual evidence-backed AI | 0–1 | Actual model receipts, quote/schema rejection, manual fallback labeling |
| FR-03 explicit baseline | 1 | Correct/reject/manual additions, approval and edits |
| FR-04 compound requirements | 1–2 | Variant/count/type interpretation, no silent disambiguation |
| FR-05 bounded intake | 2 | Limit-1/limit/limit+1, type signature, blocked parsing |
| FR-06 technical properties | 2 | Actual alpha, encoded dimensions, safe SVG metadata |
| FR-07 count intent | 2–3 | Exact/at-least, duplicates, intentional repeated files |
| FR-08 semantic matches | 2 | Valid source paragraphs, misleading filenames, held-out baseline |
| FR-09 uncertainty | 2–3 | No match, several matches, no default confirmation |
| FR-10 manual/exception honesty | 3 | Technical failure remains visible, separate manual provenance |
| FR-11 invalidation | 1–3 | Packet/baseline mutation, cancel/late result/export races |
| FR-12 recovery | 1–3 | Reload/restart, storage error, revisions/migration |
| FR-13 export | 3 | Same safe projection, immutable snapshot, privacy/escaping/gaps |
| FR-14 privacy/security | 1–5 | Loopback/token/Origin/Host, no execution/network from input |
| FR-15 usability and honest coverage | 4–5 | Full task, accessibility, public-sample labels and limitations |

Use the actual PRD row text if titles evolve; this map is navigation, not a separate conflicting requirement set.

## Still unverified

- Customer's recurring problem, actual representative packet, and willingness to pay.
- Selected model/task quality, exact artifact/runtime/dependency pins and Mac cold/warm performance.
- Parser installability and real resource behavior under the proposed caps.
- Working persistence/job/export security and full browser flow.
- Actual client export usability, accessibility and first-user results.
- Week 2 final publication, account recognition and any necessary final terms/eligibility confirmation.

These are deliberately scheduled gates, not flaws being hidden by a finished document. No performance, savings, sales or contest odds are invented. Every stage needs an evidence record before being called complete.
