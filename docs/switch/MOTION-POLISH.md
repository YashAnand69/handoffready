# Interface motion and surface polish — 6 November 2026

This scoped pass changes only `frontend/src/style.css`, the existing `frontend/src/useEntranceMotion.ts` helper and its new focused test file. No API, application workflow, review/approval action, packet, source evidence, live data or account state was changed. The existing App hook call remains sufficient; no App wiring change is needed.

## Visible changes

- The existing warm paper/forest palette gains quiet card surfaces, a slightly deeper focus-within shadow, restrained interactive-card lift and immediate button press feedback. Noninteractive content does not gain a pointer cursor or exaggerated lift.
- The home `primary-link` now receives the existing solid primary-action treatment. Record return `checkline` labels now share the checkbox layout, readable weight and minimum 44px label target, with a visible keyboard focus boundary.
- Returned records have visible separation, digest treatment and adjacent-card spacing. Source/file disclosure summaries gain small color feedback; open disclosure boundaries remain explicit.
- The mobile Review queue always stacks its search, filters and requirement buttons at 700px and below. Buttons use the available width without forcing a 170px horizontal strip or depending on `:has` support.
- Scroll entry uses a small 8px translation and 0.88→1 opacity over 320ms, with no delay. New workflow/context cards mounted after the first render are discovered as well as dashboard panels. The short decorative headline entry is retained with a readable start; status/error/live announcements and sticky navigation are excluded from observer reveals.

These are presentation changes. They do not make an unresolved record ready, submit a form, change a selection or supply an assessment.

## Critical reading of the supplied reports

The missing `.checkline` and `.primary-link` treatments were confirmed against current markup and repaired by supporting those classes in CSS, without changing component contracts.

The reports correctly identify old `.queue-search` / `.queue-filters` names that do not match the current `review-queue-tools` / `review-queue-filters` markup. Their blanket claim that the current queue is broken on every mobile viewport overstates this snapshot: a later existing `:has(.review-queue-tools)` override already stacks it in supporting browsers. This pass removes the contradictory dead selectors and makes stacking the unconditional mobile baseline. It is a robustness/readability repair; no claim of reproducing an absent universal breakage is made.

Other report proposals, including allowing navigation to interrupt unknown room mutations, are outside this presentation scope. No busy-lock bypass, automatic timeout release, new LAN mode or guessed external-link policy was added by this pass. Functional review belongs to the separate implementation owner.

## Motion safety and fallback

Readable CSS is the default. The helper never sets a hidden class, inline opacity, `visibility:hidden`, `display:none`, `inert` or pointer-blocking style. Without JavaScript, animation support, IntersectionObserver or a positively matched `prefers-reduced-motion: no-preference`, content remains at its ordinary visible position. If the browser refuses an animation, the effect catches that failure without affecting the workflow.

IntersectionObserver replaces scroll-position polling. MutationObserver watches only added/removed content below the existing workspace, so async room cards and new step panels can be discovered without rerendering the app. Each node reveals once. Removed nodes are unobserved; completed/cancelled animations leave no retained transform or opacity. There is no animation library, continuous loop, parallax, scroll listener, scroll hijack, delayed control enablement or layout-property animation.

A panel already containing focus is skipped. If focus or pointer interaction enters an animating panel, that decoration is cancelled immediately and focus is left where the browser/user placed it. Live preference changes disconnect observers and cancel running decoration when reduced motion is requested; switching back can discover eligible unrevealed panels. Unmount/location change clears observers/listeners/animations.

CSS decorative animations are opt-in under `prefers-reduced-motion: no-preference`. The reduced-motion rule also suppresses hover/active transforms, so controls do not jump when CSS transitions are disabled. Focus outlines and busy/status text stay visible independent of animation.

## Verification performed

The new `useEntranceMotion.test.tsx` focused run passed **8 tests**, covering:

1. Visible, enabled controls before observation, bounded nonblocking reveal and once-only behavior.
2. Reduced/unknown preference remains still.
3. Missing observation/animation APIs retain readable content.
4. Newly mounted workflow/context panels are discovered.
5. Focused panels are skipped; entering keyboard focus cancels a running effect and remains unchanged.
6. Pointer interaction and live reduced-motion preference cancel decoration.
7. Unmount cleans up pending observers/listeners/animations.
8. Browser animation refusal remains a readable, usable fallback.

The initial production build of this scoped source passed using the installed Node 24. A later concurrent build/format attempt encountered `ApiAudit.test.ts` unknown-type/format issues owned by the functional agent; those were reported rather than edited here. After that agent repaired them and this motion source was frozen, its final integrated run passed **146 tests across 13 files**, the TypeScript/Vite production build and full frontend formatting. That final agent run reported the existing Node 20.18 support warning; it is not a newly installed or recommended runtime. The supported documented build runtime remains Node 24 (or Node 22.12+). No duplicate integrated run was performed by this motion owner.

Focused tests use jsdom and browser API doubles. They validate lifecycle/interaction contracts, not visual smoothness, actual browser rendering, physical mobile operation or assistive-technology certification. Parent browser QA remains the check for actual home/Review/Handoff layout, keyboard use and reduced-motion presentation. No claim of that visual pass is made by this document.

## Community input inspected

Two DEV author accounts informed the failure cases, with both comment threads inspected and empty. This is a narrow evidence base, not consensus or a substitute for the checks above.

- [You're Animating for Everyone. `prefers-reduced-motion` Fixes That.](https://dev.to/parsajiravand/youre-animating-for-everyone-prefers-reduced-motion-fixes-that-2ond), by [@parsajiravand](https://dev.to/parsajiravand), argues for stillness as the default and positive motion opt-in; this pass uses that gating for observer effects.
- [How an Accessibility SaaS Broke Its Own Landing (and How We Fixed It)](https://dev.to/lawebe/how-an-accessibility-saas-broke-its-own-landing-and-how-we-fixed-it-5802), by [@lawebe](https://dev.to/lawebe), reports reveal content left invisible for reduced-motion users. This pass avoids hidden base styles entirely rather than adopting its code example without verification.

No dependency installation, new provider, live send, commit or publication was performed.
