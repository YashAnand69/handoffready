# HandoffReady UI/UX specification

Version 1.0 • 13 October 2026 • Planning specification, not an implemented or usability-tested interface.

## Experience intent

A calm delivery desk for a freelance web developer/designer. The customer should understand: what was requested, what files support it, what remains unresolved, and what will be included in the client handoff. The core interface is a review workspace, not a chatbot. Original design direction: warm white surfaces, charcoal ink, restrained cobalt actions, generous spacing, precise file/evidence details. Do not reuse Soundwalk's illustration or make the old application the Week 2 project.

## Information architecture

One project workspace with five named steps: **Brief → Checklist → Files → Review → Handoff**. Settings and model readiness belong in a compact utility area. A project selector is sufficient; no sales dashboards, empty integrations, account creation or revenue graphs. Progress indicates workflow position, never contract completion.

| Screen | Primary user question | Main action | Important secondary action |
|---|---|---|---|
| Start | Can I try this, and where does my data go? | New handoff | Open labeled sample; model setup |
| Brief | What did we agree to deliver? | Suggest checklist | Create checklist manually; replace brief |
| Checklist | Are these really the agreed requirements? | Confirm baseline | Correct/add/remove candidates, view quoted source |
| Files | What am I delivering? | Inspect selected files | Remove rejected files, identify intended final versions |
| Review | What is missing or ambiguous? | Review next unresolved item | Inspect source, change mapping, record manual exception |
| Handoff | What exactly will the client receive? | Preview export | Return to unresolved items; choose client-visible notes |
| History/settings | What changed, and can I recover my work? | Open latest saved project | View revisions, storage location, export/delete controls |

## Screen contracts

### Start and model readiness

Give two honest paths: a local working project and a clearly labeled public example. Show model state as Not prepared, Starting, Available, Unavailable, or Failed with the useful next action. Model absence does not erase saved work or fabricate suggestions. Permit manual checklist/review, but label that run manual. Public sample states “Recorded model suggestions on example files”; no pretend upload-to-AI button. The final entry must also show a real local inference run.

### Brief

A large labeled text field, optional source title, and limits before submission. P0 brief intake is pasted text only. Native-text PDF brief intake is P1 and may be added only after the parser gate passes. Preview extracted text with page references; if text cannot be extracted, invite pasted text rather than showing an empty successful brief. A label such as “Client-approved brief supplied by you” records the user's description, not cryptographic proof of approval. Saving draft and running extraction are separate operations. Unsaved text remains recoverable or visibly warns before leaving.

### Checklist

Each candidate is a card or row with editable deliverable name, verbatim brief quote, source locator, quantity/unit, supported technical requirements and manual requirements. Clicking source opens the matching excerpt. Model-inferred numbers without evidence remain unset. Confirmation applies to the complete reviewed revision; edits afterward create a new revision and invalidate dependent results. Model candidates never auto-enter the approved baseline. A manual item states “Added by you” instead of inventing a quote.

### Files

Use a native multi-file picker with drag-and-drop as an enhancement, not the sole method. Display actual supported type, dimensions/page count where known, size, parsing state and rejection reason. Duplicate content is grouped visibly; identical names from separate folders must not collapse silently. Show which artifacts are final only after user selection. Files remain local; the file picker is not a cloud upload. Re-selecting changed bytes produces a new artifact revision. Unsupported/failed files are distinct from absent files.

### Review — signature workspace

At desktop width, use three areas: requirement queue at left, selected requirement/match inspector in the middle, and source/file evidence at right. The right panel is sticky only when it does not obstruct focus. Keep exact source quotes beside proposed matches, and actual metadata beside check findings. Show a requirement's **mapping**, **technical checks**, and **human review** independently.

Example selected item:

- Requirement: three 1080 × 1080 launch exports.
- Source: exact sentence from approved brief.
- Candidate artifacts: tile-a.png, tile-b.png, tile-c-copy.png.
- Check finding: two distinct contents; third file duplicates tile-a.
- Actions: select replacement, inspect files, or record a reasoned exception.

Every state has text and icon, not color alone. Suggested matches say “Suggested”; inspected dimensions say “Measured”; a review says “Confirmed by you.” A technical success cannot conceal an unresolved semantic match. Summary counts use independent categories and disclose overlap, or count requirement-level unresolved cases once; do not sum overlapping categories into a fake total.

Selecting Confirm match saves a review decision for the current hashes and revisions. Reject suggestion preserves its original output for history. A manual exception requires a reason and remains visible in export; it never turns a failed check into a verified pass. Website behavior, design quality and legal/IP suitability are manual/not-assessed requirements, not automatic green badges.

### Handoff

Show a readable preview before export. Include project name, requirement-to-file mapping, user-written usage notes, factual checks, human confirmations and unresolved/manual items. Internal source conversations and model prompts are excluded from client export by default. Clearly indicate what is included. Do not include original asset bytes automatically; this MVP prepares a manifest for the existing packet. Export client-safe JSON, Markdown and printable HTML from the same safe client projection. A separately labeled private-evidence JSON export is P1 and may include source evidence only after explicit selection and a privacy warning; never silently include raw brief text in a client download. A valid export can contain unresolved items when prominently disclosed. Do not label it “Certified complete.”

## Visual system

| Token | Initial value / intent |
|---|---|
| Canvas | #F6F7F9 |
| Surface | #FFFFFF |
| Primary ink | #18212F |
| Secondary ink | #4B5563 |
| Action | #2453C6; white text, verify contrast |
| Evidence tint | #EDF2FF with dark ink |
| Warning | #8A4B0F on #FFF5E6; verify contrast |
| Success | #176344 on #EAF6EF; verify contrast |
| Error | #9B2535 on #FDEDEF; verify contrast |
| Type | System sans for UI, system monospace for filenames/metadata |
| Spacing | 4/8/12/16/24/32/48 px scale |
| Controls | 44 px preferred hit area, visible focus ring, 8–12 px radii |

Colors are proposed tokens, not audited conformance results. Verify every actual text/state pairing. Use 16px body text, restrained 24–32px section headings, readable 60–80 character passages and clear table labels. Never truncate the evidence necessary to judge a match; offer expansion. Filenames wrap or expose their full name on focus, not only hover.

## Motion

Use 120–180 ms fades for opening evidence, a short confirmation transition and a subtle packet-to-manifest transition. Avoid autoplay canvas, perpetual particles, scroll hijacking and large hero motion in the working desk. Respect reduced-motion changes dynamically; all content remains visible without animation. If a decorative animation is introduced, offer a visible pause. Loading uses actual job state and elapsed time, not invented percentages. If no estimate exists, show “Analysing 2 of 8 items” only when the job really tracks those items.

## Responsive and accessible behavior

- Desktop: source beside decision. Tablet: queue and inspector with an expandable source drawer. Phone: one requirement at a time with source/check disclosure before actions; clearly recommend desktop for file-heavy work without blocking readable review.
- Targets: prefer 44px. WCAG 2.2's AA minimum is 24px with exceptions; the larger design target is intentional. [W3C target guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).
- Keyboard: logical tab order, native buttons/labels, skip link, focus restored after dialogs, Escape closes non-destructive drawers, visible focus not hidden by sticky controls. [Focus not obscured](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html).
- Announce save/job/error transitions through appropriate status regions without repeated announcements on every keystroke. [Status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html).
- No animation dependence; respect the interaction-animation guidance, a stronger design target rather than claiming automatic AA conformance. [Animation guidance](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html).
- Verify 390/768/1280px, 200% zoom and 320px reflow; long names/notes, empty source, storage failure and keyboard review.

## Error copy and recovery

| Situation | Useful message and next step |
|---|---|
| Parser fails | “We couldn't read this file. It hasn't been checked. Paste the relevant text or choose another file.” |
| Model unavailable | “Suggestions need the local model. Your saved files and manual review are still available.” |
| Model lacks valid evidence | “This suggestion couldn't be tied to the supplied text. Review the requirement manually.” |
| File changed | “The packet changed after your review. All previous review decisions need checking again.” |
| Save conflict | “This project changed elsewhere. Reload the latest version or keep a copy of your draft.” |
| Export stale | “The project changed while this export was prepared. Preview the current version before exporting.” |
| Ambiguous match | “More than one file could fit. Choose the intended final artifact.” |

## UI acceptance and review

A tester can find the first useful action, understand local storage/model setup, inspect one quoted source, reject an incorrect match, replace a wrong artifact and export a truthful handoff. Independent review checks misleading success language, missing states, export privacy and focus. Record observed usability issues and resolve them before decorative polish. UI prototype is a design illustration with synthetic state; it does not claim working inference or file inspection.
