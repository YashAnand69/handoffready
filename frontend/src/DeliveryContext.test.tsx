import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import DeliveryContext from "./components/DeliveryContext";
import { ApiError } from "./api";
import type { Project } from "./types";
const mock = vi.hoisted(() => ({ api: vi.fn() }));
vi.mock("./api", async (original) => ({
  ...(await original<typeof import("./api")>()),
  api: mock.api,
}));
const project = {
  id: "synthetic",
  revision: 4,
  input_hash: "b".repeat(64),
  baseline: {
    state: "approved",
    requirements: [
      { id: "req-a", title: "Deliver the source" },
      { id: "req-b", title: "Confirm dimensions" },
    ],
  },
  files: [{ id: "file", name: "source.txt" }],
} as Project;
const reply = (id: string) => ({
  reply_id: id,
  source_ref: `room-message-${id}`,
  reported_speaker: "Reported teammate",
  text: `Correction ${id}`,
  text_hash: "d".repeat(64),
  created_at: "2026-11-05",
});
const question = (id: string, replies = [reply("r1"), reply("r2")]) => ({
  question_id: id,
  requirement_id: id === "q1" ? "req-a" : "req-b",
  question: `Please clarify ${id}`,
  source_ref: `room-question-${id}`,
  source_revision: 4,
  input_hash: "b".repeat(64),
  source_hash: "a".repeat(64),
  file_ids: ["file"],
  evidence: [
    { kind: "presence", status: "unknown", reason: "No confirmed selection." },
  ],
  legacy: false,
  state: "pending",
  active_context: null as null | {
    used_replies: { reply_id: string; text_hash: string; source_ref: string }[];
  },
  replies,
  latest_resolution: null as null | {
    resolution_id: string;
    action: string;
    reason: string;
    covered_reply_ids: string[];
    used_reply_ids: string[];
    created_at: string;
  },
});
const initialContext = () => ({
  job_id: "job",
  source_revision: 4,
  input_hash: "b".repeat(64),
  context_epoch: 7,
  questions: [question("q1"), question("q2", [])],
});
let data: ReturnType<typeof initialContext>;
let enabled = true;
const storageKey = "handoff-context-operation-synthetic";
const posts = () =>
  mock.api.mock.calls.filter(([, method]) => method === "POST");
beforeEach(() => {
  sessionStorage.clear();
  mock.api.mockReset();
  data = initialContext();
  enabled = true;
  mock.api.mockImplementation(
    async (
      path: string,
      method = "GET",
      payload?: {
        action: string;
        covered_reply_ids: string[];
        used_reply_ids: string[];
        reason: string;
      },
    ) => {
      if (method === "GET" && path.endsWith("/delivery-context"))
        return { enabled, job: structuredClone(data) };
      if (method === "POST" && path.endsWith("/resolve")) {
        const id = path.split("/").at(-2)!;
        const q = data.questions.find((row) => row.question_id === id)!;
        q.state = "resolved";
        q.latest_resolution = {
          resolution_id: "resolution",
          action: payload!.action,
          reason: payload!.reason,
          covered_reply_ids: payload!.covered_reply_ids,
          used_reply_ids: payload!.used_reply_ids,
          created_at: "2026-11-05",
        };
        if (payload!.action === "accept")
          q.active_context = {
            used_replies: q.replies
              .filter((r) => payload!.used_reply_ids.includes(r.reply_id))
              .map(({ reply_id, text_hash, source_ref }) => ({
                reply_id,
                text_hash,
                source_ref,
              })),
          };
        if (payload!.action === "withdraw") q.active_context = null;
        data.context_epoch++;
        return { state: "succeeded", result: { question_id: id } };
      }
      throw new Error(`Unexpected path ${path}`);
    },
  );
});
afterEach(cleanup);
function setup(
  options: {
    disabled?: boolean;
    onCommitted?: () => Promise<unknown>;
    onBusy?: (busy: boolean) => void;
    onChecklist?: () => void;
    project?: Project;
  } = {},
) {
  const props = {
    project: options.project || project,
    disabled: options.disabled || false,
    onCommitted: options.onCommitted || vi.fn().mockResolvedValue(undefined),
    onBusy: options.onBusy || vi.fn(),
    onChecklist: options.onChecklist || vi.fn(),
  };
  return { ...props, ...render(<DeliveryContext {...props} />) };
}
async function card(id = "q1") {
  return within(await screen.findByRole("article", { name: `Question ${id}` }));
}
async function prepare(id = "q1", used = ["r2"]) {
  const q = await card(id);
  for (const replyId of used)
    fireEvent.click(
      q.getByRole("checkbox", { name: `Use reply ${replyId} as context` }),
    );
  fireEvent.change(
    q.getByRole("textbox", { name: "Reason for this context decision" }),
    { target: { value: "Checked the original conversation." } },
  );
  fireEvent.click(q.getByRole("checkbox", { name: /I checked the question/ }));
  return q;
}
it("reviews two questions independently with exact covered and selected used reply sets", async () => {
  const { onCommitted, onBusy } = setup();
  const q = await card();
  expect(
    q.getByText(/Unverified question source: room-question-q1/),
  ).toBeTruthy();
  expect(q.getAllByText(/Unverified reported speaker/)).toHaveLength(2);
  expect(q.getByText(/provisional findings/)).toBeTruthy();
  expect(
    q
      .getByRole("button", { name: "Use selected replies" })
      .hasAttribute("disabled"),
  ).toBe(true);
  await prepare();
  fireEvent.click(q.getByRole("button", { name: "Use selected replies" }));
  await screen.findByText(/Context decision recorded/);
  expect(posts()).toHaveLength(1);
  expect(posts()[0][0]).toBe("/delivery/jobs/job/questions/q1/resolve");
  expect(posts()[0][2]).toMatchObject({
    expected_revision: 4,
    input_hash: project.input_hash,
    expected_context_epoch: 7,
    action: "accept",
    covered_reply_ids: ["r1", "r2"],
    used_reply_ids: ["r2"],
    confirmed_reviewed: true,
  });
  expect(await screen.findByText(/1 pending question/)).toBeTruthy();
  expect(
    (await card("q2")).getByText("Pending · delivery on hold"),
  ).toBeTruthy();
  expect(onCommitted).toHaveBeenCalledOnce();
  expect(onBusy).toHaveBeenCalledWith(true);
  expect(onBusy).toHaveBeenLastCalledWith(false);
  expect(sessionStorage.getItem(storageKey)).toBeNull();
});
it("requires a fresh reviewed checkbox after changing reply selection or reason", async () => {
  setup();
  const q = await prepare();
  fireEvent.change(q.getByRole("textbox"), {
    target: { value: "Updated reason" },
  });
  expect(
    (
      q.getByRole("checkbox", {
        name: /I checked the question/,
      }) as HTMLInputElement
    ).checked,
  ).toBe(false);
  fireEvent.click(q.getByRole("checkbox", { name: /I checked the question/ }));
  fireEvent.click(q.getByRole("checkbox", { name: "Use reply r1 as context" }));
  expect(
    q
      .getByRole("button", { name: "Use selected replies" })
      .hasAttribute("disabled"),
  ).toBe(true);
  expect(posts()).toHaveLength(0);
});
it("dismisses an unanswered question with empty covered and used sets", async () => {
  setup();
  const q = await prepare("q2", []);
  fireEvent.click(q.getByRole("button", { name: "Dismiss question" }));
  await screen.findByText(/Context decision recorded/);
  expect(posts()[0][2]).toMatchObject({
    action: "dismiss",
    covered_reply_ids: [],
    used_reply_ids: [],
    confirmed_reviewed: true,
  });
  expect(
    (await card("q2")).queryByText(/An unanswered question still holds/),
  ).toBeNull();
});
it("keeps earlier accepted context after dismissing a follow-up and withdraws only explicitly", async () => {
  data.questions[0].active_context = {
    used_replies: [
      {
        reply_id: "r1",
        text_hash: "d".repeat(64),
        source_ref: "room-message-r1",
      },
    ],
  };
  setup();
  const q = await prepare();
  fireEvent.click(q.getByRole("button", { name: "Dismiss question" }));
  await screen.findByText("Earlier accepted context is still active.");
  expect(posts()[0][2]).toMatchObject({
    action: "dismiss",
    used_reply_ids: [],
  });
  const refreshed = await prepare("q1", []);
  fireEvent.click(
    refreshed.getByRole("button", { name: "Withdraw accepted context" }),
  );
  await waitFor(() => expect(posts()).toHaveLength(2));
  await waitFor(() =>
    expect(
      screen.queryByText("Earlier accepted context is still active."),
    ).toBeNull(),
  );
  expect(posts()[1][2]).toMatchObject({
    action: "withdraw",
    covered_reply_ids: ["r1", "r2"],
    used_reply_ids: [],
  });
});
it("checklist navigation makes no request or decision and leaves both holds intact", async () => {
  const { onChecklist, onCommitted } = setup();
  fireEvent.click(
    await screen.findByRole("button", { name: "Changes checklist →" }),
  );
  expect(onChecklist).toHaveBeenCalledOnce();
  expect(onCommitted).not.toHaveBeenCalled();
  expect(posts()).toHaveLength(0);
  expect(screen.getByText(/2 pending questions/)).toBeTruthy();
  expect(sessionStorage.getItem(storageKey)).toBeNull();
});
it("replays the exact stored operation after a lost response and a remount", async () => {
  const original = mock.api.getMockImplementation()!;
  let first = true;
  mock.api.mockImplementation(async (...args: unknown[]) => {
    if (args[1] === "POST" && first) {
      first = false;
      throw new Error("Reply lost after request");
    }
    return original(...args);
  });
  const view = setup();
  const q = await prepare();
  fireEvent.click(q.getByRole("button", { name: "Use selected replies" }));
  await screen.findByRole("alert");
  const stored = JSON.parse(sessionStorage.getItem(storageKey)!);
  view.unmount();
  data.context_epoch = 99;
  setup();
  fireEvent.click(
    await screen.findByRole("button", { name: "Reconcile the same decision" }),
  );
  await screen.findByText(/Context decision recorded/);
  expect(posts()).toHaveLength(2);
  expect(posts()[1][2]).toEqual(posts()[0][2]);
  expect(posts()[1][2]).toEqual(stored.payload);
  expect(sessionStorage.getItem(storageKey)).toBeNull();
});
it("waits for project and context refresh before announcing completion", async () => {
  let releaseProject: () => void = () => {};
  let releaseContext: () => void = () => {};
  const refresh = vi.fn(
    () =>
      new Promise<void>((resolve) => {
        releaseProject = resolve;
      }),
  );
  const original = mock.api.getMockImplementation()!;
  let reads = 0;
  mock.api.mockImplementation(async (...args: unknown[]) => {
    if (args[1] !== "POST" && ++reads === 2)
      await new Promise<void>((resolve) => {
        releaseContext = resolve;
      });
    return original(...args);
  });
  setup({ onCommitted: refresh });
  const q = await prepare();
  fireEvent.click(q.getByRole("button", { name: "Use selected replies" }));
  await waitFor(() => expect(refresh).toHaveBeenCalledOnce());
  expect(screen.queryByText(/Context decision recorded/)).toBeNull();
  releaseProject();
  await waitFor(() => expect(reads).toBe(2));
  expect(screen.queryByText(/Context decision recorded/)).toBeNull();
  expect(sessionStorage.getItem(storageKey)).not.toBeNull();
  releaseContext();
  await screen.findByText(/Context decision recorded/);
});
it("retains the operation and reports no success when authoritative refresh fails", async () => {
  setup({
    onCommitted: vi.fn().mockRejectedValue(new Error("Cannot refresh project")),
  });
  const q = await prepare();
  fireEvent.click(q.getByRole("button", { name: "Use selected replies" }));
  await screen.findByText("Cannot refresh project");
  expect(screen.queryByText(/Context decision recorded/)).toBeNull();
  expect(sessionStorage.getItem(storageKey)).not.toBeNull();
  expect(
    screen.getByRole("button", { name: "Reconcile the same decision" }),
  ).toBeTruthy();
});
it("does not treat an unconfirmed operation envelope as success", async () => {
  const original = mock.api.getMockImplementation()!;
  mock.api.mockImplementation(async (...args: unknown[]) =>
    args[1] === "POST" ? { state: "unknown" } : original(...args),
  );
  const { onCommitted } = setup();
  const q = await prepare();
  fireEvent.click(q.getByRole("button", { name: "Use selected replies" }));
  await screen.findByRole("alert");
  expect(onCommitted).not.toHaveBeenCalled();
  expect(sessionStorage.getItem(storageKey)).not.toBeNull();
  expect(screen.queryByText(/Context decision recorded/)).toBeNull();
});
it("clears a definitely refused reply-race operation and requires renewed review", async () => {
  const original = mock.api.getMockImplementation()!;
  mock.api.mockImplementation(async (...args: unknown[]) => {
    if (args[1] === "POST")
      throw new ApiError(
        "Replies changed. Refresh.",
        "delivery_reply_set_conflict",
      );
    return original(...args);
  });
  setup();
  const q = await prepare();
  fireEvent.click(q.getByRole("button", { name: "Use selected replies" }));
  await screen.findByText("Replies changed. Refresh.");
  expect(sessionStorage.getItem(storageKey)).toBeNull();
  expect(
    q
      .getByRole("button", { name: "Use selected replies" })
      .hasAttribute("disabled"),
  ).toBe(true);
  expect(screen.queryByText(/Context decision recorded/)).toBeNull();
});
it("shows superseded late replies as history without controls and restricts legacy to dismissal", async () => {
  data.questions[0].state = "superseded";
  data.questions[1].legacy = true;
  setup();
  const historical = await card();
  expect(historical.getByText(/Superseded · history/)).toBeTruthy();
  expect(historical.getByText("Correction r1")).toBeTruthy();
  expect(historical.queryByRole("textbox")).toBeNull();
  expect(historical.queryByRole("checkbox")).toBeNull();
  const legacy = await card("q2");
  expect(legacy.getByText(/Original source anchor is unknown/)).toBeTruthy();
  expect(
    legacy.queryByRole("button", { name: "Use selected replies" }),
  ).toBeNull();
  expect(legacy.getByRole("button", { name: "Dismiss question" })).toBeTruthy();
});
it("retains disabled integration holds and history with resolution mutations disabled", async () => {
  enabled = false;
  setup();
  const q = await card();
  expect(screen.getByText(/Delivery integration is disabled/)).toBeTruthy();
  expect(screen.getByText(/2 pending questions/)).toBeTruthy();
  expect(
    q
      .getByRole("group", { name: "Your local context decision" })
      .hasAttribute("disabled"),
  ).toBe(true);
  expect(
    q
      .getByRole("checkbox", { name: "Use reply r1 as context" })
      .hasAttribute("disabled"),
  ).toBe(true);
  fireEvent.click(q.getByRole("button", { name: "Dismiss question" }));
  expect(posts()).toHaveLength(0);
});
it("ignores a prior project's late response after unmount", async () => {
  let finish: (value: unknown) => void = () => {};
  mock.api.mockImplementation((path: string) =>
    path.includes("synthetic/")
      ? new Promise((resolve) => {
          finish = resolve;
        })
      : Promise.resolve({ enabled: true, job: null }),
  );
  const first = setup();
  first.unmount();
  setup({ project: { ...project, id: "second" } });
  finish({ enabled: true, job: initialContext() });
  await waitFor(() =>
    expect(screen.queryByText(/Checking room context/)).toBeNull(),
  );
  expect(
    screen.queryByRole("region", { name: "Room context review" }),
  ).toBeNull();
});

it("preserves reconciliation when context refresh fails after the project refresh", async () => {
  const original = mock.api.getMockImplementation()!;
  let reads = 0;
  mock.api.mockImplementation(async (...args: unknown[]) => {
    if (args[1] !== "POST" && ++reads > 1)
      throw new Error("Cannot refresh room context");
    return original(...args);
  });
  const { onCommitted } = setup();
  const q = await prepare();
  fireEvent.click(q.getByRole("button", { name: "Use selected replies" }));
  await screen.findByText("Cannot refresh room context");
  expect(onCommitted).toHaveBeenCalledOnce();
  expect(screen.queryByText(/Context decision recorded/)).toBeNull();
  expect(sessionStorage.getItem(storageKey)).not.toBeNull();
});

it("does not refresh a different project after an old decision response arrives", async () => {
  const original = mock.api.getMockImplementation()!;
  let finish: (value: unknown) => void = () => {};
  mock.api.mockImplementation(async (...args: unknown[]) => {
    if (args[1] === "POST")
      return new Promise((resolve) => {
        finish = resolve;
      });
    if ((args[0] as string).includes("second/"))
      return { enabled: true, job: null };
    return original(...args);
  });
  const first = setup();
  const q = await prepare();
  fireEvent.click(q.getByRole("button", { name: "Use selected replies" }));
  await waitFor(() => expect(posts()).toHaveLength(1));
  first.unmount();
  const second = setup({ project: { ...project, id: "second" } });
  finish({ state: "succeeded", result: { question_id: "q1" } });
  await waitFor(() =>
    expect(screen.queryByText(/Checking room context/)).toBeNull(),
  );
  expect(first.onCommitted).not.toHaveBeenCalled();
  expect(second.onCommitted).not.toHaveBeenCalled();
  expect(sessionStorage.getItem(storageKey)).not.toBeNull();
  expect(screen.queryByText(/Context decision recorded/)).toBeNull();
});

it("preserves authored context drafts across a newer project/reply epoch and requires renewed source acknowledgement", async () => {
  const props = {
    project,
    disabled: false,
    onCommitted: vi.fn(),
    onBusy: vi.fn(),
    onChecklist: vi.fn(),
  };
  const view = render(<DeliveryContext {...props} />);
  await prepare();
  const q = await card();
  const reason = q.getByRole("textbox");
  fireEvent.change(reason, {
    target: { value: "Keep this detailed local reasoning" },
  });
  data.context_epoch++;
  data.source_revision++;
  data.questions[0].replies.push(reply("new-reply"));
  view.rerender(
    <DeliveryContext
      {...props}
      project={{ ...project, revision: project.revision + 1 }}
    />,
  );
  await waitFor(() =>
    expect(
      mock.api.mock.calls.filter(([path]) => path.endsWith("delivery-context"))
        .length,
    ).toBe(2),
  );
  await waitFor(() =>
    expect((q.getByRole("textbox") as HTMLTextAreaElement).value).toBe(
      "Keep this detailed local reasoning",
    ),
  );
  expect(
    (q.getByRole("checkbox", { name: /I checked/ }) as HTMLInputElement)
      .checked,
  ).toBe(false);
  expect(
    (
      q.getByRole("button", {
        name: /Use selected replies/,
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
});
