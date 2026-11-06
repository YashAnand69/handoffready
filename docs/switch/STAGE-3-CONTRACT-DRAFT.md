# Stage3 preparation — contextual clarification and correction

4 November2026. **Design preparation, not implemented or a passed stage.** The dedicated-agent Discord intake gate is still pending. This narrows the approved Stage3 plan using a read-only independent design review. Freeze schemas and tests before implementation after the intake gate passes.

## User journey

The assistant reads the confirmed requirements/current packet and calls the existing provisional selection checks. It asks one useful context-dependent question in the delivery room: for example, whether a guide's named campaign/reference really is the agreed one. File metadata cannot answer that question. A teammate replies or supplies a complete corrected packet. The lead sees the question/reply beside the relevant requirement in the existing Review screen, checks its conversation source, and makes the decision there. No additional approval screen is required just to ask an ordinary question.

## Immutable proposals, human resolution

- A question names the requirement, proposed file IDs, exact revision/input hash and bounded question text. Its technical evidence is calculated by the backend from that selection, not accepted from model-written claims. This remains a provisional check, never a saved mapping/assessment.
- A reply is an append-only unverified conversation receipt linked to the question. Store its source message reference, reported speaker, bounded text/text hash and original question currency. Model-provided identity/source references are not independently authenticated transport evidence.
- The local lead gets one inline panel with three choices: **Use for this review**, **Changes the checklist**, or **Does not apply** with a reason. Acceptance records the context basis and invalidates prior assessments. Checklist changes require the existing editor and fresh checklist confirmation. Dismissal records its reason without changing scope or saved assessments. Neither accepted context nor checklist confirmation claims client acceptance.
- Original proposal/reply text cannot be silently overwritten. Corrections append a new receipt and preserve the previous source. Notes remain private to the review desk by default; future export projections must separately preview any text deliberately shared.

## Currency and workflow hold

Add an integration schema migration and monotonic per-job `context_epoch`. Each new question, reply and resolution advances it. Unresolved current context takes priority over `ready_to_prepare_record`. Enforce the same hold in the backend when creating a new ready record/share intent; a disabled button alone is insufficient. A deliberately requested draft may preserve unresolved items with a conspicuous draft label. Existing historical exports remain readable and byte-identical.

Only explicit local acceptance adds a bounded accepted-context digest to project input identity and invalidates old assessments. Include that digest in `input_hash` only when accepted context exists, preserving hashes for old/unbound projects. Scope remains the separately confirmed checklist. Accepted context, project invalidation, epoch/resolution and operation result commit together under the one Store owner. Return the committed revision/hash; the current `_operation` helper computes currency before `apply` and cannot be reused unchanged for this mutation.

Late replies retain their original revision/hash and remain historical proposals. Never automatically apply/rebase them to a new packet. The lead may explicitly adopt one for current review while retaining its original source. Identical operation keys/payloads replay their stored result before current-version checks; altered payloads conflict. Every successful replay still refreshes the current UI. A future share intent binds both project input hash and `context_epoch`, so a later question/reply requires a fresh share decision.

## Boundary and bounds to freeze

Agent tools may propose questions and record reported replies; no scope approval, acceptance/dismissal, assessment or sharing tool. Local resolution requires the authenticated desk and current context epoch/revision/hash. Add conservative per-job question/reply/text budgets under the existing operation/result budgets. Keep unknown outcomes explicit and preserve the original operation key. Do not add model providers or another service for this stage.

The existing foundation checks readiness before stored blockers. Correct that ordering and add the backend hold before exposing new blocker tools. Pending staged files and damaged evidence also keep their own holds; context resolution must never make an incomplete packet appear ready.

## Required evidence gate

Test: backend-derived findings; irrelevant same-name guide; ambiguous brief; duplicate bytes; instructions inside uploads; wrong binding; pending context blocking readiness/new ready export; accepted context staling assessments; dismissal preserving them; checklist resolution requiring confirmation; stale replies not auto-applying; identical retry not advancing epoch/invalidation twice; altered-key payload conflict; committed result currency; and a late reply staling a prepared share intent.

Then demonstrate an actual room question, substantive human response/correction, complete replacement packet, current checks and fresh local review. Run a second differently composed packet. Record operator actions/assistance and do not call an author role-play a second-person trial. A test suite or transcript template cannot substitute for this gate.
