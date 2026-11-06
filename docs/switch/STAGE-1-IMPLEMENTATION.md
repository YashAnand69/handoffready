# Delivery Room: implementation checkpoint

Historical Stage1 checkpoint; the current [Stage2 implementation](STAGE-2-IMPLEMENTATION.md) and machine-readable verification supersede its test counts.

4 November 2026. This document describes executable work in this branch, not a completed contest entry.

## Implemented and checked

- A delivery job permanently binds one configured Switch server/room/thread to one existing project. The assistant cannot choose a destination in its tool arguments.
- New versioned SQLite tables preserve existing project and export table layouts. Pending bytes live outside the originals directory.
- Operations record a payload fingerprint and result together. Repeated keys return the committed result; conflicting reuse is refused. A later project revision does not cause an already completed operation to execute twice.
- Staged attachments have count, byte and operation budgets. Missing, changed or symlinked staged bytes are reported as unavailable independently of the historical receipt. A failed disk write does not commit a receipt.
- The agent-facing API exposes status and provisional selection checks. It reconciles original files, enforces the exact revision/hash, and cannot save a human assessment or authorize a record share.
- Status identifies the next actor and distinguishes scope review, missing packet, damaged evidence, correction, stale review and readiness to prepare a record.
- Status omits brief/file text, private review notes, source literal expectations, manual instruction text and local file paths. Approved checklist titles, filenames, numeric inspection metadata, identifiers and review counts are visible. Use synthetic data for the current integration spike.
- A small standard-library MCP stdio adapter exposes exactly `delivery_status` and `delivery_check_preview`. It rejects arbitrary URLs, paths, unknown tools, extra arguments, redirects and proxy configuration. Its documented protocol subset is not a claim of full MCP conformance or actual Switch interoperability.
- Delivery routes are disabled unless explicitly configured. A separate private configuration file enables them without editing the user's global provider settings.

## Verification

Latest backend run after the private adapter-configuration and CLI-command extensions: **364 tests passed**. The earlier frontend checkpoint remains **75 existing tests passed**, production build and formatting passed, and npm dependency audit reported zero vulnerabilities; frontend code has not changed since that checkpoint. One existing Starlette/httpx deprecation warning remains. These are code checks, not a security certification or product validation. [Recorded check scope](verification-20261104.json).

`tests/test_delivery_roundtrip.py` starts an actual local server with disposable storage and drives the stdio process over HTTP into SQLite. It creates a synthetic checklist, finds a missing guide, adds a correction, refuses the old preview, checks the new packet, verifies that no human assessment was saved by a tool, refuses an unresolved record, then exercises the local assessment/export path. It also tests duplicate job creation after later changes. All roles in this test are automated fixtures, not people.

Other tests cover binding refusal, narrow credentials, privacy projections, migration preservation/newer-schema refusal, concurrent duplicate intake, restart survival, missing/tampered originals, missing/tampered staging, and disk failure.

`tests/test_delivery_scenarios.py` exercises the five-file agency packet through the actual parsers and scoped preview routes: three PNG names versus two unique hashes, wrong dimensions, an irrelevant guide, a readable one-page PDF and corrected replacements. Technical passes still leave manual judgments unknown. An additional case checks that an explicit scope exception preserves failed technical facts without incorrectly asking for a correction that the reviewer has already excluded.

## Safe local setup

The inherited app starts normally with delivery routes disabled. To opt in, pass `--delivery-config /absolute/path/to/private-config.json` to `scripts/start.py`, alongside an isolated `--data-dir` and an available `--port`.

The JSON file contains `binding_id`, `server`, `room`, optional `thread`, and `token`. The token must be a freshly generated random secret. The file must be a regular file owned by the operator, at an absolute path, with permissions 600; symlink, public-readable, oversized, duplicate-key and malformed files are refused. Keep it outside the repository. Never put a real credential into an example, chat message, screenshot or Git.

The local operator creates a job through `POST /api/v1/delivery/jobs` with `project_id` and `operation_key`, using the normal local session credential and origin. This is not an agent tool. The result supplies the job ID.

The stdio process runs `scripts/delivery_tools.py` with these environment variables:

| Variable | Meaning |
| --- | --- |
| `HANDOFFREADY_DELIVERY_ORIGIN` | Exact loopback HTTP origin, including port |
| `HANDOFFREADY_DELIVERY_BINDING` | Configured binding ID |
| `HANDOFFREADY_DELIVERY_TOKEN` | Separate delivery credential |

Alternatively, pass `--config-file /absolute/path/to/private-client.json`. The adapter accepts only a bounded, owner-private regular JSON file with schema version 1 and the origin, binding and token fields; symlinks, duplicate keys, malformed values and unsafe permissions are refused. This keeps credentials out of command-line arguments. Use an absolute Python interpreter and script path. A project-scoped MCP configuration remains a Codex prototype. After the Codex usage limit, the restored `handoffready-yash` uses Antigravity and the tested CLI mode; its actual status invocation inside Switch is verified. This is not native custom MCP.

This is a lead-operated local service. The scoped tool list is a product contract, not isolation from an assistant that also has unrestricted same-user shell/network access. The usual local bootstrap remains available to local processes. No remote/multiuser authentication claim is made.

## Gates still open

The owner-operated Discord message route and a synthetic attachment round trip are independently verified. The downloaded returned file is byte-for-byte equal to the 109-byte original; see [Discord evidence](DISCORD-TRIAL-SETUP.md). This is not the full business workflow or a colleague trial.

1. The restored `handoffready-yash` Antigravity agent has completed a real scoped CLI status call in its Console direct chat and joined the existing Discord room. Its dedicated-agent room attachment/correction loop remains to verify; the earlier helper file round trip is separate evidence.
2. Second-person addressing/access configuration and an actual second account/device.
3. Explicit complete-packet confirmation/replacement, meaningful contextual clarification and corrected packet through that room.
4. A local share preview, frozen export plus share intent, supervised artifact return and honest send reconciliation.
5. Genuine freelancer trial, offline/reconnect check, a second differently composed packet, measured human effort and final demo.

Do not describe the foundation tests as those completed gates. Do not publish a simulated collaboration as a user trial.

## Provider-compatible command bridge

The same adapter also supports `--call-tool delivery_status` or `--call-tool delivery_check_preview`, with exactly one bounded JSON arguments object on standard input and the existing private configuration. It reuses the same tool validation and scoped client, returns structured JSON, and exits 0 for success, 1 for service failure, 2 for invalid input/configuration. It is a command-tool/CLI bridge, not native custom MCP. Unknown options and remote errors do not echo arbitrary arguments or credentials. The 74-test targeted adapter/HTTP/SQLite rehearsal and 364-test full backend suite passed. A parent-run call into the live synthetic job returned scope_review; actual invocation by the restored Switch-managed Antigravity agent is now verified in its Console direct chat.

Switch Console0.40.1 reports Antigravity Installed/Signed in and Ready after the official ACP1.1.1 setup. The earlier Codex agent received the test but hit its account usage limit before tool execution; the user accidentally deleted it, and the replacement uses Antigravity. No payment, account change or usage-limit workaround was attempted.
