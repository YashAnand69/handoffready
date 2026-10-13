import { checkIssue } from "../presentation";
import { useState } from "react";
import type { Project, Requirement, CheckSpec } from "../types";
export default function Checklist({
  project,
  disabled,
  ready,
  extract,
  save,
}: {
  project: Project;
  disabled: boolean;
  ready: boolean;
  extract: () => void;
  save: (rows: Requirement[], approve: boolean) => void;
}) {
  const [rows, setRows] = useState(project.baseline.requirements),
    [confirmed, setConfirmed] = useState(false);
  const update = (id: string, patch: Partial<Requirement>) => {
    setRows(rows.map((r) => (r.id === id ? { ...r, ...patch } : r)));
    setConfirmed(false);
  };
  return (
    <section className="card">
      <div className="section-top">
        <div>
          <p className="eyebrow">02 / YOUR CHECKLIST</p>
          <h2>Make the requirements yours.</h2>
        </div>
        <button
          disabled={
            disabled ||
            !ready ||
            !project.brief ||
            project.baseline.state === "approved"
          }
          onClick={extract}
        >
          Suggest with local AI
        </button>
      </div>
      {project.baseline.state === "approved" && (
        <p className="note">
          This checklist is confirmed. Edit its requirements to revise it, or
          save a changed brief to generate a new draft. AI will not overwrite an
          approved checklist.
        </p>
      )}
      <p className="muted">
        Review source quotes, quantities and every explicitly required file
        format before confirming. AI can miss a format or misread a promise;
        correct those omissions here. Add manual items when the brief needs your
        interpretation.
      </p>
      {!rows.length && (
        <div className="empty">
          <h3>No requirements yet.</h3>
          <p>
            Use local AI to propose a checklist, or start with one item you can
            verify.
          </p>
        </div>
      )}
      {project.brief && (
        <details className="brief-context">
          <summary>Review the full saved brief</summary>
          <pre className="source-text">{project.brief.text}</pre>
        </details>
      )}
      {rows.map((r, index) => (
        <article className="requirement-edit" key={r.id}>
          <div className="row-top">
            <span className="eyebrow">
              ITEM {String(index + 1).padStart(2, "0")} ·{" "}
              {r.origin === "human_added" ? "ADDED BY YOU" : "MODEL SUGGESTION"}
            </span>
            <button
              className="quiet"
              disabled={disabled}
              onClick={() => {
                setRows(rows.filter((x) => x.id !== r.id));
                setConfirmed(false);
              }}
              aria-label={`Remove item ${index + 1}`}
            >
              Remove
            </button>
          </div>
          <label>
            Requirement
            <input
              value={r.title}
              disabled={disabled}
              maxLength={160}
              onChange={(e) => update(r.id, { title: e.target.value })}
            />
          </label>
          {r.quote && <blockquote>{r.quote}</blockquote>}
          <label>
            Your clarification{r.origin === "human_added" ? " (required)" : ""}
            <input
              value={r.human_note || ""}
              disabled={disabled}
              maxLength={2000}
              onChange={(e) => update(r.id, { human_note: e.target.value })}
            />
          </label>
          {r.checks.map((c, i) => (
            <div key={i} className="check-group">
              <CheckEditor
                check={c}
                disabled={disabled}
                set={(next) =>
                  update(r.id, {
                    checks: r.checks.map((v, j) => (j === i ? next : v)),
                  })
                }
              />
              <button
                className="quiet"
                disabled={disabled || r.checks.length <= 1}
                aria-label={`Remove check ${i + 1} from item ${index + 1}`}
                onClick={() =>
                  update(r.id, { checks: r.checks.filter((_, j) => j !== i) })
                }
              >
                Remove check
              </button>
            </div>
          ))}
          <button
            className="quiet"
            disabled={disabled || r.checks.length >= 10}
            onClick={() =>
              update(r.id, {
                checks: [
                  ...r.checks,
                  {
                    kind: "manual",
                    instruction: "Review this requirement yourself",
                  },
                ],
              })
            }
          >
            + Add a check
          </button>
        </article>
      ))}
      <button
        disabled={disabled || rows.length >= 20}
        onClick={() => {
          setRows([
            ...rows,
            {
              id: crypto.randomUUID(),
              title: "",
              origin: "human_added",
              quote: null,
              source_id: null,
              checks: [
                {
                  kind: "manual",
                  instruction: "Confirm this deliverable manually",
                },
              ],
              human_note: "",
            },
          ]);
          setConfirmed(false);
        }}
      >
        + Add a requirement
      </button>
      <div className="confirm-baseline">
        <label className="checkbox">
          <input
            type="checkbox"
            checked={confirmed}
            disabled={disabled}
            onChange={(e) => setConfirmed(e.target.checked)}
          />
          I reviewed these requirements, their source and the limits of each
          check.
        </label>
        <div className="actions">
          <button
            disabled={
              disabled ||
              !rows.length ||
              rows.some((r) => r.checks.some((c) => !!checkIssue(c)))
            }
            onClick={() => save(rows, false)}
          >
            Save draft
          </button>
          <button
            className="primary"
            disabled={
              disabled ||
              !confirmed ||
              !rows.length ||
              rows.some(
                (r) =>
                  !r.title.trim() ||
                  (r.origin === "human_added" && !r.human_note.trim()) ||
                  r.checks.some((c) => !!checkIssue(c)),
              )
            }
            onClick={() => save(rows, true)}
          >
            Confirm checklist →
          </button>
        </div>
      </div>
    </section>
  );
}
function CheckEditor({
  check: c,
  set,
  disabled,
}: {
  check: CheckSpec;
  set: (c: CheckSpec) => void;
  disabled: boolean;
}) {
  const options = [
    ["manual", "Manual review"],
    ["presence", "File format / presence"],
    ["count", "Number of files"],
    ["image_dimensions", "Image dimensions"],
    ["png_nonopaque_pixels", "PNG has nonopaque pixels"],
    ["pdf_pages", "PDF page count"],
    ["literal_text", "Exact text appears"],
  ];
  return (
    <div className="check-editor">
      {checkIssue(c) && (
        <p className="check-error" role="status">
          {checkIssue(c)}
        </p>
      )}
      <label>
        Check
        <select
          value={c.kind}
          disabled={disabled}
          onChange={(e) => {
            const kind = e.target.value;
            set(
              kind === "count"
                ? {
                    kind,
                    comparison: "exact",
                    value: 1,
                    distinct_bytes: true,
                    types: ["png", "jpeg", "svg", "pdf", "text", "markdown"],
                  }
                : kind === "image_dimensions"
                  ? { kind, width_px: 1080, height_px: 1080 }
                  : kind === "presence"
                    ? { kind, types: ["png"] }
                    : kind === "pdf_pages"
                      ? { kind, comparison: "at_least", value: 1 }
                      : kind === "literal_text"
                        ? { kind, needle: "" }
                        : kind === "manual"
                          ? { kind, instruction: "Confirm manually" }
                          : { kind },
            );
          }}
        >
          {options.map(([v, n]) => (
            <option key={v} value={v}>
              {n}
            </option>
          ))}
        </select>
      </label>
      {["presence", "count"].includes(c.kind) && (
        <fieldset className="format-picks">
          <legend>Allowed formats</legend>
          {["png", "jpeg", "svg", "pdf", "text", "markdown"].map((t) => (
            <label className="checkbox" key={t}>
              <input
                type="checkbox"
                disabled={disabled}
                checked={(c.types || []).includes(t)}
                onChange={(e) =>
                  set({
                    ...c,
                    types: e.target.checked
                      ? [...(c.types || []), t]
                      : (c.types || []).filter((v) => v !== t),
                  })
                }
              />
              {t}
            </label>
          ))}
        </fieldset>
      )}
      {["count", "pdf_pages"].includes(c.kind) && (
        <>
          <label>
            Quantity rule
            <select
              value={c.comparison || "exact"}
              disabled={disabled}
              onChange={(e) =>
                set({
                  ...c,
                  comparison: e.target.value as "exact" | "at_least",
                })
              }
            >
              <option value="exact">Exactly</option>
              <option value="at_least">At least</option>
            </select>
          </label>
          <label>
            Quantity
            <input
              type="number"
              min={1}
              max={c.kind === "count" ? 30 : 10}
              disabled={disabled}
              value={c.value ?? ""}
              onChange={(e) => set({ ...c, value: Number(e.target.value) })}
            />
          </label>
          {c.kind === "count" && (
            <label className="checkbox">
              <input
                type="checkbox"
                disabled={disabled}
                checked={!!c.distinct_bytes}
                onChange={(e) =>
                  set({ ...c, distinct_bytes: e.target.checked })
                }
              />
              Count identical file contents once
            </label>
          )}
        </>
      )}
      {c.kind === "image_dimensions" && (
        <>
          <label>
            Width in pixels
            <input
              type="number"
              min={1}
              max={10000}
              value={c.width_px ?? ""}
              disabled={disabled}
              onChange={(e) => set({ ...c, width_px: Number(e.target.value) })}
            />
          </label>
          <label>
            Height in pixels
            <input
              type="number"
              min={1}
              max={10000}
              value={c.height_px ?? ""}
              disabled={disabled}
              onChange={(e) => set({ ...c, height_px: Number(e.target.value) })}
            />
          </label>
        </>
      )}
      {c.kind === "manual" && (
        <label>
          What needs your judgment?
          <input
            value={c.instruction || ""}
            disabled={disabled}
            onChange={(e) => set({ ...c, instruction: e.target.value })}
          />
        </label>
      )}
      {c.kind === "literal_text" && (
        <label>
          Exact text
          <input
            value={c.needle || ""}
            disabled={disabled}
            onChange={(e) => set({ ...c, needle: e.target.value })}
          />
        </label>
      )}
      {c.kind === "png_nonopaque_pixels" && (
        <p className="fine">
          This checks whether any pixel has alpha below 255. Correct background
          removal still needs your review.
        </p>
      )}
    </div>
  );
}
