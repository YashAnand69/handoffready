import { useEffect, useState } from "react";
import AttentionOverview, { deliveryLabel } from "./AttentionOverview";
import type { Project, AttentionSummary } from "../types";
import { readable, findingValue, bytes } from "../presentation";
import { api } from "../api";
interface ClientPreview {
  project_name: string;
  schema_version?: number;
  source_revision?: number;
  attention_summary?: AttentionSummary;
  files?: {
    id: string;
    name: string;
    type?: string;
    size?: number;
    sha256?: string;
  }[];
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
    client_exception_note?: string;
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
  review,
}: {
  project: Project;
  disabled: boolean;
  exportNow: (ack: boolean, previewRevision?: number) => void;
  downloadFile: (id: string, format: string) => void;
  review?: (id: string) => void;
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
        if (current) {
          if (
            p.input_hash !== project.input_hash ||
            (p.source_revision !== undefined &&
              p.source_revision !== project.revision)
          ) {
            setPreviewError(
              "The delivery preview is out of date. Retry before preparing a snapshot.",
            );
          } else setPreview(p);
        }
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
      <p className="eyebrow">05 / THE CLIENT DELIVERY RECORD</p>
      <h2>A clear record of this delivery.</h2>
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
          <div className="record-identity">
            <span
              className={`badge ${preview.status === "reviewed" ? "neutral" : "warning"}`}
            >
              {deliveryLabel(preview.status)}
            </span>
            <span className="fine">
              Live preview · revision{" "}
              {preview.source_revision ?? project.revision}
            </span>
          </div>
          {preview.attention_summary && (
            <AttentionOverview
              summary={preview.attention_summary}
              disabled={disabled}
              review={review}
            />
          )}
          <details className="record-input-identity">
            <summary>Source and packet identity</summary>
            <code className="source-identity">{preview.input_hash}</code>
            <p className="fine">
              This identifies the saved inputs. A review change can produce a
              new revision without changing those inputs.
            </p>
          </details>
          <p className="record-originals">
            <b>Send the original files alongside this record.</b> The record
            contains explanations and file identities, not your delivery file
            bytes.
          </p>
          {!!preview.files?.length && (
            <section className="record-inventory">
              <h3>Delivery file inventory</h3>
              <ul>
                {preview.files.map((f) => (
                  <li key={f.id}>
                    <b>{f.name}</b>
                    <span className="fine">
                      {f.type && readable(f.type)}
                      {f.size !== undefined ? ` · ${bytes(f.size)}` : ""}
                    </span>
                    {f.sha256 && (
                      <details>
                        <summary>File identity</summary>
                        <code className="source-identity">
                          SHA-256 {f.sha256}
                        </code>
                      </details>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          )}
          <h3>Requirement-by-requirement record</h3>
          {preview.requirements.map((r) => (
            <article key={r.id}>
              <b>{r.title}</b>
              <span
                className={`badge ${r.human_disposition === "satisfied" && r.review_state === "confirmed" ? "neutral" : "warning"}`}
              >
                Human assessment: {readable(r.human_disposition)} ·{" "}
                {readable(r.review_state)}
              </span>
              <ul>
                {r.files.map((f) => (
                  <li key={f.id}>{f.name}</li>
                ))}
              </ul>
              {r.human_disposition === "not_applicable" && (
                <div className="record-exception">
                  <b>Reviewer scope exception</b>
                  <p>
                    {r.client_exception_note ||
                      "No public exception explanation has been provided."}
                  </p>
                </div>
              )}
              {r.client_usage_note && <p>{r.client_usage_note}</p>}
              {r.checks.map((c, i) => (
                <p key={i} className="manifest-finding">
                  <span
                    className={`badge ${c.kind === "manual" ? "neutral" : c.status === "pass" ? "good" : "warning"}`}
                  >
                    {c.kind === "manual"
                      ? "Human judgment"
                      : readable(c.status)}
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
              {!!r.gaps.length && review && (
                <button
                  className="quiet"
                  disabled={disabled}
                  onClick={() => review(r.id)}
                >
                  Return to review: {r.title} →
                </button>
              )}
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
          (preview.source_revision !== undefined &&
            preview.source_revision !== project.revision) ||
          project.baseline.state !== "approved"
        }
        onClick={() => {
          if (preview) exportNow(ack, preview.source_revision);
        }}
      >
        Prepare handoff snapshot →
      </button>
      {project.exports.length > 0 && (
        <section className="exports">
          <h3>Saved exports</h3>
          {[...project.exports].reverse().map((e, index) => (
            <div key={e.id}>
              <div className="snapshot-label">
                <strong>
                  {index === 0
                    ? "Latest saved client record"
                    : "Earlier saved record"}
                </strong>
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
              {["html", "md", "json"].map((f) => (
                <button
                  key={f}
                  className={f === "html" && index === 0 ? "primary" : ""}
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
