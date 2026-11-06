import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import DeliveryIntake from "./components/DeliveryIntake";
import type { Project } from "./types";
const mock = vi.hoisted(() => ({ api: vi.fn() }));
vi.mock("./api", async (original) => ({
  ...(await original<typeof import("./api")>()),
  api: mock.api,
}));
const project = { id: "synthetic", revision: 4 } as Project;
const receipt = (
  id: string,
  name: string,
  considered = false,
  availability = "available",
) => ({
  receipt_id: id,
  filename: name,
  source_id: `source-${id}`,
  sha256: "a".repeat(64),
  size: 123,
  availability,
  considered,
});
const intake = {
  job_id: "job",
  source_revision: 4,
  input_hash: "b".repeat(64),
  receipts: [
    receipt("new", "new.txt"),
    receipt("old", "keep.txt", true),
    receipt("bad", "broken.pdf", false, "unavailable"),
  ],
  pending_count: 2,
  last_packet: null,
};
const preview = {
  manifest_hash: "c".repeat(64),
  source_revision: 4,
  input_hash: "b".repeat(64),
  receipts: [receipt("new", "new.txt")],
  excluded_receipt_ids: ["old", "bad"],
  excluded_receipts: [
    receipt("old", "keep.txt", true),
    receipt("bad", "broken.pdf", false, "unavailable"),
  ],
  total_bytes: 123,
  changes: {
    added: ["new.txt"],
    replaced: [],
    removed: ["keep.txt"],
    unchanged: [],
  },
  review_will_be_stale: true,
};
beforeEach(() => {
  sessionStorage.clear();
  mock.api.mockReset();
  mock.api.mockImplementation(async (path: string) => {
    if (path.endsWith("/delivery"))
      return { enabled: true, job: structuredClone(intake) };
    if (path.endsWith("/packet-preview")) return structuredClone(preview);
    if (path.endsWith("/packet-confirm")) return { state: "succeeded" };
    throw new Error("Unexpected path");
  });
});
afterEach(cleanup);
function setup(onCommitted = vi.fn().mockResolvedValue(undefined)) {
  return {
    onCommitted,
    ...render(
      <DeliveryIntake
        project={project}
        disabled={false}
        onCommitted={onCommitted}
        onBusy={vi.fn()}
      />,
    ),
  };
}
async function prepare() {
  fireEvent.click(
    await screen.findByRole("button", { name: "Preview packet changes" }),
  );
  await screen.findByRole("heading", { name: "1 file · 123 B" });
}
it("defaults only available pending files and requires complete-packet confirmation", async () => {
  const { onCommitted } = setup();
  await prepare();
  const call = mock.api.mock.calls.find(([path]) =>
    path.endsWith("packet-preview"),
  );
  expect(call?.[2].receipt_ids).toEqual(["new"]);
  expect(
    screen
      .getByRole("checkbox", { name: /broken.pdf/ })
      .hasAttribute("disabled"),
  ).toBe(true);
  const confirm = screen.getByRole("button", {
    name: "Confirm complete packet",
  });
  expect(confirm.hasAttribute("disabled")).toBe(true);
  expect(screen.getByText(/Earlier assessments become stale/)).toBeTruthy();
  fireEvent.click(
    screen.getByRole("checkbox", { name: /I checked the conversation/ }),
  );
  fireEvent.click(confirm);
  await screen.findByText(/Complete packet recorded/);
  expect(onCommitted).toHaveBeenCalledOnce();
  const sent = mock.api.mock.calls.find(([path]) =>
    path.endsWith("packet-confirm"),
  )?.[2];
  expect(sent.confirmed_complete).toBe(true);
  expect(sent.manifest_hash).toBe(preview.manifest_hash);
  expect(
    sessionStorage.getItem("handoff-intake-operation-synthetic"),
  ).toBeNull();
});
it("invalidates the preview when the selection changes", async () => {
  setup();
  await prepare();
  fireEvent.click(screen.getByRole("checkbox", { name: /keep.txt/ }));
  expect(
    screen.queryByRole("button", { name: "Confirm complete packet" }),
  ).toBeNull();
});
it("names an excluded attachment that arrived after the intake list loaded", async () => {
  mock.api.mockImplementation(async (path: string) => {
    if (path.endsWith("/delivery"))
      return { enabled: true, job: structuredClone(intake) };
    if (path.endsWith("/packet-preview"))
      return {
        ...structuredClone(preview),
        excluded_receipt_ids: ["late"],
        excluded_receipts: [receipt("late", "late-correction.txt")],
      };
    throw new Error("Unexpected path");
  });
  setup();
  await prepare();
  expect(
    screen.getByText("late-correction.txt · Source: source-late"),
  ).toBeTruthy();
  expect(screen.getByText(/To include an excluded attachment/)).toBeTruthy();
  expect(
    screen
      .getByRole("button", { name: "Confirm complete packet" })
      .hasAttribute("disabled"),
  ).toBe(true);
});
it("requires a selection within the packet file limit before previewing", async () => {
  mock.api.mockResolvedValue({
    enabled: true,
    job: {
      ...intake,
      receipts: Array.from({ length: 31 }, (_, index) =>
        receipt(`r${index}`, `file${index}.txt`),
      ),
    },
  });
  setup();
  const button = await screen.findByRole("button", {
    name: "Preview packet changes",
  });
  expect(button.hasAttribute("disabled")).toBe(true);
  fireEvent.click(screen.getByRole("checkbox", { name: /file0.txt/ }));
  expect(button.hasAttribute("disabled")).toBe(false);
});
it("reconciles a lost reply using exactly the same operation key and input", async () => {
  setup();
  await prepare();
  const original = mock.api.getMockImplementation()!;
  let calls = 0;
  mock.api.mockImplementation(async (...args: unknown[]) => {
    if ((args[0] as string).endsWith("packet-confirm") && ++calls === 1)
      throw new Error("Connection lost after request");
    return original(...args);
  });
  fireEvent.click(
    screen.getByRole("checkbox", { name: /I checked the conversation/ }),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Confirm complete packet" }),
  );
  await screen.findByRole("alert");
  fireEvent.click(
    screen.getByRole("button", { name: "Reconcile the same confirmation" }),
  );
  await screen.findByText(/Complete packet recorded/);
  const confirmations = mock.api.mock.calls.filter(([path]) =>
    path.endsWith("packet-confirm"),
  );
  expect(confirmations).toHaveLength(2);
  expect(confirmations[0][2]).toEqual(confirmations[1][2]);
});
it("restores an interrupted confirmation across remount without making a new key", async () => {
  const operation = {
    operation_key: "stable",
    receipt_ids: ["new"],
    expected_revision: 4,
    input_hash: "b".repeat(64),
    manifest_hash: "c".repeat(64),
    confirmed_complete: true,
  };
  sessionStorage.setItem(
    "handoff-intake-operation-synthetic",
    JSON.stringify(operation),
  );
  setup();
  fireEvent.click(
    await screen.findByRole("button", {
      name: "Reconcile the same confirmation",
    }),
  );
  await screen.findByText(/Complete packet recorded/);
  expect(
    mock.api.mock.calls.find(([path]) => path.endsWith("packet-confirm"))?.[2],
  ).toEqual(operation);
});
it("does not announce completion before the authoritative project refresh", async () => {
  let release: () => void = () => {};
  const refresh = vi.fn(
    () =>
      new Promise<void>((resolve) => {
        release = resolve;
      }),
  );
  setup(refresh);
  await prepare();
  fireEvent.click(
    screen.getByRole("checkbox", { name: /I checked the conversation/ }),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Confirm complete packet" }),
  );
  await waitFor(() => expect(refresh).toHaveBeenCalledOnce());
  expect(screen.queryByText(/Complete packet recorded/)).toBeNull();
  release();
  await screen.findByText(/Complete packet recorded/);
});
it("does not show an intake form for an unbound project", async () => {
  mock.api.mockResolvedValue({ enabled: true, job: null });
  setup();
  await waitFor(() =>
    expect(screen.queryByText(/Checking room intake/)).toBeNull(),
  );
  expect(
    screen.queryByRole("region", { name: "Room packet intake" }),
  ).toBeNull();
});
