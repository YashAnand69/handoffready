/** Isolated UI regressions; API doubles here do not establish model quality. */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import App from "./App";
import type { Project, CheckResult } from "./types";
const mock = vi.hoisted(() => ({
  api: vi.fn(),
  bootstrap: vi.fn(),
  download: vi.fn(),
}));
vi.mock("./api", () => mock);
let project: Project;
let preview: {
  input_hash: string;
  project_name: string;
  status: string;
  scope_notice: string;
  requirements: {
    id: string;
    title: string;
    origin: string;
    review_state: string;
    human_disposition: string;
    client_usage_note: string;
    checks: CheckResult[];
    files: [];
    gaps: string[];
  }[];
  gaps: { requirement_id: string; message: string }[];
};
beforeEach(() => {
  localStorage.clear();
  mock.api.mockReset();
  mock.bootstrap.mockResolvedValue({ token: "local" });
  project = {
    id: "audit-project",
    name: "Audit Desk",
    revision: 1,
    input_hash: "current",
    brief: {
      id: "b1",
      text: "Private agreed source.",
      label: "Brief",
      sha256: "brief",
    },
    baseline: {
      id: "base",
      hash: "hash",
      state: "approved",
      requirements: [
        {
          id: "r1",
          title: "Contact guide",
          origin: "human_added",
          quote: null,
          source_id: null,
          human_note: "Private clarification",
          checks: [{ kind: "manual", instruction: "Review the guide." }],
        },
      ],
    },
    files: [],
    proposals: [],
    decisions: [
      {
        requirement_id: "r1",
        file_ids: [],
        review_state: "confirmed",
        human_disposition: "satisfied",
        internal_decision_note: "PRIVATE INTERNAL NOTE",
        client_usage_note: "Use the settings page.",
        input_hash: "current",
      },
    ],
    jobs: [],
    exports: [],
    checks: [
      {
        requirement_id: "r1",
        kind: "manual",
        status: "unknown",
        reason: "Review the guide.",
      },
    ],
  };
  preview = {
    input_hash: "current",
    project_name: "Audit Desk",
    status: "reviewed",
    scope_notice: "Human review only.",
    requirements: [
      {
        id: "r1",
        title: "Contact guide",
        origin: "human_added",
        review_state: "confirmed",
        human_disposition: "satisfied",
        client_usage_note: "Use the settings page.",
        checks: [
          {
            requirement_id: "r1",
            kind: "manual",
            status: "unknown",
            reason: "Review the guide.",
          },
        ],
        files: [],
        gaps: [],
      },
    ],
    gaps: [],
  };
  mock.api.mockImplementation(async (path: string) =>
    path === "/projects"
      ? [{ id: project.id, name: project.name }]
      : path === "/capabilities"
        ? { model: { available: true } }
        : path.endsWith("/handoff-preview")
          ? preview
          : project,
  );
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
async function openPreview() {
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Audit Desk ↗" }));
  await screen.findByRole("heading", { name: "Audit Desk", level: 1 });
  fireEvent.click(screen.getByRole("button", { name: "05 Handoff" }));
  await screen.findByText("Use the settings page.");
}
describe("Client-safe review projection", () => {
  it("does not expose the exact private literal in a client-facing preview", async () => {
    project.baseline.requirements[0].checks = [
      { kind: "literal_text", needle: "PRIVATE_LITERAL_473" },
    ];
    project.checks = [
      {
        requirement_id: "r1",
        kind: "literal_text",
        status: "pass",
        reason: "Case-sensitive text checked.",
        expected: "PRIVATE_LITERAL_473",
        actual: true,
      },
    ];
    preview.requirements[0].checks = [
      {
        requirement_id: "r1",
        kind: "literal_text",
        status: "pass",
        reason: "Case-sensitive text checked.",
        actual: true,
      },
    ];
    await openPreview();
    expect(screen.queryByText(/PRIVATE_LITERAL_473/)).toBeNull();
    expect(screen.queryByText("PRIVATE INTERNAL NOTE")).toBeNull();
  });
  it("does not call a manually satisfied judgment an unresolved technical gap", async () => {
    await openPreview();
    expect(screen.queryByText(/item\(s\) still require attention/)).toBeNull();
  });
  it("respects an explicitly explained not-applicable disposition in gap counts", async () => {
    project.decisions[0].human_disposition = "not_applicable";
    preview.requirements[0].human_disposition = "not_applicable";
    project.decisions[0].internal_decision_note =
      "Client removed this deliverable from scope.";
    project.checks = [
      {
        requirement_id: "r1",
        kind: "presence",
        status: "fail",
        reason: "No matching file.",
      },
    ];
    await openPreview();
    expect(screen.queryByText(/item\(s\) still require attention/)).toBeNull();
  });
});

async function openWorkspace() {
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Audit Desk ↗" }));
  await screen.findByRole("heading", { name: "Audit Desk", level: 1 });
}
describe("Edit and privacy safeguards", () => {
  it("retains unsaved checklist edits when navigation discard is declined", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    await openWorkspace();
    fireEvent.click(screen.getByRole("button", { name: "02 Checklist" }));
    fireEvent.change(screen.getByLabelText("Requirement"), {
      target: { value: "Changed contact guide" },
    });
    fireEvent.click(screen.getByRole("button", { name: "03 Files" }));
    expect(confirm).toHaveBeenCalled();
    expect(
      (screen.getByLabelText("Requirement") as HTMLInputElement).value,
    ).toBe("Changed contact guide");
    const event = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
  });
  it("retains private review notes when the handoff shortcut discard is declined", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    await openWorkspace();
    fireEvent.click(screen.getByRole("button", { name: "04 Review" }));
    fireEvent.change(screen.getByLabelText("Private review note"), {
      target: { value: "Unsaved private reasoning" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Preview handoff →" }));
    expect(confirm).toHaveBeenCalled();
    expect(
      (screen.getByLabelText("Private review note") as HTMLTextAreaElement)
        .value,
    ).toBe("Unsaved private reasoning");
  });
  it("removes all browser brief versions when the project is deleted", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    localStorage.setItem(
      "handoff-brief-audit-project-old",
      "Old private source",
    );
    localStorage.setItem(
      "handoff-brief-audit-project-brief",
      "Current private source",
    );
    localStorage.setItem("unrelated-preference", "Preserve");
    await openWorkspace();
    fireEvent.click(
      screen.getByRole("button", { name: "Delete this project" }),
    );
    await waitFor(() =>
      expect(
        localStorage.getItem("handoff-brief-audit-project-brief"),
      ).toBeNull(),
    );
    expect(localStorage.getItem("handoff-brief-audit-project-old")).toBeNull();
    expect(localStorage.getItem("unrelated-preference")).toBe("Preserve");
  });
  it("ignores a recovered draft from a different saved brief version", async () => {
    localStorage.setItem(
      "handoff-brief-audit-project-old",
      "Stale private source",
    );
    await openWorkspace();
    fireEvent.click(screen.getByRole("button", { name: "01 Brief" }));
    expect(
      (screen.getByLabelText("Agreed brief") as HTMLTextAreaElement).value,
    ).toBe("Private agreed source.");
  });
  it("removes recovered browser drafts only after the brief is saved successfully", async () => {
    localStorage.setItem(
      "handoff-brief-audit-project-brief",
      "Recovered private draft",
    );
    await openWorkspace();
    fireEvent.click(screen.getByRole("button", { name: "01 Brief" }));
    fireEvent.click(
      screen.getByRole("button", { name: "Save brief & continue →" }),
    );
    await waitFor(() =>
      expect(
        localStorage.getItem("handoff-brief-audit-project-brief"),
      ).toBeNull(),
    );
  });
  it("serializes duplicate project submissions before state has rerendered", async () => {
    let release: (p: Project) => void = () => {};
    const pending = new Promise<Project>((resolve) => {
      release = resolve;
    });
    mock.api.mockImplementation(async (path: string, method = "GET") =>
      path === "/projects"
        ? method === "POST"
          ? pending
          : []
        : path === "/capabilities"
          ? { model: { available: false } }
          : project,
    );
    render(<App />);
    await screen.findByText("A clear desk. A fresh start.");
    fireEvent.change(screen.getByLabelText("Project name"), {
      target: { value: "One project" },
    });
    await waitFor(() =>
      expect(
        (
          screen.getByRole("button", {
            name: /Create a handoff/,
          }) as HTMLButtonElement
        ).disabled,
      ).toBe(false),
    );
    const form = screen.getByLabelText("Project name").closest("form")!;
    act(() => {
      fireEvent.submit(form);
      fireEvent.submit(form);
    });
    expect(
      mock.api.mock.calls.filter(
        (args) => args[0] === "/projects" && args[1] === "POST",
      ),
    ).toHaveLength(1);
    await act(async () => {
      release(project);
      await pending;
    });
  });
});

describe("Refactored workflow edit boundaries", () => {
  it("does not clear the leave warning by clicking the current workflow step", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    await openWorkspace();
    fireEvent.click(screen.getByRole("button", { name: "02 Checklist" }));
    fireEvent.change(screen.getByLabelText("Requirement"), {
      target: { value: "Unsaved checklist title" },
    });
    fireEvent.click(screen.getByRole("button", { name: "02 Checklist" }));
    fireEvent.click(screen.getByRole("button", { name: "03 Files" }));
    expect(confirm).toHaveBeenCalled();
    expect(
      (screen.getByLabelText("Requirement") as HTMLInputElement).value,
    ).toBe("Unsaved checklist title");
  });
  it("prevents changing the brief while its save is in progress", async () => {
    let release: (value: Project) => void = () => {};
    const pending = new Promise<Project>((resolve) => {
      release = resolve;
    });
    const defaultApi = mock.api.getMockImplementation()!;
    mock.api.mockImplementation(async (...args: unknown[]) => {
      if (args[0] === "/projects/audit-project/brief" && args[1] === "PUT")
        return pending;
      return defaultApi(...args);
    });
    await openWorkspace();
    fireEvent.click(screen.getByRole("button", { name: "01 Brief" }));
    fireEvent.change(screen.getByLabelText("Agreed brief"), {
      target: { value: "Saved draft" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Save brief & continue →" }),
    );
    expect(
      (screen.getByLabelText("Agreed brief") as HTMLTextAreaElement).disabled,
    ).toBe(true);
    expect(
      (screen.getByLabelText("Source label") as HTMLInputElement).disabled,
    ).toBe(true);
    await act(async () => {
      release(project);
      await pending;
    });
  });
});
