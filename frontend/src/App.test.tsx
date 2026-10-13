import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import App from "./App";
import type { Project } from "./types";
const mock = vi.hoisted(() => ({
  api: vi.fn(),
  bootstrap: vi.fn(),
  download: vi.fn(),
}));
vi.mock("./api", () => mock);
const source = (): Project => ({
  id: "p1",
  name: "North Studio",
  revision: 1,
  input_hash: "current",
  brief: {
    id: "b1",
    text: "Deliver one PNG.",
    label: "Brief",
    sha256: "briefhash",
  },
  baseline: {
    id: "base",
    hash: "bh",
    state: "approved",
    requirements: [
      {
        id: "r1",
        title: "Deliver logo",
        origin: "model_suggested",
        quote: "Deliver one PNG.",
        source_id: "b1",
        human_note: "",
        checks: [{ kind: "png_nonopaque_pixels" }],
      },
    ],
  },
  files: [
    {
      id: "f1",
      name: "logo.png",
      type: "png",
      size: 500,
      sha256: "abcdef123456",
      inspection: "inspected",
      metadata: { nonopaque_pixels: false },
      text: "",
      error: null,
    },
  ],
  proposals: [
    {
      id: "match1",
      requirement_id: "r1",
      candidates: [{ file_id: "f1", reason: "Name resembles requested logo." }],
      coverage: "candidate",
      model: {},
    },
  ],
  decisions: [],
  jobs: [],
  exports: [],
  checks: [
    {
      requirement_id: "r1",
      kind: "png_nonopaque_pixels",
      status: "unknown",
      reason: "No files selected.",
    },
  ],
});
let project: Project;
beforeEach(() => {
  project = source();
  localStorage.clear();
  mock.api.mockReset();
  mock.bootstrap.mockResolvedValue({ token: "local" });
  mock.api.mockImplementation(async (path: string, method = "GET") => {
    if (path === "/projects") return [{ id: "p1", name: "North Studio" }];
    if (path === "/capabilities") return { model: { available: true } };
    if (path === "/projects/p1" && method === "GET") return project;
    if (path === "/projects/p1/handoff-preview") {
      const d = project.decisions.find(
        (d) =>
          d.review_state === "confirmed" && d.input_hash === project.input_hash,
      );
      return {
        project_name: project.name,
        input_hash: project.input_hash,
        status: "draft_with_gaps",
        scope_notice: "Human review only",
        gaps: [{ requirement_id: "r1", message: "Review check." }],
        requirements: [
          {
            id: "r1",
            title: "Deliver logo",
            review_state: d ? "confirmed" : "stale",
            human_disposition: d?.human_disposition || "unresolved",
            client_usage_note: d?.client_usage_note || "",
            files: [],
            checks: project.checks,
            gaps: [],
          },
        ],
      };
    }
    return project;
  });
});
afterEach(cleanup);
async function open() {
  render(<App />);
  fireEvent.click(
    await screen.findByRole("button", { name: "North Studio ↗" }),
  );
  await screen.findByRole("heading", { name: "North Studio", level: 1 });
}
describe("Human review boundaries", () => {
  it("does not confirm a baseline without explicit review acknowledgement", async () => {
    await open();
    fireEvent.click(screen.getByRole("button", { name: "02 Checklist" }));
    expect(
      (
        screen.getByRole("button", {
          name: "Confirm checklist →",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    fireEvent.click(
      screen.getByLabelText(
        "I reviewed these requirements, their source and the limits of each check.",
      ),
    );
    expect(
      (
        screen.getByRole("button", {
          name: "Confirm checklist →",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(false);
  });
  it("does not select files or satisfy a requirement from a model suggestion", async () => {
    await open();
    fireEvent.click(screen.getByRole("button", { name: "04 Review" }));
    expect(
      (screen.getByRole("checkbox", { name: /logo.png/ }) as HTMLInputElement)
        .checked,
    ).toBe(false);
    expect(
      (screen.getByLabelText("Your assessment") as HTMLSelectElement).value,
    ).toBe("unresolved");
    fireEvent.click(screen.getByRole("button", { name: "Save my review" }));
    await waitFor(() =>
      expect(mock.api).toHaveBeenCalledWith(
        "/projects/p1/decisions/r1",
        "PUT",
        expect.objectContaining({
          file_ids: [],
          human_disposition: "unresolved",
          client_usage_note: "",
        }),
        1,
      ),
    );
  });
  it("keeps a failed technical finding in client preview despite a satisfied human assessment", async () => {
    project.decisions = [
      {
        requirement_id: "r1",
        file_ids: ["f1"],
        review_state: "confirmed",
        human_disposition: "satisfied",
        internal_decision_note: "PRIVATE CONTRACT NOTE",
        client_usage_note: "Use this in the header.",
        input_hash: "current",
      },
    ];
    project.checks = [
      {
        requirement_id: "r1",
        kind: "png_nonopaque_pixels",
        status: "fail",
        reason: "No nonopaque pixel found.",
      },
    ];
    await open();
    fireEvent.click(screen.getByRole("button", { name: "05 Handoff" }));
    expect(await screen.findByText(/No nonopaque pixel found./)).toBeTruthy();
    expect(screen.queryByText("PRIVATE CONTRACT NOTE")).toBeNull();
    expect(
      screen.getByText(/1 item\(s\) still require attention/),
    ).toBeTruthy();
    expect(
      (
        screen.getByRole("button", {
          name: "Prepare handoff snapshot →",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
  });
  it("shows stale reviews as unresolved and requires a fresh export acknowledgement", async () => {
    project.decisions = [
      {
        requirement_id: "r1",
        file_ids: ["f1"],
        review_state: "stale",
        human_disposition: "satisfied",
        internal_decision_note: "",
        client_usage_note: "Old note",
        input_hash: "old",
      },
    ];
    await open();
    fireEvent.click(screen.getByRole("button", { name: "05 Handoff" }));
    expect(await screen.findByText(/unresolved · stale/)).toBeTruthy();
    expect(screen.queryByText("Old note")).toBeNull();
    expect(
      (
        screen.getByRole("button", {
          name: "Prepare handoff snapshot →",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
  });
});
