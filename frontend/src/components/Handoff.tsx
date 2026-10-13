import { useEffect, useState } from "react";
import type { Project } from "../types";
import { readable, findingValue } from "../presentation";
import { api } from "../api";
interface ClientPreview {
  project_name: string;
  input_hash: string;
  status: string;
  scope_notice: string;
  gaps: { requirement_id: string; message: string }[];
  requirements: {
    id: string;
    title: string;
    review_state: string;
    human_disposition: string;
    client_usage_note: string;
    files: { id: string; name: string }[];
    checks: {
      kind: string;
      status: string;
      reason: string;
      expected?: unknown;
      actual?: unknown;
    }[];
    gaps: string[];
  }[];
}
export default function Handoff({
  project,
  disabled,
  exportNow,
  downloadFile,
}: {
  project: Project;
  disabled: boolean;
  exportNow: (ack: boolean) => void;
  downloadFile: (id: string, format: string) => void;
}) {
  const [ack, setAck] = useState(false),
    [preview, setPreview] = useState<ClientPreview | null>(null),
    [previewError, setPreviewError] = useState(""),
    [retry, setRetry] = useState(0);
  useEffect(() => {
    let current = true;
    setAck(false);
    setPreview(null);
    setPreviewError("");
    api<ClientPreview>(`/projects/${project.id}/handoff-preview`)
      .then((p) => {
        if (current) setPreview(p);
      })
      .catch((e) => {
        if (current) setPreviewError(e.message);
      });
    return () => {
      current = false;
    };
  }, [project.id, project.input_hash, project.revision, retry]);
  return (
    <section className="card">
      <p className="eyebrow">05 / THE CLIENT HANDOFF</p>
      <h2>A packet with a clear explanation.</h2>
      <p className="muted">
        Raw brief and private evidence fields stay out of the export. Approved
        requirement titles, check descriptions and client usage notes are
        shared; review them before sending. Unresolved items and technical
        mismatches remain visible.
      </p>
      <p className="note">
        The manifest explains the delivery. It does not contain the original
        files; send those files alongside it.
      </p>
      {previewError && (
        <div className="alert warning" role="alert">
          <p>{previewError}</p>
          <button disabled={disabled} onClick={() => setRetry((v) => v + 1)}>
            Retry preview
          </button>
        </div>
      )}
      {!preview && !previewError && (
        <p role="status">Preparing the current client preview…</p>
      )}
      {preview && (
        <div className="manifest-preview">
          <h3>{preview.project_name}</h3>
          <span className="badge neutral">{readable(preview.status)}</span>
          {preview.requirements.map((r) => (
            <article key={r.id}>
              <b>{r.title}</b>
              <span
                className={`badge ${r.human_disposition === "satisfied" ? "good" : "warning"}`}
              >
                {readable(r.human_disposition)} · {readable(r.review_state)}
              </span>
              <ul>
                {r.files.map((f) => (
                  <li key={f.id}>{f.name}</li>
                ))}
              </ul>
              {r.client_usage_note && <p>{r.client_usage_note}</p>}
              {r.checks.map((c, i) => (
                <p key={i} className="manifest-finding">
                  <span
                    className={`badge ${c.status === "pass" ? "good" : "warning"}`}
                  >
                    {readable(c.status)}
                  </span>{" "}
                  {c.reason}
                  {c.actual !== undefined && (
                    <> Observed: {findingValue(c.actual)}.</>
                  )}
                  {c.expected !== undefined && (
                    <> Expected: {findingValue(c.expected)}.</>
                  )}
                </p>
              ))}
              {r.gaps.map((g, i) => (
                <p className="warning" key={i}>
                  Unresolved: {g}
                </p>
              ))}
            </article>
          ))}
          <p className="fine">{preview.scope_notice}</p>
        </div>
      )}
      <label className="checkbox">
        <input
          type="checkbox"
          checked={ack}
          onChange={(e) => setAck(e.target.checked)}
          disabled={disabled || !preview}
        />
        I reviewed this preview and understand that any unresolved, manual or
        failed checks will remain in the export.
      </label>
      {!!preview?.gaps.length && (
        <p className="warning">
          {new Set(preview.gaps.map((g) => g.requirement_id)).size} item(s)
          still require attention or clarification.
        </p>
      )}
      <button
        className="primary"
        disabled={
          disabled ||
          !ack ||
          !preview ||
          preview.input_hash !== project.input_hash ||
          project.baseline.state !== "approved"
        }
        onClick={() => exportNow(ack)}
      >
        Prepare handoff snapshot →
      </button>
      {project.exports.length > 0 && (
        <section className="exports">
          <h3>Saved exports</h3>
          {project.exports.map((e) => (
            <div key={e.id}>
              <div className="snapshot-label">
                <code>{e.snapshot_hash?.slice(0, 12) || e.id.slice(0, 8)}</code>
                {e.created_at && (
                  <p className="fine">
                    Saved {new Date(e.created_at).toLocaleString()}
                  </p>
                )}
                {e.status && (
                  <span className="badge neutral">{readable(e.status)}</span>
                )}
                <p className="fine">
                  {e.preview?.input_hash === project.input_hash
                    ? "Same source and packet; saved reviews may differ."
                    : "Earlier source or packet."}{" "}
                  This snapshot does not update.
                </p>
              </div>
              {["md", "json", "html"].map((f) => (
                <button
                  key={f}
                  disabled={disabled}
                  onClick={() => downloadFile(e.id, f)}
                >
                  {f === "html"
                    ? "Print-ready HTML"
                    : f === "md"
                      ? "Markdown"
                      : "JSON"}{" "}
                  ↓
                </button>
              ))}
            </div>
          ))}
        </section>
      )}
    </section>
  );
}
