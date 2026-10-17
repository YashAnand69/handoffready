/** Observable workflow regressions; API doubles do not substantiate model accuracy. */
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  act,
  cleanup,
  within,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import App from "./App";
import SourceEvidence from "./components/SourceEvidence";
import type { AttentionSummary, Project, SourceSpan } from "./types";
const mock = vi.hoisted(() => ({
  api: vi.fn(),
  bootstrap: vi.fn(),
  download: vi.fn(),
}));
vi.mock("./api", () => mock);
let project: Project;
let summary: AttentionSummary;
beforeEach(() => {
  localStorage.clear();
  mock.api.mockReset();
  mock.bootstrap.mockResolvedValue({ token: "local" });
  summary = {
    contract_version: 1,
    source_revision: 3,
    input_hash: "input",
    baseline_approved: true,
    status: "draft_with_gaps",
    requirement_count: 2,
    current_review_count: 1,
    stale_review_count: 0,
    unreviewed_count: 1,
    needs_work_count: 0,
    unresolved_count: 1,
    exception_count: 0,
    failed_check_count: 1,
    unknown_check_count: 0,
    manual_requirement_count: 1,
    failed_requirement_ids: ["r1"],
    unknown_requirement_ids: [],
    attention_requirement_ids: ["r2"],
    exception_requirement_ids: [],
    rows: [],
  };
  project = {
    id: "upgrade",
    name: "Upgrade test",
    revision: 3,
    input_hash: "input",
    brief: {
      id: "brief",
      text: "Deliver a logo. Deliver a guide.",
      label: "Brief",
      sha256: "hash",
    },
    baseline: {
      id: "base",
      hash: "baseline",
      state: "approved",
      requirements: [
        {
          id: "r1",
          title: "Logo",
          origin: "human_added",
          quote: null,
          source_id: null,
          human_note: "Manual scope",
          checks: [{ kind: "presence", types: ["png"] }],
        },
        {
          id: "r2",
          title: "Guide",
          origin: "human_added",
          quote: null,
          source_id: null,
          human_note: "Manual scope",
          checks: [{ kind: "manual", instruction: "Read guide" }],
        },
      ],
    },
    files: [],
    proposals: [],
    jobs: [],
    exports: [],
    attention_summary: summary,
    decisions: [
      {
        requirement_id: "r1",
        file_ids: [],
        review_state: "confirmed",
        human_disposition: "satisfied",
        internal_decision_note: "PRIVATE_NOTE_147",
        client_usage_note: "",
        input_hash: "input",
      },
    ],
    checks: [
      {
        requirement_id: "r1",
        kind: "presence",
        status: "fail",
        reason: "No PNG selected.",
      },
    ],
  };
  mock.api.mockImplementation(async (path: string) =>
    path === "/projects"
      ? [{ id: project.id, name: project.name }]
      : path === "/capabilities"
        ? { model: { available: false } }
        : path.endsWith("handoff-preview")
          ? {
              project_name: project.name,
              input_hash: project.input_hash,
              source_revision: project.revision,
              status: summary.status,
              attention_summary: summary,
              scope_notice: "Narrow findings, human review.",
              files: [
                {
                  id: "f",
                  name: "deliverable.png",
                  type: "png",
                  size: 100,
                  sha256: "abc",
                },
              ],
              requirements: [
                {
                  id: "r1",
                  title: "Logo",
                  review_state: "confirmed",
                  human_disposition: "satisfied",
                  client_usage_note: "",
                  checks: project.checks,
                  files: [],
                  gaps: ["Missing PNG."],
                },
              ],
              gaps: [{ requirement_id: "r1", message: "Missing PNG." }],
            }
          : project,
  );
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.useRealTimers();
});
async function open(step = "04 Review") {
  render(<App />);
  fireEvent.click(
    await screen.findByRole("button", { name: "Upgrade test ↗" }),
  );
  await screen.findByRole("heading", { name: "Upgrade test", level: 1 });
  fireEvent.click(screen.getByRole("button", { name: step }));
}
it("locates the correct repeated occurrence after an emoji using code points", () => {
  const text = "😀 Repeat.\r\nRepeat.";
  const span: SourceSpan = {
    source_unit_id: "brief",
    source_text_sha256: "h",
    start_cp: 11,
    end_cp: 18,
    quote: "Repeat.",
  };
  render(
    <SourceEvidence
      text={text}
      quote={span.quote}
      span={span}
      unitId="occurrence-2"
      label="Brief source"
    />,
  );
  fireEvent.click(screen.getByText("View exact source location"));
  const marked = document.querySelector("mark")!;
  expect(marked.textContent).toBe("Repeat.");
  expect(marked.previousSibling?.textContent).toBe("😀 Repeat.\r\n");
});
it("does not highlight a forged or stale source range", () => {
  render(
    <SourceEvidence
      text="Actual text"
      quote="Invented text"
      span={{
        source_unit_id: "b",
        source_text_sha256: "h",
        start_cp: 0,
        end_cp: 5,
        quote: "Invented text",
      }}
      label="Brief source"
    />,
  );
  expect(screen.queryByText("View exact source location")).toBeNull();
  expect(screen.getByText(/Exact occurrence unavailable/)).toBeTruthy();
});
it("keeps dirty review edits when attention navigation is declined", async () => {
  const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
  await open();
  fireEvent.change(screen.getByLabelText("Private review note"), {
    target: { value: "Unsaved reasoning" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Review outstanding items →" }),
  );
  expect(confirm).toHaveBeenCalled();
  expect(
    (screen.getByLabelText("Private review note") as HTMLTextAreaElement).value,
  ).toBe("Unsaved reasoning");
  expect(screen.getByRole("heading", { name: "Logo", level: 2 })).toBeTruthy();
});
it("attention navigation selects the server-identified requirement and focuses it", async () => {
  await open();
  fireEvent.click(
    screen.getByRole("button", { name: "Review outstanding items →" }),
  );
  expect(document.activeElement).toBe(
    screen.getByRole("heading", { name: "Guide", level: 2 }),
  );
});
it("separates satisfied human assessment from failed technical findings", async () => {
  await open();
  const queue = screen.getByRole("button", {
    name: "Logo confirmed · satisfied",
  });
  expect(queue.textContent).toContain("1 technical failure(s)");
  expect(
    screen.getByRole("heading", {
      name: "Draft · attention required",
      level: 2,
    }),
  ).toBeTruthy();
});
it("saves an explicitly entered public exception separately from private notes", async () => {
  await open();
  fireEvent.change(screen.getByLabelText("Your assessment"), {
    target: { value: "not_applicable" },
  });
  fireEvent.change(
    screen.getByLabelText("Client-facing exception explanation (public)"),
    { target: { value: "Excluded from this delivery by reviewer." } },
  );
  fireEvent.click(screen.getByRole("button", { name: "Save my review" }));
  await waitFor(() =>
    expect(
      mock.api.mock.calls.find(
        (args) =>
          args[0] === "/projects/upgrade/decisions/r1" && args[1] === "PUT",
      ),
    ).toBeTruthy(),
  );
  const payload = mock.api.mock.calls.find(
    (args) => args[0] === "/projects/upgrade/decisions/r1" && args[1] === "PUT",
  )![2];
  expect(payload.client_exception_note).toBe(
    "Excluded from this delivery by reviewer.",
  );
  expect(payload.internal_decision_note).toBe("PRIVATE_NOTE_147");
});
it("renders only the client projection, with originals instruction and file inventory", async () => {
  await open("05 Handoff");
  await screen.findByText("deliverable.png");
  expect(screen.getByText("Delivery file inventory")).toBeTruthy();
  expect(
    screen.getByText("Send the original files alongside this record."),
  ).toBeTruthy();
  expect(screen.queryByText("PRIVATE_NOTE_147")).toBeNull();
  expect(
    screen.getByRole("button", { name: "Return to review: Logo →" }),
  ).toBeTruthy();
});
it("rejects a preview from another review revision before acknowledgement", async () => {
  const normal = mock.api.getMockImplementation()!;
  mock.api.mockImplementation(async (...args: unknown[]) => {
    const result = await normal(...args);
    return String(args[0]).endsWith("handoff-preview")
      ? { ...result, source_revision: 2 }
      : result;
  });
  await open("05 Handoff");
  await screen.findByText(
    "The delivery preview is out of date. Retry before preparing a snapshot.",
  );
  expect(
    (
      screen.getByRole("button", {
        name: "Prepare handoff snapshot →",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
});
it("keeps explained scope exceptions distinct from clean reviewed status and retains failed counts", async () => {
  summary.status = "reviewed_with_exceptions";
  summary.exception_count = 1;
  summary.attention_requirement_ids = [];
  summary.exception_requirement_ids = ["r1"];
  await open();
  const heading = screen.getByRole("heading", {
    name: "Reviewed with scope exceptions",
    level: 2,
  });
  expect(heading).toBeTruthy();
  const counts = screen.getByText("Failed technical checks").closest("div")!;
  expect(counts.textContent).toContain("1");
  expect(
    screen.queryByRole("button", { name: "Review outstanding items →" }),
  ).toBeNull();
  expect(screen.getByText(/Underlying findings remain visible/)).toBeTruthy();
});
it("treats a saved assessment on older inputs as stale instead of a current satisfaction", async () => {
  project.decisions[0].input_hash = "older-input";
  await open();
  expect(
    screen.getByRole("button", { name: "Logo Stale · needs fresh review" }),
  ).toBeTruthy();
  expect(
    (screen.getByLabelText("Your assessment") as HTMLSelectElement).value,
  ).toBe("unresolved");
  expect(screen.getByText(/The packet or checklist changed/)).toBeTruthy();
});
it("submits the exact acknowledged preview revision when preparing an export", async () => {
  await open("05 Handoff");
  await screen.findByText("deliverable.png");
  fireEvent.click(
    screen.getByRole("checkbox", { name: /I reviewed this preview/ }),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Prepare handoff snapshot →" }),
  );
  await waitFor(() =>
    expect(
      mock.api.mock.calls.find(
        (args) => args[0] === "/projects/upgrade/exports" && args[1] === "POST",
      ),
    ).toBeTruthy(),
  );
  const request = mock.api.mock.calls.find(
    (args) => args[0] === "/projects/upgrade/exports" && args[1] === "POST",
  )!;
  expect(request[2]).toEqual({
    acknowledge_unresolved: true,
    input_hash: "input",
    preview_revision: 3,
  });
  expect(request[3]).toBe(3);
});
function addPreviewFile() {
  project.files = [
    {
      id: "f1",
      name: "logo.png",
      type: "png",
      size: 1,
      sha256: "filehash",
      inspection: "inspected",
      metadata: {},
      text: "",
      error: null,
    },
  ];
}
function selectionResponse(ids: string[]) {
  return {
    preview: true,
    project_id: project.id,
    requirement_id: "r1",
    source_revision: project.revision,
    input_hash: project.input_hash,
    file_ids: ids,
    selection_hash: "selection",
    checks: [
      {
        requirement_id: "r1",
        kind: "presence",
        status: "pass",
        reason: "DRAFT PNG FOUND",
      },
    ],
  };
}
it("previews a draft selection with a revision guard without saving or changing saved facts", async () => {
  addPreviewFile();
  const normal = mock.api.getMockImplementation()!;
  mock.api.mockImplementation(async (...args: unknown[]) =>
    String(args[0]).endsWith("check-preview")
      ? selectionResponse(["f1"])
      : normal(...args),
  );
  await open();
  fireEvent.click(screen.getByRole("button", { name: /^Logo confirmed/ }));
  fireEvent.click(screen.getByRole("checkbox", { name: /logo.png/ }));
  fireEvent.change(screen.getByLabelText("Private review note"), {
    target: { value: "Still unsaved" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Preview selected files" }),
  );
  const panel = screen.getByRole("region", {
    name: "Unsaved selection preview",
  });
  expect(await within(panel).findByText("DRAFT PNG FOUND")).toBeTruthy();
  expect(screen.getByText("No PNG selected.")).toBeTruthy();
  expect(
    (screen.getByLabelText("Private review note") as HTMLTextAreaElement).value,
  ).toBe("Still unsaved");
  expect(
    mock.api.mock.calls.find((args) => String(args[0]).includes("/decisions/")),
  ).toBeUndefined();
  const request = mock.api.mock.calls.find((args) =>
    String(args[0]).endsWith("check-preview"),
  )!;
  expect(request.slice(1)).toEqual([
    "POST",
    { file_ids: ["f1"], input_hash: "input" },
    3,
  ]);
});
it("discards a late draft-preview reply after the selection changes", async () => {
  addPreviewFile();
  let resolve!: (response: unknown) => void;
  const pending = new Promise((done) => {
    resolve = done;
  });
  const normal = mock.api.getMockImplementation()!;
  mock.api.mockImplementation(async (...args: unknown[]) =>
    String(args[0]).endsWith("check-preview") ? pending : normal(...args),
  );
  await open();
  fireEvent.click(screen.getByRole("button", { name: /^Logo confirmed/ }));
  fireEvent.click(screen.getByRole("checkbox", { name: /logo.png/ }));
  fireEvent.click(
    screen.getByRole("button", { name: "Preview selected files" }),
  );
  fireEvent.click(screen.getByRole("checkbox", { name: /logo.png/ }));
  await act(async () => {
    resolve(selectionResponse(["f1"]));
    await pending;
  });
  expect(screen.queryByText("DRAFT PNG FOUND")).toBeNull();
  expect(screen.getByText("No PNG selected.")).toBeTruthy();
});
it("retains the draft and saved facts when a selected-file preview requires refreshed inputs", async () => {
  addPreviewFile();
  const normal = mock.api.getMockImplementation()!;
  mock.api.mockImplementation(async (...args: unknown[]) => {
    if (String(args[0]).endsWith("check-preview"))
      throw new Error("Original file changed; refresh required.");
    return normal(...args);
  });
  await open();
  fireEvent.click(screen.getByRole("button", { name: /^Logo confirmed/ }));
  fireEvent.click(screen.getByRole("checkbox", { name: /logo.png/ }));
  fireEvent.change(screen.getByLabelText("Private review note"), {
    target: { value: "Retain reasoning" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Preview selected files" }),
  );
  expect(await screen.findByRole("alert")).toHaveProperty(
    "textContent",
    expect.stringContaining("Original file changed"),
  );
  expect(
    (screen.getByRole("checkbox", { name: /logo.png/ }) as HTMLInputElement)
      .checked,
  ).toBe(true);
  expect(
    (screen.getByLabelText("Private review note") as HTMLTextAreaElement).value,
  ).toBe("Retain reasoning");
  expect(screen.getByText("No PNG selected.")).toBeTruthy();
});
async function openPolling() {
  vi.useFakeTimers();
  await act(async () => {
    render(<App />);
  });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "Upgrade test ↗" }));
  });
}
it("polls only job status while inference is active and reconciles once at completion", async () => {
  project.jobs = [
    {
      id: "job",
      kind: "extract",
      state: "running",
      stage: "Generating",
      error: null,
    },
  ];
  let completed = false;
  const normal = mock.api.getMockImplementation()!;
  mock.api.mockImplementation(async (...args: unknown[]) =>
    String(args[0]).endsWith("job-status")
      ? {
          revision: 4,
          jobs: project.jobs.map((job) => ({
            ...job,
            state: completed ? "succeeded" : "running",
            stage: "Status-only stage",
          })),
        }
      : args[0] === "/projects/upgrade" && completed
        ? {
            ...project,
            jobs: project.jobs.map((job) => ({ ...job, state: "succeeded" })),
            revision: 4,
          }
        : normal(...args),
  );
  await openPolling();
  const initialReads = mock.api.mock.calls.filter(
    (args) => args[0] === "/projects/upgrade",
  ).length;
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1400);
  });
  expect(
    mock.api.mock.calls.filter((args) => args[0] === "/projects/upgrade"),
  ).toHaveLength(initialReads);
  expect(screen.getByText("extract · Status-only stage")).toBeTruthy();
  completed = true;
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1400);
  });
  expect(
    mock.api.mock.calls.filter((args) => args[0] === "/projects/upgrade"),
  ).toHaveLength(initialReads + 1);
  expect(
    screen.getByText(/Local checklist suggestions are ready/),
  ).toBeTruthy();
  const statusReads = mock.api.mock.calls.filter((args) =>
    String(args[0]).endsWith("job-status"),
  ).length;
  await act(async () => {
    await vi.advanceTimersByTimeAsync(2800);
  });
  expect(
    mock.api.mock.calls.filter((args) =>
      String(args[0]).endsWith("job-status"),
    ),
  ).toHaveLength(statusReads);
});
it("reports status-poll failure without claiming model completion", async () => {
  project.jobs = [
    {
      id: "job",
      kind: "extract",
      state: "running",
      stage: "Generating",
      error: null,
    },
  ];
  const normal = mock.api.getMockImplementation()!;
  mock.api.mockImplementation(async (...args: unknown[]) => {
    if (String(args[0]).endsWith("job-status"))
      throw new Error("Status service unavailable");
    return normal(...args);
  });
  await openPolling();
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1400);
  });
  expect(screen.getByRole("alert").textContent).toContain(
    "Status service unavailable",
  );
  expect(
    screen.queryByText(/Local checklist suggestions are ready/),
  ).toBeNull();
});
it("rejects preview identities that do not match the current draft", async () => {
  const normal = mock.api.getMockImplementation()!;
  mock.api.mockImplementation(async (...args: unknown[]) =>
    String(args[0]).endsWith("check-preview")
      ? { ...selectionResponse([]), source_revision: 2 }
      : normal(...args),
  );
  await open();
  fireEvent.click(
    screen.getByRole("button", { name: "Preview selected files" }),
  );
  expect(await screen.findByRole("alert")).toHaveProperty(
    "textContent",
    "This selection preview is out of date. Request it again for your current selection.",
  );
  expect(screen.queryByText("DRAFT PNG FOUND")).toBeNull();
});
it("discards a preview reply when another requirement is opened", async () => {
  let resolve!: (response: unknown) => void;
  const pending = new Promise((done) => {
    resolve = done;
  });
  const normal = mock.api.getMockImplementation()!;
  mock.api.mockImplementation(async (...args: unknown[]) =>
    String(args[0]).endsWith("check-preview") ? pending : normal(...args),
  );
  await open();
  fireEvent.click(
    screen.getByRole("button", { name: "Preview selected files" }),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Guide Needs your review" }),
  );
  await act(async () => {
    resolve(selectionResponse([]));
    await pending;
  });
  expect(screen.queryByText("DRAFT PNG FOUND")).toBeNull();
  expect(screen.getByRole("heading", { name: "Guide", level: 2 })).toBeTruthy();
});
it("rejects a late terminal refresh after switching to another handoff", async () => {
  project.jobs = [
    {
      id: "job",
      kind: "extract",
      state: "running",
      stage: "Generating",
      error: null,
    },
  ];
  const other = { ...project, id: "other", name: "Other handoff", jobs: [] };
  let resolve!: (response: Project) => void;
  const pending = new Promise<Project>((done) => {
    resolve = done;
  });
  let originalReads = 0;
  const normal = mock.api.getMockImplementation()!;
  mock.api.mockImplementation(async (...args: unknown[]) => {
    if (args[0] === "/projects")
      return [
        { id: project.id, name: project.name },
        { id: other.id, name: other.name },
      ];
    if (args[0] === "/projects/other") return other;
    if (String(args[0]).endsWith("job-status"))
      return {
        revision: 4,
        jobs: project.jobs.map((job) => ({ ...job, state: "succeeded" })),
      };
    if (args[0] === "/projects/upgrade" && ++originalReads > 1) return pending;
    return normal(...args);
  });
  await openPolling();
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1400);
  });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "← All handoffs" }));
  });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "Other handoff ↗" }));
  });
  await act(async () => {
    resolve({
      ...project,
      jobs: project.jobs.map((job) => ({ ...job, state: "succeeded" })),
      revision: 4,
    });
    await pending;
  });
  expect(
    screen.getByRole("heading", { name: "Other handoff", level: 1 }),
  ).toBeTruthy();
  expect(
    screen.queryByRole("heading", { name: "Upgrade test", level: 1 }),
  ).toBeNull();
  expect(
    screen.queryByText(/Local checklist suggestions are ready/),
  ).toBeNull();
});
it("focuses the actual workflow heading rather than the attention overview", async () => {
  await open("03 Files");
  const heading = document.querySelector(".workspace-step h2");
  expect(heading).toBeTruthy();
  expect(document.activeElement).toBe(heading);
  expect(document.activeElement).not.toBe(
    screen.getByRole("heading", {
      name: "Draft · attention required",
      level: 2,
    }),
  );
});
it("does not mark the checklist dirty merely by clicking Suggest", async () => {
  project.baseline.state = "draft";
  const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
  const normal = mock.api.getMockImplementation()!;
  mock.api.mockImplementation(async (...args: unknown[]) =>
    args[0] === "/capabilities"
      ? { model: { available: true } }
      : normal(...args),
  );
  await open("02 Checklist");
  fireEvent.click(
    screen.getByRole("button", { name: "Suggest with local AI" }),
  );
  expect(confirm).not.toHaveBeenCalled();
  await waitFor(() =>
    expect(
      mock.api.mock.calls.some(
        (args) => args[0] === "/projects/upgrade/jobs/extract",
      ),
    ).toBe(true),
  );
});
it("preserves structural checklist edits when discard before Suggest is declined", async () => {
  project.baseline.state = "draft";
  const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
  const normal = mock.api.getMockImplementation()!;
  mock.api.mockImplementation(async (...args: unknown[]) =>
    args[0] === "/capabilities"
      ? { model: { available: true } }
      : normal(...args),
  );
  await open("02 Checklist");
  fireEvent.click(screen.getByRole("button", { name: "+ Add a requirement" }));
  fireEvent.click(
    screen.getByRole("button", { name: "Suggest with local AI" }),
  );
  expect(confirm).toHaveBeenCalled();
  expect(screen.getAllByLabelText("Requirement")).toHaveLength(3);
  expect(
    mock.api.mock.calls.some(
      (args) => args[0] === "/projects/upgrade/jobs/extract",
    ),
  ).toBe(false);
});
it("shows one authoritative overview on the client delivery-record step", async () => {
  await open("05 Handoff");
  await screen.findByText("deliverable.png");
  expect(
    screen.getAllByRole("region", { name: "Before you send" }),
  ).toHaveLength(1);
  expect(document.activeElement).toBe(
    screen.getByRole("heading", {
      name: "A clear record of this delivery.",
      level: 2,
    }),
  );
});
