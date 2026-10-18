/** Integrated navigation checks; API doubles do not establish model accuracy. */
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  act,
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
  mock.bootstrap.mockResolvedValue({ token: "local" });
  project = {
    id: "desk",
    name: "Delivery desk",
    revision: 4,
    input_hash: "current",
    brief: {
      id: "brief",
      text: "Deliver a logo, guide, and website.",
      label: "Brief",
      sha256: "brief-hash",
    },
    baseline: {
      id: "baseline",
      hash: "baseline",
      state: "approved",
      requirements: ["Logo", "Guide", "Website"].map((title, index) => ({
        id: `r${index}`,
        title,
        origin: "human_added",
        quote: null,
        source_id: null,
        human_note: "Agreed requirement",
        checks: [{ kind: "manual", instruction: "Inspect the deliverable" }],
      })),
    },
    files: ["logo.png", "guide.txt"].map((name, index) => ({
      id: `f${index}`,
      name,
      type: index ? "text" : "png",
      size: 20,
      sha256: `hash${index}`,
      inspection: "inspected",
      metadata: {},
      text: "",
      error: null,
    })),
    decisions: [
      {
        requirement_id: "r0",
        file_ids: ["f0"],
        review_state: "confirmed",
        human_disposition: "satisfied",
        internal_decision_note: "Saved",
        client_usage_note: "",
        input_hash: "current",
      },
    ],
    proposals: [],
    jobs: [],
    exports: [],
    checks: [],
    attention_summary: {
      contract_version: 1,
      source_revision: 4,
      input_hash: "current",
      baseline_approved: true,
      status: "draft_with_gaps",
      requirement_count: 3,
      current_review_count: 1,
      stale_review_count: 0,
      unreviewed_count: 2,
      needs_work_count: 0,
      unresolved_count: 2,
      exception_count: 0,
      failed_check_count: 0,
      unknown_check_count: 0,
      manual_requirement_count: 3,
      failed_requirement_ids: [],
      unknown_requirement_ids: [],
      attention_requirement_ids: ["r1", "r2"],
      exception_requirement_ids: [],
      rows: (["current", "unreviewed", "unreviewed"] as const).map(
        (currency, index) => ({
          requirement_id: `r${index}`,
          review_currency: currency,
          human_disposition: index ? "unresolved" : "satisfied",
          applicable_attention: index > 0,
          is_exception: false,
          reason_codes: [],
          messages: [],
          failed_check_count: 0,
          unknown_check_count: 0,
          has_manual_checks: true,
        }),
      ),
    },
  };
  mock.api.mockImplementation(async (path: string) => {
    if (path === "/projects") return [{ id: project.id, name: project.name }];
    if (path === "/capabilities") return { model: { available: false } };
    if (path === "/projects/desk") return structuredClone(project);
    throw new Error(`Unexpected test request: ${path}`);
  });
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
async function open() {
  render(<App />);
  fireEvent.click(
    await screen.findByRole("button", { name: "Delivery desk ↗" }),
  );
  await screen.findByRole("heading", { name: "Guide", level: 2 });
}
function changeReview() {
  fireEvent.click(screen.getByRole("checkbox", { name: /guide.txt/ }));
  fireEvent.change(screen.getByLabelText("Private review note"), {
    target: { value: "Read the guide and checked its steps." },
  });
  fireEvent.change(screen.getByLabelText("Your assessment"), {
    target: { value: "satisfied" },
  });
}
it("resumes a saved handoff at the first server attention requirement", async () => {
  await open();
  expect(screen.queryByLabelText("Agreed brief")).toBeNull();
  expect(screen.getByRole("heading", { name: "Guide", level: 2 })).toBeTruthy();
  expect(
    screen
      .getByRole("button", { name: /04 Review/ })
      .getAttribute("aria-current"),
  ).toBe("step");
  expect(mock.api.mock.calls.filter((call) => call[1] === "PUT")).toHaveLength(
    0,
  );
});
it("advances only after both saving and authoritative project refresh finish", async () => {
  await open();
  const original = mock.api.getMockImplementation()!;
  let releaseSave: (result: unknown) => void = () => {};
  let releaseRefresh: (result: unknown) => void = () => {};
  const pendingSave = new Promise((resolve) => {
    releaseSave = resolve;
  });
  const pendingRefresh = new Promise((resolve) => {
    releaseRefresh = resolve;
  });
  mock.api.mockImplementation(
    (path: string, method?: string, ...rest: unknown[]) => {
      if (path === "/projects/desk/decisions/r1" && method === "PUT")
        return pendingSave;
      if (path === "/projects/desk") return pendingRefresh;
      return original(path, method, ...rest);
    },
  );
  changeReview();
  fireEvent.click(screen.getByRole("button", { name: "Save and next item →" }));
  expect(screen.getByRole("heading", { name: "Guide", level: 2 })).toBeTruthy();
  expect(
    (
      screen.getByRole("button", {
        name: "Save and next item →",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  await act(async () => {
    releaseSave({});
    await pendingSave;
  });
  expect(screen.getByRole("heading", { name: "Guide", level: 2 })).toBeTruthy();
  project.revision += 1;
  project.attention_summary!.source_revision += 1;
  project.attention_summary!.attention_requirement_ids = ["r2"];
  project.attention_summary!.rows[1].review_currency = "current";
  project.attention_summary!.rows[1].human_disposition = "satisfied";
  await act(async () => {
    releaseRefresh(structuredClone(project));
    await pendingRefresh;
  });
  await screen.findByRole("heading", { name: "Website", level: 2 });
  const writes = mock.api.mock.calls.filter((call) => call[1] === "PUT");
  expect(writes).toHaveLength(1);
  expect(writes[0]).toEqual([
    "/projects/desk/decisions/r1",
    "PUT",
    expect.objectContaining({
      file_ids: ["f1"],
      human_disposition: "satisfied",
      internal_decision_note: "Read the guide and checked its steps.",
      input_hash: "current",
    }),
    4,
  ]);
});
it("finishes unreviewed items before revisiting saved needs-work decisions", async () => {
  await open();
  const original = mock.api.getMockImplementation()!;
  project.attention_summary!.rows[0].human_disposition = "needs_work";
  project.attention_summary!.attention_requirement_ids = ["r0", "r1", "r2"];
  mock.api.mockImplementation(
    async (path: string, method?: string, ...rest: unknown[]) => {
      if (path.startsWith("/projects/desk/decisions/") && method === "PUT") {
        const id = path.split("/").at(-1)!;
        const row = project.attention_summary!.rows.find(
          (entry) => entry.requirement_id === id,
        )!;
        row.review_currency = "current";
        row.human_disposition = "needs_work";
        project.revision += 1;
        project.attention_summary!.source_revision = project.revision;
        return {};
      }
      if (path === "/projects/desk/handoff-preview")
        return {
          project_name: project.name,
          input_hash: project.input_hash,
          source_revision: project.revision,
          status: "draft_with_gaps",
          scope_notice: "Synthetic test record",
          gaps: [{ requirement_id: "r0", message: "Still needs work" }],
          requirements: [],
        };
      return original(path, method, ...rest);
    },
  );
  changeReview();
  fireEvent.change(screen.getByLabelText("Your assessment"), {
    target: { value: "needs_work" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Save and next item →" }));
  await screen.findByRole("heading", { name: "Website", level: 2 });
  fireEvent.change(screen.getByLabelText("Your assessment"), {
    target: { value: "needs_work" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Save and next item →" }));
  await screen.findByRole("heading", {
    name: "A clear record of this delivery.",
  });
  await screen.findByText(/still require attention or clarification/);
  expect(project.attention_summary!.attention_requirement_ids).toEqual([
    "r0",
    "r1",
    "r2",
  ]);
  expect(project.attention_summary!.status).toBe("draft_with_gaps");
});
it("retains notes, selection and current item when saving fails", async () => {
  await open();
  const original = mock.api.getMockImplementation()!;
  mock.api.mockImplementation(
    (path: string, method?: string, ...rest: unknown[]) =>
      path === "/projects/desk/decisions/r1" && method === "PUT"
        ? Promise.reject(new Error("Could not save this review"))
        : original(path, method, ...rest),
  );
  changeReview();
  fireEvent.click(screen.getByRole("button", { name: "Save and next item →" }));
  await screen.findByText("Could not save this review");
  await waitFor(() =>
    expect(
      (
        screen.getByRole("button", {
          name: "Save and next item →",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(false),
  );
  expect(screen.getByRole("heading", { name: "Guide", level: 2 })).toBeTruthy();
  expect(
    (screen.getByLabelText("Private review note") as HTMLTextAreaElement).value,
  ).toBe("Read the guide and checked its steps.");
  expect(
    (screen.getByRole("checkbox", { name: /guide.txt/ }) as HTMLInputElement)
      .checked,
  ).toBe(true);
  expect(
    screen.queryByRole("heading", { name: "Website", level: 2 }),
  ).toBeNull();
  const event = new Event("beforeunload", { cancelable: true });
  window.dispatchEvent(event);
  expect(event.defaultPrevented).toBe(true);
});
it("search and queue filters do not create unsaved-review warnings", async () => {
  const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
  await open();
  fireEvent.change(screen.getByLabelText("Find a requirement"), {
    target: { value: "Guide" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Needs review" }));
  fireEvent.change(screen.getByLabelText("Find a delivery file"), {
    target: { value: "guide" },
  });
  const event = new Event("beforeunload", { cancelable: true });
  window.dispatchEvent(event);
  expect(event.defaultPrevented).toBe(false);
  fireEvent.click(screen.getByRole("button", { name: /03 Files/ }));
  await screen.findByRole("heading", {
    name: "Bring what you plan to deliver.",
  });
  expect(confirm).not.toHaveBeenCalled();
  expect(mock.api.mock.calls.filter((call) => call[1] === "PUT")).toHaveLength(
    0,
  );
});
it("keeps unsaved review protection when Continue already targets the current item", async () => {
  const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
  await open();
  changeReview();
  fireEvent.click(screen.getByRole("button", { name: "Continue →" }));
  expect(confirm).not.toHaveBeenCalled();
  expect(
    (screen.getByLabelText("Private review note") as HTMLTextAreaElement).value,
  ).toBe("Read the guide and checked its steps.");
  const event = new Event("beforeunload", { cancelable: true });
  window.dispatchEvent(event);
  expect(event.defaultPrevented).toBe(true);
});

it("shows saved review context without claiming the originals are verified", async () => {
  const implementation = mock.api.getMockImplementation()!;
  mock.api.mockImplementation(async (path: string, ...args: unknown[]) => {
    if (path === "/projects")
      return [
        {
          id: project.id,
          name: project.name,
          saved_review: {
            status: "draft_with_gaps",
            baseline_approved: true,
            requirement_count: 3,
            attention_count: 2,
            stale_review_count: 1,
            file_count: 2,
            originals_verified: false,
          },
        },
      ];
    return implementation(path, ...args);
  });
  render(<App />);
  expect(
    await screen.findByText("Saved review: 2 of 3 items need attention"),
  ).toBeTruthy();
  expect(screen.getByText("2 files · 1 stale review")).toBeTruthy();
  expect(
    screen.getByText(
      "Saved review status. Original files are verified when you open a handoff.",
    ),
  ).toBeTruthy();
  expect(screen.queryByText(/Updated/)).toBeNull();
});
