import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import Checklist from "./components/Checklist";
import type { Project } from "./types";

afterEach(cleanup);
function setup() {
  const project: Project = {
    id: "project",
    name: "Delivery",
    revision: 1,
    input_hash: "input",
    brief: null,
    baseline: { id: "base", hash: "base", state: "draft", requirements: [] },
    files: [],
    decisions: [],
    proposals: [],
    jobs: [],
    exports: [],
  };
  const save = vi.fn();
  render(
    <Checklist
      project={project}
      disabled={false}
      ready={false}
      extract={vi.fn()}
      save={save}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: "+ Add a requirement" }));
  return save;
}

it("prevents a blank or whitespace requirement from reaching draft save, then preserves a valid draft", () => {
  const save = setup();
  fireEvent.change(screen.getByLabelText("Your clarification (required)"), {
    target: { value: "Review against the client brief." },
  });
  const title = screen.getByLabelText("Requirement");
  const button = screen.getByRole("button", {
    name: "Save draft",
  }) as HTMLButtonElement;
  expect(button.disabled).toBe(true);
  fireEvent.click(button);
  expect(save).not.toHaveBeenCalled();
  expect(title.getAttribute("aria-invalid")).toBe("true");
  expect(
    document.getElementById(title.getAttribute("aria-describedby")!)
      ?.textContent,
  ).toContain("before saving");
  fireEvent.change(title, { target: { value: "   " } });
  expect(button.disabled).toBe(true);
  fireEvent.change(title, { target: { value: "Review logo usage" } });
  expect(button.disabled).toBe(false);
  fireEvent.click(button);
  expect(save).toHaveBeenCalledWith(
    [
      expect.objectContaining({
        title: "Review logo usage",
        human_note: "Review against the client brief.",
      }),
    ],
    false,
  );
});

it("requires human clarification for draft and confirmation, and resets confirmation after editing", () => {
  const save = setup();
  fireEvent.change(screen.getByLabelText("Requirement"), {
    target: { value: "Review logo usage" },
  });
  const acknowledgment = screen.getByRole("checkbox", {
    name: /I reviewed these requirements/,
  });
  fireEvent.click(acknowledgment);
  const confirm = screen.getByRole("button", {
    name: "Confirm checklist →",
  }) as HTMLButtonElement;
  expect(confirm.disabled).toBe(true);
  expect(
    (screen.getByRole("button", { name: "Save draft" }) as HTMLButtonElement)
      .disabled,
  ).toBe(true);
  fireEvent.change(screen.getByLabelText("Your clarification (required)"), {
    target: { value: "Check spacing against the approved design." },
  });
  expect((acknowledgment as HTMLInputElement).checked).toBe(false);
  fireEvent.click(acknowledgment);
  expect(confirm.disabled).toBe(false);
  fireEvent.click(confirm);
  expect(save).toHaveBeenCalledWith(
    [
      expect.objectContaining({
        human_note: "Check spacing against the approved design.",
      }),
    ],
    true,
  );
});
