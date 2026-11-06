import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api";
import type { Project } from "../types";

type Share = {
  intent_id: string;
  job_id: string;
  export_id: string;
  source_revision: number;
  filename: string;
  artifact_sha256: string;
  artifact_size: number;
  status: string;
  state: string;
  is_current: boolean;
  expires_at: string;
  destination: { label: string; url: string };
  events: { state: string; attempt_id?: string; message_url?: string }[];
};
type Preview = {
  job_id: string;
  source_revision: number;
  input_hash: string;
  preview_hash: string;
  preview_markdown: string;
  destination: { label: string; url: string };
  draft: boolean;
  duplicate_risk: boolean;
  active_intent_id: string | null;
};
type History = { enabled: boolean; bound: boolean; items: Share[] };
type Pending = {
  project_id: string;
  kind: "authorize" | "cancel" | "verify";
  intent_id?: string;
  payload: Record<string, unknown>;
};
const key = (id: string) => `handoff-share-operation-${id}`;
const refusals = new Set([
  "invalid_fields",
  "delivery_invalid_input",
  "revision_conflict",
  "delivery_hold",
  "delivery_share_preview_conflict",
  "delivery_share_draft",
  "delivery_share_duplicate_risk",
  "delivery_share_pending",
  "delivery_share_limit",
  "export_history_limit",
  "delivery_share_disabled",
  "delivery_share_outcome_conflict",
  "delivery_share_unknown",
  "delivery_share_attempt_missing",
  "delivery_share_destination_mismatch",
  "delivery_share_artifact_changed",
]);
function restore(id: string): Pending | null {
  try {
    const v = JSON.parse(sessionStorage.getItem(key(id)) || "null");
    return v?.project_id === id &&
      ["authorize", "cancel", "verify"].includes(v.kind) &&
      typeof v.payload?.operation_key === "string"
      ? v
      : null;
  } catch {
    return null;
  }
}
// Match the backend's fixed Discord destination authority. Do not turn a
// malformed persisted/API value into a generic HTTP(S) navigation capability.
const channelUrl = (value: unknown): value is string =>
  typeof value === "string" &&
  /^https:\/\/discord\.com\/channels\/[0-9]{1,30}\/[0-9]{1,30}$/.test(value);
const messageUrl = (value: unknown, channel: unknown): value is string =>
  channelUrl(channel) &&
  typeof value === "string" &&
  value.startsWith(channel + "/") &&
  /^[0-9]{1,30}$/.test(value.slice(channel.length + 1));
const expiryText = (value: unknown) =>
  typeof value === "string" && Number.isFinite(Date.parse(value))
    ? new Date(value).toLocaleString()
    : "an unavailable time; refresh the return status";

export default function DeliveryShare({
  project,
  disabled,
  onBusy,
  onCommitted,
}: {
  project: Project;
  disabled: boolean;
  onBusy: (value: boolean) => void;
  onCommitted: () => Promise<unknown>;
}) {
  const [history, setHistory] = useState<History | null>(null),
    [preview, setPreview] = useState<Preview | null>(null),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false),
    [reviewed, setReviewed] = useState(false),
    [draftAck, setDraftAck] = useState(false),
    [repeatAck, setRepeatAck] = useState(false),
    [pending, setPending] = useState<Pending | null>(() => restore(project.id));
  const [files, setFiles] = useState<Record<string, File>>({}),
    [urls, setUrls] = useState<Record<string, string>>({}),
    [destinations, setDestinations] = useState<Record<string, boolean>>({}),
    [reasons, setReasons] = useState<Record<string, string>>({}),
    [risks, setRisks] = useState<Record<string, boolean>>({});
  const mounted = useRef(false),
    lock = useRef(false),
    seq = useRef(0),
    busyCallback = useRef(onBusy);
  busyCallback.current = onBusy;
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      seq.current++;
      busyCallback.current(false);
    };
  }, []);
  async function load() {
    const ticket = ++seq.current;
    const data = await api<History>(`/projects/${project.id}/delivery-shares`);
    if (!mounted.current || ticket !== seq.current) return false;
    if (
      !data ||
      typeof data.enabled !== "boolean" ||
      typeof data.bound !== "boolean" ||
      !Array.isArray(data.items)
    )
      throw new Error("Return status could not be read. Refresh to check it.");
    setError("");
    setHistory(data);
    setPreview(null);
    setReviewed(false);
    setDraftAck(false);
    setRepeatAck(false);
    if (data.enabled && data.bound) {
      try {
        const value = await api<Preview>(
          `/projects/${project.id}/delivery-share-preview`,
        );
        if (mounted.current && ticket === seq.current) setPreview(value);
      } catch (e) {
        if (mounted.current && ticket === seq.current)
          setError((e as Error).message);
      }
    }
    return mounted.current && ticket === seq.current ? data : false;
  }
  useEffect(() => {
    void load().catch((e) => {
      if (mounted.current) setError(e.message);
    });
  }, [project.id, project.revision, project.input_hash]);
  function remember(value: Pending | null) {
    setPending(value);
    try {
      if (value) sessionStorage.setItem(key(project.id), JSON.stringify(value));
      else sessionStorage.removeItem(key(project.id));
    } catch {
      /* Keep the same operation in memory. */
    }
  }
  async function act(operation: () => Promise<void>) {
    if (lock.current) return;
    lock.current = true;
    seq.current++;
    setBusy(true);
    onBusy(true);
    setError("");
    setMessage("");
    try {
      await operation();
    } catch (e) {
      if (mounted.current) setError((e as Error).message);
    } finally {
      lock.current = false;
      if (mounted.current) {
        setBusy(false);
        busyCallback.current(false);
      }
    }
  }
  async function submit(next?: Pending) {
    const operation = pending || next;
    if (!operation) return;
    remember(operation);
    let path = `/projects/${project.id}/delivery-shares`,
      body: unknown = operation.payload;
    if (operation.kind !== "authorize")
      path += `/${operation.intent_id}/${operation.kind}`;
    if (operation.kind === "verify") {
      const file = files[operation.intent_id!];
      if (!file)
        throw new Error(
          "Choose the exact returned Markdown file again to reconcile this verification.",
        );
      const form = new FormData();
      form.append("file", file);
      form.append("metadata", JSON.stringify(operation.payload));
      body = form;
    }
    let committedIntent = "";
    try {
      const result = await api<{
        state: string;
        result: { intent_id: string };
      }>(path, "POST", body);
      if (
        result?.state !== "succeeded" ||
        !result.result?.intent_id ||
        (operation.intent_id && result.result.intent_id !== operation.intent_id)
      )
        throw new Error(
          "The local result is uncertain. Reconcile the same operation before doing anything else.",
        );
      committedIntent = result.result.intent_id;
    } catch (e) {
      if (mounted.current && e instanceof ApiError && refusals.has(e.code)) {
        remember(null);
        if (operation.kind === "authorize") {
          setPreview(null);
          setReviewed(false);
        }
      }
      throw e;
    }
    if (!mounted.current) return;
    await onCommitted();
    if (!mounted.current) return;
    const refreshed = await load();
    const record =
      refreshed &&
      refreshed.items.find((item) => item.intent_id === committedIntent);
    if (!record)
      throw new Error(
        "Refresh was interrupted. Reconcile the same operation to check its result.",
      );
    remember(null);
    setMessage(
      operation.kind === "authorize"
        ? record.state === "authorized"
          ? "Record frozen and one return authorized. Nothing has been verified as sent."
          : "The earlier operation is recorded in history. No new send was authorized; read its current return status below."
        : operation.kind === "verify"
          ? "Returned bytes match. Destination was checked by you; this is operator confirmation, not independent transport proof."
          : "Return cancelled. Any earlier unverified send remains uncertain.",
    );
  }
  const blocked = disabled || busy,
    locked = blocked || !!pending;
  if (history && !history.bound && !history.items.length && !pending)
    return null;
  return (
    <section
      className="card"
      aria-label="Supervised record return"
      onChange={(e) => e.stopPropagation()}
    >
      <p className="eyebrow">RETURN TO YOUR DELIVERY ROOM</p>
      <h2>Freeze the record. Verify its return.</h2>
      <p>
        Review the public content and fixed destination before authorizing one
        Markdown return. Original delivery files are not included. An issued
        record stays unverified until you check the returned file and its
        destination.
      </p>
      {error && (
        <p role="alert" className="warning">
          {error}
        </p>
      )}
      {message && (
        <p role="status" className="note">
          {message}
        </p>
      )}
      {pending && (
        <div role="status" className="warning">
          <p>
            A local operation needs reconciliation. Keep the same decision and
            key; do not authorize another return.
          </p>
          <button
            disabled={
              blocked ||
              (pending.kind === "verify" && !files[pending.intent_id!])
            }
            onClick={() => void act(() => submit())}
          >
            Reconcile the same operation
          </button>
          {pending.kind === "verify" && (
            <p>
              Reselect the exact returned file below if this page was reopened.
            </p>
          )}
        </div>
      )}
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
        Refresh return status
      </button>
      {history && !history.enabled && (
        <p className="fine">
          New returns are not configured. Retained history and local
          returned-file verification remain available.
        </p>
      )}
      {preview && (
        <div className="manifest-preview">
          <h3>Destination: {preview.destination.label}</h3>
          {channelUrl(preview.destination.url) ? (
            <a
              href={preview.destination.url}
              target="_blank"
              rel="noopener noreferrer"
            >
              Open the configured main channel ↗
            </a>
          ) : (
            <p className="warning">
              The configured channel link is invalid. Refresh before authorizing
              a return.
            </p>
          )}
          <details>
            <summary>Read the public content to be frozen</summary>
            <pre
              style={{
                whiteSpace: "pre-wrap",
                maxHeight: "28rem",
                overflow: "auto",
                fontFamily: "inherit",
              }}
            >
              {preview.preview_markdown}
            </pre>
          </details>
          <p className="fine">
            Record ID and time are assigned when frozen. Private brief/file
            text, internal assessment notes and room replies are excluded;
            approved titles, check descriptions and public notes are included.
          </p>
          {preview.draft && (
            <p className="warning">
              This is a draft with outstanding items. It must not be presented
              as ready.
            </p>
          )}
          {preview.duplicate_risk && (
            <p className="warning">
              A return of this same review was already issued. Inspect the room
              before considering another.
            </p>
          )}
          {preview.active_intent_id && (
            <p className="note">
              This review already has an authorized record below. Use or cancel
              that authorization.
            </p>
          )}
          <label className="checkline">
            <input
              type="checkbox"
              checked={reviewed}
              disabled={locked}
              onChange={(e) => setReviewed(e.target.checked)}
            />
            I reviewed the public content and this destination.
          </label>
          {preview.draft && (
            <label className="checkline">
              <input
                type="checkbox"
                checked={draftAck}
                disabled={locked}
                onChange={(e) => setDraftAck(e.target.checked)}
              />
              I explicitly authorize a draft return with its outstanding items
              visible.
            </label>
          )}
          {preview.duplicate_risk && (
            <label className="checkline">
              <input
                type="checkbox"
                checked={repeatAck}
                disabled={locked}
                onChange={(e) => setRepeatAck(e.target.checked)}
              />
              I checked the room and accept the risk of another copy.
            </label>
          )}
          <button
            disabled={
              locked ||
              !reviewed ||
              !channelUrl(preview.destination.url) ||
              !!preview.active_intent_id ||
              (preview.draft && !draftAck) ||
              (preview.duplicate_risk && !repeatAck)
            }
            onClick={() =>
              void act(() =>
                submit({
                  project_id: project.id,
                  kind: "authorize",
                  payload: {
                    operation_key: crypto.randomUUID(),
                    expected_revision: preview.source_revision,
                    input_hash: preview.input_hash,
                    preview_hash: preview.preview_hash,
                    confirmed_reviewed: true,
                    acknowledge_draft: draftAck,
                    acknowledge_duplicate_risk: repeatAck,
                  },
                }),
              )
            }
          >
            Freeze record and authorize one return
          </button>
        </div>
      )}
      {history?.items.map((item) => {
        const attempt = item.events.find(
          (e) => e.state === "issued_unverified",
        )?.attempt_id;
        const verification = item.events.find(
          (e) => e.state === "operator_confirmed",
        );
        const canVerify = item.state === "issued_unverified";
        return (
          <article className="record-row" key={item.intent_id}>
            <h3>
              Source revision {item.source_revision} ·{" "}
              {item.state.replaceAll("_", " ")}
            </h3>
            {!item.is_current && (
              <p className="warning">
                Historical record. It does not represent the current packet or
                review.
              </p>
            )}
            <p>
              {item.destination.label} · {item.filename} · {item.artifact_size}{" "}
              bytes
            </p>
            <code className="source-identity">{item.artifact_sha256}</code>
            {item.state === "authorized" && (
              <div className="note">
                <p>
                  Authorized until {expiryText(item.expires_at)}. Ask your
                  delivery agent to return this authorized record once, using
                  its configured record-return tool.
                </p>
                <p>
                  Record ID: <code>{item.intent_id}</code>
                </p>
                <p className="fine">
                  Job: <code>{item.job_id}</code>. No send is verified yet.
                </p>
              </div>
            )}
            {(canVerify ||
              (pending?.kind === "verify" &&
                pending.intent_id === item.intent_id)) && (
              <fieldset
                disabled={
                  blocked || (!!pending && pending.intent_id !== item.intent_id)
                }
              >
                <legend>Verify the actual return</legend>
                <p className="warning">
                  Send outcome is unverified. Download the attachment from the
                  configured main channel; do not resend blindly.
                </p>
                <label>
                  Returned Markdown file
                  <input
                    type="file"
                    accept=".md,text/markdown,text/plain"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) setFiles((v) => ({ ...v, [item.intent_id]: f }));
                    }}
                  />
                </label>
                <label>
                  Discord message link
                  <input
                    value={urls[item.intent_id] || ""}
                    disabled={!!pending}
                    onChange={(e) =>
                      setUrls((v) => ({
                        ...v,
                        [item.intent_id]: e.target.value,
                      }))
                    }
                    placeholder={`${item.destination.url}/message-id`}
                  />
                </label>
                <label className="checkline">
                  <input
                    type="checkbox"
                    checked={!!destinations[item.intent_id]}
                    disabled={!!pending}
                    onChange={(e) =>
                      setDestinations((v) => ({
                        ...v,
                        [item.intent_id]: e.target.checked,
                      }))
                    }
                  />
                  I checked that this file was returned in the configured
                  destination.
                </label>
                <button
                  disabled={
                    locked ||
                    !files[item.intent_id] ||
                    !urls[item.intent_id]?.trim() ||
                    !destinations[item.intent_id]
                  }
                  onClick={() =>
                    void act(() =>
                      submit({
                        project_id: project.id,
                        kind: "verify",
                        intent_id: item.intent_id,
                        payload: {
                          operation_key: crypto.randomUUID(),
                          attempt_id: attempt,
                          message_url: urls[item.intent_id].trim(),
                          confirmed_destination: true,
                        },
                      }),
                    )
                  }
                >
                  Verify returned bytes and destination
                </button>
              </fieldset>
            )}
            {verification?.message_url && (
              <p className="note">
                Operator-confirmed exact bytes and destination.{" "}
                {messageUrl(verification.message_url, item.destination.url) ? (
                  <a
                    href={verification.message_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Open the checked message ↗
                  </a>
                ) : (
                  <span>
                    The checked message link is invalid; verify its configured
                    destination.
                  </span>
                )}
              </p>
            )}
            {[
              "authorized",
              "expired",
              "superseded",
              "issued_unverified",
            ].includes(item.state) && (
              <details>
                <summary>Cancel this authorization</summary>
                <label>
                  Cancellation reason
                  <textarea
                    value={reasons[item.intent_id] || ""}
                    disabled={locked}
                    maxLength={1000}
                    onChange={(e) =>
                      setReasons((v) => ({
                        ...v,
                        [item.intent_id]: e.target.value,
                      }))
                    }
                  />
                </label>
                {canVerify && (
                  <label className="checkline">
                    <input
                      type="checkbox"
                      checked={!!risks[item.intent_id]}
                      disabled={locked}
                      onChange={(e) =>
                        setRisks((v) => ({
                          ...v,
                          [item.intent_id]: e.target.checked,
                        }))
                      }
                    />
                    I understand this record may already have been sent;
                    cancellation does not prove otherwise.
                  </label>
                )}
                <button
                  disabled={
                    locked ||
                    !reasons[item.intent_id]?.trim() ||
                    (canVerify && !risks[item.intent_id])
                  }
                  onClick={() =>
                    void act(() =>
                      submit({
                        project_id: project.id,
                        kind: "cancel",
                        intent_id: item.intent_id,
                        payload: {
                          operation_key: crypto.randomUUID(),
                          reason: reasons[item.intent_id].trim(),
                          acknowledge_may_have_sent: !!risks[item.intent_id],
                        },
                      }),
                    )
                  }
                >
                  Cancel authorization
                </button>
              </details>
            )}
          </article>
        );
      })}
    </section>
  );
}
