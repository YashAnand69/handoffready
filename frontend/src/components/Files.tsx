import { useState, useEffect } from "react";
import type { Project, Artifact } from "../types";
import { bytes, readable } from "../presentation";
import { imageUrl } from "../api";
const MIB = 1024 * 1024;
const acceptedExtensions = ".png,.jpg,.jpeg,.svg,.pdf,.txt,.md";
function intakeIssue(existing: Artifact[], selected: File[]): string {
  if (existing.length + selected.length > 30)
    return "A packet holds up to 30 files. Remove a file or choose fewer files.";
  for (const file of selected) {
    if (!file.size) return `${file.name} is empty. Choose a file with content.`;
    if (file.size > 10 * MIB)
      return `${file.name} exceeds 10 MiB. Export a smaller file and try again.`;
    const extension = file.name.split(".").pop()?.toLowerCase();
    if (["svg", "txt", "md"].includes(extension || "") && file.size > MIB)
      return `${file.name} exceeds the 1 MiB text/SVG limit. Export a smaller file and try again.`;
  }
  if (
    [...existing, ...selected].reduce((total, file) => total + file.size, 0) >
    50 * MIB
  )
    return "These files would exceed the 50 MiB packet limit. Choose fewer or smaller files.";
  return "";
}
function recoveryAdvice(file: Artifact): string {
  const reason = file.error || "";
  if (/extension mismatch/i.test(reason))
    return "Use the extension for the actual file format, or export the intended format from its original app. Renaming cannot convert file contents.";
  if (/scanned|extractable native text|encrypted/i.test(reason))
    return "Export an unencrypted PDF with selectable text, or provide a supported text/Markdown guide. Scanned pages need a readable alternative.";
  if (/time limit|memory limit|inspection budget|decoded content/i.test(reason))
    return "Export a simpler or smaller version from its original app, then replace this file. Retrying identical contents may reach the same limit.";
  if (/svg|external|embedded|stylesheet|event handler/i.test(reason))
    return "Export a static SVG without scripts or external resources, or use a PNG if the agreed scope permits it.";
  if (/unsupported/i.test(reason))
    return "Choose PNG, JPEG, static SVG, readable PDF, UTF-8 text or Markdown. Export from the original app; changing the filename alone does not convert a file.";
  return "Check the stated limit or error, then export a fresh supported copy and replace this file. A blocked file cannot be selected as inspected evidence.";
}
export default function Files({
  project,
  disabled,
  upload,
  onRenameDirty,
  replace,
  rename,
  remove,
  match,
  ready,
  next,
}: {
  project: Project;
  disabled: boolean;
  upload: (f: File[]) => void;
  onRenameDirty: (id: string, value: boolean) => void;
  replace: (id: string, file: File) => void;
  rename: (id: string, name: string) => void;
  remove: (id: string) => void;
  match: () => void;
  ready: boolean;
  next: () => void;
}) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [intakeError, setIntakeError] = useState("");
  const duplicates = new Set(
    project.files
      .filter((file) =>
        project.files.some(
          (other) => other.id !== file.id && other.sha256 === file.sha256,
        ),
      )
      .map((file) => file.id),
  );
  const shown = project.files.filter(
    (file) =>
      file.name
        .toLocaleLowerCase()
        .includes(query.trim().toLocaleLowerCase()) &&
      (filter === "all" ||
        (filter === "attention"
          ? file.inspection !== "inspected"
          : duplicates.has(file.id))),
  );
  function receive(selected: File[], replacing?: string) {
    if (!selected.length) return;
    const problem = intakeIssue(
      project.files.filter((file) => file.id !== replacing),
      selected,
    );
    setIntakeError(problem);
    if (problem) return;
    if (replacing) replace(replacing, selected[0]);
    else upload(selected);
  }
  return (
    <section className="card">
      <p className="eyebrow">03 / THE ACTUAL PACKET</p>
      <h2>Bring what you plan to deliver.</h2>
      <p className="muted">
        Up to 30 files, 50 MiB per packet, 10 MiB per file. Supported: PNG,
        JPEG, SVG metadata, readable PDF, text and Markdown. Files remain on
        this computer.
      </p>
      <details className="packet-intake">
        <summary>File limits and supported contents</summary>
        <ul>
          <li>
            Text, Markdown and SVG: up to 1 MiB. Text must be UTF-8 and at most
            20,000 characters per file.
          </li>
          <li>
            PNG/JPEG: a single frame, at most 10 megapixels and 10,000 pixels on
            either side.
          </li>
          <li>
            PDF: 1–10 pages with selectable native text, at most 20,000
            extracted characters. Encrypted PDFs and scans are unsupported.
          </li>
          <li>
            SVG: static metadata only; scripts and external resources are
            blocked. The app does not render SVG previews.
          </li>
        </ul>
        <p className="fine">
          The local service inspects actual contents after selection. A filename
          or browser file type does not establish a valid format.
        </p>
      </details>
      <label className="file-picker">
        Choose delivery files
        <input
          type="file"
          multiple
          accept={acceptedExtensions}
          disabled={disabled}
          onChange={(e) => {
            if (e.target.files) receive(Array.from(e.target.files));
            e.target.value = "";
          }}
        />
      </label>
      {intakeError && (
        <p className="warning" role="alert">
          {intakeError} Nothing from this selection was submitted.
        </p>
      )}
      {!!project.files.length && (
        <div
          className="packet-tools"
          onChange={(event) => event.stopPropagation()}
        >
          <label className="packet-search">
            Find a file
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search filenames"
            />
          </label>
          <div className="packet-filters" aria-label="Filter packet files">
            {[
              ["all", "All"],
              ["attention", "Needs attention"],
              ["duplicates", "Duplicates"],
            ].map(([value, label]) => (
              <button
                key={value}
                type="button"
                className="quiet"
                aria-pressed={filter === value}
                onClick={() => setFilter(value)}
              >
                {label}
              </button>
            ))}
            {(query || filter !== "all") && (
              <button
                type="button"
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
          <p className="fine" role="status">
            Showing {shown.length} of {project.files.length} files. Filtering
            does not change your packet or reviews.
          </p>
        </div>
      )}
      {project.files.length ? (
        <div className="file-list">
          {!shown.length && (
            <p className="empty">
              No files match these filters. Clear filters to see the whole
              packet.
            </p>
          )}
          {project.files.map((f) => (
            <div
              key={f.id + f.name}
              hidden={!shown.some((file) => file.id === f.id)}
            >
              <FileCard
                onRenameDirty={onRenameDirty}
                projectId={project.id}
                file={f}
                disabled={disabled}
                duplicateNames={project.files
                  .filter(
                    (other) => other.id !== f.id && other.sha256 === f.sha256,
                  )
                  .map((other) => other.name)}
                remove={() => remove(f.id)}
                replace={(file) => receive([file], f.id)}
                rename={(name) => rename(f.id, name)}
              />
            </div>
          ))}
        </div>
      ) : (
        <div className="empty">
          A filename is a clue. Inspected contents provide the evidence.
        </div>
      )}
      <div className="actions">
        <button
          className="primary"
          disabled={
            disabled ||
            !ready ||
            project.baseline.state !== "approved" ||
            !project.files.length
          }
          onClick={match}
        >
          Suggest matches with local AI →
        </button>
        <button
          disabled={disabled || project.baseline.state !== "approved"}
          onClick={next}
        >
          Review manually
        </button>
      </div>
    </section>
  );
}
function FileCard({
  projectId,
  file: f,
  duplicateNames,
  onRenameDirty,
  disabled,
  remove,
  replace,
  rename,
}: {
  projectId: string;
  file: Artifact;
  duplicateNames: string[];
  onRenameDirty: (id: string, value: boolean) => void;
  disabled: boolean;
  remove: () => void;
  replace: (file: File) => void;
  rename: (name: string) => void;
}) {
  const [editing, setEditing] = useState(false),
    [name, setName] = useState(f.name);
  useEffect(() => {
    onRenameDirty(f.id, name !== f.name);
    return () => onRenameDirty(f.id, false);
  }, [editing, name, f.id, f.name, onRenameDirty]);
  return (
    <article>
      <div className="file-info">
        <b>{f.name}</b>
        <span
          className={`badge ${f.inspection === "inspected" ? "good" : "warning"}`}
        >
          {readable(f.inspection)}
        </span>
        <p className="fine">
          {f.type} · {bytes(f.size)} · {f.sha256.slice(0, 12)}
        </p>
        {f.error && (
          <div className="file-recovery">
            <p className="warning">{f.error}</p>
            <p className="fine">{recoveryAdvice(f)}</p>
          </div>
        )}
        <details className="file-details">
          <summary>Inspected properties and file identity</summary>
          <Metadata file={f} />
          <p className="fine">
            SHA-256 <code className="source-identity">{f.sha256}</code>
          </p>
        </details>
        {!!duplicateNames.length && (
          <p className="note">
            Identical file contents: {duplicateNames.join(", ")}. Different
            names do not make distinct designs.
          </p>
        )}
        {["png", "jpeg"].includes(f.type) && f.inspection === "inspected" && (
          <ImageEvidence projectId={projectId} file={f} />
        )}
        <div className="file-actions">
          <label className="replace-file">
            Replace file
            <input
              type="file"
              accept={acceptedExtensions}
              disabled={disabled}
              aria-label={`Replace ${f.name}`}
              onChange={(e) => {
                if (e.target.files?.[0]) replace(e.target.files[0]);
                e.target.value = "";
              }}
            />
          </label>
          <button
            className="quiet"
            disabled={disabled}
            aria-label={`Rename ${f.name}`}
            onClick={() => setEditing(!editing)}
          >
            Rename
          </button>
          <button
            className="quiet"
            disabled={disabled}
            aria-label={`Remove ${f.name}`}
            onClick={() => {
              if (
                confirm(
                  `Remove ${f.name} from this packet? Current reviews will become stale.`,
                )
              )
                remove();
            }}
          >
            Remove
          </button>
        </div>
        {editing && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              rename(name);
            }}
          >
            <label>
              Delivery filename
              <input
                value={name}
                maxLength={180}
                disabled={disabled}
                onChange={(e) => {
                  setName(e.target.value);
                  onRenameDirty(f.id, e.target.value !== f.name);
                }}
              />
            </label>
            <p className="fine">
              Renaming reinspects the original bytes and makes current reviews
              stale. Changing an extension cannot convert the file.
            </p>
            <button disabled={disabled || !name.trim() || name === f.name}>
              Save filename
            </button>
          </form>
        )}
      </div>
    </article>
  );
}
export function ImageEvidence({
  projectId,
  file,
}: {
  projectId: string;
  file: Artifact;
}) {
  const [shown, setShown] = useState(false),
    [url, setUrl] = useState(""),
    [error, setError] = useState("");
  useEffect(() => {
    if (!shown) return;
    let active = true,
      loaded = "";
    imageUrl(`/projects/${projectId}/files/${file.id}/preview`)
      .then((value) => {
        loaded = value;
        if (active) setUrl(value);
        else URL.revokeObjectURL(value);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
      if (loaded) URL.revokeObjectURL(loaded);
      setUrl("");
    };
  }, [shown, projectId, file.id]);
  return (
    <div className="image-evidence">
      <button
        className="quiet"
        onClick={() => {
          setShown(!shown);
          setError("");
        }}
      >
        {shown ? "Hide" : "Inspect"} image visually
      </button>
      {shown && (
        <>
          {error ? (
            <p className="warning" role="alert">
              {error}
            </p>
          ) : url ? (
            <div className="checkerboard">
              <img src={url} alt={`Delivery preview of ${file.name}`} />
            </div>
          ) : (
            <p className="fine">Loading the inspected local image…</p>
          )}
          <p className="fine">
            Your visual review. The app does not judge design quality or correct
            background removal.
          </p>
        </>
      )}
    </div>
  );
}
export function Metadata({ file }: { file: Artifact }) {
  return (
    <div className="metadata">
      {Object.entries(file.metadata || {}).map(([k, v]) => (
        <span key={k}>
          {readable(k)}:{" "}
          <b>{typeof v === "object" ? JSON.stringify(v) : String(v)}</b>
        </span>
      ))}
    </div>
  );
}
