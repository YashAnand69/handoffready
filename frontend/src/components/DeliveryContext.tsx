import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api";
import type { CheckResult, Project } from "../types";
import "../delivery-context.css";

type Reply = {
  reply_id: string;
  source_ref: string;
  reported_speaker: string;
  text: string;
  text_hash: string;
  created_at: string;
};
type Resolution = {
  resolution_id: string;
  action: string;
  reason: string;
  covered_reply_ids: string[];
  used_reply_ids: string[];
  created_at: string;
};
type Question = {
  question_id: string;
  requirement_id: string;
  question: string;
  source_ref: string;
  source_revision: number;
  input_hash: string;
  source_hash: string | null;
  file_ids: string[];
  evidence: CheckResult[];
  legacy: boolean;
  state: "pending" | "resolved" | "superseded";
  active_context: {
    used_reply_ids?: string[];
    used_replies?: {
      reply_id: string;
      text_hash: string;
      source_ref: string;
    }[];
  } | null;
  replies: Reply[];
  latest_resolution: Resolution | null;
};
type Context = {
  job_id: string;
  source_revision: number;
  input_hash: string;
  context_epoch: number;
  questions: Question[];
};
type Action = "accept" | "dismiss" | "withdraw";
type Operation = {
  project_id: string;
  job_id: string;
  question_id: string;
  payload: {
    operation_key: string;
    expected_revision: number;
    input_hash: string;
    expected_context_epoch: number;
    action: Action;
    covered_reply_ids: string[];
    used_reply_ids: string[];
    reason: string;
    confirmed_reviewed: true;
  };
};
type Draft = { used: string[]; reason: string; reviewed: boolean };
const blankDraft = (): Draft => ({ used: [], reason: "", reviewed: false });
const storageKey = (id: string) => `handoff-context-operation-${id}`;
const ids = (value: unknown): value is string[] =>
  Array.isArray(value) &&
  value.length <= 200 &&
  value.every((entry) => typeof entry === "string") &&
  new Set(value).size === value.length;
function pendingOperation(id: string): Operation | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(storageKey(id)) || "null");
    const payload = value?.payload;
    if (
      value?.project_id === id &&
      typeof value.job_id === "string" &&
      typeof value.question_id === "string" &&
      typeof payload?.operation_key === "string" &&
      Number.isSafeInteger(payload.expected_revision) &&
      typeof payload.input_hash === "string" &&
      Number.isSafeInteger(payload.expected_context_epoch) &&
      ["accept", "dismiss", "withdraw"].includes(payload.action) &&
      ids(payload.covered_reply_ids) &&
      ids(payload.used_reply_ids) &&
      typeof payload.reason === "string" &&
      payload.reason.length <= 1000 &&
      payload.confirmed_reviewed === true
    )
      return value;
  } catch {
    // Browser storage is optional; this mount still retains the same operation.
  }
  return null;
}
const definiteRefusals = new Set([
  "invalid_fields",
  "delivery_invalid_input",
  "revision_conflict",
  "delivery_input_conflict",
  "delivery_context_conflict",
  "delivery_reply_set_conflict",
  "delivery_question_historical",
  "delivery_legacy_dismiss_only",
  "delivery_operation_conflict",
  "delivery_operation_limit",
  "delivery_result_limit",
  "delivery_resolution_limit",
  "baseline_not_approved",
  "storage_limit",
]);

export default function DeliveryContext({
  project,
  disabled,
  hasUnsaved = false,
  onCommitted,
  onBusy,
  onChecklist,
}: {
  project: Project;
  disabled: boolean;
  hasUnsaved?: boolean;
  onCommitted: () => Promise<unknown>;
  onBusy: (value: boolean) => void;
  onChecklist: () => void;
}) {
  const [context, setContext] = useState<Context | null>(null);
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [pending, setPending] = useState(() => pendingOperation(project.id));
  const mounted = useRef(false);
  const lock = useRef(false);
  const sequence = useRef(0);
  const busyCallback = useRef(onBusy);
  busyCallback.current = onBusy;
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      sequence.current++;
      busyCallback.current(false);
    };
  }, []);

  async function load() {
    const ticket = ++sequence.current;
    const result = await api<{ enabled: boolean; job: Context | null }>(
      `/projects/${project.id}/delivery-context`,
    );
    if (!mounted.current || ticket !== sequence.current) return false;
    setEnabled(result.enabled);
    setContext(result.job);
    setDrafts((previous) =>
      Object.fromEntries(
        (result.job?.questions || [])
          .filter((question) => previous[question.question_id])
          .map((question) => {
            const old = previous[question.question_id];
            // Keep authored text/selection, but fresh authority always requires
            // rechecking sources after a revision, reply or epoch refresh.
            const replyIds = new Set(
              question.replies.map((reply) => reply.reply_id),
            );
            return [
              question.question_id,
              {
                ...old,
                used: old.used.filter((id) => replyIds.has(id)),
                reviewed: false,
              },
            ];
          }),
      ),
    );
    return true;
  }
  useEffect(() => {
    let active = true;
    void load()
      .catch((failure: Error) => {
        if (active && mounted.current) setError(failure.message);
      })
      .finally(() => {
        if (active && mounted.current) setLoading(false);
      });
    return () => {
      active = false;
    };
    // The parent keys this component by project to isolate pending responses.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [project.id, project.revision, project.input_hash]);

  function remember(value: Operation | null) {
    setPending(value);
    try {
      if (value)
        sessionStorage.setItem(storageKey(project.id), JSON.stringify(value));
      else sessionStorage.removeItem(storageKey(project.id));
    } catch {
      // Keep the operation in memory if storage is unavailable.
    }
  }
  async function act(action: () => Promise<void>) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    onBusy(true);
    setError("");
    setMessage("");
    try {
      await action();
    } catch (failure) {
      if (mounted.current) setError((failure as Error).message);
    } finally {
      lock.current = false;
      if (mounted.current) {
        setBusy(false);
        busyCallback.current(false);
      }
    }
  }
  async function resolve(question?: Question, action?: Action) {
    if (!pending && (!context || !question || !action)) return;
    const draft = question
      ? drafts[question.question_id] || blankDraft()
      : null;
    if (!pending && !draft?.reviewed) return;
    const operation: Operation = pending || {
      project_id: project.id,
      job_id: context!.job_id,
      question_id: question!.question_id,
      payload: {
        operation_key: crypto.randomUUID(),
        expected_revision: context!.source_revision,
        input_hash: context!.input_hash,
        expected_context_epoch: context!.context_epoch,
        action: action!,
        covered_reply_ids: question!.replies.map((reply) => reply.reply_id),
        used_reply_ids: action === "accept" ? [...draft!.used] : [],
        reason: draft!.reason.trim(),
        confirmed_reviewed: true,
      },
    };
    remember(operation);
    try {
      const result = await api<{
        state: string;
        result?: { question_id?: string };
      }>(
        `/delivery/jobs/${operation.job_id}/questions/${operation.question_id}/resolve`,
        "POST",
        operation.payload,
      );
      if (
        result?.state !== "succeeded" ||
        result.result?.question_id !== operation.question_id
      )
        throw new Error(
          "The context result could not be confirmed. Reconcile the same decision before continuing.",
        );
    } catch (failure) {
      if (
        mounted.current &&
        failure instanceof ApiError &&
        definiteRefusals.has(failure.code)
      ) {
        remember(null);
        setDrafts((previous) =>
          Object.fromEntries(
            Object.entries(previous).map(([id, draft]) => [
              id,
              { ...draft, reviewed: false },
            ]),
          ),
        );
      }
      throw failure;
    }
    if (!mounted.current) return;
    // Both authoritative views must refresh before announcing a saved result.
    await onCommitted();
    if (!mounted.current) return;
    if (!(await load()))
      throw new Error(
        "Context refresh was interrupted. Reconcile the same decision to check its result.",
      );
    if (!mounted.current) return;
    remember(null);
    setDrafts((previous) => {
      const next = { ...previous };
      delete next[operation.question_id];
      return next;
    });
    setMessage(
      "Context decision recorded. Review current evidence in the desk; no human assessment, checklist approval or share authorization was saved.",
    );
  }
  function update(id: string, patch: Partial<Draft>) {
    setDrafts((old) => ({
      ...old,
      [id]: { ...(old[id] || blankDraft()), ...patch },
    }));
    setMessage("");
  }
  if (loading)
    return (
      <p className="fine" role="status">
        Checking room context…
      </p>
    );
  if (!context && !error && !pending) return null;
  const blocked = disabled || busy || !enabled || hasUnsaved;
  const locked = blocked || !!pending;
  const count =
    context?.questions.filter((q) => q.state === "pending").length || 0;
  return (
    <section
      className="card delivery-context"
      aria-label="Room context review"
      onChange={(event) => event.stopPropagation()}
    >
      <p className="eyebrow">FROM YOUR DELIVERY ROOM</p>
      <h2>Review the conversation context.</h2>
      <p>
        Questions and replies are unverified room records. Check their sources
        before using them as context. Technical findings are provisional; a
        context decision saves no human assessment or checklist approval.
      </p>
      {hasUnsaved && (
        <p className="warning" role="status">
          Save or discard your unsaved editor changes before refreshing or
          deciding room context.
        </p>
      )}
      {enabled === false && (
        <p className="warning" role="status">
          Delivery integration is disabled. Retained questions and safety holds
          remain in effect. Context decisions are unavailable until it is
          enabled.
        </p>
      )}
      {error && (
        <p className="warning" role="alert">
          {error}
        </p>
      )}
      {message && (
        <p className="note" role="status">
          {message}
        </p>
      )}
      {pending && (
        <div className="note" role="status">
          <strong>A context decision is waiting for reconciliation.</strong>
          <p>
            Its reply or refresh may have been interrupted. Retry the same
            decision to check its stored result. Keep this browser tab until it
            is resolved.
          </p>
          <button disabled={blocked} onClick={() => void act(() => resolve())}>
            {busy ? "Checking context…" : "Reconcile the same decision"}
          </button>
        </div>
      )}
      {!context && (
        <button
          className="quiet"
          disabled={disabled || busy || hasUnsaved}
          onClick={() =>
            void act(async () => {
              await onCommitted();
              await load();
            })
          }
        >
          Refresh room context
        </button>
      )}
      {context && (
        <>
          <p className="fine" role="status">
            {count} pending question{count === 1 ? "" : "s"}. Each pending
            question keeps the delivery on hold until explicitly resolved or
            superseded by a real source change.
          </p>
          <div className="actions">
            <button
              className="quiet"
              disabled={locked}
              onClick={() =>
                void act(async () => {
                  await onCommitted();
                  await load();
                })
              }
            >
              Refresh room context
            </button>
            <button
              className="quiet"
              disabled={disabled || busy || !!pending}
              onClick={onChecklist}
            >
              Changes checklist →
            </button>
          </div>
          <p className="fine">
            Changes checklist opens the editor only. It does not resolve a
            question or clear a hold. Real edits need fresh checklist
            confirmation.
          </p>
          {!context.questions.length && (
            <p className="muted">No room questions recorded yet.</p>
          )}
          {context.questions.map((q) => {
            const draft = drafts[q.question_id] || blankDraft();
            const historical = q.state === "superseded";
            const activeIds =
              q.active_context?.used_reply_ids ||
              q.active_context?.used_replies?.map((r) => r.reply_id) ||
              [];
            const controls =
              !historical && (q.state === "pending" || !!q.active_context);
            const ready = !locked && draft.reviewed && !!draft.reason.trim();
            const requirement = project.baseline?.requirements.find(
              (r) => r.id === q.requirement_id,
            );
            return (
              <article
                className="context-question"
                key={q.question_id}
                aria-label={`Question ${q.question_id}`}
              >
                <div className="context-heading">
                  <h3>{requirement?.title || q.requirement_id}</h3>
                  <span className="badge">
                    {historical
                      ? "Superseded · history"
                      : q.state === "pending"
                        ? "Pending · delivery on hold"
                        : "Resolved"}
                  </span>
                </div>
                <p className="context-prose">{q.question}</p>
                <p className="fine context-reference">
                  Unverified question source: {q.source_ref || "Unknown"} ·
                  Original revision {q.source_revision} · Question{" "}
                  {q.question_id}
                </p>
                {q.legacy && (
                  <p className="warning">
                    Legacy unverified question. Original source anchor is
                    unknown. Dismiss only; it cannot be accepted as current
                    context.
                  </p>
                )}
                {historical && (
                  <p className="note">
                    Source changed. This question and any later replies are
                    historical and cannot be adopted here. Create an explicit
                    new current question/reference if needed.
                  </p>
                )}
                <details className="context-evidence">
                  <summary>Original selection and provisional findings</summary>
                  <p className="fine">
                    Original input hash: <code>{q.input_hash}</code>
                  </p>
                  <p>
                    Selected files:{" "}
                    {q.file_ids.length
                      ? q.file_ids
                          .map(
                            (id) =>
                              project.files?.find((f) => f.id === id)?.name ||
                              id,
                          )
                          .join(", ")
                      : "None"}
                  </p>
                  {q.evidence.length ? (
                    <ul>
                      {q.evidence.map((finding, i) => (
                        <li key={i}>
                          <strong>
                            {finding.kind} · {finding.status}
                          </strong>
                          : {finding.reason}
                          {finding.expected !== undefined && (
                            <span className="fine">
                              {" "}
                              · Expected: {JSON.stringify(finding.expected)}
                            </span>
                          )}
                          {finding.actual !== undefined && (
                            <span className="fine">
                              {" "}
                              · Observed: {JSON.stringify(finding.actual)}
                            </span>
                          )}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>No provisional findings were recorded.</p>
                  )}
                  <p className="fine">
                    These original findings are not a saved assessment of the
                    current packet.
                  </p>
                </details>
                {!!q.active_context && (
                  <div className="note context-active">
                    <strong>
                      {q.latest_resolution?.action === "dismiss"
                        ? "Earlier accepted context is still active."
                        : "Accepted context is active."}
                    </strong>
                    <p>
                      Reply IDs used: {activeIds.join(", ") || "Recorded basis"}
                      . Dismissing a follow-up keeps this basis. Use Withdraw
                      accepted context to remove it explicitly.
                    </p>
                    {q.replies
                      .filter((r) => activeIds.includes(r.reply_id))
                      .map((r) => (
                        <p className="context-prose" key={r.reply_id}>
                          {r.text}
                        </p>
                      ))}
                  </div>
                )}
                <h4>Unverified replies{historical ? " · history" : ""}</h4>
                {!q.replies.length && (
                  <p className="muted">
                    {q.state === "pending"
                      ? "No replies received. An unanswered question still holds delivery."
                      : historical
                        ? "No replies received. This historical question does not hold delivery."
                        : "No replies received."}
                  </p>
                )}
                {q.replies.map((reply) => (
                  <div className="context-reply" key={reply.reply_id}>
                    <p className="context-prose">{reply.text}</p>
                    <p className="fine context-reference">
                      Unverified reported speaker:{" "}
                      {reply.reported_speaker || "Unknown"} · Unverified source:{" "}
                      {reply.source_ref} · Reply {reply.reply_id} ·{" "}
                      {reply.created_at}
                    </p>
                    {q.state === "pending" && !q.legacy && (
                      <label className="checkbox">
                        <input
                          type="checkbox"
                          disabled={locked}
                          checked={draft.used.includes(reply.reply_id)}
                          onChange={(event) =>
                            update(q.question_id, {
                              used: event.target.checked
                                ? [...draft.used, reply.reply_id]
                                : draft.used.filter(
                                    (id) => id !== reply.reply_id,
                                  ),
                              reviewed: false,
                            })
                          }
                        />
                        Use reply {reply.reply_id} as context
                      </label>
                    )}
                  </div>
                ))}
                {q.latest_resolution && (
                  <details className="context-history">
                    <summary>
                      Latest resolution · {q.latest_resolution.action}
                    </summary>
                    <p className="context-prose">
                      {q.latest_resolution.reason}
                    </p>
                    <p className="fine">
                      Covered replies:{" "}
                      {q.latest_resolution.covered_reply_ids.join(", ") ||
                        "None"}{" "}
                      · Used replies:{" "}
                      {q.latest_resolution.used_reply_ids.join(", ") || "None"}{" "}
                      · {q.latest_resolution.created_at}
                    </p>
                  </details>
                )}
                {controls && (
                  <fieldset disabled={locked} className="context-controls">
                    <legend>Your local context decision</legend>
                    <label>
                      Reason for this context decision
                      <textarea
                        maxLength={1000}
                        value={draft.reason}
                        onChange={(event) =>
                          update(q.question_id, {
                            reason: event.target.value,
                            reviewed: false,
                          })
                        }
                      />
                    </label>
                    <label className="checkbox">
                      <input
                        type="checkbox"
                        checked={draft.reviewed}
                        onChange={(event) =>
                          update(q.question_id, {
                            reviewed: event.target.checked,
                          })
                        }
                      />
                      I checked the question, every reply and their original
                      sources.
                    </label>
                    <p className="fine">
                      This decision covers all {q.replies.length} replies
                      currently shown, including replies you do not use. A new
                      reply requires another review.
                    </p>
                    <div className="actions">
                      {q.state === "pending" && !q.legacy && (
                        <button
                          disabled={!ready || !draft.used.length}
                          onClick={() => void act(() => resolve(q, "accept"))}
                        >
                          Use selected replies
                        </button>
                      )}
                      {q.state === "pending" && (
                        <button
                          className="quiet"
                          disabled={!ready}
                          onClick={() => void act(() => resolve(q, "dismiss"))}
                        >
                          Dismiss question
                        </button>
                      )}
                      {!!q.active_context && (
                        <button
                          className="quiet"
                          disabled={!ready}
                          onClick={() => void act(() => resolve(q, "withdraw"))}
                        >
                          Withdraw accepted context
                        </button>
                      )}
                    </div>
                  </fieldset>
                )}
              </article>
            );
          })}
        </>
      )}
    </section>
  );
}
