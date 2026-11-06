# Recovery checks and operator runbook

5 November 2026. **Recovery checks passed; Stage 5 as a whole remains open.** An independent final review and the complete frozen fresh-packet protocol have not been completed. The current candidate is an uncommitted working tree. No live data was fault-injected and no real room send was retried.

## What changed and what was actually run

Added eight process-level checks in `tests/test_delivery_share_recovery.py`:

| Boundary | Observed invariant |
| --- | --- |
| Hard exit before authorization commit | No partial export, intent, operation receipt or project history; replay creates one complete record. |
| Hard exit after authorization commit, before method response | Frozen record and receipt survive; replay returns the same record without another export. |
| Hard exit before issue commit | Permission remains unconsumed; the same request can consume it once. No external effect was attempted. |
| Hard exit after issue commit, before method response | One issued attempt survives; replay returns `send_permitted:false` without sending arguments. |
| Hard exit before verification commit | Outcome stays unverified; submitting the actual synthetic verification once records one confirmation. |
| Hard exit after verification commit, before method response | Confirmation and receipt survive; replay adds no second event or record change. |
| Real HTTP server killed after permission issue, disconnected request, restart | Connection fails while offline; restarted state remains `issued_unverified`, same attempt, no second permission/material; earlier local-session token is refused. |
| Second supported server opens the same disposable data | Refused before recovery/startup writes; first server and authorized record remain usable. |

The transaction-boundary cases use `os._exit(86)` in a child process, without cleanup, with the interruption instrumented only in that test process. The HTTP case kills a real disposable server process. They are automated synthetic checks; they are not actual Discord sends, human confirmations, OS/power-loss, disk-corruption or network-filesystem tests. Permission consumption is deliberately conservative: a crash after consumption can require operator investigation even if no send happened.

First test execution found four passing cases and two failures in the new test harness's final assertion: it expected `export_id` in the agent material instead of reading it from retained share history. The harness was corrected; no product behavior was changed for that failure. The six boundary cases plus two HTTP/process cases then passed. Preserve this distinction from a product-defect repair.

Full backend verification: **531 passed, zero failed, 72.16 seconds**. Command: `PYTHONPATH=backend .venv/bin/python -m pytest -q`. Existing Starlette/httpx deprecation remains. Earlier Stage 4 full interface/build/format checks passed116 tests; no frontend/runtime code changed in this Stage 5 checkpoint, so those checks were not repeated. Eight new recovery tests are the incremental scope, not531 new cases. No dependencies were added.

## Actual owner-desk restart on 6 November

The desk was offline at the later check. With no listener or supported launcher running, an exclusive data-folder lock was acquired and a consistent private SQLite/evidence backup was created. Backup integrity check passed. The supported launcher restarted the existing desk at 8896 using its unchanged profile, without installing or enabling a model. Read-back preserved revision 13, the two-file packet, one frozen export and the operator-confirmed return. No second authorization, send, review or verification was created. Receipt: `execution/stage5-owner-restart.json`. This is an observed local recovery, not proof that the chat/provider route remained connected.

## Other failure evidence, by scope

| Concern | Existing checks / scope |
| --- | --- |
| Partial packet, corrupt staged bytes, parser failure, scratch crash | `tests/test_delivery_packets.py` tests rollback, retained originals, explicit completeness, unknown commit and abandoned preparation recovery. |
| Unsupported or timed-out replacement inspection | `tests/test_replacement_recovery.py` preserves the usable packet and prior review/export. |
| Model timeout/schema/evidence failure | `tests/test_model.py`, `tests/test_api.py`: bounded/explicit failure and interrupted-job handling; test doubles are not current provider reliability. |
| Foreign room/job, changed authority, private projection, concurrency, expiry | `tests/test_delivery_share.py` and delivery/context/API suites. |
| Lost issue reply, private output path, symlink/hardlink/collision | `tests/test_delivery_share_tools.py`; application confinement is not same-user OS isolation. |
| Actual return | Stage 4 owner-confirmed assisted synthetic Discord/Switch run, source revision 12, 2,033 bytes. External receipt: `execution/stage4-owner-verified-return.json`. Not a colleague trial. |

## When a return appears stuck

1. Read the **current** local status and retained return history. Note the record ID, source revision, hash, attempt and configured destination. Do not interpret an agent's “sent” prose as verification.
2. If the record is still **authorized**, the app has not recorded permission consumption. Check expiry/currency and pending files/questions before asking the agent to use that exact existing intent. Do not create a fresh record merely because a response was lost.
3. If **issued unverified**, stop automatic retries. Check the exact main channel, not an unrelated thread, and download the actual attachment if present. Do not substitute the local outgoing file for the downloaded return.
4. Supply that downloaded Markdown and its exact message link at **05 Handoff → Verify the actual return**. The local reviewer checks the destination personally, then verifies bytes. A successful result is **operator-confirmed**, not independent authenticated transport proof or client acceptance.
5. If nothing can establish the outcome, retain **unverified**. If the reviewer chooses to cancel, acknowledge that the attachment may already have been sent. A deliberate second authorization requires a new public preview and duplicate-risk acknowledgement. Absence from a quick room search is not conclusive proof of non-delivery.
6. If the project changed, inspect the old record as history. Do not reuse its authorization as approval of a new packet. Ask for fresh review and authorization only for the current intended state.

## When the app or model is unavailable

- An offline desk is not an empty project. Keep the existing data and private profiles. Check whether its supported launcher is still running before starting another copy; use the same configured data folder only after the owner process has stopped.
- Resume with the documented launcher/profile and actual local address. Supported launchers enforce exclusive ownership; do not open/recover a live data folder through a second ad-hoc Store instance.
- Refresh the local desk after restart; the earlier local-session token no longer grants access. Read retained operations/history before resubmitting a write.
- If the optional model fails, inspect the explicit error. Deterministic file facts and manual review remain separate. Do not fabricate model proposals or turn a failed inference into empty “all clear” output.
- Keep Switch Console and its configured provider available for room assistance. A local desk restart does not prove that a disconnected room/provider resumed. Test an ordinary read/status message separately when needed.

## Preserve evidence before recovery

Record actual status, candidate fingerprint and relevant operation IDs privately. Use a consistent SQLite backup and copy its associated originals/integration files while writes are quiesced; copying only a live `.sqlite3` file may omit WAL data. Do not delete journals, receipts or old exports to unblock a workflow. Backups include unencrypted project evidence and require private storage. Do not put private configuration or raw client data into Git, screenshots or a public report.

SQLite's [WAL documentation](https://sqlite.org/wal.html) describes the separate log and backup/copy considerations. Our process-exit checks do not certify every hardware/filesystem failure mode. The database transaction does not encompass a Discord send.

## Independent review still needed

An independent reviewer should inspect the final source, not just this report, and try at least: changed source between preview/issue; final record after source change; duplicate issue across processes; wrong job/destination and malformed verification; delayed receipt arrival; private-note/source leakage; malformed input rollback; disabled-integration restart and retained history; participant/owner access separation; misleading or blank UI success states. Require concrete findings and their reproductions. Earlier scoped reviewers reached account quota; parent checks are not independent sign-off.

The six-family fresh-packet protocol in the planning package remains an execution gate. Existing tuned scenarios and the new assistant-authored [trial kit](TRIAL-GUIDE.md) cannot be relabelled as independently held-out model validation. Second-person provider permissions, actual colleague observations, clean-source setup and the final live demo remain open.

Community sources inspected: [Your agent crashed after the write. Should you retry?](https://dev.to/fernando_azevedo_6844e930/your-agent-crashed-after-the-write-should-you-retry-232p) is an author-reported local SQLite lab, not proof of our integration; one inspected comment agrees that surviving evidence rather than a restarted process resolves ambiguity. [AI Agent Reconciliation: What to Do When a Tool Times Out After It May Have Succeeded](https://dev.to/jackm-singularity/ai-agent-reconciliation-what-to-do-when-a-tool-times-out-after-it-may-have-succeeded-442d) is design guidance with no inspected comments. These support testing lost acknowledgements and retaining uncertainty; they establish no community consensus or external certification.
