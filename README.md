# HandoffReady

A local delivery desk for web and design freelancers: turn an agreed brief into a reviewed checklist, inspect the files you intend to deliver, review evidence, and prepare a clear client manifest.

**Tested full-stack local release.** Real Gemma inference, the supported file workflow and client exports work on the tested Mac. A genuine first-user trial and public submission remain pending. Read [stage reviews](docs/STAGE-REVIEWS.md) and [model evidence](docs/MODEL-EVIDENCE.md) for verified status. Synthetic examples are not customer results.

## What it does

1. Save an English text brief. Local model extraction can propose requirements with exact quotations; you may also add explained manual items.
2. Edit and explicitly confirm the checklist. Model suggestions never approve it.
3. Bring bounded PNG, JPEG, safe SVG metadata, native readable PDF, TXT and Markdown files.
4. Review proposed matches against inspected evidence. Choose files yourself and record your assessment separately from technical check results.
5. Preview the client projection and export an immutable JSON, Markdown or print-ready HTML snapshot. Private notes and raw brief fields are omitted. Approved titles, check descriptions and deliberate client notes are shared; review their content before sending. Failed, stale and unresolved checks remain visible.

Changes to the brief, checklist or packet invalidate current mapping reviews. A filename or different file hash never proves quality or a distinct design. The app does not execute websites, certify client acceptance, judge visual quality or send files to clients.

## Local setup

Requirements: Python 3.12, Node.js 22.12+/24+, approximately 8 GB free disk for the Mac model/build tools, and an Apple Silicon Mac for the tested model installation path. The compiled runtime/model capability is documented separately; other operating systems are not yet validated.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-backend.lock
npm ci --prefix frontend
npm run build --prefix frontend
.venv/bin/python scripts/start.py
```

Open http://127.0.0.1:8877/. Select **Try the synthetic sample** to exercise an imperfect original packet. Manual checklists, file inspection, review and export work without the model server; use the launcher without `--with-model` for that mode. The interface shows when real inference is unavailable.

Free model installation is an explicit network download from pinned official sources. See the installer options before running:

```sh
.venv/bin/python scripts/prepare_model.py --help
```

If source compilation is needed, install CMake into the isolated tools directory first: `.venv/bin/python -m pip install --target .runtime/build-tools cmake==4.1.2`. Apple command-line build tools are required. Run `.venv/bin/python scripts/prepare_model.py` for explicit setup, then stop any manual app instance and run `.venv/bin/python scripts/start.py --with-model`. The installer verifies hashes and builds the pinned llama.cpp runtime on this tested Mac when the official binary cannot be downloaded, and stores ignored artifacts in `.model/` and `.runtime/`. It does not purchase anything, accept terms or upload client files. Runtime/model licenses are separate from this project's MIT license.

## Development and verification

```sh
PYTHONPATH=backend .venv/bin/python -m pytest -q
npm test --prefix frontend
npm run build --prefix frontend
npm audit --prefix frontend
```

Run `npm run dev --prefix frontend` for the local development interface (port 5174, proxying the backend). Keep one backend process; multiple workers are unsupported. The API's synthetic model doubles verify workflow invariants only; real model performance has its own benchmark script and receipts.

## Privacy and boundaries

Data defaults to `~/Library/Application Support/HandoffReady`, with owner-only permissions. Override `HANDOFFREADY_DATA` to use a dedicated local directory. Local storage is not encrypted by this app; use your device protections and avoid confidential material in demonstrations. Browser draft text is version-bound and cleared after a successful save or project deletion.

The service binds loopback, protects private reads with a session token, checks Origin on writes and uses project revision guards. Parser work runs in bounded subprocesses. These are practical local controls, not a claim of perfect sandbox isolation or a security audit. No remote AI API, account or telemetry is required. Model setup needs internet; normal supported use is local after setup.

Limits include 30 files, 50 MiB per packet, 10 MiB per file, 10 PDF pages, 10 million image pixels, 20,000 brief characters and 20 requirements. Larger or unsupported work fails explicitly. Files such as ZIP, PSD, Office documents, encrypted/scanned PDFs and animated images are outside the current scope.

## Evidence and documentation

- [PRD](docs/PRD.md) and [TRD](docs/TRD.md)
- [Complete original planning package](docs/planning/MASTER-PLAN.md), including data/API, UI, QA, release risks and essential skills
- [Implementation plan](docs/IMPLEMENTATION-PLAN.md)
- [Actual build contract](docs/BUILD-CONTRACT.md)
- [Backend scope and review findings](docs/BACKEND-IMPLEMENTATION-NOTES.md)
- [Full-stack release and run guide](docs/FULL-STACK-RELEASE.md)
- [Stage reviews](docs/STAGE-REVIEWS.md)
- [Final rules and judging review](docs/FINAL-RULES-REVIEW.md), [correctness review](docs/FINAL-CORRECTNESS-REVIEW.md), and [usability review](docs/FINAL-USABILITY-REVIEW.md)
- [Final local verification receipt](docs/final-release-checks.json)
- [Unpublished DEV submission draft](docs/DEV-SUBMISSION-DRAFT.md)
- [Model provenance and measured evidence](docs/MODEL-EVIDENCE.md)
- [First-user trial guide](docs/USER-TRIAL.md)
- [Third-party notices](THIRD-PARTY-NOTICES.md)

The user's role includes choosing the audience/problem, arranging authentic feedback, reviewing the workflow and deciding what should be delivered. AI assistance is disclosed; no human-only authorship, real customer benefit or contest result is claimed.

## Verified local checkpoint

137 Python tests and 31 interface tests passed, plus strict TypeScript/production build, formatting and focused Python correctness checks. Real v10 API extraction/matching and seven supported workflow/restart stages passed; see `docs/workflow-verification-release-reviewed.json`. Initial failures and independent synthetic model mistakes remain preserved. Model interpretation is not guaranteed: review every checklist, format and content association. The sampled model runs do not establish general accuracy or prompt-injection robustness.
