import { useState, useEffect } from "react";
import type { Project, Artifact } from "../types";
import { bytes, readable } from "../presentation";
import { imageUrl } from "../api";
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
  return (
    <section className="card">
      <p className="eyebrow">03 / THE ACTUAL PACKET</p>
      <h2>Bring what you plan to deliver.</h2>
      <p className="muted">
        Up to 30 files, 50 MB per packet, 10 MB per file. Supported: PNG, JPEG,
        SVG metadata, readable PDF, text and Markdown. Files remain on this
        computer.
      </p>
      <label className="file-picker">
        Choose delivery files
        <input
          type="file"
          multiple
          disabled={disabled}
          onChange={(e) => {
            if (e.target.files) upload(Array.from(e.target.files));
            e.target.value = "";
          }}
        />
      </label>
      {project.files.length ? (
        <div className="file-list">
          {project.files.map((f) => (
            <FileCard
              key={f.id + f.name}
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
              replace={(file) => replace(f.id, file)}
              rename={(name) => rename(f.id, name)}
            />
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
        {f.error && <p className="warning">{f.error}</p>}
        <Metadata file={f} />
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
