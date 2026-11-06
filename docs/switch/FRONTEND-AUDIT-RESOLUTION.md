# Frontend audit resolution

6 November 2026. Reviewed `FRONTEND_BUGS_REPORT.md` against current source and delivery contracts. Severity labels and recommendations were checked rather than accepted automatically. Local-only origin restrictions, approval boundaries, stable delivery operation keys and busy navigation guards remain intact. No backend/CLI changes, dependency installation, live-data access, publication or service restart was performed.

| Claim | Assessment and resolution |
|---|---|
| FE-CRIT-01 — UUID on LAN | Unsupported scenario: development and service binding are loopback-only. Kept cryptographic UUIDs and secure-context expectations. No LAN/origin support or insecure deployment promise was added; no supported-loopback crash was established. |
| FE-CRIT-02 — trapped room busy | Rejections already settle through `finally`; all three cards release busy state on unmount. Rejected the proposed interrupt-and-leave override because it would undermine reconciliation. Real indefinitely stalled requests are now bounded at 150 seconds, above the backend's 120-second inspection budget. Timeout/cancellation remains ambiguous and retains pending operation identity; navigation stays locked until settlement. |
| FE-HIGH-01 — hold ignored by next action | Confirmed. Project-wide holds take priority over readiness: pending receipts lead to Files, otherwise pending context leads to Review. An empty attention requirement list cannot suggest preparing a held record. |
| FE-HIGH-02 — stale refresh | Added project identity/revision guards to ordinary refreshes and an explicit intentional-project-opening path. Leaving clears the visible identity synchronously. A regression races a delayed revision-4 mutation refresh against revision-5 job reconciliation and verifies revision 5 remains visible. Existing busy locks remain. |
| FE-HIGH-03 — context draft wiped | Confirmed. Reload retains authored reasons and still-valid reply selections by question ID, but resets source acknowledgement. Known refusals retain drafts with acknowledgement reset; successful resolution clears only its own question draft. Pending replay payloads/keys are unchanged. |
| FE-HIGH-04 — mobile queue | Report overlooked a later selector override; its all-current-browsers conclusion was overstated. CSS owner removed dead selector dependencies and made the mobile block layout explicit. See `MOTION-POLISH.md`. Functional owner did not edit styles. |
| FE-HIGH-05 — non-JSON responses | Confirmed poor error handling; the report's unhandled-crash wording is overstated because normal callers catch failures. Bootstrap/API now validate JSON/envelopes and return safe `ApiError` messages/status for HTML, empty or malformed results. Raw response pages are not exposed. |
| FE-HIGH-06 — external links | Supported backend destinations/messages were already validated. Added frontend defense restricted to the exact Discord channel authority; checked messages must belong to that same channel plus a numeric message ID. Invalid links are warnings, and invalid channel projections cannot authorize a new return. Explicit `noopener noreferrer`; no generic HTTP(S) authority expansion. |
| FE-MED-01 — history unmount | Added read cancellation and guarded state publication. The claim that React 19 necessarily emits a historical unmounted-setState warning was not established. |
| FE-MED-02 — AbortSignal | Added optional cancellation to bootstrap/API and used it for private history cleanup. Identity/revision guards separately handle ordering; no user-facing interruption of committed delivery writes was introduced. |
| FE-MED-03 — empty source label | Confirmed. Whitespace-only label disables brief saving; click handling also guards it before a backend request. |
| FE-MED-04 — hidden rename draft | Rejected clearing dirty state merely because the editor closes: its text is still unsaved. Added visible unsaved-filename guidance and explicit discard control; Rename restores the retained text. Leave/browser-close protection remains. |
| FE-MED-05 — empty project submission | Confirmed missing handler guard. Direct form submission now requires connection and a trimmed name independently of the disabled button. |
| FE-MED-06 — exception without public note | Supported incomplete-review behavior, not an authority bypass: editor explicitly warns that missing public explanation leaves a draft and backend reports the gap. Preserved saving incomplete review; no private note is copied into public explanation. Explained exceptions remain separately tested. |
| FE-MED-07 — download anchor | Download control is now attached for its click, removed afterwards, and object URL cleaned up. No claim of actually testing Firefox/WebKit. |
| FE-MED-08 — dirty event bubbling | Current review searches already stop propagation and filters are buttons. Existing tests confirm these do not create unsaved-review warnings. No reproduced defect justified broad dirty-state rewriting. |
| FE-MED-09 — CSS classes | CSS owner added support for existing `.checkline` and `a.primary-link`; acknowledgement semantics unchanged. See `MOTION-POLISH.md`. |
| FE-LOW-01 — old brief draft keys | Existing version-scoped recovery prevents applying another source version's draft. Successful save and project deletion clear all project draft keys; existing tests cover both. No automatic deletion of unsaved older-source text was added. |
| FE-LOW-02 — history timestamp type | Corrected read-side type to `recorded_at`; no migration or invented timestamp. |
| FE-LOW-03 — expansion accessibility | Added `aria-expanded` to rename/image controls. Image errors already use alerts; hidden rename draft now has a status region. |
| FE-LOW-04 — index keys | Check editors are controlled by parent values, without independent editor state. No reassignment defect was reproduced; existing remove-check/acknowledgement tests pass. No incidental key-system rewrite. |
| FE-LOW-05 — invalid expiry | Invalid/non-string expiry now displays an unavailable-time explanation. It does not become authorization; server/current-state checks remain authoritative. |
| FE-LOW-06 — undefined finding formatting | Helper can return JavaScript `undefined`; current finding renderers guard optional expected/actual fields. No visible defect was established. No formatter rewrite required for confirmed fixes. |
| FE-LOW-07 — legacy evidence ID type | Optional read-side legacy evidence ID does not itself send a forbidden field. Current backend requirements use `source_span`; no offending current API-generated save payload was established. Evidence authority was not broadened. |
| FE-LOW-08 — Node warning | Installed Node is 20.18.0. No runtime/package upgrade performed; actual build warning/result recorded below. |

## Verification

Tests use deterministic API doubles/components; they do not establish model quality, live room behavior or cross-browser usability. New regressions cover malformed/HTML results, bootstrap token validation, structured field refusals, cancelled/hung requests without automatic write retry, attached download cleanup, hold priority, old-refresh/new-revision ordering, draft retention with renewed acknowledgement, fixed-destination links, blank project names and source labels. Existing busy navigation, replay, hidden filename draft, unsaved review, explained exception and privacy tests remain.

Implementation checks caught an initial guard that also blocked intentional project opening; an explicit activation path fixed it before final checks. Test-only unknown narrowing and full Job fixture fields were also corrected. Intermediate implementation failures are not represented as passing baseline evidence.

Final execution (all exit code 0):

- `npm test -- --run`: 146 tests passed across 13 files, 3.03 seconds.
- `npm run build`: TypeScript project build passed; Vite 7.3.7 production build completed (47 modules, 509 ms).
- `npm run format:check`: all matched files passed.
- Separate `npm run typecheck` passed before the final combined build.

The production build emitted the existing Node compatibility warning: Node 20.18.0 is below Vite's declared 20.19+/22.12+ requirement. Successful local build does not remove that support limitation. No server was restarted and no live workflow was represented as tested.
