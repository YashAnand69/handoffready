import SourceEvidence from "./SourceEvidence";
import { api } from "../api";
import { useEffect, useState, useRef } from "react";
import type { Project, Requirement, Decision, CheckResult } from "../types";
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
  save: (d: Decision, advance?: boolean) => void;
  next: () => void;
}) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const rows = project.baseline.requirements;
  const queueState = (id: string) => {
    const summary = project.attention_summary?.rows.find(
      (row) => row.requirement_id === id,
    );
    const decision = [...project.decisions]
      .reverse()
      .find((item) => item.requirement_id === id);
    const current = summary
      ? summary.review_currency === "current"
      : decision?.review_state === "confirmed" &&
        decision.input_hash === project.input_hash;
    const disposition =
      summary?.human_disposition ?? decision?.human_disposition;
    return {
      needsReview: !current,
      needsWork: current && disposition === "needs_work",
    };
  };
  const matches = rows.filter((row) => {
    const state = queueState(row.id);
    return (
      row.title
        .toLocaleLowerCase()
        .includes(query.trim().toLocaleLowerCase()) &&
      (filter === "all" ||
        (filter === "review" ? state.needsReview : state.needsWork))
    );
  });
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
        <div className="review-queue-tools">
          <label>
            Find a requirement
            <input
              type="search"
              value={query}
              onChange={(event) => {
                event.stopPropagation();
                setQuery(event.target.value);
              }}
              placeholder="Search checklist…"
            />
          </label>
          <div
            className="review-queue-filters"
            role="group"
            aria-label="Filter requirements"
          >
            {[
              ["all", "All"],
              ["review", "Needs review"],
              ["work", "Needs work"],
            ].map(([value, label]) => (
              <button
                key={value}
                className="quiet"
                aria-pressed={filter === value}
                onClick={() => setFilter(value)}
              >
                {label}
              </button>
            ))}
          </div>
          <p className="fine" role="status">
            {matches.length} of {rows.length} match
          </p>
          {(query || filter !== "all") && (
            <button
              className="quiet"
              onClick={() => {
                setQuery("");
                setFilter("all");
              }}
            >
              Clear filters
            </button>
          )}
        </div>
        {!matches.some((row) => row.id === r.id) && (
          <p className="queue-current-note note">
            Your current item is outside this filter. It stays open so your
            edits are preserved.
          </p>
        )}
        {!matches.length && (
          <p className="fine">
            No requirements match. Clear the filters to see the full checklist.
          </p>
        )}
        {rows
          .filter(
            (row) =>
              matches.some((match) => match.id === row.id) || row.id === r.id,
          )
          .map((x) => {
            const d = [...project.decisions]
              .reverse()
              .find((d) => d.requirement_id === x.id);
            const facts = (
              project.checks ||
              project.check_results ||
              []
            ).filter((c) => c.requirement_id === x.id && c.kind !== "manual");
            const rowState = project.attention_summary?.rows.find(
              (row) => row.requirement_id === x.id,
            );
            const reviewLabel = rowState
              ? rowState.review_currency === "current"
                ? "confirmed · " + readable(rowState.human_disposition)
                : rowState.review_currency === "stale"
                  ? "Stale · needs fresh review"
                  : "Needs your review"
              : d
                ? d.input_hash !== project.input_hash
                  ? "Stale · needs fresh review"
                  : readable(d.review_state) +
                    " · " +
                    readable(d.human_disposition)
                : "Needs your review";
            const failed =
              rowState?.failed_check_count ??
              facts.filter((c) => c.status === "fail").length;
            const unknown =
              rowState?.unknown_check_count ??
              facts.filter((c) => c.status === "unknown").length;
            return (
              <button
                key={x.id}
                aria-label={x.title + " " + reviewLabel}
                disabled={disabled}
                aria-pressed={x.id === r.id}
                onClick={() => setSelected(x.id)}
              >
                <b>{x.title}</b>
                <span className="fine">{reviewLabel} </span>
                <span
                  className={`queue-facts ${failed || unknown ? "warning" : "muted"}`}
                >
                  {failed
                    ? `${failed} technical failure(s)`
                    : unknown
                      ? `${unknown} unavailable check(s)`
                      : facts.length
                        ? "Saved narrow checks pass"
                        : "No automated findings"}
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
interface DraftCheckPreview {
  preview: true;
  project_id: string;
  requirement_id: string;
  source_revision: number;
  input_hash: string;
  file_ids: string[];
  selection_hash: string;
  checks: CheckResult[];
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
  save: (d: Decision, advance?: boolean) => void;
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
      existing &&
        (existing.review_state !== "confirmed" ||
          existing.input_hash !== project.input_hash)
        ? "unresolved"
        : existing?.human_disposition || "unresolved",
    ),
    [internal, setInternal] = useState(existing?.internal_decision_note || ""),
    [client, setClient] = useState(existing?.client_usage_note || ""),
    [exception, setException] = useState(existing?.client_exception_note || "");
  const [fileQuery, setFileQuery] = useState("");
  const visibleFiles = project.files.filter(
    (file) =>
      ids.includes(file.id) ||
      file.name
        .toLocaleLowerCase()
        .includes(fileQuery.trim().toLocaleLowerCase()),
  );
  const selection = [...ids].sort();
  const selectionKey = JSON.stringify(selection);
  const previewContext = JSON.stringify([
    project.id,
    project.revision,
    project.input_hash,
    r.id,
    selectionKey,
  ]);
  const contextRef = useRef(previewContext);
  contextRef.current = previewContext;
  const requestRef = useRef({ sequence: 0, pendingContext: "", mounted: true });
  const [draftPreview, setDraftPreview] = useState<{
    context: string;
    result?: DraftCheckPreview;
    error?: string;
    pending?: boolean;
  } | null>(null);
  useEffect(() => {
    requestRef.current.mounted = true;
    return () => {
      requestRef.current.mounted = false;
      requestRef.current.sequence += 1;
    };
  }, []);
  const visiblePreview =
    draftPreview?.context === previewContext ? draftPreview : null;
  async function previewSelection() {
    if (requestRef.current.pendingContext === previewContext) return;
    const ticket = ++requestRef.current.sequence;
    const context = previewContext;
    requestRef.current.pendingContext = context;
    setDraftPreview({ context, pending: true });
    const current = () =>
      requestRef.current.mounted &&
      requestRef.current.sequence === ticket &&
      contextRef.current === context;
    try {
      const result = await api<DraftCheckPreview>(
        `/projects/${project.id}/requirements/${r.id}/check-preview`,
        "POST",
        { file_ids: selection, input_hash: project.input_hash },
        project.revision,
      );
      if (!current()) return;
      if (
        result.preview !== true ||
        result.project_id !== project.id ||
        result.requirement_id !== r.id ||
        result.source_revision !== project.revision ||
        result.input_hash !== project.input_hash ||
        JSON.stringify([...result.file_ids].sort()) !== selectionKey
      ) {
        setDraftPreview({
          context,
          error:
            "This selection preview is out of date. Request it again for your current selection.",
        });
      } else setDraftPreview({ context, result });
    } catch (error) {
      if (current())
        setDraftPreview({
          context,
          error:
            (error as Error).message +
            " Your draft and saved findings are unchanged. Save or discard your edits before refreshing the handoff if its inputs changed.",
        });
    } finally {
      if (requestRef.current.sequence === ticket)
        requestRef.current.pendingContext = "";
    }
  }
  const suggestions = project.proposals.filter(
    (p) => p.requirement_id === r.id,
  );
  const checks = (project.checks || project.check_results || []).filter(
    (c) => c.requirement_id === r.id,
  );
  const reviewDisabled =
    disabled ||
    project.baseline.state !== "approved" ||
    (disposition === "not_applicable" && !internal.trim());
  const submit = (advance = false) =>
    save(
      {
        requirement_id: r.id,
        file_ids: ids,
        review_state: "confirmed",
        human_disposition: disposition,
        internal_decision_note: internal,
        client_usage_note: client,
        client_exception_note:
          disposition === "not_applicable" ? exception : "",
        input_hash: project.input_hash,
      },
      advance,
    );
  return (
    <>
      <article className="card decision-card">
        <p className="eyebrow">04 / EVIDENCE & YOUR DECISION</p>
        <h2 id="review-requirement" tabIndex={-1}>
          {r.title}
        </h2>
        {r.quote ? (
          <SourceEvidence
            quote={r.quote}
            span={r.source_span}
            text={project.brief?.text}
            label="Quoted from your brief"
            unitId={r.evidence_unit_id}
          />
        ) : (
          <p className="note">Added by you: {r.human_note}</p>
        )}
        {existing &&
          (existing.review_state === "stale" ||
            existing.input_hash !== project.input_hash) && (
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
                {c.quote ? (
                  <SourceEvidence
                    quote={c.quote}
                    span={c.source_span}
                    text={project.files.find((f) => f.id === c.file_id)?.text}
                    label="Candidate file source"
                    unitId={c.evidence_unit_id}
                  />
                ) : (
                  <p className="fine">
                    Metadata/name suggestion only; file content has not been
                    assessed by AI.
                  </p>
                )}
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
        <div className="review-file-tools">
          <label>
            Find a delivery file
            <input
              type="search"
              value={fileQuery}
              placeholder="Search filenames…"
              onChange={(event) => {
                event.stopPropagation();
                setFileQuery(event.target.value);
              }}
            />
          </label>
          <p className="fine">
            {ids.length} selected · {visibleFiles.length} of{" "}
            {project.files.length} shown. Selected files stay visible.
          </p>
          {fileQuery && (
            <button className="quiet" onClick={() => setFileQuery("")}>
              Clear file search
            </button>
          )}
        </div>
        {!visibleFiles.length && (
          <p className="fine">No files match this search.</p>
        )}
        {visibleFiles.map((f) => (
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
        <section
          className="review-evidence"
          aria-label="Evidence for this review"
        >
          <p className="eyebrow">SUPPORTED CHECKS</p>
          {r.checks.map((c, i) => (
            <div className="check-result" key={i}>
              <b>{readable(c.kind)}</b>
              <p className="fine">{checkDescription(c)}</p>
            </div>
          ))}
          <section
            className="draft-check-preview"
            aria-label="Unsaved selection preview"
          >
            <h3>Unsaved selection preview</h3>
            <p className="fine">
              Check the files selected in this draft without saving a review.
              Preview findings do not change your assessment, readiness, or
              exported record.
            </p>
            <button
              disabled={
                disabled ||
                project.baseline.state !== "approved" ||
                !!visiblePreview?.pending
              }
              onClick={previewSelection}
            >
              {visiblePreview?.pending
                ? "Checking selected files…"
                : "Preview selected files"}
            </button>
            {visiblePreview?.pending && (
              <p role="status" className="fine">
                Checking this unsaved selection…
              </p>
            )}
            {visiblePreview?.error && (
              <p role="alert" className="warning">
                {visiblePreview.error}
              </p>
            )}
            {visiblePreview?.result && (
              <div>
                <p className="fine" role="status">
                  Preview only · {selection.length} selected file(s) · revision{" "}
                  {visiblePreview.result.source_revision}
                </p>
                <FindingList checks={visiblePreview.result.checks} />
              </div>
            )}
          </section>
          <h3>Saved check findings</h3>
          {JSON.stringify([...ids].sort()) !==
            JSON.stringify([...(existing?.file_ids || [])].sort()) && (
            <p className="note">
              Your selection has changed. These findings describe the last saved
              review; save your revised selection to recompute them.
            </p>
          )}
          {checks.length ? (
            <FindingList checks={checks} />
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
        </section>
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
        {disposition === "not_applicable" && (
          <section
            className="exception-editor"
            aria-label="Public scope exception"
          >
            <span className="badge warning">Reviewer scope exception</span>
            <p className="fine">
              This excludes the item from this delivery by your assessment. It
              does not establish client agreement or erase technical findings.
            </p>
            <label>
              Client-facing exception explanation (public)
              <textarea
                rows={3}
                value={exception}
                disabled={disabled}
                maxLength={2000}
                onChange={(e) => setException(e.target.value)}
                placeholder="Explain only what the client should read. Private notes are never copied here."
              />
            </label>
            {!exception.trim() && (
              <p className="warning">
                Without a public explanation, the delivery record remains a
                draft with gaps.
              </p>
            )}
          </section>
        )}
        <label>
          Private review note
          <textarea
            rows={3}
            value={internal}
            disabled={disabled}
            maxLength={2000}
            onChange={(e) => setInternal(e.target.value)}
            placeholder="Your reasoning and questions. Kept out of the client export."
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
        <div className="review-save-actions actions">
          <button
            className="primary"
            disabled={reviewDisabled}
            onClick={() => submit()}
          >
            Save my review
          </button>
          <button disabled={reviewDisabled} onClick={() => submit(true)}>
            Save and next item →
          </button>
        </div>
        <p className="fine">
          Your assessment does not rewrite a failed technical check.
        </p>
      </article>
    </>
  );
}

function FindingList({ checks }: { checks: CheckResult[] }) {
  return (
    <>
      {checks.map((c, i) => (
        <div className="check-result" key={i}>
          <span
            className={`badge ${c.kind === "manual" ? "neutral" : c.status === "pass" ? "good" : "warning"}`}
          >
            {c.kind === "manual" ? "Human judgment" : readable(c.status)}
          </span>
          <p>{c.reason}</p>
          {c.expected !== undefined && (
            <p className="fine">Expected: {findingValue(c.expected)}</p>
          )}
          {c.actual !== undefined && (
            <p className="fine">Observed: {findingValue(c.actual)}</p>
          )}
        </div>
      ))}
    </>
  );
}
