# Contributing to HandoffReady

HandoffReady is an original local delivery review desk. Contributions should improve supported freelancer tasks without turning model suggestions into approval or expanding unsupported security claims. Discuss substantive scope changes in a GitHub issue before investing in them. Existing issues and pull requests should be checked for overlap.

## Set up and validate

Use Python 3.12 and Node.js 22.12+ or 24+. Follow the [README setup](README.md#run-locally). Manual workflows do not require model installation. Work with a disposable dedicated data directory and synthetic fixtures; never use another person's saved projects for tests.

```sh
PYTHONPATH=backend .venv/bin/python -m pytest -q
npm test --prefix frontend
npm run build --prefix frontend
npm run format:check --prefix frontend
npm audit --prefix frontend
```

Focused Python lint uses the CI-pinned Ruff version: `ruff check --select F,E9 backend scripts tests`. The broader codebase is not represented as clean under every Ruff rule. Local frontend development uses port 5174 and the default backend proxy; production frontend is served by the backend. Keep one backend process per data directory.

## Preserve the contracts

- Treat upload bytes, brief text, filenames and model output as untrusted input. Keep parser, text, job, token and output bounds explicit; reject excessive inputs rather than silently truncating them.
- Keep source evidence bound to document identity, full-text digest, exact Unicode code-point range and literal text. Repeated wording must identify its actual occurrence. Exact quotations establish location, not semantic correctness.
- Keep file inspection, model associations and human assessment separate. Model proposals never auto-select files, confirm scope or approve delivery. Manual checks must remain labeled human judgments.
- Changed inputs invalidate current reviews. No-op saves must preserve their currency. Unsaved previews cannot mutate decisions or authorize a later export.
- Retain failed/unavailable findings for reviewer exclusions. Never copy private reasons into public explanations or describe an exclusion as verified client agreement.
- Verify original byte identity before authoritative actions. Timestamps or sizes alone cannot stand in for hashes. Polling optimizations must preserve these boundaries.
- Derive readiness and all export formats from the shared server contract. Keep output escaped, bounded and free of remote assets. Preserve historic stored exports byte-for-byte.
- Preserve dirty drafts, visible keyboard focus, meaningful labels, responsive layouts and reduced-motion behavior. Do not introduce scroll hijacking or simulated success states.

## Regression coverage and model evidence

Add focused tests for observable behavior, particularly source forgery/ambiguity, stale reviews, original replacement/tampering, exception handling, privacy and immutable snapshots. Declare model doubles explicitly. Do not pass a fake-model test off as real inference.

Actual-model evaluation has a separate freeze protocol. Do not alter a held-out key, prompt or threshold in response to its predictions and then present the result as an unchanged first run. Retain failed attempts and raw/guarded outcomes. Run new real-model evaluations only with deliberate local setup and a distinct evidence path.

## Pull requests

Use a contribution branch and a focused PR. Explain the concrete problem, resulting behavior, validation actually performed and remaining limitations. Mention affected data/legacy behavior. Include genuine screenshots for UI changes when useful. Avoid unrelated formatting churn or splitting one logical fix into multiple PRs.

Disclose material AI assistance and retain required third-party notices. Do not claim human-only authorship, unperformed testing, customer validation or legal acceptance. No proprietary client files, database contents, browser tokens, keys, weights, runtimes or installed dependencies belong in Git. Public synthetic fixtures need clear rights and provenance.

Publication, contest submission, provider purchases and external outreach are separate actions requiring owner authorization. Read-only DEV dashboard inspection on 17 October confirmed HandoffReady article 6228689 remains a draft. The user subsequently requested submission that evening. Keep one current publication status in `docs/SUBMISSION-STATUS-CURRENT.md`; do not create a duplicate entry. Building or reviewing a PR does not lift that hold.

## Evidence before release

Apply the Week 1 lessons in `docs/WEEK1-POSTMORTEM-AND-WEEK2-RESPONSE.md`:

- Start from one user task and its usable output. Automated test counts and subjective scores do not establish demand or model usefulness.
- Freeze the final candidate before recording; identify the source and fixtures. Any later UI change requires checking whether screenshots and video still represent it.
- Keep one current submission-status record. Reconcile code, article, media, measurements and public links before calling the entry ready. Historical receipts keep their dates and scope.
- Record one actual failure, its user consequence and verified correction. Retain residual failures; never manufacture an all-green story.
- Use genuine user feedback when available, with consent. A missing trial remains missing; do not let it prevent completing other authorized release preparation.
- Check final public links/media from a reader's perspective after an authorized release. A successful local build does not establish public availability.
