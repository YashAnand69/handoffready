# Independent execution review

Reviewer scope: implementation and workflow review; this file only. Initial inspection: 4 November 2026 IST. Read repository AGENTS.md. Private data, credentials, model assets and synthetic-versus-real evidence boundaries remain in force. No external messages or publication in this review.

## Current evidence

The new repository inherits HandoffReady's local review engine. Initial inspection found `docs/switch/BUILD-LEDGER.md`; `delivery.py` and a delivery tool script had not yet landed. Therefore the items below are integration acceptance gates, not claims of discovered defects in files that do not exist yet. The inherited application's prior test results are not freshly rerun review evidence.

The build ledger correctly distinguishes an actual agent direct-chat diagnostic from the still-pending dedicated-room, attachment-in/artifact-out, scoped-tool and two-person workflow gates.

## Integration checks for the new routes and tool wrapper

### Token scope and configuration

- Existing `/api/` middleware accepts the broad local session token, while `/api/v1/bootstrap` issues that token. A new delivery credential must have an explicit narrow-route policy; it must not be interchangeable with the local review token or authorize generic project mutations.
- The tool wrapper should load one deliberate owner-controlled configuration. It should validate the loopback origin/port and binding at startup. Model arguments cannot choose an alternate backend URL, token file, project, server, room or destination.
- Deny unknown tool names and additional parameters. Avoid arbitrary URL fetches or filesystem path access hidden behind a nominally safe tool.
- Do not print credential values in help, errors, test artifacts or logs. A redacted actionable configuration failure is sufficient.
- Application scope is a meaningful product contract but not an operating-system boundary against a same-user coding agent with unrestricted shell/network access. Keep that limitation stated plainly.

### Job identity, currency and evidence projection

- Resolve bound project/room/server from persisted trusted configuration or a confirmed job record. A display name or model-supplied opaque ID cannot grant access.
- Read current project state and recheck stored originals before producing current facts. The inherited API's reconciliation behavior is path-sensitive; a new `/delivery/...` route must not accidentally bypass it while claiming fresh evidence.
- A status call must distinguish unknown/uninspected/blocked from zero defects. AI suggestions are not deterministic facts or human decisions.
- Return only the allowlisted projection needed in chat. Existing project envelopes contain private brief/file text and decision notes; never return that envelope wholesale to an agent intended to see a safe summary.
- Preview output is not share authorization. Draft, stale and reviewed-with-exceptions states must remain visible.

### Safe intake and recovery

- A tool cannot read any local path merely because the model calls it an attachment. Staged inputs must be bound beneath the configured job area and reject traversal/symlink escape; maintain inherited byte/type/count limits.
- A manifest's expected total is explicit. Receiving a subset cannot complete a packet after a timeout or because the model says “all files received.”
- A repeated known operation reuses its result. A lost acknowledgement is an uncertain operation requiring reconciliation, not permission to duplicate the mutation.
- A failed correction must not delete the earlier packet or relabel its old record as current.

### Formal human actions and sharing

- Tools cannot create scope approval, semantic human disposition, export/share confirmation, or an actor signature. The lead uses the local desk.
- A genuine teammate response is useful context, but a teammate's claim of client approval is not authenticated client acceptance.
- Share confirmation must identify the exact export bytes and intended destination. If the supported chat tool cannot provide an inspectable receipt, preserve `reported` or `unknown` until actual operator inspection; do not let model prose become a transport receipt.
- A changed packet before send invalidates the prepared intent. A change during an external send leaves a historical artifact and new pending review; do not claim an impossible cross-service atomic send.

## Product execution checks

The previous winner/competitor research supports a complete, inspectable business journey. It does not support imitating feature count or claiming causal winning factors. Asana/Pastel/Frame.io/Basecamp already cover ordinary review and approval mechanics; version reset is integrity hygiene.

For this implementation, verify one short sequence: teammate submits a complete packet → agent exposes a sourced gap → teammate supplies substantive clarification/correction → lead assesses the current evidence → exact reviewed record returns to the same conversation. A second person should know the next action without the builder narrating it. The lead-operated host and offline/reconnect behavior must be understandable.

Keep deterministic metadata checks separate from the contextual question. The agent must earn its role through useful coordination and grounded explanation, not merely replay a scripted warning. Record setup and interaction burden when assessing usefulness.

## Review disposition

Initial status: architecture-informed gates recorded; actual new-code review pending files landing. No statement of completed integration, security certification, customer benefit, or award readiness follows from this initial pass.
