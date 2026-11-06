import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import DeliveryShare from "./components/DeliveryShare";
import { ApiError } from "./api";
import type { Project } from "./types";
const mock = vi.hoisted(() => ({ api: vi.fn() }));
vi.mock("./api", async (original) => ({
  ...(await original<typeof import("./api")>()),
  api: mock.api,
}));
const project = {
  id: "synthetic-share",
  revision: 12,
  input_hash: "a".repeat(64),
} as Project;
const destination = {
  label: "Trial / #delivery",
  url: "https://discord.com/channels/111/222",
};
const item = () => ({
  intent_id: "intent1",
  job_id: "job",
  export_id: "export",
  source_revision: 12,
  filename: "handoff-export.md",
  artifact_sha256: "b".repeat(64),
  artifact_size: 50,
  status: "reviewed",
  state: "authorized",
  is_current: true,
  expires_at: "2026-11-05T18:00:00Z",
  destination,
  events: [] as { state: string; attempt_id?: string; message_url?: string }[],
});
let history: {
    enabled: boolean;
    bound: boolean;
    items: ReturnType<typeof item>[];
  },
  preview: {
    job_id: string;
    source_revision: number;
    input_hash: string;
    preview_hash: string;
    preview_markdown: string;
    destination: typeof destination;
    draft: boolean;
    duplicate_risk: boolean;
    active_intent_id: string | null;
  };
const onCommitted = vi.fn(),
  onBusy = vi.fn();
const posts = () =>
  mock.api.mock.calls.filter(([, method]) => method === "POST");
beforeEach(() => {
  sessionStorage.clear();
  onCommitted.mockReset();
  onCommitted.mockResolvedValue(undefined);
  onBusy.mockReset();
  mock.api.mockReset();
  history = { enabled: true, bound: true, items: [] };
  preview = {
    job_id: "job",
    source_revision: 12,
    input_hash: project.input_hash,
    preview_hash: "c".repeat(64),
    preview_markdown: "Public approved requirement and usage note.",
    destination,
    draft: false,
    duplicate_risk: false,
    active_intent_id: null,
  };
  mock.api.mockImplementation(async (path: string, method = "GET") => {
    if (method === "GET" && path.endsWith("/delivery-shares"))
      return structuredClone(history);
    if (method === "GET" && path.endsWith("/delivery-share-preview"))
      return structuredClone(preview);
    if (method === "POST") {
      if (path.endsWith("/delivery-shares")) {
        history.items = [item()];
        preview.active_intent_id = "intent1";
      }
      if (path.endsWith("/verify")) {
        history.items[0].state = "operator_confirmed";
        history.items[0].events.push({
          state: "operator_confirmed",
          message_url: destination.url + "/999",
        });
      }
      return { state: "succeeded", result: { intent_id: "intent1" } };
    }
    throw new Error("Unexpected synthetic request");
  });
});
afterEach(cleanup);
function mount(disabled = false) {
  return render(
    <DeliveryShare
      project={project}
      disabled={disabled}
      onBusy={onBusy}
      onCommitted={onCommitted}
    />,
  );
}
async function acknowledge() {
  await screen.findByText("Destination: Trial / #delivery");
  fireEvent.click(
    screen.getByRole("checkbox", {
      name: "I reviewed the public content and this destination.",
    }),
  );
}
function freeze() {
  fireEvent.click(
    screen.getByRole("button", {
      name: "Freeze record and authorize one return",
    }),
  );
}
it("requires explicit content/destination review and freezes without claiming a send", async () => {
  mount();
  await screen.findByText("Destination: Trial / #delivery");
  expect(
    (
      screen.getByRole("button", {
        name: "Freeze record and authorize one return",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  await acknowledge();
  freeze();
  await screen.findByText(
    "Record frozen and one return authorized. Nothing has been verified as sent.",
  );
  expect(posts()).toHaveLength(1);
  expect(posts()[0][2]).toMatchObject({
    expected_revision: 12,
    input_hash: project.input_hash,
    preview_hash: preview.preview_hash,
    confirmed_reviewed: true,
    acknowledge_draft: false,
    acknowledge_duplicate_risk: false,
  });
  expect(onBusy.mock.calls.map((c) => c[0])).toContain(true);
  expect(onCommitted).toHaveBeenCalledOnce();
  expect(screen.queryByText(/Operator-confirmed exact bytes/)).toBeNull();
});
it("requires both draft and repeat-risk acknowledgement when applicable", async () => {
  preview.draft = true;
  preview.duplicate_risk = true;
  mount();
  await acknowledge();
  const button = screen.getByRole("button", {
    name: "Freeze record and authorize one return",
  }) as HTMLButtonElement;
  expect(button.disabled).toBe(true);
  fireEvent.click(
    screen.getByRole("checkbox", {
      name: "I explicitly authorize a draft return with its outstanding items visible.",
    }),
  );
  expect(button.disabled).toBe(true);
  fireEvent.click(
    screen.getByRole("checkbox", {
      name: "I checked the room and accept the risk of another copy.",
    }),
  );
  expect(button.disabled).toBe(false);
  freeze();
  await waitFor(() => expect(posts()).toHaveLength(1));
  expect(posts()[0][2]).toMatchObject({
    acknowledge_draft: true,
    acknowledge_duplicate_risk: true,
  });
});
it("retains the same authorization key through a lost reply and remount", async () => {
  const normal = mock.api.getMockImplementation()!;
  let lose = true;
  mock.api.mockImplementation(async (...args: unknown[]) => {
    if (args[1] === "POST" && lose) {
      lose = false;
      await normal(...args);
      throw new Error("Reply lost");
    }
    return normal(...args);
  });
  const first = mount();
  await acknowledge();
  freeze();
  await screen.findByText("Reply lost");
  const original = posts()[0][2];
  first.unmount();
  mount();
  fireEvent.click(
    await screen.findByRole("button", { name: "Reconcile the same operation" }),
  );
  await screen.findByText(
    "Record frozen and one return authorized. Nothing has been verified as sent.",
  );
  expect(posts()).toHaveLength(2);
  expect(posts()[1][2]).toEqual(original);
  expect(history.items).toHaveLength(1);
});
it("does not announce success if authoritative refresh fails", async () => {
  onCommitted.mockRejectedValueOnce(new Error("Project refresh unavailable"));
  mount();
  await acknowledge();
  freeze();
  await screen.findByText("Project refresh unavailable");
  expect(
    screen.queryByText(
      "Record frozen and one return authorized. Nothing has been verified as sent.",
    ),
  ).toBeNull();
  expect(
    screen.getByRole("button", { name: "Reconcile the same operation" }),
  ).toBeTruthy();
});
it("suppresses duplicate clicks while an authorization is in flight", async () => {
  const normal = mock.api.getMockImplementation()!;
  let finish: () => void = () => {};
  mock.api.mockImplementation(async (...args: unknown[]) => {
    if (args[1] === "POST")
      await new Promise<void>((resolve) => {
        finish = resolve;
      });
    return normal(...args);
  });
  mount();
  await acknowledge();
  freeze();
  freeze();
  await waitFor(() => expect(posts()).toHaveLength(1));
  finish();
  await screen.findByText(
    "Record frozen and one return authorized. Nothing has been verified as sent.",
  );
});
function issued() {
  const value = item();
  value.state = "issued_unverified";
  value.events = [{ state: "issued_unverified", attempt_id: "d".repeat(32) }];
  history.items = [value];
}
function chooseReturnedFile() {
  fireEvent.change(screen.getByLabelText("Returned Markdown file"), {
    target: {
      files: [
        new File(["actual returned bytes"], "returned.md", {
          type: "text/markdown",
        }),
      ],
    },
  });
}
it("requires actual returned file, message link and destination check even with integration disabled", async () => {
  issued();
  history.enabled = false;
  mount();
  await screen.findByText("Verify the actual return");
  const button = screen.getByRole("button", {
    name: "Verify returned bytes and destination",
  }) as HTMLButtonElement;
  expect(button.disabled).toBe(true);
  chooseReturnedFile();
  fireEvent.change(screen.getByLabelText("Discord message link"), {
    target: { value: destination.url + "/999" },
  });
  expect(button.disabled).toBe(true);
  fireEvent.click(
    screen.getByRole("checkbox", {
      name: "I checked that this file was returned in the configured destination.",
    }),
  );
  fireEvent.click(button);
  await screen.findByText(
    /Returned bytes match. Destination was checked by you/,
  );
  const form = posts()[0][2] as FormData;
  expect(form.get("file")).toBeInstanceOf(File);
  expect(JSON.parse(form.get("metadata") as string)).toMatchObject({
    attempt_id: "d".repeat(32),
    message_url: destination.url + "/999",
    confirmed_destination: true,
  });
  expect(
    screen.getByText(/Operator-confirmed exact bytes and destination/),
  ).toBeTruthy();
});
it("keeps verification replay possible after a successful write but failed refresh/remount", async () => {
  issued();
  history.enabled = false;
  onCommitted.mockRejectedValueOnce(new Error("Refresh failed"));
  const first = mount();
  await screen.findByText("Verify the actual return");
  chooseReturnedFile();
  fireEvent.change(screen.getByLabelText("Discord message link"), {
    target: { value: destination.url + "/999" },
  });
  fireEvent.click(
    screen.getByRole("checkbox", {
      name: "I checked that this file was returned in the configured destination.",
    }),
  );
  fireEvent.click(
    screen.getByRole("button", {
      name: "Verify returned bytes and destination",
    }),
  );
  await screen.findByText("Refresh failed");
  const original = JSON.parse(
    (posts()[0][2] as FormData).get("metadata") as string,
  );
  first.unmount();
  mount();
  await screen.findByText("Verify the actual return");
  expect(
    (
      screen.getByRole("button", {
        name: "Reconcile the same operation",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  chooseReturnedFile();
  fireEvent.click(
    screen.getByRole("button", { name: "Reconcile the same operation" }),
  );
  await screen.findByText(
    /Returned bytes match. Destination was checked by you/,
  );
  expect(
    JSON.parse((posts()[1][2] as FormData).get("metadata") as string),
  ).toEqual(original);
});
it("requires a cancellation reason and acknowledgement of a possibly completed send", async () => {
  issued();
  mount();
  await screen.findByText("Verify the actual return");
  const button = screen.getByRole("button", {
    name: "Cancel authorization",
  }) as HTMLButtonElement;
  fireEvent.change(screen.getByLabelText("Cancellation reason"), {
    target: { value: "I inspected the room; cannot verify this return." },
  });
  expect(button.disabled).toBe(true);
  fireEvent.click(
    screen.getByRole("checkbox", {
      name: "I understand this record may already have been sent; cancellation does not prove otherwise.",
    }),
  );
  fireEvent.click(button);
  await screen.findByText(/Return cancelled/);
  expect(posts()[0][2]).toMatchObject({ acknowledge_may_have_sent: true });
});
it("blocks authorization when a reviewed snapshot has a newer pending room hold", async () => {
  const normal = mock.api.getMockImplementation()!;
  mock.api.mockImplementation(async (...args: unknown[]) => {
    if ((args[0] as string).endsWith("/delivery-share-preview"))
      throw new ApiError("Resolve pending room work", "delivery_hold");
    return normal(...args);
  });
  mount();
  await screen.findByText("Resolve pending room work");
  expect(
    screen.queryByRole("button", {
      name: "Freeze record and authorize one return",
    }),
  ).toBeNull();
  expect(posts()).toHaveLength(0);
});
it("labels a returned old revision historical and never calls it current", async () => {
  issued();
  history.items[0].state = "operator_confirmed";
  history.items[0].is_current = false;
  history.items[0].events.push({
    state: "operator_confirmed",
    message_url: destination.url + "/999",
  });
  mount();
  await screen.findByText(
    "Historical record. It does not represent the current packet or review.",
  );
  expect(
    screen.getByText(/Operator-confirmed exact bytes and destination/),
  ).toBeTruthy();
});

it("does not claim a saved authorization when the authoritative history lacks its record", async () => {
  const normal = mock.api.getMockImplementation()!;
  mock.api.mockImplementation(async (...args: unknown[]) =>
    args[1] === "POST"
      ? { state: "succeeded", result: { intent_id: "missing-record" } }
      : normal(...args),
  );
  mount();
  await acknowledge();
  freeze();
  await screen.findByText(
    "Refresh was interrupted. Reconcile the same operation to check its result.",
  );
  expect(
    screen.queryByText(
      "Record frozen and one return authorized. Nothing has been verified as sent.",
    ),
  ).toBeNull();
  expect(
    screen.getByRole("button", { name: "Reconcile the same operation" }),
  ).toBeTruthy();
});

it.each([
  "javascript:alert(1)",
  "data:text/html,unsafe",
  "https://untrusted.example/channel",
  "https://discord.com/channels/111/222?redirect=1",
])("does not activate an unapproved destination URL %s", async (url) => {
  preview.destination = { ...destination, url };
  mount();
  await screen.findByText(/configured channel link is invalid/);
  expect(
    screen.queryByRole("link", { name: /Open the configured/ }),
  ).toBeNull();
  fireEvent.click(
    screen.getByRole("checkbox", { name: /I reviewed the public/ }),
  );
  expect(
    (
      screen.getByRole("button", {
        name: "Freeze record and authorize one return",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
});
it("keeps a verified message link bound to the exact configured channel", async () => {
  const retained = item();
  retained.state = "operator_confirmed";
  retained.events = [
    {
      state: "operator_confirmed",
      message_url: "https://discord.com/channels/333/444/999",
    },
  ];
  history.items = [retained];
  mount();
  await screen.findByText(/checked message link is invalid/);
  expect(
    screen.queryByRole("link", { name: /Open the checked message/ }),
  ).toBeNull();
});
