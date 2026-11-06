# Scoped supervised-return review — 6 November 2026

Scope: `delivery_share.py`, `delivery_share_api.py`, delivery route authentication, `scripts/delivery_tools.py`, `DeliveryShare.tsx`, and their focused tests. Read repository instructions and Stage4/5 contracts. Inspected source and executed only synthetic/disposable checks. No live database/configuration, credentials, server, external messaging, or human trial was accessed or changed. This is not a whole-product or release signoff.

## Confirmed finding and authorized correction

**P1: a cleared context hold restored an earlier share authorization without fresh consent.** The original share authority digest covered input hash, project name and saved decisions but omitted durable context epochs. Questions and their dismissal can advance epoch while leaving all project JSON and review hashes unchanged. Consequently, the current-hold check blocked an old intent only temporarily.

Executed reproduction, before correction, using a disposable TestClient/SQLite packet:

1. Save current human review and authorize a frozen return.
2. Propose a new question, then locally dismiss it.
3. Issue the old intent using its original artifact SHA.
4. Observed dismissal HTTP200 and `send_permitted:true`; the old intent became `issued_unverified` without a fresh share decision.

The parent explicitly authorized a minimal correction in the share module and focused tests. New intent bodies now retain the project-wide `context_epochs` snapshot, and preview hashes include that snapshot. Current authorization requires both the original review authority digest and exact durable epochs. A later question, current reply or historical late reply therefore requires a fresh preview/authorization even after all holds clear. The existing review authority digest still controls duplicate-return risk, preserving the warning when the same review was previously issued. References: `backend/handoffready/delivery_share.py:65`, `:82`, `:164`, `:244`; regressions at `tests/test_delivery_share.py:209`.

Compatibility is deliberately conservative. Existing bodies without `context_epochs` are retained unchanged; unissued authorizations are superseded and cannot materialize or issue. Already issued/confirmed records keep their recorded state, exact export bytes and local verification path, but are labelled historical (`is_current:false`). Existing authorization replay returns its original operation receipt; current history still marks its intent superseded. Issue replay still returns `send_permitted:false` and no send arguments. No schema/table/export rewrite was introduced. Compatibility regressions: `tests/test_delivery_share.py:255`. An older application binary that omits the epoch check does not preserve this new safety rule; this review does not establish downgrade safety.

## Other inspected boundaries

- Local-only authorization, cancellation and verification remain outside the agent allowlist. Agent material/issue calls still enforce configured job binding and fixed destination. Review confirmation is strict; multipart verification accepts only the file and bounded metadata fields. Source: `delivery_api.py:85`, `delivery_share_api.py:46`.
- Issue consumption, event and operation receipt share one SQLite transaction. Concurrent/replayed issue cannot grant another permission. Actual external sending remains outside this transaction and is deliberately unverified until local inspection. Recovery tests exercise process termination before/after commits, not power-loss durability.
- The command bridge checks frozen filename/hash/size, confines output to the owner-private root, rejects unsafe collisions, and does not call Switch or retry an ambiguous send. Same-user unrestricted-shell isolation remains the explicit product limitation.
- UI unknown results retain their operation key/payload through refresh/remount. Success depends on authoritative history refresh. Reopened verification requires selecting the actual file again. Private context/source/assessment prose remains excluded from the frozen export projection and agent status in the exercised checks.

No additional concrete authorization, replay, privacy or recovery defect was established within this bounded pass. This does not assert that all possible concurrency or filesystem races were exhaustively tested.

## Executed evidence

- Pre-correction focused backend suite: **48 passed** (`test_delivery_share.py`, `test_delivery_share_tools.py`, `test_delivery_share_recovery.py`). This passing baseline did not cover the confirmed epoch gap.
- Added five meaningful cases: question→dismiss, reply→dismiss, historical late reply, and legacy issued/unissued compatibility. The epoch cases assert unchanged project JSON, stale preview refusal, old intent/material refusal, preserved replay, and successful freshly authorized issue.
- Final affected backend suite after correction: **53 passed**, one existing Starlette/httpx deprecation warning; about14.5seconds.
- `npm test -- --run src/DeliveryShare.test.tsx`: **11 passed**. UI source was not changed by this correction.

The Stage4/5 automated evidence above does not substitute for a supervised real return/download, independent transport verification, a second-person trial, or full product acceptance. The epoch/legacy behavior should be reflected in the parent-maintained Stage4 contract/implementation notes before final release review.
