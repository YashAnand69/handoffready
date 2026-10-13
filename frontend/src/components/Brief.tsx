import { useState } from "react";
import type { Project } from "../types";
export default function Brief({
  project,
  disabled,
  ready,
  save,
  extract,
}: {
  project: Project;
  disabled: boolean;
  ready: boolean;
  save: (text: string, label: string) => void;
  extract: () => void;
}) {
  const key = `handoff-brief-${project.id}-${project.brief?.sha256 || "new"}`;
  const [text, setText] = useState(() => {
      try {
        return localStorage.getItem(key) || project.brief?.text || "";
      } catch {
        return project.brief?.text || "";
      }
    }),
    [label, setLabel] = useState(project.brief?.label || "Agreed brief"),
    [draftWarning, setDraftWarning] = useState("");
  function edit(v: string) {
    setText(v);
    try {
      localStorage.setItem(key, v);
    } catch {
      setDraftWarning(
        "Draft could not be saved in this browser. Save the brief before leaving.",
      );
    }
  }
  return (
    <section className="card form-card">
      <p className="eyebrow">01 / WHAT YOU AGREED</p>
      <h2>Start with the source.</h2>
      <p className="muted">
        Paste the brief you intend to use. Confirm the resulting requirements
        yourself; AI cannot verify client approval.
      </p>
      {project.brief &&
        (text !== project.brief.text || label !== project.brief.label) && (
          <p className="note">
            You are editing an unsaved source. Saving changed source text or
            label resets the confirmed checklist and makes existing reviews
            stale; prior versions remain in private history. Suggestions use the
            saved source until you save.
          </p>
        )}
      <label htmlFor="brief-label">Source label</label>
      <input
        disabled={disabled}
        id="brief-label"
        value={label}
        onChange={(e) => setLabel(e.target.value)}
        maxLength={120}
      />
      <label htmlFor="brief-text">Agreed brief</label>
      <textarea
        disabled={disabled}
        id="brief-text"
        rows={10}
        value={text}
        onChange={(e) => edit(e.target.value)}
        placeholder="Deliverables, expected formats, sizes, and handover instructions…"
      />
      <p className="fine">
        {Array.from(text).length.toLocaleString()} / 20,000 characters. Pasted
        text first; scanned documents are not supported.
      </p>
      {draftWarning && (
        <p role="status" className="warning">
          {draftWarning}
        </p>
      )}
      <div className="actions">
        <button
          className="primary"
          disabled={disabled || !text.trim() || Array.from(text).length > 20000}
          onClick={() => save(text, label)}
        >
          Save brief & continue →
        </button>
        {project.brief && (
          <button
            disabled={
              disabled ||
              !ready ||
              text !== project.brief.text ||
              project.baseline.state === "approved"
            }
            onClick={extract}
          >
            Suggest checklist with local AI
          </button>
        )}
      </div>
    </section>
  );
}
