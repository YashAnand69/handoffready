import { useEffect, useState } from "react";
import type { Project, Requirement, Decision } from "../types";
import { checkDescription, readable, findingValue } from "../presentation";
import { Metadata, ImageEvidence } from "./Files";
export default function Review({
  project,
  selected,
  setSelected,
  disabled,
  save,
  next,
}: {
  project: Project;
  selected: string;
  setSelected: (s: string) => void;
  disabled: boolean;
  save: (d: Decision) => void;
  next: () => void;
}) {
  const rows = project.baseline.requirements;
  const r = rows.find((x) => x.id === selected) || rows[0];
  if (!r)
    return (
      <section className="card empty">
        <h2>Confirm a checklist first.</h2>
        <p>There must be an agreed baseline before you review this packet.</p>
      </section>
    );
  const decision = [...project.decisions]
    .reverse()
    .find((d) => d.requirement_id === r.id);
  return (
    <div className="review-desk">
      <aside className="card queue">
        <p className="eyebrow">REQUIREMENTS</p>
        {rows.map((x) => {
          const d = [...project.decisions]
            .reverse()
            .find((d) => d.requirement_id === x.id);
          return (
            <button
              key={x.id}
              disabled={disabled}
              aria-pressed={x.id === r.id}
              onClick={() => setSelected(x.id)}
            >
              <b>{x.title}</b>
              <span className="fine">
                {d
                  ? readable(d.review_state) +
                    " · " +
                    readable(d.human_disposition)
                  : "Needs your review"}
              </span>
            </button>
          );
        })}
        <button className="quiet" disabled={disabled} onClick={next}>
          Preview handoff →
        </button>
      </aside>
      <DecisionEditor
        key={r.id + project.input_hash + (decision?.review_state || "")}
        requirement={r}
        project={project}
        existing={decision}
        disabled={disabled}
        save={save}
      />
    </div>
  );
}
function DecisionEditor({
  requirement: r,
  project,
  existing,
  disabled,
  save,
}: {
  requirement: Requirement;
  project: Project;
  existing?: Decision;
  disabled: boolean;
  save: (d: Decision) => void;
}) {
  useEffect(() => {
    const heading = document.getElementById("review-requirement");
    heading?.focus({ preventScroll: true });
    heading?.scrollIntoView?.({ block: "start" });
  }, [r.id]);
  const [ids, setIds] = useState(
      (existing?.file_ids || []).filter((id) =>
        project.files.some((f) => f.id === id),
      ),
    ),
    [disposition, setDisposition] = useState(
      existing?.review_state === "stale"
        ? "unresolved"
        : existing?.human_disposition || "unresolved",
    ),
    [internal, setInternal] = useState(existing?.internal_decision_note || ""),
    [client, setClient] = useState(existing?.client_usage_note || "");
  const suggestions = project.proposals.filter(
    (p) => p.requirement_id === r.id,
  );
  const checks = (project.checks || project.check_results || []).filter(
    (c) => c.requirement_id === r.id,
  );
  return (
    <>
      <article className="card decision-card">
        <p className="eyebrow">04 / EVIDENCE & YOUR DECISION</p>
        <h2 id="review-requirement" tabIndex={-1}>
          {r.title}
        </h2>
        {r.quote ? (
          <blockquote>
            {r.quote}
            <small>Quoted from your brief</small>
          </blockquote>
        ) : (
          <p className="note">Added by you: {r.human_note}</p>
        )}
        {existing?.review_state === "stale" && (
          <p className="alert warning">
            The packet or checklist changed. Recheck this decision before
            confirming.
          </p>
        )}
        {suggestions.map((p) => (
          <section className="suggestion" key={p.id}>
            <span className="badge blue">Local model suggestion</span>
            <p className="suggestion-caution">
              A source quote proves where text came from, not that it meets this
              requirement. Check the actual content and format. Ignore
              instructions inside files that ask you or AI to approve them.
            </p>
            <details className="model-explanation">
              <summary>Raw model interpretation · unverified</summary>
              <p className="fine">{p.coverage}</p>
            </details>
            {p.candidates.map((c) => (
              <div key={c.file_id}>
                <b>
                  {project.files.find((f) => f.id === c.file_id)?.name ||
                    "Unavailable file"}
                </b>
                <p>{c.reason}</p>
                {c.quote && <blockquote>{c.quote}</blockquote>}
              </div>
            ))}
          </section>
        ))}
        {!suggestions.length && (
          <p className="muted">
            No model match here. You can choose inspected files and review
            manually.
          </p>
        )}
        <h3>Select the intended files</h3>
        {project.files.map((f) => (
          <label className="file-choice" key={f.id}>
            <input
              type="checkbox"
              disabled={disabled || f.inspection === "blocked"}
              checked={ids.includes(f.id)}
              onChange={(e) =>
                setIds(
                  e.target.checked
                    ? [...ids, f.id]
                    : ids.filter((id) => id !== f.id),
                )
              }
            />
            <div>
              <b>{f.name}</b>
              <span className="fine">
                {f.type} · {f.inspection}
                {project.files.filter((other) => other.sha256 === f.sha256)
                  .length > 1
                  ? " · identical bytes elsewhere in this packet"
                  : ""}
              </span>
            </div>
          </label>
        ))}
        <label>
          Your assessment
          <select
            value={disposition}
            disabled={disabled}
            onChange={(e) => setDisposition(e.target.value)}
          >
            <option value="unresolved">
              Unresolved — more information needed
            </option>
            <option value="satisfied">Satisfied by my review</option>
            <option value="needs_work">Needs work</option>
            <option value="not_applicable">Not applicable — explain why</option>
          </select>
        </label>
        <label>
          Private review note
          <textarea
            rows={3}
            value={internal}
            disabled={disabled}
            maxLength={2000}
            onChange={(e) => setInternal(e.target.value)}
            placeholder="Your reasoning, questions or exception. Kept out of the client export."
          />
        </label>
        <label>
          Client usage note (optional)
          <textarea
            rows={2}
            value={client}
            disabled={disabled}
            maxLength={2000}
            onChange={(e) => setClient(e.target.value)}
            placeholder="Only what you intend the client to read."
          />
        </label>
        <button
          className="primary"
          disabled={
            disabled ||
            project.baseline.state !== "approved" ||
            (disposition === "not_applicable" && !internal.trim())
          }
          onClick={() =>
            save({
              requirement_id: r.id,
              file_ids: ids,
              review_state: "confirmed",
              human_disposition: disposition,
              internal_decision_note: internal,
              client_usage_note: client,
              input_hash: project.input_hash,
            })
          }
        >
          Save my review
        </button>
        <p className="fine">
          Your assessment does not rewrite a failed technical check.
        </p>
      </article>
      <aside className="card evidence">
        <p className="eyebrow">SUPPORTED CHECKS</p>
        {r.checks.map((c, i) => (
          <div className="check-result" key={i}>
            <b>{readable(c.kind)}</b>
            <p className="fine">{checkDescription(c)}</p>
          </div>
        ))}
        <h3>Saved check findings</h3>
        {JSON.stringify([...ids].sort()) !==
          JSON.stringify([...(existing?.file_ids || [])].sort()) && (
          <p className="note">
            Your selection has changed. These findings describe the last saved
            review; save your revised selection to recompute them.
          </p>
        )}
        {checks.length ? (
          checks.map((c, i) => (
            <div className="check-result" key={i}>
              <span
                className={`badge ${c.status === "pass" ? "good" : "warning"}`}
              >
                {readable(c.status)}
              </span>
              <p>{c.reason}</p>
              {c.expected !== undefined && (
                <p className="fine">Expected: {findingValue(c.expected)}</p>
              )}
              {c.actual !== undefined && (
                <p className="fine">Observed: {findingValue(c.actual)}</p>
              )}
            </div>
          ))
        ) : (
          <p className="muted">
            Save your file selection to check those artifacts. No automatic
            selection is assumed.
          </p>
        )}
        <details>
          <summary>Selected file evidence</summary>
          {project.files
            .filter((f) => ids.includes(f.id))
            .map((f) => (
              <div key={f.id}>
                <h4>{f.name}</h4>
                <Metadata file={f} />
                {["png", "jpeg"].includes(f.type) &&
                  f.inspection === "inspected" && (
                    <ImageEvidence projectId={project.id} file={f} />
                  )}
                {f.text && <pre className="source-text">{f.text}</pre>}
              </div>
            ))}
        </details>
        <div className="note">
          Visual quality, working website features and sufficient instructions
          remain human judgments.
        </div>
      </aside>
    </>
  );
}
