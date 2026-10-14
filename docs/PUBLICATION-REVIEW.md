# Publication review

Reviewed 14 October 2026, before external publication. Scope: source commit `b0d87f0730eb6a10b3ad3be4316e023152057e65` and the then-current `HandoffReady-reviewed-release.zip`. This review did not publish anything, modify services/user data, rerun the test suite or install/download a model.

## Assessment

No credential, client packet, application database, private browser/session link or missing compiled React redistribution notice was identified in the reviewed materials. One avoidable local-account path remains in a verification receipt and should be sanitized before publication. This is a bounded content review, not proof that every possible sensitive value or legal issue is absent.

## Concrete finding

**P2 — local-account path in release receipt.** `docs/final-release-checks.json:54` records the Python static-check tool as an absolute executable path beneath a user's home directory. This reveals unnecessary machine/account-directory metadata. Replace that command element with `uv` or a neutral local-tool placeholder; retain the actual check result. Rebuild the archive and its hash manifest from the corrected source. The finding does not identify an API key or client secret.

The report intentionally does not reproduce the account path. The reviewed commit and initial ZIP still contain it; a later source commit alone does not rewrite earlier Git history. Publishing the branch's complete history also publishes that historical receipt, although the exposed author/account metadata is not a credential.

## Archive and source identity

The ZIP has 161 file entries: the complete reviewed tracked source, compiled frontend assets/sample files and `PACKAGE-MANIFEST.json`. Every tracked source file in the reviewed commit matches its ZIP counterpart byte-for-byte. All 160 entries recorded by the package manifest match their recorded sizes and SHA-256 hashes. The initial reviewed ZIP SHA-256 is `74c33f80d4ed318518657e715629e170d36bd4349af27b3b6608afb7429a69b9`.

No installed Python/Node package tree, `.model`, `.runtime`, `.data`, `.venv`, `.git`, `node_modules`, `__pycache__`, key file, database or log is bundled. No source maps are included. Git history at this review contains one source commit; no earlier hidden runtime/data commit was identified.

## Public-content checks

- Scanned archived text/source for absolute user/system temporary paths, common access-key markers, literal credential fields, email addresses and private ChatGPT/plugin links. The only absolute local-account path match was the finding above. No matching secret marker, credential value, private session link or email address was found.
- Checked raw synthetic model diagnoses/evaluation receipts and their generating fixtures/protocols. They contain authored example briefs, generic documentation, synthetic injection probes, model outputs and measured provenance. They do not establish customer evidence; failure reports remain preserved and labelled separately from development regressions.
- Research/planning documents describe hypotheses, intended validation and public references. They do not include a customer contract, private source conversation, authenticated account receipt or private customer contact.
- Visually inspected the three published app screenshots and the planning preview. They show the synthetic Studio North packet or the explicitly labelled design prototype; no unrelated desktop, customer project, address, credential or private chat appears. Image metadata contains only ordinary JFIF properties, with no author/location/path payload identified.
- Author attribution in the project's MIT license is deliberate public attribution. Loopback service URLs, generic local-data-directory instructions, public upstream hashes and reported benchmark hardware are documented operational/provenance information, not authentication credentials.

## Redistribution and licensing

The release includes the project's MIT license, original-fixture CC0 designation and third-party notice table. Python installations, llama.cpp binaries and model weights are excluded; the project does not claim its MIT license replaces separately installed upstream terms.

For the compiled frontend, full upstream MIT copyright/permission/warranty text is present in `licenses/react-MIT.txt`, `licenses/react-dom-MIT.txt` and `licenses/scheduler-MIT.txt`, together with exact versions in `licenses/frontend-runtime-manifest.json`: React 19.3.0, React DOM 19.3.0 and scheduler 0.28.0. Each archived license text is byte-identical to the corresponding installed dependency license. The minified JS has no inline license header, so preserve the accompanying `licenses/` directory when distributing this compiled archive or any extracted application bundle. A future standalone web bundle should likewise keep its applicable notices available with its distribution.

The pinned [Google model card](https://huggingface.co/google/gemma-4-E2B-it/blob/3e22461f65e89153144f8adb70e3b8c2cc9845a7/README.md) and [Google license page](https://ai.google.dev/gemma/apache_2) identify Apache-2.0, consistent with the source's model attribution. The pinned ggml-org conversion card could not be reopened through the web tool during this review; its previously recorded provenance is retained, and no converted weight is distributed by this package. This review does not establish a complete chain of title for every upstream work.

## Publication boundary

A sanitized reviewed source release can support public code publication. It does not establish personal contest eligibility, an authentic first-user result, deployed-demo availability, broad security, general model accuracy or a winning outcome. Keep those claims bounded as the existing release documents do.

The initial source/archive identity and findings above apply to the stated reviewed artifacts. If publication preparation changes files or rebuilds the archive, record the new source identity and recheck the changed content/manifest instead of describing this report as verification of unseen bytes.

## Parent preparation addendum

The current executable command was sanitized to `uv` before the preparation update. Earlier b0d87f0 Git history retains the author-account path, as documented above; it was classified as public author/machine metadata rather than a credential/client secret. No Git history was rewritten or claimed to be purged. The original source is now public. A separate recheck covers new synthetic demo receipts/captures, which explicitly identify agent-operated decisions, and verifies no secret draft-preview URL is committed. Public video delivery matches its encoded SHA-256; the public watch page has no live backend access or client-data upload.
