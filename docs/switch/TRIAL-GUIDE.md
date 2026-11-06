# HandoffReady: a practical 25-minute trial

**Prepared 5 November 2026. No participant has completed this trial.** The live owner rehearsal passed the real return gate; an external colleague trial, second-person access and independent final audit remain unverified. Use this guide when a suitable person is available. Do not record an imaginary participant or treat watching a demo as hands-on use.

## Who does what

| Person | Role and access |
| --- | --- |
| Participant | A practising designer, developer or freelancer who hands work to others. Uses their own Discord account to supply files, discuss problems and inspect the deliberately shared record. |
| Yash | Local reviewer and moderator. Operates HandoffReady on his computer, checks sources, confirms the complete packet and saves his own judgments. |
| Agent | Assists with intake, questions and scoped checks. It cannot confirm scope, save a human assessment, authorize sharing or verify its own send. |

The participant does not open Yash's localhost URL on their device. Do not expose the local service or distribute its configuration, credentials or bot token. If Yash must relay messages because the bridge accepts only the owner, disclose **owner-relayed collaboration**, not direct participant-to-agent access.

## Materials prepared for this guide

Run from the repository, using its existing environment:

```sh
.venv/bin/python scripts/prepare_delivery_trial.py --output /absolute/path/to/a-new-trial-kit
```

The generator refuses an existing folder. It creates:

- `participant-start.zip`: participant orientation, fictional brief and first four-file packet. Give only this at the start.
- `packet-01.zip`: first delivery originals, for convenience; extract files before submitting them to the app.
- `packet-02.zip`: complete replacement originals; keep this until the second task.
- `moderator-only/ANSWER-KEY.json`: technical facts and expected currency behavior. Keep out of the room, participant pack and agent workspace.
- `MANIFEST.json`: exact file sizes and SHA-256 values. These are authored synthetic regressions, not independently hidden model evaluation.

The images are simple generated test graphics. Assessing their dimensions or duplicate bytes is meaningful; treating them as professional artwork or measuring aesthetic design quality is not. The guide describes a fictional website, so no website execution has been demonstrated.

## Before inviting anyone: setup gate

Do this before timing the session. A prepared guide is not proof that the gate has passed.

1. Preserve the existing owner rehearsal and returned record. Use a new isolated data folder and a dedicated synthetic trial room/job; the current application permits one delivery job per configured conversation. Creating another project does not rebind an existing room. Prepare its scoped profile and agent instructions explicitly; do not reuse or overwrite the current job by accident.
2. Test the participant's own-account access. Confirm they can view the trial channel, attach one harmless practice file and receive the intended reply. Current owner-to-agent access is verified; second-person addressing is not. If a permission change is needed, Yash makes the narrow change and verifies it. Keep bypass and automatic approvals off.
3. Confirm Switch Console and the local service are running, and identify the correct local desk. The last verified owner desk is port 8896; a future isolated trial must display its own actual address. Do not assume an old temporary test port is live.
4. Ensure no participant/customer information or moderator answer key is in the room or packet. Keep the replacement packet private until Task 2. Extract the four originals from each archive; ZIP inspection is not part of the supported task.
5. Load the fictional brief. Prepare a human-reviewable checklist: three distinct 1200×1200 PNG launch images; useful contact-update instructions; the unresolved suggestion about a logo. Use the ordinary checklist editor and confirm only scope actually reviewed. Human-only meaning, intended purpose and unexecuted website checks remain explicit.
6. Test packet staging and the public-record destination on disposable practice data. Confirm each exact complete selection locally; do not select both old and new files with the same name. Only the newest intended four-file packet should be confirmed for Task 2.
7. Record the candidate revision or working-tree fingerprint, app/Switch/provider versions, setup duration, access mode and any assistance. If an essential route is unavailable, pause the hands-on trial or label the session a concept walkthrough. Never silently substitute a recording for a live feature.

No server invitation, permission change, message, review, share authorization or registration is performed by this guide.

## Consent: read before starting

“We are testing a delivery-review prototype with fictional files. Participation is voluntary; you can stop at any time. I will note actions, problems and help needed. Please do not use customer data. Screen/audio recording is optional and needs your separate agreement. Nothing you say will be quoted publicly without your separate permission. Are you comfortable taking part, and are written notes okay?”

Record the actual answers privately. No response is not consent. Use a participant code such as P1 in reports. Keep contact details/raw notes outside Git. Ask separately about recording and exact quotes. After the session, agree a deletion date for private notes/recordings; before publishing, remove identifiers and confirm permitted excerpts. Do not invite anyone or send a recruitment message on the participant's behalf.

## Session script

| Time | Moderator action | Observe |
| --- | --- | --- |
| 0–4 min | Ask how their last real handoff worked, who checked it and what caused rework. | Is this a real problem for their role? Do not pitch time savings. |
| 4–6 min | Obtain consent, explain the two human roles, supply the participant start pack and show the trial channel. | Can they distinguish room coordination from local review? |
| 6–14 min | Give Task 1 below. Wait while they work; answer requests for help neutrally. | Findings, sources consulted, clarification, next-action confusion and interventions. |
| 14–19 min | Give the replacement packet and Task 2. | Do they understand changed files, stale review, immutable old records and fresh review? |
| 19–25 min | Ask the comprehension/fit questions below. | What they think the record means, remaining checks and a specific use case or rejection. |

**Task 1 — say only:** “Read the brief. Help the reviewer understand this delivery, identify anything that needs resolving and leave a clear record of what is ready and what is not.”

**Task 2 — say only:** “The designer has supplied this replacement packet. Help the reviewer decide what should happen to the earlier review and record, and prepare the current delivery record.”

Do not tell the participant to find duplicates, specify the seeded defects, choose an assessment or repeat an answer. Allow about two minutes before offering help unless they ask or a privacy/data-loss risk appears. Log every hint or takeover. A successful assisted task remains assisted. If there is no early completed record, observe its partial state; do not invent one to make Task 2 look successful.

Yash must also use his own judgment. A correct technical result is not a reason to copy a prewritten “Satisfied” assessment. Leave uncertainty visible. The participant's chat reply does not approve the checklist or the delivery. Only deliberately previewed public material may be returned, once, to the intended room.

## Final questions

Ask in their own words: What does the final record promise? What would you still inspect? Who decided that the packet was ready? What happened to the earlier review after the replacement? Which step added unnecessary work? For your next actual handoff, would you choose this workflow or your current one, and why? What would prevent you using it?

Do not lead with “Did the AI save time?” One person thinking aloud is qualitative evidence, not a productivity benchmark. A person saying they might try it is not adoption, a paid customer or an endorsement.

## Observation sheet — fill only after observing

| Field | Actual observation |
| --- | --- |
| Participant code, role, relevant experience | |
| Date, candidate fingerprint, packet manifest hash | |
| Consent for notes / recording / exact public quote | |
| Own-account channel access and agent route | |
| Access mode: direct / owner-relayed / walkthrough | |
| Setup time / active task time / waiting time | |
| Task 1: unassisted / assisted / incomplete; concrete result | |
| Task 2: unassisted / assisted / incomplete; concrete result | |
| First wrong conclusion or missed finding | |
| Each help action, timestamp and its effect | |
| Meaning of old/current record in their words | |
| Final attachment identity and actual return state | |
| Exact permitted quote (or “no quote permission”) | |
| Observed behavior / participant opinion / our interpretation | |
| Highest-impact fix and retest result | |
| Private-note/recording deletion date | |

Keep those three last evidence categories distinct. Preserve the first attempt when a retest improves it. Do not omit failed tasks from the report. At most, report individual timings with setup/wait/help disclosed; no generalized percentage savings or model accuracy claim.

## If no participant is available

Use the kit for an explicitly authored two-role rehearsal or a recorded walkthrough. Mark external trial **not completed**. Keep its observations separate from the verified owner integration loop. Finish recovery, clean setup and evidence-based presentation without inventing a tester, consent, quote or impact statistic.

## After a real session

Fix the two largest observed frictions first. Reproduce each defect with synthetic inputs, run checks appropriate to the fix and repeat the affected task if the person agrees. Publish only consented, anonymized facts with the assistance/access mode stated. Do not submit a contest entry automatically.

Research protocol: [validation/release plan](../../../plan/05-VALIDATION-AND-RELEASE.md) and [trial research protocol](../../../research/TEST-AND-TRIAL-PROTOCOL.md). Neutral task design follows [GOV.UK moderated usability testing](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing); the small qualitative sample is not a population-level measurement.
