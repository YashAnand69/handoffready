import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api";
import type { Project } from "../types";
import { bytes } from "../presentation";

type Receipt = {
  receipt_id: string;
  source_id: string;
  filename: string;
  sha256: string;
  size: number;
  availability: string;
  considered: boolean;
};
type Intake = {
  job_id: string;
  source_revision: number;
  input_hash: string;
  receipts: Receipt[];
  pending_count: number;
  last_packet: { packet_id: string } | null;
};
type Preview = {
  manifest_hash: string;
  source_revision: number;
  input_hash: string;
  receipts: Receipt[];
  excluded_receipt_ids: string[];
  excluded_receipts: Pick<Receipt, "receipt_id" | "filename" | "source_id">[];
  total_bytes: number;
  changes: Record<"added" | "replaced" | "removed" | "unchanged", string[]>;
  review_will_be_stale: boolean;
};
type Confirmation = {
  operation_key: string;
  receipt_ids: string[];
  expected_revision: number;
  input_hash: string;
  manifest_hash: string;
  confirmed_complete: true;
};
const storageKey = (id: string) => `handoff-intake-operation-${id}`;
function pendingOperation(id: string): Confirmation | null {
  try {
    const raw = sessionStorage.getItem(storageKey(id));
    if (!raw) return null;
    const value = JSON.parse(raw);
    if (
      typeof value.operation_key === "string" &&
      Array.isArray(value.receipt_ids) &&
      value.receipt_ids.length > 0 &&
      value.receipt_ids.length <= 30 &&
      value.receipt_ids.every((entry: unknown) => typeof entry === "string") &&
      Number.isSafeInteger(value.expected_revision) &&
      typeof value.input_hash === "string" &&
      typeof value.manifest_hash === "string" &&
      value.confirmed_complete === true
    )
      return value;
  } catch {
    /* Storage is optional; current-mount retry still uses the same key. */
  }
  return null;
}
export default function DeliveryIntake({
  project,
  disabled,
  onCommitted,
  onBusy,
}: {
  project: Project;
  disabled: boolean;
  onCommitted: () => Promise<unknown>;
  onBusy: (value: boolean) => void;
}) {
  const [intake, setIntake] = useState<Intake | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [pending, setPending] = useState<Confirmation | null>(() =>
    pendingOperation(project.id),
  );
  const lock = useRef(false);
  const current = useRef(true);
  useEffect(
    () => () => {
      current.current = false;
      onBusy(false);
    },
    [onBusy],
  );
  const load = async () => {
    const result = await api<{ enabled: boolean; job: Intake | null }>(
      `/projects/${project.id}/delivery`,
    );
    if (!current.current) return;
    setIntake(result.job);
    setSelected(
      result.job?.receipts
        .filter((row) => !row.considered && row.availability === "available")
        .map((row) => row.receipt_id) || [],
    );
  };
  useEffect(() => {
    current.current = true;
    let active = true;
    void load()
      .catch((failure: Error) => {
        if (active) setError(failure.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
      current.current = false;
    };
    // This component is keyed by project, so responses cannot cross projects.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [project.id]);
  useEffect(() => {
    setPreview(null);
    setConfirmed(false);
  }, [project.revision]);
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
      if (current.current) setError((failure as Error).message);
    } finally {
      lock.current = false;
      if (current.current) {
        setBusy(false);
        onBusy(false);
      }
    }
  }
  function remember(value: Confirmation | null) {
    setPending(value);
    try {
      if (value)
        sessionStorage.setItem(storageKey(project.id), JSON.stringify(value));
      else sessionStorage.removeItem(storageKey(project.id));
    } catch {
      /* Do not put credentials or file contents in browser storage. */
    }
  }
  async function confirmPacket() {
    if (!intake || (!pending && (!preview || !confirmed))) return;
    const operation: Confirmation = pending || {
      operation_key: crypto.randomUUID(),
      receipt_ids: preview!.receipts.map((row) => row.receipt_id),
      expected_revision: preview!.source_revision,
      input_hash: preview!.input_hash,
      manifest_hash: preview!.manifest_hash,
      confirmed_complete: true,
    };
    remember(operation);
    try {
      await api(
        `/delivery/jobs/${intake.job_id}/packet-confirm`,
        "POST",
        operation,
      );
    } catch (failure) {
      if (
        failure instanceof ApiError &&
        [
          "invalid_fields",
          "delivery_invalid_input",
          "revision_conflict",
          "delivery_input_conflict",
          "delivery_manifest_changed",
          "delivery_receipt_missing",
          "delivery_receipt_unavailable",
          "delivery_filename_collision",
          "delivery_packet_limit",
          "delivery_inspection_failed",
          "delivery_operation_limit",
          "delivery_result_limit",
          "delivery_operation_conflict",
          "storage_limit",
        ].includes(failure.code)
      ) {
        remember(null);
        setPreview(null);
        setConfirmed(false);
      }
      throw failure;
    }
    // Refresh authoritative project and receipts before announcing completion.
    await onCommitted();
    await load();
    if (!current.current) return;
    remember(null);
    setPreview(null);
    setConfirmed(false);
    setMessage(
      "Complete packet recorded. Review the current evidence in the desk; no human assessment was saved by intake.",
    );
  }
  if (loading)
    return (
      <p className="fine" role="status">
        Checking room intake…
      </p>
    );
  if (!intake && !error) return null;
  const blocked = disabled || busy;
  return (
    <section
      className="card delivery-intake"
      aria-label="Room packet intake"
      onChange={(event) => event.stopPropagation()}
    >
      <p className="eyebrow">FROM YOUR DELIVERY ROOM</p>
      <h2>Confirm the complete packet.</h2>
      <p>
        Received attachments are waiting evidence, not an approved delivery.
        Compare them with the conversation and choose every file in this
        revision, including any earlier files you are keeping.
      </p>
      {error && (
        <p className="warning" role="alert">
          {error}
        </p>
      )}
      {message && (
        <p role="status" className="note">
          {message}
        </p>
      )}
      {pending && (
        <div className="note" role="status">
          <strong>A confirmation is waiting for reconciliation.</strong>
          <p>
            Its reply or refresh may have been interrupted. Retry the same
            confirmation to check its stored result; this will not create a
            second packet. Keep this browser tab until it is resolved.
          </p>
        </div>
      )}
      {intake && (
        <>
          <p className="fine">
            {intake.pending_count} new attachment
            {intake.pending_count === 1 ? "" : "s"} · {intake.receipts.length}{" "}
            retained receipt{intake.receipts.length === 1 ? "" : "s"}. Source
            references come from the assistant and need your check against the
            room.
          </p>
          <fieldset disabled={blocked || !!pending}>
            <legend>Files in this complete revision</legend>
            {!intake.receipts.length && (
              <p className="muted">
                No room attachments received yet. Ask the teammate to send the
                complete packet in the delivery channel.
              </p>
            )}
            {intake.receipts.map((row) => (
              <label className="checkbox intake-receipt" key={row.receipt_id}>
                <input
                  type="checkbox"
                  checked={selected.includes(row.receipt_id)}
                  disabled={row.availability !== "available"}
                  onChange={(event) => {
                    setSelected((old) =>
                      event.target.checked
                        ? [...old, row.receipt_id]
                        : old.filter((id) => id !== row.receipt_id),
                    );
                    setPreview(null);
                    setConfirmed(false);
                  }}
                />
                <span>
                  <strong>{row.filename}</strong> · {bytes(row.size)}
                  <small>
                    {row.availability === "available"
                      ? row.considered
                        ? "Earlier receipt — include it only if it belongs in this revision"
                        : "New attachment"
                      : "Unavailable or changed — recover this attachment before selecting it"}
                  </small>
                  <small>
                    Source: {row.source_id} · SHA-256: <code>{row.sha256}</code>
                  </small>
                </span>
              </label>
            ))}
          </fieldset>
          <p
            className={selected.length > 30 ? "warning" : "fine"}
            role="status"
          >
            {selected.length} selected · Choose between 1 and 30 files for the
            complete revision.
          </p>
          <div className="actions">
            <button
              className="quiet"
              disabled={blocked || !!pending}
              onClick={() =>
                void act(async () => {
                  setPreview(null);
                  setConfirmed(false);
                  await load();
                })
              }
            >
              Refresh received files
            </button>
            <button
              disabled={
                blocked || !!pending || !selected.length || selected.length > 30
              }
              onClick={() =>
                void act(async () => {
                  setPreview(null);
                  setConfirmed(false);
                  const result = await api<Preview>(
                    `/delivery/jobs/${intake.job_id}/packet-preview`,
                    "POST",
                    {
                      receipt_ids: selected,
                      expected_revision: intake.source_revision,
                      input_hash: intake.input_hash,
                    },
                  );
                  if (current.current) setPreview(result);
                })
              }
            >
              Preview packet changes
            </button>
          </div>
          {preview && !pending && (
            <div className="intake-preview" aria-label="Packet change preview">
              <h3>
                {preview.receipts.length} file
                {preview.receipts.length === 1 ? "" : "s"} ·{" "}
                {bytes(preview.total_bytes)}
              </h3>
              <p>
                This replaces the entire packet.{" "}
                {preview.excluded_receipt_ids.length} received attachment
                {preview.excluded_receipt_ids.length === 1
                  ? " is"
                  : "s are"}{" "}
                excluded.
              </p>
              {preview.excluded_receipts.length > 0 && (
                <div>
                  <strong>Excluded from this revision</strong>
                  <ul>
                    {preview.excluded_receipts.map((row) => (
                      <li key={row.receipt_id}>
                        {row.filename} · Source: {row.source_id}
                      </li>
                    ))}
                  </ul>
                  <p className="fine">
                    To include an excluded attachment, refresh received files,
                    adjust the selection and preview again.
                  </p>
                </div>
              )}
              {(["added", "replaced", "removed", "unchanged"] as const).map(
                (kind) => (
                  <div key={kind}>
                    <strong>{kind[0].toUpperCase() + kind.slice(1)}</strong>:{" "}
                    {preview.changes[kind].length ? (
                      <ul>
                        {preview.changes[kind].map((name) => (
                          <li key={name}>{name}</li>
                        ))}
                      </ul>
                    ) : (
                      " None"
                    )}
                  </div>
                ),
              )}
              <p className={preview.review_will_be_stale ? "warning" : "note"}>
                {preview.review_will_be_stale
                  ? "The packet changes. Earlier assessments become stale and need a fresh review."
                  : "The file contents are unchanged. Existing current assessments will be kept."}
              </p>
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={confirmed}
                  disabled={blocked}
                  onChange={(event) => setConfirmed(event.target.checked)}
                />
                I checked the conversation: this selection is the complete
                revision, and excluded attachments do not belong in it.
              </label>
            </div>
          )}
          {(preview || pending) && (
            <div className="actions">
              <button
                disabled={blocked || (!pending && !confirmed)}
                onClick={() => void act(confirmPacket)}
              >
                {busy
                  ? "Checking packet…"
                  : pending
                    ? "Reconcile the same confirmation"
                    : "Confirm complete packet"}
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}
