/** Independent usability regressions. API doubles do not measure model quality. */
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
  imageUrl: vi.fn(),
}));
vi.mock("./api", () => mock);
let project: Project;
beforeEach(() => {
  localStorage.clear();
  mock.api.mockReset();
  mock.bootstrap.mockReset();
  mock.bootstrap.mockResolvedValue({ token: "local" });
  project = {
    id: "final-audit",
    name: "Final audit desk",
    revision: 1,
    input_hash: "current",
    brief: {
      id: "brief",
      text: "Deliver the logo.",
      label: "Agreed source",
      sha256: "brief-hash",
    },
    baseline: {
      id: "base",
      state: "approved",
      hash: "base-hash",
      requirements: [
        {
          id: "r1",
          title: "Logo",
          origin: "human_added",
          quote: null,
          source_id: null,
          human_note: "Human interpretation",
          checks: [{ kind: "manual", instruction: "Review visual quality" }],
        },
      ],
    },
    files: [
      {
        id: "f1",
        name: "logo.png",
        type: "png",
        size: 10,
        sha256: "abc123",
        inspection: "inspected",
        metadata: {},
        text: "",
        error: null,
      },
    ],
    proposals: [],
    decisions: [],
    jobs: [],
    exports: [],
    checks: [],
  };
  mock.api.mockImplementation(async (path: string) =>
    path === "/projects"
      ? [{ id: project.id, name: project.name }]
      : path === "/capabilities"
        ? { model: { available: false } }
        : project,
  );
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
async function open(step: string) {
  render(<App />);
  fireEvent.click(
    await screen.findByRole("button", { name: "Final audit desk ↗" }),
  );
  await screen.findByRole("heading", { name: "Final audit desk", level: 1 });
  fireEvent.click(screen.getByRole("button", { name: step }));
}
describe("Final independent usability audit", () => {
  it("keeps the leave warning after clicking the current requirement", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    await open("04 Review");
    fireEvent.change(screen.getByLabelText("Private review note"), {
      target: { value: "Unsaved review" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Logo Needs your review" }),
    );
    expect(confirm).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "03 Files" }));
    expect(confirm).toHaveBeenCalled();
    expect(
      (screen.getByLabelText("Private review note") as HTMLTextAreaElement)
        .value,
    ).toBe("Unsaved review");
  });
  it("protects an unsaved filename when using the manual review shortcut", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    await open("03 Files");
    fireEvent.click(screen.getByRole("button", { name: /^Rename / }));
    fireEvent.change(screen.getByLabelText("Delivery filename"), {
      target: { value: "client-logo.png" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Review manually" }));
    expect(confirm).toHaveBeenCalled();
    expect(
      (screen.getByLabelText("Delivery filename") as HTMLInputElement).value,
    ).toBe("client-logo.png");
  });
  it("offers one visual inspection control for each selected image", async () => {
    project.decisions = [
      {
        requirement_id: "r1",
        file_ids: ["f1"],
        review_state: "confirmed",
        human_disposition: "unresolved",
        internal_decision_note: "",
        client_usage_note: "",
        input_hash: "current",
      },
    ];
    await open("04 Review");
    expect(
      screen.getAllByRole("button", {
        name: "Inspect image visually",
        hidden: true,
      }),
    ).toHaveLength(1);
  });
  it("warns before model matching discards an unsaved filename", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    mock.api.mockImplementation(async (path: string) =>
      path === "/projects"
        ? [{ id: project.id, name: project.name }]
        : path === "/capabilities"
          ? { model: { available: true } }
          : project,
    );
    await open("03 Files");
    fireEvent.click(screen.getByRole("button", { name: /^Rename / }));
    fireEvent.change(screen.getByLabelText("Delivery filename"), {
      target: { value: "client-logo.png" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Suggest matches with local AI →" }),
    );
    expect(confirm).toHaveBeenCalled();
    expect(
      (screen.getByLabelText("Delivery filename") as HTMLInputElement).value,
    ).toBe("client-logo.png");
  });
  it("stops adding checks at the backend limit", async () => {
    project.baseline.requirements[0].checks = Array.from(
      { length: 10 },
      () => ({
        kind: "manual",
        instruction: "Confirm manually",
      }),
    );
    await open("02 Checklist");
    expect(
      (
        screen.getByRole("button", {
          name: "+ Add a check",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
  });
  it("recovers from an initial local connection failure without losing entered project name", async () => {
    mock.bootstrap.mockRejectedValueOnce(new Error("Service starting"));
    render(<App />);
    await screen.findByText("Service starting");
    fireEvent.change(screen.getByLabelText("Project name"), {
      target: { value: "Recovered desk" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Retry local connection" }),
    );
    await waitFor(() =>
      expect(
        (
          screen.getByRole("button", {
            name: /Create a handoff/,
          }) as HTMLButtonElement
        ).disabled,
      ).toBe(false),
    );
    expect(
      (screen.getByLabelText("Project name") as HTMLInputElement).value,
    ).toBe("Recovered desk");
    expect(mock.bootstrap).toHaveBeenCalledTimes(2);
  });
  it("retries a failed client preview and still requires explicit export acknowledgement", async () => {
    const normal = mock.api.getMockImplementation()!;
    let previewCalls = 0;
    mock.api.mockImplementation(async (...args: unknown[]) => {
      if (args[0] === "/projects/final-audit/handoff-preview") {
        if (++previewCalls === 1)
          throw new Error("Preview temporarily unavailable");
        return {
          project_name: project.name,
          input_hash: project.input_hash,
          status: "reviewed",
          scope_notice: "Human review only",
          requirements: [],
          gaps: [],
        };
      }
      return normal(...args);
    });
    await open("05 Handoff");
    await screen.findByText("Preview temporarily unavailable");
    fireEvent.click(screen.getByRole("button", { name: "Retry preview" }));
    await screen.findByText("Human review only");
    expect(previewCalls).toBe(2);
    expect(
      (
        screen.getByRole("button", {
          name: "Prepare handoff snapshot →",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    expect(screen.getByText(/does not contain the original/)).toBeTruthy();
  });
  it("removes an individual check without losing its requirement and resets acknowledgement", async () => {
    project.baseline.requirements[0].checks.push({
      kind: "presence",
      types: ["png"],
    });
    await open("02 Checklist");
    fireEvent.click(
      screen.getByLabelText(
        "I reviewed these requirements, their source and the limits of each check.",
      ),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Remove check 2 from item 1" }),
    );
    expect(
      (screen.getByLabelText("Requirement") as HTMLInputElement).value,
    ).toBe("Logo");
    expect(screen.getAllByLabelText("Check")).toHaveLength(1);
    expect(
      (
        screen.getByRole("button", {
          name: "Remove check 1 from item 1",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    expect(
      (
        screen.getByLabelText(
          "I reviewed these requirements, their source and the limits of each check.",
        ) as HTMLInputElement
      ).checked,
    ).toBe(false);
  });
  it("blocks an invalid numeric check before saving", async () => {
    project.baseline.requirements[0].checks = [
      {
        kind: "count",
        comparison: "exact",
        value: 1,
        distinct_bytes: true,
        types: ["png"],
      },
    ];
    await open("02 Checklist");
    fireEvent.change(screen.getByLabelText("Quantity"), {
      target: { value: "0" },
    });
    expect(
      (screen.getByRole("button", { name: "Save draft" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
    expect(screen.getByRole("status")).toBeTruthy();
  });
  it("focuses the new step heading after navigation", async () => {
    await open("03 Files");
    expect(document.activeElement).toBe(
      screen.getByRole("heading", {
        level: 2,
        name: "Bring what you plan to deliver.",
      }),
    );
  });
  it("retains dirty filename protection after uploading an unrelated file", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    await open("03 Files");
    fireEvent.click(screen.getByRole("button", { name: /^Rename / }));
    fireEvent.change(screen.getByLabelText("Delivery filename"), {
      target: { value: "unsaved-logo.png" },
    });
    fireEvent.change(screen.getByLabelText("Choose delivery files"), {
      target: { files: [new File(["Guide"], "guide.txt")] },
    });
    if (!confirm.mock.calls.length) {
      await screen.findByText(
        "Files received and inspected. Review any blocked files before matching.",
      );
      fireEvent.click(screen.getByRole("button", { name: "04 Review" }));
    }
    expect(confirm).toHaveBeenCalled();
    expect(
      (screen.getByLabelText("Delivery filename") as HTMLInputElement).value,
    ).toBe("unsaved-logo.png");
  });
  it("saving one filename does not clear another file's draft warning", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    project.files.push({
      ...project.files[0],
      id: "f2",
      name: "second.png",
      sha256: "different",
    });
    const normal = mock.api.getMockImplementation()!;
    mock.api.mockImplementation(async (...args: unknown[]) => {
      if (args[0] === "/projects/final-audit/files/f1" && args[1] === "PATCH") {
        project = {
          ...project,
          files: project.files.map((f) =>
            f.id === "f1" ? { ...f, name: "saved-logo.png" } : f,
          ),
        };
        return project;
      }
      return normal(...args);
    });
    await open("03 Files");
    fireEvent.click(screen.getByRole("button", { name: "Rename logo.png" }));
    fireEvent.click(screen.getByRole("button", { name: "Rename second.png" }));
    const fields = screen.getAllByLabelText("Delivery filename");
    fireEvent.change(fields[0], { target: { value: "saved-logo.png" } });
    fireEvent.change(fields[1], { target: { value: "unsaved-second.png" } });
    fireEvent.submit(fields[0].closest("form")!);
    await screen.findByRole("button", { name: "Rename saved-logo.png" });
    fireEvent.click(screen.getByRole("button", { name: "04 Review" }));
    expect(confirm).toHaveBeenCalled();
    expect(
      (screen.getByLabelText("Delivery filename") as HTMLInputElement).value,
    ).toBe("unsaved-second.png");
  });
  it("a hidden rename editor retains the leave and browser-close warnings", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    await open("03 Files");
    fireEvent.click(screen.getByRole("button", { name: "Rename logo.png" }));
    fireEvent.change(screen.getByLabelText("Delivery filename"), {
      target: { value: "hidden-draft.png" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Rename logo.png" }));
    expect(screen.queryByLabelText("Delivery filename")).toBeNull();
    const closing = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(closing);
    expect(closing.defaultPrevented).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "04 Review" }));
    expect(confirm).toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Rename logo.png" }));
    expect(
      (screen.getByLabelText("Delivery filename") as HTMLInputElement).value,
    ).toBe("hidden-draft.png");
  });
  it("a saved filename clears only its own leave warning", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    const normal = mock.api.getMockImplementation()!;
    mock.api.mockImplementation(async (...args: unknown[]) => {
      if (args[0] === "/projects/final-audit/files/f1" && args[1] === "PATCH") {
        project = {
          ...project,
          files: [{ ...project.files[0], name: "saved.png" }],
        };
        return project;
      }
      return normal(...args);
    });
    await open("03 Files");
    fireEvent.click(screen.getByRole("button", { name: "Rename logo.png" }));
    fireEvent.change(screen.getByLabelText("Delivery filename"), {
      target: { value: "saved.png" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save filename" }));
    await screen.findByRole("button", { name: "Rename saved.png" });
    await waitFor(() =>
      expect(
        (
          screen.getByRole("button", {
            name: "Rename saved.png",
          }) as HTMLButtonElement
        ).disabled,
      ).toBe(false),
    );
    // Enabling the card ends the request, but its remount also schedules the
    // draft-marker cleanup and then the parent's leave-listener effect. Wait
    // for that actual completed behavior instead of asserting in between them.
    await waitFor(() => {
      const closing = new Event("beforeunload", { cancelable: true });
      window.dispatchEvent(closing);
      expect(closing.defaultPrevented).toBe(false);
    });
    fireEvent.click(screen.getByRole("button", { name: "04 Review" }));
    expect(confirm).not.toHaveBeenCalled();
    expect(screen.getByLabelText("Private review note")).toBeTruthy();
  });
  it("focuses the decision heading after selecting another requirement", async () => {
    project.baseline.requirements.push({
      ...project.baseline.requirements[0],
      id: "r2",
      title: "Second deliverable",
    });
    await open("04 Review");
    fireEvent.click(
      screen.getByRole("button", {
        name: "Second deliverable Needs your review",
      }),
    );
    expect(document.activeElement).toBe(
      screen.getByRole("heading", { level: 2, name: "Second deliverable" }),
    );
  });
  it("announces image preview failure", async () => {
    mock.imageUrl.mockRejectedValueOnce(new Error("Damaged preview"));
    await open("03 Files");
    fireEvent.click(
      screen.getByRole("button", { name: "Inspect image visually" }),
    );
    expect(await screen.findByRole("alert")).toHaveProperty(
      "textContent",
      "Damaged preview",
    );
  });
});
