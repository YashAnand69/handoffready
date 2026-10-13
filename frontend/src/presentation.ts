import type { CheckSpec } from "./types";
export function checkDescription(c: CheckSpec) {
  switch (c.kind) {
    case "presence":
      return `At least one selected ${(c.types || []).join(" or ").toUpperCase()} file`;
    case "count":
      return `${c.comparison === "exact" ? "Exactly" : "At least"} ${c.value} selected ${(c.types || []).join(" / ").toUpperCase()} file(s)${c.distinct_bytes ? ", counting identical contents once" : ""}`;
    case "image_dimensions":
      return `Every selected image: ${c.width_px} × ${c.height_px} pixels`;
    case "png_nonopaque_pixels":
      return "Every selected PNG contains at least one pixel with alpha below 255";
    case "pdf_pages":
      return `Every selected PDF: ${c.comparison === "exact" ? "exactly" : "at least"} ${c.value} page(s)`;
    case "literal_text":
      return `Readable text contains the exact phrase “${c.needle}”`;
    default:
      return c.instruction || "Review manually";
  }
}
export function findingValue(value: unknown): string {
  return typeof value === "string" ? value : JSON.stringify(value);
}

export const readable = (s: string) => s.replaceAll("_", " ");
export const bytes = (n: number) =>
  n < 1024
    ? `${n} B`
    : n < 1048576
      ? `${(n / 1024).toFixed(1)} KB`
      : `${(n / 1048576).toFixed(1)} MB`;
export const latestDecisions = (rows: import("./types").Decision[]) => [
  ...new Map(rows.map((d) => [d.requirement_id, d])).values(),
];

export function checkIssue(c: CheckSpec): string {
  if (["presence", "count"].includes(c.kind) && !c.types?.length)
    return "Choose at least one allowed file format.";
  if (
    ["count", "pdf_pages"].includes(c.kind) &&
    (!Number.isInteger(c.value) ||
      !c.value ||
      c.value < 1 ||
      c.value > (c.kind === "pdf_pages" ? 10 : 30))
  )
    return `Enter a whole quantity between 1 and ${c.kind === "pdf_pages" ? 10 : 30}.`;
  if (
    c.kind === "image_dimensions" &&
    ![c.width_px, c.height_px].every(
      (v) => v !== undefined && Number.isInteger(v) && v >= 1 && v <= 10000,
    )
  )
    return "Enter whole width and height values between 1 and 10,000 pixels.";
  if (
    c.kind === "manual" &&
    (!c.instruction?.trim() || c.instruction.length > 2000)
  )
    return "Describe the manual review in 1–2,000 characters.";
  if (c.kind === "literal_text" && (!c.needle || c.needle.length > 500))
    return "Enter an exact phrase in 1–500 characters.";
  return "";
}
