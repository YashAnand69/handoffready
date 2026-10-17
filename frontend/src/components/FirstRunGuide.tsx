export default function FirstRunGuide() {
  return (
    <details className="first-run-guide">
      <summary>First time here? Choose a starting point</summary>
      <div className="first-run-options">
        <article>
          <span className="eyebrow">EXPLORE WITHOUT YOUR FILES</span>
          <h3>Try an imperfect delivery.</h3>
          <p>
            Use the synthetic sample above. Compare the logo, launch images and
            guide against the brief, then decide what still needs work.
          </p>
          <p className="fine">
            A demonstration, not a real client project. You can review manually
            without waiting for AI.
          </p>
        </article>
        <article>
          <span className="eyebrow">BRING A REAL TASK</span>
          <h3>Start small.</h3>
          <p>
            Create a handoff with a short agreed brief and a few
            non-confidential files. Confirm the checklist, inspect the evidence
            and export your record.
          </p>
          <p className="fine">
            Send original files separately. Nothing is sent to your client by
            this app.
          </p>
        </article>
      </div>
      <div className="scope-boundary">
        <strong>A delivery-file review, not a website audit.</strong>
        <p>
          Checks cover supported file formats, dimensions, duplicate bytes and
          other selected properties. They do not test live links, forms,
          accessibility, deployment or design quality. AI suggestions can be
          wrong or incomplete; you confirm scope and judge whether the actual
          content meets it.
        </p>
        <a href="/quick-start.html" target="_blank" rel="noreferrer">
          Read the short walkthrough and limits ↗
        </a>
      </div>
    </details>
  );
}
