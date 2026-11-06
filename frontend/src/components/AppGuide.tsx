export default function AppGuide() {
  return (
    <details className="app-guide" id="app-guide">
      <summary>How to use HandoffReady · User guide</summary>
      <div className="app-guide-content">
        <p className="eyebrow">YOUR BRIEF, YOUR FILES, YOUR FINAL SAY</p>
        <h2>What does this app do?</h2>
        <p>
          HandoffReady helps you check a web or design delivery before sharing
          it. Connect the agreed brief to the actual files, inspect supported
          technical facts, record your judgment and leave a clear delivery
          record. It does not certify design quality, test a live website or
          approve work on your behalf.
        </p>
        <p className="app-guide-example">
          <strong>Try this first:</strong> choose “Try the synthetic sample” on
          the home screen. It includes an opaque logo, duplicate artwork and an
          incomplete guide. Use it to practise finding issues without uploading
          your own files. The local model is optional; add checklist items
          manually if it is unavailable.
        </p>
        <ol className="app-guide-steps">
          <li>
            <h3>01 · Save the agreed brief</h3>
            <p>
              Create a named handoff, open Brief, give the source a label and
              paste the deliverables you agreed. Save the brief before moving
              on.
            </p>
          </li>
          <li>
            <h3>02 · Confirm the checklist</h3>
            <p>
              Add requirements manually or use the optional local AI to suggest
              them. Check every requirement, source quote, quantity and file
              format. Correct omissions, review the confirmation checkbox and
              confirm the checklist.
            </p>
          </li>
          <li>
            <h3>03 · Inspect the actual files</h3>
            <p>
              Add supported PNG, JPEG, SVG, readable PDF, TXT or Markdown files.
              Read inspection warnings and duplicate-byte findings. In a
              configured room, refresh received files, select the whole intended
              packet, preview its changes and confirm it.
            </p>
          </li>
          <li>
            <h3>04 · Make your review</h3>
            <p>
              Select the files for each requirement and preview the selection.
              Read the facts and inspect the content yourself. Choose Satisfied,
              Needs work, Not applicable or Unresolved, add your reason and save
              your review. Keep private reasoning separate from anything
              intended for the client.
            </p>
          </li>
          <li>
            <h3>05 · Prepare the handoff</h3>
            <p>
              Read the public preview, including remaining gaps. Export the
              record and send the original files separately. In a configured
              room, review the exact content and destination before authorizing
              one return; check the actual returned attachment and verify its
              downloaded bytes and destination.
            </p>
          </li>
        </ol>
        <details>
          <summary>How do Switch and the room agent help?</summary>
          <p>
            Once the owner has configured Switch, the room and its agent,
            mention that agent in the delivery channel with a non-confidential
            attachment or clarification. The agent can stage received files,
            propose source-linked questions and record replies. Review the
            original conversation locally before accepting a reply as context.
            The agent cannot confirm your scope or packet, save your assessment
            or verify a return for you. Keep Switch Console and its host
            available.
          </p>
        </details>
        <details>
          <summary>What happens when a delivery is corrected?</summary>
          <p>
            Review the complete replacement packet, retaining unchanged files
            you still intend to deliver. Changed inputs make earlier reviews
            stale. Recheck the current evidence and save a fresh review; old
            exported records stay unchanged. New room questions or replies may
            also require fresh context review and return authorization.
          </p>
        </details>
        <details>
          <summary>Why can’t I continue or share?</summary>
          <p>
            Follow the next-step message. Confirm the checklist, finish pending
            file/context reviews and inspect stale assessments. If a request
            times out, its outcome may be unknown: reconcile the same operation
            before retrying. If a send is uncertain, inspect the destination; do
            not send it again just to clear the warning. If the local service is
            unavailable, start the supported launcher and use Retry local
            connection.
          </p>
        </details>
        <details>
          <summary>Where does my information go?</summary>
          <p>
            The local desk stores evidence on this computer without encryption.
            Connected room messages, attachments and agent context may also be
            processed by your chat and AI providers. Use synthetic or authorized
            non-confidential files for practice. The exported Markdown record
            does not contain the original files; review all public wording
            before sharing.
          </p>
        </details>
        <a href="/setup.html" target="_blank" rel="noreferrer">
          Setup instructions and supported limits ↗
        </a>
      </div>
    </details>
  );
}
