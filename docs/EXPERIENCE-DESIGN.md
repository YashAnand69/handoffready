# HandoffReady experience design

This upgrade gives the local delivery workspace a coherent visual identity and clearer work hierarchy. The design applies to the real React application; it does not introduce a hosted model or change the meaning of review status.

## Visual foundation

Warm ivory (`#f7f5f0`) provides the working canvas, near-white paper (`#fffef9`) holds editable content, dark ink (`#202b27`) is the primary text, and forest green (`#345c47`) marks actions and selection. Restrained copper (`#976044`) distinguishes introductory labels. Amber remains reserved for unresolved findings and scope exceptions; green technical checks do not change human review semantics.

Georgia gives headings an editorial character. System sans-serif labels and form controls stay compact and familiar. These local font stacks need no external font requests. Corners use 7–14px radii; borders and low-opacity shadows separate surfaces without deep floating panels.

## Hierarchy and usability

The dashboard pairs a focused project introduction with the original brief/files/reviewer/handoff diagram. The immediate next choices are to create a project or try the synthetic sample. Saved projects are distinct clickable rows with adequate target size. Three short workflow principles explain the workflow beneath these actions.

An open project uses a compact header, sticky five-step navigation, a narrow next-action strip and a working surface. The review layout pairs the requirement queue with the editable decision. Supporting facts sit immediately before the assessment, so narrow check failures are encountered before the reviewer saves a judgment. Selected file rows have explicit border and background changes while preserving checkboxes and labels. Sources, model suggestions, technical checks and reviewer decisions retain different visual treatments.

The client record uses spacious paper styling, a legible inventory and separately disclosed exceptions. Saved records and downloads retain their existing content and privacy behavior.

## Responsive behavior

At wide desktop sizes review has two columns: a searchable requirement queue and the decision surface, with evidence embedded before the assessment. Below 1100px the queue narrows. Below 700px all working panels stack. The five workflow controls remain visible across a 320px screen; file selectors wrap; file names and identities break safely. New dashboard content stacks on narrow screens. The small-screen queue becomes a vertical list when search/filter controls are present, so its controls are not hidden in horizontal overflow.

## Interaction and accessibility

Buttons, checkbox label regions, disclosures and file chooser buttons have at least 44px interaction height. Keyboard focus uses a visible 2px green outline. Motion is limited to 160ms hover/focus transitions and a 200–220ms entrance; there is no perpetual diagram motion competing with review work. Reduced-motion preference disables all transitions and animation. No content is hidden pending a scroll animation.

## Verification boundaries

The parent integration review must verify actual desktop and mobile rendering after all component changes land. CSS design intent does not certify contrast, physical device behavior or assistive-technology compatibility. Automated application tests and a browser walkthrough remain separate evidence. No new customer usage or contest outcome is claimed.
