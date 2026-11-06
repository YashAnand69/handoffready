import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import App from "./App";
import Brief from "./components/Brief";
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
  sessionStorage.clear();
  mock.api.mockReset();
  mock.bootstrap.mockResolvedValue({ token: "local" });
  mock.api.mockImplementation(async (path: string, method = "GET") => {
    if (path === "/projects") return [{ id: "p1", name: "North Studio" }];
    if (path.endsWith("/delivery-shares"))
      return { enabled: false, bound: false, items: [] };
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
it("distinguishes connected room providers from local-only review storage", async () => {
  const original = mock.api.getMockImplementation()!;
  mock.api.mockImplementation(async (path: string, ...args: unknown[]) => {
    if (path === "/capabilities")
      return { model: { available: false }, delivery: { enabled: true } };
    return original(path, ...args);
  });
  render(<App />);
  const notice = await screen.findByRole("complementary", {
    name: "Room coordination and privacy",
  });
  expect(notice.textContent).toContain("chat and AI providers");
  expect(notice.textContent).toContain("Keep Switch Console open");
  expect(screen.getByText("Local model optional")).toBeTruthy();
  expect(screen.queryByText("Stays on your computer")).toBeNull();
});
it("keeps standalone privacy wording when room integration is disabled", async () => {
  render(<App />);
  await screen.findByRole("button", { name: "North Studio ↗" });
  expect(screen.getByText("Stays on your computer")).toBeTruthy();
  expect(
    screen.queryByRole("complementary", {
      name: "Room coordination and privacy",
    }),
  ).toBeNull();
});
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
    expect(
      screen.getByText(/No file evidence is selected for this requirement/),
    ).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Save my review" }));
    await screen.findByText(
      /No file evidence was selected.*assessment remains Unresolved/,
    );
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

const hold = (blocked = true) => ({
  pending_context_count: blocked ? 1 : 0,
  pending_receipt_count: 0,
  blocked,
  messages: blocked ? ["Room context needs local review."] : [],
  context_epochs: { "room-job": 3 },
});
const roomJob = () => ({
  job_id: "room-job",
  source_revision: 1,
  input_hash: "current",
  context_epoch: 3,
  questions: [
    {
      question_id: "context-q",
      requirement_id: "r1",
      question: "PRIVATE_ROOM_QUESTION_42",
      source_ref: "room-question-source",
      source_revision: 1,
      input_hash: "current",
      source_hash: "source-hash",
      file_ids: ["f1"],
      evidence: [],
      legacy: false,
      state: "pending",
      active_context: null,
      replies: [
        {
          reply_id: "context-reply",
          source_ref: "room-reply-source",
          reported_speaker: "Reported teammate",
          text: "PRIVATE_ROOM_CORRECTION_42",
          text_hash: "reply-hash",
          created_at: "2026-11-05",
        },
      ],
      latest_resolution: null,
    },
  ],
});
function installRoom(enabled = false) {
  const original = mock.api.getMockImplementation()!;
  const job = roomJob();
  mock.api.mockImplementation(async (path: string, ...args: unknown[]) => {
    if (path === "/capabilities")
      return { model: { available: true }, delivery: { enabled } };
    if (path === "/projects/p1/delivery-context")
      return { enabled, job: structuredClone(job) };
    return original(path, ...args);
  });
  return { original, job };
}

describe("Room context integration", () => {
  it("shows persisted context after a disabled restart and blocks new records while retaining saved downloads", async () => {
    project.delivery_hold = hold();
    project.exports = [
      {
        id: "historical",
        snapshot_hash: "savedhash",
        preview: { input_hash: "earlier" },
      },
    ];
    installRoom(false);
    await open();
    expect(await screen.findByText("PRIVATE_ROOM_QUESTION_42")).toBeTruthy();
    expect(screen.getByText(/Delivery integration is disabled/)).toBeTruthy();
    expect(screen.getByText(/1 pending question/)).toBeTruthy();
    expect(
      screen.queryByRole("complementary", {
        name: "Room coordination and privacy",
      }),
    ).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "05 Handoff" }));
    await screen.findByText(/Delivery is on hold/);
    const acknowledgement = await screen.findByRole("checkbox", {
      name: /I reviewed this preview/,
    });
    expect((acknowledgement as HTMLInputElement).disabled).toBe(true);
    expect(
      (
        screen.getByRole("button", {
          name: "Prepare handoff snapshot →",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    expect(
      document.querySelector(".manifest-preview")?.textContent,
    ).not.toContain("PRIVATE_ROOM");
    fireEvent.click(screen.getByRole("button", { name: "Print-ready HTML ↓" }));
    await waitFor(() =>
      expect(mock.download).toHaveBeenCalledWith(
        "/projects/p1/exports/historical/html",
        "handoff-historic.html",
      ),
    );
    expect(
      mock.api.mock.calls.filter(([, method]) => method === "POST"),
    ).toHaveLength(0);
  });

  it("uses the existing unsaved-edit guard for checklist navigation without resolving the hold", async () => {
    project.delivery_hold = hold();
    installRoom();
    const confirmation = vi.spyOn(window, "confirm").mockReturnValue(false);
    try {
      await open();
      await screen.findByText("PRIVATE_ROOM_QUESTION_42");
      fireEvent.change(screen.getByLabelText("Private review note"), {
        target: { value: "Unsaved assessment draft" },
      });
      fireEvent.click(
        screen.getByRole("button", { name: "Changes checklist →" }),
      );
      expect(confirmation).toHaveBeenCalledOnce();
      expect(
        (screen.getByLabelText("Private review note") as HTMLTextAreaElement)
          .value,
      ).toBe("Unsaved assessment draft");
      confirmation.mockReturnValue(true);
      fireEvent.click(
        screen.getByRole("button", { name: "Changes checklist →" }),
      );
      expect(
        screen.getByRole("button", { name: "Confirm checklist →" }),
      ).toBeTruthy();
      expect(screen.getByText(/1 pending question/)).toBeTruthy();
      expect(project.delivery_hold.blocked).toBe(true);
      expect(
        mock.api.mock.calls.filter(([, method]) => method && method !== "GET"),
      ).toHaveLength(0);
    } finally {
      confirmation.mockRestore();
    }
  });

  it("preserves an unsaved assessment while blocking context refresh and decisions", async () => {
    project.delivery_hold = hold();
    installRoom(true);
    await open();
    const card = within(
      await screen.findByRole("region", { name: "Room context review" }),
    );
    fireEvent.click(
      card.getByRole("checkbox", {
        name: "Use reply context-reply as context",
      }),
    );
    fireEvent.change(card.getByRole("textbox"), {
      target: { value: "Checked the room source" },
    });
    fireEvent.click(
      card.getByRole("checkbox", { name: /I checked the question/ }),
    );
    expect(
      (
        card.getByRole("button", {
          name: "Use selected replies",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(false);
    fireEvent.change(screen.getByLabelText("Private review note"), {
      target: { value: "Keep this unsaved review draft" },
    });
    expect(
      card.getByText(/Save or discard your unsaved editor changes/),
    ).toBeTruthy();
    for (const name of [
      "Use selected replies",
      "Dismiss question",
      "Refresh room context",
    ]) {
      expect(
        (card.getByRole("button", { name }) as HTMLButtonElement).disabled,
      ).toBe(true);
    }
    expect(
      (screen.getByLabelText("Private review note") as HTMLTextAreaElement)
        .value,
    ).toBe("Keep this unsaved review draft");
    expect(
      mock.api.mock.calls.filter(([, method]) => method && method !== "GET"),
    ).toHaveLength(0);
  });

  it("locks navigation and other mutations until a local context operation and authoritative refresh finish", async () => {
    project.delivery_hold = hold();
    const { job } = installRoom(true);
    const original = mock.api.getMockImplementation()!;
    let finish: () => void = () => {};
    mock.api.mockImplementation(async (path: string, ...args: unknown[]) => {
      if (path.endsWith("/context-q/resolve")) {
        await new Promise<void>((resolve) => {
          finish = resolve;
        });
        job.questions[0].state = "resolved";
        project = { ...project, revision: 2, delivery_hold: hold(false) };
        job.source_revision = 2;
        job.context_epoch = 4;
        return { state: "succeeded", result: { question_id: "context-q" } };
      }
      return original(path, ...args);
    });
    await open();
    const context = within(
      await screen.findByRole("region", { name: "Room context review" }),
    );
    fireEvent.click(
      context.getByRole("checkbox", {
        name: "Use reply context-reply as context",
      }),
    );
    fireEvent.change(context.getByRole("textbox"), {
      target: { value: "Checked the original source." },
    });
    fireEvent.click(
      context.getByRole("checkbox", { name: /I checked the question/ }),
    );
    fireEvent.click(
      context.getByRole("button", { name: "Use selected replies" }),
    );
    await waitFor(() =>
      expect(
        mock.api.mock.calls.some(([path]) =>
          path.endsWith("/context-q/resolve"),
        ),
      ).toBe(true),
    );
    for (const name of [
      "02 Checklist",
      "03 Files",
      "05 Handoff",
      "← All handoffs",
      "Save my review",
      "Delete this project",
      "Changes checklist →",
    ]) {
      expect(
        (screen.getByRole("button", { name }) as HTMLButtonElement).disabled,
      ).toBe(true);
    }
    fireEvent.click(screen.getByRole("button", { name: "05 Handoff" }));
    expect(screen.getByLabelText("Private review note")).toBeTruthy();
    expect(screen.queryByText(/Context decision recorded/)).toBeNull();
    finish();
    await screen.findByText(/Context decision recorded/);
    expect(
      (screen.getByRole("button", { name: "05 Handoff" }) as HTMLButtonElement)
        .disabled,
    ).toBe(false);
    expect(screen.getByText(/0 pending questions/)).toBeTruthy();
    const mutations = mock.api.mock.calls.filter(
      ([, method]) => method && method !== "GET",
    );
    expect(mutations).toHaveLength(1);
    expect(mutations[0][2]).toMatchObject({
      confirmed_reviewed: true,
      covered_reply_ids: ["context-reply"],
      used_reply_ids: ["context-reply"],
    });
  });

  it("blocks a same-currency hold found by the client preview even if the project snapshot predates the question", async () => {
    project.delivery_hold = hold(false);
    installRoom();
    const original = mock.api.getMockImplementation()!;
    mock.api.mockImplementation(async (path: string, ...args: unknown[]) => {
      const result = await original(path, ...args);
      return path.endsWith("/handoff-preview")
        ? { ...result, delivery_hold: hold() }
        : result;
    });
    await open();
    fireEvent.click(screen.getByRole("button", { name: "05 Handoff" }));
    await screen.findByText(/Delivery is on hold/);
    expect(
      (
        screen.getByRole("button", {
          name: "Prepare handoff snapshot →",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    expect(
      (
        screen.getByRole("checkbox", {
          name: /I reviewed this preview/,
        }) as HTMLInputElement
      ).disabled,
    ).toBe(true);
  });
});

it("refuses an empty project name even when the creation form is submitted directly", async () => {
  render(<App />);
  await screen.findByRole("button", { name: "North Studio ↗" });
  fireEvent.submit(screen.getByLabelText("Project name").closest("form")!);
  await Promise.resolve();
  expect(
    mock.api.mock.calls.some(
      ([path, method]) => path === "/projects" && method === "POST",
    ),
  ).toBe(false);
});
it("requires a nonblank source label before saving a brief", () => {
  const save = vi.fn();
  render(
    <Brief
      project={project}
      disabled={false}
      ready={false}
      save={save}
      extract={vi.fn()}
    />,
  );
  fireEvent.change(screen.getByLabelText("Source label"), {
    target: { value: "   " },
  });
  const button = screen.getByRole("button", {
    name: "Save brief & continue →",
  });
  expect((button as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(button);
  expect(save).not.toHaveBeenCalled();
});
