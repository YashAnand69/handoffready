import type { Project } from "./types";

export function nextAction(project: Project) {
  if (!project.brief)
    return {
      step: 0,
      label: "Add the agreed brief",
      detail: "Start with the deliverables you promised.",
    };
  if (
    project.baseline.state !== "approved" ||
    !project.baseline.requirements.length
  )
    return {
      step: 1,
      label: "Confirm your checklist",
      detail: "Review the requirements and the checks you want to use.",
    };
  if (project.delivery_hold?.blocked) {
    const intake = project.delivery_hold.pending_receipt_count > 0;
    return {
      step: intake ? 2 : 3,
      label: intake
        ? "Confirm the complete room packet"
        : "Review the room context",
      detail: intake
        ? "New room attachments need local packet confirmation before a record can be prepared."
        : "Resolve pending room questions and check current evidence before preparing a record.",
    };
  }
  if (
    project.attention_summary &&
    ["reviewed", "reviewed_with_exceptions"].includes(
      project.attention_summary.status,
    )
  )
    return {
      step: 4,
      label: "Prepare the client record",
      detail: "Review the public notes and save a snapshot of this delivery.",
    };
  if (!project.files.some((file) => file.inspection === "inspected"))
    return {
      step: 2,
      label: "Bring your delivery files",
      detail:
        "Add supported files or replace a file that could not be inspected.",
    };
  const attention = project.attention_summary;
  const id =
    attention?.attention_requirement_ids[0] ||
    (!attention
      ? project.baseline.requirements.find((r) =>
          (() => {
            const d = [...project.decisions]
              .reverse()
              .find((entry) => entry.requirement_id === r.id);
            return (
              !d ||
              d.review_state !== "confirmed" ||
              d.input_hash !== project.input_hash ||
              d.human_disposition !== "satisfied"
            );
          })(),
        )?.id
      : undefined);
  if (id)
    return {
      step: 3,
      id,
      label: "Review what needs attention",
      detail: "Compare the evidence, resolve gaps, and record your assessment.",
    };
  return {
    step: 4,
    label: "Prepare the client record",
    detail: "Review the public notes and save a snapshot of this delivery.",
  };
}
