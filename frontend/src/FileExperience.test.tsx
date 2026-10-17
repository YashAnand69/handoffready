import { afterEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import Files from "./components/Files";
import type { Artifact, Project } from "./types";

afterEach(cleanup);
const artifact = (
  id: string,
  name: string,
  extra: Partial<Artifact> = {},
): Artifact => ({
  id,
  name,
  type: "text",
  size: 10,
  sha256: id,
  inspection: "inspected",
  metadata: {},
  text: "guide",
  error: null,
  ...extra,
});
function setup(files: Artifact[] = [], change = vi.fn()) {
  const project: Project = {
    id: "project",
    name: "Test packet",
    revision: 1,
    input_hash: "input",
    brief: null,
    baseline: {
      id: "base",
      hash: "baseline",
      state: "approved",
      requirements: [],
    },
    files,
    decisions: [],
    proposals: [],
    jobs: [],
    exports: [],
  };
  const callbacks = {
    upload: vi.fn(),
    replace: vi.fn(),
    remove: vi.fn(),
    rename: vi.fn(),
    onRenameDirty: vi.fn(),
    match: vi.fn(),
    next: vi.fn(),
  };
  const view = render(
    <div onChange={change}>
      <Files project={project} disabled={false} ready={false} {...callbacks} />
    </div>,
  );
  return { ...callbacks, ...view, project };
}
function sizedFile(name: string, size: number) {
  const file = new File(["test"], name);
  Object.defineProperty(file, "size", { value: size });
  return file;
}
function choose(files: File[]) {
  fireEvent.change(screen.getByLabelText("Choose delivery files"), {
    target: { files },
  });
}

it("rejects a selection over the count limit without submitting any of it", () => {
  const callbacks = setup(
    Array.from({ length: 30 }, (_, n) => artifact(String(n), `${n}.txt`)),
  );
  choose([new File(["more"], "extra.txt")]);
  expect(screen.getByRole("alert").textContent).toContain("up to 30 files");
  expect(callbacks.upload).not.toHaveBeenCalled();
});

it("explains tighter text/SVG and file limits, then accepts a corrected selection", () => {
  const callbacks = setup();
  choose([sizedFile("guide.MD", 1024 * 1024 + 1)]);
  expect(screen.getByRole("alert").textContent).toContain("1 MiB");
  choose([sizedFile("logo.png", 10 * 1024 * 1024 + 1)]);
  expect(screen.getByRole("alert").textContent).toContain("10 MiB");
  choose([new File([], "empty.txt")]);
  expect(screen.getByRole("alert").textContent).toContain("empty");
  expect(callbacks.upload).not.toHaveBeenCalled();
  const valid = new File(["Readable guide"], "guide.txt");
  choose([valid]);
  expect(callbacks.upload).toHaveBeenCalledExactlyOnceWith([valid]);
  expect(screen.queryByRole("alert")).toBeNull();
});

it("counts the current packet for new uploads but excludes the replaced original", () => {
  const callbacks = setup(
    Array.from({ length: 5 }, (_, n) =>
      artifact(String(n), `${n}.png`, { size: 10 * 1024 * 1024, type: "png" }),
    ),
  );
  const replacement = sizedFile("new.png", 1024);
  choose([replacement]);
  expect(screen.getByRole("alert").textContent).toContain("50 MiB packet");
  expect(callbacks.upload).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText("Replace 0.png"), {
    target: { files: [replacement] },
  });
  expect(callbacks.replace).toHaveBeenCalledExactlyOnceWith("0", replacement);
  expect(screen.queryByRole("alert")).toBeNull();
});

it("filters duplicate bytes and blocked files without changing the packet", () => {
  const callbacks = setup([
    artifact("one", "logo.png", { sha256: "same" }),
    artifact("two", "copy.png", { sha256: "same" }),
    artifact("three", "guide.pdf", {
      inspection: "blocked",
      error: "Encrypted PDFs are unsupported.",
    }),
  ]);
  fireEvent.click(screen.getByRole("button", { name: "Duplicates" }));
  expect(screen.getByRole("status").textContent).toContain("Showing 2 of 3");
  fireEvent.click(screen.getByRole("button", { name: "Needs attention" }));
  expect(screen.getByRole("status").textContent).toContain("Showing 1 of 3");
  expect(screen.getByLabelText("Replace guide.pdf")).toBeTruthy();
  expect(screen.getByText(/Export an unencrypted PDF/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Clear filters" }));
  expect(screen.getByRole("status").textContent).toContain("Showing 3 of 3");
  expect(callbacks.remove).not.toHaveBeenCalled();
  expect(callbacks.upload).not.toHaveBeenCalled();
  expect(callbacks.project.files).toHaveLength(3);
});

it("keeps an unsaved rename mounted across search and filter changes", () => {
  const dirty = vi.fn();
  const callbacks = setup(
    [artifact("one", "guide.txt"), artifact("two", "readme.md")],
    dirty,
  );
  fireEvent.click(screen.getByRole("button", { name: "Rename guide.txt" }));
  fireEvent.change(screen.getByLabelText("Delivery filename"), {
    target: { value: "revised.txt" },
  });
  expect(callbacks.onRenameDirty).toHaveBeenLastCalledWith("one", true);
  callbacks.onRenameDirty.mockClear();
  dirty.mockClear();
  fireEvent.change(screen.getByRole("searchbox"), {
    target: { value: "README" },
  });
  expect(screen.getByRole("status").textContent).toContain("Showing 1 of 2");
  expect(dirty).not.toHaveBeenCalled();
  expect(callbacks.onRenameDirty).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Clear filters" }));
  expect(
    (screen.getByLabelText("Delivery filename") as HTMLInputElement).value,
  ).toBe("revised.txt");
  fireEvent.click(screen.getByRole("button", { name: "Save filename" }));
  expect(callbacks.rename).toHaveBeenCalledExactlyOnceWith(
    "one",
    "revised.txt",
  );
});

it("retains inspectable metadata and exposes the complete file identity on demand", () => {
  setup([
    artifact("one", "guide.txt", {
      sha256: "completehash",
      metadata: { characters: 5 },
    }),
  ]);
  const details = screen
    .getByText("Inspected properties and file identity")
    .closest("details")!;
  fireEvent.click(
    within(details).getByText("Inspected properties and file identity"),
  );
  expect(details.textContent).toContain("characters");
  expect(details.textContent).toContain("completehash");
  const limits = screen
    .getByText("File limits and supported contents")
    .closest("details")!;
  expect(limits.textContent).toContain("1–10 pages");
  expect(limits.textContent).toContain("actual contents");
});
