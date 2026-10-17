import type { SourceSpan } from "../types";

/** Python locations count Unicode code points; JavaScript string offsets do not. */
export function locatedText(text: string, span: SourceSpan): boolean {
  const points = Array.from(text);
  return (
    Number.isInteger(span.start_cp) &&
    Number.isInteger(span.end_cp) &&
    span.start_cp >= 0 &&
    span.end_cp > span.start_cp &&
    span.end_cp <= points.length &&
    points.slice(span.start_cp, span.end_cp).join("") === span.quote
  );
}
export default function SourceEvidence({
  quote,
  span,
  text,
  label,
  unitId,
}: {
  quote: string;
  span?: SourceSpan | null;
  text?: string;
  label: string;
  unitId?: string | null;
}) {
  const located =
    !!span &&
    span.quote === quote &&
    text !== undefined &&
    locatedText(text, span);
  const points = located ? Array.from(text!) : [];
  const occurrenceId = span?.evidence_unit_id || unitId;
  return (
    <div className="source-evidence">
      <blockquote>
        {quote}
        <small>{label}</small>
      </blockquote>
      {located && span ? (
        <details>
          <summary>View exact source location</summary>
          <p className="fine">
            Code points {span.start_cp}–{span.end_cp} · end excluded. Location
            identifies text, not fulfillment.
          </p>
          <pre className="source-text">
            {points
              .slice(Math.max(0, span.start_cp - 100), span.start_cp)
              .join("")}
            <mark>{points.slice(span.start_cp, span.end_cp).join("")}</mark>
            {points.slice(span.end_cp, span.end_cp + 100).join("")}
          </pre>
          {occurrenceId && (
            <p className="fine source-identity">
              Evidence occurrence: <code>{occurrenceId}</code>
            </p>
          )}
        </details>
      ) : (
        <p className="fine">
          Exact occurrence unavailable in this record. Review the full source
          before confirming.
        </p>
      )}
    </div>
  );
}
