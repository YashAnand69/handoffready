import type { AttentionSummary } from "../types";
import { readable } from "../presentation";
export function deliveryLabel(status: string): string {
  return status === "reviewed"
    ? "Reviewed delivery record"
    : status === "reviewed_with_exceptions"
      ? "Reviewed with scope exceptions"
      : status === "draft_with_gaps"
        ? "Draft · attention required"
        : readable(status);
}
export default function AttentionOverview({
  summary,
  disabled,
  review,
  compact = false,
}: {
  summary: AttentionSummary;
  disabled: boolean;
  review?: (id: string) => void;
  compact?: boolean;
}) {
  return (
    <section
      className={`attention-overview ${compact ? "compact" : ""}`}
      aria-label="Before you send"
    >
      <div className="attention-heading">
        <div>
          <p className="eyebrow">BEFORE YOU SEND</p>
          <h2>{deliveryLabel(summary.status)}</h2>
        </div>
        <span
          className={`badge ${summary.status === "reviewed" ? "neutral" : "warning"}`}
        >
          {summary.current_review_count} / {summary.requirement_count} current
          reviews
        </span>
      </div>
      <p className="fine">
        {summary.status === "reviewed"
          ? "Current human reviews and available narrow checks. This is not client acceptance or a guarantee of quality."
          : summary.status === "reviewed_with_exceptions"
            ? "Reviewer exclusions are disclosed separately. Underlying findings remain visible; this is not verified client approval."
            : "Saved evidence has outstanding work, review, or clarification. Exporting a draft preserves those gaps."}
      </p>
      <dl className="attention-counts">
        <div>
          <dt>Items needing attention</dt>
          <dd>{summary.attention_requirement_ids.length}</dd>
        </div>
        <div>
          <dt>Failed technical checks</dt>
          <dd>{summary.failed_check_count}</dd>
        </div>
        <div>
          <dt>Unavailable technical checks</dt>
          <dd>{summary.unknown_check_count}</dd>
        </div>
        <div>
          <dt>Scope exceptions</dt>
          <dd>{summary.exception_count}</dd>
        </div>
        {!compact && (
          <div>
            <dt>Items with human-only checks</dt>
            <dd>{summary.manual_requirement_count}</dd>
          </div>
        )}
      </dl>
      <p className="fine">
        Counts overlap. Technical checks and checklist items have different
        totals.
      </p>
      {!!summary.attention_requirement_ids.length && review && (
        <button
          disabled={disabled}
          onClick={() => review(summary.attention_requirement_ids[0])}
        >
          Review outstanding items →
        </button>
      )}
      {!summary.baseline_approved && (
        <p className="warning">
          Confirm the checklist before preparing a delivery record.
        </p>
      )}
    </section>
  );
}
