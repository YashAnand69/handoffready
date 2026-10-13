# HandoffReady — First-user validation and evidence protocol

Planning v1 · 13 October 2026 · relates to `01-PRD.md`

**No user trial has occurred.** Yash has identified access to a potential web development/design freelancer or agency. This protocol describes how to learn from them without inventing demand, leaking client work or confusing a demonstration with measured results. A response is not required before useful synthetic prototyping starts.

## 1. Decisions this study must inform

1. Does delivery-file ambiguity/omission recur often enough to deserve a tool?
2. Does the proposed review/manifest workflow help this user on their actual task?
3. Does semantic model matching add useful proposals beyond filenames and technical rules?
4. Can the user understand and correct false matches, unsupported checks and exceptions?
5. Is local setup acceptable? Would the user return, recommend it or consider paying?

A single tester can supply valuable firsthand feedback and reveal defects. They cannot establish broad demand, causal productivity improvements, accuracy for all packets, or winning odds.

## 2. Two independent tracks

### Track A — proceed immediately without private customer data

Create a fictional brief, licensed/synthetic supported files, a clean packet and a defective packet. Hand-label the expected requirements, properties and semantic matches. Add misleading names, duplicate bytes, opaque-alpha PNG, wrong dimensions, unsupported manual checks, changed files and negative matches. Use these for implementation, safety testing and model evaluation.

Separate prompt-development cases from held-out evaluation cases before tuning. Preserve fixture source, expected outcome, hashes and model revision. If an evaluation case influences a prompt, it becomes development data; do not continue describing it as held-out. Record actual model results and failures, not a staged replay as live inference.

### Track B — consenting real-user test when the contact is available

Begin with a brief conversation, then inspect a redacted historical packet if permission permits. Try the tool after a working P0 exists. Commercial/user-success claims depend on this evidence. If the contact cannot participate, report “no external user trial,” complete the independent product/demo and describe willingness-to-pay as unvalidated.

## 3. Minimum problem interview (10–15 minutes)

Ask these without showing an enthusiastic pitch first:

- What did you deliver on your most recent web/design job, and how did you hand it over?
- Tell me about the last missing-file, wrong-export, unclear-final-version or client follow-up problem. What happened next?
- How do you currently check the delivery against the agreement? Can you walk through that process?
- Which items are files/documentation, and which need a running website or human visual judgment?
- How often does this happen, who fixes it, and how much effort did the last example take?
- Would inspecting files locally be useful, or would model setup outweigh the benefit?

Capture concrete examples, not “Would you like an AI tool?” Do not prompt the participant to invent a problem. If the pain is predominantly copy drift, conflicting feedback or another task, record it and use the recommendation's fallback decision rather than shoehorn it into a file-packet story.

### Interview decision

- **Continue:** recent concrete packet problems, compatible supported artifacts and a believable review/manifest task.
- **Narrow:** the user benefits from exports/documentation checks but not the broader packet; focus on that subset.
- **Reconsider:** delivery files are incidental, or the manual checklist already works well enough. Complete useful independent tests while making the product decision; do not call the hypothesis validated.

## 4. Minimal permissions and data handling

Before receiving artifacts, ask the participant to choose what may be used. Do not assume the freelancer owns a client's files or may publish them.

| Permission | Default | Evidence to record |
|---|---|---|
| Discuss workflow and take private notes | Ask before notes | Verbal/written agreement and date |
| Inspect supplied, redacted historical files locally | Ask separately; only authorized data | Scope and participant's confirmation of sharing rights |
| Record screen/audio | Off unless separately agreed | Recording purpose and audience |
| Publish anonymous description/aggregate observations | Ask separately | Approved wording and permitted details |
| Publish a quotation or identifiable testimonial | Off unless exact quote approved | Exact text, attribution choice and approval |
| Publish actual files/screenshots | Off; prefer recreated synthetic examples | Rights and reviewed redacted artifacts |

Suggested short consent explanation:

> I am testing a prototype that checks a delivery packet against a brief. Participation is optional. Please use only files you are allowed to share and remove client names, credentials and confidential material. The files will stay on the local test machine; I will not publish them or send them to a cloud model. May I take private notes? Any recording, quote or public example needs separate permission.

Make the actual application behavior match that explanation. If implementation later uses a network service, pause real-data intake until the participant receives the changed disclosure and permission is obtained. Initial model/dependency downloads are separate from inference; explain them honestly.

Keep client names, emails, tokens, contracts and private files out of Git, public hosting, agent session exports and the DEV entry. Use a private folder excluded from source control. Redaction must cover document metadata, filenames and screenshot sidebars as well as visible body text. A synthetically reconstructed example is safer than claiming a confidential packet is anonymous.

Record an agreed retention date for supplied test copies, ideally within seven days of the study unless the participant requests otherwise. Remove only authorized test copies when due; never delete their originals. Keep a minimal anonymized result record if separately permitted. Withdrawal means stopping further use and removing unpublished permitted copies where practicable; do not promise control over content already publicly redistributed.

## 5. Trial protocol (30–45 minutes after P0 is usable)

### Preparation

- Confirm version, machine, selected model/revision and whether the model is already installed.
- Use an authorized redacted packet or an honestly labeled synthetic reconstruction based on the real workflow.
- Establish the expected requirements and defect annotations in advance. An observed omission may be open to interpretation; record disagreements.
- Include at least one correct item and one negative semantic case; a packet composed only of defects encourages unnecessary findings.
- Keep setup cost separate from task review cost. Record help provided; coached success is not independent usability success.

### Run

1. Ask the user to explain their current checking process and establish its usual output. Do not invent a baseline time from memory.
2. If a task comparison is feasible, have the user perform comparable but different packets manually and with HandoffReady. Use matched complexity and alternate order across participants when possible. With one tester, report order and familiarity as limitations.
3. Ask the user to add the brief, inspect proposed requirements and confirm the checklist. Observe edits without directing choices.
4. Ask them to inspect the packet and resolve a semantically ambiguous match, a technical mismatch and a manual-only requirement.
5. Ask them to export the handoff and explain what is still unresolved.
6. Replace one approved file with changed bytes and ask what happened to its previous review.
7. Ask whether they would use this output on the next delivery. Find out what would stop them.

Do not rerun the same packet manually after the tool reveals its defects and call the difference “time saved.” Familiarity contaminates that comparison. A single observed task may be described as completed in a measured duration; it is not proof of comparative savings.

### Usability probes

- What do you think this status means?
- What evidence would you need before accepting this suggestion?
- Where would you look for a requirement the model missed?
- Does “unknown” mean missing, unchecked, or something else to you?
- Would the exported manifest mislead your client about what was verified?
- What should happen when a file changes?

The answer to the last two should agree with product behavior. Misunderstanding is a defect to fix, not a participant failure.

## 6. Metrics and interpretation

| Measure | How to record | Allowed interpretation |
|---|---|---|
| Setup time | Model download separately from install/run; cold/warm run latency | Actual observed machine/setup only |
| Task time | Start/end and assistance; record packet/order | Observed task duration; comparisons need credible matched baseline |
| Supported defects | Ground-truth cases detected/missed | Fixture-specific detection, with denominator |
| False flags | Correct items incorrectly flagged | Concrete burden; never hide because user corrected it |
| Semantic matches | Accepted useful proposals, rejected wrong ones, missed relevant matches | Human-judged utility on these cases |
| Baseline corrections | Edits/rejections/additions before approval | Extraction limitations and review cost |
| Unsupported/manual checks | Number and user's understanding | Honest coverage, not total-product accuracy |
| Output usefulness | What was kept, edited, discarded or used | Actual observed or reported behavior |
| Return intention | Participant's exact qualified answer | Intention, not retention/adoption |
| Payment response | Hypothetical price context and exact answer | Stated willingness, not a sale |

Report raw counts when small. Avoid an “accuracy percentage” over unlike requirements or unsupported checks. Record model/rules-only results on the same frozen test set; account for human-review time, not only inference speed. No leaderboard performance claim from hand-tuned demonstration fixtures.

## 7. Commercial questions after use

- What would this replace in your current process?
- Would you use it on your next project? Why or why not?
- Who would decide or pay in your studio?
- What would installation/support need to look like?
- Would you prefer a one-time local license, support/setup service, or something else?
- If a specific price is tested: “This is hypothetical; nothing is being sold today. At [price] for [clearly stated offering], would you consider it? What makes that worthwhile or not?”

Leave price unset until the task and offering are concrete. Do not lead with a discount to manufacture enthusiasm. No money is collected, free trial converted, checkout opened or paid service provisioned by this study. The spending constraint remains zero new charges.

## 8. Evidence record template

```text
Study ID / date:
Participant role / anonymized ID:
Permissions (notes, local files, recording, publication):
Artifact origin (real authorized / reconstructed / fictional):
App commit / model revision / hardware:
Task and packet IDs / order:
Setup time / cold inference / warm inference:
Review task duration / assistance:
Expected supported defects:
Detected / missed / false flags:
Useful / wrong / missed semantic associations:
Checklist corrections:
Manual or unsupported requirements:
Manifest edits / unresolved items:
Observed file-change/recovery behavior:
Participant feedback (exact wording; private/public status):
Next-use intention / hypothetical pricing response:
Top defects to fix / retest outcome:
Limits / disagreements / potential bias:
Public evidence approved:
Retention date / authorized cleanup scope:
```

## 9. Go / narrow / pivot and submission boundaries

**Go:** a real recent problem, a useful completed task and understandable evidence are observed. Continue fixing the largest false-match/usability burdens; a satisfied tester is still not proof of a market.

**Narrow:** technical checks help but semantic proposals are frequently wrong or unhelpful. Improve/restrict the matching task, rerun frozen cases and show failures. If AI adds no meaningful role, revise the product rather than claim a required open-AI core.

**Pivot:** the reachable user's recurring problem lies elsewhere. Use evidence to choose the documented fallback and reduce scope to preserve the deadline. Do not abandon all useful engineering merely because an interview is delayed.

**No response:** complete the synthetic workflow and actual-model demo, explicitly omit customer-success claims and fabricated “My First User” content. An optional section can be omitted instead of filled with invented testimony. [Official Week 2 brief/template](https://dev.to/challenges/hacktoberfest-week2-2026-10-12).

**Public story:** distinguish what was built, what was benchmarked, what the user tried, what failed and what remains hypothetical. Explain Yash's product decisions and any genuinely performed testing, with truthful AI/dependency attribution. Preserve permission boundaries in video, screenshots and session exports. Publish by the internal 18 October evening IST target, with the official deadline verified before submission. [Specific rules](https://dev.to/page/hacktoberfest-week2-2026-10-12-contest-rules).
