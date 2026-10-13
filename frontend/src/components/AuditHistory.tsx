import { useState } from "react";
import { api } from "../api";
import { readable } from "../presentation";
interface History {
  baseline_history: {
    baseline?: { state: string; requirements: { title: string }[] };
    source?: { label: string; text: string };
    reason?: string;
    created_at?: string;
  }[];
  proposal_history: unknown[];
  decision_history: {
    requirement_id: string;
    review_state: string;
    human_disposition: string;
    internal_decision_note: string;
    client_usage_note: string;
  }[];
}
export default function AuditHistory({ projectId }: { projectId: string }) {
  const [history, setHistory] = useState<History | null>(null),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(false);
  async function load() {
    setLoading(true);
    setError("");
    try {
      setHistory(await api<History>(`/projects/${projectId}/audit-history`));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }
  return (
    <div className="audit-history">
      <button disabled={loading} onClick={load}>
        {loading ? "Loading history…" : "View private audit history"}
      </button>
      <p className="fine">
        Prior source and review versions are private. They are not included in
        client manifests. History is capped; this is not an original-file
        backup.
      </p>
      {error && (
        <p className="warning" role="alert">
          {error}
        </p>
      )}
      {history && (
        <>
          <p>
            {history.baseline_history.length} earlier source/checklist versions
            · {history.proposal_history.length} earlier suggestion batches ·{" "}
            {history.decision_history.length} earlier reviews
          </p>
          {history.baseline_history.map((entry, i) => (
            <details key={i}>
              <summary>
                Source/checklist version {i + 1}
                {entry.reason ? ` · ${readable(entry.reason)}` : ""}
              </summary>
              {entry.source && (
                <>
                  <b>{entry.source.label}</b>
                  <pre className="source-text">{entry.source.text}</pre>
                </>
              )}
              {entry.baseline?.requirements.map((r, j) => (
                <p key={j}>{r.title}</p>
              ))}
            </details>
          ))}
          {history.decision_history.map((d, i) => (
            <details key={i}>
              <summary>
                Earlier review {i + 1} · {readable(d.human_disposition)}
              </summary>
              <p>Mapping state: {readable(d.review_state)}</p>
              {d.internal_decision_note && (
                <p>Private note: {d.internal_decision_note}</p>
              )}
              {d.client_usage_note && (
                <p>Previous client usage note: {d.client_usage_note}</p>
              )}
            </details>
          ))}
        </>
      )}
    </div>
  );
}
