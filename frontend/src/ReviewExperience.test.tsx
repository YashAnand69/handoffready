/** UI doubles verify navigation and evidence boundaries, not model accuracy. */
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import Review from "./components/Review";
import type { Project } from "./types";
const api = vi.hoisted(() => vi.fn());
vi.mock("./api", () => ({ api, imageUrl: vi.fn() }));
let project: Project;
beforeEach(() => {
  api.mockReset();
  project = {
    id: "desk",
    name: "Delivery",
    revision: 4,
    input_hash: "current",
    brief: null,
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
        checks: [{ kind: "manual", instruction: "Inspect it" }],
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
        internal_decision_note: "Saved note",
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
      current_review_count: 2,
      stale_review_count: 1,
      unreviewed_count: 0,
      needs_work_count: 1,
      unresolved_count: 0,
      exception_count: 0,
      failed_check_count: 0,
      unknown_check_count: 0,
      manual_requirement_count: 3,
      failed_requirement_ids: [],
      unknown_requirement_ids: [],
      attention_requirement_ids: ["r1", "r2"],
      exception_requirement_ids: [],
      rows: (["current", "current", "stale"] as const).map(
        (currency, index) => ({
          requirement_id: `r${index}`,
          review_currency: currency,
          human_disposition: index === 1 ? "needs_work" : "satisfied",
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
});
afterEach(cleanup);
function open(selected = "r0") {
  const save = vi.fn(),
    setSelected = vi.fn(),
    change = vi.fn();
  const view = render(
    <div onChange={change}>
      <Review
        project={project}
        selected={selected}
        setSelected={setSelected}
        disabled={false}
        save={save}
        next={vi.fn()}
      />
    </div>,
  );
  return { ...view, save, setSelected, change };
}
it("filters by server review currency while preserving the selected editor and draft", () => {
  const { save, setSelected, change } = open();
  fireEvent.change(screen.getByLabelText("Private review note"), {
    target: { value: "My unsaved note" },
  });
  change.mockClear();
  fireEvent.click(screen.getByRole("button", { name: "Needs review" }));
  expect(screen.queryByRole("button", { name: /^Guide / })).toBeNull();
  expect(screen.getByRole("button", { name: /^Website Stale/ })).toBeTruthy();
  expect(
    screen.getByText(/Your current item is outside this filter/),
  ).toBeTruthy();
  fireEvent.change(screen.getByLabelText("Find a requirement"), {
    target: { value: "missing" },
  });
  expect(
    screen.getByLabelText("Private review note").getAttribute("value"),
  ).toBeNull();
  expect(
    (screen.getByLabelText("Private review note") as HTMLTextAreaElement).value,
  ).toBe("My unsaved note");
  expect(change).not.toHaveBeenCalled();
  expect(save).not.toHaveBeenCalled();
  expect(setSelected).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Clear filters" }));
  expect(screen.getByRole("button", { name: /^Guide confirmed/ })).toBeTruthy();
});
it("uses current needs-work assessments for the needs-work queue, without approving stale work", () => {
  const { save } = open();
  fireEvent.click(screen.getByRole("button", { name: "Needs work" }));
  expect(screen.getByRole("button", { name: /^Guide confirmed/ })).toBeTruthy();
  expect(screen.queryByRole("button", { name: /^Website / })).toBeNull();
  expect(save).not.toHaveBeenCalled();
});
it("keeps selected files visible during filename search and submits their actual selection", () => {
  const { save, change } = open();
  fireEvent.change(screen.getByLabelText("Find a delivery file"), {
    target: { value: "guide" },
  });
  expect(change).not.toHaveBeenCalled();
  expect(
    (screen.getByRole("checkbox", { name: /logo.png/ }) as HTMLInputElement)
      .checked,
  ).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Save and next item →" }));
  expect(save).toHaveBeenCalledWith(
    expect.objectContaining({
      file_ids: ["f0"],
      human_disposition: "satisfied",
      input_hash: "current",
    }),
    true,
  );
});
it("places selection evidence before assessment and Save in reading order", () => {
  open();
  const evidence = screen.getByRole("region", {
    name: "Evidence for this review",
  });
  const save = screen.getByRole("button", {
    name: "Save my review",
  });
  const assessment = screen.getByLabelText("Your assessment");
  expect(
    evidence.compareDocumentPosition(assessment) &
      Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
  expect(
    evidence.compareDocumentPosition(save) & Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
  expect(
    within(evidence).getByRole("button", { name: "Preview selected files" }),
  ).toBeTruthy();
});
it("discards an outstanding check preview after the selected files change", async () => {
  let release: (result: unknown) => void = () => {};
  api.mockReturnValue(
    new Promise((resolve) => {
      release = resolve;
    }),
  );
  const { save } = open();
  fireEvent.click(
    screen.getByRole("button", { name: "Preview selected files" }),
  );
  expect(screen.getByText("Checking this unsaved selection…")).toBeTruthy();
  fireEvent.click(screen.getByRole("checkbox", { name: /guide.txt/ }));
  await act(async () =>
    release({
      preview: true,
      project_id: "desk",
      requirement_id: "r0",
      source_revision: 4,
      input_hash: "current",
      file_ids: ["f0"],
      selection_hash: "old",
      checks: [
        {
          requirement_id: "r0",
          kind: "presence",
          status: "pass",
          reason: "Old preview result",
        },
      ],
    }),
  );
  expect(screen.queryByText("Old preview result")).toBeNull();
  expect(save).not.toHaveBeenCalled();
});
it("falls back to decision currency if the server summary is unavailable", () => {
  delete project.attention_summary;
  project.decisions[0].input_hash = "old";
  open("r1");
  fireEvent.click(screen.getByRole("button", { name: "Needs review" }));
  expect(screen.getByRole("button", { name: /^Logo Stale/ })).toBeTruthy();
  expect(
    screen.getByRole("button", { name: /^Website Needs your review/ }),
  ).toBeTruthy();
});
