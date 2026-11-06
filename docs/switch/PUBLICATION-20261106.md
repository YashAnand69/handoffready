# Source and public showcase — 6 November 2026

The user explicitly authorized GitHub publication and deployment, then selected Vercel and delegated the hosting decision. This supersedes the earlier source/website publication hold. The separate narrated video and contest submission remain held.

- Public source: https://github.com/YashAnand69/handoffready
- Integration branch: `feat/switch-delivery-room`; the same source was fast-forwarded to `main`, preserving the October history.
- Published implementation commit: `522f3d85f70d53a11237198270ac2a874f9c77b5`.
- Public showcase: https://handoffready-delivery-room.vercel.app
- Vercel production deployment: `dpl_4GzMA4Na6Yp8bCNKKnfA79NZS8k7`, reported READY.
- Deployment source is the `public-showcase` directory in the implementation commit. Vercel project: `handoffready-delivery-room`, existing owner team. No old project was removed and no paid resource was provisioned.

## What is hosted

A static project website with actual synthetic interface captures, interactive workflow explanations, source/setup links, dated evidence and limitations. Anonymous HTTP returned 200 for the production page, CSS, JavaScript and referenced image assets. Actual browser verification loaded the public page and changed the workflow panel to the correction stage.

The full local React/FastAPI application and Switch bridge are published as source, but are **not running on Vercel**. No owner's project database, originals, agent profile, credential or local service was uploaded or publicly proxied. The working desk still requires its supported local launcher, persistent storage and configured Switch/provider host. Python runtime support alone does not supply the application's persistent storage, single-owner process or local agent bridge. Vercel Functions also have a documented 4.5 MB request/response payload limit, below this app's supported packet budget. A hosted multi-user service needs a separately designed authentication, durable storage, upload and background-work contract.

## Publication checks

Before publication, the staged source was checked for credential patterns and forbidden private/runtime paths: no matches. The four supplied raw audit reports were retained locally, untracked; their reviewed per-claim dispositions were published instead. The optional local model, dependencies, installed runtimes and private execution data were excluded.

The complete backend rerun passed **541 tests**, with one existing dependency deprecation warning. The previously recorded interface run passed **146 tests**, plus type/build/format checks. Focused Ruff correctness checks and frontend dependency audit passed (zero reported vulnerabilities). Publication preparation cleaned unused imports and made pytest fixture re-exports explicit. One cleanup initially removed an indirectly used fixture import, causing six setup errors; the explicit re-export was restored, the eight recovery cases passed, then the complete 541-test run passed. No frozen historical evaluation was rewritten.

The final README/publication note is a documentation-only follow-up to the implementation commit. Read prior dated check receipts as historical, not as new deployment evidence. The actual source and website publication are not a new demo recording, external colleague trial, event submission, customer result or win.

## Updating the showcase

The initial deployment used the authenticated official Vercel CLI because the newly connected app lacked the owner's team grant. The existing CLI login refreshed successfully and had access to that same owner team. No additional team grant was required or created. This is a manual deployment; automatic Git deployment has not been configured.

From `public-showcase`, run the official Vercel CLI with `deploy --prod --scope yash-56e6`. Its ignored `.vercel` link is local state; a fresh checkout must link the existing project first. Never deploy the private execution folder. Website files require no dependency installation or build.

References: [Vercel Python runtime](https://vercel.com/docs/functions/runtimes/python), [Functions limits](https://vercel.com/docs/functions/limitations), [local audit checkpoint](AUDIT-POLISH-CHECKPOINT-20261106.md), [recording script](DEMO-RECORDING-SCRIPT.md).
